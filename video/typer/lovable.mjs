// Videoanrop via Lovable AI (egen endpoint i Lovable-projektet vertex-cloud-bridge), betalt med
// Lovable-krediter. Endpointen tar video som base64, ett JSON Schema och en prompt, och svarar
// { data, usage, modell, ms }. Den skickar inte vidare fps (Gemini tar då sin standard, 1 bild/s).
//
// LOVABLE_URL och LOVABLE_NYCKEL i miljön eller i video/.env.local.
import fs from 'node:fs'

const env = namn => process.env[namn] ?? (() => {
  try { return fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).find(l => l.startsWith(`${namn}=`))?.slice(namn.length + 1).trim() } catch { return null }
})()
// LOVABLE_KONTO=2 väljer det andra projektet (cloud-canvas-bridge, eget konto och egna krediter),
// LOVABLE_KONTO=3 det tredje (4 nov), och så vidare.
const KONTO = process.env.LOVABLE_KONTO && process.env.LOVABLE_KONTO !== '1' ? `_${process.env.LOVABLE_KONTO}` : ''
const URL_ = env(`LOVABLE_URL${KONTO}`)
const NYCKEL = env(`LOVABLE_NYCKEL${KONTO}`)
export const LOVABLE_MODELL = process.env.LOVABLE_MODELL ?? 'google/gemini-3.1-flash-lite'

// Strikt JSON Schema (OpenAI-stil): alla fält krävs och inga extra fält.
function strikt(s) {
  if (s?.type === 'object') return { ...s, additionalProperties: false, properties: Object.fromEntries(Object.entries(s.properties).map(([k, v]) => [k, strikt(v)])) }
  return s
}

