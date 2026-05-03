import json
import folium

def filter_and_map_geojson(input_file, output_html):
    with open(input_file, "r") as f:
        geojson_data = json.load(f)

    # Center on Torino
    m = folium.Map(location=[45.0703, 7.6869], zoom_start=12, tiles="cartodbpositron")

    # Define color scheme
    colors = {
        "subway": "#D32F2F",  # Red
        "tram": "#388E3C",    # Green
        "train": "#1976D2",   # Blue
        "bus": "#F57C00"      # Orange
    }


    filtered_features = []
    filtered_count = 0
    temp = []

    for feature in geojson_data["features"]:
        props = feature["properties"]

        # 1. STRATEGIC FILTERING
        operator = props.get("operator", "").lower()
        network = props.get("network", "").upper()
        name = props.get("name", "").lower()
        
        temp.append({"op":operator,"net":network,"name":name})
        
        
        #is_long_distance = any(x in operator or x in name for x in ["flixbus", "itabus", "marino", "eurolines", "blablacar", "tgv"])
        #if is_long_distance:
        #    continue
#
        #filtered_features.append(feature)
#
        #route_type = props.get("route", "bus")
        #line_color = colors.get(route_type, "gray")
#
        #folium.GeoJson(
        #    feature,
        #    style_function=lambda x, color=line_color: {
        #        "color": color,
        #        "weight": 4 if route_type in ["subway", "tram"] else 2,
        #        "opacity": 0.7
        #    },
        #    tooltip=f"Type: {route_type.upper()}<br>Line: {props.get('ref', 'N/A')}<br>Name: {props.get('name', 'N/A')}"
        #).add_to(m)
        #filtered_count += 1
        
    

    # Save filtered GeoJSON
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features
    }
    with open("osm_data/torino_clean.geojson", "w") as out_geojson:
        json.dump(filtered_geojson, out_geojson)

    m.save(output_html)
    print(f"Mapped {filtered_count} local routes. Long-distance lines excluded.")

# Run the process
filter_and_map_geojson("osm_data/torino_transit.geojson", "torino_clean_map.html")