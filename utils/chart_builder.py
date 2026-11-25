"""
SmartAudit — Constructeur de graphiques Plotly.
Gabarit global ('smartaudit') appliqué à tous les graphiques de l'application.
"""

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
import streamlit as st

from utils.data_loader import get_colors, format_currency, format_number


def _contrast_text(hex_color: str) -> str:
    """Retourne '#FFFFFF' sur fond sombre, '#1A1D23' sur fond clair (luminance WCAG)."""
    try:
        h = hex_color.lstrip('#')
        if len(h) != 6:
            return '#FFFFFF'
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        def _lc(v):
            v /= 255
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        lum = 0.2126 * _lc(r) + 0.7152 * _lc(g) + 0.0722 * _lc(b)
        return '#FFFFFF' if lum < 0.40 else '#1A1D23'
    except Exception:
        return '#FFFFFF'


from utils.constants import DOWNTIME_REASON_MAP_FR

# ── Gabarit Plotly global — appliqué à tous les graphiques ───────
_smartaudit_template = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, -apple-system, BlinkMacSystemFont, sans-serif', color='#7A8094', size=12),
        title=dict(font=dict(color='#1A1D23', size=14, family='Inter, sans-serif')),
        colorway=['#005EB8', '#00A3E0', '#8FA8C8', '#A8C4A8', '#C8A0A0', '#B0A8C8'],
        xaxis=dict(gridcolor='#EEEBE5', linecolor='#EEEBE5', tickcolor='#EEEBE5',
                   tickfont=dict(color='#A0A6B4', size=11), zerolinecolor='#EEEBE5',
                   showline=False, zeroline=False),
        yaxis=dict(gridcolor='#EEEBE5', linecolor='#EEEBE5', tickcolor='#EEEBE5',
                   tickfont=dict(color='#A0A6B4', size=11), zerolinecolor='#EEEBE5',
                   showline=False, zeroline=False),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#7A8094', size=11), borderwidth=0),
        hoverlabel=dict(bgcolor='#1A1D23', bordercolor='rgba(0,0,0,0)',
                        font=dict(size=12, color='#FFFFFF')),
        margin=dict(l=40, r=20, t=40, b=40),
    )
)
pio.templates['smartaudit'] = _smartaudit_template
pio.templates.default = 'smartaudit'


def _get_layout(title='', height=400):
    """Base layout overrides (title + height). Global template handles the rest."""
    return {
        'title': dict(text=title, font=dict(size=14, color='#1A1D23', family='Inter, sans-serif'), x=0.02),
        'height': height,
        'showlegend': True,
    }


