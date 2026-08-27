# 🏔️ Landslide Sentinel AI — North East India GIS & Emergency Response Engine

> **Smart India Hackathon 2026 (SIH2026)**  
> Multi-modal GIS analytics, continuous GeoTIFF landslide risk processing, 3D WebGL map visualization, and AI incident response engine for North East India.

---

## 🌟 Project Directory Structure

A single unified **FastAPI Gateway Server** (`backend/main.py`) serves all 3 web interfaces on **Port 8000**:

```
SIH2026/
├── .env                             <-- Environment variables & API tokens (BHUVAN_ROUTING_KEY, etc.)
├── .gitignore                        <-- Git exclusion rules (cache/, virtualenvs)
├── README.md                        <-- Comprehensive Project Documentation
├── MILESTONES_PROGRESS.md           <-- Milestone & Feature Implementation Tracker
├── requirements.txt                 <-- Python Package Dependencies (fastapi, uvicorn, rasterio, etc.)
├── hero-bg.jpg                      <-- Landing Page Hero Background Image
│
├── 📦 GIS DATASETS (Root Directory)
├── ner_ilsm_cropped.tif             <-- 590.5 MB Continuous GeoTIFF Susceptibility Raster (28.4M pixels)
├── northeast_osm.geojson            <-- 46.6 MB OpenStreetMap Spatial Vector Dataset (333,593 features)
│
├── ⚙️ BACKEND MODULE (FastAPI Gateway)
├── backend/
│   ├── main.py                      <-- Central Gateway Server & All REST API Endpoints (Port 8000)
│   ├── geojson_processor.py         <-- Spatial Vector Engine & OSM District Indexer
│   ├── tif_processor.py             <-- GeoTIFF Raster Reader, PNG Overlay Generator & Pixel Sampler
│   ├── cache/                       <-- Auto-generated PNG raster overlays (landslide_overlay.png)
│   └── scripts/                     <-- GIS Data Extraction & Processing Scripts
│       ├── extract_northeast.py
│       └── new_india.py
│
├── 🌐 FRONTEND PORTAL (Served at /)
├── frontend/
│   ├── index.html                   <-- Sentinel Landing Portal HTML
│   ├── css/style.css                <-- Glassmorphism Design System & Theme Styles
│   ├── js/script.js                 <-- Interactive Counters & Portal Navigation
│   └── images/
│       └── hero-bg.jpg              <-- Synced Hero Image Asset
│
├── 🗺️ PROTO2 WEBGL MAP PORTAL (Served at /proto2/)
├── proto2/
│   ├── index.html                   <-- High-Performance WebGL Map Interface
│   ├── css/style.css                <-- Map UI, Glass Panels & Pulsing Purple Beacon Animation
│   └── js/app.js                    <-- MapLibre GL + Deck.gl GPU Renderer, Route Sampler & Fly-To
│
└── 🤖 CHATBOT INCIDENT RESPONSE PORTAL (Served at /chatbot/)
    └── Chatbot/
        ├── index.html               <-- AI Incident Response Portal HTML
        ├── static/
        │   ├── index.html           <-- Static Chatbot UI Mirror
        │   ├── css/style.css        <-- Chat UI Styling & Response Alert Cards
        │   └── js/app.js            <-- EXIF Photo Uploader, Category Prompt Chips & Pinpoint Links
        ├── tools/
        │   ├── localized_alert_dispatch_tool.py  <-- Multilingual SMS Alert Generator
        │   ├── resource_allocation_tool.py       <-- Disaster Management Resource Lookup
        │   └── reroute_corridor_tool.py          <-- Alternate Corridor Rerouting Tool
        ├── agent/
        │   └── incident_agent.py    <-- AI Agent Orchestrator & Tool Caller
        └── model/
            └── model_loader.py      <-- Offline GGUF LLM Loader & Fallback Engine
```

