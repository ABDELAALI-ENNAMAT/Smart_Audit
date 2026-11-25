"""
SmartAudit — Module de chargement et gestion des données.
Centralise le chargement, le nettoyage et le filtrage des données de production.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os

# ── Chemins des fichiers de données ──────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "production_data.csv")


# ── Protection contre la division par zéro et les valeurs aberrantes ──

def safe_divide(numerator, denominator, default=0.0):
    """Division sécurisée avec garde contre zéro et NaN."""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator


def clamp_oee(value):
    """Borne une valeur OEE dans l'intervalle [0, 1]."""
    if pd.isna(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


# ── Validation des colonnes requises en entrée ────────────────────

# Colonnes obligatoires attendues depuis le CSV
REQUIRED_COLUMNS = [
    "Date", "Shift_Type", "Production_Line", "OEE",
    "Availability", "Performance", "Quality",
    "Total_Hidden_Cost",
    "Hidden_Cost_Availability", "Hidden_Cost_Performance", "Hidden_Cost_Quality",
    "Units_Produced_Total", "Good_Units", "Defective_Units",
    "Batch_Size", "Changeover_Time", "Unplanned_Downtime",
    "Machine_Age_Years", "Last_Maintenance_Days_Ago",
    "Workforce_Attendance_Rate", "Workforce_Team_Size",
    "Equipment_Temperature_Celsius", "Material_Quality_Score",
    "Anomaly_Flag", "Downtime_Reason",
]


def validate_columns(df, required_cols=None):
    """Check all required columns exist. Returns list of missing columns."""
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS
    missing = [c for c in required_cols if c not in df.columns]
    return missing



@st.cache_data(ttl=3600)
def load_data(currency="MAD"):
    """Charge et prepare les donnees de production."""
    try:
        df = pd.read_csv(CSV_PATH)
        
        rename_map = {
            "Total_Hidden_Cost_EUR": "Total_Hidden_Cost",
            "Hidden_Cost_Availability_EUR": "Hidden_Cost_Availability",
            "Hidden_Cost_Performance_EUR": "Hidden_Cost_Performance",
            "Hidden_Cost_Quality_EUR": "Hidden_Cost_Quality"
        }
        df.rename(columns=rename_map, inplace=True)
        
        if currency == "EUR":
            cost_cols = ["Total_Hidden_Cost", "Hidden_Cost_Availability", "Hidden_Cost_Performance", "Hidden_Cost_Quality"]
            for c in cost_cols:
                if c in df.columns:
                    df[c] = df[c] / 10.8
    except FileNotFoundError:
        st.error(f"Fichier de données introuvable : {CSV_PATH}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}")
        return pd.DataFrame()

    # Validation des colonnes requises dès le chargement
    missing = validate_columns(df)
    if missing:
        import warnings
        warnings.warn(f"SmartAudit: Missing columns in CSV: {missing}")

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Contrainte OEE : composantes bornées entre 0 et 1 (ISO 22400)
    for col in ["Availability", "Performance", "Quality"]:
        if col in df.columns:
            df[col] = df[col].clip(0.0, 1.0)

    # Calculer l'OEE si absent
    if "OEE" not in df.columns:
        df["OEE"] = df["Availability"] * df["Performance"] * df["Quality"]

    # Clamp OEE to 0-1 range
    df["OEE"] = df["OEE"].clip(0.0, 1.0)

    # OEE consistency check
    if all(col in df.columns for col in ["OEE", "Availability", "Performance", "Quality"]):
        computed = df["Availability"] * df["Performance"] * df["Quality"]
        discrepancy = (df["OEE"] - computed).abs()
        if discrepancy.max() > 0.01:
            import logging
            logging.warning(f"OEE consistency: {(discrepancy > 0.01).sum()} rows with >1% discrepancy (max={discrepancy.max():.4f})")

    # OEE en pourcentage pour affichage
    df["OEE_Pct"] = (df["OEE"] * 100).round(2)
    df["Availability_Pct"] = (df["Availability"] * 100).round(2)
    df["Performance_Pct"] = (df["Performance"] * 100).round(2)
    df["Quality_Pct"] = (df["Quality"] * 100).round(2)

    # Couts caches totaux si absent
    if "Total_Hidden_Cost" not in df.columns:
        hc_cols = ["Hidden_Cost_Availability", "Hidden_Cost_Performance", "Hidden_Cost_Quality"]
        existing = [c for c in hc_cols if c in df.columns]
        df["Total_Hidden_Cost"] = df[existing].sum(axis=1) if existing else 0

    # Nom du mois en francais
    mois_fr = {1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril",
               5: "Mai", 6: "Juin", 7: "Juillet", 8: "Aout",
               9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"}
    df["Month_Name"] = df["Date"].dt.month.map(mois_fr)

    # Categorie OEE
    if "OEE_Category" not in df.columns:
        df["OEE_Category"] = df["OEE"].apply(
            lambda x: "World_Class" if x >= 0.85 else ("On_Target" if x >= 0.75 else "Below_Target")
        )

    # Affichage anomalie
    if "Anomaly_Flag" in df.columns:
        df["Is_Anomaly_Display"] = df["Anomaly_Flag"].map(
            {True: "Anomalie", False: "Normal", "True": "Anomalie", "False": "Normal"}
        )
    else:
        df["Is_Anomaly_Display"] = "Normal"

    # Tri chronologique
    df = df.sort_values("Date").reset_index(drop=True)

    return df


def get_filtered_data(df, lines=None, shifts=None, date_start=None, date_end=None):
    """Filtre le dataframe selon les parametres selectionnes."""
    filtered = df.copy()

    if date_start is not None:
        filtered = filtered[filtered["Date"] >= pd.to_datetime(date_start)]
    if date_end is not None:
        filtered = filtered[filtered["Date"] <= pd.to_datetime(date_end)]
    if lines and len(lines) > 0:
        filtered = filtered[filtered["Production_Line"].isin(lines)]
    if shifts and len(shifts) > 0:
        filtered = filtered[filtered["Shift_Type"].isin(shifts)]

    return filtered.reset_index(drop=True)


def get_summary_stats(df):
    """Calcule les statistiques cles du jeu de donnees."""
    if df.empty:
        return {
            "avg_oee": 0, "total_hidden_cost": 0, "anomaly_count": 0,
            "world_class_pct": 0, "below_target_pct": 0, "on_target_pct": 0,
            "avg_availability": 0, "avg_performance": 0, "avg_quality": 0,
            "total_shifts": 0, "avg_hidden_cost_per_shift": 0,
        }

    total_shifts = len(df)
    avg_oee = df["OEE"].mean()
    total_hc = df["Total_Hidden_Cost"].sum()

    anomaly_count = 0
    if "Anomaly_Flag" in df.columns:
        anomaly_count = int(df["Anomaly_Flag"].sum()) if df["Anomaly_Flag"].dtype == bool else int((df["Anomaly_Flag"] == True).sum())

    world_class = (df["OEE"] >= 0.85).sum()
    below_target = (df["OEE"] < 0.75).sum()
    on_target = total_shifts - world_class - below_target

    return {
        "avg_oee": round(avg_oee, 4),
        "total_hidden_cost": round(total_hc, 2),
        "anomaly_count": anomaly_count,
        "world_class_pct": round(safe_divide(world_class, total_shifts) * 100, 1),
        "below_target_pct": round(safe_divide(below_target, total_shifts) * 100, 1),
        "on_target_pct": round(safe_divide(on_target, total_shifts) * 100, 1),
        "avg_availability": round(df["Availability"].mean(), 4),
        "avg_performance": round(df["Performance"].mean(), 4),
        "avg_quality": round(df["Quality"].mean(), 4),
        "total_shifts": total_shifts,
        "avg_hidden_cost_per_shift": round(safe_divide(total_hc, total_shifts), 2),
    }


# ── Currency & Number Formatting ──

def format_currency(value, currency=None, decimals=1):
    """Format large numbers into readable millions/thousands."""
    import streamlit as st
    try:
        curr = st.session_state.get("app_currency", "MAD") if currency is None else currency
    except:
        curr = currency if currency else "MAD"
        
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return f"0 {curr}"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M {curr}"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.{decimals}f}K {curr}"
    else:
        return f"{value:.0f} {curr}"


def format_number(value, decimals=1):
    """Format numbers without currency."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "0"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def format_pct(value, decimals=1):
    """Formate un pourcentage pour affichage."""
    try:
        return f"{value * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def safe_format(value, fmt=".1f", suffix="%", default="—"):
    """Format a value safely, returning default if NaN/None/inf."""
    if value is None:
        return default
    try:
        import math
        if math.isnan(value) or math.isinf(value):
            return default
    except (TypeError, ValueError):
        return default
    try:
        return f"{value:{fmt}}{suffix}"
    except (ValueError, TypeError):
        return default


# ── Theme System — Single Gold Palette ──

import sys as _sys
import os as _os
_tokens_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "assets")
if _tokens_dir not in _sys.path:
    _sys.path.insert(0, _tokens_dir)
from design_tokens import get_colors as _dt_get_colors, get_plotly_layout, COLORS as _DT_COLORS


def _build_compat_colors():
    """Build backward-compatible color dict from gold design tokens."""
    dt = _DT_COLORS
    return {
        "bg": dt["bg_base"],
        "card_bg": dt["bg_surface"],
        "card_border": dt["border"],
        "text_primary": dt["text_primary"],
        "text_secondary": dt["text_secondary"],
        "text_muted": dt["text_muted"],
        "primary": dt["primary"],
        "primary_dim": dt["primary_dim"],
        "secondary": dt["accent_cyan"],
        "success": dt["success"],
        "warning": dt["warning"],
        "danger": dt["danger"],
        "info": dt["info"],
        "chart1": dt["chart"][0],
        "chart2": dt["chart"][1],
        "chart3": dt["chart"][2],
        "grid": dt["border"],
        "hover_bg": dt["bg_elevated"],
        "accent_cyan": dt["accent_cyan"],
        "accent_amber": dt["accent_amber"],
        "accent_purple": dt["accent_purple"],
        "accent_teal": dt["accent_teal"],
        "accent_coral": dt["accent_coral"],
        "kpi_oee": dt["kpi_oee"],
        "kpi_cost": dt["kpi_cost"],
        "kpi_anomaly": dt["kpi_anomaly"],
        "kpi_quality": dt["kpi_quality"],
        "kpi_conform": dt["kpi_conform"],
        "bg_surface": dt["bg_surface"],
        "bg_elevated": dt["bg_elevated"],
        "border": dt["border"],
        "border_strong": dt["border_strong"],
        "chart": dt["chart"],
        # Gold-specific tokens
        "primary": dt["primary"],
        "primary": dt["primary"],
        "surface_light": dt["surface_light"],
        "surface_sidebar": dt["surface_sidebar"],
        "surface_sidebar_hover": dt["surface_sidebar_hover"],
        "surface_sidebar_active": dt["surface_sidebar_active"],
        "text_on_dark": dt["text_on_dark"],
        "text_on_dark_muted": dt["text_on_dark_muted"],
        "text_gold": dt["text_gold"],
        "success_bg": dt["success_bg"],
        "danger_bg": dt["danger_bg"],
        "warning_bg": dt["warning_bg"],
    }


# Palette unique — pas de branchement thème
COLORS = _build_compat_colors()


def get_colors():
    """Retourne le dictionnaire de couleurs du système de design."""
    return COLORS


def get_theme_css():
    """Génère le CSS global de l'application — police Inter et variables de couleur.
    Chargé sur chaque page en mode multi-page Streamlit.
    """
    c = COLORS
    return f"""
    <style>
    /* ── Font Import — MUST be first ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Typographie globale ── */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {c['text_primary']} !important;
        font-family: 'Inter', sans-serif !important;
    }}
    p, label {{
        font-family: 'Inter', sans-serif !important;
    }}
    /* Scope limité aux containers markdown pour préserver les icônes Streamlit */
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] div,
    .main .block-container > div > div > div {{
        font-family: 'Inter', sans-serif !important;
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {c['text_primary']} !important;
    }}

    /* ── Fond de page ── */
    .stApp {{ background-color: {c['bg']} !important; }}
    .main .block-container {{
        background-color: {c['bg']} !important;
        max-width: 1400px !important;
        padding: 1.5rem 2rem !important;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {c['surface_sidebar']} !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }}
    section[data-testid="stSidebar"] > div {{
        background: {c['surface_sidebar']} !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stMarkdown label {{
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stDateInput label {{
        color: {c['text_on_dark_muted']} !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.08) !important;
    }}
    section[data-testid="stSidebar"] .stCaption {{
        color: {c['text_on_dark_muted']} !important;
    }}
    section[data-testid="stSidebar"] p {{
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox > div > div {{
        background-color: {c['surface_sidebar_hover']} !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] .stMultiSelect > div > div {{
        background-color: {c['surface_sidebar_hover']} !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] .stDateInput > div > div {{
        background-color: {c['surface_sidebar_hover']} !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] .stExpander {{
        border-color: rgba(255,255,255,0.08) !important;
    }}
    section[data-testid="stSidebar"] .streamlit-expanderHeader {{
        color: {c['text_on_dark']} !important;
    }}
    section[data-testid="stSidebar"] details summary span {{
        color: {c['text_on_dark']} !important;
    }}

    /* ── Masquage de l'interface Streamlit ── */
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    .stDeployButton {{ display: none !important; }}

    /* ── Métriques ── */
    [data-testid="stMetric"] {{
        background: {c['card_bg']} !important;
        border: 1px solid {c['card_border']} !important;
        border-radius: 14px !important;
        padding: 1rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {c['text_secondary']} !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {c['text_primary']} !important;
        font-weight: 700 !important;
    }}

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {{
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid {c['card_border']} !important;
    }}

    /* ── Graphiques Plotly ── */
    [data-testid="stPlotlyChart"] {{
        background: transparent !important;
        border-radius: 12px !important;
    }}
    [data-testid="stPlotlyChart"] > div {{
        background: transparent !important;
    }}

    /* ── Onglets ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px !important;
        border-bottom-color: {c['card_border']} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        color: {c['text_secondary']} !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {c['primary']} !important;
    }}

    /* ── Expanders ── */
    .streamlit-expanderHeader {{
        color: {c['text_primary']} !important;
        font-weight: 600 !important;
    }}
    details summary span {{
        color: {c['text_primary']} !important;
    }}
    .stExpander {{
        border-color: {c['card_border']} !important;
    }}

    /* ── Boutons ── */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        background-color: {c['primary']} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {{
        background-color: {c['primary_dim']} !important;
        transform: scale(0.98) !important;
    }}
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {{
        background-color: {c['card_bg']} !important;
        color: {c['text_primary']} !important;
        border: 1px solid {c['border_strong']} !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }}
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {{
        border-color: {c['primary']} !important;
        background-color: {c['surface_light']} !important;
    }}

    /* ── Boutons de téléchargement ── */
    [data-testid="stDownloadButton"] > button {{
        background: {c['primary']} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    [data-testid="stDownloadButton"] > button:hover {{
        background: {c['primary_dim']} !important;
    }}

    /* ── Selectbox / multiselect ── */
    .stSelectbox > div > div, .stMultiSelect > div > div {{
        background-color: {c['card_bg']} !important;
        border-color: {c['card_border']} !important;
        color: {c['text_primary']} !important;
        border-radius: 10px !important;
    }}
    .stSelectbox > div > div:focus-within, .stMultiSelect > div > div:focus-within {{
        border-color: {c['primary']} !important;
        box-shadow: 0 0 0 3px rgba(201, 169, 110, 0.15) !important;
    }}

    /* ── Slider ── */
    .stSlider label {{ color: {c['text_secondary']} !important; }}

    /* ── Radio ── */
    .stRadio label {{ color: {c['text_secondary']} !important; }}

    /* ── Alertes ── */
    .stAlert {{ border-radius: 10px !important; }}

    /* ── Espacement colonnes ── */
    [data-testid="stHorizontalBlock"] {{ gap: 1rem !important; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {c['border_strong']}; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {c['text_muted']}; }}
    </style>
    """
