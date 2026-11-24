// arbetsbord/web/scen3d.js
// Självständig Three.js 9:16-renderare för scenpaket/2 (Blender Z-upp, meter).
// Exakt kameraprojektion (sensor_fit = HORIZONTAL, kvaternion [qw,qx,qy,qz] -> Three (qx,qy,qz,qw))
// och T1-armatur/benmappning enligt byggsten/brygga/emit_bpy.py.

import * as THREE from '/three/three.module.js';
import { OrbitControls } from '/three/OrbitControls.js';

// Exakt BEN1-topologi från byggsten/brygga/emit_bpy.py (rad 172-180)
const BEN1_KAPSLAR = [
  ['backen', 'c_spine0', 'c_spine1', 0.115],
  ['rygg1', 'c_spine1', 'c_spine2', 0.122],
  ['rygg2', 'c_spine2', 'c_spine3', 0.132],
  ['brost', 'c_spine3', 'c_neck', 0.138],
  ['nacke', 'c_neck', 'c_head', 0.050],
  ['nyckel_l', 'l_clavicle', 'l_uparm', 0.048],
  ['overarm_l', 'l_uparm', 'l_lowarm', 0.048],
  ['underarm_l', 'l_lowarm', 'l_wrist', 0.039],
  ['hoft_l', 'c_spine0', 'l_upleg', 0.072],
  ['lar_l', 'l_upleg', 'l_lowleg', 0.072],
  ['skenben_l', 'l_lowleg', 'l_foot', 0.053],
  ['nyckel_r', 'r_clavicle', 'r_uparm', 0.048],
  ['overarm_r', 'r_uparm', 'r_lowarm', 0.048],
  ['underarm_r', 'r_lowarm', 'r_wrist', 0.039],
  ['hoft_r', 'c_spine0', 'r_upleg', 0.072],
  ['lar_r', 'r_upleg', 'r_lowleg', 0.072],
  ['skenben_r', 'r_lowleg', 'r_foot', 0.053],
];

// Fallback T0-topologi om ett äldre paket saknar c_spine1/c_spine3/clavicle
const BEN0_KAPSLAR = [
  ['rygg_nedre', 'c_spine0', 'c_spine2', 0.125],
  ['rygg_ovre', 'c_spine2', 'c_neck', 0.120],
  ['nacke', 'c_neck', 'c_head', 0.050],
  ['axel_l', 'c_neck', 'l_uparm', 0.050],
  ['overarm_l', 'l_uparm', 'l_lowarm', 0.046],
  ['underarm_l', 'l_lowarm', 'l_wrist', 0.036],
  ['axel_r', 'c_neck', 'r_uparm', 0.050],
  ['overarm_r', 'r_uparm', 'r_lowarm', 0.046],
  ['underarm_r', 'r_lowarm', 'r_wrist', 0.036],
  ['hoft_l', 'c_spine0', 'l_upleg', 0.070],
  ['lar_l', 'l_upleg', 'l_lowleg', 0.065],
  ['skenben_l', 'l_lowleg', 'l_foot', 0.050],
  ['fot_l', 'l_foot', 'l_ball', 0.035],
  ['hoft_r', 'c_spine0', 'r_upleg', 0.070],
  ['lar_r', 'r_upleg', 'r_lowleg', 0.065],
  ['skenben_r', 'r_lowleg', 'r_foot', 0.050],
  ['fot_r', 'r_foot', 'r_ball', 0.035],
];

const STANDARD_TEMA = {
  id: 'original',
  namn: 'Original',
  bakgrund: '#151820',
  golv: null,
  vagg: null,
  ljus: {
    nyckel_farg: '#fff8ee',
    nyckel_styrka: 2.1,
    fyll_farg: '#b8d0f5',
    fyll_styrka: 0.75,
    omgivning_farg: '#dce4f2',
    omgivning_styrka: 0.85,
  },
  dimma: null,
};

const UP_Y = new THREE.Vector3(0, 1, 0);
const UP_Z = new THREE.Vector3(0, 0, 1);

const TILLTRO_CYAN = 0x4dd6ff;
const UNDERBODY_JOINTS = new Set([
  'l_upleg', 'r_upleg', 'l_lowleg', 'r_lowleg', 'l_foot', 'r_foot', 'l_ball', 'r_ball',
]);

const FOOD_DEFAULT_PALETTES = {
  mat_tallrik: ['#d95338', '#f2c14e', '#4f9452'],
  mat_skal: ['#d96c32', '#f4d378', '#3e8c54'],
  mat_bricka: ['#c87b42', '#e9be69', '#56944e'],
};

function normalizeTilltroStatus(val) {
  if (!val) return null;
  if (typeof val === 'string') return val.trim().toLowerCase();
  if (typeof val === 'object') {
    const s = val.status || val.tilltro || val.niva || null;
    return typeof s === 'string' ? s.trim().toLowerCase() : null;
  }
  return null;
}

function isGhostedStatus(status) {
  return status === 'harledd_mall' || status === 'skymd_antagen';
}

function hexColor(val, fallback = '#888888') {
  try {
    return new THREE.Color(val || fallback);
  } catch {
    return new THREE.Color(fallback);
  }
}

function resolveFoodPalette(o, typ) {
  const def = FOOD_DEFAULT_PALETTES[typ] || FOOD_DEFAULT_PALETTES.mat_tallrik;
  const raw = Array.isArray(o?.farg_palett) ? o.farg_palett.filter((c) => typeof c === 'string' && c.trim()) : [];
  if (raw.length >= 3) return [raw[0].trim(), raw[1].trim(), raw[2].trim()];
  if (raw.length === 2) return [raw[0].trim(), raw[1].trim(), def[2]];
  if (raw.length === 1) return [raw[0].trim(), def[1], def[2]];
  if (o?.farg && typeof o.farg === 'string' && /^#[0-9a-fA-F]{6}$/.test(o.farg.trim())) {
    return [o.farg.trim(), def[1], def[2]];
  }
  return [...def];
}

function makeFoodSurfaceTexture(palette, style = 'tallrik') {
  const [c0, c1, c2] = palette;
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  const cx = 128;
  const cy = 128;

  if (style === 'skal') {
    // Djup buljong/innehållsyta med hög kontrast och stiliserade lager
    const grad = ctx.createRadialGradient(cx - 12, cy - 12, 16, cx, cy, 126);
    grad.addColorStop(0, c1);
    grad.addColorStop(0.52, c0);
    grad.addColorStop(1, '#261811');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);

    // Stiliserad swirl
    ctx.strokeStyle = c1;
    ctx.globalAlpha = 0.7;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(cx, cy, 74, 0.3, Math.PI * 1.45);
    ctx.stroke();

    ctx.strokeStyle = '#fff5df';
    ctx.globalAlpha = 0.32;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(cx, cy, 48, 1.1, Math.PI * 1.9);
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Kontrast-toppingar (rena vektorformer)
    const dots = [
      [88, 96, 18, c2],
      [164, 112, 20, c1],
      [122, 166, 16, c2],
      [148, 76, 12, '#fff4dc'],
      [82, 152, 11, '#fff4dc'],
    ];
    for (const [x, y, r, col] of dots) {
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.22)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  } else if (style === 'bricka') {
    // Stiliserat smörgås-/serveringspapper med rena geometriska linjer
    ctx.fillStyle = '#f3ead8';
    ctx.fillRect(0, 0, 256, 256);

    ctx.strokeStyle = 'rgba(92, 67, 48, 0.14)';
    ctx.lineWidth = 2;
    for (let p = -256; p < 512; p += 24) {
      ctx.beginPath();
      ctx.moveTo(p, 0);
      ctx.lineTo(p + 256, 256);
      ctx.stroke();
    }

    ctx.strokeStyle = c0;
    ctx.lineWidth = 10;
    ctx.strokeRect(12, 12, 232, 232);

    ctx.strokeStyle = c1;
    ctx.lineWidth = 3;
    ctx.strokeRect(24, 24, 208, 208);

    // Diskret färgfält för kontrast under matprimitiverna
    ctx.fillStyle = c2;
    ctx.globalAlpha = 0.22;
    ctx.beginPath();
    ctx.roundRect(142, 128, 78, 86, 14);
    ctx.fill();
    ctx.globalAlpha = 1;
  } else {
    // Tallrik: högkontrast porslinsbotten + såssvep + vektoriserad uppläggning
    ctx.fillStyle = '#f8f4ec';
    ctx.fillRect(0, 0, 256, 256);

    ctx.strokeStyle = 'rgba(0,0,0,0.08)';
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(cx, cy, 114, 0, Math.PI * 2);
    ctx.stroke();

    // Högkontrast sås-/basbädd i c0
    ctx.fillStyle = c0;
    ctx.beginPath();
    ctx.ellipse(cx - 4, cy + 4, 84, 68, -0.35, 0, Math.PI * 2);
    ctx.fill();

    // Sekundärt uppläggningsfält i c1
    ctx.fillStyle = c1;
    ctx.beginPath();
    ctx.arc(cx + 18, cy - 14, 48, 0, Math.PI * 2);
    ctx.fill();

    // Skarp såssväng
    ctx.strokeStyle = '#fff6e4';
    ctx.globalAlpha = 0.45;
    ctx.lineWidth = 7;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(cx, cy, 88, 0.2, 2.15);
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Garnityrpunkter i c2
    const herbs = [
      [92, 92, 11],
      [158, 86, 9],
      [168, 152, 12],
      [104, 168, 10],
      [130, 124, 8],
    ];
    ctx.fillStyle = c2;
    for (const [x, y, r] of herbs) {
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.minFilter = THREE.LinearFilter;
  return tex;
}

function makeLabelSprite(text, accentHex = '#4c8bf5', baseHeight = 0.14) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const fontSize = 28;
  const padX = 20;
  const padY = 12;
  ctx.font = `600 ${fontSize}px system-ui, -apple-system, "Segoe UI", sans-serif`;
  const clean = String(text || '').trim().slice(0, 32);
  const w = Math.ceil(ctx.measureText(clean).width + padX * 2);
  const h = fontSize + padY * 2;
  canvas.width = Math.max(64, w);
  canvas.height = Math.max(40, h);

  const r = 12;
  ctx.fillStyle = 'rgba(13, 16, 23, 0.86)';
  ctx.beginPath();
  ctx.roundRect(1, 1, canvas.width - 2, canvas.height - 2, r);
  ctx.fill();

  ctx.strokeStyle = accentHex;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.roundRect(1.5, 1.5, canvas.width - 3, canvas.height - 3, r);
  ctx.stroke();

  ctx.font = `600 ${fontSize}px system-ui, -apple-system, "Segoe UI", sans-serif`;
  ctx.fillStyle = '#f2f5fa';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(clean, canvas.width / 2, canvas.height / 2 + 1);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.minFilter = THREE.LinearFilter;
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: true, depthWrite: false });
  const sprite = new THREE.Sprite(mat);
  const aspectRatio = canvas.width / canvas.height;
  sprite.scale.set(baseHeight * aspectRatio, baseHeight, 1);
  sprite.userData._disposableTexture = tex;
  sprite.userData.baseHeight = baseHeight;
  sprite.userData.aspectRatio = aspectRatio;
  return sprite;
}

