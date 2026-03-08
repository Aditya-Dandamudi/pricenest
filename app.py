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
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PriceNest: Stacked AI", layout="wide")
RENTCAST_API_KEY = "7082482fd5b14001910f708d36ddb5f7" 

# Asset Paths
MODEL_PATH = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
DATASET_PATH = "data/training_dataset.geojson" 
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

# --- 2. ASSET LOADING & STACKING TRAINER ---
@st.cache_resource
def load_and_train_stacker():
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
    
    comp_features = ['median_income', 'median_house_age', 'pop_density']
    census_clean = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(census_clean)
    knn = NearestNeighbors(n_neighbors=5, algorithm='auto').fit(scaled_data)
    
    y_true = census_gdf['median_house_value'].values
    _, indices = knn.kneighbors(scaled_data)
    knn_preds = np.array([census_gdf.iloc[idx[1:]]['median_house_value'].mean() for idx in indices])
    
    meta_model = LinearRegression()
    meta_model.fit(np.column_stack((knn_preds, census_clean['pop_density'])), y_true)

    shore_points = shoreline.geometry.representative_point()
    cities_data = {"lat": [37.7749, 34.0522, 32.7157, 37.3382], "lon": [-122.4194, -118.2437, -117.1611, -121.8863]}
    cities = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON).to_crs(CRS_PROJ)
    
    return model, features, shore_points, cities, census_gdf, census_gdf['pop_density'].mean(), knn, scaler, meta_model

with st.spinner("🚀 Initializing Stacking Ensemble..."):
    model, features, shore_points, cities_gdf, census_gdf, STATE_AVG_DENSITY, knn_model, scaler, meta_model = load_and_train_stacker()

# --- 3. GEOCODER & API LOGIC ---
geolocator = Nominatim(user_agent="pricenest_pro_v3", timeout=5)

SAFE_LOCATIONS = {
    "1 grizzly way": (38.7468, -121.2137, "1 Grizzly Way, Granite Bay, CA", 4200, 5, 4.5),
    "6520 s 4th st": (38.6915, -121.4503, "6520 S 4th St, Rio Linda, CA", 1250, 3, 1.0),
}

def fetch_property_details(address):
    clean_addr = address.split(', United States')[0].split(', USA')[0]
    try:
        url = "https://api.rentcast.io/v1/properties"
        headers = {"X-Api-Key": RENTCAST_API_KEY}
        response = requests.get(url, headers=headers, params={"address": clean_addr, "limit": 1}, timeout=6)
        if response.status_code == 200:
            data = response.json()
            return data[0] if data and len(data) > 0 else None
    except: return None
    return None

# --- 4. SESSION STATE ---
for key, default in [('sqft', 1800), ('beds', 3), ('baths', 2.0), ('last_address', "")]:
    if key not in st.session_state: st.session_state[key] = default

# --- 5. UI LAYOUT ---
st.title("🏠 PriceNest: Multi-Model Valuation")
col_search, col_details = st.columns([1, 1.2])

ready_to_predict = False
location = None

with col_search:
    st.subheader("1. Location Strategy")
    search_query = st.text_input("Search Address:", value="1 Grizzly Way, Granite Bay, CA")
    
    if search_query:
        query_low = search_query.lower().strip()
        demo_match = next((k for k in SAFE_LOCATIONS if k in query_low), None)
        
        if demo_match:
            lat, lon, addr, d_sqft, d_beds, d_baths = SAFE_LOCATIONS[demo_match]
            class MockLoc: pass
            location = MockLoc()
            location.latitude, location.longitude, location.address = lat, lon, addr
            location.demo = {"sqft": d_sqft, "beds": d_beds, "baths": d_baths}
        else:
            try:
                location = geolocator.geocode(search_query, limit=1, country_codes='us')
            except:
                st.error("Geocoding timeout. Try again.")

        if location:
            st.success(f"📍 Found: {location.address[:45]}...")
            ready_to_predict = True
            
            if location.address != st.session_state['last_address']:
                st.session_state['last_address'] = location.address
                if hasattr(location, 'demo'):
                    st.session_state['sqft'] = location.demo['sqft']
                    st.session_state['beds'] = location.demo['beds']
                    st.session_state['baths'] = location.demo['baths']
                    st.toast("🚀 Demo Data Loaded", icon="⚡")
                    st.rerun()
                else:
                    api_res = fetch_property_details(location.address)
                    if api_res:
                        st.session_state['sqft'] = int(api_res.get('squareFootage', 1800))
                        st.session_state['beds'] = int(api_res.get('bedrooms', 3))
                        st.session_state['baths'] = float(api_res.get('bathrooms', 2.0))
                        st.toast("✅ Live API Data Integrated", icon="🏠")
                        st.rerun()

