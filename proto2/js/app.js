/**
 * North East India Spatial Map (Proto2) - WebGL & Deck.gl Application Logic
 */

const API_BASE_URL = (window.location.port === '8000') ? window.location.origin : 'http://localhost:8000';

// Global Application State
const state = {
  map: null,
  deckOverlay: null,
  routeOrigin: null,
  routeDest: null,
  pickMode: null,
  routeGeoJSON: null,
  routeMetadata: {},
  currentGeoJSON: null,
  currentLandslidesGeoJSON: null,
  currentHazardGeoJSON: null,
  allDistrictsByState: {},
  activeFilters: {
    state: '',
    district: '',
    year: '',
    searchQuery: ''
  },
  layerVisibility: {
    stations: true,
    landslides: true,
    hazard: false,
    tifRaster: true
  },
  rasterOpacity: 0.8,
  rasterInfo: null,
  availableYears: [],
  yearsCount: {},
  boundsNE: null,
  currentStyle: 'dark'
};

// MapLibre Tile Styles (100% Free, Zero-API-Key Raster Tile Sources)
const STYLES = {
  dark: {
    version: 8,
    sources: {
      'esri-dark': {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
      }
    },
    layers: [
      {
        id: 'esri-dark-layer',
        type: 'raster',
        source: 'esri-dark',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  },
  street: {
    version: 8,
    sources: {
      'osm-street': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }
    },
    layers: [
      {
        id: 'osm-street-layer',
        type: 'raster',
        source: 'osm-street',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  },
  satellite: {
    version: 8,
    sources: {
      'esri-satellite': {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: '&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
      }
    },
    layers: [
      {
        id: 'esri-sat-layer',
        type: 'raster',
        source: 'esri-satellite',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  fetchStatsAndDistricts();
  fetchGeoJSONData();
  fetchFieldIncidents();
  setupEventListeners();
  setupRoutingEventListeners();
  setTimeout(checkUrlTargeting, 1000);
});

// Fetch Field-Reported Pinpointed Incidents
async function fetchFieldIncidents() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/agent/incidents`);
    if (!res.ok) return;
    const data = await res.json();
    state.fieldIncidents = data.incidents || [];
    updateDeckLayers();
  } catch (err) {
    console.warn('Field incidents fetch note:', err);
  }
}

// Check URL Query Parameters for Targeted Incident Pinpointing (e.g. ?lat=28.06&lng=95.32)
function checkUrlTargeting() {
  const params = new URLSearchParams(window.location.search);
  const latParam = params.get('lat');
  const lngParam = params.get('lng');
  if (latParam && lngParam && state.map) {
    const lat = parseFloat(latParam);
    const lng = parseFloat(lngParam);
    const category = params.get('category') || 'Field Incident Pinpoint';
    const desc = params.get('desc') || category;
    const date = params.get('date') || new Date().toISOString().split('T')[0];
    const time = params.get('time') || new Date().toTimeString().split(' ')[0];

    state.map.flyTo({ center: [lng, lat], zoom: 12.8, pitch: 25, duration: 2200 });

    // Create pulsing purple HTML beacon marker for maximum visibility
    const el = document.createElement('div');
    el.className = 'purple-pulsing-marker';
    el.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';

    new maplibregl.Marker({ element: el })
      .setLngLat([lng, lat])
      .addTo(state.map);

    new maplibregl.Popup({ closeOnClick: false, offset: [0, -14] })
      .setLngLat([lng, lat])
      .setHTML(`
        <div style="font-family: sans-serif; padding: 6px; color: #081522; min-width: 210px;">
          <div style="color: #c084fc; font-weight: 800; font-size: 15px; margin-bottom: 4px;"><i class="fa-solid fa-triangle-exclamation"></i> ${category}</div>
          <div style="color: #0f172a; font-size: 13px; margin-bottom: 6px;"><b>What Happened:</b> ${desc}</div>
          <div style="font-family: monospace; font-size: 11.5px; color: #0284c7;">📍 Coords: ${lat}, ${lng}</div>
          <div style="font-family: monospace; font-size: 11.5px; color: #d97706;">🕒 Date & Time: ${date} at ${time}</div>
        </div>
      `)
      .addTo(state.map);
  }
}

// Initialize MapLibre GL Map & Deck.gl Overlay
function initMap() {
  // Center on North East India with regional bounds and zoom limits
  state.map = new maplibregl.Map({
    container: 'map',
    style: STYLES.dark,
    center: [92.2, 25.8],
    zoom: 6.8,
    minZoom: 5.0,
    maxZoom: 16.0,
    maxBounds: [[82.0, 18.0], [102.0, 32.5]],
    pitch: 0,
    bearing: 0
  });

  // Add standard navigation controls (Zoom, Pitch, Compass)
  state.map.addControl(new maplibregl.NavigationControl(), 'top-right');
  state.map.addControl(new maplibregl.FullscreenControl(), 'top-right');

  // Initialize Deck.gl MapboxOverlay for GPU rendering
  state.deckOverlay = new deck.MapboxOverlay({
    layers: [],
    getTooltip: getDeckTooltip
  });

  state.map.addControl(state.deckOverlay);

  // Map Click Listener for interactive Origin/Destination picking OR GeoTIFF Raster Probability Inspection
  state.map.on('click', async (e) => {
    const lat = parseFloat(e.lngLat.lat.toFixed(5));
    const lng = parseFloat(e.lngLat.lng.toFixed(5));

    if (state.pickMode === 'origin') {
      state.routeOrigin = { lat, lng };
      const origInput = document.getElementById('route-origin');
      if (origInput) origInput.value = `${lat}, ${lng}`;
      updateDeckLayers();
      state.pickMode = null;
      setRouteStatus('<i class="fa-solid fa-check"></i> Origin set! Now pick destination or click Find Path.');
      return;
    } else if (state.pickMode === 'dest') {
      state.routeDest = { lat, lng };
      const destInput = document.getElementById('route-dest');
      if (destInput) destInput.value = `${lat}, ${lng}`;
      updateDeckLayers();
      state.pickMode = null;
      setRouteStatus('<i class="fa-solid fa-check"></i> Destination set! Click Find Path.');
      return;
    }

    // Default Map Click: Query GeoTIFF Raster Probability Score
    if (state.layerVisibility.tifRaster) {
      inspectRasterPoint(lat, lng);
    }
  });

  state.map.on('load', () => {
    initRasterLayer();
    updateDeckLayers();
  });

  // Re-attach raster layer whenever basemap style reloads
  state.map.on('styledata', () => {
    if (state.map.isStyleLoaded() && state.rasterInfo && !state.map.getSource('tif-susceptibility-source')) {
      addRasterSourceAndLayer(state.rasterInfo, false);
    }
  });
}

// Fetch GeoTIFF Raster Info & Add MapLibre Raster Image Layer
async function initRasterLayer() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/raster/susceptibility/info`);
    if (!res.ok) return;
    const info = await res.json();
    state.rasterInfo = info;
    
    if (info.bounds) {
      const params = new URLSearchParams(window.location.search);
      const hasUrlTarget = params.get('lat') && params.get('lng');
      addRasterSourceAndLayer(info, !hasUrlTarget);
    }
  } catch (err) {
    console.warn('GeoTIFF raster overlay initialization note:', err);
  }
}

function addRasterSourceAndLayer(info, shouldFitBounds = true) {
  if (!state.map || !info || !info.extent) return;
  const [w, s, e, n] = info.extent; // [west, south, east, north]

  // Check if source already exists
  if (state.map.getSource('tif-susceptibility-source')) {
    if (state.map.getLayer('tif-susceptibility-layer')) {
      state.map.removeLayer('tif-susceptibility-layer');
    }
    state.map.removeSource('tif-susceptibility-source');
  }

  // Add MapLibre image source with exact coordinates
  state.map.addSource('tif-susceptibility-source', {
    type: 'image',
    url: `${API_BASE_URL}/api/raster/susceptibility/overlay.png?v=${Date.now()}`,
    coordinates: [
      [w, n], // Top-Left
      [e, n], // Top-Right
      [e, s], // Bottom-Right
      [w, s]  // Bottom-Left
    ]
  });

  // Add MapLibre raster layer below Deck.gl vector overlays
  state.map.addLayer({
    id: 'tif-susceptibility-layer',
    type: 'raster',
    source: 'tif-susceptibility-source',
    layout: {
      visibility: state.layerVisibility.tifRaster ? 'visible' : 'none'
    },
    paint: {
      'raster-opacity': state.rasterOpacity,
      'raster-fade-duration': 200
    }
  });

  // Fit map view to exact raster bounding box if requested
  if (shouldFitBounds && w && s && e && n) {
    state.map.fitBounds([
      [Math.min(w, e), Math.min(s, n)],
      [Math.max(w, e), Math.max(s, n)]
    ], { padding: 40 });
  }
}

// In-Memory Point Query Cache for GeoTIFF Raster Queries
const rasterPointCache = new Map();

// Query continuous probability score at lat/lon click point with LRU caching
async function inspectRasterPoint(lat, lng) {
  const cacheKey = `${lat.toFixed(4)},${lng.toFixed(4)}`;
  let data;

  if (rasterPointCache.has(cacheKey)) {
    data = rasterPointCache.get(cacheKey);
  } else {
    try {
      const res = await fetch(`${API_BASE_URL}/api/raster/susceptibility/query?lat=${lat}&lon=${lng}`);
      if (!res.ok) return;
      data = await res.json();
      if (rasterPointCache.size > 200) {
        const firstKey = rasterPointCache.keys().next().value;
        rasterPointCache.delete(firstKey);
      }
      rasterPointCache.set(cacheKey, data);
    } catch (err) {
      console.warn('Raster query failed:', err);
      return;
    }
  }

  const score = data.probability_score !== undefined ? data.probability_score : 0.0;
  const pct = data.percentage || `${(score * 100).toFixed(1)}%`;
  const cat = data.risk_category || 'Susceptibility Score';
  const color = data.color || '#a855f7';

  new maplibregl.Popup({ closeButton: true, className: 'custom-raster-popup' })
    .setLngLat([lng, lat])
    .setHTML(`
      <div style="font-family: var(--font-main); padding: 4px;">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
          <i class="fa-solid fa-layer-group" style="color: ${color}; font-size: 1.1rem;"></i>
          <h4 style="margin: 0; font-size: 0.95rem; color: #fff;">Landslide Susceptibility Score</h4>
        </div>
        <div style="background: rgba(0,0,0,0.3); border-radius: 6px; padding: 8px; border-left: 4px solid ${color};">
          <div style="font-size: 1.25rem; font-weight: 700; color: ${color}; font-family: var(--font-heading);">
            ${score} <span style="font-size: 0.85rem; color: #cbd5e1;">(${pct} probability)</span>
          </div>
          <div style="font-size: 0.8rem; font-weight: 600; color: #f8fafc; margin-top: 2px;">
            Risk Assessment: <span style="color: ${color};">${cat}</span>
          </div>
          <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
            📍 Coordinates: ${lat}, ${lng}
          </div>
        </div>
      </div>
    `)
    .addTo(state.map);
}

let isDeckUpdatePending = false;

// Throttled Deck.gl Layer Batching via requestAnimationFrame
function updateDeckLayers() {
  if (!state.deckOverlay) return;
  if (isDeckUpdatePending) return;

  isDeckUpdatePending = true;
  requestAnimationFrame(() => {
    isDeckUpdatePending = false;
    performDeckUpdate();
  });
}

function performDeckUpdate() {
  if (!state.deckOverlay) return;

  const layers = [];
  const searchQuery = state.activeFilters.searchQuery.toLowerCase();

  // 3. OSM Vector Features GPU Scatterplot Layer
  if (state.layerVisibility.stations && state.currentGeoJSON && state.currentGeoJSON.features) {
    const filteredOsmFeatures = state.currentGeoJSON.features.filter(feature => {
      if (!searchQuery) return true;
      const props = feature.properties || {};
      const name = String(props.name || props.station_name || '').toLowerCase();
      const fid = String(props.id || props.GmlID || '').toLowerCase();
      const dist = String(props.district__name || props.district || '').toLowerCase();
      const type = String(props.type || '').toLowerCase();
      return name.includes(searchQuery) || fid.includes(searchQuery) || dist.includes(searchQuery) || type.includes(searchQuery);
    });

    layers.push(
      new deck.ScatterplotLayer({
        id: 'osm-features-layer',
        data: filteredOsmFeatures,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 5,
        radiusMaxPixels: 12,
        lineWidthMinPixels: 1.5,
        getPosition: f => {
          const props = f.properties || {};
          const geom = f.geometry || {};
          if (geom.type === 'Point' && Array.isArray(geom.coordinates)) {
            return geom.coordinates;
          }
          return [props.long || 0, props.lat || 0];
        },
        getFillColor: [14, 165, 233, 220],
        getLineColor: [2, 132, 199, 255],
        onClick: info => handleFeatureClick(info)
      })
    );
  }

  // 4. Shortest Path Route GPU Path Layer
  if (state.routeGeoJSON) {
    layers.push(
      new deck.GeoJsonLayer({
        id: 'route-path-layer',
        data: state.routeGeoJSON,
        pickable: false,
        stroked: true,
        getLineColor: [6, 182, 212, 255],
        getLineWidth: 6,
        lineWidthMinPixels: 5
      })
    );
  }

  // 4b. Critical Hazard Route Segments Layer (Score >= 0.75 Highlight)
  if (state.criticalSegmentsGeoJSON) {
    layers.push(
      new deck.GeoJsonLayer({
        id: 'critical-route-path-layer',
        data: state.criticalSegmentsGeoJSON,
        pickable: true,
        autoHighlight: true,
        stroked: true,
        getLineColor: [239, 68, 68, 255],
        getLineWidth: 10,
        lineWidthMinPixels: 8
      })
    );
  }

  // 5. Origin and Destination Pin Markers
  const pins = [];
  if (state.routeOrigin) {
    pins.push({
      position: [state.routeOrigin.lng, state.routeOrigin.lat],
      color: [16, 185, 129, 255],
      label: 'Origin'
    });
  }
  if (state.routeDest) {
    pins.push({
      position: [state.routeDest.lng, state.routeDest.lat],
      color: [239, 68, 68, 255],
      label: 'Destination'
    });
  }

  if (pins.length > 0) {
    layers.push(
      new deck.ScatterplotLayer({
        id: 'route-pins-layer',
        data: pins,
        pickable: true,
        radiusMinPixels: 8,
        radiusMaxPixels: 14,
        getPosition: d => d.position,
        getFillColor: d => d.color,
        getLineColor: [255, 255, 255, 255],
        lineWidthMinPixels: 2
      })
    );
  }

  // 6. Field-Reported Pinpointed Incidents Layer
  if (state.fieldIncidents && state.fieldIncidents.length > 0) {
    layers.push(
      new deck.ScatterplotLayer({
        id: 'field-incidents-layer',
        data: state.fieldIncidents,
        pickable: true,
        autoHighlight: true,
        radiusMinPixels: 14,
        radiusMaxPixels: 28,
        getPosition: d => [d.lng || (d.coords ? d.coords[1] : 0), d.lat || (d.coords ? d.coords[0] : 0)],
        getFillColor: [217, 70, 239, 245],
        getLineColor: [255, 255, 255, 255],
        lineWidthMinPixels: 3.0
      })
    );
  }

  state.deckOverlay.setProps({ layers });
}


// Hover Tooltip Callback for Deck.gl
function getDeckTooltip({ object }) {
  if (!object) return null;

  if (object.category || object.status === "Pinpointed on WebGL GIS Map") {
    return {
      html: `
        <div style="font-family: sans-serif; padding: 6px; min-width: 210px;">
          <div style="color: #ef4444; font-weight: 700; font-size: 14px; margin-bottom: 4px;">🚨 ${object.category || 'Incident Pinpoint'}</div>
          <div style="color: #fff; font-size: 13px; margin-bottom: 4px;"><b>Report:</b> ${object.description || object.category}</div>
          <div style="font-family: monospace; font-size: 11.5px; color: #38bdf8;">📍 Coords: ${object.lat || (object.coords ? object.coords[0] : '')}, ${object.lng || (object.coords ? object.coords[1] : '')}</div>
          <div style="font-family: monospace; font-size: 11.5px; color: #f59e0b;">🕒 Date & Time: ${object.date || ''} ${object.time || ''}</div>
        </div>
      `
    };
  }

  const props = object.properties || {};

  const name = props.name || props.station_name || `Feature #${props.id || ''}`;
  const type = props.type || 'OSM Feature';
  return {
    html: `
      <div style="font-family: var(--font-main);">
        <h4 style="margin:0 0 4px 0; color: #38bdf8;">${name}</h4>
        <div><b>Type:</b> ${type}</div>
        ${props.district__name ? `<div><b>District:</b> ${props.district__name}</div>` : ''}
        <div><small>Click to inspect details drawer</small></div>
      </div>
    `
  };
}

// Click Inspection Handler for Deck.gl Objects
function handleFeatureClick(info) {
  if (!info || !info.object) return;
  const props = info.object.properties || {};
  const fid = props.id || props.GmlID || props.SlideNo || props.slideno;

  if (fid && typeof window.openFeatureDrawer === 'function') {
    window.openFeatureDrawer(fid);
  }
}

// Fetch Regional Statistics & Districts
async function fetchStatsAndDistricts(retries = 4) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    const stats = await res.json();
    
    state.stats = stats;
    state.allDistrictsByState = stats.districts_by_state || {};
    
    let totalDistricts = 0;
    Object.values(state.allDistrictsByState).forEach(arr => {
      totalDistricts += arr.length;
    });

    const kpiDistricts = document.getElementById('kpi-districts');
    if (kpiDistricts) {
      kpiDistricts.textContent = totalDistricts > 0 ? totalDistricts.toLocaleString() : '88+';
    }

    if (stats.landslides) {
      state.availableYears = stats.landslides.available_years || [];
      state.yearsCount = stats.landslides.years_count || {};
      populateYearControls();
    }
    
    if (stats.bounds) {
      state.boundsNE = [
        [stats.bounds.min_lng, stats.bounds.min_lat],
        [stats.bounds.max_lng, stats.bounds.max_lat]
      ];
    }

    updateKPICards();
  } catch (err) {
    if (retries > 0) {
      setTimeout(() => fetchStatsAndDistricts(retries - 1), 2500);
    }
  }
}

