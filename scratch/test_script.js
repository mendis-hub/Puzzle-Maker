
'use strict';

// ═══════════════════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const MAZE_API = '/api/generate';
const WS_API   = '/api/generate/wordsearch';
const CW_API   = '/api/generate/crossword';

// ── DOM refs ──────────────────────────────────────────────────────────────

// Tabs
const tabMaze   = document.getElementById('tab-maze');
const tabWs     = document.getElementById('tab-ws');
const tabCw     = document.getElementById('tab-cw');
const card      = document.getElementById('mainCard');
const formTitle = document.getElementById('formTitle');

// Maze form
const sizeSlider      = document.getElementById('sizeSlider');
const sizeDisplay     = document.getElementById('sizeDisplay');
const mazeTitleInput  = document.getElementById('mazeTitleInput');
const mazeSeedInput   = document.getElementById('mazeSeedInput');
const mazeSeedDisplay = document.getElementById('mazeSeedDisplay');
const mazeDiceBtn     = document.getElementById('mazeDiceBtn');
const mazeGenerateBtn = document.getElementById('mazeGenerateBtn');
const mazeProgressWrap= document.getElementById('mazeProgressWrap');
const mazeProgressBar = document.getElementById('mazeProgressBar');

// Maze stats
const statGrid     = document.getElementById('statGrid');
const statRooms    = document.getElementById('statRooms');
const statPassages = document.getElementById('statPassages');
const statDiff     = document.getElementById('statDiff');
const mazeZipFilename = document.getElementById('mazeZipFilename');

// Maze preview
const mazeCanvas = document.getElementById('mazeCanvas');

// Difficulty chips
const chips = {
  easy:   document.getElementById('chip-easy'),
  medium: document.getElementById('chip-medium'),
  hard:   document.getElementById('chip-hard'),
  expert: document.getElementById('chip-expert'),
};

// Word search form
const wsTitleInput  = document.getElementById('wsTitleInput');
const wsWordsInput  = document.getElementById('wsWordsInput');
const wsWordCount   = document.getElementById('wsWordCount');
const wsRowsSlider  = document.getElementById('wsRowsSlider');
const wsColsSlider  = document.getElementById('wsColsSlider');
const wsRowsDisplay = document.getElementById('wsRowsDisplay');
const wsColsDisplay = document.getElementById('wsColsDisplay');
const wsSeedInput   = document.getElementById('wsSeedInput');
const wsSeedDisplay = document.getElementById('wsSeedDisplay');
const wsDiceBtn     = document.getElementById('wsDiceBtn');
const wsGenerateBtn = document.getElementById('wsGenerateBtn');
const wsProgressWrap= document.getElementById('wsProgressWrap');
const wsProgressBar = document.getElementById('wsProgressBar');

// WS stats
const wsStatGrid  = document.getElementById('wsStatGrid');
const wsStatCells = document.getElementById('wsStatCells');
const wsStatWords = document.getElementById('wsStatWords');
const wsZipFilename = document.getElementById('wsZipFilename');

// WS preview
const wsArt = document.getElementById('wsArt');

// Crossword form
const cwTitleInput   = document.getElementById('cwTitleInput');
const cwWordsInput   = document.getElementById('cwWordsInput');
const cwWordCount    = document.getElementById('cwWordCount');
const cwSeedInput    = document.getElementById('cwSeedInput');
const cwSeedDisplay  = document.getElementById('cwSeedDisplay');
const cwDiceBtn      = document.getElementById('cwDiceBtn');
const cwGenerateBtn  = document.getElementById('cwGenerateBtn');
const cwProgressWrap = document.getElementById('cwProgressWrap');
const cwProgressBar  = document.getElementById('cwProgressBar');

// Crossword stats & preview
const cwStatGrid     = document.getElementById('cwStatGrid');
const cwStatPlaced   = document.getElementById('cwStatPlaced');
const cwStatAcross   = document.getElementById('cwStatAcross');
const cwStatDown     = document.getElementById('cwStatDown');
const cwToggleAnsBtn = document.getElementById('cwToggleAnsBtn');
const cwCanvas       = document.getElementById('cwCanvas');

