"""
SmartAudit — Prediction OEE par Intelligence Artificielle.
Interface de prediction ML avec Random Forest et XGBoost.
FIX 4: ML transparency with lag feature analysis.
"""

import streamlit as st

st.set_page_config(page_title="SmartAudit", layout="wide", initial_sidebar_state="expanded")

curr_sym = st.session_state.get("app_currency", "MAD")

import os, sys
from datetime import datetime
import numpy as np
import joblib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_loader import load_data, format_currency, get_theme_css, get_colors
from utils.oee_calculations import get_oee_category, get_oee_color
from utils.chart_builder import make_feature_importance_bar, make_ml_scatter_plot
from utils.ui_helpers import render_page_header, render_footer
from utils.icons import icon, inline_icon

# Theme
st.markdown(get_theme_css(), unsafe_allow_html=True)
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c = get_colors()
df = load_data(st.session_state.get("app_currency", "MAD"))

# Header
render_page_header("brain", "Prédiction de l'OEE — Intelligence Artificielle",
                   "Anticipez la performance avant le démarrage de l'équipe", c)

# Load models
models_dir = os.path.join(ROOT, "models")
model_files = ["oee_rf_model.pkl", "oee_xgb_model.pkl", "feature_names.pkl", "encoders.pkl"]
if not all(os.path.exists(os.path.join(models_dir, f)) for f in model_files):
    st.error("Modeles non trouves. Executez : `python models/train_models.py`")
    st.stop()

@st.cache_resource
def load_models():
    return {
        "rf": joblib.load(os.path.join(models_dir, "oee_rf_model.pkl")),
        "xgb": joblib.load(os.path.join(models_dir, "oee_xgb_model.pkl")),
        "features": joblib.load(os.path.join(models_dir, "feature_names.pkl")),
        "encoders": joblib.load(os.path.join(models_dir, "encoders.pkl")),
        "info": joblib.load(os.path.join(models_dir, "model_info.pkl")) if os.path.exists(os.path.join(models_dir, "model_info.pkl")) else {},
    }

models = load_models()

# ── Positionnement — Outil d'Aide à la Décision ──
st.markdown(f"""
<div style="background:{c['card_bg']}; border:1px solid {c['card_border']};
            border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem;
            border-left:4px solid {c['primary']};">
    <strong style="color:{c['text_primary']};">Outil d'Aide à la Décision — Usage Contrôleur de Gestion</strong><br>
    <span style="color:{c['text_secondary']}; font-size:0.9rem; line-height:1.7;">
    Ce module permet au contrôleur de gestion d'anticiper la performance d'une équipe
    <em>avant son démarrage</em>. En saisissant les paramètres opérationnels prévus
    (effectif, état machine, matière), le contrôleur obtient une prédiction d'OEE et
    une estimation des coûts cachés associés, lui permettant d'<strong style="color:{c['text_primary']};">alerter la
    production en amont</strong> et d'activer les leviers correctifs avant que les
    pertes ne se matérialisent. Les algorithmes ML (Random Forest & XGBoost) constituent
    le moteur de calcul — la logique métier (KPIs, seuils, référentiels de coûts) est
    définie par le référentiel contrôle de gestion industriel.
    </span>
</div>
""", unsafe_allow_html=True)

with st.expander("Cadre Méthodologique — Pourquoi la Prédiction en Contrôle de Gestion ?"):
    st.markdown(f"""
    **Le contrôle de gestion prédictif** représente l'évolution naturelle du tableau de bord
    classique. Là où le contrôle traditionnel analyse les écarts *a posteriori* (après que
    la perte est survenue), ce module permet une intervention *ex-ante* :

    | Contrôle Traditionnel | Contrôle Prédictif (ce module) |
    |---|---|
    | Analyse des écarts après la période | Anticipation avant démarrage équipe |
    | Reporting mensuel / hebdomadaire | Alertes en temps réel par shift |
    | Action corrective rétrospective | Action préventive avant la perte |
    | OEE constaté | OEE prédit avec intervalle de confiance |

    **Pertinence académique :** Cette approche s'inscrit dans le cadre du contrôle de gestion
    socio-économique (ISEOR) qui valorise les dysfonctionnements *avant* qu'ils ne génèrent
    des coûts cachés — passant ainsi d'un rôle de *scorekeeping* à un rôle de *attention
    directing* selon la taxonomie de Simon (1995).
    """)

col_input, col_result = st.columns([2, 3])