// Update Left Sidebar KPI Cards
function updateKPICards() {
  const kpiTotal = document.getElementById('kpi-total');
  const kpiLs = document.getElementById('kpi-landslides');

  const selectedState = (document.getElementById('state-select')?.value) || state.activeFilters.state;
  const selectedYear = (document.getElementById('year-select')?.value) || state.activeFilters.year;

  if (kpiLs) {
    if (selectedState && state.currentLandslidesGeoJSON && state.currentLandslidesGeoJSON.features) {
      kpiLs.textContent = state.currentLandslidesGeoJSON.features.length.toLocaleString();
    } else if (selectedYear && state.yearsCount[selectedYear] !== undefined) {
      kpiLs.textContent = state.yearsCount[selectedYear].toLocaleString();
    } else if (state.stats && state.stats.landslides && state.stats.landslides.total_landslides !== undefined) {
      kpiLs.textContent = state.stats.landslides.total_landslides.toLocaleString();
    }
  }

  if (kpiTotal) {
    if (selectedState && state.currentGeoJSON && state.currentGeoJSON.features) {
      kpiTotal.textContent = state.currentGeoJSON.features.length.toLocaleString();
    } else if (state.stats && state.stats.total_features !== undefined) {
      kpiTotal.textContent = state.stats.total_features.toLocaleString();
    }
  }
}

