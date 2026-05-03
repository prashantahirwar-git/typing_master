/* ═══════════════════════════════════════════════════════════════════════════
   TypeCraft — Main Application JS
   Sections: Navigation · Typing Engine · Timer · Metrics · History · Chart
═══════════════════════════════════════════════════════════════════════════ */

'use strict';

// ── State ────────────────────────────────────────────────────────────────────
const State = {
  section: 'tests',
  test: {
    mode: 'timed',      // 'timed' | 'page'
    duration: 60,       // seconds (for timed mode)
    text: '',
    chars: [],          // [{char, status: 'pending'|'correct'|'incorrect'}]
    currentIdx: 0,
    started: false,
    finished: false,
    startTime: null,
    timerInterval: null,
    secondsLeft: 60,
    correctChars: 0,
    totalKeystrokes: 0,
    errors: 0,
  },
  history: [],
  chart: null,
};

// ── DOM Refs ─────────────────────────────────────────────────────────────────
const dom = {
  sections:     () => document.querySelectorAll('.section'),
  navItems:     () => document.querySelectorAll('.nav-item'),
  textDisplay:  () => document.getElementById('text-display'),
  typingInput:  () => document.getElementById('typing-input'),
  typingWrapper:() => document.getElementById('typing-wrapper'),
  timerEl:      () => document.getElementById('timer-val'),
  wpmEl:        () => document.getElementById('live-wpm'),
  accEl:        () => document.getElementById('live-acc'),
  progressBar:  () => document.getElementById('progress-bar'),
  testHint:     () => document.getElementById('test-hint'),
  modalOverlay: () => document.getElementById('result-modal-overlay'),
  historyBody:  () => document.getElementById('history-tbody'),
  historyEmpty: () => document.getElementById('history-empty'),
  sidebarTests: () => document.getElementById('sidebar-tests'),
  sidebarBest:  () => document.getElementById('sidebar-best'),
};

// ── Navigation ───────────────────────────────────────────────────────────────
function navigate(sectionId) {
  State.section = sectionId;
  dom.sections().forEach(s => s.classList.toggle('active', s.id === sectionId));
  dom.navItems().forEach(n => n.classList.toggle('active', n.dataset.section === sectionId));

  const titles = { tests:'Typing Tests', lessons:'Lessons', games:'Games', progress:'Progress' };
  document.getElementById('topbar-title').textContent = titles[sectionId] || 'TypeCraft';

  if (sectionId === 'progress') renderChart();
  if (sectionId === 'progress' || sectionId === 'tests') loadHistory();
  closeSidebar();
}

// Sidebar hamburger
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }
function closeSidebar() {
  if (window.innerWidth <= 900) document.getElementById('sidebar').classList.remove('open');
}

// ── Test Mode Selection ───────────────────────────────────────────────────────
function selectMode(mode, duration) {
  State.test.mode = mode;
  State.test.duration = duration;
  document.querySelectorAll('.test-card').forEach(c => c.classList.remove('selected'));
  document.querySelector(`[data-mode="${mode}"][data-duration="${duration}"]`)?.classList.add('selected');
  loadNewTest();
}

// ── Load / Reset Test ─────────────────────────────────────────────────────────
async function loadNewTest() {
  resetTestState();
  try {
    const length = State.test.duration >= 300 ? 'long' : State.test.duration >= 180 ? 'medium' : 'short';
    const resp = await fetch(`/api/text?length=${length}`);
    const data = await resp.json();
    initText(data.text);
  } catch (e) {
    console.error('Failed to load text', e);
  }
}

function resetTestState() {
  const t = State.test;
  clearInterval(t.timerInterval);
  t.started = false;
  t.finished = false;
  t.startTime = null;
  t.currentIdx = 0;
  t.correctChars = 0;
  t.totalKeystrokes = 0;
  t.errors = 0;
  t.secondsLeft = t.duration;
  updateTimerDisplay(t.duration);
  dom.wpmEl().textContent = '0';
  dom.accEl().textContent = '100';
  if (dom.progressBar()) dom.progressBar().style.width = '0%';
  dom.timerEl()?.classList.remove('urgent');
}

function initText(text) {
  State.test.text = text;
  State.test.chars = text.split('').map(c => ({ char: c, status: 'pending' }));
  renderTextDisplay();
  showHint(true);
}