// Toasts
const toastWrap = document.getElementById('toastWrap');

// ═══════════════════════════════════════════════════════════════════════════
//  TAB SWITCHING
// ═══════════════════════════════════════════════════════════════════════════

let currentTab = 'maze';
let currentCwSeed = null;
let showCwAnswers = false;

function switchTab(tab) {
  currentTab = tab;

  // Update tab buttons
  tabMaze.classList.toggle('active', tab === 'maze');
  tabWs.classList.toggle('active', tab === 'ws');
  tabCw.classList.toggle('active', tab === 'cw');

  tabMaze.setAttribute('aria-selected', tab === 'maze');
  tabWs.setAttribute('aria-selected', tab === 'ws');
  tabCw.setAttribute('aria-selected', tab === 'cw');

  tabWs.classList.toggle('ws-active', tab === 'ws');
  tabCw.classList.toggle('cw-active', tab === 'cw');

  // Card top bar
  card.classList.toggle('ws-mode', tab === 'ws');
  card.classList.toggle('cw-mode', tab === 'cw');

  // Form panels
  document.getElementById('panel-maze').classList.toggle('active', tab === 'maze');
  document.getElementById('panel-ws').classList.toggle('active', tab === 'ws');
  document.getElementById('panel-cw').classList.toggle('active', tab === 'cw');

  // Preview panels
  document.getElementById('preview-maze').classList.toggle('active', tab === 'maze');
  document.getElementById('preview-ws').classList.toggle('active', tab === 'ws');
  document.getElementById('preview-cw').classList.toggle('active', tab === 'cw');

  // Form title
  if (tab === 'maze')      formTitle.textContent = '⚙ Maze Settings';
  else if (tab === 'ws')   formTitle.textContent = '⚙ Word Search Settings';
  else                     formTitle.textContent = '⚙ Crossword Settings';

  if (tab === 'ws') {
    updateWsStats();
    renderWsPreview();
  } else if (tab === 'cw') {
    updateCwWordCount();
    renderCwPreview();
  }
}

tabMaze.addEventListener('click', () => switchTab('maze'));
tabWs.addEventListener('click',   () => switchTab('ws'));
tabCw.addEventListener('click',   () => switchTab('cw'));

