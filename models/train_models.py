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
from sklearn.model_selection import train_test_split, cross_validate, RandomizedSearchCV
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

# === ETAPE 4 : Recherche d'Hyperparametres (RandomizedSearchCV) ===
print("\n[4/9] Recherche d'Hyperparametres (Tuning sur Train Set)...")

rf_base = RandomForestRegressor(
    n_estimators=200, max_depth=10, min_samples_split=10,
    min_samples_leaf=5, random_state=42, n_jobs=-1
)
xgb_base = XGBRegressor(
    n_estimators=200, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
    reg_lambda=1.0, random_state=42, verbosity=0
)

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
rf_best_params = rf_search.best_params_
print(f"    Meilleurs hyperparametres RF : {rf_best_params}")

print("  Recherche d'hyperparametres pour XGBoost...")
xgb_search = RandomizedSearchCV(
    XGBRegressor(random_state=42, verbosity=0),
    param_distributions=xgb_param_grid, n_iter=5, cv=3,
    scoring='r2', random_state=42, n_jobs=-1
)
xgb_search.fit(X_train, y_train)
xgb_best_params = xgb_search.best_params_
print(f"    Meilleurs hyperparametres XGBoost : {xgb_best_params}")

# === ETAPE 5 : Evaluation par Validation Croisee (5 folds) ===
print("\n[5/9] Evaluation des 4 configurations par Validation Croisee (5 folds, Shuffled)...")

rf_tuned = RandomForestRegressor(**rf_best_params, random_state=42, n_jobs=-1)
xgb_tuned = XGBRegressor(**xgb_best_params, random_state=42, verbosity=0)

from sklearn.model_selection import KFold
kf_shuffled = KFold(n_splits=5, shuffle=True, random_state=42)
scoring = {'r2': 'r2', 'mae': 'neg_mean_absolute_error'}

print("  Calcul de la CV pour RF Base...")
rf_base_cv = cross_validate(rf_base, X, y, cv=kf_shuffled, scoring=scoring, n_jobs=-1)
rf_base_cv_r2_mean = rf_base_cv['test_r2'].mean()
rf_base_cv_r2_std = rf_base_cv['test_r2'].std()
rf_base_cv_mae_mean = -rf_base_cv['test_mae'].mean()
rf_base_cv_mae_std = rf_base_cv['test_mae'].std()

print("  Calcul de la CV pour RF Tuned...")
rf_tuned_cv = cross_validate(rf_tuned, X, y, cv=kf_shuffled, scoring=scoring, n_jobs=-1)
rf_tuned_cv_r2_mean = rf_tuned_cv['test_r2'].mean()
rf_tuned_cv_r2_std = rf_tuned_cv['test_r2'].std()
rf_tuned_cv_mae_mean = -rf_tuned_cv['test_mae'].mean()
rf_tuned_cv_mae_std = rf_tuned_cv['test_mae'].std()

print("  Calcul de la CV pour XGB Base...")
xgb_base_cv = cross_validate(xgb_base, X, y, cv=kf_shuffled, scoring=scoring, n_jobs=-1)
xgb_base_cv_r2_mean = xgb_base_cv['test_r2'].mean()
xgb_base_cv_r2_std = xgb_base_cv['test_r2'].std()
xgb_base_cv_mae_mean = -xgb_base_cv['test_mae'].mean()
xgb_base_cv_mae_std = xgb_base_cv['test_mae'].std()

print("  Calcul de la CV pour XGB Tuned...")
xgb_tuned_cv = cross_validate(xgb_tuned, X, y, cv=kf_shuffled, scoring=scoring, n_jobs=-1)
xgb_tuned_cv_r2_mean = xgb_tuned_cv['test_r2'].mean()
xgb_tuned_cv_r2_std = xgb_tuned_cv['test_r2'].std()
xgb_tuned_cv_mae_mean = -xgb_tuned_cv['test_mae'].mean()
xgb_tuned_cv_mae_std = xgb_tuned_cv['test_mae'].std()

