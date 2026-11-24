// Harness steg 3 (4 nov 2026): kundprofiler. Underlag per kund:
// - serien (data/format/serie[-r]/<konto>.json): frontfigurer, format, klippens roller, röd tråd och vad som saknas
// - Lite-lagren för kontots 14 E4-klipp: mix, kapacitet (bildkvalitet, effekter, proffsljus, klippning) och tilltal
// - strategitypen ur e4/typer.json
// Pro gör en strukturerad syntes på text. Endpointen kräver video, så en tom platshållare skickas med.
//
//   node format/h-kund.mjs
// Resultat: data/format/harness/kunder/<konto>.json (underlag + profil)
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { analyseraVideo } from '../typer/lovable.mjs'
import { LOKALDELAR, VERKSAMHETER, ROLLER } from './v4.mjs'

const F = path.join(DATA, 'format'), H = path.join(F, 'harness'), UT = path.join(H, 'kunder')
fs.mkdirSync(UT, { recursive: true })
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const { kunder } = las(path.join(H, 'urval.json'))
const e4 = las(path.join(F, 'e4', 'urval.json'))
const typer = las(path.join(F, 'e4', 'typer.json'))
const TYPNAMN = ['visning med trendljud', 'dialogsketch', 'tilltal och erbjudande', 'trendsketch utan säljande']
const tal = v => typeof v === 'boolean' ? (v ? 1 : 0) : v
const medel = a => a.reduce((s, x) => s + x, 0) / a.length

function underlag(konto) {
  const sf = ['serie', 'serie-r'].map(d => path.join(F, d, `${konto}.json`)).find(fs.existsSync)
  const serie = sf ? las(sf) : null
  const lite = e4.filter(k => k.konto === konto).map(k => path.join(F, 'e4', 'lager-gemini-3.1-flash-lite', `${k.id}.json`)).filter(fs.existsSync).map(las)
  const m = n => +medel(lite.map(x => tal(x[n]))).toFixed(2)
  const typ = typer.kluster.findIndex(c => c.konton.some(k => k.konto === konto))
  return {
    konto, strategityp: typ >= 0 ? TYPNAMN[typ] : 'okänd',
    serie: serie && { frontfigurer: serie.frontfigurer, format: serie.format, klipp: serie.klipp.map(c => `${c.nr}. ${c.roll}: ${c.vad}`), rod_trad: serie.rod_trad, saknas: serie.saknas, inside: serie.inside, planerat: serie.planerat },
    lager: { klipp: lite.length, kontotyp: [...new Set(lite.map(x => x.kontotyp))].join('/'), andel_tilltal: m('tilltal'), andel_sketch: m('roll'), humor: m('humor'), andel_person: m('andel_person'), personer: m('personer'), matandel: m('mat_andel'), andel_montage: m('montage'), andel_trendljud: m('trendljud'), andel_uppmaning: m('uppmaning'), andel_erbjudande: m('erbjudande'), bildkvalitet: m('bildkvalitet'), effekter: m('effekter'), andel_proffsljus: m('proffsljus'), klipp_per_video: m('klipp'), lokal_syns: m('lokal') },
  }
}

const s = (description, enumv) => ({ type: 'string', description, ...(enumv ? { enum: enumv } : {}) })
const n = (min, max, description) => ({ type: 'integer', minimum: min, maximum: max, description })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, description })
const schema = obj({
  verksamhet: s('Vilken sorts verksamhet.', VERKSAMHETER),
  beskrivning: s('Verksamheten i en mening: vad den säljer och hur den känns.'),
  segment: s('enkel (vardaglig lokal), premium (finare lokal med egen produktionskompetens) eller kedja (volym och budget).', ['enkel', 'premium', 'kedja']),
  frontfigurer: arr(obj({ etikett: s('Personens etikett ur serien.'), roll: s('Personens vanligaste roll.', ROLLER), styrka: s('Vad personen är bra på framför kameran, en mening.') }), 'Kontots återkommande personer, viktigast först. Tom lista om ingen återkommer.'),
  personal_spelar: n(1, 5, 'Hur villig och van personalen verkar vara att spela upp situationer och sketcher. 1 = gör det aldrig, 5 = gör det ofta och bra.'),
  max_personer: n(0, 6, 'Hur många personer som brukar kunna vara med i samma klipp.'),
  produktion: n(1, 5, 'Hur mycket produktionskompetens kontot visar: ljus, foto, klippning och effekter. 1 = bara telefon och en tagning, 5 = proffsig.'),
  redigering: s('Vilken nivå av efterarbete kontot klarar: ingen, enkel, mall eller avancerad.', ['ingen', 'enkel', 'mall', 'avancerad']),
  lokal: arr(s('', LOKALDELAR), 'Delar av lokalen som syns i klippen och går att använda.'),
  produkter: s('Vad som säljs: typiska rätter, drycker eller varor.'),
  persona: s('Kontots ton och persona, en mening.'),
  stark_persona_rod_trad: b('Är en stark persona (kaxig, provocerande, personlig) kontots röda tråd?'),
  aterkommande_format: arr(s('Ett format kontot redan kör.'), 'Format som redan återkommer.'),
  luckor: arr(s('En lucka.'), 'Det som saknas i mixen, med stöd i underlaget och i det LeTrend vet om utfall. 1–3 st.'),
  bor_undvikas: arr(s('En sak.'), 'Det som inte passar kontot, t.ex. sådant som kräver mer än kontot klarar eller går emot dess ton. 0–3 st.'),
})
const KUNSKAP = `Det LeTrend vet om utfall, mätt inom samma konto: personer i bild, en spelad situation, humor och direkt tilltal ger räckvidd. En matvisning med en person i bild når ungefär dubbelt så långt som en visning utan person, och med trendljud eller som montage når den kortare. Klipp med kontots återkommande person eller i ett återkommande format når cirka 30 % längre. Tävlingar, uppmaningar och erbjudanden ger kommentarer men inte räckvidd.`
const TOM = path.join(F, 'tom.mp4')
for (const konto of kunder) {
  const ut = path.join(UT, `${konto}.json`)
  if (fs.existsSync(ut)) { console.log(`${konto}: finns`); continue }
  const u = underlag(konto)
  const prompt = `Du ser inte någon video: videon är en tom platshållare och ska bortses från. Bygg en kundprofil för TikTok-kontot @${konto}, en verksamhet som LeTrend hjälper. En content manager ska använda profilen för att välja och anpassa klipp ur LeTrends bibliotek.

Underlaget nedan är en serieanalys av tio av kontots klipp och genomsnitt av beskrivande lager över fjorton klipp. Andelarna går från 0 till 1, matandel från 0 till 4 och bildkvalitet från 1 till 5.
${JSON.stringify(u, null, 1)}

${KUNSKAP}

Var konkret och håll dig till underlaget. Svara på svenska.`
  const r = await analyseraVideo({ fil: TOM, prompt, schema, temperatur: 0.2, modell: 'google/gemini-3.1-pro-preview' })
  fs.writeFileSync(ut, JSON.stringify({ konto, underlag: u, tokens: r.usage?.total_tokens, profil: r.data }, null, 1))
  console.log(`${konto}: ${r.data.verksamhet}, ${r.data.segment}, frontfigurer ${r.data.frontfigurer.map(f => f.etikett + '/' + f.roll).join(', ') || '-'}, produktion ${r.data.produktion}, spelar ${r.data.personal_spelar} (${r.usage?.total_tokens} tokens)`)
}
