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

# === Detect lightweight mode ===
# Streamlit Cloud clones repos into /mount/src/<repo>.
# Also check common env vars and whether we're inside a subprocess from Streamlit.
LIGHTWEIGHT = (
    os.path.isdir("/mount/src")
    or os.environ.get("STREAMLIT_SHARING_MODE")
    or os.environ.get("STREAMLIT_SERVER_HEADLESS")
    or os.environ.get("IS_STREAMLIT_CLOUD")
    or BASE_DIR.startswith("/mount/src")
    or os.path.exists("/home/adminuser")
)
# Convert to bool
LIGHTWEIGHT = bool(LIGHTWEIGHT)

print("=" * 65)
print("  SmartAudit — Entrainement des Modeles ML")
print("=" * 65)
print(f"  Mode : {'leger (cloud)' if LIGHTWEIGHT else 'complet (local)'}")
print(f"  BASE_DIR : {BASE_DIR}")

# === ETAPE 1 : Chargement des donnees ===
print("\n[1] Chargement des donnees...")
if not os.path.exists(DATA_PATH):
    print(f"  [ERREUR] Fichier introuvable : {DATA_PATH}")
    sys.exit(1)

df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
print(f"  [OK] {df.shape[0]} lignes x {df.shape[1]} colonnes chargees")

# Add Month column if missing
if 'Month' not in df.columns:
    df['Month'] = df['Date'].dt.month

# === ETAPE 2 : Definition des variables ===
print("\n[2] Selection des variables...")

cat_cols = ["Shift_Type", "Production_Line", "Product_Complexity",
            "Day_of_Week", "Training_Day_Flag", "Supervisor_Present"]

num_features = [
    "Batch_Size", "Changeover_Time", "Unplanned_Downtime",
    "Machine_Age_Years", "Last_Maintenance_Days_Ago",
    "Workforce_Attendance_Rate", "Workforce_Team_Size",
    "Equipment_Temperature_Celsius", "Material_Quality_Score",
    "Consecutive_Shifts_No_Maintenance", "Month",
]

target = "OEE"

# === ETAPE 3 : Pretraitement ===
print("\n[3] Pretraitement des donnees...")

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

feature_cols = encoded_cat_features + [f for f in num_features if f in df.columns]
print(f"  [OK] {len(feature_cols)} features selectionnees")

for col in feature_cols:
    if col in df.columns and df[col].isnull().any():
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)

df = df.dropna(subset=[target])

X = df[feature_cols].values
y = df[target].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"  [OK] Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

# === ETAPE 4 : Entrainement ===
# Always use n_jobs=1 to stay safe on memory-constrained environments
rf_model = RandomForestRegressor(
    n_estimators=200, max_depth=10, min_samples_split=10,
    min_samples_leaf=5, random_state=42, n_jobs=1
)
xgb_model = XGBRegressor(
    n_estimators=200, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
    reg_lambda=1.0, random_state=42, verbosity=0, n_jobs=1
)

print("\n[4] Entrainement des modeles (n_jobs=1)...")
rf_model.fit(X_train, y_train)
print("  [OK] Random Forest entraine")
xgb_model.fit(X_train, y_train)
print("  [OK] XGBoost entraine")

# === ETAPE 5 : Evaluation ===
print("\n[5] Evaluation finale...")

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

rf_r2_no_lag = rf_metrics['R2']

# === ETAPE 6 : Isolation Forest ===
print("\n[6] Entrainement Isolation Forest...")
anomaly_features = [
    "Unplanned_Downtime", "Changeover_Time", "Machine_Age_Years",
    "Workforce_Attendance_Rate", "Equipment_Temperature_Celsius",
    "Material_Quality_Score", "Last_Maintenance_Days_Ago",
    "Consecutive_Shifts_No_Maintenance"
]
anomaly_features = [f for f in anomaly_features if f in df.columns]

X_anomaly = df[anomaly_features].values

sensitivity_results = {}
for rate in [0.03, 0.05, 0.08]:
    iso_sens = IsolationForest(contamination=rate, random_state=42, n_estimators=100, n_jobs=1)
    iso_sens.fit(X_anomaly)
    preds_sens = iso_sens.predict(X_anomaly)
    n_anom_sens = (preds_sens == -1).sum()
    mask = preds_sens == -1
    avg_oee_anom = df.loc[mask, 'OEE'].mean()
    avg_oee_norm = df.loc[~mask, 'OEE'].mean()
    gap = avg_oee_norm - avg_oee_anom
    sensitivity_results[str(rate)] = {
        "n_anomalies": int(n_anom_sens),
        "anom_oee": float(avg_oee_anom),
        "norm_oee": float(avg_oee_norm),
        "gap": float(gap)
    }
    print(f"    Contamination={rate:.2f} -> {n_anom_sens} anomalies ({n_anom_sens/len(df)*100:.1f}%)")

iso_model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100, n_jobs=1)
iso_model.fit(X_anomaly)
anomaly_preds = iso_model.predict(X_anomaly)
n_anomalies = (anomaly_preds == -1).sum()
df['Anomaly_Flag'] = anomaly_preds == -1

# Update CSV with anomaly flags
try:
    df.to_csv(DATA_PATH, index=False)
    print(f"  [OK] CSV mis a jour : {DATA_PATH}")
except Exception as e:
    print(f"  [!] Erreur ecriture CSV : {e}")

# === ETAPE 7 : Sauvegarde ===
print("\n[7] Sauvegarde des modeles...")

os.makedirs(MODELS_DIR, exist_ok=True)

joblib.dump(rf_model, os.path.join(MODELS_DIR, "oee_rf_model.pkl"))
print("  [OK] oee_rf_model.pkl")

joblib.dump(xgb_model, os.path.join(MODELS_DIR, "oee_xgb_model.pkl"))
print("  [OK] oee_xgb_model.pkl")

joblib.dump(iso_model, os.path.join(MODELS_DIR, "anomaly_model.pkl"))
print("  [OK] anomaly_model.pkl")

joblib.dump(feature_cols, os.path.join(MODELS_DIR, "feature_names.pkl"))
print("  [OK] feature_names.pkl")

joblib.dump(encoders, os.path.join(MODELS_DIR, "encoders.pkl"))
print("  [OK] encoders.pkl")

model_info = {
    "rf_metrics": rf_metrics,
    "xgb_metrics": xgb_metrics,
    "rf_train_r2": rf_train_r2,
    "xgb_train_r2": xgb_train_r2,
    "best_model": best,
    "feature_cols": feature_cols,
    "anomaly_features": anomaly_features,
    "n_anomalies": int(n_anomalies),
    "total_samples": len(df),
    "rf_r2_no_lag": rf_r2_no_lag,
    "anomaly_sensitivity": sensitivity_results,
}
joblib.dump(model_info, os.path.join(MODELS_DIR, "model_info.pkl"))
print("  [OK] model_info.pkl")

# === Resume ===
print("\n" + "=" * 65)
print(f"  Echantillons  : {len(df)}")
print(f"  Features      : {len(feature_cols)}")
print(f"  RF  R2={rf_metrics['R2']:.4f}  MAE={rf_metrics['MAE']*100:.2f}%")
print(f"  XGB R2={xgb_metrics['R2']:.4f}  MAE={xgb_metrics['MAE']*100:.2f}%")
print(f"  Anomalies     : {n_anomalies} / {len(df)}")
print(f"  Selection     : {best}")
print("=" * 65)
print("  Pret. Lancez : streamlit run app.py")
print("=" * 65)
