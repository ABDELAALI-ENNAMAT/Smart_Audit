"""
SmartAudit — Analyse des Couts Caches.
Modele de couts caches — approche inspiree ISEOR (Savall & Zardet).
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import (load_data, get_filtered_data, format_currency,
                                format_number, get_theme_css, get_colors)
from utils.oee_calculations import get_hidden_cost_breakdown, calculate_potential_savings
from utils.chart_builder import (make_hidden_cost_waterfall, make_hidden_cost_donut,
                                  make_hidden_cost_trend, make_hidden_cost_by_line)
from utils.ui_helpers import render_page_header, render_footer, render_section_title
from utils.icons import icon, inline_icon

st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()
df_all = load_data(st.session_state.get("app_currency", "MAD"))
df = get_filtered_data(df_all,
    lines=st.session_state.get("selected_lines"),
    shifts=st.session_state.get("selected_shifts"),
    date_start=st.session_state.get("date_start"),
    date_end=st.session_state.get("date_end"),
)

if df.empty:
    st.warning("Aucune donnee pour les filtres selectionnes.")
    st.stop()

# ── En-tête de page
render_page_header("coins", "Analyse des Coûts Cachés",
                   "Modèle de coûts cachés — approche inspirée ISEOR (Savall & Zardet)", c)

# ── Méthodologie ISEOR — explication du coefficient
with st.expander("Méthodologie : Coefficient 0.38 et approche ISEOR", expanded=False):
    st.markdown(f"""
    <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
        <strong style="color:{c['text_primary']};">Note importante :</strong> Cette application utilise un
        <strong style="color:{c['text_primary']};">modèle de coûts cachés inspiré de la méthodologie ISEOR</strong>
        (Institut de Socio-Économie des Entreprises et des Organisations, fondé par H. Savall et V. Zardet),
        et non une application stricte de la méthode ISEOR complète.<br><br>

        <strong style="color:{c['text_primary']};">Le coefficient 0.38 :</strong><br>
        Ce coefficient représente la marge sur coût variable unitaire utilisée pour convertir
        les pertes de production (unités non produites) en manque à gagner financier.
        Il est calibré sur les ratios de marge typiques de l'industrie du câblage automobile,
        conformément aux benchmarks de l'<strong>AIAG</strong> (Automotive Industry Action Group).<br><br>

        <strong style="color:{c['text_primary']};">Formule :</strong>
        <code style="color:{c['accent_cyan']};">Coût caché = Unités perdues × Revenu unitaire × 0.38</code>
    </div>
    """, unsafe_allow_html=True)

# ── Analyse de sensibilité du coefficient ISEOR
st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">Analyse de Sensibilité du Coefficient</p>', unsafe_allow_html=True)

hc = get_hidden_cost_breakdown(df)
total_hc = hc["total"]
avg_hc = total_hc / len(df) if len(df) > 0 else 0

# Calculate costs at different coefficients
coeff_base = 0.38
coeffs = [0.25, 0.35, 0.38, 0.45]
cost_at = {}
for coeff in coeffs:
    ratio = coeff / coeff_base
    cost_at[coeff] = total_hc * ratio

sa1, sa2, sa3, sa4 = st.columns(4)
for col, coeff in zip([sa1, sa2, sa3, sa4], coeffs):
    with col:
        is_base = coeff == coeff_base
        badge = f' <span style="background:rgba(47,129,247,0.15); color:{c["primary"]}; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:600;">actuel</span>' if is_base else ''
        border_c = c['accent_amber'] if is_base else c['card_border']
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                    border-left:4px solid {border_c}; border-radius:14px;
                    padding:1.2rem 1.4rem; box-shadow:0 2px 12px rgba(0,0,0,0.15);">
            <div style="font-size:11px; font-weight:600; color:{c['text_secondary']};
                        text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;">Coefficient {coeff}{badge}</div>
            <div style="font-size:1.6rem; font-weight:800; color:{c['accent_amber']};
                        line-height:1.15; margin-bottom:6px;">{format_currency(cost_at[coeff])}</div>
            <span style="color:{c['text_muted']}; font-size:11px;">{(cost_at[coeff]/total_hc*100) if total_hc > 0 else 0:.0f}% du ref.</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# HC Summary KPIs
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Coût Caché Total", format_currency(total_hc), delta_color="normal")
with k2:
    st.metric("Coût Moyen / Équipe", format_currency(avg_hc), delta_color="normal")
with k3:
    st.metric("Disponibilité", f"{hc['pct_availability']:.1f}%", delta_color="normal")
with k4:
    st.metric("Performance", f"{hc['pct_performance']:.1f}%", delta_color="normal")

# Charts
ch1, ch2 = st.columns([3, 2])
with ch1:
    st.plotly_chart(make_hidden_cost_waterfall(df), use_container_width=True, key="hc_wf")
with ch2:
    st.plotly_chart(make_hidden_cost_donut(df), use_container_width=True, key="hc_donut")

ch3, ch4 = st.columns(2)
with ch3:
    st.plotly_chart(make_hidden_cost_trend(df), use_container_width=True, key="hc_trend")
with ch4:
    st.plotly_chart(make_hidden_cost_by_line(df), use_container_width=True, key="hc_line")

# Improvement Simulator
st.markdown(f'<p style="font-size:15px; font-weight:700; color:{c["text_primary"]}; margin:1.5rem 0 0.75rem 0; padding-bottom:8px; border-bottom:2px solid {c["primary"]}; display:inline-block;">Simulateur d\'Amélioration</p>', unsafe_allow_html=True)

current_oee = df["OEE"].mean()
target_oee = st.slider("OEE Cible", 0.60, 0.95, 0.85, 0.01,
                        help="Déplacez pour simuler l'impact d'une amélioration de l'OEE")

if target_oee > current_oee:
    savings_shift = avg_hc * (target_oee - current_oee) / (1 - current_oee) if current_oee < 1 else 0
    savings_month = savings_shift * 90  # ~90 shifts/month
    savings_year = savings_month * 12

    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                padding:1.5rem; border-left:4px solid {c['success']};">
        <p style="color:{c['text_primary']}; font-weight:700; font-size:1rem; margin-bottom:0.8rem;">
            En atteignant un OEE de {target_oee*100:.0f}% depuis {current_oee*100:.1f}% :</p>
        <p style="color:{c['success']}; font-size:0.95rem;">
            → Économie par équipe : <strong>{format_currency(savings_shift)}</strong></p>
        <p style="color:{c['success']}; font-size:0.95rem;">
            → Économie mensuelle : <strong>{format_currency(savings_month)}</strong></p>
        <p style="color:{c['success']}; font-size:0.95rem;">
            → Économie annuelle : <strong>{format_currency(savings_year)}</strong></p>
    </div>
    """, unsafe_allow_html=True)
