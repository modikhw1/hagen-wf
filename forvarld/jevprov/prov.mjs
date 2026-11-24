// Litet sekventiellt HTTP-prov. Inga beroenden, ingen rendering.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { nyckel, MODELL } from '../../app/kalibrering/jev.mjs';

export const DIR = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(DIR, '../..');
export const OUT = path.join(DIR, 'ut');
export const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
export const write = (p, x) => { fs.mkdirSync(path.dirname(p), {recursive:true}); fs.writeFileSync(p, JSON.stringify(x, null, 2)+'\n', 'utf8'); };
export const hash = x => crypto.createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
export const DATA = read(path.join(DIR, 'meningar.json'));
export const K = read(path.join(ROOT, 'scen/3d/kontrakt/exempel/notan/kalla.json'));
const sem = K.semantik;
const roll = {woman:'kvinna/kund', man:'man/kund', waiter:'servitör'};
const personer = sem.personer.filter(p=>['A','B','C'].includes(p.id));
const personrad = p => `${p.id}: ${roll[p.roll]??p.roll}; `+sem.scener.filter(s=>s.personer.includes(p.id)).map(s=>`${s.id} ${s.bindningar.find(b=>b.person===p.id)?.hallning??'okänt'}`).join(', ');
const scenrad = s => `${s.id} ${s.funktion??'funktion okänd'}: ${s.personer.join(',')} ${s.bindningar.map(b=>b.hallning).join(',')}; `+sem.repliker.filter(r=>r.scen===s.id).map(r=>`${r.id}/${r.talare}: ${r.text}`).join(' | ');
export function states() {
  const minimal = [
    `Notan: ${K.tidsbas.langd_s} s; dialog om vem som betalar. Scenordning ${sem.scener.map(s=>s.id).join(',')}.`,
    ...personer.map(personrad), ...sem.scener.map(scenrad),
    `Plats ${sem.platser[0].id}, mall ${sem.platser[0].rumsmall_id}; ankare ${sem.platser[0].ankare.map(a=>a.id).join(',')}. Props: ${sem.props.map(p=>p.id+' '+p.etikett).join(',')}. Skärmtext: undertexter st1–st7 till r1–r7. Ljud: dialog; musik okänd. Ingen separat bild/video angiven.`,
  ].join('\n');
  const full = [
    `Notan: ${K.tidsbas.langd_s} sekunder, ${K.klipp.video.bredd}×${K.klipp.video.hojd}. Dialog om notan. Uppgifter som saknas är okända, inte förbjudna ändringar.`,
    ...personer.map(personrad),
    ...sem.scener.map(s=>`${scenrad(s)}; ${s.start_s}–${s.slut_s} s; kamera ${s.kamera}; plats ${s.plats_id}; bindning ${s.bindningar.map(b=>b.person+'='+b.ankare).join(',')}.`),
    ...sem.repliker.map(r=>`${r.id}: talare ${r.talare}, scen ${r.scen}, ${r.start_s}–${r.slut_s} s, ${r.i_bild?'i bild':'utanför bild'}, text: ${r.text}`),
    ...sem.platser.map(p=>`Plats ${p.id}: typ ${p.typ}; mall ${p.rumsmall_id}; ${p.beskrivning} Ankare: ${p.ankare.map(a=>a.id+' '+a.typ).join('; ')}.`),
    `Props i källan: ${sem.props.map(p=>p.id+' ('+p.typ+', '+p.etikett+')').join('; ')}. Övrig rekvisita är inte identifierad i denna källa.`,
    ...sem.skarmtext.map(t=>`${t.id}: ${t.typ} i ${t.scen}, replik ${t.replik}, ${t.start_s.toFixed(2)}–${t.slut_s.toFixed(2)} s, ${t.stil.storlek_px}px: ${t.text.replaceAll('\n',' ')}`),
    `Ljud: ${sem.ljud.tal}; musik ${sem.ljud.musik??'okänd'}. Separat medialager inte beskrivet. Okänd person utan roll i s4 är inte A/B/C.`,
  ].join('\n');
  return {minimal, full};
}
const FEN = ['steady or calmer camera','closer, wider or different camera angle','facial expression','body movement, gesture, stand/sit/walk','casting, clothes or color','different venue or background','change dialogue text or language','change, add or remove on-screen text or subtitles','change, add or remove a physical object','shorten or lengthen scene or clip','remove, add, move or duplicate a scene','music, sound effects or volume','insert or replace a separate image/video','clarification or slower reasoning needed; no specific edit can be selected'];
const fams = Object.keys(DATA.familjer);
const supported = {
  kamera:['kamera.stabilisera','kamera.utsnitt'],
  person_A:['person.uttryck','person.rorelse','person.utseende'],
  person_B:['person.uttryck','person.rorelse','person.utseende'],
  person_C:['person.uttryck','person.rorelse','person.utseende'],
  plats:['plats.byt'], repliker:['replik.byt'], skarmtext:['text.andra'], props:['prop.andra','kamera.utsnitt'],
  scenstruktur:['scen.langd','scen.ordning'], ljud:['ljud.andra'], medialager:['media.bild'],
};
const PEN = ['camera framing/movement','person A only','person B only','person C only','venue/background','spoken words/dialogue content','on-screen text/subtitles','physical objects','scene duration/order/structure','music/audio','separate image/video layer'];
const parts = DATA.delar;
const policy = lang => lang==='sv'
  ? 'Tolka CM:s mening som en redigeringsbegäran. Välj den direkta ändringen, inte följdarbete. Vaga kvalitetsönskemål utan angiven ändring kräver oklar. Flera tydliga ändringar får ha flera delar. Ingen ändring exekveras här.'
  : 'Interpret the CM sentence as an edit request. Select direct changes, not downstream work. Vague quality goals without a specified change require oklar. Multiple explicit edits may concern multiple parts. No edit is executed here.';
