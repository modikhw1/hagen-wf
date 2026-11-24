// Steg 1 i inlärningen: kontots baslinje och klippets residual på bankens metadata,
// och kontroller av om residualen är en signal eller brus.
// node profil/kor.mjs  →  data/profil/baslinje.json
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { residualer, pearson, spearman, medel, median, effektPerKonto } from './baslinje.mjs'

const BANK = path.join(DATA, 'bank')
const UT = path.join(DATA, 'profil')
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const f2 = v => Number.isFinite(v) ? v.toFixed(2) : '–'
const pct = v => Number.isFinite(v) ? `${Math.round(v * 100)} %` : '–'

// 1. Residualer per konto ur listorna.
const rader = []
const konton = []
for (const namn of fs.readdirSync(BANK)) {
  const fil = path.join(BANK, namn, 'lista.json')
  if (!fs.existsSync(fil)) continue
  const lista = las(fil)
  const r = residualer(lista.klipp, { idag: lista.hamtad })
  konton.push({ konto: namn, listade: lista.klipp.length, giltiga: r.length, median_visningar: Math.round(10 ** median(r.map(x => x.logv))) })
  for (const x of r) rader.push({ konto: namn, ...x })
}

// 2. Sållningen som egenskaper (bara nedladdade klipp, valda på högt engagemang).
const sallning = new Map()
const SD = path.join(BANK, 'sallning')
for (const f of fs.readdirSync(SD)) {
  const s = las(path.join(SD, f))
  sallning.set(s.id, s)
}
for (const r of rader) r.s = sallning.get(`${r.konto}-${r.id}`) ?? null
const sallade = rader.filter(r => r.s)

// 3. Kontroller.
const allaV = rader.map(r => r.logv)
const mv = medel(allaV)
const ssTot = allaV.reduce((a, v) => a + (v - mv) ** 2, 0)
const ssRes = rader.reduce((a, r) => a + r.rv ** 2, 0)

const lagPar = []
for (const k of konton) {
  const rk = rader.filter(r => r.konto === k.konto)
  for (let i = 1; i < rk.length; i++) lagPar.push([rk[i - 1].rv, rk[i].rv])
}

const sd = v => Math.sqrt(medel(v.map(x => (x - medel(v)) ** 2)))
const kontroller = {
  klipp: rader.length,
  konton: konton.filter(k => k.giltiga > 0).length,
  r2_kontots_baslinje: 1 - ssRes / ssTot,
  rv_sd: sd(rader.map(r => r.rv)),
  rv_p10_p90: [rader.map(r => r.rv).sort((a, b) => a - b)[Math.floor(rader.length * 0.1)], rader.map(r => r.rv).sort((a, b) => a - b)[Math.floor(rader.length * 0.9)]],
  autokorr_lag1: pearson(lagPar.map(p => p[0]), lagPar.map(p => p[1])),
  rv_mot_gillanden: spearman(rader.map(r => r.rv), rader.map(r => r.rl)),
  rv_mot_kommentarer: spearman(rader.map(r => r.rv), rader.map(r => r.rc)),
  rv_mot_delningar: spearman(rader.map(r => r.rv), rader.map(r => r.rs)),
  gillanden_mot_delningar: spearman(rader.map(r => r.rl), rader.map(r => r.rs)),
  rv_mot_langd: spearman(rader.map(r => r.rv), rader.map(r => r.langd)),
  rv_mot_alder: spearman(rader.map(r => r.rv), rader.map(r => r.alder)),
  sallade: sallade.length,
  sallade_rv_median: median(sallade.map(r => r.rv)),
  alla_rv_median: median(rader.map(r => r.rv)),
}

// 4. Egenskaper: effekt inom konto, i båda tidshalvorna och utan ett konto i taget.
const egenskaper = {
  'kort (≤ 15 s)': r => Number.isFinite(r.langd) ? r.langd <= 15 : null,
  'typ: relaterbar sketch': r => r.s ? r.s.typ === 'relaterbar_sketch' : null,
  'typ: matporr och process': r => r.s ? r.s.typ === 'matporr_och_process' : null,
  'typ: direkt tilltal': r => r.s ? r.s.typ === 'direkt_tilltal' : null,
  'montage': r => r.s ? !!r.s.montage : null,
  'bildspel': r => r.s ? !!r.s.bildspel : null,
  'texttungt': r => r.s ? !!r.s.text_tung : null,
  'bildkvalitet ≥ 4': r => r.s && Number.isFinite(r.s.bildkvalitet) ? r.s.bildkvalitet >= 4 : null,
  'person i bild ≥ 80 %': r => r.s && Number.isFinite(r.s.andel_med_person) ? r.s.andel_med_person >= 0.8 : null,
  'minst två personer': r => r.s && Number.isFinite(r.s.personer_max) ? r.s.personer_max >= 2 : null,
}

