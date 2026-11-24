// Varianter av ett manus: varje scen filmas och spelas med ett uttryck ur uttrycksrummet.
// Delas av reglaget (#v) och bedömningarna (#bedom), så att det man bedömer är exakt det reglaget spelar.
import { kameraFor, delaId } from './uttryck.js'

// Hela klippet: val[i] är uttrycket för scen i ('original' = originalets kamera och agerande).
export function sattIhop(bas, val) {
  return {
    ...bas, id: `${bas.klipp}/uttryck`,
    scener: bas.scener.map((sc, i) => scenMed(sc, val[i], bas.lokal?.scener?.[i])),
  }
}

// En scen med ett uttryck: kameran byts (eller behålls), agerandet skalas (amp).
export function scenMed(sc, id, lokalScen = null) {
  const { kamera, amp, bakgrund } = delaId(id)
  const ny = kamera ? { ...sc, kamera: kameraFor(sc, kamera) } : sc
  const med = amp === 1 ? ny : { ...ny, handling: ny.handling.map(h => ({ ...h, amp })) }
  return bakgrund ? { ...med, handling: [...med.handling, statist(sc, lokalScen)] } : med
}

// Statisten: en person som går förbi bakom de andra, tvärs över scenen i gångfart (1,3 m/s),
// 0,9 m bakom huvudpersonerna men framför bakväggen. Kräver rollen 'statist' i manuset.
export function statist(sc, lokalScen) {
  const o = sc.origo ?? [0, 0, 0]
  const z = sc.handling.map(h => h.bana?.ramar?.[0]?.[1] ?? h.plats?.[1]).filter(Number.isFinite)
  const vagg = lokalScen?.vagg ? o[2] + lokalScen.vagg.z + 0.45 : -Infinity
  const zs = Math.max(vagg, (z.length ? Math.min(...z) : o[2] - 2.5) - 0.9)
  const bredd = 6.4
  return { roll: 'statist', rorelse: 'ga', start: 0, slut: bredd / 1.3, vag: [[o[0] - bredd / 2, zs], [o[0] + bredd / 2, zs]] }
}

// Bara scen i, med ett uttryck: för att jämföra två sätt att filma samma scen.
export function enScen(bas, i, id) {
  return { ...bas, id: `${bas.klipp}/s${i}/${id}`, scener: [{ ...scenMed(bas.scener[i], id, bas.lokal?.scener?.[i]), in: undefined }] }
}
