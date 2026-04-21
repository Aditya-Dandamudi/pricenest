import geopandas as gpd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, ExtraTreesRegressor
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

DATA_PATH          = "data/training_dataset.geojson"
MODEL_SAVE_PATH    = "price_nest_model.joblib"
FEATURES_SAVE_PATH = "model_features.joblib"
META_SAVE_PATH     = "meta_model.joblib"
SCALER_SAVE_PATH   = "meta_scaler.joblib"

# ── Feature engineering ───────────────────────────────────────────────────────
def build_features(gdf):
    centroids   = gdf.geometry.centroid.to_crs("EPSG:4326")
    gdf = gdf.copy()
    gdf['lat']  = centroids.y
    gdf['lon']  = centroids.x

    inc = gdf['median_income']
    age = gdf['median_house_age']
    den = gdf['pop_density']
    cst = gdf['dist_coast_km']
    cit = gdf['dist_city_km']
    hu  = gdf['housing_units'].clip(lower=1)
    pop = gdf['population']

    # Existing interactions
    gdf['income_per_age']     = inc / (age + 1)
    gdf['persons_per_unit']   = pop / hu
    gdf['relative_density']   = den / den.mean()
    gdf['coast_income']       = inc / (cst + 1)
    gdf['city_density']       = den / (cit + 1)

    # Log transforms (reduce right skew)
    gdf['log_income']         = np.log1p(inc)
    gdf['log_density']        = np.log1p(den)
    gdf['log_coast']          = np.log1p(cst)
    gdf['log_city']           = np.log1p(cit)

    # Polynomial / higher-order
    gdf['income_sq']          = inc ** 2 / 1e9
    gdf['age_sq']             = age ** 2
    gdf['lat_sq']             = gdf['lat'] ** 2
    gdf['lon_sq']             = gdf['lon'] ** 2
    gdf['lat_lon']            = gdf['lat'] * gdf['lon']   # diagonal spatial interaction
    gdf['coast_sq']           = cst ** 2 / 1e4

    # Geographic context features
    gdf['coast_city_ratio']   = cit / (cst + 1)
    gdf['occupancy_pressure'] = pop / hu
    gdf['income_density']     = inc * den / 1e8            # wealth × crowding

    # Distance to premium CA metros (raw Euclidean in degrees — good enough for features)
    # Silicon Valley centroid, Beverly Hills centroid, La Jolla centroid
    gdf['dist_sv']   = np.sqrt((gdf['lat'] - 37.39)**2 + (gdf['lon'] - (-122.08))**2)
    gdf['dist_bh']   = np.sqrt((gdf['lat'] - 34.07)**2 + (gdf['lon'] - (-118.40))**2)
    gdf['dist_lj']   = np.sqrt((gdf['lat'] - 32.85)**2 + (gdf['lon'] - (-117.27))**2)
    gdf['dist_marin']= np.sqrt((gdf['lat'] - 37.95)**2 + (gdf['lon'] - (-122.53))**2)

    return gdf

FEATURE_COLS = [
    # Core census
    "median_income", "median_house_age", "population", "housing_units",
    "pop_density", "dist_coast_km", "dist_city_km",
    # Geography
    "lat", "lon", "lat_sq", "lon_sq", "lat_lon",
    # Interactions
    "income_per_age", "persons_per_unit", "relative_density",
    "coast_income", "city_density", "income_density",
    # Log transforms
    "log_income", "log_density", "log_coast", "log_city",
    # Higher-order
    "income_sq", "age_sq", "coast_sq", "coast_city_ratio", "occupancy_pressure",
    # Premium metro distances
    "dist_sv", "dist_bh", "dist_lj", "dist_marin",
]

