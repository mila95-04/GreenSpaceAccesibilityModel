import geopandas as gpd

def classify_centroids_with_buffer(centroids, green_zones, buffer_distance=150, crs_metric=3857, export_debug=None):
    """Step 3: classify centroids as B if a 100m buffer overlaps green polygons.""" #buffer changed to 150, remember to change back
    centroids = centroids.to_crs(epsg=crs_metric).copy()
    green_zones = green_zones.to_crs(epsg=crs_metric)

    centroids["centroid_id"] = centroids.index
    centroid_buffers = centroids.copy()
    centroid_buffers["geometry"] = centroid_buffers.buffer(buffer_distance)

    # Export buffers for visual inspection
    if export_debug:
        centroid_buffers.to_crs(epsg=4326).to_file(export_debug, driver="GeoJSON")

    joined = gpd.sjoin(
        centroid_buffers[["centroid_id", "geometry"]],
        green_zones,
        how="left",
        predicate="intersects"
    )

    buffer_ids = joined.loc[joined["index_right"].notnull(), "centroid_id"].unique()

    centroids["classified"] = centroids.apply(
        lambda row: "B" if (row["classified"] is None and row["centroid_id"] in buffer_ids) else row["classified"],
        axis=1
    )
    return centroids