def make_sparkline(values, color="#005EB8", height=50):
    """Create a minimal sparkline chart for KPI cards."""
    fig = go.Figure(go.Scatter(
        y=values, mode="lines+markers",
        marker=dict(size=4, color=color),
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def make_oee_gauge(oee_value, title="OEE Actuel"):
    """Jauge circulaire OEE avec zones colorees."""
    c = get_colors()
    oee_pct = oee_value * 100 if oee_value <= 1 else oee_value
    color = c["success"] if oee_pct >= 85 else (c["warning"] if oee_pct >= 75 else c["danger"])

    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=oee_pct,
        number=dict(suffix="%", font=dict(size=48, color=color, family="Inter")),
        delta={'reference': 85, 'decreasing': {'color': '#C0453B'}, 'increasing': {'color': '#2D7A52'}},
        title=dict(text=title, font=dict(size=14, color=c["text_secondary"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=2, tickcolor=c["border"],
                      tickfont=dict(color=c["text_secondary"], size=10)),
            bar=dict(color=color, thickness=0.75),
            bgcolor=c["bg_surface"],
            borderwidth=0,
            steps=[
                dict(range=[0, 65], color="rgba(248,81,73,0.12)"),
                dict(range=[65, 75], color="rgba(240,136,62,0.12)"),
                dict(range=[75, 85], color="rgba(210,153,34,0.12)"),
                dict(range=[85, 100], color="rgba(63,185,80,0.12)"),
            ],
            threshold=dict(line=dict(color=c["warning"], width=3), thickness=0.85, value=85),
        ),
    ))

    layout = _get_layout(height=320)
    layout["margin"] = dict(l=30, r=30, t=30, b=10)
    fig.update_layout(**layout)
    return fig


def make_oee_trend_line(df, title="Évolution de l'OEE — 2025", anomaly_df=None):
    """Courbe d'OEE mensuelle avec moyenne mobile et lignes cibles.
    Si anomaly_df est fourni, superpose des marqueurs pour les équipes anomaliques."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    monthly = df.groupby(df["Date"].dt.to_period("M")).agg(
        OEE_Avg=("OEE_Pct", "mean"),
        Rolling=("OEE_Pct", lambda x: x.rolling(min(3, len(x)), min_periods=1).mean().iloc[-1] if len(x) > 0 else 0)
    ).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()

    fig = go.Figure()

    # Background zones
    fig.add_hrect(y0=0, y1=75, fillcolor="rgba(248,81,73,0.04)", line_width=0)
    fig.add_hrect(y0=75, y1=85, fillcolor="rgba(210,153,34,0.04)", line_width=0)
    fig.add_hrect(y0=85, y1=100, fillcolor=f"rgba({int(c['success'][1:3],16)},{int(c['success'][3:5],16)},{int(c['success'][5:7],16)},0.04)", line_width=0)

    # Actual OEE line — primary gold as main series
    fig.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["OEE_Avg"],
        fill="tozeroy", fillcolor=f"rgba({int(c['primary'][1:3],16)},{int(c['primary'][3:5],16)},{int(c['primary'][5:7],16)},0.08)",
        line=dict(color=c["primary"], width=2.5),
        name="OEE Moyen Mensuel", mode="lines+markers",
        marker=dict(size=6),
    ))

    # Anomaly overlay (Task 3b)
    if anomaly_df is not None and not anomaly_df.empty:
        anom_monthly = anomaly_df.groupby(anomaly_df["Date"].dt.to_period("M")).agg(
            OEE_Avg=("OEE_Pct", "mean"),
            Count=("OEE_Pct", "count"),
        ).reset_index()
        anom_monthly["Date"] = anom_monthly["Date"].dt.to_timestamp()
        fig.add_trace(go.Scatter(
            x=anom_monthly["Date"], y=anom_monthly["OEE_Avg"],
            mode="markers", name="Anomalies détectées",
            marker=dict(symbol="diamond", size=9, color=c["danger"],
                        line=dict(width=1, color=c["danger_bg"])),
            hovertemplate="Anomalies : %{customdata} équipes<br>OEE moyen : %{y:.1f}%<extra></extra>",
            customdata=anom_monthly["Count"],
        ))

    # Reference lines
    fig.add_hline(y=85, line_dash="dash", line_color=c["success"], line_width=1.5,
                  annotation_text="World Class 85%", annotation_font_color=c["success"], annotation_font_size=10)
    fig.add_hline(y=75, line_dash="dot", line_color=c["warning"], line_width=1,
                  annotation_text="Seuil 75%", annotation_font_color=c["warning"], annotation_font_size=10)

    layout = _get_layout(title, height=400)
    layout["xaxis"] = {"title": "", "tickformat": "%b %Y"}
    layout["yaxis"] = {"title": "OEE (%)", "range": [max(0, monthly["OEE_Avg"].min() - 10), 100]}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                            font=dict(size=11, color=c["text_secondary"]))
    fig.update_layout(**layout)
    return fig



def make_oee_by_line_bar(df, title="OEE par Ligne de Production"):
    """Barres horizontales d'OEE par ligne."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    line_oee = df.groupby("Production_Line")["OEE_Pct"].mean().sort_values()
    avg = df["OEE_Pct"].mean()

    colors = [c["success"] if v >= 85 else (c["warning"] if v >= 75 else c["danger"]) for v in line_oee.values]

    fig = go.Figure(go.Bar(
        x=line_oee.values, y=line_oee.index,
        orientation="h", marker_color=colors,
        text=[f"{v:.1f}%" for v in line_oee.values],
        textposition="auto", textfont=dict(color=[_contrast_text(col) for col in colors], size=12, family="Inter"),
    ))

    fig.add_vline(x=avg, line_dash="dash", line_color=c["text_secondary"], line_width=1,
                  annotation_text=f"Moy. {avg:.1f}%", annotation_font_color=c["text_secondary"])

    layout = _get_layout(title, height=350)
    layout["xaxis"] = {"title": "OEE Moyen (%)"}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_oee_by_shift_bar(df, title="OEE par Équipe"):
    """Barres d'OEE par type d'equipe."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    shift_oee = df.groupby("Shift_Type")["OEE_Pct"].mean().sort_values(ascending=False)
    avg = df["OEE_Pct"].mean()

    shift_colors = {"Morning": c["success"], "Afternoon": c["primary"], "Night": c["accent_coral"]}
    colors = [shift_colors.get(s, c["primary"]) for s in shift_oee.index]

    fig = go.Figure(go.Bar(
        x=shift_oee.index, y=shift_oee.values,
        marker_color=colors,
        text=[f"{v:.1f}%" for v in shift_oee.values],
        textposition="auto", textfont=dict(color=[_contrast_text(col) for col in colors], size=13),
    ))

    fig.add_hline(y=avg, line_dash="dash", line_color=c["text_secondary"], line_width=1,
                  annotation_text=f"Moy. {avg:.1f}%")

    layout = _get_layout(title, height=350)
    layout["yaxis"] = {"title": "OEE Moyen (%)"}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_hidden_cost_donut(df, title="Coûts Cachés par Catégorie"):
    """Donut chart des couts caches."""
    c = get_colors()
    hc_avail = df["Hidden_Cost_Availability"].sum() if "Hidden_Cost_Availability" in df.columns else 0
    hc_perf = df["Hidden_Cost_Performance"].sum() if "Hidden_Cost_Performance" in df.columns else 0
    hc_qual = df["Hidden_Cost_Quality"].sum() if "Hidden_Cost_Quality" in df.columns else 0
    total = hc_avail + hc_perf + hc_qual

    fig = go.Figure(go.Pie(
        labels=["Disponibilité", "Performance", "Qualité"],
        values=[hc_avail, hc_perf, hc_qual],
        marker=dict(colors=[c["accent_amber"], c["primary"], c["accent_cyan"]]),
        hole=0.6,
        textinfo="label+percent",
        textfont=dict(color=c["text_primary"], size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} {st.session_state.get('app_currency', 'MAD')}<br>%{percent}<extra></extra>",
    ))

    fig.add_annotation(text=format_currency(total), x=0.5, y=0.5,
                       font=dict(size=16, color=c["text_primary"], family="Inter"), showarrow=False)

    layout = _get_layout(title, height=520)
    layout["margin"] = dict(l=60, r=40, t=60, b=180)
    layout["xaxis"] = {"title": "Causes d\'anomalies"}
    layout["yaxis"] = {"title": "Nombre d\'anomalies (fréquence)", "side": "left"}
    layout["yaxis2"] = {
        "title": "Cumul %", "side": "right", "overlaying": "y",
        "range": [0, 110], "showgrid": False, "tickfont": dict(size=10)
    }
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    fig.update_xaxes(
        tickangle=-40,
        automargin=True,
        tickfont=dict(size=10)
    )
    return fig


def make_hidden_cost_waterfall(df, title="Décomposition des Coûts Cachés"):
    """Waterfall chart des couts caches par categorie."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    hc_avail = df["Hidden_Cost_Availability"].sum() if "Hidden_Cost_Availability" in df.columns else 0
    hc_perf = df["Hidden_Cost_Performance"].sum() if "Hidden_Cost_Performance" in df.columns else 0
    hc_qual = df["Hidden_Cost_Quality"].sum() if "Hidden_Cost_Quality" in df.columns else 0

    fig = go.Figure(go.Waterfall(
        name="Coûts Cachés",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Disponibilité", "Performance", "Qualité", "TOTAL"],
        y=[hc_avail, hc_perf, hc_qual, 0],
        connector=dict(line=dict(color=c["border"], width=1)),
        increasing=dict(marker_color=c["danger"]),
        decreasing=dict(marker_color=c["success"]),
        totals=dict(marker_color=c["accent_amber"]),
        textposition="outside",
        text=[format_currency(v) for v in [hc_avail, hc_perf, hc_qual, hc_avail + hc_perf + hc_qual]],
        textfont=dict(color=c["text_primary"], size=11),
    ))

    layout = _get_layout(title, height=400)
    layout["yaxis"] = {"title": f"Coût ({st.session_state.get('app_currency', 'MAD')})"}
    layout["showlegend"] = False
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    return fig


def make_hidden_cost_trend(df, title="Évolution des Coûts Cachés"):
    """Courbe d'evolution mensuelle des couts caches."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    monthly = df.groupby(df["Date"].dt.to_period("M")).agg({"Total_Hidden_Cost": "sum"}).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["Total_Hidden_Cost"],
        fill="tozeroy", fillcolor=f"rgba({int(c['accent_amber'][1:3],16)},{int(c['accent_amber'][3:5],16)},{int(c['accent_amber'][5:7],16)},0.08)",
        line=dict(color=c["accent_amber"], width=2.5),
        name="Coûts Cachés Mensuels",
        hovertemplate="<b>%{x|%B %Y}</b><br>%{y:,.0f} {st.session_state.get('app_currency', 'MAD')}<extra></extra>",
    ))

    layout = _get_layout(title, height=520)
    layout["margin"] = dict(l=60, r=40, t=60, b=180)
    layout["xaxis"] = {"title": "Causes d\'anomalies"}
    layout["yaxis"] = {"title": "Nombre d\'anomalies (fréquence)", "side": "left"}
    layout["yaxis2"] = {
        "title": "Cumul %", "side": "right", "overlaying": "y",
        "range": [0, 110], "showgrid": False, "tickfont": dict(size=10)
    }
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    fig.update_xaxes(
        tickangle=-40,
        automargin=True,
        tickfont=dict(size=10)
    )
    return fig


def make_hidden_cost_by_line(df, title="Coûts Cachés par Ligne"):
    """Barres des couts caches par ligne de production."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    line_costs = df.groupby("Production_Line")["Total_Hidden_Cost"].sum().sort_values(ascending=True)

    fig = go.Figure(go.Bar(
        x=line_costs.values, y=line_costs.index,
        orientation="h", marker_color=c["accent_amber"],
        text=[format_currency(v) for v in line_costs.values],
        textposition="auto", textfont=dict(color=c["text_primary"], size=11),
    ))

    layout = _get_layout(title, height=350)
    layout["xaxis"] = {"title": f"Cout Total ({st.session_state.get('app_currency', 'MAD')})"}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_oee_by_shift_heatmap(df, title="Heatmap OEE — Ligne × Équipe"):
    """Heatmap OEE par combinaison ligne/equipe."""
    c = get_colors()
    pivot = df.pivot_table(values="OEE_Pct", index="Production_Line", columns="Shift_Type", aggfunc="mean")

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, '#F0F6FC'], [0.5, '#0082CA'], [1, '#00488C']],
        text=[[f"{v:.1f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=13, color=c["text_primary"]),
        colorbar=dict(title="OEE %", tickfont=dict(color=c["text_secondary"])),
    ))

    layout = _get_layout(title, height=400)
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    return fig


