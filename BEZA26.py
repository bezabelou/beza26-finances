import sys
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QTextEdit,
    QGridLayout,
    QFileDialog,
    QTableView,
    QListWidgetItem,
    QSpinBox
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QDate, QSettings
import json
import os
import shutil
import logging
from datetime import datetime
import locale
import qdarktheme

# Constants
DATA_FILE = "finances.json"
BUDGET_FILE = "budgets.json"
SETTINGS_FILE = "settings.json"
DEFAULT_WIDTH = 2000  # Increased width to accommodate all elements
DEFAULT_HEIGHT = 1000
APP_ICON = "path/to/your/icon.png"  # Replace with the actual path to your icon file

# Configurer la locale pour utiliser les séparateurs de milliers
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

class DashboardWidget(QWidget):
    def __init__(self, transactions):
        super().__init__()
        self.transactions = transactions
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.create_expense_pie_chart()

    def create_expense_pie_chart(self):
        expense_data = {}
        for transaction in self.transactions:
            if transaction['type'] == 'dépense':
                category = transaction['category']
                amount = transaction['amount']
                if category in expense_data:
                    expense_data[category] += amount
                else:
                    expense_data[category] = amount

        categories = list(expense_data.keys())
        amounts = list(expense_data.values())

        # Création du graphique
        fig, ax = plt.subplots()
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title('Répartition des Dépenses par Catégorie')

        # Intégration dans PyQt5
        canvas = FigureCanvas(fig)
        self.layout.addWidget(canvas)

