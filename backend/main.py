import sys
import subprocess
import os
import json
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from geojson_processor import processor
from tif_processor import tif_processor
from fastapi.responses import FileResponse

# --------------------------------------------------------------------------
# Root Directory Setup
# --------------------------------------------------------------------------
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proto2_dir = os.path.join(root_dir, "proto2")
frontend_dir = os.path.join(root_dir, "frontend")
chatbot_dir = os.path.join(root_dir, "Chatbot")

env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()
                except ValueError:
                    pass
if chatbot_dir not in sys.path:
    sys.path.insert(0, chatbot_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading spatial vector datasets and GeoTIFF rasters during application startup...")
    processor.load_data()
    try:
        tif_processor.load_and_process()
    except Exception as e:
        print(f"GeoTIFF processor initialization note: {e}")

    # Ensure hero-bg.jpg is synced to frontend/images/
    import shutil
    src_hero = os.path.join(root_dir, "hero-bg.jpg")
    dest_hero_dir = os.path.join(frontend_dir, "images")
    if os.path.exists(src_hero):
        os.makedirs(dest_hero_dir, exist_ok=True)
        shutil.copy(src_hero, os.path.join(dest_hero_dir, "hero-bg.jpg"))
    yield

app = FastAPI(
    title="North East India OSM GIS Map API",
    description="FastAPI backend providing spatial vector data, GeoTIFF raster processing, and analytics for North East India.",
    version="1.3.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/info")
def read_api_info():
    return {
        "title": "North East Region Spatial Data API",
        "status": "online",
        "total_ne_features": processor.stats.get("total_features", 0),
        "endpoints": {
            "northeast_features": "/api/geojson/northeast",
            "landslides": "/api/geojson/landslides",
            "hazard": "/api/geojson/hazard",
            "stats": "/api/stats",
            "districts": "/api/districts",
            "search": "/api/search?q=query",
            "weather_geocode": "/api/weather/geocode",
            "weather_route": "/api/weather/route"
        }
    }

@app.get("/api/keys/tomtom")
def get_tomtom_key():
    return {"key": os.getenv("TOMTOM_API_KEY", "")}

@app.get("/api/geojson/northeast")
def get_northeast_geojson(
    state: Optional[str] = Query(None, description="Filter by State name (e.g. Assam, Meghalaya)"),
    district: Optional[str] = Query(None, description="Filter by District name"),
    bbox: Optional[str] = Query(None, description="Spatial bounding box filter: min_lng,min_lat,max_lng,max_lat"),
    limit: Optional[int] = Query(None, description="Limit max features returned"),
    zoom: Optional[int] = Query(None, description="Map zoom level for state-aware sampling")
):
    """Returns GeoJSON feature collection for North East India with optional state/district/bbox/limit filtering."""
    return processor.get_northeast_geojson(state=state, district=district, bbox=bbox, limit=limit, zoom=zoom)

@app.get("/api/geojson/landslides")
def get_landslides_geojson(
    state: Optional[str] = Query(None, description="Filter by State name"),
    district: Optional[str] = Query(None, description="Filter by District name"),
    year: Optional[str] = Query(None, description="Filter by occurrence year (e.g. 2017)"),
    bbox: Optional[str] = Query(None, description="Spatial bounding box filter: min_lng,min_lat,max_lng,max_lat"),
    limit: Optional[int] = Query(None, description="Limit max features returned"),
    mode: Optional[str] = Query("polygon", description="Return mode: 'polygon' or 'centroid'"),
    zoom: Optional[int] = Query(None, description="Map zoom level for state-aware sampling")
):
    """Returns GeoJSON feature collection for NDEM/Bhuvan Landslide Polygons or Centroids."""
    return processor.get_landslides_geojson(state=state, district=district, year=year, bbox=bbox, limit=limit, mode=mode, zoom=zoom)

@app.get("/api/geojson/hazard")
def get_hazard_geojson(
    state: Optional[str] = Query(None, description="Filter by State name"),
    district: Optional[str] = Query(None, description="Filter by District name"),
    bbox: Optional[str] = Query(None, description="Spatial bounding box filter: min_lng,min_lat,max_lng,max_lat"),
    limit: Optional[int] = Query(None, description="Limit max features returned"),
    zoom: Optional[int] = Query(None, description="Map zoom level for adaptive sampling")
):
    """Returns GeoJSON feature collection for NDEM Landslide Hazard Zonation (nerlhz50dsc)."""
    return processor.get_hazard_geojson(state=state, district=district, bbox=bbox, limit=limit, zoom=zoom)

def analyze_route_hazard_segments(route_geojson):
    """
    Samples coordinates along route geometry against 563MB GeoTIFF susceptibility raster.
    Extracts critical sub-segments (susceptibility score >= 0.75) and formats risk stats.
    """
    if not route_geojson or "features" not in route_geojson or not route_geojson["features"]:
        return route_geojson, {
            "has_critical_hazards": False,
            "max_susceptibility": 0.0,
            "critical_hazard_segments": [],
            "critical_segments_geojson": None,
            "critical_sectors_count": 0
        }

    feature = route_geojson["features"][0]
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [])

    if not coords or geom.get("type") != "LineString":
        return route_geojson, {
            "has_critical_hazards": False,
            "max_susceptibility": 0.0,
            "critical_hazard_segments": [],
            "critical_segments_geojson": None,
            "critical_sectors_count": 0
        }

    # Sample points along route (max ~250 points for high performance)
    step = max(1, len(coords) // 250)
    sampled_indices = list(range(0, len(coords), step))
    if (len(coords) - 1) not in sampled_indices:
        sampled_indices.append(len(coords) - 1)

    max_score = 0.0
    critical_indices = set()

    for idx in sampled_indices:
        lon, lat = coords[idx][0], coords[idx][1]
        res = tif_processor.query_susceptibility(lat, lon)
        score = res.get("susceptibility_score", 0.0)
        if score > max_score:
            max_score = round(score, 4)
        if score >= 0.75:
            critical_indices.add(idx)

    # Group consecutive critical indices into continuous sub-line segments
    critical_sublines = []
    if critical_indices:
        sorted_crit = sorted(list(critical_indices))
        current_group = [sorted_crit[0]]
        for i in range(1, len(sorted_crit)):
            if sorted_crit[i] - sorted_crit[i-1] <= step * 2:
                current_group.append(sorted_crit[i])
            else:
                start_idx = max(0, current_group[0] - 1)
                end_idx = min(len(coords), current_group[-1] + 2)
                critical_sublines.append(coords[start_idx:end_idx])
                current_group = [sorted_crit[i]]
        if current_group:
            start_idx = max(0, current_group[0] - 1)
            end_idx = min(len(coords), current_group[-1] + 2)
            critical_sublines.append(coords[start_idx:end_idx])

    critical_features = []
    critical_segments_info = []

    for i, line_coords in enumerate(critical_sublines):
        seg_scores = [tif_processor.query_susceptibility(c[1], c[0]).get("susceptibility_score", 0.75) for c in line_coords]
        peak_seg_score = round(max(seg_scores), 4) if seg_scores else 0.75
        mid_pt = line_coords[len(line_coords) // 2]
        
        crit_feat = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": line_coords
            },
            "properties": {
                "segment_id": f"CRIT-SEG-{i+1}",
                "susceptibility_score": peak_seg_score,
                "risk_category": "Critical Hazard (≥ 0.75)",
                "midpoint": [mid_pt[1], mid_pt[0]]
            }
        }
        critical_features.append(crit_feat)
        critical_segments_info.append({
            "segment_id": f"CRIT-SEG-{i+1}",
            "susceptibility_score": peak_seg_score,
            "coords": [mid_pt[1], mid_pt[0]]
        })

    crit_geojson = {
        "type": "FeatureCollection",
        "features": critical_features
    } if critical_features else None

    has_critical = len(critical_features) > 0

    route_geojson["features"][0]["properties"]["max_susceptibility"] = max_score
    route_geojson["features"][0]["properties"]["has_critical_hazards"] = has_critical
    route_geojson["features"][0]["properties"]["critical_sectors_count"] = len(critical_features)

    analysis_result = {
        "has_critical_hazards": has_critical,
        "max_susceptibility": max_score,
        "critical_sectors_count": len(critical_features),
        "critical_hazard_segments": critical_segments_info,
        "critical_segments_geojson": crit_geojson
    }

    return route_geojson, analysis_result