def make_oee_distribution_histogram(df, title="Distribution de l'OEE"):
    """Histogramme de distribution OEE."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["OEE_Pct"], nbinsx=30,
        marker_color=c["primary"], opacity=0.75, name="Distribution",
    ))
    fig.add_vline(x=75, line_dash="dash", line_color=c["danger"], line_width=2,
                  annotation_text="Seuil 75%", annotation_font_color=c["danger"])
    fig.add_vline(x=85, line_dash="dash", line_color=c["success"], line_width=2,
                  annotation_text="World Class 85%", annotation_font_color=c["success"])

    layout = _get_layout(title, height=350)
    layout["xaxis"] = {"title": "OEE (%)"}
    layout["yaxis"] = {"title": "Nombre d'equipes"}
    layout["bargap"] = 0.05
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_feature_importance_bar(feature_names, importances, title="Facteurs d'Influence"):
    """Barres horizontales d'importance des variables."""
    c = get_colors()
    FEATURE_LABELS_FR = {
        "Unplanned_Downtime": "Arrêt Non Planifié",
        "Machine_Age_Years": "Âge Machine (ans)",
        "Last_Maintenance_Days_Ago": "Jours Depuis Maintenance",
        "Changeover_Time": "Temps de Changement",
        "Batch_Size": "Taille du Lot",
        "Material_Quality_Score": "Score Qualité Matière",
        "Workforce_Attendance_Rate": "Taux de Présence",
        "Equipment_Temperature_Celsius": "Température Équipement",
        "Energy_Consumption_KWH": "Consommation Énergie",
        "Workforce_Team_Size": "Taille de l'Équipe",
        "Consecutive_Shifts_No_Maintenance": "Shifts Sans Maintenance",
        "Previous_Shift_OEE": "OEE Shift Précédent",
        "Rolling_3Shift_OEE_Avg": "Moy. OEE 3 Shifts",
        "Rolling_7Day_OEE_Avg": "Moy. OEE 7 Jours",
        "Scheduled_Breaks": "Pauses Planifiées",
        "Planned_Production_Time": "Temps Production Planifié",
        "Planned_Maintenance_Time": "Temps Maintenance Planifiée",
    }
    feature_names = [FEATURE_LABELS_FR.get(f, f.replace("_", " ")) for f in feature_names]
    sorted_idx = np.argsort(importances)[-10:]
    names = [feature_names[i] for i in sorted_idx]
    values = [importances[i] for i in sorted_idx]

    fig = go.Figure(go.Bar(
        x=values, y=names, orientation="h",
        marker=dict(color=values, colorscale=[[0, c["accent_cyan"]], [1, c["accent_purple"]]]),
        text=[f"{v:.3f}" for v in values],
        textposition="auto", textfont=dict(color=c["text_primary"], size=11),
    ))

    layout = _get_layout(title, height=400)
    layout["xaxis"] = {"title": "Importance"}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_anomaly_scatter(df, title="Distribution des Anomalies"):
    """Scatter plot des anomalies dans le temps."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    fig = go.Figure()

    normal = df[df["Anomaly_Flag"] == False] if "Anomaly_Flag" in df.columns else df
    anomaly = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else pd.DataFrame()

    fig.add_trace(go.Scatter(
        x=normal["Date"], y=normal["OEE_Pct"],
        mode="markers", name="Normal",
        marker=dict(color=c["accent_cyan"], size=5, opacity=0.4),
    ))

    if not anomaly.empty:
        fig.add_trace(go.Scatter(
            x=anomaly["Date"], y=anomaly["OEE_Pct"],
            mode="markers", name="Anomalie",
            marker=dict(color=c["danger"], size=10, symbol="x", line=dict(width=1, color=c["danger"])),
        ))

    fig.add_hline(y=85, line_dash="dash", line_color=c["success"], line_width=1)
    fig.add_hline(y=75, line_dash="dot", line_color=c["warning"], line_width=1)

    layout = _get_layout(title, height=420)
    layout["xaxis"] = {"title": "Date"}
    layout["yaxis"] = {"title": "OEE (%)"}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    return fig


def make_component_breakdown_radar(df, line=None, title="Radar de Performance"):
    """Radar chart Availability/Performance/Quality vs cible."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    subset = df[df["Production_Line"] == line] if line else df
    actual = [subset["Availability"].mean() * 100, subset["Performance"].mean() * 100, subset["Quality"].mean() * 100]
    target = [90, 95, 99.9]
    categories = ["Disponibilite", "Performance", "Qualite"]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=actual + [actual[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor=f"rgba({int(c['accent_cyan'][1:3],16)},{int(c['accent_cyan'][3:5],16)},{int(c['accent_cyan'][5:7],16)},0.15)",
        line=dict(color=c["accent_cyan"], width=2.5), name="Actuel",
    ))
    fig.add_trace(go.Scatterpolar(
        r=target + [target[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor=f"rgba({int(c['success'][1:3],16)},{int(c['success'][3:5],16)},{int(c['success'][5:7],16)},0.08)",
        line=dict(color=c["success"], width=1.5, dash="dash"), name="Cible World Class",
    ))

    layout = _get_layout(title, height=520)
    layout["margin"] = dict(l=60, r=40, t=60, b=180)
    layout["xaxis"] = {"title": "Causes d\'anomalies"}
    layout["yaxis"] = {"title": "Nombre d\'anomalies (fréquence)", "side": "left"}
    layout["yaxis2"] = {
        "title": "Cumul %", "side": "right", "overlaying": "y",
        "range": [0, 110], "showgrid": False, "tickfont": dict(size=10)
    }
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    fig.update_xaxes(
        tickangle=-40,
        automargin=True,
        tickfont=dict(size=10)
    )
    return fig


def make_anomaly_heatmap(df, title="Anomalies par Ligne x Equipe"):
    """Heatmap du nombre d'anomalies par combinaison ligne/equipe."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    anomalies = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else pd.DataFrame()

    if anomalies.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune anomalie detectee", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color=c["text_secondary"], size=16))
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    pivot = anomalies.pivot_table(values="OEE", index="Production_Line",
                                   columns="Shift_Type", aggfunc="count", fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale="RdYlGn_r",
        text=[[str(int(v)) for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=14, color=c["text_primary"]),
        colorbar=dict(title="Nb", tickfont=dict(color=c["text_secondary"])),
    ))

    layout = _get_layout(title, height=350)
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_anomaly_by_reason_bar(df, title="Anomalies par Cause"):
    """Barres des anomalies par raison d'arret."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    anomalies = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else pd.DataFrame()

    if anomalies.empty or "Downtime_Reason" not in anomalies.columns:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color=c["text_secondary"], size=16))
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    reason_counts = anomalies["Downtime_Reason"].map(DOWNTIME_REASON_MAP_FR).value_counts().head(8)

    fig = go.Figure(go.Bar(
        x=reason_counts.values, y=reason_counts.index,
        orientation="h", marker_color=c["danger"],
        text=reason_counts.values, textposition="auto",
        textfont=dict(color=_contrast_text(c["danger"]), size=12),
    ))

    layout = _get_layout(title, height=350)
    layout["xaxis"] = {"title": "Nombre d'anomalies"}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ═══════════════════════════════════════════════════════════════
