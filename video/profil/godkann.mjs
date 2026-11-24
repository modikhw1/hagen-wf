// Läser ägarens behållna konton i data/profil/beslut.json: de
// skrivs till data/profil/godkanda.txt och får sin lista i banken, så att profil/natt.mjs tar dem.
//
//   node profil/godkann.mjs
import fs from 'node:fs'
import path from 'node:path'
import { DATA } from '../analys/pipeline.mjs'

const LISTOR = path.join(DATA, 'profil', 'sok-listor')
const UT = path.join(DATA, 'profil', 'godkanda.txt')

const kvar = Object.keys(JSON.parse(fs.readFileSync(path.join(DATA, 'profil', 'beslut.json'), 'utf8')).behall)
const tidigare = fs.existsSync(UT) ? fs.readFileSync(UT, 'utf8').split(/\r?\n/).filter(Boolean) : []
const alla = [...new Set([...tidigare, ...kvar])].sort()
for (const h of kvar) {
  const kalla = path.join(LISTOR, h, 'lista.json')
  const mal = path.join(DATA, 'bank', h, 'lista.json')
  if (fs.existsSync(kalla) && !fs.existsSync(mal)) { fs.mkdirSync(path.dirname(mal), { recursive: true }); fs.copyFileSync(kalla, mal) }
}
fs.writeFileSync(UT, alla.join('\n') + '\n')
console.log(`${kvar.length} konton kvar i listan, ${alla.length} godkända totalt i ${UT}`)
