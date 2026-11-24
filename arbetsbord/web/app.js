// arbetsbord/web/app.js
// Klientmotor för Förvärld Arbetsbord: API-integration (arbetsbord/1),
// millisekund-exakt tidssynkmotor (video/tal <-> Three.js <-> skärmtext/Whisper),
// Smart Kontext-LLM regi, feedback-operatör, snabbkontroller (<50 ms), K6-manus & K5.

import { Scen3DRenderer } from '/scen3d.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
};

const ENV_PRESETS = [
  { id: 'original', namn: 'Original', farg: '#5b6375' },
  { id: 'kok', namn: 'Kök', farg: '#b8c4d0' },
  { id: 'bar', namn: 'Bar', farg: '#c27a3e' },
  { id: 'uteservering', namn: 'Uteservering', farg: '#69a870' },
  { id: 'kafe', namn: 'Kafé', farg: '#c9a67a' },
  { id: 'foodtruck', namn: 'Foodtruck', farg: '#d96b4f' },
  { id: 'matsal', namn: 'Matsal', farg: '#8c6751' },
];

const FEEDBACK_DOMAR = [
  { id: 'kanns_ratt', label: 'Känns rätt', ok: true },
  { id: 'tappade_sjalen', label: 'Tappade själen', ok: false },
  { id: 'for_stel', label: 'För stel', ok: false },
  { id: 'fel_tidal_wave', label: 'Fel tidal wave', ok: false },
];

const QUICK_PROMPTS = [
  'Flytta scenen till ett restaurangkök med rostfri bänk',
  'Gör tajmingen tätare och mer snärtig',
  'Ta bort musiken så bara talet hörs och lägg 0.5 s paus i slutet',
  'Byt första skärmtexten så den passar kundens meny',
];

// ==================== APPLIKATIONSTILLSTÅND ====================
const state = {
  klippLista: [],
  kundLista: [],
  sessionId: null,
  tillstand: null,
  tidsavbildning: [],
  duration: 0,
  fps: 30,

  // Uppspelning & synk
  currentTime: 0,
  isPlaying: false,
  playbackSpeed: 1.0,
  loop: false,
  ljudLage: 'original', // 'original' | 'tal' | 'tyst'
  compareMode: 'av', // 'av' | 'bredvid' | 'overlag'
  orbitMode: false,
  showSubtitles: true,
  showTilltro: false,
  hudHidden: false,
  manusVy: 'kort', // 'kort' | 'md'
  activeSegIdx: 0,
  rafId: null,
  lastRafMs: 0,
  isScrubbing: false,
  wasPlayingBeforeScrub: false,
  busyRegi: false,
  loadedVideoUrl: null,
  loadedTalUrl: null,
  lastOrakelRes: null,
};

// DOM-referenser
const scenCanvas = $('scenCanvas');
const underlayVideo = $('underlayVideo');
const originalVideo = $('originalVideo');
const talAudio = $('talAudio');
const forvarldFrame = $('forvarldFrame');
const originalFrame = $('originalFrame');
const stageViewports = $('stageViewports');
const skarmtextLayer = $('skarmtextLayer');
const undertextBar = $('undertextBar');
const undertextPill = $('undertextPill');
const timelineTrack = $('timelineTrack');
const tlPlayhead = $('tlPlayhead');

// Initiera Three.js-renderaren
const scen3d = new Scen3DRenderer(scenCanvas);

const resizeObs = new ResizeObserver(() => {
  scen3d.resize();
  renderOverlaysAt(state.currentTime);
});
resizeObs.observe(forvarldFrame);

// ==================== HJÄLPFUNKTIONER ====================
let toastTimer = null;
function showToast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
}

function fmtSec(s) {
  const v = Math.max(0, Number(s) || 0);
  const mins = Math.floor(v / 60);
  const secs = v - mins * 60;
  return `${String(mins).padStart(2, '0')}:${secs.toFixed(2).padStart(5, '0')}`;
}

async function apiGet(path) {
  const r = await fetch(path);
  const data = await r.json().catch(() => ({}));
  if (!r.ok || data.fel) throw new Error(data.fel || `HTTP ${r.status}`);
  return data;
}

async function apiPost(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok || data.fel) throw new Error(data.fel || `HTTP ${r.status}`);
  return data;
}

