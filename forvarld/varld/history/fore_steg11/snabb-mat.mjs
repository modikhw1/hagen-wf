// Mätning och sanningskontroll för snabbvägen. Från projektroten:
//   node forvarld/varld/snabb-mat.mjs tid       kall / varm ny process / varm långlivad -> snabb-tider.json
//   node forvarld/varld/snabb-mat.mjs sanning   webbens reducerare mot kompilerad plan -> logg/sanning-*.json
// Ingen Blender, ingen Modal, inget Jev-anrop.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {skapaKompilator} from './kompilator.mjs';

const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../..');
const M=JSON.parse(fs.readFileSync(path.join(OUT,'paket/notan/manifest.json'),'utf8'));
const baseRegi=JSON.parse(fs.readFileSync(path.join(OUT,'pipeline/base-regi.json'),'utf8'));
const py=path.join(ROOT,'scen/.venv/Scripts/python.exe'),script=path.join(OUT,'kompilator_demon.py');
const c=x=>({ursprung:{typ:'cm'},...x});
const med=a=>{const s=[...a].sort((x,y)=>x-y);return s.length?s[Math.floor((s.length-1)/2)]:null;};

export const FALL={
 trim:[c({id:'t1',op:'trimma_scen',scen:'s3',slut_s:5.5,lage:'klipp_slut'})],
 text:[c({id:'x1',op:'skarmtext',scen:'s1',skarmtext_id:'st1',atgard:'byt',text:'Vem betalar?'})],
 prop:[c({id:'p1',op:'ta_bort_prop',scen:'s1',prop:'bord_A'})],
 ta_bort_scen:[c({id:'d1',op:'ta_bort_scen',scen:'s2'})],
 replik:[c({id:'r9',op:'byt_replik',replik:'r1',text:'Hej igen.',sprak:'sv',rost:{motor:null,rost_id:null,stil:null},tidspolicy:'samma_lucka',max_talfaktor:null})],
};

