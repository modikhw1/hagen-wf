// Regression mot kompilatorn, inklusive mål, riktning och meterskala.
// node --test forvarld/varld/stativ-test.mjs (ingen server eller Blender).
import assert from 'node:assert/strict';
import {test} from 'node:test';
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {initial,apply,timeline} from './edits.mjs';
import {stativNyckel,stativIPaket,stativMatt} from './stativ.mjs';
import {skapaKompilator} from './kompilator.mjs';

const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../..');
const read=f=>JSON.parse(fs.readFileSync(path.join(OUT,f),'utf8'));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
const vector=(a,b)=>a.forEach((x,i)=>close(x,b[i]));
const position=k=>k.matris.slice(0,3).map(r=>r[3]);

test('samtidig uppvärmning och hämtning delar samma stativunderlag',async()=>{
 const M=read('paket/notan/manifest.json'),k=skapaKompilator({OUT,ROOT,M,baseRegi:read('pipeline/base-regi.json')});
 try{
  const [,a,b]=await Promise.all([k.uppvarmning(),k.stativunderlag(),k.stativunderlag()]);
  assert.equal(a,b);assert.equal(a,M.stativunderlag);
  assert.equal(a.kameror.length,M.frames);
  assert.ok(a.scener.s7.mal.B.huvud.length>0);
 }finally{k.stang();}
});

test('webbens stativgeometri följer dagens kompilator',async()=>{
 const proc=spawn(path.join(ROOT,'scen/.venv/Scripts/python.exe'),['-B',path.join(OUT,'kompilator_demon.py')],
  {cwd:ROOT,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
 const lines=readline.createInterface({input:proc.stdout})[Symbol.asyncIterator]();
 proc.stderr.on('data',d=>process.stderr.write(d));
 try{
  assert.equal(JSON.parse((await lines.next()).value).ready,true);
  const compile=async edits=>{proc.stdin.write(JSON.stringify({cmd:'kompilera',regi:{...read('pipeline/base-regi.json'),edits}})+'\n');
   const r=JSON.parse((await lines.next()).value);assert.equal(r.ok,true,r.fel);return r.sammanfattning;};
  const M=read('paket/notan/manifest.json'),base=await compile([]);M.stativunderlag=base.stativunderlag;
  const cam=(scen,inramning,mal=null,extra={})=>({id:'kam',op:'renderkamera',ursprung:{typ:'cm'},scen,kamera_id:'k',lage:'stativ',inramning,mal,...extra});
  const trim={id:'trim',op:'trimma_scen',ursprung:{typ:'cm'},scen:'s7',slut_s:12.5,lage:'klipp_slut'};
  const hide={id:'hide',op:'ta_bort_prop',ursprung:{typ:'cm'},scen:'s1',prop:'bord_A'};
  const head={typ:'person',id:'B',punkt:'huvud'};
  const cases=[
   [cam('s7','nara',head)], [cam('s1','hel')],
   [cam('s7','halv',head,{fov_grader:55})],
   [cam('s7','hel',{typ:'person',id:'B',punkt:'kropp'})],
   [cam('s7',null,head)], [cam('s1',null)],
   [trim,cam('s7','nara',head)], [cam('s7','nara',head),trim],
   [hide,cam('s1','hel')], [cam('s1','hel'),hide],
   [cam('s7','nara',head),{id:'dup',op:'duplicera_scen',ursprung:{typ:'cm'},scen:'s7',ny_id:'kopia',efter:null,med_ljud:false}],
   [cam('s7','nara',head),cam('s7',null,null,{id:'uppmatt',lage:'folj_uppmatt'})],
  ];
  for(const edits of cases){
   let state=initial(M);for(const e of edits)state=apply(state,e,M);
   const plan=await compile(edits);assert.deepEqual(plan.ej_tillampat,[]);
   if(edits.at(-1).lage==='folj_uppmatt'){
    assert.equal(state.scenes.find(s=>s.id==='s7').camera,null);
    assert.deepEqual(plan.renderkamera,base.renderkamera);
   }
   for(const s of timeline(state).filter(s=>s.camera)){
    const key=stativNyckel(M,s),sc=plan.scener.find(x=>x.id===s.id);
    for(let f=sc.ut[0];f<sc.ut[1];f++){
     const expected=plan.renderkamera.nycklar[f];
     key.matris.forEach((r,i)=>vector(r,expected.matris[i]));
     vector(key.mal_m,expected.mal_m);close(key.lins_mm,expected.lins_mm);
    }
    const pkg=stativIPaket(M,s),a=(s.cameraSource||[s.a,s.b])[0];
    // Transformen till paketet bevarar både kameraavståndet och målvektorn.
    const dist=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i]));
    close(dist(position(pkg),position(M.cameras.nycklar[a])),dist(position(key),position(base.renderkamera.nycklar[a])));
    close(dist(position(pkg),pkg.mal_m),dist(position(key),key.mal_m));
    if(edits===cases[0]||edits===cases[1])console.log(s.id,edits[0].inramning,'flytt m',stativMatt(M,s).forskjutning_m.toFixed(6),
     'målavstånd m',dist(position(key),key.mal_m).toFixed(6),'uppmätt–mål m',dist(position(base.renderkamera.nycklar[a]),key.mal_m).toFixed(6),
     'sedda props',M.stativunderlag.scener[s.origin].props);
   }
  }
  console.log('Verifierade',cases.length,'regier mot kompilatorns alla kameranycklar.');
 }finally{proc.kill();}
});
