from __future__ import annotations
"""
SmartAudit — Moteur d'analyse comparative (Benchmark).
Calcule les KPI inter-périodes, la décomposition de l'écart OEE,
les variations de causes d'arrêt et génère une narration automatique.
"""



import pandas as pd
import numpy as np
from utils.data_loader import safe_divide


# ── Définition des KPI du benchmark ─────────────────────────────

# Chaque entrée : (libellé, clé interne, agrégation, direction "mieux")
#   agrégation : "mean" ou "sum" ou "ratio"
#   direction  : "higher" ou "lower"
def _get_kpi_definitions():
    """Build KPI definitions with current currency symbol."""
    import streamlit as st
    curr = st.session_state.get("app_currency", "MAD")
    return [
        ("OEE",                            "oee",           "mean",  "higher"),
        ("Disponibilité",                  "availability",  "mean",  "higher"),
        ("Performance",                    "performance",   "mean",  "higher"),
        ("Qualité",                        "quality",       "mean",  "higher"),
        (f"Coût Caché Total ({curr})",     "hc_total",      "sum",   "lower"),
        ("DPU (Défauts/Unité)",            "dpu",           "ratio", "lower"),
        ("Taux d'Absentéisme",             "absenteeism",   "mean",  "lower"),
        (f"Coût Caché par Unité ({curr})", "hc_per_unit",   "ratio", "lower"),
        ("Temps d'Arrêt Non Planifié",     "downtime",      "sum",   "lower"),
    ]


def _compute_kpi_value(df: pd.DataFrame, key: str, agg: str) -> float:
    """Calcule la valeur d'un KPI pour un DataFrame donné."""
    if df.empty:
        return 0.0

    if key == "oee":
        return df["OEE"].mean() if agg == "mean" else df["OEE"].sum()
    elif key == "availability":
        return df["Availability"].mean()
    elif key == "performance":
        return df["Performance"].mean()
    elif key == "quality":
        return df["Quality"].mean()
    elif key == "hc_total":
        return df["Total_Hidden_Cost"].sum()
    elif key == "dpu":
        total_def = df["Defective_Units"].sum() if "Defective_Units" in df.columns else 0
        total_prod = df["Units_Produced_Total"].sum() if "Units_Produced_Total" in df.columns else 0
        return safe_divide(total_def, total_prod)
    elif key == "absenteeism":
        if "Workforce_Attendance_Rate" in df.columns:
            return (1 - df["Workforce_Attendance_Rate"]).mean()
        return 0.0
    elif key == "hc_per_unit":
        total_hc = df["Total_Hidden_Cost"].sum()
        total_prod = df["Units_Produced_Total"].sum() if "Units_Produced_Total" in df.columns else 0
        return safe_divide(total_hc, total_prod)
    elif key == "downtime":
        return df["Unplanned_Downtime"].sum() if "Unplanned_Downtime" in df.columns else 0.0
    return 0.0


def _format_kpi_value(value: float, key: str) -> str:
    """Formate un KPI pour affichage."""
    if key in ("oee", "availability", "performance", "quality"):
        return f"{value * 100:.1f}%"
    elif key == "absenteeism":
        return f"{value * 100:.1f}%"
    elif key == "dpu":
        return f"{value * 100:.2f}%"
    elif key in ("hc_total", "hc_per_unit"):
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M {st.session_state.get('app_currency', 'MAD')}"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K {st.session_state.get('app_currency', 'MAD')}"
        return f"{value:.0f} {st.session_state.get('app_currency', 'MAD')}"
    elif key == "downtime":
        return f"{value:,.0f} min"
    return f"{value:.2f}"


def compute_benchmark_kpis(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    df_best_line: pd.DataFrame | None = None,
) -> list[dict]:
    """Calcule les KPI comparatifs entre deux périodes.

    Paramètres
    ----------
    df_a : DataFrame de la Période A (référence).
    df_b : DataFrame de la Période B (comparaison).
    df_best_line : DataFrame de la meilleure ligne (jeu complet non filtré).

    Retourne
    --------
    Liste de dicts avec : label, key, val_a, val_b, val_best, delta, delta_pct,
    status ("Amélioration", "Dégradation", "Stable"), direction.
    """
    results = []
    for label, key, agg, direction in _get_kpi_definitions():
        val_a = _compute_kpi_value(df_a, key, agg)
        val_b = _compute_kpi_value(df_b, key, agg)
        delta = val_b - val_a
        delta_pct = safe_divide(delta, abs(val_a)) * 100 if val_a != 0 else 0.0

        # Statut
        if abs(delta_pct) < 1.0:
            status = "Stable"
        else:
            if direction == "higher":
                status = "Amélioration" if delta > 0 else "Dégradation"
            else:  # lower is better
                status = "Amélioration" if delta < 0 else "Dégradation"

        # Meilleure ligne
        val_best = None
        if df_best_line is not None and not df_best_line.empty:
            val_best = _compute_kpi_value(df_best_line, key, agg)

        results.append({
            "label": label,
            "key": key,
            "val_a": val_a,
            "val_b": val_b,
            "val_best": val_best,
            "val_a_fmt": _format_kpi_value(val_a, key),
            "val_b_fmt": _format_kpi_value(val_b, key),
            "val_best_fmt": _format_kpi_value(val_best, key) if val_best is not None else "",
            "delta": delta,
            "delta_pct": delta_pct,
            "status": status,
            "direction": direction,
        })

    return results


