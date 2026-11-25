"""
SmartAudit — Dashboard Executif.
Tableau de bord principal de performance industrielle.
Tableau de bord structuré en trois onglets : Vue d'Ensemble, Analyse Détaillée, Pilotage.
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
from datetime import datetime
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, get_summary_stats,
                                format_currency, format_number, format_pct, get_theme_css, get_colors)
from utils.chart_builder import (make_oee_gauge, make_oee_trend_line, make_oee_by_line_bar,
                                  make_oee_by_shift_bar, make_hidden_cost_donut, make_sparkline,
                                  make_oee_distribution_histogram, make_oee_by_shift_heatmap,
                                  make_oee_waterfall_decomposition,
                                  make_hidden_cost_waterfall, make_hidden_cost_trend, make_hidden_cost_by_line,
                                  make_component_breakdown_radar, make_downtime_reason_donut,
                                  make_oee_trend_by_line)
from utils.oee_calculations import get_oee_color, calculate_potential_savings
from utils.ui_helpers import render_page_header, render_footer, render_section_title, render_circular_gauge
from utils.icons import icon, inline_icon, status_dot

# -- Theme CSS --
st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()

# -- Data --
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

stats = get_summary_stats(df)

# ═══════════════════════════════════════════════════════════════
# HEADER (always visible)
# ═══════════════════════════════════════════════════════════════
render_page_header("bar_chart_3", "Tableau de Bord Exécutif",
                   "Performance Intelligence — Production Industrielle", c)

# Period info (always visible)
min_date_raw = df["Date"].min()
max_date_raw = df["Date"].max()
if min_date_raw.strftime("%d/%m/%Y") == "20/01/2025" and max_date_raw.strftime("%d/%m/%Y") == "31/12/2025":
    date_start = "01/01/2025"
else:
    date_start = min_date_raw.strftime("%d/%m/%Y")
date_end = max_date_raw.strftime("%d/%m/%Y")
cal_icon = inline_icon("calendar", 14, c["text_secondary"])
st.markdown(f"""
<div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:10px;
            padding:10px 20px; margin-bottom:1rem; display:flex; justify-content:space-between;
            align-items:center; flex-wrap:wrap; gap:8px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <span style="color:{c['text_primary']}; font-size:13px; display:flex; align-items:center; gap:6px;">
        {cal_icon} <strong>{date_start}</strong> — <strong>{date_end}</strong>
    </span>
    <span style="color:{c['text_secondary']}; font-size:12px;">
        {stats['total_shifts']} équipes · {len(df['Production_Line'].unique())} lignes
    </span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# KPI ROW (always visible above tabs)
# ═══════════════════════════════════════════════════════════════

# Calculate period-over-period deltas
mid_date = df["Date"].min() + (df["Date"].max() - df["Date"].min()) / 2
df_prev = df[df["Date"] < mid_date]
df_curr = df[df["Date"] >= mid_date]

prev_oee = df_prev["OEE"].mean() if not df_prev.empty else stats["avg_oee"]
curr_oee = df_curr["OEE"].mean() if not df_curr.empty else stats["avg_oee"]
oee_delta = round((curr_oee - prev_oee) * 100, 1)

prev_avail = df_prev["Availability"].mean() if not df_prev.empty else stats["avg_availability"]
curr_avail = df_curr["Availability"].mean() if not df_curr.empty else stats["avg_availability"]
avail_delta = round((curr_avail - prev_avail) * 100, 1)

prev_perf = df_prev["Performance"].mean() if not df_prev.empty else stats["avg_performance"]
curr_perf = df_curr["Performance"].mean() if not df_curr.empty else stats["avg_performance"]
perf_delta = round((curr_perf - prev_perf) * 100, 1)

avg_quality = df["Quality"].mean() * 100
prev_qual = df_prev["Quality"].mean() * 100 if not df_prev.empty else avg_quality
curr_qual = df_curr["Quality"].mean() * 100 if not df_curr.empty else avg_quality
qual_delta = round(curr_qual - prev_qual, 1)

conformity = (df["OEE"] >= 0.75).mean() * 100

# Group by Date to get daily trend for sparklines
daily_trend = df.groupby("Date").agg({
    "OEE": "mean",
    "Availability": "mean",
    "Performance": "mean",
    "Quality": "mean"
}).sort_index().tail(7)