### Live Service Endpoints:
- 🌐 **Sentinel Landing Portal**: [`http://localhost:8000/`](http://localhost:8000/)
- 🗺️ **Proto2 WebGL GPU Map**: [`http://localhost:8000/proto2`](http://localhost:8000/proto2)
- 🤖 **AI Sentinel Chatbot**: [`http://localhost:8000/chatbot`](http://localhost:8000/chatbot)

---

## 📦 Required Data Files

The system relies on 2 core GIS datasets located in the project root:

| File Name | File Size | Description & Function |
| :--- | :--- | :--- |
| **`ner_ilsm_cropped.tif`** | **590.5 MB** | **Continuous GeoTIFF Susceptibility Raster** — Array of 28,415,020 high-resolution pixels providing exact $0.00 - 1.00$ probability scores. |
| **`northeast_osm.geojson`** | **46.6 MB** | **OSM Vector Dataset** — 333,593 spatial features (roads, buildings, infrastructure) across 8 North East states. |

---

## 🔥 Key Features & Technical Highlights

1. **563MB GeoTIFF Raster Engine**:
   - Fast raster queries (`tif_processor.py`) using `rasterio` / `tifffile` / `Pillow`.
   - Generates smooth color-gradient PNG overlays on application startup.

2. **Road Routing & Critical Hazard Detection (Score ≥ 0.75)**:
   - Road path calculation (`GET /api/route`) proxies Bhuvan/OSRM and samples route geometry points against the GeoTIFF raster.
   - Segments passing through **Critical Hazard zones ($\ge 0.75$)** are automatically extracted and highlighted in **Glowing Red** on the WebGL map.

3. **Field Geotagged Photo EXIF Inspection**:
   - Parses camera EXIF GPS tags (`POST /api/agent/upload-incident`).
   - If tags are missing, explicitly notifies the user without generating fake fallbacks.

4. **Interactive Incident Pinpointing**:
   - Select categories (Road Blockage, Landslide, Flash Flood, Rockfall) or type custom 3–4 word descriptions (`POST /api/agent/report-incident`).
   - Generates a **Pulsing Purple Beacon Effect** (`#d946ef`) on the WebGL map with date, time, and coordinates.

5. **Multilingual Alert Dispatcher**:
   - Generates localized emergency warning SMS cards in English, Assamese, Khasi, and Hindi (`POST /api/agent/dispatch-alert`).

6. **100% Free, Zero-API-Key Basemaps**:
   - Uses Esri World Dark Gray Canvas, OpenStreetMap, and Esri World Imagery with **zero watermarks** and **zero API key dependencies**.

---

## 🛠️ Quickstart & Setup Guide

### 1. Prerequisites
- **Python**: Version `3.10` or higher
- **Web Browser**: Chrome, Edge, or Firefox with WebGL enabled

### 2. Environment & Data Files Setup
Clone or navigate to your workspace root directory:

```powershell
cd c:\Users\Karan\Desktop\cursorprojects\SIH2026
```

Create a `.env` file in the project root directory and add the environment variable:

```env
BHUVAN_ROUTING_KEY=your_bhuvan_routing_key_here
```

Ensure the following 2 required GIS dataset files are placed in the project root directory:
- **`ner_ilsm_cropped.tif`** (590.5 MB Continuous GeoTIFF Susceptibility Raster)
- **`northeast_osm.geojson`** (46.6 MB OpenStreetMap Spatial Vector Dataset)

Create and activate a virtual environment (optional but recommended):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
Install all required Python packages from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### 4. Run the Gateway Server
Launch the central FastAPI application:

```powershell
python backend/main.py
```

### 5. Access the Web Applications
Once Uvicorn displays `INFO: Application startup complete.`, open your browser:
- **Landing Portal**: `http://localhost:8000/`
- **WebGL GPU Map**: `http://localhost:8000/proto2`
- **AI Chatbot Agent**: `http://localhost:8000/chatbot`

---

## 📡 REST API Documentation Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/info` | API metadata and loaded dataset status |
| `GET` | `/api/stats` | Regional spatial statistics and state/district feature counts |
| `GET` | `/api/geojson/northeast` | Filterable OSM spatial vector GeoJSON |
| `GET` | `/api/raster/susceptibility/info` | GeoTIFF raster bounds, statistics, and extent |
| `GET` | `/api/raster/susceptibility/query` | Continuous risk score for specific `lat` & `lon` |
| `GET` | `/api/route` | Road routing API with GeoTIFF hazard sampling & critical segment extraction |
| `POST` | `/api/agent/upload-incident` | Upload field photo & extract EXIF GPS coordinates |
| `POST` | `/api/agent/report-incident` | Submit pinpointed incident with category, custom message, date & time |
| `GET` | `/api/agent/incidents` | Fetch active pinpointed field incidents for map overlays |
| `POST` | `/api/agent/dispatch-alert` | Generate multilingual SMS cards for emergency authorities |

---

## 📜 License
Developed for Smart India Hackathon 2026 (SIH2026). Open source under MIT License.
