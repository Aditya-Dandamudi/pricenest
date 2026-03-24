from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import joblib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import numpy as np
import requests
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from contextlib import asynccontextmanager

# --- 1. CONFIGURATION ---
RENTCAST_API_KEY = "7082482fd5b14001910f708d36ddb5f7" 
MODEL_PATH = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
DATASET_PATH = "data/training_dataset.geojson" 
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

# Global variables to hold our models in memory
ml_assets = {}

# --- 2. STARTUP LOGIC (Runs once when server starts) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Booting PriceNest AI Engine...")
    
    # Load base model & data
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
    shoreline = gpd.read_file(SHORELINE_PATH).to_crs(CRS_PROJ)
    
    if 'total_rooms' in census_gdf.columns and 'households' in census_gdf.columns:
        census_gdf['avg_rooms'] = census_gdf['total_rooms'] / census_gdf['households']
    else:
        census_gdf['avg_rooms'] = 5.5 
        
    if 'median_house_value' not in census_gdf.columns:
        for alt in ['medianHouseValue', 'price', 'value']:
            if alt in census_gdf.columns:
                census_gdf['median_house_value'] = census_gdf[alt]
                break
        else:
            census_gdf['median_house_value'] = np.random.normal(600000, 150000, len(census_gdf))
    
    # Train KNN & Stacker
    comp_features = ['median_income', 'median_house_age', 'pop_density']
    census_clean = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(census_clean)
    knn_model = NearestNeighbors(n_neighbors=5, algorithm='auto').fit(scaled_data)
    
    y_true = census_gdf['median_house_value'].values
    _, indices = knn_model.kneighbors(scaled_data)
    knn_preds = np.array([census_gdf.iloc[idx[1:]]['median_house_value'].mean() for idx in indices])
    
    meta_model = LinearRegression()
    meta_model.fit(np.column_stack((knn_preds, census_clean['pop_density'])), y_true)

    # Spatial context
    shore_points = shoreline.geometry.representative_point()
    cities_data = {"lat": [37.7749, 34.0522, 32.7157, 37.3382], "lon": [-122.4194, -118.2437, -117.1611, -121.8863]}
    cities_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON).to_crs(CRS_PROJ)
    
    # Store in memory
    ml_assets.update({
        "model": model, "features": features, "shore_points": shore_points,
        "cities_gdf": cities_gdf, "census_gdf": census_gdf, 
        "STATE_AVG_DENSITY": census_gdf['pop_density'].mean(),
        "knn_model": knn_model, "scaler": scaler, "meta_model": meta_model
    })
    print("✅ AI Engine Ready!")
    yield
    ml_assets.clear()

# --- 3. FASTAPI SETUP ---
app = FastAPI(title="PriceNest API", lifespan=lifespan)

# Allow the frontend to talk to this backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

geolocator = Nominatim(user_agent="pricenest_api", timeout=5)

# --- 4. DATA SCHEMAS ---
# This defines what the frontend needs to send us
class ValuationRequest(BaseModel):
    address: str
    sqft: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    condition: str = "Avg" # Options: Fixer, Avg, Good, Mint

SAFE_LOCATIONS = {
    "1 grizzly way": (38.7468, -121.2137, "1 Grizzly Way, Granite Bay, CA", 4200, 5, 4.5),
}

# --- 5. ENDPOINTS ---
@app.get("/")
def health_check():
    return {"status": "PriceNest Stacking API is running."}

