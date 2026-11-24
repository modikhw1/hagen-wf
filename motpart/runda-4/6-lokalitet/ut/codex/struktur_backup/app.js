import {Scen3DRenderer} from '/renderer.js';
import * as THREE from '/three/three.module.js';
const el = id => document.getElementById(id);
const video = el('original');
let views = [], ready = false, renderedTime = -1, fps = 30, shots = [], rapport = null, klippId = null, gen = 0;

function draw(t) {
  if (!ready) return;
  if (videoTex && video.readyState >= 2) videoTex.needsUpdate = true;  // även vid sökning i pausat läge
  let id = null;
  for (const v of views) {
    if (v.nat) {
      const tid = v.r._findActiveTagning ? v.r._findActiveTagning(t * fps)?.id : null; const rum = v.nat.get(tid)?.userData.rum; const hela = el('helarum')?.checked;
      for (const [sid, g] of v.nat) {
        g.visible = sid === tid || (hela && rum && g.userData.rum === rum && !rum.startsWith('egen_'));
        const fri = v.r.orbitMode;
        // antaget visas bara i fri kamera och egen tagning; från originalkameran syns bakgrundsduken (originalets pixlar) i stället
        const dukPa = el('duk') ? el('duk').checked : true;
        // med duk: antaget visas bara i fri kamera (originalets pixlar syns i stället); utan duk: antaget (grått) syns alltid
        for (const m of g.children) if (m.userData.antagen) m.visible = sid === tid && (fri || !dukPa);
        if (g.userData.duk) g.userData.duk.visible = sid === tid && !fri && dukPa;
      }
    }
    const s = v.r.setTime(t); if (v.id.startsWith('L') || !id) id = s.tagning_id;
    if (v.nat) {  // bakgrundsduken följer kameran för denna ruta: 40 m framför, täckande synfältet
      let synlig = false;
      for (const [, g] of v.nat) { const duk = g.userData.duk; if (duk && duk.visible) {
        const c = v.r.camera; const d = 40; const hgt = 2 * d * Math.tan(THREE.MathUtils.degToRad(c.fov / 2));
        duk.position.copy(c.position).add(new THREE.Vector3(0, 0, -d).applyQuaternion(c.quaternion));
        duk.quaternion.copy(c.quaternion); duk.scale.set(hgt * c.aspect, hgt, 1); synlig = true; } }
      if (synlig) v.r.renderFrame();
    }
  }
  renderedTime = t;
  el('clock').textContent = t.toFixed(2) + ' s'; el('seek').value = t; el('shot').textContent = (id || '—').toUpperCase();
  for (const b of el('shots').children) b.classList.toggle('active', b.dataset.shot === id);
  info(id);
}
let lastInfo = null;
function info(id) {
  if (id === lastInfo) return; lastInfo = id;
  const r = rapport?.tagningar?.[id];
  if (!r) { el('info').textContent = '—'; return; }
  const rad = [];
  rad.push(`<b>${id.toUpperCase()}</b> · lodlinje: ${r.lodlinje.kalla}. Lutning ${r.lutning_grader}°${r.A_lutning_grader != null ? ' (A ' + r.A_lutning_grader + '°)' : ''}.`);
  rad.push(`Kamerahöjd ${r.kamerahojd.m} m ur ${r.kamerahojd.kalla}${r.kamerahojd.fotter_m != null ? ` (fötterna säger ${r.kamerahojd.fotter_m} m)` : ''}. Skala: ${r.skala.kalla} (${r.skala.varde}).`);
  if (r.registrering_2d_px?.efter != null) rad.push(`Kroppens 2D-fel ${r.registrering_2d_px.fore} → ${r.registrering_2d_px.efter} px.`);
  if (r.fot_over_golv_m) rad.push('Fötter över golvet: ' + Object.entries(r.fot_over_golv_m).map(([p, v]) => p + ' ' + v + ' m').join(', ') + '.');
  if (r.dubbletter_bort) rad.push('Dubbletter borttagna: ' + r.dubbletter_bort.join(', ') + '.');
  rad.push(`Maträtter: ${r.matratter}.`);
  if (r.tillforlitlighet) rad.unshift(`<b>Tillförlitlighet: ${r.tillforlitlighet.dom}</b> · ` + r.tillforlitlighet.signaler.map(x => `${x.signal}: ${x.status} (${x.detalj})`).join(' · '));
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
el('texmode').onchange = bytTextur;
el('helarum').onchange = () => draw(video.currentTime);
el('duk').onchange = () => draw(video.currentTime);
function natCentrum(v) {  // viktad mittpunkt av aktiva tagningens bitar (orbit-centrum även utan kroppar)
  const tid = v.r._findActiveTagning?.(video.currentTime * fps)?.id; const g = v.nat.get(tid); if (!g) return null;
  const c = new THREE.Vector3(); let n = 0;
  for (const m of g.children) { m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox.getCenter(new THREE.Vector3()); const w = m.geometry.attributes.position.count; c.addScaledVector(b, w); n += w; }
  return n ? c.divideScalar(n) : null;
}
function orbit(on) {
  for (const v of views) if (v.nat) {
    v.r.setOrbitMode(on);
    if (on) { const c = natCentrum(v); if (c) { v.r.controls.target.copy(c); v.r.camera.lookAt(c); } v.r.renderFrame(); }
  }
  draw(video.currentTime);
}
el('orbit').onchange = () => orbit(el('orbit').checked);
const bitFarg = (i) => new THREE.Color().setHSL(((i * 0.6180339) % 1 + 1) % 1, 0.65, 0.55);
el('bitfarg').onchange = () => {
  for (const v of views) if (v.nat) for (const [, g] of v.nat) g.children.forEach((m, i) => {
    if (el('bitfarg').checked) { m.userData.orig = m.userData.orig || {map: m.material.map, color: m.material.color.clone()}; m.material.map = null; m.material.color = bitFarg(m.userData.instans + i); }
    else if (m.userData.orig) { m.material.map = m.userData.orig.map; m.material.color = m.userData.orig.color; }
    m.material.needsUpdate = true;
  });
  draw(video.currentTime);
};
el('uncertain').onchange = () => { for (const v of views) v.r.setShowTilltro(el('uncertain').checked); draw(video.currentTime); };
el('feedback').onsubmit = async e => {
  e.preventDefault(); el('save').disabled = true; const at = video.currentTime;
  try {
    const r = await fetch('/api/svar', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({klipp: klippId, variant: el('fvariant').value, time: at, shot: el('shot').textContent.toLowerCase(), dom: el('dom').value, comment: el('comment').value})});
    const j = await r.json(); if (!r.ok) throw Error(j.error);
    el('saved').textContent = `Sparat för ${klippId}/${el('fvariant').value} vid ${at.toFixed(2)} s.`; el('comment').value = '';
  } catch (err) { el('saved').textContent = 'Kunde inte spara: ' + err.message; } finally { el('save').disabled = false; }
};

