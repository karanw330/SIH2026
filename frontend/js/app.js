/**
 * North East India Spatial Map - Frontend Application Logic
 */

const API_BASE_URL = 'http://localhost:8000';

// Global Application State
const state = {
  map: null,
  markersLayer: null,
  landslidesLayer: null,
  hazardLayer: null,
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
  availableYears: [],
  yearsCount: {},
  tileLayers: {},
  boundsNE: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  fetchStatsAndDistricts();
  fetchGeoJSONData();
  fetchLandslidesData();
  fetchHazardData();
  setupEventListeners();
});

// Initialize Leaflet Map
function initMap() {
  // Center on North East India
  state.map = L.map('map', {
    center: [25.5788, 91.8933],
    zoom: 8,
    zoomControl: false
  });

  // Add Zoom control at top right
  L.control.zoom({ position: 'topright' }).addTo(state.map);

  // Basemap Tile Layers
  state.tileLayers.dark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  });

  state.tileLayers.satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19,
    maxNativeZoom: 18
  });

  state.tileLayers.street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  });

  // Set default dark layer
  state.tileLayers.dark.addTo(state.map);

  // Marker Cluster Group for OSM features with fallback
  if (typeof L.markerClusterGroup === 'function') {
    state.markersLayer = L.markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 40,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        return L.divIcon({
          html: `<div class="cluster-inner"><span>${count}</span></div>`,
          className: 'custom-cluster-icon',
          iconSize: L.point(40, 40)
        });
      }
    });
  } else {
    state.markersLayer = L.layerGroup();
  }

  // Global Canvas Renderer for high-performance vector rendering
  state.canvasRenderer = L.canvas({ padding: 0.2 });

  // Layer groups for NDEM Hazard Zonation and Landslide Polygons
  state.hazardLayer = L.layerGroup();
  state.landslidesLayer = L.layerGroup();

  // Order layers: Baseline Hazard Risk at bottom, Landslide Polygons in middle, Point Markers on top
  state.map.addLayer(state.hazardLayer);
  state.map.addLayer(state.landslidesLayer);
  state.map.addLayer(state.markersLayer);
}

// Fetch Regional Statistics & Districts
async function fetchStatsAndDistricts() {
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
      state.boundsNE = L.latLngBounds(
        [stats.bounds.min_lat, stats.bounds.min_lng],
        [stats.bounds.max_lat, stats.bounds.max_lng]
      );
    }

    updateKPICards();
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

// Update Left Sidebar KPI Cards to display complete information regardless of viewport/zoom
function updateKPICards() {
  const kpiTotal = document.getElementById('kpi-total');
  const kpiLs = document.getElementById('kpi-landslides');

  const selectedState = (document.getElementById('state-select')?.value) || state.activeFilters.state;
  const selectedYear = (document.getElementById('year-select')?.value) || state.activeFilters.year;

  // 1. Landslide Total Metric
  if (kpiLs) {
    if (selectedState && state.currentLandslidesGeoJSON && state.currentLandslidesGeoJSON.features) {
      kpiLs.textContent = state.currentLandslidesGeoJSON.features.length.toLocaleString();
    } else if (selectedYear && state.yearsCount[selectedYear] !== undefined) {
      kpiLs.textContent = state.yearsCount[selectedYear].toLocaleString();
    } else if (state.stats && state.stats.landslides && state.stats.landslides.total_landslides !== undefined) {
      kpiLs.textContent = state.stats.landslides.total_landslides.toLocaleString();
    }
  }

  // 2. Total Spatial Features Metric
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
async function fetchGeoJSONData() {
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
    renderMapFeatures();
  } catch (err) {
    console.error('Error fetching GeoJSON:', err);
  }
}