function makeSignTexture(text, bgHex = '#1c2230', fgHex = '#f5f7fb') {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 192;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = bgHex;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'rgba(255,255,255,0.22)';
  ctx.lineWidth = 8;
  ctx.strokeRect(8, 8, canvas.width - 16, canvas.height - 16);
  ctx.fillStyle = fgHex;
  ctx.font = '700 44px system-ui, -apple-system, "Segoe UI", sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const clean = String(text || '').trim().slice(0, 26);
  ctx.fillText(clean, canvas.width / 2, canvas.height / 2);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// Binärsökning för nycklar sorterade på r[0] (ruta u)
function findBracket(arr, u) {
  const n = arr.length;
  if (n === 0) return null;
  if (n === 1 || u <= arr[0][0]) return [arr[0], arr[0], 0];
  if (u >= arr[n - 1][0]) return [arr[n - 1], arr[n - 1], 0];
  let lo = 0;
  let hi = n - 1;
  while (lo + 1 < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid][0] <= u) lo = mid;
    else hi = mid;
  }
  const a = arr[lo];
  const b = arr[hi];
  const span = b[0] - a[0];
  const alpha = span > 1e-9 ? Math.max(0, Math.min(1, (u - a[0]) / span)) : 0;
  return [a, b, alpha];
}

function isVisibleAt(intervall, u, antalRutor) {
  if (!Array.isArray(intervall) || intervall.length === 0) return true;
  for (let i = 0; i < intervall.length; i++) {
    const iv = intervall[i];
    if (!Array.isArray(iv) || iv.length < 2) continue;
    const a = iv[0];
    const b = iv[1];
    if (u >= a - 1e-6 && u < b) return true;
    if (antalRutor > 0 && b >= antalRutor && u >= antalRutor - 1e-3 && u <= antalRutor + 1e-3) return true;
  }
  return false;
}