// Populate Year Select & Timeline Pills
function populateYearControls() {
  const yearSelect = document.getElementById('year-select');
  const yearPillsContainer = document.getElementById('year-pills-container');

  if (yearSelect) {
    yearSelect.innerHTML = '<option value="">All Years</option>';
    state.availableYears.forEach(yr => {
      const count = state.yearsCount[yr] ? ` (${state.yearsCount[yr].toLocaleString()})` : '';
      const opt = document.createElement('option');
      opt.value = yr;
      opt.textContent = `Year ${yr}${count}`;
      yearSelect.appendChild(opt);
    });
    if (state.activeFilters.year) {
      yearSelect.value = state.activeFilters.year;
    }
  }

  if (yearPillsContainer) {
    yearPillsContainer.innerHTML = '';
    
    const allPill = document.createElement('button');
    allPill.className = `year-pill ${!state.activeFilters.year ? 'active' : ''}`;
    allPill.dataset.year = '';
    allPill.textContent = 'All';
    yearPillsContainer.appendChild(allPill);

    state.availableYears.forEach(yr => {
      const pill = document.createElement('button');
      pill.className = `year-pill ${state.activeFilters.year === yr ? 'active' : ''}`;
      pill.dataset.year = yr;
      pill.textContent = yr;
      yearPillsContainer.appendChild(pill);
    });
  }
}

