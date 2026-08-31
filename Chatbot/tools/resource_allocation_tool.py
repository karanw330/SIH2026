import json


def resource_allocation_tool(photo_gps_coords: list, search_radius_km: float = 25.0) -> str:
    """
    Queries spatial database to identify and mobilize nearest disaster management assets 
    when a citizen/field officer uploads a geotagged photo of a blocked road.

    Args:
        photo_gps_coords: [latitude, longitude] extracted from photo EXIF data (e.g. [28.06, 95.32])
        search_radius_km: Distance radius to query emergency resources
    """
    lat, lng = photo_gps_coords

    # Simulated OSM / Bhuvan proximity query results
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
        },
        {
            "asset_id": "MED_UNIT_09",
            "type": "Mobile Trauma Ambulance",
            "location_name": "District Hospital Upper Siang",
            "distance_km": 11.1,
            "status": "AVAILABLE",
            "eta_minutes": 30
        }
    ]

    allocation_response = {
        "incident_coordinates": [lat, lng],
        "hazard_flagged": "Road Blockage / Debris Obstruction",
        "matched_resources_found": len(nearby_resources),
        "recommended_action": f"Dispatch JCB_EXCAVATOR_102 from Pasighat PWD Depot (ETA: 25 mins)",
        "resources": nearby_resources
    }

    return json.dumps(allocation_response)
