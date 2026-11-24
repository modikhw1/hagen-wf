// Harness steg 4a (4 nov 2026): matchning av biblioteket (formatkort v4) mot kundprofiler.
// Matchningen görs i två steg, och varje beslut får ett skäl så att CM kan se varför.
//
// Hårda grindar, där klippet faller bort:
//   zon ute; verksamhet utan överlapp; segment premium eller kedja hos en kund i ett annat segment;
//   fler personer än kunden brukar ha; mer efterarbete än kunden klarar; skådespel högre än
//   personalens vana + 1 (ändrat 4 nov innan valideringen: tidigare gällde bara skådespel ≥ 4); stark persona när personan inte är kundens röda tråd; produktion > kundens + 1.
// Mjuk passform, i poäng med vikter från E4 och serietestet:
//   +0,25 huvudrollen kan spelas av kundens frontfigur, och kunden har en (serietestet: ×1,3–1,6)
//   +0,20 kött när kundens andel sketcher < 0,5; +0,15 stöd när kundens andel frågor < 0,15 (portföljen)
//   +0,10 visning med person i bild; −0,20 visning till trendljud (visningsregeln: ×2,0 mot ×0,58)
//   −0,10 trendljud som inte går att byta mot egna repliker
//   +0,10 zon kärna; +0,05 evergreen
//   +0,05 per lokaldel kunden har, högst +0,10
//   produkt: +0,05 för ingen, valfri, mat eller dryck; +0,10 när en specifik produkt matchar kundens
//   produkter (ord som överlappar); −0,15 när den inte matchar
//   +0,10 skådespel ≤ 3 hos en kund med personal_spelar ≤ 2 (lågt tröskelvärde för ovan personal)
//
//   node format/h-match.mjs
// Resultat: data/format/harness/match/<konto>.json (alla klipp med poäng, skäl och grindar)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const H = path.join(DATA, 'format', 'harness'), UT = path.join(H, 'match')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
// Hyllan är kurerad: för klipp som ägaren har bedömt gäller ägarens zon (ja → kärna, villkorat → mitten,
// nej → ute). Modellens zon gäller för resten. v4 missade bland annat metaskämtet i klipp 14.
const agare = las(path.join(DATA, 'format', 'kalib', 'agare.json')).klipp, kalib = las(path.join(DATA, 'format', 'kalib', 'urval.json'))
const AGZON = { ja: 'karna', villkorat: 'mitten', nej: 'ute' }
const kort = fs.readdirSync(path.join(H, 'v4')).map(f => las(path.join(H, 'v4', f))).map(k => { const nr = kalib.findIndex(x => x.id === k.id) + 1; const o = nr ? agare[nr] : null; return o ? { ...k, zon_modell: k.zon, zon: AGZON[o.bibliotek], zon_kalla: 'ägaren' } : { ...k, zon_kalla: 'modellen' } })
const kunder = fs.readdirSync(path.join(H, 'kunder')).map(f => las(path.join(H, 'kunder', f)))
const FAMILJ = { restaurang: 'mat', snabbmat: 'mat', finare_restaurang: 'mat', kafe: 'kafe', bar: 'bar', butik: 'butik', aktivitet: 'aktivitet' }
const NIVA = { ingen: 0, enkel: 1, mall: 2, avancerad: 3 }
const ord = t => new Set((t ?? '').toLowerCase().replace(/[^a-zåäöé ]/g, ' ').split(/\s+/).filter(w => w.length > 3))