class SavingsChartWidget(QWidget):
    """Widget pour afficher le graphique de l'épargne sur une période personnalisée"""
    
    def __init__(self, transactions, currency="Ar", start_date=None, end_date=None):
        super().__init__()
        self.transactions = transactions
        self.currency = currency
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Date selectors
        self.start_date = QDateEdit()
        if start_date:
            self.start_date.setDate(start_date)
        else:
            self.start_date.setDate(QDate.currentDate().addMonths(-11))  # Default: 12 months ago
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumDate(QDate(2000, 1, 1))
        self.start_date.setMaximumDate(QDate.currentDate())
        self.start_date.setDisplayFormat("MM/yyyy")
        
        self.end_date = QDateEdit()
        if end_date:
            self.end_date.setDate(end_date)
        else:
            self.end_date.setDate(QDate.currentDate())  # Default: today
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumDate(QDate(2000, 1, 1))
        self.end_date.setMaximumDate(QDate.currentDate())
        self.end_date.setDisplayFormat("MM/yyyy")
        
        # Update button
        self.update_btn = QPushButton("🔄 Mettre à jour le graphique")
        self.update_btn.clicked.connect(self.update_chart_from_dates)
        self.update_btn.setStyleSheet(self.get_button_style())
        
        # Add controls to layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Du:"))
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(QLabel("Au:"))
        controls_layout.addWidget(self.end_date)
        controls_layout.addWidget(self.update_btn)
        self.layout.addLayout(controls_layout)
        
        self.create_savings_chart()
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """
    
    def update_chart_from_dates(self):
        """Met à jour le graphique selon les dates sélectionnées et sauvegarde les dates"""
        self.create_savings_chart()
        # Save the selected dates
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        # Get parent FinanceApp to save settings
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, FinanceApp):
                parent.save_chart_dates(start_date, end_date)
                break
            parent = parent.parent()
    
    def create_savings_chart(self):
        """Crée un graphique linéaire montrant l'évolution de l'épargne sur la période sélectionnée"""
        # First, remove any existing canvas (but keep the controls)
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, FigureCanvas):
                widget.deleteLater()
                break
        
        # Get selected dates
        start_qdate = self.start_date.date()
        end_qdate = self.end_date.date()
        
        start_year, start_month = start_qdate.year(), start_qdate.month()
        end_year, end_month = end_qdate.year(), end_qdate.month()
        
        # Generate months data
        months_data = []
        month_labels = []
        
        current_year = start_year
        current_month = start_month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            # Formater le mois pour la comparaison (YYYY-MM)
            month_str = f"{current_year:04d}-{current_month:02d}"
            
            # Nom du mois pour l'affichage
            try:
                month_date = datetime(current_year, current_month, 1)
                month_name = month_date.strftime("%b %Y").upper()
            except:
                month_name = f"{current_month}/{current_year}"
            
            month_labels.append(month_name)
            
            # Calculer les revenus et dépenses pour ce mois
            month_income = sum(t['amount'] for t in self.transactions 
                             if t['type'] == 'revenu' and t['date'].startswith(month_str))
            month_expense = sum(t['amount'] for t in self.transactions 
                              if t['type'] == 'dépense' and t['date'].startswith(month_str))
            
            monthly_savings = month_income - month_expense
            months_data.append(monthly_savings)
            
            # Move to next month
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        # Créer le graphique
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        
        # Couleurs différentes pour les valeurs positives et négatives
        colors = ['#28a745' if val >= 0 else '#dc3545' for val in months_data]
        
        # Créer le bar chart
        bars = ax.bar(range(len(months_data)), months_data, color=colors, alpha=0.8, width=0.6)
        
        # Ajouter une ligne de tendance
        if len(months_data) > 1:
            ax.plot(range(len(months_data)), months_data, color='blue', 
                   linewidth=2, marker='o', markersize=4, alpha=0.6, zorder=5)
        
        # Configuration des axes
        ax.set_xlabel('Mois', fontsize=10, fontweight='bold')
        ax.set_ylabel(f'Épargne ({self.currency})', fontsize=10, fontweight='bold')
        ax.set_title('Évolution de l\'Épargne', fontsize=12, fontweight='bold', pad=15)
        
        # Ajouter la grille
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Définir les étiquettes des mois - horizontales
        ax.set_xticks(range(len(month_labels)))
        ax.set_xticklabels(month_labels, rotation=0, ha='center', fontsize=8)
        
        # Ajouter une ligne horizontale à zéro
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        
        # Ajuster la mise en page pour centrer et éviter les coupures
        fig.tight_layout(pad=2.0)
        plt.tight_layout()
        
        # Intégration dans PyQt5
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(canvas)
    
    def update_chart(self, transactions, currency):
        """Met à jour le graphique avec de nouvelles données"""
        self.transactions = transactions
        self.currency = currency
        # Supprimer l'ancien graphique
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        # Recréer le graphique
        self.create_savings_chart()
class TransactionDialog(QDialog):
    expense_categories = ["ENFANTS", "ALIMENTATION", "HABIT", "TRANSPORT", "VOITURE", "IMPREVUE", "CHARGES", "ANIMAUX",
                          "GADGETS", "EQUIPEMENTS ET MEUBLES", "IMPOTS", "TAXES", "AUTRES"]
    income_categories = ["SALAIRE", "VENTES", "CONSULTATION EN LIGNE", "MAQUILLAGE", "COURS DE MAQUILLAGE", "AUTRES"]

    def __init__(self, parent=None, transaction_type=""):
        super().__init__(parent)

        self.transaction_type = transaction_type
        if transaction_type == "revenu":
            self.setWindowTitle("Ajouter un revenu")
        elif transaction_type == "dépense":
            self.setWindowTitle("Ajouter une dépense")
        else:
            self.setWindowTitle("Ajouter une transaction")  # Fallback

        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setMinimumDate(QDate(2000, 1, 1))  # Allow dates from year 2000
        self.date_selector.setMaximumDate(QDate.currentDate().addYears(10))  # Allow future dates

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Montant (Ar)")

        # Categories
        self.category_combo = QComboBox()
        if transaction_type == "dépense":
            self.category_combo.addItems(self.expense_categories)
        elif transaction_type == "revenu":
            self.category_combo.addItems(self.income_categories)
        else:
            self.category_combo.addItem("Non défini")  # Cas par défaut si le type n'est pas spécifié

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description (optionnelle)")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()  # Use QGridLayout for better alignment
        layout.addWidget(QLabel("Date:"), 0, 0)
        layout.addWidget(self.date_selector, 0, 1)
        layout.addWidget(QLabel("Montant:"), 1, 0)
        layout.addWidget(self.amount_input, 1, 1)
        layout.addWidget(QLabel("Catégorie:"), 2, 0)
        layout.addWidget(self.category_combo, 2, 1)
        layout.addWidget(QLabel("Description:"), 3, 0)
        layout.addWidget(self.description_input, 3, 1)
        layout.addWidget(self.button_box, 4, 0, 1, 2)  # Span button box across two columns

        self.setLayout(layout)

    def get_data(self):
        amount_input = self.amount_input.text().replace('\xa0', '').replace(' ', '').replace(',', '.')
        try:
            amount = float(amount_input)
            if amount <= 0:
                QMessageBox.warning(self, "Erreur", "Montant doit être supérieur à zéro.")
                return None
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide")
            return None

        date_str = self.date_selector.date().toString("yyyy-MM-dd")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')  # Validate date format
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Date invalide")
            return None

        category = self.category_combo.currentText()
        description = self.description_input.toPlainText()
        return {"date": date_str, "amount": amount, "category": category, "description": description,
                "type": self.transaction_type}

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("YourOrganization", "FinanceApp")  # Organization and app name

        self.setWindowTitle("Gestion de Finances Personnelles")
        self.setGeometry(100, 100, DEFAULT_WIDTH, DEFAULT_HEIGHT)

        # Load saved geometry
        self.resize(self.settings.value("windowSize", self.size()))
        self.move(self.settings.value("windowPosition", self.pos()))

        self.transactions = []
        self.filtered_transactions = []
        self.load_data()
        self.selected_transaction = None  # Track selected transaction

        # Set the application icon
        self.setWindowIcon(QIcon(APP_ICON))

        # Attempt to change the title bar color (may not work on all platforms)
        palette = self.palette()
        palette.setColor(QPalette.Active, QPalette.Window, QColor(0, 0, 0))  # Black
        self.setPalette(palette)
        # Load saved currency from settings
        self.currency = "Ar"
        self.load_currency()

        self.budgets = {}
        self.load_budgets()
        
        # Custom category names (for display) - must load BEFORE init_ui
        self.category_display_names = {}
        self.load_category_names()
        print(f"Loaded category names: {self.category_display_names}")  # Debug

        # Economy section data
        self.investment_percentage = 50
        self.emergency_fund_percentage = 30
        self.savings_percentage = 20
        self.previous_investment_percentage = self.investment_percentage
        self.previous_emergency_fund_percentage = self.emergency_fund_percentage
        self.previous_savings_percentage = self.savings_percentage

        self.budget_exceeded_categories = []
        self.total_income_all_time = 0.0
        self.total_expense_all_time = 0.0
        self.update_all_time_totals()
        self.init_ui()
        self.update_totals()  # Initial calculation after UI is set up

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()  # Use QHBoxLayout for overall layout
        central_widget.setLayout(main_layout)

        # Left Panel (Transactions)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Month Selector
        self.month_selector = QComboBox()
        self.update_month_selector()
        self.month_selector.currentIndexChanged.connect(self.update_transaction_list)
        left_layout.addWidget(self.month_selector)

        # Transaction List
        self.transaction_list = QListWidget()
        self.transaction_list.itemClicked.connect(self.select_transaction)
        left_layout.addWidget(self.transaction_list)

        # Right Panel (Buttons, Details, Economy, Budget)
        right_panel = QWidget()
        right_layout = QVBoxLayout()  # Use QVBoxLayout for the right panel
        right_panel.setLayout(right_layout)

        # Buttons
        button_layout = QHBoxLayout()  # Horizontal layout for buttons
        self.add_income_btn = QPushButton("Ajouter Revenu")
        self.add_income_btn.clicked.connect(lambda: self.show_transaction_dialog("revenu"))
        self.add_income_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_income_btn.setStyleSheet(self.get_button_style("blue"))
        button_layout.addWidget(self.add_income_btn)

        self.add_expense_btn = QPushButton("Ajouter Dépense")
        self.add_expense_btn.clicked.connect(lambda: self.show_transaction_dialog("dépense"))
        self.add_expense_btn.setIcon(QIcon.fromTheme("list-remove"))
        self.add_expense_btn.setStyleSheet(self.get_button_style("red"))
        button_layout.addWidget(self.add_expense_btn)

        self.modify_btn = QPushButton("Modifier")
        self.modify_btn.clicked.connect(self.modify_transaction)
        self.modify_btn.setIcon(QIcon.fromTheme("edit"))
        self.modify_btn.setStyleSheet(self.get_button_style("green"))
        button_layout.addWidget(self.modify_btn)

        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.clicked.connect(self.delete_transaction)
        self.delete_btn.setIcon(QIcon.fromTheme("delete"))
        self.delete_btn.setStyleSheet(self.get_button_style("red"))
        button_layout.addWidget(self.delete_btn)

        self.save_btn = QPushButton("Sauvegarder")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setIcon(QIcon.fromTheme("document-save"))
        self.save_btn.setStyleSheet(self.get_button_style("blue"))
        button_layout.addWidget(self.save_btn)

        # Refresh Button
        self.refresh_btn = QPushButton("Rafraîchir")
        self.refresh_btn.clicked.connect(self.refresh_data)  # Connect to refresh function
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.setStyleSheet(self.get_button_style("blue"))
        button_layout.addWidget(self.refresh_btn)
        right_layout.addLayout(button_layout)

        # Transaction Details Display
        self.transaction_details_label = QLabel("Sélectionnez une transaction pour voir les détails")
        right_layout.addWidget(self.transaction_details_label)

        # Totals Display
        self.total_income_label = QLabel()
        self.total_expense_label = QLabel()
        self.monthly_savings_label = QLabel()
        self.savings_label = QLabel()
        right_layout.addWidget(self.total_income_label)
        right_layout.addWidget(self.total_expense_label)
        right_layout.addWidget(self.monthly_savings_label)
        right_layout.addWidget(self.savings_label)

        self.total_income_all_time_label = QLabel()  # New label for total income all time
        self.total_expense_all_time_label = QLabel()  # New label for total expense all time
        self.all_time_savings_label = QLabel()
        right_layout.addWidget(self.total_income_all_time_label)
        right_layout.addWidget(self.total_expense_all_time_label)
        right_layout.addWidget(self.all_time_savings_label)

        # Settings Button for Currency
        self.settings_btn = QPushButton("⚙ Paramètres")
        self.settings_btn.setMaximumWidth(165)
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        self.settings_btn.setStyleSheet(self.get_button_style("green"))
        right_layout.addWidget(self.settings_btn)

        # Currency Display Label
        self.currency_label = QLabel(f"Devise actuelle : {self.currency}")
        self.currency_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        right_layout.addWidget(self.currency_label)

        # Economy Section
        economy_layout = QFormLayout()
        self.investment_label = QLabel("Investissement (%):")
        self.investment_input = QLineEdit(str(self.investment_percentage))
        self.investment_input.setMaximumWidth(50)  # Reduced width
        self.investment_input.textChanged.connect(self.validate_economy_values)  # Connect to validation
        economy_layout.addRow(self.investment_label, self.investment_input)

        self.emergency_fund_label = QLabel("Fond d'urgence (%):")
        self.emergency_fund_input = QLineEdit(str(self.emergency_fund_percentage))
        self.emergency_fund_input.setMaximumWidth(50)  # Reduced width
        self.emergency_fund_input.textChanged.connect(self.validate_economy_values)  # Connect to validation
        economy_layout.addRow(self.emergency_fund_label, self.emergency_fund_input)

        self.savings_label_economy = QLabel("Épargne (%):")
        self.savings_input = QLineEdit(str(self.savings_percentage))
        self.savings_input.setMaximumWidth(50)  # Reduced width
        self.savings_input.textChanged.connect(self.validate_economy_values)  # Connect to validation
        economy_layout.addRow(self.savings_label_economy, self.savings_input)

        self.investment_value_label = QLabel("Valeur Investissement:")
        self.emergency_fund_value_label = QLabel("Valeur Fond d'urgence:")
        self.savings_value_label = QLabel("Valeur Épargne:")
        economy_layout.addRow(self.investment_value_label)
        economy_layout.addRow(self.emergency_fund_value_label)
        economy_layout.addRow(self.savings_value_label)
        right_layout.addLayout(economy_layout)

        # Load saved chart dates
        chart_start_date, chart_end_date = self.load_chart_dates()
        
        # 12-Month Savings Chart
        self.savings_chart = SavingsChartWidget(self.transactions, self.currency, 
                                                 chart_start_date, chart_end_date)
        self.savings_chart.setMaximumHeight(450)  # Increased from 250 to 320
        self.savings_chart.setMinimumHeight(400)  # Added minimum height
        right_layout.addWidget(self.savings_chart)

        # Budget Section (Integrated into the main window)
    
        budget_group = QWidget()
        budget_layout = QFormLayout()
        budget_group.setLayout(budget_layout)

        self.save_budgets_btn = QPushButton("💰 Enregistrer les plafonds")
        self.save_budgets_btn.clicked.connect(self.save_integrated_budgets)
        self.save_budgets_btn.setFixedSize(200, 25)  # Réduire la taille du bouton
        self.save_budgets_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0069d9;
                color: white;
                border-radius: 5px;
            }
        """)  # Mettre le bouton en bleu et ajouter un effet au survol
        budget_layout.addRow(QLabel(""), self.save_budgets_btn)  # Ajouter le bouton avant les champs de texte 

        self.category_edits = {}
        for category in TransactionDialog.expense_categories:
            # Check if we should skip this category (empty custom name means hide)
            if category in self.category_display_names and self.category_display_names[category] == "":
                # Skip this category entirely - don't add to layout
                self.category_edits[category] = None  # Mark as hidden
                continue

            edit = QLineEdit()
            edit.setPlaceholderText("Entrez le plafond...")
            edit.setMaximumWidth(90)  # Limiter la largeur des champs de texte
            if category in self.budgets:
                edit.setText(locale.format_string('%.2f', self.budgets[category], grouping=True) + " " + self.currency)
            self.category_edits[category] = edit

            # Use custom display name if available
            if category in self.category_display_names:
                display_name = self.category_display_names[category]
            else:
                display_name = category
            budget_layout.addRow(QLabel(display_name), edit)

        right_layout.addWidget(budget_group)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 2)  # Transactions
        main_layout.addWidget(right_panel, 3)  # Buttons, Details, Economy

        self.update_transaction_list()

        
    def get_button_style(self, color):
        bg_color = {
            "blue": "#007bff",
            "red": "#dc3545",
            "green": "#28a745"
        }.get(color, "#007bff")  # Default to blue if color is not found

        hover_color = {
            "blue": "#3399ff",
            "red": "#f05667",
            "green": "#5cb85c"
        }.get(color, "#3399ff")  # Default to blue hover if color is not found

        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            """

    def open_settings_dialog(self):
        """Open settings dialog to change currency and other preferences"""
        dialog = SettingsDialog(self, self.currency, self.category_display_names)
        if dialog.exec_() == QDialog.Accepted:
            new_currency = dialog.get_currency()
            if new_currency != self.currency:
                self.currency = new_currency
                self.currency_label.setText(f"Devise actuelle : {self.currency}")
                self.update_currency_in_ui()
                self.save_currency()  # Save currency to settings
                QMessageBox.information(self, "Devise mise à jour", 
                                       f"La devise a été changée en {self.currency}")
            
            # Update category display names
            new_names = dialog.get_category_names()
            if new_names != self.category_display_names:
                self.category_display_names = new_names
                self.save_category_names()
                self.update_budget_labels()  # Update budget labels with new names
                QMessageBox.information(self, "Catégories mises à jour", 
                                       "Les noms des catégories ont été mis à jour.")

    def change_currency(self):
        if self.currency_button.text() == "Devise : Ar":
            self.currency_button.setText("Devise : €")
            self.currency = "€"
        else:
            self.currency_button.setText("Devise : Ar")
            self.currency = "Ar"

        # Mettre à jour les devises dans les éléments de l'interface utilisateur
        self.update_currency_in_ui()

    def update_currency_in_ui(self):
        # Mettre à jour les devises dans les labels
        self.total_income_label.setText(self.total_income_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.total_expense_label.setText(self.total_expense_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.monthly_savings_label.setText(self.monthly_savings_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.total_income_all_time_label.setText(self.total_income_all_time_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.total_expense_all_time_label.setText(self.total_expense_all_time_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.all_time_savings_label.setText(self.all_time_savings_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.investment_value_label.setText(self.investment_value_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.emergency_fund_value_label.setText(self.emergency_fund_value_label.text().replace("Ar", self.currency).replace("€", self.currency))
        self.savings_value_label.setText(self.savings_value_label.text().replace("Ar", self.currency).replace("€", self.currency))

        # Mettre à jour les devises dans les éléments de la liste des transactions
        for i in range(self.transaction_list.count()):
            item = self.transaction_list.item(i)
            item.setText(item.text().replace("Ar", self.currency).replace("€", self.currency))

        # Mettre à jour les devises dans les budgets
        for category, edit in self.category_edits.items():
            edit.setText(edit.text().replace("Ar", self.currency).replace("€", self.currency))

    def update_month_selector(self):
        self.month_selector.clear()
        months = sorted(set(t["date"][:7] for t in self.transactions))
        for month in months:
            date_object = datetime.strptime(month, "%Y-%m")
            formatted_month = date_object.strftime("%B %Y").upper()  # Mettre en majuscule le mois
            self.month_selector.addItem(formatted_month)
        
        current_month = datetime.now()
        formatted_current_month = current_month.strftime("%B %Y").upper()  # Mettre en majuscule le mois
        if formatted_current_month not in [self.month_selector.itemText(i) for i in range(self.month_selector.count())]:
            self.month_selector.addItem(formatted_current_month)
        self.month_selector.setCurrentText(formatted_current_month)
    def save_integrated_budgets(self):
        self.budgets = self.get_integrated_budgets()
        self.save_budgets()
        self.check_budget_status()  # Re-check limits after updating budgets
        self.update_totals() 

    def modify_transaction(self):
        selected_item = self.transaction_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une transaction à modifier.")
            return

        selected_index = self.transaction_list.row(selected_item)
        transaction_to_modify = self.filtered_transactions[selected_index]

        dialog = TransactionDialog(self, transaction_to_modify["type"])
        dialog.date_selector.setDate(QDate.fromString(transaction_to_modify["date"], "yyyy-MM-dd"))
        dialog.amount_input.setText(str(transaction_to_modify["amount"]))
        dialog.category_combo.setCurrentText(transaction_to_modify["category"])
        dialog.description_input.setText(transaction_to_modify["description"])

        result = dialog.exec_()
        if result == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                # Find the index of the transaction in the original list
                original_index = self.transactions.index(transaction_to_modify)

                # Update the transaction in the original list
                self.transactions[original_index] = {
                    "type": transaction_to_modify["type"],
                    "amount": data["amount"],
                    "category": data["category"],
                    "date": data["date"],
                    "description": data["description"]
                }

                self.update_transaction_list()
                self.update_totals()
                self.save_data()

    def show_transaction_dialog(self, transaction_type):
        dialog = TransactionDialog(self, transaction_type)
        if dialog.exec_():
            new_transaction = dialog.get_data()
            if new_transaction:
                self.transactions.append(new_transaction)
                self.save_data()
                self.update_month_selector()  # Appeler la méthode update_month_selector ici
                self.update_transaction_list()
                self.update_totals()

    def delete_transaction(self):
        selected_item = self.transaction_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une transaction à supprimer.")
            return

        reply = QMessageBox.question(self, 'Supprimer',
                                     "Êtes-vous sûr de vouloir supprimer cette transaction?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            selected_index = self.transaction_list.row(selected_item)
            transaction_to_delete = self.filtered_transactions[selected_index]

            # Remove the transaction from the original list
            self.transactions.remove(transaction_to_delete)

            self.update_transaction_list()
            self.update_totals()
            self.save_data()

    def update_transaction_list(self):
        self.transaction_list.clear()
        current_month = self.month_selector.currentText()
        if not current_month:  # Vérifier si current_month est vide
            return
        
        date_object = datetime.strptime(current_month, "%B %Y")
        formatted_month = date_object.strftime("%Y-%m")
        self.filtered_transactions = sorted([t for t in self.transactions if t["date"].startswith(formatted_month)], key=lambda x: x['date'])
        for transaction in self.filtered_transactions:
            item = QListWidgetItem()
            date = datetime.strptime(transaction['date'], "%Y-%m-%d")
            formatted_date = date.strftime("%d/%m/%Y")
            amount = locale.format_string('%.2f', transaction['amount'], grouping=True)
            category = transaction['category']
            description = transaction['description']
            nature = "Dépense" if transaction['type'] == 'dépense' else "Revenu"
            item_text = f"{formatted_date} - {nature} - {amount} {self.currency} - {category} - {description}"
            item.setText(item_text)
            
            # Mettre à jour la couleur des transactions qui dépassent le budget plafond
            if category in self.budget_exceeded_categories:
                item.setForeground(Qt.red)
            
            self.transaction_list.addItem(item)
        
        # Calculer et afficher les totaux
        total_income = sum(t['amount'] for t in self.filtered_transactions if t['type'] == 'revenu')
        total_expense = sum(t['amount'] for t in self.filtered_transactions if t['type'] == 'dépense')
        monthly_savings = total_income - total_expense
        
        # Format amounts with thousand separators
        formatted_income = locale.format_string("%.2f", total_income, grouping=True)
        formatted_expense = locale.format_string("%.2f", total_expense, grouping=True)
        formatted_savings = locale.format_string("%.2f", monthly_savings, grouping=True)
        
        self.total_income_label.setText(f"Revenu total ({current_month.upper()}) : {formatted_income} {self.currency}")
        self.total_expense_label.setText(f"Dépense totale ({current_month.upper()}) : {formatted_expense} {self.currency}")
        self.monthly_savings_label.setText(f"Économies mensuelles ({current_month.upper()}) : {formatted_savings} {self.currency}")
        
        # Rafraîchir les informations de la transaction sélectionnée
        self.select_transaction()
        # Mettre à jour les budgets plafond
        self.budget_exceeded_categories = []
        for category, edit in self.category_edits.items():
            # Skip hidden categories (edit is None)
            if edit is None:
                continue
            total_expense = sum(t['amount'] for t in self.transactions if t['type'] == 'dépense' and t['category'] == category and t['date'].startswith(formatted_month))
            if category in self.budgets:
                budget_value = self.budgets[category]
                edit.setText(locale.format_string('%.2f', budget_value, grouping=True) + " " + self.currency)
                if total_expense >= budget_value:
                    self.budget_exceeded_categories.append(category)
                    edit.setStyleSheet("background-color: red; color: white;")
                    # Mettre à jour la couleur des transactions qui dépassent le budget plafond
                    for i in range(self.transaction_list.count()):
                        item = self.transaction_list.item(i)
                        if category in item.text():
                            item.setForeground(Qt.red)
                else:
                    edit.setStyleSheet("")
            else:
                edit.setText("")
    def check_budget_status(self):
        self.budget_exceeded_categories = []
        for category, budget in self.budgets.items():
            # Skip hidden categories
            if category in self.category_edits and self.category_edits[category] is None:
                continue
            total_expense = sum(t['amount'] for t in self.transactions if t['category'] == category and t['type'] == 'dépense')
            if total_expense >= budget:
                self.budget_exceeded_categories.append(category)
                if category in self.category_edits and self.category_edits[category] is not None:
                    self.category_edits[category].setStyleSheet("background-color: red; color: white;")
                QMessageBox.warning(self, "Alerte Budget", f"Le budget pour la catégorie {category} a été dépassé!")
            else:
                if category in self.category_edits and self.category_edits[category] is not None:
                    self.category_edits[category].setStyleSheet("")

    def select_transaction(self):
        selected_item = self.transaction_list.currentItem()
        if selected_item:
            selected_index = self.transaction_list.row(selected_item)
            transaction = self.filtered_transactions[selected_index]
            
            # Format the date to "dd/MM/yyyy"
            date_obj = datetime.strptime(transaction['date'], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
            
            # Format the amount with thousand separators
            formatted_amount = locale.format_string("%.2f", transaction['amount'], grouping=True)
            
            details = f"Type: {transaction['type'].capitalize().replace('é', 'e').replace('dépense', 'Dépense')}\n"
            details += f"Date: {formatted_date}\n"
            details += f"Montant: {formatted_amount} {self.currency}\n"
            details += f"Catégorie: {transaction['category']}\n"
            details += f"Description: {transaction['description']}"
            
            self.transaction_details_label.setText(details)

    def update_totals(self):
        total_income = sum(
            t['amount'] for t in self.filtered_transactions if t['type'] == 'revenu')
        total_expense = sum(
            t['amount'] for t in self.filtered_transactions if t['type'] == 'dépense')
        monthly_savings = total_income - total_expense

        # Update all-time totals
        self.update_all_time_totals()

        # Format amounts with thousand separators
        formatted_income = locale.format_string("%.2f", total_income, grouping=True)
        formatted_expense = locale.format_string("%.2f", total_expense, grouping=True)
        formatted_savings = locale.format_string("%.2f", monthly_savings, grouping=True)
        formatted_income_all_time = locale.format_string("%.2f", self.total_income_all_time, grouping=True)
        formatted_expense_all_time = locale.format_string("%.2f", self.total_expense_all_time, grouping=True)
        formatted_all_time_savings = locale.format_string("%.2f", (self.total_income_all_time - self.total_expense_all_time), grouping=True)

        self.total_income_label.setText(f"Revenu total (ce mois): {formatted_income} {self.currency}")
        self.total_expense_label.setText(f"Dépense totale (ce mois): {formatted_expense} {self.currency}")
        self.monthly_savings_label.setText(f"Économies mensuelles (ce mois): {formatted_savings} {self.currency}")

        self.total_income_all_time_label.setText(f"Revenu total (tout le temps): {formatted_income_all_time} {self.currency}")
        self.total_expense_all_time_label.setText(f"Dépense totale (tout le temps): {formatted_expense_all_time} {self.currency}")
        self.all_time_savings_label.setText(f"Économies totales (tout le temps): {formatted_all_time_savings} {self.currency}")

        self.update_economy_values()
        self.check_budget_status()  # Appel à la méthode check_budget_status
        self.update_transaction_list()

    def check_budget_status_by_month(self):
        """Check budget status for the current month (alternative version)"""
        self.budget_exceeded_categories = []
        current_month = self.month_selector.currentText()
        date_object = datetime.strptime(current_month, "%B %Y")
        formatted_month = date_object.strftime("%Y-%m")
        for category, budget in self.budgets.items():
            # Skip hidden categories
            if category in self.category_edits and self.category_edits[category] is None:
                continue
            total_expense = sum(t['amount'] for t in self.transactions if t['type'] == 'dépense' and t['category'] == category and t['date'].startswith(formatted_month))
            if total_expense >= budget:
                self.budget_exceeded_categories.append(category)
                if category in self.category_edits and self.category_edits[category] is not None:
                    self.category_edits[category].setStyleSheet("background-color: red; color: white;")
                QMessageBox.warning(self, "Budget dépassé", f"Le budget pour la catégorie '{category}' a été dépassé.")
            else:
                if category in self.category_edits and self.category_edits[category] is not None:
                    self.category_edits[category].setStyleSheet("")

    def save_integrated_budgets_full(self):
        """Save budgets with full update (alternative version)"""
        for category, edit in self.category_edits.items():
            # Skip hidden categories
            if edit is None:
                continue
            try:
                budget_value = locale.atof(edit.text().split()[0])
                self.budgets[category] = budget_value
            except (ValueError, IndexError):
                self.budgets[category] = 0
        self.save_budgets()
        self.check_budget_status()
        self.budgets = self.get_integrated_budgets()
        self.save_budgets()
        self.check_budget_limits()
        self.update_totals()
        self.update_budget_colors() 
        QMessageBox.information(self, "Budgets sauvegardés", "Les budgets ont été mis à jour avec succès.")

    def update_budget_colors(self):
        """Update budget colors for exceeded categories"""
        for category, edit in self.category_edits.items():
            # Skip hidden categories
            if edit is None:
                continue
            total_expense = sum(t['amount'] for t in self.transactions if t['type'] == 'dépense' and t['category'] == category)
            if category in self.budgets and total_expense >= self.budgets[category]:
                edit.setStyleSheet("background-color: red; color: white;")
                QMessageBox.warning(self, "Budget dépassé", f"Le budget pour la catégorie '{category}' a été dépassé.")
            else:
                edit.setStyleSheet("")

    def update_economy_values(self):
        # Use all-time savings for calculations
        all_time_savings = self.total_income_all_time - self.total_expense_all_time

        # Check if the total percentage is greater than 100 before calculating
        total_percentage = self.investment_percentage + self.emergency_fund_percentage + self.savings_percentage
        if total_percentage > 100:
            QMessageBox.warning(self, "Erreur", "La somme des pourcentages ne doit pas dépasser 100%.")
            # Revert to previous values
            self.investment_percentage = self.previous_investment_percentage
            self.emergency_fund_percentage = self.previous_emergency_fund_percentage
            self.savings_percentage = self.previous_savings_percentage
            self.investment_input.setText(str(self.investment_percentage))
            self.emergency_fund_input.setText(str(self.emergency_fund_percentage))
            self.savings_input.setText(str(self.savings_percentage))
            return  # Exit the function without updating values
        else:
            # Store current values as previous values
            self.previous_investment_percentage = self.investment_percentage
            self.previous_emergency_fund_percentage = self.emergency_fund_percentage
            self.previous_savings_percentage = self.savings_percentage

        investment_value = (self.investment_percentage / 100) * all_time_savings
        emergency_fund_value = (self.emergency_fund_percentage / 100) * all_time_savings
        savings_value = (self.savings_percentage / 100) * all_time_savings

        # Format amounts with thousand separators
        formatted_investment = locale.format_string("%.2f", investment_value, grouping=True)
        formatted_emergency_fund = locale.format_string("%.2f", emergency_fund_value, grouping=True)
        formatted_savings = locale.format_string("%.2f", savings_value, grouping=True)

        self.investment_value_label.setText(f"Valeur Investissement: {formatted_investment} {self.currency}")
        self.emergency_fund_value_label.setText(
            f"Valeur Fond d'urgence: {formatted_emergency_fund} {self.currency}")
        self.savings_value_label.setText(f"Valeur Épargne: {formatted_savings} {self.currency}")

    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.transactions = json.load(f)
        except FileNotFoundError:
            # Créer le fichier si il n'existe pas
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            self.transactions = []
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de décodage JSON : {e}")
            QMessageBox.critical(self, "Erreur",
                                "Erreur lors de la lecture des données. Le fichier est peut-être corrompu.")
            self.transactions = []
        else:
            self.update_all_time_totals()  # Make sure to calculate these after loading the data

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.transactions, f, indent=4, ensure_ascii=False)
            logging.info("Données sauvegardées avec succès.")
            QMessageBox.information(self, "Sauvegarde", "Données sauvegardées avec succès.")  # Message de succès
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des données : {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde des données : {e}")

    def load_budgets(self):
        try:
            with open(BUDGET_FILE, 'r', encoding='utf-8') as f:
                self.budgets = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de décodage JSON : {e}")
            QMessageBox.critical(self, "Erreur",
                                 "Erreur lors de la lecture des budgets. Le fichier est peut-être corrompu.")
            self.budgets = {}

    def save_budgets(self):
        try:
            with open(BUDGET_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.budgets, f, indent=4, ensure_ascii=False)
            logging.info("Budgets sauvegardés avec succès.")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des budgets : {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde des budgets : {e}")

    def closeEvent(self, event):
        # Save window geometry
        self.settings.setValue("windowSize", self.size())
        self.settings.setValue("windowPosition", self.pos())
        event.accept()

    def update_all_time_totals(self):
        self.total_income_all_time = sum(t['amount'] for t in self.transactions if t['type'] == 'revenu')
        self.total_expense_all_time = sum(t['amount'] for t in self.transactions if t['type'] == 'dépense')

    def get_integrated_budgets(self):
        budgets = {}
        for category, edit in self.category_edits.items():
            # Skip hidden categories (edit is None)
            if edit is None:
                continue
            try:
                value = locale.atof(edit.text().replace(self.currency, ''))
                if value > 0:
                    budgets[category] = value
            except ValueError:
                continue
        return budgets

    def save_integrated_budgets(self):
        self.budgets = self.get_integrated_budgets()
        self.save_budgets()
        self.check_budget_status()  # Re-check limits after updating budgets
        self.update_totals()  # Update to reflect budget changes

    def validate_economy_values(self, text):
        try:
            investment = int(self.investment_input.text())
            emergency = int(self.emergency_fund_input.text())
            savings = int(self.savings_input.text())
        except ValueError:
            return  # Ignore invalid input

        total_percentage = investment + emergency + savings

        if total_percentage > 100:
            QMessageBox.warning(self, "Erreur", "La somme des pourcentages ne doit pas dépasser 100%.")
            # Optionally, reset values to the previous state
            self.investment_input.setText(str(self.investment_percentage))
            self.emergency_fund_input.setText(str(self.emergency_fund_percentage))
            self.savings_input.setText(str(self.savings_percentage))
        else:
            self.investment_percentage = investment
            self.emergency_fund_percentage = emergency
            self.savings_percentage = savings
            self.update_economy_values()

    def refresh_data(self):
        self.load_data()
        self.load_budgets()
        self.load_category_names()
        self.update_transaction_list()
        self.update_totals()

    def load_currency(self):
        """Load saved currency from settings file"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                saved_currency = settings.get('currency')
                if saved_currency:
                    self.currency = saved_currency
        except FileNotFoundError:
            pass  # Use default "Ar"
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de décodage JSON : {e}")

    def save_currency(self):
        """Save current currency to settings file"""
        try:
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {}
            
            settings['currency'] = self.currency
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la devise : {e}")

    def load_category_names(self):
        """Load custom category display names from settings file"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.category_display_names = settings.get('category_names', {})
        except FileNotFoundError:
            self.category_display_names = {}
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de décodage JSON : {e}")
            self.category_display_names = {}

    def save_category_names(self):
        """Save custom category display names to settings file"""
        try:
            # Load existing settings or create new
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {}
            
            settings['category_names'] = self.category_display_names
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logging.info("Noms des catégories sauvegardés avec succès.")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des noms des catégories : {e}")

    def load_chart_dates(self):
        """Load saved chart dates from settings file"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                start_date_str = settings.get('chart_start_date')
                end_date_str = settings.get('chart_end_date')
                
                start_date = None
                end_date = None
                
                if start_date_str:
                    try:
                        parts = start_date_str.split('-')
                        start_date = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    except:
                        pass
                
                if end_date_str:
                    try:
                        parts = end_date_str.split('-')
                        end_date = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    except:
                        pass
                
                return start_date, end_date
        except (FileNotFoundError, json.JSONDecodeError):
            return None, None

    def save_chart_dates(self, start_date, end_date):
        """Save chart dates to settings file"""
        try:
            # Load existing settings or create new
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {}
            
            settings['chart_start_date'] = start_date.toString("yyyy-MM-dd")
            settings['chart_end_date'] = end_date.toString("yyyy-MM-dd")
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des dates du graphique : {e}")

    def update_budget_labels(self):
        """Update budget section labels with custom category display names"""
        # We need to rebuild the budget section with new labels
        # Find the right_panel from central widget
        central_widget = self.centralWidget()
        main_layout = central_widget.layout()
        
        # Right panel is the second item (index 1) in the horizontal layout
        if main_layout.count() > 1:
            right_panel_item = main_layout.itemAt(1)
            if right_panel_item:
                right_panel = right_panel_item.widget()
                if right_panel:
                    right_layout = right_panel.layout()
                    
                    # Find and remove the budget_group widget
                    # It's the last widget in the right_layout
                    for i in reversed(range(right_layout.count())):
                        item = right_layout.itemAt(i)
                        widget = item.widget()
                        if widget and isinstance(widget, QWidget):
                            # Check if this is the budget group by looking for the save button
                            try:
                                layout = widget.layout()
                                if layout and isinstance(layout, QFormLayout):
                                    # Check if it has the save_budgets_btn
                                    for j in range(layout.count()):
                                        form_item = layout.itemAt(j)
                                        field_widget = form_item.widget()
                                        if isinstance(field_widget, QPushButton) and "Enregistrer les plafonds" in field_widget.text():
                                            # Found the budget group, remove it
                                            widget.deleteLater()
                                            break
                            except:
                                pass
                    
                    # Recreate the budget section
                    budget_group = QWidget()
                    budget_layout = QFormLayout()
                    budget_group.setLayout(budget_layout)

                    self.save_budgets_btn = QPushButton("💰 Enregistrer les plafonds")
                    self.save_budgets_btn.clicked.connect(self.save_integrated_budgets)
                    self.save_budgets_btn.setFixedSize(200, 25)
                    self.save_budgets_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #007bff;
                            color: white;
                            border-radius: 5px;
                        }
                        QPushButton:hover {
                            background-color: #0069d9;
                            color: white;
                            border-radius: 5px;
                        }
                    """)
                    budget_layout.addRow(QLabel(""), self.save_budgets_btn)

                    self.category_edits = {}
                    for category in TransactionDialog.expense_categories:
                        # Check if we should skip this category (empty custom name means hide)
                        if category in self.category_display_names and self.category_display_names[category] == "":
                            # Skip this category entirely - don't add to layout
                            self.category_edits[category] = None  # Mark as hidden
                            continue
                        
                        edit = QLineEdit()
                        edit.setPlaceholderText("Entrez le plafond...")
                        edit.setMaximumWidth(90)
                        if category in self.budgets:
                            edit.setText(locale.format_string('%.2f', self.budgets[category], grouping=True) + " " + self.currency)
                        self.category_edits[category] = edit

                        # Use custom display name if available
                        if category in self.category_display_names:
                            display_name = self.category_display_names[category]
                        else:
                            display_name = category
                        budget_layout.addRow(QLabel(display_name), edit)

                    right_layout.addWidget(budget_group)
                    budget_group.show()


class SettingsDialog(QDialog):
    """Dialog for application settings including currency selection and category customization"""
    
    CURRENCIES = {
        "Ariary Malgache (Ar)": "Ar",
        "Euro (€)": "€",
        "Dollar US ($)": "$",
        "Livre Sterling (£)": "£",
        "Franc CFA (FCFA)": "FCFA",
        "Yen Japonais (¥)": "¥"
    }
    
    def __init__(self, parent=None, current_currency="Ar", category_display_names=None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Paramètres")
        self.setFixedSize(500, 600)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # === Section 1: Currency Settings ===
        currency_group = QWidget()
        currency_layout = QFormLayout()
        currency_group.setLayout(currency_layout)
        
        # Currency Selection
        self.currency_combo = QComboBox()
        for name, symbol in self.CURRENCIES.items():
            self.currency_combo.addItem(name)
            if symbol == current_currency:
                self.currency_combo.setCurrentText(name)
        
        currency_layout.addRow(QLabel("Devise :"), self.currency_combo)
        main_layout.addWidget(currency_group)
        
        # === Section 2: Category Names ===
        categories_group = QWidget()
        categories_layout = QVBoxLayout()
        categories_group.setLayout(categories_layout)
        
        categories_layout.addWidget(QLabel("<b>Personnaliser les noms des catégories de budget :</b>"))
        categories_layout.addWidget(QLabel("Laissez vide pour utiliser le nom par défaut."))
        
        # Scroll area for categories
        scroll_content = QWidget()
        scroll_layout = QFormLayout()
        scroll_content.setLayout(scroll_layout)
        
        self.category_name_edits = {}
        for category in TransactionDialog.expense_categories:
            edit = QLineEdit()
            edit.setPlaceholderText(category)  # Show default name as placeholder
            edit.setText(category_display_names.get(category, "") if category_display_names else "")
            self.category_name_edits[category] = edit
            scroll_layout.addRow(QLabel(category + " :"), edit)
        
        # Create scroll area
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        categories_layout.addWidget(scroll_area)
        main_layout.addWidget(categories_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def get_currency(self):
        """Get the selected currency symbol"""
        selected_text = self.currency_combo.currentText()
        return self.CURRENCIES.get(selected_text, "Ar")
    
    def get_category_names(self):
        """Get the customized category names (including empty strings for blank fields)"""
        category_names = {}
        for category, edit in self.category_name_edits.items():
            custom_name = edit.text().strip()
            # Store all custom names, including empty strings
            # Empty string means "show nothing" for that category
            category_names[category] = custom_name
        return category_names


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainWin = FinanceApp()
    mainWin.show()
    sys.exit(app.exec_())
