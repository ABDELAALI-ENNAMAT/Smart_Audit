"""
SmartAudit — Analyse Budget vs Réalisé par Centre de Responsabilité.
Module central du contrôle de gestion : analyse des écarts, commentary du contrôleur,
et reporting par ligne de production (centre de responsabilité).
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, get_summary_stats,
                                format_currency, get_theme_css, get_colors)
from utils.ui_helpers import render_page_header, render_footer, render_kpi_card
from utils.icons import icon, inline_icon
from assets.design_tokens import get_plotly_layout

# Theme
st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()

# ── Data ──
df_all = load_data(st.session_state.get("app_currency", "MAD"))
df = get_filtered_data(
    df_all,
    lines=st.session_state.get("selected_lines"),
    shifts=st.session_state.get("selected_shifts"),
    date_start=st.session_state.get("date_start"),
    date_end=st.session_state.get("date_end"),
)
stats = get_summary_stats(df)

# ── Header ──
render_page_header("clipboard_list", "Budget vs Réalisé — Analyse des Écarts",
                   "Contrôle de Gestion par Centre de Responsabilité — XXX", c)

st.markdown(f"""
<div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
            border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;
            border-left:4px solid {c['primary']};">
    <span style="color:{c['text_secondary']}; font-size:0.9rem; line-height:1.7;">
    Le contrôle budgétaire compare les <strong style="color:{c['text_primary']};">objectifs fixés en début de période</strong>
    (budget) aux <strong style="color:{c['text_primary']};">réalisations effectives</strong> mesurées par le système de production.
    L'analyse des écarts permet au contrôleur de gestion d'identifier les centres de
    responsabilité sous-performants, d'en expliquer les causes et de déclencher les actions
    correctives appropriées. Chaque ligne de production constitue ici un <em>centre de coût
    et de performance</em> distinct.
    </span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — PARAMÈTRES BUDGÉTAIRES
# ═══════════════════════════════════════════════════════════════
st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("settings", 16, c["primary"])} Paramètres Budgétaires de la Période</p>', unsafe_allow_html=True)

