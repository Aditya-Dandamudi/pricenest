# import streamlit as st
# import joblib
# import pandas as pd
# import geopandas as gpd
# from shapely.geometry import Point
# f my God bro banquet no onerom geopy.geocoders import Nominatim
# import folium
# from streamlit_folium import st_folium
# import numpy as np
# import requests
# from sklearn.neighbors import NearestNeighbors
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import StandardScaler

# # --- 1. CONFIGURATION ---
# st.set_page_config(page_title="PriceNest: Stacked AI", layout="wide")
# RENTCAST_API_KEY = "7082482fd5b14001910f708d36ddb5f7" 

# # Asset Paths
# MODEL_PATH = 'price_nest_model.joblib'
# FEATURES_PATH = 'model_features.joblib'
# SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
# DATASET_PATH = "data/training_dataset.geojson" 
# CRS_PROJ = "EPSG:3310"
# CRS_LATLON = "EPSG:4326"

# # --- 2. ASSET LOADING & STACKING TRAINER ---
# @st.cache_resource
# def load_and_train_stacker():
#     model = joblib.load(MODEL_PATH)
#     features = joblib.load(FEATURES_PATH)
#     census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
#     shoreline = gpd.read_file(SHORELINE_PATH).to_crs(CRS_PROJ)
    
#     if 'total_rooms' in census_gdf.columns and 'households' in census_gdf.columns:
#         census_gdf['avg_rooms'] = census_gdf['total_rooms'] / census_gdf['households']
#     else:
#         census_gdf['avg_rooms'] = 5.5 
        
#     if 'median_house_value' not in census_gdf.columns:
#         for alt in ['medianHouseValue', 'price', 'value']:
#             if alt in census_gdf.columns:
#                 census_gdf['median_house_value'] = census_gdf[alt]
#                 break
#         else:
#             census_gdf['median_house_value'] = np.random.normal(600000, 150000, len(census_gdf))
    
#     comp_features = ['median_income', 'median_house_age', 'pop_density']
#     census_clean = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
#     scaler = StandardScaler()
#     scaled_data = scaler.fit_transform(census_clean)
#     knn = NearestNeighbors(n_neighbors=5, algorithm='auto').fit(scaled_data)
    
#     y_true = census_gdf['median_house_value'].values
#     _, indices = knn.kneighbors(scaled_data)
#     knn_preds = np.array([census_gdf.iloc[idx[1:]]['median_house_value'].mean() for idx in indices])
    
#     meta_model = LinearRegression()
#     meta_model.fit(np.column_stack((knn_preds, census_clean['pop_density'])), y_true)

#     shore_points = shoreline.geometry.representative_point()
#     cities_data = {"lat": [37.7749, 34.0522, 32.7157, 37.3382], "lon": [-122.4194, -118.2437, -117.1611, -121.8863]}
#     cities = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON).to_crs(CRS_PROJ)
    
#     return model, features, shore_points, cities, census_gdf, census_gdf['pop_density'].mean(), knn, scaler, meta_model

# with st.spinner("🚀 Initializing Stacking Ensemble..."):
#     model, features, shore_points, cities_gdf, census_gdf, STATE_AVG_DENSITY, knn_model, scaler, meta_model = load_and_train_stacker()

# # --- 3. GEOCODER & API LOGIC ---
# geolocator = Nominatim(user_agent="pricenest_pro_v3", timeout=5)

# SAFE_LOCATIONS = {
#     "1 grizzly way": (38.7468, -121.2137, "1 Grizzly Way, Granite Bay, CA", 4200, 5, 4.5),
#     "6520 s 4th st": (38.6915, -121.4503, "6520 S 4th St, Rio Linda, CA", 1250, 3, 1.0),
# }

# def fetch_property_details(address):
#     clean_addr = address.split(', United States')[0].split(', USA')[0]
#     try:
#         url = "https://api.rentcast.io/v1/properties"
#         headers = {"X-Api-Key": RENTCAST_API_KEY}
#         response = requests.get(url, headers=headers, params={"address": clean_addr, "limit": 1}, timeout=6)
#         if response.status_code == 200:
#             data = response.json()
#             return data[0] if data and len(data) > 0 else None
#     except: return None
#     return None

# # --- 4. SESSION STATE ---
# for key, default in [('sqft', 1800), ('beds', 3), ('baths', 2.0), ('last_address', "")]:
#     if key not in st.session_state: st.session_state[key] = default

# # --- 5. UI LAYOUT ---
# st.title("🏠 PriceNest: Multi-Model Valuation")
# col_search, col_details = st.columns([1, 1.2])

# ready_to_predict = False
# location = None

# with col_search:
#     st.subheader("1. Location Strategy")
#     search_query = st.text_input("Search Address:", value="1 Grizzly Way, Granite Bay, CA")
    
#     if search_query:
#         query_low = search_query.lower().strip()
#         demo_match = next((k for k in SAFE_LOCATIONS if k in query_low), None)
        
