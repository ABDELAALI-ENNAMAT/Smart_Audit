"""
SmartAudit — Système d'Alertes et Détection d'Anomalies.
Cartes de détection structurées avec cartographie des responsabilités.
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, format_currency,
                                get_theme_css, get_colors)
from utils.chart_builder import (make_anomaly_scatter, make_anomaly_by_reason_bar,
                                  make_anomaly_heatmap, make_anomaly_by_reason_pareto)
from utils.ui_helpers import render_page_header, render_footer, render_finding_card
from utils.icons import icon, inline_icon

st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()
df_all = load_data(st.session_state.get("app_currency", "MAD"))
df = get_filtered_data(df_all,
    lines=st.session_state.get("selected_lines"),
    shifts=st.session_state.get("selected_shifts"),
    date_start=st.session_state.get("date_start"),
    date_end=st.session_state.get("date_end"),
)

if df.empty:
    st.warning("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

render_page_header("alert_triangle", "Système d'Alertes — Détection d'Anomalies",
                   "Surveillance proactive par Isolation Forest", c)

# Stats
anomalies = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else pd.DataFrame()
n_anom = len(anomalies)
n_total = len(df)
pct_anom = n_anom / n_total * 100 if n_total > 0 else 0

normal_hc = df[df["Anomaly_Flag"] == False]["Total_Hidden_Cost"].mean() if "Anomaly_Flag" in df.columns else 0
anom_hc = anomalies["Total_Hidden_Cost"].mean() if not anomalies.empty else 0
if pd.isna(normal_hc): normal_hc = 0
if pd.isna(anom_hc): anom_hc = 0
extra_cost = anom_hc - normal_hc

normal_oee = df[df["Anomaly_Flag"] == False]["OEE"].mean() * 100 if "Anomaly_Flag" in df.columns and not df[df["Anomaly_Flag"] == False].empty else 0
anom_oee = anomalies["OEE"].mean() * 100 if not anomalies.empty else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Anomalies Détectées", f"{n_anom}", f"{pct_anom:.1f}% du total", delta_color="normal")
with k2:
    st.metric("OEE Anomalies", f"{anom_oee:.1f}%", f"{anom_oee - normal_oee:.1f}% vs normal", delta_color="normal")
with k3:
    st.metric("Surcoût par Anomalie", format_currency(extra_cost), delta=" ", delta_color="off")
with k4:
    total_extra = extra_cost * n_anom
    st.metric("Impact Total", format_currency(total_extra), delta=" ", delta_color="off")

# Charts
ch1, ch2 = st.columns(2)
with ch1:
    st.plotly_chart(make_anomaly_scatter(df), use_container_width=True, key="anom_scatter")
with ch2:
    st.plotly_chart(make_anomaly_by_reason_pareto(df), use_container_width=True, key="anom_reason")

st.plotly_chart(make_anomaly_heatmap(df, title="Anomalies par Ligne × Équipe"), use_container_width=True, key="anom_heatmap")

# ═══════════════════════════════════════════════════════════════
# ── Cartes de détection structurées par anomalie
# ═══════════════════════════════════════════════════════════════

# Shift and Downtime translation maps
SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
DOWNTIME_REASON_MAP_FR = {
    "Supplier_Delay": "Retard Fournisseur",
    "Supplier Delay": "Retard Fournisseur",
    "IT_SAP_Issue": "Problème IT/SAP",
    "IT SAP Issue": "Problème IT/SAP",
    "Changeover_Issue": "Changement de Série",
    "Changeover Issue": "Changement de Série",
    "Operator_Absence": "Absence Opérateur",
    "Operator Absence": "Absence Opérateur",
    "Tool_Breakage": "Casse d'Outil",
    "Tool Breakage": "Casse d'Outil",
    "Quality_Hold": "Blocage Qualité",
    "Quality Hold": "Blocage Qualité",
    "Machine_Failure": "Panne Machine",
    "Machine Failure": "Panne Machine",
    "Material_Shortage": "Manque Matière",
    "Material Shortage": "Manque Matière",
    "Safety_Stop": "Arrêt Sécurité",
    "Safety Stop": "Arrêt Sécurité",
    "None": "Non spécifié",
}

# Responsibility mapping
RESPONSABLE_MAP = {
    "Machine_Failure": "Maintenance",
    "Material_Shortage": "Supply Chain",
    "Operator_Absence": "RH",
    "Quality_Hold": "Qualité",
    "IT_SAP_Issue": "IT",
    "Tool_Breakage": "Maintenance",
    "Safety_Stop": "HSE",
    "Changeover_Issue": "Méthodes",
    "Supplier_Delay": "Achats",
    "Non spécifié": "Superviseur Production",
}

# Action recommendations by cause
ACTION_MAP = {
    "Machine_Failure": "Planifier une révision majeure et activer la maintenance prédictive. Vérifier le plan de maintenance préventive.",
    "Material_Shortage": "Revoir les niveaux de stock minimum et diversifier les fournisseurs. Activer le stock de sécurité.",
    "Operator_Absence": "Analyser les causes d'absentéisme, renforcer le pool de remplacement et adapter le planning.",
    "Quality_Hold": "Renforcer les contrôles à la réception matière, auditer le processus qualité et former les opérateurs.",
    "IT_SAP_Issue": "Escalader au service IT, vérifier la connectivité SAP et activer les procédures de contournement.",
    "Tool_Breakage": "Inspecter l'outillage, commander les pièces de rechange et revoir le programme de remplacement préventif.",
    "Safety_Stop": "Conduire une analyse de risque, vérifier la conformité EHS et mettre à jour les procédures de sécurité.",
    "Changeover_Issue": "Appliquer la méthode SMED, standardiser les procédures de changement et former les équipes.",
    "Supplier_Delay": "Contacter le fournisseur, activer les sources alternatives et revoir les conditions contractuelles.",
    "Non spécifié": "Suivre les indicateurs de performance standards et valider la saisie des arrêts.",
}

CAUSE_MAP = {
    "Machine_Failure": "Défaillance mécanique ou électrique de l'équipement de production.",
    "Material_Shortage": "Rupture de stock ou indisponibilité des matières premières nécessaires.",
    "Operator_Absence": "Absence non planifiée d'opérateurs clés impactant la capacité de la ligne.",
    "Quality_Hold": "Blocage qualité suite à des non-conformités détectées en cours de production.",
    "IT_SAP_Issue": "Dysfonctionnement du système SAP impactant le pilotage de la production.",
    "Tool_Breakage": "Casse d'outillage nécessitant un arrêt pour remplacement.",
    "Safety_Stop": "Arrêt de sécurité déclenché suite à un incident ou une alerte HSE.",
    "Changeover_Issue": "Temps de changement de série excessif impactant la disponibilité.",
    "Supplier_Delay": "Retard de livraison fournisseur perturbant le planning de production.",
    "Non spécifié": "Aucun dysfonctionnement ou arrêt majeur déclaré.",
}

if not anomalies.empty:
    st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["danger"]}; display:inline-block;">{inline_icon("target", 16, c["danger"])} Fiches de Constat — Top 5 Anomalies</p>', unsafe_allow_html=True)

    # Top 5 anomalies by hidden cost
    top5 = anomalies.nlargest(5, "Total_Hidden_Cost")

    for _, row in top5.iterrows():
        cause = str(row.get("Downtime_Reason", "Non spécifié"))
        if pd.isna(row.get("Downtime_Reason")):
            cause = "Non spécifié"

        line = row.get("Production_Line", "N/A")
        shift = row.get("Shift_Type", "N/A")
        date_str = row["Date"].strftime("%d/%m/%Y") if hasattr(row["Date"], "strftime") else str(row["Date"])
        oee_val = row.get("OEE", 0) * 100
        hc_val = row.get("Total_Hidden_Cost", 0)
        extra = hc_val - normal_hc

        shift_fr = SHIFT_MAP_FR.get(shift, shift)
        cause_fr = DOWNTIME_REASON_MAP_FR.get(cause, cause)
        constat = f"{line} / {shift_fr} le {date_str} — OEE {oee_val:.1f}% (cause : {cause_fr})"
        impact = f"{format_currency(hc_val)} de coûts cachés (surcout : {format_currency(max(0, extra))})"
        cause_desc = CAUSE_MAP.get(cause, f"Cause identifiée : {cause}. Analyse approfondie requise.")
        recommandation = ACTION_MAP.get(cause, "Analyser la cause racine et mettre en place un plan d'action correctif.")
        responsable = RESPONSABLE_MAP.get(cause, "Direction Production")

        render_finding_card(constat, impact, cause_desc, recommandation, responsable, c)

    # Anomaly table
    st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("clipboard_list", 16, c["primary"])} Détail des Anomalies</p>', unsafe_allow_html=True)

    show_df = anomalies.sort_values("Date", ascending=False).head(30).copy()
    show_df["Date_Fmt"] = show_df["Date"].dt.strftime("%d/%m/%Y")
    show_df["OEE_Fmt"] = show_df["OEE_Pct"].apply(lambda x: f"{x:.1f}%")
    show_df["HC_Fmt"] = show_df["Total_Hidden_Cost"].apply(lambda x: format_currency(x))
    show_df["Extra"] = show_df["Total_Hidden_Cost"].apply(lambda x: format_currency(x - normal_hc))

    # Translate display values
    show_df["Shift_Type"] = show_df["Shift_Type"].map(SHIFT_MAP_FR).fillna(show_df["Shift_Type"])
    if "Downtime_Reason" in show_df.columns:
        show_df["Downtime_Reason"] = show_df["Downtime_Reason"].map(DOWNTIME_REASON_MAP_FR).fillna(show_df["Downtime_Reason"])

    display_cols = {
        "Date_Fmt": "Date", "Production_Line": "Ligne", "Shift_Type": "Équipe",
        "OEE_Fmt": "OEE", "HC_Fmt": "Coût Caché", "Extra": "Surcoût vs Normal"
    }
    if "Downtime_Reason" in show_df.columns:
        display_cols["Downtime_Reason"] = "Cause"

    st.dataframe(
        show_df[list(display_cols.keys())].rename(columns=display_cols),
        use_container_width=True, hide_index=True, height=400,
    )
else:
    st.success("Aucune anomalie détectée dans la période sélectionnée.")

# ═══════════════════════════════════════════════════════════════
# MÉTHODOLOGIE — Isolation Forest (Task 4)
# ═══════════════════════════════════════════════════════════════

with st.expander("Méthodologie : Détection d'Anomalies (Isolation Forest)", expanded=False):
    st.markdown(f"""
    <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
        <strong style="color:{c['text_primary']};">Algorithme utilisé :</strong> Le système utilise
        <strong style="color:{c['text_primary']};">Isolation Forest</strong> (Liu, Ting & Zhou, 2008),
        un algorithme de détection d'anomalies non supervisé particulièrement adapté aux données
        multidimensionnelles de production industrielle.<br><br>

        <strong style="color:{c['text_primary']};">Paramétrage :</strong><br>
        <code style="color:{c['accent_cyan']};">contamination = 0.05</code> — environ 5% des équipes
        sont attendues comme statistiquement atypiques, conformément aux benchmarks AIAG.<br>
        <code style="color:{c['accent_cyan']};">n_estimators = 100</code> — nombre d'arbres d'isolation
        garantissant la stabilité des résultats.<br>
        <code style="color:{c['accent_cyan']};">random_state = 42</code> — reproductibilité totale
        des résultats entre exécutions.<br><br>

        <strong style="color:{c['text_primary']};">Interprétation :</strong> Une « anomalie » au sens
        statistique signifie qu'une équipe présente un profil
        <strong style="color:{c['text_primary']};">atypique par rapport à la distribution normale</strong>
        des paramètres de production — ce n'est pas nécessairement une erreur. C'est un
        <strong style="color:{c['text_primary']};">signal d'alerte pour investigation</strong>,
        qui alimente directement le Plan d'Action ci-dessous.
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PLAN D'ACTION — Suivi des Corrections (Task 2)
# ═══════════════════════════════════════════════════════════════