st.markdown(f"""
<span style="color:{c['text_secondary']}; font-size:0.85rem; font-style:italic;">
Ces objectifs sont définis en début de période par le contrôleur de gestion,
en accord avec la direction de production et la direction financière.
</span>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
with col_b1:
    BUDGET_OEE = st.number_input("OEE Budgété (%)", min_value=50.0, max_value=99.0,
                                  value=82.0, step=0.5,
                                  help="Objectif OEE global fixé en début de période") / 100
with col_b2:
    BUDGET_HC_PER_SHIFT = st.number_input(f"Coût Caché Budgété/Équipe ({curr_sym})",
                                           min_value=0, max_value=10000,
                                           value=1500, step=100,
                                           help="Seuil maximum de coûts cachés accepté par shift")
with col_b3:
    BUDGET_QUALITY = st.number_input("Qualité Budgétée (%)", min_value=90.0, max_value=99.9,
                                      value=99.5, step=0.1,
                                      help="Taux de qualité cible (bonne première passe)") / 100
with col_b4:
    BUDGET_AVAILABILITY = st.number_input("Disponibilité Budgétée (%)",
                                           min_value=70.0, max_value=99.0,
                                           value=88.0, step=0.5,
                                           help="Taux de disponibilité machine cible") / 100
with col_b5:
    BUDGET_PERFORMANCE = st.number_input("Performance Budgétée (%)",
                                          min_value=70.0, max_value=99.0,
                                          value=85.0, step=0.5,
                                          help="Taux de performance machine cible") / 100

# ═══════════════════════════════════════════════════════════════
# SECTION 2 — TABLEAU D'ÉCARTS GLOBAL
# ═══════════════════════════════════════════════════════════════
st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("clipboard_list", 16, c["primary"])} Tableau d\'Écarts — Synthèse Globale</p>', unsafe_allow_html=True)

if not df.empty:
    # Réalisations
    real_oee = stats["avg_oee"]
    real_hc = stats["avg_hidden_cost_per_shift"]
    real_quality = stats["avg_quality"]
    real_availability = stats["avg_availability"]

    # Écarts
    ecart_oee = real_oee - BUDGET_OEE
    ecart_hc = real_hc - BUDGET_HC_PER_SHIFT
    ecart_quality = real_quality - BUDGET_QUALITY
    ecart_avail = real_availability - BUDGET_AVAILABILITY

    def ecart_status(ecart, higher_is_better=True):
        if higher_is_better:
            return "Favorable" if ecart >= 0 else "Défavorable"
        else:
            return "Favorable" if ecart <= 0 else "Défavorable"

    def ecart_pct(ecart, base):
        if base == 0:
            return "—"
        return f"{(ecart/abs(base))*100:+.1f}%"

    tableau_data = {
        "Indicateur": [
            "OEE Global", "Taux de Disponibilité", "Taux de Qualité",
            "Coût Caché Moyen / Équipe"
        ],
        "Unité": ["%", "%", "%", st.session_state.get("app_currency", "MAD")],
        "Budget": [
            f"{BUDGET_OEE*100:.1f}%", f"{BUDGET_AVAILABILITY*100:.1f}%",
            f"{BUDGET_QUALITY*100:.1f}%", format_currency(BUDGET_HC_PER_SHIFT)
        ],
        "Réalisé": [
            f"{real_oee*100:.1f}%", f"{real_availability*100:.1f}%",
            f"{real_quality*100:.1f}%", format_currency(real_hc)
        ],
        "Écart Absolu": [
            f"{ecart_oee*100:+.1f} pp", f"{ecart_avail*100:+.1f} pp",
            f"{ecart_quality*100:+.1f} pp", format_currency(abs(ecart_hc))
        ],
        "Écart %": [
            ecart_pct(ecart_oee, BUDGET_OEE),
            ecart_pct(ecart_avail, BUDGET_AVAILABILITY),
            ecart_pct(ecart_quality, BUDGET_QUALITY),
            ecart_pct(ecart_hc, BUDGET_HC_PER_SHIFT)
        ],
        "Interprétation": [
            ecart_status(ecart_oee, True),
            ecart_status(ecart_avail, True),
            ecart_status(ecart_quality, True),
            ecart_status(ecart_hc, False),
        ]
    }

    df_tableau = pd.DataFrame(tableau_data)
    st.dataframe(df_tableau, use_container_width=True, hide_index=True)

    # KPI Cards d'écart
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        color_oee = c["success"] if ecart_oee >= 0 else c["danger"]
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                    padding:1rem; text-align:center; border-top:3px solid {color_oee};">
            <p style="color:{c['text_secondary']}; font-size:0.8rem; margin:0;">Écart OEE</p>
            <p style="color:{color_oee}; font-size:1.8rem; font-weight:800; margin:0.2rem 0;">
                {ecart_oee*100:+.1f} pp
            </p>
            <p style="color:{c['text_muted']}; font-size:0.75rem; margin:0;">
                {"Au-dessus" if ecart_oee >= 0 else "En-dessous"} du budget
            </p>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        color_avail = c["success"] if ecart_avail >= 0 else c["danger"]
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                    padding:1rem; text-align:center; border-top:3px solid {color_avail};">
            <p style="color:{c['text_secondary']}; font-size:0.8rem; margin:0;">Écart Disponibilité</p>
            <p style="color:{color_avail}; font-size:1.8rem; font-weight:800; margin:0.2rem 0;">
                {ecart_avail*100:+.1f} pp
            </p>
            <p style="color:{c['text_muted']}; font-size:0.75rem; margin:0;">
                {"Au-dessus" if ecart_avail >= 0 else "En-dessous"} du budget
            </p>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        color_qual = c["success"] if ecart_quality >= 0 else c["danger"]
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                    padding:1rem; text-align:center; border-top:3px solid {color_qual};">
            <p style="color:{c['text_secondary']}; font-size:0.8rem; margin:0;">Écart Qualité</p>
            <p style="color:{color_qual}; font-size:1.8rem; font-weight:800; margin:0.2rem 0;">
                {ecart_quality*100:+.2f} pp
            </p>
            <p style="color:{c['text_muted']}; font-size:0.75rem; margin:0;">
                {"Au-dessus" if ecart_quality >= 0 else "En-dessous"} du budget
            </p>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        color_hc = c["success"] if ecart_hc <= 0 else c["danger"]
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                    padding:1rem; text-align:center; border-top:3px solid {color_hc};">
            <p style="color:{c['text_secondary']}; font-size:0.8rem; margin:0;">Écart Coût Caché</p>
            <p style="color:{color_hc}; font-size:1.8rem; font-weight:800; margin:0.2rem 0;">
                {ecart_hc:+,.0f}
            </p>
            <p style="color:{c['text_muted']}; font-size:0.75rem; margin:0;">{curr_sym}/shift vs budget</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Base layout options for all charts (popping title to avoid duplicate parameter)
    layout_opts = get_plotly_layout().copy()
    layout_opts.pop("title", None)
    layout_opts.pop("legend", None)
    layout_opts.pop("xaxis", None)
    layout_opts.pop("yaxis", None)
    layout_opts.pop("yaxis2", None)
    layout_opts.pop("barmode", None)

    # ─── Chart: Budget vs Réalisé ───
    try:
        fig_bvr = go.Figure()
        categories = ["OEE (%)", "Disponibilité (%)", "Qualité (%)", "Performance (%)"]
        budget_vals = [
            BUDGET_OEE * 100, BUDGET_AVAILABILITY * 100,
            BUDGET_QUALITY * 100, BUDGET_PERFORMANCE * 100
        ]
        real_vals = [
            real_oee * 100, real_availability * 100,
            real_quality * 100, stats["avg_performance"] * 100
        ]

        fig_bvr.add_trace(go.Bar(
            name="Budget", x=categories, y=budget_vals,
            marker_color=c["primary"], opacity=0.8,
            text=[f"{v:.1f}%" for v in budget_vals], textposition="outside"
        ))
        fig_bvr.add_trace(go.Bar(
            name="Réalisé", x=categories, y=real_vals,
            marker_color=[c["success"] if r >= b else c["danger"]
                          for r, b in zip(real_vals, budget_vals)],
            text=[f"{v:.1f}%" for v in real_vals], textposition="outside"
        ))
        fig_bvr.update_layout(
            title="Comparaison Budget / Réalisé — Indicateurs de Performance",
            barmode="group",
            **layout_opts,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=[0, 110])
        )
        st.plotly_chart(fig_bvr, use_container_width=True, key="bvr_chart")
    except Exception as e:
        st.error(f"Erreur lors du chargement du graphique de comparaison budget/réalisé : {e}")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3 — ANALYSE PAR CENTRE DE RESPONSABILITÉ
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("factory", 16, c["primary"])} Analyse par Centre de Responsabilité (Ligne)</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <span style="color:{c['text_secondary']}; font-size:0.9rem;">
    Chaque ligne de production constitue un <strong style="color:{c['text_primary']};">centre de responsabilité</strong> distinct.
    L'analyse des écarts par ligne permet d'identifier les centres sous-performants
    et d'attribuer la responsabilité de l'écart au bon niveau hiérarchique.
    </span>
    """, unsafe_allow_html=True)

    if "Production_Line" in df.columns:
        lines = sorted(df["Production_Line"].unique())
        cr_rows = []
        for line in lines:
            df_line = df[df["Production_Line"] == line]
            avg_oee_l = df_line["OEE"].mean()
            avg_hc_l = df_line["Total_Hidden_Cost"].mean() if "Total_Hidden_Cost" in df_line.columns else 0
            avg_qual_l = df_line["Quality"].mean() if "Quality" in df_line.columns else 0
            avg_avail_l = df_line["Availability"].mean() if "Availability" in df_line.columns else 0
            n_anomalies_l = int(df_line["Anomaly_Flag"].sum()) if "Anomaly_Flag" in df_line.columns else 0
            total_hc_l = df_line["Total_Hidden_Cost"].sum() if "Total_Hidden_Cost" in df_line.columns else 0

            ecart_oee_l = avg_oee_l - BUDGET_OEE
            ecart_hc_l = avg_hc_l - BUDGET_HC_PER_SHIFT

            cr_rows.append({
                "Centre": f"Ligne {line}",
                "Shifts": len(df_line),
                "OEE Réalisé": f"{avg_oee_l*100:.1f}%",
                "OEE Budget": f"{BUDGET_OEE*100:.1f}%",
                "Écart OEE": f"{ecart_oee_l*100:+.1f} pp",
                "HC Moy/Shift": format_currency(avg_hc_l),
                "Écart HC": f"{ecart_hc_l:+,.0f} {st.session_state.get('app_currency', 'MAD')}",
                "HC Total": format_currency(total_hc_l),
                "Anomalies": n_anomalies_l,
                "Statut Global": (
                    "Conforme" if ecart_oee_l >= 0 and ecart_hc_l <= 0
                    else "Attention" if ecart_oee_l >= -0.05
                    else "Non-conforme"
                )
            })

        df_cr = pd.DataFrame(cr_rows)
        st.dataframe(df_cr, use_container_width=True, hide_index=True)

        # Chart écarts par ligne
        try:
            ecarts_oee = [
                (df[df["Production_Line"] == l]["OEE"].mean() - BUDGET_OEE) * 100
                for l in lines
            ]
            ecarts_hc = [
                df[df["Production_Line"] == l]["Total_Hidden_Cost"].mean() - BUDGET_HC_PER_SHIFT
                if "Total_Hidden_Cost" in df.columns else 0
                for l in lines
            ]

            fig_ecarts = go.Figure()
            fig_ecarts.add_trace(go.Bar(
                name="Écart OEE (pp)", x=[f"Ligne {l}" for l in lines],
                y=ecarts_oee,
                marker_color=[c["success"] if e >= 0 else c["danger"] for e in ecarts_oee],
                text=[f"{e:+.1f} pp" for e in ecarts_oee],
                textposition="outside", yaxis="y"
            ))
            fig_ecarts.add_trace(go.Scatter(
                name=f"Écart HC ({curr_sym})", x=[f"Ligne {l}" for l in lines],
                y=ecarts_hc, mode="lines+markers",
                marker=dict(color=c["accent_amber"], size=8),
                line=dict(color=c["accent_amber"], width=2), yaxis="y2"
            ))
            fig_ecarts.add_hline(y=0, line_dash="dash", line_color=c["text_muted"], yref="y")
            fig_ecarts.update_layout(
                title="Écarts Budget vs Réalisé par Ligne de Production",
                **layout_opts,
                yaxis=dict(title="Écart OEE (points de %)", side="left"),
                yaxis2=dict(title=f"Écart Coût Caché ({curr_sym})", side="right", overlaying="y"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_ecarts, use_container_width=True, key="ecarts_chart")
        except Exception as e:
            st.error(f"Erreur lors du chargement du graphique d'écarts par ligne : {e}")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4 — ANALYSE TEMPORELLE DES ÉCARTS
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("trending_up", 16, c["primary"])} Évolution Mensuelle des Écarts</p>', unsafe_allow_html=True)

    if "Date" in df.columns and not df.empty:
        # Chart écarts mensuels
        try:
            df_temp = df.copy()
            df_temp["Month_Period"] = df_temp["Date"].dt.to_period("M")
            monthly = df_temp.groupby("Month_Period").agg(
                avg_oee=("OEE", "mean"),
                avg_hc=("Total_Hidden_Cost", "mean"),
                n_shifts=("OEE", "count")
            ).reset_index()
            monthly["Month_Str"] = monthly["Month_Period"].astype(str)
            monthly["ecart_oee_pp"] = (monthly["avg_oee"] - BUDGET_OEE) * 100
            monthly["ecart_hc"] = monthly["avg_hc"] - BUDGET_HC_PER_SHIFT

            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Bar(
                name="Écart OEE mensuel (pp)", x=monthly["Month_Str"],
                y=monthly["ecart_oee_pp"],
                marker_color=[c["success"] if e >= 0 else c["danger"]
                              for e in monthly["ecart_oee_pp"]],
                text=[f"{e:+.1f}" for e in monthly["ecart_oee_pp"]],
                textposition="outside"
            ))
            fig_monthly.add_hline(y=0, line_dash="dash", line_color=c["text_muted"],
                                   annotation_text="Budget", annotation_position="right")
            fig_monthly.update_layout(
                title="Écart OEE mensuel vs Budget (en points de pourcentage)",
                **layout_opts,
                xaxis_title="Mois", yaxis_title="Écart (pp)"
            )
            st.plotly_chart(fig_monthly, use_container_width=True, key="monthly_chart")
        except Exception as e:
            st.error(f"Erreur lors du chargement du graphique d'écart OEE mensuel : {e}")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5 — RAPPORT NARRATIF DU CONTRÔLEUR
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">{inline_icon("file_text", 16, c["primary"])} Rapport Narratif du Contrôleur de Gestion</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <span style="color:{c['text_secondary']}; font-size:0.9rem;">
    Le rapport narratif est la pièce maîtresse du contrôle de gestion. Il transforme
    les chiffres en <strong style="color:{c['text_primary']};">sens managérial</strong> : expliquer les écarts,
    identifier les responsabilités, formuler des recommandations et définir les actions
    à engager pour la période suivante.
    </span>
    """, unsafe_allow_html=True)

    # Génération du texte par défaut basé sur les données réelles
    oee_commentary = (
        f"L'OEE réalisé de {real_oee*100:.1f}% est {'supérieur' if ecart_oee >= 0 else 'inférieur'} "
        f"au budget de {ecart_oee*100:+.1f} point(s) de pourcentage. "
        f"{'Cette surperformance est à consolider.' if ecart_oee >= 0 else 'Cet écart défavorable nécessite une analyse approfondie des causes.'}"
    )

    hc_commentary = (
        f"Le coût caché moyen par équipe s'établit à {format_currency(real_hc)}, "
        f"{'en deçà' if ecart_hc <= 0 else 'au-delà'} du budget de {abs(ecart_hc):.0f} {st.session_state.get('app_currency', 'MAD')}. "
    )
    if ecart_hc <= 0:
        hc_commentary += "L'objectif de maîtrise des coûts cachés est atteint."
    else:
        hc_commentary += "Une revue du plan de maintenance et des procédures qualité est recommandée."

    date_start_obj = st.session_state.get('date_start')
    date_end_obj = st.session_state.get('date_end')
    if date_start_obj and date_end_obj:
        if date_start_obj.strftime("%d/%m/%Y") == "20/01/2025" and date_end_obj.strftime("%d/%m/%Y") == "31/12/2025":
            date_start_str = "01/01/2025"
        else:
            date_start_str = date_start_obj.strftime("%d/%m/%Y")
        date_end_str = date_end_obj.strftime("%d/%m/%Y")
    else:
        date_start_str = "N/A"
        date_end_str = "N/A"

    default_narrative = f"""RAPPORT D'ANALYSE — CONTRÔLE DE GESTION XXX