#         if demo_match:
#             lat, lon, addr, d_sqft, d_beds, d_baths = SAFE_LOCATIONS[demo_match]
#             class MockLoc: pass
#             location = MockLoc()
#             location.latitude, location.longitude, location.address = lat, lon, addr
#             location.demo = {"sqft": d_sqft, "beds": d_beds, "baths": d_baths}
#         else:
#             try:
#                 location = geolocator.geocode(search_query, limit=1, country_codes='us')
#             except:
#                 st.error("Geocoding timeout. Try again.")

#         if location:
#             st.success(f"📍 Found: {location.address[:45]}...")
#             ready_to_predict = True
            
#             if location.address != st.session_state['last_address']:
#                 st.session_state['last_address'] = location.address
#                 if hasattr(location, 'demo'):
#                     st.session_state['sqft'] = location.demo['sqft']
#                     st.session_state['beds'] = location.demo['beds']
#                     st.session_state['baths'] = location.demo['baths']
#                     st.toast("🚀 Demo Data Loaded", icon="⚡")
#                     st.rerun()
#                 else:
#                     api_res = fetch_property_details(location.address)
#                     if api_res:
#                         st.session_state['sqft'] = int(api_res.get('squareFootage', 1800))
#                         st.session_state['beds'] = int(api_res.get('bedrooms', 3))
#                         st.session_state['baths'] = float(api_res.get('bathrooms', 2.0))
#                         st.toast("✅ Live API Data Integrated", icon="🏠")
#                         st.rerun()

# with col_details:
#     st.subheader("2. Property DNA")
#     c1, c2, c3 = st.columns(3)
#     sqft = c1.number_input("Sq Footage", 300, 10000, key='sqft')
#     beds = c2.number_input("Beds", 0, 10, key='beds')
#     baths = c3.number_input("Baths", 1.0, 10.0, step=0.5, key='baths')
    
#     st.write("---")
#     condition = st.select_slider("Condition", options=["Fixer", "Avg", "Good", "Mint"], value="Avg")

# # --- 6. PREDICTION ENGINE ---
# st.divider()
# if ready_to_predict and location:
#     point = Point(location.longitude, location.latitude)
#     match = census_gdf[census_gdf.contains(point)]
#     t_data = match.iloc[0] if not match.empty else census_gdf.mean(numeric_only=True)
    
#     p_m = gpd.GeoSeries([point], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
#     d_c = shore_points.distance(p_m).min() / 1000
#     d_v = cities_gdf.distance(p_m).min() / 1000
    
#     base_in = pd.DataFrame([[
#         t_data['median_income'], t_data['median_house_age'], t_data['population'],
#         t_data['housing_units'], t_data['pop_density'], d_c, d_v,
#         t_data['median_income']/(t_data['median_house_age']+1),
#         t_data['population']/(t_data['housing_units']+1),
#         t_data['pop_density']/STATE_AVG_DENSITY
#     ]], columns=features)
#     p_base = model.predict(base_in)[0]

#     q_scale = scaler.transform(pd.DataFrame([t_data[['median_income', 'median_house_age', 'pop_density']]]))
#     _, idxs = knn_model.kneighbors(q_scale, n_neighbors=4)
#     comps = [census_gdf.iloc[i]['median_house_value'] * (sqft/(census_gdf.iloc[i].get('avg_rooms', 5.5)*280)) for i in idxs[0][1:]]
#     p_knn = np.mean(comps)

#     p_stacked = (p_base * 0.5) + (meta_model.predict(np.array([[p_knn, t_data['pop_density']]]))[0] * 0.5)
    
#     size_ratio = (sqft / (t_data.get('avg_rooms', 5.5) * 275)) ** 0.65 
#     cond_factor = {"Fixer": 0.85, "Avg": 1.0, "Good": 1.15, "Mint": 1.3}[condition]
#     f_price = p_stacked * size_ratio * cond_factor

#     res_col, map_col = st.columns([1.2, 1])
#     with res_col:
#         st.write("### Estimated Market Value")
#         st.header(f"${f_price:,.0f}")
#         st.markdown(f"**Confidence Range:** ${f_price*0.93:,.0f} — ${f_price*1.07:,.0f}")
        
#         with st.expander("AI Technical Breakdown"):
#             st.write(f"🤖 **Base AI (RF):** ${p_base:,.0f}")
#             st.write(f"🏘️ **Neighbor Comps (KNN):** ${p_knn:,.0f}")
    
#     with map_col:
#         m = folium.Map(location=[location.latitude, location.longitude], zoom_start=14, tiles="CartoDB Positron")
#         folium.Marker([location.latitude, location.longitude], icon=folium.Icon(color="blue", icon="home")).add_to(m)
#         st_folium(m, height=250, width=None)


import os
import re
import time
import logging
import joblib
import pandas as pd
import geopandas as gpd
import numpy as np
import requests
from functools import lru_cache
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from shapely.geometry import Point, Polygon as ShapelyPolygon
from shapely.ops import unary_union as _shapely_unary_union
from scipy.spatial import cKDTree
from geopy.geocoders import Nominatim
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)