# ── Décomposition de l'écart OEE (méthode du point milieu) ──────

def compute_oee_gap_decomposition(
    metrics_a: dict,
    metrics_b: dict,
) -> dict:
    """Décompose l'écart OEE entre deux périodes via la méthode du point milieu.

    Paramètres
    ----------
    metrics_a / metrics_b : dicts avec clés 'availability', 'performance', 'quality'
                            (valeurs en ratio 0-1).

    Retourne
    --------
    Dict avec : oee_a, oee_b, delta_oee, effet_disponibilite, effet_performance,
    effet_qualite, effet_interaction, dominant_factor, dominant_value.
    """
    A_a = metrics_a["availability"]
    P_a = metrics_a["performance"]
    Q_a = metrics_a["quality"]
    A_b = metrics_b["availability"]
    P_b = metrics_b["performance"]
    Q_b = metrics_b["quality"]

    oee_a = A_a * P_a * Q_a
    oee_b = A_b * P_b * Q_b
    delta_oee = oee_b - oee_a

    dA = A_b - A_a
    dP = P_b - P_a
    dQ = Q_b - Q_a
    A_bar = (A_a + A_b) / 2
    P_bar = (P_a + P_b) / 2
    Q_bar = (Q_a + Q_b) / 2

    effet_dispo = dA * P_bar * Q_bar
    effet_perf = A_bar * dP * Q_bar
    effet_qual = A_bar * P_bar * dQ
    effet_inter = delta_oee - (effet_dispo + effet_perf + effet_qual)

    _sum_check = abs(effet_dispo + effet_perf + effet_qual + effet_inter - delta_oee)
    if _sum_check > 0.0001:
        import logging
        logging.warning(f"OEE gap decomposition imbalance: residual={_sum_check:.6f}")

    # Facteur dominant
    effects = {
        "Disponibilité": effet_dispo,
        "Performance": effet_perf,
        "Qualité": effet_qual,
    }
    dominant = max(effects, key=lambda k: abs(effects[k]))

    return {
        "oee_a": oee_a,
        "oee_b": oee_b,
        "delta_oee": delta_oee,
        "effet_disponibilite": effet_dispo,
        "effet_performance": effet_perf,
        "effet_qualite": effet_qual,
        "effet_interaction": effet_inter,
        "dominant_factor": dominant,
        "dominant_value": effects[dominant],
    }


# ── Variations des causes d'arrêt ───────────────────────────────

def compute_downtime_reason_deltas(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    top_n: int = 8,
) -> pd.DataFrame:
    """Compare la distribution des causes d'arrêt entre deux périodes.

    Utilise la somme de Unplanned_Downtime par raison (mesure de sévérité).

    Retourne
    --------
    DataFrame avec : Reason, Downtime_A, Downtime_B, Delta, pct trié par |Delta|
    décroissant, top_n lignes.
    """
    col = "Downtime_Reason"
    dt_col = "Unplanned_Downtime"

    if col not in df_a.columns or dt_col not in df_a.columns:
        return pd.DataFrame(columns=["Reason", "Downtime_A", "Downtime_B", "Delta"])

    dt_a = df_a.groupby(col)[dt_col].sum().rename("Downtime_A")
    dt_b = df_b.groupby(col)[dt_col].sum().rename("Downtime_B") if not df_b.empty else pd.Series(dtype=float, name="Downtime_B")

    merged = pd.DataFrame({"Downtime_A": dt_a, "Downtime_B": dt_b}).fillna(0)
    merged["Delta"] = merged["Downtime_B"] - merged["Downtime_A"]
    merged = merged.reindex(merged["Delta"].abs().sort_values(ascending=False).index)
    merged = merged.head(top_n).reset_index()
    merged = merged.rename(columns={col: "Reason"})

    return merged


