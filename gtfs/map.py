import json
import folium

INPUT_FILE = "osm_data/torino_transit.geojson"


def get_color(route_type):
    # Standard transit colors
    colors = {
        "subway": "red",
        "tram": "green",
        "bus": "orange"
    }
    return colors.get(route_type, "gray")
  
def create_map(input_file):
    with open(input_file) as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"Total features: {len(features)}")

    stop_tags = {
        f["geometry"]["coordinates"][0]: f
        for f in features
        if f["geometry"]["type"] == "Point"
    }

    m = folium.Map(location=[45.0703, 7.6869], zoom_start=12, tiles="cartodbpositron")

    for feature in features:
        props = feature["properties"]
        geom = feature["geometry"]
        route_type = props.get("route", "")

        if geom["type"] == "MultiLineString":
            for line in geom["coordinates"]:
                locations = [(lat, lon) for lon, lat in line]
                folium.PolyLine(
                    locations=locations,
                    color=get_color(route_type),
                    weight=4 if route_type in ["subway", "tram"] else 2,
                    opacity=0.8,
                    tooltip=f"{route_type.upper()} {props.get('ref', '')}: {props.get('name', '')}"
                ).add_to(m)

        elif geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            folium.CircleMarker(
                location=(lat, lon),
                radius=4,
                color="blue",
                fill=True,
                fill_opacity=0.9,
                tooltip=props.get("name", "stop")
            ).add_to(m)

    m.save("torino_transit_map.html")
    print("Success: 'torino_transit_map.html' generated.")


create_map(INPUT_FILE)