# ── Base learners ─────────────────────────────────────────────────────────────
def make_base_learners():
    rf = RandomForestRegressor(
        n_estimators=500, max_depth=20, min_samples_leaf=2,
        max_features=0.6, random_state=42, n_jobs=-1)

    et = ExtraTreesRegressor(
        n_estimators=400, max_depth=20, min_samples_leaf=2,
        max_features=0.6, random_state=42, n_jobs=-1)

    hgb = HistGradientBoostingRegressor(
        max_iter=600, max_depth=10, learning_rate=0.03,
        min_samples_leaf=10, l2_regularization=0.1, random_state=42)

    xgb_m = xgb.XGBRegressor(
        n_estimators=700, max_depth=8, learning_rate=0.025,
        subsample=0.8, colsample_bytree=0.75, reg_alpha=0.05,
        reg_lambda=1.5, tree_method='hist', random_state=42, n_jobs=-1)

    lgb_m = lgb.LGBMRegressor(
        n_estimators=700, max_depth=9, learning_rate=0.025,
        subsample=0.8, colsample_bytree=0.75, reg_alpha=0.05,
        reg_lambda=1.5, num_leaves=63, random_state=42, n_jobs=-1,
        verbose=-1)

    return [('rf', rf), ('et', et), ('hgb', hgb), ('xgb', xgb_m), ('lgb', lgb_m)]

def train_model():
    print("Loading and preparing data...")
    gdf = gpd.read_file(DATA_PATH)

    # Clip bottom/top 0.5% — tighter than before to keep more high-value data
    lower = gdf['median_home_value'].quantile(0.005)
    upper = gdf['median_home_value'].quantile(0.995)
    gdf = gdf[(gdf['median_home_value'] >= lower) & (gdf['median_home_value'] <= upper)].copy()
    print(f"Price range: ${lower:,.0f} – ${upper:,.0f}  ({len(gdf):,} tracts)")

    gdf = build_features(gdf)
    gdf = gdf.dropna(subset=FEATURE_COLS + ['median_home_value'])
    print(f"Feature matrix: {len(gdf):,} tracts × {len(FEATURE_COLS)} features")

    X    = gdf[FEATURE_COLS].values
    y    = np.log(gdf['median_home_value'].values)   # log-transform target
    y_raw = gdf['median_home_value'].values

    learners = make_base_learners()

    # ── Out-of-fold stacking (5-fold) ─────────────────────────────────────────
    # Each base model's OOF predictions are used to train the Ridge meta-learner.
    # This prevents the meta-model from seeing in-sample predictions, which would
    # let it overfit. The result is a much better-calibrated ensemble.
    print(f"\nBuilding 5-fold OOF predictions for {len(learners)} base models...")
    kf      = KFold(n_splits=5, shuffle=True, random_state=42)
    oof     = np.zeros((len(X), len(learners)))

    for j, (name, est) in enumerate(learners):
        print(f"  [{j+1}/{len(learners)}] {name} OOF...", end=' ', flush=True)
        for tr, va in kf.split(X):
            est_clone = type(est)(**est.get_params())
            est_clone.fit(X[tr], y[tr])
            oof[va, j] = est_clone.predict(X[va])
        # OOF R² in dollar space
        oof_dollar = np.exp(oof[:, j])
        print(f"MAE ${mean_absolute_error(y_raw, oof_dollar):,.0f}")

    # Meta-learner: Ridge on OOF predictions
    meta_scaler = StandardScaler()
    oof_scaled  = meta_scaler.fit_transform(oof)
    meta        = Ridge(alpha=10.0)
    meta.fit(oof_scaled, y)
    meta_pred   = meta.predict(oof_scaled)
    meta_dollar = np.exp(meta_pred)
    print(f"\nMeta-model OOF  R²  : {r2_score(y_raw, meta_dollar):.4f}")
    print(f"Meta-model OOF  MAE : ${mean_absolute_error(y_raw, meta_dollar):,.0f}")

    # ── Retrain all base models on full data ──────────────────────────────────
    print("\nRetraining all base models on full dataset...")
    trained = []
    for name, est in learners:
        print(f"  Fitting {name}...", end=' ', flush=True)
        est.fit(X, y)
        trained.append((name, est))
        print("done")

    # ── Save ──────────────────────────────────────────────────────────────────
    joblib.dump(trained,      MODEL_SAVE_PATH)
    joblib.dump(FEATURE_COLS, FEATURES_SAVE_PATH)
    joblib.dump(meta,         META_SAVE_PATH)
    joblib.dump(meta_scaler,  SCALER_SAVE_PATH)
    print(f"\nSaved: {MODEL_SAVE_PATH}, {META_SAVE_PATH}")
    print(f"Features: {len(FEATURE_COLS)}")

if __name__ == "__main__":
    train_model()
