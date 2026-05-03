import csv
import io
import json
import zipfile
from collections import defaultdict

GTFS_ZIP = "gtt_gtfs_data/gtt_gtfs.zip"
OUTPUT = "gtt_gtfs_data/stops.geojson"


def read_csv(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, "utf-8")))


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
    served = sorted(
        {route_info[r]["route_short_name"] for r in stop_routes.get(s["stop_id"], []) if r in route_info}
    )
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(s["stop_lon"]), float(s["stop_lat"])]
        },
        "properties": {
            "stop_id": s["stop_id"],
            "name": s["stop_name"],
            "routes": served
        }
    })

geojson = {"type": "FeatureCollection", "features": features}
with open(OUTPUT, "w") as f:
    json.dump(geojson, f)

print(f"Saved {len(features)} stops to {OUTPUT}")