// Keyboard navigation
const allTabBtns = [tabMaze, tabWs, tabCw];
allTabBtns.forEach((btn, idx) => {
  btn.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = allTabBtns[(idx + 1) % allTabBtns.length];
      next.focus();
      next.click();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = allTabBtns[(idx - 1 + allTabBtns.length) % allTabBtns.length];
      prev.focus();
      prev.click();
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  MAZE LOGIC
// ═══════════════════════════════════════════════════════════════════════════

function updateSliderFill(slider) {
  const min = +slider.min, max = +slider.max, val = +slider.value;
  const pct = ((val - min) / (max - min) * 100).toFixed(1) + '%';
  slider.style.setProperty('--pct', pct);
}

function getDifficulty(size) {
  if (size <= 11) return { label: 'Easy',   chip: 'easy'   };
  if (size <= 21) return { label: 'Medium', chip: 'medium' };
  if (size <= 31) return { label: 'Hard',   chip: 'hard'   };
  return               { label: 'Expert', chip: 'expert' };
}

function updateMazeStats() {
  const size  = +sizeSlider.value;
  const rooms = Math.floor(size / 2) * Math.floor(size / 2);
  const diff  = getDifficulty(size);

  sizeDisplay.textContent  = `${size} × ${size}`;
  statGrid.textContent     = `${size}×${size}`;
  statRooms.textContent    = rooms.toLocaleString();
  statPassages.textContent = `~${(rooms - 1).toLocaleString()}`;
  statDiff.textContent     = diff.label;
  mazeZipFilename.textContent = `maze_${size}x${size}.zip`;

  Object.entries(chips).forEach(([key, el]) => {
    el.classList.toggle('active', key === diff.chip);
  });
}

function updateMazeSeedDisplay() {
  mazeSeedDisplay.textContent = mazeSeedInput.value.trim() === '' ? 'random' : mazeSeedInput.value.trim();
}

mazeDiceBtn.addEventListener('click', () => {
  mazeSeedInput.value = Math.floor(Math.random() * 999999);
  updateMazeSeedDisplay();
  mazeDiceBtn.classList.add('spinning');
  setTimeout(() => mazeDiceBtn.classList.remove('spinning'), 400);
});

// ── Maze preview (CSS grid DFS) ────────────────────────────────────────────

const WALL = 0, PATH = 1;
const _DIRS = [[-2,0],[2,0],[0,-2],[0,2]];

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function buildPreviewMaze(dim) {
  const grid    = Array.from({length: dim}, () => new Uint8Array(dim));
  const visited = new Set();
  const stack   = [];
  function key(r,c){ return r*1000+c; }
  function push(r,c){
    visited.add(key(r,c));
    grid[r][c] = PATH;
    stack.push([r,c,shuffle([..._DIRS]),0]);
  }
  push(1,1);
  while(stack.length){
    const f = stack[stack.length-1];
    let carved = false;
    while(f[3] < f[2].length){
      const [dr,dc] = f[2][f[3]++];
      const nr=f[0]+dr, nc=f[1]+dc;
      const wr=f[0]+dr/2, wc=f[1]+dc/2;
      if(nr>=0&&nr<dim&&nc>=0&&nc<dim&&!visited.has(key(nr,nc))){
        grid[wr][wc]=PATH;
        push(nr,nc);
        carved=true; break;
      }
    }
    if(!carved) stack.pop();
  }
  return grid;
}

function bfsPath(grid, dim, sr, sc, er, ec){
  const came = new Map();
  came.set(sr*1000+sc, null);
  const q=[[sr,sc]]; let h=0;
  while(h<q.length){
    const [r,c]=q[h++];
    if(r===er&&c===ec) break;
    for(const [dr,dc] of [[-1,0],[1,0],[0,-1],[0,1]]){
      const nr=r+dr,nc=c+dc;
      const k=nr*1000+nc;
      if(nr>=0&&nr<dim&&nc>=0&&nc<dim&&grid[nr][nc]===PATH&&!came.has(k)){
        came.set(k,r*1000+c); q.push([nr,nc]);
      }
    }
  }
  const path=new Set();
  let node=er*1000+ec;
  while(node!==null){ path.add(node); node=came.get(node); }
  return path;
}

let currentMazeSeed  = null;
let currentMazeShape = 'square';
let currentWsSeed    = null;

document.querySelectorAll('.shape-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.shape-chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMazeShape = btn.dataset.shape;
    document.getElementById('shapeDisplay').textContent = btn.dataset.shape.charAt(0).toUpperCase() + btn.dataset.shape.slice(1);
    scheduleMazePreview();
  });
});

let mazePreviewTimer = null;
function scheduleMazePreview() {
  clearTimeout(mazePreviewTimer);
  mazePreviewTimer = setTimeout(renderMazePreview, 120);
}

async function renderMazePreview() {
  const size  = +sizeSlider.value;
  const seedRaw = mazeSeedInput.value.trim();
  const seed  = seedRaw !== '' ? parseInt(seedRaw, 10) : currentMazeSeed;
  const shape = currentMazeShape;

  try {
    const res = await fetch('/api/preview/maze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ size, seed, shape, title: 'Preview' }),
    });
    if (!res.ok) return;
    const data = await res.json();
    currentMazeSeed = data.seed_used;

    const dim = data.rows;
    const pathSet = new Set(data.solution.map(([r, c]) => r * 1000 + c));

    mazeCanvas.style.gridTemplateColumns = `repeat(${dim}, 1fr)`;
    mazeCanvas.style.gridTemplateRows    = `repeat(${dim}, 1fr)`;
    mazeCanvas.innerHTML = '';

    for (let r = 0; r < dim; r++) {
      for (let c = 0; c < dim; c++) {
        const div = document.createElement('div');
        div.className = 'mc';
        const k = r * 1000 + c;

        if (r === data.start[0] && c === data.start[1])      div.classList.add('start');
        else if (r === data.end[0] && c === data.end[1])     div.classList.add('end');
        else if (pathSet.has(k) && data.grid[r][c] === 1)    div.classList.add('path');
        else if (data.grid[r][c] === 1)                      div.classList.add('open');
        else if (data.grid[r][c] === 0)                      div.classList.add('wall');
        else                                                 div.style.background = 'transparent';
        mazeCanvas.appendChild(div);
      }
    }
  } catch (err) {
    console.error('Maze preview fetch error:', err);
  }
}