function renderTextDisplay() {
  const display = dom.textDisplay();
  display.innerHTML = State.test.chars.map((c, i) => {
    const cls = i === State.test.currentIdx
      ? `char current`
      : `char ${c.status}`;
    const ch = c.char === ' ' ? '&nbsp;' : c.char;
    return `<span class="${cls}" data-idx="${i}">${ch}</span>`;
  }).join('');
}

function updateCharDisplay(idx, status) {
  const spans = dom.textDisplay().querySelectorAll('.char');
  if (!spans.length) { renderTextDisplay(); return; }
  if (spans[idx]) {
    spans[idx].className = `char ${status}`;
  }
  // Update cursor
  spans.forEach(s => s.classList.remove('current'));
  const nextIdx = State.test.currentIdx;
  if (spans[nextIdx]) spans[nextIdx].classList.add('current');
}

function showHint(show) {
  const hint = dom.testHint();
  if (hint) hint.style.opacity = show ? '1' : '0';
}

// ── Input Handling ────────────────────────────────────────────────────────────
function focusInput() {
  dom.typingInput()?.focus();
  dom.typingWrapper()?.classList.add('focused');
  showHint(false);
}

function handleKeydown(e) {
  const t = State.test;
  if (t.finished) return;
  if (e.key === 'Tab') { e.preventDefault(); loadNewTest(); return; }
  if (e.ctrlKey || e.altKey || e.metaKey) return;
  if (e.key.length !== 1 && e.key !== 'Backspace') return;

  if (!t.started && e.key !== 'Backspace') {
    startTest();
  }
  if (!t.started) return;

  if (e.key === 'Backspace') {
    handleBackspace();
    return;
  }

  processChar(e.key);
}

function handleBackspace() {
  const t = State.test;
  if (t.currentIdx === 0) return;
  t.currentIdx--;
  t.chars[t.currentIdx].status = 'pending';
  updateCharDisplay(t.currentIdx, 'pending');
  updateProgress();
}

function processChar(key) {
  const t = State.test;
  const expected = t.chars[t.currentIdx].char;
  const correct = key === expected;
  t.totalKeystrokes++;
  if (correct) {
    t.correctChars++;
    t.chars[t.currentIdx].status = 'correct';
    updateCharDisplay(t.currentIdx, 'correct');
  } else {
    t.errors++;
    t.chars[t.currentIdx].status = 'incorrect';
    updateCharDisplay(t.currentIdx, 'incorrect');
  }
  t.currentIdx++;

  updateLiveMetrics();
  updateProgress();

  // Check page-test completion
  if (t.mode === 'page' && t.currentIdx >= t.chars.length) {
    finishTest();
  }
}

// ── Timer ─────────────────────────────────────────────────────────────────────
function startTest() {
  const t = State.test;
  t.started = true;
  t.startTime = performance.now();
  if (t.mode === 'timed') {
    t.secondsLeft = t.duration;
    t.timerInterval = setInterval(tickTimer, 1000);
  } else {
    // Page mode: count up
    t.timerInterval = setInterval(() => {
      const elapsed = Math.floor((performance.now() - t.startTime) / 1000);
      updateTimerDisplay(elapsed);
    }, 1000);
  }
}

function tickTimer() {
  const t = State.test;
  t.secondsLeft--;
  updateTimerDisplay(t.secondsLeft);
  if (t.secondsLeft <= 10) dom.timerEl()?.classList.add('urgent');
  if (t.secondsLeft <= 0) finishTest();
}

