// node --test kalibrering/modell.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { trana, overens, korsvalidera, skala, nastaPar } from './modell.mjs'

// deterministisk slump
const rng = (s = 7) => () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646

function varld(nItems = 120, nBed = 300, brus = 0.3) {
  const r = rng()
  const items = Array.from({ length: nItems }, (_, i) => ({ id: `k${i % 30}#${i}`, e: { x1: r(), x2: r(), x3: r() } }))
  const sann = e => 2 * e.x1 - e.x2 // x3 spelar ingen roll
  const bedomningar = Array.from({ length: nBed }, () => {
    const a = items[Math.floor(r() * nItems)]
    const b = items[Math.floor(r() * nItems)]
    const d = sann(a.e) - sann(b.e) + (r() - 0.5) * brus
    return { a: a.id, b: b.id, val: Math.abs(d) < 0.03 ? 'lika' : d > 0 ? 'a' : 'b' }
  }).filter(b => b.a !== b.b)
  return { items, bedomningar, sann }
}

test('modellen återhittar en känd sanning', () => {
  const { items, bedomningar } = varld()
  const mod = trana({ items, bedomningar, namn: ['x1', 'x2', 'x3'] })
  const o = overens(mod, items, bedomningar)
  assert.ok(o.andel > 0.9, `överens ${o.andel}`)
  assert.ok(mod.w[0] > 0 && mod.w[1] < 0, `vikter ${mod.w}`)
  assert.ok(Math.abs(mod.w[2]) < Math.abs(mod.w[0]) / 3, 'x3 ska få liten vikt')
})

test('korsvalidering mäter på osedda klipp och håller hög nivå', () => {
  const { items, bedomningar } = varld()
  const cv = korsvalidera({ items, bedomningar, namn: ['x1', 'x2', 'x3'] })
  assert.ok(cv.andel > 0.85, `cv ${cv.andel}`)
})

test('utan bedömningar gäller startvikterna', () => {
  const { items } = varld()
  const mod = trana({ items, bedomningar: [], namn: ['x1', 'x2'], start: { x1: 1 } })
  assert.deepEqual(mod.w, [1, 0])
})

test('skalan går från 1 till 10 i nyttans ordning', () => {
  const { items, bedomningar } = varld()
  const mod = trana({ items, bedomningar, namn: ['x1', 'x2', 'x3'] })
  const s = [...skala(mod, items).values()].sort((a, b) => a.u - b.u)
  assert.equal(s[0].steg, 1)
  assert.equal(s.at(-1).steg, 10)
})

test('nästa par är inte redan bedömt', () => {
  const { items, bedomningar } = varld(20, 30)
  const mod = trana({ items, bedomningar, namn: ['x1', 'x2'] })
  const p = nastaPar(mod, items, bedomningar, rng(3))
  const gjorda = new Set(bedomningar.map(b => [b.a, b.b].sort().join('|')))
  assert.ok(p && !gjorda.has([p.a, p.b].sort().join('|')))
})

test('korsvalidering per klipp: ett klipp finns aldrig både i träning och test', () => {
  const items = []
  for (const c of ['A', 'B', 'C', 'D', 'E']) for (let j = 0; j < 4; j++) items.push({ id: `${c}#${j}`, e: { x: j + (c.charCodeAt(0) % 3) } })
  // par mellan klipp: A–B och A–C får inte låta A läcka mellan delar
  const bed = [['A#0', 'B#3'], ['A#1', 'C#2'], ['B#0', 'B#3'], ['C#0', 'C#3'], ['D#1', 'D#2'], ['E#0', 'E#3'], ['A#0', 'A#3']].map(([a, b]) => ({ a, b, val: 'b' }))
  const r = korsvalidera({ items, bedomningar: bed, namn: ['x'], start: { x: 1 }, k: 5 })
  // bara par inom samma klipp kan testas (5 st); par mellan klipp hamnar aldrig i ett test
  assert.equal(r.n, 5)
  assert.equal(r.grupper, 5)
})