// Fetch GeoJSON collection for NDEM/Bhuvan Landslide Polygons
async function fetchLandslidesData(shouldFitBounds = false) {
  try {
    let url = `${API_BASE_URL}/api/geojson/landslides?`;
    const stateSelect = document.getElementById('state-select');
    const districtSelect = document.getElementById('district-select');
    const yearSelect = document.getElementById('year-select');

    const selectedState = (stateSelect && stateSelect.value) || state.activeFilters.state;
    const selectedDistrict = (districtSelect && districtSelect.value) || state.activeFilters.district;

    if (selectedState) url += `state=${encodeURIComponent(selectedState)}&`;
    if (selectedDistrict) url += `district=${encodeURIComponent(selectedDistrict)}&`;
    
    const activeYear = (yearSelect && yearSelect.value) || state.activeFilters.year;
    if (activeYear) url += `year=${encodeURIComponent(activeYear)}&`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load Landslides GeoJSON');
    
    state.currentLandslidesGeoJSON = await res.json();
    renderLandslideFeatures(shouldFitBounds);
  } catch (err) {
    console.error('Error fetching Landslides GeoJSON:', err);
  }
}

// Fetch GeoJSON collection for NDEM Hazard Zonation Polygons (nerlhz50dsc) - 100% full dataset (no zoom/bbox clipping)
async function fetchHazardData() {
  try {
    let url = `${API_BASE_URL}/api/geojson/hazard?`;
    const stateSelect = document.getElementById('state-select');
    const districtSelect = document.getElementById('district-select');

    const selectedState = (stateSelect && stateSelect.value) || state.activeFilters.state;
    const selectedDistrict = (districtSelect && districtSelect.value) || state.activeFilters.district;

    if (selectedState) url += `state=${encodeURIComponent(selectedState)}&`;
    if (selectedDistrict) url += `district=${encodeURIComponent(selectedDistrict)}&`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load Hazard GeoJSON');

    state.currentHazardGeoJSON = await res.json();
    renderHazardFeatures();
  } catch (err) {
    console.error('Error fetching Hazard GeoJSON:', err);
  }
}

// Render GeoJSON Features (OSM Vector Points) on Map
function renderMapFeatures() {
  if (!state.currentGeoJSON || !state.markersLayer) return;

  state.markersLayer.clearLayers();

  const toggleStations = document.getElementById('toggle-stations');
  const kpiTotal = document.getElementById('kpi-total');

  if (toggleStations && !toggleStations.checked) {
    if (kpiTotal) kpiTotal.textContent = '0';
    return;
  }

  const features = state.currentGeoJSON.features || [];
  const searchQuery = state.activeFilters.searchQuery.toLowerCase();
  let validMarkerCount = 0;

  features.forEach((feature, index) => {
    const props = feature.properties || {};
    const geom = feature.geometry || {};

    if (searchQuery) {
      const name = String(props.name || props.station_name || '').toLowerCase();
      const fid = String(props.id || props.GmlID || '').toLowerCase();
      const dist = String(props.district__name || props.district || '').toLowerCase();
      const type = String(props.type || '').toLowerCase();

      if (!name.includes(searchQuery) && !fid.includes(searchQuery) && !dist.includes(searchQuery) && !type.includes(searchQuery)) {
        return;
      }
    }

    let lat = props.lat;
    let lng = props.long;

    if (geom.type === 'Point' && Array.isArray(geom.coordinates)) {
      lng = geom.coordinates[0];
      lat = geom.coordinates[1];
    }

    if (typeof lat === 'number' && typeof lng === 'number' && !isNaN(lat) && !isNaN(lng)) {
      const customIcon = L.divIcon({
        className: 'custom-marker surface',
        html: '<i class="fa-solid fa-location-dot"></i>',
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });
      const featureId = props.id || props.GmlID || `feat_${index}`;

      const popupHtml = `
        <div class="popup-card">
          <span class="popup-tag surface">${props.type || 'OSM Feature'}</span>
          <h3>${props.name || props.station_name || `Feature #${featureId}`}</h3>
          <div class="popup-meta">
            <div><strong>ID:</strong> ${featureId}</div>
            <div><strong>Coordinates:</strong> ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
            ${props.state_name ? `<div><strong>State:</strong> ${props.state_name}</div>` : ''}
            ${props.district__name ? `<div><strong>District:</strong> ${props.district__name}</div>` : ''}
          </div>
          <button class="popup-btn" onclick="openFeatureDrawer('${featureId}', ${index})">View Details</button>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.featureData = props;

      state.markersLayer.addLayer(marker);
      validMarkerCount++;
    }
  });

  updateKPICards();
}

