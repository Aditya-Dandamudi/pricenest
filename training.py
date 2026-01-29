import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import joblib


# 1. Load the dataset
print("Loading dataset...")
gdf = gpd.read_file("data/training_dataset.geojson")

# 2. Prepare Features (X) and Target (y)
# We exclude 'GEOID' and 'geometry' as they aren't predictive numbers
features = [
    "median_income", "median_house_age", "population", 
    "housing_units", "pop_density", "dist_coast_km", "dist_city_km"
]
X = gdf[features]
y = gdf["median_home_value"]

# 3. Split into Training and Testing sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train the Model
print("Training Random Forest Model...")
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# Save the trained model to a file
joblib.dump(model, 'price_nest_model.joblib')

# Save the feature names so the next script knows the exact order
joblib.dump(features, 'model_features.joblib')
print("\nModel saved successfully as 'price_nest_model.joblib'")

# 5. Evaluate
y_pred = model.predict(X_test)
print("\n--- Model Performance ---")
print(f"R² Score: {r2_score(y_test, y_pred):.4f}")
print(f"Mean Absolute Error: ${mean_absolute_error(y_test, y_pred):,.2f}")

# 6. Feature Importance (Which variable mattered most?)
importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("\n--- Feature Importance ---")
print(importances)

# 7. Quick Visualization of Prediction Accuracy
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.3)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel("Actual Value")
plt.ylabel("Predicted Value")
plt.title("Actual vs Predicted Home Values")
plt.show()