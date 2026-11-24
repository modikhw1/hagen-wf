// Väljaren: när reglaget går till ett nytt mål avgörs per scen om den stannar i sin verklighet
// eller byts. Svaret har samma form som ett Jev-anrop (Choice per scen med sannolikhet), så att
// regeln här kan ersättas av Jev utan att resten ändras.
//
// Regel (den billiga lösaren):
// 1. En scen stannar om dess mätta värde ligger inom toleransen från målet.
// 2. Annars byts den mot den verklighet vars värde ligger närmast målet; vid lika, den närmast
//    nuvarande verkligheten (mindre ryck).
// 3. Hamnar klippets snitt ändå för långt från målet byts den scen som avviker mest, tills snittet håller.

import { ORIGINAL_STEG } from '../manus/regissor'

export const MIN_SYNS = 0.7

export function valj({ mal, nu, varden, tolerans }) {
  const alla = Object.keys(varden).map(Number)
  // En version där motivet knappt syns (kameran i en vägg, för nära) får inte väljas.
  const giltig = (s, i) => s === ORIGINAL_STEG || varden[s][i].syns >= MIN_SYNS
  const v = (k, i) => varden[k][i].v
  const val = nu.map((k, i) => {
    const d = Math.abs(v(k, i) - mal)
    if (d <= tolerans && giltig(k, i)) return { scen: i, val: k, beslut: 'stanna', p: 1 - d / (2 * tolerans) }
    const best = alla.filter(s => giltig(s, i))
      .map(s => ({ s, d: Math.abs(v(s, i) - mal), hopp: Math.abs(s - k) }))
      .sort((a, b) => a.d - b.d || a.hopp - b.hopp)[0]
    return { scen: i, val: best.s, beslut: 'byt', fran: k, p: Math.max(0.5, 1 - best.d / 10) }
  })
  const snitt = () => val.reduce((s, x) => s + v(x.val, x.scen), 0) / val.length
  for (let n = 0; n < val.length && Math.abs(snitt() - mal) > tolerans / 2; n++) {
    const worst = val
      .filter(x => x.beslut === 'stanna')
      .sort((a, b) => Math.abs(v(b.val, b.scen) - mal) - Math.abs(v(a.val, a.scen) - mal))[0]
    if (!worst) break
    const best = alla.filter(s => giltig(s, worst.scen)).map(s => ({ s, d: Math.abs(v(s, worst.scen) - mal) })).sort((a, b) => a.d - b.d)[0]
    Object.assign(worst, { val: best.s, beslut: 'byt', fran: worst.val, p: 0.6 })
  }
  return { val, snitt: snitt() }
}

// Ett manus av scener ur olika verkligheter: scen i tas ur verklighet val[i].
export function sattIhop(verkligheter, val) {
  const bas = verkligheter[ORIGINAL_STEG]
  return { ...bas, id: `${bas.klipp}/mix`, verklighet: 'mix', scener: val.map((k, i) => verkligheter[k].scener[i]) }
}