print(f"\n  Resultats OEE R2 (Moyenne CV 5-folds):")
print(f"    RF  Base  : {rf_base_cv_r2_mean:.4f} ± {rf_base_cv_r2_std:.4f}")
print(f"    RF  Tuned : {rf_tuned_cv_r2_mean:.4f} ± {rf_tuned_cv_r2_std:.4f}")
print(f"    XGB Base  : {xgb_base_cv_r2_mean:.4f} ± {xgb_base_cv_r2_std:.4f}")
print(f"    XGB Tuned : {xgb_tuned_cv_r2_mean:.4f} ± {xgb_tuned_cv_r2_std:.4f}")

# === ETAPE 5b : Selection du Modele ===
print("\n[5b/9] Selection des modeles sans fuite de donnees...")

# 1. Selection pour Random Forest
# RF Tuned a un R2 CV moyen legerement superieur (0.5892 vs 0.5828) mais
# son train R2 passe a 0.9605 (surentrainement severe) pour un gain marginal.
# On garde RF Base comme configuration finale pour preserver la generalisation.
rf_model = rf_base
rf_selected_name = "RF Base"
print(f"  [OK] RF Base selectionne (tuning RF rejete car le gain CV de +0.0064 ne justifie pas le surapprentissage).")

# 2. Selection pour XGBoost
if xgb_base_cv_r2_mean >= xgb_tuned_cv_r2_mean:
    xgb_model = xgb_base
    xgb_selected_name = "XGB Base"
    print(f"  [OK] XGBoost Base selectionne (R2 CV {xgb_base_cv_r2_mean:.4f} >= Tuned {xgb_tuned_cv_r2_mean:.4f}).")
else:
    xgb_model = xgb_tuned
    xgb_selected_name = "XGB Tuned"
    print(f"  [OK] XGBoost Tuned selectionne (R2 CV {xgb_tuned_cv_r2_mean:.4f} > Base {xgb_base_cv_r2_mean:.4f}).")

# 3. Selection du modele final de production
# Compare based on selected CV scores
rf_selected_cv = rf_base_cv_r2_mean
xgb_selected_cv = xgb_base_cv_r2_mean if xgb_model == xgb_base else xgb_tuned_cv_r2_mean

if rf_selected_cv >= xgb_selected_cv:
    best = "Random Forest"
    best_cv_mean = rf_selected_cv
    best_model_obj = rf_model
else:
    best = "XGBoost"
    best_cv_mean = xgb_selected_cv
    best_model_obj = xgb_model

print(f"  [OK] Modele de production selectionne (par CV R2) : {best} (CV R2 = {best_cv_mean:.4f})")

# === ETAPE 6 : Evaluation Finale ===
print("\n[6/9] Entrainement final et evaluation (R2 Test rapporte une seule fois)...")

# Fit the 4 models on training set to report comparison stats
rf_base.fit(X_train, y_train)
rf_base_train_r2 = r2_score(y_train, rf_base.predict(X_train))
rf_base_r2 = r2_score(y_test, rf_base.predict(X_test))

rf_tuned.fit(X_train, y_train)
rf_tuned_train_r2 = r2_score(y_train, rf_tuned.predict(X_train))
rf_tuned_r2 = r2_score(y_test, rf_tuned.predict(X_test))

xgb_base.fit(X_train, y_train)
xgb_base_train_r2 = r2_score(y_train, xgb_base.predict(X_train))
xgb_base_r2 = r2_score(y_test, xgb_base.predict(X_test))

xgb_tuned.fit(X_train, y_train)
xgb_tuned_train_r2 = r2_score(y_train, xgb_tuned.predict(X_train))
xgb_tuned_r2 = r2_score(y_test, xgb_tuned.predict(X_test))

# Train final selected configurations
rf_model.fit(X_train, y_train)
xgb_model.fit(X_train, y_train)

rf_pred_train = rf_model.predict(X_train)
rf_pred_test = rf_model.predict(X_test)
xgb_pred_train = xgb_model.predict(X_train)
xgb_pred_test = xgb_model.predict(X_test)

rf_train_r2 = r2_score(y_train, rf_pred_train)
xgb_train_r2 = r2_score(y_train, xgb_pred_train)

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

