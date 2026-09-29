/**
 * CityPulse: The Live Civic Health Dashboard
 * Frontend Application Controller
 * Handles WebSocket streaming, Leaflet maps, plain-language summaries,
 * alerting, and historical replay.
 */

// Application State
let cityState = null;
let cityZones = null;
let map = null;
let zonePolygons = {};
let eventMarkersLayer = null;
let ws = null;
let activeTab = 'correlations';
let replayInterval = null;
let activeLayers = {
  weather: true,
  transit: true,
  311: true,
  aqi: true,
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initWebSocket();
  setupUIEventListeners();
  loadInitialData();
  initOfficialConsole();
  lucide.createIcons();
});

// ============================================================================
// 1. MAP INITIALIZATION & RENDERING
// ============================================================================

function initMap() {
  // Center near Metropolis Downtown
  map = L.map('city-map', {
    zoomControl: true,
    attributionControl: false,
  }).setView([40.716, -73.990], 13);

  // CartoDB Dark Matter tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd',
  }).addTo(map);

  eventMarkersLayer = L.layerGroup().addTo(map);

  document.getElementById('btn-reset-map-view').addEventListener('click', () => {
    map.setView([40.716, -73.990], 13);
  });
}

async function loadZones() {
  try {
    const res = await fetch('/api/zones');
    cityZones = await res.json();
    renderZonePolygons();
  } catch (err) {
    console.error('Failed to load zones:', err);
  }
}

function renderZonePolygons() {
  if (!map || !cityZones) return;

  for (const [zid, z] of Object.entries(cityZones)) {
    const health = cityState?.zones?.[zid]?.health_score ?? 85.0;
    const color = getHealthHexColor(health);

    if (zonePolygons[zid]) {
      zonePolygons[zid].setStyle({
        color: color,
        fillColor: color,
      });
    } else {
      const polygon = L.polygon(z.bounds, {
        color: color,
        fillColor: color,
        fillOpacity: 0.18,
        weight: 2,
        dashArray: '4, 4',
      }).addTo(map);

      polygon.bindPopup(`
        <div class="p-1">
          <div class="font-bold text-sm text-slate-100">${z.name}</div>
          <p class="text-xs text-slate-400 mt-1">${z.description}</p>
          <div class="mt-2 text-xs flex justify-between font-mono">
            <span class="text-slate-400">Health Score:</span>
            <span class="font-bold" style="color:${color}">${health.toFixed(1)}/100</span>
          </div>
        </div>
      `);

      zonePolygons[zid] = polygon;
    }
  }
}

function renderEventMarkers() {
  if (!map || !eventMarkersLayer || !cityState) return;
  eventMarkersLayer.clearLayers();

  const events = cityState.recent_events || [];
  events.forEach((e) => {
    // Check layer filter
    const ftLower = e.feed_type.toLowerCase();
    if (ftLower.includes('weather') && !activeLayers.weather) return;
    if (ftLower.includes('transit') && !activeLayers.transit) return;
    if (ftLower.includes('311') && !activeLayers['311']) return;
    if (ftLower.includes('air') && !activeLayers.aqi) return;

    if (!e.location || !e.location.lat || !e.location.lng) return;

    const color = getSeverityColor(e.severity);
    const radius = e.severity === 'CRITICAL' ? 10 : (e.severity === 'HIGH' ? 8 : 6);

    const marker = L.circleMarker([e.location.lat, e.location.lng], {
      radius: radius,
      color: color,
      fillColor: color,
      fillOpacity: 0.75,
      weight: 1.5,
    });

    marker.bindPopup(`
      <div class="p-1 text-xs">
        <div class="font-bold text-slate-100 flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" style="background:${color}"></span>
          <span>${e.feed_type}</span>
          <span class="text-[10px] text-slate-400 font-mono ml-auto">${e.severity}</span>
        </div>
        <p class="text-slate-200 mt-1 font-medium">${e.summary_headline}</p>
        <div class="mt-1 text-[11px] text-slate-400 flex justify-between">
          <span>District: ${e.zone_name}</span>
          <span>Impact: ${e.civic_impact_score}/100</span>
        </div>
      </div>
    `);

    eventMarkersLayer.addLayer(marker);
  });
}