// Fetch GeoJSON FeatureCollection for OSM Features
async function fetchGeoJSONData(retries = 4) {
  try {
    let url = `${API_BASE_URL}/api/geojson/northeast?`;
    const stateSelect = document.getElementById('state-select');
    const districtSelect = document.getElementById('district-select');

    const selectedState = (stateSelect && stateSelect.value) || state.activeFilters.state;
    const selectedDistrict = (districtSelect && districtSelect.value) || state.activeFilters.district;
    if (selectedState) url += `state=${encodeURIComponent(selectedState)}&`;
    if (selectedDistrict) url += `district=${encodeURIComponent(selectedDistrict)}&`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load GeoJSON');
    
    state.currentGeoJSON = await res.json();
    updateDeckLayers();
    updateKPICards();
  } catch (err) {
    if (retries > 0) {
      setTimeout(() => fetchGeoJSONData(retries - 1), 2500);
    }
  }
}

// Global Feature Drawer Inspection
window.openFeatureDrawer = function(featureId) {
  let feature = null;
  let isLandslide = false;

  if (state.currentGeoJSON && state.currentGeoJSON.features) {
    feature = state.currentGeoJSON.features.find((f, idx) => {
      const p = f.properties || {};
      return String(p.id || p.GmlID || `feat_${idx}`) === String(featureId);
    });
  }

  if (!feature && state.currentLandslidesGeoJSON && state.currentLandslidesGeoJSON.features) {
    feature = state.currentLandslidesGeoJSON.features.find((f, idx) => {
      const p = f.properties || {};
      return String(p.SlideNo || p.slideno || p.id || `ls_${idx}`) === String(featureId);
    });
    if (feature) isLandslide = true;
  }

  if (!feature) return;

  const props = feature.properties || {};
  const geom = feature.geometry || {};

  const detailCode = document.getElementById('detail-code');
  const detailState = document.getElementById('detail-state');
  const detailDistrict = document.getElementById('detail-district');
  const detailCoords = document.getElementById('detail-coords');
  const drawerTag = document.getElementById('drawer-type-tag');
  const drawerName = document.getElementById('drawer-station-name');

  if (isLandslide) {
    const slideNo = props.SlideNo || props.slideno || props.id || featureId;
    if (detailCode) detailCode.textContent = slideNo;
    if (detailState) detailState.textContent = props.State || props.state || props.state_name || 'N/A';
    if (detailDistrict) detailDistrict.textContent = props.District || props.district || props.district__name || 'N/A';

    let lat, lng;
    if (geom.type === 'Point' && Array.isArray(geom.coordinates)) {
      [lng, lat] = geom.coordinates;
    } else if (geom.type === 'Polygon' && geom.coordinates && geom.coordinates.length > 0) {
      const ring = geom.coordinates[0];
      lat = ring.reduce((s, c) => s + c[1], 0) / ring.length;
      lng = ring.reduce((s, c) => s + c[0], 0) / ring.length;
    }
    if (detailCoords) detailCoords.textContent = `${lat ? lat.toFixed(4) : '--'}, ${lng ? lng.toFixed(4) : '--'}`;
    if (drawerTag) drawerTag.textContent = 'NDEM Landslide';
    if (drawerName) drawerName.textContent = `Landslide ${slideNo}`;
  } else {
    if (detailCode) detailCode.textContent = props.id || props.GmlID || featureId;
    if (detailState) detailState.textContent = props.state_name || state.activeFilters.state || 'N/A';
    if (detailDistrict) detailDistrict.textContent = props.district__name || props.district || 'N/A';

    let lat = props.lat;
    let lng = props.long;
    if (geom.type === 'Point' && Array.isArray(geom.coordinates)) {
      lng = geom.coordinates[0];
      lat = geom.coordinates[1];
    }

    if (detailCoords) detailCoords.textContent = `${lat ? lat.toFixed(4) : '--'}, ${lng ? lng.toFixed(4) : '--'}`;
    if (drawerTag) drawerTag.textContent = props.type || 'OSM Feature';
    if (drawerName) drawerName.textContent = props.name || props.station_name || `Feature #${featureId}`;
  }

  const drawerBackdrop = document.getElementById('drawer-backdrop');
  const stationDrawer = document.getElementById('station-drawer');

  if (drawerBackdrop) drawerBackdrop.classList.remove('hidden');
  if (stationDrawer) stationDrawer.classList.remove('hidden');
};

