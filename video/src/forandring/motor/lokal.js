import * as THREE from 'three'
import { toon, toonGradient } from './docka'

// Lokalen är låst: kundens egen verksamhet, en halvfast rekommendation. Byggs en gång per kund.
// Enkla block, men i rätt skala (meter), så att kameran och rörelserna beter sig som i verkligheten.

export const LOKALER = {
  fratelli: {
    vagg: '#f3eee5', golv: '#e6dfd2', disk: '#c7ad8a', diskskiva: '#ece5d8', ugn: '#b9603f', dorr: '#9b8b74',
  },
}

function box(w, h, d, mat, x, y, z, { cast = true, receive = true } = {}) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat)
  m.position.set(x, y, z)
  m.castShadow = cast
  m.receiveShadow = receive
  return m
}

function menyTextur() {
  const c = document.createElement('canvas')
  c.width = 512
  c.height = 256
  const g = c.getContext('2d')
  g.fillStyle = '#2b2b2b'
  g.fillRect(0, 0, 512, 256)
  g.strokeStyle = '#e9e4da'
  g.lineWidth = 7
  g.lineCap = 'round'
  const rows = [[40, 50, 300], [40, 100, 380], [40, 150, 260], [40, 200, 330]]
  for (const [x, y, w] of rows) { g.beginPath(); g.moveTo(x, y); g.lineTo(x + w, y); g.stroke(); g.beginPath(); g.moveTo(430, y); g.lineTo(470, y); g.stroke() }
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

// Ytor med textur. Riktiga lokaler har mönster (kakel, trä, puts, tegel) som analysens kamera-
// följning håller sig i; helt platta ytor gav bryggan för få punkter (inlier-andel 0,3–0,5).
// Deterministisk slump, så att samma lokal alltid ser likadan ut.
function rng(s) { return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646 }
function canvasTextur(w, h, rita, repeat = [1, 1]) {
  const c = document.createElement('canvas')
  c.width = w
  c.height = h
  rita(c.getContext('2d'), w, h)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  t.wrapS = t.wrapT = THREE.RepeatWrapping
  t.repeat.set(...repeat)
  t.anisotropy = 4
  return t
}
const brus = (g, w, h, r, styrka, n = 2500) => {
  for (let i = 0; i < n; i++) {
    const a = (r() - 0.5) * styrka
    g.fillStyle = a > 0 ? `rgba(255,255,255,${a})` : `rgba(0,0,0,${-a})`
    g.fillRect(r() * w, r() * h, 1 + r() * 2, 1 + r() * 2)
  }
}
export const TEXTURER = {
  kakel: (bas, fog) => canvasTextur(256, 256, (g, w, h) => {
    const r = rng(11)
    g.fillStyle = bas; g.fillRect(0, 0, w, h)
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = `rgba(0,0,0,${r() * 0.06})`; g.fillRect(x * 64 + 2, y * 64 + 2, 60, 60) }
    g.strokeStyle = fog; g.lineWidth = 3
    for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, h); g.stroke(); g.beginPath(); g.moveTo(0, i * 64); g.lineTo(w, i * 64); g.stroke() }
    brus(g, w, h, r, 0.12)
  }, [10, 10]),
  puts: bas => canvasTextur(512, 512, (g, w, h) => {
    const r = rng(23)
    g.fillStyle = bas; g.fillRect(0, 0, w, h)
    for (let i = 0; i < 160; i++) { g.fillStyle = `rgba(${r() > 0.5 ? '255,255,255' : '90,70,50'},${r() * 0.07})`; g.beginPath(); g.ellipse(r() * w, r() * h, 10 + r() * 40, 6 + r() * 25, r() * 3, 0, 7); g.fill() }
    brus(g, w, h, r, 0.1, 6000)
  }, [6, 2]),
  tra: (bas, ljus) => canvasTextur(512, 256, (g, w, h) => {
    const r = rng(37)
    g.fillStyle = bas; g.fillRect(0, 0, w, h)
    for (let p = 0; p < 6; p++) {
      const y0 = (p * h) / 6
      g.fillStyle = `rgba(0,0,0,${0.04 + r() * 0.06})`; g.fillRect(0, y0, w, h / 6)
      g.strokeStyle = 'rgba(60,40,20,0.35)'; g.lineWidth = 2; g.beginPath(); g.moveTo(0, y0); g.lineTo(w, y0); g.stroke()
      for (let k = 0; k < 9; k++) { g.strokeStyle = `rgba(${ljus},${0.1 + r() * 0.15})`; g.lineWidth = 1; g.beginPath(); const yy = y0 + r() * (h / 6); g.moveTo(0, yy); for (let x = 0; x <= w; x += 32) g.lineTo(x, yy + Math.sin(x / 40 + k) * 3); g.stroke() }
      g.fillStyle = 'rgba(60,40,20,0.5)'; g.beginPath(); g.ellipse(r() * w, y0 + h / 12, 6, 3, 0, 0, 7); g.fill()
    }
    brus(g, w, h, r, 0.08)
  }, [2, 1]),
  sten: bas => canvasTextur(256, 256, (g, w, h) => {
    const r = rng(41)
    g.fillStyle = bas; g.fillRect(0, 0, w, h)
    for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${r() > 0.5 ? '40,40,40' : '255,255,255'},${r() * 0.25})`; g.beginPath(); g.arc(r() * w, r() * h, 0.5 + r() * 2, 0, 7); g.fill() }
  }, [3, 1]),
  tegel: (bas, fog) => canvasTextur(256, 256, (g, w, h) => {
    const r = rng(53)
    g.fillStyle = fog; g.fillRect(0, 0, w, h)
    for (let y = 0; y < 8; y++) for (let x = -1; x < 5; x++) {
      const ox = (y % 2) * 32
      g.fillStyle = bas; g.fillRect(x * 64 + ox + 2, y * 32 + 2, 60, 28)
      g.fillStyle = `rgba(0,0,0,${r() * 0.18})`; g.fillRect(x * 64 + ox + 2, y * 32 + 2, 60, 28)
    }
    brus(g, w, h, r, 0.12)
  }, [2, 2]),
  tavla: seed => canvasTextur(256, 320, (g, w, h) => {
    const r = rng(seed)
    g.fillStyle = `hsl(${r() * 360},35%,${55 + r() * 20}%)`; g.fillRect(0, 0, w, h)
    for (let i = 0; i < 7; i++) { g.fillStyle = `hsla(${r() * 360},45%,${35 + r() * 40}%,0.85)`; g.beginPath(); g.ellipse(r() * w, r() * h, 20 + r() * 70, 20 + r() * 70, r() * 3, 0, 7); g.fill() }
  }),
}

// Var en kamera får stå: inne i rummet och inte i disken eller ugnen.
export const RUM = {
  fratelli: {
    x: [-2.6, 6], y: [0.15, 3.3], z: [-2.55, 8],
    hinder: [{ x: [0.05, 2.05], y: [0, 1.0], z: [-1.8, -1.1] }, { x: [1.95, 3.15], y: [0, 1.4], z: [-2.6, -1.6] }],
  },
}
const inom = (v, [a, b]) => v >= a && v <= b
export function kameraOk(id, p) {
  if (typeof id === 'object' && id?.scener) return kameraOkData(id, p)
  const R = typeof id === 'string' ? RUM[id] : null
  if (!R) return true
  if (!inom(p.x, R.x) || !inom(p.y, R.y) || !inom(p.z, R.z)) return false
  return !R.hinder.some(h => inom(p.x, h.x) && inom(p.y, h.y) && inom(p.z, h.z))
}

const medTextur = map => { const m = toon('#ffffff'); m.map = map; return m }

export function buildLokal(id) {
  if (typeof id === 'object') return buildLokalData(id)
  const L = LOKALER[id]
  const g = new THREE.Group()
  const m = {
    vagg: medTextur(TEXTURER.puts(L.vagg)), golv: medTextur(TEXTURER.kakel(L.golv, '#b9b0a2')), disk: medTextur(TEXTURER.tra(L.disk, '255,235,200')), skiva: medTextur(TEXTURER.sten(L.diskskiva)),
    ugn: medTextur(TEXTURER.tegel(L.ugn, '#d9c9b4')), dorr: medTextur(TEXTURER.tra(L.dorr, '230,210,180')), mork: toon('#2a2a2a'), deg: toon('#f1e4c8'), pizza: toon('#e8b27a'), tomat: toon('#c4472f'),
  }
  // golv och väggar
  const golv = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), m.golv)
  golv.rotation.x = -Math.PI / 2
  golv.receiveShadow = true
  g.add(golv)
  g.add(box(10, 3.4, 0.1, m.vagg, 0.4, 1.7, -2.65, { cast: false }))
  g.add(box(0.1, 3.4, 6, m.vagg, -2.7, 1.7, 0.3, { cast: false }))
  g.add(box(10, 0.12, 0.04, m.dorr, 0.4, 0.06, -2.58, { cast: false })) // golvlist
  // dörr i bakväggen
  g.add(box(0.98, 2.14, 0.06, m.mork, -1.6, 1.07, -2.6, { cast: false }))
  g.add(box(0.86, 2.06, 0.06, m.dorr, -1.6, 1.03, -2.57, { cast: false }))
  g.add(box(0.5, 0.6, 0.02, m.vagg, -1.6, 1.55, -2.53, { cast: false }))
  // disk
  // disk, skiva och ugn skymmer det som står bakom (motorns syn räknar med det, som MediaPipe gör)
  const diskkropp = box(1.9, 0.92, 0.6, m.disk, 1.05, 0.46, -1.45)
  diskkropp.userData.skymmer = true
  g.add(diskkropp)
  const skiva = box(2.0, 0.05, 0.7, m.skiva, 1.05, 0.945, -1.45)
  skiva.userData.coco = 'dining table' // COCO-namn, som objektdetektorn i analysen
  skiva.userData.skymmer = true
  g.add(skiva)
  g.add(box(1.9, 0.06, 0.02, m.skiva, 1.05, 0.62, -1.14))
  // deg och pizza på disken (rekvisita, låst)
  const deg = new THREE.Mesh(new THREE.SphereGeometry(0.13, 18, 10), m.deg)
  deg.scale.set(1, 0.32, 0.8)
  deg.position.set(0.85, 0.99, -1.62)
  deg.castShadow = true
  g.add(deg)
  const pizza = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.025, 28), m.pizza)
  pizza.position.set(1.55, 0.985, -1.4)
  pizza.castShadow = true
  pizza.userData.coco = 'pizza'
  g.add(pizza)
  for (const [x, z] of [[1.5, -1.36], [1.6, -1.44], [1.53, -1.47], [1.62, -1.34]]) {
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.03, 10), m.tomat)
    p.position.set(x, 0.995, z)
    g.add(p)
  }
  // ugn
  const ugnen = box(1.1, 0.8, 0.9, m.ugn, 2.55, 0.4, -2.1)
  ugnen.userData.coco = 'oven'
  ugnen.userData.skymmer = true
  g.add(ugnen)
  const kupol = new THREE.Mesh(new THREE.SphereGeometry(0.55, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), m.ugn)
  kupol.position.set(2.55, 0.8, -2.1)
  kupol.castShadow = true
  g.add(kupol)
  const lucka = new THREE.Mesh(new THREE.CircleGeometry(0.2, 20, 0, Math.PI), m.mork)
  lucka.position.set(2.55, 0.82, -1.64)
  g.add(lucka)
  g.add(box(0.16, 1.4, 0.16, m.ugn, 2.55, 1.9, -2.2))
  // meny på väggen
  const meny = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 0.65), new THREE.MeshBasicMaterial({ map: menyTextur() }))
  meny.position.set(0.95, 2.05, -2.59)
  g.add(meny)
  // lampa över disken
  g.add(box(0.012, 1.1, 0.012, m.mork, 1.05, 2.85, -1.45, { cast: false }))
  const lampa = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.18, 20, 1, true), m.mork)
  lampa.material = m.mork.clone()
  lampa.material.side = THREE.DoubleSide
  lampa.position.set(1.05, 2.25, -1.45)
  g.add(lampa)
  // tavlor och en hylla på väggarna (det man ser bakom personerna i riktiga lokaler)
  for (const [x, y, w, h, seed] of [[-0.6, 1.75, 0.55, 0.7, 7], [2.3, 2.15, 0.6, 0.45, 19], [3.4, 1.7, 0.5, 0.65, 29]]) {
    g.add(box(w + 0.06, h + 0.06, 0.03, m.mork, x, y, -2.6, { cast: false }))
    const t = new THREE.Mesh(new THREE.PlaneGeometry(w, h), medTextur(TEXTURER.tavla(seed)))
    t.position.set(x, y, -2.58)
    g.add(t)
  }
  g.add(box(1.4, 0.04, 0.25, m.disk, -0.4, 2.5, -2.5))
  for (let i = 0; i < 6; i++) g.add(box(0.1, 0.18 + (i % 3) * 0.05, 0.1, toon(['#7a9e7e', '#c9a86a', '#8c5a3c'][i % 3]), -0.95 + i * 0.2, 2.6 + (i % 3) * 0.025, -2.5))
  // fönster i sidoväggen
  g.add(box(0.04, 1.1, 1.4, m.mork, -2.64, 1.6, 0.4, { cast: false }))
  g.add(box(0.04, 1.0, 1.3, toon('#dfe8ee'), -2.62, 1.6, 0.4, { cast: false }))
  return g
}

export function buildLjus(scene) {
  scene.add(new THREE.HemisphereLight('#fffaf0', '#d8cfc0', 1.6))
  const sol = new THREE.DirectionalLight('#ffffff', 2.2)
  sol.position.set(2.5, 5, 4)
  sol.castShadow = true
  sol.shadow.mapSize.set(1024, 1024)
  sol.shadow.camera.left = -4
  sol.shadow.camera.right = 4
  sol.shadow.camera.top = 4
  sol.shadow.camera.bottom = -4
  sol.shadow.bias = -0.0008
  sol.shadow.radius = 3
  scene.add(sol)
  scene.add(sol.target)
  return sol
}

// ---------- lokal som data (rekonstruerad ur ett riktigt klipp) ----------
// { id, scener: [{ origo: [x, 0, z], golv: { farg, material }, vagg: { z, farg, material },
//                  element: [{ namn, form, pos: [x, y, z], storlek: [b, h, d], rotY, farg, material, lyser, coco, skymmer }] }] }
// Varje scen står för sig kring sitt origo (scenerna i ett riktigt klipp är filmade var för sig).
// Formerna är enkla (låda, platta, cylinder, klot) i rätt skala och färg: det som avgör hur bilden
// rör sig och hur stor plats saker tar, inte detaljerna.
const MATERIAL = {
  tra: f => TEXTURER.tra(f, '255,235,200'), sten: f => TEXTURER.sten(f), kakel: f => TEXTURER.kakel(f, '#9a948a'),
  puts: f => TEXTURER.puts(f), tegel: f => TEXTURER.tegel(f, '#d9c9b4'),
}
const texturCache = new Map()
function material(farg = '#cccccc', namn, lyser) {
  if (lyser) return new THREE.MeshBasicMaterial({ color: farg })
  if (namn && MATERIAL[namn]) {
    const nyckel = namn + farg
    if (!texturCache.has(nyckel)) texturCache.set(nyckel, MATERIAL[namn](farg))
    return medTextur(texturCache.get(nyckel))
  }
  if (namn === 'metall') return new THREE.MeshToonMaterial({ color: farg, gradientMap: toonGradient() })
  if (namn === 'glas') return new THREE.MeshBasicMaterial({ color: farg, transparent: true, opacity: 0.35 })
  return toon(farg)
}
function form(e) {
  const [b, h, d] = e.storlek
  const mat = material(e.farg, e.material, e.lyser)
  let m
  if (e.form === 'platta') m = new THREE.Mesh(new THREE.PlaneGeometry(b, h), mat)
  else if (e.form === 'cylinder') m = new THREE.Mesh(new THREE.CylinderGeometry(b / 2, b / 2, h, 20), mat)
  else if (e.form === 'klot') { m = new THREE.Mesh(new THREE.SphereGeometry(0.5, 18, 12), mat); m.scale.set(b, h, d) }
  else m = new THREE.Mesh(new THREE.BoxGeometry(b, h, d), mat)
  m.position.set(...e.pos)
  if (e.rotY) m.rotation.y = e.rotY * Math.PI / 180
  m.castShadow = e.form !== 'platta' && !e.lyser
  m.receiveShadow = true
  if (e.coco) m.userData.coco = e.coco
  if (e.skymmer) m.userData.skymmer = true
  m.name = e.namn ?? ''
  return m
}
// Projicerad bild: originalets rena skiva (utan personer) läggs på geometrin från originalkamerans
// läge, som en diaprojektor. Där projektorn inte når (utanför bilden, baksidor) syns föremålets färg.
// Belysningen finns redan i fotot, så materialet är obelyst.
const PROJ_VERT = `varying vec3 vVarld; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vVarld = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`
const PROJ_FRAG = `
uniform sampler2D karta; uniform mat4 projVP; uniform vec3 bas; uniform vec3 projPos; uniform float markera;
varying vec3 vVarld;
void main(){
  vec4 c = projVP * vec4(vVarld, 1.0);
  vec3 farg = markera > 0.5 ? vec3(1.0, 0.0, 1.0) : bas;
  if (c.w > 0.0) {
    vec2 ndc = c.xy / c.w;
    if (abs(ndc.x) <= 1.0 && abs(ndc.y) <= 1.0) farg = texture2D(karta, ndc * 0.5 + 0.5).rgb;
  }
  gl_FragColor = vec4(farg, 1.0);
  #include <colorspace_fragment>
}`
function projektor(p) {
  const cam = new THREE.PerspectiveCamera(p.fov, p.aspekt, 0.05, 100)
  cam.position.set(...p.pos)
  cam.quaternion.set(...p.q)
  cam.updateMatrixWorld(true)
  cam.updateProjectionMatrix()
  return new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse)
}
// Täckning: med markeringen på ritas det projektorn inte når i magenta (och bakgrunden sätts till
// magenta av den som mäter), så att andelen bild som originalet faktiskt såg kan räknas.
export const MARKERA = { value: 0 }
export const MAGENTA = '#ff00ff'
function projMaterial(karta, projVP, farg) {
  return new THREE.ShaderMaterial({
    uniforms: { karta: { value: karta }, projVP: { value: projVP }, bas: { value: new THREE.Color(farg ?? '#888888') }, markera: MARKERA },
    vertexShader: PROJ_VERT, fragmentShader: PROJ_FRAG,
  })
}

function buildLokalData(spec) {
  const g = new THREE.Group()
  const laddar = []
  for (const sc of spec.scener) {
    // ren skiva för scenen: allt i scenen (golv, vägg, föremål) får projektionen
    let proj = null
    if (sc.platta) {
      const karta = new THREE.Texture()
      karta.colorSpace = THREE.SRGBColorSpace
      laddar.push(new Promise(res => {
        const img = new Image()
        img.onload = () => { karta.image = img; karta.needsUpdate = true; res() }
        img.onerror = () => res()
        img.src = sc.platta.url
      }))
      proj = { karta, vp: projektor(sc.platta) }
    }
    const sattProj = m => {
      if (!proj) return m
      // dekal (modellerad scen): bilden bara på plana ytor där den hör hemma: bakväggen, golvet och
      // föremålens framsida (mot originalkameran, +z). Övriga sidor behåller föremålets färg, så att
      // scenen tål nya vinklar utan att bilden smetas ut över baksidor.
      if (sc.dekal) {
        if (m.userData.rumYta === 'sida' || m.userData.rumYta === 'tak') return m
        const farg = m.material?.color ? '#' + m.material.color.getHexString() : null
        const pm = projMaterial(proj.karta, proj.vp, farg)
        if (m.geometry.type === 'BoxGeometry' && !m.userData.rumYta) {
          const bas = m.material
          m.material = [bas, bas, pm, bas, pm, bas] // ovansida (2) och framsida (4) syns från originalkameran
        } else m.material = pm
        m.userData.projicerad = true
        return m
      }
      const farg = m.material?.color ? '#' + m.material.color.getHexString() : null
      m.material = projMaterial(proj.karta, proj.vp, farg)
      m.userData.projicerad = true
      m.castShadow = false
      return m
    }
    const scenStart = g.children.length
    const o = sc.origo ?? [0, 0, 0]
    const golv = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), material(sc.golv?.farg ?? '#d9d2c5', sc.golv?.material ?? 'kakel'))
    golv.rotation.x = -Math.PI / 2
    golv.position.set(o[0], 0, o[2] - 4)
    golv.userData.rumYta = 'golv'
    golv.receiveShadow = true
    g.add(golv)
    if (sc.vagg) {
      // hög vägg: övre delen av bilden (tak, lampor) hamnar också på den
      const v = new THREE.Mesh(new THREE.BoxGeometry(24, 7, 0.1), material(sc.vagg.farg ?? '#eeeae2', sc.vagg.material ?? 'puts'))
      v.userData.rumYta = 'vagg'
      v.position.set(o[0], 3.5, o[2] + sc.vagg.z)
      v.receiveShadow = true
      g.add(v)
    }
    if (sc.rum && sc.vagg) {
      // modellerat rum: sidoväggar och tak i väggens färg, från bakväggen till bakom kameran
      const z0 = o[2] + sc.vagg.z, z1 = o[2] + 4, d = z1 - z0, mat = material(sc.vagg.farg ?? '#eeeae2', sc.vagg.material ?? 'puts')
      for (const sx of [-4.5, 4.5]) { const w = new THREE.Mesh(new THREE.BoxGeometry(0.1, 3.4, d), mat); w.position.set(o[0] + sx, 1.7, z0 + d / 2); w.receiveShadow = true; w.userData.rumYta = 'sida'; g.add(w) }
      const tak = new THREE.Mesh(new THREE.BoxGeometry(9, 0.1, d), material('#f4f1ea'))
      tak.userData.rumYta = 'tak'
      tak.position.set(o[0], 3.4, z0 + d / 2)
      g.add(tak)
    }
    for (const e of sc.element ?? []) g.add(form(e))
    for (const m of g.children.slice(scenStart)) sattProj(m)
  }
  g.userData.laddar = Promise.all(laddar)
  return g
}

// I en lokal som data: ovanför golvet, framför bakväggen, inte inne i föremål som står på golvet.
// Scenen avgörs av närmaste origo (scenerna står 40 m isär).
function kameraOkData(spec, p) {
  if (p.y < 0.15 || p.y > 3.6) return false
  const sc = spec.scener.reduce((a, s) => (Math.abs((s.origo?.[0] ?? 0) - p.x) < Math.abs((a.origo?.[0] ?? 0) - p.x) ? s : a))
  const o = sc.origo ?? [0, 0, 0]
  if (sc.vagg && p.z < o[2] + sc.vagg.z + 0.25) return false
  for (const e of sc.element ?? []) {
    if (e.form === 'platta' || e.storlek[1] < 0.3) continue
    const [b, h, d] = e.storlek
    const m = 0.12
    if (Math.abs(p.x - e.pos[0]) < b / 2 + m && Math.abs(p.z - e.pos[2]) < d / 2 + m && p.y > e.pos[1] - h / 2 - m && p.y < e.pos[1] + h / 2 + m) return false
  }
  return true
}