RENTCAST_API_KEY   = os.environ.get("RENTCAST_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
MODEL_PATH    = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
META_PATH     = 'meta_model.joblib'
META_SCALER_PATH = 'meta_scaler.joblib'
DATASET_PATH  = "data/training_dataset.geojson"
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
CRS_PROJ  = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

log.info("Loading model assets...")
_base_learners = joblib.load(MODEL_PATH)   # list of (name, estimator) tuples
features       = joblib.load(FEATURES_PATH)

# Load OOF-trained meta-model and its scaler if available; fall back to inline Ridge
if os.path.exists(META_PATH) and os.path.exists(META_SCALER_PATH):
    meta_model   = joblib.load(META_PATH)
    meta_scaler  = joblib.load(META_SCALER_PATH)
    _oof_meta    = True
    log.info("Loaded OOF meta-model from disk")
else:
    meta_model  = None
    meta_scaler = None
    _oof_meta   = False
    log.info("No OOF meta-model found — will use simple average of base learners")

def _ensemble_predict(X_df):
    """Predict log(price) from all base learners, then meta-blend."""
    X = X_df[features].fillna(0.0).values   # NaN in any feature → 0 rather than crash
    preds = np.array([est.predict(X)[0] for _, est in _base_learners])
    if _oof_meta and meta_model is not None:
        scaled = meta_scaler.transform(preds.reshape(1, -1))
        return float(meta_model.predict(scaled)[0])
    return float(np.mean(preds))

census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
census_gdf['avg_rooms'] = 5.5

_census_sindex = census_gdf.sindex
log.info(f"Spatial index built over {len(census_gdf):,} census tracts")

_price_sorted   = np.sort(census_gdf['median_home_value'].values)
_density_sorted = np.sort(census_gdf['pop_density'].values)
_city_sorted    = np.sort(census_gdf['dist_city_km'].values)

def _percentile_of(sorted_arr, value):
    return round(float(np.searchsorted(sorted_arr, value)) / len(sorted_arr) * 100, 1)

# Lightweight KNN for neighborhood comp lookup (used in contributions only)
comp_features = ['median_income', 'median_house_age', 'pop_density', 'dist_coast_km', 'dist_city_km']
census_clean  = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
_knn_scaler   = StandardScaler()
_knn_scaled   = _knn_scaler.fit_transform(census_clean)
knn_model     = NearestNeighbors(n_neighbors=8, algorithm='ball_tree').fit(_knn_scaled)
log.info("KNN neighborhood model ready")

# Shoreline: GSHHS L1 polygons are land-area polygons, so distance() from an inland
# point to the filled polygon = 0 (inside it). We need the exterior ring (boundary line)
# which is the actual coastline. Filter to CA first to avoid the global TopologyException.
_shoreline_raw = gpd.read_file(SHORELINE_PATH)
_ca_shore      = _shoreline_raw.cx[-126.0:-113.5, 32.0:43.5]   # clip to CA in WGS84
_shore_proj    = _ca_shore.to_crs(CRS_PROJ)
_shore_lines   = [g.buffer(0).exterior for g in _shore_proj.geometry if not g.is_empty]
shore_geom     = _shapely_unary_union(_shore_lines) if _shore_lines else None
log.info(f"CA coastline loaded: {len(_shore_lines)} segments → boundary lines for coast distance")

# Build a KD-tree from all coastal vertex coordinates (in EPSG:3310 meters).
# This gives a second, independent distance measurement used to double-check the
# primary tract value — if they disagree by >50%, the KD-tree wins.
def _extract_coast_coords(geom):
    if geom is None:
        return []
    if geom.geom_type == 'LineString':
        return list(geom.coords)
    if geom.geom_type == 'MultiLineString':
        coords = []
        for seg in geom.geoms:
            coords.extend(seg.coords)
        return coords
    return []

_coast_coords = _extract_coast_coords(shore_geom)
_coast_kdtree = cKDTree(np.array(_coast_coords)) if _coast_coords else None
log.info(f"Coast KD-tree built: {len(_coast_coords):,} coastal vertices")

# Major CA cities — expanded from 4 to 10 for better dist_city estimates
cities_data = {
    "lat": [37.7749, 34.0522, 32.7157, 37.3382, 38.5816, 36.7468, 35.3733, 33.7701, 37.8044, 33.8366],
    "lon": [-122.4194, -118.2437, -117.1611, -121.8863, -121.4944, -119.7726, -119.0187, -118.1937, -122.2712, -117.9143],
}  # SF, LA, SD, SJ, Sacramento, Fresno, Bakersfield, Pasadena, Oakland, Anaheim
cities_gdf = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]), crs=CRS_LATLON
).to_crs(CRS_PROJ)

STATE_AVG_DENSITY  = census_gdf['pop_density'].mean()


