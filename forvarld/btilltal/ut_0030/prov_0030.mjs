// Uppdrag 0030: b-tilltals tio meningar (forvarld/btilltal/meningar.json) med källan kalla_0030 (handlingsspår och relevans), samma väg som gelato 0029.
// Kopia av forvarld/gelato/prov.mjs; tillståndet har b-tilltals form ur forvarld/btilltal/prov.mjs (0016) plus meningen i villkoret MED.
// Uppdrag 0029: de tio gelato-meningarna genom tillstånd -> Jev familj -> Jev delar -> konkret val -> regi, i två villkor:
//   MED=1: tillståndet har handlingsspåret och relevanslistan i kort form (ut/), MED=0: samma tillstånd utan dem (ut_utan/).
// Anpassat från forvarld/btilltal/prov.mjs (som inte ändras). Familjer och delar är Notan-provets frysta, plus handling.andra (0029).
// Nyckeln läses med app/kalibrering/jev.mjs:nyckel() och skrivs aldrig ut. Varje anrop sparas i <ut>/anrop/ och återanvänds.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { nyckel, MODELL } from '../../../app/kalibrering/jev.mjs';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(DIR, '../../..');
const MED = process.env.MED !== '0';
const OUT = path.join(DIR, MED ? 'med' : 'utan');
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const write = (p, x) => { fs.mkdirSync(path.dirname(p), {recursive:true}); fs.writeFileSync(p, JSON.stringify(x, null, 2)+'\n', 'utf8'); };
const JEV = read(path.join(ROOT, 'forvarld/jevprov/meningar.json'));
const M = read(path.join(DIR, '..', 'meningar.json'));
const KALLA = path.join(ROOT, 'scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand/kalla_0030.json');
const K = read(KALLA); const sem = K.semantik;
const BAS = read(path.join(DIR, '..', 'ut_0016/regi/bas.json'));
const namn = {A:'Mads', B:'Morten', C:'Lærke'};
const PLAN = read(path.join(ROOT, 'scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand/narvaro/plan.json'));
const fmt = x => (Math.round(x*100)/100).toFixed(2).replace('.', ',');
const V = f => f?.varde ?? null;
// Verben i handlingsspårets ordförråd på svenska (ordförrådet är kodord; Jev läser svenska).
const VERB = {sta:'står', ga:'går', luta_sig:'lutar sig', rata_pa_sig:'rätar på sig', vanda_sig:'vänder sig', titta:'tittar', peka:'pekar', ta:'tar (skopar upp)', halla:'håller fram', lyfta:'lyfter', sanka:'sänker', racka:'räcker fram'};
const verb = g => VERB[V(g.handling)] ?? V(g.handling);

