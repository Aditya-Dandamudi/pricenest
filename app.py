import streamlit as st
import joblib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import numpy as np
import random
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PriceNest: Pro", layout="wide")

# Paths
MODEL_PATH = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
DATASET_PATH = "data/training_dataset.geojson" 
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

# --- 2. ASSET LOADING ---
@st.cache_resource
def load_assets():
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
    avg_density = census_gdf['pop_density'].mean()
    
    # Calculate average rooms if missing
    if 'total_rooms' in census_gdf.columns and 'households' in census_gdf.columns:
        census_gdf['avg_rooms'] = census_gdf['total_rooms'] / census_gdf['households']
    else:
        census_gdf['avg_rooms'] = 5.5 
        
    shoreline = gpd.read_file(SHORELINE_PATH).to_crs(CRS_PROJ)
    shore_points = shoreline.geometry.representative_point()
    
    cities_data = {"lat": [37.7749, 34.0522, 32.7157, 37.3382], "lon": [-122.4194, -118.2437, -117.1611, -121.8863]}
    cities = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON).to_crs(CRS_PROJ)
    
    return model, features, shore_points, cities, census_gdf, avg_density

# Load Assets
with st.spinner("Loading System..."):
    model, features, shore_points, cities_gdf, census_gdf, STATE_AVG_DENSITY = load_assets()

geolocator = Nominatim(user_agent="price_nest_live_v4", timeout=10)

# --- 3. MOCK API (Network Free) ---
def fetch_property_details(address):
    # Fake delay
    time.sleep(0.5)
    # Deterministic random numbers
    seed_val = sum(ord(char) for char in address) 
    random.seed(seed_val)
    
    mock_beds = random.randint(2, 5)
    mock_baths = mock_beds - random.choice([0, 0.5, 1])
    if mock_baths < 1: mock_baths = 1.0
    
    return {
        "beds": mock_beds,
        "baths": mock_baths,
        "sqft": random.randint(1200, 3500),
        "year_built": random.randint(1960, 2020)
    }

# --- 4. SESSION STATE ---
if 'sqft' not in st.session_state: st.session_state['sqft'] = 1800
if 'beds' not in st.session_state: st.session_state['beds'] = 3
if 'baths' not in st.session_state: st.session_state['baths'] = 2.0
if 'last_address' not in st.session_state: st.session_state['last_address'] = ""

# --- 5. UI LAYOUT ---
st.title("🏠 PriceNest: Pro Valuation Engine")

col_search, col_details = st.columns([1, 1.2])

# Global variables to store prediction data
p_lat, p_lon = 38.75, -121.14 # Default (Granite Bay)
tract_data = None
ready_to_predict = False

with col_search:
    st.subheader("1. Location")
    search_query = st.text_input("Address:", "1 Grizzly Way, Granite Bay, CA")
    
    # GEOCODING
    if search_query:
        try:
            suggestions = geolocator.geocode(search_query, exactly_one=False, limit=3, country_codes='us')
            if suggestions:
                ca_suggestions = [s for s in suggestions if "California" in s.address]
                if ca_suggestions:
                    location = st.selectbox("Confirm Location:", options=ca_suggestions, format_func=lambda x: x.address)
                    
                    if location:
                        p_lat = location.latitude
                        p_lon = location.longitude
                        ready_to_predict = True
                        
                        # DATA AUTO-FETCH
                        if location.address != st.session_state['last_address']:
                            st.session_state['last_address'] = location.address
                            data = fetch_property_details(location.address)
                            st.session_state['sqft'] = int(data['sqft'])
                            st.session_state['beds'] = int(data['beds'])
                            st.session_state['baths'] = float(data['baths'])
                            st.rerun() # Refresh inputs immediately
        except:
            st.warning("Locating...")

    # NEIGHBORHOOD LOOKUP
    if ready_to_predict:
        point_geom = Point(p_lon, p_lat)
        match = census_gdf[census_gdf.contains(point_geom)]
        if not match.empty:
            tract_data = match.iloc[0]
            st.success("✅ Neighborhood Data Connected")
        else:
            # FALLBACK: If outside area, use average values so app DOES NOT CRASH
            st.warning("⚠️ Outside training area. Using CA averages.")
            tract_data = census_gdf.mean(numeric_only=True)

with col_details:
    st.subheader("2. House Specifics")
    c1, c2, c3 = st.columns(3)
    with c1:
        sqft = st.number_input("Square Feet", 300, 10000, key='sqft')
    with c2:
        beds = st.number_input("Bedrooms", 0, 10, key='beds')
    with c3:
        baths = st.number_input("Bathrooms", 1.0, 10.0, step=0.5, key='baths')
    condition = st.select_slider("Condition", options=["Fixer-Upper", "Average", "Updated", "Luxury"], value="Average")

# --- 6. AUTOMATIC PREDICTION (No Button Needed) ---
st.divider()

if ready_to_predict and tract_data is not None:
    # 1. Spatial Math
    p_meters = gpd.GeoSeries([Point(p_lon, p_lat)], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
    d_coast = shore_points.distance(p_meters).min() / 1000
    d_city = cities_gdf.distance(p_meters).min() / 1000
    
    # 2. Ratios
    inc_age_ratio = tract_data['median_income'] / (tract_data['median_house_age'] + 1)
    ppl_per_unit = tract_data['population'] / (tract_data['housing_units'] + 1)
    rel_density = tract_data['pop_density'] / STATE_AVG_DENSITY

    # 3. Baseline Prediction
    input_vals = [
        tract_data['median_income'], tract_data['median_house_age'], 
        tract_data['population'], tract_data['housing_units'], 
        tract_data['pop_density'], d_coast, d_city,
        inc_age_ratio, ppl_per_unit, rel_density
    ]
    baseline_price = model.predict(pd.DataFrame([input_vals], columns=features))[0]

    # 4. Individual Adjustments
    avg_tract_rooms = tract_data.get('avg_rooms', 5.5)
    estimated_avg_sqft = avg_tract_rooms * 275
    size_ratio = sqft / estimated_avg_sqft
    
    bed_factor = 1 + ((beds - 3) * 0.03) 
    bath_factor = 1 + ((baths - 2) * 0.05)
    layout_factor = bed_factor * bath_factor
    
    cond_factor = {"Fixer-Upper": 0.8, "Average": 1.0, "Updated": 1.15, "Luxury": 1.3}[condition]
    drift_factor = (1 + 0.035) ** (2026 - 2022)

    final_price = baseline_price * np.sqrt(size_ratio) * layout_factor * cond_factor * drift_factor

    # 5. RENDER RESULTS
    r1, r2 = st.columns([1, 1])
    with r1:
        st.write("### Estimated Value (2026)")
        st.header(f"${final_price:,.0f}")
        st.caption(f"Price per SqFt: ${final_price/sqft:.0f}")
    with r2:
        st.write("### Factors")
        if size_ratio > 1.0: st.success(f"Size Premium: +{int((size_ratio-1)*50)}%")
        else: st.warning(f"Size Discount: -{int((1-size_ratio)*50)}%")
        st.info(f"Condition: {cond_factor}x")

    # 6. RENDER MAP
    m = folium.Map(location=[p_lat, p_lon], zoom_start=16)
    folium.Marker(
        [p_lat, p_lon], 
        tooltip=f"${final_price:,.0f}", 
        icon=folium.Icon(color="green", icon="home")
    ).add_to(m)
    st_folium(m, height=400, width=None)

else:
    st.info("👈 Enter an address to see the valuation.")
