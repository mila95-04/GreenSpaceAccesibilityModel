import geopandas as gpd

def assign_classification_to_grid(grid, centroids, output_path="output/grid_classified.geojson"):
    """
    Step 6: Assign classification from centroids back to grid polygons.
    Each grid cell inherits the classification of its centroid.
    """
    # Ensure both are in the same CRS
    assert grid.crs == centroids.crs, "CRS mismatch between grid and centroids!"

    # Join grid polygons with centroid classification (one-to-one)
    grid["centroid_id"] = grid.index
    centroids["centroid_id"] = centroids.index

    classified_grid = grid.merge(
        centroids[["centroid_id", "classified"]],
        on="centroid_id",
        how="left"
    )

    # Save for visualization in QGIS
    classified_grid.to_crs(epsg=4326).to_file(output_path, driver="GeoJSON")

    return classified_grid