# ── Narration automatique ────────────────────────────────────────

def generate_benchmark_narrative(
    period_a_label: str,
    period_b_label: str,
    kpi_results: list[dict],
    gap_decomposition: dict,
    reason_deltas: pd.DataFrame,
) -> str:
    """Génère un paragraphe narratif résumant l'analyse comparative.

    Retourne une chaîne de 3-5 phrases en français.
    """
    delta_oee = gap_decomposition["delta_oee"]
    oee_a_pct = gap_decomposition["oee_a"] * 100
    oee_b_pct = gap_decomposition["oee_b"] * 100
    dominant = gap_decomposition["dominant_factor"]
    dominant_val = gap_decomposition["dominant_value"] * 100

    # Phrase 1 : évolution globale OEE
    if abs(delta_oee * 100) < 0.5:
        phrase1 = (
            f"Entre {period_a_label} et {period_b_label}, l'OEE est resté stable "
            f"autour de {oee_a_pct:.1f}% (Δ ≈ 0 point)."
        )
    else:
        direction = "passé" if delta_oee > 0 else "reculé"
        phrase1 = (
            f"Entre {period_a_label} et {period_b_label}, l'OEE est {direction} "
            f"de {oee_a_pct:.1f}% à {oee_b_pct:.1f}% "
            f"(Δ = {delta_oee * 100:+.1f} points)."
        )

    # Phrase 2 : facteur dominant
    if abs(dominant_val) < 0.1:
        phrase2 = "Les trois composantes (Disponibilité, Performance, Qualité) ont contribué de manière équilibrée à cette évolution."
    else:
        phrase2 = (
            f"Cette évolution s'explique principalement par l'effet {dominant} "
            f"({dominant_val:+.1f} points)"
        )
        # Ajouter un effet secondaire si pertinent
        effects = {
            "Disponibilité": gap_decomposition["effet_disponibilite"] * 100,
            "Performance": gap_decomposition["effet_performance"] * 100,
            "Qualité": gap_decomposition["effet_qualite"] * 100,
        }
        secondary = sorted(
            [(k, v) for k, v in effects.items() if k != dominant],
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        if secondary and abs(secondary[0][1]) > 0.1:
            phrase2 += f", suivi par l'effet {secondary[0][0]} ({secondary[0][1]:+.1f} points)"
        phrase2 += "."

    # Phrase 3 : cause d'arrêt dominante
    if reason_deltas.empty:
        phrase3 = ""
    else:
        top_reason = reason_deltas.iloc[0]
        reason_name = str(top_reason["Reason"]).replace("_", " ")
        reason_delta = top_reason["Delta"]
        if abs(reason_delta) > 0:
            direction_txt = "en hausse" if reason_delta > 0 else "en baisse"
            phrase3 = (
                f"Du côté des arrêts non planifiés, la cause '{reason_name}' "
                f"présente la plus forte variation ({direction_txt} de {abs(reason_delta):.0f} min), "
                f"ce qui constitue une piste d'action prioritaire."
            )
        else:
            phrase3 = ""

    # Phrase 4 : synthèse
    # Compter améliorations vs dégradations
    n_better = sum(1 for k in kpi_results if k["status"] == "Amélioration")
    n_worse = sum(1 for k in kpi_results if k["status"] == "Dégradation")
    n_stable = sum(1 for k in kpi_results if k["status"] == "Stable")

    if n_better > n_worse:
        phrase4 = (
            f"En synthèse, {n_better} indicateurs sur {len(kpi_results)} affichent une amélioration, "
            f"confirmant une dynamique globalement positive sur la période."
        )
    elif n_worse > n_better:
        phrase4 = (
            f"En synthèse, {n_worse} indicateurs sur {len(kpi_results)} se sont dégradés, "
            f"signalant un besoin de mesures correctives ciblées."
        )
    else:
        phrase4 = (
            f"En synthèse, la performance est globalement stable avec "
            f"{n_stable} indicateurs inchangés sur {len(kpi_results)}."
        )

    parts = [p for p in [phrase1, phrase2, phrase3, phrase4] if p]
    return " ".join(parts)


def find_best_line(df_full: pd.DataFrame) -> str | None:
    """Identifie la ligne de production avec le meilleur OEE moyen
    sur l'ensemble du jeu de données non filtré."""
    if df_full.empty or "Production_Line" not in df_full.columns:
        return None
    line_oee = df_full.groupby("Production_Line")["OEE"].mean()
    if line_oee.empty:
        return None
    return str(line_oee.idxmax())