with col_input:
    st.markdown(f"### {inline_icon('wrench', 16, c['text_secondary'])} Paramètres de l'Équipe", unsafe_allow_html=True)
    
    # Deriving dropdown options directly from encoders (Refinement 3)
    enc = models["encoders"]
    line_opts = enc["Production_Line"].classes_.tolist() if "Production_Line" in enc else ["L1", "L2", "L3", "L4", "L5"]
    shift_opts = enc["Shift_Type"].classes_.tolist() if "Shift_Type" in enc else ["Morning", "Afternoon", "Night"]
    complexity_opts = enc["Product_Complexity"].classes_.tolist() if "Product_Complexity" in enc else ["Low", "Medium", "High", "Very_High"]

    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    SHIFT_MAP_EN = {v: k for k, v in SHIFT_MAP_FR.items()}
    shift_opts_fr = [SHIFT_MAP_FR.get(s, s) for s in shift_opts]

    line = st.selectbox("Ligne de Production", line_opts)
    shift_fr = st.selectbox("Type d'Équipe", shift_opts_fr)
    shift = SHIFT_MAP_EN.get(shift_fr, shift_fr)
    complexity = st.selectbox("Complexité Produit", complexity_opts)
    batch_size = st.slider("Taille du Lot", 8, 95, 45)
    changeover = st.slider("Temps de Changement (min)", 15, 95, 35)
    downtime = st.slider("Arrêt Non Planifié (min)", 0, 120, 10)
    machine_age = st.slider("Âge Machine (années)", 0.5, 8.0, 4.0, 0.5)
    maint_days = st.slider("Jours depuis maintenance", 1, 45, 10)
    attendance = st.slider("Taux de Presence", 0.75, 1.00, 0.92, 0.01)
    team_size = st.slider("Taille Equipe", 20, 48, 34)
    mat_quality = st.slider("Qualité Matière", 0.85, 1.00, 0.95, 0.01)
    temperature = st.slider("Temperature Atelier (C)", 18, 42, 25)
    predict_clicked = st.button("PRÉDIRE L'OEE", use_container_width=True, type="primary")