function isLightHex(hex) {
  if (!hex || typeof hex !== 'string' || !/^#[0-9a-fA-F]{6}$/.test(hex)) return true;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return 0.299 * r + 0.587 * g + 0.114 * b > 140;
}

// ==================== TIDSSYNKMOTOR (SOUNDOVERLAY-EXAKT) ====================
function normalizeTidsavbildning(ts) {
  const dur = Number(ts?.klipp?.langd_s) || (ts?.scen ? ts.scen.tidsbas.antal_rutor / ts.scen.tidsbas.fps : 0) || 0;
  const raw = Array.isArray(ts?.tidsavbildning) ? ts.tidsavbildning : [];
  if (raw.length > 0) {
    return raw.map((seg) => ({
      tagning: seg.tagning || null,
      typ: seg.typ === 'hall' ? 'hall' : 'spela',
      ny_fran_s: Number(seg.ny_fran_s) || 0,
      ny_till_s: Number(seg.ny_till_s) || 0,
      orig_fran_s: Number(seg.orig_fran_s) || 0,
      orig_till_s: Number(seg.orig_till_s) || 0,
      tempo: Math.max(0.1, Number(seg.tempo) || 1.0),
    }));
  }
  if (dur > 0) {
    return [{
      tagning: ts?.tagningar?.[0]?.id || 's1',
      typ: 'spela',
      ny_fran_s: 0,
      ny_till_s: dur,
      orig_fran_s: 0,
      orig_till_s: dur,
      tempo: 1.0,
    }];
  }
  return [];
}

function findSegmentIndexAt(nyT) {
  const segs = state.tidsavbildning;
  if (!segs.length) return -1;
  for (let i = 0; i < segs.length; i++) {
    if (nyT >= segs[i].ny_fran_s - 1e-6 && nyT < segs[i].ny_till_s) return i;
  }
  if (nyT < segs[0].ny_fran_s) return 0;
  return segs.length - 1;
}

function mapNyTillOrig(nyT) {
  const idx = findSegmentIndexAt(nyT);
  if (idx < 0) return { idx: -1, seg: null, origT: nyT, isHold: false };
  const seg = state.tidsavbildning[idx];
  if (seg.typ === 'hall') {
    return { idx, seg, origT: seg.orig_fran_s, isHold: true };
  }
  const dt = Math.max(0, nyT - seg.ny_fran_s);
  const origT = Math.min(seg.orig_till_s, Math.max(seg.orig_fran_s, seg.orig_fran_s + dt * seg.tempo));
  return { idx, seg, origT, isHold: false };
}

function mapOrigTillNy(origT, seg) {
  if (!seg || seg.typ === 'hall') return seg ? seg.ny_fran_s : state.currentTime;
  const ny = seg.ny_fran_s + (origT - seg.orig_fran_s) / seg.tempo;
  return Math.min(seg.ny_till_s, Math.max(seg.ny_fran_s, ny));
}

function getActiveVideoEl() {
  return state.compareMode === 'bredvid' ? originalVideo : underlayVideo;
}

function getInactiveVideoEl() {
  return state.compareMode === 'bredvid' ? underlayVideo : originalVideo;
}

function hasUsableMedia(mediaEl) {
  return Boolean(mediaEl && mediaEl.getAttribute('src') && mediaEl.readyState >= 1);
}

function safePlay(mediaEl, allowMutedFallback = false) {
  if (!mediaEl || !mediaEl.getAttribute('src')) return;
  const p = mediaEl.play();
  if (p && typeof p.catch === 'function') {
    p.catch(() => {
      if (allowMutedFallback && !mediaEl.muted) {
        mediaEl.muted = true;
        mediaEl.play().catch(() => {});
      }
    });
  }
}

function applyAudioMuteRouting(isHold = false) {
  const activeVid = getActiveVideoEl();
  const inactiveVid = getInactiveVideoEl();

  inactiveVid.muted = true;
  if (!inactiveVid.paused) inactiveVid.pause();

  const effectiveMode = isHold ? 'tyst' : state.ljudLage;
  const hasTal = Boolean(state.tillstand?.media?.tal_url);

  if (effectiveMode === 'original') {
    activeVid.muted = false;
    talAudio.muted = true;
    if (!talAudio.paused) talAudio.pause();
  } else if (effectiveMode === 'tal' && hasTal) {
    activeVid.muted = true;
    talAudio.muted = false;
  } else {
    activeVid.muted = true;
    talAudio.muted = true;
    if (!talAudio.paused) talAudio.pause();
  }
}

function syncMediaElementsToTime(nyT, shouldPlay) {
  const { idx, seg, origT, isHold } = mapNyTillOrig(nyT);
  state.activeSegIdx = idx;

  const activeVid = getActiveVideoEl();
  const inactiveVid = getInactiveVideoEl();
  inactiveVid.pause();
  inactiveVid.muted = true;

  const rate = Math.max(0.25, Math.min(4.0, (seg?.tempo || 1.0) * state.playbackSpeed));
  applyAudioMuteRouting(isHold);

  const hasVideo = Boolean(state.tillstand?.media?.video_url);
  const hasTal = Boolean(state.tillstand?.media?.tal_url);
  const needVideoVisible =
    state.compareMode === 'bredvid' ||
    state.compareMode === 'overlag' ||
    !state.tillstand?.klipp?.har_3d;

  if (hasVideo && hasUsableMedia(activeVid)) {
    activeVid.playbackRate = rate;
    if (Math.abs((activeVid.currentTime || 0) - origT) > 0.03) {
      try {
        activeVid.currentTime = origT;
      } catch {
        // Ignorera innan metadata laddats
      }
    }
    if (shouldPlay && !isHold && (state.ljudLage === 'original' || needVideoVisible)) {
      safePlay(activeVid, true);
    } else if (!activeVid.paused) {
      activeVid.pause();
    }
  }

  if (hasTal && hasUsableMedia(talAudio)) {
    talAudio.playbackRate = rate;
    if (Math.abs((talAudio.currentTime || 0) - origT) > 0.03) {
      try {
        talAudio.currentTime = origT;
      } catch {
        // Ignorera innan metadata laddats
      }
    }
    if (shouldPlay && !isHold && state.ljudLage === 'tal') {
      safePlay(talAudio, false);
    } else if (!talAudio.paused) {
      talAudio.pause();
    }
  }
}

function startPlayback() {
  if (!state.tillstand || state.duration <= 0) return;
  if (state.currentTime >= state.duration - 0.02) {
    state.currentTime = 0;
  }
  state.isPlaying = true;
  state.lastRafMs = performance.now();
  $('playBtn').textContent = '⏸';
  syncMediaElementsToTime(state.currentTime, true);
  if (state.rafId) cancelAnimationFrame(state.rafId);
  state.rafId = requestAnimationFrame(playbackTick);
}

function pausePlayback() {
  state.isPlaying = false;
  $('playBtn').textContent = '▶';
  if (state.rafId) {
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }
  underlayVideo.pause();
  originalVideo.pause();
  talAudio.pause();
}

function togglePlayback() {
  if (state.isPlaying) pausePlayback();
  else startPlayback();
}

function advanceToNextSegmentOrStop(now) {
  const nextIdx = state.activeSegIdx + 1;
  if (nextIdx >= state.tidsavbildning.length) {
    if (state.loop) {
      state.currentTime = 0;
      state.lastRafMs = now;
      syncMediaElementsToTime(0, true);
      renderAtTime(0, false);
      return true;
    }
    state.currentTime = state.duration;
    renderAtTime(state.duration, false);
    pausePlayback();
    return false;
  }
  const nextSeg = state.tidsavbildning[nextIdx];
  state.activeSegIdx = nextIdx;
  state.currentTime = nextSeg.ny_fran_s;
  state.lastRafMs = now;
  syncMediaElementsToTime(state.currentTime, true);
  renderAtTime(state.currentTime, false);
  return true;
}

function playbackTick(now) {
  if (!state.isPlaying) return;
  const segs = state.tidsavbildning;
  if (!segs.length) {
    pausePlayback();
    return;
  }

  let idx = state.activeSegIdx;
  if (idx < 0 || idx >= segs.length) {
    idx = findSegmentIndexAt(state.currentTime);
    state.activeSegIdx = idx;
  }
  const seg = segs[idx];
  const activeVid = getActiveVideoEl();
  const hasTal = Boolean(state.tillstand?.media?.tal_url);

  // Välj master-klocka: <video> vid 'original', <audio> vid 'tal', väggklocka vid 'tyst' eller 'hall'
  let master = null;
  if (seg.typ === 'spela') {
    if (state.ljudLage === 'original' && hasUsableMedia(activeVid) && !activeVid.paused) {
      master = activeVid;
    } else if (state.ljudLage === 'tal' && hasTal && hasUsableMedia(talAudio) && !talAudio.paused) {
      master = talAudio;
    }
  }

  if (master) {
    const mTime = master.currentTime;
    if (mTime >= seg.orig_till_s - 0.01 || master.ended) {
      const cont = advanceToNextSegmentOrStop(now);
      if (cont) state.rafId = requestAnimationFrame(playbackTick);
      return;
    }
    state.currentTime = mapOrigTillNy(mTime, seg);

    // Om talAudio är master och video syns (bredvid/överlägg/2D), håll videon stramt slavad
    if (master === talAudio && hasUsableMedia(activeVid)) {
      const needVid =
        state.compareMode === 'bredvid' ||
        state.compareMode === 'overlag' ||
        !state.tillstand?.klipp?.har_3d;
      if (needVid) {
        if (activeVid.paused) safePlay(activeVid, true);
        if (Math.abs(activeVid.currentTime - mTime) > 0.05) {
          activeVid.currentTime = mTime;
        }
      }
    }
  } else {
    // Väggklocka (tyst läge, paus-segment 'hall', eller headless utan ljud)
    const dt = Math.min(0.1, Math.max(0, (now - state.lastRafMs) / 1000)) * state.playbackSpeed;
    state.currentTime += dt;
    if (state.currentTime >= seg.ny_till_s - 0.002) {
      const cont = advanceToNextSegmentOrStop(now);
      if (cont) state.rafId = requestAnimationFrame(playbackTick);
      return;
    }
    // Håll ev. synlig video i synk även i tyst läge
    if (seg.typ === 'spela' && hasUsableMedia(activeVid)) {
      const needVid =
        state.compareMode === 'bredvid' ||
        state.compareMode === 'overlag' ||
        !state.tillstand?.klipp?.har_3d;
      if (needVid) {
        const expectedOrig = seg.orig_fran_s + (state.currentTime - seg.ny_fran_s) * seg.tempo;
        if (activeVid.paused) safePlay(activeVid, true);
        if (Math.abs(activeVid.currentTime - expectedOrig) > 0.08) {
          activeVid.currentTime = expectedOrig;
        }
      }
    }
  }

  state.lastRafMs = now;
  renderAtTime(state.currentTime, false);
  state.rafId = requestAnimationFrame(playbackTick);
}

function seekTo(nyT, syncMedia = true) {
  const clamped = Math.max(0, Math.min(Number(nyT) || 0, state.duration || 0));
  state.currentTime = clamped;
  state.lastRafMs = performance.now();
  if (syncMedia) {
    syncMediaElementsToTime(clamped, state.isPlaying);
  }
  return renderAtTime(clamped, false);
}

// ==================== RENDERING AV 3D + SKÄRMTEXT + UNDERTTEXT + HUD ====================
function renderAtTime(nyT, syncVideo = false) {
  const snap = state.tillstand?.scen ? scen3d.setTime(nyT) : {
    tid_s: Number(nyT.toFixed(4)),
    ruta: Number((nyT * state.fps).toFixed(3)),
    fps: state.fps,
    antal_rutor: Math.round(state.duration * state.fps),
    tagning_id: findTagningIdAt(nyT),
    synliga_personer: [],
    orbit_lage: state.orbitMode,
    kamera: null,
  };

  if (syncVideo) {
    syncMediaElementsToTime(nyT, state.isPlaying);
  }

  renderOverlaysAt(nyT);
  updateTransportHUD(nyT, snap);
  return snap;
}

function findTagningIdAt(nyT) {
  const segIdx = findSegmentIndexAt(nyT);
  if (segIdx >= 0 && state.tidsavbildning[segIdx]?.tagning) {
    return state.tidsavbildning[segIdx].tagning;
  }
  const tags = state.tillstand?.tagningar || [];
  for (const t of tags) {
    if (t.stryk || t.ny_fran_s == null || t.ny_till_s == null) continue;
    if (nyT >= t.ny_fran_s - 1e-4 && nyT < t.ny_till_s) return t.id;
  }
  return tags.find((t) => !t.stryk)?.id || null;
}

function renderOverlaysAt(nyT) {
  const media = state.tillstand?.media;
  const frameRect = forvarldFrame.getBoundingClientRect();
  const frameH = Math.max(240, frameRect.height || 520);

  // 1. Skärmtext enligt medielager/1
  skarmtextLayer.replaceChildren();
  const texter = Array.isArray(media?.skarmtext) ? media.skarmtext : [];
  for (const item of texter) {
    if (!item || !item.text) continue;
    if (item.typ === 'scen' && !item.andrad && !item.ny) continue;
    const fran = Number(item.fran_s ?? item.fran ?? 0);
    const till = Number(item.till_s ?? item.till ?? 0);
    if (nyT < fran - 1e-4 || nyT > till + 1e-4) continue;

    const stil = item.stil || {};
    const box = Array.isArray(item.box) && item.box.length === 4 ? item.box : null;
    let cx = 0.5;
    let cy = stil.position === 'ovre' ? 0.18 : stil.position === 'nedre' ? 0.78 : 0.48;
    if (box) {
      cx = (box[0] + box[2]) / 2;
      cy = (box[1] + box[3]) / 2;
    }

    const radh = Math.max(0.02, Math.min(0.12, Number(stil.radhojd ?? stil.radhojd_rel ?? 0.036)));
    const fontPx = Math.max(12, Math.round(frameH * radh * 0.92));

    const div = el('div', 'skarmtext-item' + (item.andrad || item.ny ? ' andrad' : ''), item.text);
    div.style.left = `${(cx * 100).toFixed(2)}%`;
    div.style.top = `${(cy * 100).toFixed(2)}%`;
    div.style.fontSize = `${fontPx}px`;
    div.style.color = stil.glyffarg || '#ffffff';
    if (stil.versaler) div.style.textTransform = 'uppercase';

    if (stil.platta) {
      div.style.backgroundColor = stil.bakgrund || '#ffffff';
      if (!stil.glyffarg) {
        div.style.color = isLightHex(stil.bakgrund || '#ffffff') ? '#111111' : '#ffffff';
      }
      div.style.textShadow = 'none';
    } else {
      const kFarg = stil.kontur || (isLightHex(stil.glyffarg || '#ffffff') ? '#000000' : '#ffffff');
      const px = Math.max(1.5, Math.round(fontPx / 14));
      div.style.backgroundColor = 'transparent';
      div.style.textShadow = [
        `${-px}px ${-px}px 0 ${kFarg}`,
        `${px}px ${-px}px 0 ${kFarg}`,
        `${-px}px ${px}px 0 ${kFarg}`,
        `${px}px ${px}px 0 ${kFarg}`,
        `0 2px 8px rgba(0,0,0,0.65)`,
      ].join(', ');
    }
    skarmtextLayer.appendChild(div);
  }

  // 2. Whisper undertextremsa
  const tal = Array.isArray(media?.tal) ? media.tal : [];
  if (!state.showSubtitles || tal.length === 0) {
    undertextBar.hidden = true;
    undertextPill.replaceChildren();
    return;
  }
  const activeTal = tal.find((s) => nyT >= Number(s.fran_s ?? s.fran ?? 0) - 0.02 && nyT <= Number(s.till_s ?? s.till ?? 0) + 0.04);
  if (!activeTal || !activeTal.text) {
    undertextBar.hidden = true;
    undertextPill.replaceChildren();
    return;
  }

  undertextBar.hidden = false;
  undertextPill.replaceChildren();
  if (activeTal.talare) {
    undertextPill.appendChild(el('span', 'talare', `${activeTal.talare}:`));
  }
  if (Array.isArray(activeTal.ord) && activeTal.ord.length > 0) {
    for (let i = 0; i < activeTal.ord.length; i++) {
      const w = activeTal.ord[i];
      const sp = document.createElement('span');
      sp.textContent = (i > 0 ? ' ' : '') + (w.o ?? w.ord ?? '');
      const wf = Number(w.fran_s ?? w.fran ?? 0);
      const wt = Number(w.till_s ?? w.till ?? 0);
      if (nyT >= wf && nyT <= wt + 0.05) sp.className = 'ord-aktiv';
      undertextPill.appendChild(sp);
    }
  } else {
    undertextPill.appendChild(document.createTextNode(activeTal.text));
  }
}

function updateTransportHUD(nyT, snap) {
  const pct = state.duration > 0 ? Math.max(0, Math.min(100, (nyT / state.duration) * 100)) : 0;
  tlPlayhead.style.left = `${pct.toFixed(3)}%`;

  const ruta = Math.round(snap.ruta ?? nyT * state.fps);
  const totR = snap.antal_rutor || Math.round(state.duration * state.fps);
  $('timecodeDisplay').innerHTML =
    `${fmtSec(nyT)} <span class="dim">/ ${fmtSec(state.duration)} · R${ruta}/${totR}</span>`;

  const tid = snap.tagning_id || findTagningIdAt(nyT) || '–';
  const tagInfo = (state.tillstand?.tagningar || []).find((t) => t.id === tid);
  const linsTxt = snap.kamera?.lins_mm ? `${snap.kamera.lins_mm.toFixed(1)}mm` : (tagInfo?.lins_mm ? `${Number(tagInfo.lins_mm).toFixed(1)}mm` : '');
  const kamTyp = tagInfo?.kamera_typ || '';
  $('shotBadge').textContent = [tid, linsTxt, kamTyp].filter(Boolean).join(' · ');

  $('vpTagLeft').textContent = state.tillstand?.klipp?.har_3d
    ? `Förvärld 3D · ${tid}`
    : `Medielager · ${tid}`;
  const tilltroSuffix = state.showTilltro && state.tillstand?.klipp?.har_3d ? ' · Tilltro' : '';
  $('vpTagRight').textContent = (state.orbitMode ? 'Fri Orbit' : (linsTxt ? `1:1 · ${linsTxt}` : '1:1')) + tilltroSuffix;

  const shotBadge = $('orakelShotBadge');
  if (shotBadge) shotBadge.textContent = tid;

  // Markera aktiv tagning i tidslinje, piller och manuskort
  document.querySelectorAll('.tl-shot').forEach((node) => {
    node.classList.toggle('active', node.dataset.tagning === tid);
  });
  document.querySelectorAll('.shot-pill').forEach((node) => {
    node.classList.toggle('active', node.dataset.tagning === tid);
  });
  document.querySelectorAll('.manus-scene').forEach((node) => {
    node.classList.toggle('active', node.dataset.tagning === tid);
  });
}

// ==================== JÄMFÖRELSELÄGE & KAMERALÄGE ====================
function setCompareMode(mode) {
  const next = ['av', 'bredvid', 'overlag'].includes(mode) ? mode : 'av';
  const wasPlaying = state.isPlaying;
  if (wasPlaying) {
    underlayVideo.pause();
    originalVideo.pause();
  }
  state.compareMode = next;

  $('jamforBtn').classList.toggle('active', next === 'bredvid');
  $('overlagBtn').classList.toggle('active', next === 'overlag');
  $('opacityWrap').hidden = next !== 'overlag';

  originalFrame.hidden = next !== 'bredvid';
  stageViewports.classList.toggle('side-by-side', next === 'bredvid');

  const har3d = Boolean(state.tillstand?.klipp?.har_3d);
  if (!har3d) {
    scenCanvas.style.display = 'none';
    underlayVideo.classList.remove('hidden-video');
    underlayVideo.style.opacity = '1';
  } else if (next === 'overlag') {
    scenCanvas.style.display = 'block';
    scenCanvas.style.opacity = String(Number($('opacitySlider').value) / 100);
    underlayVideo.classList.remove('hidden-video');
    underlayVideo.style.opacity = '1';
    scen3d.setTransparentBackground(true);
  } else {
    scenCanvas.style.display = 'block';
    scenCanvas.style.opacity = '1';
    underlayVideo.classList.add('hidden-video');
    scen3d.setTransparentBackground(false);
  }

  scen3d.resize();
  syncMediaElementsToTime(state.currentTime, wasPlaying);
  renderAtTime(state.currentTime, false);
}

function setCameraMode(mode) {
  const orbit = mode === 'orbit';
  state.orbitMode = orbit;
  scen3d.setOrbitMode(orbit);
  $('kameraSeg').querySelectorAll('button').forEach((b) => {
    b.classList.toggle('active', (b.dataset.cam === 'orbit') === orbit);
  });
  $('resetCamBtn').hidden = !orbit;
  updateTransportHUD(state.currentTime, scen3d.getSnapshot());
}

function setShowTilltro(enabled) {
  const next = Boolean(enabled);
  state.showTilltro = next;
  const btn = $('tilltroToggleBtn');
  if (btn) btn.classList.toggle('active', next);
  scen3d.setShowTilltro(next);
  updateTransportHUD(state.currentTime, scen3d.getSnapshot());
  return next;
}

function updateAudioModeUI(lage) {
  state.ljudLage = lage || 'original';
  const hasTal = Boolean(state.tillstand?.media?.tal_url);
  const labelMap = { original: 'Original', tal: 'Endast tal', tyst: 'Tyst' };
  $('origAudioTag').textContent = `Ljud: ${labelMap[state.ljudLage] || state.ljudLage}`;

  $('ljudSeg').querySelectorAll('button').forEach((b) => {
    b.classList.toggle('active', b.dataset.lage === state.ljudLage);
    if (b.dataset.lage === 'tal') b.disabled = !hasTal;
  });
  $('snabbLjudRow').querySelectorAll('button').forEach((b) => {
    b.classList.toggle('active', b.dataset.lage === state.ljudLage);
    if (b.dataset.lage === 'tal') b.disabled = !hasTal;
  });
  syncMediaElementsToTime(state.currentTime, state.isPlaying);
}

// ==================== APPLICERA TILLSTÅND FRÅN BACKEND ====================
function applyTillstand(ts, resetTime = false) {
  state.tillstand = ts;
  state.sessionId = ts.session_id || state.sessionId;
  state.fps = Number(ts.klipp?.fps || ts.scen?.tidsbas?.fps || 30);
  state.duration = Number(ts.klipp?.langd_s) || (ts.scen ? ts.scen.tidsbas.antal_rutor / state.fps : 0);
  state.tidsavbildning = normalizeTidsavbildning(ts);

  // Topp-knappar & metadata
  $('angraBtn').disabled = !ts.kan_angra;
  $('aterstallBtn').disabled = !(ts.andringar && ts.andringar.length > 0);
  const k7Ok = ts.k7 ? (!ts.k7.generativt && !ts.k7.spegling) : true;
  $('k7Badge').textContent = k7Ok ? 'K7 OK' : 'K7 VARN';
  $('clipTitle').textContent = ts.klipp?.namn || ts.klipp?.nyckel || 'Klipp';

  const tema = ts.miljo_tema || ts.scen?.miljo_tema || null;
  $('envBadge').textContent = tema?.namn || tema?.id || 'Original';

  if (document.activeElement !== $('avsiktInput')) {
    $('avsiktInput').value = ts.avsikt || '';
    $('avsiktInput').classList.toggle('saved', Boolean(ts.avsikt));
  }

  // Ladda media-källor om klippet bytts
  const videoUrl = ts.media?.video_url || null;
  const talUrl = ts.media?.tal_url || null;
  if (videoUrl !== state.loadedVideoUrl) {
    state.loadedVideoUrl = videoUrl;
    if (videoUrl) {
      underlayVideo.src = videoUrl;
      originalVideo.src = videoUrl;
      underlayVideo.load();
      originalVideo.load();
    } else {
      underlayVideo.removeAttribute('src');
      originalVideo.removeAttribute('src');
    }
  }
  if (talUrl !== state.loadedTalUrl) {
    state.loadedTalUrl = talUrl;
    if (talUrl) {
      talAudio.src = talUrl;
      talAudio.load();
    } else {
      talAudio.removeAttribute('src');
    }
  }

  // Anpassa 9:16-ramarnas faktiska bildformat exakt efter klippets mått
  const bW = Number(ts.klipp?.bredd || ts.scen?.bild?.bredd || 576);
  const bH = Number(ts.klipp?.hojd || ts.scen?.bild?.hojd || 1024);
  if (bW > 0 && bH > 0) {
    forvarldFrame.style.aspectRatio = `${bW} / ${bH}`;
    originalFrame.style.aspectRatio = `${bW} / ${bH}`;
  }

  // Ladda 3D-scen eller 2D-medielagerläge (t.ex. btilltal)
  const har3d = Boolean(ts.klipp?.har_3d && ts.scen);
  $('no3dBanner').hidden = har3d;
  $('overlagBtn').disabled = !har3d;
  $('tilltroToggleBtn').disabled = !har3d;
  $('kameraSeg').querySelectorAll('button').forEach((b) => { b.disabled = !har3d; });
  if (har3d) {
    scen3d.loadScene(ts.scen, tema, ts.kropps_kontrakt || null);
    scen3d.setShowTilltro(state.showTilltro);
    if (state.compareMode === 'overlag') {
      scen3d.setTransparentBackground(true);
    }
  } else {
    scen3d.loadScene(null, tema, null);
    if (state.compareMode === 'overlag') state.compareMode = 'av';
  }

  if (resetTime) {
    state.lastOrakelRes = null;
    if ($('orakelResultat')) $('orakelResultat').hidden = true;
    resetOrakelSliders();
  }

  // Ljudläge & visningsläge
  updateAudioModeUI(ts.media?.ljud_lage || 'original');
  setCompareMode(state.compareMode);

  // Rendera DAW-tidslinje & sidopaneler
  renderTimeline();
  renderSnabbPanel(resetTime);
  renderManusPanel();
  renderK5Panel();

  // Sätt tidpunkt och rendera synkront
  const targetT = resetTime ? 0 : Math.min(state.currentTime, state.duration || 0);
  seekTo(targetT, true);
}

// ==================== TIDSLINJE-RENDERING ====================
function renderTimeline() {
  const tlShots = $('tlShots');
  const tlSpeech = $('tlSpeech');
  const shotPills = $('shotPills');
  tlShots.replaceChildren();
  tlSpeech.replaceChildren();
  shotPills.replaceChildren();

  const dur = Math.max(0.001, state.duration);
  const segs = state.tidsavbildning;
  segs.forEach((seg, idx) => {
    const left = (seg.ny_fran_s / dur) * 100;
    const width = Math.max(0.6, ((seg.ny_till_s - seg.ny_fran_s) / dur) * 100);
    const cls = ['tl-shot', idx % 2 === 1 ? 'alt' : '', seg.typ === 'hall' ? 'hall' : ''].filter(Boolean).join(' ');
    const label = seg.typ === 'hall'
      ? `⏸ ${seg.tagning || ''}`
      : `${seg.tagning || `s${idx + 1}`}${Math.abs(seg.tempo - 1) > 0.03 ? ` ${seg.tempo.toFixed(2)}×` : ''}`;
    const d = el('div', cls, label);
    d.dataset.tagning = seg.tagning || '';
    d.style.left = `${left.toFixed(3)}%`;
    d.style.width = `${width.toFixed(3)}%`;
    d.title = `${seg.tagning || ''} (${fmtSec(seg.ny_fran_s)}–${fmtSec(seg.ny_till_s)})`;
    tlShots.appendChild(d);
  });

  // Repliker & skärmtext på spår 2
  const tal = state.tillstand?.media?.tal || [];
  for (const s of tal) {
    const a = Number(s.fran_s ?? s.fran ?? 0);
    const b = Number(s.till_s ?? s.till ?? a);
    if (b <= a) continue;
    const d = el('div', 'tl-speech-seg', s.text || '');
    d.style.left = `${((a / dur) * 100).toFixed(3)}%`;
    d.style.width = `${Math.max(1, ((b - a) / dur) * 100).toFixed(3)}%`;
    d.title = `${s.talare ? s.talare + ': ' : ''}${s.text || ''}`;
    tlSpeech.appendChild(d);
  }
  const texter = state.tillstand?.media?.skarmtext || [];
  for (const x of texter) {
    if (x.typ === 'scen' && !x.andrad && !x.ny) continue;
    const a = Number(x.fran_s ?? x.fran ?? 0);
    const b = Number(x.till_s ?? x.till ?? a);
    if (b <= a) continue;
    const m = el('div', 'tl-text-mark');
    m.style.left = `${((a / dur) * 100).toFixed(3)}%`;
    m.style.width = `${Math.max(0.8, ((b - a) / dur) * 100).toFixed(3)}%`;
    m.title = `Skärmtext: "${x.text}"`;
    tlSpeech.appendChild(m);
  }

  // Hoppa-till-tagning knappar
  const tags = state.tillstand?.tagningar || [];
  for (const t of tags) {
    const p = el(
      'button',
      'shot-pill' + (t.stryk ? ' struken' : ''),
      t.stryk
        ? `${t.id} (struken)`
        : `${t.id} · ${((t.ny_till_s ?? t.orig_till_s) - (t.ny_fran_s ?? t.orig_fran_s)).toFixed(1)}s`
    );
    p.type = 'button';
    p.dataset.tagning = t.id;
    p.disabled = Boolean(t.stryk);
    p.onclick = () => {
      if (t.ny_fran_s != null) seekTo(t.ny_fran_s + 0.01, true);
    };
    shotPills.appendChild(p);
  }
}

// ==================== SNABBKONTROLLER (<50 MS) + KROPPSORAKEL & MATSHOTS ====================
const MATSHOT_RE = /\b(mat|matshot|rätt|ratt|tallrik|skål|skal|bricka|server|närbild|narbild|produkt|pasta|gelato|pizza|guacamole|kaffe|drink|dessert|burgare|taco|glass|soppa|sallad)\b/i;

function isMatshotTagning(tag, ts) {
  if (!tag) return false;
  if (tag.ar_matshot || tag.matshot) return true;
  const textBlob = [
    tag.funktion,
    tag.syfte,
    tag.anteckning,
    ...(Array.isArray(tag.k5_bar) ? tag.k5_bar : []),
  ]
    .filter(Boolean)
    .join(' ');
  if (MATSHOT_RE.test(textBlob)) return true;

  // Kontrollera om ett mat_*-objekt redan är synligt i denna tagning
  const scenTag = (ts?.scen?.tagningar || []).find((st) => st.id === tag.id);
  const ut = scenTag?.ut;
  if (Array.isArray(ut) && ut.length >= 2) {
    const objs = ts?.scen?.objekt || [];
    for (const o of objs) {
      if (!String(o.typ || '').toLowerCase().startsWith('mat_')) continue;
      const ivs = Array.isArray(o.synlig_ut) && o.synlig_ut.length ? o.synlig_ut : [[0, 1e9]];
      if (ivs.some((iv) => Math.min(ut[1], iv[1]) > Math.max(ut[0], iv[0]))) return true;
    }
  }

  // Ren närbild/insert utan synliga personer är ofta mat-/produktbild
  if (Array.isArray(tag.personer) && tag.personer.length === 0 && !tag.stryk) return true;
  return false;
}

function fmtOrakelScore(val) {
  if (val === undefined || val === null || Number.isNaN(Number(val))) return '–';
  const n = Number(val);
  if (n >= 0 && n <= 1.0001) return String(Math.round(n * 100));
  return String(Math.round(n));
}

function syncOrakelSlidersUI() {
  const sl = Number($('orakelSlapphet')?.value || 0);
  const lu = Number($('orakelLutning')?.value || 0);
  const ge = Number($('orakelGest')?.value || 1);
  if ($('orakelSlapphetVal')) $('orakelSlapphetVal').textContent = `${sl > 0 ? '+' : ''}${sl.toFixed(2)}`;
  if ($('orakelLutningVal')) $('orakelLutningVal').textContent = `${lu > 0 ? '+' : ''}${Math.round(lu)}°`;
  if ($('orakelGestVal')) $('orakelGestVal').textContent = `${ge.toFixed(2)}×`;
}

function resetOrakelSliders() {
  if ($('orakelSlapphet')) $('orakelSlapphet').value = '0';
  if ($('orakelLutning')) $('orakelLutning').value = '0';
  if ($('orakelGest')) $('orakelGest').value = '1';
  syncOrakelSlidersUI();
}

function getActiveOrakelTarget() {
  const personId = $('orakelPersonSelect')?.value || null;
  const activeTid = findTagningIdAt(state.currentTime);
  let tagningId = null;
  if (personId && activeTid) {
    const tracks = state.tillstand?.scen?.rorelse?.[personId] || [];
    const inActiveShot = tracks.some((tr) => tr.tagning === activeTid);
    if (inActiveShot) tagningId = activeTid;
  }
  return { personId, tagningId };
}

function buildKroppAttitydParams() {
  const { personId, tagningId } = getActiveOrakelTarget();
  return {
    person_id: personId,
    tagning_id: tagningId,
    slapphet_delta: Number($('orakelSlapphet')?.value || 0),
    lutning_delta_deg: Number($('orakelLutning')?.value || 0),
    gest_skala: Number($('orakelGest')?.value || 1),
  };
}

function renderOrakelResultat(orakel, opLabel = 'kropp_attityd') {
  const box = $('orakelResultat');
  if (!box || !orakel) return;
  box.hidden = false;
  box.replaceChildren();

  const rawDom = String(orakel.dom || 'rimlig').toLowerCase();
  const domCls = rawDom === 'orimlig' ? 'orimlig' : rawDom === 'delvis_rimlig' ? 'delvis_rimlig' : 'rimlig';
  const domTextMap = {
    rimlig: 'Rimlig',
    delvis_rimlig: 'Delvis rimlig',
    orimlig: 'Orimlig',
  };

  const head = el('div', 'orakel-res-head');
  const domPill = el('span', `orakel-dom ${domCls}`, domTextMap[domCls] || rawDom);
  const msStr = orakel.ms != null ? `${Number(orakel.ms).toFixed(1)} ms` : '–';
  head.append(domPill, el('span', 'orakel-res-meta', `${opLabel} · ${msStr}`));
  box.appendChild(head);

  const poang = orakel.poang || {};
  const scores = el('div', 'orakel-scores');
  for (const [label, key] of [['Fysisk', 'fysisk'], ['Kontext', 'kontext'], ['Rytm', 'rytm']]) {
    const brick = el('div', 'orakel-brick');
    brick.append(
      el('span', 'orakel-brick-label', label),
      el('span', 'orakel-brick-val', fmtOrakelScore(poang[key]))
    );
    scores.appendChild(brick);
  }
  box.appendChild(scores);

  if (orakel.tilltro_notis) {
    box.appendChild(el('div', 'orakel-notis', `Tilltro: ${orakel.tilltro_notis}`));
  }
  if (orakel.forslag_justering) {
    box.appendChild(el('div', 'orakel-hint', `Förslag: ${orakel.forslag_justering}`));
  }
  if (Array.isArray(orakel.flaggor) && orakel.flaggor.length > 0) {
    const flags = el('div', 'orakel-flags');
    for (const fl of orakel.flaggor) {
      const txt = typeof fl === 'string' ? fl : (fl.kod || fl.text || JSON.stringify(fl));
      flags.appendChild(el('span', 'orakel-flag', txt));
    }
    box.appendChild(flags);
  }
}

async function callOrakelProva(op, params) {
  if (!state.sessionId) return null;
  const t0 = performance.now();
  const res = await apiPost('/api/orakel/prova', {
    session_id: state.sessionId,
    op,
    params,
  });
  const orakel = res.orakel || res;
  if (orakel && orakel.ms == null) {
    orakel.ms = Number((performance.now() - t0).toFixed(1));
  }
  state.lastOrakelRes = orakel;
  renderOrakelResultat(orakel, op);
  return orakel;
}

function renderSnabbPanel(resetClip = false) {
  const ts = state.tillstand;
  if (!ts) return;

  // Miljöknappar
  const activeTema = (ts.miljo_tema?.id || ts.scen?.miljo_tema?.id || 'original').toLowerCase();
  const envGrid = $('envGrid');
  envGrid.replaceChildren();
  for (const p of ENV_PRESETS) {
    const b = el('button', 'env-btn' + (activeTema === p.id ? ' active' : ''));
    b.type = 'button';
    const sw = el('span', 'env-swatch');
    sw.style.background = p.farg;
    b.append(sw, document.createTextNode(p.namn));
    b.onclick = () => runQuickOp('byt_miljo', { tema: p.id });
    envGrid.appendChild(b);
  }

  // Kroppsorakel & Kinematik: person-väljare
  const har3d = Boolean(ts.klipp?.har_3d && ts.scen);
  const pSel = $('orakelPersonSelect');
  const prevPid = resetClip ? '' : pSel.value;
  const pidSet = new Set([
    ...Object.keys(ts.scen?.rorelse || {}),
    ...Object.keys(ts.scen?.personer || {}),
    ...Object.keys(ts.kropps_kontrakt?.personer || {}),
  ]);
  const pids = [...pidSet];
  pSel.replaceChildren();
  if (!pids.length) {
    pSel.appendChild(new Option('Inga 3D-personer', ''));
  } else {
    for (const pid of pids) {
      const meta = ts.scen?.personer?.[pid] || {};
      const rollTxt = meta.roll && meta.roll !== pid ? ` · ${meta.roll}` : '';
      pSel.appendChild(new Option(`Person ${pid}${rollTxt}`, pid));
    }
    if (prevPid && pids.includes(prevPid)) {
      pSel.value = prevPid;
    } else {
      const vis = scen3d.getSnapshot()?.synliga_personer || [];
      pSel.value = vis.find((p) => pids.includes(p)) || pids[0];
    }
  }
  const kroppDisabled = !har3d || !pids.length;
  for (const id of ['orakelPersonSelect', 'orakelSlapphet', 'orakelLutning', 'orakelGest', 'orakelProvaBtn', 'orakelAppliceraBtn', 'orakelHandIkBtn', 'orakelResetSlidersBtn']) {
    if ($(id)) $(id).disabled = kroppDisabled;
  }
  syncOrakelSlidersUI();

  // Matshot & Rytm: tagningsväljare med förhandsmärkta mat-tagningar
  const mSel = $('matshotTagningSelect');
  const prevMatTid = resetClip ? '' : mSel.value;
  mSel.replaceChildren();
  const tags = ts.tagningar || [];
  let firstMatId = null;
  let matCount = 0;
  for (const t of tags) {
    const isMat = isMatshotTagning(t, ts);
    if (isMat) {
      matCount++;
      if (!firstMatId && !t.stryk) firstMatId = t.id;
    }
    const matTag = isMat ? ' · ★ Mat' : '';
    const strykTag = t.stryk ? ' (struken)' : '';
    mSel.appendChild(new Option(`${t.id}${matTag}${strykTag} · ${t.kamera_typ || ''}`, t.id));
  }
  if (prevMatTid && [...mSel.options].some((o) => o.value === prevMatTid)) {
    mSel.value = prevMatTid;
  } else if (firstMatId) {
    mSel.value = firstMatId;
  }
  if ($('matshotBadge')) {
    $('matshotBadge').textContent = matCount > 0 ? `${matCount} mat` : `${tags.length} tagn`;
  }
  for (const id of ['matshotTagningSelect', 'matshotRattInput', 'matshotStilSelect', 'matshotKameraSelect', 'matshotUpdateBtn']) {
    if ($(id)) $(id).disabled = !har3d || tags.length === 0;
  }

  // Skärmtext direktredigering
  const texter = (ts.media?.skarmtext || []).filter((x) => x.typ !== 'scen' || x.andrad || x.ny);
  $('skarmtextCount').textContent = String(texter.length);
  const list = $('skarmtextEditorList');
  list.replaceChildren();
  if (!texter.length) {
    list.appendChild(el('div', 'empty-note', 'Ingen skärmtext i klippet än. Lägg till nedan.'));
  }
  for (const x of texter) {
    const row = el('div', 'text-edit-row');
    const meta = el('div', 'text-edit-meta');
    meta.append(
      el('span', '', `${x.id} · ${(x.fran_s ?? 0).toFixed(1)}–${(x.till_s ?? 0).toFixed(1)} s · ${x.stil?.position || 'mitt'}`),
      el('span', '', x.andrad ? 'ändrad' : (x.ny ? 'ny' : 'original'))
    );
    const inp = el('input');
    inp.type = 'text';
    inp.value = x.text || '';
    const saveBtn = el('button', 'btn sm prim', 'Spara');
    saveBtn.type = 'button';
    const doSave = () => {
      const val = inp.value.trim();
      if (val && val !== x.text) runQuickOp('skarmtext_byt', { id: x.id, text: val });
    };
    saveBtn.onclick = doSave;
    inp.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        doSave();
      }
    };
    const delBtn = el('button', 'btn sm danger', '×');
    delBtn.type = 'button';
    delBtn.title = 'Ta bort skärmtext';
    delBtn.onclick = () => runQuickOp('skarmtext_ta_bort', { id: x.id });

    row.append(meta, inp, saveBtn, delBtn);
    list.appendChild(row);
  }

  // Tagningsväljare
  const sel = $('snabbTagningSelect');
  const prevVal = sel.value;
  sel.replaceChildren();
  for (const t of ts.tagningar || []) {
    sel.appendChild(new Option(`${t.id}${t.stryk ? ' (struken)' : ''} · ${t.kamera_typ || ''}`, t.id));
  }
  if (prevVal && [...sel.options].some((o) => o.value === prevVal)) {
    sel.value = prevVal;
  }
}

