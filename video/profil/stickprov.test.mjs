import test from 'node:test'
import assert from 'node:assert/strict'
import { valjStickprov } from './stickprov.mjs'

const rader = Array.from({ length: 40 }, (_, i) => ({ konto: i < 30 ? 'a' : 'b', id: String(i), langd: i === 0 ? 3 : 20, alder: i === 1 ? 1200 : 100, rv: i / 10 }))

test('stickprovet är reproducerbart och håller sig till kontot', () => {
  const x = valjStickprov(rader, 'a', 10).map(r => r.id)
  assert.deepEqual(x, valjStickprov(rader, 'a', 10).map(r => r.id))
  assert.equal(x.length, 10)
  assert.ok(valjStickprov(rader, 'a', 10).every(r => r.konto === 'a'))
})

test('för korta och för gamla klipp är inte behöriga', () => {
  const ids = valjStickprov(rader, 'a', 100).map(r => r.id)
  assert.equal(ids.length, 28)
  assert.ok(!ids.includes('0') && !ids.includes('1'))
})

test('urvalet beror inte på utfallet', () => {
  const ids = valjStickprov(rader, 'a', 10).map(r => Number(r.id))
  assert.notDeepEqual(ids, [...ids].sort((p, q) => q - p).slice(0, 10))
})
