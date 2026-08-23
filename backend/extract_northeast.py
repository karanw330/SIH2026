import os
import json
import time

NORTHEAST_STATES = {
    "ARUNACHAL PRADESH", "ASSAM", "MANIPUR", "MEGHALAYA",
    "MIZORAM", "NAGALAND", "SIKKIM", "TRIPURA"
}

NORTHEAST_CODES = {"AR", "AS", "MN", "ML", "MZ", "NL", "SK", "TR"}

def extract_northeast_features():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_file = os.path.join(root_dir, "converted_osm.geojson")
    dest_file = os.path.join(root_dir, "northeast_osm.geojson")

    if not os.path.exists(src_file):
        print(f"Source file {src_file} does not exist.")
        return

    print(f"Streaming and extracting North East features from {src_file}...")
    start_time = time.time()

    ne_features = []
    current_block = []
    in_feature = False
    feature_count = 0
    extracted_count = 0

    with open(src_file, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "{" or stripped.startswith('{"type": "Feature"'):
                in_feature = True
                current_block = [line]
            elif in_feature:
                current_block.append(line)
                if stripped.startswith("}") or stripped.startswith("},"):
                    in_feature = False
                    block_str = "".join(current_block).rstrip(",\n\r ")
                    try:
                        feat = json.loads(block_str)
                        feature_count += 1
                        
                        props = feat.get("properties", {})
                        state_name = str(props.get("state_name", props.get("state", ""))).strip().upper()
                        
                        geom = feat.get("geometry", {})
                        long_val, lat = None, None
                        
                        if geom and geom.get("type") == "Point" and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) >= 2:
                            c1, c2 = geom["coordinates"][0], geom["coordinates"][1]
                            if isinstance(c1, (int, float)) and isinstance(c2, (int, float)):
                                if 65.0 <= c1 <= 100.0 and 5.0 <= c2 <= 40.0:
                                    long_val, lat = c1, c2
                                elif 65.0 <= c2 <= 100.0 and 5.0 <= c1 <= 40.0:
                                    long_val, lat = c2, c1
                                else:
                                    long_val, lat = c1, c2
                        
                        # Check spatial bounds for North East India (87.5E-97.5E, 21.5N-29.5N) or state match
                        is_ne = False
                        if state_name in NORTHEAST_STATES or state_name in NORTHEAST_CODES:
                            is_ne = True
                        elif isinstance(long_val, (int, float)) and isinstance(lat, (int, float)):
                            if 87.5 <= long_val <= 97.5 and 21.5 <= lat <= 29.5:
                                is_ne = True
                        
                        if is_ne:
                            ne_features.append(feat)
                            extracted_count += 1
                    except Exception:
                        pass
                    current_block = []

            if feature_count > 0 and feature_count % 500000 == 0:
                print(f"Processed {feature_count:,} features, found {extracted_count:,} North East features...")

    geojson_output = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": ne_features
    }

    with open(dest_file, "w", encoding="utf-8") as out:
        json.dump(geojson_output, out, indent=2)

    elapsed = time.time() - start_time
    print(f"Extraction complete in {elapsed:.2f}s! Saved {extracted_count:,} features to {dest_file}.")

if __name__ == "__main__":
    extract_northeast_features()
