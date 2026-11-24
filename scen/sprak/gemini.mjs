// Scenskrift ss/0.1: låt Gemini skriva klippets tidsbundna JSON.
// node sprak/gemini.mjs klipp/c-sketch-tre.mp4 [--modell gemini-3.8-flash] [--fps 10] [--nyckel GEMINI_API_KEY_GRATIS] [--upplosning LOW]
import fs from 'node:fs';
import path from 'node:path';

const arg = process.argv.slice(2);
const opt = (n, d) => { const i = arg.indexOf('--' + n); return i >= 0 ? arg[i + 1] : d; };
const video = arg[0];
const MODELL = opt('modell', 'gemini-3.8-flash');
const FPS = parseFloat(opt('fps', '10'));
const NYCKELNAMN = opt('nyckel', 'GEMINI_API_KEY_GRATIS');
const UPPL = opt('upplosning', 'LOW');
const ROT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1')), '..');

const env = Object.fromEntries(fs.readFileSync(path.join(ROT, '..', 'video', '.env.local'), 'utf8')
  .split('\n').filter(r => /^\w+=/.test(r)).map(r => [r.slice(0, r.indexOf('=')), r.slice(r.indexOf('=') + 1).trim()]));
const NYCKEL = env[NYCKELNAMN];
if (!NYCKEL) throw new Error('ingen nyckel ' + NYCKELNAMN);

const namn = path.basename(video, '.mp4');
const langdS = parseFloat(opt('langd', '0')) || null;

