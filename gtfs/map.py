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
    if not data:
        return
      
    for rel in data.get("elements", []):
      if rel["type"] != "relation":
          continue
      for member in rel.get("members", []):
          if member["type"] == "node":
              print(member)
              break
      break
    return

    stop_tags = {
        el["id"]: {"lat": el["lat"], "lon": el["lon"], "tags": el.get("tags", {})}
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }

    m = folium.Map(location=[45.0703, 7.6869], zoom_start=12, tiles="cartodbpositron")
    seen_stops = set()

    for rel in data.get("elements", []):
        if rel["type"] != "relation":
            continue

        tags = rel.get("tags", {})
        route_type = tags.get("route")
        ref = tags.get("ref", "")
        name = tags.get("name", "")

        for member in rel.get("members", []):
            if "geometry" in member:
                locations = [(p["lat"], p["lon"]) for p in member["geometry"]]
                folium.PolyLine(
                    locations=locations,
                    color=get_color(route_type),
                    weight=4 if route_type in ["subway", "tram"] else 2,
                    opacity=0.8,
                    tooltip=f"{route_type.upper()} {ref}: {name}"
                ).add_to(m)

            if member["type"] == "node" and member.get("role") in ("stop", "stop_position"):
                node_id = member["ref"]
                if node_id in seen_stops:
                    continue
                seen_stops.add(node_id)
                tags = stop_tags.get(node_id, {})
                folium.CircleMarker(
                    location=(member["lat"], member["lon"]),
                    radius=4,
                    color=get_color(route_type),
                    fill=True,
                    fill_opacity=0.9,
                    tooltip=tags.get("name", node_id)
                ).add_to(m)

    m.save("torino_transit_map.html")
    print("Success: 'torino_transit_map.html' generated.")


create_map(INPUT_FILE)