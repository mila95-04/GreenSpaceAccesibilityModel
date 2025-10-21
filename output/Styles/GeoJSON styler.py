import json

# Input and output paths
input_file = "C:\Users\Ceballosc\Documents\Green space mapping\FullModel_V1\output\grid_classified_V7.geojson"
output_file = "C:\Users\Ceballosc\Documents\Green space mapping\FullModel_V1\output\grid_classified_styled.geojson"

# Define style per class
style_map = {
    "A": {"fill": "#abdda4", "fill-opacity": 0.5, "stroke": "none"},
    "B": {"fill": "#ffffbf", "fill-opacity": 0.5, "stroke": "none"},
    "C": {"fill": "#fdae61", "fill-opacity": 0.5, "stroke": "none"},
    "D": {"fill": "#d7191c", "fill-opacity": 0.5, "stroke": "none"},
}

# Load GeoJSON
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Add style properties
for feature in data["features"]:
    cls = feature["properties"].get("class")  # adapt if field name differs
    if cls in style_map:
        feature["properties"].update(style_map[cls])
    else:
        # Optional default style for unclassified cells
        feature["properties"].update({"fill": "#cccccc", "fill-opacity": 0.3, "stroke": "none"})

# Save new styled GeoJSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Styled GeoJSON saved as: {output_file}")
