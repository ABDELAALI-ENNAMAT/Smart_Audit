"""
SmartAudit — UI Helper Functions.
Composants UI réutilisables avec styles inline pour un rendu Streamlit fiable.
"""

import math
import streamlit as st
from utils.icons import icon, inline_icon, status_dot


def render_kpi_card(label, value, delta_text, delta_positive, accent_color, c, col, tooltip=None):
    """Affiche une carte KPI avec bordure colorée et badge de variation.
    Si tooltip est fourni, une icône d'information apparaît au survol du libellé."""
    delta_bg = c["success_bg"] if delta_positive else c["danger_bg"]
    delta_color = c["success"] if delta_positive else c["danger"]
    arrow_icon = inline_icon("trending_up", size=12, color=delta_color) if delta_positive else inline_icon("trending_down", size=12, color=delta_color)

    tooltip_html = ""
    if tooltip:
        info_svg = inline_icon("info", size=12, color=c["text_muted"])
        tooltip_html = (
            f' <span title="{tooltip}" style="cursor:help; vertical-align:middle; '
            f'opacity:0.7;">{info_svg}</span>'
        )

    with col:
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                    border-left:4px solid {accent_color}; border-radius:14px;
                    padding:1.2rem 1.4rem; box-shadow:0 1px 3px rgba(0,0,0,0.06);
                    margin-bottom:0.5rem;">
          <div style="font-size:12px; font-weight:500; color:{c['text_secondary']};
                      text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">{label}{tooltip_html}</div>
          <div style="font-size:28px; font-weight:700; color:{c['text_primary']};
                      line-height:1.15; margin-bottom:6px;">{value}</div>
          <span style="font-size:12px; font-weight:600; color:{delta_color};
                       background:{delta_bg}; padding:3px 10px; border-radius:20px;
                       display:inline-flex; align-items:center; gap:4px;">
            {arrow_icon} {delta_text}
          </span>
        </div>
        """, unsafe_allow_html=True)



def render_page_header(icon_name, title, subtitle, c):
    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<div style="font-size:12px; font-weight:600; color:{c["text_secondary"]}; margin-bottom:8px;">DEVISE GLOBALE</div>', unsafe_allow_html=True)
    curr = st.sidebar.radio("Devise", ["MAD", "EUR"], index=0 if st.session_state.get("app_currency", "MAD") == "MAD" else 1, horizontal=True, label_visibility="collapsed")
    
    if curr != st.session_state.get("app_currency", "MAD"):
        st.session_state["app_currency"] = curr
        st.cache_data.clear() # Clear cache to reload data with new currency
        st.rerun()

    """Render a consistent page header with gold gradient underline.
    icon_name should be a Lucide icon name string (e.g. 'bar_chart_3').
    """
    svg = inline_icon(icon_name, size=22, color=c['primary'])
    st.markdown(f"""
    <div style="margin-bottom:0;">
        <h1 style="font-size:22px !important; font-weight:600 !important;
                   color:{c['text_primary']} !important; margin:0 !important;
                   line-height:1.3; display:flex; align-items:center; gap:8px;">
            {svg} {title}
        </h1>
        <div style="font-size:13px; color:{c['text_secondary']}; margin-top:2px;">{subtitle}</div>
    </div>
    <div style="height:3px; background:linear-gradient(90deg, {c['primary']}, {c['accent_amber']}, {c['primary']}40);
                border-radius:2px; margin:0.6rem 0 1rem 0;"></div>
    """, unsafe_allow_html=True)


def render_footer(c):
    """Render the standard app footer."""
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center;
                padding:12px 0; border-top:1px solid {c['card_border']};
                margin-top:2rem; font-size:12px; color:{c['text_muted']};
                flex-wrap:wrap; gap:8px;">
      <span>SmartAudit · Système d'Information de Contrôle de Gestion</span>
      <span>ENCG Agadir · PFA 2025-2026 · Données : simulation sectorielle automobile</span>
    </div>
    """, unsafe_allow_html=True)


