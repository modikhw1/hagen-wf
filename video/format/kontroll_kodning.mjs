// Blind kodning av ett K1-transkript: modellen ser bara transkriptet, aldrig las.json (prognoser, hyllor, utfall).
//   cd video && LOVABLE_KONTO=beacon node format/kontroll_kodning.mjs <transkript.txt> <ut.json> [modell]
import fs from 'node:fs'
import { beaconDelar, beaconKostnad } from '../typer/lovable.mjs'

const [, , inn, ut, modell = 'google/gemini-3.1-pro-preview', lage] = process.argv
const utanSiffror = lage === 'utan-siffror'
const text = fs.readFileSync(inn, 'utf8')
const prompt = `Below is a raw speech-to-text transcript of a recorded session. The owner of LeTrend (a company that helps restaurants, bars and cafés make TikTok content filmed by their own staff) watched pairs of TikTok clips (a first/left clip and a second/right clip). A voice assistant asked, per pair: "Which one would you rather have in the library?" (LeTrend's library of clips a content manager recommends to clients). ${utanSiffror ? "In this session no audience numbers were shown; code changed_after_numbers as unclear and after_numbers as empty. The assistant sometimes described the clips itself; only the owner's own words count." : "Then the owner pressed a button that showed audience numbers and was asked if that changes anything."}

The transcript is messy: the assistant's questions, the owner's answers and the clips' own audio (often Swedish, German or French) are mixed together and speaker labels are unreliable. Pair numbers are spoken by the assistant ("Pair 3, watch both...").${utanSiffror ? "" : " One pair (pair 4) is mis-transcribed as \"Care for\"."}

For each pair you can find, code the owner's answers. Be strict: use "unclear" when the owner does not land. Do not quote the transcript; paraphrase in English, max 25 words per field.

Fields:
- library_choice: first | second | neither | both | unclear — the clip the owner would rather have in the library, as the owner finally lands.
- library_confidence: clear | leaning | torn
- content_preference: first | second | unclear — which clip the owner says is better content / likes more / finds more interesting to watch, independent of the library question. Often the owner separates these two.
- changed_after_numbers: yes | no | unclear
- library_reason: why the library choice (paraphrase)
- content_reason: why the content preference (paraphrase)
- after_numbers: what the owner says after seeing numbers (paraphrase)

TRANSCRIPT:
${text}`
const schema = { type: 'object', properties: { pairs: { type: 'array', items: { type: 'object', properties: {
  pair: { type: 'integer' }, library_choice: { type: 'string', enum: ['first', 'second', 'neither', 'both', 'unclear'] },
  library_confidence: { type: 'string', enum: ['clear', 'leaning', 'torn'] }, content_preference: { type: 'string', enum: ['first', 'second', 'unclear'] },
  changed_after_numbers: { type: 'string', enum: ['yes', 'no', 'unclear'] }, library_reason: { type: 'string' }, content_reason: { type: 'string' }, after_numbers: { type: 'string' } },
  required: ['pair', 'library_choice', 'library_confidence', 'content_preference', 'changed_after_numbers', 'library_reason', 'content_reason', 'after_numbers'] } } }, required: ['pairs'] }
const r = await beaconDelar({ delar: [{ text: prompt }], schema, temperatur: 0.1, modell })
fs.writeFileSync(ut, JSON.stringify({ modell: r.modell, ms: r.ms, usage: r.usage, ...r.data }, null, 1))
console.log(r.modell, r.ms, 'ms', JSON.stringify(r.usage), 'kostnad', beaconKostnad)