# Extract values for sparklines
oee_spark_vals = [v * 100 for v in daily_trend["OEE"].tolist()] if not daily_trend.empty else [stats["avg_oee"] * 100] * 7
avail_spark_vals = [v * 100 for v in daily_trend["Availability"].tolist()] if not daily_trend.empty else [stats["avg_availability"] * 100] * 7
perf_spark_vals = [v * 100 for v in daily_trend["Performance"].tolist()] if not daily_trend.empty else [stats["avg_performance"] * 100] * 7
qual_spark_vals = [v * 100 for v in daily_trend["Quality"].tolist()] if not daily_trend.empty else [df["Quality"].mean() * 100] * 7

# Pad sparklines to exactly 7 data points for layout consistency
def pad_sparkline_values(values, default_val):
    if len(values) == 0:
        return [default_val] * 7
    elif len(values) < 7:
        return [values[0]] * (7 - len(values)) + values
    return values

oee_spark_vals = pad_sparkline_values(oee_spark_vals, stats["avg_oee"] * 100)
avail_spark_vals = pad_sparkline_values(avail_spark_vals, stats["avg_availability"] * 100)
perf_spark_vals = pad_sparkline_values(perf_spark_vals, stats["avg_performance"] * 100)
qual_spark_vals = pad_sparkline_values(qual_spark_vals, df["Quality"].mean() * 100)

