// E15: underlag till geometrin. En rad per sållat bankklipp: id, konto, text (sållningens mening + bildtext),
// datum och visningar. Resultat: data/format/e15/klipp.jsonl
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
const las = f => JSON.parse(fs.readFileSync(f, 'utf8'))
const SAL = path.join(DATA, 'bank', 'sallning'), ut = []
const listor = {}
for (const f of fs.readdirSync(SAL)) {
  const s = las(path.join(SAL, f)), k = s.konto
  if (!(k in listor)) { const lf = path.join(DATA, 'bank', k, 'lista.json'); listor[k] = fs.existsSync(lf) ? Object.fromEntries(las(lf).klipp.map(x => [x.id, x])) : {} }
  const m = listor[k][s.id.slice(k.length + 1)] ?? {}
  ut.push(JSON.stringify({ id: s.id, konto: k, innehall: s.innehall ?? '', bildtext: (m.text ?? '').replace(/#\S+/g, '').replace(/\s+/g, ' ').trim().slice(0, 200), typ: s.typ, datum: m.datum ?? null, visningar: m.visningar ?? null, langd: m.langd ?? null }))
}
fs.mkdirSync(path.join(DATA, 'format', 'e15'), { recursive: true })
fs.writeFileSync(path.join(DATA, 'format', 'e15', 'klipp.jsonl'), ut.join('\n'))
console.log(ut.length, 'klipp,', Object.keys(listor).length, 'konton')