# ── Décomposition OEE en cascade (Disponibilité × Performance × Qualité)
# ═══════════════════════════════════════════════════════════════

def make_oee_waterfall_decomposition(df):
    """OEE variance decomposition waterfall: 100% → -Avail loss → -Perf loss → -Quality loss → OEE actual."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    avg_avail = df["Availability"].mean() * 100
    avg_perf = df["Performance"].mean() * 100
    avg_qual = df["Quality"].mean() * 100
    avg_oee = df["OEE"].mean() * 100

    avail_loss = 100 - avg_avail
    # Performance loss relative to what's left after availability
    perf_loss = avg_avail * (1 - df["Performance"].mean())
    # Quality loss relative to what's left after availability and performance
    qual_loss = avg_avail * df["Performance"].mean() * (1 - df["Quality"].mean())

    measures = ["absolute", "relative", "relative", "relative", "total"]
    x_labels = ["Potentiel 100%", "Perte Disponibilité", "Perte Performance", "Perte Qualité", "OEE Actuel"]
    y_vals = [100, -avail_loss, -perf_loss, -qual_loss, 0]
    texts = ["100%", f"-{avail_loss:.1f}%", f"-{perf_loss:.1f}%", f"-{qual_loss:.1f}%", f"{avg_oee:.1f}%"]
    values = [-avail_loss, -perf_loss, -qual_loss]

    # Balance verification
    total_check = sum(v for v in values if v is not None)
    if abs(total_check + avg_oee - 100) > 0.5:  # tolerance
        import logging
        logging.warning(f"OEE waterfall imbalance: residual={total_check + avg_oee - 100:.2f}%")

    fig = go.Figure()
    fig.add_trace(go.Waterfall(
        name="Décomposition OEE",
        orientation="v",
        measure=measures,
        x=x_labels,
        y=y_vals,
        connector=dict(line=dict(color=c["border"], width=1, dash="dot")),
        decreasing=dict(marker_color=c["danger"]),
        increasing=dict(marker_color=c["success"]),
        totals=dict(marker_color=c["primary"]),
        textposition="outside",
        text=texts,
        textfont=dict(color=c["text_primary"], size=12, family="Inter"),
    ))

    layout = _get_layout("Décomposition des Pertes OEE (Waterfall)", height=420)
    layout["yaxis"] = {"title": "OEE (%)", "range": [0, 115]}
    layout["showlegend"] = False
    fig.update_layout(**layout)

    # Add colored annotations for each loss category
    fig.add_annotation(x="Perte Disponibilité", y=100 - avail_loss/2, text="Disponibilité",
                        showarrow=False, font=dict(color=c["accent_teal"], size=10))
    fig.add_annotation(x="Perte Performance", y=100 - avail_loss - perf_loss/2, text="Performance",
                        showarrow=False, font=dict(color=c["accent_amber"], size=10))
    fig.add_annotation(x="Perte Qualité", y=avg_oee + qual_loss/2, text="Qualité",
                        showarrow=False, font=dict(color=c["accent_coral"], size=10))

    return fig


# ═══════════════════════════════════════════════════════════════
# Benchmark — OEE Gap Waterfall & Downtime Reason Comparison
# ═══════════════════════════════════════════════════════════════

def make_oee_gap_waterfall(gap_decomposition, title="Décomposition de l'Écart d'OEE"):
    """Waterfall de décomposition de l'écart OEE entre deux périodes (méthode du point milieu)."""
    c = get_colors()
    d = gap_decomposition

    oee_a_pct = d["oee_a"] * 100
    oee_b_pct = d["oee_b"] * 100
    e_dispo = d["effet_disponibilite"] * 100
    e_perf = d["effet_performance"] * 100
    e_qual = d["effet_qualite"] * 100
    e_inter = d["effet_interaction"] * 100

    fig = go.Figure(go.Waterfall(
        name="Écart OEE",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=["OEE Période A", "Effet Disponibilité", "Effet Performance",
           "Effet Qualité", "Effet Interaction", "OEE Période B"],
        y=[oee_a_pct, e_dispo, e_perf, e_qual, e_inter, 0],
        connector=dict(line=dict(color=c["border"], width=1, dash="dot")),
        increasing=dict(marker_color=c["success"]),
        decreasing=dict(marker_color=c["danger"]),
        totals=dict(marker_color=c["primary"]),
        textposition="outside",
        text=[
            f"{oee_a_pct:.1f}%",
            f"{e_dispo:+.2f}%",
            f"{e_perf:+.2f}%",
            f"{e_qual:+.2f}%",
            f"{e_inter:+.2f}%",
            f"{oee_b_pct:.1f}%",
        ],
        textfont=dict(color=c["text_primary"], size=11, family="Inter"),
    ))

    layout = _get_layout(title, height=420)
    layout["yaxis"] = {
        "title": "OEE (%)",
        "range": [max(0, min(oee_a_pct, oee_b_pct) - 10),
                  min(100, max(oee_a_pct, oee_b_pct) + 10)],
    }
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def make_downtime_reason_comparison(reason_deltas_df, title="Évolution des Causes d'Arrêt"):
    """Barres horizontales groupées comparant les causes d'arrêt entre deux périodes."""
    c = get_colors()

    if reason_deltas_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée de cause d'arrêt disponible",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color=c["text_secondary"], size=14),
        )
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    df = reason_deltas_df.sort_values("Delta", key=abs, ascending=True)
    reasons = [DOWNTIME_REASON_MAP_FR.get(str(r), str(r).replace("_", " ")) for r in df["Reason"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=reasons, x=df["Downtime_A"], name="Période A",
        orientation="h", marker_color=c["accent_cyan"],
        text=[f"{v:.0f}" for v in df["Downtime_A"]],
        textposition="auto", textfont=dict(size=10),
    ))
    fig.add_trace(go.Bar(
        y=reasons, x=df["Downtime_B"], name="Période B",
        orientation="h", marker_color=c["accent_amber"],
        text=[f"{v:.0f}" for v in df["Downtime_B"]],
        textposition="auto", textfont=dict(size=10),
    ))

    layout = _get_layout(title, height=max(300, len(df) * 50))
    layout["xaxis"] = {"title": "Temps d'arrêt (min)"}
    layout["barmode"] = "group"
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
        font=dict(size=11, color=c["text_secondary"]),
    )
    fig.update_layout(**layout)
    return fig


