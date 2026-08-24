import os
import json
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from geojson_processor import processor
from tif_processor import tif_processor
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Loading spatial vector datasets and GeoTIFF rasters during application startup...")
    processor.load_data()
    processor.load_landslides_data()
    processor.load_hazard_data()
    try:
        tif_processor.load_and_process()
    except Exception as e:
        print(f"⚠️ GeoTIFF processor initialization note: {e}")
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

@app.get("/")
def read_root():
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
            "search": "/api/search?q=query"
        }
    }

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

@app.get("/api/route")
def get_shortest_path(
    lat1: float = Query(..., description="Origin latitude"),
    lon1: float = Query(..., description="Origin longitude"),
    lat2: float = Query(..., description="Destination latitude"),
    lon2: float = Query(..., description="Destination longitude")
):
    """Proxies Bhuvan Shortest Path Routing API with automatic OSRM fallback."""
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
                    return {
                        "status": "success",
                        "provider": "OSRM Routing Engine",
                        "geojson": geojson,
                        "distance_km": round(route.get("distance", 0) / 1000, 2),
                        "duration_min": round(route.get("duration", 0) / 60, 1)
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
                            return {
                                "status": "success",
                                "provider": "Bhuvan Routing API",
                                "geojson": data
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

# Serve static frontend & proto2 files directly from FastAPI backend
from fastapi.staticfiles import StaticFiles

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proto2_dir = os.path.join(root_dir, "proto2")
frontend_dir = os.path.join(root_dir, "frontend")

if os.path.exists(proto2_dir):
    app.mount("/proto2", StaticFiles(directory=proto2_dir, html=True), name="proto2")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

