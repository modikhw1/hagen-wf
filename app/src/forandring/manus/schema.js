import { ORDBOK } from '../motor/ordbok'
import { OPS, UTSNITT } from '../motor/kamera'
import { LOKALER } from '../motor/lokal'
import { FIGURER } from '../motor/docka'

// Manuset är det enda en AI-regissör skriver. Data, ingen kod. Formatet:
//
// {
//   id, klipp, verklighet (1–10, eller null för originalet), instruktion,
//   lokal: 'fratelli',                       låst
//   roller: { marco: 'marco', nonna: 'nonna' }, låst: roll → figur
//   scener: [{
//     id, text, tid (sekunder),               text och antal scener är låsta
//     in: { typ: 'klipp'|'mjuk'|'whip'|'zoom', tid }   övergången in i scenen
//     handling: [{ roll, rorelse, start, slut?, tempo?, amp?, plats?: [x, z], vag?: [[x, z], [x, z]],
//                  riktning?: grader, blick?: roll | [x, y, z] }]
//     kamera: { utsnitt, mal: { roll, led } | { punkt: [x, y, z] }, vinkel, hojd, lins?, roll?, skak?,
//               ops: [{ op, mangd, fran?, till? }] }
//   }]
// }
//
// Låsta fält jämförs mot originalet; validera() säger vad som bryter låsningen.

export const OVERGANGAR = ['klipp', 'mjuk', 'whip', 'zoom']

export function validera(manus, original = null) {
  const fel = []
  const f = (sti, msg) => fel.push(`${sti}: ${msg}`)
  if (typeof manus.lokal === 'string' ? !LOKALER[manus.lokal] : !manus.lokal?.scener) f('lokal', `okänd lokal "${manus.lokal?.id ?? manus.lokal}"`)
  for (const [r, fig] of Object.entries(manus.roller ?? {})) if (!FIGURER[fig] && !manus.figurer?.[fig]) f(`roller.${r}`, `okänd figur "${fig}"`)
  manus.scener.forEach((s, i) => {
    const p = `scener[${i}]`
    if (!(s.tid > 0)) f(p, 'tid saknas')
    if (s.in && !OVERGANGAR.includes(s.in.typ)) f(`${p}.in`, `okänd övergång "${s.in.typ}"`)
    for (const [k, h] of (s.handling ?? []).entries()) {
      if (!manus.roller[h.roll]) f(`${p}.handling[${k}]`, `okänd roll "${h.roll}"`)
      if (!ORDBOK[h.rorelse] && !manus.rorelser?.[h.rorelse]) f(`${p}.handling[${k}]`, `rörelsen "${h.rorelse}" finns inte i ordboken`)
    }
    const kam = s.kamera
    if (!kam?.bana && !UTSNITT[kam?.utsnitt]) f(`${p}.kamera`, `okänt utsnitt "${kam?.utsnitt}"`)
    for (const o of kam?.ops ?? []) if (!OPS.includes(o.op)) f(`${p}.kamera.ops`, `okänd operation "${o.op}"`)
  })
  if (original) {
    if (JSON.stringify(manus.lokal) !== JSON.stringify(original.lokal)) f('lokal', 'låst: får inte ändras')
    if (JSON.stringify(manus.roller) !== JSON.stringify(original.roller)) f('roller', 'låst: får inte ändras')
    if (manus.scener.length !== original.scener.length) f('scener', `låst: ${original.scener.length} scener`)
    manus.scener.forEach((s, i) => {
      if (original.scener[i] && s.text !== original.scener[i].text) f(`scener[${i}].text`, 'låst: handlingen får inte ändras')
    })
  }
  return fel
}
