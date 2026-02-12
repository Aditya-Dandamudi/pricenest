import pandas as pd
import geopandas as gpd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# SETTINGS & PATHS---
DATA_PATH = "data/training_dataset.geojson"
MODEL_SAVE_PATH = "price_nest_model.joblib"
FEATURES_SAVE_PATH = "model_features.joblib"

def train_model():
    print("🚀 Loading and preparing data...")
    gdf = gpd.read_file(DATA_PATH)

    # DATA CLEANING: OUTLIER REMOVAL 
    lower_limit = gdf['median_home_value'].quantile(0.01)
    upper_limit = gdf['median_home_value'].quantile(0.99)
    
    gdf = gdf[(gdf['median_home_value'] >= lower_limit) & 
              (gdf['median_home_value'] <= upper_limit)].copy()
    
    print(f"✅ Cleaned data: Removed prices below ${lower_limit:,.0f} and above ${upper_limit:,.0f}")

    #FEATURE ENGINEERING 
    # A. Wealth Index: Income relative to house age (Gentrification proxy)
    gdf['income_per_age'] = gdf['median_income'] / (gdf['median_house_age'] + 1)
    
    # B. Crowding Index: Population per housing unit
    gdf['persons_per_unit'] = gdf['population'] / (gdf['housing_units'] + 1)
    
    # C. Density Ratio: How this tract compares to the CA average
    gdf['relative_density'] = gdf['pop_density'] / gdf['pop_density'].mean()

    # Define the final feature set
    features = [
        "median_income", 
        "median_house_age", 
        "population", 
        "housing_units", 
        "pop_density", 
        "dist_coast_km", 
        "dist_city_km",
        "income_per_age",    # Engineered
        "persons_per_unit",  # Engineered
        "relative_density"   # Engineered
    ]

    X = gdf[features]
    y = gdf["median_home_value"]

    #TRAINING 
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"🧠 Training Random Forest on {len(X_train)} samples...")
    model = RandomForestRegressor(
        n_estimators=200, 
        max_depth=15, 
        random_state=42, 
        n_jobs=-1 # 
    )
    model.fit(X_train, y_train)

    # EVALUATION 
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)

    print(f"📊 Model Performance:")
    print(f"   - R² Score: {r2:.4f}")
    print(f"   - Mean Absolute Error: ${mae:,.2f}")

    # SAVE ASSETS
    joblib.dump(model, MODEL_SAVE_PATH)
    joblib.dump(features, FEATURES_SAVE_PATH)
    print(f"💾 Model and features saved to disk!")

if __name__ == "__main__":
    train_model()