# Pre-compute market stats once at startup — served instantly via /market-stats
_prices  = census_gdf['median_home_value'].dropna()
_coastal = census_gdf[census_gdf['dist_coast_km'].fillna(999) <  15]['median_home_value'].dropna()
_inland  = census_gdf[census_gdf['dist_coast_km'].fillna(0)   >  80]['median_home_value'].dropna()
_c_med   = float(_coastal.median()) if len(_coastal) else float(_prices.quantile(0.75))
_i_med   = float(_inland.median())  if len(_inland)  else float(_prices.quantile(0.25))
_market_stats = {
    'ca_median':           round(float(_prices.median()), -3),
    'coastal_median':      round(_c_med, -3),
    'inland_median':       round(_i_med, -3),
    'coastal_premium_pct': round((_c_med - _i_med) / max(1.0, _i_med) * 100, 1),
    'p25':  round(float(_prices.quantile(0.25)), -3),
    'p75':  round(float(_prices.quantile(0.75)), -3),
    'p90':  round(float(_prices.quantile(0.90)), -3),
    'total_tracts': len(census_gdf),
}
log.info(f"Market stats ready — CA median ${_market_stats['ca_median']:,.0f}, coastal premium +{_market_stats['coastal_premium_pct']}%")

# CA medians used as the "neutral baseline" for contribution analysis
_CA_MEDIANS = {
    'median_income':    census_gdf['median_income'].median(),
    'median_house_age': census_gdf['median_house_age'].median(),
    'pop_density':      census_gdf['pop_density'].median(),
    'dist_coast_km':    census_gdf['dist_coast_km'].median(),
    'dist_city_km':     census_gdf['dist_city_km'].median(),
}

# ── County-level appreciation factors (ACS 2020 → CAR Q4 2024) ──────────────
# Expensive markets (Bay Area) barely moved in % terms; cheap inland markets
# surged. Using actual CAR county median data, not a generic formula.
_COUNTY_FACTORS = {
    # Training data is ACS 2021-22 (already captures post-COVID run-up).
    # These factors represent only the modest delta from 2022 → 2024.
    # Bay Area — prices peaked 2022, slight decline since
    'San Francisco': 0.97, 'San Mateo': 0.98, 'Santa Clara': 1.00,
    'Marin': 0.98, 'Napa': 1.02, 'Sonoma': 1.03,
    'Alameda': 1.00, 'Contra Costa': 1.03,
    # SoCal — modest recovery from 2022 peak
    'Los Angeles': 1.05, 'Orange': 1.06, 'San Diego': 1.07,
    'Ventura': 1.04, 'Santa Barbara': 1.03,
    # Sacramento region
    'Sacramento': 1.06, 'Placer': 1.06, 'El Dorado': 1.05,
    'Yolo': 1.05, 'Solano': 1.05, 'Nevada': 1.05, 'Amador': 1.04,
    # Central Valley
    'Fresno': 1.08, 'Kern': 1.07, 'Tulare': 1.08,
    'Stanislaus': 1.07, 'San Joaquin': 1.07, 'Merced': 1.08,
    'Madera': 1.07, 'Kings': 1.06,
    # Central Coast
    'Santa Cruz': 1.01, 'Monterey': 1.02, 'San Luis Obispo': 1.03,
    # North CA
    'Shasta': 1.05, 'Butte': 1.06, 'Tehama': 1.04, 'Glenn': 1.03,
    'Siskiyou': 1.03, 'Humboldt': 1.03, 'Mendocino': 1.02,
    # Inland Empire — strongest post-peak recovery
    'Riverside': 1.09, 'San Bernardino': 1.08, 'Imperial': 1.06,
    # Other
    'Lake': 1.04, 'Colusa': 1.03, 'Sutter': 1.05,
}

def _extract_county(address: str) -> str:
    """Pull county name from a Nominatim display_name string."""
    m = re.search(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+County\b', address)
    return m.group(1).strip() if m else ''

# ── RentCast AVM — live comparable-sales valuation ───────────────────────────
@lru_cache(maxsize=256)
def _rentcast_avm(address: str, sqft: int, beds: int, baths: float):
    """Call RentCast AVM endpoint. Returns estimated price or None on failure."""
    if not RENTCAST_API_KEY:
        return None
    try:
        r = requests.get(
            'https://api.rentcast.io/v1/avm/value',
            headers={'X-Api-Key': RENTCAST_API_KEY},
            params={
                'address':       address,
                'propertyType':  'Single Family',
                'bedrooms':      int(beds),
                'bathrooms':     float(baths),
                'squareFootage': int(sqft),
            },
            timeout=6,
        )
        if r.status_code == 200:
            d = r.json()
            price = d.get('price') or d.get('value')
            if price and float(price) > 50_000:
                log.info(f"RentCast AVM: ${float(price):,.0f} for {address[:40]}")
                return float(price)
    except Exception as e:
        log.warning(f"RentCast AVM unavailable: {e}")
    return None

geolocator = Nominatim(user_agent="pricenest_v2", timeout=5)

# California bounding box — geopy expects (latitude, longitude) order, NOT (lon, lat)
_CA_VIEWBOX = [(42.0, -124.5), (32.5, -114.0)]  # [(NW lat/lon), (SE lat/lon)]

def _in_california(loc) -> bool:
    return (loc is not None
            and 32.5 <= loc.latitude  <= 42.0
            and -124.5 <= loc.longitude <= -114.0)

def _geocode_one(query, **kwargs):
    """Single Nominatim call with 3-attempt retry and backoff."""
    for attempt in range(3):
        try:
            time.sleep(1.1)   # Nominatim ToS: max 1 req/sec
            return geolocator.geocode(query, **kwargs)
        except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable):
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                return None
    return None

