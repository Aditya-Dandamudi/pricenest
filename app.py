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
import logging
import joblib
import pandas as pd
import geopandas as gpd
import numpy as np
import requests
from functools import lru_cache
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from shapely.geometry import Point, Polygon as ShapelyPolygon
from shapely.ops import unary_union as _shapely_unary_union
from scipy.spatial import cKDTree
from geopy.geocoders import Nominatim
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import Ridge
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

RENTCAST_API_KEY = os.environ.get("RENTCAST_API_KEY", "")
MODEL_PATH = 'price_nest_model.joblib'
FEATURES_PATH = 'model_features.joblib'
DATASET_PATH = "data/training_dataset.geojson" 
SHORELINE_PATH = "data/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp" 
CRS_PROJ = "EPSG:3310"
CRS_LATLON = "EPSG:4326"

log.info("Loading model assets...")
model = joblib.load(MODEL_PATH)
features = joblib.load(FEATURES_PATH)
census_gdf = gpd.read_file(DATASET_PATH).to_crs(CRS_LATLON)
census_gdf['avg_rooms'] = 5.5  # CA median proxy — no room count in dataset

# Spatial index: O(log n) tract lookup instead of scanning all 8,766 polygons
_census_sindex = census_gdf.sindex
log.info(f"Spatial index built over {len(census_gdf):,} census tracts")

# Pre-sort arrays for fast O(log n) percentile lookups in neighborhood stats
_price_sorted   = np.sort(census_gdf['median_home_value'].values)
_density_sorted = np.sort(census_gdf['pop_density'].values)
_city_sorted    = np.sort(census_gdf['dist_city_km'].values)

def _percentile_of(sorted_arr, value):
    """Return 0-100 percentile of value within a pre-sorted array."""
    return round(float(np.searchsorted(sorted_arr, value)) / len(sorted_arr) * 100, 1)

# KNN stacking setup — ball_tree is more efficient for geographic feature spaces
comp_features = ['median_income', 'median_house_age', 'pop_density']
census_clean = census_gdf[comp_features].fillna(census_gdf[comp_features].mean())
scaler = StandardScaler()
scaled_data = scaler.fit_transform(census_clean)
knn_model = NearestNeighbors(n_neighbors=6, algorithm='ball_tree').fit(scaled_data)

# Meta-model: Ridge regression with 5 features (was LinearRegression with 2).
# Adding income, coast distance, and city distance gives the stacker geographic context.
y_true    = census_gdf['median_home_value'].values
_, indices = knn_model.kneighbors(scaled_data)
knn_preds  = np.array([census_gdf.iloc[idx[1:]]['median_home_value'].mean() for idx in indices])
coast_vals  = census_gdf['dist_coast_km'].fillna(census_gdf['dist_coast_km'].mean()).values
city_vals   = census_gdf['dist_city_km'].fillna(census_gdf['dist_city_km'].mean()).values
meta_model  = Ridge(alpha=1000.0)
meta_model.fit(
    np.column_stack([knn_preds, census_clean['median_income'], census_clean['pop_density'], coast_vals, city_vals]),
    y_true
)
log.info("Meta-model (Ridge) trained with 5-feature stacking")

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

STATE_AVG_DENSITY = census_gdf['pop_density'].mean()

# CA medians used as the "neutral baseline" for contribution analysis
_CA_MEDIANS = {
    'median_income':    census_gdf['median_income'].median(),
    'median_house_age': census_gdf['median_house_age'].median(),
    'pop_density':      census_gdf['pop_density'].median(),
    'dist_coast_km':    census_gdf['dist_coast_km'].median(),
    'dist_city_km':     census_gdf['dist_city_km'].median(),
}

geolocator = Nominatim(user_agent="pricenest_v2", timeout=5)

@lru_cache(maxsize=512)
def _geocode_cached(address: str):
    """Cache Nominatim results so identical addresses skip the network call."""
    return geolocator.geocode(address, limit=1, country_codes='us')

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
@limiter.limit("10 per minute")
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

        # Base model input
        input_dict = {
            'median_income':    t_data['median_income'],
            'median_house_age': t_data['median_house_age'],
            'population':       t_data['population'],
            'housing_units':    t_data['housing_units'],
            'pop_density':      t_data['pop_density'],
            'dist_coast_km':    dist_coast,
            'dist_city_km':     dist_city,
            'income_per_age':   t_data['median_income'] / (t_data['median_house_age'] + 1),
            'persons_per_unit': t_data['population'] / (t_data['housing_units'] + 1),
            'relative_density': t_data['pop_density'] / STATE_AVG_DENSITY,
        }
        p_base = model.predict(pd.DataFrame([input_dict])[features])[0]

        # KNN stacking — find similar tracts and compute size-adjusted comp prices
        q_scale = scaler.transform(pd.DataFrame([t_data[comp_features]]))
        _, idxs = knn_model.kneighbors(q_scale, n_neighbors=5)
        comps = [
            census_gdf.iloc[i]['median_home_value']
            * (u_sqft / (census_gdf.iloc[i]['avg_rooms'] * 280))
            for i in idxs[0][1:]
        ]
        p_knn = np.mean(comps)

        # Meta-model: Ridge with 5 features (was LinearRegression with 2)
        p_stacked = (p_base * 0.5) + (
            meta_model.predict([[p_knn, t_data['median_income'], t_data['pop_density'], dist_coast, dist_city]])[0] * 0.5
        )

        # Size and condition adjustment
        typical_sqft = max(500.0, (u_beds * 300) + (u_baths * 150) + 400)
        size_ratio   = (u_sqft / typical_sqft) ** 0.65
        cond_factor  = {'Fixer': 0.85, 'Avg': 1.0, 'Good': 1.15, 'Mint': 1.3}[u_cond]
        f_price      = float(p_stacked * size_ratio * cond_factor)

        # Safety clamp — CA home prices realistically range $80K–$15M
        f_price = max(80_000.0, min(15_000_000.0, f_price))

        # --- Feature contribution analysis ---
        # For each key feature, replace its value with the CA median and re-run the full
        # prediction pipeline. The dollar difference = that feature's contribution to price.
        def _price_with(overrides):
            d = input_dict.copy()
            d.update(overrides)
            # Keep derived features consistent with any overridden inputs
            d['income_per_age']   = d['median_income'] / (d['median_house_age'] + 1)
            d['relative_density'] = d['pop_density'] / STATE_AVG_DENSITY
            b = model.predict(pd.DataFrame([d])[features])[0]
            s = (b * 0.5) + (
                meta_model.predict([[p_knn, d['median_income'], d['pop_density'],
                                     d['dist_coast_km'], d['dist_city_km']]])[0] * 0.5
            )
            return max(80_000.0, min(15_000_000.0, float(s * size_ratio * cond_factor)))

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

        return jsonify({
            "status": "success",
            "valuation": {
                "estimated_value": round(f_price, -3),
                "range_low":       round(f_price * 0.93, -3),
                "range_high":      round(f_price * 1.07, -3),
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

if __name__ == '__main__':
    app.run(port=8000, debug=False)
