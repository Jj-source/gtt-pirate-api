import json
import requests

import logging

logging.basicConfig(
    filename="osm_debug.log",
    level=logging.DEBUG,
    format="%(levelname)s %(message)s",
    filemode="w"
)

EXCLUDE_OPERATORS = ["flixbus", "itabus", "marino", "eurolines", "blablacar"]
EXCLUDE_NETWORKS = ["flixbus"]
EXCLUDE_NAMES = []

STOP_ROLES = {"stop", "stop_position", "platform"}

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
    node_tags = {
        el["id"]: el.get("tags", {})
        for el in data.get("elements", [])
        if el["type"] == "node"
    }

    features = []
    seen_node_ids = set()

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
            if member["type"] != "node" or member.get("role") not in STOP_ROLES:
                continue
            node_id = member["ref"]
            if node_id in seen_node_ids:
                continue
            seen_node_ids.add(node_id)
            
            if member["lon"] is None or member["lat"] is None:
                logging.warning(f"node {node_id} role={member.get('role')} missing coords")
            if not node_tags:
                logging.warning(f"node {node_id} role={member.get('role')} missing tags")
            
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [member["lon"], member["lat"]]},
                "properties": node_tags.get(node_id, {})
            })

    geojson_data = {"type": "FeatureCollection", "features": features}
    with open(filename, "w") as f:
        json.dump(geojson_data, f)
    print(f"Saved {len(features)} features to {filename}")


data = fetch_all()
types = [el["type"] for el in data["elements"]]
print("relations:", types.count("relation"), "nodes:", types.count("node"))
save_as_geojson(data)