sizeSlider.addEventListener('input', () => {
  updateSliderFill(sizeSlider);
  updateMazeStats();
  scheduleMazePreview();
});

mazeSeedInput.addEventListener('input', () => {
  currentMazeSeed = null;
  updateMazeSeedDisplay();
  scheduleMazePreview();
});

mazeDiceBtn.addEventListener('click', () => {
  mazeSeedInput.value = Math.floor(Math.random() * 999999);
  currentMazeSeed = parseInt(mazeSeedInput.value, 10);
  updateMazeSeedDisplay();
  mazeDiceBtn.classList.add('spinning');
  setTimeout(() => mazeDiceBtn.classList.remove('spinning'), 400);
  scheduleMazePreview();
});

// ═══════════════════════════════════════════════════════════════════════════
//  WORD SEARCH LOGIC
// ═══════════════════════════════════════════════════════════════════════════

function getWsWords() {
  return wsWordsInput.value
    .split('\n')
    .map(w => w.trim().replace(/[^a-zA-Z]/g, '').toUpperCase())
    .filter(w => w.length >= 2);
}

function updateWsWordCount() {
  const words = getWsWords();
  const n = words.length;
  wsWordCount.textContent = `${n} word${n !== 1 ? 's' : ''}`;
  wsStatWords.textContent = n;

  // Activate correct chip
  document.getElementById('wcc-few').classList.toggle('active',  n >= 1  && n <= 5);
  document.getElementById('wcc-med').classList.toggle('active',  n >= 6  && n <= 12);
  document.getElementById('wcc-many').classList.toggle('active', n >= 13 && n <= 20);
  document.getElementById('wcc-lots').classList.toggle('active', n >= 21);
}

function updateWsStats() {
  const rows = +wsRowsSlider.value;
  const cols = +wsColsSlider.value;
  wsRowsDisplay.textContent = rows;
  wsColsDisplay.textContent = cols;
  wsStatGrid.textContent    = `${rows}×${cols}`;
  wsStatCells.textContent   = (rows * cols).toLocaleString();
  wsZipFilename.textContent = `wordsearch_${rows}x${cols}.zip`;
  updateSliderFill(wsRowsSlider);
  updateSliderFill(wsColsSlider);
  updateWsWordCount();
}

function updateWsSeedDisplay() {
  wsSeedDisplay.textContent = wsSeedInput.value.trim() === '' ? 'random' : wsSeedInput.value.trim();
}

let wsPreviewTimer = null;
function scheduleWsPreview() {
  clearTimeout(wsPreviewTimer);
  wsPreviewTimer = setTimeout(renderWsPreview, 120);
}

wsWordsInput.addEventListener('input', () => { updateWsWordCount(); scheduleWsPreview(); });
wsRowsSlider.addEventListener('input', () => { updateWsStats(); scheduleWsPreview(); });
wsColsSlider.addEventListener('input', () => { updateWsStats(); scheduleWsPreview(); });
wsSeedInput.addEventListener('input',  () => {
  currentWsSeed = null;
  updateWsSeedDisplay();
  scheduleWsPreview();
});

wsDiceBtn.addEventListener('click', () => {
  wsSeedInput.value = Math.floor(Math.random() * 999999);
  currentWsSeed = parseInt(wsSeedInput.value, 10);
  updateWsSeedDisplay();
  wsDiceBtn.classList.add('spinning');
  setTimeout(() => wsDiceBtn.classList.remove('spinning'), 400);
  scheduleWsPreview();
});