def analyze_route_weather(route_geojson):
    import urllib.request
    import json

    if not route_geojson or "features" not in route_geojson or not route_geojson["features"]:
        return route_geojson, {"weather_warnings_geojson": None, "max_precipitation": 0.0}

    feature = route_geojson["features"][0]
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [])

    if not coords or geom.get("type") != "LineString":
        return route_geojson, {"weather_warnings_geojson": None, "max_precipitation": 0.0}

    # Sample ~10 points along the route
    step = max(1, len(coords) // 10)
    sampled_indices = list(range(0, len(coords), step))
    if (len(coords) - 1) not in sampled_indices:
        sampled_indices.append(len(coords) - 1)

    lats = []
    lons = []
    sampled_coords = []
    for idx in sampled_indices:
        lats.append(str(coords[idx][1]))
        lons.append(str(coords[idx][0]))
        sampled_coords.append((coords[idx][0], coords[idx][1]))

    lats_str = ",".join(lats)
    lons_str = ",".join(lons)
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats_str}&longitude={lons_str}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=auto"
    
    warnings_features = []
    max_precip = 0.0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            
            if isinstance(data, list):
                responses = data
            else:
                responses = [data]
                
            for i, resp in enumerate(responses):
                if "current" in resp:
                    curr = resp["current"]
                    temp = curr.get("temperature_2m", 0)
                    precip = curr.get("precipitation", 0)
                    wind = curr.get("wind_speed_10m", 0)
                    code = curr.get("weather_code", 0)
                    
                    if precip > max_precip:
                        max_precip = precip
                        
                    warning_types = []
                    if temp > 38:
                        warning_types.append(f"Extreme Heat ({temp}°C)")
                    if precip > 5.0:
                        warning_types.append(f"Heavy Rainfall ({precip}mm)")
                    if wind > 40:
                        warning_types.append(f"High Winds ({wind}km/h)")
                    if code in [95, 96, 99]:
                        warning_types.append("Thunderstorms")
                    
                    if warning_types:
                        warnings_features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [sampled_coords[i][0], sampled_coords[i][1]]
                            },
                            "properties": {
                                "warning_type": "Extreme Weather",
                                "details": ", ".join(warning_types),
                                "temperature": temp,
                                "precipitation": precip,
                                "wind_speed": wind
                            }
                        })
    except Exception as e:
        print(f"Weather sampling failed: {e}")
        
    weather_geojson = {
        "type": "FeatureCollection",
        "features": warnings_features
    } if warnings_features else None
    
    return route_geojson, {"weather_warnings_geojson": weather_geojson, "max_precipitation": max_precip}