async function runQuickOp(op, params) {
  if (!state.sessionId) return;
  try {
    const t0 = performance.now();
    const res = await apiPost('/api/operation', {
      session_id: state.sessionId,
      op,
      params,
    });
    const ms = res.utford?.ms ?? Math.round(performance.now() - t0);
    $('snabbMs').textContent = `${ms} ms`;
    applyTillstand(res.tillstand, false);
    const msg = res.utford?.beskrivning || `${op} utförd`;
    showToast(`${msg} (${ms} ms)`);
    if (res.utford?.k5_varning) {
      const kv = res.utford.k5_varning;
      const kvText = typeof kv === 'string' ? kv : kv.text;
      if (kvText) appendSysLog(`K5-notis (${op}): ${kvText}`, 'ok');
    }
    return res;
  } catch (err) {
    showToast(`Fel: ${err.message}`);
    appendSysLog(`Operation ${op} misslyckades: ${err.message}`, 'err');
  }
}

// ==================== MANUS (K6) ====================
function renderManusPanel() {
  const container = $('manusContent');
  container.replaceChildren();
  const manus = state.tillstand?.manus;
  if (!manus) {
    container.appendChild(el('div', 'empty-note', 'Inget manus laddat ännu.'));
    return;
  }

  if (state.manusVy === 'md') {
    const pre = el('pre', 'manus-md-pre', manus.md || '(tomt manus)');
    container.appendChild(pre);
    return;
  }

  // Huvudkort
  const h = manus.huvud || {};
  const headCard = el('div', 'card');
  headCard.appendChild(el('div', 'card-title', `Inspelningsmanus · ${h.klipp || state.tillstand.klipp?.namn || ''}`));
  const summary = [
    h.langd != null ? `${h.langd} s` : `${state.duration.toFixed(1)} s`,
    h.scener != null ? `${h.scener} scener` : '',
    h.musik ? `Ljud: ${h.musik}` : '',
    h.miljo ? `Miljö: ${h.miljo}` : '',
  ].filter(Boolean).join(' · ');
  headCard.appendChild(el('div', '', summary));
  if (h.karna_kort || h.handling_kort || h.avsikt) {
    headCard.appendChild(el('div', 'k5-item-why', h.avsikt ? `Avsikt: ${h.avsikt}` : (h.karna_kort || h.handling_kort)));
  }
  container.appendChild(headCard);

  // Scen för scen
  for (const sc of manus.scener || []) {
    const card = el('div', 'manus-scene' + (sc.stryk ? ' struken' : ''));
    card.dataset.tagning = sc.id || '';
    const fran = sc.fran ?? sc.ny_fran_s ?? 0;
    const till = sc.till ?? sc.ny_till_s ?? 0;
    const langd = sc.langd ?? Math.max(0, till - fran);

    const hd = el('div', 'manus-scene-head');
    hd.append(
      el('strong', '', `Scen ${sc.nr} · ${sc.id}`),
      el('span', 'badge', sc.stryk ? 'Struken' : `${Number(fran).toFixed(2)}–${Number(till).toFixed(2)} s (${Number(langd).toFixed(1)} s)`)
    );
    card.appendChild(hd);

    const kv = el('div', 'manus-kv');
    const addRow = (k, v) => {
      if (!v) return;
      kv.append(el('span', 'k', k), el('span', 'v', v));
    };
    addRow('Vem', sc.vem);
    addRow('Var', sc.var);
    addRow('Kamera', Array.isArray(sc.hur) ? sc.hur.join(', ') : sc.hur);
    addRow('Vad sägs', sc.replik_ny ? `${sc.replik_ny} (ny; orig: ${sc.sags || '–'})` : sc.sags);
    addRow('Skärmtext', Array.isArray(sc.skarmtext) && sc.skarmtext.length ? sc.skarmtext.join(' · ') : (typeof sc.skarmtext === 'string' ? sc.skarmtext : null));
    if (sc.kansla) addRow('Känsla', sc.kansla);
    if (sc.anteckning) addRow('Regi', sc.anteckning);
    card.appendChild(kv);

    if (Array.isArray(sc.andrat) && sc.andrat.length > 0) {
      card.appendChild(el('div', 'manus-andrat', sc.andrat.join(' · ')));
    }
    if (sc.instruktion) {
      card.appendChild(el('div', 'k5-item-why', sc.instruktion));
    }

    if (!sc.stryk) {
      card.onclick = () => seekTo(Number(fran) + 0.01, true);
    }
    container.appendChild(card);
  }
}