from utils.ui_helpers import render_section_title, render_empty_state
from utils.icons import status_dot
from datetime import datetime, timedelta

render_section_title(
    f"{inline_icon('clipboard_list', 16, c['primary'])} Plan d'Action — Suivi des Corrections", c, c["primary"]
)


def _build_action_plan_df(anomalies_df, normal_hc_val):
    """Construit le DataFrame du plan d'action à partir des anomalies détectées."""
    if anomalies_df.empty:
        return pd.DataFrame(columns=[
            "Constat", "Cause", "Action Recommandée", f"Gain Estimé ({curr_sym})",
            "Responsable", "Échéance", "Statut", "Commentaire",
        ])

    top5 = anomalies_df.nlargest(5, "Total_Hidden_Cost")
    rows = []
    for _, row in top5.iterrows():
        cause = str(row.get("Downtime_Reason", "Non spécifié"))
        if pd.isna(row.get("Downtime_Reason")):
            cause = "Non spécifié"
        line = row.get("Production_Line", "N/A")
        shift = row.get("Shift_Type", "N/A")
        date_str = row["Date"].strftime("%d/%m/%Y") if hasattr(row["Date"], "strftime") else str(row["Date"])
        oee_val = row.get("OEE", 0) * 100
        hc_val = row.get("Total_Hidden_Cost", 0)
        extra = max(0, hc_val - normal_hc_val)

        shift_fr = SHIFT_MAP_FR.get(shift, shift)
        constat = f"{line} / {shift_fr} le {date_str} — OEE {oee_val:.1f}%"
        cause_desc = CAUSE_MAP.get(cause, cause)
        recommandation = ACTION_MAP.get(cause, "Analyser la cause racine et définir un plan d'action correctif.")
        responsable = RESPONSABLE_MAP.get(cause, "Direction Production")

        rows.append({
            "Constat": constat,
            "Cause": cause_desc[:80],
            "Action Recommandée": recommandation[:100],
            f"Gain Estimé ({curr_sym})": round(extra, 0),
            "Responsable": responsable,
            "Échéance": (datetime.now() + timedelta(days=30)).date(),
            "Statut": "À faire",
            "Commentaire": "",
        })

    return pd.DataFrame(rows)


