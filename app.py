import streamlit as st
import joblib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import numpy as np
import requests
import time
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PriceNest: Pro", layout="wide")
RENTCAST_API_KEY = "7082482fd5b14001910f708d36ddb5f7" 

# Paths
MODEL_PATH = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
DATASET_PATH = "data/training_dataset.geojson" 
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

# --- 2. ASSET LOADING & COMPS ENGINE ---
@st.cache_resource
def load_assets():
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
    
    # Cleaning & Calc
    avg_density = census_gdf['pop_density'].mean()
    if 'total_rooms' in census_gdf.columns and 'households' in census_gdf.columns:
        census_gdf['avg_rooms'] = census_gdf['total_rooms'] / census_gdf['households']
    else:
        census_gdf['avg_rooms'] = 5.5 
    
    # --- BUILD COMPS ENGINE (KNN) ---
    # We use these factors to find "Sister Neighborhoods"
    comp_features = ['median_income', 'median_house_age', 'pop_density']
    
    # Fill NA to prevent crashes
    census_clean = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
    
    # Scale data (normalize) so Income doesn't overpower Age
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(census_clean)
    
    # Fit Nearest Neighbors Model
    knn = NearestNeighbors(n_neighbors=5, algorithm='auto')
    knn.fit(scaled_data)
        
    shoreline = gpd.read_file(SHORELINE_PATH).to_crs(CRS_PROJ)
    shore_points = shoreline.geometry.representative_point()
    
    cities_data = {"lat": [37.7749, 34.0522, 32.7157, 37.3382], "lon": [-122.4194, -118.2437, -117.1611, -121.8863]}
    cities = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON).to_crs(CRS_PROJ)
    
    return model, features, shore_points, cities, census_gdf, avg_density, knn, scaler, census_clean

with st.spinner("Initializing Market Analysis Engine..."):
    model, features, shore_points, cities_gdf, census_gdf, STATE_AVG_DENSITY, knn_model, scaler, census_clean = load_assets()

# --- 3. NETWORK-PROOF GEOCODER ---
geolocator = Nominatim(user_agent="price_nest_comps_v1", timeout=3)

SAFE_LOCATIONS = {
    "1 grizzly way": (38.7468, -121.2137, "1 Grizzly Way, Granite Bay, CA"),
    "granite bay high": (38.7468, -121.2137, "1 Grizzly Way, Granite Bay, CA"),
    "6520 s 4th st": (38.6915, -121.4503, "6520 S 4th St, Rio Linda, CA"),
    "rio linda": (38.6915, -121.4503, "6520 S 4th St, Rio Linda, CA"),
}

def get_coordinates(search_text):
    clean_search = search_text.lower().strip()
    for key in SAFE_LOCATIONS:
        if key in clean_search:
            lat, lon, addr = SAFE_LOCATIONS[key]
            class MockLocation:
                def __init__(self, lat, lon, addr):
                    self.latitude = lat
                    self.longitude = lon
                    self.address = addr
            return MockLocation(lat, lon, addr)
    try:
        return geolocator.geocode(search_text, limit=1, country_codes='us')
    except:
        return None

# --- 4. DATA FETCHING ---
def fetch_property_details(address):
    try:
        url = "https://api.rentcast.io/v1/properties"
        params = {"address": address, "limit": 1}
        headers = {"X-Api-Key": RENTCAST_API_KEY}
        response = requests.get(url, headers=headers, params=params, timeout=2)
        data = response.json()
        if data and len(data) > 0:
            return data[0]
    except:
        pass 
    return None

# --- 5. SESSION STATE ---
if 'sqft' not in st.session_state: st.session_state['sqft'] = 1800
if 'beds' not in st.session_state: st.session_state['beds'] = 3
if 'baths' not in st.session_state: st.session_state['baths'] = 2.0
if 'last_address' not in st.session_state: st.session_state['last_address'] = ""

# --- 6. UI LAYOUT ---
st.title("🏠 PriceNest: Pro Valuation Engine")

