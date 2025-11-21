import geopandas as gpd

def classify_centroids_direct_overlap(centroids, green_zones, crs_metric=3857):
    """
    Step 2: classify centroids directly overlapping green polygons as A.
    Also assigns:
        - green_id (polygon index)
        - green_area_sqm (area of that polygon)
    """

    # Ensure consistent CRS
    centroids = centroids.to_crs(epsg=crs_metric).copy()
    green_zones = green_zones.to_crs(epsg=crs_metric)

    # Create a green_id column in the green zones
    if "green_id" not in green_zones.columns:
        green_zones["green_id"] = green_zones.index

    # Precompute green polygon areas
    if "green_area_sqm" not in green_zones.columns:
        green_zones["green_area_sqm"] = green_zones.geometry.area

    # Spatial join: intersect centroids with green polygons
    joined = gpd.sjoin(centroids, green_zones, how="left", predicate="intersects")

    # Classification: A if intersecting a green polygon
    centroids["classified"] = joined["index_right"].notnull().map(
        lambda x: "A" if x else None
    )

    # Assign green_id for intersecting centroids
    centroids["green_id"] = joined["green_id"]

    # Assign green area for intersecting centroids
    centroids["green_area_sqm"] = centroids["green_id"].map(
        green_zones.set_index("green_id")["green_area_sqm"]
    )

    return centroids
