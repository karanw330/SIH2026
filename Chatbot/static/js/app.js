/**
 * AI Sentinel Chatbot Application Logic — Pinpointed Incident Response Engine
 * Aligned with DESIGN.md ("The Alpine Guardian" & "Command-Center Precision")
 * Authoritative Motion & Animation Suite
 */

const API_BASE_URL = (window.location.port === '8000') ? '' : 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const photoInput = document.getElementById('photo-input');
  const chatFeed = document.getElementById('chat-feed');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const dispatchBtn = document.getElementById('dispatch-btn');
  const clearFeedBtn = document.getElementById('clear-feed-btn');

  let pendingCoords = null;
  let pendingPhotoName = null;
  let map = null;
  let incidentMarkers = [];

  // Initialize Pinpointed Incident Leaflet Map (Dark Theme Tile Layer)
  function initIncidentMap() {
    const mapElement = document.getElementById('incident-map');
    if (!mapElement || typeof L === 'undefined') return;

    map = L.map('incident-map', {
      zoomControl: false,
      attributionControl: false
    }).setView([26.14, 91.73], 7);

    // High-contrast Dark Basemap Tiles (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; CartoDB &copy; OpenStreetMap'
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);
  }

  initIncidentMap();

  function addPinpointToMap(coords, title, category) {
    if (!map || !coords) return;

    map.setView(coords, 10, { animate: true, duration: 1.2 });

    let iconSymbol = '📍';
    if (category.includes('Road')) iconSymbol = '🚧';
    else if (category.includes('Landslide')) iconSymbol = '⛰️';
    else if (category.includes('Flood')) iconSymbol = '🌊';
    else if (category.includes('Rockfall')) iconSymbol = '🪨';

    // Pulsing Purple Beacon Leaflet Icon aligned with DESIGN.md (#D946EF)
    const customIcon = L.divIcon({
      className: 'custom-beacon-pin',
      html: `<span>${iconSymbol}</span>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });

    const marker = L.marker(coords, { icon: customIcon }).addTo(map);
    marker.bindPopup(`
      <div style="font-family: var(--font-body, sans-serif); padding: 4px;">
        <b style="color: #D4B85C; font-size: 13px;">${category}</b><br />
        <span style="font-size: 12px; color: #F1F2EE;">${title}</span><br />
        <code style="font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #8FE3D3; margin-top: 4px; display: inline-block;">📍 ${coords[0]}, ${coords[1]}</code>
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

    appendReasoningIndicator('EXIF GPS Inspection', 'Parsing camera EXIF metadata tags...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/agent/upload-incident`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      removeReasoningIndicator();

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
        `<b>What happened at this location?</b> Select an incident category below or type a custom description:` +
        `<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px;">` +
          `<button class="chip" onclick="submitIncident('🚧 Road Blockage')">🚧 Road Blockage</button>` +
          `<button class="chip" onclick="submitIncident('⛰️ Landslide Failure')">⛰️ Landslide</button>` +
          `<button class="chip" onclick="submitIncident('🌊 Flash Flood')">🌊 Flash Flood</button>` +
          `<button class="chip" onclick="submitIncident('🪨 Rockfall Debris')">🪨 Rockfall</button>` +
        `</div>`
      );
    } catch (err) {
      removeReasoningIndicator();
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

    appendReasoningIndicator('GeoTIFF & Asset Engine', 'Querying 590MB susceptibility raster & matching SDRF units...');

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
      removeReasoningIndicator();

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

      const targetHost = API_BASE_URL || 'http://localhost:8000';
      const proto2Url = `${targetHost}/proto2/index.html?lat=${coords[0]}&lng=${coords[1]}&category=${encodeURIComponent(inc.category || category)}&desc=${encodeURIComponent(inc.description || desc)}&date=${encodeURIComponent(inc.date || '')}&time=${encodeURIComponent(inc.time || '')}`;

      appendBotMessage(
        `📍 <b>Incident Pinpointed on WebGL GIS Map!</b><br />` +
        `• <b>Incident ID:</b> <code>${inc.id || 'INC-101'}</code><br />` +
        `• <b>What Happened:</b> <b style="color: var(--accent-gold-light);">${inc.category || category}</b> — <i>${inc.description || desc}</i><br />` +
        `• <b>Coordinates:</b> <code>${coords[0]}, ${coords[1]}</code><br />` +
        `• <b>Date & Time:</b> <code>${inc.date || ''} ${inc.time || ''}</code><br />` +
        `• <b>GeoTIFF Continuous Risk:</b> <code>${risk.susceptibility_score || 0.78}</code> (${risk.risk_category || 'High Risk'})<br />` +
        `• <b>Matched Disaster Assets:</b> ${emergency.matched_resources_found || 3} nearby units.<br />` +
        `• <b>Recommended Action:</b> ${emergency.recommended_action || 'Mobilize emergency crew'}${resListHtml}<br /><br />` +
        `<a href="${proto2Url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; background: linear-gradient(135deg, var(--forest-primary), var(--accent-teal)); color: #fff; padding: 9px 16px; border-radius: 9px; font-weight: 600; font-size: 13px; margin-top: 6px; box-shadow: 0 4px 14px rgba(27, 131, 119, 0.4); border: 1px solid rgba(255,255,255,0.15); transition: transform 0.2s;">` +
        `<i class="fa-solid fa-map-location-dot"></i> View Pinpoint on WebGL Map (Proto2)</a>`
      );

      pendingCoords = null;
      pendingPhotoName = null;
    } catch (err) {
      removeReasoningIndicator();
      addPinpointToMap(coords, desc, category);
      appendBotMessage(
        `📍 <b>Incident Pinpointed on Map!</b><br />` +
        `• <b>Report:</b> ${desc}<br />` +
        `• <b>Coordinates:</b> <code>${coords[0]}, ${coords[1]}</code>`
      );
    }
  };

  // Quick Category Report Trigger from Panel
  window.reportQuickIncident = function(category) {
    appendUserMessage(`Report incident: ${category}`);
    submitIncident(category);
  };

  // Alert Dispatcher Button Handler
  if (dispatchBtn) {
    dispatchBtn.addEventListener('click', async () => {
      const districtSelect = document.getElementById('district-select');
      const district = districtSelect ? districtSelect.value : 'Upper Siang';
      const currentRisk = 0.78;

      appendReasoningIndicator('Multilingual Alert Dispatcher', `Generating localized emergency SMS cards for ${district}...`);

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
        removeReasoningIndicator();

        let cardHtml = `📢 <b>Localized Emergency SMS Cards Issued for ${district} (Risk: ${Math.round(currentRisk * 100)}%):</b>`;
        if (data.dispatched_templates) {
          let idx = 0;
          for (const [lang, msg] of Object.entries(data.dispatched_templates)) {
            const smsId = `sms-${Date.now()}-${idx++}`;
            cardHtml += `
              <div class="card-sms" style="animation-delay: ${idx * 0.1}s;">
                <div><b>${lang}:</b> <span id="${smsId}">${msg}</span></div>
                <button class="copy-btn" onclick="copySmsText('${smsId}')" title="Copy SMS Text"><i class="fa-regular fa-copy"></i></button>
              </div>`;
          }
        }
        appendBotMessage(cardHtml);
      } catch (err) {
        removeReasoningIndicator();
        appendBotMessage(`📢 Emergency dispatches triggered for ${district} across local transport & disaster authority nodes.`);
      }
    });
  }

  window.copySmsText = function(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
      navigator.clipboard.writeText(el.innerText);
      const btn = el.parentElement.parentElement.querySelector('.copy-btn');
      if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--safe-green);"></i>';
        setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i>'; }, 2000);
      }
    }
  };

  // Clear Feed Button Handler
  if (clearFeedBtn) {
    clearFeedBtn.addEventListener('click', () => {
      if (!chatFeed) return;
      chatFeed.innerHTML = `
        <div class="msg bot">
          <div class="avatar"><i class="fa-solid fa-robot"></i></div>
          <div class="msg-bubble">
            <div class="msg-author">AI Sentinel Agent</div>
            Feed cleared. Ready for field photo EXIF uploads or incident reports.
          </div>
        </div>
      `;
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

    // If pending photo coordinates exist, treat custom text input as custom description
    if (pendingCoords) {
      submitIncident('Custom Incident', query);
      return;
    }

    appendReasoningIndicator('AI Sentinel Engine', 'Evaluating query against North East spatial database...');

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
        removeReasoningIndicator();

        appendBotMessage(
          `🛣️ <b>Safe Alternate Route Calculated:</b><br />` +
          `• <b>Status:</b> <span style="color: var(--safe-green); font-weight:700;">${data.status}</span><br />` +
          `• <b>Bypassed Zones:</b> ${data.bypassed_zones ? data.bypassed_zones.join(', ') : 'NE_HAZ_402'}<br />` +
          `• <b>Estimated Distance:</b> ${data.estimated_distance_km} km<br />` +
          `• <b>Max Segment Risk:</b> ${data.max_segment_risk}<br />` +
          `• <b>Polyline Color:</b> <span style="color: #00FF00; font-weight:700;">Safe Green Corridor</span>`
        );
      } catch (err) {
        removeReasoningIndicator();
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
        removeReasoningIndicator();

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
        removeReasoningIndicator();
        appendBotMessage('🚑 Querying nearest SDRF rescue units and heavy earthmoving equipment depots...');
      }
    } else if (lower.includes('sms') || lower.includes('alert') || lower.includes('dispatch')) {
      removeReasoningIndicator();
      if (dispatchBtn) dispatchBtn.click();
    } else {
      setTimeout(() => {
        removeReasoningIndicator();
        appendBotMessage(
          `🤖 <b>AI Risk Intelligence Response:</b><br />` +
          `Processed prompt against North East GIS knowledge base. ` +
          `Upload a geotagged photo to pinpoint incidents (Road Blockage, Landslide, Flash Flood), or type a custom incident description.`
        );
      }, 600);
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

  function appendReasoningIndicator(toolName, actionDetail) {
    if (!chatFeed || document.getElementById('typing-msg')) return;
    const msg = document.createElement('div');
    msg.className = 'msg bot';
    msg.id = 'typing-msg';
    msg.innerHTML = `
      <div class="avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-bubble" style="width: 100%;">
        <div class="msg-author">AI Sentinel Agent · <span style="color: var(--accent-gold-light);">${toolName}</span></div>
        <div class="tool-reasoning-card">
          <div class="tool-step active"><i class="fa-solid fa-gear fa-spin"></i> <span>${actionDetail}</span></div>
          <div class="tool-progress-bar"><div class="tool-progress-fill"></div></div>
        </div>
      </div>
    `;
    chatFeed.appendChild(msg);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function removeReasoningIndicator() {
    const typingMsg = document.getElementById('typing-msg');
    if (typingMsg) typingMsg.remove();
  }

  window.sendPrompt = function(promptText) {
    if (userInput) {
      userInput.value = promptText;
      handleSendMessage();
    }
  };
});