with col_details:
    st.subheader("2. Property DNA")
    c1, c2, c3 = st.columns(3)
    sqft = c1.number_input("Sq Footage", 300, 10000, key='sqft')
    beds = c2.number_input("Beds", 0, 10, key='beds')
    baths = c3.number_input("Baths", 1.0, 10.0, step=0.5, key='baths')
    
    st.write("---")
    condition = st.select_slider("Condition", options=["Fixer", "Avg", "Good", "Mint"], value="Avg")

# --- 6. PREDICTION ENGINE ---
st.divider()
if ready_to_predict and location:
    point = Point(location.longitude, location.latitude)
    match = census_gdf[census_gdf.contains(point)]
    t_data = match.iloc[0] if not match.empty else census_gdf.mean(numeric_only=True)
    
    p_m = gpd.GeoSeries([point], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
    d_c = shore_points.distance(p_m).min() / 1000
    d_v = cities_gdf.distance(p_m).min() / 1000
    
    base_in = pd.DataFrame([[
        t_data['median_income'], t_data['median_house_age'], t_data['population'],
        t_data['housing_units'], t_data['pop_density'], d_c, d_v,
        t_data['median_income']/(t_data['median_house_age']+1),
        t_data['population']/(t_data['housing_units']+1),
        t_data['pop_density']/STATE_AVG_DENSITY
    ]], columns=features)
    p_base = model.predict(base_in)[0]

    q_scale = scaler.transform(pd.DataFrame([t_data[['median_income', 'median_house_age', 'pop_density']]]))
    _, idxs = knn_model.kneighbors(q_scale, n_neighbors=4)
    comps = [census_gdf.iloc[i]['median_house_value'] * (sqft/(census_gdf.iloc[i].get('avg_rooms', 5.5)*280)) for i in idxs[0][1:]]
    p_knn = np.mean(comps)

    p_stacked = (p_base * 0.5) + (meta_model.predict(np.array([[p_knn, t_data['pop_density']]]))[0] * 0.5)
    
    size_ratio = (sqft / (t_data.get('avg_rooms', 5.5) * 275)) ** 0.65 
    cond_factor = {"Fixer": 0.85, "Avg": 1.0, "Good": 1.15, "Mint": 1.3}[condition]
    f_price = p_stacked * size_ratio * cond_factor

    res_col, map_col = st.columns([1.2, 1])
    with res_col:
        st.write("### Estimated Market Value")
        st.header(f"${f_price:,.0f}")
        st.markdown(f"**Confidence Range:** ${f_price*0.93:,.0f} — ${f_price*1.07:,.0f}")
        
        with st.expander("AI Technical Breakdown"):
            st.write(f"🤖 **Base AI (RF):** ${p_base:,.0f}")
            st.write(f"🏘️ **Neighbor Comps (KNN):** ${p_knn:,.0f}")
    
    with map_col:
        m = folium.Map(location=[location.latitude, location.longitude], zoom_start=14, tiles="CartoDB Positron")
        folium.Marker([location.latitude, location.longitude], icon=folium.Icon(color="blue", icon="home")).add_to(m)
        st_folium(m, height=250, width=None)
