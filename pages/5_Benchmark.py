"""
SmartAudit — Analyse Comparative (Benchmark).
Compare deux périodes pour piloter l'amélioration continue.
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, get_theme_css, get_colors)
from utils.benchmark_engine import (
    compute_benchmark_kpis, compute_oee_gap_decomposition,
    compute_downtime_reason_deltas, generate_benchmark_narrative,
    find_best_line,
)
from utils.chart_builder import make_oee_gap_waterfall, make_downtime_reason_comparison
from utils.ui_helpers import (render_page_header, render_footer, render_section_title,
                               render_empty_state, render_benchmark_kpi_table)
from utils.icons import inline_icon

# ── Thème ──
st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()
df_all = load_data(st.session_state.get("app_currency", "MAD"))

# ═══════════════════════════════════════════════════════════════
# EN-TÊTE
# ═══════════════════════════════════════════════════════════════
render_page_header(
    icon_name="ruler",
    title="Analyse Comparative (Benchmark)",
    subtitle="Comparez deux périodes pour piloter l'amélioration continue",
    c=c,
)

# Résumé KPI comparatif — rendu dynamique après sélection des périodes
summary_placeholder = st.empty()

# ═══════════════════════════════════════════════════════════════
# SÉLECTEURS DE PÉRIODES
# ═══════════════════════════════════════════════════════════════

# Construire les tuples (Année, Mois) disponibles dans les données
df_all = df_all.copy()
df_all["_Year"] = df_all["Date"].dt.year
df_all["_Month"] = df_all["Date"].dt.month
mois_fr = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
           5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
           9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}

period_combos = (
    df_all[["_Year", "_Month"]].drop_duplicates()
    .sort_values(["_Year", "_Month"])
    .reset_index(drop=True)
)
period_labels = [f"{mois_fr.get(row['_Month'], row['_Month'])} {row['_Year']}"
                 for _, row in period_combos.iterrows()]

if len(period_labels) < 2:
    render_empty_state(
        icon_name="calendar",
        title="Données insuffisantes",
        description="Au moins deux mois de données sont nécessaires pour l'analyse comparative.",
        c=c,
    )
    render_footer(c)
    st.stop()

# Défauts : avant-dernier mois vs dernier mois
default_a = max(0, len(period_labels) - 2)
default_b = len(period_labels) - 1

col_a, col_b = st.columns(2)
with col_a:
    sel_a = st.selectbox("Période A (référence)", period_labels, index=default_a, key="bench_period_a")
with col_b:
    sel_b = st.selectbox("Période B (comparaison)", period_labels, index=default_b, key="bench_period_b")

idx_a = period_labels.index(sel_a)
idx_b = period_labels.index(sel_b)
year_a, month_a = int(period_combos.iloc[idx_a]["_Year"]), int(period_combos.iloc[idx_a]["_Month"])
year_b, month_b = int(period_combos.iloc[idx_b]["_Year"]), int(period_combos.iloc[idx_b]["_Month"])

# Filtres partagés (optionnels)
with st.expander("Filtres avancés (appliqués aux deux périodes)", expanded=False):
    f1, f2 = st.columns(2)
    all_lines = sorted(df_all["Production_Line"].unique().tolist())
    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    SHIFT_MAP_EN = {v: k for k, v in SHIFT_MAP_FR.items()}
    all_shifts_raw = sorted(df_all["Shift_Type"].unique().tolist())
    all_shifts_fr = [SHIFT_MAP_FR.get(s, s) for s in all_shifts_raw]
    with f1:
        bench_lines = st.multiselect("Lignes de Production", all_lines, default=all_lines, key="bench_lines")
    with f2:
        bench_shifts_fr = st.multiselect("Type d'Équipe", all_shifts_fr, default=all_shifts_fr, key="bench_shifts_fr")
    bench_shifts = [SHIFT_MAP_EN.get(s, s) for s in bench_shifts_fr]

# ═══════════════════════════════════════════════════════════════
# FILTRAGE DES DONNÉES
# ═══════════════════════════════════════════════════════════════

df_filtered = get_filtered_data(df_all, lines=bench_lines, shifts=bench_shifts)
df_a = df_filtered[(df_filtered["_Year"] == year_a) & (df_filtered["_Month"] == month_a)]
df_b = df_filtered[(df_filtered["_Year"] == year_b) & (df_filtered["_Month"] == month_b)]

# Garde : vérifier que les deux périodes ont des données
if df_a.empty or df_b.empty:
    empty_period = sel_a if df_a.empty else sel_b
    render_empty_state(
        icon_name="calendar",
        title="Aucune donnée pour la période sélectionnée",
        description=f"La période « {empty_period} » ne contient aucune donnée avec les filtres actuels.",
        c=c,
    )
    render_footer(c)
    st.stop()

# ═══════════════════════════════════════════════════════════════
# MEILLEURE LIGNE (calculée sur le jeu COMPLET non filtré)
# ═══════════════════════════════════════════════════════════════

best_line_name = find_best_line(df_all)
df_best_line = df_all[df_all["Production_Line"] == best_line_name] if best_line_name else None

# ═══════════════════════════════════════════════════════════════
# CALCULS
# ═══════════════════════════════════════════════════════════════

kpi_results = compute_benchmark_kpis(df_a, df_b, df_best_line)

metrics_a = {
    "availability": df_a["Availability"].mean(),
    "performance": df_a["Performance"].mean(),
    "quality": df_a["Quality"].mean(),
}
metrics_b = {
    "availability": df_b["Availability"].mean(),
    "performance": df_b["Performance"].mean(),
    "quality": df_b["Quality"].mean(),
}

gap_decomposition = compute_oee_gap_decomposition(metrics_a, metrics_b)
reason_deltas = compute_downtime_reason_deltas(df_a, df_b)

# ═══════════════════════════════════════════════════════════════
# RÉSUMÉ DES KPI EN HAUT DE LA PAGE
# ═══════════════════════════════════════════════════════════════
try:
    oee_a = df_a["OEE"].mean() * 100
    oee_b = df_b["OEE"].mean() * 100
    delta_oee = oee_b - oee_a
    
    # Coûts cachés
    hc_a = df_a["Total_Hidden_Cost"].sum()
    hc_b = df_b["Total_Hidden_Cost"].sum()
    delta_hc = hc_b - hc_a
    
    if delta_oee >= 0.5:
        oee_color = c["success"]
        oee_icon = inline_icon("arrow_up_right", 16, c["success"])
        status_text = "Amélioration globale de la performance"
    elif delta_oee <= -0.5:
        oee_color = c["danger"]
        oee_icon = inline_icon("arrow_down_right", 16, c["danger"])
        status_text = "Dégradation de la performance générale"
    else:
        oee_color = c["info"]
        oee_icon = inline_icon("arrow_right", 16, c["info"])
        status_text = "Performance stable"
        
    hc_color = c["success"] if delta_hc <= 0 else c["danger"]
    
    with summary_placeholder.container():
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-left:4px solid {oee_color};
                    border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="display:flex; justify-content:space-around; align-items:center; flex-wrap:wrap; gap:1.5rem;">
                <div style="text-align:center;">
                    <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">OEE {sel_a}</div>
                    <div style="font-size:2rem; font-weight:800; color:{c['text_secondary']};">{oee_a:.1f}%</div>
                </div>
                <div style="font-size:1.8rem; color:{c['text_muted']};">vs</div>
                <div style="text-align:center;">
                    <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">OEE {sel_b}</div>
                    <div style="font-size:2rem; font-weight:800; color:{c["primary"]};">{oee_b:.1f}%</div>
                </div>
                <div style="text-align:center;">
                    <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">Écart OEE</div>
                    <div style="font-size:1.6rem; font-weight:800; color:{oee_color}; display:flex; align-items:center; justify-content:center; gap:4px;">
                        {oee_icon} {delta_oee:+.1f} pp
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="color:{c['text_muted']}; font-size:11px; text-transform:uppercase; margin-bottom:4px;">Écart Coûts Cachés</div>
                    <div style="font-size:1.6rem; font-weight:800; color:{hc_color};">{delta_hc:+,.0f} {curr_sym}</div>
                </div>
                <div>
                    <span style="background:{c['bg_surface']}; border:1px solid {c['card_border']}; color:{c['text_primary']};
                                 padding:6px 16px; border-radius:20px; font-size:12px; font-weight:600;">{status_text}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
except Exception as e:
    summary_placeholder.error(f"Erreur lors de la génération du résumé des KPI : {e}")

# ═══════════════════════════════════════════════════════════════
# TABLEAU KPI COMPARATIF
# ═══════════════════════════════════════════════════════════════

render_section_title(
    f"{inline_icon('bar_chart_3', 16, c["primary"])} Comparaison des Indicateurs Clés",
    c, c["primary"],
)

best_label = f"Réf. {best_line_name}" if best_line_name else None
render_benchmark_kpi_table(kpi_results, sel_a, sel_b, best_label, c)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# WATERFALL — DÉCOMPOSITION DE L'ÉCART OEE
# ═══════════════════════════════════════════════════════════════

render_section_title(
    f"{inline_icon('trending_up', 16, c["primary"])} Décomposition de l'Écart d'OEE",
    c, c["primary"],
)

wf_col, info_col = st.columns([3, 2])
with wf_col:
    st.plotly_chart(make_oee_gap_waterfall(gap_decomposition), use_container_width=True, key="bench_wf")

with info_col:
    # Détails de la méthode
    with st.expander("Méthodologie : Analyse des Écarts (Méthode du Point Milieu)", expanded=False):
        st.markdown(f"""
        <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
            <strong style="color:{c['text_primary']};">Principe :</strong> La décomposition
            de l'écart OEE utilise la <strong style="color:{c['text_primary']};">méthode du point milieu
            (midpoint decomposition)</strong>, technique classique de l'analyse des écarts
            en contrôle de gestion.<br><br>

            <strong style="color:{c['text_primary']};">Formules :</strong><br>
            <code style="color:{c['accent_cyan']};">Effet Disponibilité = ΔA × P̄ × Q̄</code><br>
            <code style="color:{c['accent_cyan']};">Effet Performance = Ā × ΔP × Q̄</code><br>
            <code style="color:{c['accent_cyan']};">Effet Qualité = Ā × P̄ × ΔQ</code><br>
            <code style="color:{c['accent_cyan']};">Effet Interaction = résidu</code><br><br>

            <strong style="color:{c['text_primary']};">Garantie :</strong>
            Les quatre effets somment exactement à OEE<sub>B</sub> - OEE<sub>A</sub>,
            assurant une décomposition complète et cohérente de l'écart.
        </div>
        """, unsafe_allow_html=True)

    # Résumé chiffré
    d = gap_decomposition
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-radius:12px; padding:1.2rem; margin-top:0.5rem;
                box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:12px; color:{c['text_muted']}; text-transform:uppercase; margin-bottom:6px;">
            Facteur dominant</div>
        <div style="font-size:1.1rem; font-weight:700; color:{c['text_primary']};">
            {d['dominant_factor']}</div>
        <div style="font-size:13px; color:{c['text_secondary']}; margin-top:4px;">
            Contribution : {d['dominant_value'] * 100:+.2f} points</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CAUSES D'ARRÊT — COMPARAISON
# ═══════════════════════════════════════════════════════════════

render_section_title(
    f"{inline_icon('alert_triangle', 16, c['accent_amber'])} Évolution des Causes d'Arrêt",
    c, c["accent_amber"],
)

st.plotly_chart(make_downtime_reason_comparison(reason_deltas), use_container_width=True, key="bench_reasons")

# ═══════════════════════════════════════════════════════════════
# NARRATION AUTOMATIQUE
# ═══════════════════════════════════════════════════════════════

render_section_title(
    f"{inline_icon('book_open', 16, c["primary"])} Analyse de l'Écart",
    c, c["primary"],
)

narrative = generate_benchmark_narrative(sel_a, sel_b, kpi_results, gap_decomposition, reason_deltas)

# Couleur de fond selon direction globale
delta_oee = gap_decomposition["delta_oee"]
if abs(delta_oee) < 0.005:
    narrative_bg = c.get("info_bg", "#EEF4FF")
    narrative_border = c["info"]
elif delta_oee > 0:
    narrative_bg = c["success_bg"]
    narrative_border = c["success"]
else:
    narrative_bg = c["danger_bg"]
    narrative_border = c["danger"]

st.markdown(f"""
<div style="background:{narrative_bg}; border:1px solid {narrative_border};
            border-left:4px solid {narrative_border}; border-radius:12px;
            padding:1.2rem 1.5rem; margin-bottom:1rem; line-height:1.8;">
    <div style="font-size:13px; color:{c['text_primary']};">
        {narrative}
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PIED DE PAGE
# ═══════════════════════════════════════════════════════════════
render_footer(c)