@app.post("/predict")
def predict_price(request: ValuationRequest):
    # Unpack loaded assets
    census_gdf = ml_assets["census_gdf"]
    model = ml_assets["model"]
    features = ml_assets["features"]
    shore_points = ml_assets["shore_points"]
    cities_gdf = ml_assets["cities_gdf"]
    STATE_AVG_DENSITY = ml_assets["STATE_AVG_DENSITY"]
    knn_model = ml_assets["knn_model"]
    scaler = ml_assets["scaler"]
    meta_model = ml_assets["meta_model"]

    query_low = request.address.lower().strip()
    demo_match = next((k for k in SAFE_LOCATIONS if k in query_low), None)
    
    lat, lon, formatted_address = None, None, None
    sqft, beds, baths = request.sqft, request.beds, request.baths

    # 1. GEOCODING & PROPERTY DATA
    if demo_match:
        lat, lon, formatted_address, d_sqft, d_beds, d_baths = SAFE_LOCATIONS[demo_match]
        sqft = sqft or d_sqft
        beds = beds or d_beds
        baths = baths or d_baths
    else:
        try:
            location = geolocator.geocode(request.address, limit=1, country_codes='us')
            if not location:
                raise HTTPException(status_code=404, detail="Address not found.")
            lat, lon, formatted_address = location.latitude, location.longitude, location.address
            
            # RentCast API Fallback if frontend didn't provide sqft
            if not sqft:
                clean_addr = formatted_address.split(', United States')[0].split(', USA')[0]
                res = requests.get("https://api.rentcast.io/v1/properties", 
                                   headers={"X-Api-Key": RENTCAST_API_KEY}, 
                                   params={"address": clean_addr, "limit": 1}, timeout=6)
                if res.status_code == 200 and res.json():
                    data = res.json()[0]
                    sqft = int(data.get('squareFootage', 1800))
                    beds = int(data.get('bedrooms', 3))
                    baths = float(data.get('bathrooms', 2.0))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Geocoding/API Error: {str(e)}")

    # Default fallbacks if everything fails
    sqft, beds, baths = sqft or 1800, beds or 3, baths or 2.0

    # 2. MACHINE LEARNING PREDICTION
    point = Point(lon, lat)
    match = census_gdf[census_gdf.contains(point)]
    t_data = match.iloc[0] if not match.empty else census_gdf.mean(numeric_only=True)
    
    p_m = gpd.GeoSeries([point], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
    d_c = shore_points.distance(p_m).min() / 1000
    d_v = cities_gdf.distance(p_m).min() / 1000
    
    # Layer 1: Base AI
    base_in = pd.DataFrame([[
        t_data['median_income'], t_data['median_house_age'], t_data['population'],
        t_data['housing_units'], t_data['pop_density'], d_c, d_v,
        t_data['median_income']/(t_data['median_house_age']+1),
        t_data['population']/(t_data['housing_units']+1),
        t_data['pop_density']/STATE_AVG_DENSITY
    ]], columns=features)
    p_base = float(model.predict(base_in)[0])

    # Layer 2: KNN
    q_scale = scaler.transform(pd.DataFrame([t_data[['median_income', 'median_house_age', 'pop_density']]]))
    _, idxs = knn_model.kneighbors(q_scale, n_neighbors=4)
    comps = [census_gdf.iloc[i]['median_house_value'] * (sqft/(census_gdf.iloc[i].get('avg_rooms', 5.5)*280)) for i in idxs[0][1:]]
    p_knn = float(np.mean(comps))

    # Layer 3: Stacker
    p_stacked = (p_base * 0.5) + (meta_model.predict(np.array([[p_knn, t_data['pop_density']]]))[0] * 0.5)
    
    size_ratio = (sqft / (t_data.get('avg_rooms', 5.5) * 275)) ** 0.65 
    cond_factor = {"Fixer": 0.85, "Avg": 1.0, "Good": 1.15, "Mint": 1.3}.get(request.condition, 1.0)
    
    f_price = float(p_stacked * size_ratio * cond_factor)

    # 3. RETURN JSON RESPONSE
    return {
        "status": "success",
        "location": {
            "address": formatted_address,
            "latitude": lat,
            "longitude": lon
        },
        "property_specs": {
            "sqft": sqft,
            "beds": beds,
            "baths": baths,
            "condition": request.condition
        },
        "valuation": {
            "estimated_value": round(f_price, 0),
            "confidence_low": round(f_price * 0.93, 0),
            "confidence_high": round(f_price * 1.07, 0)
        },
        "ai_breakdown": {
            "base_model_prediction": round(p_base, 0),
            "knn_comp_prediction": round(p_knn, 0),
            "tract_population_density": round(float(t_data['pop_density']), 2)
        }
    }
