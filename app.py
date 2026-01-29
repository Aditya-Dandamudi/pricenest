import streamlit as st
import joblib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

# --- 1. LOAD MODEL & DATA ---
model = joblib.load('price_nest_model.joblib')
features = joblib.load('model_features.joblib')

# Load shoreline for real-time distance calculation
# (Make sure this path matches your folder structure)
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

@st.cache_resource
def load_spatial_data():
    shoreline = gpd.read_file(SHORELINE_PATH).to_crs(CRS_PROJ)
    # Simplify for speed in the web app
    shore_geom = shoreline.geometry.union_all().simplify(500)
    
    cities_data = {
        "lat": [37.7749, 34.0522, 32.7157, 37.3382],
        "lon": [-122.4194, -118.2437, -117.1611, -121.8863]
    }
    cities = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]),
        crs=CRS_LATLON
    ).to_crs(CRS_PROJ)
    return shore_geom, cities

shore_geom, cities_gdf = load_spatial_data()

# --- 2. UI LAYOUT ---
st.set_page_config(layout="wide")
st.title("🏠 PriceNest Interactive CA Predictor")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Click a Location in California")
    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)
    map_data = st_folium(m, height=400, width=600)
    
    # Defaults
    lat, lon = 34.0522, -118.2437 # LA Default
    
    if map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.write(f"Selected: {lat:.4f}, {lon:.4f}")

with col2:
    st.subheader("2. Adjust Local Metrics")
    income = st.slider("Median Household Income ($)", 20000, 250000, 85000)
    age = st.slider("Median House Age (Years)", 1, 100, 30)
    pop = st.number_input("Tract Population", value=4000)
    units = st.number_input("Housing Units", value=1200)
    density = pop / (units / 500) # Simple density proxy if unknown

# --- 3. SPATIAL MATH & PREDICTION ---
if st.button("Calculate Value for This Spot"):
    # Convert click to meters
    p = gpd.GeoSeries([Point(lon, lat)], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
    
    # Calculate Distances
    d_coast = shore_geom.distance(p) / 1000
    d_city = cities_gdf.distance(p).min() / 1000
    
    st.write(f"📏 Distance to Coast: {d_coast:.1f} km")
    st.write(f"🏙️ Distance to nearest City: {d_city:.1f} km")

    # Predict
    input_df = pd.DataFrame([[
        income, age, pop, units, density, d_coast, d_city
    ]], columns=features)
    
    prediction = model.predict(input_df)[0]
    st.metric("Estimated Median Value", f"${prediction:,.2f}")