// Render NDEM Landslide Polygons on Map using Hardware 2D Canvas
function renderLandslideFeatures(shouldFitBounds = false) {
  if (!state.currentLandslidesGeoJSON || !state.landslidesLayer) return;

  state.landslidesLayer.clearLayers();

  const toggleLandslides = document.getElementById('toggle-landslides');

  if (toggleLandslides && !toggleLandslides.checked) {
    const kpiLs = document.getElementById('kpi-landslides');
    if (kpiLs) kpiLs.textContent = '0';
    return;
  }

  const features = state.currentLandslidesGeoJSON.features || [];
  updateKPICards();

  const searchQuery = state.activeFilters.searchQuery.toLowerCase();

  const filteredFeatures = features.filter((feat) => {
    if (!searchQuery) return true;
    const props = feat.properties || {};
    const stateName = String(props.State || props.state || props.state_name || '').toLowerCase();
    const dist = String(props.District || props.district || props.district__name || '').toLowerCase();
    const activity = String(props.Activity || props.activity || props.lanslide_1 || '').toLowerCase();
    const slideno = String(props.SlideNo || props.slideno || props.id || '').toLowerCase();
    return stateName.includes(searchQuery) || dist.includes(searchQuery) || activity.includes(searchQuery) || slideno.includes(searchQuery);
  });

  const geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: filteredFeatures }, {
    renderer: state.canvasRenderer,
    pointToLayer: function(feature, latlng) {
      return L.circleMarker(latlng, {
        renderer: state.canvasRenderer,
        radius: 4,
        fillColor: '#ef4444',
        color: '#dc2626',
        weight: 1,
        opacity: 0.9,
        fillOpacity: 0.7
      });
    },
    style: function(feature) {
      const props = feature.properties || {};
      const activity = String(props.Activity || props.activity || props.lanslide_1 || '').toLowerCase();
      const isActive = activity.includes('active');
      return {
        renderer: state.canvasRenderer,
        color: isActive ? '#ef4444' : '#f59e0b',
        weight: 2,
        opacity: 0.9,
        fillColor: isActive ? '#ef4444' : '#f59e0b',
        fillOpacity: 0.4
      };
    },
    onEachFeature: function(feature, layer) {
      const props = feature.properties || {};
      const activity = props.Activity || props.activity || props.lanslide_1 || 'Landslide Feature';
      const stateName = props.State || props.state || props.state_name || 'N/A';
      const district = props.District || props.district || props.district__name || 'N/A';
      const rawYear = (props.Year || props.year || props.year_ || 'N/A').toString();
      const yearVal = rawYear.replace('.0', '');
      const slideNo = props.SlideNo || props.slideno || props.id || 'N/A';
      const area = props.Area_sqm || props.area_sqm || props.area || props.area_sq_m || 'N/A';
      const trigger = props.Triggering || props.triggering || props.trigg_fact || 'Rainfall';
      const geomorph = props.Geomorph || props.geomorph || 'N/A';
      const lithology = props.Lithology || props.lithology || 'N/A';
      const lulc = props.LULC || props.lulc || 'N/A';

      const isActive = String(activity).toLowerCase().includes('active');

      const popupHtml = `
        <div class="popup-card">
          <span class="popup-tag" style="background: ${isActive ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)'}; color: ${isActive ? '#ef4444' : '#f59e0b'};">
            <i class="fa-solid fa-triangle-exclamation"></i> ${activity}
          </span>
          <h3>Landslide ${slideNo}</h3>
          <div class="popup-meta">
            <div><strong>Year:</strong> <span style="color: var(--accent-amber); font-weight:700;">${yearVal}</span></div>
            <div><strong>State:</strong> ${stateName}</div>
            <div><strong>District:</strong> ${district}</div>
            <div><strong>Area:</strong> ${typeof area === 'number' ? area.toLocaleString() + ' sq m' : area}</div>
            <div><strong>Trigger Factor:</strong> ${trigger}</div>
            ${geomorph !== 'N/A' ? `<div><strong>Geomorphology:</strong> ${geomorph}</div>` : ''}
            ${lithology !== 'N/A' ? `<div><strong>Lithology:</strong> ${lithology}</div>` : ''}
            ${lulc !== 'N/A' ? `<div><strong>Land Cover (LULC):</strong> ${lulc}</div>` : ''}
          </div>
        </div>
      `;
      layer.bindPopup(popupHtml);
    }
  });

  state.landslidesLayer.addLayer(geoJsonLayer);

  if (shouldFitBounds && filteredFeatures.length > 0) {
    const layerBounds = geoJsonLayer.getBounds();
    if (layerBounds.isValid()) {
      state.map.fitBounds(layerBounds, { padding: [40, 40] });
    }
  }
}