// Tillståndet: samma form som b-tilltal (0016), byggt ur gelatos källa. Mening (handlingsspår och relevans) bara i villkoret MED.
export function state(med) {
  const hand = sem.handling ?? []; const rel = sem.relevans;
  return [
    `b-tilltal-ravara: ${K.tidsbas.langd_s} sekunder, ${K.klipp.video.bredd}×${K.klipp.video.hojd}. Montage i en slaktarbutik: tre personer gissar vad en köttbit väger, den vägs sist. Uppgifter som saknas är okända, inte förbjudna ändringar.`,
    ...sem.personer.map(p => `${p.id}: ${p.roll}, ${p.beskrivning} Namn i skärmtexten: ${namn[p.id]??'okänt'}. Scener: ${sem.scener.filter(s=>s.personer.includes(p.id)).map(s=>s.id).join(',')}.`),
    ...sem.scener.map(s => `${s.id} ${s.funktion}: ${s.syfte} Personer ${s.personer.join(',')} (${s.bindningar.map(b=>b.person+'='+b.ankare+' '+b.hallning).join(',')}); ${s.start_s}–${s.slut_s} s; kamera ${s.kamera}; plats ${s.plats_id}.`),
    ...sem.repliker.map(r => `${r.id}: talare ${r.talare??'okänd'}, scen ${r.scen}, ${r.start_s}–${r.slut_s} s, ${r.i_bild?'i bild':'utanför bild'}, text (${r.sprak}): ${r.text}`),
    ...sem.platser.map(p => `Plats ${p.id}: typ ${p.typ}. Ankare: ${p.ankare.map(a=>a.id).join(', ')}.`),
    `Props i källan: ${sem.props.map(p=>p.id+' ('+p.typ+')'+(p.deklaration?` syns i ${p.deklaration.scener.join(',')}${p.deklaration.pa?', står på '+p.deklaration.pa:''}${p.deklaration.i_hand.length?', i hand hos '+[...new Set(p.deklaration.i_hand.map(h=>h.person))].join(','):''}`:'')).join('; ')}. Övrig rekvisita är inte identifierad i denna källa.`,
    ...(sem.scengrupper??[]).map(g=>`Scengrupp ${g.id}: ${namn[g.roll]??g.roll} i bild i ${g.scener.join(',')}; flyttas och tas bort som en enhet.`),
    `Skärmtext: ${sem.skarmtext.length} överlägg, en löpande resultattavla. ` + [...new Set(sem.skarmtext.map(t=>t.scen))].map(sc=>sc+': '+sem.skarmtext.filter(t=>t.scen===sc).map(t=>t.id+' "'+t.text+'"').join(' ')).join(' | '),
    `Ljud: ${sem.ljud?.tal??'tal'}; musik ${sem.ljud?.musik??'okänd'}.`,
    ...(med ? [
      ...hand.map(h => `Handlingar i ${h.scen}: ` + h.segment.map(g => `${g.id} ${fmt(g.tid_s[0])}–${fmt(g.tid_s[1])} s ${namn[g.vem]??g.vem} ${verb(g)}${V(g.i_handen)?' håller '+V(g.i_handen):''}${V(g.mal)?' mot '+V(g.mal):''}${V(g.blick)?' tittar '+V(g.blick):''}`).join('; ') + '.'),
      ...(rel ? [`Klippets mening: ${rel.mening}`,
                 `Bär meningen: ${rel.poster.filter(p=>p.roll==='bar').map(p=>`${p.namn??p.id}${p.ref?' ('+p.ref+')':''}`).join(', ')}. Ramar: ${rel.poster.filter(p=>p.roll==='ramar').map(p=>`${p.namn??p.id}`).join(', ')}. Brus: ${rel.poster.filter(p=>p.roll==='brus').map(p=>p.namn??p.id).join(', ')||'inget'}.`] : []),
      'Segmenten kan tas bort, spelas långsammare eller snabbare, eller upprepas.',
    ] : []),
  ].join('\n');
}


const FAM = {...JEV.familjer}; delete FAM.oklar; FAM['handling.andra'] = 'en handling i klippet: ta bort den, sakta ned, snabba upp eller upprepa den'; FAM.oklar = JEV.familjer.oklar;
const parts = JEV.delar;
const policy = 'Tolka CM:s mening som en redigeringsbegäran. Välj den direkta ändringen, inte följdarbete. Vaga kvalitetsönskemål utan angiven ändring kräver oklar. Flera tydliga ändringar får ha flera delar. Ingen ändring exekveras här.';
const choice = (instructions, criteria) => ({type:'choice', instructions, criteria});
const sets = [[], ...parts.map(p=>[p]), ...parts.flatMap((p,i)=>parts.slice(i+1).map(q=>[p,q]))];

let calls = 0;
async function api(tag, st, questions) {
  const target = path.join(OUT, 'anrop', tag+'.json');
  if (fs.existsSync(target)) return read(target);
  if (++calls > 45) throw new Error('Anropstaket för villkoret (45) nått');
  const key = nyckel(path.join(ROOT, 'app')); if (!key) throw new Error('API-nyckel saknas');
  const request = {model:MODELL, state:st, questions}; const t = performance.now();
  const r = await fetch('https://api.typesafe.ai/v1/systemone', {method:'POST', headers:{Authorization:`Bearer ${key}`, 'Content-Type':'application/json'}, body:JSON.stringify(request), signal:AbortSignal.timeout(30000)});
  const body = await r.text(); let raw; try { raw = JSON.parse(body); } catch { raw = {fel:'inte JSON'}; }
  const res = {tag, request, status:r.status, raw, ms:performance.now()-t}; write(target, res);
  fs.appendFileSync(path.join(OUT, 'anropslogg.jsonl'), JSON.stringify({tag, tid:new Date().toISOString(), status:r.status, input_tokens:raw?.usage?.input_tokens, ms:Math.round(res.ms)})+'\n');
  if (r.status !== 200) throw new Error(`HTTP ${r.status} för ${tag}`);
  return res;
}

