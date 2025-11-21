import geopandas as gpd

def classify_centroids_direct_overlap(centroids, green_zones, crs_metric=3857):
    """Step 2: classify centroids directly overlapping green polygons as A."""
    centroids = centroids.to_crs(epsg=crs_metric).copy()
    green_zones = green_zones.to_crs(epsg=crs_metric)

    joined = gpd.sjoin(centroids, green_zones, how="left", predicate="intersects")

    centroids["classified"] = joined["index_right"].notnull().map(
        lambda x: "A" if x else None
    )

    centroids["green_id"] = joined["index_right"]

    if "green_area_sqm" not in green_zones.columns:
        green_zones["green_area_sqm"] = green_zones.geometry.area

    centroids["green_area_sqm"] = centroids["green_id"].map(
    green_zones["green_area_sqm"]
    )

    centroids.loc[centroids["classified"] == "A", "green_id"] = centroids["green_id"]
    centroids.loc[centroids["classified"] == "A", "green_area_sqm"] = centroids["green_area_sqm"]

    return centroids