function halvor(rk) {
  const perKonto = new Map()
  for (const r of rk) (perKonto.get(r.konto) ?? perKonto.set(r.konto, []).get(r.konto)).push(r)
  const tidig = [], sen = []
  for (const lista of perKonto.values()) {
    const s = [...lista].sort((a, b) => a.datum.localeCompare(b.datum))
    s.forEach((r, i) => (i < s.length / 2 ? tidig : sen).push(r))
  }
  return [tidig, sen]
}

function effekterFor(urval, falt) {
  const ut = {}
  for (const [namn, fn] of Object.entries(egenskaper)) {
    const bas = namn.startsWith('kort') ? rader : urval
    const hel = effektPerKonto(bas, fn, { falt })
    const [tidig, sen] = halvor(bas).map(h => effektPerKonto(h, fn, { falt }))
    const loo = hel.effekter.map(e => medel(hel.effekter.filter(x => x.konto !== e.konto).map(x => x.effekt)))
    const tecken = Math.sign(hel.medel)
    ut[namn] = {
      konton: hel.konton,
      medel: hel.medel,
      andelPositiv: hel.andelPositiv,
      tidig: tidig.medel,
      sen: sen.medel,
      halvorna_overens: Math.sign(tidig.medel) === Math.sign(sen.medel) && Math.sign(sen.medel) === tecken,
      loo_samma_tecken: loo.length ? loo.filter(v => Math.sign(v) === tecken).length / loo.length : NaN,
    }
  }
  return ut
}

// Stickprovet (profil/stickprov.mjs): slumpvisa klipp oavsett utfall.
const spFil = path.join(UT, 'stickprov.json')
const spIds = fs.existsSync(spFil) ? new Set(las(spFil).klipp.map(k => `${k.handtag}-${k.id}`)) : null
const stickprov = spIds ? sallade.filter(r => spIds.has(`${r.konto}-${r.id}`)) : []
kontroller.stickprov = stickprov.length
kontroller.stickprov_rv_median = median(stickprov.map(r => r.rv))

const effekter = { urval: Object.fromEntries(['rv', 'rl', 'rs'].map(f => [f, effekterFor(sallade, f)])) }
if (stickprov.length) effekter.stickprov = Object.fromEntries(['rv', 'rl', 'rs'].map(f => [f, effekterFor(stickprov, f)]))

fs.mkdirSync(UT, { recursive: true })
fs.writeFileSync(path.join(UT, 'baslinje.json'), JSON.stringify({ skapad: new Date().toISOString(), kontroller, effekter, konton, rader: rader.map(({ s, ...r }) => r) }, null, 1) + '\n')

// 5. Rapport.
const k = kontroller
console.log(`${k.klipp} klipp från ${k.konton} konton (minst 14 dagar gamla, med visningar)`)
console.log(`Kontots rullande baslinje förklarar ${pct(k.r2_kontots_baslinje)} av variansen i log-visningar`)
console.log(`Residual rv (log10): sd ${f2(k.rv_sd)}, p10–p90 ${f2(k.rv_p10_p90[0])} till ${f2(k.rv_p10_p90[1])}`)
console.log(`Autokorrelation mellan grannklipp: ${f2(k.autokorr_lag1)}`)
console.log(`rv mot gillanden/visning ${f2(k.rv_mot_gillanden)}, kommentarer ${f2(k.rv_mot_kommentarer)}, delningar ${f2(k.rv_mot_delningar)}; gillanden mot delningar ${f2(k.gillanden_mot_delningar)}`)
console.log(`rv mot längd ${f2(k.rv_mot_langd)}, mot ålder ${f2(k.rv_mot_alder)}`)
console.log(`Sållade ${k.sallade}: median rv ${f2(k.sallade_rv_median)} (alla ${f2(k.alla_rv_median)})`)
if (stickprov.length) console.log(`Stickprov ${k.stickprov} sållade: median rv ${f2(k.stickprov_rv_median)}`)
for (const [urval, perFalt] of Object.entries(effekter)) {
  for (const [falt, eff] of Object.entries(perFalt)) {
    console.log(`\n${urval} · ${falt}\nEgenskap                     konton  effekt  pos   tidig   sen   halvor  loo`)
    for (const [n, e] of Object.entries(eff)) {
      console.log(`${n.padEnd(28)} ${String(e.konton).padStart(5)}  ${f2(e.medel).padStart(6)}  ${pct(e.andelPositiv).padStart(4)}  ${f2(e.tidig).padStart(6)}  ${f2(e.sen).padStart(5)}   ${e.halvorna_overens ? 'ja ' : 'nej'}    ${pct(e.loo_samma_tecken)}`)
    }
  }
}