const scener = Object.fromEntries(sem.scener.map(s=>[s.id, `${s.id}: ${s.syfte} (${s.personer.join(',')}, ${s.start_s}–${s.slut_s} s)`]));
const grupper = Object.fromEntries((sem.scengrupper??[]).map(g=>[g.id, `${g.id}: grupp, ${namn[g.roll]??g.roll} i ${g.scener.join('+')}`]));
const ordet = m => (m.match(/\bmot (?:en |ett )?([a-zåäö]+)/i)||[])[1] ?? null;   // ny typ ur meningen, som citat för text
const personer = Object.fromEntries(sem.personer.map(p=>[p.id, `${p.id}: ${namn[p.id]}, ${p.roll}`]));
const texter = Object.fromEntries(sem.skarmtext.map(t=>[t.id, `${t.id} i ${t.scen}: "${t.text}"`]));
const props = {...Object.fromEntries(sem.props.map(p=>[p.id, p.id+' ('+p.typ+')'])), saknas:'Föremålet finns inte bland källans props'};
const rum = Object.fromEntries(fs.readdirSync(path.join(ROOT,'scen/3d/kontrakt/rumsmall')).filter(n=>n.endsWith('.json')&&!n.startsWith('dekl_')&&!['rumsmall.schema.json','lokalkoder.json'].includes(n)).map(n=>{const r=read(path.join(ROOT,'scen/3d/kontrakt/rumsmall',n));return [r.id, (r.beskrivning??r.id).slice(0,140)];}));
const proptyper = (()=>{ try { const b=read(path.join(ROOT,'scen/3d/kontrakt/propbank/propbank.json')); return Object.fromEntries((b.typer??b.props??[]).map(x=>[x.id??x.typ, x.beskrivning??x.id??x.typ]).slice(0,60)); } catch { return {}; } })();
const citat = s => (s.match(/"([^"]+)"/g)||[]).map(x=>x.slice(1,-1));

// Konkreta frågor per familj: bara slutna, lagliga alternativ ur tillståndet. Ny text tas ur citat, aldrig ur Jev.
// Segmenten som korta svenska val: verb, mål och föremål med relevanslistans namn (källans id där namn saknas).
const namnFor = id => { if (!id) return null; const ps = (sem.relevans?.poster??[]).filter(x=>x.ref && (x.ref===id || String(id).startsWith(x.ref+':'))).sort((a,b)=>b.ref.length-a.ref.length); return (ps[0]?.namn ?? id).toLowerCase(); };
const segment = Object.fromEntries((sem.handling??[]).flatMap(h=>h.segment.map(g=>[g.id, `${verb(g)}${V(g.mal)?' mot '+namnFor(V(g.mal)):''}${V(g.foremal)?' med '+namnFor(V(g.foremal)):''} (${fmt(g.tid_s[0])}–${fmt(g.tid_s[1])} s)`])));
const segScen = Object.fromEntries((sem.handling??[]).flatMap(h=>h.segment.map(g=>[g.id, h.scen])));

