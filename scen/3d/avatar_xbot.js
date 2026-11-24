// Fas 4: neutral, färdig riggad avatar (Mixamo X Bot ur three.js-exemplen r170) styrd av de stabiliserade lederna.
// Samma gränssnitt som Character i meshes.js: root, update(frame, sourceCamera, placement), joints[33], grips, mouth, mouthOpen.
// Ingen likhet med källans skapare: neutral docka, en dämpad färg per roll, minimalt ansikte (ögon, bryn, mun).
//
// Retargeting (ingen T/A-pose-gissning): varje ben får en anatomisk ram mätt i dockans vilopose (primär + sekundär axel),
// och sätts i världen som  ram(mål) · ram(vila)⁻¹ · vila.  Lemmar jagar målpunkter från det FAKTISKA ledläget
// (nyckelben -> axel, överarm -> armbåge, underarm -> handled), så fel i bålen inte förs vidare ut i händerna.
// Proportioner: dockans ben sträcks per aktör till look.proportions (uppmätt i data/motion-3.json).
import * as THREE from 'three';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const V = (a) => new THREE.Vector3(...a);
const Q = () => new THREE.Quaternion();
const ROLLFÄRG = {A: '#b0644c', B: '#4f7099', C: '#5d7d66', guest: '#8a8174'};   // tröjans färg = rollen (casting), inte personens kläder
const HUD = '#d6c2aa', BYXOR = '#3a3e45', SKOR = '#2a2a2d', HÅR = '#3b332d';   // samma hårkalott för alla dockor (ingen frisyr kopieras)                         // samma neutrala ton för alla
const VOLYM = n => /Spine/.test(n) ? 0.030 : /Shoulder/.test(n) ? 0.022 : /Arm/.test(n) ? 0.018 : /Hips|UpLeg|Leg/.test(n) ? 0.006 : 0;   // m utåt längs normalen: lös tröja och ärmar, lika för alla (silhuett utan likhet)
const region = n => /Head|Neck|Eye/.test(n) || /Hand/.test(n) ? 'skin' : /Foot|Toe/.test(n) ? 'shoes' : /Hips|UpLeg|Leg/.test(n) ? 'bottom' : 'top';
const SKALA_POSE = {A: 1.65, B: 1.78, C: 1.78};   // samma som Character (posen är i aktörens verkliga storlek)
const SITT = {23: [.13, 0, 0], 24: [-.13, 0, 0], 25: [.14, -.13, .35], 26: [-.14, -.13, .35], 27: [.14, -.53, .37], 28: [-.14, -.53, .37], 31: [.14, -.55, .48], 32: [-.14, -.55, .48]};
const FINGRAR = {Thumb: [1, 2, 3, 4], Index: [5, 6, 7, 8], Middle: [9, 10, 11, 12], Ring: [13, 14, 15, 16], Pinky: [17, 18, 19, 20]};
let ANSIKTE = null;   // ansiktsdragens lägen i huvudbenets ram, mätta en gång (samma huvud för alla aktörer)

function basisQuat(x, y) {        // ortonormerad ram: x primär, y sekundär (ortogonaliseras), z = x × y
  const X = x.clone().normalize(), Y = y.clone().sub(X.clone().multiplyScalar(y.dot(X))).normalize(), Z = new THREE.Vector3().crossVectors(X, Y);
  return Q().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z));
}
const mitt = (a, b) => a.clone().add(b).multiplyScalar(.5);