# Initialiser le plan d'action UNE SEULE FOIS par session
if "action_plan_df" not in st.session_state:
    st.session_state["action_plan_df"] = _build_action_plan_df(anomalies, normal_hc)
    st.session_state["action_plan_initialized"] = True

action_df = st.session_state["action_plan_df"]

if action_df.empty:
    render_empty_state(
        icon_name="clipboard_list",
        title="Aucune action en attente",
        description="Aucune anomalie détectée — le plan d'action est vide. Les actions seront générées automatiquement lors de la détection d'anomalies.",
        c=c,
    )
else:
    # Résumé des statuts
    status_counts = action_df["Statut"].value_counts().to_dict()
    status_pills_html = " ".join([
        status_dot(
            c["warning"] if s == "À faire" else (c["info"] if s == "En cours" else (c["success"] if s == "Fait" else c["danger"])),
            f"{s} : {count}"
        )
        for s, count in status_counts.items()
    ])
    st.markdown(f"""
    <div style="margin-bottom:0.8rem; display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
        {status_pills_html}
    </div>
    """, unsafe_allow_html=True)

    # Éditeur de données
    edited_df = st.data_editor(
        action_df,
        use_container_width=True,
        hide_index=True,
        key="action_plan_editor",
        disabled=["Constat", "Cause", "Action Recommandée", f"Gain Estimé ({curr_sym})"],
        column_config={
            "Constat": st.column_config.TextColumn("Constat", width="large"),
            "Cause": st.column_config.TextColumn("Cause", width="medium"),
            "Action Recommandée": st.column_config.TextColumn("Action", width="large"),
            f"Gain Estimé ({curr_sym})": st.column_config.NumberColumn(f"Gain ({curr_sym})", format="%.0f"),
            "Responsable": st.column_config.TextColumn("Responsable", width="small"),
            "Échéance": st.column_config.DateColumn("Échéance", format="DD/MM/YYYY"),
            "Statut": st.column_config.SelectboxColumn(
                "Statut", options=["À faire", "En cours", "Fait", "Annulé"], width="small"
            ),
            "Commentaire": st.column_config.TextColumn("Commentaire", width="medium"),
        },
    )

    # Persister les modifications
    st.session_state["action_plan_df"] = edited_df

    # Boutons : export + régénération
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        csv_data = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Télécharger le plan d'action (CSV)",
            data=csv_data,
            file_name=f"SmartAudit_Plan_Action_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_action_plan",
            use_container_width=True,
        )
    with btn_col2:
        if st.button("Régénérer depuis les anomalies actuelles", key="btn_regen_action", use_container_width=True):
            st.session_state["action_plan_df"] = _build_action_plan_df(anomalies, normal_hc)
            st.warning("Plan d'action régénéré — les modifications manuelles précédentes ont été réinitialisées.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# PAP Cross-Reference Link
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
            border-left:4px solid {c['primary']}; border-radius:12px;
            padding:1.2rem 1.5rem; margin-top:1.5rem;">
    <p style="color:{c['text_primary']}; font-weight:700; font-size:0.95rem; margin-bottom:0.4rem;">
        Plan d'Actions Prioritaires (PAP)
    </p>
    <p style="color:{c['text_secondary']}; font-size:0.85rem; line-height:1.6; margin:0;">
        Les anomalies détectées sur cette page alimentent directement le
        <strong style="color:{c['text_primary']};">Plan d'Actions Prioritaires (PAP)</strong>
        disponible dans la page
        <strong style="color:{c['primary']};">Analyse des Coûts Cachés</strong>
        (onglet <em>Instruments ISEOR → PAP</em>).
        Chaque dysfonctionnement y est associé à une action corrective, un responsable et une estimation du ROI.
    </p>
</div>
""", unsafe_allow_html=True)

# Footer
render_footer(c)