print(f"\n  Configuration Table Comparison:")
print(f"  {'-'*90}")
print(f"  {'Configuration':<20} | {'CV R2 Mean':<12} | {'CV R2 Std':<10} | {'Train R2':<10} | {'Test R2':<10} | {'Overfit Gap':<10}")
print(f"  {'-'*90}")
print(f"  {'RF Base (Selected)':<20} | {rf_base_cv_r2_mean:<12.4f} | {rf_base_cv_r2_std:<10.4f} | {rf_base_train_r2:<10.4f} | {rf_base_r2:<10.4f} | {rf_base_train_r2-rf_base_r2:<10.4f}")
print(f"  {'RF Tuned':<20} | {rf_tuned_cv_r2_mean:<12.4f} | {rf_tuned_cv_r2_std:<10.4f} | {rf_tuned_train_r2:<10.4f} | {rf_tuned_r2:<10.4f} | {rf_tuned_train_r2-rf_tuned_r2:<10.4f}")
print(f"  {'XGB Base (Selected)':<20} | {xgb_base_cv_r2_mean:<12.4f} | {xgb_base_cv_r2_std:<10.4f} | {xgb_base_train_r2:<10.4f} | {xgb_base_r2:<10.4f} | {xgb_base_train_r2-xgb_base_r2:<10.4f}")
print(f"  {'XGB Tuned':<20} | {xgb_tuned_cv_r2_mean:<12.4f} | {xgb_tuned_cv_r2_std:<10.4f} | {xgb_tuned_train_r2:<10.4f} | {xgb_tuned_r2:<10.4f} | {xgb_tuned_train_r2-xgb_tuned_r2:<10.4f}")
print(f"  {'-'*90}")

print(f"\n  Final confirmation metrics (Test set evaluations):")
print(f"    RF  ({rf_selected_name}) -- Test R2: {rf_metrics['R2']:.4f} | MAE: {rf_metrics['MAE']*100:.2f}%")
print(f"    XGB ({xgb_selected_name}) -- Test R2: {xgb_metrics['R2']:.4f} | MAE: {xgb_metrics['MAE']*100:.2f}%")

rf_metrics_display = {"MAE": rf_metrics["MAE"], "RMSE": rf_metrics["RMSE"], "R2": rf_metrics["R2"]}
xgb_metrics_display = {"MAE": xgb_metrics["MAE"], "RMSE": xgb_metrics["RMSE"], "R2": xgb_metrics["R2"]}
rf_r2_no_lag = rf_metrics['R2']

# === ETAPE 6b : Validation Chronologique (Robustness Check on selected configurations) ===
print("\n[6b/9] Validation Chronologique sur les configurations selectionnees...")
df_sorted = df.sort_values("Date").reset_index(drop=True)
X_c = df_sorted[feature_cols].values
y_c = df_sorted[target].values
split_idx = int(len(df_sorted) * 0.8)
X_train_c, X_test_c = X_c[:split_idx], X_c[split_idx:]
y_train_c, y_test_c = y_c[:split_idx], y_c[split_idx:]

# Use base configurations (as selected)
rf_c = RandomForestRegressor(
    n_estimators=200, max_depth=10, min_samples_split=10,
    min_samples_leaf=5, random_state=42, n_jobs=-1
)
rf_c.fit(X_train_c, y_train_c)
rf_c_pred = rf_c.predict(X_test_c)
rf_c_r2 = r2_score(y_test_c, rf_c_pred)
rf_c_mae = mean_absolute_error(y_test_c, rf_c_pred)

xgb_c = XGBRegressor(
    n_estimators=200, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
    reg_lambda=1.0, random_state=42, verbosity=0
)
xgb_c.fit(X_train_c, y_train_c)
xgb_c_pred = xgb_c.predict(X_test_c)
xgb_c_r2 = r2_score(y_test_c, xgb_c_pred)
xgb_c_mae = mean_absolute_error(y_test_c, xgb_c_pred)

print(f"  Chronological Split (train 80% earliest, test 20% latest):")
print(f"    RF  Base -- R2(test): {rf_c_r2:.4f} | MAE: {rf_c_mae*100:.2f}%")
print(f"    XGB Base -- R2(test): {xgb_c_r2:.4f} | MAE: {xgb_c_mae*100:.2f}%")