elif target_oee < current_oee:
    st.info("Objectif inférieur au niveau actuel — aucune économie possible.")
else:
    st.info("L'objectif correspond au niveau actuel.")

# ═══════════════════════════════════════════════════════════════
# ISEOR INSTRUMENTS — Grille de Compétences, Tableau de Bord, PAP
# ═══════════════════════════════════════════════════════════════

st.markdown('---')
render_section_title("Instruments ISEOR — Analyse Socio-Économique", c, c['primary'])

st.markdown(f"""
<div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
            border-left:4px solid {c['primary']}; border-radius:12px;
            padding:1.2rem 1.5rem; margin-bottom:1.2rem;">
    <p style="color:{c['text_primary']}; font-weight:700; font-size:0.95rem; margin-bottom:0.5rem;">Méthodologie ISEOR (Savall & Zardet)</p>
    <p style="color:{c['text_secondary']}; font-size:0.85rem; line-height:1.7; margin:0;">
        Les instruments ci-dessous s'inspirent de la <strong style="color:{c['text_primary']}">méthode ISEOR</strong> de management socio-économique.
        Ils permettent de diagnostiquer les dysfonctionnements, quantifier les coûts cachés et piloter
        les actions correctives selon trois axes : <strong style="color:{c['text_primary']}">compétences</strong>,
        <strong style="color:{c['text_primary']}">indicateurs socio-économiques</strong> et
        <strong style="color:{c['text_primary']}">plan d'actions prioritaires (PAP)</strong>.
    </p>
</div>
""", unsafe_allow_html=True)