col_search, col_details = st.columns([1, 1.2])
p_lat, p_lon = 38.75, -121.14 
tract_data = None
ready_to_predict = False
current_tract_idx = None # To track which tract we are in

with col_search:
    st.subheader("1. Location Strategy")
    search_query = st.text_input("Address:", "1 Grizzly Way, Granite Bay, CA")
    
    if search_query:
        location = get_coordinates(search_query)
        if location:
            st.success(f"📍 {location.address[:40]}...")
            p_lat = location.latitude
            p_lon = location.longitude
            ready_to_predict = True
        else:
            st.warning("Locating...")

    if ready_to_predict:
        point_geom = Point(p_lon, p_lat)
        match = census_gdf[census_gdf.contains(point_geom)]
        if not match.empty:
            tract_data = match.iloc[0]
            current_tract_idx = match.index[0]
            
            # --- AUTO-FILL LOGIC ---
            if location.address != st.session_state['last_address']:
                st.session_state['last_address'] = location.address
                api_data = fetch_property_details(location.address)
                
                if api_data:
                    if api_data.get('squareFootage'): st.session_state['sqft'] = int(api_data['squareFootage'])
                    if api_data.get('bedrooms'): st.session_state['beds'] = int(api_data['bedrooms'])
                    if api_data.get('bathrooms'): st.session_state['baths'] = float(api_data['bathrooms'])
                    st.toast("✅ Real Data Loaded", icon="🏠")
                else:
                    avg_rooms = tract_data.get('avg_rooms', 5.5)
                    st.session_state['sqft'] = int(avg_rooms * 280)
                    st.session_state['beds'] = max(2, int(avg_rooms * 0.6))
                    st.session_state['baths'] = 2.0
                    st.toast("⚠️ Using Census Defaults", icon="🤖")
                st.rerun()
        else:
            st.warning("Outside Training Area.")
            tract_data = census_gdf.mean(numeric_only=True)

with col_details:
    st.subheader("2. Property DNA")
    c1, c2, c3 = st.columns(3)
    with c1:
        sqft = st.number_input("Square Feet", 300, 10000, key='sqft')
    with c2:
        beds = st.number_input("Bedrooms", 0, 10, key='beds')
    with c3:
        baths = st.number_input("Bathrooms", 1.0, 10.0, step=0.5, key='baths')
    
    st.write("---")
    growth_col, cond_col = st.columns(2)
    with growth_col:
        growth_rate = st.slider("Market Momentum", -5, 10, 4, format="%d%%")
    with cond_col:
        condition = st.select_slider("Condition", options=["Fixer", "Avg", "Good", "Mint"], value="Avg")

# --- 7. CORE ENGINE (ML + COMPS) ---
st.divider()

