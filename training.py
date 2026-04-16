import pandas as pd
import geopandas as gpd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error

DATA_PATH       = "data/training_dataset.geojson"
MODEL_SAVE_PATH = "price_nest_model.joblib"
FEATURES_SAVE_PATH = "model_features.joblib"

def train_model():
    print("Loading and preparing data...")
    gdf = gpd.read_file(DATA_PATH)

    # Remove bottom/top 1% to avoid extreme outliers skewing the model
    lower = gdf['median_home_value'].quantile(0.01)
    upper = gdf['median_home_value'].quantile(0.99)
    gdf = gdf[(gdf['median_home_value'] >= lower) & (gdf['median_home_value'] <= upper)].copy()
    print(f"Cleaned: kept prices ${lower:,.0f} – ${upper:,.0f} ({len(gdf):,} tracts)")

    # Feature engineering
    gdf['income_per_age']   = gdf['median_income'] / (gdf['median_house_age'] + 1)
    gdf['persons_per_unit'] = gdf['population'] / (gdf['housing_units'] + 1)
    gdf['relative_density'] = gdf['pop_density'] / gdf['pop_density'].mean()

    feature_cols = [
        "median_income",
        "median_house_age",
        "population",
        "housing_units",
        "pop_density",
        "dist_coast_km",
        "dist_city_km",
        "income_per_age",
        "persons_per_unit",
        "relative_density",
    ]

    X = gdf[feature_cols]
    y = gdf["median_home_value"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # VotingRegressor: RandomForest handles non-linear interactions well;
    # HistGradientBoosting handles mixed feature scales and is faster to train.
    # Averaging the two is more stable than either alone.
    rf = RandomForestRegressor(n_estimators=300, max_depth=15, random_state=42, n_jobs=-1)
    gb = HistGradientBoostingRegressor(max_iter=400, max_depth=8, learning_rate=0.05, random_state=42)
    model = VotingRegressor(estimators=[('rf', rf), ('gb', gb)], n_jobs=-1)

    print(f"Training VotingRegressor (RF + HistGradientBoosting) on {len(X_train):,} samples...")
    model.fit(X_train, y_train)

    # Hold-out evaluation
    preds = model.predict(X_test)
    print(f"\nHold-out performance:")
    print(f"  R²  : {r2_score(y_test, preds):.4f}")
    print(f"  MAE : ${mean_absolute_error(y_test, preds):,.0f}")

    # 3-fold cross-validation — more honest than a single split
    print("\nRunning 3-fold cross-validation (this takes a minute)...")
    cv_r2  = cross_val_score(model, X, y, cv=3, scoring='r2', n_jobs=-1)
    cv_mae = cross_val_score(model, X, y, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
    print(f"  CV R²  : {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")
    print(f"  CV MAE : ${-cv_mae.mean():,.0f} ± ${cv_mae.std():,.0f}")

    joblib.dump(model, MODEL_SAVE_PATH)
    joblib.dump(feature_cols, FEATURES_SAVE_PATH)
    print(f"\nSaved model → {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()