// ==================== K5 & KONTEXT ====================
function renderK5Panel() {
  const container = $('k5Content');
  container.replaceChildren();
  const ts = state.tillstand;
  if (!ts) return;

  const poster = ts.k5?.poster || [];
  const varningar = ts.k5?.varningar || [];
  const barPoster = poster.filter((p) => p.roll === 'bar');
  const ramarPoster = poster.filter((p) => p.roll === 'ramar');
  const ovrigaPoster = poster.filter((p) => p.roll !== 'bar' && p.roll !== 'ramar');

  $('k5Count').textContent = String(barPoster.length || poster.length);

  // Aktiva K5-varningar
  if (varningar.length > 0) {
    const vc = el('div', 'card');
    vc.appendChild(el('div', 'card-title', 'Aktiva K5-varningar'));
    for (const v of varningar) {
      const b = el('div', `k5-box ${v.niva || 'varning'}`, `${v.op ? `[${v.op}] ` : ''}${v.text}`);
      vc.appendChild(b);
    }
    container.appendChild(vc);
  }

  // Formatkort & Takter
  if (ts.formatkort) {
    const fk = ts.formatkort;
    const fc = el('div', 'card');
    fc.appendChild(el('div', 'card-title', `Formatkort · ${fk.typ || 'sekvens'}`));
    if (fk.karna) fc.appendChild(el('div', '', fk.karna));
    if (fk.handling && fk.handling !== fk.karna) {
      fc.appendChild(el('div', 'k5-item-why', fk.handling));
    }
    if (Array.isArray(fk.beats) && fk.beats.length > 0) {
      for (const b of fk.beats) {
        const br = el('div', 'beat-row');
        br.append(el('span', 'beat-fn', b.funktion || 'takt'), el('span', '', b.vad || ''));
        fc.appendChild(br);
      }
    }
    container.appendChild(fc);
  }

  // Kundprofil
  if (ts.kund) {
    const k = typeof ts.kund === 'string' ? { konto: ts.kund } : ts.kund;
    const kc = el('div', 'card');
    kc.appendChild(el('div', 'card-title', `Kundprofil · @${k.konto || ''}`));
    const det = [
      k.antal_klipp != null ? `${k.antal_klipp} klipp i banken` : '',
      Array.isArray(k.rum) && k.rum.length ? `Rum: ${k.rum.slice(0, 4).join(', ')}` : '',
      Array.isArray(k.produkter) && k.produkter.length ? `Produkter: ${k.produkter.slice(0, 4).join(', ')}` : '',
    ].filter(Boolean).join(' · ');
    kc.appendChild(el('div', 'k5-item-why', det || 'Aktiv kundkontext för LLM-regin.'));
    container.appendChild(kc);
  }

  // K5 Bärlista
  const buildGroup = (title, items) => {
    if (!items.length) return;
    const card = el('div', 'card');
    card.appendChild(el('div', 'card-title', `${title} (${items.length})`));
    for (const p of items) {
      const it = el('div', `k5-item ${p.roll || ''}`);
      const h = el('div', 'k5-item-head');
      const tags = Array.isArray(p.tagningar) && p.tagningar.length ? p.tagningar.join(', ') : '';
      h.append(el('span', '', p.namn || p.id), el('span', 'badge', [p.typ, tags].filter(Boolean).join(' · ')));
      it.appendChild(h);
      if (p.varfor) it.appendChild(el('div', 'k5-item-why', p.varfor));
      card.appendChild(it);
    }
    container.appendChild(card);
  };
  buildGroup('K5 · Bär meningen (bar)', barPoster);
  buildGroup('K5 · Ramar in (ramar)', ramarPoster);
  buildGroup('K5 · Brus & tillfälligt', ovrigaPoster);

  if (!poster.length) {
    const nc = el('div', 'card');
    nc.appendChild(el('div', 'card-title', 'K5 Bärlista'));
    nc.appendChild(el('div', 'empty-note', 'Ingen separat K5-bärlista för detta klipp.'));
    container.appendChild(nc);
  }

  // Ändringshistorik + K7
  const hc = el('div', 'card');
  hc.appendChild(el('div', 'card-title', `Ändringar (${(ts.andringar || []).length}) · K7-spärr`));
  if (!ts.andringar || ts.andringar.length === 0) {
    hc.appendChild(el('div', 'empty-note', 'Inga ändringar gjorda ännu (original 1:1).'));
  } else {
    for (const a of [...ts.andringar].reverse()) {
      const r = el('div', 'hist-row');
      r.append(
        el('span', '', `#${a.nr} ${a.beskrivning || a.op}`),
        el('span', 'badge', a.kalla || 'op')
      );
      hc.appendChild(r);
    }
  }
  hc.appendChild(
    el('div', 'k5-box ingen', 'K7 aktiv: Noll generativ bild/video/röst · Noll spegling (byt_hand spärrad)')
  );
  container.appendChild(hc);
}