export class XbotCharacter {
  static async create(spec, url = './modeller/Xbot.glb') { return new XbotCharacter(spec, await loader.loadAsync(url)); }
  static nyckel(spec) { const l = spec.look || {}; return JSON.stringify([l.roleColor, l.proportions, l.klädvolym, l.height, l.hår, l.hårfärg]); }   // ändras den byggs dockan om
  constructor(spec, gltf) {
    this.spec = spec; this.nyckel = XbotCharacter.nyckel(spec); this.root = new THREE.Group(); this.root.name = 'xbot-' + spec.id; this.root.userData.actor = spec.id;
    this.model = gltf.scene; this.root.add(this.model); this.bones = {}; this.grips = {}; this.mouthOpen = 0; this.meshes = [];
    const färg = {top: new THREE.Color(spec.look?.roleColor || ROLLFÄRG[spec.id] || ROLLFÄRG.guest), skin: new THREE.Color(HUD), bottom: new THREE.Color(BYXOR), shoes: new THREE.Color(SKOR)};
    this.model.traverse(o => {
      if (o.isBone) this.bones[o.name.replace(/^mixamorig:?/, '')] = o;
      if (o.isMesh) {
        o.frustumCulled = false; o.userData.actor = spec.id; this.meshes.push(o);
        const leder = /Joints/i.test(o.name + (o.material?.name || ''));
        if (o.isSkinnedMesh) this._kläd(o, färg, leder, spec.look?.klädvolym ?? 1);
        o.material = new THREE.MeshStandardMaterial({vertexColors: true, roughness: .8, metalness: 0});
      }
    });
    this.root.updateMatrixWorld(true);
    const p = n => this.bones[n].getWorldPosition(new THREE.Vector3());
    this.modelHöjd = p('HeadTop_End').y - Math.min(p('LeftToe_End').y, p('RightToe_End').y) + .02;
    this.proportioner = this._proportioner(spec.look?.proportions, (spec.look?.height || 1.75) / this.modelHöjd);
    this.restLocal = new Map(); this.restRel = {}; this.restPos = new Map();
    for (const [n, b] of Object.entries(this.bones)) { this.restLocal.set(b, b.quaternion.clone()); this.restPos.set(b, b.position.clone()); this.restRel[n] = b.getWorldQuaternion(Q()); }
    // anatomiska ramar i vila (primär, sekundär axel)
    const upp = mitt(p('LeftArm'), p('RightArm')).sub(mitt(p('LeftUpLeg'), p('RightUpLeg')));
    const fram = V([0, 0, 1]), huvudUpp = p('HeadTop_End').sub(p('Head'));
    this.ram = {Hips: basisQuat(p('LeftUpLeg').sub(p('RightUpLeg')), upp), Spine2: basisQuat(p('LeftArm').sub(p('RightArm')), upp), Head: basisQuat(huvudUpp, fram)};
    for (const s of ['Left', 'Right']) {
      const h = this.bones[s + 'Hand'] && this.bones[s + 'HandMiddle1'] && this.bones[s + 'HandIndex1'] && this.bones[s + 'HandPinky1'];
      if (h) this.ram[s + 'Hand'] = basisQuat(p(s + 'HandMiddle1').sub(p(s + 'Hand')), p(s + 'HandIndex1').sub(p(s + 'HandPinky1')));
    }
    // ansikte: en grupp på huvudbenet vars ram i vila är huvudets anatomiska (+y upp längs huvudet, +z framåt)
    const head = this.bones.Head; this.face = new THREE.Group(); head.add(this.face);
    const Y = huvudUpp.clone().normalize(), Z = fram.clone().sub(Y.clone().multiplyScalar(fram.dot(Y))).normalize(), X = new THREE.Vector3().crossVectors(Y, Z);
    const F = Q().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z));
    this.face.quaternion.copy(this.restRel.Head.clone().invert().multiply(F));
    this.face.scale.setScalar(1 / head.getWorldScale(new THREE.Vector3()).x);
    this.face.position.set(0, 0, 0); this.root.updateMatrixWorld(true);
    if (!ANSIKTE) ANSIKTE = this._mätAnsikte(p, Y, Z);
    const mat = c => new THREE.MeshStandardMaterial({color: c, roughness: .55});
    const ell = (c, d, s) => { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 12), mat(c)); m.position.fromArray(d.pos); m.quaternion.fromArray(d.q); m.scale.set(...s); m.userData.actor = spec.id; this.face.add(m); return m; };
    const k = ANSIKTE.k; this.k = k;
    this.eyes = [ANSIKTE.ögaV, ANSIKTE.ögaH].map(d => ell('#202226', d, [.0115 * k, .0135 * k, .004 * k]));
    this.brows = [ANSIKTE.brynV, ANSIKTE.brynH].map(d => ell('#2a2c30', d, [.02 * k, .0035 * k, .004 * k]));
    this.browBas = this.brows.map(b => [b.position.clone(), b.quaternion.clone()]);
    this.mouth = ell('#3a2626', ANSIKTE.mun, [.021 * k, .003 * k, .004 * k]);
    this.näsa = V(ANSIKTE.näsa); this.öron = [V(ANSIKTE.öraV), V(ANSIKTE.öraH)];
    // hår (look.hår: 'kort' som standard, 'ingen' stänger av): huvudets egen yta, uppblåst längs normalen, ovanför ett hårfäste
    // som lutar bakåt (55° från hjässan fram, 120° bak, 87,5° vid sidorna). Samma för alla dockor: ingen frisyr kopieras.
    if ((spec.look?.hår ?? 'kort') !== 'ingen') this._hår(spec);
    this.joints = [];
  }
  _kläd(mesh, färg, leder, build = 1) {   // build: klädvolymens multiplikator (look.klädvolym; silhuett, inte likhet)      // region per hörn ur skinvikterna (dominerande ben): färg + klädvolym längs normalen
    const g = mesh.geometry = mesh.geometry.clone(), si = g.attributes.skinIndex, sw = g.attributes.skinWeight, pos = g.attributes.position, nor = g.attributes.normal;
    const namn = mesh.skeleton.bones.map(b => b.name.replace(/^mixamorig:?/, '')), skala = new THREE.Vector3().setFromMatrixScale(mesh.bindMatrix).x || 1;
    const col = new Float32Array(pos.count * 3), c = new THREE.Color();
    for (let i = 0; i < pos.count; i++) {
      const vikt = {}; let d = 0;
      for (let k = 0; k < 4; k++) { const bn = namn[si.getComponent(i, k)] || '', w = sw.getComponent(i, k), r = region(bn); vikt[r] = (vikt[r] || 0) + w; d += w * VOLYM(bn); }
      const r = Object.entries(vikt).sort((a, b) => b[1] - a[1])[0][0];
      c.copy(färg[r]); if (leder) c.multiplyScalar(.82); col.set([c.r, c.g, c.b], i * 3);
      d = r === 'skin' ? 0 : d * build / skala;
      if (d && nor) pos.setXYZ(i, pos.getX(i) + nor.getX(i) * d, pos.getY(i) + nor.getY(i) * d, pos.getZ(i) + nor.getZ(i) * d);
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3)); pos.needsUpdate = true; g.boundingSphere = null; g.boundingBox = null; mesh.boundingSphere = null;
  }
  _hår(spec) {
    const kropp = this.meshes.find(m => m.isSkinnedMesh && !/Joints/i.test(m.name)); if (!kropp) return;
    const g0 = kropp.geometry, pos = g0.attributes.position, nor = g0.attributes.normal, si = g0.attributes.skinIndex, sw = g0.attributes.skinWeight;
    const namn = kropp.skeleton.bones.map(b => b.name.replace(/^mixamorig:?/, '')), skala = new THREE.Vector3().setFromMatrixScale(kropp.bindMatrix).x || 1;
    const h = ANSIKTE.huvud, c = V(h.c), a = THREE.MathUtils.degToRad(32.5), axel = V([0, Math.cos(a), -Math.sin(a)]), cosT = Math.cos(THREE.MathUtils.degToRad(87.5));
    const behåll = new Uint8Array(pos.count), v = new THREE.Vector3();
    for (let i = 0; i < pos.count; i++) {
      let w = 0; for (let k = 0; k < 4; k++) if (/^Head/.test(namn[si.getComponent(i, k)] || '')) w += sw.getComponent(i, k);
      if (w < .6) continue;
      v.fromBufferAttribute(pos, i).applyMatrix4(kropp.bindMatrix); this.face.worldToLocal(v);   // vila = bindpose
      if (v.sub(c).normalize().dot(axel) > cosT) behåll[i] = 1;
    }
    const idx = g0.index ? g0.index.array : [...Array(pos.count).keys()], tri = [];
    for (let t = 0; t < idx.length; t += 3) if (behåll[idx[t]] && behåll[idx[t + 1]] && behåll[idx[t + 2]]) tri.push(idx[t], idx[t + 1], idx[t + 2]);
    const g = new THREE.BufferGeometry(), p2 = pos.array.slice(), d = .008 / skala, medel = new Map(), nyckel = i => `${pos.getX(i).toFixed(4)},${pos.getY(i).toFixed(4)},${pos.getZ(i).toFixed(4)}`;
    for (let i = 0; i < pos.count; i++) if (behåll[i]) { const k = nyckel(i), n = medel.get(k) || new THREE.Vector3(); n.x += nor.getX(i); n.y += nor.getY(i); n.z += nor.getZ(i); medel.set(k, n); }   // sömmar: samma normal för delade lägen
    for (let i = 0; i < pos.count; i++) if (behåll[i]) { const n = medel.get(nyckel(i)).clone().normalize(); p2[i * 3] += n.x * d; p2[i * 3 + 1] += n.y * d; p2[i * 3 + 2] += n.z * d; }
    g.setAttribute('position', new THREE.BufferAttribute(p2, 3)); g.setAttribute('normal', nor.clone()); g.setAttribute('skinIndex', si.clone()); g.setAttribute('skinWeight', sw.clone()); g.setIndex(tri);
    const hår = new THREE.SkinnedMesh(g, new THREE.MeshStandardMaterial({color: spec.look?.hårfärg || HÅR, roughness: .92}));
    hår.bind(kropp.skeleton, kropp.bindMatrix); hår.frustumCulled = false; hår.userData.actor = spec.id; kropp.parent.add(hår); this.hår = hår; this.meshes.push(hår);
  }
  _proportioner(prop, s) {       // sträck barnbenens lägen så att dockans mått (i slutlig skala s) blir aktörens
    if (!prop) return null;
    const B = this.bones, p = n => B[n].getWorldPosition(new THREE.Vector3()), upd = () => this.root.updateMatrixWorld(true), ut = {};
    const lös = (namn, mät, mål, nycklar) => {
      if (!mål || !nycklar.every(n => B[n])) return;
      const skala = f => { for (const n of nycklar) B[n].position.multiplyScalar(f); upd(); };
      let k0 = 1, m0 = mät(), k1 = mål / m0; skala(k1); let m1 = mät();
      for (let i = 0; i < 5 && Math.abs(m1 - mål) > 2e-4 && Math.abs(m1 - m0) > 1e-7; i++) { const k2 = k1 + (mål - m1) * (k1 - k0) / (m1 - m0); skala(k2 / k1); k0 = k1; m0 = m1; k1 = k2; m1 = mät(); }
      ut[namn] = {faktor: +k1.toFixed(3), mm: Math.round(m1 * 1000), mål_mm: Math.round(mål * 1000)};
    };
    lös('torso', () => mitt(p('LeftArm'), p('RightArm')).distanceTo(mitt(p('LeftUpLeg'), p('RightUpLeg'))) * s, prop.torso, ['Spine', 'Spine1', 'Spine2']);
    lös('shoulderWidth', () => p('LeftArm').distanceTo(p('RightArm')) * s, prop.shoulderWidth, ['LeftArm', 'RightArm']);
    lös('upperArm', () => (p('LeftArm').distanceTo(p('LeftForeArm')) + p('RightArm').distanceTo(p('RightForeArm'))) / 2 * s, prop.upperArm, ['LeftForeArm', 'RightForeArm']);
    lös('foreArm', () => (p('LeftForeArm').distanceTo(p('LeftHand')) + p('RightForeArm').distanceTo(p('RightHand'))) / 2 * s, prop.foreArm, ['LeftHand', 'RightHand']);
    return ut;
  }
  _mätAnsikte(p, Y, Z) {         // strålar från huvudets mitt mot ytan; dragen läggs strax utanför ytan, vända längs strålen
    const head = this.bones.Head, top = p('HeadTop_End'), hp = p('Head'), L = top.distanceTo(hp), k = L / .178;
    const c = hp.clone().lerp(top, .4), X = new THREE.Vector3().crossVectors(Y, Z), ray = new THREE.Raycaster();
    const ögonY = this.bones.LeftEye ? p('LeftEye').sub(c).dot(Y) : .0;
    const punkt = (x, y, z, ut = .0015) => {
      const dir = X.clone().multiplyScalar(x).addScaledVector(Y, y).addScaledVector(Z, z).normalize();
      ray.set(c.clone().addScaledVector(dir, L * 1.2), dir.clone().negate()); ray.far = L * 1.2;   // utifrån och in (framsidor)
      const hit = ray.intersectObjects(this.meshes, false)[0];
      const d = hit ? L * 1.2 - hit.distance : L * .55, w = c.clone().addScaledVector(dir, d + ut * k);
      const lok = this.face.worldToLocal(w.clone()), dl = this.face.worldToLocal(c.clone().add(dir)).sub(this.face.worldToLocal(c.clone())).normalize();
      const xp = new THREE.Vector3().crossVectors(V([0, 1, 0]), dl).normalize(), yp = new THREE.Vector3().crossVectors(dl, xp);   // vågrätt i ansiktsramen, normal = strålen
      return {pos: lok.toArray(), q: Q().setFromRotationMatrix(new THREE.Matrix4().makeBasis(xp, yp, dl)).toArray(), träff: !!hit, d};
    };
    const e = ögonY;
    const yta = (x, y, z) => {   // avstånd från mitten till huvudets yta längs riktningen (ramen X, Y, Z)
      const dir = X.clone().multiplyScalar(x).addScaledVector(Y, y).addScaledVector(Z, z).normalize();
      ray.set(c.clone().addScaledVector(dir, L * 1.2), dir.clone().negate()); ray.far = L * 1.2;
      const hit = ray.intersectObjects(this.meshes, false)[0]; return hit ? L * 1.2 - hit.distance : L * .5;
    };
    const huvud = {c: this.face.worldToLocal(c.clone()).toArray(), rx: (yta(1, 0, 0) + yta(-1, 0, 0)) / 2, ry: yta(0, 1, 0), rzF: yta(0, .25, 1), rzB: yta(0, .25, -1)};
    // +x i ramen = dockans vänster (dockan tittar mot +z)
    return {k, huvud, ögaV: punkt(.033, e, .08), ögaH: punkt(-.033, e, .08), brynV: punkt(.035, e + .03, .08), brynH: punkt(-.035, e + .03, .08),
      mun: punkt(0, e - .062, .08), näsa: punkt(0, e - .025, .08, 0).pos, öraV: punkt(.1, e - .01, 0, 0).pos, öraH: punkt(-.1, e - .01, 0, 0).pos};
  }
  _align(bone, child, from, to) {     // rotera benet (i världen) så att ben->barn pekar som from->to
    const a = bone.getWorldPosition(new THREE.Vector3()), b = child.getWorldPosition(new THREE.Vector3());
    const cur = b.sub(a).normalize(), des = to.clone().sub(from).normalize();
    if (cur.lengthSq() < 1e-8 || des.lengthSq() < 1e-8) return;
    const qw = Q().setFromUnitVectors(cur, des), bw = bone.getWorldQuaternion(Q()), pw = bone.parent.getWorldQuaternion(Q());
    bone.quaternion.copy(pw.invert().multiply(qw.multiply(bw))); bone.updateMatrixWorld(true);
  }
  _chase(bone, child, target) { this._align(bone, child, bone.getWorldPosition(new THREE.Vector3()), target); }
  _setWorld(bone, qWorld) { const pw = bone.parent.getWorldQuaternion(Q()); bone.quaternion.copy(pw.invert().multiply(qWorld)); bone.updateMatrixWorld(true); }
  _delta(namn, prim, sek) { return basisQuat(prim, sek).multiply(this.ram[namn].clone().invert()); }   // världsrotation från vila till mål
  update(frame, sourceCamera, placement) {
    const id = this.spec.id, l = this.spec.look || {}, B = this.bones, wp = n => B[n].getWorldPosition(new THREE.Vector3());
    for (const [b, q] of this.restLocal) { b.quaternion.copy(q); b.position.copy(this.restPos.get(b)); }
    const yaw = THREE.MathUtils.degToRad(placement.yaw || 0), höjd = l.height || 1.75;
    this.root.position.fromArray(placement.position); this.root.rotation.set(0, yaw, 0);
    this.root.scale.setScalar(höjd / this.modelHöjd); this.root.updateMatrixWorld(true);
    // målleder i världen (som Character): lokal = (x,-y,-z)·skala, sedan aktörens placering
    const charSkala = höjd / (SKALA_POSE[id] || 1.78), M = new THREE.Matrix4().compose(V(placement.position), Q().setFromAxisAngle(V([0, 1, 0]), yaw), V([charSkala, charSkala, charSkala]));
    const lok = frame.pose.map(a => new THREE.Vector3(a[0], -a[1], -a[2]));
    if (this.spec.seated) for (const [k, v] of Object.entries(SITT)) lok[k] = V(v);
    const T = lok.map(v => v.clone().applyMatrix4(M));
    const hipC = mitt(T[23], T[24]), shC = mitt(T[11], T[12]), upp = shC.clone().sub(hipC);
    // bål: höfter (orientering ur höftlinjen och ryggen), rygg fördelad mellan höft och bröst, bröst ur axellinjen
    const dH = this._delta('Hips', T[23].clone().sub(T[24]), upp), dC = this._delta('Spine2', T[11].clone().sub(T[12]), upp);
    this._setWorld(B.Hips, dH.clone().multiply(this.restRel.Hips));
    const höftMitt = mitt(wp('LeftUpLeg'), wp('RightUpLeg')), hw = wp('Hips').add(hipC.clone().sub(höftMitt));   // dockans höftleder på målets
    B.Hips.position.copy(B.Hips.parent.worldToLocal(hw)); B.Hips.updateMatrixWorld(true);
    this._setWorld(B.Spine, dH.clone().slerp(dC, 1 / 3).multiply(this.restRel.Spine));
    this._setWorld(B.Spine1, dH.clone().slerp(dC, 2 / 3).multiply(this.restRel.Spine1));
    this._setWorld(B.Spine2, dC.clone().multiply(this.restRel.Spine2));
    // rättning: vrid ryggen så att dockans axelmitt hamnar på målets (sedan bröstets orientering igen)
    const s0 = wp('Spine'), är = mitt(wp('LeftArm'), wp('RightArm')).sub(s0), bör = shC.clone().sub(s0);
    if (är.lengthSq() > 1e-8) this._setWorld(B.Spine, Q().setFromUnitVectors(är.normalize(), bör.normalize()).multiply(B.Spine.getWorldQuaternion(Q())));
    this._setWorld(B.Spine2, dC.clone().multiply(this.restRel.Spine2));
    // nacke mot huvudet, huvud ur ansiktets orientering mot källkameran (anatomisk ram: upp längs huvudet, fram)
    const näsa = T[0], öron = mitt(T[7], T[8]);
    this._chase(B.Neck, B.Head, öron.clone().lerp(näsa, .2));
    const fq = frame.face?.quaternion ? sourceCamera.quaternion.clone().multiply(Q().fromArray(frame.face.quaternion)) : null;
    const huvudQ = fq ? this._delta('Head', V([0, 1, 0]).applyQuaternion(fq), V([0, 0, 1]).applyQuaternion(fq)).multiply(this.restRel.Head) : null;
    if (huvudQ) this._setWorld(B.Head, huvudQ);
    // näsan på målets näsa: vrid nacken mot den och justera halsens längd (±20 %), huvudets orientering hålls
    for (let i = 0; i < 3; i++) {
      this.root.updateMatrixWorld(true);
      const n0 = wp('Neck'), är = this.face.localToWorld(this.näsa.clone()).sub(n0), bör = näsa.clone().sub(n0);
      if (är.lengthSq() < 1e-8) break;
      this._setWorld(B.Neck, Q().setFromUnitVectors(är.clone().normalize(), bör.clone().normalize()).multiply(B.Neck.getWorldQuaternion(Q())));
      const f = THREE.MathUtils.clamp(bör.length() / är.length(), .9, 1.1);
      B.Head.position.multiplyScalar(f); const lo = this.restPos.get(B.Head).length(); B.Head.position.setLength(THREE.MathUtils.clamp(B.Head.position.length(), lo * .75, lo * 1.35));
      if (huvudQ) this._setWorld(B.Head, huvudQ); else B.Head.updateMatrixWorld(true);
    }
    // titta mot (op titta): bara huvudet, kring huvudbenet, högst 80° från den uppmätta blicken
    if (placement.lookAt?.amount > 0) {
      const hp = wp('Head'), f2 = V(placement.lookAt.target).sub(hp).normalize(), nu = B.Head.getWorldQuaternion(Q());
      const mål = this._delta('Head', V([0, 1, 0]), f2).multiply(this.restRel.Head), vinkel = nu.angleTo(mål);
      const andel = vinkel > 1e-4 ? Math.min(placement.lookAt.amount, THREE.MathUtils.degToRad(80) / vinkel) : 0;
      this._setWorld(B.Head, nu.slerp(mål, andel));
    }
    // armar: nyckelben mot axeln, överarm mot armbågen, underarm mot handleden; hand och fingrar ur handdetektorn
    for (const [sida, s, e, w] of [['Left', 11, 13, 15], ['Right', 12, 14, 16]]) {
      if (B[sida + 'Shoulder']) this._chase(B[sida + 'Shoulder'], B[sida + 'Arm'], T[s]);
      this._chase(B[sida + 'Arm'], B[sida + 'ForeArm'], T[e]);
      this._chase(B[sida + 'ForeArm'], B[sida + 'Hand'], T[w]);
      const hand = frame.hands?.find(h => h.side === sida);
      if (hand) {
        const hp = hand.world.map(a => new THREE.Vector3(a[0], -a[1], -a[2]).applyQuaternion(Q().setFromAxisAngle(V([0, 1, 0]), yaw)));
        if (this.ram[sida + 'Hand']) this._setWorld(B[sida + 'Hand'], this._delta(sida + 'Hand', hp[9].clone().sub(hp[0]), hp[5].clone().sub(hp[17])).multiply(this.restRel[sida + 'Hand']));
        for (const [fn, idx] of Object.entries(FINGRAR)) for (let k = 0; k < 3; k++) {
          const b0 = B[`${sida}Hand${fn}${k + 1}`], b1 = B[`${sida}Hand${fn}${k + 2}`];
          if (b0 && b1) this._align(b0, b1, hp[idx[k]], hp[idx[k + 1]]);
        }
      }
      const gi = B[sida + 'HandIndex2'], gt = B[sida + 'HandThumb3'];
      this.grips[sida] = gi && gt ? mitt(gi.getWorldPosition(new THREE.Vector3()), gt.getWorldPosition(new THREE.Vector3())) : wp(sida + 'Hand');
    }
    // ben: jaga knä, fotled, tå
    for (const [sida, k, a, t] of [['Left', 25, 27, 31], ['Right', 26, 28, 32]]) {
      this._chase(B[sida + 'UpLeg'], B[sida + 'Leg'], T[k]); this._chase(B[sida + 'Leg'], B[sida + 'Foot'], T[a]);
      if (B[sida + 'ToeBase']) this._align(B[sida + 'Foot'], B[sida + 'ToeBase'], T[a], T[t]);
    }
    // ansikte: mun (jawOpen, extern kurva eller MediaPipe), ögonlock, bryn
    // grundnivån per aktör (motion.faceBaseline) dras av: ett vilande ansikte ska se neutralt ut, inte oroligt
    const rå = frame.face?.blendshapes || {}, bas = this.spec.motion?.faceBaseline || {};
    const bs = new Proxy({}, {get: (_, n) => n === 'jawOpen' ? (rå[n] || 0) : Math.max(0, ((rå[n] || 0) - (bas[n] || 0)) / Math.max(.3, 1 - (bas[n] || 0)))});
    const jaw = Math.max(0, Math.min(1, bs.jawOpen)); this.mouthOpen = jaw; const k = this.k;
    this.mouth.scale.set(k * (.021 + .006 * ((bs.mouthSmileLeft || 0) + (bs.mouthSmileRight || 0)) - .006 * (bs.mouthPucker || 0)), k * (.003 + .02 * jaw), k * .004);
    this.eyes.forEach((e, i) => e.scale.y = k * .0135 * Math.max(.1, 1 - (bs[i ? 'eyeBlinkRight' : 'eyeBlinkLeft'] || 0)));
    this.brows.forEach((b, i) => {   // [vänster, höger]; inre änden lyfts av browInnerUp
      const ned = bs[i ? 'browDownRight' : 'browDownLeft'];   // höjning = förvåning/fråga, sänkning + inåtlutning = irritation
      b.position.copy(this.browBas[i][0]); b.position.y += k * (.009 * bs.browInnerUp + .004 * (bs[i ? 'browOuterUpRight' : 'browOuterUpLeft']) - .007 * ned);
      b.quaternion.copy(this.browBas[i][1]).multiply(Q().setFromAxisAngle(V([0, 0, 1]), (i ? 1 : -1) * (.12 * bs.browInnerUp - .3 * ned)));
    });
    this.root.updateMatrixWorld(true);
    // leder för mätning (MediaPipe-index): benens världspositioner där avataren har dem, annars målet
    const j = T.map(v => v.clone());
    const karta = {11: 'LeftArm', 12: 'RightArm', 13: 'LeftForeArm', 14: 'RightForeArm', 15: 'LeftHand', 16: 'RightHand', 23: 'LeftUpLeg', 24: 'RightUpLeg', 25: 'LeftLeg', 26: 'RightLeg', 27: 'LeftFoot', 28: 'RightFoot', 31: 'LeftToeBase', 32: 'RightToeBase'};
    for (const [i, n] of Object.entries(karta)) if (B[n]) j[i] = wp(n);
    j[0] = this.face.localToWorld(this.näsa.clone()); j[7] = this.face.localToWorld(this.öron[0].clone()); j[8] = this.face.localToWorld(this.öron[1].clone());
    this.joints = j;
  }
}
