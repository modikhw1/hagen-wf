// Gemini som semantisk detektor på stillbilder: föremål, möbler och rum med rutor (0-1000).
// node sprak/gemini_bild.mjs <bild.jpg> [--modell gemini-3.5-flash-lite] [--ut fil.json] [--kontext "text"]
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';

const arg = process.argv.slice(2);
const opt = (n, d) => { const i = arg.indexOf('--' + n); return i >= 0 ? arg[i + 1] : d; };
const bild = arg[0];
const MODELL = opt('modell', 'gemini-3.5-flash-lite');
const ROT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1')), '..');
const env = Object.fromEntries(fs.readFileSync(path.join(ROT, '..', 'video', '.env.local'), 'utf8')
  .split('\n').filter(r => /^\w+=/.test(r)).map(r => [r.slice(0, r.indexOf('=')), r.slice(r.indexOf('=') + 1).trim()]));
const NYCKEL = env[opt('nyckel', 'GEMINI_API_KEY_GRATIS')];

const S = (type, x = {}) => ({ type, ...x });
const schema = S('OBJECT', { properties: {
  saker: S('ARRAY', { items: S('OBJECT', { properties: {
    etikett: S('STRING', { description: 'kort svensk etikett, t.ex. pizzabit på papper, pappmugg, burk, pommes, bord, vägg, fönster, lampa' }),
    kategori: S('STRING', { enum: ['person', 'mat', 'dryck', 'förpackning', 'servis', 'möbel', 'rum', 'teknik', 'annat'] }),
    box_2d: S('ARRAY', { items: S('INTEGER'), description: '[ymin, xmin, ymax, xmax] 0-1000' }),
    karna: S('BOOLEAN', { description: 'sant om saken bär handlingen eller produkten i bilden' }),
    pa: S('STRING', { description: 'vad saken står på eller hålls av: bord, golv, vägg, hand, person' }) },
    required: ['etikett', 'kategori', 'box_2d', 'karna'] }) }) }, required: ['saker'] });

const prompt = `Bilden är en linjeteckning av en scen i en restaurang. Lista personer, varje enskilt föremål på borden och i händerna,
samt de viktigaste delarna av rummet (bord, väggar, fönster, lampor, disk). En ruta per föremål, tight runt föremålet.
${opt('kontext', '')}`;
const kropp = { contents: [{ role: 'user', parts: [{ inline_data: { mime_type: 'image/jpeg', data: fs.readFileSync(bild).toString('base64') } }, { text: prompt }] }],
  generationConfig: { responseMimeType: 'application/json', responseSchema: schema, temperature: 0.1, maxOutputTokens: 4000 } };
const kf = path.join(os.tmpdir(), `gb-${process.pid}.json`); fs.writeFileSync(kf, JSON.stringify(kropp));
const a = Date.now();
let r, j;
for (let f = 0; f < 4; f++) {
  r = spawnSync('curl', ['-sS', '--max-time', '600', '-X', 'POST', `https://generativelanguage.googleapis.com/v1beta/models/${MODELL}:generateContent`,
    '-H', 'content-type: application/json', '-H', `x-goog-api-key: ${NYCKEL}`, '--data-binary', '@' + kf], { encoding: 'utf8', maxBuffer: 1 << 26 });
  j = JSON.parse(r.stdout || '{}');
  if (!(j.error && /UNAVAILABLE|503|overloaded|high demand/i.test(j.error.status + j.error.message))) break;
  spawnSync(process.platform === 'win32' ? 'timeout' : 'sleep', process.platform === 'win32' ? ['/t', String(10 * (f + 1)), '/nobreak'] : [String(10 * (f + 1))], { stdio: 'ignore', shell: true });
}
fs.rmSync(kf, { force: true });
if (j.error) { console.log('FEL', j.error.code, j.error.message.slice(0, 200)); process.exit(1); }
const ut = JSON.parse(j.candidates[0].content.parts.map(p => p.text || '').join(''));
const fil = opt('ut', bild.replace(/\.jpg$/i, `.gemini-${MODELL}.json`));
fs.writeFileSync(fil, JSON.stringify({ modell: MODELL, ms: Date.now() - a, usage: j.usageMetadata, ...ut }, null, 1));
console.log(path.basename(bild), MODELL, 'ms', Date.now() - a, 'saker', ut.saker.length, '|', ut.saker.map(s => s.etikett + (s.karna ? '*' : '')).join(', '));
