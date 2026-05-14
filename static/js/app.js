/* DocuMind Web — app.js */
'use strict';

let currentResult  = null;
let history        = JSON.parse(localStorage.getItem('dm_history') || '[]');
let docCount       = parseInt(localStorage.getItem('dm_doc_count') || '0');
let activeView     = 'dashboard';
let activePanelTab = 'entities';
let activeTemplate = null;
let isSampleResult = false;

// ── Settings state ──────────────────────────────
let activeFilters = new Set(Object.keys({
  PERSON:1,ORG:1,DATE:1,GPE:1,MONEY:1,CARDINAL:1,PERCENT:1,TIME:1,
  EMAIL:1,PHONE:1,INVOICE_NUMBER:1,'Invoice Number':1,'Invoice Date':1,
  'Total Amount':1,GSTIN:1,PAN:1,URL:1
}));
let currentOcrMode = 'standard';
let currentPsm     = 6;

const PSM_HINTS = {
  0: 'PSM 0 — use for detecting page orientation only',
  1: 'PSM 1 — automatic detection with OSD; experimental',
  3: 'PSM 3 — fully automatic; good default for mixed layouts',
  4: 'PSM 4 — best for documents with a single text column',
  6: 'PSM 6 — best for clean, multi-paragraph documents',
  7: 'PSM 7 — use for single-line images (e.g. stamps, labels)',
  8: 'PSM 8 — use for images of a single word',
  11:'PSM 11 — best for receipts and sparse/scattered text',
  13:'PSM 13 — raw line mode, treats image as one text line',
};

const ENTITY_TYPE_COLORS = {
  PERSON:'#7c3aed', ORG:'#2563eb', DATE:'#0891b2', GPE:'#0d9488',
  MONEY:'#16a34a', CARDINAL:'#9f1239', PERCENT:'#c2410c', TIME:'#7e22ce',
  EMAIL:'#1d4ed8', PHONE:'#be185d', INVOICE_NUMBER:'#b45309',
  'Invoice Number':'#b45309','Invoice Date':'#0369a1','Total Amount':'#15803d',
  GSTIN:'#6d28d9', PAN:'#be123c', URL:'#0f766e',
};
const ENTITY_TYPE_LABELS = Object.keys(ENTITY_TYPE_COLORS);

// ── View routing ──────────────────────────────────
function showView(view) {
  activeView = view;
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  document.querySelectorAll('.nav-item,.mob-nav-item').forEach(n => n.classList.remove('active'));

  const map = {
    dashboard: {el:'viewDashboard', nav:'navDashboard', mnav:'mnavDashboard'},
    results:   {el:'viewResults',   nav:'navDashboard', mnav:'mnavResults'},
    history:   {el:'viewHistory',   nav:'navHistory',   mnav:'mnavHistory'},
  };
  const m = map[view] || map.dashboard;
  const el = document.getElementById(m.el);
  if (el) el.style.display = '';
  const nav = document.getElementById(m.nav);
  if (nav) nav.classList.add('active');
  const mnav = document.getElementById(m.mnav);
  if (mnav) mnav.classList.add('active');

  const titleMap = {dashboard:'DocuMind', results:'Document Results', history:'Analysis History'};
  document.getElementById('topbarTitle').textContent = titleMap[view] || 'DocuMind';

  const tabs   = document.getElementById('topbarTabs');
  const search = document.getElementById('topbarSearch');
  const fab    = document.getElementById('fab');

  if (view === 'results') {
    tabs.style.display = '';
    search.style.display = 'none';
    fab.style.display = '';
    const mr = document.getElementById('mnavResults');
    if (mr) mr.style.display = '';
  } else {
    tabs.style.display = 'none';
    search.style.display = '';
    fab.style.display = 'none';
  }

  if (view === 'history') renderHistory();
}

function switchPanelTab(tab) {
  activePanelTab = tab;
  ['Dual','Entities','Structure','Json','Analytics','Preview'].forEach(t => {
    const btn   = document.getElementById('pt'+t);
    const panel = document.getElementById('panel'+t);
    if (btn)   btn.classList.remove('active');
    if (panel) panel.style.display = 'none';
  });
  const cap = tab.charAt(0).toUpperCase() + tab.slice(1);
  const actBtn = document.getElementById('pt'+cap);
  if (actBtn) actBtn.classList.add('active');
  const actPanel = document.getElementById('panel'+cap);
  if (actPanel) actPanel.style.display = '';
  // Re-render filtered views when switching tabs
  if (currentResult) {
    if (tab === 'entities') renderEntitiesView(currentResult);
    if (tab === 'json')     renderJsonView(currentResult);
  }
}

