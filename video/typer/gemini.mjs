// Gemini via Vertex AI med användarens gcloud-inloggning (samma projekt som hagen-ui, "Hagen").
// Ingen nyckel i repot: token hämtas med `gcloud auth print-access-token` och förnyas efter 45 min.
// Endpoint och generationConfig följer hagen-ui (artifacts/api-server/src/lib/vertex-gemini.ts).
import { execSync } from 'node:child_process'
import fs from 'node:fs'

// Med GEMINI_API_KEY (miljön eller video/.env.local) går anropen till Google AI Studio i stället
// för Vertex: samma modeller och samma schema, annan fakturering. Utan nyckel används Vertex.
// GEMINI_VAG=vertex tvingar Vertex även när en nyckel finns.
function lasNyckel() {
  if (process.env.GEMINI_VAG === 'vertex') return null
  if (process.env.GEMINI_API_KEY) return process.env.GEMINI_API_KEY.trim()
  try {
    const rad = fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).find(l => l.startsWith('GEMINI_API_KEY='))
    return rad ? rad.slice('GEMINI_API_KEY='.length).trim() || null : null
  } catch { return null }
}
const NYCKEL = lasNyckel()
export const VAG = NYCKEL ? 'aistudio' : 'vertex'

function adress(modell) {
  if (NYCKEL) return {
    url: `https://generativelanguage.googleapis.com/v1beta/models/${modell}:generateContent`,
    headers: () => ({ 'x-goog-api-key': NYCKEL, 'Content-Type': 'application/json' }),
  }
  return {
    url: `https://${VARD}/v1/projects/${PROJEKT}/locations/${PLATS}/publishers/google/models/${modell}:generateContent`,
    headers: () => ({ Authorization: `Bearer ${hamtaToken()}`, 'Content-Type': 'application/json', 'x-goog-user-project': PROJEKT }),
  }
}

export const PROJEKT = process.env.GCP_PROJECT_ID || 'gen-lang-client-0853618366'
export const PLATS = process.env.GCP_VERTEX_LOCATION || 'global'
const VARD = PLATS === 'global' ? 'aiplatform.googleapis.com' : `${PLATS}-aiplatform.googleapis.com`

// Pris i öre per 1 000 tokens, från hagen-ui (evals/metrics.ts).
export const PRIS = {
  'gemini-3.1-pro-preview': { in: 2.1, ut: 12.6 },
  'gemini-3.8-flash': { in: 0.79, ut: 3.94 },
  'gemini-3-flash-preview': { in: 0.53, ut: 3.15 },
  'gemini-2.5-flash': { in: 0.32, ut: 2.63 },
  'gemini-3.5-flash-lite': { in: 0.11, ut: 0.42 },
}

let token = null
let tokenTid = 0
function hamtaToken() {
  if (token && Date.now() - tokenTid < 45 * 60_000) return token
  token = execSync('gcloud auth print-access-token', { encoding: 'utf8', windowsHide: true }).trim()
  tokenTid = Date.now()
  return token
}

export function kostnadOre(modell, u) {
  const p = PRIS[modell]
  if (!p || !u) return null
  return ((u.promptTokenCount ?? 0) / 1000) * p.in + (((u.candidatesTokenCount ?? 0) + (u.thoughtsTokenCount ?? 0)) / 1000) * p.ut
}

// Ett anrop. parts: [{ text }] eller [{ inlineData: { mimeType, data } , videoMetadata }]. Med schema
// kommer svaret som JSON enligt schemat. Försöker igen vid 429/5xx.
// sok: true slår på Google-sökning (grundning); kan inte kombineras med schema.
export async function generera({ modell, system, parts, schema, temperatur = 0.2, tankande, upplosning, sok }) {
  const { url, headers } = adress(modell)
  const body = {
    ...(system ? { systemInstruction: { parts: [{ text: system }] } } : {}),
    contents: [{ role: 'user', parts }],
    ...(sok ? { tools: [{ googleSearch: {} }] } : {}),
    generationConfig: {
      temperature: temperatur,
      ...(schema ? { responseMimeType: 'application/json', responseJsonSchema: schema } : {}),
      ...(tankande ? { thinkingConfig: { thinkingLevel: tankande } } : {}),
      ...(upplosning ? { mediaResolution: upplosning } : {}),
    },
  }
  for (let forsok = 0; ; forsok++) {
    const t0 = Date.now()
    const res = await fetch(url, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(420_000),
    })
    if ((res.status === 429 || res.status >= 500) && forsok < 4) {
      await new Promise(r => setTimeout(r, 2000 * 2 ** forsok))
      continue
    }
    if (res.status === 401 && forsok < 1) { token = null; continue }
    const text = await res.text()
    if (!res.ok) throw new Error(`${VAG} ${res.status} (${modell}): ${text.slice(0, 400)}`)
    const j = JSON.parse(text)
    const svar = (j.candidates?.[0]?.content?.parts ?? []).filter(p => !p.thought).map(p => p.text ?? '').join('')
    const usage = j.usageMetadata
    let data = null
    if (schema) {
      try { data = JSON.parse(svar) } catch { throw new Error(`ogiltig JSON från ${modell}: ${svar.slice(0, 200)}`) }
    }
    return { text: svar, data, usage, ore: kostnadOre(modell, usage), ms: Date.now() - t0, modell }
  }
}

// Redigera en bild (Gemini bildmodell): bild in, bild ut. Returnerar { data (base64), mimeType, usage, ore }.
// Pris: ungefär 0,4 kr per bild ut (gemini-2.5-flash-image, 1 290 bildtokens).
export async function redigeraBild({ modell = 'gemini-2.5-flash-image', bild, mimeType = 'image/jpeg', text }) {
  const { url, headers } = adress(modell)
  for (let forsok = 0; ; forsok++) {
    const res = await fetch(url, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ contents: [{ role: 'user', parts: [{ inlineData: { mimeType, data: bild } }, { text }] }], generationConfig: { responseModalities: ['IMAGE'], temperature: 0.2 } }),
      signal: AbortSignal.timeout(180_000),
    })
    // bildmodellens kvot är delad och tar slut i stötar: vänta längre (upp till ~4 min totalt)
    if ((res.status === 429 || res.status >= 500) && forsok < 7) { await new Promise(r => setTimeout(r, 4000 * 2 ** Math.min(forsok, 5))); continue }
    const j = await res.json()
    if (!res.ok) throw new Error(`${VAG} ${res.status} (${modell}): ${JSON.stringify(j).slice(0, 300)}`)
    const p = j.candidates?.[0]?.content?.parts?.find(x => x.inlineData)
    if (!p) { if (forsok < 2) continue; throw new Error(`ingen bild från ${modell}`) }
    const ut = j.usageMetadata?.candidatesTokenCount ?? 1290
    return { data: p.inlineData.data, mimeType: p.inlineData.mimeType, usage: j.usageMetadata, ore: (ut / 1000) * 31.5 + ((j.usageMetadata?.promptTokenCount ?? 0) / 1000) * 0.32 }
  }
}