export class Scen3DRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.options = options;

    this.paket = null;
    this.miljoTema = null;
    this.kroppsKontrakt = null;
    this.fps = 30.0;
    this.antalRutor = 0;
    this.bredd = 576;
    this.hojd = 1024;
    this.sensorMm = 36.0;

    this.currentTime = 0;
    this.currentFrame = 0;
    this.activeTagning = null;
    this.orbitMode = false;
    this.transparentBg = false;
    this.showLabels = true;
    this.showTilltro = false;
    this.showGrid = true;
    this._lastTilltroStats = { objekt: 0, leder: 0 };

    // Renderer: preserveDrawingBuffer: true för deterministisk Playwright/soundoverlay-fångst
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
      powerPreference: 'high-performance',
    });
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.08;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    // Scen (Z-upp)
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(STANDARD_TEMA.bakgrund);

    // Kamera (Z-upp, Blender-kompatibel lokal -Z fram, +Y upp, +X höger)
    this.camera = new THREE.PerspectiveCamera(60, 9 / 16, 0.03, 120);
    this.camera.up.set(0, 0, 1);

    // OrbitControls för fri 3D-inspektion
    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.screenSpacePanning = true;
    this.controls.minDistance = 0.4;
    this.controls.maxDistance = 35;
    this.controls.enabled = false;
    this.controls.addEventListener('change', () => {
      if (this.orbitMode) this.renderFrame();
    });

    // Delade geometrier (noll allokering per ruta)
    this._sharedGeo = {
      box: new THREE.BoxGeometry(1, 1, 1),
      cyl: new THREE.CylinderGeometry(1, 1, 1, 14),
      sphere: new THREE.SphereGeometry(1, 16, 12),
      jointSphere: new THREE.SphereGeometry(1, 10, 8),
      headSphere: new THREE.SphereGeometry(0.095, 20, 14),
      noseSphere: new THREE.SphereGeometry(0.028, 12, 10),
    };

    // Delade material för tilltro-spökning (härledd_mall / skymd_antagen)
    this._ghostWireMat = new THREE.MeshBasicMaterial({
      color: TILLTRO_CYAN,
      wireframe: true,
      transparent: true,
      opacity: 0.75,
      depthWrite: false,
    });
    this._ghostEdgeMat = new THREE.LineBasicMaterial({
      color: TILLTRO_CYAN,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
    });
    this._ghostObjMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#6ee2ff'),
      emissive: new THREE.Color('#135870'),
      emissiveIntensity: 0.35,
      roughness: 0.35,
      metalness: 0.08,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    });

    // Ljusgrupp
    this.hemiLight = new THREE.HemisphereLight(0xdce4f2, 0x3b3530, 0.85);
    this.hemiLight.position.set(0, 0, 10);
    this.scene.add(this.hemiLight);

    this.keyLight = new THREE.DirectionalLight(0xfff8ee, 2.1);
    this.keyLight.position.set(2.8, -4.2, 6.5);
    this.keyLight.castShadow = true;
    this.keyLight.shadow.mapSize.set(1024, 1024);
    this.keyLight.shadow.camera.near = 0.5;
    this.keyLight.shadow.camera.far = 28;
    this.keyLight.shadow.camera.left = -7;
    this.keyLight.shadow.camera.right = 7;
    this.keyLight.shadow.camera.top = 7;
    this.keyLight.shadow.camera.bottom = -7;
    this.keyLight.shadow.bias = -0.0005;
    this.scene.add(this.keyLight);
    this.scene.add(this.keyLight.target);

    this.fillLight = new THREE.DirectionalLight(0xb8d0f5, 0.75);
    this.fillLight.position.set(-3.5, 3.8, 3.5);
    this.scene.add(this.fillLight);

    this.rimLight = new THREE.DirectionalLight(0xffe7cc, 0.35);
    this.rimLight.position.set(0.5, 5.2, 2.6);
    this.scene.add(this.rimLight);

    // Rotgrupper för scenens innehåll
    this.objektGroup = new THREE.Group();
    this.objektGroup.name = 'OBJEKT';
    this.scene.add(this.objektGroup);

    this.personGroup = new THREE.Group();
    this.personGroup.name = 'PERSONER';
    this.scene.add(this.personGroup);

    this.gridHelper = null;

    // Internt register
    this._objektEntries = [];
    this._personRigs = new Map();
    this._jointIndex = {};
    this._disposables = [];

    // Scratch-objekt för noll GC-tryck under uppspelning
    this._vA = new THREE.Vector3();
    this._vB = new THREE.Vector3();
    this._vDir = new THREE.Vector3();
    this._vMid = new THREE.Vector3();
    this._vX = new THREE.Vector3();
    this._vY = new THREE.Vector3();
    this._vZ = new THREE.Vector3();
    this._m4 = new THREE.Matrix4();
    this._q0 = new THREE.Quaternion();
    this._q1 = new THREE.Quaternion();
    this._qOut = new THREE.Quaternion();
    this._camFwd = new THREE.Vector3();
    this._vLabelWorld = new THREE.Vector3();
    this._lastCamInfo = {
      pos: [0, 0, 0],
      quat: [1, 0, 0, 0],
      lins_mm: 50,
      fov_v: 60,
    };

    this.resize();
  }

  resize() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const w = Math.max(180, Math.round(rect.width));
    const h = Math.max(320, Math.round(rect.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = this.bredd / this.hojd;
    this.camera.updateProjectionMatrix();
    if (this.paket) this.renderFrame();
  }

  _clearDynamicScene() {
    while (this.objektGroup.children.length > 0) {
      this.objektGroup.remove(this.objektGroup.children[0]);
    }
    while (this.personGroup.children.length > 0) {
      this.personGroup.remove(this.personGroup.children[0]);
    }
    if (this.gridHelper) {
      this.scene.remove(this.gridHelper);
      this.gridHelper.geometry?.dispose?.();
      this.gridHelper.material?.dispose?.();
      this.gridHelper = null;
    }
    for (const d of this._disposables) {
      d?.dispose?.();
    }
    this._disposables = [];
    this._objektEntries = [];
    this._personRigs.clear();
  }

  loadScene(paket, miljoTema = null, kroppsKontrakt = null) {
    this._clearDynamicScene();
    this.paket = paket || null;
    this.miljoTema = miljoTema || paket?.miljo_tema || null;
    this.kroppsKontrakt =
      kroppsKontrakt ||
      paket?.kropps_kontrakt ||
      paket?.tillstand?.kropps_kontrakt ||
      null;

    if (!this.paket) {
      this.fps = 30.0;
      this.antalRutor = 0;
      this.activeTagning = null;
      this.applyEnvironmentTheme(this.miljoTema);
      this.renderFrame();
      return;
    }

    this.fps = Number(this.paket.tidsbas?.fps) || 30.0;
    this.antalRutor = Number(this.paket.tidsbas?.antal_rutor) || 0;
    this.bredd = Number(this.paket.bild?.bredd) || 576;
    this.hojd = Number(this.paket.bild?.hojd) || 1024;
    this.sensorMm = Number(this.paket.bild?.sensor_mm) || 36.0;

    this.camera.aspect = this.bredd / this.hojd;
    this.camera.updateProjectionMatrix();

    // Indexera leder
    const leder = Array.isArray(this.paket.leder) ? this.paket.leder : [];
    this._jointIndex = {};
    for (let i = 0; i < leder.length; i++) {
      this._jointIndex[leder[i]] = i;
    }

    // Bygg objekt (inkl. ev. miljo_tema.extra_props)
    const allaObjekt = [
      ...(Array.isArray(this.paket.objekt) ? this.paket.objekt : []),
      ...(Array.isArray(this.miljoTema?.extra_props) ? this.miljoTema.extra_props : []),
    ];
    this._buildObjects(allaObjekt);

    // Bygg golvrutnät för rumsdjup
    this._buildFloorGrid();

    // Bygg personriggar (T1 eller T0 fallback)
    this._buildPersons(this.paket.rorelse || {}, this.paket.personer || {});

    // Applicera belysning, bakgrund och ev. tilltro-spökning
    this.applyEnvironmentTheme(this.miljoTema);
    this._applyTilltroToObjects();

    // Rendera aktuell tid
    this.setTime(this.currentTime);
  }

  setKroppsKontrakt(kontrakt) {
    this.kroppsKontrakt = kontrakt || null;
    this._applyTilltroToObjects();
    if (this.paket) {
      this._updatePersonsForFrame(this.currentFrame);
      this.renderFrame();
    }
  }

  setShowTilltro(enabled) {
    this.showTilltro = Boolean(enabled);
    this._applyTilltroToObjects();
    if (this.paket) {
      this._updatePersonsForFrame(this.currentFrame);
    }
    this.renderFrame();
    return this.showTilltro;
  }

  _buildFloorGrid() {
    if (!this.showGrid) return;
    const golvZ = Number(this.paket?.golv_z ?? 0);
    // Beräkna golvets utbredning för lagom rutnät
    let size = 12;
    let cx = 0;
    let cy = 0;
    const golvObj = (this.paket?.objekt || []).find((o) => o.typ === 'golv');
    if (golvObj && Array.isArray(golvObj.matt)) {
      size = Math.max(6, Math.ceil(Math.max(golvObj.matt[0], golvObj.matt[1])));
      cx = golvObj.pos?.[0] || 0;
      cy = golvObj.pos?.[1] || 0;
    }
    const divisions = Math.max(8, Math.min(28, Math.round(size * 2)));
    const grid = new THREE.GridHelper(size, divisions, 0x5c6678, 0x3b4252);
    grid.rotation.x = Math.PI / 2; // GridHelper är XZ; rotera till XY (Z-upp)
    grid.position.set(cx, cy, golvZ + 0.003);
    const mats = Array.isArray(grid.material) ? grid.material : [grid.material];
    for (const mt of mats) {
      mt.transparent = true;
      mt.opacity = 0.14;
      mt.depthWrite = false;
    }
    this.gridHelper = grid;
    this.scene.add(grid);
  }

  _buildMatshotObject(group, o, typ, sx, sy, sz) {
    const pal = resolveFoodPalette(o, typ);
    const col0 = hexColor(pal[0], '#d95338');
    const col1 = hexColor(pal[1], '#f2c14e');
    const col2 = hexColor(pal[2], '#4f9452');

    const mat0 = new THREE.MeshStandardMaterial({ color: col0, roughness: 0.44, metalness: 0.05 });
    const mat1 = new THREE.MeshStandardMaterial({ color: col1, roughness: 0.48, metalness: 0.04 });
    const mat2 = new THREE.MeshStandardMaterial({ color: col2, roughness: 0.56, metalness: 0.02 });
    const ceramicMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#f4efe6'),
      roughness: 0.24,
      metalness: 0.06,
    });
    this._disposables.push(mat0, mat1, mat2, ceramicMat);

    const meshParts = [];
    const addPart = (geo, mat, pos, rot = null, scale = null, disposableGeo = false) => {
      if (disposableGeo) this._disposables.push(geo);
      const mesh = new THREE.Mesh(geo, mat);
      if (pos) mesh.position.set(pos[0], pos[1], pos[2]);
      if (rot) mesh.rotation.set(rot[0], rot[1], rot[2]);
      if (scale) mesh.scale.set(scale[0], scale[1], scale[2]);
      mesh.castShadow = true;
      mesh.receiveShadow = true;

      const wireOverlay = new THREE.Mesh(geo, this._ghostWireMat);
      wireOverlay.scale.setScalar(1.025);
      wireOverlay.visible = false;
      mesh.add(wireOverlay);

      group.add(mesh);
      meshParts.push({ mesh, normalMat: mat, wireOverlay });
      return mesh;
    };

    let labelZ = sz * 0.5 + 0.16;

    if (typ === 'mat_tallrik') {
      const r = Math.max(0.09, Math.min(sx, sy) * 0.5);
      const h = Math.max(0.032, Math.min(0.14, sz));

      // Låg cylindrisk porslinsskiva (roterad X=PI/2 för Z-upp)
      const baseGeo = new THREE.CylinderGeometry(r * 0.86, r * 0.68, h * 0.42, 24);
      addPart(baseGeo, ceramicMat, [0, 0, -h * 0.28], [Math.PI / 2, 0, 0], null, true);

      // Ytterbrätte (torus i XY-planet)
      const rimGeo = new THREE.TorusGeometry(r * 0.88, Math.max(0.009, r * 0.115), 10, 28);
      addPart(rimGeo, ceramicMat, [0, 0, -h * 0.03], null, [1, 1, 0.48], true);

      // Färgad kontrastlinje på brättet
      const accentRimGeo = new THREE.TorusGeometry(r * 0.75, Math.max(0.003, r * 0.022), 8, 28);
      addPart(accentRimGeo, mat0, [0, 0, h * 0.03], null, [1, 1, 0.55], true);

      // Högkontrast CanvasTexture-yta ovanpå tallriken
      const surfTex = makeFoodSurfaceTexture(pal, 'tallrik');
      const surfMat = new THREE.MeshStandardMaterial({
        map: surfTex,
        roughness: 0.46,
        metalness: 0.04,
      });
      this._disposables.push(surfTex, surfMat);
      const discGeo = new THREE.CircleGeometry(r * 0.74, 24);
      addPart(discGeo, surfMat, [0, 0, h * 0.045], null, null, true);

      // Stiliserad låg-poly matkomposition + garnityr
      const unit = r * 0.34;
      addPart(this._sharedGeo.box, mat0, [-r * 0.14, r * 0.06, h * 0.20], [0.06, -0.08, 0.35], [unit * 1.15, unit * 0.78, Math.max(0.016, h * 0.36)]);
      addPart(this._sharedGeo.box, mat0, [r * 0.16, -r * 0.08, h * 0.18], [-0.05, 0.07, -0.45], [unit * 1.0, unit * 0.72, Math.max(0.014, h * 0.32)]);
      addPart(this._sharedGeo.sphere, mat1, [r * 0.14, r * 0.22, h * 0.22], null, [unit * 0.48, unit * 0.42, Math.max(0.012, h * 0.30)]);
      addPart(this._sharedGeo.sphere, mat1, [-r * 0.24, -r * 0.20, h * 0.17], null, [unit * 0.36, unit * 0.34, Math.max(0.010, h * 0.24)]);
      addPart(this._sharedGeo.box, mat2, [0, r * 0.02, h * 0.38], [0.25, 0.3, 0.6], [unit * 0.26, unit * 0.26, Math.max(0.009, h * 0.18)]);
      addPart(this._sharedGeo.sphere, mat2, [-r * 0.06, -r * 0.14, h * 0.28], null, [unit * 0.20, unit * 0.20, Math.max(0.008, h * 0.16)]);
      addPart(this._sharedGeo.sphere, mat2, [r * 0.22, r * 0.06, h * 0.26], null, [unit * 0.18, unit * 0.18, Math.max(0.008, h * 0.15)]);

      labelZ = h * 0.5 + 0.16;
    } else if (typ === 'mat_skal') {
      const r = Math.max(0.08, Math.min(sx, sy) * 0.5);
      const h = Math.max(0.06, Math.min(0.22, sz));

      // Kontrasterande keramikskål via öppen LatheGeometry (roterad X=PI/2 -> Z-upp)
      const bowlMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color('#2d3442'),
        roughness: 0.32,
        metalness: 0.08,
        side: THREE.DoubleSide,
      });
      this._disposables.push(bowlMat);

      const pts = [
        new THREE.Vector2(0.001, -h * 0.5),
        new THREE.Vector2(r * 0.56, -h * 0.5),
        new THREE.Vector2(r * 0.84, -h * 0.18),
        new THREE.Vector2(r * 1.0, h * 0.45),
        new THREE.Vector2(r * 0.93, h * 0.50),
        new THREE.Vector2(r * 0.86, h * 0.44),
        new THREE.Vector2(r * 0.72, -h * 0.12),
        new THREE.Vector2(r * 0.48, -h * 0.36),
        new THREE.Vector2(0.001, -h * 0.36),
      ];
      const bowlGeo = new THREE.LatheGeometry(pts, 24);
      addPart(bowlGeo, bowlMat, [0, 0, 0], [Math.PI / 2, 0, 0], null, true);

      // Kontrastkant längs skålens övre brätte
      const lipGeo = new THREE.TorusGeometry(r * 0.94, Math.max(0.004, r * 0.036), 8, 28);
      addPart(lipGeo, mat1, [0, 0, h * 0.47], null, [1, 1, 0.7], true);

      // Innehållsyta med högkontrast CanvasTexture
      const surfTex = makeFoodSurfaceTexture(pal, 'skal');
      const surfMat = new THREE.MeshStandardMaterial({
        map: surfTex,
        roughness: 0.36,
        metalness: 0.05,
      });
      this._disposables.push(surfTex, surfMat);
      const fillGeo = new THREE.CircleGeometry(r * 0.83, 24);
      addPart(fillGeo, surfMat, [0, 0, h * 0.24], null, null, true);

      // Stiliserade låg-poly-toppingar i ytan
      const u = r * 0.30;
      addPart(this._sharedGeo.sphere, mat0, [-r * 0.20, r * 0.14, h * 0.29], null, [u * 0.72, u * 0.56, h * 0.18]);
      addPart(this._sharedGeo.box, mat1, [r * 0.22, -r * 0.10, h * 0.31], [0.22, -0.18, 0.5], [u * 0.78, u * 0.48, h * 0.18]);
      addPart(this._sharedGeo.sphere, mat2, [r * 0.04, r * 0.26, h * 0.30], null, [u * 0.42, u * 0.42, h * 0.14]);
      addPart(this._sharedGeo.box, mat2, [-r * 0.14, -r * 0.24, h * 0.29], [0.15, 0.2, 0.8], [u * 0.38, u * 0.38, h * 0.13]);

      labelZ = h * 0.5 + 0.16;
    } else {
      // mat_bricka: fasad bricka med 3 enkla block-/sallads-/brödprimitiver
      const w = Math.max(0.22, sx);
      const d = Math.max(0.16, sy);
      const h = Math.max(0.036, Math.min(0.16, sz));

      const trayMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color('#5a4130'),
        roughness: 0.58,
        metalness: 0.06,
      });
      this._disposables.push(trayMat);

      // Brickbotten + 4 fasade kantlister
      const baseH = Math.max(0.01, h * 0.26);
      const railH = Math.max(0.016, h * 0.44);
      const railT = Math.max(0.012, Math.min(w, d) * 0.06);
      addPart(this._sharedGeo.box, trayMat, [0, 0, -h * 0.37], null, [w * 0.94, d * 0.94, baseH]);
      addPart(this._sharedGeo.box, trayMat, [0, d * 0.47, -h * 0.18], [-0.24, 0, 0], [w, railT, railH]);
      addPart(this._sharedGeo.box, trayMat, [0, -d * 0.47, -h * 0.18], [0.24, 0, 0], [w, railT, railH]);
      addPart(this._sharedGeo.box, trayMat, [w * 0.47, 0, -h * 0.18], [0, 0.24, 0], [railT, d, railH]);
      addPart(this._sharedGeo.box, trayMat, [-w * 0.47, 0, -h * 0.18], [0, -0.24, 0], [railT, d, railH]);

      // Serveringspapper med CanvasTexture
      const paperTex = makeFoodSurfaceTexture(pal, 'bricka');
      const paperMat = new THREE.MeshStandardMaterial({
        map: paperTex,
        roughness: 0.72,
        metalness: 0.02,
      });
      this._disposables.push(paperTex, paperMat);
      const paperGeo = new THREE.PlaneGeometry(w * 0.84, d * 0.82);
      addPart(paperGeo, paperMat, [0, 0, -h * 0.23], null, null, true);

      // 1. Huvudrättsblock / bröd-lager till vänster
      const blockW = w * 0.34;
      const blockD = d * 0.44;
      const blockH = Math.max(0.024, h * 0.56);
      addPart(this._sharedGeo.box, mat1, [-w * 0.18, 0, -h * 0.22 + blockH * 0.25], [0, 0, 0.08], [blockW, blockD, blockH * 0.48]);
      addPart(this._sharedGeo.box, mat0, [-w * 0.18, 0, -h * 0.22 + blockH * 0.62], [0, 0, 0.08], [blockW * 0.92, blockD * 0.92, blockH * 0.28]);
      addPart(this._sharedGeo.box, mat1, [-w * 0.18, 0, -h * 0.22 + blockH * 0.90], [0, 0, 0.08], [blockW * 0.96, blockD * 0.94, blockH * 0.34]);

      // 2. Salladskluster fram-höger
      const salR = Math.min(w, d) * 0.11;
      addPart(this._sharedGeo.sphere, mat2, [w * 0.18, d * 0.15, -h * 0.10], null, [salR, salR * 0.9, salR * 0.75]);
      addPart(this._sharedGeo.sphere, mat2, [w * 0.25, d * 0.07, -h * 0.08], null, [salR * 0.85, salR * 0.85, salR * 0.7]);
      addPart(this._sharedGeo.sphere, mat2, [w * 0.13, d * 0.05, -h * 0.11], null, [salR * 0.8, salR * 0.75, salR * 0.65]);
      addPart(this._sharedGeo.box, mat0, [w * 0.20, d * 0.12, -h * 0.02], [0.3, 0.4, 0.5], [salR * 0.55, salR * 0.55, salR * 0.55]);

      // 3. Bröd / dippskål bak-höger
      const dipR = Math.min(w, d) * 0.14;
      const dipH = Math.max(0.02, h * 0.48);
      addPart(this._sharedGeo.cyl, ceramicMat, [w * 0.21, -d * 0.17, -h * 0.22 + dipH * 0.5], [Math.PI / 2, 0, 0], [dipR, dipH, dipR]);
      addPart(this._sharedGeo.cyl, mat1, [w * 0.21, -d * 0.17, -h * 0.22 + dipH * 0.84], [Math.PI / 2, 0, 0], [dipR * 0.78, dipH * 0.28, dipR * 0.78]);

      labelZ = h * 0.5 + 0.18;
    }

    return { meshParts, labelZ, accentHex: pal[0] };
  }

  _buildObjects(objektLista) {
    const tema = this.miljoTema || {};
    for (const o of objektLista) {
      if (!o) continue;
      const typ = String(o.typ || 'prop').toLowerCase();
      const pos = Array.isArray(o.pos) ? o.pos : [0, 0, 0];
      const rot = Array.isArray(o.rot) ? o.rot : [0, 0, 0];
      const matt = Array.isArray(o.matt) ? o.matt : [0.4, 0.4, 0.4];

      // Färg: respektera objektets färg; om golv/vagg använder standardfärg, låt miljo_tema färgsätta
      let farg = o.farg || '#7c766e';
      if (typ === 'golv' && tema.golv && (!o.farg || o.farg.toLowerCase() === '#3d3832')) {
        farg = tema.golv;
      } else if (typ === 'vagg' && tema.vagg && (!o.farg || o.farg.toLowerCase() === '#8a8275')) {
        farg = tema.vagg;
      }

      const group = new THREE.Group();
      group.name = `OBJ_${o.id || typ}`;
      group.position.set(Number(pos[0]) || 0, Number(pos[1]) || 0, Number(pos[2]) || 0);
      // Blender Euler XYZ (extrinsisk X,Y,Z = Rz*Ry*Rx) motsvarar Three.js intrinsisk 'ZYX'!
      group.rotation.order = 'ZYX';
      group.rotation.set(Number(rot[0]) || 0, Number(rot[1]) || 0, Number(rot[2]) || 0);

      const sx = Math.max(0.01, Number(matt[0]) || 0.2);
      const sy = Math.max(0.01, Number(matt[1]) || 0.2);
      const sz = Math.max(0.01, Number(matt[2]) || 0.2);

      const isMatshot = typ === 'mat_tallrik' || typ === 'mat_skal' || typ === 'mat_bricka';
      let primaryMesh = null;
      let meshParts = [];
      let normalEdges = null;
      let tilltroEdges = null;
      let labelZ = sz * 0.5 + 0.16;
      let labelAccent = farg;

      if (isMatshot) {
        const built = this._buildMatshotObject(group, o, typ, sx, sy, sz);
        meshParts = built.meshParts;
        primaryMesh = meshParts[0]?.mesh || null;
        labelZ = built.labelZ;
        labelAccent = built.accentHex;
      } else {
        const roughness =
          typ === 'golv' ? 0.88 :
          typ === 'vagg' ? 0.90 :
          typ === 'kaffemaskin' || typ === 'spis' ? 0.34 :
          typ === 'lampa' ? 0.25 :
          typ === 'bord' || typ === 'disk' || typ === 'bank' ? 0.56 : 0.48;
        const metalness =
          typ === 'kaffemaskin' || typ === 'spis' ? 0.42 :
          typ === 'lampa' ? 0.15 : 0.06;

        const color = hexColor(farg, '#7c766e');
        const matOpts = { color, roughness, metalness };
        if (typ === 'lampa') {
          matOpts.emissive = color.clone();
          matOpts.emissiveIntensity = 0.55;
        }
        if (typ === 'skylt' && o.etikett) {
          const signTex = makeSignTexture(o.etikett, farg);
          matOpts.map = signTex;
          matOpts.color = new THREE.Color('#ffffff');
          matOpts.roughness = 0.4;
          this._disposables.push(signTex);
        }

        const mat = new THREE.MeshStandardMaterial(matOpts);
        this._disposables.push(mat);

        const mesh = new THREE.Mesh(this._sharedGeo.box, mat);
        mesh.scale.set(sx, sy, sz);
        mesh.castShadow = typ !== 'golv';
        mesh.receiveShadow = true;
        group.add(mesh);
        primaryMesh = mesh;
        meshParts.push({ mesh, normalMat: mat, wireOverlay: null });

        // Diskreta kantlinjer på möbler & props + cyan tilltro-wireframe för alla lådobjekt
        const edgeGeo = new THREE.EdgesGeometry(this._sharedGeo.box);
        this._disposables.push(edgeGeo);

        if (typ !== 'golv' && typ !== 'vagg') {
          const edgeMat = new THREE.LineBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: typ === 'skylt' ? 0.30 : 0.16,
          });
          normalEdges = new THREE.LineSegments(edgeGeo, edgeMat);
          normalEdges.scale.set(sx * 1.002, sy * 1.002, sz * 1.002);
          group.add(normalEdges);
          this._disposables.push(edgeMat);
        }

        tilltroEdges = new THREE.LineSegments(edgeGeo, this._ghostEdgeMat);
        tilltroEdges.scale.set(sx * 1.005, sy * 1.005, sz * 1.005);
        tilltroEdges.visible = false;
        group.add(tilltroEdges);
      }

      // 3D-etikett över props / skyltar / matshots om etikett finns
      let labelSprite = null;
      if (o.etikett && typ !== 'golv' && typ !== 'vagg') {
        labelSprite = makeLabelSprite(o.etikett, labelAccent, 0.14);
        labelSprite.position.set(0, 0, labelZ);
        labelSprite.visible = this.showLabels;
        group.add(labelSprite);
        this._disposables.push(labelSprite.material, labelSprite.userData._disposableTexture);
      }

      this.objektGroup.add(group);
      this._objektEntries.push({
        id: o.id,
        typ,
        group,
        mesh: primaryMesh,
        meshParts,
        normalEdges,
        tilltroEdges,
        tilltroStatic: normalizeTilltroStatus(o.tilltro),
        labelSprite,
        synlig_ut: o.synlig_ut || null,
      });
    }
  }

  _resolveObjectTilltro(entry) {
    const k = this.kroppsKontrakt;
    if (k && entry.id) {
      let fromObj = null;
      if (Array.isArray(k.objekt)) {
        const hit = k.objekt.find((x) => x && x.id === entry.id);
        fromObj = hit?.tilltro ?? hit ?? null;
      } else {
        fromObj = k.objekt?.[entry.id] ?? k.objekt_tilltro?.[entry.id] ?? null;
      }
      const norm = normalizeTilltroStatus(fromObj);
      if (norm) return norm;
    }
    return entry.tilltroStatic || 'observerad';
  }

  _applyTilltroToObjects() {
    let ghostedObj = 0;
    for (let i = 0; i < this._objektEntries.length; i++) {
      const entry = this._objektEntries[i];
      const status = this._resolveObjectTilltro(entry);
      const ghost = this.showTilltro && isGhostedStatus(status);
      if (ghost) ghostedObj++;

      for (let j = 0; j < entry.meshParts.length; j++) {
        const part = entry.meshParts[j];
        part.mesh.material = ghost ? this._ghostObjMat : part.normalMat;
        part.mesh.castShadow = !ghost && entry.typ !== 'golv';
        if (part.wireOverlay) {
          part.wireOverlay.visible = ghost;
        }
      }
      if (entry.normalEdges) {
        entry.normalEdges.visible = !ghost;
      }
      if (entry.tilltroEdges) {
        entry.tilltroEdges.visible = ghost;
      }
    }
    this._lastTilltroStats.objekt = ghostedObj;
  }

  _buildPersons(rorelse, personerMeta) {
    const ix = this._jointIndex;
    const harT1 = 'c_spine1' in ix && 'c_spine3' in ix && 'huvud_upp' in ix;
    const benSpec = (harT1 ? BEN1_KAPSLAR : BEN0_KAPSLAR).filter((b) => b[1] in ix && b[2] in ix);

    const skinMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#df9b7a'),
      roughness: 0.55,
      metalness: 0.02,
    });
    this._disposables.push(skinMat);

    for (const [pid, spar] of Object.entries(rorelse)) {
      if (!Array.isArray(spar) || spar.length === 0) continue;
      const meta = personerMeta[pid] || {};
      const fargHex = meta.farg || '#4c8bf5';
      const bodyColor = hexColor(fargHex, '#4c8bf5');

      const bodyMat = new THREE.MeshStandardMaterial({
        color: bodyColor,
        roughness: 0.44,
        metalness: 0.08,
      });
      const jointMat = new THREE.MeshStandardMaterial({
        color: bodyColor.clone().multiplyScalar(0.84),
        roughness: 0.50,
        metalness: 0.10,
      });
      const accentMat = new THREE.MeshStandardMaterial({
        color: bodyColor.clone().lerp(new THREE.Color('#ffffff'), 0.22),
        roughness: 0.40,
        metalness: 0.08,
      });
      const ghostBodyMat = new THREE.MeshStandardMaterial({
        color: bodyColor.clone().lerp(new THREE.Color('#4dd6ff'), 0.62),
        emissive: new THREE.Color('#135870'),
        emissiveIntensity: 0.38,
        roughness: 0.35,
        metalness: 0.08,
        transparent: true,
        opacity: 0.28,
        depthWrite: false,
      });
      const ghostJointMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color('#5ee0ff'),
        emissive: new THREE.Color('#135870'),
        emissiveIntensity: 0.32,
        roughness: 0.40,
        metalness: 0.08,
        transparent: true,
        opacity: 0.28,
        depthWrite: false,
      });
      this._disposables.push(bodyMat, jointMat, accentMat, ghostBodyMat, ghostJointMat);

      const group = new THREE.Group();
      group.name = `RIG_${pid}`;
      group.visible = false;

      // Bygg cylindrar + ändklot per ben (exakt kapsel-geometri utan deformation)
      const bones = [];
      for (const [namn, aName, bName, radius] of benSpec) {
        const cyl = new THREE.Mesh(this._sharedGeo.cyl, bodyMat);
        cyl.castShadow = true;
        cyl.receiveShadow = true;
        const wire = new THREE.Mesh(this._sharedGeo.cyl, this._ghostWireMat);
        wire.scale.set(1.03, 1.008, 1.03);
        wire.visible = false;
        cyl.add(wire);
        group.add(cyl);

        const capA = new THREE.Mesh(this._sharedGeo.jointSphere, jointMat);
        capA.scale.setScalar(radius);
        capA.castShadow = true;
        group.add(capA);

        const capB = new THREE.Mesh(this._sharedGeo.jointSphere, jointMat);
        capB.scale.setScalar(radius);
        capB.castShadow = true;
        group.add(capB);

        bones.push({
          namn,
          aName,
          bName,
          ia: ix[aName],
          ib: ix[bName],
          radius,
          cyl,
          wire,
          capA,
          capB,
        });
      }

      // Huvud + näsa enligt emit_bpy.py rad 246-261
      const headGroup = new THREE.Group();
      const headMesh = new THREE.Mesh(this._sharedGeo.headSphere, accentMat);
      headMesh.castShadow = true;
      headMesh.receiveShadow = true;
      const headWire = new THREE.Mesh(this._sharedGeo.headSphere, this._ghostWireMat);
      headWire.scale.setScalar(1.04);
      headWire.visible = false;
      headMesh.add(headWire);
      headGroup.add(headMesh);

      const noseMesh = new THREE.Mesh(this._sharedGeo.noseSphere, skinMat);
      noseMesh.castShadow = true;
      headGroup.add(noseMesh);
      group.add(headGroup);

      // Händer (lådor enligt emit_bpy.py rad 250)
      const hands = [];
      for (const sd of ['l', 'r']) {
        const wKey = `${sd}_wrist`;
        const mKey = `${sd}_hand_mitt`;
        const iKey = `${sd}_index1`;
        if (wKey in ix && mKey in ix) {
          const hg = new THREE.Group();
          const hm = new THREE.Mesh(this._sharedGeo.box, skinMat);
          hm.castShadow = true;
          const hw = new THREE.Mesh(this._sharedGeo.box, this._ghostWireMat);
          hw.scale.setScalar(1.04);
          hw.visible = false;
          hm.add(hw);
          hg.add(hm);
          group.add(hg);
          hands.push({
            group: hg,
            mesh: hm,
            wire: hw,
            wName: wKey,
            mName: mKey,
            iw: ix[wKey],
            im: ix[mKey],
            ii: iKey in ix ? ix[iKey] : -1,
          });
        }
      }

      // Fötter (lådor enligt emit_bpy.py rad 251)
      const feet = [];
      for (const sd of ['l', 'r']) {
        const fKey = `${sd}_foot`;
        const bKey = `${sd}_ball`;
        if (fKey in ix && bKey in ix) {
          const fg = new THREE.Group();
          const fm = new THREE.Mesh(this._sharedGeo.box, jointMat);
          fm.castShadow = true;
          fm.receiveShadow = true;
          const fw = new THREE.Mesh(this._sharedGeo.box, this._ghostWireMat);
          fw.scale.setScalar(1.04);
          fw.visible = false;
          fm.add(fw);
          fg.add(fm);
          group.add(fg);
          feet.push({
            group: fg,
            mesh: fm,
            wire: fw,
            fName: fKey,
            bName: bKey,
            ifoot: ix[fKey],
            iball: ix[bKey],
          });
        }
      }

      // Diskret roll-etikett över huvudet (A, B, C...)
      const badge = makeLabelSprite(meta.roll || pid, fargHex, 0.11);
      badge.visible = this.showLabels;
      group.add(badge);
      this._disposables.push(badge.material, badge.userData._disposableTexture);

      // Försortera rutor i varje spår på rutnummer u
      const sortedTracks = spar
        .filter((sp) => Array.isArray(sp?.rutor) && sp.rutor.length > 0)
        .map((sp) => ({
          tagning: sp.tagning || null,
          tilltro: sp.tilltro || null,
          ut: Array.isArray(sp.ut) ? sp.ut : [sp.rutor[0][0], sp.rutor[sp.rutor.length - 1][0] + 1],
          rutor: [...sp.rutor].sort((a, b) => a[0] - b[0]),
        }));

      this.personGroup.add(group);
      this._personRigs.set(pid, {
        pid,
        fargHex,
        group,
        bodyMat,
        jointMat,
        accentMat,
        skinMat,
        ghostBodyMat,
        ghostJointMat,
        metaTilltro: meta.tilltro || null,
        bones,
        headGroup,
        headMesh,
        headWire,
        noseMesh,
        hands,
        feet,
        badge,
        tracks: sortedTracks,
        hasHeadUp: 'c_head' in ix && 'huvud_upp' in ix,
        iHead: ix.c_head ?? -1,
        iHeadUp: ix.huvud_upp ?? -1,
        iNose: ix.nasa_mal ?? -1,
        iNeck: ix.c_neck ?? -1,
        iSpine0: ix.c_spine0 ?? -1,
        lastCenter: new THREE.Vector3(),
      });
    }
  }

  applyEnvironmentTheme(tema) {
    this.miljoTema = tema || null;
    const t = tema || STANDARD_TEMA;
    const ljus = t.ljus || STANDARD_TEMA.ljus;

    if (this.transparentBg) {
      this.scene.background = null;
      this.renderer.setClearColor(0x000000, 0);
    } else {
      const bgHex = t.bakgrund || t.bg || STANDARD_TEMA.bakgrund;
      this.scene.background = hexColor(bgHex, STANDARD_TEMA.bakgrund);
      this.renderer.setClearColor(this.scene.background, 1);
    }

    if (t.dimma && !this.transparentBg) {
      const fogColor = hexColor(
        typeof t.dimma === 'string' ? t.dimma : (t.dimma.farg || t.bakgrund || '#151820')
      );
      const near = typeof t.dimma === 'object' ? Number(t.dimma.nara ?? 6) : 6;
      const far = typeof t.dimma === 'object' ? Number(t.dimma.borta ?? 22) : 22;
      this.scene.fog = new THREE.Fog(fogColor, near, far);
    } else {
      this.scene.fog = null;
    }

    this.keyLight.color.copy(hexColor(ljus.nyckel_farg || STANDARD_TEMA.ljus.nyckel_farg));
    this.keyLight.intensity = Number(ljus.nyckel_styrka ?? STANDARD_TEMA.ljus.nyckel_styrka);

    this.fillLight.color.copy(hexColor(ljus.fyll_farg || STANDARD_TEMA.ljus.fyll_farg));
    this.fillLight.intensity = Number(ljus.fyll_styrka ?? STANDARD_TEMA.ljus.fyll_styrka);

    this.hemiLight.color.copy(hexColor(ljus.omgivning_farg || STANDARD_TEMA.ljus.omgivning_farg));
    this.hemiLight.intensity = Number(ljus.omgivning_styrka ?? STANDARD_TEMA.ljus.omgivning_styrka);
  }

  setTransparentBackground(enabled) {
    this.transparentBg = Boolean(enabled);
    this.applyEnvironmentTheme(this.miljoTema);
    this.renderFrame();
  }

  setShowLabels(enabled) {
    this.showLabels = Boolean(enabled);
    for (const entry of this._objektEntries) {
      if (entry.labelSprite) entry.labelSprite.visible = this.showLabels;
    }
    for (const rig of this._personRigs.values()) {
      if (rig.badge) rig.badge.visible = this.showLabels;
    }
    this.renderFrame();
  }

  setOrbitMode(enabled) {
    const next = Boolean(enabled);
    if (this.orbitMode === next) return;
    this.orbitMode = next;
    this.controls.enabled = next;

    if (next) {
      // Ställ OrbitControls target mot synliga personer (eller 2.2 m framför kameran) utan ryck
      const target = this._computeFocusTarget();
      this.controls.target.copy(target);
      this.camera.up.set(0, 0, 1);
      this.controls.update();
    } else {
      // Återställ direkt till 1:1 låst kamera för aktuell ruta
      this._updateCameraForFrame(this.currentFrame);
    }
    this.renderFrame();
  }

  resetCamera() {
    this.orbitMode = false;
    this.controls.enabled = false;
    this._updateCameraForFrame(this.currentFrame);
    this.renderFrame();
  }

  _computeFocusTarget() {
    const acc = new THREE.Vector3();
    let count = 0;
    for (const rig of this._personRigs.values()) {
      if (rig.group.visible) {
        acc.add(rig.lastCenter);
        count++;
      }
    }
    if (count > 0) {
      return acc.divideScalar(count);
    }
    // Fallback: 2.2 m framför kamerans -Z-riktning
    this._camFwd.set(0, 0, -1).applyQuaternion(this.camera.quaternion).normalize();
    return this.camera.position.clone().addScaledVector(this._camFwd, 2.2);
  }

  _findActiveTagning(u) {
    const tagningar = this.paket?.tagningar;
    if (!Array.isArray(tagningar) || tagningar.length === 0) return null;
    for (let i = 0; i < tagningar.length; i++) {
      const t = tagningar[i];
      if (!t?.ut || t.ut.length < 2) continue;
      if (u >= t.ut[0] - 1e-6 && u < t.ut[1]) return t;
    }
    // Vid exakt slutruta eller utanför: närmaste klampade tagning
    if (u < tagningar[0].ut[0]) return tagningar[0];
    return tagningar[tagningar.length - 1];
  }

  _updateCameraForFrame(u) {
    const t = this._findActiveTagning(u);
    this.activeTagning = t;
    if (!t || !t.kamera || !Array.isArray(t.kamera.nycklar) || t.kamera.nycklar.length === 0) {
      return;
    }
    const nycklar = t.kamera.nycklar;
    // Klampa strikt inom tagningens intervall så slerp aldrig går över hårt klipp
    const uClamped = Math.max(t.ut[0], Math.min(u, Math.max(t.ut[0], t.ut[1] - 1e-4)));

    let x, y, z, qw, qx, qy, qz, lins;
    if (t.kamera.statisk || nycklar.length === 1) {
      const k = nycklar[0];
      [, x, y, z, qw, qx, qy, qz, lins] = k;
    } else {
      const br = findBracket(nycklar, uClamped);
      const [k0, k1, alpha] = br;
      x = k0[1] + (k1[1] - k0[1]) * alpha;
      y = k0[2] + (k1[2] - k0[2]) * alpha;
      z = k0[3] + (k1[3] - k0[3]) * alpha;
      lins = k0[8] + (k1[8] - k0[8]) * alpha;

      // Paketet har [qw, qx, qy, qz], Three.js tar (qx, qy, qz, qw)!
      this._q0.set(k0[5], k0[6], k0[7], k0[4]).normalize();
      this._q1.set(k1[5], k1[6], k1[7], k1[4]).normalize();
      this._qOut.slerpQuaternions(this._q0, this._q1, alpha);
      qx = this._qOut.x;
      qy = this._qOut.y;
      qz = this._qOut.z;
      qw = this._qOut.w;
    }

    const safeLens = Math.max(8, Number(lins) || 50);
    // Vertikal FOV för Blender sensor_fit = HORIZONTAL:
    // fovV = 2 * atan((sensor_mm / (2 * lins_mm)) * (hojd / bredd)) * 180 / PI
    const fovV =
      2 * Math.atan((this.sensorMm / (2 * safeLens)) * (this.hojd / this.bredd)) * (180 / Math.PI);

    this._lastCamInfo = {
      pos: [x, y, z],
      quat: [qw, qx, qy, qz],
      lins_mm: safeLens,
      fov_v: fovV,
    };

    if (!this.orbitMode) {
      this.camera.up.set(0, 0, 1);
      this.camera.position.set(x, y, z);
      this.camera.quaternion.set(qx, qy, qz, qw).normalize();
      this.camera.fov = Math.max(8, Math.min(145, fovV));
      this.camera.aspect = this.bredd / this.hojd;
      this.camera.updateProjectionMatrix();
    }
  }

  _updateObjectsForFrame(u) {
    for (let i = 0; i < this._objektEntries.length; i++) {
      const entry = this._objektEntries[i];
      entry.group.visible = isVisibleAt(entry.synlig_ut, u, this.antalRutor);
    }
  }

  _sampleJoint(r0, r1, alpha, idx, outVec) {
    const base = 1 + 3 * idx;
    const x = (r0[base] + (r1[base] - r0[base]) * alpha) * 0.001;
    const y = (r0[base + 1] + (r1[base + 1] - r0[base + 1]) * alpha) * 0.001;
    const z = (r0[base + 2] + (r1[base + 2] - r0[base + 2]) * alpha) * 0.001;
    return outVec.set(x, y, z);
  }

  _setBasisMatrix(origin, dirY, targetZHint, outObj) {
    // Högerhänt bas: Y längs benet, Z mot targetZHint (vinkelrät mot Y), X = Y x Z
    this._vY.copy(dirY).normalize();
    this._vZ.copy(targetZHint).addScaledVector(this._vY, -targetZHint.dot(this._vY));
    if (this._vZ.lengthSq() < 1e-8) {
      // Fallback om parallell
      const alt = Math.abs(this._vY.z) < 0.9 ? UP_Z : UP_Y;
      this._vZ.copy(alt).addScaledVector(this._vY, -alt.dot(this._vY));
    }
    this._vZ.normalize();
    this._vX.crossVectors(this._vY, this._vZ).normalize();
    this._m4.makeBasis(this._vX, this._vY, this._vZ);
    outObj.position.copy(origin);
    outObj.quaternion.setFromRotationMatrix(this._m4);
  }

  _extractJointStatusFromBlock(block, jointName) {
    if (!block) return null;
    if (typeof block === 'string') return normalizeTilltroStatus(block);
    if (typeof block !== 'object') return null;

    if (block.leder && typeof block.leder === 'object' && jointName in block.leder) {
      const s = normalizeTilltroStatus(block.leder[jointName]);
      if (s) return s;
    }
    if (jointName in block) {
      const s = normalizeTilltroStatus(block[jointName]);
      if (s) return s;
    }
    if (UNDERBODY_JOINTS.has(jointName) && block.underkropp) {
      const s = normalizeTilltroStatus(block.underkropp);
      if (s) return s;
    }
    if (!UNDERBODY_JOINTS.has(jointName) && block.overkropp) {
      const s = normalizeTilltroStatus(block.overkropp);
      if (s) return s;
    }
    return normalizeTilltroStatus(block.status || block.standard || null);
  }

  _resolveJointTilltro(rig, jointName, tagningId, track) {
    // 1. Spår-specifik tilltro (ex. direkt från ingest_v2)
    if (track?.tilltro) {
      const s = this._extractJointStatusFromBlock(track.tilltro, jointName);
      if (s) return s;
    }

    // 2. Kroppskontrakt (per person & tagning enligt kropps_kontrakt/1)
    const k = this.kroppsKontrakt;
    if (k) {
      const pNode = k.personer?.[rig.pid] || null;
      const tid = tagningId || track?.tagning || null;
      const candidates = [
        tid && pNode?.tagningar?.[tid]?.tilltro,
        tid && pNode?.per_tagning?.[tid]?.tilltro,
        tid && k.tagningar?.[tid]?.personer?.[rig.pid]?.tilltro,
        tid && k.per_tagning?.[tid]?.[rig.pid]?.tilltro,
        tid && pNode?.tilltro?.[tid],
        pNode?.tilltro,
        tid && pNode?.tagningar?.[tid],
      ];
      for (const blk of candidates) {
        const s = this._extractJointStatusFromBlock(blk, jointName);
        if (s) return s;
      }
    }

    // 3. Fallback: personMeta.tilltro i scenpaketet
    if (rig.metaTilltro) {
      const tid = tagningId || track?.tagning || null;
      if (tid && typeof rig.metaTilltro === 'object' && rig.metaTilltro[tid]) {
        const s = this._extractJointStatusFromBlock(rig.metaTilltro[tid], jointName);
        if (s) return s;
      }
      const s = this._extractJointStatusFromBlock(rig.metaTilltro, jointName);
      if (s) return s;
    }

    return 'observerad';
  }

  _updatePersonsForFrame(u) {
    const activeTid = this.activeTagning?.id || null;
    let ghostedLimbs = 0;

    for (const rig of this._personRigs.values()) {
      // Hitta spår inom samma tagning (aldrig interpolering över klipp!)
      let track = null;
      for (let i = 0; i < rig.tracks.length; i++) {
        const tr = rig.tracks[i];
        const inRange =
          (u >= tr.ut[0] - 1e-6 && u < tr.ut[1]) ||
          (this.antalRutor > 0 && tr.ut[1] >= this.antalRutor && u >= this.antalRutor - 1e-3);
        if (!inRange) continue;
        if (activeTid && tr.tagning && tr.tagning === activeTid) {
          track = tr;
          break;
        }
        if (!track) track = tr;
      }

      if (!track || track.rutor.length === 0) {
        rig.group.visible = false;
        continue;
      }

      rig.group.visible = true;
      const uClamped = Math.max(track.ut[0], Math.min(u, Math.max(track.ut[0], track.ut[1] - 1e-4)));
      const [r0, r1, alpha] = findBracket(track.rutor, uClamped);
      const tidForTilltro = track.tagning || activeTid;

      // 1. Uppdatera alla kapselben + per-led tilltro-spökning (ärver sämsta ändled)
      for (let i = 0; i < rig.bones.length; i++) {
        const b = rig.bones[i];
        this._sampleJoint(r0, r1, alpha, b.ia, this._vA);
        this._sampleJoint(r0, r1, alpha, b.ib, this._vB);
        this._vDir.subVectors(this._vB, this._vA);
        const len = this._vDir.length();

        b.capA.position.copy(this._vA);
        b.capB.position.copy(this._vB);

        const ghostA = this.showTilltro && isGhostedStatus(this._resolveJointTilltro(rig, b.aName, tidForTilltro, track));
        const ghostB = this.showTilltro && isGhostedStatus(this._resolveJointTilltro(rig, b.bName, tidForTilltro, track));
        const ghostBone = ghostA || ghostB;
        if (ghostBone) ghostedLimbs++;

        b.cyl.material = ghostBone ? rig.ghostBodyMat : rig.bodyMat;
        b.cyl.castShadow = !ghostBone;
        if (b.wire) b.wire.visible = ghostBone;
        b.capA.material = ghostA ? rig.ghostJointMat : rig.jointMat;
        b.capA.castShadow = !ghostA;
        b.capB.material = ghostB ? rig.ghostJointMat : rig.jointMat;
        b.capB.castShadow = !ghostB;

        if (len > 1e-5) {
          b.cyl.visible = true;
          this._vMid.addVectors(this._vA, this._vB).multiplyScalar(0.5);
          b.cyl.position.copy(this._vMid);
          b.cyl.scale.set(b.radius, len, b.radius);
          b.cyl.quaternion.setFromUnitVectors(UP_Y, this._vDir.divideScalar(len));
        } else {
          b.cyl.visible = false;
        }
      }

      // 2. Uppdatera huvud + näsa (emit_bpy.py rad 246-261)
      const ghostHead =
        this.showTilltro &&
        (isGhostedStatus(this._resolveJointTilltro(rig, 'c_head', tidForTilltro, track)) ||
          isGhostedStatus(this._resolveJointTilltro(rig, 'c_neck', tidForTilltro, track)));
      if (ghostHead) ghostedLimbs++;
      rig.headMesh.material = ghostHead ? rig.ghostBodyMat : rig.accentMat;
      rig.headMesh.castShadow = !ghostHead;
      if (rig.headWire) rig.headWire.visible = ghostHead;
      rig.noseMesh.material = ghostHead ? rig.ghostJointMat : rig.skinMat;
      rig.noseMesh.castShadow = !ghostHead;

      if (rig.hasHeadUp && rig.iHead >= 0 && rig.iHeadUp >= 0) {
        const headPos = this._sampleJoint(r0, r1, alpha, rig.iHead, new THREE.Vector3());
        const headUpPos = this._sampleJoint(r0, r1, alpha, rig.iHeadUp, new THREE.Vector3());
        const upDir = this._vDir.subVectors(headUpPos, headPos);
        const Lb = Math.max(0.06, Math.min(0.22, upDir.length()));
        if (upDir.lengthSq() < 1e-8) upDir.set(0, 0, 1);

        let noseDir = new THREE.Vector3(0, -1, 0);
        if (rig.iNose >= 0) {
          const nosePos = this._sampleJoint(r0, r1, alpha, rig.iNose, new THREE.Vector3());
          noseDir.subVectors(nosePos, headPos);
        }
        this._setBasisMatrix(headPos, upDir, noseDir, rig.headGroup);
        rig.headMesh.position.set(0, Lb * 0.55, 0.015);
        rig.noseMesh.position.set(0, Lb * 0.35, 0.105);
        rig.noseMesh.visible = rig.iNose >= 0;

        // Etikett ovanför huvudet
        rig.badge.position.set(headUpPos.x, headUpPos.y, headUpPos.z + 0.22);
      } else if (rig.iHead >= 0) {
        const headPos = this._sampleJoint(r0, r1, alpha, rig.iHead, new THREE.Vector3());
        rig.headGroup.position.copy(headPos);
        rig.headGroup.quaternion.identity();
        rig.headMesh.position.set(0, 0, 0.05);
        rig.noseMesh.visible = false;
        rig.badge.position.set(headPos.x, headPos.y, headPos.z + 0.28);
      }

      // 3. Uppdatera händer (emit_bpy.py rad 250: sx=.022, sy=Lb*1.7, sz=.085, cy=Lb*.85)
      for (let i = 0; i < rig.hands.length; i++) {
        const h = rig.hands[i];
        const ghostHand =
          this.showTilltro &&
          (isGhostedStatus(this._resolveJointTilltro(rig, h.wName, tidForTilltro, track)) ||
            isGhostedStatus(this._resolveJointTilltro(rig, h.mName, tidForTilltro, track)));
        if (ghostHand) ghostedLimbs++;
        h.mesh.material = ghostHand ? rig.ghostBodyMat : rig.skinMat;
        h.mesh.castShadow = !ghostHand;
        if (h.wire) h.wire.visible = ghostHand;

        const wPos = this._sampleJoint(r0, r1, alpha, h.iw, new THREE.Vector3());
        const mPos = this._sampleJoint(r0, r1, alpha, h.im, new THREE.Vector3());
        const dir = this._vDir.subVectors(mPos, wPos);
        const Lb = Math.max(0.045, Math.min(0.14, dir.length()));
        if (dir.lengthSq() > 1e-8) {
          const rollHint = new THREE.Vector3(0, 0, 1);
          if (h.ii >= 0) {
            const idxPos = this._sampleJoint(r0, r1, alpha, h.ii, new THREE.Vector3());
            rollHint.subVectors(idxPos, wPos);
          }
          this._setBasisMatrix(wPos, dir, rollHint, h.group);
          h.mesh.scale.set(0.024, Lb * 1.7, 0.082);
          h.mesh.position.set(0, Lb * 0.85, 0);
          h.group.visible = true;
        } else {
          h.group.visible = false;
        }
      }

      // 4. Uppdatera fötter (emit_bpy.py rad 251: sx=.09, sy=Lb+.06, sz=.06, cy=Lb*.5)
      for (let i = 0; i < rig.feet.length; i++) {
        const f = rig.feet[i];
        const ghostFoot =
          this.showTilltro &&
          (isGhostedStatus(this._resolveJointTilltro(rig, f.fName, tidForTilltro, track)) ||
            isGhostedStatus(this._resolveJointTilltro(rig, f.bName, tidForTilltro, track)));
        if (ghostFoot) ghostedLimbs++;
        f.mesh.material = ghostFoot ? rig.ghostJointMat : rig.jointMat;
        f.mesh.castShadow = !ghostFoot;
        if (f.wire) f.wire.visible = ghostFoot;

        const fPos = this._sampleJoint(r0, r1, alpha, f.ifoot, new THREE.Vector3());
        const bPos = this._sampleJoint(r0, r1, alpha, f.iball, new THREE.Vector3());
        const dir = this._vDir.subVectors(bPos, fPos);
        const Lb = Math.max(0.08, Math.min(0.24, dir.length()));
        if (dir.lengthSq() > 1e-8) {
          this._setBasisMatrix(fPos, dir, UP_Z, f.group);
          f.mesh.scale.set(0.09, Lb + 0.06, 0.06);
          f.mesh.position.set(0, Lb * 0.5, 0);
          f.group.visible = true;
        } else {
          f.group.visible = false;
        }
      }

      // Spara personens ungefärliga centrum för OrbitControls-fokus
      if (rig.iSpine0 >= 0) {
        this._sampleJoint(r0, r1, alpha, rig.iSpine0, rig.lastCenter);
        rig.lastCenter.z += 0.35;
      }
    }

    this._lastTilltroStats.leder = ghostedLimbs;
  }

  _clampSpriteToCamera(sprite, parentVisible, tanHalfFov, aspect) {
    if (!sprite) return;
    if (!this.showLabels || !parentVisible) {
      sprite.visible = false;
      return;
    }
    sprite.getWorldPosition(this._vLabelWorld);
    const dist = this.camera.position.distanceTo(this._vLabelWorld);
    const safeDist = Math.max(0.25, dist);
    const visH = 2 * safeDist * tanHalfFov;
    const visW = visH * aspect;

    const baseH = sprite.userData.baseHeight || 0.14;
    const ar = Math.max(0.8, sprite.userData.aspectRatio || 2.5);

    // Klampa skalan så närbilder mot Hörnbänk/Hylla aldrig spränger eller klipps i 9:16-viewporten
    const maxHByWidth = (visW * 0.34) / ar;
    const maxHByHeight = visH * 0.044;
    const clampedH = Math.max(0.018, Math.min(baseH, maxHByWidth, maxHByHeight));
    sprite.scale.set(clampedH * ar, clampedH, 1);

    // Mjuk uttoning när kameraavståndet är närmare än 1.1 m
    if (dist < 1.1) {
      const fade = Math.max(0, Math.min(1, (dist - 0.50) / (1.1 - 0.50)));
      sprite.material.opacity = fade;
      sprite.visible = fade > 0.04;
    } else {
      sprite.material.opacity = 1.0;
      sprite.visible = true;
    }
  }

  _updateLabelsForCamera() {
    this.scene.updateMatrixWorld(false);
    const fovRad = THREE.MathUtils.degToRad(Math.max(8, Math.min(145, this.camera.fov || 60)));
    const tanHalfFov = Math.tan(fovRad * 0.5);
    const aspect = this.camera.aspect || (9 / 16);

    for (let i = 0; i < this._objektEntries.length; i++) {
      const entry = this._objektEntries[i];
      if (entry.labelSprite) {
        this._clampSpriteToCamera(entry.labelSprite, entry.group.visible, tanHalfFov, aspect);
      }
    }
    for (const rig of this._personRigs.values()) {
      if (rig.badge) {
        this._clampSpriteToCamera(rig.badge, rig.group.visible, tanHalfFov, aspect);
      }
    }
  }

  setTime(tidS) {
    const maxS = this.antalRutor > 0 ? this.antalRutor / this.fps : 0;
    this.currentTime = Math.max(0, maxS > 0 ? Math.min(Number(tidS) || 0, maxS) : Number(tidS) || 0);
    const uMax = Math.max(0, this.antalRutor - 1e-4);
    this.currentFrame = Math.max(0, Math.min(this.currentTime * this.fps, uMax));

    if (!this.paket) {
      this.renderFrame();
      return this.getSnapshot();
    }

    this._updateCameraForFrame(this.currentFrame);
    this._updateObjectsForFrame(this.currentFrame);
    this._updatePersonsForFrame(this.currentFrame);

    if (this.orbitMode) {
      this.controls.update();
    }
    this.renderFrame();
    return this.getSnapshot();
  }

  renderFrame() {
    if (this.orbitMode) {
      this.controls.update();
    }
    this._updateLabelsForCamera();
    this.renderer.render(this.scene, this.camera);
    return this.getSnapshot();
  }

  getSnapshot() {
    const synligaPersoner = [];
    for (const rig of this._personRigs.values()) {
      if (rig.group.visible) synligaPersoner.push(rig.pid);
    }
    return {
      tid_s: Number(this.currentTime.toFixed(4)),
      ruta: Number(this.currentFrame.toFixed(3)),
      fps: this.fps,
      antal_rutor: this.antalRutor,
      tagning_id: this.activeTagning?.id || null,
      synliga_personer: synligaPersoner,
      orbit_lage: this.orbitMode,
      tilltro_lage: this.showTilltro,
      tilltro_spokade: {
        objekt: this._lastTilltroStats.objekt,
        leder: this._lastTilltroStats.leder,
      },
      kamera: {
        pos: this._lastCamInfo.pos.map((v) => Number(v.toFixed(4))),
        quat_wxyz: this._lastCamInfo.quat.map((v) => Number(v.toFixed(5))),
        lins_mm: Number(this._lastCamInfo.lins_mm.toFixed(2)),
        fov_v: Number(this._lastCamInfo.fov_v.toFixed(2)),
      },
      bredd: this.bredd,
      hojd: this.hojd,
    };
  }

  dispose() {
    this._clearDynamicScene();
    for (const g of Object.values(this._sharedGeo)) g.dispose();
    this._ghostWireMat?.dispose?.();
    this._ghostEdgeMat?.dispose?.();
    this._ghostObjMat?.dispose?.();
    this.controls.dispose();
    this.renderer.dispose();
  }
}