tab_comp, tab_tdb, tab_pap = st.tabs([
    "Grille de Compétences",
    "Tableau de Bord Socio-Économique",
    "Plan d'Actions Prioritaires (PAP)"
])

# ───────────────────────────────────────────────────────────────
# TAB 1 — Grille de Compétences
# ───────────────────────────────────────────────────────────────
with tab_comp:
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-radius:12px; padding:1rem 1.4rem; margin-bottom:1rem;">
        <p style="color:{c['text_secondary']}; font-size:0.85rem; line-height:1.6; margin:0;">
            La grille de compétences identifie les écarts entre le <strong style="color:{c['text_primary']}">niveau requis</strong>
            et le <strong style="color:{c['text_primary']}">niveau observé</strong> pour chaque poste clé.
            Chaque écart génère un coût caché mensuel estimé.
        </p>
    </div>
    """, unsafe_allow_html=True)

    competences_data = pd.DataFrame({
        "Poste": [
            "Opérateur Coupe", "Opérateur Sertissage", "Opérateur Assemblage",
            "Contrôleur Qualité", "Chef de Ligne", "Technicien Maintenance",
            "Opérateur Test Électrique", "Cariste / Approvisionneur",
            "Superviseur Production", "Technicien Méthodes"
        ],
        "Compétence Requise": [
            "Réglage machine coupe", "Sertissage multi-contacts", "Lecture schéma câblage",
            "Maîtrise contrôle dimensionnel", "Gestion d'équipe & planification",
            "Maintenance préventive & prédictive", "Interprétation résultats test",
            "Gestion flux & FIFO", "Pilotage indicateurs OEE",
            "Analyse temps & méthodes SMED"
        ],
        "Niveau Requis": [4, 4, 3, 4, 5, 5, 4, 3, 5, 5],
        "Niveau Observé": [3, 2, 3, 3, 4, 3, 3, 2, 3, 4],
        "Écart": [1, 2, 0, 1, 1, 2, 1, 1, 2, 1],
        "Coût Caché Estimé ({st.session_state.get('app_currency', 'MAD')}/mois)": [
            950, 1800, 0, 1200, 1500, 2400, 850, 700, 2100, 1700
        ],
        "Action ISEOR": [
            "Formation réglage avancé",
            "Tutorat + certification interne",
            "Niveau conforme",
            "Formation métrologie avancée",
            "Coaching management opérationnel",
            "Plan de montée en compétences maintenance",
            "Formation interprétation tests",
            "Formation logistique Lean",
            "Formation pilotage KPI & OEE",
            "Certification SMED"
        ]
    })

    st.dataframe(
        competences_data,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Niveau Requis": st.column_config.NumberColumn("Niveau Requis", format="%d /5"),
            "Niveau Observé": st.column_config.NumberColumn("Niveau Observé", format="%d /5"),
            "Écart": st.column_config.NumberColumn("Écart", format="%d"),
            "Coût Caché Estimé ({st.session_state.get('app_currency', 'MAD')}/mois)": st.column_config.NumberColumn(
                "Coût Caché ({st.session_state.get('app_currency', 'MAD')}/mois)", format=f"%.0f {st.session_state.get('app_currency', 'MAD')}"
            ),
        },
    )

    total_ecarts = competences_data["Coût Caché Estimé ({st.session_state.get('app_currency', 'MAD')}/mois)"].sum()
    st.markdown(f"""
    <div style="background:{c['warning_bg']}; border:1px solid {c['warning']};
                border-radius:10px; padding:0.9rem 1.3rem; margin-top:0.5rem;">
        <p style="color:{c['text_primary']}; font-size:0.9rem; margin:0;">
            <strong>Total des écarts de compétences :</strong>
            <span style="color:{c['warning']}; font-weight:800; font-size:1.05rem;">{format_currency(total_ecarts)}/mois</span>
            — soit environ <strong>{format_currency(total_ecarts * 12)}/an</strong> de coûts cachés liés aux sous-compétences.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# TAB 2 — Tableau de Bord Socio-Économique
