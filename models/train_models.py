"""
SmartAudit — Script d'entrainement des modeles ML.
Entraine Random Forest, XGBoost et Isolation Forest pour la prediction OEE.
"""

import os
import sys
import io
import warnings
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings("ignore")

# -- Chemins --
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "production_data.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

print("=" * 65)
print("  SmartAudit — Entrainement des Modeles ML")
print("=" * 65)

# === ETAPE 1 : Chargement des donnees ===
print("\n[1/9] Chargement des donnees...")
df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
print(f"  [OK] {df.shape[0]} lignes x {df.shape[1]} colonnes chargees")

# Add Month column if missing
if 'Month' not in df.columns:
    df['Month'] = df['Date'].dt.month

# === ETAPE 2 : Definition des variables ===
print("\n[2/9] Selection des variables...")

# Colonnes categorielles a encoder
cat_cols = ["Shift_Type", "Production_Line", "Product_Complexity",
            "Day_of_Week", "Training_Day_Flag", "Supervisor_Present"]

# Colonnes numeriques pour la prediction OEE
# ── VARIABLES INTERDITES — Fuite de données (data leakage) ──────
# À exclure : Previous_Shift_OEE, Rolling_7Day_OEE_Avg, Rolling_3Shift_OEE_Avg,
#             OEE_Trend_Direction, ou toute colonne dérivée de l'OEE.
# Ces colonnes sont des proxies de la cible : elles gonflent artificiellement le R².
# Seuls les indicateurs avancés réels (paramètres machine, shift, opérateurs,
# données environnementales) sont admis comme prédicteurs.
num_features = [
    "Batch_Size", "Changeover_Time", "Unplanned_Downtime",
    "Machine_Age_Years", "Last_Maintenance_Days_Ago",
    "Workforce_Attendance_Rate", "Workforce_Team_Size",
    "Equipment_Temperature_Celsius", "Material_Quality_Score",
    "Consecutive_Shifts_No_Maintenance", "Month",
]

target = "OEE"

# === ETAPE 3 : Pretraitement ===
print("\n[3/9] Pretraitement des donnees...")

# Encodage des categorielles
encoders = {}
encoded_cat_features = []
for col in cat_cols:
    if col in df.columns:
        le = LabelEncoder()
        col_encoded = f"{col}_encoded"
        df[col_encoded] = le.fit_transform(df[col].astype(str).fillna("Unknown"))
        encoders[col] = le
        encoded_cat_features.append(col_encoded)
        print(f"  [OK] {col} -> {col_encoded} ({len(le.classes_)} classes)")

# Construction de la liste finale des features
feature_cols = encoded_cat_features + [f for f in num_features if f in df.columns]
print(f"  [OK] {len(feature_cols)} features selectionnees")

# Gestion des valeurs manquantes
for col in feature_cols:
    if col in df.columns and df[col].isnull().any():
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        print(f"  [!] {col}: NaN remplaces par {median_val:.2f}")

# Verification de la cible
df = df.dropna(subset=[target])

X = df[feature_cols].values
y = df[target].values

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"  [OK] Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

# === Detect lightweight mode (Streamlit Cloud has ~1GB RAM) ===
LIGHTWEIGHT = os.environ.get("STREAMLIT_SHARING_MODE") or os.path.exists("/mount/src")

# === ETAPE 4 : Entrainement des modeles ===
rf_model = RandomForestRegressor(
    n_estimators=200, max_depth=10, min_samples_split=10,
    min_samples_leaf=5, random_state=42, n_jobs=1
)
xgb_model = XGBRegressor(
    n_estimators=200, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
    reg_lambda=1.0, random_state=42, verbosity=0, n_jobs=1
)

if LIGHTWEIGHT:
    print("\n[4/7] Mode leger (cloud) — entrainement direct sans tuning...")
    rf_model.fit(X_train, y_train)
    xgb_model.fit(X_train, y_train)