// Render NDEM Hazard Zonation Polygons on Map using Hardware 2D Canvas
function renderHazardFeatures() {
  if (!state.currentHazardGeoJSON || !state.hazardLayer) return;

  state.hazardLayer.clearLayers();

  const toggleHazard = document.getElementById('toggle-hazard');
  if (toggleHazard && !toggleHazard.checked) return;

  const features = state.currentHazardGeoJSON.features || [];

  const geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: features }, {
    renderer: state.canvasRenderer,
    style: function(feature) {
      const props = feature.properties || {};
      const gridCode = props.grid_code || 3;

      let color = '#f59e0b';
      let fillColor = 'rgba(245, 158, 11, 0.40)';

      if (gridCode >= 4) {
        color = '#ef4444';
        fillColor = 'rgba(239, 68, 68, 0.45)';
      } else if (gridCode === 3) {
        color = '#f59e0b';
        fillColor = 'rgba(245, 158, 11, 0.40)';
      } else {
        color = '#eab308';
        fillColor = 'rgba(234, 179, 8, 0.35)';
      }

      return {
        renderer: state.canvasRenderer,
        color: color,
        weight: 1.5,
        opacity: 0.85,
        fillColor: fillColor,
        fillOpacity: 0.45
      };
    },
    onEachFeature: function(feature, layer) {
      const props = feature.properties || {};
      const gridCode = props.grid_code || 3;
      const zone = props.zone || 'NER';
      const fid = feature.id || props.id || 'N/A';

      let riskLabel = 'Moderate Risk';
      let riskBadgeStyle = 'background: rgba(245,158,11,0.2); color: #f59e0b;';

      if (gridCode >= 4) {
        riskLabel = 'High Risk';
        riskBadgeStyle = 'background: rgba(239,68,68,0.2); color: #ef4444;';
      } else if (gridCode <= 2) {
        riskLabel = 'Low Risk';
        riskBadgeStyle = 'background: rgba(234,179,8,0.2); color: #eab308;';
      }

      const popupHtml = `
        <div class="popup-card">
          <span class="popup-tag" style="${riskBadgeStyle}">
            <i class="fa-solid fa-shield-halved"></i> ${riskLabel} Zone
          </span>
          <h3>Hazard Feature ${fid}</h3>
          <div class="popup-meta">
            <div><strong>Grid Severity Code:</strong> ${gridCode}</div>
            <div><strong>Spatial Region:</strong> North East (${zone.toUpperCase()})</div>
            <div><strong>Baseline Risk:</strong> Structurally Vulnerable Terrain Overlay</div>
          </div>
        </div>
      `;
      layer.bindPopup(popupHtml);
    }
  });

  state.hazardLayer.addLayer(geoJsonLayer);
}

