/* ─────────────────────────────────────────────────
   DocuMind Web — app.js
   ───────────────────────────────────────────────── */
'use strict';

// ── State ────────────────────────────────────────
let currentResult = null;
let history       = JSON.parse(localStorage.getItem('dm_history') || '[]');
let docCount      = parseInt(localStorage.getItem('dm_doc_count') || '0');
let activeView    = 'dashboard';
let activePanelTab = 'dual';

const ENTITY_TYPE_COLORS = {
  PERSON:'#7c3aed', ORG:'#2563eb', DATE:'#0891b2', GPE:'#0d9488',
  MONEY:'#16a34a', CARDINAL:'#9f1239', PERCENT:'#c2410c', TIME:'#7e22ce',
  EMAIL:'#1d4ed8', PHONE:'#be185d', INVOICE_NUMBER:'#b45309',
  'Invoice Number':'#b45309','Invoice Date':'#0369a1','Total Amount':'#15803d',
  GSTIN:'#6d28d9', PAN:'#be123c', URL:'#0f766e',
};

const ENTITY_TYPE_LABELS = Object.keys(ENTITY_TYPE_COLORS);

// ── View routing ─────────────────────────────────
function showView(view) {
  activeView = view;
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const map = {
    dashboard:  {el:'viewDashboard',  nav:'navDashboard'},
    results:    {el:'viewResults',    nav:'navDashboard'},
    history:    {el:'viewHistory',    nav:'navHistory'},
    automation: {el:'viewAutomation', nav:'navAutomation'},
  };
  const m = map[view] || map.dashboard;
  const el = document.getElementById(m.el);
  if (el) el.style.display = '';
  const nav = document.getElementById(m.nav);
  if (nav) nav.classList.add('active');

  // Topbar
  const titleMap = {
    dashboard:'Document Results', results:'Document Results',
    history:'Analysis History', automation:'Automation'
  };
  document.getElementById('topbarTitle').textContent = titleMap[view] || 'DocuMind';

  const tabs     = document.getElementById('topbarTabs');
  const search   = document.getElementById('topbarSearch');
  const resetBtn = document.getElementById('btnReset');
  const fab      = document.getElementById('fab');

  if (view === 'results') {
    tabs.style.display = '';
    search.style.display = 'none';
    resetBtn.style.display = '';
    fab.style.display = '';
  } else {
    tabs.style.display = 'none';
    search.style.display = '';
    resetBtn.style.display = 'none';
    fab.style.display = 'none';
  }

  if (view === 'history') renderHistory();
  if (view === 'automation') renderAutomation();
}

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
  // Tab in results maps to panel tab
  switchPanelTab(tab === 'overview' ? 'dual' : tab === 'structure' ? 'structure' : 'json');
}

function switchPanelTab(tab) {
  activePanelTab = tab;
  ['Dual','Entities','Structure','Json','Analytics','Preview'].forEach(t => {
    const btn = document.getElementById('pt'+t);
    if (btn) btn.classList.remove('active');
    const panel = document.getElementById('panel'+t);
    if (panel) panel.style.display = 'none';
  });
  const capTab = tab.charAt(0).toUpperCase() + tab.slice(1);
  const actBtn = document.getElementById('pt'+capTab);
  if (actBtn) actBtn.classList.add('active');
  const actPanel = document.getElementById('panel'+capTab);
  if (actPanel) actPanel.style.display = '';
}

function setViewMode(mode) {
  const grid     = document.getElementById('dualGrid');
  const colRaw   = document.getElementById('colRaw');
  const colClean = document.getElementById('colCleaned');
  if (!grid || !colRaw || !colClean) return;

  if (mode === 'sidebyside') {
    grid.style.gridTemplateColumns = '1fr 1fr';
    colRaw.style.display   = '';
    colClean.style.display = '';
  } else if (mode === 'raw') {
    grid.style.gridTemplateColumns = '1fr';
    colRaw.style.display   = '';
    colClean.style.display = 'none';
  } else if (mode === 'cleaned') {
    grid.style.gridTemplateColumns = '1fr';
    colRaw.style.display   = 'none';
    colClean.style.display = '';
  }
}

