from shapely.ops import nearest_points

def find_nearest_nodes(centroids, roads, green_zones, search_radius=200):
    """
    Step 4: find nearest road edge and nearest green zone polygon
    for centroids not yet classified (skip A and B).
    """

    # Only work with unclassified centroids
    unclassified = centroids[~centroids["classified"].isin(["A", "B"])].copy()

    # Build unions for faster nearest search
    road_union = roads.unary_union
    green_union = green_zones.unary_union

    # Ensure columns exist
    if "nearest_road" not in centroids.columns:
        centroids["nearest_road"] = None
    if "nearest_green" not in centroids.columns:
        centroids["nearest_green"] = None

    # Iterate only over unclassified centroids
    for idx, row in unclassified.iterrows():
        point = row.geometry

        # nearest road edge
        nearest_road = nearest_points(point, road_union)[1]
        centroids.at[idx, "nearest_road"] = nearest_road

        # nearest green zone polygon
        nearest_green = nearest_points(point, green_union)[1]
        centroids.at[idx, "nearest_green"] = nearest_green

    return centroids
