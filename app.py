#94532ff79fc3d87f643d667d1ad4bcee4beb330b API KEY   ACS variables	Census

# ACS variables	Census API / data.census.gov                   x
# Census Tracts shapefile	Census TIGER download              x
# Coastline	NOAA shoreline or OSM water polygons               
# Land use	OSM via Overpass or osmnx                          x

import osmnx as ox

tags = {"landuse": True}
gdf = ox.geometries_from_point((lat, lon), tags, dist=1000)







