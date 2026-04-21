import os
import zipfile
import urllib.request
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
from shapely.geometry import Point

#    CONFIGURATION 
ACS_API_KEY = "94532ff79fc3d87f643d667d1ad4bcee4beb330b" 
STATE_FIPS = "06"  # California
CRS_PROJ = "EPSG:3310"  # California Albers (Meters)
CRS_LATLON = "EPSG:4326"

#  FILE PATHS
DATA_DIR = "data"
TRACTS_PATH = "tl_2025_06_tract/tl_2025_06_tract.shp" 
SHORELINE_PATH = f"{DATA_DIR}/shoreline/GSHHS_shp/h/GSHHS_h_L1.shp"
OUTPUT_PATH = f"{DATA_DIR}/training_dataset.geojson"

os.makedirs(DATA_DIR, exist_ok=True)

def download_file(url, dest_path):
    if not os.path.exists(dest_path):
        print(f"Downloading {os.path.basename(dest_path)}...")
        urllib.request.urlretrieve(url, dest_path)

#  LOAD CENSUS TRACTS 
print("Loading Census Tracts...")
if not os.path.exists(TRACTS_PATH):
    raise FileNotFoundError(f"Tracts shapefile not found at {TRACTS_PATH}.")

tracts = gpd.read_file(TRACTS_PATH).to_crs(CRS_LATLON)

if "GEOID" not in tracts.columns and "GEOID10" in tracts.columns:
    tracts["GEOID"] = tracts["GEOID10"]

# FETCH ACS DATA 
print("Fetching ACS Data...")
ACS_VARS = {
    "B25077_001E": "median_home_value",
    "B19013_001E": "median_income",
    "B01003_001E": "population",
    "B25002_001E": "housing_units",
    "B25035_001E": "median_house_age"
}

var_string = ",".join(ACS_VARS.keys())
acs_url = (f"https://api.census.gov/data/2022/acs/acs5?get={var_string}&for=tract:*&in=state:{STATE_FIPS}&key={ACS_API_KEY}")

resp = requests.get(acs_url)
resp.raise_for_status()

acs_data = resp.json()
acs_df = pd.DataFrame(acs_data[1:], columns=acs_data[0])
acs_df["GEOID"] = acs_df["state"] + acs_df["county"] + acs_df["tract"]
acs_df = acs_df.rename(columns=ACS_VARS)

for col in ACS_VARS.values():
    acs_df[col] = pd.to_numeric(acs_df[col], errors="coerce")

acs_df = acs_df.dropna(subset=["median_home_value"])
acs_df = acs_df[acs_df["median_home_value"] > 0]

tracts = tracts.merge(acs_df, on="GEOID", how="inner")
print(f"Merged dataset size: {len(tracts)} tracts")

# SPATIAL ENGINEERING: SHORELINE (STABILIZED) 
print("Processing Shoreline...")
shoreline_zip = f"{DATA_DIR}/shoreline_gshhg.zip"
download_file("https://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.7.zip", shoreline_zip)

shoreline_extract_dir = f"{DATA_DIR}/shoreline"
if not os.path.exists(shoreline_extract_dir):
    with zipfile.ZipFile(shoreline_zip, "r") as z:
        z.extractall(shoreline_extract_dir)

# Read shoreline using bounding box
bounds_tuple = tuple(tracts.total_bounds)
shoreline = gpd.read_file(SHORELINE_PATH, bbox=bounds_tuple)

print(f"Found {len(shoreline)} shoreline segments.")

tracts_proj = tracts.to_crs(CRS_PROJ)
tracts_proj["centroid"] = tracts_proj.geometry.centroid

if len(shoreline) == 0:
    print("Warning: No shoreline found. Setting coast distance to 500km.")
    tracts_proj["dist_coast_km"] = 500.0
else:
    # Project to meters first
    shoreline = shoreline.to_crs(CRS_PROJ)
    
    # Filter for valid, non-empty geometries
    valid_geoms = [g for g in shoreline.geometry if g is not None and not g.is_empty]
    
    print(f"Merging {len(valid_geoms)} segments cumulatively...")
    
    # CUMULATIVE UNION: We join shapes one-by-one to bypass the TypeError
    shoreline_geom = valid_geoms[0]
    for i in range(1, len(valid_geoms)):
        try:
            shoreline_geom = shoreline_geom.union(valid_geoms[i])
        except Exception:
            continue 
            
    shoreline_geom = shoreline_geom.simplify(tolerance=100)

    print("Calculating Coast Distance...")
    tracts_proj["dist_coast_km"] = tracts_proj["centroid"].apply(
        lambda x: shoreline_geom.distance(x) / 1000
    )

# SPATIAL ENGINEERING: MAJOR CITIES 
cities_data = {
    "city": ["San Francisco", "Los Angeles", "San Diego", "San Jose"],
    "lat": [37.7749, 34.0522, 32.7157, 37.3382],
    "lon": [-122.4194, -118.2437, -117.1611, -121.8863]
}
cities_gdf = gpd.GeoDataFrame(
    cities_data, 
    geometry=gpd.points_from_xy(cities_data["lon"], cities_data["lat"]),
    crs=CRS_LATLON
).to_crs(CRS_PROJ)

print("Calculating City Distances...")
def get_nearest_city_dist(point):
    return cities_gdf.distance(point).min() / 1000

tracts_proj["dist_city_km"] = tracts_proj["centroid"].apply(get_nearest_city_dist)

#URBANIZATION PROXY
tracts_proj["area_sqkm"] = tracts_proj.geometry.area / 10**6
tracts_proj["pop_density"] = tracts_proj["population"] / tracts_proj["area_sqkm"]

#EXPORT 
final_cols = [
    "GEOID", "median_home_value", "median_income", "median_house_age",
    "population", "housing_units", "pop_density", "dist_coast_km", 
    "dist_city_km", "geometry"
]

final_gdf = tracts_proj.to_crs(CRS_LATLON)[final_cols]
final_gdf.to_file(OUTPUT_PATH, driver="GeoJSON")

print(f"Success! Final dataset saved to {OUTPUT_PATH}")
print(final_gdf.head())