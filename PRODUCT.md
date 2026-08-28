# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
FastAPI, Python, HTML5, Vanilla CSS (Glassmorphism design system), JavaScript, MapLibre GL, Deck.gl, GeoTIFF / rasterio

## Users
Disaster response officials, emergency authorities, field teams, regional administrators, and citizens in North East India needing landslide risk analytics, safe corridor routing, and incident reporting.

## Product Purpose
Multi-modal GIS analytics, continuous GeoTIFF landslide risk processing (590MB raster engine), 3D WebGL GPU map visualization, and AI incident response engine for North East India (SIH2026).

## Positioning
Combines continuous $0.00-1.00$ landslide susceptibility score querying against 28.4M raster pixels with real-time WebGL route hazard sampling, geotagged photo EXIF inspection, glowing red risk overlays, pulsing purple incident beacons, and multilingual emergency SMS alert dispatch (English, Assamese, Khasi, Hindi) on zero-API-key basemaps.

## Operating Context
- Emergency control rooms monitoring regional hazard levels.
- Field crews reporting on-ground road blockages, landslides, flash floods, and rockfalls with photo evidence.
- Travelers and logistics operators searching for safe mountain corridor routing.

## Capabilities and Constraints
- **Multi-Portal Gateway**: Single FastAPI server powering Landing Portal (`/`), Proto2 WebGL Map (`/proto2`), and AI Sentinel Chatbot (`/chatbot`).
- **GeoTIFF Raster Engine**: Reads `ner_ilsm_cropped.tif` (590.5 MB) via rasterio/Pillow for precise lat/lon risk score calculation and PNG overlay generation.
- **Vector Spatial Engine**: Reads `northeast_osm.geojson` (46.6 MB) with 333k spatial features.
- **WebGL GPU Map**: MapLibre GL + Deck.gl rendering with Esri Dark Gray / OSM basemaps.
- **Route Hazard Detection**: Highlights route segments passing through critical hazard zones ($\ge 0.75$) in glowing red.
- **EXIF GPS Inspection**: Parses camera EXIF data from field upload photos without generating fake coordinates.
- **Multilingual Dispatch Tool**: Produces emergency warning SMS cards in English, Assamese, Khasi, and Hindi.

## Brand Commitments
- **Name**: Landslide Sentinel AI — North East India GIS & Emergency Response Engine
- **Visual Identity**: Dark mode, vibrant high-contrast accents, glowing hazard overlays (`#ef4444`), glassmorphism UI, pulsing purple incident beacons (`#d946ef`).
- **Basemaps**: 100% free, zero-API-key Esri & OpenStreetMap basemaps with zero watermarks.

## Evidence on Hand
- `ner_ilsm_cropped.tif`: 590.5 MB continuous GeoTIFF raster dataset.
- `northeast_osm.geojson`: 46.6 MB OpenStreetMap spatial vector dataset.
- `hero-bg.jpg` / `frontend/images/hero-bg.jpg`: Landing page background imagery.
- `MILESTONES_PROGRESS.md`: Feature implementation tracker.

## Product Principles
1. **Empirical Precision Over Fallbacks**: Never simulate or fabricate risk scores, coordinates, or EXIF data; surface true system measurements and missing data states explicitly.
2. **Actionable Emergency Visuals**: Prioritize immediate visual clarity during crises—use glowing red hazard highlights, pulsing purple incident beacons, and glassmorphic telemetry cards.
3. **Multi-Audience Resilience**: Serve emergency decision-makers, field units, and citizens seamlessly across specialized web portals.
4. **Zero-Lockin Spatial Stack**: Rely on open standards, zero-API-key basemaps, and fast local raster computation.

## Accessibility & Inclusion
- High contrast dark mode UI optimized for low-light control rooms and daylight outdoor field usage.
- Multilingual alert support (English, Assamese, Khasi, Hindi).
