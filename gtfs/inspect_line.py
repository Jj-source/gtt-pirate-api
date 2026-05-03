import json


INPUT_FILE = "osm_data/torino_transit.geojson"

FILTER_OPERATOR = ""
FILTER_NETWORK = ""
FILTER_NAME = "feriale"
FILTER_REF = ""


def matches(props):
    if FILTER_OPERATOR and FILTER_OPERATOR.lower() not in props.get("operator", "").lower():
        return False
    if FILTER_NETWORK and FILTER_NETWORK.lower() not in props.get("network", "").lower():
        return False
    if FILTER_NAME and FILTER_NAME.lower() not in props.get("name", "").lower():
        return False
    if FILTER_REF and FILTER_REF.lower() not in props.get("ref", "").lower():
        return False
    return True


def inspect(input_file):
    with open(input_file) as f:
        data = json.load(f)

    routes = [
        f for f in data["features"]
        if f["geometry"]["type"] == "MultiLineString"
    ]

    matched = [r for r in routes if matches(r["properties"])]

    print(f"{'TYPE':<10} {'REF':<8} {'OPERATOR':<30} {'NETWORK':<20} NAME")
    print("-" * 90)
    for r in matched:
        p = r["properties"]
        print(
            f"{p.get('route', ''):<10} "
            f"{p.get('ref', ''):<8} "
            f"{p.get('operator', ''):<30} "
            f"{p.get('network', ''):<20} "
            f"{p.get('name', '')}"
        )

    print(f"\n{len(matched)} / {len(routes)} routes")


inspect(INPUT_FILE)