@lru_cache(maxsize=512)
def _geocode_cached(address: str):
    """Three-tier California-preferring geocoder with retry."""
    # Tier 1 — restrict results to CA bounding box
    loc = _geocode_one(address, limit=1, country_codes='us',
                       viewbox=_CA_VIEWBOX, bounded=True)
    if _in_california(loc):
        return loc

    # Tier 2 — CA as preference only
    loc = _geocode_one(address, limit=1, country_codes='us',
                       viewbox=_CA_VIEWBOX, bounded=False)
    if _in_california(loc):
        return loc

    # Tier 3 — append ', California' for bare street queries with no state context
    has_ca = any(x in address.lower() for x in ['california', ', ca', ' ca '])
    if not has_ca:
        loc = _geocode_one(address + ', California', limit=1, country_codes='us')
        if _in_california(loc):
            return loc

    return None  # no California result found at any tier

def _find_census_tract(point: Point):
    """Return the census tract row for a point using the R-tree spatial index."""
    candidates = list(_census_sindex.intersection(point.bounds))
    if candidates:
        subset = census_gdf.iloc[candidates]
        match  = subset[subset.contains(point)]
        if not match.empty:
            return match.iloc[0]
    return census_gdf.mean(numeric_only=True)

# --- 3. ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
@limiter.limit("60 per minute")
def predict():
    try:
        data = request.get_json(silent=True) or {}

        # Input validation
        address = data.get('address', '').strip()
        if not address:
            return jsonify({"error": "Address is required"}), 400

        try:
            u_sqft = max(100.0, min(50000.0, float(data.get('sqft', 1800))))
            u_beds = max(0.0,   min(20.0,    float(data.get('beds', 3))))
            u_baths = max(0.0,  min(20.0,    float(data.get('baths', 2.0))))
        except (ValueError, TypeError):
            return jsonify({"error": "sqft, beds, and baths must be numbers"}), 400

        u_cond = data.get('condition', 'Avg')
        if u_cond not in ('Fixer', 'Avg', 'Good', 'Mint'):
            u_cond = 'Avg'

        # Geocoding — cached so repeat addresses skip the network call
        location = _geocode_cached(address)
        if not location:
            return jsonify({"error": "Address not found. Try including city and state."}), 404

        lat, lon = location.latitude, location.longitude

        # Reject addresses outside California — the model is CA-only and extrapolates badly elsewhere
        CA_BOUNDS = {"lat_min": 32.5, "lat_max": 42.0, "lon_min": -124.5, "lon_max": -114.0}
        if not (CA_BOUNDS["lat_min"] <= lat <= CA_BOUNDS["lat_max"] and
                CA_BOUNDS["lon_min"] <= lon <= CA_BOUNDS["lon_max"]):
            return jsonify({"error": "PriceNest only covers California addresses. Please enter a CA location."}), 400

        point = Point(lon, lat)

        # Census tract lookup via R-tree spatial index
        t_data = _find_census_tract(point)

        # Project point once — used for both city and coast fallback
        p_m       = gpd.GeoSeries([point], crs=CRS_LATLON).to_crs(CRS_PROJ).iloc[0]
        dist_city = cities_gdf.distance(p_m).min() / 1000

        # Coast distance — three-source resolution with cross-validation:
        #   1. Census tract pre-computed value (same source as training data, preferred)
        #   2. Shapely boundary-line distance (geometric fallback)
        #   3. KD-tree nearest-vertex distance (independent double-check)
        _tract_coast = float(t_data.get('dist_coast_km', -1))
        if _tract_coast >= 0 and not np.isnan(_tract_coast):
            dist_coast = _tract_coast
        elif shore_geom is not None:
            dist_coast = shore_geom.distance(p_m) / 1000
        else:
            dist_coast = float(census_gdf['dist_coast_km'].median())

        # Double-check: query the KD-tree for an independent geometric measurement.
        # KD-tree distance is in EPSG:3310 meters → convert to km.
        # If the primary value and KD-tree disagree by more than 50%, the KD-tree wins —
        # it cannot be fooled by stale tract data or shapely polygon-interior issues.
        if _coast_kdtree is not None:
            _kd_dist_km = float(_coast_kdtree.query([[p_m.x, p_m.y]])[0][0]) / 1000
            _discrepancy = abs(dist_coast - _kd_dist_km) / max(_kd_dist_km, 1.0)
            if _discrepancy > 0.50:
                log.warning(
                    f"Coast distance overridden: primary={dist_coast:.1f}km "
                    f"vs KD-tree={_kd_dist_km:.1f}km (Δ={_discrepancy:.0%}) → using KD-tree"
                )
                dist_coast = _kd_dist_km
            else:
                log.info(f"Coast distance OK: {dist_coast:.1f}km (KD-tree={_kd_dist_km:.1f}km, Δ={_discrepancy:.0%})")

        # Safely extract tract values — fall back to CA medians if NaN
        def _safe(key, fallback):
            v = t_data.get(key, fallback)
            return fallback if (v is None or (isinstance(v, float) and np.isnan(v))) else float(v)

        _inc = _safe('median_income',    65_000.0)
        _age = _safe('median_house_age', 30.0)
        _pop = _safe('population',       4_000.0)
        _hu  = _safe('housing_units',    1_500.0)
        _den = _safe('pop_density',      2_000.0)

        # Base model input — must match training.py FEATURE_COLS exactly
        input_dict = {
            # Core census
            'median_income':      _inc,
            'median_house_age':   _age,
            'population':         _pop,
            'housing_units':      _hu,
            'pop_density':        _den,
            'dist_coast_km':      dist_coast,
            'dist_city_km':       dist_city,
            # Geography + polynomial
            'lat':                lat,
            'lon':                lon,
            'lat_sq':             lat ** 2,
            'lon_sq':             lon ** 2,
            'lat_lon':            lat * lon,
            # Interactions
            'income_per_age':     _inc / (_age + 1),
            'persons_per_unit':   _pop / (_hu + 1),
            'relative_density':   _den / STATE_AVG_DENSITY,
            'coast_income':       _inc / (dist_coast + 1),
            'city_density':       _den / (dist_city  + 1),
            'income_density':     _inc * _den / 1e8,
            # Log transforms
            'log_income':         np.log1p(_inc),
            'log_density':        np.log1p(_den),
            'log_coast':          np.log1p(dist_coast),
            'log_city':           np.log1p(dist_city),
            # Higher-order
            'income_sq':          _inc ** 2 / 1e9,
            'age_sq':             _age ** 2,
            'coast_sq':           dist_coast ** 2 / 1e4,
            'coast_city_ratio':   dist_city / (dist_coast + 1),
            'occupancy_pressure': _pop / max(1.0, _hu),
            # Distance to premium metros
            'dist_sv':    ((lat - 37.39)**2 + (lon - (-122.08))**2) ** 0.5,
            'dist_bh':    ((lat - 34.07)**2 + (lon - (-118.40))**2) ** 0.5,
            'dist_lj':    ((lat - 32.85)**2 + (lon - (-117.27))**2) ** 0.5,
            'dist_marin': ((lat - 37.95)**2 + (lon - (-122.53))**2) ** 0.5,
        }
        # Ensemble predict — log(price) → exp → dollars
        p_base = float(np.exp(_ensemble_predict(pd.DataFrame([input_dict]))))

        # KNN neighborhood comps
        q_vals  = {'median_income': _inc, 'median_house_age': _age, 'pop_density': _den,
                   'dist_coast_km': dist_coast, 'dist_city_km': dist_city}
        q_scale = _knn_scaler.transform(pd.DataFrame([q_vals])[comp_features])
        _, idxs = knn_model.kneighbors(q_scale, n_neighbors=7)
        # At inference time the query is NOT a training point — include all 7 neighbors
        p_knn   = float(np.mean([census_gdf.iloc[i]['median_home_value'] for i in idxs[0]]))

        # Census tract median — ground-truth anchor for this neighborhood
        tract_anchor = float(t_data.get('median_home_value', p_base))

        # Three-way blend: ensemble ML + KNN neighborhood comps + tract anchor
        # p_knn was previously computed but never used — now included at 20% weight
        p_stacked = p_base * 0.30 + p_knn * 0.20 + tract_anchor * 0.50

        # ── County-level appreciation (CAR Q4 2024 vs ACS 2020) ─────────────
        # Look up the county from the geocoded address first; fall back to a
        # price-tiered formula for counties not in the table.
        _county      = _extract_county(location.address)
        if _county in _COUNTY_FACTORS:
            appreciation = _COUNTY_FACTORS[_county]
            log.info(f"County appreciation: {_county} → {appreciation:.2f}x")
        else:
            # Fallback: small delta from 2022 peak — expensive areas flat, cheaper areas up slightly
            _pr          = min(2.0, tract_anchor / 600_000.0)
            appreciation = max(1.03, 1.08 - 0.03 * _pr)
            log.info(f"County '{_county}' not in table → price-based {appreciation:.2f}x")

        # Current market value for a typical home in this neighborhood
        market_base = tract_anchor * appreciation

        # ── Property adjustments (additive — no multiplicative stacking) ──────
        CA_AVG_SQFT = 1650.0

        # 1. Square footage — moderate curve so large homes don't explode the price
        size_adj = (u_sqft / CA_AVG_SQFT) ** 0.48 - 1.0

        # 2. Bedrooms vs 3bd baseline
        bed_adj = max(-0.15, min(0.18, (u_beds - 3.0) * 0.028))

        # 3. Bathrooms vs 2ba baseline
        bath_adj = max(-0.08, min(0.12, (u_baths - 2.0) * 0.018))

        # 4. Condition
        cond_adj = {'Fixer': -0.13, 'Avg': 0.0, 'Good': 0.07, 'Mint': 0.15}[u_cond]

        # 5. Housing age (non-linear: newer is better up to a point)
        house_age = float(t_data['median_house_age'])
        if   house_age < 10:  age_adj =  0.04
        elif house_age < 20:  age_adj =  0.02
        elif house_age < 35:  age_adj =  0.00
        elif house_age < 55:  age_adj = -0.02
        elif house_age < 75:  age_adj = -0.04
        else:                 age_adj =  0.01   # vintage premium in older neighborhoods

        # Total property adjustment — hard cap ±28%
        total_adj = max(-0.28, min(0.28, size_adj + bed_adj + bath_adj + cond_adj + age_adj))

        # ── Model signal — blended ML insight, tightly dampened ──────────────
        # The ensemble adds cross-CA pattern recognition but is not allowed to
        # significantly override the price-calibrated market_base.
        raw_signal   = (p_stacked - tract_anchor) * 0.15
        model_signal = max(-market_base * 0.08, min(market_base * 0.08, raw_signal))

        f_price = (market_base * (1.0 + total_adj)) + model_signal

        # Hard ceiling: no property can exceed 2.2x the neighborhood's current
        # market price. Prevents KNN or meta-model outliers from escaping.
        f_price = min(f_price, market_base * 2.2)
        f_price = max(150_000.0, min(15_000_000.0, float(f_price)))

        # ── RentCast AVM — live comparable-sales signal ───────────────────────
        # If the API key is set, blend in RentCast's valuation (based on real
        # MLS comparable sales) at 70% weight. Our model stays as a 30% sanity
        # check so a single bad API response can't wildly skew the result.
        rc_price = _rentcast_avm(location.address, int(u_sqft), int(u_beds), u_baths)
        if rc_price:
            f_price = 0.70 * rc_price + 0.30 * f_price
            f_price = max(150_000.0, min(15_000_000.0, float(f_price)))

        # --- Feature contribution analysis ---
        # For each key feature, replace its value with the CA median and re-run the full
        # prediction pipeline. The dollar difference = that feature's contribution to price.
        def _price_with(overrides):
            d = input_dict.copy()
            d.update(overrides)
            i, a, p2, h, dn = (d['median_income'], d['median_house_age'],
                                d['population'], d['housing_units'], d['pop_density'])
            dc, dv = d['dist_coast_km'], d['dist_city_km']
            d['income_per_age']     = i / (a + 1)
            d['relative_density']   = dn / STATE_AVG_DENSITY
            d['coast_income']       = i / (dc + 1)
            d['city_density']       = dn / (dv + 1)
            d['income_density']     = i * dn / 1e8
            d['income_sq']          = i ** 2 / 1e9
            d['log_income']         = np.log1p(i)
            d['log_density']        = np.log1p(dn)
            d['log_coast']          = np.log1p(dc)
            d['log_city']           = np.log1p(dv)
            d['age_sq']             = a ** 2
            d['coast_sq']           = dc ** 2 / 1e4
            d['coast_city_ratio']   = dv / (dc + 1)
            d['occupancy_pressure'] = p2 / max(1.0, h)
            d['lat_sq']             = d['lat'] ** 2
            d['lon_sq']             = d['lon'] ** 2
            d['lat_lon']            = d['lat'] * d['lon']
            d['dist_sv']    = ((d['lat']-37.39)**2 + (d['lon']-(-122.08))**2)**0.5
            d['dist_bh']    = ((d['lat']-34.07)**2 + (d['lon']-(-118.40))**2)**0.5
            d['dist_lj']    = ((d['lat']-32.85)**2 + (d['lon']-(-117.27))**2)**0.5
            d['dist_marin'] = ((d['lat']-37.95)**2 + (d['lon']-(-122.53))**2)**0.5
            b  = float(np.exp(_ensemble_predict(pd.DataFrame([d]))))
            s  = b * 0.45 + tract_anchor * 0.55
            # Use the same county appreciation already resolved for this address
            o_mbase = market_base
            o_h_age = float(d.get('median_house_age', house_age))
            if   o_h_age < 10:  o_age_adj =  0.04
            elif o_h_age < 20:  o_age_adj =  0.02
            elif o_h_age < 35:  o_age_adj =  0.00
            elif o_h_age < 55:  o_age_adj = -0.02
            elif o_h_age < 75:  o_age_adj = -0.04
            else:               o_age_adj =  0.01
            o_adj  = max(-0.28, min(0.28, size_adj + bed_adj + bath_adj + cond_adj + o_age_adj))
            o_sig  = max(-o_mbase * 0.08, min(o_mbase * 0.08, (s - tract_anchor) * 0.15))
            result = (o_mbase * (1.0 + o_adj)) + o_sig
            return max(150_000.0, min(15_000_000.0, min(result, o_mbase * 2.2)))

        contributions = {
            "Neighborhood Income":  round(f_price - _price_with({'median_income':    _CA_MEDIANS['median_income']}),    -2),
            "Coast Access":         round(f_price - _price_with({'dist_coast_km':    _CA_MEDIANS['dist_coast_km']}),    -2),
            "City Proximity":       round(f_price - _price_with({'dist_city_km':     _CA_MEDIANS['dist_city_km']}),     -2),
            "Population Density":   round(f_price - _price_with({'pop_density':      _CA_MEDIANS['pop_density']}),      -2),
            "Housing Age":          round(f_price - _price_with({'median_house_age': _CA_MEDIANS['median_house_age']}), -2),
        }

        log.info(f"Prediction: {address!r} → ${f_price:,.0f} (base={p_base:.0f}, knn={p_knn:.0f})")
        log.info(f"Contributions: { {k: f'${v:+,.0f}' for k,v in contributions.items()} }")

        tract_median = float(t_data.get('median_home_value', f_price))
        vs_median_pct = round((f_price - tract_median) / tract_median * 100, 1) if tract_median else 0

        # Google Street View Static API — exterior photo of the property
        if GOOGLE_MAPS_API_KEY:
            photo_url = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size=640x420&location={lat},{lon}"
                f"&fov=90&pitch=5&source=outdoor&key={GOOGLE_MAPS_API_KEY}"
            )
        else:
            photo_url = None

        return jsonify({
            "status": "success",
            "valuation": {
                "estimated_value": round(f_price, -3),
                "range_low":       round(f_price * 0.93, -3),
                "range_high":      round(f_price * 1.07, -3),
            },
            "calc_base": {
                "market_base":  round(market_base, 0),
                "model_signal": round(model_signal, 0),
                "age_adj":      age_adj,
            },
            "location": {"lat": lat, "lon": lon, "address": location.address},
            "neighborhood": {
                "price_percentile":   _percentile_of(_price_sorted, tract_median),
                "density_percentile": _percentile_of(_density_sorted, float(t_data['pop_density'])),
                "city_percentile":    _percentile_of(_city_sorted,    dist_city),
                "dist_coast_km":      round(dist_coast, 1),
                "dist_city_km":       round(dist_city, 1),
                "pop_density":        round(float(t_data['pop_density']), 0),
                "tract_median":       round(tract_median, -3),
                "vs_median_pct":      vs_median_pct,
            },
            "contributions": contributions,
            "photo_url": photo_url,
        })

    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        log.exception("Predict error")
        return jsonify({"error": "Internal server error"}), 500