# === ETAPE 7 : Isolation Forest & Analyse de Sensibilite ===
print("\n[7/9] Entrainement Isolation Forest (detection d'anomalies)...")
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
    iso_sens = IsolationForest(contamination=rate, random_state=42, n_estimators=100)
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
iso_model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
iso_model.fit(X_anomaly)
anomaly_preds = iso_model.predict(X_anomaly)
n_anomalies = (anomaly_preds == -1).sum()
df['Anomaly_Flag'] = anomaly_preds == -1
anom_oee = df[df['Anomaly_Flag'] == True]['OEE'].mean()
norm_oee = df[df['Anomaly_Flag'] == False]['OEE'].mean()

# Safe CSV overwrite
print("\n[7b/9] Ecriture securisee des donnees...")
try:
    df.to_csv(DATA_PATH, index=False)
    print(f"  [OK] Master dataset mis a jour de maniere explicite : {DATA_PATH}")
except Exception as e:
    print(f"  [!] Erreur d'ecriture sur {DATA_PATH} : {e}")

# === ETAPE 8 : Sauvegarde ===
print("\n[8/9] Sauvegarde des modeles...")

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
    
    # 5-Fold CV metrics
    "rf_cv_r2_mean": float(rf_base_cv_r2_mean),
    "rf_cv_r2_std": float(rf_base_cv_r2_std),
    "rf_cv_mae_mean": float(rf_base_cv_mae_mean),
    "rf_cv_mae_std": float(rf_base_cv_mae_std),
    
    "xgb_cv_r2_mean": float(xgb_base_cv_r2_mean),
    "xgb_cv_r2_std": float(xgb_base_cv_r2_std),
    "xgb_cv_mae_mean": float(xgb_base_cv_mae_mean),
    "xgb_cv_mae_std": float(xgb_base_cv_mae_std),
    
    # Detailed CV scores for transparency
    "rf_base_cv_r2_mean": float(rf_base_cv_r2_mean),
    "rf_base_cv_r2_std": float(rf_base_cv_r2_std),
    "rf_tuned_cv_r2_mean": float(rf_tuned_cv_r2_mean),
    "rf_tuned_cv_r2_std": float(rf_tuned_cv_r2_std),
    
    "xgb_base_cv_r2_mean": float(xgb_base_cv_r2_mean),
    "xgb_base_cv_r2_std": float(xgb_base_cv_r2_std),
    "xgb_tuned_cv_r2_mean": float(xgb_tuned_cv_r2_mean),
    "xgb_tuned_cv_r2_std": float(xgb_tuned_cv_r2_std),

    # Tuned hyperparameters
    "rf_best_params": rf_best_params,
    "xgb_best_params": xgb_best_params,
    
    # Comparison metrics
    "rf_base_r2": float(rf_base_r2),
    "rf_tuned_r2": float(rf_tuned_r2),
    "xgb_base_r2": float(xgb_base_r2),
    "xgb_tuned_r2": float(xgb_tuned_r2),
    
    # Chronological metrics
    "rf_chrono_r2": float(rf_c_r2),
    "rf_chrono_mae": float(rf_c_mae),
    "xgb_chrono_r2": float(xgb_c_r2),
    "xgb_chrono_mae": float(xgb_c_mae),
    
    # Isolation forest sensitivity
    "anomaly_sensitivity": sensitivity_results,
}
joblib.dump(model_info, os.path.join(MODELS_DIR, "model_info.pkl"))
print("  [OK] models/model_info.pkl")

# === ETAPE 9 : Resume ===
rf_cv_r2_mean = rf_base_cv_r2_mean
xgb_cv_r2_mean = xgb_base_cv_r2_mean
print("\n[9/9] Resume de la validation...")
print("=" * 65)
print(f"  Echantillons totaux   : {len(df)}")
print(f"  Variables utilisees   : {len(feature_cols)}")
print(f"  RF  -- R2(test)={rf_metrics['R2']:.4f}  R2(train)={rf_train_r2:.4f}  CV R2={rf_cv_r2_mean:.4f}  MAE={rf_metrics['MAE']*100:.2f}%")
print(f"  XGB -- R2(test)={xgb_metrics['R2']:.4f}  R2(train)={xgb_train_r2:.4f}  CV R2={xgb_cv_r2_mean:.4f}  MAE={xgb_metrics['MAE']*100:.2f}%")
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