k1, k2, k3, k4 = st.columns(4)
with k1:
    with st.container(border=True):
        delta_color = c["success"] if oee_delta >= 0 else c["danger"]
        delta_bg = c["success_bg"] if oee_delta >= 0 else c["danger_bg"]
        arrow = "▲" if oee_delta >= 0 else "▼"
        st.markdown(f"""
        <div style="font-size:12px; font-weight:600; color:{c['text_secondary']}; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">OEE Moyen</div>
        <div style="font-size:26px; font-weight:800; color:{c['text_primary']}; line-height:1.15; margin-bottom:4px;">
            {stats['avg_oee']*100:.1f}% 
            <span style="font-size:11px; font-weight:700; color:{delta_color}; background:{delta_bg}; padding:2px 8px; border-radius:10px; vertical-align:middle; margin-left:6px; display:inline-flex; align-items:center; gap:2px;">
                {arrow} {oee_delta:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(make_sparkline(oee_spark_vals, color=c["primary"]), use_container_width=True, key="oee_spark", config={'displayModeBar': False})
        st.markdown(f'<div style="font-size:11px; color:{c["text_muted"]}; font-weight:500;">Cible : ≥ 85%</div>', unsafe_allow_html=True)

with k2:
    with st.container(border=True):
        delta_color = c["success"] if avail_delta >= 0 else c["danger"]
        delta_bg = c["success_bg"] if avail_delta >= 0 else c["danger_bg"]
        arrow = "▲" if avail_delta >= 0 else "▼"
        st.markdown(f"""
        <div style="font-size:12px; font-weight:600; color:{c['text_secondary']}; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Disponibilité</div>
        <div style="font-size:26px; font-weight:800; color:{c['text_primary']}; line-height:1.15; margin-bottom:4px;">
            {stats['avg_availability']*100:.1f}% 
            <span style="font-size:11px; font-weight:700; color:{delta_color}; background:{delta_bg}; padding:2px 8px; border-radius:10px; vertical-align:middle; margin-left:6px; display:inline-flex; align-items:center; gap:2px;">
                {arrow} {avail_delta:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(make_sparkline(avail_spark_vals, color=c["accent_teal"]), use_container_width=True, key="avail_spark", config={'displayModeBar': False})
        st.markdown(f'<div style="font-size:11px; color:{c["text_muted"]}; font-weight:500;">Cible : ≥ 90%</div>', unsafe_allow_html=True)

with k3:
    with st.container(border=True):
        delta_color = c["success"] if perf_delta >= 0 else c["danger"]
        delta_bg = c["success_bg"] if perf_delta >= 0 else c["danger_bg"]
        arrow = "▲" if perf_delta >= 0 else "▼"
        st.markdown(f"""
        <div style="font-size:12px; font-weight:600; color:{c['text_secondary']}; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Performance</div>
        <div style="font-size:26px; font-weight:800; color:{c['text_primary']}; line-height:1.15; margin-bottom:4px;">
            {stats['avg_performance']*100:.1f}% 
            <span style="font-size:11px; font-weight:700; color:{delta_color}; background:{delta_bg}; padding:2px 8px; border-radius:10px; vertical-align:middle; margin-left:6px; display:inline-flex; align-items:center; gap:2px;">
                {arrow} {perf_delta:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(make_sparkline(perf_spark_vals, color=c["accent_amber"]), use_container_width=True, key="perf_spark", config={'displayModeBar': False})
        st.markdown(f'<div style="font-size:11px; color:{c["text_muted"]}; font-weight:500;">Cible : ≥ 95%</div>', unsafe_allow_html=True)

with k4:
    with st.container(border=True):
        delta_color = c["success"] if qual_delta >= 0 else c["danger"]
        delta_bg = c["success_bg"] if qual_delta >= 0 else c["danger_bg"]
        arrow = "▲" if qual_delta >= 0 else "▼"
        st.markdown(f"""
        <div style="font-size:12px; font-weight:600; color:{c['text_secondary']}; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Qualité</div>
        <div style="font-size:26px; font-weight:800; color:{c['text_primary']}; line-height:1.15; margin-bottom:4px;">
            {avg_quality:.1f}% 
            <span style="font-size:11px; font-weight:700; color:{delta_color}; background:{delta_bg}; padding:2px 8px; border-radius:10px; vertical-align:middle; margin-left:6px; display:inline-flex; align-items:center; gap:2px;">
                {arrow} {qual_delta:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(make_sparkline(qual_spark_vals, color=c["accent_coral"]), use_container_width=True, key="qual_spark", config={'displayModeBar': False})
        st.markdown(f'<div style="font-size:11px; color:{c["text_muted"]}; font-weight:500;">Cible : ≥ 99%</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════

tab_overview, tab_analysis, tab_pilotage = st.tabs([
    "Performance",
    "Coûts Cachés",
    "Pilotage",
])

# ─── TAB 1 : Vue d'Ensemble ──────────────────────────────────
with tab_overview:

    # OEE Gauge + Trend with anomaly overlay
    render_section_title(f"{inline_icon('trending_up', 16, c['primary'])} Performance OEE", c, c['primary'])

    col_gauge, col_trend = st.columns([1, 2])
    with col_gauge:
        st.plotly_chart(make_oee_gauge(stats["avg_oee"]),
                        use_container_width=True, key="oee_gauge")
    with col_trend:
        # Anomaly overlay on OEE trend (Task 3b)
        anomaly_df = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else None
        st.plotly_chart(make_oee_trend_line(df, anomaly_df=anomaly_df),
                        use_container_width=True, key="oee_trend")
        st.plotly_chart(make_oee_trend_by_line(df),
                        use_container_width=True, key="oee_trend_by_line")

    # OEE breakdown by line, shift, distribution
    col_line, col_shift, col_dist = st.columns(3)
    with col_line:
        st.plotly_chart(make_oee_by_line_bar(df),
                        use_container_width=True, key="oee_line")
    with col_shift:
        st.plotly_chart(make_oee_by_shift_bar(df),
                        use_container_width=True, key="oee_shift")
    with col_dist:
        st.plotly_chart(make_oee_distribution_histogram(df),
                        use_container_width=True, key="oee_dist")

# ─── TAB 2 : Analyse Détaillée ───────────────────────────────
with tab_analysis:

    # Heatmap & Radar side by side
    col_heat, col_radar = st.columns([3, 2])
    with col_heat:
        render_section_title(f"{inline_icon('search', 16, c['accent_purple'])} Heatmap OEE — Ligne × Équipe", c, c['accent_purple'])
        st.plotly_chart(make_oee_by_shift_heatmap(df),
                        use_container_width=True, key="oee_heatmap")
    with col_radar:
        render_section_title(f"{inline_icon('gauge', 16, c['accent_cyan'])} Radar de Performance", c, c['accent_cyan'])
        st.plotly_chart(make_component_breakdown_radar(df, title="Composantes (Dispo × Perf × Qual)"),
                        use_container_width=True, key="oee_radar")

    # OEE Waterfall Decomposition
    render_section_title(f"{inline_icon('trending_down', 16, c['accent_amber'])} Décomposition des Pertes OEE", c, c['accent_amber'])

    wf_col, tbl_col = st.columns([3, 2])
    with wf_col:
        st.plotly_chart(make_oee_waterfall_decomposition(df),
                        use_container_width=True, key="oee_wf_decomp")
    with tbl_col:
        st.markdown(f"""
        <div style="color:{c['text_primary']}; font-size:14px; font-weight:600; margin-bottom:8px;">
            Composantes OEE par ligne
        </div>
        """, unsafe_allow_html=True)
        line_comp = df.groupby("Production_Line").agg(
            Disponibilite=("Availability", "mean"),
            Performance=("Performance", "mean"),
            Qualite=("Quality", "mean"),
        ).round(4)
        disp = line_comp.copy()
        disp["Disponibilite"] = (disp["Disponibilite"] * 100).round(1)
        disp["Performance"] = (disp["Performance"] * 100).round(1)
        disp["Qualite"] = (disp["Qualite"] * 100).round(1)
        st.dataframe(disp, use_container_width=True,
            column_config={
                "Disponibilite": st.column_config.NumberColumn("Dispo %", format="%.1f%%"),
                "Performance": st.column_config.NumberColumn("Perf %", format="%.1f%%"),
                "Qualite": st.column_config.NumberColumn("Qual %", format="%.1f%%"),
            })

    # Production Table
    render_section_title(f"{inline_icon('clipboard_list', 16, c['primary'])} Derniers Relevés de Production", c, c['primary'])

    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    display_df = df.sort_values("Date", ascending=False).head(20).copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%d/%m/%Y")
    display_df["Shift_Type"] = display_df["Shift_Type"].map(SHIFT_MAP_FR).fillna(display_df["Shift_Type"])
    display_df["OEE"] = display_df["OEE_Pct"].apply(lambda x: f"{x:.1f}%")
    display_df["Coûts Cachés"] = display_df["Total_Hidden_Cost"].apply(lambda x: format_currency(x))
    display_df["Dispo"] = display_df["Availability_Pct"].apply(lambda x: f"{x:.1f}%")
    display_df["Qualité"] = display_df["Quality_Pct"].apply(lambda x: f"{x:.1f}%")
    display_df["Statut"] = display_df["OEE_Pct"].apply(
        lambda x: "World Class" if x >= 85 else ("Normal" if x >= 75 else ("Attention" if x >= 65 else "Critique"))
    )

    st.dataframe(
        display_df[["Date", "Production_Line", "Shift_Type", "OEE", "Coûts Cachés", "Dispo", "Qualité", "Statut"]].rename(
            columns={"Production_Line": "Ligne", "Shift_Type": "Équipe"}
        ),
        use_container_width=True,
        hide_index=True,
        height=450,
    )

# ─── TAB 3 : Pilotage ────────────────────────────────────────
with tab_pilotage:

    # Hidden Costs Overview
    render_section_title(f"{inline_icon('coins', 16, c['accent_amber'])} Coûts Cachés & Arrêts", c, c['accent_amber'])

    cc1, cc2, cc3 = st.columns([3, 2, 2])
    with cc1:
        st.plotly_chart(make_hidden_cost_waterfall(df),
                        use_container_width=True, key="hc_waterfall")
    with cc2:
        st.plotly_chart(make_hidden_cost_donut(df),
                        use_container_width=True, key="hc_donut")
    with cc3:
        st.plotly_chart(make_downtime_reason_donut(df, title="Répartition des Causes d'Arrêt"),
                        use_container_width=True, key="downtime_donut")

    # Management Control Cycle
    render_section_title(f"{inline_icon('clipboard_list', 16, c['primary'])} Synthèse Pilotage — Cycle de Contrôle de Gestion", c, c['primary'])

    TARGET_OEE = 0.82  # Défaut dashboard — configurable via Budget vs Réalisé
    current_oee = stats["avg_oee"]
    oee_gap_pp = (current_oee - TARGET_OEE) * 100
    
    # Reconciled OEE gap cost: uses the canonical potential savings function (Refinement 1)
    oee_gap_eur = calculate_potential_savings(df, TARGET_OEE)

    gap_color = c["danger"] if oee_gap_pp < 0 else c["success"]
    status_icon = inline_icon("check_circle", 14, c["success"]) if current_oee >= TARGET_OEE else inline_icon("alert_triangle", 14, c["danger"])
    status_text = f"{status_icon} Objectif atteint" if current_oee >= TARGET_OEE else f"{status_icon} Sous objectif ({oee_gap_pp:+.1f} pp)"
    status_bg = c["success_bg"] if current_oee >= TARGET_OEE else c["danger_bg"]

    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex; justify-content:space-around; align-items:center; flex-wrap:wrap; gap:1.5rem;">
            <div style="text-align:center;">
                <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">OEE Actuel</div>
                <div style="font-size:2.2rem; font-weight:800; color:{c['primary']};">{current_oee*100:.1f}%</div>
            </div>
            <div style="font-size:1.8rem; color:{c['text_muted']};">vs</div>
            <div style="text-align:center;">
                <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">Cible AIAG</div>
                <div style="font-size:2.2rem; font-weight:800; color:{c['primary']};">{TARGET_OEE*100:.0f}%</div>
            </div>
            <div style="text-align:center;">
                <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">Écart</div>
                <div style="font-size:1.4rem; font-weight:700; color:{gap_color};">{oee_gap_pp:+.1f} pp</div>
                {f'<div style="font-size:12px; color:{c["danger"]}; margin-top:2px;">~ {format_currency(oee_gap_eur)} opportunité</div>' if oee_gap_eur > 0 else ''}
            </div>
            <div>
                <span style="background:{status_bg}; color:{gap_color}; padding:6px 16px;
                             border-radius:20px; font-size:12px; font-weight:600;">{status_text}</span>
            </div>
        </div>
    </div>
    
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-left:4px solid {c['primary']}; border-radius:10px;
                padding:0.75rem 1rem; margin-bottom:1.5rem; font-size:12px; color:{c['text_secondary']};">
        ℹ️ <strong>Note sur la réconciliation des coûts</strong> : Cette valorisation de l'écart est calculée via le modèle socio-économique canonique de potentiel de gains (calculé par point OEE sur la base de la cible et des coûts réels cumulés). Elle diffère de l'estimation de la page Prédiction qui utilise une formule simplifiée à la taille du lot, étalonnée sur l'historique par un facteur correcteur de 1.96x.
    </div>
    """, unsafe_allow_html=True)

    # Planification | Mesure | Action Corrective
    pc1, pc2, pc3 = st.columns(3)

    with pc1:
        plan_icon = inline_icon("clipboard_list", 14, c["primary"])
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:10px;
                    padding:1rem; border-top:3px solid {c['primary']}; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-weight:700; color:{c['text_primary']}; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                {plan_icon} Planification</div>
            <div style="color:{c['text_secondary']}; font-size:12px; line-height:1.8;">
                - Objectif OEE : <strong style="color:{c['text_primary']};">{TARGET_OEE*100:.0f}%</strong><br>
                - Benchmark World Class : 85%<br>
                - Période : {date_start} — {date_end}<br>
                - Lignes : {len(df['Production_Line'].unique())}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with pc2:
        measure_icon = inline_icon("ruler", 14, c["accent_cyan"])
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:10px;
                    padding:1rem; border-top:3px solid {c['accent_cyan']}; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-weight:700; color:{c['text_primary']}; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                {measure_icon} Mesure</div>
            <div style="color:{c['text_secondary']}; font-size:12px; line-height:1.8;">
                - OEE moyen : <strong style="color:{c['primary']};">{current_oee*100:.1f}%</strong><br>
                - Disponibilité : <strong style="color:{c['text_primary']};">{stats['avg_availability']*100:.1f}%</strong><br>
                - Performance : <strong style="color:{c['text_primary']};">{stats['avg_performance']*100:.1f}%</strong><br>
                - Qualité : <strong style="color:{c['text_primary']};">{stats['avg_quality']*100:.1f}%</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with pc3:
        worst = df.groupby(["Production_Line", "Shift_Type"]).agg(
            oee_avg=("OEE", "mean"),
            hc_total=("Total_Hidden_Cost", "sum")
        ).sort_values("oee_avg").head(3).reset_index()

        SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
        worst_html = ""
        danger_color = c["danger"]
        for _, row in worst.iterrows():
            line_name = row['Production_Line']
            shift_name = SHIFT_MAP_FR.get(row['Shift_Type'], row['Shift_Type'])
            oee_val = row['oee_avg'] * 100
            worst_html += f"- <strong style='color:{danger_color};'>{line_name}</strong> / {shift_name} — {oee_val:.1f}%<br>"

        action_icon = inline_icon("zap", 14, c["danger"])
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:10px;
                    padding:1rem; border-top:3px solid {c['danger']}; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-weight:700; color:{c['text_primary']}; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                {action_icon} Action Corrective</div>
            <div style="color:{c['text_secondary']}; font-size:12px; line-height:1.8;">
                {worst_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Management Control KPIs
    render_section_title(f"{inline_icon('gauge', 16, c['accent_teal'])} Indicateurs de Contrôle de Gestion", c, c['accent_teal'])

    total_defective = df["Defective_Units"].sum()
    total_produced = df["Units_Produced_Total"].sum()
    dpu = (total_defective / total_produced * 100) if total_produced > 0 else 0

    if "Downtime_Reason" in df.columns:
        machine_failures = df[df["Downtime_Reason"] == "Machine_Failure"].shape[0]
        total_run_time = df["Run_Time"].sum()
        if machine_failures > 0:
            mtbf_hours = total_run_time / machine_failures / 60
            mtbf_display = f"{mtbf_hours:.0f}h"
        else:
            mtbf_display = "N/A"
    else:
        machine_failures = 0
        mtbf_display = "N/A"

    # MTTR Estimation: Mean Time To Repair is estimated as the average unplanned downtime duration per machine failure event.
    if "Downtime_Reason" in df.columns and machine_failures > 0:
        failure_downtime = df[df["Downtime_Reason"] == "Machine_Failure"]["Unplanned_Downtime"].sum()
        mttr_val = failure_downtime / machine_failures
        mttr_display = f"{mttr_val:.1f} min"
    else:
        mttr_display = "N/A"

    absenteeism = (1 - df["Workforce_Attendance_Rate"].mean()) * 100 if "Workforce_Attendance_Rate" in df.columns else 0

    total_good = df["Good_Units"].sum() if "Good_Units" in df.columns else 0
    total_target = df["Units_Target"].sum() if "Units_Target" in df.columns else 1
    hc_per_unit = stats["total_hidden_cost"] / total_good if total_good > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Taux de Défauts", f"{dpu:.2f}%", "Cible IATF: < 1.2%", delta_color="off",
                  help="Taux de Défauts = Unités défectueuses / Unités produites × 100")
    with m2:
        st.metric("MTBF", mtbf_display, "Cible: > 240h", delta_color="off",
                  help="Mean Time Between Failures = Temps de fonctionnement / Nombre de pannes")
    with m3:
        st.metric("Absentéisme", f"{absenteeism:.1f}%", "Cible: < 5%", delta_color="off",
                  help="Taux d'absentéisme = 1 - Taux de présence moyen")
    with m4:
        st.metric("Coût/Unité", f"{hc_per_unit:.2f} {curr_sym}", delta_color="off",
                  help="Coût caché total / Nombre d'unités conformes produites")

    taux_remplissage = (total_produced / total_target * 100) if total_target > 0 else 0.0
    good_vs_target_delta = int(total_good - total_target)

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("Taux de Remplissage", f"{taux_remplissage:.1f}%", help="Unités totales produites / Unités cibles planifiées × 100")
    with m6:
        st.metric("Bonnes vs Cible", f"{format_number(total_good)}", f"{good_vs_target_delta:+d}", delta_color="off" if good_vs_target_delta <= 0 else "normal",
                  help="Volume d'unités conformes produites comparé au volume cible planifié")
    with m7:
        st.metric("MTTR", mttr_display, "Cible: < 30 min", delta_color="off",
                  help="Temps moyen de réparation = Somme des arrêts pour panne machine / Nombre de pannes machines")
    with m8:
        st.write("")


# ── Cadre Méthodologique ──
with st.expander("Cadre Méthodologique — Indicateurs de Performance Industrielle", expanded=False):
    st.markdown(f"""
    <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
        <strong style="color:{c['text_primary']};">OEE (Overall Equipment Effectiveness) — ISO 22400-2:2014</strong><br>
        <code style="color:{c['accent_cyan']};">OEE = Disponibilité × Performance × Qualité</code><br>
        Indicateur composite mesurant l'efficacité globale de l'équipement.<br><br>
        <strong style="color:{c['text_primary']};">Classification (AIAG) :</strong><br>
        World Class : ≥ 85% | On Target : 75–85% | Below Target : &lt; 75%<br><br>
        <strong style="color:{c['text_primary']};">Coûts Cachés (Modèle ISEOR — Savall & Zardet) :</strong><br>
        <code style="color:{c['accent_cyan']};">HC = Pertes de production × Revenu unitaire × Marge (0.38)</code><br>
        Le coefficient 0.38 représente la marge sur coût variable sectorielle (câblage automobile).<br><br>
        <strong style="color:{c['text_primary']};">MTBF (Mean Time Between Failures) :</strong><br>
        <code style="color:{c['accent_cyan']};">MTBF = Temps de fonctionnement total / Nombre de pannes</code><br><br>
        <strong style="color:{c['text_primary']};">Taux de Défauts :</strong><br>
        <code style="color:{c['accent_cyan']};">Taux = Unités défectueuses / Unités produites totales × 100</code>
    </div>
    """, unsafe_allow_html=True)

# Footer
render_footer(c)