function closeDrawer() {
  const drawerBackdrop = document.getElementById('drawer-backdrop');
  const stationDrawer = document.getElementById('station-drawer');
  if (drawerBackdrop) drawerBackdrop.classList.add('hidden');
  if (stationDrawer) stationDrawer.classList.add('hidden');
}

function updateDistrictDropdown() {
  const stateSelect = document.getElementById('state-select');
  const districtSelect = document.getElementById('district-select');
  if (!stateSelect || !districtSelect) return;

  const selectedState = stateSelect.value;
  districtSelect.innerHTML = '<option value="">All Districts</option>';

  if (!selectedState) return;

  const districts = state.allDistrictsByState[selectedState] || [];
  districts.forEach(dist => {

    const opt = document.createElement('option');
    opt.value = dist;
    opt.textContent = dist;
    districtSelect.appendChild(opt);
  });
}

// Setup Main UI Event Listeners
function setupEventListeners() {
  const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
  if (toggleSidebarBtn) {
    toggleSidebarBtn.addEventListener('click', () => {
      const sidebar = document.getElementById('sidebar-controls');
      if (sidebar) sidebar.classList.toggle('mobile-open');
    });
  }


  const stateSelect = document.getElementById('state-select');
  const districtSelect = document.getElementById('district-select');
  const searchInput = document.getElementById('search-input');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const resetFiltersBtn = document.getElementById('reset-filters-btn');
  const resetBoundsBtn = document.getElementById('reset-bounds-btn');
  const toggleThemeBtn = document.getElementById('toggle-theme-btn');
  const toggleStations = document.getElementById('toggle-stations');
  const toggleLandslides = document.getElementById('toggle-landslides');
  const toggleHazard = document.getElementById('toggle-hazard');
  const closeDrawerBtn = document.getElementById('close-drawer-btn');
  const drawerBackdrop = document.getElementById('drawer-backdrop');

  if (stateSelect) {
    stateSelect.addEventListener('change', (e) => {
      state.activeFilters.state = e.target.value;
      state.activeFilters.district = '';
      updateDistrictDropdown();
      fetchGeoJSONData();
    });
  }

  if (districtSelect) {
    districtSelect.addEventListener('change', (e) => {
      state.activeFilters.district = e.target.value;
      fetchGeoJSONData();
    });
  }

  const toggleTifRaster = document.getElementById('toggle-tif-raster');
  const tifOpacitySlider = document.getElementById('tif-opacity-slider');
  const tifOpacityVal = document.getElementById('tif-opacity-val');

  if (toggleTifRaster) {
    toggleTifRaster.addEventListener('change', (e) => {
      state.layerVisibility.tifRaster = e.target.checked;
      if (state.map && state.map.getLayer('tif-susceptibility-layer')) {
        state.map.setLayoutProperty(
          'tif-susceptibility-layer',
          'visibility',
          e.target.checked ? 'visible' : 'none'
        );
      }
    });
  }

  if (tifOpacitySlider) {
    tifOpacitySlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value, 10);
      const opacityFloat = val / 100.0;
      state.rasterOpacity = opacityFloat;
      if (tifOpacityVal) tifOpacityVal.textContent = `${val}%`;
      if (state.map && state.map.getLayer('tif-susceptibility-layer')) {
        state.map.setPaintProperty('tif-susceptibility-layer', 'raster-opacity', opacityFloat);
      }
    });
  }

  if (toggleStations) {
    toggleStations.addEventListener('change', (e) => {
      state.layerVisibility.stations = e.target.checked;
      updateDeckLayers();
    });
  }

  if (toggleLandslides) {
    toggleLandslides.addEventListener('change', (e) => {
      state.layerVisibility.landslides = e.target.checked;
      updateDeckLayers();
    });
  }

  if (toggleHazard) {
    toggleHazard.addEventListener('change', (e) => {
      state.layerVisibility.hazard = e.target.checked;
      if (e.target.checked && (!state.currentHazardGeoJSON || !state.currentHazardGeoJSON.features)) {
        fetchHazardData();
      } else {
        updateDeckLayers();
      }
    });
  }

  if (searchInput) {
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      state.activeFilters.searchQuery = val;
      if (clearSearchBtn) clearSearchBtn.classList.toggle('hidden', val.length === 0);

      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        updateDeckLayers();
      }, 300);
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      state.activeFilters.searchQuery = '';
      clearSearchBtn.classList.add('hidden');
      updateDeckLayers();
    });
  }

  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      if (stateSelect) stateSelect.value = '';
      if (districtSelect) districtSelect.innerHTML = '<option value="">All Districts</option>';
      if (searchInput) searchInput.value = '';
      state.activeFilters = { state: '', district: '', searchQuery: '' };
      if (clearSearchBtn) clearSearchBtn.classList.add('hidden');
      if (toggleStations) { toggleStations.checked = true; state.layerVisibility.stations = true; }

      fetchGeoJSONData();
    });
  }

  if (resetBoundsBtn) {
    resetBoundsBtn.addEventListener('click', () => {
      if (state.boundsNE && state.map) {
        state.map.fitBounds(state.boundsNE, { padding: 40 });
      } else if (state.map) {
        state.map.flyTo({ center: [91.8933, 25.5788], zoom: 7.8 });
      }
    });
  }

  // Basemap Switcher Buttons
  const layerBtns = document.querySelectorAll('.layer-btn');
  layerBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetLayer = btn.getAttribute('data-layer');
      if (!targetLayer || !STYLES[targetLayer] || !state.map) return;

      layerBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      state.currentStyle = targetLayer;
      state.map.setStyle(STYLES[targetLayer]);

      // Re-attach GeoTIFF raster overlay & Deck.gl layers once new basemap style is completely idle
      const reattachLayers = () => {
        if (state.rasterInfo) {
          addRasterSourceAndLayer(state.rasterInfo, false);
        }
        updateDeckLayers();
      };

      if (state.map.isStyleLoaded()) {
        reattachLayers();
      } else {
        state.map.once('idle', reattachLayers);
      }
    });
  });

  if (closeDrawerBtn) closeDrawerBtn.addEventListener('click', closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);

  if (toggleThemeBtn) {
    toggleThemeBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      document.body.classList.toggle('dark-theme');
      const isDark = document.body.classList.contains('dark-theme');
      toggleThemeBtn.innerHTML = isDark ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });
  }
}