# --------------------------------------------------------------------------
# Weather & Geocoding Endpoints
# --------------------------------------------------------------------------
@app.get("/api/weather/geocode")
def geocode_location(
    name: str = Query(..., description="Location name to search for (e.g. 'Guwahati')")
):
    """Geocodes a location name to coordinates using Open-Meteo Geocoding API."""
    import urllib.request
    import urllib.parse
    
    encoded_name = urllib.parse.quote(name)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_name}&count=5&language=en&format=json"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            if "results" in data:
                return {
                    "status": "success",
                    "provider": "Open-Meteo Geocoding API",
                    "results": data["results"]
                }
            else:
                return {
                    "status": "success",
                    "provider": "Open-Meteo Geocoding API",
                    "results": []
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to geocode location: {str(e)}",
            "results": None
        }

@app.get("/api/weather/route")
def get_route_weather(
    lat1: float = Query(..., description="Origin latitude"),
    lon1: float = Query(..., description="Origin longitude"),
    lat2: float = Query(..., description="Destination latitude"),
    lon2: float = Query(..., description="Destination longitude"),
    waypoints: Optional[str] = Query(None, description="Comma-separated lat,lon pairs for waypoints, e.g., 'lat,lon;lat,lon'")
):
    """Fetches live weather data for origin, destination, and waypoints using Open-Meteo Forecast API."""
    import urllib.request
    
    lats = [str(lat1), str(lat2)]
    lons = [str(lon1), str(lon2)]

    if waypoints:
        pts = waypoints.split(";")
        for pt in pts:
            parts = pt.split(",")
            if len(parts) == 2:
                try:
                    lats.append(str(float(parts[0].strip())))
                    lons.append(str(float(parts[1].strip())))
                except ValueError:
                    pass

    lats_str = ",".join(lats)
    lons_str = ",".join(lons)
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats_str}&longitude={lons_str}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=auto"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            
            weather_results = []
            if isinstance(data, list):
                responses = data
            else:
                responses = [data]
                
            labels = ["origin", "destination"] + [f"waypoint_{i+1}" for i in range(len(lats) - 2)]
            
            for i, resp in enumerate(responses):
                if "current" in resp:
                    weather_results.append({
                        "point": labels[i],
                        "latitude": resp["latitude"],
                        "longitude": resp["longitude"],
                        "weather": resp["current"],
                        "elevation": resp.get("elevation")
                    })
            
            return {
                "status": "success",
                "provider": "Open-Meteo Forecast API",
                "weather_data": weather_results
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch weather data: {str(e)}",
            "weather_data": None
        }

