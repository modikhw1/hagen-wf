// Gemini via Vertex AI med användarens gcloud-inloggning (samma projekt som hagen-ui, "Hagen").
// Ingen nyckel i repot: token hämtas med `gcloud auth print-access-token` och förnyas efter 45 min.
// Endpoint och generationConfig följer hagen-ui (artifacts/api-server/src/lib/vertex-gemini.ts).
import { execSync } from 'node:child_process'

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
export async function generera({ modell, system, parts, schema, temperatur = 0.2, tankande, upplosning }) {
  const url = `https://${VARD}/v1/projects/${PROJEKT}/locations/${PLATS}/publishers/google/models/${modell}:generateContent`
  const body = {
    ...(system ? { systemInstruction: { parts: [{ text: system }] } } : {}),
    contents: [{ role: 'user', parts }],
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
      headers: { Authorization: `Bearer ${hamtaToken()}`, 'Content-Type': 'application/json', 'x-goog-user-project': PROJEKT },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(420_000),
    })
    if ((res.status === 429 || res.status >= 500) && forsok < 4) {
      await new Promise(r => setTimeout(r, 2000 * 2 ** forsok))
      continue
    }
    if (res.status === 401 && forsok < 1) { token = null; continue }
    const text = await res.text()
    if (!res.ok) throw new Error(`Vertex ${res.status} (${modell}): ${text.slice(0, 400)}`)
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
  const url = `https://${VARD}/v1/projects/${PROJEKT}/locations/${PLATS}/publishers/google/models/${modell}:generateContent`
  for (let forsok = 0; ; forsok++) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${hamtaToken()}`, 'Content-Type': 'application/json', 'x-goog-user-project': PROJEKT },
      body: JSON.stringify({ contents: [{ role: 'user', parts: [{ inlineData: { mimeType, data: bild } }, { text }] }], generationConfig: { responseModalities: ['IMAGE'], temperature: 0.2 } }),
      signal: AbortSignal.timeout(180_000),
    })
    // bildmodellens kvot är delad och tar slut i stötar: vänta längre (upp till ~4 min totalt)
    if ((res.status === 429 || res.status >= 500) && forsok < 7) { await new Promise(r => setTimeout(r, 4000 * 2 ** Math.min(forsok, 5))); continue }
    const j = await res.json()
    if (!res.ok) throw new Error(`Vertex ${res.status} (${modell}): ${JSON.stringify(j).slice(0, 300)}`)
    const p = j.candidates?.[0]?.content?.parts?.find(x => x.inlineData)
    if (!p) { if (forsok < 2) continue; throw new Error(`ingen bild från ${modell}`) }
    const ut = j.usageMetadata?.candidatesTokenCount ?? 1290
    return { data: p.inlineData.data, mimeType: p.inlineData.mimeType, usage: j.usageMetadata, ore: (ut / 1000) * 31.5 + ((j.usageMetadata?.promptTokenCount ?? 0) / 1000) * 0.32 }
  }
}