// ==================== REGI-CHATT (SMART KONTEXT-LLM + FEEDBACK) ====================
function appendSysLog(text, kind = '') {
  const log = $('regiLogg');
  const item = el('div', `msg-sys ${kind}`, text);
  log.appendChild(item);
  item.scrollIntoView({ block: 'nearest' });
  return item;
}

function appendLlmResponseCard(res) {
  const log = $('regiLogg');
  const sv = res.llm_svar || {};
  const feedbackId = res.feedback_id || null;

  const card = el('div', 'llm-card');

  // Header
  const head = el('div', 'llm-head');
  head.append(
    el('span', '', `${sv.modell || $('modellSelect').value}${sv.via ? ` · ${sv.via}` : ''}`),
    el('span', '', sv.ms != null ? `${(sv.ms / 1000).toFixed(1)} s` : '')
  );
  card.appendChild(head);

  const body = el('div', 'llm-body');

  // Svar till CM
  if (sv.svar_till_cm) {
    body.appendChild(el('div', 'llm-svar', sv.svar_till_cm));
  }

  // Tolkning
  if (sv.tolkning) {
    const sec = el('div', 'llm-sec');
    sec.append(el('div', 'llm-sec-title', 'Tolkning'), el('div', '', sv.tolkning));
    body.appendChild(sec);
  }

  // Tidal waves över sekvensen
  if (Array.isArray(sv.tidal_waves) && sv.tidal_waves.length > 0) {
    const sec = el('div', 'llm-sec');
    sec.appendChild(el('div', 'llm-sec-title', 'Tidal waves över sekvensen'));
    const ul = document.createElement('ul');
    for (const tw of sv.tidal_waves) {
      const txt = typeof tw === 'string' ? tw : `${tw.tagning ? `[${tw.tagning}] ` : ''}${tw.effekt || tw.text || JSON.stringify(tw)}`;
      ul.appendChild(el('li', '', txt));
    }
    sec.appendChild(ul);
    body.appendChild(sec);
  }

  // Ärvs 1:1
  if (Array.isArray(sv.arver_1till1) && sv.arver_1till1.length > 0) {
    const sec = el('div', 'llm-sec');
    sec.appendChild(el('div', 'llm-sec-title', 'Ärvs 1:1'));
    const row = el('div', 'pill-row');
    for (const item of sv.arver_1till1) {
      row.appendChild(el('span', 'pill-1to1', item));
    }
    sec.appendChild(row);
    body.appendChild(sec);
  }

  // K5-varning
  if (sv.k5_varning) {
    const niva = sv.k5_varning.niva || 'ingen';
    const txt = sv.k5_varning.text || (niva === 'ingen' ? 'K5 intakt – inga bärande element skadade.' : '');
    if (txt) {
      body.appendChild(el('div', `k5-box ${niva}`, `K5 (${niva}): ${txt}`));
    }
  }

  // Kroppsbehov
  if (sv.kropp_behov) {
    const sec = el('div', 'llm-sec');
    sec.append(el('div', 'llm-sec-title', 'Kroppsbehov'), el('div', '', sv.kropp_behov));
    body.appendChild(sec);
  }

  // Kroppsorakel förhandsgranskning
  const granskning = Array.isArray(sv.orakel_granskning)
    ? sv.orakel_granskning
    : (Array.isArray(res.orakel_granskning) ? res.orakel_granskning : []);
  if (granskning.length > 0) {
    const sec = el('div', 'llm-sec');
    sec.appendChild(el('div', 'llm-sec-title', `Kroppsorakel · förhandsgranskning (${granskning.length})`));
    const row = el('div', 'pill-row');
    for (const g of granskning) {
      if (!g) continue;
      const rawDom = String(g.dom || (g.godkand === false ? 'orimlig' : 'rimlig')).toLowerCase();
      const domCls = rawDom === 'orimlig' || g.godkand === false
        ? 'orimlig'
        : rawDom === 'delvis_rimlig'
          ? 'delvis_rimlig'
          : 'rimlig';
      const icon = domCls === 'orimlig' ? '✕' : domCls === 'delvis_rimlig' ? '!' : '✓';
      let scoreVal = null;
      let scoreDetail = '';
      if (g.poang && typeof g.poang === 'object') {
        scoreVal = g.poang.total ?? g.poang.fysisk ?? null;
        scoreDetail = `F:${fmtOrakelScore(g.poang.fysisk)} K:${fmtOrakelScore(g.poang.kontext)} R:${fmtOrakelScore(g.poang.rytm)}`;
      } else if (g.poang !== undefined && g.poang !== null) {
        scoreVal = g.poang;
      }
      const scoreTxt = scoreVal !== null ? ` (${fmtOrakelScore(scoreVal)})` : '';
      const sparrTxt = g.godkand === false ? ' · spärrad' : '';
      const pill = el('span', `orakel-pill ${domCls}`, `${icon} ${g.op || 'op'} · ${rawDom}${scoreTxt}${sparrTxt}`);
      const tipParts = [scoreDetail, g.tilltro_notis, g.forslag_justering].filter(Boolean);
      if (tipParts.length) pill.title = tipParts.join(' · ');
      row.appendChild(pill);
    }
    sec.appendChild(row);
    body.appendChild(sec);
  }

  // Utförda operationer
  if (Array.isArray(sv.operationer) && sv.operationer.length > 0) {
    const sec = el('div', 'llm-sec');
    sec.appendChild(el('div', 'llm-sec-title', `Utförda operationer (${sv.operationer.length})`));
    const ol = el('div', 'op-list');
    for (const op of sv.operationer) {
      const ok = op.ok !== false && !op.fel;
      const r = el('div', 'op-row');
      r.append(
        el('span', `op-status ${ok ? 'ok' : 'fail'}`, ok ? '✓' : '✕'),
        el('span', 'op-name', op.op || 'op'),
        el('span', '', op.beskrivning || op.fel || '')
      );
      ol.appendChild(r);
    }
    sec.appendChild(ol);
    body.appendChild(sec);
  }

  card.appendChild(body);

  // Feedback-operatörsknappar
  if (feedbackId) {
    const fb = el('div', 'fb-bar');
    const statusSpan = el('span', '', '');
    const fbHead = el('div', 'fb-head');
    fbHead.append(el('span', '', 'Bedöm regin (sparas i utvärderingslogg)'), statusSpan);
    fb.appendChild(fbHead);

    const commentRow = el('div', 'fb-comment-row');
    const commentInput = el('input');
    commentInput.type = 'text';
    commentInput.placeholder = 'Valfri kort kommentar (skickas med omdömet)…';
    commentRow.appendChild(commentInput);

    const btns = el('div', 'fb-btns');
    for (const dom of FEEDBACK_DOMAR) {
      const b = el('button', 'fb-btn', dom.label);
      b.type = 'button';
      b.dataset.dom = dom.id;
      b.onclick = async () => {
        try {
          await apiPost('/api/feedback', {
            session_id: state.sessionId,
            feedback_id: feedbackId,
            dom: dom.id,
            kommentar: commentInput.value.trim(),
          });
          btns.querySelectorAll('button').forEach((x) => x.classList.remove('chosen-ok', 'chosen-warn'));
          b.classList.add(dom.ok ? 'chosen-ok' : 'chosen-warn');
          statusSpan.textContent = `Sparat: ${dom.label}`;
          showToast(`Feedback sparad: ${dom.label}`);
        } catch (err) {
          showToast(`Feedback-fel: ${err.message}`);
        }
      };
      btns.appendChild(b);
    }

    fb.append(btns, commentRow);
    card.appendChild(fb);
  }

  log.appendChild(card);
  card.scrollIntoView({ block: 'nearest' });
}