def render_finding_card(constat, impact, cause, recommandation, responsable, c):
    """Render a management control finding card with SVG icons."""
    pin_svg = inline_icon("pin", size=12, color=c["text_muted"])
    coins_svg = inline_icon("coins", size=12, color=c["text_muted"])
    search_svg = inline_icon("search", size=12, color=c["text_muted"])
    bulb_svg = inline_icon("lightbulb", size=12, color=c["text_muted"])
    user_svg = inline_icon("user", size=12, color=c["text_muted"])
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-left:4px solid {c['danger']}; border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:1rem;
                box-shadow:0 1px 3px rgba(0,0,0,0.06);">
        <div style="margin-bottom:8px;">
            <div style="font-size:11px; font-weight:600; color:{c['text_muted']};
                        text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:4px;">
                {pin_svg} Constat</div>
            <div style="font-size:13px; color:{c['text_secondary']}; line-height:1.5;">{constat}</div>
        </div>
        <div style="margin-bottom:8px;">
            <div style="font-size:11px; font-weight:600; color:{c['text_muted']};
                        text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:4px;">
                {coins_svg} Impact financier</div>
            <div style="color:{c['danger']}; font-weight:700; font-size:14px;">{impact}</div>
        </div>
        <div style="margin-bottom:8px;">
            <div style="font-size:11px; font-weight:600; color:{c['text_muted']};
                        text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:4px;">
                {search_svg} Cause probable</div>
            <div style="font-size:13px; color:{c['text_secondary']}; line-height:1.5;">{cause}</div>
        </div>
        <div style="margin-bottom:8px;">
            <div style="font-size:11px; font-weight:600; color:{c['text_muted']};
                        text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:4px;">
                {bulb_svg} Recommandation</div>
            <div style="font-size:13px; color:{c['text_secondary']}; line-height:1.5;">{recommandation}</div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:600; color:{c['text_muted']};
                        text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:4px;">
                {user_svg} Responsable suggere</div>
            <span style="display:inline-block; padding:2px 10px; border-radius:12px;
                         background:rgba(201,169,110,0.12); color:{c['text_gold']};
                         font-size:11px; font-weight:600;">{responsable}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(text, c, border_color=None):
    """Affiche un titre de section avec bordure inférieure colorée."""
    bc = border_color or c["primary"]
    st.markdown(f"""
    <p style="font-size:15px; font-weight:700; color:{c['text_primary']};
              margin:1.5rem 0 0.75rem 0; padding-bottom:8px;
              border-bottom:2px solid {bc}; display:inline-block;">{text}</p>
    """, unsafe_allow_html=True)