// ============================================================================
// 2. WEBSOCKET & DATA INGESTION
// ============================================================================

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/pulse`;

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[CityPulse WebSocket] Connected to live civic stream');
    };

    ws.onmessage = (event) => {
      try {
        const state = JSON.parse(event.data);
        handleStateUpdate(state);
      } catch (err) {
        console.error('Error parsing WebSocket state payload', err);
      }
    };

    ws.onclose = () => {
      console.warn('[CityPulse WebSocket] Disconnected. Polling fallback active...');
      setTimeout(initWebSocket, 4000);
    };

    ws.onerror = () => {
      if (ws) ws.close();
    };
  } catch (err) {
    console.error('WebSocket connection error:', err);
  }

  // Backup polling fallback every 4 seconds
  setInterval(async () => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      try {
        const res = await fetch('/api/pulse');
        const state = await res.json();
        handleStateUpdate(state);
      } catch (e) {
        // ignore offline poll error
      }
    }
  }, 4000);
}

async function loadInitialData() {
  await loadZones();
  try {
    const res = await fetch('/api/pulse');
    const state = await res.json();
    handleStateUpdate(state);
  } catch (err) {
    console.error('Initial state fetch error:', err);
  }
}

// ============================================================================
// 3. STATE UPDATE & UI RENDERING
// ============================================================================

function handleStateUpdate(state) {
  cityState = state;
  updatePulseGauge();
  updatePlainLanguageSummary();
  updateDistrictChips();
  updateCorrelationsAndAnomalies();
  updateEventStream();
  renderZonePolygons();
  renderEventMarkers();
  updateAlertsBadge();
  updateReplayUI();
  lucide.createIcons();
}

function updatePulseGauge() {
  if (!cityState) return;

  const score = cityState.overall_health_score;
  const bpm = cityState.pulse_rate_bpm;
  const label = cityState.overall_status_label;

  // Header quick metrics
  document.getElementById('header-pulse-bpm').textContent = `${bpm} BPM`;
  const headerScore = document.getElementById('header-health-score');
  headerScore.textContent = `${score.toFixed(0)}/100 · ${score >= 80 ? 'Calm' : (score >= 60 ? 'Active' : 'Distressed')}`;
  
  // Hero score
  const heroScoreEl = document.getElementById('hero-health-score');
  heroScoreEl.textContent = score.toFixed(0);
  document.getElementById('hero-pulse-bpm').textContent = bpm;
  document.getElementById('hero-status-label').textContent = label;

  // Update classes and colors
  const container = document.getElementById('heartbeat-container');
  const ekgPath = document.getElementById('ekg-svg');

  container.className = 'relative flex items-center justify-center w-10 h-10 rounded-xl border ';
  if (score >= 80) {
    heroScoreEl.className = 'text-5xl font-black text-emerald-400 tracking-tight';
    headerScore.className = 'font-bold px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-300';
    container.classList.add('bg-emerald-500/10', 'border-emerald-500/30', 'text-emerald-400', 'pulse-healthy');
    ekgPath.classList.remove('ekg-fast');
  } else if (score >= 60) {
    heroScoreEl.className = 'text-5xl font-black text-amber-400 tracking-tight';
    headerScore.className = 'font-bold px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-300';
    container.classList.add('bg-amber-500/10', 'border-amber-500/30', 'text-amber-400', 'pulse-warning');
    ekgPath.classList.add('ekg-fast');
  } else {
    heroScoreEl.className = 'text-5xl font-black text-rose-500 tracking-tight';
    headerScore.className = 'font-bold px-2 py-0.5 rounded text-xs bg-rose-500/20 text-rose-300';
    container.classList.add('bg-rose-500/10', 'border-rose-500/30', 'text-rose-400', 'pulse-critical');
    ekgPath.classList.add('ekg-fast');
  }

  // Relative updated time
  document.getElementById('pulse-updated-ago').textContent = new Date().toLocaleTimeString();
}

function updateDistrictChips() {
  if (!cityState || !cityState.zones) return;
  const container = document.getElementById('district-chips-container');
  container.innerHTML = '';

  for (const [zid, z] of Object.entries(cityState.zones)) {
    const chip = document.createElement('div');
    const color = getHealthHexColor(z.health_score);
    chip.className = 'p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 cursor-pointer hover:border-slate-500 transition';
    chip.innerHTML = `
      <div class="text-[10px] font-bold text-slate-300 truncate">${z.zone_name.split(' ')[0]}</div>
      <div class="text-xs font-mono font-bold mt-0.5" style="color: ${color}">${z.health_score.toFixed(0)}</div>
    `;

    chip.addEventListener('click', () => {
      if (cityZones && cityZones[zid]) {
        map.flyTo([cityZones[zid].center.lat, cityZones[zid].center.lng], 15);
        if (zonePolygons[zid]) zonePolygons[zid].openPopup();
      }
    });

    container.appendChild(chip);
  }
}

// ============================================================================
// 4. POINT 5: PLAIN-LANGUAGE RESIDENT NARRATIVE RENDERING
// ============================================================================

function updatePlainLanguageSummary() {
  if (!cityState || !cityState.plain_language_summary) return;

  const s = cityState.plain_language_summary;

  // 10-Second Executive Headline
  const tenSecEl = document.getElementById('summary-ten-second');
  tenSecEl.textContent = s.ten_second_headline;

  // What is happening
  const happeningList = document.getElementById('summary-happening-list');
  happeningList.innerHTML = '';
  (s.what_is_happening || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = `• ${item}`;
    happeningList.appendChild(li);
  });

  // Why it matters
  const mattersList = document.getElementById('summary-matters-list');
  mattersList.innerHTML = '';
  (s.why_it_matters || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = `• ${item}`;
    mattersList.appendChild(li);
  });

  // Actionable advice
  const actionList = document.getElementById('summary-action-list');
  actionList.innerHTML = '';
  (s.actionable_advice || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = `• ${item}`;
    actionList.appendChild(li);
  });

  // Epistemic note
  if (s.epistemic_note) {
    document.getElementById('summary-epistemic-note').textContent = s.epistemic_note;
  }
  document.getElementById('summary-timestamp').textContent = `Synthesized at ${new Date(s.generated_at).toLocaleTimeString()}`;
}

// ============================================================================
// 5. CORRELATIONS & ANOMALIES RENDERING
// ============================================================================

function updateCorrelationsAndAnomalies() {
  if (!cityState) return;

  const corrContainer = document.getElementById('correlations-container');
  const anomContainer = document.getElementById('anomalies-container');
  const badge = document.getElementById('corr-count-badge');

  const correlations = cityState.active_correlations || [];
  const anomalies = cityState.active_anomalies || [];

  badge.textContent = correlations.length + anomalies.length;
  corrContainer.innerHTML = '';
  anomContainer.innerHTML = '';

  if (correlations.length === 0) {
    corrContainer.innerHTML = `
      <div class="text-center py-6 text-slate-500 text-xs">
        <i data-lucide="check-circle-2" class="w-8 h-8 mx-auto text-slate-600 mb-2"></i>
        <span>No cross-feed compound crises detected. Feeds are uncorrelated and calm.</span>
      </div>
    `;
  } else {
    correlations.forEach(c => {
      const card = document.createElement('div');
      card.className = 'glass-card rounded-xl p-3 border border-amber-500/40 bg-gradient-to-r from-amber-950/20 to-slate-900/40';
      
      const feedBadges = (c.feeds_involved || []).map(f => 
        `<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-amber-300 border border-amber-500/30">${f}</span>`
      ).join(' ');

      card.innerHTML = `
        <div class="flex items-center justify-between gap-2 mb-1.5">
          <div class="font-bold text-xs text-amber-300 flex items-center gap-1.5">
            <i data-lucide="network" class="w-4 h-4 text-amber-400"></i>
            <span>${c.title}</span>
          </div>
          <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
            ${Math.round(c.confidence_score * 100)}% Conf.
          </span>
        </div>
        <p class="text-xs text-slate-200 leading-snug mb-2">${c.hypothesis}</p>
        <p class="text-[11px] text-slate-400 leading-snug mb-2 font-light">${c.impact_rationale}</p>
        <div class="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <div class="flex gap-1">${feedBadges}</div>
          <span class="text-[9px] text-slate-500 italic max-w-[200px] truncate" title="${c.epistemic_disclaimer}">
            Epistemic: Probable link, not confirmed causation
          </span>
        </div>
      `;
      corrContainer.appendChild(card);
    });
  }

  // Anomalies
  if (anomalies.length === 0) {
    anomContainer.innerHTML = `
      <div class="text-slate-500 text-xs italic py-1">All metrics within 2.0σ rolling baseline.</div>
    `;
  } else {
    anomalies.forEach(a => {
      const item = document.createElement('div');
      item.className = 'p-2 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs flex items-start gap-2';
      item.innerHTML = `
        <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-400 shrink-0 mt-0.5"></i>
        <div class="flex-1">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-slate-200">${a.zone_name}</span>
            <span class="text-[10px] font-mono text-amber-400 font-bold">Z: +${a.z_score.toFixed(1)}σ</span>
          </div>
          <p class="text-[11px] text-slate-300 mt-0.5">${a.description}</p>
        </div>
      `;
      anomContainer.appendChild(item);
    });
  }
}

