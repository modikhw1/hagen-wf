// Uppdrag 0031: meningarna mot liggarens Jev-yta. Tillståndet: klippet i en rad, poängen, förloppen och de lagliga ändringarna (ytan).
// En fråga per mening: vilken ändring (eller ingen_passar). Frågan är skriven före första körningen och ändras inte efter svaren.
// RUNDOR körningar per mening, var och en ett eget anrop (tag m<n>-k<runda>). Nyckeln läses med app/kalibrering/jev.mjs och skrivs aldrig ut.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { nyckel, MODELL } from '../../app/kalibrering/jev.mjs';
const DIR = path.dirname(fileURLToPath(import.meta.url)); const ROOT = path.resolve(DIR, '../..');
const OUT = path.join(DIR, process.env.UT ?? 'ut_0031/med'); const RUNDOR = Number(process.env.RUNDOR ?? 5);
const read = p => JSON.parse(fs.readFileSync(p, 'utf8')); const write = (p, x) => { fs.mkdirSync(path.dirname(p), {recursive:true}); fs.writeFileSync(p, JSON.stringify(x, null, 2)+'\n', 'utf8'); };
const M = read(path.join(DIR, 'meningar_0031.json'));
const Y = read(path.join(DIR, process.env.YTA ?? 'ut_0031/jev_yta.json'));
const L = read(path.join(ROOT, 'scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/liggare_0031.json'));
const st = [
  `kand-kennysgelato: 8,4 s, 2 scener. Expediten A ger en kund ett pyttelitet smakprov (s1) och tar sedan en jätteportion till sig själv (s2).`,
  `Poängen: ${L.mening.poang}`,
  ...L.forlopp.map(f => `Förlopp ${f.id}: ${f.syfte} (${f.handelser.map(h => L.handelser.find(x => x.id === h).ram).join(', ')}).`),
  `Lagliga ändringar (ur liggaren): ` + Y.rader.map(r => `${r.id}: ${r.text}${r.regi ? '' : ' [kan inte utföras än]'}`).join('; '),
].join('\n');
write(path.join(OUT, 'tillstand.json'), {text: st, rader: st.split('\n').length, tecken: st.length});
const fraga = {andring: {type: 'choice', instructions: 'Vilken av de lagliga ändringarna är det CM ber om? Välj ingen_passar om ingen av dem är det meningen ber om, även om en liknar.', criteria: Object.fromEntries(Y.rader.map(r => [r.id, r.text]))}};
let calls = 0;
async function api(tag, state, questions) {
  const t = path.join(OUT, 'anrop', tag + '.json'); if (fs.existsSync(t)) return read(t);
  if (++calls > 120) throw new Error('anropstaket');
  const key = nyckel(path.join(ROOT, 'app')); const request = {model: MODELL, state, questions}; const t0 = performance.now();
  const r = await fetch('https://api.typesafe.ai/v1/systemone', {method: 'POST', headers: {Authorization: `Bearer ${key}`, 'Content-Type': 'application/json'}, body: JSON.stringify(request), signal: AbortSignal.timeout(30000)});
  const raw = JSON.parse(await r.text()); const res = {tag, request, status: r.status, raw, ms: performance.now() - t0}; write(t, res);
  fs.appendFileSync(path.join(OUT, 'anropslogg.jsonl'), JSON.stringify({tag, status: r.status, input_tokens: raw?.usage?.input_tokens, ms: Math.round(res.ms)}) + '\n');
  if (r.status !== 200) throw new Error('HTTP ' + r.status); return res;
}
const res = [];
for (const m of M.meningar) for (let k = 1; k <= RUNDOR; k++) {
  const a = await api(`m${m.nr}-k${k}`, st + '\nCM: ' + m.text, fraga); const v = a.raw.answers.andring;
  res.push({nr: m.nr, runda: k, val: v.choice, sannolikhet: v.probabilities?.[v.choice] ?? null, ms: Math.round(a.ms)});
}
write(path.join(OUT, 'val.json'), {modell: MODELL, rundor: RUNDOR, resultat: res}); console.log('klart', res.length);
