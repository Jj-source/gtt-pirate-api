import json
import logging

logging.basicConfig(
    filename="osm_stops_debug.log",
    level=logging.DEBUG,
    format="%(levelname)s %(message)s",
    filemode="w"
)

INPUT_FILE = "gtt_gtfs_data/stops.geojson"

FILTER_NAME = ""
FILTER_ID = ""
FILTER_ROUTE = ""

def matches(props):
        if FILTER_NAME and FILTER_NAME.lower() not in props.get("name", "").lower():
            return False
        if FILTER_ID and FILTER_ID.lower() not in props.get("stop_id", "").lower():
            return False
        if FILTER_ROUTE and FILTER_ROUTE not in props.get("routes", []):
            return False
        return True
    
def missing(props):
    p = props["properties"]
    if not p.get('stop_id', ''):
        logging.warning(f"node named {p.get('name', '')} missing id")
    if not p.get('stop_code', ''):
        logging.warning(f"node id {p.get('stop_id', '')} missing code")
    if not p.get('routes', ''):
        logging.warning(f"node id {p.get('stop_id', '')} missing routes")
    if not p.get('name', ''):
        logging.warning(f"node id {p.get('stop_id', '')} missing name")

def inspect_stops(input_file):
    with open(input_file) as f:
        data = json.load(f)

    stops = data["features"]
    
    matched = [s for s in stops if matches(s["properties"])]

    print(f"{'ID':<10} {'ROUTE':<80} {'NAME':<50}")
    print("-" * 100)
    for s in matched:
        missing(s)
        p = s["properties"]
        print(
            f"{p.get('stop_id', ''):<10} "
            f"{', '.join(p.get('routes', [])):<80} "
            f"{p.get('name', ''):<50} "
        )

    print(f"\n{len(matched)} / {len(stops)} stops")

inspect_stops(INPUT_FILE)