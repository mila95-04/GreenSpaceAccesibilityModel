import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString
from scipy.spatial import cKDTree
import numpy as np


def build_graph(roads_gdf):
    """Build a NetworkX graph from road LineStrings."""
    G = nx.Graph()
    for _, row in roads_gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
            for u, v in zip(coords[:-1], coords[1:]):
                dist = Point(u).distance(Point(v))
                G.add_edge(u, v, weight=dist)
    return G


def classify_by_network_distance(roads, centroids, green_zones=None, export_csv=None, export_paths=True):
    """
    Step 5: compute shortest path distances and classify into B, C, or D.
    Also assigns:
        - green_id (for C/D)
        - green_area_sqm (for C/D)
    """
    # Build graph from roads
    G = build_graph(roads)

    # Prepare KDTree from graph nodes
    nodes = list(G.nodes)
    coords = np.array(nodes)
    kdtree = cKDTree(coords)

    distances = []
    path_records = []  # for path geometries
    skipped_paths = 0  # counter for single-point paths

    for cid, row in centroids.iterrows():
        # Skip if already classified as A or B
        if row.get("classified") in ["A", "B"]:
            continue

        start_pt = row.get("nearest_road")
        end_pt = row.get("nearest_green_geom")  # <-- UPDATED: use nearest geometry saved in Step 4

        if start_pt is None or end_pt is None:
            distances.append({
                "centroid_id": cid,
                "distance": None,
                "classification": None,
                "start_x": None,
                "start_y": None,
                "end_x": None,
                "end_y": None,
                "path_nodes": None
            })
            continue

        # Snap nearest_road and nearest_green to graph nodes
        _, start_idx = kdtree.query([start_pt.x, start_pt.y], k=1)
        _, end_idx = kdtree.query([end_pt.x, end_pt.y], k=1)
        start_node = tuple(coords[start_idx])
        end_node = tuple(coords[end_idx])

        try:
            path_nodes = nx.shortest_path(G, source=start_node, target=end_node, weight="weight")
            length = nx.shortest_path_length(G, source=start_node, target=end_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path_nodes = None
            length = None

        try:
            length = float(length)
        except (TypeError, ValueError):
            length = None

        # Classification rules
        if length is not None:
            if length <= 100:
                label = "B"
            elif 100 < length <= 250:
                label = "C"
            elif length > 250:
                label = "D"
            else:
                label = "D"
        else:
            label = "D"

        # Record
        distances.append({
            "centroid_id": cid,
            "distance": length,
            "classification": label,
            "start_x": start_pt.x,
            "start_y": start_pt.y,
            "end_x": end_pt.x,
            "end_y": end_pt.y,
            "path_nodes": path_nodes
        })

        # --- Create path geometry safely for visualization ---
        if path_nodes and export_paths:
            valid_coords = []
            for xy in path_nodes:
                if xy is None or len(xy) != 2:
                    continue
                x, y = xy
                if x is not None and y is not None and np.isfinite(x) and np.isfinite(y):
                    valid_coords.append((float(x), float(y)))

            # Remove duplicate consecutive points
            deduped_coords = []
            for pt in valid_coords:
                if not deduped_coords or deduped_coords[-1] != pt:
                    deduped_coords.append(pt)

            if len(deduped_coords) > 1:
                try:
                    path_geom = LineString(deduped_coords)
                    path_records.append({
                        "centroid_id": cid,
                        "classification": label,
                        "distance": length,
                        "geometry": path_geom
                    })
                except Exception:
                    skipped_paths += 1
            else:
                skipped_paths += 1

    # Export debug CSV
    if export_csv:
        pd.DataFrame(distances).to_csv(export_csv, index=False)

    # Update centroid attributes with results
    dist_map = {d["centroid_id"]: d for d in distances}

    centroids["network_distance"] = centroids.index.map(
        lambda cid: dist_map[cid]["distance"] if cid in dist_map else None
    )
    centroids["classified"] = centroids.apply(
        lambda row: row["classified"]
        if row["classified"] is not None
        else (dist_map[row.name]["classification"] if row.name in dist_map else None),
        axis=1,
    )

    # --------------------------------------------------------------------
    # 🔥 NEW PART: Assign green_id and green_area_sqm for C/D centroids
    # --------------------------------------------------------------------
    if green_zones is not None:
        # Ensure polygon IDs and areas exist
        if "green_id" not in green_zones.columns:
            green_zones["green_id"] = green_zones.index
        if "green_area_sqm" not in green_zones.columns:
            green_zones["green_area_sqm"] = green_zones.geometry.area

        # Assign green_id for C and D cells using Step 4 result
        centroids.loc[
            centroids["classified"].isin(["C", "D"]),
            "green_id"
        ] = centroids["nearest_green_id"]

        # Assign area
        centroids["green_area_sqm"] = centroids["green_id"].map(
            green_zones.set_index("green_id")["green_area_sqm"]
        )

    return centroids