// LOVABLE_KONTO=aistudio skickar samma anrop direkt till Google AI Studio med AISTUDIO_NYCKEL (standard:
// GEMINI_API_KEY_GRATIS). Gratisnivån tar Flash-modellerna (3-flash-preview, 3.5-flash, 3.1-flash-lite) men inte
// Pro eller Argon. Samma svarform som bryggan.
async function aistudio({ fil, base64, prompt, schema, temperatur, modell }) {
  const nyckel = env(process.env.AISTUDIO_NYCKEL ?? 'GEMINI_API_KEY_GRATIS'), m = modell.replace(/^google\//, '')
  const body = JSON.stringify({ contents: [{ role: 'user', parts: [{ inlineData: { mimeType: 'video/mp4', data: base64 ?? fs.readFileSync(fil).toString('base64') } }, { text: prompt }] }], generationConfig: { ...extra, temperature: temperatur, responseMimeType: 'application/json', responseJsonSchema: strikt(schema) } })
  for (let forsok = 0; ; forsok++) {
    const t0 = Date.now()
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent`, { method: 'POST', headers: { 'x-goog-api-key': nyckel, 'content-type': 'application/json' }, body, signal: AbortSignal.timeout(300_000) })
    const text = await res.text()
    if ((res.status === 429 || res.status >= 500) && forsok < 6) { await new Promise(r => setTimeout(r, 5000 * 2 ** Math.min(forsok, 4))); continue }
    if (!res.ok) throw new Error(`aistudio ${res.status}: ${text.slice(0, 300)}`)
    const j = JSON.parse(text), svar = (j.candidates?.[0]?.content?.parts ?? []).filter(p => !p.thought).map(p => p.text ?? '').join('')
    return { data: JSON.parse(svar), usage: { total_tokens: j.usageMetadata?.totalTokenCount }, modell: `google/${m}`, ms: Date.now() - t0 }
  }
}

// LOVABLE_KONTO=beacon går via budgetproxyn token-budget-beacon (16 nov) till Vertex AI på ägarens GCP-krediter.
// Proxyn tar Vertex generateContent-kropp plus "model" och lägger till { proxy: { cost_usd, ... } } i svaret.
// BEACON_NYCKEL (och valfritt BEACON_URL) i video/.env.local. Stopp från proxyn (budgettak, kill switch,
// slut på krediter) kommer med placeholder: true och försöks inte om.
export const beaconKostnad = { usd: 0, anrop: 0 }
// beaconDelar: flera delar i ett anrop, t.ex. en kunds hela historik som video följt av en kandidat (E13).
// delar: [{ text } | { fil } | { base64 }]. Tankarna strömmas med (includeThoughts) så att första tecknet kommer
// tidigt och gatewayens 60 s-gräns inte kapar långa läsningar; de filtreras bort ur svaret.
// extra: fler fält i generationConfig, t.ex. { topP, topK, seed } (E23)
export async function beaconDelar({ delar, schema, temperatur = 0.1, modell = LOVABLE_MODELL, maxUt, extra = {} }) {
  const nyckel = env('BEACON_NYCKEL'), url = env('BEACON_URL') ?? 'https://token-budget-beacon.lovable.app/api/public/v1/generate'
  if (!nyckel) throw new Error('BEACON_NYCKEL saknas (video/.env.local)')
  const m = modell.replace(/^google\//, ''), argon = /argon/.test(m)
  const parts = delar.map(d => d.text != null ? { text: d.text } : { inlineData: { mimeType: 'video/mp4', data: d.base64 ?? fs.readFileSync(d.fil).toString('base64') } })
  const max = maxUt ?? (process.env.BEACON_MAX_UT ? +process.env.BEACON_MAX_UT : null)
  const body = JSON.stringify({ model: m, upstreamStream: true, contents: [{ role: 'user', parts }], generationConfig: { temperature: temperatur, responseMimeType: 'application/json', responseJsonSchema: strikt(schema), ...(max ? { maxOutputTokens: max } : {}), ...(argon ? {} : { thinkingConfig: extra.thinkingConfig ?? { includeThoughts: true } }) } })
  for (let forsok = 0; ; forsok++) {
    const t0 = Date.now()
    let res, text
    try { res = await fetch(url, { method: 'POST', headers: { authorization: `Bearer ${nyckel}`, 'content-type': 'application/json' }, body, signal: AbortSignal.timeout(170_000) }); text = await res.text() }
    catch (e) { if (forsok < 3) { await new Promise(r => setTimeout(r, 5000)); continue } throw new Error(`beacon nät: ${e.message}`) }
    let j = null
    try { j = JSON.parse(text) } catch {}
    const stopp = j?.placeholder && j.error !== 'quota_exhausted'
    // gemini-4-argon hänger (502 efter 60 s) på vissa prompter, t.ex. frågor om vad som sägs. 502 får därför
    // bara två omförsök, annars står körningen i minuter per klipp.
    if (!stopp && (res.status === 429 || res.status >= 500) && forsok < (res.status === 502 && argon ? 1 : 5)) { await new Promise(r => setTimeout(r, 4000 * 2 ** Math.min(forsok, 4))); continue }
    if (!res.ok) throw new Error(`beacon ${res.status}: ${text.slice(0, 300)}`)
    const svar = (j.candidates?.[0]?.content?.parts ?? []).filter(p => !p.thought).map(p => p.text ?? '').join('')
    let data
    try { data = JSON.parse(svar) } catch { if (forsok < 2) continue; throw new Error(`beacon: svaret är inte JSON (${j.candidates?.[0]?.finishReason}): ${svar.slice(0, 200)}`) }
    beaconKostnad.usd += j.proxy?.cost_usd ?? 0; beaconKostnad.anrop++
    return { data, usage: { total_tokens: j.usageMetadata?.totalTokenCount, in_tokens: j.usageMetadata?.promptTokenCount, cost_usd: j.proxy?.cost_usd }, modell: `google/${m}`, ms: Date.now() - t0 }
  }
}
const beacon = ({ fil, base64, prompt, schema, temperatur, modell }) => beaconDelar({ delar: [base64 ? { base64 } : { fil }, { text: prompt }], schema, temperatur, modell })

export async function analyseraVideo({ fil, base64, prompt, schema, temperatur = 0.1, modell = LOVABLE_MODELL }) {
  if (process.env.LOVABLE_KONTO === 'aistudio') return aistudio({ fil, base64, prompt, schema, temperatur, modell })
  if (process.env.LOVABLE_KONTO === 'beacon') return beacon({ fil, base64, prompt, schema, temperatur, modell })
  if (!URL_ || !NYCKEL) throw new Error('LOVABLE_URL eller LOVABLE_NYCKEL saknas (video/.env.local)')
  const kropp = JSON.stringify({ modell, video: { mime: 'video/mp4', base64: base64 ?? fs.readFileSync(fil).toString('base64') }, fps: 1, prompt, schema: strikt(schema), temperatur })
  for (let forsok = 0; ; forsok++) {
    const res = await fetch(URL_, { method: 'POST', headers: { 'content-type': 'application/json', 'x-nyckel': NYCKEL }, body: kropp })
    const text = await res.text()
    if ((res.status === 429 || res.status >= 500) && forsok < 4) { await new Promise(r => setTimeout(r, 3000 * 2 ** forsok)); continue }
    if (!res.ok) throw new Error(`lovable ${res.status}: ${text.slice(0, 300)}`)
    const j = JSON.parse(text)
    return { data: j.data, usage: j.usage, modell: j.modell, ms: j.ms }
  }
}
