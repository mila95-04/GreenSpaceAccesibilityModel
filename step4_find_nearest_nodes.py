from shapely.ops import nearest_points
import geopandas as gpd

def find_nearest_nodes(centroids, roads, green_zones, search_radius=200):
    """
    Step 4: find nearest road edge and nearest green zone polygon
    for centroids not yet classified (skip A and B).
    
    This version also computes:
        - nearest_green_id (polygon index)
    but does NOT classify. Classification happens in Step 5.
    """

    # Work only with unclassified centroids
    unclassified = centroids[~centroids["classified"].isin(["A", "B"])].copy()

    # Ensure green_zones have polygon IDs
    if "green_id" not in green_zones.columns:
        green_zones["green_id"] = green_zones.index

    # Ensure green_zones have areas (needed later in step 5)
    if "green_area_sqm" not in green_zones.columns:
        green_zones["green_area_sqm"] = green_zones.geometry.area

    # Build unions for nearest searches
    road_union = roads.unary_union
    green_union = green_zones.unary_union

    # Ensure output columns exist in centroids
    if "nearest_road" not in centroids.columns:
        centroids["nearest_road"] = None
    if "nearest_green_id" not in centroids.columns:
        centroids["nearest_green_id"] = None
    if "nearest_green_geom" not in centroids.columns:
        centroids["nearest_green_geom"] = None

    # Iterate only over unclassified centroids
    for idx, row in unclassified.iterrows():
        point = row.geometry

        # Nearest road edge geometry
        nearest_road_geom = nearest_points(point, road_union)[1]
        centroids.at[idx, "nearest_road"] = nearest_road_geom

        # Nearest green polygon geometry
        nearest_green_geom = nearest_points(point, green_union)[1]
        centroids.at[idx, "nearest_green_geom"] = nearest_green_geom

        # Determine which actual polygon this geometry belongs to
        nearest_green_id = green_zones.distance(nearest_green_geom).idxmin()
        centroids.at[idx, "nearest_green_id"] = nearest_green_id

    return centroids
