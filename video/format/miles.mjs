// Miles-pass för kalibreringen av formatkortet: ägaren tittar på klippen ett i taget, Miles (Sesame)
// frågar punkt för punkt och Granola spelar in. Per klipp svarar ägaren först blint (bär, roll),
// sedan läser Miles upp modellens läsning (Pro med principer) och frågar efter det som är fel.
//
//   node format/miles.mjs [--variant v1-konst-gemini-3.1-pro-preview] [--per-pass 10]
// Resultat: karta/videoforandring/miles/pass-<n>.md
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const VARIANT = varde('--variant', 'v1-konst-gemini-3.1-pro-preview')
const PER = Number(varde('--per-pass', 10))
const UT = path.join(DATA, '..', 'karta', 'videoforandring', 'miles')
fs.mkdirSync(UT, { recursive: true })
const urval = JSON.parse(fs.readFileSync(path.join(DATA, 'format', 'kalib', 'urval.json'), 'utf8'))

const HANG = { person: 'personen', lokal: 'lokalen', rekvisita: 'en rekvisita', nisch: 'en nisch', produkt: 'just produkten', trend: 'en trend', produktion: 'produktionen', inget: 'inget' }
const VARDE = { ide: 'idén', framforande: 'framförandet', produktion: 'produktionen', produkt: 'produkten', trend: 'trenden' }
const ROLL = { karna: 'kärna', inslag: 'inslag', utanfor: 'utanför' }
const RATT = { ingen: '', unik: ', rätten bär för att den är unik', aptitlig: ', rätten bär för att den ser god ut', signatur: ', verksamhetens signaturrätt är poängen' }
const kort = t => t.replace(/\s+/g, ' ').trim()

function klipp(k) {
  const x = JSON.parse(fs.readFileSync(path.join(DATA, 'format', VARIANT, `${k.id}.json`), 'utf8'))
  const v = Object.entries(x.vardet).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([n, p]) => `${VARDE[n]} ${p}`).join(', ')
  const bar = x.bartest.betyg >= 4 ? 'BÄR' : 'BÄR INTE'
  return `CLIP ${k.nr} (@${k.konto})
Model says: ${bar} (${x.bartest.betyg}/5), hangs on ${x.bartest.hanger_pa.map(h => HANG[h]).join(' and ')}; role ${ROLL[x.roll].toUpperCase()}.
- What happens: ${kort(x.handling)}
- Core: ${kort(x.karna)}
- Template: ${kort(x.mall)}
- Without this person: ${kort(x.bartest.skal)}
- Appeal carried by ${v}; showcase level ${x.visning.grad}/3${RATT[x.visning.ratt]}.
- Tone: self-irony ${x.ton.sjalvdistans}/5, inside feel ${x.ton.inside}/5, brand risk ${x.ton.varumarkesrisk}/5. Effort to film ${x.troskel.produktionskrav}/5, acting ${x.troskel.agerande}/5.`
}

const huvud = (n, antal, forsta, sista) => `Conduct this conversation in Swedish. Begin immediately with the first turn below. Do not greet me, explain the exercise, praise my answers or summarise with your own adjectives. Another system will analyse the recording afterwards.

WHO I AM
I own LeTrend, which helps local restaurants, bars and cafés make TikTok content that staff film themselves. Names you will hear: LeTrend, TikTok, CM (content manager), sketch, montage.

WHAT WE ARE DOING
I watch TikTok clips one at a time on my screen, numbered ${forsta}–${sista}. For each clip an AI model has written a reading (below). Your job is to collect my judgement and find exactly where the model reads the clip wrong. Two terms:
- BÄR: the idea still works if an ordinary, inexperienced employee acts it out from a short instruction. It does not "bär" if it depends on this specific person, venue, prop or a niche only this business has.
- ROLE in a LeTrend series: KÄRNA (people- and humour-driven idea any business can adapt), INSLAG (acceptable but not central, e.g. food showcase, montage, offer), UTANFÖR (does not fit).

FOR EACH CLIP, IN THIS ORDER
1. Say "Klipp ${'<number>'}, at <account>." and ask me to tell you when I have watched it. Wait.
2. Ask: "Bär idén, ja eller nej, och varför?" One question only. Do not reveal the model yet.
3. Ask: "Kärna, inslag eller utanför?"
4. Now read the model's verdict, core and template aloud in one or two sentences, then ask: "Vad i det stämmer inte?"
5. If my verdict on BÄR or ROLE differs from the model's, read the model's reason ("Without this person …" or "hangs on …") and ask: "Vad ser modellen fel där?" If we agree, instead read one of the other model points (appeal, showcase, tone) that seems most doubtful, and ask whether it is right.
6. Ask at most one follow-up, only if my answer names something new that the model has no field for (for example a quality, a distinction or a reason). Ask: "Vad skulle du kalla det, och hur ser man det i ett klipp?"
7. Then move to the next clip. Never more than six questions per clip.

HOW TO ASK
- Exactly one short question per turn. Never combine two questions.
- Treat everything you say as a question, never as fact. Do not add your own interpretations or numbers.
- If I say "nästa", move on immediately. If I say "samma som förra", accept it and move on.
- If I give a general principle instead of talking about the clip, accept it once, repeat it back in one sentence, and continue with the clip.

TIME
This session has a hard limit of about 25 minutes for ${antal} clips, roughly two minutes each. If we fall behind, skip step 5 and 6. When the clips are done or I say "avsluta", give a closing list of no more than six short lines: the distinctions or principles I named that were not in the model's points. Then ask: "Saknas något viktigt?"

THE MODEL'S READINGS
`

const pass = []
for (let i = 0; i < urval.length; i += PER) pass.push(urval.slice(i, i + PER))
for (const [p, l] of pass.entries()) {
  const forsta = l[0].nr, sista = l.at(-1).nr
  const text = `${huvud(p + 1, l.length, forsta, sista)}${l.map(klipp).join('\n\n')}

Your first turn must be exactly: "Klipp ${forsta}, @${l[0].konto}. Säg till när du har sett det."`
  const lista = l.map(k => `${k.nr}. ${k.url}`).join('\n')
  fs.writeFileSync(path.join(UT, `pass-${p + 1}.txt`), text)
  fs.writeFileSync(path.join(UT, `pass-${p + 1}-lankar.md`), `# Pass ${p + 1}: klipp ${forsta}–${sista}\n\nÖppna ett i taget när Miles säger numret.\n\n${lista}\n`)
  console.log(`pass ${p + 1}: ${text.length} tecken`)
}