// Routing Event Listeners
function setupRoutingEventListeners() {
  const presetSelect = document.getElementById('route-preset-select');
  const btnPickOrigin = document.getElementById('btn-pick-origin');
  const btnPickDest = document.getElementById('btn-pick-dest');
  const btnCalcRoute = document.getElementById('btn-calc-route');
  const btnClearRoute = document.getElementById('btn-clear-route');
  const origInput = document.getElementById('route-origin');
  const destInput = document.getElementById('route-dest');

  if (presetSelect) {
    presetSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (!val) return;
      const [orig, dest] = val.split('|');
      const [oLat, oLng] = orig.split(',').map(Number);
      const [dLat, dLng] = dest.split(',').map(Number);

      state.routeOrigin = { lat: oLat, lng: oLng };
      state.routeDest = { lat: dLat, lng: dLng };

      if (origInput) origInput.value = `${oLat}, ${oLng}`;
      if (destInput) destInput.value = `${dLat}, ${dLng}`;

      updateDeckLayers();
      fetchShortestPathRoute();
    });
  }

  if (origInput) {
    let origDebounce;
    origInput.addEventListener('input', () => {
      clearTimeout(origDebounce);
      origDebounce = setTimeout(() => {
        parseRouteInputField('origin', false);
      }, 500);
    });
    origInput.addEventListener('change', () => {
      parseRouteInputField('origin', true);
    });
  }

  if (destInput) {
    let destDebounce;
    destInput.addEventListener('input', () => {
      clearTimeout(destDebounce);
      destDebounce = setTimeout(() => {
        parseRouteInputField('dest', false);
      }, 500);
    });
    destInput.addEventListener('change', () => {
      parseRouteInputField('dest', true);
    });
  }

  if (btnPickOrigin) {
    btnPickOrigin.addEventListener('click', () => {
      state.pickMode = 'origin';
      setRouteStatus('<i class="fa-solid fa-crosshairs"></i> Click anywhere on map to set <b>ORIGIN</b> point...');
    });
  }

  if (btnPickDest) {
    btnPickDest.addEventListener('click', () => {
      state.pickMode = 'dest';
      setRouteStatus('<i class="fa-solid fa-flag-checkered"></i> Click anywhere on map to set <b>DESTINATION</b> point...');
    });
  }

  if (btnCalcRoute) {
    btnCalcRoute.addEventListener('click', async () => {
      await parseRouteInputField('origin', true);
      await parseRouteInputField('dest', true);
      fetchShortestPathRoute();
    });
  }

  if (btnClearRoute) {
    btnClearRoute.addEventListener('click', () => {
      clearRoute();
    });
  }
}