def render_circular_gauge(value, max_val=100, label="", target=None, c=None):
    """Render a circular gauge using SVG with gold fill arc.

    Args:
        value: current value
        max_val: maximum value for the gauge
        label: text label below the number
        target: optional target value to display
        c: color dict (uses gold tokens)
    """
    if c is None:
        from utils.data_loader import get_colors
        c = get_colors()

    radius = 54
    circumference = 2 * math.pi * radius
    fill_ratio = min(value / max_val, 1.0) if max_val > 0 else 0
    dash_offset = circumference * (1 - fill_ratio)
    display_val = f"{value:.1f}" if isinstance(value, float) else str(value)
    unit = "%" if "%" in label or max_val == 100 else ""

    target_html = ""
    if target is not None:
        target_html = f'<div style="font-size:11px; color:{c["text_muted"]}; margin-top:4px;">Cible: {target}</div>'

    st.markdown(f"""
    <div style="text-align:center; padding:0.5rem;">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="{radius}" fill="none"
          stroke="#F0EDE8" stroke-width="12" />
        <circle cx="70" cy="70" r="{radius}" fill="none"
          stroke="{c['primary']}" stroke-width="12"
          stroke-linecap="round"
          stroke-dasharray="{circumference}"
          stroke-dashoffset="{dash_offset}"
          transform="rotate(-90 70 70)"
          style="transition: stroke-dashoffset 0.8s ease;" />
        <text x="70" y="65" text-anchor="middle"
          style="font-size:24px; font-weight:700; fill:{c['text_primary']}; font-family:Inter,sans-serif;">
          {display_val}{unit}
        </text>
        <text x="70" y="85" text-anchor="middle"
          style="font-size:11px; fill:{c['text_muted']}; font-family:Inter,sans-serif;">
          {label}
        </text>
      </svg>
      {target_html}
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(icon_name, title, description, c=None):
    """Render a designed empty state with SVG icon, title, and description."""
    if c is None:
        from utils.data_loader import get_colors
        c = get_colors()

    svg = icon(icon_name, size=48, color=c["text_muted"])
    st.markdown(f"""
    <div style="text-align:center; padding:3rem 2rem;">
      <div style="margin-bottom:1rem;">{svg}</div>
      <div style="font-size:16px; font-weight:600; color:{c['text_primary']}; margin-bottom:0.5rem;">{title}</div>
      <div style="font-size:14px; color:{c['text_muted']}; max-width:400px; margin:0 auto;">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_benchmark_kpi_table(kpi_results, period_a_label, period_b_label, best_line_name, c):
    status_styles = {
        "Amélioration": (c["success"], c["success_bg"]),
        "Dégradation":  (c["danger"], c["danger_bg"]),
        "Stable":       (c["info"], c.get("info_bg", "#EEF4FF")),
    }

    best_col_hdr = f"<th style='{_th_style(c)}'>Réf. Meilleure Ligne</th>" if best_line_name else ""
    header = f"""<tr>
<th style="{_th_style(c)}; text-align:left;">KPI</th>
<th style="{_th_style(c)}">{period_a_label}</th>
<th style="{_th_style(c)}">{period_b_label}</th>
{best_col_hdr}
<th style="{_th_style(c)}">Δ</th>
<th style="{_th_style(c)}">Δ %</th>
<th style="{_th_style(c)}">Statut</th>
</tr>"""

    rows = ""
    for kpi in kpi_results:
        status_color, status_bg = status_styles.get(kpi["status"], (c["info"], "#EEF4FF"))
        pill = f'<span style="display:inline-block; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; background:{status_bg}; color:{status_color};">{kpi["status"]}</span>'

        delta_key = kpi["key"]
        if delta_key in ("oee", "availability", "performance", "quality", "absenteeism", "dpu"):
            delta_fmt = f'{kpi["delta"] * 100:+.2f} pp'
        elif delta_key in ("hc_total", "hc_per_unit"):
            delta_fmt = f'{kpi["delta"]:+,.0f}'
        else:
            delta_fmt = f'{kpi["delta"]:+,.0f}'

        delta_pct_fmt = f'{kpi["delta_pct"]:+.1f}%'

        best_col = f'<td style="{_td_style(c)}">{kpi["val_best_fmt"]}</td>' if best_line_name else ""

        rows += f"""<tr>
<td style="{_td_style(c)}; text-align:left; font-weight:600;">{kpi["label"]}</td>
<td style="{_td_style(c)}">{kpi["val_a_fmt"]}</td>
<td style="{_td_style(c)}">{kpi["val_b_fmt"]}</td>
{best_col}
<td style="{_td_style(c)}; color:{status_color};">{delta_fmt}</td>
<td style="{_td_style(c)}; color:{status_color};">{delta_pct_fmt}</td>
<td style="{_td_style(c)}">{pill}</td>
</tr>"""

    st.markdown(f"""<div style="overflow-x:auto;">
<table style="width:100%; border-collapse:collapse; background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
<thead>{header}</thead>
<tbody>{rows}</tbody>
</table>
</div>""", unsafe_allow_html=True)


def _th_style(c):
    """Style CSS inline pour les en-têtes du tableau benchmark."""
    return (
        f"padding:10px 14px; font-size:11px; font-weight:700; color:{c['text_secondary']}; "
        f"text-transform:uppercase; letter-spacing:0.05em; text-align:center; "
        f"border-bottom:2px solid {c['card_border']}; background:{c.get('bg_elevated', '#F3F0EB')}"
    )


def _td_style(c):
    """Style CSS inline pour les cellules du tableau benchmark."""
    return (
        f"padding:10px 14px; font-size:13px; color:{c['text_primary']}; "
        f"text-align:center; border-bottom:1px solid {c['card_border']}"
    )