// ── Upload / file handling ────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.add('drag-over');
}
function handleDragLeave(e) {
  document.getElementById('uploadZone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) processFile(file);
}

async function processFile(file) {
  if (file.size > 10 * 1024 * 1024) {
    showToast('File exceeds 10 MB limit.', 'error');
    return;
  }

  try {
    document.getElementById('previewImage').src = URL.createObjectURL(file);
  } catch (e) {}

  showProcessing(true);
  animateSteps();

  const fd = new FormData();
  fd.append('file', file);

  try {
    const res  = await fetch('/api/analyze', {method:'POST', body:fd});
    const data = await res.json();
    showProcessing(false);
    if (!res.ok || data.error) {
      showToast(data.error || 'Analysis failed.', 'error');
      return;
    }
    currentResult = data;
    renderResults(data);
    saveToHistory(data, file.name);
    showView('results');
  } catch(err) {
    showProcessing(false);
    showToast('Network error: ' + err.message, 'error');
  }
}

async function loadSample(name) {
  showProcessing(true);
  animateSteps();
  try {
    const listRes  = await fetch('/api/samples');
    const samples  = await listRes.json();
    const match    = samples.find(s => s.name === name || s.filename.startsWith(name));
    if (!match) { showProcessing(false); showToast('Sample not found.','error'); return; }
    const blob  = await fetch('/api/samples/' + match.filename).then(r => r.blob());
    const file  = new File([blob], match.filename, {type: blob.type});
    showProcessing(false);
    processFile(file);
  } catch(e) {
    showProcessing(false);
    showToast('Could not load sample: ' + e.message, 'error');
  }
}

// ── Processing UI ─────────────────────────────────
let _stepTimer = null;
function showProcessing(show) {
  document.getElementById('processingOverlay').style.display = show ? '' : 'none';
  if (!show && _stepTimer) { clearInterval(_stepTimer); _stepTimer = null; }
}
function animateSteps() {
  let s = 1;
  ['step1','step2','step3'].forEach(id => document.getElementById(id).classList.remove('active'));
  document.getElementById('step1').classList.add('active');
  _stepTimer = setInterval(() => {
    s++;
    if (s > 3) { clearInterval(_stepTimer); return; }
    document.getElementById('step'+(s-1)).classList.remove('active');
    document.getElementById('step'+s).classList.add('active');
  }, 900);
}

// ── Results rendering ─────────────────────────────
function renderResults(data) {
  // Metrics
  set('rEntities', data.entity_count);
  set('rOcrAcc',   data.ocr_confidence + '%');
  set('rSpeed',    (data.total_time_ms/1000).toFixed(1) + 's');
  set('rConf',     data.avg_confidence);
  set('filenameTag', data.filename || '—');
  set('auditId',   'DM-' + Math.floor(Math.random()*9000+1000) + '-X');
  set('modelUsed', data.model_used || '—');

  // Update dashboard metrics too
  docCount++;
  localStorage.setItem('dm_doc_count', docCount);
  set('mTotalDocs', docCount);
  set('mExtrRate',  data.ocr_confidence + '%');
  set('mVerified',  data.entity_count);

  renderRawPanel(data);
  renderVerifiedPanel(data);
  renderEntitiesView(data);
  renderStructureView(data);
  renderJsonView(data);
  renderAnalyticsView(data);
}

function renderAnalyticsView(data) {
  const m = data.metrics || {};
  const metricsHtml = `
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;box-shadow: 1px 1px 0 0 #e2e1de;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">PRECISION (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.precision_proxy || '0'}%</p>
    </div>
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;box-shadow: 1px 1px 0 0 #e2e1de;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">RECALL (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.recall_proxy || '0'}%</p>
    </div>
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;box-shadow: 1px 1px 0 0 #e2e1de;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">F1 SCORE (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.f1_proxy || '0'}%</p>
    </div>
  `;
  document.getElementById('analyticsMetrics').innerHTML = metricsHtml;

  const t = data.timings || {};
  let timelineHtml = '<div style="display:flex;gap:4px;height:16px;border-radius:4px;overflow:hidden;">';
  let total = Object.values(t).reduce((a,b)=>a+b, 0) || 1;
  const colors = {preprocess_ms:'#f59e0b',ocr_ms:'#3b82f6',clean_ms:'#10b981',nlp_pre_ms:'#84cc16',extraction_ms:'#8b5cf6'};
  const labels = {preprocess_ms:'Preprocess',ocr_ms:'OCR',clean_ms:'Cleaning',nlp_pre_ms:'NLP',extraction_ms:'Extraction'};
  
  for (const [k,v] of Object.entries(t)) {
    if (v > 0 && colors[k]) {
      timelineHtml += `<div style="flex:${v/total};background:${colors[k]};" title="${labels[k]||k}: ${v}ms"></div>`;
    }
  }
  timelineHtml += '</div><div style="margin-top:24px;display:flex;flex-direction:column;gap:12px;font-size:14px;color:#271813;">';
  for (const [k,v] of Object.entries(t)) {
    if(v > 0 && labels[k]) {
      timelineHtml += `<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(228,190,180,0.3);padding-bottom:8px;">
        <span style="font-weight:500;">${labels[k]}</span><b style="color:#ab2f00;">${v} ms</b>
      </div>`;
    }
  }
  timelineHtml += '</div>';
  document.getElementById('analyticsTimeline').innerHTML = timelineHtml;
}

function renderRawPanel(data) {
  const lines = (data.raw_text || '').split('\n').filter(l => l.trim());
  const el = document.getElementById('rawTextContent');
  el.innerHTML = lines.map(l =>
    `<p class="raw-line">${escHtml(l)}</p>`
  ).join('');
}

function renderVerifiedPanel(data) {
  const el = document.getElementById('verifiedBody');
  const ents = data.entities || [];

  // doc type
  let html = `
    <div class="group-field">
      <label class="v-field-label">Document Type</label>
      <div class="v-field-box">
        <span>${escHtml(titleCase(data.doc_type || 'General'))}</span>
        <span class="material-symbols-outlined">edit</span>
      </div>
    </div>`;

  // Key entities as labeled fields
  const seen = new Set();
  const priority = ['INVOICE_NUMBER','Invoice Number','DATE','Invoice Date','PERSON','ORG','MONEY','Total Amount'];
  const shown = [];
  for (const type of priority) {
    const e = ents.find(x => x.type === type && !seen.has(x.value));
    if (e) { seen.add(e.value); shown.push(e); }
  }
  // Grid for first two shown
  if (shown.length >= 2) {
    html += `<div class="v-grid-2">`;
    for (let i = 0; i < Math.min(2, shown.length); i++) {
      html += `<div>
        <label class="v-field-label">${escHtml(shown[i].type)}</label>
        <div class="v-field-box">${escHtml(shown[i].value)}</div>
      </div>`;
    }
    html += `</div>`;
  }

  // Person/Org entity block
  const org = ents.find(e => e.type === 'ORG');
  const person = ents.find(e => e.type === 'PERSON');
  const mainEnt = org || person;
  if (mainEnt) {
    html += `<div>
      <label class="v-field-label">Entity: ${escHtml(mainEnt.type)}</label>
      <div class="v-entity-box">
        <p class="v-entity-name">${escHtml(mainEnt.value)}</p>
        ${ents.filter(e => e.type === 'GPE' || e.type === 'FAC').slice(0,2).map(e =>
          `<p class="v-entity-detail">${escHtml(e.value)}</p>`
        ).join('')}
      </div>
    </div>`;
  }

  // Line items table (money entities)
  const money = ents.filter(e => e.type === 'MONEY' || e.type === 'Total Amount');
  if (money.length) {
    html += `<div>
      <label class="v-field-label">Extracted Line Items</label>
      <table class="v-table">
        <thead><tr><th>Description</th><th>Amount</th></tr></thead>
        <tbody>
          ${money.slice(0, -1).map((e,i) =>
            `<tr><td>Item ${i+1}</td><td>${escHtml(e.value)}</td></tr>`
          ).join('')}
          <tr><td>Total Verified</td><td>${escHtml(money[money.length-1].value)}</td></tr>
        </tbody>
      </table>
    </div>`;
  }

  // Actions
  html += `<div class="v-actions">
    <button class="btn-approve" onclick="downloadJSON()">Approve & Export</button>
    <button class="btn-more"><span class="material-symbols-outlined">more_horiz</span></button>
  </div>`;

  el.innerHTML = html;
}

function renderEntitiesView(data) {
  const el = document.getElementById('entitiesView');
  const ents = data.entities || [];
  if (!ents.length) {
    el.innerHTML = '<p class="empty-state">No entities detected.</p>';
    return;
  }

  // Group by type
  const groups = {};
  ents.forEach(e => {
    if (!groups[e.type]) groups[e.type] = [];
    groups[e.type].push(e);
  });

  let html = `<div style="padding:24px;">
    <h3 class="panel-section-label" style="margin-bottom:20px;">DETECTED ENTITIES <span style="font-weight:400;font-size:11px;color:#9b7f78;margin-left:8px;">${ents.length} total</span></h3>
    <div style="display:flex;flex-direction:column;gap:16px;">`;

  for (const [type, items] of Object.entries(groups)) {
    const color = ENTITY_TYPE_COLORS[type] || '#6b7280';
    html += `
      <div style="background:#fff;border:1px solid rgba(228,190,180,0.5);border-radius:6px;padding:16px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <span style="background:${color}18;color:${color};font-size:11px;font-weight:700;letter-spacing:0.08em;padding:4px 10px;border-radius:4px;border:1px solid ${color}33;">${escHtml(type)}</span>
          <span style="font-size:11px;color:#9b7f78;font-weight:600;">${items.length} found</span>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          ${items.map(e => {
            const confColor = e.confidence === 'high' ? '#15803d' : e.confidence === 'medium' ? '#b45309' : '#be185d';
            return `<div style="display:flex;align-items:center;gap:8px;background:#f8f7f4;border:1px solid rgba(228,190,180,0.4);border-radius:4px;padding:6px 12px;">
              <span style="font-size:13px;font-weight:500;color:#271813;">${escHtml(e.value)}</span>
              <span style="font-size:10px;font-weight:700;color:${confColor};letter-spacing:0.05em;">${(e.confidence||'').toUpperCase()}</span>
            </div>`;
          }).join('')}
        </div>
      </div>`;
  }

  html += `</div></div>`;
  el.innerHTML = html;
}

function renderStructureView(data) {
  const el = document.getElementById('structureView');
  const ents = data.entities || [];
  if (!ents.length) {
    el.innerHTML = '<p class="empty-state">No entities detected.</p>';
    return;
  }
  el.innerHTML = ents.map(e => {
    const color = ENTITY_TYPE_COLORS[e.type] || '#6b7280';
    const confClass = e.confidence === 'high' ? 'conf-high' : e.confidence === 'medium' ? 'conf-medium' : 'conf-low';
    return `<div class="struct-entity">
      <div style="display:flex;align-items:center;gap:16px;">
        <span class="struct-type" style="background:${color}18;color:${color};">${escHtml(e.type)}</span>
        <span class="struct-value">${escHtml(e.value)}</span>
      </div>
      <span class="struct-conf ${confClass}">${(e.confidence||'').toUpperCase()}</span>
    </div>`;
  }).join('');
}

function renderJsonView(data) {
  const payload = {
    entities: data.entities,
    doc_type: data.doc_type,
    ocr_confidence: data.ocr_confidence,
    processing_timings_ms: data.timings,
    metrics: data.metrics,
  };
  document.getElementById('jsonPre').textContent = JSON.stringify(payload, null, 2);
}

// ── History ───────────────────────────────────────
function saveToHistory(data, filename) {
  history.unshift({
    filename: filename || data.filename,
    doc_type: data.doc_type,
    entity_count: data.entity_count,
    ocr_confidence: data.ocr_confidence,
    ts: new Date().toISOString(),
    data: data,
  });
  history = history.slice(0, 20);
  localStorage.setItem('dm_history', JSON.stringify(history));
}

function renderHistory() {
  const el = document.getElementById('historyList');
  if (!history.length) {
    el.innerHTML = '<p class="empty-state">No analyses yet. Upload a document to begin.</p>';
    return;
  }
  el.innerHTML = history.map((h,i) => `
    <div class="history-item" onclick="replayHistory(${i})">
      <div>
        <p class="h-name">${escHtml(h.filename)}</p>
        <p class="h-meta">${titleCase(h.doc_type)} · ${h.entity_count} entities · ${new Date(h.ts).toLocaleString()}</p>
      </div>
      <span class="h-badge">${h.ocr_confidence}%</span>
    </div>`
  ).join('');
}

function replayHistory(idx) {
  const h = history[idx];
  if (!h) return;
  currentResult = h.data;
  renderResults(h.data);
  showView('results');
}

// ── Automation view ───────────────────────────────
function renderAutomation() {
  const grid = document.getElementById('entityFilterGrid');
  if (!grid) return;
  grid.innerHTML = ENTITY_TYPE_LABELS.map(t =>
    `<span class="entity-chip selected" onclick="toggleChip(this,'${t}')">${t}</span>`
  ).join('');
  const rangeEl = document.getElementById('settingsConf');
  if (rangeEl) rangeEl.oninput = function(){ set('settingsConfVal', this.value + '%'); };
}

function toggleChip(el, type) {
  el.classList.toggle('selected');
}

// ── Reset ─────────────────────────────────────────
function resetToUpload() {
  currentResult = null;
  document.getElementById('fileInput').value = '';
  showView('dashboard');
}

// ── Download JSON ─────────────────────────────────
function downloadJSON() {
  if (!currentResult) return;
  const payload = {
    entities: currentResult.entities,
    doc_type: currentResult.doc_type,
    ocr_confidence: currentResult.ocr_confidence,
    timings: currentResult.timings,
    metrics: currentResult.metrics,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'documind_extraction.json';
  a.click();
}

// ── Toast ─────────────────────────────────────────
let _toastTimer = null;
function showToast(msg, type='error') {
  const el = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  el.className = 'toast' + (type === 'success' ? ' success' : '');
  el.style.display = '';
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(hideToast, 5000);
}
function hideToast() {
  document.getElementById('toast').style.display = 'none';
}

// ── Utility ───────────────────────────────────────
function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function titleCase(s) {
  return String(s||'').replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ── Init ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  showView('dashboard');
  set('mTotalDocs', docCount);
  // wire tab buttons on results topbar
  document.getElementById('tabOverview').onclick = () => { switchTab('overview'); };
  document.getElementById('tabStructure').onclick = () => { switchTab('structure'); };
  document.getElementById('tabJson').onclick = () => { switchTab('json'); };
});