def make_downtime_reason_donut(df, title="Répartition des Causes d'Arrêt"):
    """Donut chart of downtime reasons weighted by unplanned downtime."""
    if df is None or df.empty or "Downtime_Reason" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Pas de données", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=350)
        return fig
    dt_col = "Unplanned_Downtime" if "Unplanned_Downtime" in df.columns else None
    if dt_col:
        reason_data = df.groupby("Downtime_Reason")[dt_col].sum().sort_values(ascending=False).head(8)
    else:
        reason_data = df["Downtime_Reason"].value_counts().head(8)
    labels = [DOWNTIME_REASON_MAP_FR.get(r, str(r).replace("_", " ")) for r in reason_data.index]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=reason_data.values,
        hole=0.55, textinfo="percent+label", textposition="outside",
        pull=[0.05] + [0]*(len(labels)-1),
        marker=dict(colors=['#005EB8','#00A3E0','#8FA8C8','#A8C4A8','#C8A0A0','#B0A8C8','#38BDF8','#0082CA']),
    )])
    fig.update_layout(title=title, template='smartaudit', height=400, showlegend=True,
                      legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
    return fig


def make_anomaly_by_reason_pareto(df, title="Anomalies par Cause (Pareto)"):
    """Pareto chart of anomaly reasons: frequency bars + cumulative percentage line."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    anomalies = df[df["Anomaly_Flag"] == True] if "Anomaly_Flag" in df.columns else pd.DataFrame()

    if anomalies.empty or "Downtime_Reason" not in anomalies.columns:
        fig = go.Figure()
        fig.add_annotation(text="Aucune anomalie détectée", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color=c["text_secondary"], size=16))
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    reason_counts = anomalies["Downtime_Reason"].map(DOWNTIME_REASON_MAP_FR).value_counts()
    if reason_counts.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color=c["text_secondary"], size=16))
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    df_pareto = pd.DataFrame({'Reason': reason_counts.index, 'Count': reason_counts.values})
    df_pareto['Cumulative'] = df_pareto['Count'].cumsum()
    total_count = df_pareto['Count'].sum()
    df_pareto['Cumulative_Pct'] = (df_pareto['Cumulative'] / total_count * 100) if total_count > 0 else 0

    fig = go.Figure()

    # Bar chart for frequencies
    fig.add_trace(go.Bar(
        x=df_pareto['Reason'], y=df_pareto['Count'],
        name="Fréquence", marker_color=c["danger"],
        text=df_pareto['Count'], textposition="outside",
        cliponaxis=False, constraintext="none",
        yaxis="y"
    ))

    # Line chart for cumulative percentages
    fig.add_trace(go.Scatter(
        x=df_pareto['Reason'], y=df_pareto['Cumulative_Pct'],
        name="Cumul %", marker=dict(color=c["accent_amber"], size=6),
        line=dict(color=c["accent_amber"], width=2.5),
        yaxis="y2"
    ))

    # 80% Pareto threshold line
    fig.add_hline(y=80, line_dash="dash", line_color=c["text_muted"], yref="y2",
                  annotation_text="Seuil 80%", annotation_font_color=c["text_muted"], annotation_position="left")

    layout = _get_layout(title, height=520)
    layout["margin"] = dict(l=60, r=40, t=60, b=180)
    layout["xaxis"] = {"title": "Causes d\'anomalies"}
    layout["yaxis"] = {"title": "Nombre d\'anomalies (fréquence)", "side": "left"}
    layout["yaxis2"] = {
        "title": "Cumul %", "side": "right", "overlaying": "y",
        "range": [0, 110], "showgrid": False, "tickfont": dict(size=10)
    }
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    fig.update_xaxes(
        tickangle=-40,
        automargin=True,
        tickfont=dict(size=10)
    )
    return fig


def make_oee_trend_by_line(df, title="Évolution de l'OEE par Ligne de Production"):
    """Monthly OEE trend chart for each line on a single chart with distinct colors."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données pour cette période", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    df_temp = df.copy()
    df_temp["Month_Start"] = df_temp["Date"].dt.to_period("M").dt.to_timestamp()

    monthly_line = df_temp.groupby(["Month_Start", "Production_Line"])["OEE_Pct"].mean().reset_index()

    fig = go.Figure()

    lines = sorted(monthly_line["Production_Line"].unique())
    colors = c["chart"]

    for i, line in enumerate(lines):
        line_df = monthly_line[monthly_line["Production_Line"] == line]
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=line_df["Month_Start"], y=line_df["OEE_Pct"],
            mode="lines+markers", name=f"Ligne {line}",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate="<b>Ligne " + str(line) + "</b><br>Date: %{x|%B %Y}<br>OEE: %{y:.1f}%<extra></extra>"
        ))

    # Reference lines
    fig.add_hline(y=85, line_dash="dash", line_color=c["success"], line_width=1,
                  annotation_text="World Class 85%", annotation_font_color=c["success"], annotation_font_size=10)

    layout = _get_layout(title, height=400)
    layout["xaxis"] = {"title": "", "tickformat": "%b %Y"}
    layout["yaxis"] = {"title": "OEE (%)", "range": [0, 105]}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    return fig


