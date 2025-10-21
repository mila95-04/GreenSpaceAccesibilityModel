import geopandas as gpd

def load_geojson(filepath):
    """Load a GeoJSON as GeoDataFrame with EPSG:3857 projection (for distance ops)."""
    gdf = gpd.read_file(filepath)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)  # assume WGS84 if not set
    return gdf.to_crs(epsg=3857)

def save_geojson(gdf, filepath):
    """Save GeoDataFrame as GeoJSON in WGS84 (for QGIS compatibility)."""
    gdf.to_crs(epsg=4326).to_file(filepath, driver="GeoJSON")

import pandas as pd

def save_distances_to_csv(results, filepath):
    """
    Save distance results from network analysis into CSV.
    results: list of dicts {centroid_id, entry_point_id, exit_point_id, distance}
    """
    df = pd.DataFrame(results)
    df.to_csv(filepath, index=False)
