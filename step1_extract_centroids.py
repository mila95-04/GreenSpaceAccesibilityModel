import geopandas as gpd

def extract_centroids(grid_gdf):
    """
    Extract centroids of grid polygons.
    """
    centroids = grid_gdf.copy()
    centroids["geometry"] = centroids["geometry"].centroid
    centroids["centroid_id"] = centroids.index
    return centroids
