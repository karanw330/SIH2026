import os
import json
from typing import Dict, Any, List

NORTHEAST_STATES = {
    "ARUNACHAL PRADESH",
    "ASSAM",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "SIKKIM",
    "TRIPURA"
}

NORTHEAST_STATE_CODES = {
    "AR", "AS", "MN", "ML", "MZ", "NL", "SK", "TR"
}

STATE_ALIAS_MAP = {
    # Manipur
    "MN": "Manipur",
    "MANI": "Manipur",
    "LS_MANIPUR": "Manipur",
    "MANIPUR": "Manipur",
    
    # Mizoram
    "MZ": "Mizoram",
    "MIZO": "Mizoram",
    "MIZORAM": "Mizoram",
    
    # Nagaland
    "NL": "Nagaland",
    "NAGA": "Nagaland",
    "NAGALAND": "Nagaland",
    
    # Arunachal Pradesh
    "AR": "Arunachal Pradesh",
    "ARUNACHAL PRADESH": "Arunachal Pradesh",
    
    # Assam
    "AS": "Assam",
    "ASSAM": "Assam",
    
    # Meghalaya
    "ML": "Meghalaya",
    "MEGHALAYA": "Meghalaya",
    
    # Sikkim
    "SK": "Sikkim",
    "SIKKIM": "Sikkim",
    
    # Tripura
    "TR": "Tripura",
    "TRIPURA": "Tripura"
}

def normalize_state_name(raw_name: str) -> str:
    """Normalizes state codes, aliases (e.g. MANI, MIZO, NAGA, MN, MZ, NL) to full state names."""
    if not raw_name:
        return ""
    clean = str(raw_name).strip().upper()
    if clean in STATE_ALIAS_MAP:
        return STATE_ALIAS_MAP[clean]
    for key, target in STATE_ALIAS_MAP.items():
        if key in clean or clean in key:
            return target
    return str(raw_name).strip().title()


FALLBACK_NE_FEATURES = [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [91.7362, 26.1445]}, "properties": {"id": "NE_01", "name": "Guwahati City Hub", "type": "Urban Node", "state_name": "Assam", "district__name": "Kamrup Metropolitan"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [91.8933, 25.5788]}, "properties": {"id": "NE_02", "name": "Shillong Peak Station", "type": "Highland Point", "state_name": "Meghalaya", "district__name": "East Khasi Hills"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.9368, 24.8170]}, "properties": {"id": "NE_03", "name": "Imphal Valley Station", "type": "Regional Hub", "state_name": "Manipur", "district__name": "Imphal West"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [91.2868, 23.8315]}, "properties": {"id": "NE_04", "name": "Agartala Boundary Point", "type": "Transit Node", "state_name": "Tripura", "district__name": "West Tripura"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [94.1086, 25.6751]}, "properties": {"id": "NE_05", "name": "Kohima Ridge Feature", "type": "Elevated Node", "state_name": "Nagaland", "district__name": "Kohima"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [92.7176, 23.7307]}, "properties": {"id": "NE_06", "name": "Aizawl Center Node", "type": "Hilly Station", "state_name": "Mizoram", "district__name": "Aizawl"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.6053, 27.0844]}, "properties": {"id": "NE_07", "name": "Itanagar Foothills", "type": "Capital Node", "state_name": "Arunachal Pradesh", "district__name": "Papum Pare"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.6138, 27.3389]}, "properties": {"id": "NE_08", "name": "Gangtok High Altitude Point", "type": "Mountain Node", "state_name": "Sikkim", "district__name": "East Sikkim"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [92.6841, 26.6528]}, "properties": {"id": "NE_09", "name": "Tezpur Brahmaputra Crossing", "type": "Waterway Crossing", "state_name": "Assam", "district__name": "Sonitpur"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [94.9120, 27.4728]}, "properties": {"id": "NE_10", "name": "Dibrugarh Upper Assam Hub", "type": "Riverine Station", "state_name": "Assam", "district__name": "Dibrugarh"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [91.7314, 25.2637]}, "properties": {"id": "NE_11", "name": "Cherrapunji Rainfall Node", "type": "Hydrological Landmark", "state_name": "Meghalaya", "district__name": "East Khasi Hills"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [94.2037, 26.7509]}, "properties": {"id": "NE_12", "name": "Jorhat Tea Region Center", "type": "Agricultural Node", "state_name": "Assam", "district__name": "Jorhat"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.8052, 24.5574]}, "properties": {"id": "NE_13", "name": "Loktak Lake Observation Point", "type": "Freshwater Wetland Node", "state_name": "Manipur", "district__name": "Bishnupur"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [94.1770, 26.9538]}, "properties": {"id": "NE_14", "name": "Majuli River Island Node", "type": "Inland Island Point", "state_name": "Assam", "district__name": "Majuli"}}
]