function resetRegiWelcome() {
  const log = $('regiLogg');
  log.replaceChildren();
  const intro = el('div', 'empty-note', 'Beskriv hur scenen ska bearbetas. Kontext-LLM känner till alla tagningar, repliker, skärmtexter, kameratyp och K5-bärlistan.');
  const chips = el('div', 'prompt-chips');
  for (const p of QUICK_PROMPTS) {
    const b = el('button', 'prompt-chip', p);
    b.type = 'button';
    b.onclick = () => {
      $('regiInput').value = p;
      $('regiInput').focus();
    };
    chips.appendChild(b);
  }
  log.append(intro, chips);
}

// ==================== LADDA KLIPP & INIT ====================
async function loadClip(klippNyckel, kundKonto = null) {
  pausePlayback();
  $('loadingVeil').hidden = false;
  $('laddaBtn').disabled = true;
  try {
    const res = await apiPost('/api/ladda', {
      klipp: klippNyckel,
      kund: kundKonto || null,
    });
    state.sessionId = res.session_id;
    resetRegiWelcome();
    applyTillstand(res.tillstand, true);
    showToast(`Laddade ${res.tillstand.klipp?.namn || klippNyckel}`);
    return res.tillstand;
  } catch (err) {
    showToast(`Kunde inte ladda klipp: ${err.message}`);
    appendSysLog(`Fel vid laddning: ${err.message}`, 'err');
    throw err;
  } finally {
    $('loadingVeil').hidden = true;
    $('laddaBtn').disabled = false;
  }
}

