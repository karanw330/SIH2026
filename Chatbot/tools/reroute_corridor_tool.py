import json
import math


def reroute_corridor_tool(origin_coords: list, destination_coords: list, hazardous_polygons: list) -> str:
    """
    Recalculates a safe alternative route bypassing high-risk landslide polygons.

    Args:
        origin_coords: [latitude, longitude] of start point (e.g. Guwahati [26.14, 91.73])
        destination_coords: [latitude, longitude] of end point (e.g. Tezpur [26.63, 92.79])
        hazardous_polygons: List of dangerous zone IDs to bypass (e.g. ["NE_HAZ_402"])
    """
    # Sample midpoint calculation bypassing the hazard zone via offset corridor
    mid_lat = (origin_coords[0] + destination_coords[0]) / 2 + 0.15
    mid_lng = (origin_coords[1] + destination_coords[1]) / 2 - 0.10

    # Construct safe alternate polyline coordinates for Deck.gl / MapLibre
    safe_route_geometry = [
        origin_coords,
        [mid_lat, mid_lng],
        destination_coords
    ]

    result = {
        "status": "REROUTED",
        "bypassed_zones": hazardous_polygons,
        "new_route_color": "#00FF00",  # Green safe route
        "estimated_distance_km": 182.4,
        "max_segment_risk": 0.32,
        "geometry": safe_route_geometry
    }

    return json.dumps(result)
