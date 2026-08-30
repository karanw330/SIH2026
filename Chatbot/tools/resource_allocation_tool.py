import json
import urllib.request
import urllib.parse
import os

def resource_allocation_tool(photo_gps_coords: list, search_radius_km: float = 25.0) -> str:
    """
    Queries spatial database to identify and mobilize nearest disaster management assets 
    when a citizen/field officer uploads a geotagged photo of a blocked road.

    Args:
        photo_gps_coords: [latitude, longitude] extracted from photo EXIF data (e.g. [28.06, 95.32])
        search_radius_km: Distance radius to query emergency resources
    """
    lat, lng = photo_gps_coords
    buffer_meters = int(search_radius_km * 1000)

    live_resources = []
    
    # Query Bhuvan Proximity API for hospitals (as per api2.py)
    bhuvan_url = "https://bhuvan-app1.nrsc.gov.in/api/api_proximity/curl_hos_pos_prox.php"
    token = os.getenv("BHUVAN_PROXIMITY_KEY", "303b7fcc8c8916b80f09df7feb65d39802f809c4")
    
    params = {
        "theme": "hospital",
        "lat": str(lat),
        "lon": str(lng),
        "buffer": str(buffer_meters),
        "token": token
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{bhuvan_url}?{query_string}"
    
    try:
        req = urllib.request.Request(full_url, headers={
            "Content-Type": "application/x-www-form-urlencoded", 
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            
            # Bhuvan API might return a list directly or a dict depending on the exact theme/endpoint behavior
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "hospital" in data:
                    items = data["hospital"]
                elif "data" in data and isinstance(data["data"], list):
                    items = data["data"]
            
            for i, item in enumerate(items):
                if isinstance(item, dict) and "name" in item:
                    dist_km = round(float(item.get("distance", 0)) / 1000, 2) if item.get("distance") else "Unknown"
                    live_resources.append({
                        "asset_id": f"HOSPITAL_{i+1}",
                        "type": "Emergency Hospital",
                        "location_name": item.get("name", "Unknown Hospital"),
                        "distance_km": dist_km,
                        "status": "AVAILABLE",
                        "eta_minutes": "Variable"
                    })
    except Exception as e:
        print(f"Bhuvan live query failed: {e}")

    # Simulated OSM non-hospital rescue resources 
    nearby_resources = [
        {
            "asset_id": "JCB_EXCAVATOR_102",
            "type": "Heavy Earthmoving Machinery",
            "location_name": "Pasighat PWD Depot",
            "distance_km": 8.4,
            "status": "AVAILABLE",
            "eta_minutes": 25
        },
        {
            "asset_id": "SDRF_NODE_04",
            "type": "Emergency Rescue Team",
            "location_name": "Yingkiong Base",
            "distance_km": 14.2,
            "status": "STANDBY",
            "eta_minutes": 40
        }
    ]
    
    # If live Bhuvan hospitals failed or returned empty (e.g., token expired), add a simulated one to ensure UI has data
    if not live_resources:
        live_resources = [{
            "asset_id": "MED_UNIT_09",
            "type": "Mobile Trauma Ambulance",
            "location_name": "District Hospital Upper Siang (Simulated due to API failure)",
            "distance_km": 11.1,
            "status": "AVAILABLE",
            "eta_minutes": 30
        }]
        
    nearby_resources.extend(live_resources)
    
    # Sort by distance
    def get_sort_key(res):
        dist = res.get("distance_km")
        return dist if isinstance(dist, (int, float)) else 999.0

    nearby_resources.sort(key=get_sort_key)

    if nearby_resources:
        closest = nearby_resources[0]
        recommended = f"Dispatch {closest['asset_id']} from {closest['location_name']}"
    else:
        recommended = "No nearby resources found within radius."

    allocation_response = {
        "incident_coordinates": [lat, lng],
        "hazard_flagged": "Road Blockage / Debris Obstruction",
        "matched_resources_found": len(nearby_resources),
        "recommended_action": recommended,
        "resources": nearby_resources
    }

    return json.dumps(allocation_response)