function updateTimerDisplay(val) {
  const min = Math.floor(Math.abs(val) / 60);
  const sec = Math.abs(val) % 60;
  if (dom.timerEl()) dom.timerEl().textContent = `${String(min).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
}

// ── Metrics ───────────────────────────────────────────────────────────────────
function calcWPM() {
  const t = State.test;
  if (!t.startTime) return 0;
  const elapsed = (performance.now() - t.startTime) / 60000; // minutes
  if (elapsed < 0.001) return 0;
  return Math.round((t.correctChars / 5) / elapsed);
}

function calcAccuracy() {
  const t = State.test;
  if (!t.totalKeystrokes) return 100;
  return Math.round((t.correctChars / t.totalKeystrokes) * 100);
}

function updateLiveMetrics() {
  dom.wpmEl().textContent = calcWPM();
  dom.accEl().textContent = calcAccuracy();
}

function updateProgress() {
  const t = State.test;
  const pct = Math.round((t.currentIdx / t.chars.length) * 100);
  if (dom.progressBar()) dom.progressBar().style.width = pct + '%';
}

// ── Finish Test ───────────────────────────────────────────────────────────────
async function finishTest() {
  const t = State.test;
  if (t.finished) return;
  t.finished = true;
  clearInterval(t.timerInterval);

  const elapsed = t.startTime ? (performance.now() - t.startTime) / 1000 : t.duration;
  const wpm = calcWPM();
  const accuracy = calcAccuracy();

  // Save result
  try {
    await fetch('/api/results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wpm, accuracy,
        duration: Math.round(elapsed),
        chars: t.correctChars,
        errors: t.errors,
      })
    });
  } catch (e) { console.error('Failed to save', e); }

  showResultModal(wpm, accuracy, Math.round(elapsed));
  loadSidebarStats();
}

// ── Result Modal ──────────────────────────────────────────────────────────────
function showResultModal(wpm, accuracy, duration) {
  document.getElementById('res-wpm').textContent = wpm;
  document.getElementById('res-acc').textContent = accuracy + '%';
  document.getElementById('res-chars').textContent = State.test.correctChars;
  document.getElementById('res-errors').textContent = State.test.errors;
  document.getElementById('res-time').textContent = formatDuration(duration);
  dom.modalOverlay().classList.add('open');
}

function closeModal() {
  dom.modalOverlay().classList.remove('open');
}

function formatDuration(s) {
  const m = Math.floor(s / 60), sec = s % 60;
  return m ? `${m}m ${sec}s` : `${sec}s`;
}

// ── History ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  try {
    const resp = await fetch('/api/results');
    State.history = await resp.json();
    renderHistory();
  } catch (e) { console.error(e); }
}

function renderHistory() {
  const tbody = dom.historyBody();
  const empty = dom.historyEmpty();
  if (!tbody) return;
  if (!State.history.length) {
    tbody.innerHTML = '';
    empty?.classList.remove('d-none');
    return;
  }
  empty?.classList.add('d-none');
  tbody.innerHTML = State.history.map(r => `
    <tr>
      <td>${r.date}</td>
      <td class="wpm-badge" style="color:${wpmColor(r.wpm)}">${r.wpm}</td>
      <td>
        <div class="accuracy-bar">
          <div class="acc-bar-outer">
            <div class="acc-bar-inner" style="width:${r.accuracy}%"></div>
          </div>
          <span>${r.accuracy}%</span>
        </div>
      </td>
      <td>${formatDuration(r.duration)}</td>
      <td>${r.errors}</td>
      <td>
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="printCert(${r.id})">🏆 Certificate</button>
          <button class="btn btn-danger btn-sm" onclick="deleteResult(${r.id})">✕</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function wpmColor(wpm) {
  if (wpm >= 80) return 'var(--amber)';
  if (wpm >= 50) return 'var(--green)';
  return 'var(--text)';
}

async function deleteResult(id) {
  if (!confirm('Delete this result?')) return;
  try {
    await fetch(`/api/results/${id}`, { method: 'DELETE' });
    State.history = State.history.filter(r => r.id !== id);
    renderHistory();
    renderChart();
  } catch (e) { console.error(e); }
}

// ── Certificate ───────────────────────────────────────────────────────────────
function printCert(id) {
  const r = State.history.find(h => h.id === id);
  if (!r) return;
  const cert = document.getElementById('cert-print');
  cert.innerHTML = `
    <div class="certificate">
      <h1>🏆 Certificate of Achievement</h1>
      <p class="cert-line" style="font-size:1.3rem;margin-top:16px">This certifies that the holder has completed a typing assessment</p>
      <div class="cert-stats">
        <div class="cs-item"><div class="cs-val">${r.wpm}</div><div class="cs-lbl">WPM</div></div>
        <div class="cs-item"><div class="cs-val">${r.accuracy}%</div><div class="cs-lbl">Accuracy</div></div>
      </div>
      <p class="cert-line">Completed on ${r.date}</p>
      <p class="cert-line" style="margin-top:24px;font-size:0.8rem;color:#888">TypeCraft Typing Platform</p>
    </div>
  `;
  cert.style.display = 'flex';
  window.print();
  cert.style.display = 'none';
}

// ── Chart ─────────────────────────────────────────────────────────────────────
async function renderChart() {
  try {
    const resp = await fetch('/api/stats');
    const data = await resp.json();
    buildChart(data.history);
    updateSidebarStats(data);
  } catch (e) { console.error(e); }
}

function buildChart(history) {
  const canvas = document.getElementById('progress-chart');
  if (!canvas) return;

  if (State.chart) { State.chart.destroy(); State.chart = null; }

  if (!history.length) {
    canvas.parentElement.innerHTML = `
      <div class="empty-state">
        <div class="es-icon">📊</div>
        <p>Complete some tests to see your progress chart.</p>
      </div>`;
    return;
  }

  const labels = history.map((r, i) => `Test ${i + 1}`);
  const wpmData = history.map(r => r.wpm);
  const accData = history.map(r => r.accuracy);

  const style = getComputedStyle(document.documentElement);
  const amber = '#f0a500';
  const green = '#39d353';
  const gridColor = 'rgba(48,54,61,0.8)';

  State.chart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'WPM',
          data: wpmData,
          borderColor: amber,
          backgroundColor: 'rgba(240,165,0,0.08)',
          borderWidth: 2.5,
          pointBackgroundColor: amber,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
          yAxisID: 'y',
        },
        {
          label: 'Accuracy %',
          data: accData,
          borderColor: green,
          backgroundColor: 'rgba(57,211,83,0.06)',
          borderWidth: 2,
          pointBackgroundColor: green,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.4,
          fill: true,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: '#7d8590', font: { family: "'DM Sans', sans-serif", size: 12 }, boxWidth: 14 }
        },
        tooltip: {
          backgroundColor: '#1c2128',
          borderColor: '#30363d',
          borderWidth: 1,
          titleColor: '#e6edf3',
          bodyColor: '#7d8590',
          titleFont: { family: "'Space Mono', monospace", size: 11 },
          bodyFont: { family: "'DM Sans', sans-serif", size: 12 },
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: '#7d8590', font: { family: "'DM Sans'", size: 11 } }
        },
        y: {
          position: 'left',
          grid: { color: gridColor },
          ticks: { color: amber, font: { family: "'Space Mono'", size: 11 }, callback: v => v + ' wpm' },
          title: { display: true, text: 'WPM', color: amber, font: { size: 11 } }
        },
        y1: {
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: green, font: { family: "'Space Mono'", size: 11 }, callback: v => v + '%' },
          title: { display: true, text: 'Accuracy', color: green, font: { size: 11 } },
          min: 0, max: 100,
        }
      }
    }
  });
}