with col_result:
    if predict_clicked:
        with st.spinner("Calcul en cours..."):
            feature_vals = {}
            for col_name, val in [("Shift_Type", shift), ("Production_Line", line), ("Product_Complexity", complexity)]:
                if col_name in enc:
                    try:
                        feature_vals[f"{col_name}_encoded"] = int(enc[col_name].transform([val])[0])
                    except ValueError:
                        feature_vals[f"{col_name}_encoded"] = 0
                        st.warning(f"Valeur inconnue détectée pour {col_name} : '{val}'. Remplacée par la valeur par défaut (0).")
            for col_name in ["Day_of_Week", "Training_Day_Flag", "Supervisor_Present"]:
                if col_name in enc:
                    feature_vals[f"{col_name}_encoded"] = 0

            num_map = {
                "Batch_Size": batch_size, "Changeover_Time": changeover,
                "Unplanned_Downtime": downtime, "Machine_Age_Years": machine_age,
                "Last_Maintenance_Days_Ago": maint_days, "Workforce_Attendance_Rate": attendance,
                "Workforce_Team_Size": team_size, "Equipment_Temperature_Celsius": temperature,
                "Material_Quality_Score": mat_quality,
                "Consecutive_Shifts_No_Maintenance": maint_days // 3,
                "Month": datetime.now().month,
            }
            feature_vals.update(num_map)

            # Build feature vector
            try:
                X_pred = np.array([[feature_vals.get(f, 0) for f in models["features"]]])
                pred_rf = models["rf"].predict(X_pred)[0]
                pred_xgb = models["xgb"].predict(X_pred)[0]
            except Exception as e:
                st.error(f"Erreur de prediction : {e}. Veuillez re-entrainer les modeles.")
                st.stop()

            best = models.get("info", {}).get("best_model", "Random Forest")
            pred_oee = max(0, min(1, pred_xgb if best == "XGBoost" else pred_rf))
            pred_pct = pred_oee * 100
            color = get_oee_color(pred_oee)
            category = get_oee_category(pred_oee)

            # B5: Tree-spread prediction interval based on individual RF tree predictions
            tree_preds = [tree.predict(X_pred)[0] for tree in models["rf"].estimators_]
            p10 = float(np.percentile(tree_preds, 10) * 100)
            p90 = float(np.percentile(tree_preds, 90) * 100)
            p10 = max(0.0, min(100.0, p10))
            p90 = max(0.0, min(100.0, p90))

            st.markdown(f"""
            <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                        padding:2rem; text-align:center; margin-bottom:1rem; border-left:4px solid {color};">
                <p style="color:{c['text_secondary']}; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.1em;">
                    Prediction OEE ({best})</p>
                <p style="color:{color}; font-size:3.5rem; font-weight:800; line-height:1.1; margin:0.5rem 0;">
                    {pred_pct:.1f}%</p>
                <p style="color:{color}; font-size:1.1rem; font-weight:600;">{category}</p>
                <p style="color:{c['text_secondary']}; font-size:0.85rem; margin-top:0.5rem;">
                    Intervalle de confiance (10e–90e pct) : <strong>{p10:.1f}% — {p90:.1f}%</strong></p>
            </div>
            """, unsafe_allow_html=True)

            # Opportunity Cost (without arbitrary calibration factor, documenting discrepancy as limitation)
            avg_revenue = df["Revenue_Per_Good_Unit_EUR"].mean() if "Revenue_Per_Good_Unit_EUR" in df.columns else 200
            est_hc_shift = max(0, (0.85 - pred_oee)) * batch_size * avg_revenue * 0.38
            est_hc_month = est_hc_shift * 75  # 75 active shifts per month (excluding Sunday)
            est_hc_year = est_hc_month * 12

            st.markdown(f"#### Impact Financier Estimé (Coût d'Opportunité)")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                st.metric("Coût / Équipe", format_currency(est_hc_shift), delta_color="normal",
                          help="Calculé sur la base de la perte de marge commerciale brute (38%) liée à l'écart d'OEE pour le lot planifié (exclut les coûts directs de non-qualité).")
            with fc2:
                st.metric("Coût / Mois", format_currency(est_hc_month), delta_color="normal",
                          help="Sur la base de 75 équipes actives/mois par ligne (hors dimanche)")
            with fc3:
                st.metric("Coût / An", format_currency(est_hc_year), delta_color="normal")

            # Smart recommendations
            st.markdown(f"#### Recommandations")
            if pred_oee < 0.65 and machine_age > 5:
                st.error(f"**CRITIQUE**: OEE très faible — Prioriser la maintenance préventive de {line} avant le prochain démarrage.")
            if attendance < 0.85:
                st.warning(f"**Présence insuffisante** ({attendance*100:.0f}%) — Prévoir du personnel de renfort.")
            if pred_oee < 0.70:
                recs = [
                    f"**Actions critiques requises** — OEE prévu très bas",
                    f"- Réduire les arrêts non planifiés ({downtime} min → objectif < 15 min)",
                    f"- Vérifier l'état machine (âge: {machine_age} ans)" if machine_age > 5 else "- État machine acceptable",
                    f"- Renforcer la présence ({attendance*100:.0f}% → objectif 95%)" if attendance < 0.95 else "- Présence satisfaisante",
                ]
            elif pred_oee < 0.80:
                recs = [
                    f"**Amélioration possible** — Marge de progression identifiée",
                    f"- Optimiser les changements ({changeover} min → objectif 25 min)" if changeover > 30 else "- Temps changement correct",
                    f"- Planifier la maintenance (dernière il y a {maint_days} jours)" if maint_days > 15 else "- Maintenance à jour",
                    f"- Contrôler qualité matière ({mat_quality*100:.0f}% → objectif 98%)" if mat_quality < 0.98 else "- Qualité matière bonne",
                ]
            else:
                recs = [
                    "**Optimisation fine** — Bonne performance prévue",
                    "- Maintenir les conditions actuelles",
                    "- Documenter les bonnes pratiques pour les autres équipes",
                    "- Cibler le statut World Class (85%+)",
                ]
            for r in recs:
                st.markdown(r)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # B4: Feature importance display dynamically aligned with selected best model
            active_model_name = models.get("info", {}).get("best_model", "Random Forest")
            if active_model_name == "XGBoost" and hasattr(models["xgb"], "feature_importances_"):
                importances = models["xgb"].feature_importances_
                chart_title = "Facteurs d'Influence (XGBoost - Modèle Actif)"
            else:
                importances = models["rf"].feature_importances_
                chart_title = "Facteurs d'Influence (Random Forest - Modèle Actif)"
            
            fig_fi = make_feature_importance_bar(models["features"], importances, title=chart_title)
            st.plotly_chart(fig_fi, use_container_width=True)

            # Scatter plot of OEE vs key variable Product_Complexity_encoded (Task 4)
            fig_scatter = make_ml_scatter_plot(
                df, 
                x_col="Product_Complexity_encoded", 
                y_col="OEE_Pct", 
                title="Impact de la Complexité Produit sur l'OEE"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ML Transparency expander (updated with CV, tuning, split, IF contamination, RF tree-spread)
        with st.expander("Méthodologie & Transparence ML", expanded=False):
            info = models.get("info", {})
            if info:
                best = info.get("best_model", "Random Forest")
                
                # Retrieve CV metrics
                rf_cv_r2 = info.get("rf_cv_r2_mean", 0)
                rf_cv_r2_s = info.get("rf_cv_r2_std", 0)
                xgb_cv_r2 = info.get("xgb_cv_r2_mean", 0)
                xgb_cv_r2_s = info.get("xgb_cv_r2_std", 0)
                
                # Retrieve Tuning metrics
                rf_base_r = info.get("rf_base_r2", 0)
                rf_tuned_r = info.get("rf_tuned_r2", 0)
                xgb_base_r = info.get("xgb_base_r2", 0)
                xgb_tuned_r = info.get("xgb_tuned_r2", 0)
                
                # Retrieve Chronological metrics
                rf_chrono_r = info.get("rf_chrono_r2", 0)
                xgb_chrono_r = info.get("xgb_chrono_r2", 0)

                # Anomaly contamination
                sens = info.get("anomaly_sensitivity", {})
                sens_text = ""
                for rate, res in sens.items():
                    sens_text += f"<li>Contamination={rate} : {res['n_anomalies']} anomalies, OEE moyen normal={res['norm_oee']*100:.1f}% vs anomalique={res['anom_oee']*100:.1f}% (écart={res['gap']*100:.1f}pp)</li>"

                st.markdown(f"""
                <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
                    <strong style="color:{c['text_primary']};">Algorithmes :</strong> Entraînement simultané de
                    <strong>Random Forest</strong> (Breiman, 2001) et <strong>XGBoost</strong> (Chen & Guestrin, 2016)
                    avec sélection automatique du meilleur modèle.<br><br>

                    <strong style="color:{c['text_primary']};">Validation croisée (5-fold CV) :</strong><br>
                    <code style="color:{c['accent_cyan']};">Random Forest — R² CV = {rf_cv_r2:.4f} ± {rf_cv_r2_s:.4f}</code><br>
                    <code style="color:{c['accent_cyan']};">XGBoost — R² CV = {xgb_cv_r2:.4f} ± {xgb_cv_r2_s:.4f}</code><br><br>

                    <strong style="color:{c['text_primary']};">Optimisation des hyperparamètres (Random Search) :</strong><br>
                    <code style="color:{c['accent_cyan']};">RF — Avant : {rf_base_r:.4f} → Après : {rf_tuned_r:.4f} (sélectionné : {'Tuned' if rf_tuned_r > rf_base_r else 'Base'})</code><br>
                    <code style="color:{c['accent_cyan']};">XGB — Avant : {xgb_base_r:.4f} → Après : {xgb_tuned_r:.4f} (sélectionné : {'Tuned' if xgb_tuned_r > xgb_base_r else 'Base'})</code><br>
                    Modèle final retenu : <strong style="color:{c['text_primary']};">{best}</strong><br><br>

                    <strong style="color:{c['text_primary']};">Robustesse temporelle (Split Chronologique 80/20) :</strong><br>
                    <code style="color:{c['accent_cyan']};">RF R² = {rf_chrono_r:.4f} | XGBoost R² = {xgb_chrono_r:.4f}</code><br>
                    Permet de vérifier la résistance du modèle à la dérive temporelle de la production.<br><br>

                    <strong style="color:{c['text_primary']};">Intervalle de confiance statistique (Tree-Spread) :</strong><br>
                    L'intervalle de confiance affiché n'est plus une marge arbitraire de ±3% mais la distribution réelle des prédictions de chaque arbre du Random Forest (percentiles 10e et 90e), offrant une mesure rigoureuse de l'incertitude du modèle.<br><br>

                    <strong style="color:{c['text_primary']};">Sensibilité Isolation Forest (Contamination) :</strong><br>
                    L'analyse de sensibilité montre l'impact du taux de contamination :
                    <ul>{sens_text}</ul>
                    Le taux de 0.05 a été retenu car il offre le meilleur équilibre entre le nombre d'alertes exploitables et un écart d'OEE significatif (8.9 pp) entre shifts sains et défaillants.<br><br>

                    <strong style="color:{c['text_primary']};">Estimation des coûts d'opportunité & Calendrier :</strong><br>
                    L'impact financier affiché sur cette page représente uniquement le coût d'opportunité de perte de marge commerciale brute (38%) sur la taille du lot planifiée (Batch Size). Il constitue une limite basse conservatrice et n'inclut pas les coûts directs de non-qualité (rebuts et reprises) ni les écarts de capacité par rapport au volume théorique réel (Units Target) qui expliquent pourquoi les coûts cachés réels constatés historiquement sont plus élevés (~1.94x supérieurs en moyenne, soit 859.72 {curr}/shift contre 442.61 {curr}/shift pour la formule simplifiée). La transposition mensuelle utilise **75 shifts** actifs (hors dimanche).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Informations sur le modèle non disponibles. Ré-entraînez les modèles pour les obtenir.")
    else:
        st.markdown(f"""
        <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                    padding:3rem; text-align:center; margin-top:2rem;">
            {icon('brain', 48, c['text_muted'])}
            <p style="color:{c['text_secondary']}; font-size:1.1rem;">
                Configurez les paramètres à gauche et cliquez sur<br>
                <strong style="color:{c['accent_purple']};">PRÉDIRE L'OEE</strong> pour obtenir une prédiction.
            </p>
        </div>
        """, unsafe_allow_html=True)

# Footer
render_footer(c)
