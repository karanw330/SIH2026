import time
from geojson_processor import GeoJSONProcessor

print("Testing GeoJSON Processor performance...")
start = time.time()
p = GeoJSONProcessor()
p.load_data()
p.load_landslides_data()
elapsed = time.time() - start

print(f"✅ Loaded in {elapsed:.2f} seconds.")
print(f"Total features: {len(p.features)}")
print(f"Total landslides: {len(p.landslide_features)}")
print(f"Landslide stats: {p.landslide_stats}")