async function renderWsPreview() {
  const words = getWsWords();
  if (words.length === 0) return;

  const rows  = +wsRowsSlider.value;
  const cols  = +wsColsSlider.value;
  const seedRaw = wsSeedInput.value.trim();
  const seed  = seedRaw !== '' ? parseInt(seedRaw, 10) : currentWsSeed;

  try {
    const res = await fetch('/api/preview/wordsearch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, rows, cols, seed, title: 'Preview' }),
    });

    if (!res.ok) return;
    const data = await res.json();
    currentWsSeed = data.seed_used;

    const cellColorMap = new Map();
    data.placements.forEach((pl, pIdx) => {
      pl.cells.forEach(([r, c]) => {
        cellColorMap.set(r * 1000 + c, pIdx);
      });
    });

    const wsCanvas = document.getElementById('wsCanvas');
    if (!wsCanvas) return;

    wsCanvas.style.gridTemplateColumns = `repeat(${data.cols}, 1fr)`;
    wsCanvas.style.gridTemplateRows    = `repeat(${data.rows}, 1fr)`;
    wsCanvas.innerHTML = '';

    const maxDim = Math.max(data.rows, data.cols);
    wsCanvas.style.gap = maxDim > 18 ? '1px' : '2px';

    let fontSize = '0.75rem';
    if (maxDim > 12) fontSize = '0.62rem';
    if (maxDim > 16) fontSize = '0.52rem';
    if (maxDim > 20) fontSize = '0.42rem';
    if (maxDim > 24) fontSize = '0.34rem';
    if (maxDim > 28) fontSize = '0.28rem';

    const PREVIEW_PALETTE = [
      { bg: 'rgba(56, 189, 248, 0.25)', fg: '#38bdf8' },  // Sky Blue
      { bg: 'rgba(134, 239, 172, 0.25)', fg: '#4ade80' }, // Lime Green
      { bg: 'rgba(244, 114, 182, 0.25)', fg: '#f472b6' }, // Pink
      { bg: 'rgba(253, 224, 71, 0.25)', fg: '#fde047' },  // Yellow
      { bg: 'rgba(192, 132, 252, 0.25)', fg: '#c084fc' }, // Violet
      { bg: 'rgba(251, 146, 60, 0.25)', fg: '#fb923c' },  // Orange
      { bg: 'rgba(167, 243, 208, 0.25)', fg: '#34d399' }, // Mint
      { bg: 'rgba(147, 197, 253, 0.25)', fg: '#60a5fa' }, // Blue
    ];

    for (let r = 0; r < data.rows; r++) {
      for (let c = 0; c < data.cols; c++) {
        const div = document.createElement('div');
        div.className = 'wsc';
        div.style.fontSize = fontSize;
        div.textContent = data.grid[r][c];

        const key = r * 1000 + c;
        if (cellColorMap.has(key)) {
          const pIdx = cellColorMap.get(key);
          const style = PREVIEW_PALETTE[pIdx % PREVIEW_PALETTE.length];
          div.classList.add('highlight');
          div.style.background = style.bg;
          div.style.color      = style.fg;
        }
        wsCanvas.appendChild(div);
      }
    }

    wsStatWords.textContent = data.hidden_words.length;
  } catch (err) {
    console.error('Word search preview fetch error:', err);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  CROSSWORD LOGIC
// ═══════════════════════════════════════════════════════════════════════════

function getCwWordLines() {
  return cwWordsInput.value
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0);
}

function updateCwWordCount() {
  const lines = getCwWordLines();
  const n = lines.length;
  cwWordCount.textContent = `${n} word${n !== 1 ? 's' : ''}`;
}

function updateCwSeedDisplay() {
  cwSeedDisplay.textContent = cwSeedInput.value.trim() === '' ? 'random' : cwSeedInput.value.trim();
}

let cwPreviewTimer = null;
function scheduleCwPreview() {
  clearTimeout(cwPreviewTimer);
  cwPreviewTimer = setTimeout(renderCwPreview, 150);
}

