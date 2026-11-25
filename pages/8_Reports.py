"""
SmartAudit — Generation de Rapports PDF et Excel.
Includes session_state persistence for download buttons and period-filtered exports.
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
import pandas as pd
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, format_currency,
                                get_theme_css, get_colors)
from utils.report_generator import generate_daily_report, generate_monthly_report, generate_excel_report
from utils.ui_helpers import render_page_header, render_footer
from utils.icons import icon, inline_icon

# -- Theme CSS --
st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()
df_all = load_data(st.session_state.get("app_currency", "MAD"))

render_page_header("file_text", "Génération de Rapports",
                   "Rapports Flash Journaliers et Mensuels — Format PDF et Excel", c)

# ── Session state initialization ──
for key in ["pdf_bytes", "pdf_filename", "excel_bytes", "excel_filename"]:
    if key not in st.session_state:
        st.session_state[key] = None

df_report = pd.DataFrame()  # Initialize early to prevent undefined variable risk

# ── Report type selection ──
report_type = st.radio("Type de Rapport", ["Rapport Journalier", "Rapport Mensuel"],
                       horizontal=True, key="report_type_radio")

if report_type == "Rapport Journalier":
    available_dates = sorted(df_all["Date"].dt.date.unique())
    selected_date = st.selectbox("Date du Rapport", available_dates,
                                  index=len(available_dates) - 1, key="daily_date")

    # Filter data by the REPORT page's own selector
    df_report = df_all[df_all["Date"].dt.date == selected_date].copy()
    period_label = str(selected_date)

    if df_report.empty:
        st.warning(f"Aucune donnée pour le {selected_date}")
    else:
        st.success(f"{len(df_report)} équipes trouvées pour le {selected_date}")

        # Preview
        with st.expander("Aperçu des données", expanded=False):
            preview = df_report[["Date", "Production_Line", "Shift_Type", "OEE_Pct",
                                 "Total_Hidden_Cost", "Availability_Pct", "Quality_Pct"]].copy()
            SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
            preview["Shift_Type"] = preview["Shift_Type"].map(SHIFT_MAP_FR).fillna(preview["Shift_Type"])
            preview["Total_Hidden_Cost"] = preview["Total_Hidden_Cost"].apply(lambda x: format_currency(x))
            preview.columns = ["Date", "Ligne", "Équipe", "OEE %", "Coûts Cachés", "Disponibilité %", "Qualité %"]
            st.dataframe(preview, use_container_width=True, hide_index=True)

    st.markdown("---")

    # PDF Generation
    p1, p2 = st.columns(2)
    with p1:
        if st.button("Générer Rapport PDF", key="btn_gen_pdf", type="primary",
                     use_container_width=True, disabled=df_report.empty if 'df_report' in dir() else True):
            with st.spinner("Génération du PDF en cours..."):
                try:
                    pdf_bytes = generate_daily_report(df_report, period_label)
                    st.session_state["pdf_bytes"] = bytes(pdf_bytes) if not isinstance(pdf_bytes, bytes) else pdf_bytes
                    st.session_state["pdf_filename"] = f"SmartAudit_Flash_{period_label}.pdf"
                    st.success("PDF généré avec succès !")
                except Exception as e:
                    st.error(f"Erreur PDF : {e}")

    with p2:
        if st.button("Générer Rapport Excel", key="btn_gen_excel", type="primary",
                     use_container_width=True, disabled=df_report.empty if 'df_report' in dir() else True):
            with st.spinner("Génération de l'Excel en cours..."):
                try:
                    excel_bytes = generate_excel_report(df_report, period_label)
                    st.session_state["excel_bytes"] = bytes(excel_bytes) if not isinstance(excel_bytes, bytes) else excel_bytes
                    st.session_state["excel_filename"] = f"SmartAudit_Data_{period_label}.xlsx"
                    st.success("Excel généré avec succès !")
                except Exception as e:
                    st.error(f"Erreur Excel : {e}")

else:
    # Monthly report
    mois_options = {
        "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6,
        "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12
    }
    available_months = sorted(df_all["Date"].dt.month.unique())
    month_names = [k for k, v in mois_options.items() if v in available_months]

    selected_month_name = st.selectbox("Mois du Rapport", month_names,
                                        index=len(month_names) - 1, key="monthly_month")
    selected_month = mois_options[selected_month_name]

    # Filter by REPORT page selector
    df_report = df_all[df_all["Date"].dt.month == selected_month].copy()
    data_year = df_all["Date"].dt.year.max() if not df_all.empty else 2025
    period_label = f"{data_year}-{selected_month:02d}_{selected_month_name}"

    if df_report.empty:
        st.warning(f"Aucune donnée pour {selected_month_name}")
    else:
        st.success(f"{len(df_report)} équipes trouvées pour {selected_month_name} {data_year}")

    st.markdown("---")

    p1, p2 = st.columns(2)
    with p1:
        if st.button("Générer Rapport Mensuel PDF", key="btn_gen_monthly_pdf", type="primary",
                     use_container_width=True, disabled=df_report.empty):
            with st.spinner("Génération du rapport mensuel..."):
                try:
                    pdf_bytes = generate_monthly_report(df_report, selected_month_name)
                    st.session_state["pdf_bytes"] = bytes(pdf_bytes) if not isinstance(pdf_bytes, bytes) else pdf_bytes
                    st.session_state["pdf_filename"] = f"SmartAudit_Mensuel_{period_label}.pdf"
                    st.success("PDF mensuel généré !")
                except Exception as e:
                    st.error(f"Erreur PDF : {e}")

    with p2:
        if st.button("Générer Excel Mensuel", key="btn_gen_monthly_excel", type="primary",
                     use_container_width=True, disabled=df_report.empty):
            with st.spinner("Génération de l'Excel..."):
                try:
                    excel_bytes = generate_excel_report(df_report, period_label)
                    st.session_state["excel_bytes"] = bytes(excel_bytes) if not isinstance(excel_bytes, bytes) else excel_bytes
                    st.session_state["excel_filename"] = f"SmartAudit_Data_{period_label}.xlsx"
                    st.success("Excel généré !")
                except Exception as e:
                    st.error(f"Erreur Excel : {e}")

# ── Download buttons ALWAYS visible ──
st.markdown("---")
dl1, dl2 = st.columns(2)

with dl1:
    if st.session_state["pdf_bytes"] is not None:
        st.download_button(
            label="Télécharger PDF",
            data=st.session_state["pdf_bytes"],
            file_name=st.session_state["pdf_filename"],
            mime="application/pdf",
            key="btn_dl_pdf",
            use_container_width=True,
        )

with dl2:
    if st.session_state["excel_bytes"] is not None:
        st.download_button(
            label="Télécharger Excel",
            data=st.session_state["excel_bytes"],
            file_name=st.session_state["excel_filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_dl_excel",
            use_container_width=True,
        )

# Footer
render_footer(c)