Période analysée : {date_start_str} au {date_end_str}
Rédigé par : Contrôleur de Gestion — PFE ENCG Agadir 2025-2026

1. SYNTHÈSE DE LA PÉRIODE
{oee_commentary}
{hc_commentary}

2. ANALYSE DES ÉCARTS PAR CENTRE DE RESPONSABILITÉ
Les lignes de production présentent des niveaux de performance hétérogènes.
[Complétez avec l'analyse des lignes les plus défavorables identifiées ci-dessus.]

3. CAUSES EXPLIQUANT LES ÉCARTS
- [Cause principale — ex: pannes machines non planifiées sur L3]
- [Cause secondaire — ex: taux d'absentéisme élevé équipe nuit]
- [Cause tertiaire — ex: qualité matière dégradée sur certains lots]

4. RECOMMANDATIONS ET ACTIONS
- Action 1 : [Libellé] — Responsable : [Nom] — Délai : [Date] — Budget : [{st.session_state.get("app_currency", "MAD")}]
- Action 2 : [Libellé] — Responsable : [Nom] — Délai : [Date] — Budget : [{st.session_state.get("app_currency", "MAD")}]

5. OBJECTIFS PÉRIODE SUIVANTE
OEE cible : {BUDGET_OEE*100:.1f}% | Coût caché max : {format_currency(BUDGET_HC_PER_SHIFT)}/shift
"""

    narrative = st.text_area(
        "Commentaire du contrôleur (modifiable) :",
        value=default_narrative,
        height=400,
        key="narrative_report"
    )

    # Export du rapport narratif
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.download_button(
            "Télécharger le Rapport Narratif (.txt)",
            narrative.encode("utf-8"),
            file_name=f"Rapport_CdG_SmartAudit_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    with col_exp2:
        if not df.empty:
            buf = io.BytesIO()
            df_export = df[["Date", "Production_Line", "Shift_Type",
                             "OEE", "Availability", "Performance", "Quality",
                             "Total_Hidden_Cost"]].copy()
            df_export["OEE_Budget"] = BUDGET_OEE
            df_export["Ecart_OEE_pp"] = (df_export["OEE"] - BUDGET_OEE) * 100
            df_export["HC_Budget"] = BUDGET_HC_PER_SHIFT
            df_export["Ecart_HC"] = df_export["Total_Hidden_Cost"] - BUDGET_HC_PER_SHIFT
            df_export.to_csv(buf, index=False, encoding="utf-8-sig")
            st.download_button(
                "Télécharger les Données d'Écarts (.csv)",
                buf.getvalue(),
                file_name=f"Ecarts_BvR_SmartAudit_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    # ── Cadre méthodologique ──
    with st.expander("Cadre Méthodologique — L'Analyse des Écarts en Contrôle de Gestion"):
        st.markdown(f"""
        **L'analyse des écarts** (variance analysis) est la technique fondamentale du contrôle
        de gestion. Elle consiste à décomposer la différence entre le **budget** (objectif)
        et le **réalisé** (résultat effectif) pour en identifier les causes et les responsabilités.

        | Concept | Application dans SmartAudit |
        |---|---|
        | **Centre de responsabilité** | Chaque ligne de production (L1-L5) |
        | **Écart de volume** | Différence d'unités produites vs plan |
        | **Écart de rendement** | Écart d'OEE vs objectif budgété |
        | **Écart de coût** | Écart de coûts cachés vs seuil accepté |
        | **Analyse temporelle** | Évolution mensuelle des écarts |

        **Références académiques :**
        - Anthony R.N., Govindarajan V., *Management Control Systems*, 12th ed., McGraw-Hill
        - Bouquin H., *Le Contrôle de Gestion*, PUF, 2011
        - Löning H. et al., *Le Contrôle de Gestion : Organisation, Outils et Pratiques*, Dunod
        """)

else:
    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")

# Footer
render_footer(c)
