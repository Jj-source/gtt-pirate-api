import csv
import io
import json
import zipfile
from collections import defaultdict

GTFS_ZIP = "gtt_gtfs_data/gtt_gtfs.zip"
OUTPUT = "gtt_gtfs_data/stops.geojson"

# get city from stop_attributes
# join on id

def read_csv(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, "utf-8")))

TO_REMOVE = {"special", "festivo"}

def feriale_o_speciale(route):
    return any(kw in route.get("route_short_name").lower() for kw in TO_REMOVE)

with zipfile.ZipFile(GTFS_ZIP) as z:
    stops = read_csv(z, "stops.txt")
    routes = read_csv(z, "routes.txt")
    trips = read_csv(z, "trips.txt")
    stop_times = read_csv(z, "stop_times.txt")

route_info = {r["route_id"]: r for r in routes}
trip_to_route = {t["trip_id"]: t["route_id"] for t in trips}

stop_routes = defaultdict(set)
for st in stop_times:
    route_id = trip_to_route.get(st["trip_id"])
    if route_id:
        stop_routes[st["stop_id"]].add(route_id)

features = []
for s in stops:
    
    route_ids = [r for r in stop_routes.get(s["stop_id"], []) if r in route_info]

    normal_routes = [r for r in route_ids if not feriale_o_speciale(route_info[r])]
    special_routes = [r for r in route_ids if feriale_o_speciale(route_info[r])]

    # Skip stop if it has no normal routes at all
    if not normal_routes and route_ids:
        continue
    
    served = sorted(
        {route_info[r]["route_short_name"] for r in stop_routes.get(s["stop_id"], []) if r in route_info and not feriale_o_speciale(route_info[r])}
    )
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(s["stop_lon"]), float(s["stop_lat"])]
        },
        "properties": {
            "stop_id": s["stop_id"],
            "stop_code": s["stop_code"],
            "name": s["stop_name"],
            "routes": served,
            "stop_desc": s["stop_desc"],
            "zone_id": s["zone_id"],
            "wheelchair_boarding": s["wheelchair_boarding"]
        }
    })

geojson = {"type": "FeatureCollection", "features": features}
with open(OUTPUT, "w") as f:
    json.dump(geojson, f)

print(f"Saved {len(features)} stops to {OUTPUT}")