export function matcha(k, p, u) {
  const grind = [], skal = []
  let poang = 0
  const kr = k.krav
  if (k.zon === 'ute') grind.push('zon ute')
  const fam = new Set(kr.verksamheter.map(v => FAMILJ[v]))
  if (!fam.has(FAMILJ[p.verksamhet]) && !(FAMILJ[p.verksamhet] === 'bar' && fam.has('mat')) && !(FAMILJ[p.verksamhet] === 'kafe' && fam.has('mat'))) grind.push(`verksamhet (${kr.verksamheter.join('/')} mot ${p.verksamhet})`)
  if ((kr.segment === 'premium' || kr.segment === 'kedja') && p.segment !== kr.segment) grind.push(`segment ${kr.segment}`)
  if (kr.personer_min > p.max_personer) grind.push(`${kr.personer_min} personer mot ${p.max_personer}`)
  if (NIVA[kr.redigering] > NIVA[p.redigering]) grind.push(`efterarbete ${kr.redigering} mot ${p.redigering}`)
  if (kr.skadespel > p.personal_spelar + 1) grind.push(`skådespel ${kr.skadespel} mot personal ${p.personal_spelar}`)
  if (kr.persona === 'stark' && !p.stark_persona_rod_trad) grind.push('stark persona utan röd tråd')
  if (kr.produktion > p.produktion + 1) grind.push(`produktion ${kr.produktion} mot ${p.produktion}`)

  if (kr.frontfigur.passar && p.frontfigurer.length) { poang += 0.25; skal.push(`frontfiguren ${p.frontfigurer[0].etikett} kan ta rollen som ${kr.frontfigur.roll}`) }
  if (k.funktion === 'kott' && u.lager.andel_sketch < 0.5) { poang += 0.2; skal.push(`fyller luckan kött (sketcher ${Math.round(100 * u.lager.andel_sketch)} %)`) }
  if (k.funktion === 'stod' && u.lager.andel_uppmaning + u.lager.andel_erbjudande < 0.15) { poang += 0.15; skal.push('fyller luckan fråga till publiken') }
  if (k.regler.visning_med_person && u.lager.matandel >= 1.5 && k.funktion !== 'kott') { poang += 0.1; skal.push('visning med person i bild') }
  if (k.regler.trendljud_i_visning) { poang -= 0.2; skal.push('visning till trendljud (−)') }
  if (kr.ljud === 'trendljud' && !kr.trendljud_utbytbart) { poang -= 0.1; skal.push('trendljud som inte går att byta (−)') }
  if (k.zon === 'karna') { poang += 0.1; skal.push('kärnhyllan') }
  if (k.evergreen) poang += 0.05
  const lok = kr.lokal.filter(l => l !== 'ingen_sarskild' && p.lokal.includes(l))
  if (lok.length) { poang += Math.min(0.1, 0.05 * lok.length); skal.push(`lokal: ${lok.join(', ')}`) }
  if (['ingen', 'valfri', 'mat', 'dryck'].includes(kr.produkt)) poang += 0.05
  else if (kr.produkt === 'specifik' || kr.produkt === 'varor') {
    const a = ord(kr.produkt_typ), bb = ord(p.produkter)
    if ([...a].some(w => [...bb].some(x => x.startsWith(w.slice(0, 5)) || w.startsWith(x.slice(0, 5))))) { poang += 0.1; skal.push(`produkt: ${kr.produkt_typ}`) }
    else { poang -= 0.15; skal.push(`kräver ${kr.produkt_typ} (−)`) }
  }
  if (kr.skadespel <= 3 && p.personal_spelar <= 2) { poang += 0.1; skal.push('låg tröskel för ovan personal') }
  if (kr.situation !== 'vardag') skal.push(`situation: ${kr.situation}`)
  return { id: k.id, konto: k.konto, url: k.url, zon: k.zon, funktion: k.funktion, karna: k.karna, poang: +poang.toFixed(2), godkand: grind.length === 0, grind, skal }
}

if (process.argv[1]?.endsWith('h-match.mjs')) {
  for (const { konto, profil: p, underlag: u } of kunder) {
    const res = kort.filter(k => k.konto !== konto).map(k => matcha(k, p, u)).sort((a, b) => (b.godkand - a.godkand) || (b.poang - a.poang))
    fs.writeFileSync(path.join(UT, `${konto}.json`), JSON.stringify({ konto, profil: p, resultat: res }, null, 1))
    const ok = res.filter(r => r.godkand)
    console.log(`\n== ${konto} (${p.verksamhet}, ${p.segment}, frontfigurer ${p.frontfigurer.length}, spelar ${p.personal_spelar}): ${ok.length} av ${res.length} klarar grindarna`)
    for (const r of ok.slice(0, 5)) console.log(`  ${r.poang.toFixed(2)} ${r.zon}/${r.funktion} @${r.konto}: ${r.karna.slice(0, 80)} | ${r.skal.slice(0, 3).join('; ')}`)
    const vanligaste = Object.entries(res.flatMap(r => r.grind.map(g => g.split(' (')[0].replace(/[0-9]+ /g, ''))).reduce((m, g) => ({ ...m, [g]: (m[g] ?? 0) + 1 }), {})).sort((a, b) => b[1] - a[1]).slice(0, 4)
    console.log('  vanligaste grindar:', vanligaste.map(([g, c]) => `${g} ${c}`).join(', '))
  }
}
