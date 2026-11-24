// node --test analys/
// Reglerna i tolka.mjs, med fall tagna ur riktiga klipp (2026-10-31).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { klassaKlipp, scenindelning, utsnittFor, kameraOrd } from './tolka.mjs'

test('riktigt scenbyte: låg likhet och starkt klipp (basso, 3,17 s)', () => {
  const k = klassaKlipp([{ t: 3.167, styrka: 0.392 }], [{ inliers: 9, inl: 0.033, skala: 1.005 }])
  assert.equal(k[0].typ, 'scen')
})

test('zoomryck: samma uppställning, inzoomad (blackstone, 11,2 s)', () => {
  const k = klassaKlipp([{ t: 11.2, styrka: 0.389 }], [{ inliers: 60, inl: 0.112, skala: 0.874 }])
  assert.equal(k[0].typ, 'zoomryck')
})

test('hoppklipp: samma uppställning, samma skala (blackstone, 13,2 s)', () => {
  const k = klassaKlipp([{ t: 13.2, styrka: 0.145 }], [{ inliers: 120, inl: 0.25, skala: 1.001 }])
  assert.equal(k[0].typ, 'hopp')
})

test('svag kandidat med låg likhet är inget klipp', () => {
  const k = klassaKlipp([{ t: 5, styrka: 0.18 }], [{ inliers: 3, inl: 0.01 }])
  assert.equal(k[0].typ, 'svag')
})

test('kandidater tätare än 0,15 s slås ihop', () => {
  const k = klassaKlipp([{ t: 4, styrka: 0.35 }, { t: 4.1, styrka: 0.6 }], [{}, {}])
  assert.equal(k.length, 1)
  assert.equal(k[0].styrka, 0.6)
})

test('bitar kortare än 0,5 s blir inskott i grannscenen', () => {
  const klipp = [{ t: 3, typ: 'scen' }, { t: 3.3, typ: 'scen' }, { t: 7, typ: 'scen' }]
  const s = scenindelning(10, klipp)
  assert.deepEqual(s.map(x => [x.start, x.slut]), [[0, 3.3], [3.3, 7], [7, 10]])
  assert.equal(klipp[0].typ, 'inskott')
})

test('montage: flera inskott i rad blir en scen', () => {
  const klipp = [1, 1.3, 1.6, 1.9, 2.2].map(t => ({ t, typ: 'scen' }))
  const s = scenindelning(5, klipp)
  assert.ok(s.some(x => x.montage))
})

test('utsnitt ur synliga punkter', () => {
  const lm = new Array(99).fill(0)
  const syns = (i, x = 0.5, y = 0.5) => { lm[i * 3] = x; lm[i * 3 + 1] = y; lm[i * 3 + 2] = 0.9 }
  syns(0); syns(11); syns(12)
  assert.equal(utsnittFor(lm), 'nara')
  syns(23)
  assert.equal(utsnittFor(lm), 'halvbild')
  syns(27, 0.5, 0.98)
  assert.equal(utsnittFor(lm), 'total')
})

test('stativ: brus under golvet blir stilla, inte zoom', () => {
  const rutor = Array.from({ length: 280 }, () => ({ k: [0.0005, -0.0004, 0.05, 1.002] }))
  assert.deepEqual(kameraOrd(rutor, 10).ord, ['stilla'])
})

test('panorering höger: innehållet flyttar sig åt vänster', () => {
  const rutor = Array.from({ length: 30 }, () => ({ k: [-0.01, 0, 0, 1] }))
  assert.ok(kameraOrd(rutor, 10).ord.includes('pan höger'))
})

test('övergång: svag kandidat där bilden före och efter är olika (renderad tonad övergång, 7,1 s)', () => {
  const k = klassaKlipp([{ t: 7.1, styrka: 0.216 }], [{ inliers: 4, inl: 0.007, vid: { inliers: 3, inl: 0.005 } }])
  assert.equal(k[0].typ, 'overgang')
})

test('svag kandidat där bilden före och efter är samma uppställning förblir svag (snabb rörelse)', () => {
  const k = klassaKlipp([{ t: 4, styrka: 0.18 }], [{ inliers: 5, inl: 0.02, vid: { inliers: 80, inl: 0.2 } }])
  assert.equal(k[0].typ, 'svag')
})

test('en övergång delar scener', () => {
  const s = scenindelning(10, [{ t: 5, typ: 'overgang' }])
  assert.equal(s.length, 2)
})

test('ryck: jämn rörelse ger lågt, hackig högt, stilla 0', async () => {
  const { ryck } = await import('./tolka.mjs')
  const jamn = Array.from({ length: 20 }, () => [0.01, 0])
  const hackig = Array.from({ length: 20 }, (_, i) => [i % 2 ? 0.02 : -0.01, 0])
  const stilla = Array.from({ length: 20 }, () => [0, 0])
  assert.ok(ryck(jamn) < 0.05)
  assert.ok(ryck(hackig) > 0.5)
  assert.equal(ryck(stilla), 0)
})
