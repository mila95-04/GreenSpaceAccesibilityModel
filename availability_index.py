# availability_index.py
import geopandas as gpd
import pandas as pd
import numpy as np
import os

# ---------- USER PARAMETERS ----------
GRID_PATH = r"C:\Users\Ceballosc\OneDrive - AIT\Green space accesibility model\GreenSpaceAccesibilityModel\data\Brabrand_age_and_occupancy_250m.json"   # your uploaded file
GREEN_PATH = r"C:\Users\Ceballosc\OneDrive - AIT\Green space accesibility model\GreenSpaceAccesibilityModel\data\Brabrand_GreenZones_Compiled.geojson"  # set to e.g. "/path/to/green_spaces.geojson" OR None if you already have cell->green mapping
OUTPUT_PATH = r"C:\Users\Ceballosc\OneDrive - AIT\Green space accesibility model\GreenSpaceAccesibilityModel\output\Availability Index\Braband_250for_Availabilityindex_V2.json"
# -------------------------------------

def load_grid(path):
    g = gpd.read_file(path)
    # ensure CRS is set (file uses EPSG:25832). If missing, set it:
    if g.crs is None:
        g.set_crs(epsg=25832, inplace=True)
    else:
        # normalize to EPSG:25832 (units = metres -> area in sqm)
        g = g.to_crs(epsg=25832)
    return g

def load_greens(path, target_crs=25832):
    greens = gpd.read_file(path)
    # convert to same CRS (meters)
    if greens.crs is None:
        greens.set_crs(epsg=target_crs, inplace=True)
    else:
        greens = greens.to_crs(epsg=target_crs)
    # compute area in square metres
    greens["green_area_sqm"] = greens.geometry.area
    # ensure an id column exists
    if "green_id" not in greens.columns:
        greens = greens.reset_index().rename(columns={"index":"green_id"})
    return greens

def compute_availability_from_nearest(grid_gdf, greens_gdf, pop_col="Age total"):
    # compute centroids (in same CRS)
    centroids = grid_gdf.copy()
    centroids["geometry"] = centroids.geometry.centroid

    # use geopandas sjoin_nearest to find the nearest green polygon for each centroid
    # requires geopandas >= 0.10; if unavailable you'll need custom spatial index nearest
    joined = gpd.sjoin_nearest(centroids, greens_gdf[["green_id","green_area_sqm","geometry"]], how="left", distance_col="dist_m")
    # joined now has green_id and green_area_sqm added
    # compute availability
    def safe_divide(area, pop):
        try:
            if pop is None:
                return None
            if pd.isna(pop):
                return None
            if pop <= 0:
                return None  # avoid division by zero: store None (or np.nan) to indicate no population
            return float(area) / float(pop)
        except Exception:
            return None

    joined["availability_index"] = joined.apply(
        lambda r: safe_divide(r.get("green_area_sqm", np.nan), r.get(pop_col, np.nan)), axis=1
    )

    # take availability_index and nearest green id back to original grid_gdf (matching by index)
    result = grid_gdf.copy()
    result["availability_index"] = joined["availability_index"].values
    result["closest_green_id"] = joined["green_id"].values
    result["closest_green_distance_m"] = joined["dist_m"].values
    return result

def compute_availability_from_mapping(grid_gdf, greens_gdf, mapping_col="closest_green_id", pop_col="Age total"):
    # mapping_col must contain green id that matches greens_gdf.green_id
    # ensure greens indexed by green_id
    greens_lookup = greens_gdf.set_index("green_id")["green_area_sqm"].to_dict()
    def safe_divide_by_lookup(row):
        gid = row.get(mapping_col)
        area = greens_lookup.get(gid) if pd.notna(gid) else None
        pop = row.get(pop_col)
        if area is None or pop is None or pd.isna(pop) or pop <= 0:
            return None
        return float(area) / float(pop)
    grid_gdf["availability_index"] = grid_gdf.apply(safe_divide_by_lookup, axis=1)
    return grid_gdf

def main():
    # Load grid
    grid = load_grid(GRID_PATH)
    # check population column exists
    if "Age total" not in grid.columns and "Age_total" not in grid.columns:
        raise ValueError("Population column 'Age total' not found in grid properties. File must contain a total population per cell.")
    pop_col = "Age total" if "Age total" in grid.columns else "Age_total"

    if GREEN_PATH:
        greens = load_greens(GREEN_PATH)
        result = compute_availability_from_nearest(grid, greens, pop_col=pop_col)
    else:
        # if user already has a column linking to nearest green (e.g. 'closest_green_id'), use that mapping
        if "closest_green_id" in grid.columns:
            # but to compute area we still need a greens file or a dataframe of green areas
            # If there is also a green_area_sqm column already in the accessibility model, we can use it:
            if "closest_green_area_sqm" in grid.columns:
                grid["availability_index"] = grid.apply(
                    lambda r: (None if (r.get(pop_col) is None or r.get(pop_col) <= 0) else r.get("closest_green_area_sqm") / r.get(pop_col)),
                    axis=1
                )
                result = grid
            else:
                raise ValueError("Grid contains 'closest_green_id' but there is no green-area lookup in the grid. Provide GREEN_PATH or a greens table.")
        else:
            raise ValueError("No GREEN_PATH provided and no existing closest_green_id mapping found. Provide a green-space GeoJSON path or an existing mapping column.")

    # Save output
    # keep the same geometry type (polygons). availability_index is in properties.
    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # write GeoJSON
    result.to_file(OUTPUT_PATH, driver="GeoJSON")
    print(f"Saved output with availability_index to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
