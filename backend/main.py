import os
import json
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from geojson_processor import processor

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Loading spatial vector datasets during application startup...")
    processor.load_data()
    processor.load_landslides_data()
    processor.load_hazard_data()
    yield

app = FastAPI(
    title="North East India OSM GIS Map API",
    description="FastAPI backend providing spatial vector data and analytics for North East India.",
    version="1.2.0",
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
    zoom: Optional[int] = Query(None, description="Map zoom level for state-aware sampling")
):
    """Returns GeoJSON feature collection for North East India with optional state/district/zoom filtering."""
    return processor.get_northeast_geojson(state=state, district=district, zoom=zoom)

@app.get("/api/geojson/landslides")
def get_landslides_geojson(
    state: Optional[str] = Query(None, description="Filter by State name"),
    district: Optional[str] = Query(None, description="Filter by District name"),
    year: Optional[str] = Query(None, description="Filter by occurrence year (e.g. 2017)"),
    bbox: Optional[str] = Query(None, description="Spatial bounding box filter: min_lng,min_lat,max_lng,max_lat"),
    mode: Optional[str] = Query("polygon", description="Return mode: 'polygon' or 'centroid'"),
    zoom: Optional[int] = Query(None, description="Map zoom level for state-aware sampling")
):
    """Returns GeoJSON feature collection for NDEM/Bhuvan Landslide Polygons or Centroids."""
    return processor.get_landslides_geojson(state=state, district=district, year=year, bbox=bbox, mode=mode, zoom=zoom)

@app.get("/api/geojson/hazard")
def get_hazard_geojson(
    state: Optional[str] = Query(None, description="Filter by State name"),
    district: Optional[str] = Query(None, description="Filter by District name"),
    bbox: Optional[str] = Query(None, description="Spatial bounding box filter: min_lng,min_lat,max_lng,max_lat"),
    zoom: Optional[int] = Query(None, description="Map zoom level for adaptive sampling")
):
    """Returns GeoJSON feature collection for NDEM Landslide Hazard Zonation (nerlhz50dsc)."""
    return processor.get_hazard_geojson(state=state, district=district, bbox=bbox, zoom=zoom)



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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
