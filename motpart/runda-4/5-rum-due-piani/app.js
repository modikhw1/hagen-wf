import {Scen3DRenderer} from '/renderer.js';
const el = id => document.getElementById(id);
const video = el('original');
const FOKUS = {s2: 'fokus', s8: 'fokus', s10: 'fokus', s1: 'kontroll'};
const views = [];
let ready = false, renderedTime = -1, fps = 30, shots = [], recept = null;

function draw(t) {
  if (!ready) return;
  let id = null;
  for (const v of views) { const s = v.r.setTime(t); id = s.tagning_id; }
  renderedTime = t;
  el('clock').textContent = t.toFixed(2) + ' s'; el('seek').value = t; el('shot').textContent = (id || '—').toUpperCase();
  for (const b of el('shots').children) b.classList.toggle('active', b.dataset.shot === id);
  info(id);
}
let lastInfo = null;
function info(id) {
  if (id === lastInfo) return; lastInfo = id;
  const r = recept?.tagningar?.[id];
  if (!r) { el('info').textContent = '—'; return; }
  const rad = [];
  rad.push(`<b>${id.toUpperCase()}</b> · regler ${r.regler.join(', ')}`);
  rad.push(`Kameralutning A ${r.A_lutning_grader}° → B ${r.B_lutning_grader}°. A:s kamera ${r.A_kamera === 'rorlig' ? 'åkte ' + r.A_framat_m + ' m framåt (schablon)' : 'stod still'}; B står still.`);
  const m = r.bildmatning; rad.push(`Bildmätning i originalet: skala ${m.skala_forsta_till_sista} första→sista ruta, mittförflyttning ${m.mitt_forflyttning_px.join(' / ')} px.`);
  if (r.registrering_2d_px?.efter != null) rad.push(`Kroppens 2D-fel mot originalets leder: ${r.registrering_2d_px.fore} px → ${r.registrering_2d_px.efter} px (median).`);
  if (r.lodlinje) rad.push('Lodlinje: ' + r.lodlinje + '.');
  if (r.dubbletter_bort) rad.push(`Dubbletter av samma person borttagna: ${r.dubbletter_bort.join(', ')}.`);
  if (r.avstand_kamera_foremal_m) rad.push(`Avstånd kamera–föremål ${r.avstand_kamera_foremal_m} m (ur ellips och antagen diameter).`);
  if (r.matratt) rad.push('Maträtt: ' + r.matratt + '.');
  el('info').innerHTML = '<ul>' + rad.map(x => '<li>' + x + '</li>').join('') + '</ul>';
}
function tick(_, md) { if (!video.seeking) draw(video.paused ? video.currentTime : md.mediaTime); video.requestVideoFrameCallback(tick); }
video.requestVideoFrameCallback(tick);
video.addEventListener('seeked', () => draw(video.currentTime));
video.addEventListener('play', () => el('play').textContent = 'Pausa');
video.addEventListener('pause', () => el('play').textContent = 'Spela');
el('play').onclick = () => video.paused ? video.play() : video.pause();
el('seek').oninput = () => { video.currentTime = Number(el('seek').value); };
el('slow').onchange = () => { video.playbackRate = el('slow').checked ? 0.5 : 1; };
el('uncertain').onchange = () => { for (const v of views) v.r.setShowTilltro(el('uncertain').checked); draw(video.currentTime); };

el('feedback').onsubmit = async e => {
  e.preventDefault(); el('save').disabled = true; const at = video.currentTime;
  try {
    const r = await fetch('/api/svar', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({variant: el('fvariant').value, time: at, shot: el('shot').textContent.toLowerCase(), dom: el('dom').value, comment: el('comment').value})});
    const j = await r.json(); if (!r.ok) throw Error(j.error);
    el('saved').textContent = `Sparat för ${el('fvariant').value} vid ${at.toFixed(2)} s.`; el('comment').value = '';
  } catch (err) { el('saved').textContent = 'Kunde inte spara: ' + err.message; } finally { el('save').disabled = false; }
};

window.experiment = {get ready() { return ready; }, get renderedTime() { return renderedTime; }, views, draw};
try {
  const t0 = performance.now();
  const list = await (await fetch('/api/varianter')).json();
  document.documentElement.style.setProperty('--n', String(list.length + 1));
  const prov = {};
  for (const [i, v] of list.entries()) {
    const data = await (await fetch('/api/variant/' + v.id)).json();
    const sec = document.createElement('section');
    sec.innerHTML = `<h2><span>0${i + 2}</span> ${v.name}</h2><div class="viewport"><canvas data-variant="${v.id}"></canvas></div><p>${v.id === 'A' ? 'Befintlig ingest, oförändrad.' : 'Samma kroppsspår och renderare som A.'}</p>`;
    el('views').append(sec);
    const r = new Scen3DRenderer(sec.querySelector('canvas'));
    r.setShowLabels(false); r.setShowTilltro(true); r.loadScene(data.package);
    views.push({id: v.id, r, data});
    el('fvariant').add(new Option(v.name, v.id));
    prov[v.id] = data.provenance;
    if (v.id === 'B') recept = data.recept;
    if (v.id === 'A') { shots = data.package.tagningar; fps = data.package.tidsbas.fps; }
  }
  el('fvariant').value = 'B';
  for (const s of shots) {
    const b = document.createElement('button'); b.textContent = s.id.toUpperCase() + (FOKUS[s.id] === 'kontroll' ? ' (kontroll)' : '');
    b.dataset.shot = s.id; if (FOKUS[s.id]) b.classList.add(FOKUS[s.id]);
    b.onclick = () => { video.currentTime = (s.ut[0] + 0.5) / fps; };
    el('shots').append(b);
  }
  if (video.readyState < 2) await new Promise(res => video.addEventListener('loadeddata', res, {once: true}));
  ready = true; draw(0);
  for (const id of ['play', 'seek', 'save']) el(id).disabled = false;
  el('risk').textContent = 'B använder manuell kartläggning av tallrik/panna i S2, S8 och S10 (diagnostiskt) och antagna mått: bänkhöjd 0,90 m, tallrik 0,30 m, panna 0,34 m. Cyan = antaget.';
  el('provenance').textContent = JSON.stringify({proveniens: prov, recept_B: recept}, null, 1);
  el('timing').textContent = 'Laddat på ' + (performance.now() - t0).toFixed(0) + ' ms';
} catch (e) { el('risk').textContent = 'Kunde inte öppna: ' + e.message; console.error(e); }
