// Sållar alla hämtade men osållade stickprovsklipp i prioriterad ordning: ägarens ögontest-konton
// först, sedan förebilderna, sist resten. Varvat mellan konton, så att ett avbrott ändå ger jämn
// täckning. Filen raderas efter sållningen (som i profil/natt.mjs).
//
//   SALLNING_VAG=lovable node profil/salla-ko.mjs [--par 8] [--max 10000]
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'
import { sallaKlipp } from '../bank/sallning.mjs'

const args = process.argv.slice(2)
const varde = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const PAR = Number(varde('--par', 8))
const MAX = Number(varde('--max', 10000))
const KALLOR = path.join(DATA, 'kallor.json')
const SALLNING = path.join(DATA, 'bank', 'sallning')
const las = f => { for (let i = 0; i < 20; i++) { try { return JSON.parse(fs.readFileSync(f, 'utf8')) } catch {} } throw new Error(`kunde inte läsa ${f}`) }
const typer = las(path.join(DATA, 'typer', 'typer.json')).typer
const sp = new Set(las(path.join(DATA, 'profil', 'stickprov.json')).klipp.map(k => `${k.handtag}-${k.id}`))
const godk = new Set(fs.readFileSync(path.join(DATA, 'profil', 'godkanda.txt'), 'utf8').split(/\r?\n/).filter(Boolean))
const fore = new Set((fs.readFileSync(path.join(DATA, 'profil', 'forebilder.txt'), 'utf8').match(/@[a-z0-9._]+/g) ?? []).map(h => h.slice(1)))
const prio = konto => godk.has(konto) ? 0 : fore.has(konto) ? 1 : 2

const kallor = las(KALLOR)
const vantar = Object.entries(kallor).filter(([id, k]) => sp.has(id) && !k.raderad && k.fil && fs.existsSync(k.fil) && !fs.existsSync(path.join(SALLNING, `${id}.json`)))
const perKonto = new Map()
for (const [id, k] of vantar) { const l = perKonto.get(k.konto) ?? []; l.push([id, k]); perKonto.set(k.konto, l) }
const grupper = [0, 1, 2].map(p => [...perKonto.entries()].filter(([konto]) => prio(konto) === p).map(([, l]) => l))
const ko = []
for (const g of grupper) for (let i = 0; g.some(l => i < l.length); i++) for (const l of g) if (i < l.length) ko.push(l[i])
ko.splice(MAX)
console.log(`${ko.length} klipp att sålla (ögontest ${grupper[0].flat().length}, förebilder ${grupper[1].flat().length}, övriga ${grupper[2].flat().length})`)

let i = 0, ok = 0, fel = 0
const t0 = Date.now()
await Promise.all(Array.from({ length: PAR }, async () => {
  while (i < ko.length) {
    const [id, k] = ko[i++]
    try {
      await sallaKlipp(id, k, typer)
      ok++
      fs.rmSync(k.fil, { force: true })
      const kl = las(KALLOR)
      if (kl[id]) { kl[id].raderad = true; fs.writeFileSync(KALLOR, JSON.stringify(kl, null, 2)) }
    } catch (e) {
      fel++
      console.warn(`${id}: ${e.message.slice(0, 160)}`)
      if (/ 40[12]:/.test(e.message)) { console.error('nyckel eller krediter: stoppar'); process.exit(1) }
    }
    if ((ok + fel) % 50 === 0) console.log(`${ok + fel}/${ko.length}: ${ok} sållade, ${fel} fel, ${((Date.now() - t0) / 1000 / (ok + fel)).toFixed(2)} s/klipp`)
  }
}))
console.log(`klart: ${ok} sållade, ${fel} fel`)
