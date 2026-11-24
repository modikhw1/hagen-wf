import test from 'node:test'
import assert from 'node:assert/strict'
import { median, spearman, rullandeBaslinje, residualer, effektPerKonto } from './baslinje.mjs'

test('median och spearman', () => {
  assert.equal(median([3, 1, 2]), 2)
  assert.equal(median([4, 1, 2, 3]), 2.5)
  assert.equal(spearman([1, 2, 3, 4], [10, 20, 30, 400]), 1)
  assert.equal(spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1)
})

test('rullande baslinje utesluter klippet självt', () => {
  const b = rullandeBaslinje([1, 1, 1, 1, 1, 9], [1, 2, 3, 4, 5, 6], 5)
  assert.equal(b[5], 1)
  assert.equal(b[0], 1)
})

test('residual är noll för ett jämnt konto och positiv för ett klipp som sticker ut', () => {
  const klipp = Array.from({ length: 20 }, (_, i) => ({
    id: String(i), langd: 10, visningar: i === 10 ? 100_000 : 1000, gillanden: 50, kommentarer: 2, delningar: 1,
    datum: new Date(Date.UTC(2026, 0, 1 + i * 3)).toISOString().slice(0, 10),
  }))
  const r = residualer(klipp, { idag: '2026-12-01', k: 10 })
  assert.equal(r.length, 20)
  assert.ok(Math.abs(r.find(x => x.id === '10').rv - 2) < 1e-9)
  assert.equal(r.find(x => x.id === '3').rv, 0)
})

test('unga klipp och klipp utan visningar räknas inte', () => {
  const klipp = [
    ...Array.from({ length: 10 }, (_, i) => ({ id: String(i), visningar: 1000, datum: `2026-01-${String(i + 1).padStart(2, '0')}` })),
    { id: 'ung', visningar: 5, datum: '2026-11-30' },
    { id: 'tom', visningar: 0, datum: '2026-01-15' },
  ]
  const ids = residualer(klipp, { idag: '2026-12-01', k: 5 }).map(r => r.id)
  assert.ok(!ids.includes('ung'))
  assert.ok(!ids.includes('tom'))
})

test('effekt per konto kräver klipp på båda sidor', () => {
  const rader = [
    { konto: 'a', rv: 1, m: true }, { konto: 'a', rv: 1, m: true }, { konto: 'a', rv: 0, m: false }, { konto: 'a', rv: 0, m: false },
    { konto: 'b', rv: 1, m: true }, { konto: 'b', rv: 0, m: false },
  ]
  const e = effektPerKonto(rader, r => r.m)
  assert.equal(e.konton, 1)
  assert.equal(e.medel, 1)
  assert.equal(e.andelPositiv, 1)
})
