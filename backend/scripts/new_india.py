import os
import json
import time

PRECISION_DECIMALS = 5

# North East Region Bounding Box (Lng: 87.80°E to 97.50°E, Lat: 21.80°N to 29.60°N)
MIN_LNG, MAX_LNG = 87.80, 97.50
MIN_LAT, MAX_LAT = 21.80, 29.60

NORTHEAST_STATES = {
    "ARUNACHAL PRADESH", "ASSAM", "MANIPUR", "MEGHALAYA",
    "MIZORAM", "NAGALAND", "SIKKIM", "TRIPURA",
    "AR", "AS", "MN", "ML", "MZ", "NL", "SK", "TR"
}

def find_osm_file():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "..", "converted_osm.geojson"),
        os.path.join(base_dir, "..", "converted_osm.geojson"),
        "converted_osm.geojson"
    ]
    for path in candidates:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    raise FileNotFoundError("converted_osm.geojson not found in root project folder.")

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def clean_precision(val, decimals: int = PRECISION_DECIMALS):
    """Cleans floating point noise (e.g. -7e-05) and rounds to standard decimal places."""
    f = safe_float(val)
    if f is None:
        return None
    if abs(f) < 1e-6:
        return 0.0
    return round(f, decimals)

def extract_lng_lat(feature: dict):
    geom = feature.get("geometry") or {}
    props = feature.get("properties") or {}

    # 1. Parse Geometry Coordinates
    if geom.get("type") == "Point":
        coords = geom.get("coordinates", [])
        if isinstance(coords, list) and len(coords) >= 2:
            c1, c2 = safe_float(coords[0]), safe_float(coords[1])
            if c1 is not None and c2 is not None:
                # Check if c1 is Lng and c2 is Lat (or 0.0 latitude placeholder)
                if MIN_LNG <= c1 <= MAX_LNG and (MIN_LAT <= c2 <= MAX_LAT or c2 == 0.0 or abs(c2) < 1e-4):
                    return c1, c2
                # Check if c2 is Lng and c1 is Lat (or 0.0 latitude placeholder)
                if MIN_LNG <= c2 <= MAX_LNG and (MIN_LAT <= c1 <= MAX_LAT or c1 == 0.0 or abs(c1) < 1e-4):
                    return c2, c1

    # 2. Fallback to properties
    p_lat = safe_float(props.get("lat") or props.get("latitude"))
    p_lng = safe_float(props.get("long") or props.get("longitude") or props.get("lng"))
    if p_lat is not None and p_lng is not None:
        if MIN_LNG <= p_lng <= MAX_LNG and (MIN_LAT <= p_lat <= MAX_LAT or p_lat == 0.0):
            return p_lng, p_lat

    # 3. Check State attribute fallback if present
    st_name = str(props.get("state_name", props.get("state", ""))).strip().upper()
    if st_name and st_name in NORTHEAST_STATES:
        if geom.get("type") == "Point":
            coords = geom.get("coordinates", [])
            if isinstance(coords, list) and len(coords) >= 2:
                c1, c2 = safe_float(coords[0]), safe_float(coords[1])
                if c1 and MIN_LNG <= c1 <= MAX_LNG:
                    return c1, c2 if c2 else 0.0
                if c2 and MIN_LNG <= c2 <= MAX_LNG:
                    return c2, c1 if c1 else 0.0

    return None, None

def is_point_in_target_bounds(feature: dict) -> bool:
    lng, lat = extract_lng_lat(feature)
    return lng is not None and lat is not None

def clean_feature_precision(feature: dict) -> dict:
    """Normalizes coordinate precision (5 decimals ~1m accuracy) and cleans scientific float noise."""
    lng, lat = extract_lng_lat(feature)
    if lng is not None and lat is not None:
        clean_lng = clean_precision(lng)
        clean_lat = clean_precision(lat)
        
        geom = feature.get("geometry")
        if isinstance(geom, dict) and geom.get("type") == "Point":
            feature["geometry"]["coordinates"] = [clean_lng, clean_lat]
            
        props = feature.get("properties")
        if isinstance(props, dict):
            if "lat" in props:
                props["lat"] = clean_lat
            if "long" in props:
                props["long"] = clean_lng
            if "latitude" in props:
                props["latitude"] = clean_lat
            if "longitude" in props:
                props["longitude"] = clean_lng

    return feature

def stream_geojson_features(filepath):
    """Yields parsed feature dicts one by one from a large GeoJSON file with low RAM usage."""
    with open(filepath, "r", encoding="utf-8") as f:
        in_features_array = False
        current_block = []
        depth = 0
        in_string = False
        escape = False

        for line in f:
            if not in_features_array:
                if '"features"' in line and '[' in line:
                    in_features_array = True
                continue

            for char in line:
                if depth > 0:
                    current_block.append(char)

                if escape:
                    escape = False
                    continue

                if char == '\\':
                    escape = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        if depth == 0:
                            current_block = [char]
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            block_str = "".join(current_block)
                            try:
                                yield json.loads(block_str)
                            except Exception:
                                pass
                            current_block = []

def extract_target_points():
    osm_path = find_osm_file()
    output_path = os.path.join(os.path.dirname(osm_path), "northeast_osm.geojson")
    
    file_size_mb = os.path.getsize(osm_path) / (1024 * 1024)
    print(f"Reading {osm_path} ({file_size_mb:.1f} MB)...")
    print(f"Target Bounds: Longitude {MIN_LNG}°E to {MAX_LNG}°E | Latitude {MIN_LAT}°N to {MAX_LAT}°N")
    
    start_time = time.time()
    filtered_features = []
    total_parsed = 0

    print(f"Using streaming parser with {PRECISION_DECIMALS}-decimal coordinate precision cleaning...")
    for feature in stream_geojson_features(osm_path):
        total_parsed += 1
        if is_point_in_target_bounds(feature):
            cleaned_feature = clean_feature_precision(feature)
            filtered_features.append(cleaned_feature)

        if total_parsed % 250000 == 0:
            print(f"Processed {total_parsed:,} features... Kept {len(filtered_features):,} features inside target region.")

    print(f"Filter complete in {time.time() - start_time:.2f}s. Total inspected: {total_parsed:,}. Kept: {len(filtered_features):,}.")
    
    geojson_out = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": filtered_features
    }
    
    print(f"Saving output to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_out, f)
    
    print(f"Done! Saved {len(filtered_features):,} target point features with clean precision to {output_path}.")

if __name__ == "__main__":
    extract_target_points()