// Global function triggered from popup button
window.openFeatureDrawer = function(featureId, index) {
  if (!state.currentGeoJSON) return;

  const feature = state.currentGeoJSON.features.find((f, idx) => {
    const p = f.properties || {};
    return String(p.id || p.GmlID || `feat_${idx}`) === String(featureId);
  });

  if (!feature) return;

  const props = feature.properties || {};
  const geom = feature.geometry || {};

  const detailCode = document.getElementById('detail-code');
  const detailState = document.getElementById('detail-state');
  const detailDistrict = document.getElementById('detail-district');
  const detailCoords = document.getElementById('detail-coords');
  const drawerTag = document.getElementById('drawer-type-tag');
  const drawerName = document.getElementById('drawer-station-name');

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

// Event Listeners
function setupEventListeners() {
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
      fetchLandslidesData(true);
      fetchHazardData();
    });
  }

  if (districtSelect) {
    districtSelect.addEventListener('change', (e) => {
      state.activeFilters.district = e.target.value;
      fetchGeoJSONData();
      fetchLandslidesData(true);
      fetchHazardData();
    });
  }

  const yearSelect = document.getElementById('year-select');
  if (yearSelect) {
    yearSelect.addEventListener('change', (e) => {
      const selectedYear = e.target.value;
      state.activeFilters.year = selectedYear;

      // Update pills active state
      const yearPills = document.querySelectorAll('.year-pill');
      yearPills.forEach(p => {
        p.classList.toggle('active', (p.dataset.year || '') === selectedYear);
      });

      fetchLandslidesData();
    });
  }

  const yearPillsContainer = document.getElementById('year-pills-container');
  if (yearPillsContainer) {
    yearPillsContainer.addEventListener('click', (e) => {
      const pill = e.target.closest('.year-pill');
      if (!pill) return;

      const selectedYear = pill.dataset.year || '';
      state.activeFilters.year = selectedYear;

      if (yearSelect) yearSelect.value = selectedYear;

      const yearPills = document.querySelectorAll('.year-pill');
      yearPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      fetchLandslidesData();
    });
  }

  if (toggleStations) {
    toggleStations.addEventListener('change', () => {
      renderMapFeatures();
    });
  }

  if (toggleLandslides) {
    toggleLandslides.addEventListener('change', () => {
      renderLandslideFeatures();
    });
  }

  if (toggleHazard) {
    toggleHazard.addEventListener('change', () => {
      renderHazardFeatures();
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
        renderMapFeatures();
        renderLandslideFeatures();
      }, 300);
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      state.activeFilters.searchQuery = '';
      clearSearchBtn.classList.add('hidden');
      renderMapFeatures();
      renderLandslideFeatures();
    });
  }

  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      if (stateSelect) stateSelect.value = '';
      if (districtSelect) districtSelect.innerHTML = '<option value="">All Districts</option>';
      if (yearSelect) yearSelect.value = '';
      if (searchInput) searchInput.value = '';
      state.activeFilters = { state: '', district: '', year: '', searchQuery: '' };
      if (clearSearchBtn) clearSearchBtn.classList.add('hidden');
      if (toggleStations) toggleStations.checked = true;
      if (toggleLandslides) toggleLandslides.checked = true;

      const yearPills = document.querySelectorAll('.year-pill');
      yearPills.forEach(p => p.classList.toggle('active', p.dataset.year === ''));

      fetchGeoJSONData();
      fetchLandslidesData();
    });
  }

  if (resetBoundsBtn) {
    resetBoundsBtn.addEventListener('click', () => {
      if (state.boundsNE) {
        state.map.fitBounds(state.boundsNE);
      } else {
        state.map.setView([25.5788, 91.8933], 8);
      }
    });
  }

  // Basemap Switcher Buttons
  const layerBtns = document.querySelectorAll('.layer-btn');
  layerBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetLayer = btn.getAttribute('data-layer');
      if (!targetLayer || !state.tileLayers[targetLayer]) return;

      // Update active button UI
      layerBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Remove existing tile layers and add target layer
      Object.keys(state.tileLayers).forEach(key => {
        if (state.map.hasLayer(state.tileLayers[key])) {
          state.map.removeLayer(state.tileLayers[key]);
        }
      });

      state.tileLayers[targetLayer].addTo(state.map);
      state.tileLayers[targetLayer].bringToBack();
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