def make_ml_scatter_plot(df, x_col, y_col="OEE_Pct", title="Analyse de la Variable Clé"):
    """Scatter plot of OEE vs a key feature with manual OLS trend line (no statsmodels needed)."""
    c = get_colors()

    if df is None or (hasattr(df, 'empty') and df.empty):
        fig = go.Figure()
        fig.add_annotation(text="Pas de données", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#7A8094"))
        fig.update_layout(template='smartaudit', height=300)
        return fig

    # Map labels to French if possible
    FEATURE_LABELS_FR = {
        "Product_Complexity_encoded": "Complexité Produit (Encodée)",
        "Shift_Type_encoded": "Type d'Équipe (Encodé)",
        "Month": "Mois de l'Année",
        "Changeover_Time": "Temps de Changement (min)",
        "Unplanned_Downtime": "Arrêt Non Planifié (min)",
        "Machine_Age_Years": "Âge Machine (années)",
        "Last_Maintenance_Days_Ago": "Jours depuis Maintenance",
    }
    x_label = FEATURE_LABELS_FR.get(x_col, x_col.replace("_", " "))

    df_clean = df.dropna(subset=[x_col, y_col]).copy()
    if df_clean.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**_get_layout(title, height=350))
        return fig

    # Scatter points colored by Production_Line
    fig = px.scatter(
        df_clean, x=x_col, y=y_col,
        color="Production_Line",
        labels={x_col: x_label, y_col: "OEE (%)", "Production_Line": "Ligne"},
        color_discrete_sequence=c["chart"]
    )

    # Compute OLS Trend Line manually using numpy.polyfit to avoid statsmodels dependency
    try:
        x_vals = df_clean[x_col].astype(float)
        y_vals = df_clean[y_col].astype(float)
        if len(x_vals) > 1:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
            y_line = slope * x_line + intercept
            
            fig.add_trace(go.Scatter(
                x=x_line, y=y_line,
                mode="lines",
                name="Tendance OLS",
                line=dict(color=c["danger"], width=2.5, dash="dash"),
                hovertemplate="Tendance OLS<br>Pente: " + f"{slope:.4f}<extra></extra>"
            ))
    except Exception as e:
        import warnings
        warnings.warn(f"OLS Trendline calculation failed: {e}")

    layout = _get_layout(title, height=400)
    layout["xaxis"] = {"title": x_label}
    layout["yaxis"] = {"title": "OEE (%)"}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
    fig.update_layout(**layout)
    return fig

