"""
SmartAudit — Design Tokens
Palette de couleurs corporate — source unique pour toutes les teintes de l'application.
"""

# ── GOLD PALETTE ──────────────────────────────────────────────────────────
COLORS = {
    # Brand Gold — Primary Accent
    "surface_light":  "#F0F6FC",
    "gold_100": "#E8EEF7",
    "gold_200": "#EDD49E",
    "gold_300": "#38BDF8",
    "primary": "#005EB8",
    "gold_600": "#A67C3D",
    "gold_700": "#00488C",
    "gold_800": "#002D59",
    "gold_900": "#4D3316",

    # Surfaces
    "surface_page":    "#F8F6F2",
    "surface_card":    "#FFFFFF",
    "surface_sidebar": "#1C1F26",
    "surface_sidebar_hover": "#252932",
    "surface_sidebar_active": "#2E3340",
    "surface_input":   "#FDFCFB",

    # Backgrounds — compat aliases
    "bg_base":       "#F8F6F2",
    "bg_surface":    "#FFFFFF",
    "bg_elevated":   "#F3F0EB",
    "bg_input":      "#FDFCFB",

    # Borders
    "border":        "#EEEBE5",
    "border_strong": "#DDD9D1",
    "border_gold":   "#0082CA",

    # Text
    "text_primary":   "#1A1D23",
    "text_secondary": "#52586A",  # darkened for WCAG AA contrast (6.5:1 vs #F8F6F2)
    "text_muted":     "#7A8094",  # darkened for WCAG AA contrast (4.0:1 vs #F8F6F2)
    "text_on_dark":   "#F0EDE8",
    "text_on_dark_muted": "#8D94A8",
    "text_gold":      "#A67C3D",

    # Semantic — status colors
    "success":       "#2D7A52",
    "success_bg":    "#EDF7F1",
    "success_icon":  "#3DAA72",
    "warning":       "#9A6B1A",
    "warning_bg":    "#FFF8EC",
    "warning_icon":  "#0082CA",
    "danger":        "#C0453B",
    "danger_bg":     "#FDF0EF",
    "danger_icon":   "#E05C52",
    "info":          "#3A5FA8",
    "info_bg":       "#EEF4FF",
    "info_icon":     "#5580D0",

    # Brand accents — mapped for backward compat
    "primary_dim":   "#A67C3D",
    "accent_cyan":   "#8FA8C8",
    "accent_amber":  "#0082CA",
    "accent_purple": "#B0A8C8",
    "accent_teal":   "#A8C4A8",
    "accent_coral":  "#C8A0A0",

    # Chart series (ordered for Plotly)
    "chart": ["#005EB8", "#00A3E0", "#8FA8C8", "#A8C4A8", "#C8A0A0", "#B0A8C8", "#38BDF8"],
    "chart_1": "#005EB8",
    "chart_2": "#00A3E0",
    "chart_3": "#8FA8C8",
    "chart_4": "#A8C4A8",
    "chart_5": "#C8A0A0",
    "chart_6": "#B0A8C8",
    "chart_bar_primary": "#005EB8",
    "chart_bar_secondary": "#E8D5B7",
    "chart_line": "#005EB8",
    "chart_gauge_fill": "#005EB8",
    "chart_gauge_track": "#F0EDE8",

    # KPI card accent borders
    "kpi_oee":       "#005EB8",
    "kpi_cost":      "#0082CA",
    "kpi_anomaly":   "#C0453B",
    "kpi_quality":   "#A8C4A8",
    "kpi_conform":   "#2D7A52",

    # Shadows
    "shadow_card":       "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    "shadow_card_hover": "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)",
    "shadow_dropdown":   "0 8px 24px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)",

    # Radius
    "radius_sm":   "6px",
    "radius_md":   "10px",
    "radius_lg":   "14px",
    "radius_xl":   "20px",
    "radius_full": "9999px",
}


def get_colors() -> dict:
    """Retourne le dictionnaire de couleurs du système de design."""
    return COLORS


def get_plotly_layout() -> dict:
    """Return a Plotly layout dict consistent with the gold design system."""
    c = COLORS
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "font":          {"color": c["text_secondary"], "family": "Inter, sans-serif", "size": 12},
        "title":         {"font": {"color": c["text_primary"], "size": 14, "family": "Inter, sans-serif"}},
        "xaxis": {
            "gridcolor": c["border"], "linecolor": c["border"],
            "tickcolor": c["border"], "tickfont": {"color": c["text_muted"], "size": 11},
            "zerolinecolor": c["border"], "showline": False, "zeroline": False,
        },
        "yaxis": {
            "gridcolor": c["border"], "linecolor": c["border"],
            "tickcolor": c["border"], "tickfont": {"color": c["text_muted"], "size": 11},
            "zerolinecolor": c["border"], "showline": False, "zeroline": False,
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": c["text_secondary"], "size": 11},
            "bordercolor": c["border"],
            "borderwidth": 0,
        },
        "hoverlabel": {
            "bgcolor": c["text_primary"],
            "bordercolor": "rgba(0,0,0,0)",
            "font": {"size": 12, "color": "#FFFFFF"},
        },
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        "colorway": c["chart"],
    }
