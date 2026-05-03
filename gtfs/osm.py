import json
import requests
import folium

EXCLUDE_OPERATORS = ["flixbus", "itabus", "marino", "eurolines", "blablacar"]
EXCLUDE_NETWORKS = ["Flixbus"]
EXCLUDE_NAMES = []


def fetch_lines():
    query = """
        [out:json][timeout:90];
        area["name"="Torino"]["admin_level"="8"]->.a;
        (
        relation(area.a)["type"="route"]
        ["route"~"bus|tram|subway"]
        ["operator"!~"flixbus|itabus|marino",i]
        ["ref"!~"frecciarossa",i]
        ["network"!~"flixbus|TGV",i]
        ["name"!~"speciale|festivo",i];
        );
        out geom;
        """
    url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "TurinTransitMapper/1.0"}
    response = requests.post(url, data={"data": query}, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()

def fetch_all():
    query = """
    [out:json][timeout:190];
    area["name"="Torino"]["admin_level"="8"]->.a;
    (
    relation(area.a)["type"="route"]
        ["route"~"bus|tram|subway"]
        ["operator"!~"flixbus|itabus|marino",i]
        ["network"!~"flixbus|TGV",i]
        ["name"!~"speciale|festivo",i];
    )->.routes;
    .routes out geom;
    node(r.routes);
    out body;
    """
    url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "TurinTransitMapper/1.0"}
    response = requests.post(url, data={"data": query}, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()

def fetch_transit_network():
    routes_query = """
    [out:json][timeout:90];
    area["name"="Torino"]["admin_level"="8"]->.a;
    (
      relation(area.a)
      ["type"="route"]
        ["route"~"bus|tram|subway"]
        ["operator"!~"flixbus|itabus|marino",i]
        ["ref"!~"frecciarossa",i]
        ["network"!~"flixbus|TGV",i]
        ["name"!~"speciale|festivo",i];
    );
    out geom;
    """

    stops_query = """
[out:json][timeout:90];
area["name"="Torino"]["admin_level"="8"]->.a;
(
  relation(area.a)["type"="route"]["route"~"bus|tram|subway|train"]["operator"!~"[Ff]lixbus|[Ii]tabus|[Mm]arino"];
)->.routes;
(
  node(r.routes)["public_transport"="platform"];
  node(r.routes)["highway"="bus_stop"];
);
out body;
"""

    url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "TurinTransitMapper/1.0"}

    print("Fetching routes...")
    r1 = requests.post(url, data={"data": routes_query}, headers=headers, timeout=120)
    r1.raise_for_status()
    routes_data = r1.json()

    print("Fetching stops...")
    r2 = requests.post(url, data={"data": stops_query}, headers=headers, timeout=120)
    r2.raise_for_status()
    stops_data = r2.json()
    
    print("Routes elements:", len(routes_data.get("elements", [])))
    print("Stops elements:", len(stops_data.get("elements", [])))
    if len(routes_data.get("elements", [])) == 0 or len(stops_data.get("elements", [])) == 0:
        print(r1.text[:500])

    routes_data["elements"] += stops_data["elements"]
    return routes_data

def is_excluded(props):
    operator = props.get("operator", "").lower()
    network = props.get("network", "").lower()
    name = props.get("name", "").lower()
    if any(x in operator for x in EXCLUDE_OPERATORS):
        return True
    if any(x in network for x in EXCLUDE_NETWORKS):
        return True
    if any(x in name for x in EXCLUDE_NAMES):
        return True
    return False


def save_as_geojson(data, filename="osm_data/torino_transit.geojson"):
    stop_tags = {
        el["id"]: el.get("tags", {})
        for el in data.get("elements", [])
        if el["type"] == "node"
    }

    features = []
    seen_stops = set()

    for rel in data.get("elements", []):
        if rel["type"] != "relation" or "members" not in rel:
            continue

        props = rel.get("tags", {})
        if is_excluded(props):
            continue

        coords = [
            [[p["lon"], p["lat"]] for p in member["geometry"]]
            for member in rel["members"]
            if "geometry" in member
        ]
        if coords:
            features.append({
                "type": "Feature",
                "geometry": {"type": "MultiLineString", "coordinates": coords},
                "properties": props
            })

        for member in rel["members"]:
            if member["type"] != "node" or member.get("role") not in ("stop", "stop_position"):
                continue
            node_id = member["ref"]
            if node_id in seen_stops:
                continue
            seen_stops.add(node_id)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [member["lon"], member["lat"]]},
                "properties": stop_tags.get(node_id, {})
            })

    geojson_data = {"type": "FeatureCollection", "features": features}
    with open(filename, "w") as f:
        json.dump(geojson_data, f)
    print(f"Saved {len(features)} features to {filename}")


data = fetch_all()
save_as_geojson(data)