// Parse Route Input Text (Coordinates or Geocoding)
async function parseRouteInputField(type, allowGeocode = true) {
  const inputEl = document.getElementById(type === 'origin' ? 'route-origin' : 'route-dest');
  if (!inputEl) return false;

  const rawVal = inputEl.value.trim();
  if (!rawVal) {
    if (type === 'origin') state.routeOrigin = null;
    else state.routeDest = null;
    updateDeckLayers();
    return false;
  }

  // 1. Try parsing Lat, Lng numeric coordinates
  const coordRegex = /^\s*(-?\d+(?:\.\d+)?)\s*[, \t]\s*(-?\d+(?:\.\d+)?)\s*$/;
  const match = rawVal.match(coordRegex);

  if (match) {
    const lat = parseFloat(match[1]);
    const lng = parseFloat(match[2]);

    if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      if (type === 'origin') state.routeOrigin = { lat, lng };
      else state.routeDest = { lat, lng };
      updateDeckLayers();
      return true;
    }
  }

  // 2. Geocode Location Name
  if (allowGeocode && rawVal.length >= 2) {
    try {
      const searchRes = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(rawVal)}&limit=1`);
      if (searchRes.ok) {
        const data = await searchRes.json();
        if (data.results && data.results.length > 0) {
          const feat = data.results[0];
          let lat = feat.lat;
          let lng = feat.long;

          if (typeof lat === 'number' && typeof lng === 'number') {
            if (type === 'origin') state.routeOrigin = { lat, lng };
            else state.routeDest = { lat, lng };
            inputEl.value = `${feat.name || rawVal} (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
            updateDeckLayers();
            return true;
          }
        }
      }

      const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(rawVal + ', North East India')}&limit=1`);
      if (geoRes.ok) {
        const geoData = await geoRes.json();
        if (geoData && geoData.length > 0) {
          const lat = parseFloat(geoData[0].lat);
          const lng = parseFloat(geoData[0].lon);
          if (type === 'origin') state.routeOrigin = { lat, lng };
          else state.routeDest = { lat, lng };
          inputEl.value = `${geoData[0].display_name.split(',')[0]} (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
          updateDeckLayers();
          return true;
        }
      }
    } catch (err) {
      console.warn('Geocoding error:', err);
    }
  }

  return false;
}

