import geopandas as gpd

def classify_centroids_direct_overlap(centroids, green_zones, crs_metric=3857):
    """Step 2: classify centroids directly overlapping green polygons as A."""
    centroids = centroids.to_crs(epsg=crs_metric).copy()
    green_zones = green_zones.to_crs(epsg=crs_metric)

    joined = gpd.sjoin(centroids, green_zones, how="left", predicate="intersects")

    centroids["classified"] = joined["index_right"].notnull().map(
        lambda x: "A" if x else None
    )
    return centroids