if ready_to_predict and tract_data is not None:
    # A. ML PREDICTION (The Baseline)
    p_meters = gpd.GeoSeries([Point(p_lon, p_lat)], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
    d_coast = shore_points.distance(p_meters).min() / 1000
    d_city = cities_gdf.distance(p_meters).min() / 1000
    
    inc_age_ratio = tract_data['median_income'] / (tract_data['median_house_age'] + 1)
    ppl_per_unit = tract_data['population'] / (tract_data['housing_units'] + 1)
    rel_density = tract_data['pop_density'] / STATE_AVG_DENSITY

    input_vals = [
        tract_data['median_income'], tract_data['median_house_age'], 
        tract_data['population'], tract_data['housing_units'], 
        tract_data['pop_density'], d_coast, d_city,
        inc_age_ratio, ppl_per_unit, rel_density
    ]
    baseline_price = model.predict(pd.DataFrame([input_vals], columns=features))[0]

    # B. COMPS ANALYSIS (The New Feature)
    # 1. Create vector for current location
    query_vector = pd.DataFrame([tract_data[['median_income', 'median_house_age', 'pop_density']]])
    query_scaled = scaler.transform(query_vector)
    
    # 2. Find 3 Nearest Neighbors (Sister Tracts)
    # We ask for 4 because the 1st match is usually the tract itself
    distances, indices = knn_model.kneighbors(query_scaled, n_neighbors=4)
    
    neighbor_prices = []
    comp_adjustments = []
    
    st.write("### 📊 Comparable Market Analysis (Comps)")
    comp_cols = st.columns(3)
    
    # Loop through found neighbors (skip index 0 if it's identical to self)
    start_idx = 1 if indices[0][0] == current_tract_idx else 0
    
    for i in range(start_idx, start_idx + 3):
        idx = indices[0][i]
        neighbor_tract = census_gdf.iloc[idx]
        
        # Calculate a "Comparable Price" from this neighbor
        # We assume the neighbor sold for its median value, scaled to OUR size
        comp_base_val = neighbor_tract['median_house_value']
        # Adjust for size difference
        comp_price = comp_base_val * (sqft / (neighbor_tract['avg_rooms'] * 280))
        
        neighbor_prices.append(comp_price)
        
        # Display Comp Card
        with comp_cols[i-start_idx]:
            diff = comp_price - baseline_price
            color = "green" if diff > 0 else "red"
            sign = "+" if diff > 0 else ""
            
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:10px; border-radius:5px; font-size:0.9em;">
                <strong>Comp #{i-start_idx+1}</strong><br>
                Similar Neighborhood<br>
                <span style="font-size:1.2em; font-weight:bold">${comp_price:,.0f}</span><br>
                <span style="color:{color}">{sign}${abs(diff):,.0f} vs Est.</span>
            </div>
            """, unsafe_allow_html=True)

    # C. FINAL WEIGHTING
    # We blend the ML Model (70%) with the Comps Average (30%)
    avg_comp_price = np.mean(neighbor_prices)
    weighted_price = (baseline_price * 0.7) + (avg_comp_price * 0.3)
    
    # D. ADJUSTMENTS (Condition, Market)
    avg_tract_rooms = tract_data.get('avg_rooms', 5.5)
    size_ratio = sqft / (avg_tract_rooms * 275)
    size_factor = size_ratio ** 0.65 
    
    ideal_baths = beds * 0.6
    layout_factor = 1.0 + ((baths - ideal_baths) * 0.03)
    
    cond_map = {"Fixer": 0.85, "Avg": 1.0, "Good": 1.15, "Mint": 1.3}
    cond_factor = cond_map[condition]
    
    market_factor = (1 + (growth_rate/100)) ** 3 

    # Apply adjustments to the WEIGHTED price
    final_price = weighted_price * size_factor * layout_factor * cond_factor * market_factor

    # E. RENDER FINAL RESULTS
    st.divider()
    r1, r2 = st.columns([1.5, 2.5])
    
    with r1:
        st.write("#### Final Valuation")
        st.header(f"${final_price:,.0f}")
        
        # Confidence Range
        range_pct = 0.08
        if condition == "Fixer": range_pct = 0.12
        low = final_price * (1 - range_pct)
        high = final_price * (1 + range_pct)
        
        st.caption(f"Confidence Range: ${low/1e6:.2f}M - ${high/1e6:.2f}M")

    with r2:
        # Map showing the Comps
        m = folium.Map(location=[p_lat, p_lon], zoom_start=13, tiles="CartoDB positron")
        
        # Subject Property
        folium.Marker(
            [p_lat, p_lon], tooltip="Subject Property", 
            icon=folium.Icon(color="blue", icon="home")
        ).add_to(m)
        
        # Add Markers for Comps
        for i in range(start_idx, start_idx + 3):
            idx = indices[0][i]
            n_row = census_gdf.iloc[idx]
            # Use representative point for tract location
            n_geom = n_row.geometry.centroid
            folium.Marker(
                [n_geom.y, n_geom.x], 
                tooltip=f"Comp: ${neighbor_prices[i-start_idx]:,.0f}",
                icon=folium.Icon(color="gray", icon="info-sign")
            ).add_to(m)

        st_folium(m, height=250, width=None)

else:
    st.info("👈 Enter an address to start the Comparable Market Analysis.")
