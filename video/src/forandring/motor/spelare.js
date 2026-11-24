import * as THREE from 'three'
import { kontur, KONTUR } from './kontur'
import { INDEX } from './skelett'
import { ORDBOK } from './ordbok'
import { sampleSemantic, sampleJoints, toQuats } from './pose'
import { buildDocka, FIGURER } from './docka'
import { buildLokal, buildLjus } from './lokal'
import { evalKamera, applyKamera } from './kamera'

// Spelaren: manus + tid → bild. Helt deterministisk: samma t ger samma bild, oavsett vad som
// spelades innan. Det gör att samma kod kan förhandsvisa live, rendera till video och mätas.

const D = THREE.MathUtils.DEG2RAD
const BLEND = 0.25 // sekunder mellan två rörelser för samma roll

export function tidslinje(manus) {
  let t = 0
  return manus.scener.map((s, i) => {
    const r = { i, start: t, slut: t + s.tid, tid: s.tid, in: i === 0 ? null : (s.in ?? { typ: 'klipp' }) }
    t += s.tid
    return r
  })
}
export const langd = manus => manus.scener.reduce((a, s) => a + s.tid, 0)

// En rolls pose vid scentid u: senaste handlingen som har börjat, mjukt övertonad från den förra.
// rorelser: manusets egna rörelser (rekonstruerade ur ett riktigt klipp), före ordboken.
function rollPose(handlingar, u, rorelser = null) {
  const sorted = handlingar.slice().sort((a, b) => a.start - b.start)
  let k = sorted.findLastIndex(h => h.start <= u)
  if (k < 0) k = 0
  const one = h => {
    const clip = rorelser?.[h.rorelse] ?? ORDBOK[h.rorelse]
    const tl = Math.max(0, u - h.start) * (h.tempo ?? 1)
    const amp = h.amp ?? 1
    let q, lift = 0
    if (clip.typ === 'semantisk') {
      const p = sampleSemantic(clip, tl, amp)
      q = toQuats(p)
      lift = p.lift
    } else q = sampleJoints(clip, tl, amp)
    // plats och riktning
    let x, z, yaw = h.riktning
    if (h.bana) {
      // bana per ruta: [x, z, gir, lyft], samma tid som rörelsen (tempo gäller båda)
      const B = h.bana.ramar
      const xx = Math.max(0, Math.min(B.length - 1, tl * h.bana.fps))
      const i0 = Math.floor(xx), i1 = Math.min(B.length - 1, i0 + 1), f = xx - i0
      const L = k => B[i0][k] + (B[i1][k] - B[i0][k]) * f
      x = L(0); z = L(1); yaw = L(2); lift += L(3)
    } else if (h.vag) {
      const t1 = h.slut ?? h.start + 1
      const f = Math.max(0, Math.min(1, (u - h.start) / (t1 - h.start)))
      const [[x0, z0], [x1, z1]] = h.vag
      x = x0 + (x1 - x0) * f
      z = z0 + (z1 - z0) * f
      yaw ??= Math.atan2(x1 - x0, z1 - z0) / D
    } else [x, z] = h.plats ?? [0, 0]
    return { q, lift, x, z, yaw: yaw ?? 0, blick: h.blick, har: h.har ?? null, liv: clip.liv !== false }
  }
  const cur = one(sorted[k])
  if (!cur.liv) return cur // rekonstruerad rörelse har redan andning och mikrorörelser
  const prev = k > 0 ? sorted[k - 1] : null
  const f = prev ? Math.min(1, (u - sorted[k].start) / BLEND) : 1
  if (prev && f < 1) {
    const a = one(prev)
    cur.q = a.q.map((qa, n) => qa.clone().slerp(cur.q[n], f))
    cur.lift = a.lift + (cur.lift - a.lift) * f
    cur.x = a.x + (cur.x - a.x) * f
    cur.z = a.z + (cur.z - a.z) * f
    let dy = ((cur.yaw - a.yaw + 540) % 360) - 180
    cur.yaw = a.yaw + dy * f
  }
  return cur
}

// Andning och mikrorörelser: deterministiska, så att ingen står som en staty.
function liv(q, t, seed) {
  const a = Math.sin(t * 1.9 + seed) * 1.1
  const b = Math.sin(t * 0.7 + seed * 3) * 1.4
  q[INDEX.spine3].multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(a * D, 0, 0)))
  q[INDEX.head].multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, b * D, a * 0.5 * D)))
}