// En kompilering i en ny Pythonprocess: väggtid från start av processen till svar (inkluderar import).
async function nyProcess(edits,env){
 const t0=performance.now();
 const p=spawn(py,['-B',script],{cwd:ROOT,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1',...env}});
 const lines=readline.createInterface({input:p.stdout})[Symbol.asyncIterator]();
 const ready=JSON.parse((await lines.next()).value);const tReady=performance.now()-t0;
 p.stdin.write(JSON.stringify({id:'x',cmd:'kompilera',regi:{...baseRegi,edits}})+'\n');
 const r=JSON.parse((await lines.next()).value);const tot=performance.now()-t0;
 p.stdin.write('{"cmd":"stang"}\n');p.kill();
 if(!r.ok)throw Error(r.fel);
 return {vaggMs:tot,importMs:ready.importMs,tillReadyMs:tReady,kompileraMs:r.kompileraMs};
}

async function tid(){
 const res={datum:new Date().toISOString(),maskin:`${os.cpus()[0].model}, ${os.cpus().length} trådar, ${Math.round(os.totalmem()/2**30)} GiB`,kall:{},varmNyProcess:{},langlivad:{}};
 for(const [namn,edits] of Object.entries(FALL)){
  const cache=fs.mkdtempSync(path.join(os.tmpdir(),'notan-cache-'));
  res.kall[namn]=await nyProcess(edits,{NOTAN_CACHE:cache});     // tom cache (och tom talcache)          // tom cache
  res.varmNyProcess[namn]=[];for(let i=0;i<3;i++)res.varmNyProcess[namn].push(await nyProcess(edits,{NOTAN_CACHE:cache}));
  fs.rmSync(cache,{recursive:true,force:true});fs.rmSync(cache+'_tal',{recursive:true,force:true});
 }
 // Långlivad: en process, grundkompilering först, sedan varje fall fem gånger i följd, mätt som webbvägen (submit -> klart).
 const k=skapaKompilator({OUT,ROOT,M,baseRegi});await k.uppvarmning();
 for(const [namn,edits] of Object.entries(FALL)){
  const rundtur=[],komp=[],post=[];
  for(let i=0;i<6;i++){const s=k.submit(edits,'mat');const p=await k.waitFor(s);if(i===0)continue;rundtur.push(p.ms);komp.push(p.kompileraMs);post.push(p.sanningMs);}
  res.langlivad[namn]={medianTotalMs:med(rundtur),minTotalMs:Math.min(...rundtur),maxTotalMs:Math.max(...rundtur),medianKompileraMs:med(komp),medianSanningMs:med(post),prov:rundtur.length};
 }
 k.stang();
 for(const g of ['kall','varmNyProcess'])for(const [n,v] of Object.entries(res[g]))if(Array.isArray(v))res[g][n]={medianVaggMs:med(v.map(x=>x.vaggMs)),prov:v.map(x=>Math.round(x.vaggMs)),importMs:Math.round(v[0].importMs)};
 fs.writeFileSync(path.join(OUT,'snabb-tider.json'),JSON.stringify(res,null,2));
 console.log(JSON.stringify(res,null,1));
}

const FALL_SANNING=[
 ['trim',[c({id:'a1',op:'trimma_scen',scen:'s3',slut_s:5.5,lage:'klipp_slut'})]],
 ['text (byt)',[c({id:'a2',op:'skarmtext',scen:'s1',skarmtext_id:'st1',atgard:'byt',text:'Vem betalar?'})]],
 ['text (ta bort)',[c({id:'a3',op:'skarmtext',scen:'s2',skarmtext_id:'st2',atgard:'ta_bort'})]],
 ['text (lägg till, annan stil)',[c({id:'a4',op:'skarmtext',scen:'s2',skarmtext_id:'ny_1',atgard:'lagg_till',text:'Ny text',box:[25,90,526,100]})]],
 ['prop (dölj kort)',[c({id:'a5',op:'ta_bort_prop',scen:'s1',prop:'bord_A'})]],
 ['prop (byt kort)',[c({id:'a6',op:'byt_prop',scen:'s1',prop:'bord_A',ny_typ:'foreground',tillgang_id:'s3:foreground'})]],
 ['lokalbyte',[c({id:'a7',op:'byt_miljo',scen:'s1',rum:{kalla:'bank',tillgang_id:'b_s2',ord:[],beskrivning:'x'}})]],
 ['kamera (stativ, närmare B)',[c({id:'a8',op:'renderkamera',scen:'s7',kamera_id:'k1',lage:'stativ',inramning:'nara',mal:{typ:'person',id:'B',punkt:'huvud'}})]],
 ['kamera (stativ, vidare)',[c({id:'a9',op:'renderkamera',scen:'s1',kamera_id:'k2',lage:'stativ',inramning:'hel',mal:null})]],
 ['helkroppston + rollnamn',[c({id:'b1',op:'casta',person:'A',kundroll:{id:'A',namn:'CM'},utseende:{troja_farg:'#80a8ff'}})]],
 ['ta bort scen',[c({id:'b2',op:'ta_bort_scen',scen:'s2'})]],
 ['flytta scen',[c({id:'b3',op:'flytta_scen',scen:'s7',efter:null})]],
 ['duplicera scen',[c({id:'b4',op:'duplicera_scen',scen:'s1',ny_id:'s1_copy',efter:'s1',med_ljud:false})]],
 ['byt replik',[c({id:'b5',op:'byt_replik',replik:'r1',text:'Hej igen.',sprak:'sv',rost:{motor:null,rost_id:null,stil:null},tidspolicy:'samma_lucka',max_talfaktor:null})]],
 ['trim + text + ta bort scen (sammansatt)',[c({id:'c1',op:'trimma_scen',scen:'s3',slut_s:5.5,lage:'klipp_slut'}),c({id:'c2',op:'skarmtext',scen:'s1',skarmtext_id:'st1',atgard:'byt',text:'Vem?'}),c({id:'c3',op:'ta_bort_scen',scen:'s5'})]],
];

async function sanningKor(){
 const k=skapaKompilator({OUT,ROOT,M,baseRegi});await k.uppvarmning();
 const rader=[];
 for(const [namn,edits] of FALL_SANNING){
  const s=k.submit(edits,namn);const p=await k.waitFor(s);
  rader.push({namn,ops:edits.map(e=>e.op),kompilerad:p.kompilerad,fel:p.fel,ms:p.ms,avvikelserN:p.avvikelserN,jamforda:p.jamforda,antal:p.antal,avvikelser:p.avvikelser,rader:k.rader()});
  console.log(namn.padEnd(40),p.kompilerad?`${Math.round(p.ms)} ms  jämförda ${p.jamforda}  avvikelser ${p.avvikelserN}`:'KOMPILERAS INTE: '+String(p.fel).split('\n')[0].slice(0,120));
 }
 // Ångra: trim -> trim + text -> (ångra text = trim). Planen efter ångra ska vara lika med planen före texten.
 const a=[FALL_SANNING[0][1][0]],b=[...a,FALL_SANNING[1][1][0]];
 const grab=async e=>{const s=k.submit(e,'angra');const p=await k.waitFor(s);return {p,rader:k.rader()};};
 const r1=await grab(a),r2=await grab(b),r3=await grab(a),rg=await grab([]);
 const ensam=x=>JSON.stringify(x.rader.map(r=>[r.falt,r.status,r.webblasare,r.kompilerad]));
 const angra={efterTrim:r1.p.avvikelserN,efterText:r2.p.avvikelserN,efterAngra:r3.p.avvikelserN,raderLika_trim_vs_angra:ensam(r1)===ensam(r3),msAngra:r3.p.ms,
  anm:'Ångra i webben = reducerare på kortare edit-lista; i kompilatorn = ny kompilering av kortare regi. Likhet mäts på sanningsraderna (inkl. källrutor, texter, tidskarta).'};
 console.log('ångra',JSON.stringify(angra));
 k.stang();
 const fil=path.join(OUT,'logg',`sanning-${new Date().toISOString().replace(/[:.]/g,'-')}.json`);
 fs.writeFileSync(fil,JSON.stringify({datum:new Date().toISOString(),rader,angra},null,1));
 console.log('skrev',path.relative(ROOT,fil));
}

if(process.argv[2]==='tid')await tid();
else if(process.argv[2]==='sanning')await sanningKor();
else console.log('node forvarld/varld/snabb-mat.mjs tid|sanning');
