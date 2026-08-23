import os
import json
import urllib.request
from dotenv import load_dotenv

# Load env variables from root .env if present
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

token = os.getenv("BHUVAN_ROUTING_KEY")

# Coordinates in NE India or sample test (Guwahati to Shillong: lat1=26.1445, lon1=91.7362, lat2=25.5788, lon2=91.8933)
lat1, lon1 = 26.1445, 91.7362
lat2, lon2 = 25.5788, 91.8933

url = f"https://bhuvan-app1.nrsc.gov.in/api/routing/curl_routing_state.php?lat1={lat1}&lon1={lon1}&lat2={lat2}&lon2={lon2}&token={token}"

print(f"Fetching route from Bhuvan API:\n{url}\n")

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=15) as response:
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        raw_body = response.read().decode("utf-8")
        
        print(f"HTTP Status: {status}")
        print(f"Content-Type: {content_type}")
        print("\n=== Raw Response Body (First 2000 chars) ===")
        print(raw_body[:2000])

        try:
            parsed = json.loads(raw_body)
            print("\n=== Parsed JSON Structure ===")
            if isinstance(parsed, dict):
                print(f"Keys: {list(parsed.keys())}")
            elif isinstance(parsed, list):
                print(f"List length: {len(parsed)}")
                if len(parsed) > 0:
                    print(f"First item keys: {list(parsed[0].keys()) if isinstance(parsed[0], dict) else type(parsed[0])}")
        except Exception as pe:
            print(f"\nResponse is not JSON or failed to parse: {pe}")

except Exception as e:
    print(f"Request failed: {e}")