function updateEventStream() {
  if (!cityState) return;
  const container = document.getElementById('events-stream-container');
  const events = (cityState.recent_events || []).slice(-20).reverse();
  container.innerHTML = '';

  events.forEach(e => {
    const color = getSeverityColor(e.severity);
    const item = document.createElement('div');
    item.className = 'p-2 rounded-lg bg-slate-800/40 border border-slate-800 flex items-start gap-2';
    item.innerHTML = `
      <span class="w-2 h-2 rounded-full mt-1.5 shrink-0" style="background:${color}"></span>
      <div class="flex-1">
        <div class="flex items-center justify-between text-[10px] text-slate-400 mb-0.5 font-mono">
          <span class="font-semibold text-slate-300">${e.feed_type}</span>
          <span>${new Date(e.timestamp).toLocaleTimeString()}</span>
        </div>
        <p class="text-xs text-slate-200">${e.summary_headline}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

// ============================================================================
// 6. ALERTING CENTER & NOTIFICATIONS (Point 6)
// ============================================================================

function updateAlertsBadge() {
  if (!cityState) return;
  const alerts = cityState.active_alerts || [];
  const badge = document.getElementById('unread-alert-badge');
  const unreadCount = alerts.filter(a => !a.acknowledged).length;

  if (unreadCount > 0) {
    badge.textContent = unreadCount;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

async function renderAlertsModal() {
  try {
    const res = await fetch('/api/alerts');
    const data = await res.json();
    const list = document.getElementById('modal-active-alerts-list');
    list.innerHTML = '';

    const active = data.active_alerts || [];
    if (active.length === 0) {
      list.innerHTML = '<div class="text-slate-500 py-3 text-center">No active threshold alerts.</div>';
    } else {
      active.forEach(a => {
        const item = document.createElement('div');
        item.className = `p-2.5 rounded-xl border flex items-start justify-between gap-2 ${
          a.severity === 'CRITICAL' ? 'bg-rose-950/30 border-rose-500/50' : 'bg-slate-800 border-slate-700'
        }`;
        item.innerHTML = `
          <div>
            <div class="font-bold text-slate-200 flex items-center gap-1.5">
              <span class="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-900">${a.severity}</span>
              <span>${a.title}</span>
            </div>
            <p class="text-[11px] text-slate-300 mt-1">${a.message}</p>
          </div>
          <button class="btn-ack-alert text-[10px] px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 shrink-0" data-id="${a.alert_id}">
            Dismiss
          </button>
        `;
        list.appendChild(item);
      });

      // Hook dismiss
      document.querySelectorAll('.btn-ack-alert').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const aid = e.target.getAttribute('data-id');
          await fetch(`/api/alerts/clear/${aid}`, { method: 'POST' });
          renderAlertsModal();
        });
      });
    }

    // Webhook log text
    const webhookBox = document.getElementById('webhook-log-text');
    const webhookLogs = data.webhook_dispatch_log || [];
    if (webhookLogs.length > 0) {
      webhookBox.innerHTML = webhookLogs.slice(-5).map(w => 
        `[${new Date(w.dispatched_at).toLocaleTimeString()}] DISPATCH -> ${w.destination}: ${w.payload.title}`
      ).join('<br/>');
    }
  } catch (err) {
    console.error('Failed to load alerts modal data', err);
  }
}

// ============================================================================
// 7. HISTORICAL REPLAY CONTROLLER (Point 7)
// ============================================================================

async function initReplayScenarios() {
  try {
    const res = await fetch('/api/replay/scenarios');
    const scenarios = await res.json();
    const select = document.getElementById('replay-scenario-select');
    select.innerHTML = '';

    scenarios.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = `${s.title} (${s.total_steps} steps)`;
      select.appendChild(opt);
    });

    select.addEventListener('change', async (e) => {
      await fetch('/api/replay/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: e.target.value })
      });
    });
  } catch (err) {
    console.error('Failed to load scenarios', err);
  }
}

function updateReplayUI() {
  const replayBar = document.getElementById('replay-bar');
  const modeBadge = document.getElementById('mode-badge');
  const replayBtnLabel = document.getElementById('replay-btn-label');

  if (cityState && cityState.is_replay_mode) {
    replayBar.classList.remove('hidden');
    modeBadge.textContent = 'Historical Replay Mode';
    modeBadge.className = 'text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-indigo-500/20 border border-indigo-500/40 text-indigo-300';
    replayBtnLabel.textContent = 'Replay Active';

    const meta = cityState.replay_meta || {};
    document.getElementById('replay-step-label').textContent = `Step ${(meta.step_index ?? 0) + 1}/${meta.total_steps ?? 1}`;
    document.getElementById('replay-time-label').textContent = meta.frame_label || '';

    const scrubber = document.getElementById('replay-scrubber');
    scrubber.max = (meta.total_steps ?? 1) - 1;
    scrubber.value = meta.step_index ?? 0;
  } else {
    replayBar.classList.add('hidden');
    modeBadge.textContent = 'Live Telemetry';
    modeBadge.className = 'text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-emerald-500/10 border border-emerald-500/30 text-emerald-300';
    replayBtnLabel.textContent = 'Historical Replay';
  }
}

// ============================================================================
// 8. EVENT LISTENERS & MODAL CONTROLLERS
// ============================================================================

function setupUIEventListeners() {
  // Tab switching
  const tabCorr = document.getElementById('tab-btn-correlations');
  const tabStream = document.getElementById('tab-btn-stream');
  const contentCorr = document.getElementById('tab-content-correlations');
  const contentStream = document.getElementById('tab-content-stream');

  tabCorr.addEventListener('click', () => {
    tabCorr.className = 'tab-btn px-3 py-1 rounded-lg text-xs font-bold bg-slate-800 text-emerald-400 border border-slate-700';
    tabStream.className = 'tab-btn px-3 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200';
    contentCorr.classList.remove('hidden');
    contentStream.classList.add('hidden');
  });

  tabStream.addEventListener('click', () => {
    tabStream.className = 'tab-btn px-3 py-1 rounded-lg text-xs font-bold bg-slate-800 text-emerald-400 border border-slate-700';
    tabCorr.className = 'tab-btn px-3 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200';
    contentStream.classList.remove('hidden');
    contentCorr.classList.add('hidden');
  });

  // Layer Toggles
  document.querySelectorAll('.layer-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const layer = e.target.getAttribute('data-layer');
      activeLayers[layer] = !activeLayers[layer];
      if (activeLayers[layer]) {
        e.target.classList.remove('opacity-40');
      } else {
        e.target.classList.add('opacity-40');
      }
      renderEventMarkers();
    });
  });

  // Modal open buttons
  document.getElementById('btn-open-simulate').addEventListener('click', () => {
    openModal('modal-simulate');
  });

  document.getElementById('btn-open-feeds').addEventListener('click', () => {
    renderFeedsModal();
    openModal('modal-feeds');
  });

  document.getElementById('btn-open-alerts').addEventListener('click', () => {
    renderAlertsModal();
    openModal('modal-alerts');
  });

  // Close modals
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const mid = btn.getAttribute('data-modal');
      closeModal(mid);
    });
  });

  // Replay toggle button
  document.getElementById('btn-toggle-replay').addEventListener('click', async () => {
    if (cityState && cityState.is_replay_mode) {
      await fetch('/api/replay/exit', { method: 'POST' });
    } else {
      await initReplayScenarios();
      await fetch('/api/replay/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: 'flash_flood' })
      });
    }
  });

  document.getElementById('btn-exit-replay').addEventListener('click', async () => {
    await fetch('/api/replay/exit', { method: 'POST' });
  });

  // Replay Step buttons
  document.getElementById('btn-replay-prev').addEventListener('click', async () => {
    await fetch('/api/replay/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'back' })
    });
  });

  document.getElementById('btn-replay-next').addEventListener('click', async () => {
    await fetch('/api/replay/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'forward' })
    });
  });

  document.getElementById('replay-scrubber').addEventListener('input', async (e) => {
    await fetch('/api/replay/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'seek', step_index: parseInt(e.target.value) })
    });
  });

  // Replay auto play
  document.getElementById('btn-replay-play').addEventListener('click', (e) => {
    if (replayInterval) {
      clearInterval(replayInterval);
      replayInterval = null;
      e.currentTarget.innerHTML = '<i data-lucide="play" class="w-4 h-4"></i><span>Play</span>';
    } else {
      e.currentTarget.innerHTML = '<i data-lucide="pause" class="w-4 h-4"></i><span>Pause</span>';
      replayInterval = setInterval(async () => {
        await fetch('/api/replay/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'forward' })
        });
      }, 3000);
    }
    lucide.createIcons();
  });

  // Incident injections
  document.querySelectorAll('.btn-inject-scenario').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const type = btn.getAttribute('data-type');
      const zid = document.getElementById('sim-target-zone').value;
      closeModal('modal-simulate');
      showToast(`Injecting ${type} in ${zid}...`, 'info');
      await fetch('/api/inject/incident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone_id: zid, scenario_type: type })
      });
    });
  });

  document.getElementById('btn-reset-city').addEventListener('click', async () => {
    closeModal('modal-simulate');
    showToast('Resetting city feeds to calm baseline...', 'success');
    await fetch('/api/reset', { method: 'POST' });
  });

  // Threshold sliders
  const sHealth = document.getElementById('slider-thresh-health');
  sHealth.addEventListener('input', async (e) => {
    document.getElementById('label-thresh-health').textContent = `< ${e.target.value}`;
    await fetch('/api/alerts/rules/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_id: 'rule_health_drop', new_threshold: parseFloat(e.target.value) })
    });
  });

  const sAqi = document.getElementById('slider-thresh-aqi');
  sAqi.addEventListener('input', async (e) => {
    document.getElementById('label-thresh-aqi').textContent = `> ${e.target.value} AQI`;
    await fetch('/api/alerts/rules/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_id: 'rule_aqi_spike', new_threshold: parseFloat(e.target.value) })
    });
  });
}

function renderFeedsModal() {
  if (!cityState || !cityState.feeds_health) return;
  const container = document.getElementById('feed-toggles-list');
  container.innerHTML = '';

  for (const [ft, fh] of Object.entries(cityState.feeds_health)) {
    const isLive = fh.status === 'LIVE';
    const item = document.createElement('div');
    item.className = 'p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between';
    item.innerHTML = `
      <div>
        <div class="font-bold text-slate-200 flex items-center gap-2">
          <span>${ft}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
            isLive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
          }">${fh.status}</span>
        </div>
        <div class="text-[11px] text-slate-400 mt-1">
          Latency: ${fh.latency_ms}ms · Last Hour: ${fh.event_count_last_hour} items
        </div>
      </div>
      <div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" class="sr-only peer feed-checkbox" data-feed="${ft}" ${isLive ? 'checked' : ''} />
          <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
        </label>
      </div>
    `;
    container.appendChild(item);
  }

  // Hook toggle
  document.querySelectorAll('.feed-checkbox').forEach(cb => {
    cb.addEventListener('change', async (e) => {
      const ft = e.target.getAttribute('data-feed');
      const enabled = e.target.checked;
      await fetch('/api/feeds/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feed_type: ft, enabled: enabled })
      });
      showToast(`${ft} feed turned ${enabled ? 'ON' : 'OFF (Graceful Degradation test)'}`, 'info');
    });
  });
}

function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
  lucide.createIcons();
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  const color = type === 'success' ? 'border-emerald-500 text-emerald-300' : 'border-sky-500 text-sky-300';
  toast.className = `toast-item px-4 py-2.5 rounded-xl bg-slate-900 border ${color} shadow-2xl text-xs font-semibold flex items-center gap-2`;
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}

// Helpers
function getHealthHexColor(score) {
  if (score >= 80) return '#10b981'; // Emerald
  if (score >= 65) return '#14b8a6'; // Teal
  if (score >= 50) return '#f59e0b'; // Amber
  if (score >= 35) return '#f97316'; // Orange
  return '#ef4444'; // Rose
}

function getSeverityColor(sev) {
  switch (sev) {
    case 'CRITICAL': return '#ef4444';
    case 'HIGH': return '#f97316';
    case 'MODERATE': return '#f59e0b';
    case 'LOW': return '#38bdf8';
    default: return '#10b981';
  }
}

// ============================================================================
// 9. CITYPULSE OFFICIAL CONSOLE CONTROLLER (Left Sideways Column)
// ============================================================================

var $ = function(i) { return document.getElementById(i); };

var D = [
  ["2026-09-24", "09:12", "Pothole", "Tonk Road", "Jaipur", "Open", 0],
  ["2026-09-24", "10:40", "Water outage", "Jhotwara", "Jaipur", "Open", 1],
  ["2026-09-23", "14:05", "Streetlight", "Malviya Nagar", "Jaipur", "Solved", 0],
  ["2026-09-23", "18:22", "Garbage", "C-Scheme", "Jaipur", "Solved", 0],
  ["2026-09-22", "08:50", "Traffic signal", "Sindhi Camp", "Jaipur", "Open", 0],
  ["2026-09-25", "07:30", "Pothole", "Tonk Road", "Jaipur", "Open", 0],
  ["2026-09-25", "08:15", "Noise", "Raja Park", "Jaipur", "Solved", 0],
  ["2026-09-24", "20:01", "Pothole", "Tonk Road", "Jaipur", "Open", 0],
  ["2026-09-21", "11:11", "Water outage", "Sardarpura", "Jodhpur", "Solved", 0],
  ["2026-09-22", "16:47", "Pothole", "Ratanada", "Jodhpur", "Open", 0],
  ["2026-09-23", "09:03", "Garbage", "Paota", "Jodhpur", "Open", 0],
  ["2026-09-25", "06:40", "Streetlight", "Sardarpura", "Jodhpur", "Solved", 0]
];

function login() {
  var u = $("u") ? $("u").value.trim() : "";
  var p = $("p") ? $("p").value : "";
  if (u == "official@jaipur.gov.in" && p == "admin123") {
    $("login").classList.add("hide");
    $("app").classList.remove("hide");
    setCity();
    render();
    beepReady();
    setTimeout(incoming, 4000);
  } else {
    if ($("err")) $("err").textContent = "Wrong ID or password. Use the demo login below.";
  }
}

function logout() {
  if ($("app")) $("app").classList.add("hide");
  if ($("login")) $("login").classList.remove("hide");
}

function initOfficialConsole() {
  document.querySelectorAll("#tabs button").forEach(function(b) {
    b.onclick = function() {
      document.querySelectorAll("#tabs button").forEach(function(x) {
        x.classList.toggle("on", x == b);
      });
      ["mp", "inc", "an"].forEach(function(t) {
        var el = $(t);
        if (el) el.classList.toggle("hide", t != b.dataset.t);
      });
    };
  });

  setCity();
  render();
  beepReady();
  setTimeout(incoming, 6000);
}

function setCity() {
  var c = $("city") ? $("city").value : "Jaipur";
  var mapEl = $("mapf");
  if (mapEl) {
    mapEl.src = "https://www.google.com/maps?q=" + encodeURIComponent(c + ", India") + "&t=k&z=13&output=embed";
  }
}

function esc(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function render() {
  var tb = $("tb");
  if (tb) {
    tb.innerHTML = D.slice().reverse().map(function(r) {
      return "<tr><td class='py-1.5 px-2 font-mono text-slate-400'>" + r[0] + "</td><td class='py-1.5 px-2 font-mono text-slate-400'>" + r[1] + "</td><td class='py-1.5 px-2 font-semibold text-slate-200'>" + esc(r[2]) + "</td><td class='py-1.5 px-2 text-slate-300'>" + esc(r[3]) + "</td><td class='py-1.5 px-2 text-slate-400'>" + r[4] + "</td><td class='py-1.5 px-2'><span class='tag " + (r[6] ? "e" : r[5] == "Solved" ? "d" : "o") + "'>" + (r[6] ? "Urgent" : r[5]) + "</span></td></tr>";
    }).join("");
  }

  var incCount = $("inc-count");
  if (incCount) incCount.textContent = D.length;

  var res = D.filter(function(r) { return r[5] == "Solved"; }).length;
  var urg = D.filter(function(r) { return r[6] && r[5] != "Solved"; }).length;

  if ($("tot")) $("tot").textContent = D.length;
  if ($("res")) $("res").textContent = res;
  if ($("opn")) $("opn").textContent = D.length - res;
  if ($("urg")) $("urg").textContent = urg;

  var by = {};
  D.forEach(function(r) { by[r[3]] = (by[r[3]] || 0) + 1; });
  var max = 0;
  Object.keys(by).forEach(function(k) { if (by[k] > max) max = by[k]; });
  var rows = Object.keys(by).sort(function(a, b) { return by[b] - by[a]; });

  var areasEl = $("areas");
  if (areasEl) {
    areasEl.innerHTML = rows.map(function(k) {
      var pct = Math.round(by[k] / max * 100);
      return "<div class='hot-item text-xs'><span>" + (by[k] == max ? "🔥 " : "") + esc(k) + "</span><span style='display:flex;align-items:center;gap:8px;min-width:110px;justify-content:flex-end'><span class='prog-bar'><i style='width:" + pct + "%'></i></span><b class='text-slate-300'>" + by[k] + "</b></span></div>";
    }).join("");
  }

  var insightsEl = $("insights");
  if (insightsEl) {
    var list = insights();
    insightsEl.innerHTML = list.map(function(s) {
      return "<div class='hot-item text-xs text-slate-300 leading-snug'><span>" + s + "</span></div>";
    }).join("") || "<p class='mut-text text-xs'>No unusual pattern in current data.</p>";
  }
}

function insights() {
  var byAC = {}, byA = {}, total = D.length, out = [];
  D.forEach(function(r) {
    var a = r[3], c = r[2];
    byA[a] = (byA[a] || 0) + 1;
    byAC[a] = byAC[a] || {};
    byAC[a][c] = (byAC[a][c] || 0) + 1;
  });

  Object.keys(byAC).forEach(function(a) {
    Object.keys(byAC[a]).forEach(function(c) {
      var share = byAC[a][c] / byA[a];
      if (byAC[a][c] >= 2 && share >= 0.5) {
        out.push(esc(a) + " is showing a repeat pattern of <b class='text-amber-300'>" + esc(c).toLowerCase() + "</b> complaints (" + byAC[a][c] + " of " + byA[a] + ") — worth a targeted inspection.");
      }
    });
  });

  if (byA["Tonk Road"] >= 3) {
    out.push("Tonk Road has logged complaints on 3+ separate days — a possible sign of an unresolved underlying road issue rather than isolated incidents.");
  }
  var urgShare = D.filter(function(r) { return r[6]; }).length / total;
  if (urgShare > 0.1) {
    out.push("Urgent complaints are " + Math.round(urgShare * 100) + "% of total volume, above the typical range — flag for review.");
  }
  return out;
}

var ctx;
function beepReady() {
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
  } catch (e) {}
}

function beep() {
  if (!ctx) return;
  try {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.connect(g);
    g.connect(ctx.destination);
    o.frequency.value = 880;
    g.gain.value = 0.15;
    o.start();
    setTimeout(function() { o.stop(); }, 220);
  } catch (e) {}
}

function toast(msg) {
  var t = document.createElement("div");
  t.id = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { if (t) t.remove(); }, 5000);
}

function incoming() {
  var now = new Date(), areas = ["Vaishali Nagar", "Mansarovar", "Tonk Road"], a = areas[Math.floor(Math.random() * 3)];
  D.push([now.toISOString().slice(0, 10), now.toTimeString().slice(0, 5), "Emergency", "Emergency · " + a, $("city") ? $("city").value : "Jaipur", "Open", 1]);
  beep();
  toast("🚨 Urgent complaint received — " + a);
  render();
}