function setRouteStatus(msg, isError = false) {
  const statusEl = document.getElementById('route-status-msg');
  if (statusEl) {
    statusEl.style.color = isError ? '#ef4444' : 'var(--text-muted)';
    statusEl.innerHTML = msg;
  }
}

function clearRoute() {
  state.routeOrigin = null;
  state.routeDest = null;
  state.pickMode = null;
  state.routeGeoJSON = null;
  state.criticalSegmentsGeoJSON = null;
  state.routeMetadata = {};
  updateDeckLayers();

  const origInput = document.getElementById('route-origin');
  const destInput = document.getElementById('route-dest');
  const presetSelect = document.getElementById('route-preset-select');

  if (origInput) origInput.value = '';
  if (destInput) destInput.value = '';
  if (presetSelect) presetSelect.value = '';

  setRouteStatus('');
}

async function fetchShortestPathRoute() {
  if (!state.routeOrigin) await parseRouteInputField('origin', true);
  if (!state.routeDest) await parseRouteInputField('dest', true);

  if (!state.routeOrigin || !state.routeDest) {
    setRouteStatus('<i class="fa-solid fa-triangle-exclamation"></i> Please enter or pick valid Origin and Destination first!', true);
    return;
  }

  setRouteStatus('<i class="fa-solid fa-spinner fa-spin"></i> Calculating route & analyzing GeoTIFF hazard susceptibility...');

  try {
    const url = `${API_BASE_URL}/api/route?lat1=${state.routeOrigin.lat}&lon1=${state.routeOrigin.lng}&lat2=${state.routeDest.lat}&lon2=${state.routeDest.lng}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status === 'error' || !data.geojson) {
      setRouteStatus(`<i class="fa-solid fa-circle-exclamation" style="color:#ef4444;"></i> ${data.message || 'Routing failed.'}`, true);
      return;
    }

    state.routeGeoJSON = data.geojson;
    state.criticalSegmentsGeoJSON = data.critical_segments_geojson || null;
    state.routeMetadata = data;
    updateDeckLayers();

    const distText = data.distance_km ? ` | <b>${data.distance_km} km</b>` : '';
    const durText = data.duration_min ? ` (~${data.duration_min} mins)` : '';

    let hazardAlert = '';
    if (data.has_critical_hazards) {
      hazardAlert = `<div style="margin-top: 6px; padding: 8px 10px; background: rgba(239, 68, 68, 0.18); border: 1px solid rgba(239, 68, 68, 0.5); border-radius: 6px; color: #f87171; font-weight: 700; font-size: 0.75rem;">` +
        `<i class="fa-solid fa-triangle-exclamation"></i> CRITICAL ROUTE HAZARD: Passes through <b>${data.critical_sectors_count}</b> Critical Sector(s) (Peak Susceptibility: <span style="color:#fff; background:#dc2626; padding:1px 5px; border-radius:3px;">${data.max_susceptibility}</span> ≥ 0.75)! Highlighted in Red on WebGL map.` +
        `</div>`;
    } else {
      hazardAlert = `<div style="margin-top: 4px; color: #10b981; font-size: 0.72rem;"><i class="fa-solid fa-shield-halved"></i> Safe Corridor: Peak susceptibility along route is ${data.max_susceptibility || '0.00'} (< 0.75).</div>`;
    }

    setRouteStatus(`<i class="fa-solid fa-check-circle" style="color:#10b981;"></i> Route calculated!${distText}${durText}${hazardAlert}`);
  } catch (err) {
    console.error('Error fetching route:', err);
    setRouteStatus('<i class="fa-solid fa-circle-exclamation" style="color:#ef4444;"></i> Request failed to connect backend.', true);
  }
}