function setViewMode(mode) {
  const grid     = document.getElementById('dualGrid');
  const colRaw   = document.getElementById('colRaw');
  const colClean = document.getElementById('colCleaned');
  if (!grid || !colRaw || !colClean) return;
  if (mode === 'sidebyside') {
    grid.style.gridTemplateColumns = '1fr 1fr';
    colRaw.style.display = ''; colClean.style.display = '';
  } else if (mode === 'raw') {
    grid.style.gridTemplateColumns = '1fr';
    colRaw.style.display = ''; colClean.style.display = 'none';
  } else if (mode === 'cleaned') {
    grid.style.gridTemplateColumns = '1fr';
    colRaw.style.display = 'none'; colClean.style.display = '';
  }
}

// ── Settings Panel helpers ────────────────────────
function toggleSettingsPanel() {
  const body    = document.getElementById('settingsPanelBody');
  const chevron = document.getElementById('settingsPanelChevron');
  if (!body) return;
  const open = body.style.display !== 'none';
  body.style.display   = open ? 'none' : '';
  if (chevron) chevron.textContent = open ? 'expand_more' : 'expand_less';
}

function syncOcrMode(val) { currentOcrMode = val; }

function updatePsmHint() {
  const sel = document.getElementById('psmMode');
  if (!sel) return;
  currentPsm = parseInt(sel.value, 10);
  const hint = document.getElementById('psmHint');
  if (hint) hint.textContent = PSM_HINTS[currentPsm] || '';
}

function renderFilters() {
  const grid = document.getElementById('entityFilterGrid');
  if (!grid) return;
  grid.innerHTML = [...activeFilters, ...Object.keys(ENTITY_TYPE_COLORS).filter(k => !activeFilters.has(k))]
    .reduce((acc, t) => { if (!acc.seen.has(t)) { acc.seen.add(t); acc.list.push(t); } return acc; }, {seen:new Set(), list:[]})
    .list
    .map(t => {
      const on = activeFilters.has(t);
      return `<span class="entity-chip${on ? ' selected' : ''}" onclick="toggleFilter('${escJs(t)}')">${escHtml(t)}</span>`;
    }).join('');
  updateFilterStatus();
}

function toggleFilter(type) {
  if (activeFilters.has(type)) { activeFilters.delete(type); }
  else                         { activeFilters.add(type); }
  // Update chip visual
  document.querySelectorAll('#entityFilterGrid .entity-chip').forEach(chip => {
    const t = chip.textContent.trim();
    chip.classList.toggle('selected', activeFilters.has(t));
  });
  updateFilterStatus();
  // Live re-render
  if (currentResult) {
    renderEntitiesView(currentResult);
    renderJsonView(currentResult);
  }
}

function resetFilters() {
  activeFilters = new Set(Object.keys(ENTITY_TYPE_COLORS));
  renderFilters();
  if (currentResult) { renderEntitiesView(currentResult); renderJsonView(currentResult); }
}

function updateFilterStatus() {
  if (!currentResult) return;
  const all     = (currentResult.entities || []);
  const visible = all.filter(e => activeFilters.has(e.type)).length;
  const total   = all.length;
  const hidden  = total - visible;
  const statusEl = document.getElementById('filterStatus');
  if (!statusEl) return;
  if (hidden > 0) {
    set('filterVisible', visible); set('filterTotal', total); set('filterHidden', hidden);
    statusEl.style.display = '';
  } else {
    statusEl.style.display = 'none';
  }
  // Update tab badge
  const badge = document.getElementById('entitiesTabCount');
  if (badge) { badge.textContent = visible; badge.style.display = total ? '' : 'none'; }
}

