import geopandas as gpd

def classify_centroids_with_buffer(centroids, green_zones, buffer_distance=150, crs_metric=3857, export_debug=None):
    """
    Step 3: classify centroids as B if a buffer overlaps green polygons.
    Also assigns:
        - green_id (polygon index)
        - green_area_sqm (area of that polygon)
    Only applied to centroids not already classified as A.
    """

    # Ensure consistent CRS
    centroids = centroids.to_crs(epsg=crs_metric).copy()
    green_zones = green_zones.to_crs(epsg=crs_metric)

    # Assign IDs if missing
    if "green_id" not in green_zones.columns:
        green_zones["green_id"] = green_zones.index

    # Precompute green polygon areas
    if "green_area_sqm" not in green_zones.columns:
        green_zones["green_area_sqm"] = green_zones.geometry.area

    # Ensure centroids have unique IDs
    centroids["centroid_id"] = centroids.index

    # Create buffers
    centroid_buffers = centroids.copy()
    centroid_buffers["geometry"] = centroid_buffers.buffer(buffer_distance)

    # Optional debug export
    if export_debug:
        centroid_buffers.to_crs(epsg=4326).to_file(export_debug, driver="GeoJSON")

    # Spatial join between buffers and green polygons
    joined = gpd.sjoin(
        centroid_buffers[["centroid_id", "geometry"]],
        green_zones,
        how="left",
        predicate="intersects"
    )

    # Identify which centroid buffers intersect green zones
    buffer_hits = joined.loc[joined["index_right"].notnull(), ["centroid_id", "green_id"]].drop_duplicates()

    # Create lookup dict
    buffer_green_lookup = buffer_hits.set_index("centroid_id")["green_id"].to_dict()

    # Assign B classification only where classification is still None
    centroids["classified"] = centroids.apply(
        lambda row: "B" if (row["classified"] is None and row["centroid_id"] in buffer_green_lookup) 
        else row["classified"],
        axis=1
    )

    # Assign green_id only for B-class cells
    centroids["green_id"] = centroids.apply(
        lambda row: buffer_green_lookup.get(row["centroid_id"], row.get("green_id", None)),
        axis=1
    )

    # Assign green_area_sqm based on green_id
    centroids["green_area_sqm"] = centroids["green_id"].map(
        green_zones.set_index("green_id")["green_area_sqm"]
    )

    return centroids