cwWordsInput.addEventListener('input', () => { updateCwWordCount(); scheduleCwPreview(); });
cwSeedInput.addEventListener('input',  () => {
  currentCwSeed = null;
  updateCwSeedDisplay();
  scheduleCwPreview();
});

cwDiceBtn.addEventListener('click', () => {
  cwSeedInput.value = Math.floor(Math.random() * 999999);
  currentCwSeed = parseInt(cwSeedInput.value, 10);
  updateCwSeedDisplay();
  cwDiceBtn.classList.add('spinning');
  setTimeout(() => cwDiceBtn.classList.remove('spinning'), 400);
  scheduleCwPreview();
});

cwToggleAnsBtn.addEventListener('click', () => {
  showCwAnswers = !showCwAnswers;
  cwToggleAnsBtn.textContent = showCwAnswers ? '🙈 Hide Answers' : '👁 Show Answers';
  renderCwPreview();
});

async function renderCwPreview() {
  const words = getCwWordLines();
  if (words.length === 0) return;

  const seedRaw = cwSeedInput.value.trim();
  const seed = seedRaw !== '' ? parseInt(seedRaw, 10) : currentCwSeed;

  try {
    const res = await fetch('/api/preview/crossword', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, seed, title: 'Preview' }),
    });

    if (!res.ok) return;
    const data = await res.json();
    currentCwSeed = data.seed_used;

    cwStatGrid.textContent   = `${data.rows}×${data.cols}`;
    cwStatPlaced.textContent = data.placed_words.length;
    cwStatAcross.textContent = data.across_placements.length;
    cwStatDown.textContent   = data.down_placements.length;

    cwCanvas.style.gridTemplateColumns = `repeat(${data.cols}, 1fr)`;
    cwCanvas.style.gridTemplateRows    = `repeat(${data.rows}, 1fr)`;
    cwCanvas.innerHTML = '';

    const maxDim = Math.max(data.rows, data.cols);
    cwCanvas.style.gap = maxDim > 18 ? '1px' : '2px';

    let fontSize = '0.75rem';
    if (maxDim > 12) fontSize = '0.62rem';
    if (maxDim > 16) fontSize = '0.52rem';
    if (maxDim > 20) fontSize = '0.42rem';
    if (maxDim > 24) fontSize = '0.34rem';

    for (let r = 0; r < data.rows; r++) {
      for (let c = 0; c < data.cols; c++) {
        const div = document.createElement('div');
        const letter = data.grid[r][c];

        if (!letter) {
          div.className = 'cwc empty';
        } else {
          div.className = 'cwc';
          div.style.fontSize = fontSize;

          const numKey = `${r},${c}`;
          if (data.cell_numbers[numKey]) {
            const numSpan = document.createElement('span');
            numSpan.className = 'cwc-num';
            numSpan.textContent = data.cell_numbers[numKey];
            div.appendChild(numSpan);
          }

          const letSpan = document.createElement('span');
          letSpan.className = 'cwc-letter';
          letSpan.textContent = showCwAnswers ? letter : '';
          div.appendChild(letSpan);
        }

        cwCanvas.appendChild(div);
      }
    }
  } catch (err) {
    console.error('Crossword preview fetch error:', err);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  SHARED BUTTON STATE + PROGRESS
// ═══════════════════════════════════════════════════════════════════════════

let isBusy = false;

function setButtonState(btn, progressWrap, progressBar, state, label) {
  btn.className = 'btn-generate' + (btn === wsGenerateBtn ? ' ws-btn' : (btn === cwGenerateBtn ? ' cw-btn' : '')) + ' ' + state;
  btn.querySelector('.btn-label').textContent = label;
  btn.disabled = (state === 'loading');
  isBusy = (state === 'loading');
}

function animateProgress(progressWrap, progressBar) {
  progressWrap.classList.add('visible');
  progressBar.style.width = '0%';
  let pct = 0;
  const fast = setInterval(() => {
    pct = Math.min(pct + (Math.random() * 8 + 3), 70);
    progressBar.style.width = pct + '%';
    if (pct >= 70) clearInterval(fast);
  }, 120);
  return fast;
}

function finishProgress(progressWrap, progressBar) {
  progressBar.style.width = '100%';
  setTimeout(() => {
    progressWrap.classList.remove('visible');
    progressBar.style.width = '0%';
  }, 600);
}

function showToast(type, title, msg, duration = 4000) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warn: '⚠️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `
    <span class="toast-icon">${icons[type] ?? '💬'}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>`;
  toastWrap.appendChild(t);
  setTimeout(() => {
    t.classList.add('leave');
    t.addEventListener('animationend', () => t.remove(), { once: true });
  }, duration);
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

// ═══════════════════════════════════════════════════════════════════════════
//  MAZE GENERATE HANDLER
// ═══════════════════════════════════════════════════════════════════════════

async function handleMazeGenerate() {
  if (isBusy) return;
  const size  = +sizeSlider.value;
  const title = mazeTitleInput.value.trim() || 'Maze Puzzle';
  const seedRaw = mazeSeedInput.value.trim();
  const seed  = seedRaw !== '' ? parseInt(seedRaw, 10) : currentMazeSeed;
  const shape = currentMazeShape;

  setButtonState(mazeGenerateBtn, mazeProgressWrap, mazeProgressBar, 'loading', 'Generating maze…');
  const fastTimer = animateProgress(mazeProgressWrap, mazeProgressBar);

  try {
    const response = await fetch(MAZE_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ size, seed, shape, title }),
    });
    clearInterval(fastTimer);

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try { const json = await response.json(); detail = json.detail ?? detail; } catch {}
      throw new Error(detail);
    }

    const blob = await response.blob();
    const dim  = size % 2 === 0 ? size + 1 : size;
    const filename = `maze_${dim}x${dim}.zip`;
    finishProgress(mazeProgressWrap, mazeProgressBar);
    triggerDownload(blob, filename);
    setButtonState(mazeGenerateBtn, mazeProgressWrap, mazeProgressBar, 'success', '✓ Download started!');
    showToast('success', 'Maze ready!', `${filename} (${(blob.size / 1024).toFixed(1)} KB) downloaded.`);
    setTimeout(() => setButtonState(mazeGenerateBtn, mazeProgressWrap, mazeProgressBar, '', 'Generate & Download'), 2500);
    renderMazePreview();

  } catch (err) {
    clearInterval(fastTimer);
    finishProgress(mazeProgressWrap, mazeProgressBar);
    setButtonState(mazeGenerateBtn, mazeProgressWrap, mazeProgressBar, 'error', '✗ Generation failed');
    showToast('error', 'Generation failed', err.message ?? 'Unknown error. Check the server logs.');
    setTimeout(() => setButtonState(mazeGenerateBtn, mazeProgressWrap, mazeProgressBar, '', 'Generate & Download'), 3000);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  WORD SEARCH GENERATE HANDLER
// ═══════════════════════════════════════════════════════════════════════════

async function handleWsGenerate() {
  if (isBusy) return;
  const words = getWsWords();
  if (words.length === 0) {
    showToast('warn', 'No words', 'Please enter at least one word (2+ letters).');
    return;
  }
  const rows  = +wsRowsSlider.value;
  const cols  = +wsColsSlider.value;
  const title = wsTitleInput.value.trim() || 'Word Search';
  const seedRaw = wsSeedInput.value.trim();
  const seed  = seedRaw !== '' ? parseInt(seedRaw, 10) : currentWsSeed;

  setButtonState(wsGenerateBtn, wsProgressWrap, wsProgressBar, 'loading', 'Generating word search…');
  const fastTimer = animateProgress(wsProgressWrap, wsProgressBar);

  try {
    const response = await fetch(WS_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, rows, cols, seed, title }),
    });
    clearInterval(fastTimer);

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try { const json = await response.json(); detail = json.detail ?? detail; } catch {}
      throw new Error(detail);
    }

    const blob = await response.blob();
    const filename = `wordsearch_${rows}x${cols}.zip`;
    finishProgress(wsProgressWrap, wsProgressBar);
    triggerDownload(blob, filename);
    setButtonState(wsGenerateBtn, wsProgressWrap, wsProgressBar, 'success', '✓ Download started!');
    showToast('success', 'Word Search ready!', `${filename} (${(blob.size / 1024).toFixed(1)} KB) downloaded.`);
    setTimeout(() => setButtonState(wsGenerateBtn, wsProgressWrap, wsProgressBar, '', 'Generate & Download'), 2500);
    renderWsPreview();

  } catch (err) {
    clearInterval(fastTimer);
    finishProgress(wsProgressWrap, wsProgressBar);
    setButtonState(wsGenerateBtn, wsProgressWrap, wsProgressBar, 'error', '✗ Generation failed');
    showToast('error', 'Generation failed', err.message ?? 'Unknown error. Check the server logs.');
    setTimeout(() => setButtonState(wsGenerateBtn, wsProgressWrap, wsProgressBar, '', 'Generate & Download'), 3000);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  CROSSWORD GENERATE HANDLER
// ═══════════════════════════════════════════════════════════════════════════

async function handleCwGenerate() {
  if (isBusy) return;
  const words = getCwWordLines();
  if (words.length === 0) {
    showToast('warn', 'No words', 'Please enter at least one word.');
    return;
  }
  const title = cwTitleInput.value.trim() || 'Crossword puzzle';
  const seedRaw = cwSeedInput.value.trim();
  const seed  = seedRaw !== '' ? parseInt(seedRaw, 10) : currentCwSeed;

  setButtonState(cwGenerateBtn, cwProgressWrap, cwProgressBar, 'loading', 'Generating crossword…');
  const fastTimer = animateProgress(cwProgressWrap, cwProgressBar);

  try {
    const response = await fetch(CW_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, seed, title }),
    });
    clearInterval(fastTimer);

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try { const json = await response.json(); detail = json.detail ?? detail; } catch {}
      throw new Error(detail);
    }

    const blob = await response.blob();
    const filename = `crossword_puzzle.zip`;
    finishProgress(cwProgressWrap, cwProgressBar);
    triggerDownload(blob, filename);
    setButtonState(cwGenerateBtn, cwProgressWrap, cwProgressBar, 'success', '✓ Download started!');
    showToast('success', 'Crossword ready!', `${filename} (${(blob.size / 1024).toFixed(1)} KB) downloaded.`);
    setTimeout(() => setButtonState(cwGenerateBtn, cwProgressWrap, cwProgressBar, '', 'Generate & Download'), 2500);
    renderCwPreview();

  } catch (err) {
    clearInterval(fastTimer);
    finishProgress(cwProgressWrap, cwProgressBar);
    setButtonState(cwGenerateBtn, cwProgressWrap, cwProgressBar, 'error', '✗ Generation failed');
    showToast('error', 'Generation failed', err.message ?? 'Unknown error. Check the server logs.');
    setTimeout(() => setButtonState(cwGenerateBtn, cwProgressWrap, cwProgressBar, '', 'Generate & Download'), 3000);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  EVENT WIRING
// ═══════════════════════════════════════════════════════════════════════════

mazeGenerateBtn.addEventListener('click', handleMazeGenerate);
wsGenerateBtn.addEventListener('click',   handleWsGenerate);
cwGenerateBtn.addEventListener('click',   handleCwGenerate);

// Keyboard shortcuts: Ctrl/Cmd+Enter
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    if (currentTab === 'maze')      handleMazeGenerate();
    else if (currentTab === 'ws')   handleWsGenerate();
    else                            handleCwGenerate();
  }
});

// ═══════════════════════════════════════════════════════════════════════════
//  INITIAL RENDER
// ═══════════════════════════════════════════════════════════════════════════

updateSliderFill(sizeSlider);
updateMazeStats();
renderMazePreview();
updateWsStats();
renderWsPreview();
updateCwWordCount();
renderCwPreview();
