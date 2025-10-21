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


def classify_by_network_distance(roads, centroids, export_csv=None, export_paths=True):
    """
    Step 5: compute shortest path distances and classify into B, C, or D.
    Also exports path geometries for QGIS visualization.

    B = ≤100m
    C = 100–250m
    D = >250m
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
        end_pt = row.get("nearest_green")

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

        # Snap nearest_road and nearest_green to actual graph nodes
        _, start_idx = kdtree.query([start_pt.x, start_pt.y], k=1)
        _, end_idx = kdtree.query([end_pt.x, end_pt.y], k=1)
        start_node = tuple(coords[start_idx])
        end_node = tuple(coords[end_idx])

        try:
            # Get shortest path and length
            path_nodes = nx.shortest_path(G, source=start_node, target=end_node, weight="weight")
            length = nx.shortest_path_length(G, source=start_node, target=end_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path_nodes = None
            length = None

        # Ensure numeric type
        try:
            length = float(length)
        except (TypeError, ValueError):
            length = None

        # Classification thresholds
        if length is not None:
            if length <= 100:
                label = "B"
            elif 100 < length <= 250:
                label = "C"
            elif length > 250:
                label = "D"
            else:
                label = "D" #standard is "none", changed to avoid nulls on export for DT uploading
        else:
            label = "D" #standard is "none", changed to avoid nulls on export for DT uploading

        # Record data
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
            # Convert to numeric coordinate tuples
            valid_coords = []
            for xy in path_nodes:
                if xy is None or len(xy) != 2:
                    continue
                x, y = xy
                if (
                    x is not None and y is not None
                    and not np.isnan(x) and not np.isnan(y)
                    and np.isfinite(x) and np.isfinite(y)
                ):
                    valid_coords.append((float(x), float(y)))

            # Remove consecutive duplicates
            deduped_coords = []
            for pt in valid_coords:
                if not deduped_coords or deduped_coords[-1] != pt:
                    deduped_coords.append(pt)

            # Create line only if >= 2 distinct, valid points
            if len(deduped_coords) > 1:
                try:
                    path_geom = LineString(deduped_coords)
                    path_records.append({
                        "centroid_id": cid,
                        "classification": label,
                        "distance": length,
                        "geometry": path_geom
                    })
                except Exception as e:
                    skipped_paths += 1
                    print(f"⚠️ Skipped invalid path for centroid {cid}: {e}")
            else:
                skipped_paths += 1  # single or invalid coordinate list
                print(f"⚠️ Skipped centroid {cid}: path had <2 valid points or duplicate coordinates.")


    # Export extended debug CSV
    if export_csv:
        df = pd.DataFrame(distances)
        df.to_csv(export_csv, index=False)
        print(f"✅ Exported extended distance debug CSV: {export_csv}")

    # Export zero-distance cases as GeoJSON for QGIS inspection
    zero_debug = [
        {
            "centroid_id": d["centroid_id"],
            "geometry": LineString([
                Point(d["start_x"], d["start_y"]),
                Point(d["end_x"], d["end_y"])
            ])
        }
        for d in distances if d["distance"] == 0 and d["start_x"] is not None
    ]

    if zero_debug:
        zero_gdf = gpd.GeoDataFrame(zero_debug, geometry="geometry", crs=centroids.crs)
        zero_gdf.to_crs(epsg=4326).to_file("output/debug_zero_distance_Brabrand_Horticulture.geojson", driver="GeoJSON") #change file name here
        print(f"⚠️ Exported {len(zero_gdf)} zero-distance cases for QGIS inspection.")

    # Export all computed paths
    if path_records:
        paths_gdf = gpd.GeoDataFrame(path_records, geometry="geometry", crs=centroids.crs)
        paths_gdf.to_crs(epsg=4326).to_file("output/debug_paths_Brabrand_Horticulture.geojson", driver="GeoJSON") #change file name here
        print(f"📍 Exported {len(paths_gdf)} network paths for QGIS visualization.")
    if skipped_paths > 0:
        print(f"⚠️ Skipped {skipped_paths} single-point paths (likely zero-distance cases).")

    # Update centroids with results
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

    return centroids

