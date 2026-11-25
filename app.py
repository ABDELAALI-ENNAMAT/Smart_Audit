"""
SmartAudit — Système d'Intelligence de Performance.
Point d'entrée principal de l'application Streamlit.
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Répertoire racine ajouté au path pour les imports relatifs
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# ── Configuration de la page ──────────────────────────────────────
favicon_path = os.path.join(ROOT_DIR, "assets", "favicon.ico")
st.set_page_config(
    page_title="SmartAudit — Performance Intelligence System",
    page_icon=favicon_path if os.path.exists(favicon_path) else "🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

curr_sym = st.session_state.get("app_currency", "MAD")

from utils.data_loader import load_data, get_filtered_data, get_summary_stats, format_currency, get_theme_css, get_colors
from utils.ui_helpers import render_page_header, render_footer, render_kpi_card
from utils.icons import icon, inline_icon

# ── Feuille de style globale ──────────────────────────────────────
st.markdown(get_theme_css(), unsafe_allow_html=True)

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()

# ── Chargement des données de production ─────────────────────────
df = load_data(st.session_state.get("app_currency", "MAD"))
stats = get_summary_stats(df)

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    # Branding sidebar
    st.markdown(f"""
    <div style="font-size:20px; font-weight:800; color:#FFFFFF;
                padding:8px 0; margin-bottom:12px; letter-spacing:-0.02em;
                display:flex; align-items:center; gap:8px;">
        {inline_icon('settings', size=20, color='#FFFFFF')} SmartAudit
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{c["border"]};">', unsafe_allow_html=True)

    # Statut système et horodatage
    st.markdown(f"""
    <div style="color:{c['text_on_dark']};">
        <strong>{inline_icon('check_circle', size=14, color=c['success'])} Système Actif</strong>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption(f"Équipes analysées : **{stats['total_shifts']}**")

    st.markdown(f'<hr style="border-color:{c["border"]};">', unsafe_allow_html=True)

    # ── Filtres globaux ───────────────────────────────────────────
    st.markdown(f"""
    <div style="color:{c['text_on_dark_muted']}; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;">
        {inline_icon('sliders_horizontal', size=12, color=c['text_on_dark_muted'])} FILTRES
    </div>
    """, unsafe_allow_html=True)

    date_min = df["Date"].min().date()
    date_max = df["Date"].max().date()
    date_range = st.date_input("Période", value=(date_min, date_max),
                                min_value=date_min, max_value=date_max)

    all_lines = sorted(df["Production_Line"].unique().tolist())
    selected_lines = st.multiselect("Lignes de Production", all_lines, default=all_lines)

    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    SHIFT_MAP_EN = {v: k for k, v in SHIFT_MAP_FR.items()}

    all_shifts_raw = sorted(df["Shift_Type"].unique().tolist())
    all_shifts_fr = [SHIFT_MAP_FR.get(s, s) for s in all_shifts_raw]
    selected_shifts_fr = st.multiselect("Type d'Équipe", all_shifts_fr, default=all_shifts_fr)
    selected_shifts = [SHIFT_MAP_EN.get(s, s) for s in selected_shifts_fr]

    st.markdown(f'<hr style="border-color:{c["border"]};">', unsafe_allow_html=True)

    # ── Navigation — Cycle de Contrôle de Gestion ──
    with st.expander("Cycle de Contrôle de Gestion", expanded=False):
        st.markdown(f"""
        <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
            <span style="display:inline-flex; align-items:center; gap:4px; padding:6px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;
                         background:rgba(47,129,247,0.1); color:{c['primary']};">{inline_icon('clipboard_list', 12, c['primary'])} Planification</span>
            <span style="color:{c['text_muted']}; font-size:14px;">→</span>
            <span style="display:inline-flex; align-items:center; gap:4px; padding:6px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;
                         background:rgba(57,197,207,0.1); color:{c['accent_cyan']};">{inline_icon('ruler', 12, c['accent_cyan'])} Mesure</span>
            <span style="color:{c['text_muted']}; font-size:14px;">→</span>
            <span style="display:inline-flex; align-items:center; gap:4px; padding:6px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;
                         background:rgba(163,113,247,0.1); color:{c['accent_purple']};">{inline_icon('search', 12, c['accent_purple'])} Analyse</span>
            <span style="color:{c['text_muted']}; font-size:14px;">→</span>
            <span style="display:inline-flex; align-items:center; gap:4px; padding:6px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;
                         background:rgba(248,81,73,0.1); color:{c['danger']};">{inline_icon('zap', 12, c['danger'])} Action</span>
            <span style="color:{c['text_muted']}; font-size:14px;">→</span>
            <span style="display:inline-flex; align-items:center; gap:4px; padding:6px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;
                         background:rgba(63,185,80,0.1); color:{c['success']};">{inline_icon('file_text', 12, c['success'])} Reporting</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin-top:10px; font-size:12px; color:{c['text_secondary']};">
            <strong style="color:{c['text_primary']};">Pages associées :</strong><br>
            {inline_icon('clipboard_list', 12, c['primary'])} <strong>Planification</strong> → Dashboard<br>
            {inline_icon('ruler', 12, c['accent_cyan'])} <strong>Mesure</strong> → Dashboard &amp; Prédiction OEE<br>
            {inline_icon('search', 12, c['accent_purple'])} <strong>Analyse</strong> → Coûts Cachés &amp; Anomalies<br>
            {inline_icon('zap', 12, c['danger'])} <strong>Action</strong> → Anomalies (Actions Correctives)<br>
            {inline_icon('file_text', 12, c['success'])} <strong>Reporting</strong> → Rapports
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{c["border"]};">', unsafe_allow_html=True)

    # ── Méthodologie des Données ──────────────────────────────────
    with st.expander("Méthodologie des Données", expanded=False):
        st.markdown(f"""
        <div style="font-size:12px; color:{c['text_secondary']}; line-height:1.7;">
            Les données utilisées sont des <strong style="color:{c['text_on_dark']};">données simulées calibrées</strong>
            sur des benchmarks sectoriels (AIAG, ISEOR, ISO 22400) et construites à partir
            d'<strong style="color:{c['text_on_dark']};">entretiens terrain</strong> avec les responsables
            de production du site de production.<br><br>
            Elles respectent les contraintes de confidentialité industrielle (NDA) tout en
            reproduisant fidèlement les ordres de grandeur opérationnels observés.<br><br>
            <em>PFA — ENCG Agadir 2025–2026</em>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{c["border"]};">', unsafe_allow_html=True)
    st.caption(f"SmartAudit | Devise : {curr_sym}")

# ── Persistance des filtres en session ────────────────────────────
if isinstance(date_range, tuple) and len(date_range) == 2:
    st.session_state["date_start"] = date_range[0]
    st.session_state["date_end"] = date_range[1]
else:
    st.session_state["date_start"] = date_min
    st.session_state["date_end"] = date_max

st.session_state["selected_lines"] = selected_lines
st.session_state["selected_shifts"] = selected_shifts

# ═══════════════════════════════════════════════════════════════
# CONTENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════

render_page_header("factory", "Système d'Intelligence de Performance",
                   "Pilotage Intelligent de la Production Industrielle", c)

# ── Vérification de la présence des modèles ML ───────────────────
models_dir = os.path.join(ROOT_DIR, "models")
models_exist = all(os.path.exists(os.path.join(models_dir, f))
                   for f in ["oee_rf_model.pkl", "oee_xgb_model.pkl", "anomaly_model.pkl"])

if not models_exist:
    st.warning("Les modèles ML ne sont pas encore entraînés.")
    st.info("Exécutez la commande suivante pour entraîner les modèles :")
    st.code("python models/train_models.py", language="bash")

    if st.button("Entraîner les Modèles", type="primary"):
        with st.spinner("Entraînement en cours..."):
            import subprocess
            result = subprocess.run(
                [sys.executable, os.path.join(models_dir, "train_models.py")],
                capture_output=True, text=True, cwd=ROOT_DIR
            )
            if result.returncode == 0:
                st.success("Modèles entraînés avec succès ! Rechargez la page.")
                st.code(result.stdout[-1500:] if len(result.stdout) > 1500 else result.stdout)
            else:
                st.error("Erreur lors de l'entraînement")
                st.code(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
else:
    # ── KPI synthèse — 4 indicateurs clés ────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    render_kpi_card("OEE Moyen", f"{stats['avg_oee']*100:.1f}%",
                    "Performance globale", True, c["kpi_oee"], c, k1)
    render_kpi_card("Coûts Cachés", format_currency(stats['total_hidden_cost']),
                    "Total période", False, c["kpi_cost"], c, k2)
    render_kpi_card("Anomalies", str(stats['anomaly_count']),
                    "Détections", False, c["kpi_anomaly"], c, k3)
    render_kpi_card("Conformité", f"{stats['world_class_pct'] + stats['on_target_pct']:.0f}%",
                    "Taux global", True, c["kpi_conform"], c, k4)

    # ── Positionnement Métier — Contrôle de Gestion ──────────────
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-radius:16px; padding:2rem; margin-top:1rem;">
        <h3 style="color:{c['primary']}; margin-top:0; font-size:1.1rem;
                   text-transform:uppercase; letter-spacing:0.08em;">
            Positionnement Métier — Contrôle de Gestion
        </h3>
        <p style="color:{c['text_secondary']}; font-size:0.95rem; line-height:1.7; margin-bottom:1rem;">
            Ce système est un <strong style="color:{c['text_primary']};">Outil d'Aide à la Décision (OAD)</strong>
            conçu pour le contrôleur de gestion industriel. Il automatise la collecte et le
            traitement des données opérationnelles, libérant le contrôleur pour se concentrer
            sur <strong style="color:{c['text_primary']};">l'interprétation, l'action corrective et le reporting</strong>
            à la direction générale.
        </p>
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:1rem;">
            <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                        border-radius:10px; padding:1rem; border-top:3px solid {c['primary']};">
                <p style="color:{c['primary']}; font-weight:700; margin:0 0 0.4rem 0; font-size:0.85rem;">
                    MESURE
                </p>
                <p style="color:{c['text_muted']}; font-size:0.82rem; margin:0;">
                    OEE, taux de disponibilité, performance et qualité calculés automatiquement
                    par shift et par ligne selon ISO 22400.
                </p>
            </div>
            <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                        border-radius:10px; padding:1rem; border-top:3px solid {c['danger']};">
                <p style="color:{c['danger']}; font-weight:700; margin:0 0 0.4rem 0; font-size:0.85rem;">
                    VALORISATION
                </p>
                <p style="color:{c['text_muted']}; font-size:0.82rem; margin:0;">
                    Coûts cachés quantifiés selon la méthode ISEOR (Savall &amp; Zardet) :
                    non-disponibilité, sous-performance et non-qualité en {curr_sym}.
                </p>
            </div>
            <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                        border-radius:10px; padding:1rem; border-top:3px solid {c['success']};">
                <p style="color:{c['success']}; font-weight:700; margin:0 0 0.4rem 0; font-size:0.85rem;">
                    PILOTAGE
                </p>
                <p style="color:{c['text_muted']}; font-size:0.82rem; margin:0;">
                    Analyse Budget vs Réalisé, écarts par centre de responsabilité,
                    prédictions préventives et plan d'actions correctives prioritaires.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Pied de page ──────────────────────────────────────────────────
render_footer(c)