const desc = (f,lang) => lang==='sv'?DATA.familjer[f]:FEN[fams.indexOf(f)];
const pd = (p,lang) => lang==='sv'?p:PEN[parts.indexOf(p)];
const choice = (instructions,criteria) => ({type:'choice', instructions, criteria});
function familyQ(lang, allowed=fams, subject='') {
  return choice(policy(lang)+' '+(lang==='sv'?`Vilken ändringsfamilj passar bäst ${subject}?`:`Which edit family fits best ${subject}?`),Object.fromEntries(allowed.map(f=>[f,desc(f,lang)])));
}
function partsQ(lang, family) {
  // Alla tomma, enkla och dubbla delmängder ryms under API-gränsen 255.
  const sets=[[],...parts.map(p=>[p]),...parts.flatMap((p,i)=>parts.slice(i+1).map(q=>[p,q]))];
  return choice(policy(lang)+' '+(lang==='sv'?`Vilka delar ändras direkt? Vald familj: ${family}. Tom mängd om ingen konkret ändring kan väljas.`:`Which parts are directly changed? Selected family: ${family}. Empty set if no concrete edit can be selected.`),Object.fromEntries(sets.map((s,i)=>['p'+i,s.length?s.map(p=>pd(p,lang)).join(' + '):(lang==='sv'?'inga delar / oklar':'no parts / unclear')])));
}
function decodeParts(v) {
  const sets=[[],...parts.map(p=>[p]),...parts.flatMap((p,i)=>parts.slice(i+1).map(q=>[p,q]))];
  return sets[Number(v?.slice(1))]??[];
}
export async function api(tag,state,questions) {
  const target=path.join(OUT,'anrop',tag+'.json');
  if(fs.existsSync(target)) throw new Error('Redan utfört anrop: '+tag);
  const ledger=path.join(OUT,'anropslogg.jsonl');
  const count=fs.existsSync(ledger)?fs.readFileSync(ledger,'utf8').trim().split('\n').filter(Boolean).length:0;
  if(count>=1990) throw new Error('Anropstaket nått');
  const key=nyckel(path.join(ROOT,'app')); if(!key) throw new Error('API-nyckel saknas');
  const request={model:MODELL,state,questions};
  fs.mkdirSync(path.dirname(target),{recursive:true});
  const t=performance.now();
  fs.appendFileSync(ledger,JSON.stringify({tag,tid:new Date().toISOString(),nummer:count+1})+'\n');
  let response,raw,status;
  try {
    const r=await fetch('https://api.typesafe.ai/v1/systemone',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify(request),signal:AbortSignal.timeout(30000)});
    status=r.status; const body=await r.text();
    try {raw=JSON.parse(body);} catch {raw={fel:'Svaret var inte JSON',status};}
    response={tag,request,status,raw,ms:performance.now()-t};
  } catch(e) {response={tag,request,status:null,raw:null,ms:performance.now()-t,fel:e.name};}
  write(target,response);
  if(response.status!==200) throw new Error(`Anrop misslyckades: ${tag}, HTTP ${response.status}, se sparad post`);
  return response;
}
export async function route(strategy,item,config,tag) {
  const state=config.state+'\nCM: '+item.mening;
  const lang=config.language; const calls=[]; const t=performance.now();
  const ask=async(q,suffix)=>{const r=await api(tag+'-'+suffix,state,q);calls.push(r);return r.raw.answers;};
  let families=[],selected=[],margin=null,ranking=null;
  if(strategy==='a') {
    const q=Object.fromEntries(parts.map(p=>[p,choice(policy(lang)+' '+(lang==='sv'?`Du ansvarar för ${pd(p,lang)}. Gäller begäran en direkt ändring hos dig?`:`You control ${pd(p,lang)}. Does this request directly concern you?`),{ja:lang==='sv'?'Ja, min del ändras direkt':'Yes, my part is directly changed',nej:lang==='sv'?'Nej':'No'})]));
    const a=await ask(q,'delar'); selected=parts.filter(p=>a[p]?.choice==='ja');
    if(selected.length) {
      const b=await ask(Object.fromEntries(selected.map(p=>[p,familyQ(lang,[...supported[p],'oklar'],pd(p,lang))])),'familjer');
      families=[...new Set(selected.map(p=>b[p].choice))];
    } else families=['oklar'];
  } else {
    let a;
    if(strategy==='b') {a=await ask({familj:familyQ(lang)},'familj');families=[a.familj.choice];}
    else {
      a=await ask(Object.fromEntries(fams.map((f,i)=>['f'+i,{type:'score',instructions:policy(lang)+' '+(lang==='sv'?`Hur väl stämmer familjen ${f}: ${desc(f,lang)} med den direkta begäran?`:`How well does family ${f}: ${desc(f,lang)} match the direct request?`),criteria:lang==='sv'?['0: stämmer inte','1: svagt','2: möjligt','3: tydligt','4: exakt']:['0: no match','1: weak','2: possible','3: clear','4: exact']}])),'poang');
      ranking=fams.map((f,i)=>({family:f,score:a['f'+i].score,confidence:a['f'+i].confidence})).sort((x,y)=>y.score-x.score||fams.indexOf(x.family)-fams.indexOf(y.family));
      families=[ranking[0].family];margin=ranking[0].score-ranking[1].score;
    }
    if(families[0]!=='oklar') {
      const b=await ask({delar:partsQ(lang,families[0])},'delar'); selected=decodeParts(b.delar.choice);
    }
  }
  const result={id:item.id,mening:item.mening,strategy,config:config.id,families,parts:selected,margin,ranking,ms:performance.now()-t,http_ms:calls.reduce((s,c)=>s+c.ms,0),calls:calls.length,input_tokens:calls.reduce((s,c)=>s+(c.raw.usage?.input_tokens??0),0),requests:calls.map(c=>c.tag)};
  write(path.join(OUT,'rutter',tag+'.json'),result);return result;
}
export function judge(r,item) {
  const acceptable=[item.familj,...(item.andra_familj?[item.andra_familj]:[])];
  if(item.id==='u3')acceptable.push('oklar');
  if(item.id==='t15')acceptable.push('kamera.utsnitt');
  if(item.id==='t20')acceptable.push('scen.ordning');
  let expected=[item.delar];
  if(['t3','t12','t14'].includes(item.id))expected=[['person_A'],['person_B']];
  if(item.id==='u3')expected=[['person_A'],['person_B'],['person_C'],[]];
  if(item.id==='t15')expected.push(['props']);
  const same=(a,b)=>[...a].sort().join('|')===[...b].sort().join('|');
  return {family:r.families.some(f=>acceptable.includes(f)),family_all:r.families.every(f=>acceptable.includes(f)),parts_exact:expected.some(s=>same(s,r.parts)),parts_any:expected.some(s=>s.length?s.some(p=>r.parts.includes(p)):!r.parts.length),oklar_expected:item.familj==='oklar',oklar:r.families.includes('oklar')};
}
export const quantile=(a,p)=>{a=[...a].sort((a,b)=>a-b);return a[Math.max(0,Math.ceil(p*a.length)-1)]??null;};
async function development() {
  if(fs.existsSync(path.join(OUT,'fryst.json')))throw new Error('Redan fryst; utv får inte ändra testet');
  const ss=states();write(path.join(OUT,'tillstand.json'),ss);
  const measures={};
  for(const [size,state] of Object.entries(ss)) {
    const r=await api('storlek-'+size,state,{q:choice('Är detta ett klipp?',{ja:'Ja',nej:'Nej'})});
    measures[size]={lines:state.split('\n').length,characters:state.length,input_tokens:r.raw.usage?.input_tokens,usage:r.raw.usage};
  }
  const all=[];
  for(const size of ['minimal','full'])for(const language of ['sv','en']) {
    const config={id:size+'-'+language,language,state:ss[size]};
    for(const item of DATA.utv)for(const strategy of ['a','b','c'])all.push(await route(strategy,item,config,`utv-${config.id}-${item.id}-${strategy}`));
    console.log('Klar utv '+config.id);
  }
  const summary=[];
  for(const size of ['minimal','full'])for(const language of ['sv','en']) {
    const id=size+'-'+language;const rows=all.filter(r=>r.config===id);
    const j=rows.map(r=>judge(r,DATA.utv.find(i=>i.id===r.id)));
    summary.push({id,size,language,family:j.filter(x=>x.family).length,parts_exact:j.filter(x=>x.parts_exact).length,n:rows.length,median_ms:quantile(rows.map(r=>r.ms),.5),tokens:rows.reduce((s,r)=>s+r.input_tokens,0)/rows.length});
  }
  // Förhandsbestämt val: flest rätt familjer, därefter exakta delar, färre tokens och svenska vid lika.
  summary.sort((a,b)=>b.family-a.family||b.parts_exact-a.parts_exact||a.tokens-b.tokens||a.language.localeCompare(b.language));
  write(path.join(OUT,'utveckling.json'),{measures,summary,rows:all});
  const best=summary[0];
  const frozen={id:best.id,language:best.language,size:best.size,state:ss[best.size],frozen_at:new Date().toISOString(),script_sha256:hash(fs.readFileSync(fileURLToPath(import.meta.url),'utf8')),meningar_sha256:hash(fs.readFileSync(path.join(DIR,'meningar.json'),'utf8')),selection_rule:'Familj, exakta delar, lägst medeltokens. Ingen testmening används.',score_tie_rule:'Första familjen i den ursprungliga slutna listan vid lika score.',price_usd_per_million_input:0.04};
  write(path.join(OUT,'fryst.json'),frozen);console.log(JSON.stringify({measures,summary,frozen:best.id},null,2));
}
async function tests() {
  const config=read(path.join(OUT,'fryst.json'));
  if(hash(fs.readFileSync(fileURLToPath(import.meta.url),'utf8'))!==config.script_sha256)throw new Error('Fryst skript har ändrats');
  for(let run=1;run<=3;run++)for(const item of DATA.test)for(const strategy of ['a','b','c']) {
    const tag=`test-${run}-${item.id}-${strategy}`;
    // Fortsättning hoppar bara över redan sparade fullständiga meningar.
    if(fs.existsSync(path.join(OUT,'rutter',tag+'.json')))continue;
    await route(strategy,item,config,tag);
    if(item.id==='t20'&&strategy==='c')console.log('Klar testomgång '+run);
  }
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const cmd=process.argv[2];
  if(cmd==='utv')await development();else if(cmd==='test')await tests();else console.log('node forvarld/jevprov/prov.mjs utv|test');
}