@app.get("/api/route")
def get_shortest_path(
    lat1: float = Query(..., description="Origin latitude"),
    lon1: float = Query(..., description="Origin longitude"),
    lat2: float = Query(..., description="Destination latitude"),
    lon2: float = Query(..., description="Destination longitude")
):
    """Proxies Bhuvan Shortest Path Routing API with automatic OSRM fallback & GeoTIFF critical hazard analysis."""
    import urllib.request
    import urllib.parse

    def fetch_osrm():
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        try:
            req = urllib.request.Request(osrm_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    geojson = {
                        "type": "FeatureCollection",
                        "features": [{
                            "type": "Feature",
                            "geometry": route["geometry"],
                            "properties": {
                                "distance_km": round(route.get("distance", 0) / 1000, 2),
                                "duration_min": round(route.get("duration", 0) / 60, 1),
                                "provider": "OSRM Routing Engine"
                            }
                        }]
                    }
                    geojson, hazard_analysis = analyze_route_hazard_segments(geojson)
                    geojson, weather_analysis = analyze_route_weather(geojson)
                    
                    base_score = hazard_analysis.get("max_susceptibility", 0.0)
                    max_precip = weather_analysis.get("max_precipitation", 0.0)
                    dynamic_risk = round(min(1.0, base_score * (1 + (max_precip / 50.0))), 4)
                    
                    return {
                        "status": "success",
                        "provider": "OSRM Routing Engine",
                        "geojson": geojson,
                        "distance_km": round(route.get("distance", 0) / 1000, 2),
                        "duration_min": round(route.get("duration", 0) / 60, 1),
                        "dynamic_risk": dynamic_risk,
                        "max_precipitation": max_precip,
                        **hazard_analysis,
                        **weather_analysis
                    }
        except Exception as oe:
            print(f"OSRM fallback failed: {oe}")
        return {
            "status": "error",
            "message": "Routing failed on both Bhuvan and fallback engines.",
            "geojson": None
        }

    token = os.getenv("BHUVAN_ROUTING_KEY")
    if token:
        bhuvan_url = f"https://bhuvan-app1.nrsc.gov.in/api/routing/curl_routing_state.php?lat1={lat1}&lon1={lon1}&lat2={lat2}&lon2={lon2}&token={token}"
        try:
            req = urllib.request.Request(bhuvan_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                body = res.read().decode("utf-8").strip()
                if "same state" not in body.lower():
                    try:
                        data = json.loads(body)
                        if data and not (isinstance(data, dict) and data.get("status") == "error"):
                            data, hazard_analysis = analyze_route_hazard_segments(data)
                            data, weather_analysis = analyze_route_weather(data)
                            
                            base_score = hazard_analysis.get("max_susceptibility", 0.0)
                            max_precip = weather_analysis.get("max_precipitation", 0.0)
                            dynamic_risk = round(min(1.0, base_score * (1 + (max_precip / 50.0))), 4)
                            
                            return {
                                "status": "success",
                                "provider": "Bhuvan Routing API",
                                "geojson": data,
                                "dynamic_risk": dynamic_risk,
                                "max_precipitation": max_precip,
                                **hazard_analysis,
                                **weather_analysis
                            }
                    except Exception:
                        pass
        except Exception as e:
            print(f"Bhuvan routing failed, falling back to OSRM: {e}")

    # Fallback to OSRM Engine
    return fetch_osrm()

@app.get("/api/stats")
def get_stats():
    """Returns summary statistics for North East features."""
    return processor.stats

@app.get("/api/districts")
def get_districts(state: Optional[str] = None):
    """Returns district hierarchy by state."""
    districts = processor.stats.get("districts_by_state", {})
    if state:
        state_title = state.title()
        return {state_title: districts.get(state_title, [])}
    return districts

@app.get("/api/search")
def search_features(
    q: str = Query(..., min_length=1, description="Search term for feature name, ID, district or type"),
    limit: int = Query(50, ge=1, le=200)
):
    """Search spatial features by query string."""
    return {
        "query": q,
        "results": processor.search_stations(query=q, limit=limit)
    }

@app.get("/api/health-facilities/stats")
def get_health_facilities_stats():
    """Returns statistics for health facilities loaded from GPKG/GeoJSON."""
    stats = processor.stats.get("health_facilities", {})
    return {
        "status": "success",
        "data": stats
    }

@app.get("/api/proximity")
def get_proximity(
    theme: str = Query("hospital", description="Theme to search (e.g., hospital, police)"),
    lat: float = Query(..., description="Latitude coordinate"),
    lon: float = Query(..., description="Longitude coordinate"),
    buffer: int = Query(3000, description="Buffer radius in meters")
):
    """Queries local GPKG for hospitals, and falls back to Bhuvan API for other themes."""
    if theme.lower() == "hospital":
        try:
            local_results = processor.search_hospitals_proximity(lat, lon, buffer)
            return {
                "status": "success",
                "provider": "Local HOTOSM GPKG",
                "data": {"hospital": local_results}
            }
        except Exception as e:
            print(f"Local hospital search failed: {e}")
            # Fall back to Bhuvan if local fails
            pass

    import urllib.request
    import urllib.parse
    
    # We use a default token here but it can be overridden in the .env file
    token = os.getenv("BHUVAN_PROXIMITY_KEY", "303b7fcc8c8916b80f09df7feb65d39802f809c4")
    url = "https://bhuvan-app1.nrsc.gov.in/api/api_proximity/curl_hos_pos_prox.php"
    params = {
        "theme": theme,
        "lat": str(lat),
        "lon": str(lon),
        "buffer": str(buffer),
        "token": token
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    try:
        req = urllib.request.Request(full_url, headers={
            "Content-Type": "application/x-www-form-urlencoded", 
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            return {
                "status": "success",
                "provider": "Bhuvan Proximity API",
                "data": data
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Bhuvan proximity query failed: {str(e)}",
            "data": None
        }

# --------------------------------------------------------------------------
# GeoTIFF Landslide Susceptibility Raster Endpoints
# --------------------------------------------------------------------------
@app.get("/api/raster/susceptibility/info")
def get_raster_info():
    """Returns metadata, status, spatial bounding box, and probability stats for the GeoTIFF raster."""
    if not tif_processor.is_loaded:
        res = tif_processor.load_and_process()
        return res
    return {
        "status": "active",
        "file": os.path.basename(tif_processor.tif_path) if tif_processor.tif_path else None,
        "bounds": tif_processor.bounds,
        "extent": tif_processor.extent_bbox,
        "has_raster": tif_processor.raster_data is not None,
        "stats": {
            "min_susceptibility": round(tif_processor.min_val, 4),
            "max_susceptibility": round(tif_processor.max_val, 4),
            "mean_susceptibility": round(tif_processor.mean_val, 4)
        }
    }

@app.get("/api/raster/susceptibility/overlay.png")
def get_raster_overlay_png():
    """Serves the continuous color-mapped RGBA PNG overlay generated from GeoTIFF raster."""
    png_path = os.path.join(tif_processor.cache_dir, "landslide_overlay.png")
    
    if not tif_processor.is_loaded:
        tif_processor.load_and_process()
    
    # Regenerate if file doesn't exist or is tiny placeholder (< 1KB)
    if not os.path.exists(png_path) or os.path.getsize(png_path) < 1000:
        tif_processor.load_and_process()

    if os.path.exists(png_path):
        return FileResponse(
            png_path,
            media_type="image/png",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    
    from PIL import Image
    placeholder = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    placeholder.save(png_path)
    return FileResponse(png_path, media_type="image/png")

@app.get("/api/raster/susceptibility/query")
def query_raster_point(
    lat: float = Query(..., description="Latitude coordinate"),
    lon: float = Query(..., description="Longitude coordinate")
):
    """Queries exact continuous probability score (0.0 to 1.0) for a specific lat/lon coordinate."""
    return tif_processor.query_susceptibility(lat=lat, lon=lon)

# --------------------------------------------------------------------------
# AI Chatbot Agent REST API Endpoints
# --------------------------------------------------------------------------
from pydantic import BaseModel, Field
from fastapi import UploadFile, File

try:
    from tools.reroute_corridor_tool import reroute_corridor_tool
    from tools.localized_alert_dispatch_tool import localized_alert_dispatch_tool
    from tools.resource_allocation_tool import resource_allocation_tool
except Exception as ie:
    print(f"Chatbot tools import note: {ie}")

class RerouteRequest(BaseModel):
    origin: list[float] = Field(..., description="[latitude, longitude]")
    destination: list[float] = Field(..., description="[latitude, longitude]")
    hazardous_polygons: Optional[list[str]] = Field(default=["NE_HAZ_402"])

class AlertDispatchRequest(BaseModel):
    district_name: str
    risk_score: float
    hazard_type: Optional[str] = "Landslide Warning"

class ResourceAllocationRequest(BaseModel):
    photo_gps_coords: list[float] = Field(..., description="[latitude, longitude]")
    search_radius_km: Optional[float] = 25.0

class RouteAnalysisRequest(BaseModel):
    geojson: dict

@app.post("/api/route/analyze")
def api_analyze_custom_route(req: RouteAnalysisRequest):
    """Analyzes dynamic risk score and weather for a custom GeoJSON route."""
    data, hazard_analysis = analyze_route_hazard_segments(req.geojson)
    data, weather_analysis = analyze_route_weather(data)
    
    base_score = hazard_analysis.get("max_susceptibility", 0.0)
    max_precip = weather_analysis.get("max_precipitation", 0.0)
    dynamic_risk = round(min(1.0, base_score * (1 + (max_precip / 50.0))), 4)
    
    return {
        "status": "success",
        "dynamic_risk": dynamic_risk,
        "max_precipitation": max_precip,
        **hazard_analysis,
        **weather_analysis
    }

@app.post("/api/agent/reroute")
def api_agent_reroute(req: RerouteRequest):
    """Recalculates safe corridor route bypassing landslide hazards."""
    res_str = reroute_corridor_tool(req.origin, req.destination, req.hazardous_polygons or [])
    return json.loads(res_str)

@app.post("/api/agent/dispatch-alert")
def api_agent_dispatch_alert(req: AlertDispatchRequest):
    """Generates localized SMS templates in English, Assamese, Khasi, and Hindi."""
    res_str = localized_alert_dispatch_tool(req.district_name, req.risk_score, req.hazard_type)
    return json.loads(res_str)

@app.post("/api/agent/resources")
def api_agent_resources(req: ResourceAllocationRequest):
    """Queries nearest disaster management assets around given coordinates."""
    res_str = resource_allocation_tool(req.photo_gps_coords, req.search_radius_km or 25.0)
    return json.loads(res_str)

@app.post("/api/agent/upload-incident")
async def api_agent_upload_incident(file: UploadFile = File(...)):
    """Parses uploaded incident photo EXIF GPS data, queries point risk & nearby emergency resources."""
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    import io

    def get_decimal_from_dms(dms, ref):
        degrees, minutes, seconds = dms
        decimal = float(degrees) + float(minutes)/60.0 + float(seconds)/3600.0
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    content = await file.read()
    coords = None
    try:
        image = Image.open(io.BytesIO(content))
        exif_data = image._getexif()
        if exif_data:
            gps_info = {}
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == "GPSInfo":
                    for key in value:
                        sub_tag = GPSTAGS.get(key, key)
                        gps_info[sub_tag] = value[key]
            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
                lng = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
                coords = [lat, lng]
    except Exception as e:
        print(f"EXIF parsing note: {e}")

    if not coords:
        return {
            "filename": file.filename,
            "has_exif_gps": False,
            "extracted_coords": None,
            "error": "No EXIF GPS metadata found in this photo. Geotags are typically missing if photos are saved via chat apps or web exports. Please upload a raw camera photo captured with location/GPS enabled."
        }

    point_susceptibility = tif_processor.query_susceptibility(lat=coords[0], lon=coords[1])
    res_str = resource_allocation_tool(coords, 25.0)
    resources_data = json.loads(res_str)

    return {
        "filename": file.filename,
        "has_exif_gps": True,
        "extracted_coords": coords,
        "susceptibility_assessment": point_susceptibility,
        "emergency_allocation": resources_data
    }

# --------------------------------------------------------------------------
# Pinpointed Incident Reporting Endpoints
# --------------------------------------------------------------------------
import time

field_incidents = []

class IncidentReportRequest(BaseModel):
    category: str
    custom_message: Optional[str] = None
    coords: list[float]
    photo_filename: Optional[str] = None

@app.post("/api/agent/report-incident")
def api_agent_report_incident(req: IncidentReportRequest):
    """Submits a pinpointed field incident report with category, custom message, GPS coordinates, date, and time."""
    incident_id = f"INC-{len(field_incidents) + 101}"
    desc = req.custom_message.strip() if (req.custom_message and req.custom_message.strip()) else req.category
    
    now = time.localtime()
    date_str = time.strftime("%Y-%m-%d", now)
    time_str = time.strftime("%H:%M:%S", now)
    timestamp_str = f"{date_str} {time_str}"
    
    incident = {
        "id": incident_id,
        "category": req.category,
        "description": desc,
        "coords": req.coords,
        "lat": req.coords[0],
        "lng": req.coords[1],
        "date": date_str,
        "time": time_str,
        "timestamp": timestamp_str,
        "photo_filename": req.photo_filename,
        "status": "Pinpointed on WebGL GIS Map"
    }
    field_incidents.append(incident)
    
    point_susceptibility = tif_processor.query_susceptibility(lat=req.coords[0], lon=req.coords[1])
    res_str = resource_allocation_tool(req.coords, 25.0)
    resources_data = json.loads(res_str)
    
    return {
        "status": "success",
        "incident": incident,
        "susceptibility_assessment": point_susceptibility,
        "emergency_allocation": resources_data,
        "total_active_incidents": len(field_incidents)
    }

@app.get("/api/agent/incidents")
def api_agent_get_incidents():
    """Returns all pinpointed field incidents for map overlays."""
    return {"incidents": field_incidents}

# Serve static landing portal, proto2 WebGL MVP, and Chatbot UI directly from FastAPI backend
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

@app.get("/proto2")
def serve_proto2_redirect():
    return RedirectResponse(url="/proto2/", status_code=307)

@app.get("/proto2/")
def serve_proto2():
    proto2_index = os.path.join(proto2_dir, "index.html")
    if os.path.exists(proto2_index):
        return FileResponse(proto2_index)
    return {"error": "Proto2 index.html not found"}

@app.get("/chatbot")
def serve_chatbot_redirect():
    return RedirectResponse(url="/chatbot/", status_code=307)

@app.get("/chatbot/")
def serve_chatbot():
    chatbot_index = os.path.join(chatbot_dir, "index.html")
    if os.path.exists(chatbot_index):
        return FileResponse(chatbot_index)
    return {"error": "Chatbot index.html not found"}

if os.path.exists(proto2_dir):
    app.mount("/proto2", StaticFiles(directory=proto2_dir, html=True), name="proto2_static")

if os.path.exists(chatbot_dir):
    app.mount("/chatbot", StaticFiles(directory=chatbot_dir, html=True), name="chatbot_static")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