# ───────────────────────────────────────────────────────────────
with tab_tdb:
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-radius:12px; padding:1rem 1.4rem; margin-bottom:1rem;">
        <p style="color:{c['text_secondary']}; font-size:0.85rem; line-height:1.6; margin:0;">
            Indicateurs socio-économiques calculés à partir des <strong style="color:{c['text_primary']}">données réelles</strong>
            de production, comparés aux <strong style="color:{c['text_primary']}">références ISEOR</strong> et benchmarks sectoriels.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Compute live indicators
    _abs_rate = (1 - df["Workforce_Attendance_Rate"].mean()) * 100 if "Workforce_Attendance_Rate" in df.columns else 0
    _avg_downtime = df["Unplanned_Downtime"].mean() if "Unplanned_Downtime" in df.columns else 0
    _defect_rate = (1 - df["Quality"].mean()) * 100 if "Quality" in df.columns else 0
    _anomaly_flag_col = df["Anomaly_Flag"] if "Anomaly_Flag" in df.columns else pd.Series([False]*len(df))
    _anomaly_rate = _anomaly_flag_col.mean() * 100
    _oee_mean = df["OEE"].mean() * 100 if "OEE" in df.columns else 0
    _turnover_est = max(0, (_abs_rate - 2) * 0.8)  # estimated from absenteeism proxy

    def _iseor_status(observed, ref_good, ref_bad, lower_is_better=True):
        """Return status emoji based on ISEOR thresholds."""
        if lower_is_better:
            if observed <= ref_good:
                return "Conforme"
            elif observed <= ref_bad:
                return "À surveiller"
            else:
                return "Critique"
        else:
            if observed >= ref_good:
                return "Conforme"
            elif observed >= ref_bad:
                return "À surveiller"
            else:
                return "Critique"

    tdb_data = pd.DataFrame({
        "Catégorie ISEOR": [
            "Absentéisme",
            "Rotation du personnel (est.)",
            "Temps d'arrêt non planifié",
            "Taux de défauts qualité",
            "Taux d'anomalies (Isolation Forest)",
            "OEE moyen",
        ],
        "Valeur Observée": [
            f"{_abs_rate:.1f}%",
            f"{_turnover_est:.1f}%",
            f"{_avg_downtime:.0f} min",
            f"{_defect_rate:.2f}%",
            f"{_anomaly_rate:.1f}%",
            f"{_oee_mean:.1f}%",
        ],
        "Référence ISEOR/Secteur": [
            "< 3%",
            "< 5%",
            "< 15 min",
            "< 1.5%",
            "< 5%",
            "> 75%",
        ],
        "Statut": [
            _iseor_status(_abs_rate, 3, 6),
            _iseor_status(_turnover_est, 5, 10),
            _iseor_status(_avg_downtime, 15, 30),
            _iseor_status(_defect_rate, 1.5, 3),
            _iseor_status(_anomaly_rate, 5, 10),
            _iseor_status(_oee_mean, 75, 65, lower_is_better=False),
        ],
        "Coût Caché Lié": [
            format_currency(_abs_rate / 100 * total_hc * 0.3),
            format_currency(_turnover_est / 100 * total_hc * 0.15),
            format_currency(hc.get("availability", 0)),
            format_currency(hc.get("quality", 0)),
            format_currency(total_hc * _anomaly_rate / 100),
            format_currency(total_hc * max(0, (75 - _oee_mean)) / 100),
        ],
    })

    st.dataframe(
        tdb_data,
        use_container_width=True,
        hide_index=True,
        height=280,
    )

    # Summary row
    _n_critical = tdb_data["Statut"].str.contains("Critique").sum()
    _n_warning = tdb_data["Statut"].str.contains("surveiller").sum()
    _n_ok = tdb_data["Statut"].str.contains("Conforme").sum()

    _status_color = c['danger'] if _n_critical > 0 else (c['warning'] if _n_warning > 0 else c['success'])
    _status_bg = c['danger_bg'] if _n_critical > 0 else (c['warning_bg'] if _n_warning > 0 else c['success_bg'])
    st.markdown(f"""
    <div style="background:{_status_bg}; border:1px solid {_status_color};
                border-radius:10px; padding:0.9rem 1.3rem; margin-top:0.5rem;">
        <p style="color:{c['text_primary']}; font-size:0.9rem; margin:0;">
            <strong>Bilan :</strong>
            <span style="color:{c['success']};">{_n_ok} conforme(s)</span> •
            <span style="color:{c['warning']};">{_n_warning} à surveiller</span> •
            <span style="color:{c['danger']};">{_n_critical} critique(s)</span>
            — Coût caché total de la période : <strong style="color:{_status_color};">{format_currency(total_hc)}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# TAB 3 — Plan d'Actions Prioritaires (PAP)
# ───────────────────────────────────────────────────────────────
with tab_pap:
    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
                border-radius:12px; padding:1rem 1.4rem; margin-bottom:1rem;">
        <p style="color:{c['text_secondary']}; font-size:0.85rem; line-height:1.6; margin:0;">
            Le PAP synthétise les <strong style="color:{c['text_primary']}">actions correctives prioritaires</strong>
            issues du diagnostic des coûts cachés et des anomalies détectées, avec estimation du retour sur investissement.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Build PAP from top 5 downtime reasons
    _dt_counts = df["Downtime_Reason"].value_counts().head(5) if "Downtime_Reason" in df.columns else pd.Series(dtype=int)

    _pap_actions = {
        "Machine_Failure": {
            "cause": "Vieillissement équipements, maintenance préventive insuffisante",
            "action": "Déployer programme de maintenance prédictive (capteurs IoT)",
            "responsable": "Dir. Maintenance",
            "delai": "3 mois",
            "invest": 25000,
            "saving": 120000,
        },
        "Material_Shortage": {
            "cause": "Ruptures fréquentes, stock de sécurité mal calibré",
            "action": "Recalibrer stocks sécurité, contrats VMI fournisseurs",
            "responsable": "Dir. Supply Chain",
            "delai": "2 mois",
            "invest": 8000,
            "saving": 65000,
        },
        "Operator_Absence": {
            "cause": "Absentéisme récurrent, conditions de travail",
            "action": "Plan de fidélisation, polyvalence, amélioration conditions",
            "responsable": "DRH",
            "delai": "6 mois",
            "invest": 15000,
            "saving": 80000,
        },
        "Quality_Hold": {
            "cause": "Non-conformités récurrentes, contrôle réception insuffisant",
            "action": "SPC en ligne, renforcement contrôle réception, formation",
            "responsable": "Dir. Qualité",
            "delai": "3 mois",
            "invest": 12000,
            "saving": 55000,
        },
        "Changeover_Issue": {
            "cause": "Temps de changement excessifs, méthodes non standardisées",
            "action": "Déploiement SMED, standardisation des procédures",
            "responsable": "Dir. Méthodes",
            "delai": "4 mois",
            "invest": 10000,
            "saving": 45000,
        },
        "IT_SAP_Issue": {
            "cause": "Instabilité système, interfaces défaillantes",
            "action": "Upgrade infrastructure, plan de continuité IT",
            "responsable": "DSI",
            "delai": "2 mois",
            "invest": 18000,
            "saving": 35000,
        },
        "Tool_Breakage": {
            "cause": "Outillage usé, suivi de durée de vie insuffisant",
            "action": "Système de suivi outillage, remplacement préventif",
            "responsable": "Dir. Maintenance",
            "delai": "2 mois",
            "invest": 8500,
            "saving": 30000,
        },
        "Safety_Stop": {
            "cause": "Incidents sécurité, procédures non respectées",
            "action": "Audit sécurité, formation EHS, mise à jour procédures",
            "responsable": "Resp. HSE",
            "delai": "1 mois",
            "invest": 5000,
            "saving": 20000,
        },
        "Supplier_Delay": {
            "cause": "Fournisseurs non fiables, dépendance mono-source",
            "action": "Diversification fournisseurs, pénalités contractuelles",
            "responsable": "Dir. Achats",
            "delai": "4 mois",
            "invest": 3200,
            "saving": 18000,
        },
    }

    DOWNTIME_REASON_MAP_FR = {
        "Machine_Failure": "Panne Machine",
        "Material_Shortage": "Rupture de Matière",
        "Operator_Absence": "Absence d'Opérateur",
        "Quality_Hold": "Blocage Qualité",
        "Changeover_Issue": "Problème de Changement de Série",
        "IT_SAP_Issue": "Problème IT/SAP",
        "Tool_Breakage": "Casse d'Outil",
        "Safety_Stop": "Arrêt Sécurité",
        "Supplier_Delay": "Retard Fournisseur",
    }
    _pap_rows = []
    for i, (reason, count) in enumerate(_dt_counts.items(), 1):
        info = _pap_actions.get(reason, {
            "cause": "Analyse approfondie requise",
            "action": "Investigation et plan d'action correctif",
            "responsable": "Dir. Production",
            "delai": "3 mois",
            "invest": 10000,
            "saving": 40000,
        })
        _pap_rows.append({
            "N°": i,
            "Priorité": "Critique" if i <= 2 else ("Haute" if i <= 3 else "Moyenne"),
            "Dysfonctionnement": DOWNTIME_REASON_MAP_FR.get(reason, reason.replace("_", " ")) + f" ({count} occurrences)",
            "Cause Racine": info["cause"],
            "Action Corrective": info["action"],
            "Responsable": info["responsable"],
            "Délai": info["delai"],
            f"Invest. ({curr_sym})": info["invest"],
            f"Économie/an ({curr_sym})": info["saving"],
        })

    if _pap_rows:
        pap_df = pd.DataFrame(_pap_rows)
        st.dataframe(
            pap_df,
            use_container_width=True,
            hide_index=True,
            height=250,
            column_config={
                "N°": st.column_config.NumberColumn("N°", width="small"),
                "Priorité": st.column_config.TextColumn("Priorité", width="small"),
                f"Invest. ({curr_sym})": st.column_config.NumberColumn(f"Invest. ({curr_sym})", format=f"%.0f {st.session_state.get('app_currency', 'MAD')}"),
                f"Économie/an ({curr_sym})": st.column_config.NumberColumn(f"Économie/an ({curr_sym})", format=f"%.0f {st.session_state.get('app_currency', 'MAD')}"),
            },
        )

        _total_invest = pap_df[f"Invest. ({curr_sym})"].sum()
        _total_saving = pap_df[f"Économie/an ({curr_sym})"].sum()
        _roi_months = (_total_invest / (_total_saving / 12)) if _total_saving > 0 else 0

        st.markdown(f"""
        <div style="background:{c['success_bg']}; border:1px solid {c['success']};
                    border-radius:12px; padding:1.2rem 1.5rem; margin-top:0.8rem;">
            <p style="color:{c['text_primary']}; font-weight:700; font-size:1rem; margin-bottom:0.6rem;">Synthèse ROI du Plan d'Actions</p>
            <div style="display:flex; gap:2rem; flex-wrap:wrap;">
                <div>
                    <span style="color:{c['text_secondary']}; font-size:0.8rem;">Investissement total</span><br>
                    <span style="color:{c['warning']}; font-weight:800; font-size:1.2rem;">{format_currency(_total_invest)}</span>
                </div>
                <div>
                    <span style="color:{c['text_secondary']}; font-size:0.8rem;">Économies estimées / an</span><br>
                    <span style="color:{c['success']}; font-weight:800; font-size:1.2rem;">{format_currency(_total_saving)}</span>
                </div>
                <div>
                    <span style="color:{c['text_secondary']}; font-size:0.8rem;">ROI (retour sur investissement)</span><br>
                    <span style="color:{c['primary']}; font-weight:800; font-size:1.2rem;">{_roi_months:.1f} mois</span>
                </div>
            </div>
            <p style="color:{c['text_secondary']}; font-size:0.82rem; margin-top:0.7rem; margin-bottom:0;">
                L'investissement est récupéré en <strong style="color:{c['text_primary']};">{_roi_months:.1f} mois</strong>.
                Ratio bénéfice/coût : <strong style="color:{c['success']};">{_total_saving/_total_invest:.1f}x</strong> par an.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aucune donnée d'arrêt disponible pour construire le PAP.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.text_area(
        "Commentaire du contrôleur de gestion",
        placeholder="Ajoutez vos observations, validations ou ajustements au plan d'actions...",
        height=100,
        key="pap_controller_comment",
    )

# Footer
render_footer(c)