async function init() {
  try {
    const [klipp, kunder] = await Promise.all([apiGet('/api/klipp'), apiGet('/api/kunder')]);
    state.klippLista = klipp;
    state.kundLista = kunder;

    const kSel = $('klippSelect');
    kSel.replaceChildren();
    for (const k of klipp) {
      const suffix = k.har_3d ? `3D · ${Number(k.langd_s || 0).toFixed(1)}s` : `Media · ${Number(k.langd_s || 0).toFixed(1)}s`;
      kSel.appendChild(new Option(`${k.namn || k.nyckel} (${suffix})`, k.nyckel));
    }

    const cSel = $('kundSelect');
    cSel.replaceChildren(new Option('Ingen kundprofil', ''));
    for (const c of kunder) {
      cSel.appendChild(new Option(`@${c.konto} (${c.antal_klipp} klipp)`, c.konto));
    }

    // Läs URL-parametrar eller välj guacamole/notan som default
    const params = new URLSearchParams(location.search);
    const reqKlipp = params.get('klipp');
    const reqKund = params.get('kund') || '';
    const defaultKlipp =
      (reqKlipp && klipp.some((k) => k.nyckel === reqKlipp) && reqKlipp) ||
      (klipp.some((k) => k.nyckel === 'guacamole') && 'guacamole') ||
      klipp[0]?.nyckel;

    if (defaultKlipp) {
      kSel.value = defaultKlipp;
      cSel.value = reqKund;
      await loadClip(defaultKlipp, reqKund || null);
    }
  } catch (err) {
    showToast(`Startfel: ${err.message}`);
    appendSysLog(`Kunde inte ansluta till backend: ${err.message}`, 'err');
  }
}

// ==================== EVENT-LYSSNARE ====================
$('laddaBtn').onclick = () => {
  loadClip($('klippSelect').value, $('kundSelect').value || null);
};

$('angraBtn').onclick = async () => {
  if (!state.sessionId) return;
  try {
    const res = await apiPost('/api/angra', { session_id: state.sessionId });
    applyTillstand(res.tillstand, false);
    appendSysLog('Ångrade senaste ändringen.', 'ok');
    showToast('Ångrade senaste ändringen');
  } catch (err) {
    showToast(`Ångra-fel: ${err.message}`);
  }
};

$('aterstallBtn').onclick = () => runQuickOp('aterstall', {});

// Ljudlägesknappar (topplist + snabbpanel)
const onAudioClick = (e) => {
  const btn = e.target.closest('button[data-lage]');
  if (!btn || btn.disabled) return;
  const lage = btn.dataset.lage;
  updateAudioModeUI(lage);
  if (state.sessionId) {
    runQuickOp('ljud_musik', { lage });
  }
};
$('ljudSeg').onclick = onAudioClick;
$('snabbLjudRow').onclick = onAudioClick;

// Jämförelseknappar
$('jamforBtn').onclick = () => {
  setCompareMode(state.compareMode === 'bredvid' ? 'av' : 'bredvid');
};
$('overlagBtn').onclick = () => {
  setCompareMode(state.compareMode === 'overlag' ? 'av' : 'overlag');
};
$('opacitySlider').oninput = () => {
  if (state.compareMode === 'overlag') {
    scenCanvas.style.opacity = String(Number($('opacitySlider').value) / 100);
  }
};

// Kameraläge
$('kameraSeg').onclick = (e) => {
  const btn = e.target.closest('button[data-cam]');
  if (!btn || btn.disabled) return;
  setCameraMode(btn.dataset.cam);
};
$('resetCamBtn').onclick = () => {
  scen3d.resetCamera();
  setCameraMode('las');
};

// Undertexter, Tilltro & Ren bild
$('subToggleBtn').onclick = () => {
  state.showSubtitles = !state.showSubtitles;
  $('subToggleBtn').classList.toggle('active', state.showSubtitles);
  renderOverlaysAt(state.currentTime);
};
$('tilltroToggleBtn').onclick = () => {
  setShowTilltro(!state.showTilltro);
};
$('hudToggleBtn').onclick = () => {
  state.hudHidden = !state.hudHidden;
  $('hudToggleBtn').classList.toggle('active', state.hudHidden);
  stageViewports.classList.toggle('hud-hidden', state.hudHidden);
  scen3d.setShowLabels(!state.hudHidden);
};

// Transport
$('playBtn').onclick = togglePlayback;
$('prevFrameBtn').onclick = () => {
  pausePlayback();
  seekTo(state.currentTime - 1 / state.fps, true);
};
$('nextFrameBtn').onclick = () => {
  pausePlayback();
  seekTo(state.currentTime + 1 / state.fps, true);
};
$('speedSeg').onclick = (e) => {
  const btn = e.target.closest('button[data-rate]');
  if (!btn) return;
  state.playbackSpeed = Number(btn.dataset.rate) || 1.0;
  $('speedSeg').querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === btn));
  syncMediaElementsToTime(state.currentTime, state.isPlaying);
};
$('loopBtn').onclick = () => {
  state.loop = !state.loop;
  $('loopBtn').classList.toggle('active', state.loop);
};

// Tidslinjeskrubber (pointer-drag)
function timeFromPointerEvent(e) {
  const rect = timelineTrack.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / Math.max(1, rect.width)));
  return ratio * state.duration;
}
timelineTrack.addEventListener('pointerdown', (e) => {
  if (!state.tillstand || state.duration <= 0) return;
  state.isScrubbing = true;
  state.wasPlayingBeforeScrub = state.isPlaying;
  if (state.isPlaying) pausePlayback();
  timelineTrack.setPointerCapture(e.pointerId);
  seekTo(timeFromPointerEvent(e), true);
});
timelineTrack.addEventListener('pointermove', (e) => {
  if (!state.isScrubbing) return;
  seekTo(timeFromPointerEvent(e), true);
});
timelineTrack.addEventListener('pointerup', (e) => {
  if (!state.isScrubbing) return;
  state.isScrubbing = false;
  timelineTrack.releasePointerCapture(e.pointerId);
  if (state.wasPlayingBeforeScrub) startPlayback();
});

// Media metadata klar -> synka direkt
for (const mEl of [underlayVideo, originalVideo, talAudio]) {
  mEl.addEventListener('loadedmetadata', () => {
    syncMediaElementsToTime(state.currentTime, state.isPlaying);
  });
}

// Flikväxling
document.querySelectorAll('.tab-btn').forEach((btn) => {
  btn.onclick = () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach((b) => {
      const on = b === btn;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', String(on));
    });
    document.querySelectorAll('.tab-pane').forEach((p) => {
      p.classList.toggle('active', p.id === `tab-${tab}`);
    });
  };
});

// Avsikt
const saveAvsikt = async () => {
  if (!state.sessionId) return;
  const val = $('avsiktInput').value.trim();
  if (val === (state.tillstand?.avsikt || '')) return;
  try {
    const res = await apiPost('/api/avsikt', { session_id: state.sessionId, avsikt: val });
    state.tillstand = res.tillstand;
    $('avsiktInput').classList.toggle('saved', Boolean(val));
    $('avsiktStatus').textContent = 'Sparad';
    setTimeout(() => { $('avsiktStatus').textContent = ''; }, 1800);
    renderManusPanel();
  } catch (err) {
    showToast(`Avsikt-fel: ${err.message}`);
  }
};
$('avsiktInput').addEventListener('change', saveAvsikt);
$('avsiktInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    saveAvsikt();
    $('regiInput').focus();
  }
});

