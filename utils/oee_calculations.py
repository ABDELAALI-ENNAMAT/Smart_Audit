"""
SmartAudit -- Fonctions de calcul OEE et couts caches.
Implemente les formules OEE (ISO 22400) et un modele de couts caches
(approche inspiree ISEOR de Savall & Zardet).
"""

import pandas as pd
import numpy as np


def calculate_oee(availability, performance, quality):
    """Calcule l'OEE a partir de ses trois composantes."""
    try:
        return float(availability) * float(performance) * float(quality)
    except (ValueError, TypeError):
        return 0.0


def calculate_hidden_cost_availability(units_target, units_produced, revenue_per_unit, margin=0.38):
    """Cout cache de non-disponibilite : perte de production x revenu unitaire x marge."""
    lost = max(0, units_target - units_produced)
    return lost * revenue_per_unit * margin


def calculate_hidden_cost_performance(ideal_units, actual_units, revenue_per_unit, margin=0.38, speed_factor=0.5):
    """Cout cache de sous-performance : ralentissement x revenu x marge x facteur vitesse.

    Note : Le facteur vitesse (speed_factor=0.5) reflète le fait que les pertes
    de cadence n'entraînent que 50% de l'impact des arrêts complets sur les
    coûts d'opportunité (production ralentie vs production stoppée).
    """
    speed_loss = max(0, ideal_units - actual_units)
    return speed_loss * revenue_per_unit * margin * speed_factor


def calculate_hidden_cost_quality(rework_units, rework_cost, scrap_units, scrap_cost):
    """Cout cache de non-qualite : reprise + rebuts (couts directs)."""
    return (rework_units * rework_cost) + (scrap_units * scrap_cost)


def calculate_total_hidden_cost(hc_availability, hc_performance, hc_quality):
    """Somme des trois categories de couts caches."""
    return hc_availability + hc_performance + hc_quality


def get_oee_category(oee_value):
    """Classifie l'OEE en categorie de performance."""
    if oee_value >= 0.85:
        return "World Class"
    elif oee_value >= 0.75:
        return "On Target"
    else:
        return "Below Target"


def get_oee_color(oee_value):
    """Retourne la couleur associee a la categorie OEE (gold design system)."""
    if oee_value >= 0.85:
        return "#2D7A52"   # success — positive green
    elif oee_value >= 0.75:
        return "#0082CA"   # warning — gold accent
    else:
        return "#C0453B"   # danger — negative red


def calculate_cost_per_oee_point(df, target_oee=0.85):
    """Calcule le cout par point de pourcentage d'OEE perdu vs la cible."""
    if df.empty:
        return 0.0
    avg_oee = df["OEE"].mean()
    total_hc = df["Total_Hidden_Cost"].sum()
    gap = (target_oee - avg_oee) * 100
    if gap <= 0 or total_hc <= 0:
        return 0.0
    return total_hc / gap


def calculate_potential_savings(df, target_oee=0.85):
    """Estime les economies si l'OEE moyen atteignait la cible."""
    if df.empty:
        return 0.0
    avg_oee = df["OEE"].mean()
    if avg_oee >= target_oee:
        return 0.0
    cost_per_point = calculate_cost_per_oee_point(df, target_oee=target_oee)
    gap_points = (target_oee - avg_oee) * 100
    return cost_per_point * gap_points


def get_hidden_cost_breakdown(df):
    """Retourne la decomposition des couts caches par categorie."""
    hc_avail = df["Hidden_Cost_Availability"].sum() if "Hidden_Cost_Availability" in df.columns else 0
    hc_perf = df["Hidden_Cost_Performance"].sum() if "Hidden_Cost_Performance" in df.columns else 0
    hc_qual = df["Hidden_Cost_Quality"].sum() if "Hidden_Cost_Quality" in df.columns else 0
    total = hc_avail + hc_perf + hc_qual

    return {
        "availability": round(hc_avail, 2),
        "performance": round(hc_perf, 2),
        "quality": round(hc_qual, 2),
        "total": round(total, 2),
        "pct_availability": round(hc_avail / total * 100, 1) if total > 0 else 0,
        "pct_performance": round(hc_perf / total * 100, 1) if total > 0 else 0,
        "pct_quality": round(hc_qual / total * 100, 1) if total > 0 else 0,
    }