class GeoJSONProcessor:
    def __init__(self, filepath: str = None):
        if filepath is None:
            ne_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "northeast_osm.geojson"))
            root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "converted_osm.geojson"))
            curr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "converted_osm.geojson"))
            
            if os.path.exists(ne_path):
                filepath = ne_path
            elif os.path.exists(root_path):
                filepath = root_path
            elif os.path.exists(curr_path):
                filepath = curr_path
            else:
                filepath = "converted_osm.geojson"
        
        self.filepath = filepath
        self.northeast_geojson: Dict[str, Any] = {}
        self.features: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}
        self.landslide_geojson: Dict[str, Any] = {"type": "FeatureCollection", "features": []}
        self.landslide_features: List[Dict[str, Any]] = []
        self.landslide_stats: Dict[str, Any] = {"total_landslides": 0, "active_count": 0, "dormant_count": 0}
        self.hazard_geojson: Dict[str, Any] = {"type": "FeatureCollection", "features": []}
        self.hazard_features: List[Dict[str, Any]] = []
        self.hazard_stats: Dict[str, Any] = {"total_hazard_polygons": 0}
        self.is_loaded = False
        self.is_landslides_loaded = False
        self.is_hazard_loaded = False

    def load_data(self):
        """Loads raw GeoJSON and extracts features for North East India with fallbacks."""
        if self.is_loaded:
            return
            
        if not os.path.exists(self.filepath):
            print(f"Warning: File {self.filepath} not found. Using North East region fallback dataset.")
            self._use_fallback_data()
            return

        print(f"Loading GeoJSON data from {self.filepath}...")
        try:
            ne_features = []
            state_counts = {}
            district_map = {}
            type_counts = {}

            min_lat, max_lat = 90.0, -90.0
            min_lng, max_lng = 180.0, -180.0

            # For very large files (>50MB), stream line by line to prevent memory spikes
            if os.path.getsize(self.filepath) > 50 * 1024 * 1024:
                print(f"Streaming features from large dataset ({os.path.getsize(self.filepath)/(1024*1024):.1f} MB)...")
                current_block = []
                in_feature = False
                with open(self.filepath, "r", encoding="utf-8") as f:
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
                                    feature = json.loads(block_str)
                                    props = feature.get("properties", {})
                                    state_name = str(props.get("state_name", props.get("state", ""))).strip().upper()
                                    geom = feature.get("geometry", {})
                                    lat = props.get("lat")
                                    long_val = props.get("long")

                                    if geom and geom.get("type") == "Point" and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) >= 2:
                                        c1, c2 = geom["coordinates"][0], geom["coordinates"][1]
                                        if isinstance(c1, (int, float)) and isinstance(c2, (int, float)):
                                            if 65.0 <= c1 <= 100.0 and 5.0 <= c2 <= 40.0:
                                                long_val, lat = c1, c2
                                            elif 65.0 <= c2 <= 100.0 and 5.0 <= c1 <= 40.0:
                                                long_val, lat = c2, c1
                                            else:
                                                long_val, lat = c1, c2

                                    if isinstance(long_val, (int, float)) and isinstance(lat, (int, float)):
                                        is_ne = False
                                        norm_st = normalize_state_name(state_name) if state_name else ""
                                        if norm_st and norm_st in ("Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"):
                                            is_ne = True
                                        elif 87.5 <= long_val <= 97.5 and 21.5 <= lat <= 29.5:
                                            is_ne = True

                                        if is_ne:
                                            ne_features.append(feature)
                                            min_lng = min(min_lng, long_val)
                                            max_lng = max(max_lng, long_val)
                                            min_lat = min(min_lat, lat)
                                            max_lat = max(max_lat, lat)

                                            norm_state = norm_st if norm_st else "North East Region"
                                            state_counts[norm_state] = state_counts.get(norm_state, 0) + 1
                                            dist = str(props.get("district__name", props.get("district", ""))).title()
                                            if dist and dist not in ("Null", "None", "Unknown"):
                                                if norm_state not in district_map:
                                                    district_map[norm_state] = set()
                                                district_map[norm_state].add(dist)
                                            f_type = str(props.get("type", props.get("category", "OSM Feature")))
                                            type_counts[f_type] = type_counts.get(f_type, 0) + 1
                                except Exception:
                                    pass
                                current_block = []
            else:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                all_features = data.get("features", [])
                for feature in all_features:
                    props = feature.get("properties", {})
                    state_name = str(props.get("state_name", props.get("state", ""))).strip().upper()

                    geom = feature.get("geometry", {})
                    lat = props.get("lat")
                    long_val = props.get("long")

                    if geom and geom.get("type") == "Point" and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) >= 2:
                        c1, c2 = geom["coordinates"][0], geom["coordinates"][1]
                        if isinstance(c1, (int, float)) and isinstance(c2, (int, float)):
                            if 65.0 <= c1 <= 100.0 and 5.0 <= c2 <= 40.0:
                                long_val, lat = c1, c2
                            elif 65.0 <= c2 <= 100.0 and 5.0 <= c1 <= 40.0:
                                long_val, lat = c2, c1
                            else:
                                long_val, lat = c1, c2

                    if isinstance(long_val, (int, float)) and isinstance(lat, (int, float)):
                        if -90.0 <= lat <= 90.0 and -180.0 <= long_val <= 180.0:
                            min_lng = min(min_lng, long_val)
                            max_lng = max(max_lng, long_val)
                            min_lat = min(min_lat, lat)
                            max_lat = max(max_lat, lat)

                            ne_features.append(feature)

                            if state_name and state_name in NORTHEAST_STATES:
                                norm_state = state_name.title()
                            elif props.get("state_name"):
                                norm_state = str(props.get("state_name")).title()
                            else:
                                norm_state = "North East Region"

                            state_counts[norm_state] = state_counts.get(norm_state, 0) + 1

                            dist = str(props.get("district__name", props.get("district", ""))).title()
                            if dist and dist not in ("Null", "None", "Unknown"):
                                if norm_state not in district_map:
                                    district_map[norm_state] = set()
                                district_map[norm_state].add(dist)

                            f_type = str(props.get("type", props.get("category", "OSM Feature")))
                            type_counts[f_type] = type_counts.get(f_type, 0) + 1

            if not ne_features:
                print("No features parsed from dataset file. Initializing North East regional fallback dataset...")
                self._use_fallback_data()
                return

            district_list_by_state = {k: sorted(list(v)) for k, v in district_map.items()}

            self.features = ne_features
            self.northeast_geojson = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": ne_features
            }

            self.stats = {
                "total_features": len(ne_features),
                "state_counts": state_counts,
                "districts_by_state": district_list_by_state,
                "feature_types": type_counts,
                "bounds": {
                    "min_lat": min_lat if min_lat != 90.0 else 21.5,
                    "max_lat": max_lat if max_lat != -90.0 else 29.5,
                    "min_lng": min_lng if min_lng != 180.0 else 87.5,
                    "max_lng": max_lng if max_lng != -180.0 else 97.5,
                }
            }
            self.is_loaded = True
            print(f"Successfully processed {len(ne_features)} features.")

        except Exception as e:
            print(f"Error loading GeoJSON data ({e}). Falling back to North East dataset...")
            self._use_fallback_data()

    def load_landslides_data(self):
        """Loads Bhuvan/NDEM Landslide Polygons GeoJSON or GeoJSONL dataset."""
        if self.is_landslides_loaded:
            return

        ls_file = None
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Priority order for landslide datasets
        candidate_files = [
            "Bhuvan_Landslides.geojsonl",
            "Bhuvan_Landslides.geojson",
            "NDEM_Landslide_Hazard.geojsonl",
            "NDEM_Landslide_Hazard.geojson"
        ]
        
        for fname in candidate_files:
            target = os.path.join(base_dir, fname)
            if os.path.exists(target):
                ls_file = target
                break
                
        if not ls_file:
            for fname in os.listdir(base_dir):
                if (fname.startswith("Bhuvan_") or fname.startswith("NDEM_")) and (fname.endswith(".geojson") or fname.endswith(".geojsonl")):
                    ls_file = os.path.join(base_dir, fname)
                    break
        
        if not ls_file or not os.path.exists(ls_file):
            print("No Landslide Polygons dataset file found.")
            return

        print(f"Loading Landslide Polygons from {ls_file}...")
        try:
            ls_features = []
            if ls_file.endswith(".geojsonl"):
                with open(ls_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            ls_features.append(json.loads(line))
            else:
                with open(ls_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ls_features = data.get("features", [])

            active_cnt = 0
            dormant_cnt = 0
            historical_cnt = 0
            year_counts = {}
            centroid_features = []
            current_year = 2026

            for feat in ls_features:
                props = feat.get("properties", {})
                activity = str(props.get("Activity", props.get("activity", props.get("lanslide_1", "")))).lower()
                
                raw_yr = str(props.get("Year", props.get("year", props.get("year_", "")))).strip()
                feat_yr = None
                if raw_yr and raw_yr not in ("None", "Null", "unknown", "nan", ""):
                    yr = raw_yr.split(".")[0]
                    year_counts[yr] = year_counts.get(yr, 0) + 1
                    if yr.isdigit():
                        feat_yr = int(yr)

                if feat_yr is not None and feat_yr > 1900:
                    age = current_year - feat_yr
                else:
                    age = 0 if "active" in activity else 10

                if age < 1:
                    active_cnt += 1
                elif 1 <= age <= 5:
                    dormant_cnt += 1
                else:
                    historical_cnt += 1

                # Calculate Feature Bounding Box & Centroid
                geom = feat.get("geometry", {})
                coords = []
                gtype = geom.get("type") if geom else ""
                if gtype == "Polygon" and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) > 0:
                    coords = geom["coordinates"][0]
                elif gtype == "MultiPolygon" and isinstance(geom.get("coordinates"), list):
                    for poly in geom["coordinates"]:
                        if poly and len(poly) > 0:
                            coords.extend(poly[0])

                if coords:
                    lats = [c[1] for c in coords if len(c) >= 2 and isinstance(c[1], (int, float))]
                    lngs = [c[0] for c in coords if len(c) >= 2 and isinstance(c[0], (int, float))]
                    if lats and lngs:
                        f_min_lat, f_max_lat = min(lats), max(lats)
                        f_min_lng, f_max_lng = min(lngs), max(lngs)
                        c_lat = (f_min_lat + f_max_lat) / 2.0
                        c_lng = (f_min_lng + f_max_lng) / 2.0
                        feat["_bbox"] = (f_min_lat, f_max_lat, f_min_lng, f_max_lng)
                        feat["_centroid"] = (c_lat, c_lng)

                        centroid_features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [round(c_lng, 5), round(c_lat, 5)]},
                            "properties": props
                        })

            sorted_years = sorted(list(year_counts.keys()), key=lambda x: int(x) if x.isdigit() else x)

            self.landslide_features = ls_features
            self.landslide_centroid_features = centroid_features
            self.landslide_geojson = {
                "type": "FeatureCollection",
                "features": ls_features
            }
            self.landslide_stats = {
                "total_landslides": len(ls_features),
                "active_count": active_cnt,
                "dormant_count": dormant_cnt,
                "historical_count": historical_cnt,
                "years_count": year_counts,
                "available_years": sorted_years
            }
            self.stats["landslides"] = self.landslide_stats
            self.is_landslides_loaded = True
            print(f"Successfully processed {len(ls_features):,} landslide features ({active_cnt:,} active [<1yr], {dormant_cnt:,} dormant [1-5yrs], {historical_cnt:,} historical [>5yrs]).")
        except Exception as e:
            print(f"Error loading landslide dataset: {e}")

    def load_hazard_data(self):
        """Loads NDEM Landslide Hazard Zonation Polygons dataset (nerlhz50dsc)."""
        if self.is_hazard_loaded:
            return

        hz_file = None
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidate_files = [
            "NDEM_Landslide_Hazard.geojsonl",
            "NDEM_Landslide_Hazard.geojson",
            "nerlhz50dsc.geojsonl",
            "nerlhz50dsc.geojson"
        ]
        for fname in candidate_files:
            target = os.path.join(base_dir, fname)
            if os.path.exists(target):
                hz_file = target
                break

        if not hz_file:
            print("No Landslide Hazard dataset file found.")
            return

        print(f"Loading Hazard Zonation Polygons from {hz_file}...")
        try:
            hz_features = []
            if hz_file.endswith(".geojsonl"):
                with open(hz_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            hz_features.append(json.loads(line))
            else:
                with open(hz_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    hz_features = data.get("features", [])

            high_cnt = 0
            mod_cnt = 0
            low_cnt = 0

            for feat in hz_features:
                props = feat.get("properties", {})
                grid_code = props.get("grid_code", 3)
                if grid_code in (4, 5):
                    high_cnt += 1
                elif grid_code == 3:
                    mod_cnt += 1
                else:
                    low_cnt += 1

                # Calculate Feature Bounding Box
                geom = feat.get("geometry", {})
                coords = []
                gtype = geom.get("type") if geom else ""
                if gtype == "Polygon" and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) > 0:
                    coords = geom["coordinates"][0]
                elif gtype == "MultiPolygon" and isinstance(geom.get("coordinates"), list):
                    for poly in geom["coordinates"]:
                        if poly and len(poly) > 0:
                            coords.extend(poly[0])

                if coords:
                    lats = [c[1] for c in coords if len(c) >= 2 and isinstance(c[1], (int, float))]
                    lngs = [c[0] for c in coords if len(c) >= 2 and isinstance(c[0], (int, float))]
                    if lats and lngs:
                        feat["_bbox"] = (min(lats), max(lats), min(lngs), max(lngs))

            self.hazard_features = hz_features
            self.hazard_geojson = {
                "type": "FeatureCollection",
                "features": hz_features
            }
            self.hazard_stats = {
                "total_hazard_polygons": len(hz_features),
                "high_risk_count": high_cnt,
                "moderate_risk_count": mod_cnt,
                "low_risk_count": low_cnt
            }
            self.stats["hazard"] = self.hazard_stats
            self.is_hazard_loaded = True
            print(f"Successfully processed {len(hz_features):,} hazard zonation polygons ({high_cnt:,} High Risk, {mod_cnt:,} Moderate Risk, {low_cnt:,} Low Risk).")
        except Exception as e:
            print(f"Error loading hazard dataset: {e}")

    def get_hazard_geojson(self, state: str = None, district: str = None, bbox: str = None, zoom: int = None) -> Dict[str, Any]:
        """Returns Hazard Zonation GeoJSON collection (100% features, no zoom/bbox clipping)."""
        filtered = []
        for feat in self.hazard_features:
            props = feat.get("properties", {})
            st_raw = str(props.get("State", props.get("state", props.get("state_name", ""))))
            st_norm = normalize_state_name(st_raw).strip().lower() if st_raw else ""

            if state and st_norm and st_norm != normalize_state_name(state).strip().lower():
                continue

            filtered.append(feat)

        return {
            "type": "FeatureCollection",
            "features": filtered
        }

    def get_landslides_geojson(self, state: str = None, district: str = None, year: str = None, bbox: str = None, mode: str = "polygon", zoom: int = None) -> Dict[str, Any]:
        """Returns Landslides GeoJSON collection filtered strictly by state, district, or year (no zoom/bbox dependencies)."""
        filtered = []

        for feat in self.landslide_features:
            props = feat.get("properties", {})
            st_raw = str(props.get("State", props.get("state", props.get("state_name", ""))))
            st_norm = normalize_state_name(st_raw).strip().lower()
            dist = str(props.get("District", props.get("district", props.get("district__name", "")))).strip().lower()
            raw_yr = str(props.get("Year", props.get("year", props.get("year_", "")))).strip().lower()
            yr = raw_yr.split(".")[0]

            if state and st_norm != normalize_state_name(state).strip().lower():
                continue
            if district and dist != district.strip().lower():
                continue
            if year and yr != year.strip().lower():
                continue

            filtered.append(feat)

        return {
            "type": "FeatureCollection",
            "features": filtered
        }

    def _use_fallback_data(self):
        state_counts = {}
        district_map = {}
        type_counts = {}
        
        for feat in FALLBACK_NE_FEATURES:
            props = feat["properties"]
            st = props["state_name"]
            dist = props["district__name"]
            ftype = props["type"]

            state_counts[st] = state_counts.get(st, 0) + 1
            if st not in district_map:
                district_map[st] = set()
            district_map[st].add(dist)
            type_counts[ftype] = type_counts.get(ftype, 0) + 1

        district_list_by_state = {k: sorted(list(v)) for k, v in district_map.items()}

        self.features = FALLBACK_NE_FEATURES
        self.northeast_geojson = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": FALLBACK_NE_FEATURES
        }

        self.stats = {
            "total_features": len(FALLBACK_NE_FEATURES),
            "state_counts": state_counts,
            "districts_by_state": district_list_by_state,
            "feature_types": type_counts,
            "bounds": {
                "min_lat": 23.5,
                "max_lat": 27.5,
                "min_lng": 88.5,
                "max_lng": 95.5,
            }
        }
        self.is_loaded = True

    def get_northeast_geojson(self, state: str = None, district: str = None, zoom: int = None) -> Dict[str, Any]:
        """Returns GeoJSON optionally filtered by state, district, or adaptive zoom sampling."""
        if not state and not district and (zoom is None or zoom >= 9):
            return self.northeast_geojson

        filtered = []
        for feat in self.features:
            props = feat.get("properties", {})
            
            if state and str(props.get("state_name", props.get("state", ""))).strip().lower() != state.strip().lower():
                continue
            if district and str(props.get("district__name", props.get("district", ""))).strip().lower() != district.strip().lower():
                continue

            filtered.append(feat)

        return {
            "type": "FeatureCollection",
            "crs": self.northeast_geojson.get("crs"),
            "features": filtered
        }

    def search_stations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search features by name, id, district, or type."""
        if not query:
            return []
        
        q = query.strip().lower()
        results = []
        for feat in self.features:
            props = feat.get("properties", {})
            name = str(props.get("name", props.get("station_name", ""))).lower()
            fid = str(props.get("id", "")).lower()
            dist = str(props.get("district__name", props.get("district", ""))).lower()
            ftype = str(props.get("type", "")).lower()

            if q in name or q in fid or q in dist or q in ftype:
                results.append(props)
                if len(results) >= limit:
                    break
        return results

# Singleton instance for app reuse
processor = GeoJSONProcessor()

