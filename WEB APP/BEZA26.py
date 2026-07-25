import streamlit as st
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import locale

# Configuration de la page Streamlit
st.set_page_config(page_title="BEZA26 - Gestion de Finances", layout="wide")

try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except:
    pass

# Style CSS personnalisé
st.markdown("""
<style>
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button {
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stFormSubmitButton > button:hover {
        background-color: #1b5e20 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stForm {
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 1.5rem !important;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Fichiers de données BEZA26
DATA_FILE = "beza26_finances.json"
BUDGET_FILE = "beza26_budgets.json"
SETTINGS_FILE = "beza26_settings.json"

DEFAULT_EXPENSE_CATEGORIES = ["ENFANTS", "ALIMENTATION", "HABIT", "TRANSPORT", "VOITURE", "IMPREVUE", "CHARGES", "ANIMAUX", "GADGETS", "EQUIPEMENTS ET MEUBLES", "IMPOTS", "TAXES", "AUTRES"]
DEFAULT_INCOME_CATEGORIES = ["SALAIRE", "VENTES", "CONSULTATION EN LIGNE", "MAQUILLAGE", "COURS DE MAQUILLAGE", "AUTRES"]

# -----------------------------------------------------------------------------
# FONCTIONS DE CHARGEMENT / SAUVEGARDE DATA
# -----------------------------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_budgets():
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_budgets(budgets):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(budgets, f, indent=4, ensure_ascii=False)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "currency": "Ar",
        "app_title": "🦅 BEZA26 — Votre Gestionnaire de Finances Personnelles",
        "expense_categories": DEFAULT_EXPENSE_CATEGORIES,
        "income_categories": DEFAULT_INCOME_CATEGORIES,
        "invest_pct": 50,
        "emergency_pct": 30,
        "savings_pct": 20
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

# Initialisation des variables de Session Streamlit
if "transactions" not in st.session_state:
    st.session_state.transactions = load_data()
if "budgets" not in st.session_state:
    st.session_state.budgets = load_budgets()
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

if "expense_categories" not in st.session_state.settings:
    st.session_state.settings["expense_categories"] = DEFAULT_EXPENSE_CATEGORIES
if "income_categories" not in st.session_state.settings:
    st.session_state.settings["income_categories"] = DEFAULT_INCOME_CATEGORIES

if "currency" not in st.session_state:
    st.session_state.currency = st.session_state.settings.get("currency", "Ar")
if "app_title" not in st.session_state:
    st.session_state.app_title = st.session_state.settings.get("app_title", "🦅 BEZA26 — Votre Gestionnaire de Finances Personnelles")

if "editing_tx" not in st.session_state:
    st.session_state.editing_tx = None

transactions = st.session_state.transactions
budgets = st.session_state.budgets

# -----------------------------------------------------------------------------
# FENÊTRE DIALOGUE (MODALE) DES PARAMÈTRES
# -----------------------------------------------------------------------------
@st.dialog("⚙️ Paramètres & Configuration", width="large")
def open_settings_dialog():
    st.markdown("### 🏷️ Titre & Devise")
    new_title = st.text_input("Nom de l'application", value=st.session_state.app_title)
    currency_list = ["Ar", "€", "$", "FCFA", "CHF"]
    default_curr_idx = currency_list.index(st.session_state.currency) if st.session_state.currency in currency_list else 0
    selected_currency = st.selectbox("Devise principale", currency_list, index=default_curr_idx)

    st.markdown("---")
    st.markdown("### 📂 Gestion des Catégories (Ajouter / Modifier / Supprimer)")
    
    col_cat1, col_cat2 = st.columns(2)
    
    # 1. Catégories Dépenses
    with col_cat1:
        st.write("**Catégories de Dépenses**")
        current_exp_cats = st.session_state.settings.get("expense_categories", DEFAULT_EXPENSE_CATEGORIES)
        
        # Ajout
        new_exp_cat = st.text_input("➕ Ajouter une dépense", key="add_exp_input")
        if st.button("Ajouter Dépense") and new_exp_cat.strip():
            cat_upper = new_exp_cat.strip().upper()
            if cat_upper not in current_exp_cats:
                current_exp_cats.append(cat_upper)
                st.session_state.settings["expense_categories"] = current_exp_cats
                save_settings(st.session_state.settings)
                st.success(f"Ajouté : {cat_upper}")
                st.rerun()

        # Modification / Renommage
        st.markdown("_Modifier un nom_")
        exp_to_rename = st.selectbox("Sélectionner à modifier", ["-- Choisir --"] + current_exp_cats, key="rename_exp_select")
        if exp_to_rename != "-- Choisir --":
            new_name_exp = st.text_input("Nouveau nom", value=exp_to_rename, key="rename_exp_val")
            if st.button("✏️ Valider modification (Dépense)"):
                new_name_upper = new_name_exp.strip().upper()
                if new_name_upper and new_name_upper != exp_to_rename:
                    idx = current_exp_cats.index(exp_to_rename)
                    current_exp_cats[idx] = new_name_upper
                    
                    # Mettre à jour les transactions existantes portant ce nom
                    for t in st.session_state.transactions:
                        if t["type"] == "dépense" and t["category"] == exp_to_rename:
                            t["category"] = new_name_upper
                    save_data(st.session_state.transactions)
                    
                    st.session_state.settings["expense_categories"] = current_exp_cats
                    save_settings(st.session_state.settings)
                    st.success("Catégorie modifiée !")
                    st.rerun()

        # Suppression
        cat_to_remove_exp = st.selectbox("Supprimer une catégorie", ["-- Aucune --"] + current_exp_cats, key="del_exp_select")
        if st.button("🗑️ Supprimer (Dépense)") and cat_to_remove_exp != "-- Aucune --":
            current_exp_cats.remove(cat_to_remove_exp)
            st.session_state.settings["expense_categories"] = current_exp_cats
            save_settings(st.session_state.settings)
            st.warning(f"Retiré : {cat_to_remove_exp}")
            st.rerun()

    # 2. Catégories Revenus
    with col_cat2:
        st.write("**Catégories de Revenus**")
        current_inc_cats = st.session_state.settings.get("income_categories", DEFAULT_INCOME_CATEGORIES)
        
        # Ajout
        new_inc_cat = st.text_input("➕ Ajouter un revenu", key="add_inc_input")
        if st.button("Ajouter Revenu") and new_inc_cat.strip():
            cat_upper = new_inc_cat.strip().upper()
            if cat_upper not in current_inc_cats:
                current_inc_cats.append(cat_upper)
                st.session_state.settings["income_categories"] = current_inc_cats
                save_settings(st.session_state.settings)
                st.success(f"Ajouté : {cat_upper}")
                st.rerun()

        # Modification / Renommage
        st.markdown("_Modifier un nom_")
        inc_to_rename = st.selectbox("Sélectionner à modifier", ["-- Choisir --"] + current_inc_cats, key="rename_inc_select")
        if inc_to_rename != "-- Choisir --":
            new_name_inc = st.text_input("Nouveau nom", value=inc_to_rename, key="rename_inc_val")
            if st.button("✏️ Valider modification (Revenu)"):
                new_name_upper = new_name_inc.strip().upper()
                if new_name_upper and new_name_upper != inc_to_rename:
                    idx = current_inc_cats.index(inc_to_rename)
                    current_inc_cats[idx] = new_name_upper
                    
                    # Mettre à jour les transactions existantes portant ce nom
                    for t in st.session_state.transactions:
                        if t["type"] == "revenu" and t["category"] == inc_to_rename:
                            t["category"] = new_name_upper
                    save_data(st.session_state.transactions)

                    st.session_state.settings["income_categories"] = current_inc_cats
                    save_settings(st.session_state.settings)
                    st.success("Catégorie modifiée !")
                    st.rerun()

        # Suppression
        cat_to_remove_inc = st.selectbox("Supprimer une catégorie", ["-- Aucune --"] + current_inc_cats, key="del_inc_select")
        if st.button("🗑️ Supprimer (Revenu)") and cat_to_remove_inc != "-- Aucune --":
            current_inc_cats.remove(cat_to_remove_inc)
            st.session_state.settings["income_categories"] = current_inc_cats
            save_settings(st.session_state.settings)
            st.warning(f"Retiré : {cat_to_remove_inc}")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Répartition Objectifs Épargne (%)")
    c_inv, c_emg, c_sav = st.columns(3)
    with c_inv:
        inv_pct = st.number_input("Investissement (%)", value=st.session_state.settings.get("invest_pct", 50))
    with c_emg:
        emg_pct = st.number_input("Fond d'urgence (%)", value=st.session_state.settings.get("emergency_pct", 30))
    with c_sav:
        sav_pct = st.number_input("Épargne (%)", value=st.session_state.settings.get("savings_pct", 20))

    st.markdown("---")
    st.markdown("### 🚨 Plafonds Budgets")
    updated_budgets = {}
    for cat in current_exp_cats:
        old_val = budgets.get(cat, 0.0)
        updated_budgets[cat] = st.number_input(f"Plafond : {cat} ({selected_currency})", value=float(old_val), key=f"dlg_bug_{cat}")

    if st.button("💾 Enregistrer toute la configuration", type="primary"):
        st.session_state.app_title = new_title
        st.session_state.currency = selected_currency
        st.session_state.budgets = updated_budgets

        st.session_state.settings.update({
            "currency": selected_currency,
            "app_title": new_title,
            "expense_categories": current_exp_cats,
            "income_categories": current_inc_cats,
            "invest_pct": inv_pct,
            "emergency_pct": emg_pct,
            "savings_pct": sav_pct
        })
        
        save_settings(st.session_state.settings)
        save_budgets(updated_budgets)
        st.success("Paramètres enregistrés avec succès !")
        st.rerun()

# -----------------------------------------------------------------------------
# INTERFACE PRINCIPALE (UI)
# -----------------------------------------------------------------------------
header_col, param_col = st.columns([4, 1])
with header_col:
    st.title(st.session_state.app_title)
with param_col:
    st.write(" ")
    if st.button("⚙️ Paramètres", type="secondary"):
        open_settings_dialog()

st.markdown("---")

currency = st.session_state.currency
EXPENSE_CATEGORIES = st.session_state.settings.get("expense_categories", DEFAULT_EXPENSE_CATEGORIES)
INCOME_CATEGORIES = st.session_state.settings.get("income_categories", DEFAULT_INCOME_CATEGORIES)

# Filtre par mois principal
months_available = sorted(list(set(t["date"][:7] for t in transactions)))
current_month_str = datetime.now().strftime("%Y-%m")
if current_month_str not in months_available:
    months_available.append(current_month_str)

selected_month = st.selectbox("Sélectionner un mois pour l'analyse", months_available, 
                              index=months_available.index(current_month_str) if current_month_str in months_available else 0)

# Filtrer les données pour le mois choisi
filtered_tx = [t for t in transactions if t["date"].startswith(selected_month)]

# Calculs
total_income_all = sum(t["amount"] for t in transactions if t["type"] == "revenu")
total_expense_all = sum(t["amount"] for t in transactions if t["type"] == "dépense")
all_time_savings = total_income_all - total_expense_all

total_income_m = sum(t["amount"] for t in filtered_tx if t["type"] == "revenu")
total_expense_m = sum(t["amount"] for t in filtered_tx if t["type"] == "dépense")
monthly_savings = total_income_m - total_expense_m

# -----------------------------------------------------------------------------
# KPI
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"Revenus ({selected_month})", value=f"{total_income_m:,.2f} {currency}")
    st.metric(label="Revenus Historiques", value=f"{total_income_all:,.2f} {currency}")
with col2:
    st.metric(label=f"Dépenses ({selected_month})", value=f"{total_expense_m:,.2f} {currency}")
    st.metric(label="Dépenses Historiques", value=f"{total_expense_all:,.2f} {currency}")
with col3:
    st.metric(label=f"Épargne du Mois", value=f"{monthly_savings:,.2f} {currency}")
    st.metric(label="Épargne Totale Globale", value=f"{all_time_savings:,.2f} {currency}")

st.markdown("---")

# Layout Gauche / Droite
main_col1, main_col2 = st.columns([1.2, 1])

with main_col1:
    is_editing = st.session_state.editing_tx is not None
    
    if is_editing:
        st.subheader("✏️ Modifier la transaction")
        current_tx = st.session_state.editing_tx
        default_type = current_tx["type"]
        default_date = datetime.strptime(current_tx["date"], "%Y-%m-%d")
        default_amount = float(current_tx["amount"])
        default_desc = current_tx["description"]
        categories = INCOME_CATEGORIES if default_type == "revenu" else EXPENSE_CATEGORIES
        default_cat_idx = categories.index(current_tx["category"]) if current_tx["category"] in categories else 0
    else:
        st.subheader("💳 Saisir une nouvelle opération")
        default_type = "revenu"
        default_date = datetime.now()
        default_amount = 0.0
        default_desc = ""
        default_cat_idx = 0

    if hasattr(st, "segmented_control"):
        tx_type = st.segmented_control("Type d'opération", ["revenu", "dépense"], default=default_type, disabled=is_editing)
    else:
        tx_type = st.radio("Type d'opération", ["revenu", "dépense"], horizontal=True, index=["revenu", "dépense"].index(default_type), disabled=is_editing)
    
    if not tx_type:
        tx_type = default_type

    categories = INCOME_CATEGORIES if tx_type == "revenu" else EXPENSE_CATEGORIES

    with st.form("transaction_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            tx_date = st.date_input("Date", value=default_date)
        with f_col2:
            tx_amount = st.number_input(f"Montant ({currency})", min_value=0.0, step=10.0, value=default_amount)
            
        tx_cat = st.selectbox("Catégorie", categories, index=default_cat_idx if default_cat_idx < len(categories) else 0)
        tx_desc = st.text_area("Description / Note", value=default_desc, placeholder="Détails de la transaction...")
        
        submit_label = "💾 Valider les modifications" if is_editing else "✨ Enregistrer l'opération"
        submit = st.form_submit_button(submit_label)
        
        if submit and tx_amount > 0:
            if is_editing:
                idx_to_update = st.session_state.transactions.index(st.session_state.editing_tx)
                st.session_state.transactions[idx_to_update] = {
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "amount": tx_amount,
                    "category": tx_cat,
                    "description": tx_desc,
                    "type": tx_type
                }
                st.session_state.editing_tx = None
                st.success("Transaction modifiée !")
            else:
                new_t = {
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "amount": tx_amount,
                    "category": tx_cat,
                    "description": tx_desc,
                    "type": tx_type
                }
                st.session_state.transactions.append(new_t)
                st.success("Transaction enregistrée !")
                
            save_data(st.session_state.transactions)
            st.rerun()
            
    if is_editing:
        if st.button("❌ Annuler l'édition"):
            st.session_state.editing_tx = None
            st.rerun()

    st.markdown("---")
    st.subheader(f"📑 Transactions du mois ({selected_month})")
    
    if not filtered_tx:
        st.write("Aucune transaction enregistrée pour cette période.")
    else:
        for idx, t in enumerate(filtered_tx):
            color = "🟢" if t["type"] == "revenu" else "🔴"
            
            try:
                date_obj = datetime.strptime(t["date"], "%Y-%m-%d")
                date_formatted = date_obj.strftime("%d/%m/%Y")
            except:
                date_formatted = t["date"]
                
            st.write(f"{color} **{t['amount']:,.2f} {currency}** — {t['category']} ({date_formatted})")
            if t['description']:
                st.caption(f"_{t['description']}_")
            
            btn_col1, btn_col2, _ = st.columns([1, 1, 2])
            with btn_col1:
                if st.button("✏️ Modif.", key=f"edit_{idx}_{t['amount']}"):
                    st.session_state.editing_tx = t
                    st.rerun()
            with btn_col2:
                if st.button("🗑️ Suppr.", key=f"del_{idx}_{t['amount']}"):
                    if st.session_state.editing_tx == t:
                        st.session_state.editing_tx = None
                    st.session_state.transactions.remove(t)
                    save_data(st.session_state.transactions)
                    st.warning("Transaction supprimée")
                    st.rerun()
            st.markdown(" ")

with main_col2:
    inv_p = st.session_state.settings.get("invest_pct", 50)
    emg_p = st.session_state.settings.get("emergency_pct", 30)
    sav_p = st.session_state.settings.get("savings_pct", 20)

    st.subheader("📊 Dispatch Épargne Mensuelle Réelle")
    st.info(f"**Investissement ({inv_p}%)** : {max(0.0, monthly_savings * inv_p / 100):,.2f} {currency}")
    st.info(f"**Fond d'urgence ({emg_p}%)** : {max(0.0, monthly_savings * emg_p / 100):,.2f} {currency}")
    st.info(f"**Épargne pure ({sav_p}%)** : {max(0.0, monthly_savings * sav_p / 100):,.2f} {currency}")

    st.markdown("---")
    
    st.subheader("🥧 Répartition des dépenses")
    expense_data = {}
    for t in filtered_tx:
        if t['type'] == 'dépense':
            expense_data[t['category']] = expense_data.get(t['category'], 0) + t['amount']
            
    if expense_data:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(expense_data.values(), labels=expense_data.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.info("Aucune dépense ce mois-ci pour générer le graphique.")

    st.markdown("---")
    st.subheader("⚠️ Alertes Budget")
    for cat, limit in budgets.items():
        if limit > 0:
            spent = sum(t["amount"] for t in filtered_tx if t["type"] == "dépense" and t["category"] == cat)
            if spent > limit:
                st.error(f"🚨 **Dépassement sur {cat}** : {spent:,.2f} / {limit:,.2f} {currency} consommés !")
            elif spent > limit * 0.8:
                st.warning(f"⚠️ **Attention sur {cat}** : {spent:,.2f} / {limit:,.2f} {currency} (80% atteint)")