else:
    from sklearn.model_selection import cross_validate, RandomizedSearchCV, KFold
    print("\n[4/9] Recherche d'Hyperparametres (Tuning sur Train Set)...")

    rf_param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [8, 10, 12, None],
        'min_samples_split': [5, 10, 15],
        'min_samples_leaf': [2, 5, 10]
    }
    xgb_param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9]
    }

    print("  Recherche d'hyperparametres pour Random Forest...")
    rf_search = RandomizedSearchCV(
        RandomForestRegressor(random_state=42, n_jobs=-1),
        param_distributions=rf_param_grid, n_iter=5, cv=3,
        scoring='r2', random_state=42, n_jobs=-1
    )
    rf_search.fit(X_train, y_train)
    print(f"    Meilleurs hyperparametres RF : {rf_search.best_params_}")

    print("  Recherche d'hyperparametres pour XGBoost...")
    xgb_search = RandomizedSearchCV(
        XGBRegressor(random_state=42, verbosity=0),
        param_distributions=xgb_param_grid, n_iter=5, cv=3,
        scoring='r2', random_state=42, n_jobs=-1
    )
    xgb_search.fit(X_train, y_train)
    print(f"    Meilleurs hyperparametres XGBoost : {xgb_search.best_params_}")

    # Cross-validation
    print("\n[5/9] Validation Croisee (5 folds)...")
    kf_shuffled = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring_dict = {'r2': 'r2', 'mae': 'neg_mean_absolute_error'}

    rf_base_cv = cross_validate(rf_model, X, y, cv=kf_shuffled, scoring=scoring_dict, n_jobs=-1)
    xgb_base_cv = cross_validate(xgb_model, X, y, cv=kf_shuffled, scoring=scoring_dict, n_jobs=-1)

    print(f"    RF  Base  : R2 = {rf_base_cv['test_r2'].mean():.4f} +/- {rf_base_cv['test_r2'].std():.4f}")
    print(f"    XGB Base  : R2 = {xgb_base_cv['test_r2'].mean():.4f} +/- {xgb_base_cv['test_r2'].std():.4f}")

    # Train final
    rf_model.fit(X_train, y_train)
    xgb_model.fit(X_train, y_train)

# === Evaluation finale ===
step = "5/7" if LIGHTWEIGHT else "6/9"
print(f"\n[{step}] Evaluation finale...")

rf_pred_test = rf_model.predict(X_test)
xgb_pred_test = xgb_model.predict(X_test)

rf_train_r2 = r2_score(y_train, rf_model.predict(X_train))
xgb_train_r2 = r2_score(y_train, xgb_model.predict(X_train))

rf_metrics = {
    "MAE": mean_absolute_error(y_test, rf_pred_test),
    "RMSE": np.sqrt(mean_squared_error(y_test, rf_pred_test)),
    "R2": r2_score(y_test, rf_pred_test),
}
xgb_metrics = {
    "MAE": mean_absolute_error(y_test, xgb_pred_test),
    "RMSE": np.sqrt(mean_squared_error(y_test, xgb_pred_test)),
    "R2": r2_score(y_test, xgb_pred_test),
}

best = "Random Forest" if rf_metrics["R2"] >= xgb_metrics["R2"] else "XGBoost"
print(f"    RF  -- R2(test): {rf_metrics['R2']:.4f} | MAE: {rf_metrics['MAE']*100:.2f}%")
print(f"    XGB -- R2(test): {xgb_metrics['R2']:.4f} | MAE: {xgb_metrics['MAE']*100:.2f}%")
print(f"    Modele selectionne : {best}")

rf_metrics_display = rf_metrics
xgb_metrics_display = xgb_metrics
rf_r2_no_lag = rf_metrics['R2']

# === Isolation Forest & Analyse de Sensibilite ===
step = "6/7" if LIGHTWEIGHT else "7/9"
print(f"\n[{step}] Entrainement Isolation Forest (detection d'anomalies)...")
anomaly_features = [
    "Unplanned_Downtime", "Changeover_Time", "Machine_Age_Years",
    "Workforce_Attendance_Rate", "Equipment_Temperature_Celsius",
    "Material_Quality_Score", "Last_Maintenance_Days_Ago",
    "Consecutive_Shifts_No_Maintenance"
]
anomaly_features = [f for f in anomaly_features if f in df.columns]
print(f"  Features used for anomalies: {anomaly_features}")

X_anomaly = df[anomaly_features].values