const KONKRET = {
  'scen.ordning': {q:{atgard:choice('Vilken scenåtgärd?',{ta_bort:'ta bort en scen',flytta:'flytta en scen',duplicera:'duplicera en scen',lagg_till:'lägg till en ny scen'}),scen:choice('Vilken scen eller scengrupp gäller det?',{...scener,...grupper}),efter:choice('Om scenen flyttas eller läggs till: efter vilken scen eller grupp? (forst = först)',{forst:'först, före alla',...scener,...grupper})},
    build:(a)=>a.atgard==='ta_bort'?[{op:'ta_bort_scen',scen:a.scen}]:a.atgard==='flytta'?[{op:'flytta_scen',scen:a.scen,efter:a.efter==='forst'?null:a.efter}]:a.atgard==='duplicera'?[{op:'duplicera_scen',scen:a.scen,ny_id:a.scen+'_kopia',efter:a.efter==='forst'?null:a.efter,med_ljud:true}]
      :[{op:'lagg_till_scen',ny_id:'s_ny',efter:a.efter==='forst'?null:a.efter,mall:{fran_scen:a.scen,motiv:null},langd_s:1.5,personer:['PLATSHALLARE:ny_person'],kommentar:'ingen fjärde person finns i källan'}]},
  'text.andra': {q:{text:choice('Vilken befintlig skärmtext avses?',texter),atgard:choice('Vad ska göras med den?',{byt:'byt texten',ta_bort:'ta bort den'})},
    build:(a,m)=>[{op:'skarmtext',atgard:a.atgard,skarmtext_id:a.text,scen:sem.skarmtext.find(t=>t.id===a.text).scen,text:a.atgard==='byt'?(citat(m).at(-1)??null):null}]},
  'kamera.utsnitt': {q:{scen:choice('Vilken scen?',scener),person:choice('Vem ska kameran rikta in sig på?',personer),inramning:choice('Vilket utsnitt?',{nara:'nära',halv:'halv',hel:'hel'})},
    build:(a)=>[{op:'renderkamera',scen:a.scen,kamera_id:'jev_kam',lage:'stativ',inramning:a.inramning,mal:{typ:'person',id:a.person,punkt:'huvud'}}]},
  'kamera.stabilisera': {q:{scen:choice('Vilken scen?',scener)}, build:(a)=>[{op:'renderkamera',scen:a.scen,kamera_id:'jev_kam',lage:'stativ'}]},
  'prop.andra': {q:{prop:choice('Vilket befintligt föremål avses? Välj saknas om det inte finns bland källans props.',props),atgard:choice('Vad ska göras?',{ta_bort:'ta bort',byt:'byt mot annat föremål'}),scen:choice('I vilken omfattning? Välj alla scener om meningen inte själv nämner en scen.',{alla:'alla scener',...scener}),
      ny_typ:choice('Om föremålet byts: vilken ny typ? (meningens = det föremål meningen själv namnger, saknas om ingen passar)',{...proptyper,meningens:'det föremål meningen namnger',saknas:'ingen passande typ'})},
    build:(a,m)=>{const p=a.prop==='saknas'?'PLATSHALLARE:foremal':a.prop;const nt=a.ny_typ==='meningens'?(ordet(m)??'PLATSHALLARE:typ'):a.ny_typ==='saknas'?'PLATSHALLARE:typ':a.ny_typ;return a.atgard==='ta_bort'?[{op:'ta_bort_prop',scen:a.scen,prop:p,kommentar:a.prop==='saknas'?'föremålet saknas bland källans props':undefined}]:[{op:'byt_prop',scen:a.scen,prop:p,ny_typ:nt,kommentar:'0014/0016'}];}},
  'plats.byt': {q:{rum:choice('Vilken verklig mall i banken motsvarar begärd lokal?',rum)}, build:(a)=>[{op:'byt_miljo',scen:'alla',rum:{kalla:'bank',tillgang_id:a.rum,rumsmall_id:a.rum,ord:[],beskrivning:null}}]},
  'scen.langd': {q:{scen:choice('Vilken scen ska ändra längd?',scener),andring:choice('Hur mycket?',{p05:'+0,5 s',p10:'+1,0 s',m05:'-0,5 s',m10:'-1,0 s'})},
    build:(a)=>{const s=sem.scener.find(x=>x.id===a.scen);const d={p05:.5,p10:1,m05:-.5,m10:-1}[a.andring];return d>0?[{op:'trimma_scen',scen:a.scen,slut_s:+(s.slut_s+d).toFixed(4),lage:'hall_sista'}]:[{op:'trimma_scen',scen:a.scen,start_s:s.start_s,slut_s:+(s.slut_s+d).toFixed(4),lage:'klipp_slut'}];}},
  'person.rorelse': {q:{person:choice('Vilken person?',personer),scen:choice('I vilken scen?',scener)},
    build:(a,m)=>[{op:'rorelse',person:a.person,scen:a.scen,motiv:'armar_i_kors',bibliotek:{id:'PLATSHALLARE:bibliotek',version:'saknas'},hastighet:1,intensitet:1,blandning_s:.3,rotjustering:'behall_uppmatt_rot',kontaktpolicy:'behall_fotkontakt',kommentar:'inget rörelsebibliotek med armar i kors finns; motivet är meningens'}]},
  'person.utseende': {q:{person:choice('Vilken person?',personer)}, build:(a)=>[{op:'casta',person:a.person,kundroll:{roll:'okänd'},utseende:{}}]},
  'handling.andra': {q:{atgard:choice('Vad ska göras med handlingen?',{ta_bort:'ta bort den (hoppa över den)',langsammare:'spela den långsammare',snabbare:'spela den snabbare',upprepa:'upprepa den'}),
      antal:choice('Om den upprepas: hur många gånger totalt?',{a2:'två gånger',a3:'tre gånger'})},
    build:(a)=>{ if (a.fran==='saknas') return [{op:'ta_bort_handling',scen:'PLATSHALLARE:scen',segment:'PLATSHALLARE:segment',kommentar:'handlingen finns inte i tillståndet'}];
      const sc=segScen[a.fran];
      return a.atgard==='ta_bort'?[{op:'ta_bort_handling',scen:sc,segment:a.fran}]:a.atgard==='langsammare'?[{op:'tempo_handling',scen:sc,segment:a.fran,faktor:2}]:a.atgard==='snabbare'?[{op:'tempo_handling',scen:sc,segment:a.fran,faktor:.5}]
        :[{op:'upprepa_handling',scen:sc,fran:a.fran,till:(a.till==='saknas'||segScen[a.till]!==sc)?a.fran:a.till,antal:a.antal==='a3'?3:2}]; }},
};