def _make_hex(cx, cy, r):
    """Return a pointy-top hexagon polygon centered at (cx, cy) with circumradius r."""
    angles = [np.radians(30 + 60 * i) for i in range(6)]
    coords = [(round(cx + r * np.cos(a), 6), round(cy + r * np.sin(a), 6)) for a in angles]
    coords.append(coords[0])  # close ring
    return ShapelyPolygon(coords)

def _build_hex_cache():
    global _heatmap_cache

    r = 0.08          # hex circumradius in degrees (~9 km)
    dx = np.sqrt(3) * r   # horizontal center-to-center spacing
    dy = 1.5 * r          # vertical center-to-center spacing

    minx, miny, maxx, maxy = census_gdf.total_bounds

    # Build grid of hex centroids + geometries
    hex_ids, hex_geoms, cx_list, cy_list = [], [], [], []
    row, hid = 0, 0
    y = miny - r
    while y <= maxy + r:
        x_offset = (row % 2) * dx / 2
        x = minx - dx + x_offset
        while x <= maxx + dx:
            hex_geoms.append(_make_hex(x, y, r))
            cx_list.append(x); cy_list.append(y)
            hex_ids.append(hid); hid += 1
            x += dx
        y += dy; row += 1

    # GeoDataFrame of hex centroids for spatial join
    centroids_gdf = gpd.GeoDataFrame(
        {'hex_id': hex_ids},
        geometry=gpd.points_from_xy(cx_list, cy_list),
        crs='EPSG:4326'
    )

    # Join each hex centroid to the census tract that contains it
    tracts = census_gdf[['geometry', 'median_home_value']].copy()
    joined = gpd.sjoin(centroids_gdf, tracts, how='inner', predicate='within')
    matched = joined.groupby('hex_id')['median_home_value'].mean()

    # Build GeoJSON features — use hex_features to avoid shadowing the model features list
    hex_features = []
    for hid, price in matched.items():
        geom = hex_geoms[hid]
        coords = [[c[0], c[1]] for c in geom.exterior.coords]
        hex_features.append({
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [coords]},
            'properties': {'price': round(float(price), 0)}
        })

    _heatmap_cache = {
        'type': 'FeatureCollection',
        'features': hex_features,
        'scale': {'min': 300000, 'mid': 2650000, 'max': 5000000}
    }
    log.info(f"Hexmap ready: {len(hex_features):,} hexagons over {len(census_gdf):,} tracts")

log.info("Pre-computing hex map...")
_heatmap_cache = None
_build_hex_cache()

@app.route('/heatmap-data')
def heatmap_data():
    return jsonify(_heatmap_cache)

@app.route('/market-stats')
def market_stats():
    return jsonify(_market_stats)

if __name__ == '__main__':
    app.run(port=8000, debug=False)