import json

INPUT_FILE = "gtt_gtfs_data/stops.geojson"

FILTER_NAME = ""
FILTER_ID = ""
FILTER_ROUTE = ""

def inspect_stops(input_file):
    with open(input_file) as f:
        data = json.load(f)

    stops = data["features"]
    
    def matches(props):
        if FILTER_NAME and FILTER_NAME.lower() not in props.get("name", "").lower():
            return False
        if FILTER_ID and FILTER_ID.lower() not in props.get("stop_id", "").lower():
            return False
        if FILTER_ROUTE and FILTER_ROUTE != props.get("routes", ""):
            return False
        return True

    matched = [s for s in stops if matches(s["properties"])]

    print(f"{'ID':<10} {'ROUTE':<80} {'NAME':<50}")
    print("-" * 100)
    for s in matched:
        p = s["properties"]
        print(
            f"{p.get('stop_id', ''):<10} "
            f"{', '.join(p.get('routes', [])):<80} "
            f"{p.get('name', ''):<50} "
        )

    print(f"\n{len(matched)} / {len(stops)} stops")

inspect_stops(INPUT_FILE)