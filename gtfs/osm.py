import requests
import folium
import random
import json

def save_as_geojson(data, filename="torino_transit.geojson"):
    features = []
    for rel in data.get("elements", []):
        if "members" in rel:
            # Combine all way geometries into a MultiLineString
            coords = []
            for member in rel["members"]:
                if "geometry" in member:
                    coords.append([[p["lon"], p["lat"]] for p in member["geometry"]])
            
            if coords:
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "MultiLineString", "coordinates": coords},
                    "properties": rel.get("tags", {})
                }
                features.append(feature)
    
    geojson_data = {"type": "FeatureCollection", "features": features}
    
    with open(filename, "w") as f:
        json.dump(geojson_data, f)
    print(f"Data saved to {filename}")

def fetch_transit_network():
    # Regular expression for route types; excludes 'FlixBus' operator
    query = """
    [out:json][timeout:90];
    area["name"="Torino"]["admin_level"="8"]->.a;
    (
      relation(area.a)["type"="route"]["route"~"bus|tram|subway|train"]["operator"!~"FlixBus"];
    );
    out geom;
    """
    url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "TurinTransitMapper/1.0"}
    
    try:
        response = requests.post(url, data={'data': query}, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        with open("osm_raw_data.json", "w") as f:
            json.dump(data, f)
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_color(route_type):
    # Standard transit colors
    colors = {
        "subway": "red",
        "tram": "green",
        "train": "blue",
        "bus": "orange"
    }
    return colors.get(route_type, "gray")

def create_map(data):
    if not data:
        return

    # Center on Torino
    m = folium.Map(location=[45.0703, 7.6869], zoom_start=12, tiles="cartodbpositron")
    
    elements = data.get("elements", [])
    for rel in elements:
        if rel["type"] == "relation":
            tags = rel.get("tags", {})
            route_type = tags.get("route")
            ref = tags.get("ref", "")
            name = tags.get("name", "")
            
            # Map members to lines
            for member in rel.get("members", []):
                if "geometry" in member:
                    locations = [(p["lat"], p["lon"]) for p in member["geometry"]]
                    
                    folium.PolyLine(
                        locations=locations,
                        color=get_color(route_type),
                        weight=4 if route_type in ['subway', 'tram'] else 2,
                        opacity=0.8,
                        tooltip=f"{route_type.upper()} {ref}: {name}"
                    ).add_to(m)

    m.save("torino_transit_map.html")
    print("Success: 'torino_transit_map.html' generated.")

data = fetch_transit_network()
if data:
    save_as_geojson(data)
    #create_map(data)
else:
    print("No data to process.")