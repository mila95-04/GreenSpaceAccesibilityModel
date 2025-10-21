from io_utils import load_geojson, save_geojson
from step1_extract_centroids import extract_centroids  
from step2_check_direct_overlap import classify_centroids_direct_overlap
from step3_buffer_overlap import classify_centroids_with_buffer
from step4_find_nearest_nodes import find_nearest_nodes
from step5_network_distance import classify_by_network_distance
from step6_assign_to_grid import assign_classification_to_grid



def main():
    # Load data
    grid = load_geojson("data/Brabrand_G100.geojson")
    green_zones = load_geojson("data\Brabrand_GreenZones_Compiled.geojson")
    roads = load_geojson("data/BrabrandNetwork_Filtered.geojson")

    # Step 1: extract centroids
    centroids = extract_centroids(grid)

    # Step 2: direct overlap (A)
    centroids = classify_centroids_direct_overlap(centroids, green_zones)

    # Step 3: buffer overlap (B)
    centroids = classify_centroids_with_buffer(
        centroids,
        green_zones,
        buffer_distance=150, #buffer changed to 150, remember to change back on the step script
        export_debug="output/buffer_debug_G100_Brabrand_GreenZones_Compiled.geojson" #remember to change back to G250 if grid changes
    )

     # Step 4: nearest road + nearest green zone
    centroids = find_nearest_nodes(centroids, roads, green_zones, search_radius=200)
            #buffer changed to 250, remember to change back on the step script
     
    # Step 5: network distance classification (B, C, D)
    centroids = classify_by_network_distance(
        roads,
        centroids,
        export_csv="output/distances_debug_G100_Brabrand_GreenZones_Compiled.csv" #remember to change back to G250 if grid changes
    )

    # Step 6: assign classifications back to the grid polygons
    classified_grid = assign_classification_to_grid(
        grid,
        centroids,
        output_path="output/grid_classified_Brabrand_GreenZones_Compiled.geojson" #remember to change back to G250 if grid changes, also version
    )

    # Save final classified centroids
    save_geojson(centroids, "output/centroids_classified_G100_Brabrand_GreenZones_Compiled.geojson") #remember to change back to G250 if grid changes, also version


if __name__ == "__main__":
    main()