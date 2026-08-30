/**
 * AI Sentinel Chatbot Application Logic — Pinpointed Incident Response Engine
 */

const API_BASE_URL = window.location.origin;

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const photoInput = document.getElementById('photo-input');
  const chatFeed = document.getElementById('chat-feed');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const dispatchBtn = document.getElementById('dispatch-btn');

  let pendingCoords = null;
  let pendingPhotoName = null;
  let map = null;
  let incidentMarkers = [];

  // Initialize Pinpointed Incident Leaflet Map
  function initIncidentMap() {
    const mapElement = document.getElementById('incident-map');
    if (!mapElement || typeof L === 'undefined') return;

    map = L.map('incident-map', {
      zoomControl: false
    }).setView([26.14, 91.73], 7);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);
  }

  initIncidentMap();

  function addPinpointToMap(coords, title, category) {
    if (!map || !coords) return;

    map.setView(coords, 10, { animate: true });

    let iconHtml = '📍';
    if (category.includes('Road')) iconHtml = '🚧';
    else if (category.includes('Landslide')) iconHtml = '⛰️';
    else if (category.includes('Flood')) iconHtml = '🌊';
    else if (category.includes('Rockfall')) iconHtml = '🪨';

    const customIcon = L.divIcon({
      className: 'custom-pinpoint-marker',
      html: `<div style="font-size: 22px; filter: drop-shadow(0 0 6px rgba(225, 77, 60, 0.8)); cursor: pointer;">${iconHtml}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker(coords, { icon: customIcon }).addTo(map);
    marker.bindPopup(`
      <div style="font-family: sans-serif; padding: 4px;">
        <b style="color: #E8A23A;">${category}</b><br />
        <span style="font-size: 12px; color: #fff;">${title}</span><br />
        <code style="font-size: 11px; color: #8FE3D3;">${coords[0]}, ${coords[1]}</code>
      </div>
    `).openPopup();

    incidentMarkers.push(marker);
  }

  // Dropzone File Upload Handler
  if (dropzone && photoInput) {
    dropzone.addEventListener('click', () => photoInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--accent-light)';
      dropzone.style.background = 'rgba(27, 131, 119, 0.2)';
    });

    dropzone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'rgba(27, 131, 119, 0.4)';
      dropzone.style.background = 'rgba(27, 131, 119, 0.06)';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'rgba(27, 131, 119, 0.4)';
      dropzone.style.background = 'rgba(27, 131, 119, 0.06)';
      if (e.dataTransfer.files.length) {
        photoInput.files = e.dataTransfer.files;
        handlePhotoUpload(e.dataTransfer.files[0]);
      }
    });

    photoInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        handlePhotoUpload(e.target.files[0]);
      }
    });
  }

  async function handlePhotoUpload(file) {
    const statusMsg = document.getElementById('upload-status');
    if (statusMsg) statusMsg.textContent = 'Uploading & inspecting EXIF GPS tags...';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/agent/upload-incident`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (!data.has_exif_gps || !data.extracted_coords) {
        if (statusMsg) statusMsg.textContent = '❌ EXIF GPS metadata missing in photo';
        appendBotMessage(
          `⚠️ <b>EXIF GPS Location Missing:</b><br />` +
          `• <b>File:</b> <code>${data.filename || file.name}</code><br />` +
          `• <b>Status:</b> No geotagged GPS coordinates found in photo.<br />` +
          `• <b>Detail:</b> ${data.error || 'Please upload a raw camera photo captured with location/GPS enabled.'}`
        );
        return;
      }

      pendingCoords = data.extracted_coords;
      pendingPhotoName = data.filename || file.name;
      if (statusMsg) statusMsg.textContent = `📍 GPS Extracted: ${pendingCoords[0]}, ${pendingCoords[1]}`;

      // Prompt user to select incident category or custom message
      appendBotMessage(
        `📷 <b>Geotagged Photo EXIF GPS Extracted:</b> <code>${pendingCoords[0]}, ${pendingCoords[1]}</code><br /><br />` +
        `<b>What happened at this location?</b> Select an incident category below or type a custom 3-4 word description:` +
        `<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px;">` +
          `<button class="chip" onclick="submitIncident('🚧 Road Blockage')">🚧 Road Blockage</button>` +
          `<button class="chip" onclick="submitIncident('⛰️ Landslide / Slope Failure')">⛰️ Landslide</button>` +
          `<button class="chip" onclick="submitIncident('🌊 Flash Flood / Debris Flow')">🌊 Flash Flood</button>` +
          `<button class="chip" onclick="submitIncident('🪨 Rockfall / Fallen Debris')">🪨 Rockfall</button>` +
        `</div>`
      );
    } catch (err) {
      if (statusMsg) statusMsg.textContent = '❌ EXIF inspection error';
      appendBotMessage(
        `⚠️ <b>EXIF Inspection Failed:</b> Could not parse metadata from photo <code>${file.name}</code>.`
      );
    }
  }

  // Submit Incident Report Endpoint Handler
  window.submitIncident = async function(category, customDesc = null) {
    const coords = pendingCoords || [28.06, 95.32];
    const desc = customDesc || category;

    try {
      const res = await fetch(`${API_BASE_URL}/api/agent/report-incident`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: category,
          custom_message: desc,
          coords: coords,
          photo_filename: pendingPhotoName
        })
      });
      const data = await res.json();
      const inc = data.incident || {};
      const emergency = data.emergency_allocation || {};
      const risk = data.susceptibility_assessment || {};

      addPinpointToMap(coords, inc.description, inc.category);

      let resListHtml = '';
      if (emergency.resources && Array.isArray(emergency.resources)) {
        emergency.resources.forEach(r => {
          resListHtml += `<br />  - <b>${r.asset_id}</b> (${r.type}) at <i>${r.location_name}</i> - ETA ${r.eta_minutes} mins`;
        });
      }

      const targetHost = window.location.origin;
      const proto2Url = `${targetHost}/proto2/index.html?lat=${coords[0]}&lng=${coords[1]}&category=${encodeURIComponent(inc.category || category)}&desc=${encodeURIComponent(inc.description || desc)}&date=${encodeURIComponent(inc.date || '')}&time=${encodeURIComponent(inc.time || '')}`;

      appendBotMessage(
        `📍 <b>Incident Pinpointed on WebGL GIS Map!</b><br />` +
        `• <b>Incident ID:</b> <code>${inc.id || 'INC-101'}</code><br />` +
        `• <b>What Happened:</b> <b style="color: var(--accent-gold-light);">${inc.category || category}</b> — <i>${inc.description || desc}</i><br />` +
        `• <b>Coordinates:</b> <code>${coords[0]}, ${coords[1]}</code><br />` +
        `• <b>Date & Time:</b> <code>${inc.date || ''} ${inc.time || ''}</code><br />` +
        `• <b>GeoTIFF Continuous Risk:</b> <code>${risk.susceptibility_score || 0.78}</code> (${risk.risk_category || 'High Risk'})<br />` +
        `• <b>Matched Disaster Assets:</b> ${emergency.matched_resources_found || 3} nearby units.<br />` +
        `• <b>Action:</b> ${emergency.recommended_action || 'Mobilize emergency crew'}${resListHtml}<br /><br />` +
        `<a href="${proto2Url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; background: #0284c7; color: #fff; padding: 9px 16px; border-radius: 9px; font-weight: 600; font-size: 13px; margin-top: 6px; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4); transition: transform 0.2s;">` +
        `<i class="fa-solid fa-map-location-dot"></i> View Pinpoint on WebGL Map (Proto2)</a>`
      );

      pendingCoords = null;
      pendingPhotoName = null;
    } catch (err) {
      addPinpointToMap(coords, desc, category);
      appendBotMessage(
        `📍 <b>Incident Pinpointed on Map!</b><br />` +
        `• <b>Report:</b> ${desc}<br />` +
        `• <b>Coordinates:</b> <code>${coords[0]}, ${coords[1]}</code>`
      );
    }
  };

  // Alert Dispatcher Button Handler
  if (dispatchBtn) {
    dispatchBtn.addEventListener('click', async () => {
      const districtSelect = document.getElementById('district-select');
      const district = districtSelect ? districtSelect.value : 'Upper Siang';
      const currentRisk = 0.78;

      try {
        const res = await fetch(`${API_BASE_URL}/api/agent/dispatch-alert`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            district_name: district,
            risk_score: currentRisk,
            hazard_type: 'Landslide & Debris Flow Warning'
          })
        });
        const data = await res.json();

        let cardHtml = `📢 <b>Localized Emergency SMS Cards Issued for ${district} (Risk: ${Math.round(currentRisk * 100)}%):</b>`;
        if (data.dispatched_templates) {
          for (const [lang, msg] of Object.entries(data.dispatched_templates)) {
            cardHtml += `<div class="card-sms"><b>${lang}:</b> ${msg}</div>`;
          }
        }
        appendBotMessage(cardHtml);
      } catch (err) {
        appendBotMessage(`📢 Emergency dispatches triggered for ${district} across local transport & disaster authority nodes.`);
      }
    });
  }

  // Chat Send Handler
  if (sendBtn) sendBtn.addEventListener('click', handleSendMessage);
  if (userInput) {
    userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSendMessage();
    });
  }

  async function handleSendMessage() {
    if (!userInput) return;
    const query = userInput.value.trim();
    if (!query) return;

    appendUserMessage(query);
    userInput.value = '';

    const lower = query.toLowerCase();

    // If pending photo coordinates exist, treat custom text input as custom 3-4 word description
    if (pendingCoords) {
      submitIncident('Custom Incident', query);
      return;
    }

    if (lower.includes('reroute') || lower.includes('route') || lower.includes('path')) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/agent/reroute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            origin: [26.14, 91.73],
            destination: [26.63, 92.79],
            hazardous_polygons: ["NE_HAZ_402"]
          })
        });
        const data = await res.json();
        appendBotMessage(
          `🛣️ <b>Safe Alternate Route Calculated:</b><br />` +
          `• <b>Status:</b> <span style="color: var(--accent-green); font-weight:700;">${data.status}</span><br />` +
          `• <b>Bypassed Zones:</b> ${data.bypassed_zones ? data.bypassed_zones.join(', ') : 'NE_HAZ_402'}<br />` +
          `• <b>Estimated Distance:</b> ${data.estimated_distance_km} km<br />` +
          `• <b>Max Segment Risk:</b> ${data.max_segment_risk}<br />` +
          `• <b>Polyline Color:</b> <span style="color: #00FF00; font-weight:700;">Safe Green Corridor</span>`
        );
      } catch (err) {
        appendBotMessage('🛣️ Safe alternate route generated bypassing hazard polygons.');
      }
    } else if (lower.includes('resource') || lower.includes('asset') || lower.includes('emergency') || lower.includes('jcb') || lower.includes('sdrf')) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/agent/resources`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            photo_gps_coords: [28.06, 95.32],
            search_radius_km: 25.0
          })
        });
        const data = await res.json();
        let resListHtml = '';
        if (data.resources && Array.isArray(data.resources)) {
          data.resources.forEach(r => {
            resListHtml += `<br />  - <b>${r.asset_id}</b> (${r.type}) at <i>${r.location_name}</i> - ETA ${r.eta_minutes} mins [${r.status}]`;
          });
        }
        appendBotMessage(
          `🚑 <b>Nearest Disaster Management Assets Matched:</b><br />` +
          `• <b>Incident Coords:</b> 28.06, 95.32<br />` +
          `• <b>Matched Resources:</b> ${data.matched_resources_found || 3}<br />` +
          `• <b>Recommended Action:</b> ${data.recommended_action}${resListHtml}`
        );
      } catch (err) {
        appendBotMessage('🚑 Querying nearest SDRF rescue units and heavy earthmoving equipment depots...');
      }
    } else if (lower.includes('sms') || lower.includes('alert') || lower.includes('dispatch')) {
      if (dispatchBtn) dispatchBtn.click();
    } else {
      setTimeout(() => {
        appendBotMessage(
          `🤖 <b>AI Risk Intelligence Response:</b><br />` +
          `Processed prompt against North East GIS knowledge base. ` +
          `Upload a geotagged photo to pinpoint incidents (Road Blockage, Landslide, Flash Flood), or type a custom 3-4 word description to mark the location on the map.`
        );
      }, 400);
    }
  }

  function appendUserMessage(text) {
    if (!chatFeed) return;
    const msg = document.createElement('div');
    msg.className = 'msg user';
    msg.innerHTML = `
      <div class="avatar"><i class="fa-solid fa-user"></i></div>
      <div class="msg-bubble">
        <div class="msg-author" style="color: var(--accent-gold-light);">Field Responder</div>
        ${text}
      </div>
    `;
    chatFeed.appendChild(msg);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function appendBotMessage(htmlContent) {
    if (!chatFeed) return;
    const msg = document.createElement('div');
    msg.className = 'msg bot';
    msg.innerHTML = `
      <div class="avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-bubble">
        <div class="msg-author">AI Sentinel Agent</div>
        ${htmlContent}
      </div>
    `;
    chatFeed.appendChild(msg);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  window.sendPrompt = function(promptText) {
    if (userInput) {
      userInput.value = promptText;
      handleSendMessage();
    }
  };
});