// Regi-formulär (Smart Kontext-LLM)
$('regiForm').onsubmit = async (e) => {
  e.preventDefault();
  if (state.busyRegi || !state.sessionId) return;
  const text = $('regiInput').value.trim();
  if (!text) return;

  state.busyRegi = true;
  $('regiInput').value = '';
  $('regiSendBtn').disabled = true;

  // Rensa startmeddelandet vid första riktiga regin
  const log = $('regiLogg');
  if (log.querySelector('.prompt-chips')) log.replaceChildren();

  const cmMsg = el('div', 'msg-cm', text);
  log.appendChild(cmMsg);
  cmMsg.scrollIntoView({ block: 'nearest' });

  const modell = $('modellSelect').value;
  const t0 = performance.now();
  const waitEl = appendSysLog(`Kontext-LLM (${modell}) analyserar scen & tidal waves…`, 'wait');
  const tick = setInterval(() => {
    waitEl.textContent = `Kontext-LLM (${modell}) analyserar scen & tidal waves… ${((performance.now() - t0) / 1000).toFixed(0)} s`;
  }, 500);

  try {
    const res = await apiPost('/api/regi', {
      session_id: state.sessionId,
      text,
      avsikt: $('avsiktInput').value.trim(),
      modell,
    });
    clearInterval(tick);
    waitEl.remove();
    appendLlmResponseCard(res);
    if (res.tillstand) {
      applyTillstand(res.tillstand, false);
    }
  } catch (err) {
    clearInterval(tick);
    waitEl.remove();
    appendSysLog(`Regi-fel: ${err.message}`, 'err');
    showToast(`Regi-fel: ${err.message}`);
  } finally {
    state.busyRegi = false;
    $('regiSendBtn').disabled = false;
    $('regiInput').focus();
  }
};

// Snabbkontroller: Kroppsorakel & Kinematik
for (const sliderId of ['orakelSlapphet', 'orakelLutning', 'orakelGest']) {
  $(sliderId).addEventListener('input', syncOrakelSlidersUI);
}
$('orakelResetSlidersBtn').onclick = () => {
  resetOrakelSliders();
};
$('orakelProvaBtn').onclick = async () => {
  const params = buildKroppAttitydParams();
  if (!params.person_id) {
    showToast('Ingen 3D-person tillgänglig');
    return;
  }
  $('orakelProvaBtn').disabled = true;
  try {
    const orakel = await callOrakelProva('kropp_attityd', params);
    if (orakel) {
      showToast(`Orakel: ${orakel.dom} (${Number(orakel.ms ?? 0).toFixed(1)} ms)`);
    }
  } catch (err) {
    showToast(`Orakel-fel: ${err.message}`);
    appendSysLog(`Orakelprov (kropp_attityd) misslyckades: ${err.message}`, 'err');
  } finally {
    $('orakelProvaBtn').disabled = false;
  }
};
$('orakelAppliceraBtn').onclick = () => {
  const params = buildKroppAttitydParams();
  if (!params.person_id) {
    showToast('Ingen 3D-person tillgänglig');
    return;
  }
  runQuickOp('kropp_attityd', params);
};
$('orakelHandIkBtn').onclick = async () => {
  const { personId, tagningId } = getActiveOrakelTarget();
  if (!personId) {
    showToast('Ingen 3D-person tillgänglig');
    return;
  }
  const params = {
    person_id: personId,
    hand: 'vanster',
    dz: 0.15,
    tagning_id: tagningId,
  };
  $('orakelHandIkBtn').disabled = true;
  try {
    const orakel = await callOrakelProva('kropp_hand_ik', params);
    if (orakel && String(orakel.dom || '').toLowerCase() === 'orimlig') {
      showToast(`Oraklet avvisade vänster hand IK: orimlig`);
      return;
    }
    await runQuickOp('kropp_hand_ik', params);
  } catch (err) {
    showToast(`Hand-IK-fel: ${err.message}`);
    appendSysLog(`Vänster hand IK misslyckades: ${err.message}`, 'err');
  } finally {
    $('orakelHandIkBtn').disabled = false;
  }
};

// Snabbkontroller: Matshot & Rytm
$('matshotForm').onsubmit = (e) => {
  e.preventDefault();
  const tagning_id = $('matshotTagningSelect').value || selectedShotId();
  if (!tagning_id) return;
  const ratt_namn = $('matshotRattInput').value.trim() || null;
  const stil = $('matshotStilSelect').value || 'tallrik';
  const kamera_rorelse = $('matshotKameraSelect').value || 'behall';
  runQuickOp('matshot_uppdatera', {
    tagning_id,
    ratt_namn,
    stil,
    kamera_rorelse,
  });
};

// Snabbkontroller: lägg till skärmtext
$('addTextForm').onsubmit = (e) => {
  e.preventDefault();
  const text = $('addTextInput').value.trim();
  if (!text) return;
  const position = $('addTextPos').value;
  const fran_s = Number($('addTextFran').value) || 0;
  const till_s = Math.max(fran_s + 0.2, Number($('addTextTill').value) || fran_s + 2.5);
  $('addTextInput').value = '';
  runQuickOp('skarmtext_lagg_till', { text, position, fran_s, till_s });
};

// Snabbkontroller: tagningsjusteringar
const selectedShotId = () => $('snabbTagningSelect').value || state.tillstand?.tagningar?.[0]?.id || 's1';
$('zoomInBtn').onclick = () => runQuickOp('kamera_justera', { tagning_id: selectedShotId(), zoom: 1.15 });
$('zoomOutBtn').onclick = () => runQuickOp('kamera_justera', { tagning_id: selectedShotId(), zoom: 0.88 });
$('stabiliseraBtn').onclick = () => runQuickOp('kamera_justera', { tagning_id: selectedShotId(), stabilisera: true });
$('tempoSlowBtn').onclick = () => runQuickOp('tidslinje_tempo', { tagning_id: selectedShotId(), tempo: 0.85 });
$('tempoNormBtn').onclick = () => runQuickOp('tidslinje_tempo', { tagning_id: selectedShotId(), tempo: 1.0 });
$('tempoFastBtn').onclick = () => runQuickOp('tidslinje_tempo', { tagning_id: selectedShotId(), tempo: 1.25 });
$('pausBtn').onclick = () => runQuickOp('tidslinje_paus', { tagning_id: selectedShotId(), sekunder: 0.6 });
$('strykBtn').onclick = () => {
  const id = selectedShotId();
  const tag = (state.tillstand?.tagningar || []).find((t) => t.id === id);
  runQuickOp('tidslinje_stryk', { tagning_id: id, aterstall: Boolean(tag?.stryk) });
};

// Snabbkontroller: lägg till objekt
$('addObjForm').onsubmit = (e) => {
  e.preventDefault();
  const typ = $('addObjTyp').value;
  const etikett = $('addObjLabel').value.trim() || undefined;
  $('addObjLabel').value = '';
  runQuickOp('objekt_lagg_till', { typ, etikett });
};

// Manus (K6) knappar
$('manusVySeg').onclick = (e) => {
  const btn = e.target.closest('button[data-vy]');
  if (!btn) return;
  state.manusVy = btn.dataset.vy;
  $('manusVySeg').querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === btn));
  renderManusPanel();
};
$('copyManusBtn').onclick = async () => {
  const md = state.tillstand?.manus?.md || '';
  if (!md) return;
  try {
    await navigator.clipboard.writeText(md);
    showToast('Manus kopierat som Markdown');
  } catch {
    showToast('Kunde inte kopiera till urklipp');
  }
};
$('dlManusBtn').onclick = () => {
  const md = state.tillstand?.manus?.md || '';
  if (!md) return;
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${state.tillstand?.klipp?.nyckel || 'klipp'}_manus.md`;
  a.click();
  URL.revokeObjectURL(a.href);
};

// Tangentbordsgenvägar (ej när textfält har fokus)
window.addEventListener('keydown', (e) => {
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  if (e.code === 'Space') {
    e.preventDefault();
    togglePlayback();
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault();
    pausePlayback();
    seekTo(state.currentTime - (e.shiftKey ? 10 : 1) / state.fps, true);
  } else if (e.code === 'ArrowRight') {
    e.preventDefault();
    pausePlayback();
    seekTo(state.currentTime + (e.shiftKey ? 10 : 1) / state.fps, true);
  } else if (e.code === 'KeyO' && state.tillstand?.klipp?.har_3d) {
    setCameraMode(state.orbitMode ? 'las' : 'orbit');
  } else if (e.code === 'KeyR' && state.tillstand?.klipp?.har_3d) {
    scen3d.resetCamera();
    setCameraMode('las');
  }
});

// ==================== PLAYWRIGHT / SOUNDOVERLAY DEBUG API ====================
window.__arbetsbordDebug = {
  setTime(s) {
    pausePlayback();
    return seekTo(Number(s) || 0, true);
  },
  renderFrame() {
    return state.tillstand?.scen ? scen3d.renderFrame() : renderAtTime(state.currentTime, false);
  },
  getState() {
    const visibleTexts = [...skarmtextLayer.querySelectorAll('.skarmtext-item')].map((n) => n.textContent);
    return {
      session_id: state.sessionId,
      klipp: state.tillstand?.klipp || null,
      tid_s: Number(state.currentTime.toFixed(4)),
      ruta: Number((state.currentTime * state.fps).toFixed(3)),
      fps: state.fps,
      langd_s: state.duration,
      isPlaying: state.isPlaying,
      ljud_lage: state.ljudLage,
      compareMode: state.compareMode,
      orbitMode: state.orbitMode,
      showTilltro: state.showTilltro,
      activeTagningId: findTagningIdAt(state.currentTime),
      skarmtext_synliga: visibleTexts,
      undertext: undertextBar.hidden ? '' : undertextPill.textContent,
      snapshot: state.tillstand?.scen ? scen3d.getSnapshot() : null,
      tillstand: state.tillstand,
    };
  },
  setCameraMode(mode) {
    setCameraMode(mode);
    return scen3d.getSnapshot();
  },
  setCompareMode(mode) {
    setCompareMode(mode);
    return state.compareMode;
  },
  setAudioMode(lage) {
    updateAudioModeUI(lage);
    return state.ljudLage;
  },
  setShowTilltro(enabled) {
    return setShowTilltro(enabled);
  },
  async provaOrakel(op, params) {
    return await callOrakelProva(op, params);
  },
  setHudHidden(hidden) {
    state.hudHidden = Boolean(hidden);
    $('hudToggleBtn').classList.toggle('active', state.hudHidden);
    stageViewports.classList.toggle('hud-hidden', state.hudHidden);
    scen3d.setShowLabels(!state.hudHidden);
    return state.hudHidden;
  },
  async loadClip(klipp, kund = null) {
    $('klippSelect').value = klipp;
    if (kund !== null) $('kundSelect').value = kund;
    return await loadClip(klipp, kund);
  },
  async runOperation(op, params) {
    return await runQuickOp(op, params);
  },
  getCanvasDataURL() {
    if (state.tillstand?.scen) scen3d.renderFrame();
    return scenCanvas.toDataURL('image/png');
  },
};

init();