async function load(k) {
  const token = ++gen, t0 = performance.now(); ready = false; video.pause(); klippId = k.id; lastInfo = null; rapport = null;
  for (const v of views) v.sec.remove(); views = []; el('shots').replaceChildren(); el('fvariant').replaceChildren();
  document.documentElement.style.setProperty('--n', String(k.varianter.length + 1));
  const prov = {};
  for (const [i, v] of k.varianter.entries()) {
    const data = await (await fetch(`/api/variant/${k.id}/${v.id}`)).json(); if (token !== gen) return;
    const sec = document.createElement('section');
    sec.innerHTML = `<h2><span>0${i + 2}</span> ${v.name}</h2><div class="viewport"><canvas></canvas></div><p>${v.id.startsWith('L') ? 'Samma kod på alla klipp.' : v.id === 'A' ? 'Befintlig ingest.' : 'Handkartlagd jämförelse (bara Due Piani).'}</p>`;
    el('views').append(sec);
    const r = new Scen3DRenderer(sec.querySelector('canvas')); r.setShowLabels(false); r.setShowTilltro(el('uncertain').checked);
    { // skydd: renderarens orbit-läge ritar om inifrån sin egen ändringshändelse (rekursion); omritning får inte starta i en omritning
      const orig = r.renderFrame.bind(r); let inne = false;
      r.renderFrame = () => { if (inne) return r.getSnapshot(); inne = true; try { return orig(); } finally { inne = false; } };
    }
    // texturerat lager ersätter lådorna helt; föremål i händerna har egen textur i näten (L3d maskar dem inte)
    const pk = (v.id === 'Lt' || v.id === 'Ls') ? {...data.package, objekt: []} : data.package;
    r.loadScene(pk);
    const nat = v.id === 'Lt' ? await laddaNat(k.id, r) : v.id === 'Ls' ? await laddaNat(k.id, r, 'struktur') : null; if (token !== gen) return;
    views.push({id: v.id, r, data, sec, nat}); el('fvariant').add(new Option(v.name, v.id)); prov[v.id] = data.provenance;
    if (v.id === 'L') { rapport = data.recept; shots = data.package.tagningar; fps = data.package.tidsbas.fps; }
  }
  el('fvariant').value = k.varianter.some(v => v.id === 'Lt') ? 'Lt' : 'L';
  video.src = '/media/' + k.id;
  await new Promise(res => video.addEventListener('loadeddata', res, {once: true})); if (token !== gen) return;
  el('seek').max = video.duration;
  for (const s of shots) {
    const b = document.createElement('button'); b.textContent = s.id.toUpperCase(); b.dataset.shot = s.id;
    b.onclick = () => { video.currentTime = (s.ut[0] + 0.5) / fps; }; el('shots').append(b);
  }
  ready = true; draw(0); for (const id of ['play', 'seek', 'save']) el(id).disabled = false;
  el('risk').textContent = `${k.id}: ${shots.length} tagningar. Rapporten per tagning visas under spelaren.`;
  el('provenance').textContent = JSON.stringify({proveniens: prov, rapport_L: rapport}, null, 1);
  el('timing').textContent = 'Laddat på ' + (performance.now() - t0).toFixed(0) + ' ms';
}
// Texturerade instanser: ett nät per OneFormer-instans; textur = originalvideon (levande) eller nyckelrutan (fryst).
let videoTex = null, vantar = 0; const frysta = new Map();
function textur(kid, ruta) {
  if (el('texmode').value === 'video') {
    if (!videoTex) { videoTex = new THREE.VideoTexture(video); videoTex.colorSpace = THREE.SRGBColorSpace; }
    return videoTex;
  }
  return frystTex(kid, ruta);
}
function strukturTex(kid, sid) {  // struktur/1: mittrutan (bakom personen rumshjärnans hypotes där grinden släppt den)
  const key = 'struktur/' + kid + '/' + sid;
  if (!frysta.has(key)) { vantar++; const t = new THREE.TextureLoader().load(`/media/struktur/${kid}/${sid}`, () => { vantar--; draw(video.currentTime); }, undefined, () => vantar--); t.colorSpace = THREE.SRGBColorSpace; frysta.set(key, t); }
  return frysta.get(key);
}
function genTex(kid, sid) {  // rumshjärnans genererade rum utan förgrund (hypotes)
  const key = 'gen/' + kid + '/' + sid;
  if (!frysta.has(key)) { vantar++; const t = new THREE.TextureLoader().load(`/media/fyllnad/${kid}/${sid}`, () => { vantar--; draw(video.currentTime); }, undefined, () => vantar--); t.colorSpace = THREE.SRGBColorSpace; frysta.set(key, t); }
  return frysta.get(key);
}
function frystTex(kid, ruta) {
  const key = kid + '/' + ruta;
  if (!frysta.has(key)) { vantar++; const t = new THREE.TextureLoader().load(`/media/ruta/${kid}/${ruta}`, () => { vantar--; draw(video.currentTime); }, undefined, () => vantar--); t.colorSpace = THREE.SRGBColorSpace; frysta.set(key, t); }
  return frysta.get(key);
}
async function laddaNat(kid, r, bas = 'nat') {
  const man = await (await fetch(`/api/${bas}/${kid}/manifest`)).json(); const grupper = new Map();
  for (const [sid, t] of Object.entries(man.tagningar)) {
    const buf = await (await fetch(`/api/${bas}/${kid}/${t.fil}`)).arrayBuffer(); const g = new THREE.Group(); g.name = 'NAT_' + sid; g.userData.ruta = t.ruta;
    for (const b of t.bitar) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, b.pos[0], b.pos[1] / 4), 3));
      geo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, b.uv[0], b.uv[1] / 4), 2));
      geo.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, b.ind[0], b.ind[1] / 4), 1));
      // observerad bakgrund bakom person: textur ur rutan där den syntes; antagen fyllnad: neutral grå, aldrig personens pixlar
      const mat = b.textur === 'farg' ? new THREE.MeshBasicMaterial({color: new THREE.Color(b.farg || '#8a8f94'), side: THREE.DoubleSide})
        : b.textur === 'struktur' ? new THREE.MeshBasicMaterial({map: strukturTex(kid, sid), side: THREE.DoubleSide})
        : b.textur === 'ingen' ? new THREE.MeshBasicMaterial({color: 0x6b6f73, side: THREE.DoubleSide})
        : b.textur === 'genererad' ? new THREE.MeshBasicMaterial({map: genTex(kid, sid), side: THREE.DoubleSide})
        : new THREE.MeshBasicMaterial({map: b.textur === 'fryst' ? frystTex(kid, b.textur_ruta) : (t.rorlig ? frystTex(kid, t.ruta) : textur(kid, t.ruta)), side: THREE.DoubleSide});
      mat.userData = {fast: b.textur !== 'original' || !!t.rorlig};  // struktur/farg/genererad: alltid fast  // rörlig kamera: levande video förskjuts i bild, därför fryst textur
      const m = new THREE.Mesh(geo, mat);
      m.name = `${sid}:${b.etikett}:${b.instans}`; m.userData = {etikett: b.etikett, grupp: b.grupp, instans: b.instans, antagen: b.tilltro === 'antagen' || b.tilltro === 'genererad'};
      g.add(m);
    }
    if (t.transform) { const M = new THREE.Matrix4(); M.set(...t.transform.flat()); g.applyMatrix4(M); }  // L7: gemensam ram för samma plats
    g.userData.rum = t.rum || ('egen_' + sid);
    { // bakgrundsduk: originalets pixlar långt bakom scenen i kamerans synfält (syns genom skarvar och hål från originalkameran)
      const duk = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({map: t.rorlig ? frystTex(kid, t.ruta) : textur(kid, t.ruta), depthWrite: false}));
      duk.renderOrder = -10; duk.userData = {duk: true, fast: !!t.rorlig}; duk.material.userData = {fast: !!t.rorlig}; g.userData.duk = duk; r.scene.add(duk); duk.visible = false;
    }
    g.visible = false; r.scene.add(g); grupper.set(sid, g);
  }
  return grupper;
}
function bytTextur() { for (const v of views) if (v.nat) for (const [, g] of v.nat) for (const m of g.children) { if (m.material.userData.fast) continue; m.material.map = textur(klippId, g.userData.ruta); m.material.needsUpdate = true; } draw(video.currentTime); }

window.experiment = {orbit, get vantar() { return vantar; }, get ready() { return ready; }, get renderedTime() { return renderedTime; }, get views() { return views; }, load, draw};
try {
  const lista = await (await fetch('/api/klipp')).json();
  for (const k of lista) el('klipp').add(new Option(k.id, k.id));
  el('klipp').onchange = () => load(lista.find(k => k.id === el('klipp').value)).catch(e => el('risk').textContent = e.message);
  const start = new URLSearchParams(location.search).get('klipp');
  const k0 = lista.find(k => k.id === start) || lista[0];
  if (k0) { el('klipp').value = k0.id; await load(k0); } else el('risk').textContent = 'Inga klipp med L ännu.';
} catch (e) { el('risk').textContent = 'Kunde inte öppna: ' + e.message; console.error(e); }