# Sensitivity analysis
contamination_rates = [0.03, 0.05, 0.08]
sensitivity_results = {}
for rate in contamination_rates:
    iso_sens = IsolationForest(contamination=rate, random_state=42, n_estimators=100, n_jobs=1)
    iso_sens.fit(X_anomaly)
    preds_sens = iso_sens.predict(X_anomaly)
    n_anom_sens = (preds_sens == -1).sum()
    df_temp_flag = preds_sens == -1
    avg_oee_anom = df[df_temp_flag == True]['OEE'].mean()
    avg_oee_norm = df[df_temp_flag == False]['OEE'].mean()
    gap = avg_oee_norm - avg_oee_anom
    sensitivity_results[str(rate)] = {
        "n_anomalies": int(n_anom_sens),
        "anom_oee": float(avg_oee_anom),
        "norm_oee": float(avg_oee_norm),
        "gap": float(gap)
    }
    print(f"    Contamination={rate:.2f} -> Anomalies: {n_anom_sens} ({n_anom_sens/len(df)*100:.1f}%), OEE Normal: {avg_oee_norm*100:.1f}% vs Anom: {avg_oee_anom*100:.1f}% (gap: {gap*100:.1f}pp)")

# Save production anomaly flags
iso_model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100, n_jobs=1)
iso_model.fit(X_anomaly)
anomaly_preds = iso_model.predict(X_anomaly)
n_anomalies = (anomaly_preds == -1).sum()
df['Anomaly_Flag'] = anomaly_preds == -1
anom_oee = df[df['Anomaly_Flag'] == True]['OEE'].mean()
norm_oee = df[df['Anomaly_Flag'] == False]['OEE'].mean()

# Safe CSV overwrite
print("\n  Ecriture securisee des donnees...")
try:
    df.to_csv(DATA_PATH, index=False)
    print(f"  [OK] Master dataset mis a jour de maniere explicite : {DATA_PATH}")
except Exception as e:
    print(f"  [!] Erreur d'ecriture sur {DATA_PATH} : {e}")

# === Sauvegarde ===
step = "7/7" if LIGHTWEIGHT else "8/9"
print(f"\n[{step}] Sauvegarde des modeles...")

os.makedirs(MODELS_DIR, exist_ok=True)

joblib.dump(rf_model, os.path.join(MODELS_DIR, "oee_rf_model.pkl"))
print("  [OK] models/oee_rf_model.pkl")

joblib.dump(xgb_model, os.path.join(MODELS_DIR, "oee_xgb_model.pkl"))
print("  [OK] models/oee_xgb_model.pkl")

joblib.dump(iso_model, os.path.join(MODELS_DIR, "anomaly_model.pkl"))
print("  [OK] models/anomaly_model.pkl")

joblib.dump(feature_cols, os.path.join(MODELS_DIR, "feature_names.pkl"))
print("  [OK] models/feature_names.pkl")

joblib.dump(encoders, os.path.join(MODELS_DIR, "encoders.pkl"))
print("  [OK] models/encoders.pkl")

model_info = {
    "rf_metrics": rf_metrics_display,
    "xgb_metrics": xgb_metrics_display,
    "rf_train_r2": rf_train_r2,
    "xgb_train_r2": xgb_train_r2,
    "best_model": best,
    "feature_cols": feature_cols,
    "anomaly_features": anomaly_features,
    "n_anomalies": int(n_anomalies),
    "total_samples": len(df),
    "rf_r2_no_lag": rf_r2_no_lag,
    "lightweight_mode": LIGHTWEIGHT,
    "anomaly_sensitivity": sensitivity_results,
}
joblib.dump(model_info, os.path.join(MODELS_DIR, "model_info.pkl"))
print("  [OK] models/model_info.pkl")

# === Resume ===
print("\n  Resume de la validation...")
print("=" * 65)
print(f"  Echantillons totaux   : {len(df)}")
print(f"  Variables utilisees   : {len(feature_cols)}")
print(f"  Mode                  : {'leger (cloud)' if LIGHTWEIGHT else 'complet (local)'}")
print(f"  RF  -- R2(test)={rf_metrics['R2']:.4f}  R2(train)={rf_train_r2:.4f}  MAE={rf_metrics['MAE']*100:.2f}%")
print(f"  XGB -- R2(test)={xgb_metrics['R2']:.4f}  R2(train)={xgb_train_r2:.4f}  MAE={xgb_metrics['MAE']*100:.2f}%")
print(f"  Anomalies detectees   : {n_anomalies} / {len(df)}")
print(f"  Modele selectionne    : {best}")

# Top 10 feature importances
print(f"\n  Top 10 facteurs d'influence :")
fi = rf_model.feature_importances_
sorted_idx = np.argsort(fi)[::-1][:10]
for rank, idx in enumerate(sorted_idx, 1):
    print(f"    {rank:>2}. {feature_cols[idx]:<40s} {fi[idx]:.4f}")

print("\n" + "=" * 65)
print("  Tous les modeles sont prets. Lancez : streamlit run app.py")
print("=" * 65)