const COMP_VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`
const COMP_FRAG = `
uniform sampler2D tA; uniform sampler2D tB; uniform float f; uniform int mode;
varying vec2 vUv;
vec4 blurX(sampler2D t, vec2 uv, float s){ vec4 c = vec4(0.0); for(int i=0;i<14;i++){ float k = float(i)/13.0 - 0.5; c += texture2D(t, uv + vec2(k*s, 0.0)); } return c/14.0; }
vec4 blurR(sampler2D t, vec2 uv, float s){ vec4 c = vec4(0.0); vec2 d = uv - 0.5; for(int i=0;i<12;i++){ float k = float(i)/11.0; c += texture2D(t, 0.5 + d*(1.0 - k*s)); } return c/12.0; }
void main(){
  vec4 a; vec4 b;
  if (mode == 0) { gl_FragColor = texture2D(tA, vUv); }
  else if (mode == 1) { float m = smoothstep(0.0, 1.0, f); gl_FragColor = mix(texture2D(tA, vUv), texture2D(tB, vUv), m); }
  else if (mode == 2) {
    float s = sin(3.14159 * f) * 0.18;
    a = blurX(tA, vUv + vec2(f * 0.7, 0.0), s);
    b = blurX(tB, vUv - vec2((1.0 - f) * 0.7, 0.0), s);
    gl_FragColor = mix(a, b, smoothstep(0.42, 0.58, f));
  } else {
    float s = sin(3.14159 * f) * 0.25;
    a = blurR(tA, 0.5 + (vUv - 0.5) / (1.0 + f * 0.8), s);
    b = blurR(tB, 0.5 + (vUv - 0.5) * (1.0 + (1.0 - f) * 0.6), s);
    gl_FragColor = mix(a, b, smoothstep(0.35, 0.65, f));
  }
  #include <colorspace_fragment>
}`
const MODE = { klipp: 0, mjuk: 1, whip: 2, zoom: 3 }

export class Spelare {
  constructor(canvas, { bredd, hojd, pixelRatio }) {
    this.W = bredd
    this.H = hojd
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
    this.renderer.setPixelRatio(pixelRatio ?? Math.min(2, window.devicePixelRatio || 1))
    this.renderer.setSize(bredd, hojd, false)
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFShadowMap
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color('#f3eee5')
    this.cam = new THREE.PerspectiveCamera(50, bredd / hojd, 0.05, 60)
    this.sol = buildLjus(this.scene)
    const size = new THREE.Vector2()
    this.renderer.getDrawingBufferSize(size)
    const rt = () => new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 })
    this.rtA = rt()
    this.rtB = rt()
    this.comp = new THREE.ShaderMaterial({
      uniforms: { tA: { value: this.rtA.texture }, tB: { value: this.rtB.texture }, f: { value: 0 }, mode: { value: 0 } },
      vertexShader: COMP_VERT, fragmentShader: COMP_FRAG, depthTest: false, depthWrite: false,
    })
    this.quadScene = new THREE.Scene()
    this.quadScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.comp))
    this.quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)
    this.t = 0
    this.playing = false
    this.onTime = null
  }

  load(manus) {
    // Samma lokal och roller: byt bara manus. Det är det som gör bytet blixtsnabbt.
    const lokalId = m => (typeof m.lokal === 'string' ? m.lokal : m.lokal?.id) + (m.stil ?? '')
    const same = this.manus && lokalId(this.manus) === lokalId(manus) && JSON.stringify(this.manus.roller) === JSON.stringify(manus.roller) && JSON.stringify(this.manus.figurer ?? null) === JSON.stringify(manus.figurer ?? null)
    this.manus = manus
    this.tl = tidslinje(manus)
    this.dur = langd(manus)
    if (same) { this.renderAt(Math.min(this.t, this.dur - 1e-3)); return }
    if (this.lokal) this.scene.remove(this.lokal)
    for (const d of Object.values(this.dockor ?? {})) this.scene.remove(d.root)
    // projicerade ytor (rekonstruktionens rena skiva) får ingen kontur: kanterna finns redan i fotot
    this.lokal = kontur(buildLokal(manus.lokal), { skip: o => o.geometry.type === 'PlaneGeometry' || o.geometry.type === 'CircleGeometry' || o.userData.projicerad })
    this.redo = this.lokal.userData.laddar ?? Promise.resolve()
    this.scene.add(this.lokal)
    this.dockor = Object.fromEntries(Object.entries(manus.roller).map(([r, fig]) => {
      const d = buildDocka(manus.figurer?.[fig] ?? FIGURER[fig], { stil: manus.stil })
      // små delar (ögon, glasögon, läppar) får ingen kontur: kanten blir tjockare än delen själv
      if (manus.stil !== 'foto') kontur(d.root, { skip: o => { o.geometry.computeBoundingSphere(); return o.geometry.boundingSphere.radius * Math.max(o.scale.x, o.scale.y, o.scale.z) < 0.03 } })
      this.scene.add(d.root)
      return [r, d]
    }))
    this.renderAt(Math.min(this.t, this.dur - 1e-3))
  }

  // Byt manus utan att rendera (samma lokal och roller måste redan vara laddade). För mätning av
  // tusentals uttryck, där bara motorns syn behövs.
  sattManus(manus) {
    this.manus = manus
    this.tl = tidslinje(manus)
    this.dur = langd(manus)
  }

  // Ställ upp scen i vid scentid u: dockornas poser och kameran. Returnerar läget för mätning.
  stage(i, u) {
    const s = this.manus.scener[i]
    const per = {}
    for (const h of s.handling ?? []) (per[h.roll] ||= []).push(h)
    const poser = {}
    for (const [r, d] of Object.entries(this.dockor)) {
      // synlig: [t0, t1] i scenens tid (rekonstruerade personer som kommer in eller går ut ur bild)
      d.root.visible = !!per[r] && per[r].some(h => !h.synlig || (u >= h.synlig[0] && u <= h.synlig[1]))
      if (!per[r]) continue
      poser[r] = rollPose(per[r], u, this.manus.rorelser)
    }
    // först utan blick, för att veta var alla huvuden är
    for (const [r, p] of Object.entries(poser)) this.dockor[r].setPose(p.q, p.x, p.z, p.yaw, p.lift)
    const head = r => this.dockor[r].joints()[INDEX.head]
    for (const [r, p] of Object.entries(poser)) {
      if (p.liv) liv(p.q, u + i * 3.1, r.length * 1.7)
      if (p.blick) {
        const mal = typeof p.blick === 'string' ? (poser[p.blick] ? head(p.blick) : null) : new THREE.Vector3(...p.blick)
        if (mal) {
          const h = head(r)
          const lok = mal.clone().sub(h).applyAxisAngle(new THREE.Vector3(0, 1, 0), -p.yaw * D)
          const ang = Math.max(-75, Math.min(75, Math.atan2(lok.x, lok.z) / D))
          const pitch = Math.max(-25, Math.min(25, -Math.atan2(lok.y, Math.hypot(lok.x, lok.z)) / D))
          p.q[INDEX.neck].multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(pitch * 0.4 * D, ang * 0.4 * D, 0, 'YXZ')))
          p.q[INDEX.head].multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(pitch * 0.6 * D, ang * 0.6 * D, 0, 'YXZ')))
        }
      }
      this.dockor[r].setPose(p.q, p.x, p.z, p.yaw, p.lift)
      this.dockor[r].setProp(p.har)
    }
    // kameran
    const k = s.kamera
    const malAt = uu => {
      if (k.mal.punkt || !per[k.mal.roll]) return new THREE.Vector3(...(k.mal.punkt ?? [s.origo?.[0] ?? 0, 1.2, -2]))
      if (uu === u) return this.dockor[k.mal.roll].joints()[INDEX[k.mal.led]]
      const p = rollPose(per[k.mal.roll], uu, this.manus.rorelser)
      const d = this.dockor[k.mal.roll]
      d.setPose(p.q, p.x, p.z, p.yaw, p.lift)
      const j = d.joints()[INDEX[k.mal.led]]
      return j
    }
    const malU = malAt(u)
    const jointsNu = Object.fromEntries(Object.keys(poser).map(r => [r, this.dockor[r].joints()]))
    const mal0 = k.ops?.some(o => o.op === 'tracking') || !k.mal.punkt ? malAt(0) : malU
    // malAt(0) kan ha flyttat dockan; ställ tillbaka
    for (const [r, p] of Object.entries(poser)) this.dockor[r].setPose(p.q, p.x, p.z, p.yaw, p.lift)
    const ks = evalKamera(k, u, s.tid, mal0, malU, i + 1)
    applyKamera(this.cam, ks)
    // rekonstruerade scener står var för sig (origo per scen): ljuset och skuggorna följer med
    const o = s.origo ?? [0, 0, 0]
    if (this.sol) { this.sol.position.set(o[0] + 2.5, 5, o[2] + 4); this.sol.target.position.set(o[0], 0, o[2]); this.sol.target.updateMatrixWorld() }
    return { scen: i, u, joints: jointsNu, kamera: ks }
  }

  // Vilken scen (och ev. övergång) gäller vid global tid t.
  where(t) {
    const tl = this.tl
    for (let n = 1; n < tl.length; n++) {
      const tr = tl[n].in
      const d = tr.typ === 'klipp' ? 0 : (tr.tid ?? 0.3)
      if (d && t >= tl[n].start - d / 2 && t < tl[n].start + d / 2) {
        return { a: n - 1, b: n, f: (t - (tl[n].start - d / 2)) / d, mode: MODE[tr.typ] }
      }
    }
    const i = Math.max(0, tl.findIndex(s => t < s.slut))
    return { a: t >= this.dur ? tl.length - 1 : i, b: null, f: 0, mode: 0 }
  }

  renderScene(i, u, target) {
    const st = this.stage(i, Math.max(0, Math.min(this.manus.scener[i].tid, u)))
    if (this.oversikt) applyKamera(this.cam, this.oversikt) // felsökning: fri kamera
    KONTUR.uniforms.aspect.value = this.cam.aspect
    this.renderer.setRenderTarget(target)
    this.renderer.render(this.scene, this.cam)
    return st
  }

  renderAt(t) {
    this.t = t
    const w = this.where(t)
    const ua = t - this.tl[w.a].start
    const st = this.renderScene(w.a, ua, this.rtA)
    if (w.b !== null) this.renderScene(w.b, t - this.tl[w.b].start, this.rtB)
    this.comp.uniforms.f.value = w.f
    this.comp.uniforms.mode.value = w.b === null ? 0 : w.mode
    this.renderer.setRenderTarget(null)
    this.renderer.render(this.quadScene, this.quadCam)
    this.onTime?.(t, w)
    return st
  }

  play() {
    if (this.playing) return
    this.playing = true
    let last = performance.now()
    // Klockan läses med performance.now(): rAF:s tidsstämpel kan ligga före den, vilket gav negativ tid.
    const loop = () => {
      if (!this.playing) return
      const now = performance.now()
      const dt = Math.max(0, Math.min(0.1, (now - last) / 1000))
      last = now
      let t = Math.max(0, this.t) + dt
      if (t >= this.dur) t = 0
      this.renderAt(t)
      this.raf = requestAnimationFrame(loop)
    }
    this.raf = requestAnimationFrame(loop)
  }
  pause() { this.playing = false; cancelAnimationFrame(this.raf) }
  seek(t) { this.renderAt(Math.max(0, Math.min(this.dur - 1e-3, t))) }

  // En liten bild av scen i vid scentid u, som data-URL.
  thumb(i, u, w, h) {
    const rt = new THREE.WebGLRenderTarget(w, h, { samples: 4 })
    const aspect = this.cam.aspect
    this.cam.aspect = w / h
    this.cam.updateProjectionMatrix()
    this.renderScene(i, u, rt)
    const px = new Uint8Array(w * h * 4)
    this.renderer.readRenderTargetPixels(rt, 0, 0, w, h, px)
    this.cam.aspect = aspect
    this.cam.updateProjectionMatrix()
    rt.dispose()
    const c = document.createElement('canvas')
    c.width = w
    c.height = h
    const g = c.getContext('2d')
    const img = g.createImageData(w, h)
    const lut = Spelare.lut ||= Array.from({ length: 256 }, (_, v) => {
      const x = v / 255
      return Math.round(255 * (x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055))
    })
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const s = ((h - 1 - y) * w + x) * 4
      const d = (y * w + x) * 4
      img.data[d] = lut[px[s]]; img.data[d + 1] = lut[px[s + 1]]; img.data[d + 2] = lut[px[s + 2]]; img.data[d + 3] = 255
    }
    g.putImageData(img, 0, 0)
    this.renderAt(this.t)
    return c.toDataURL('image/png')
  }

  dispose() { this.pause(); this.renderer.dispose() }
}