function escJs(s) { return String(s||'').replace(/'/g, "\\'"); }

// ── Template selection ────────────────────────────
const TEMPLATE_CONFIG = {
  legal:   { label:'Legal Clause Extraction',  mode:'standard', entities:['PERSON','ORG','DATE','MONEY'] },
  invoice: { label:'Invoice & Ledger Audit',   mode:'standard', entities:['MONEY','ORG','DATE','CARDINAL','PERCENT'] },
  letter:  { label:'Business Letter Parse',    mode:'standard', entities:['PERSON','ORG','DATE'] },
};

function selectTemplate(key) {
  activeTemplate = key;
  document.querySelectorAll('.template-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById('tpl-'+key);
  if (card) card.classList.add('active');

  const cfg = TEMPLATE_CONFIG[key];
  const bar = document.getElementById('templateConfirmBar');
  const msg = document.getElementById('templateConfirmMsg');
  if (bar && msg) {
    msg.textContent = `${cfg.label} template active — entity filters configured automatically.`;
    bar.style.display = 'flex';
  }
  // Pre-set OCR mode radio
  document.querySelectorAll('input[name="ocrMode"]').forEach(r => r.checked = r.value === cfg.mode);
  currentOcrMode = cfg.mode;
}

// ── Upload / file handling ────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.add('drag-over');
}
function handleDragLeave() {
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
  if (file.size > 10 * 1024 * 1024) { showToast('File exceeds 10 MB limit.', 'error'); return; }
  isSampleResult = false;
  try { document.getElementById('previewImage').src = URL.createObjectURL(file); } catch(e){}

  showProcessing(true);
  animateSteps();

  const fd = new FormData();
  fd.append('file', file);
  fd.append('mode', currentOcrMode);
  fd.append('psm',  currentPsm);

  try {
    const res  = await fetch('/api/analyze', {method:'POST', body:fd});
    const data = await res.json();
    showProcessing(false);
    if (!res.ok || data.error) { showToast(data.error || 'Analysis failed.', 'error'); return; }
    currentResult = data;
    renderResults(data);
    saveToHistory(data, file.name);
    showView('results');
    showPipelineStrip(data);
    showActionBar();
    switchPanelTab('entities');
  } catch(err) {
    showProcessing(false);
    showToast('Network error: ' + err.message, 'error');
  }
}

async function loadSample(name) {
  isSampleResult = true;
  showProcessing(true);
  animateSteps();
  try {
    const listRes = await fetch('/api/samples');
    const samples = await listRes.json();
    const match   = samples.find(s => s.name === name || s.filename.startsWith(name));
    if (!match) { showProcessing(false); showToast('Sample not found.','error'); return; }
    const blob = await fetch('/api/samples/' + match.filename).then(r => r.blob());
    const file = new File([blob], match.filename, {type: blob.type});
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

// ── Pipeline Strip ────────────────────────────────
function showPipelineStrip(data) {
  const strip = document.getElementById('pipelineStrip');
  if (!strip) return;
  strip.style.display = 'flex';

  // Reset all to spinner
  ['pipeOcr','pipeEntities','pipeConf'].forEach(id => {
    const step = document.getElementById(id);
    if (!step) return;
    step.querySelector('.pipe-spinner').style.display = '';
    step.querySelector('.pipe-check').style.display = 'none';
    step.classList.remove('done');
  });

  const steps = [
    { id:'pipeOcr',      valId:'pipeOcrVal',   val: data.total_time_ms + ' ms' },
    { id:'pipeEntities', valId:'pipeEntVal',    val: data.entity_count + ' found' },
    { id:'pipeConf',     valId:'pipeConfVal',   val: data.ocr_confidence + '%' },
  ];

  steps.forEach((s, i) => {
    setTimeout(() => {
      set(s.valId, s.val);
      const step = document.getElementById(s.id);
      if (!step) return;
      step.querySelector('.pipe-spinner').style.display = 'none';
      step.querySelector('.pipe-check').style.display = '';
      step.classList.add('done');
    }, 500 + i * 600);
  });

  // Show sample banner if needed
  const banner = document.getElementById('sampleBanner');
  if (banner) banner.style.display = isSampleResult ? 'flex' : 'none';
}

function showActionBar() {
  const bar = document.getElementById('actionBar');
  if (bar) bar.style.display = 'flex';
}

// ── Results rendering ─────────────────────────────
function renderResults(data) {
  set('rEntities', data.entity_count);
  set('rOcrAcc',   data.ocr_confidence + '%');
  set('rSpeed',    data.total_time_ms + ' ms');
  set('rConf',     data.avg_confidence);
  set('filenameTag', data.filename || '—');
  set('auditId',   'DM-' + Math.floor(Math.random()*9000+1000) + '-X');
  set('modelUsed', data.model_used || '—');

  docCount++;
  localStorage.setItem('dm_doc_count', docCount);
  set('mTotalDocs', docCount);
  set('mExtrRate',  data.ocr_confidence + '%');
  set('mVerified',  data.entity_count);

  // Reset filters so all types are shown for new doc
  activeFilters = new Set(Object.keys(ENTITY_TYPE_COLORS));
  renderFilters();

  renderRawPanel(data);
  renderVerifiedPanel(data);
  renderEntitiesView(data);
  renderStructureView(data);
  renderJsonView(data);
  renderAnalyticsView(data);
  updateFilterStatus();
}

function renderRawPanel(data) {
  const lines = (data.raw_text || '').split('\n').filter(l => l.trim());
  document.getElementById('rawTextContent').innerHTML =
    lines.map(l => `<p class="raw-line">${escHtml(l)}</p>`).join('');
}

function renderVerifiedPanel(data) {
  const el = document.getElementById('verifiedBody');
  const ents = data.entities || [];

  let html = `<div class="group-field">
    <label class="v-field-label">Document Type</label>
    <div class="v-field-box">
      <span>${escHtml(titleCase(data.doc_type || 'General'))}</span>
      <span class="material-symbols-outlined">edit</span>
    </div>
  </div>`;

  const seen = new Set();
  const priority = ['INVOICE_NUMBER','Invoice Number','DATE','Invoice Date','PERSON','ORG','MONEY','Total Amount'];
  const shown = [];
  for (const type of priority) {
    const e = ents.find(x => x.type === type && !seen.has(x.value));
    if (e) { seen.add(e.value); shown.push(e); }
  }
  if (shown.length >= 2) {
    html += `<div class="v-grid-2">`;
    for (let i = 0; i < Math.min(2, shown.length); i++) {
      html += `<div><label class="v-field-label">${escHtml(shown[i].type)}</label>
        <div class="v-field-box">${escHtml(shown[i].value)}</div></div>`;
    }
    html += `</div>`;
  }

  const mainEnt = ents.find(e => e.type === 'ORG') || ents.find(e => e.type === 'PERSON');
  if (mainEnt) {
    html += `<div><label class="v-field-label">Entity: ${escHtml(mainEnt.type)}</label>
      <div class="v-entity-box">
        <p class="v-entity-name">${escHtml(mainEnt.value)}</p>
        ${ents.filter(e => e.type==='GPE'||e.type==='FAC').slice(0,2)
          .map(e=>`<p class="v-entity-detail">${escHtml(e.value)}</p>`).join('')}
      </div></div>`;
  }

  const money = ents.filter(e => e.type==='MONEY'||e.type==='Total Amount');
  if (money.length) {
    html += `<div><label class="v-field-label">Extracted Line Items</label>
      <table class="v-table"><thead><tr><th>Description</th><th>Amount</th></tr></thead><tbody>
        ${money.slice(0,-1).map((e,i)=>`<tr><td>Item ${i+1}</td><td>${escHtml(e.value)}</td></tr>`).join('')}
        <tr><td>Total Verified</td><td>${escHtml(money[money.length-1].value)}</td></tr>
      </tbody></table></div>`;
  }

  html += `<div class="v-actions">
    <button class="btn-approve" onclick="downloadJSON()">Approve &amp; Export</button>
    <button class="btn-more"><span class="material-symbols-outlined">more_horiz</span></button>
  </div>`;
  el.innerHTML = html;
}

function renderEntitiesView(data) {
  const el = document.getElementById('entitiesView');
  const allEnts = data.entities || [];
  // Apply active filters
  const ents = allEnts.filter(e => activeFilters.has(e.type));

  if (!allEnts.length) {
    el.innerHTML = '<p class="empty-state">No entities detected.</p>';
    return;
  }
  if (!ents.length) {
    el.innerHTML = '<p class="empty-state">All entity types are hidden by your filters. <button class="sp-reset-btn" onclick="resetFilters()">Reset Filters</button></p>';
    return;
  }

  const groups = {};
  ents.forEach(e => { if (!groups[e.type]) groups[e.type] = []; groups[e.type].push(e); });

  let html = `<div style="padding:24px;">
    <h3 class="panel-section-label" style="margin-bottom:20px;">DETECTED ENTITIES
      <span style="font-weight:400;font-size:11px;color:#9b7f78;margin-left:8px;">${ents.length} of ${allEnts.length}</span>
    </h3>
    <div style="display:flex;flex-direction:column;gap:16px;">`;

  for (const [type, items] of Object.entries(groups)) {
    const color = ENTITY_TYPE_COLORS[type] || '#6b7280';
    html += `<div style="background:#fff;border:1px solid rgba(228,190,180,0.5);border-radius:6px;padding:16px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span style="background:${color}18;color:${color};font-size:11px;font-weight:700;letter-spacing:0.08em;padding:4px 10px;border-radius:4px;border:1px solid ${color}33;">${escHtml(type)}</span>
        <span style="font-size:11px;color:#9b7f78;font-weight:600;">${items.length} found</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;">
        ${items.map(e => {
          const cc = e.confidence==='high'?'#15803d':e.confidence==='medium'?'#b45309':'#be185d';
          return `<div style="display:flex;align-items:center;gap:8px;background:#f8f7f4;border:1px solid rgba(228,190,180,0.4);border-radius:4px;padding:6px 12px;">
            <span style="font-size:13px;font-weight:500;color:#271813;">${escHtml(e.value)}</span>
            <span style="font-size:10px;font-weight:700;color:${cc};letter-spacing:0.05em;">${(e.confidence||'').toUpperCase()}</span>
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
  if (!ents.length) { el.innerHTML = '<p class="empty-state">No entities detected.</p>'; return; }
  el.innerHTML = ents.map(e => {
    const color = ENTITY_TYPE_COLORS[e.type] || '#6b7280';
    const cc = e.confidence==='high'?'conf-high':e.confidence==='medium'?'conf-medium':'conf-low';
    return `<div class="struct-entity">
      <div style="display:flex;align-items:center;gap:16px;">
        <span class="struct-type" style="background:${color}18;color:${color};">${escHtml(e.type)}</span>
        <span class="struct-value">${escHtml(e.value)}</span>
      </div>
      <span class="struct-conf ${cc}">${(e.confidence||'').toUpperCase()}</span>
    </div>`;
  }).join('');
}

function renderJsonView(data) {
  const filteredEnts = (data.entities || []).filter(e => activeFilters.has(e.type));
  document.getElementById('jsonPre').textContent = JSON.stringify({
    entities: filteredEnts,
    doc_type: data.doc_type,
    ocr_confidence: data.ocr_confidence,
    processing_timings_ms: data.timings,
    metrics: data.metrics,
  }, null, 2);
}

function renderAnalyticsView(data) {
  const m = data.metrics || {};
  document.getElementById('analyticsMetrics').innerHTML = `
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">PRECISION (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.precision_proxy||'0'}%</p>
    </div>
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">RECALL (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.recall_proxy||'0'}%</p>
    </div>
    <div style="background:#f8f7f4;padding:24px;border:1px solid rgba(228,190,180,0.5);border-radius:4px;">
      <p style="font-size:11px;color:#5b4039;font-weight:700;letter-spacing:0.1em;margin-bottom:8px;">F1 SCORE (EST)</p>
      <p style="font-size:42px;font-family:'Instrument Serif',serif;color:#ab2f00;line-height:1;">${m.f1_proxy||'0'}%</p>
    </div>`;

  const t = data.timings || {};
  const total = Object.values(t).reduce((a,b)=>a+b,0)||1;
  const colors = {preprocess_ms:'#f59e0b',ocr_ms:'#3b82f6',clean_ms:'#10b981',nlp_pre_ms:'#84cc16',extraction_ms:'#8b5cf6'};
  const labels = {preprocess_ms:'Preprocess',ocr_ms:'OCR',clean_ms:'Cleaning',nlp_pre_ms:'NLP',extraction_ms:'Extraction'};
  let html = '<div style="display:flex;gap:4px;height:16px;border-radius:4px;overflow:hidden;">';
  for (const [k,v] of Object.entries(t)) {
    if (v>0&&colors[k]) html += `<div style="flex:${v/total};background:${colors[k]};" title="${labels[k]||k}: ${v}ms"></div>`;
  }
  html += '</div><div style="margin-top:24px;display:flex;flex-direction:column;gap:12px;font-size:14px;color:#271813;">';
  for (const [k,v] of Object.entries(t)) {
    if (v>0&&labels[k]) html += `<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(228,190,180,0.3);padding-bottom:8px;">
      <span style="font-weight:500;">${labels[k]}</span><b style="color:#ab2f00;">${v} ms</b></div>`;
  }
  html += '</div>';
  document.getElementById('analyticsTimeline').innerHTML = html;
}

// ── History ───────────────────────────────────────
function saveToHistory(data, filename) {
  history.unshift({ filename: filename||data.filename, doc_type:data.doc_type,
    entity_count:data.entity_count, ocr_confidence:data.ocr_confidence,
    ts: new Date().toISOString(), data });
  history = history.slice(0,20);
  localStorage.setItem('dm_history', JSON.stringify(history));
}
function renderHistory() {
  const el = document.getElementById('historyList');
  if (!history.length) { el.innerHTML = '<p class="empty-state">No analyses yet. Upload a document to begin.</p>'; return; }
  el.innerHTML = history.map((h,i) => `
    <div class="history-item" onclick="replayHistory(${i})">
      <div>
        <p class="h-name">${escHtml(h.filename)}</p>
        <p class="h-meta">${titleCase(h.doc_type)} · ${h.entity_count} entities · ${new Date(h.ts).toLocaleString()}</p>
      </div>
      <span class="h-badge">${h.ocr_confidence}%</span>
    </div>`).join('');
}
function replayHistory(idx) {
  const h = history[idx]; if (!h) return;
  currentResult = h.data; renderResults(h.data);
  showView('results'); switchPanelTab('entities');
  showPipelineStrip(h.data); showActionBar();
}

// ── Settings ──────────────────────────────────────
function renderSettings() {
  const grid = document.getElementById('entityFilterGrid');
  if (!grid) return;
  grid.innerHTML = ENTITY_TYPE_LABELS.map(t =>
    `<span class="entity-chip selected" onclick="toggleChip(this,'${t}')">${t}</span>`).join('');
  const rangeEl = document.getElementById('settingsConf');
  if (rangeEl) rangeEl.oninput = function(){ set('settingsConfVal', this.value+'%'); };
}
function toggleChip(el) { el.classList.toggle('selected'); }

// ── Reset ─────────────────────────────────────────
function resetToUpload() {
  currentResult = null;
  isSampleResult = false;
  document.getElementById('fileInput').value = '';
  const strip = document.getElementById('pipelineStrip');
  if (strip) strip.style.display = 'none';
  const bar = document.getElementById('actionBar');
  if (bar) bar.style.display = 'none';
  showView('dashboard');
}

// ── Download JSON ─────────────────────────────────
function downloadJSON() {
  if (!currentResult) return;
  const blob = new Blob([JSON.stringify({
    entities: currentResult.entities, doc_type: currentResult.doc_type,
    ocr_confidence: currentResult.ocr_confidence, timings: currentResult.timings,
    metrics: currentResult.metrics,
  }, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'documind_extraction.json';
  a.click();
}

// ── Download CSV ──────────────────────────────────
function downloadCSV() {
  if (!currentResult) return;
  const rows = [['Entity','Type','Confidence']];
  (currentResult.entities||[]).forEach(e => rows.push([`"${e.value}"`, e.type, e.confidence||'']));
  const blob = new Blob([rows.map(r=>r.join(',')).join('\n')], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'documind_entities.csv';
  a.click();
}

// ── Copy Cleaned Text ─────────────────────────────
function copyCleanedText() {
  if (!currentResult) return;
  const text = (currentResult.cleaned_text || currentResult.raw_text || '');
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('btnCopyText');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-outlined">check</span> Copied!';
    btn.classList.add('action-success');
    setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('action-success'); }, 2000);
  });
}

// ── Toast ─────────────────────────────────────────
let _toastTimer = null;
function showToast(msg, type='error') {
  const el = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  el.className = 'toast' + (type==='success'?' success':'');
  el.style.display = '';
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(hideToast, 5000);
}
function hideToast() { document.getElementById('toast').style.display = 'none'; }

// ── Utility ───────────────────────────────────────
function set(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function titleCase(s) {
  return String(s||'').replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ── Init ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  showView('dashboard');
  set('mTotalDocs', docCount);
  switchPanelTab('entities');
  renderFilters();
  updatePsmHint();
  // On mobile, collapse settings panel by default
  if (window.innerWidth < 1024) {
    const body = document.getElementById('settingsPanelBody');
    const chevron = document.getElementById('settingsPanelChevron');
    if (body)    body.style.display = 'none';
    if (chevron) chevron.textContent = 'expand_more';
  }
});