if (process.argv[1] && !process.argv[1].endsWith('prov_0030.mjs')) throw new Error('prov_0030.mjs körs som skript, inte som modul');
const st = state(MED); write(path.join(OUT, 'tillstand.json'), {text:st, rader:st.split('\n').length, tecken:st.length, med_mening:MED});
const res = [];
for (const m of M.meningar) {
  const s2 = st + '\nCM: ' + m.text; const t0 = performance.now(); let ms = 0;
  const f = await api(`m${m.nr}-familj`, s2, {familj:choice(policy+' Vilken ändringsfamilj passar bäst?', FAM)}); ms += f.ms;
  const fam = f.raw.answers.familj.choice; let delar = [], konkret = null, regi = null;
  if (fam !== 'oklar') {
    const d = await api(`m${m.nr}-delar`, s2, {delar:choice(policy+` Vilka delar ändras direkt? Vald familj: ${fam}. Tom mängd om ingen konkret ändring kan väljas.`, Object.fromEntries(sets.map((x,i)=>['p'+i, x.length?x.join(' + '):'inga delar / oklar'])))}); ms += d.ms;
    delar = sets[Number(d.raw.answers.delar.choice.slice(1))] ?? [];
    if (KONKRET[fam] && !(fam==='handling.andra' && !Object.keys(segment).length)) {
      const q = fam==='handling.andra' && !MED ? null : KONKRET[fam].q;
      if (q) {
        const c = await api(`m${m.nr}-konkret`, s2, q); ms += c.ms;
        const a = Object.fromEntries(Object.entries(c.raw.answers).map(([k,v])=>[k,v.choice]));
        if (fam === 'handling.andra') {
          // Segmentet i ett eget anrop (en fråga), utan saknas: familjen har redan sagt att det är en handling. Tidigare versioner i ut/*_segmentfraga/.
          const g = await api(`m${m.nr}-segment`, s2, {fran:choice('Familjen är redan vald som en handling i klippet. I vilket handlingssegment gör personen det som meningen beskriver?',{...segment})}); ms += g.ms;
          a.fran = g.raw.answers.fran.choice; c.raw.answers.fran = g.raw.answers.fran;
          if (a.atgard === 'upprepa') {
            const t = await api(`m${m.nr}-till`, s2, {till:choice(`Följden som upprepas börjar i ${a.fran}. Vilket segment avslutar den? Välj ${a.fran} om bara det segmentet upprepas.`,{...segment})}); ms += t.ms;
            a.till = t.raw.answers.till.choice; c.raw.answers.till = t.raw.answers.till;
          } else a.till = a.fran;
        }
        regi = JSON.parse(JSON.stringify(BAS)); regi.kalla.revision = K.revision; regi.edits = [];
        regi.edits = KONKRET[fam].build(a, m.text).map((e,i)=>({id:`m${m.nr}_${i}`, ursprung:{typ:'cm'}, ...Object.fromEntries(Object.entries(e).filter(([,v])=>v!==undefined))}));
        konkret = {svar:a, marginal:Object.fromEntries(Object.entries(c.raw.answers).map(([k,v])=>[k, v.probabilities?Object.values(v.probabilities).sort((x,y)=>y-x).slice(0,2):null]))};
        write(path.join(OUT, 'regi', `m${m.nr}.json`), regi);
      } else konkret = {saknas:'handlingsspåret finns inte i tillståndet; inga segment att välja'};
    } else konkret = {saknas:`ingen konkret väg för familjen ${fam} i provet`};
  }
  res.push({nr:m.nr, text:m.text, familj:fam, familj_sannolikheter:f.raw.answers.familj.probabilities??null, delar, konkret, edits:regi?.edits??null, jev_ms:Math.round(ms), vagg_ms:Math.round(performance.now()-t0)});
  console.log(m.nr, fam, delar.join('+'), JSON.stringify(konkret?.svar??konkret));
}
const logg = fs.readFileSync(path.join(OUT,'anropslogg.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const tok = logg.reduce((s,x)=>s+(x.input_tokens||0),0);
write(path.join(OUT, 'routning.json'), {modell:MODELL, med_mening:MED, nya_anrop:calls, anrop_totalt:logg.length, input_tokens_totalt:tok, usd_uppskattat:+(tok*0.04/1e6).toFixed(5), resultat:res});