// ---------- schema (Geminis OpenAPI-delmängd) ----------
const S = (type, extra = {}) => ({ type, ...extra });
const E = (vals) => ({ type: 'STRING', enum: vals });
const PUNKT = S('ARRAY', { items: S('INTEGER'), description: '[y, x] 0-1000' });
const K = ['står', 'går', 'springer', 'sitter', 'böjd', 'hukar', 'sträcker'];
const H = ['tomma', 'håller', 'ger', 'tar', 'pekar', 'gestikulerar', 'arbetar', 'äter', 'betalar', 'telefon', 'ansikte'];
const ID = ['K', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6'];
const V = ['kamera', 'vänster', 'höger', 'bort', ...ID];
const VERB = ['går_in', 'går_ut', 'går_till', 'vänder_sig', 'sätter_sig', 'reser_sig', 'räcker', 'tar_emot', 'tar', 'lägger', 'håller_upp', 'visar', 'serverar', 'beställer', 'betalar', 'ringer', 'pratar', 'frågar', 'svarar', 'skär', 'lagar', 'smakar', 'äter', 'väger', 'reagerar', 'skrattar', 'döljer_ansikte', 'pekar', 'klappar'];
const schema = S('OBJECT', {
  properties: {
    huvud: S('OBJECT', { properties: { ss: S('STRING'), tick: S('NUMBER'), langd: S('INTEGER'), fps_sedd: S('NUMBER') }, required: ['ss', 'tick', 'langd'] }),
    rum: S('ARRAY', { items: S('OBJECT', { properties: {
      id: S('STRING'), typ: S('STRING'), beskr: S('STRING'), golv_y: S('INTEGER'),
      ankare: S('ARRAY', { items: S('OBJECT', { properties: { namn: S('STRING'), p: PUNKT, d: S('INTEGER') }, required: ['namn', 'p', 'd'] }) }) },
      required: ['id', 'typ', 'beskr', 'ankare'] }) }),
    roller: S('ARRAY', { items: S('OBJECT', { properties: { id: S('STRING'), roll: S('STRING'), utseende: S('STRING'), funktion: S('STRING') }, required: ['id', 'roll', 'utseende', 'funktion'] }) }),
    foremal: S('ARRAY', { items: S('OBJECT', { properties: { id: S('STRING'), typ: S('STRING'), beskr: S('STRING'), vikt: E(['bärande', 'stöd', 'bakgrund']) }, required: ['id', 'typ', 'vikt'] }) }),
    tagningar: S('ARRAY', { items: S('OBJECT', { properties: {
      id: S('STRING'), in: S('INTEGER'), ut: S('INTEGER'), rum: S('STRING'),
      utsnitt: E(['detalj', 'närbild', 'halvbild', 'helbild', 'total', 'pov']), kamera: E(['statisk', 'handhållen', 'panorering', 'åkning', 'zoom']),
      vinkel: S('STRING'), takt: E(['krok', 'uppbyggnad', 'vändning', 'payoff', 'avslut']), avsikt: S('STRING') },
      required: ['id', 'in', 'ut', 'rum', 'utsnitt', 'kamera', 'takt', 'avsikt'] }) }),
    banor: S('ARRAY', { items: S('OBJECT', { properties: {
      av: E(ID), tagning: S('STRING'),
      wp: S('ARRAY', { items: S('OBJECT', { properties: {
        t: S('INTEGER'), p: PUNKT, d: S('INTEGER'), f: PUNKT, k: E(K), v: E(V), h: E(H) }, required: ['t', 'p', 'd'] }) }) },
      required: ['av', 'tagning', 'wp'] }) }),
    handlingar: S('ARRAY', { items: S('OBJECT', { properties: { t: S('INTEGER'), dur: S('INTEGER'), vem: E(ID), verb: E(VERB), obj: E(ID), mot: E(ID) }, required: ['t', 'dur', 'vem', 'verb'] }) }),
    repliker: S('ARRAY', { items: S('OBJECT', { properties: { t: S('INTEGER'), dur: S('INTEGER'), vem: E(ID), till: E(ID), text: S('STRING') }, required: ['t', 'vem', 'text'] }) }),
    textlager: S('ARRAY', { items: S('OBJECT', { properties: { in: S('INTEGER'), ut: S('INTEGER'), text: S('STRING'), p: PUNKT }, required: ['in', 'ut', 'text'] }) }),
  },
  required: ['huvud', 'rum', 'roller', 'foremal', 'tagningar', 'banor', 'handlingar', 'repliker', 'textlager'],
});

const spec = fs.readFileSync(path.join(ROT, 'sprak', 'README.md'), 'utf8');
const prompt = `Du skriver Scenskrift ss/0.1 för den bifogade videon. Specifikationen:

${spec}

Instruktioner:
- 1 takt = 0,1 s. Videon samplas i ${FPS} bildrutor per sekund; ange tider i takter (heltal) så exakt du ser dem.${langdS ? ` Videon är ${langdS} s = ${Math.round(langdS * 10)} takter.` : ''}
- Varje klipp i videon är en egen tagning (S1, S2 …). Samma person i olika tagningar ska ha samma P-id (använd utseende).
- Följ waypoint-reglerna noga. Personer: punkt = höftmitt. Kameran räknas som egen aktör "K" om någon bakom kameran pratar eller räcker fram något.
- Repliker: skriv originalspråket ordagrant. Textlager: text som är inbränd i bilden.
- Beskrivningar (beskr, utseende, funktion, avsikt) på svenska, korta.
- Hitta inte på: utelämna det du inte ser.`;

const b64 = fs.readFileSync(video).toString('base64');
const kropp = {
  contents: [{ role: 'user', parts: [
    { inline_data: { mime_type: 'video/mp4', data: b64 }, videoMetadata: { fps: FPS } },
    { text: prompt }] }],
  generationConfig: {
    responseMimeType: 'application/json', responseSchema: schema, temperature: 0.2,
    mediaResolution: `MEDIA_RESOLUTION_${UPPL}`, maxOutputTokens: parseInt(opt('maxut', '16000')),
  },
};

const a = Date.now();
const TANK = opt('tank', 'low');
if (TANK !== 'av') kropp.generationConfig.thinkingConfig = { thinkingLevel: TANK };
// curl i stället för fetch: Nodes fetch ger upp efter 300 s utan svarshuvud
import { spawn } from 'node:child_process';
import os from 'node:os';
async function strom(kropp) {
  const kf = path.join(os.tmpdir(), `ss-kropp-${process.pid}.json`);
  fs.writeFileSync(kf, JSON.stringify(kropp));
  const cu = spawn('curl', ['-sS', '-N', '--max-time', '1800', '-X', 'POST',
    `https://generativelanguage.googleapis.com/v1beta/models/${MODELL}:streamGenerateContent?alt=sse`,
    '-H', 'content-type: application/json', '-H', `x-goog-api-key: ${NYCKEL}`, '--data-binary', '@' + kf]);
  let buf = '', text = '', usage = null, finish = null, forst = null, n = 0, ra = '';
  const dec = new TextDecoder();
  for await (const bit of cu.stdout) {
    const s = dec.decode(bit, { stream: true }); buf += s; if (ra.length < 4000) ra += s;
    let i;
    if (!buf.includes('data: ') && /^\s*[\[{]/.test(buf) && /"error"/.test(buf)) continue;
    buf = buf.replace(/\r\n/g, '\n');
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const rad = buf.slice(0, i); buf = buf.slice(i + 2);
      const dl = rad.split('\n').filter(x => x.startsWith('data: ')).map(x => x.slice(6)).join('');
      if (!dl) continue;
      const j = JSON.parse(dl);
      if (j.error) return { error: j.error };
      const t = j.candidates?.[0]?.content?.parts?.filter(p => !p.thought).map(p => p.text || '').join('') || '';
      if (t && forst === null) forst = Date.now() - a;
      text += t; usage = j.usageMetadata || usage; finish = j.candidates?.[0]?.finishReason || finish;
      if (++n % 40 === 0) process.stdout.write(`[${((Date.now() - a) / 1000).toFixed(0)}s ${text.length} tecken] `);
    }
  }
  fs.rmSync(kf, { force: true });
  if (!text && /"error"/.test(ra)) { try { const e = JSON.parse(ra); return { error: (Array.isArray(e) ? e[0] : e).error }; } catch { return { error: { message: ra.slice(0, 300) } }; } }
  return { text, usage, finish, forst };
}
let j = await strom(kropp);
for (let f = 1; f <= 5 && j.error && /UNAVAILABLE|overloaded|high demand|503/i.test(j.error.status + j.error.message); f++) { console.log(`503, försök ${f + 1} om ${15 * f}s`); await new Promise(r => setTimeout(r, 15000 * f)); j = await strom(kropp); }
if (j.error && /thinking/i.test(j.error.message)) { console.log('tänkande avvisades:', j.error.message.slice(0, 120)); delete kropp.generationConfig.thinkingConfig; j = await strom(kropp); }
if (j.error && /processing/i.test(j.error.message)) {
  console.log('processing avvisades, provar videoMetadata:', j.error.message.slice(0, 160));
  kropp.contents[0].parts[0] = { inline_data: kropp.contents[0].parts[0].inline_data, videoMetadata: { fps: FPS } };
  j = await strom(kropp);
}
const ms = Date.now() - a;
if (j.error) { console.log('FEL', j.error.code, j.error.status, j.error.message.slice(0, 400)); process.exit(1); }
const text = j.text || '';
let ss = null; try { ss = JSON.parse(text); } catch (e) { console.log('JSON-fel', e.message); }
const ut = path.join(ROT, 'data', namn, `ss-${MODELL}-fps${FPS}.json`);
fs.writeFileSync(ut, JSON.stringify({ modell: MODELL, fps: FPS, upplosning: UPPL, ms, forsta_token_ms: j.forst, usage: j.usage, finish: j.finish, ss, ratext: ss ? undefined : text }, null, 1));
const u = j.usage || {};
console.log(namn, MODELL, 'fps', FPS, 'ms', ms, 'in', u.promptTokenCount, 'ut', u.candidatesTokenCount, 'tänk', u.thoughtsTokenCount || 0, 'finish', j.finish, 'första token ms', j.forst);
if (ss) console.log('tagningar', ss.tagningar?.length, 'roller', ss.roller?.length, 'banor', ss.banor?.length, 'waypoints', ss.banor?.reduce((s, b) => s + b.wp.length, 0), 'handlingar', ss.handlingar?.length, 'repliker', ss.repliker?.length);
console.log('->', ut);
