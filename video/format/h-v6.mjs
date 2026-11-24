// Harness v6 (4 nov 2026): två mått som inte blandas.
//   varde(c, L)  LeTrend-värde (preferens): grund() + ett MJUKT linjeräcke. Fortsättning på kundens strategi
//                väger hälften så mycket som i v5, och ett avsteg med högt grundvärde märks som medvetet.
//                Kantighet uppåt, tilltal hos en kund som aldrig talar till kameran, och fokus utan frontfigur
//                kvarstår som räcken. Förlagan som i v5.
//   nytta(id)    Förväntad nytta: E7:s helhetsfråga (1–10), data/format/e7/*.json.
// Med --las-pass6 låses v6:s prognoser för pass 6 i en egen fil, innan ägaren sett klippen.
//   node format/h-v6.mjs --las-pass6
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { grund, forlaga } from './h-match5.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const KANT = { familjar: 0, lekfull: 1, kantig: 2, vuxen: 3 }, TEMPO = { lugnt: 0, medel: 1, hogt: 2 }
export function linje6(c, L) {
  const s = c.sprak, d = []; let p = 0
  const vikt = c.grundvarde.hylla === 'karna' ? 0.25 : 1
  if (s.strategi === L.strategi) { p += vikt; d.push('kundens strategi') } else if (s.strategi === L.strategi_sekundar) p += vikt / 2
  else if (grund(c).p >= 4) d.push(`medvetet avsteg: ${s.strategi} hos en ${L.strategi}-kund, med högt grundvärde`)
  const dk = KANT[s.kantighet] - KANT[L.kantighet]
  if (dk > 0) { p -= s.kantighet === 'lekfull' ? 0.25 : dk; d.push(`kantigare än kunden (${s.kantighet})`) }
  const dt = TEMPO[L.tempo] - TEMPO[s.tempo]; if (dt > 0) p -= 0.5 * dt
  if (s.person === 'fokus' && !L.frontfigurer?.length) { p -= 2; d.push('kräver en frontfigur, kunden har ingen') }
  if (s.tilltal === 'till_kamera' && L.tilltal_antal / (L.klipp?.length || 10) < 0.2) { p -= 1; d.push('tilltal till kameran, som kunden sällan gör') }
  return { p, d }
}
export const varde = (c, L) => { const g = grund(c), l = linje6(c, L), f = forlaga(c, L); return { varde: g.p + l.p + f.p, skal: [...g.d, ...l.d, ...f.d], avsteg: l.d.some(x => x.startsWith('medvetet avsteg')) } }
const E7 = { ...las(path.join(F, 'e7', 'bibliotek.json')), ...las(path.join(F, 'e7', 'e6.json')) }
// E7-frågan låstes som nytta för pass 6, men replikerades inte i E6-R (+0,08). Den behålls bara för pass 6.
export const nytta = id => E7[id]?.varde ?? null
// Rättad förväntad nytta (efter E6-R): grundvärdet + eget ljud + person i visning, minus trendljud.
// Grunden är replikerad (+0,17 i båda urvalen), eget tal +0,16/+0,19, trendljud −0,16/−0,11, visning med person +0,20 (E6) och ×2 (E4).
export const nytta6 = c => grund(c).p + (c.krav.ljud === 'eget_tal' ? 1 : 0) - (c.krav.ljud === 'trendljud' ? 1 : 0) + (c.regler?.visning_med_person ? 0.5 : 0)

if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}` && process.argv.includes('--las-pass6')) {
  const P = path.join(H, 'pass6'), R = las(path.join(P, 'forregistrering.json')), ut = path.join(P, 'forregistrering-v6.json')
  if (fs.existsSync(path.join(P, 'agare.json'))) { console.log('ägarens svar finns redan: v6 kan inte låsas för pass 6'); process.exit(1) }
  if (fs.existsSync(ut)) { console.log('v6 är redan låst'); process.exit(0) }
  const kortFil = id => [path.join(H, 'v5', `${id}.json`), path.join(F, 'e6', 'kort', `${id}.json`)].find(fs.existsSync)
  const prognos = Object.fromEntries(R.kunder.map(k => { const L = las(path.join(H, 'linje', `${k}.json`)); return [k, R.prognos[k].map(x => { const v = varde(las(kortFil(x.id)), L); return { id: x.id, v6_varde: +v.varde.toFixed(2), avsteg: v.avsteg, v6_nytta: nytta(x.id), skal: v.skal } })] }))
  fs.writeFileSync(ut, JSON.stringify({
    last: new Date().toISOString() + ' (efter v5-låsningen, innan ägaren sett något klipp i pass 6)',
    prognos,
    HP6f: 'v6 LeTrend-värde korrelerar med ägarens passform minst lika starkt som v5 total (samma 15 par).',
    HP6g: 'v6 förväntad nytta (E7) korrelerar svagare med ägarens passform än v6 LeTrend-värde: nytta och preferens är olika mått.',
    HP6h: 'Inom de delade klippen ordnar v6 LeTrend-värde kunderna rätt minst lika ofta som v5 total.',
  }, null, 1))
  for (const k of R.kunder) console.log(`${k}: ${prognos[k].map(x => `${x.v6_varde}/${x.v6_nytta}${x.avsteg ? '*' : ''}`).join(' | ')}`)
}

// v6.2 (efter E9 och E9-R): kroken läses ur rutnätsvyn när den finns. nytta62 = nytta6 + krok ur rutnätet
// (stark 1, svag 0,5). Rutnätskorten ligger i e9/rutnat, e9/agare-rutnat, e9r/rutnat och karna-rutnat/kort.
const RUTNAT = ['e9/rutnat', 'e9/agare-rutnat', 'e9r/rutnat', 'karna-rutnat/kort', 'hyllor-rutnat/kort'].map(d => path.join(F, d))
export const rutnatKort = id => { for (const d of RUTNAT) { const f = path.join(d, `${id}.json`); if (fs.existsSync(f)) return las(f) } return null }
export const nytta62 = c => { const r = rutnatKort(c.id); return nytta6(c) + (r ? { stark: 1, svag: 0.5, ingen: 0 }[r.grundvarde.krok] : 0) }