// ── Sidebar Stats ─────────────────────────────────────────────────────────────
async function loadSidebarStats() {
  try {
    const resp = await fetch('/api/stats');
    const data = await resp.json();
    updateSidebarStats(data);
  } catch (e) {}
}

function updateSidebarStats(data) {
  const testsEl = dom.sidebarTests();
  const bestEl  = dom.sidebarBest();
  if (testsEl) testsEl.textContent = data.total_tests;
  if (bestEl)  bestEl.textContent  = data.best_wpm ? Math.round(data.best_wpm) : '—';
}

// ── Lessons ───────────────────────────────────────────────────────────────────
async function loadLessons() {
  try {
    const resp = await fetch('/api/lessons');
    const lessons = await resp.json();
    const grid = document.getElementById('lessons-grid');
    if (!grid) return;
    grid.innerHTML = lessons.map(l => `
      <div class="lesson-card" onclick="startLesson(${l.id})">
        <div class="lesson-header">
          <span class="lesson-icon">${l.icon}</span>
          <div>
            <div class="lesson-title">${l.title}</div>
            <span class="lesson-level level-${l.level}">${l.level}</span>
          </div>
        </div>
        <p class="lesson-desc">${l.desc}</p>
        <div style="margin-top:14px">
          <button class="btn btn-secondary btn-sm">Start Lesson →</button>
        </div>
      </div>
    `).join('');
  } catch (e) {}
}

function startLesson(id) {
  navigate('tests');
  selectMode('page', 0);
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Nav clicks
  dom.navItems().forEach(item => {
    item.addEventListener('click', () => navigate(item.dataset.section));
  });

  // Typing input
  const input = dom.typingInput();
  if (input) {
    input.addEventListener('keydown', handleKeydown);
  }

  // Click wrapper to focus
  dom.typingWrapper()?.addEventListener('click', focusInput);
  dom.typingWrapper()?.addEventListener('focus', () => {
    dom.typingWrapper()?.classList.add('focused');
    showHint(false);
  }, true);
  document.addEventListener('blur', (e) => {
    if (e.target === dom.typingInput()) {
      dom.typingWrapper()?.classList.remove('focused');
    }
  }, true);

  // Default: select 1-min timed test
  selectMode('timed', 60);
  loadSidebarStats();
  loadHistory();
  loadLessons();
  navigate('tests');
});
