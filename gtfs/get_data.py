from collections import defaultdict
import zipfile, io, csv
from google.transit import gtfs_realtime_pb2  # pip install gtfs-realtime-bindings
import networkx as nx
from pathlib import Path

GTFS_ZIP = "gtt_gtfs_data/gtt_gtfs.zip"

# ── Load static GTFS ─────────────────────────────────────────────
def read_csv(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, "utf-8")))

with zipfile.ZipFile(GTFS_ZIP) as z:
    stops      = read_csv(z, "stops.txt")
    routes     = read_csv(z, "routes.txt")
    trips      = read_csv(z, "trips.txt")
    stop_times = read_csv(z, "stop_times.txt")

print(f"Stops: {len(stops)}, Routes: {len(routes)}, Trips: {len(trips)}, StopTimes: {len(stop_times)}")

# ── Build NetworkX graph ─────────────────────────────────────────
G = nx.DiGraph()

# Nodes: one per stop
for s in stops:
    G.add_node(s["stop_id"],
               name=s["stop_name"],
               lat=float(s["stop_lat"]),
               lon=float(s["stop_lon"]))

# Index lookups
trip_to_route = {t["trip_id"]: t["route_id"] for t in trips}
route_info    = {r["route_id"]: r for r in routes}

# Group stop_times by trip, sort by stop_sequence
by_trip = defaultdict(list)
for st in stop_times:
    by_trip[st["trip_id"]].append(st)

# Edges: consecutive stops within each trip
# Collapse multiple trips into unique (stop_a, stop_b, route_id) — keep set of trips
edge_data = defaultdict(lambda: {"trips": set(), "route_short_name": ""})

for trip_id, sts in by_trip.items():
    sts_sorted = sorted(sts, key=lambda x: int(x["stop_sequence"]))
    route_id   = trip_to_route.get(trip_id, "")
    short_name = route_info.get(route_id, {}).get("route_short_name", route_id)
    for a, b in zip(sts_sorted, sts_sorted[1:]):
        key = (a["stop_id"], b["stop_id"], route_id)
        edge_data[key]["trips"].add(trip_id)
        edge_data[key]["route_short_name"] = short_name

for (src, dst, route_id), data in edge_data.items():
    G.add_edge(src, dst,
               route_id=route_id,
               route_short_name=data["route_short_name"],
               n_trips=len(data["trips"]))

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ── Basic stats ──────────────────────────────────────────────────
print(f"Lines (routes): {len(routes)}")
print(f"Weakly connected components: {nx.number_weakly_connected_components(G)}")

# Most connected stops (by degree)
top_stops = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
stop_name = {s["stop_id"]: s["stop_name"] for s in stops}
print("\nTop 10 stops by degree:")
for stop_id, deg in top_stops:
    print(f"  {stop_name.get(stop_id, stop_id)}: {deg}")


print(f"Stops: {len(stops)}, Routes: {len(routes)}, Trips: {len(trips)}, StopTimes: {len(stop_times)}")


import folium

m = folium.Map(location=[45.0703, 7.6869], zoom_start=12)

# one color per route
import hashlib
def route_color(route_id):
    h = hashlib.md5(route_id.encode()).hexdigest()
    return f"#{h[:6]}"

stop_coords = {s["stop_id"]: (float(s["stop_lat"]), float(s["stop_lon"])) for s in stops}

for (src, dst, route_id), data in edge_data.items():
    if src in stop_coords and dst in stop_coords:
        folium.PolyLine(
            [stop_coords[src], stop_coords[dst]],
            color=route_color(route_id),
            weight=1.5,
            opacity=0.6,
            tooltip=data["route_short_name"]
        ).add_to(m)

m.save("data/network_map.html")
print("Saved to data/network_map.html")











## ── 2. GTFS REALTIME ─────────────────────────────────────────────
#
#RT_FILES = {
#    "trip_updates":      Path("data/trip_update.bin"),
#    "vehicle_positions": Path("data/vehicle_position.bin"),
#    "alerts":            Path("data/alerts.bin"),
#}
#
#def fetch_rt(path):
#    feed = gtfs_realtime_pb2.FeedMessage()
#    feed.ParseFromString(path.read_bytes())
#    return feed
#
#vp_feed = fetch_rt(RT_FILES["vehicle_positions"])
#print(f"Entities: {len(vp_feed.entity)}")
#trip_feed = fetch_rt(RT_FILES["vehicle_positions"])
#print(f"Entities: {len(trip_feed.entity)}")
#
#for entity in vp_feed.entity[:50]:
#    if entity.HasField("vehicle"):
#        v = entity.vehicle
#        print(v.vehicle.id, v.position.latitude, v.position.longitude)
#
## ── 3. BUILD NETWORKX GRAPH ──────────────────────────────────────
#def build_graph(stops, stop_times, trips):
#    G = nx.DiGraph()
#
#    # Nodes: one per stop
#    stop_map = {s["stop_id"]: s for s in stops}
#    for s in stops:
#        G.add_node(s["stop_id"],
#                   name=s["stop_name"],
#                   lat=float(s["stop_lat"]),
#                   lon=float(s["stop_lon"]))
#
#    # Edges: consecutive stops within each trip
#    trip_map = {t["trip_id"]: t for t in trips}
#    # group stop_times by trip_id
#    from collections import defaultdict
#    by_trip = defaultdict(list)
#    for st in stop_times:
#        by_trip[st["trip_id"]].append(st)
#
#    for trip_id, sts in by_trip.items():
#        sts_sorted = sorted(sts, key=lambda x: int(x["stop_sequence"]))
#        route_id = trip_map.get(trip_id, {}).get("route_id", "")
#        for a, b in zip(sts_sorted, sts_sorted[1:]):
#            G.add_edge(a["stop_id"], b["stop_id"],
#                       trip_id=trip_id,
#                       route_id=route_id,
#                       dep=a["departure_time"],
#                       arr=b["arrival_time"])
#    return G
#
#G = build_graph(stops, stop_times, trips)
#print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")