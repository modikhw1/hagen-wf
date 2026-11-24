// Jev (TypeSafe System One) som snabb bedömare inom en vertikal. Körs bara på servern: nyckeln
// lämnar aldrig datorn till webbläsaren. API: POST https://api.typesafe.ai/v1/systemone
// (docs.typesafe.ai/api). Två sätt att fråga:
//   score: en scen i taget, nivåerna ur vertikalens kriterier → ett tal per scen
//   par:   två scener, choice a / b / lika → samma fråga som människan svarar på
// Svaren sparas i data/jev/<vertikal>.json per (item, kriteriernas hash), så att samma fråga inte
// betalas två gånger och så att olika formuleringar av kriterierna kan jämföras.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

const URL = 'https://api.typesafe.ai/v1/systemone'
export const MODELL = process.env.TYPESAFE_MODEL ?? 'jev-latest'

export function nyckel(appDir) {
  if (process.env.TYPESAFE_API_KEY) return process.env.TYPESAFE_API_KEY
  try {
    const rad = fs.readFileSync(path.join(appDir, '.env.local'), 'utf8').split(/\r?\n/).find(l => l.startsWith('TYPESAFE_API_KEY='))
    return rad ? rad.slice('TYPESAFE_API_KEY='.length).trim() : null
  } catch { return null }
}

const hash = o => crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex').slice(0, 12)

async function fraga(key, state, questions) {
  const r = await fetch(URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: MODELL, state, questions }),
  })
  if (!r.ok) throw new Error(`Jev ${r.status}: ${(await r.text()).slice(0, 300)}`)
  return r.json()
}

// Kör uppgifter med begränsad samtidighet.
async function iTakt(lista, n, f) {
  const ut = new Array(lista.length)
  let i = 0
  await Promise.all(Array.from({ length: n }, async () => { while (i < lista.length) { const k = i++; ut[k] = await f(lista[k]) } }))
  return ut
}

export function cache(dataDir, vid) {
  const fil = path.join(dataDir, 'jev', `${vid}.json`)
  let c = {}
  try { c = JSON.parse(fs.readFileSync(fil, 'utf8')) } catch {}
  return {
    get: k => c[k],
    set: (k, v) => { c[k] = v },
    spara: () => { fs.mkdirSync(path.dirname(fil), { recursive: true }); fs.writeFileSync(fil, JSON.stringify(c, null, 1)) },
    alla: () => c,
  }
}

export async function jevScore({ key, dataDir, vertikal, items }) {
  const q = { niva: { type: 'score', instructions: `${vertikal.namn}. ${vertikal.fraga} Bedöm scenen nedan på skalan.`, criteria: vertikal.kriterier } }
  const h = hash({ q, MODELL })
  const c = cache(dataDir, vertikal.id)
  const ut = await iTakt(items, 4, async it => {
    const k = `score|${h}|${it.id}`
    if (c.get(k)) return { id: it.id, ...c.get(k), cache: true }
    const svar = await fraga(key, it.text, q)
    const a = svar.answers.niva
    const v = { score: a.score, steg: 1 + (9 * a.score) / Math.max(1, vertikal.kriterier.length - 1), konfidens: a.confidence, p: a.probabilities, tokens: svar.usage?.input_tokens }
    c.set(k, v)
    return { id: it.id, ...v }
  })
  c.spara()
  return { kriterier: h, svar: ut }
}

export async function jevPar({ key, dataDir, vertikal, par }) {
  const q = {
    val: {
      type: 'choice',
      instructions: `${vertikal.namn}. ${vertikal.fraga} Svara a, b eller lika.`,
      criteria: { a: 'Scen A har tydligt mer.', b: 'Scen B har tydligt mer.', lika: 'Ungefär lika, eller går inte att avgöra.' },
    },
  }
  const h = hash({ q, MODELL })
  const c = cache(dataDir, vertikal.id)
  const ut = await iTakt(par, 4, async p => {
    const k = `par|${h}|${p.a}|${p.b}`
    if (c.get(k)) return { a: p.a, b: p.b, ...c.get(k), cache: true }
    const svar = await fraga(key, `Scen A: ${p.textA}\n\nScen B: ${p.textB}`, q)
    const a = svar.answers.val
    const v = { val: a.choice, konfidens: a.confidence, p: a.probabilities, tokens: svar.usage?.input_tokens }
    c.set(k, v)
    return { a: p.a, b: p.b, ...v }
  })
  c.spara()
  return { kriterier: h, svar: ut }
}

// Live: välj kamerauttryck för scener som ska bytas när reglaget dras. Kandidaterna är redan
// filtrerade (närmast målet, minst ryck); Jev väljer med helheten i texten: scenens innehåll,
// originalets kamera och grannscenernas valda kameror. Choice tar högst 255 alternativ.
export async function jevUttryck({ key, vertikal, mal, scener }) {
  const t0 = Date.now()
  const svar = await iTakt(scener, 5, async s => {
    const nycklar = s.kandidater.map((_, k) => `u${k}`)
    const q = {
      val: {
        type: 'choice',
        instructions: `${vertikal.namn}: reglaget står på ${mal} av 10 för hela klippet, där 1 är ${vertikal.andar[0]} och 10 är ${vertikal.andar[1]}. ${s.mal != null ? `Den här scenens mål i kedjan är ${(+s.mal).toFixed(1)} (originalet låg på ${(+s.profil).toFixed(1)}). ` : ''}Välj det kamerauttryck som bäst når scenens mål och samtidigt fungerar i följden med grannscenerna (inga onödiga ryck, men tydlig skillnad när målet kräver det).`,
        criteria: Object.fromEntries(s.kandidater.map((k, j) => [nycklar[j], k.text])),
      },
    }
    const state = [
      `Scenen: ${s.text}.`,
      `Originalets kamera: ${s.original}.`,
      s.fore ? `Scenen före filmas: ${s.fore}.` : 'Det här är första scenen.',
      s.efter ? `Scenen efter filmas: ${s.efter}.` : 'Det här är sista scenen.',
    ].join('\n')
    const t = Date.now()
    const r = await fraga(key, state, q)
    const a = r.answers.val
    const j = nycklar.indexOf(a.choice)
    return { scen: s.i, val: s.kandidater[j]?.id ?? s.kandidater[0].id, konfidens: a.confidence, ms: Date.now() - t, tokens: r.usage?.input_tokens }
  })
  return { ms: Date.now() - t0, svar }
}
