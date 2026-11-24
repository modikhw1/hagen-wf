// Håller kompilatorprocessen vid liv, kompilerar varje godkänd regi i bakgrunden (snabbvägen) och
// kör sanningskontrollen mot webbens reducerare. Blockerar aldrig det som visas.
import {spawn} from 'node:child_process';
import readline from 'node:readline';
import fs from 'node:fs';
import path from 'node:path';
import {sanning} from './sanning.mjs';

export function skapaKompilator({OUT,ROOT,M,baseRegi}){
 const py=path.join(ROOT,'scen/.venv/Scripts/python.exe'),script=path.join(OUT,'kompilator_demon.py');
 const loggFil=path.join(OUT,'logg/kompilering.jsonl');
 const log=o=>{try{fs.appendFileSync(loggFil,JSON.stringify({t:new Date().toISOString(),...o})+'\n');}catch{}};
 const proc=(namn)=>{
  const p=spawn(py,['-B',script],{cwd:ROOT,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1'}});
  const w=[];let readyMs=null;let dead=false;const stderr=[];
  const ready=new Promise(res=>w.push(m=>{readyMs=m.importMs;res(m);}));
  readline.createInterface({input:p.stdout}).on('line',l=>{let m;try{m=JSON.parse(l);}catch{return;}const f=w.shift();if(f)f(m);});
  p.stderr.on('data',d=>{stderr.push(String(d));if(stderr.length>20)stderr.shift();});
  p.on('exit',code=>{dead=true;for(const f of w.splice(0))f({ok:false,fel:`${namn}: processen avslutades (${code}) ${stderr.join('').slice(-400)}`});});
  const send=obj=>new Promise(res=>{w.push(res);p.stdin.write(JSON.stringify(obj)+'\n');});
  return {p,send,ready,get dead(){return dead;},get importMs(){return readyMs;}};
 };
 let main=null,seq=0,running=false,pending=null,grund=null;
 const waiters=[];
 const state={seq:0,klar:0,kompilerar:false,senaste:null,start:null,grundKlar:false,kvalitet:{kor:false,senaste:null}};
 const ensure=async()=>{if(!main||main.dead){main=proc('kompilator');await main.ready;}return main;};
 async function compileRaw(edits){
  const m=await ensure();
  const t=performance.now();
  const r=await m.send({id:'c'+(++seq),cmd:'kompilera',regi:{...baseRegi,skapad:null,edits}});
  return {r,ms:performance.now()-t};
 }
 async function ensureGrund(){
  if(grund)return grund;const {r,ms}=await compileRaw([]);
  if(!r.ok)throw Error('Grundkompilering misslyckades: '+r.fel);
  grund=r.sammanfattning;state.grundKlar=true;log({typ:'grund',kompileraMs:r.kompileraMs,ms,importMs:main.importMs});
  // Förvärm skymningens rutdata för alla källrutor (en gång; beständig cache). Kompileringar som kommer under tiden köas i kompilatorprocessen.
  main.send({id:'fv',cmd:'forvarm'}).then(f=>log({typ:'forvarm',...f})).catch(()=>{});
  return grund;
 }
 async function loop(){
  if(running)return;running=true;
  try{
   await ensureGrund();
   while(pending){
    const job=pending;pending=null;state.kompilerar=true;
    let post;
    try{
     const {r,ms}=await compileRaw(job.edits);
     const slut=performance.now();
     if(!r.ok){post={seq:job.seq,kompilerad:false,fel:r.fel,antalEdits:job.edits.length,ms:slut-job.start};log({typ:'fel',seq:job.seq,fel:r.fel,edits:job.edits.map(e=>e.op)});}
     else{
      const t=performance.now(),s=sanning(job.edits,M,r.sammanfattning,grund),sanningMs=performance.now()-t;
      post={seq:job.seq,kompilerad:true,antalEdits:job.edits.length,etikett:job.etikett,
       ms:slut-job.start,koIMs:job.begar-job.start,kompileraMs:r.kompileraMs,rundturMs:ms,sanningMs,
       avvikelserN:s.avvikelserN,jamforda:s.jamforda,antal:s.antal,avvikelser:s.avvikelser,rader:s.rader,
       diagnostik:r.sammanfattning.diagnostik,varningar:r.sammanfattning.varningar};
      log({typ:'kompilerad',seq:job.seq,etikett:job.etikett,ops:job.edits.map(e=>e.op),ms:post.ms,kompileraMs:r.kompileraMs,rundturMs:ms,sanningMs,avvikelserN:s.avvikelserN,jamforda:s.jamforda,antal:s.antal,avvikelser:s.avvikelser});
     }
    }catch(e){post={seq:job.seq,kompilerad:false,fel:String(e.message||e),antalEdits:job.edits.length,ms:performance.now()-job.start};log({typ:'undantag',seq:job.seq,fel:post.fel});}
    state.senaste=post;state.klar=job.seq;state.kompilerar=false;
    for(const w of waiters.splice(0))w(post);
   }
  }finally{running=false;state.kompilerar=false;if(pending)loop();}
 }
 return {
  // Anropas efter varje godkänd ändring (och efter ångra/återställ) med hela edit-listan. Svarar direkt.
  submit(edits,etikett){const s=++state.seq;const start=performance.now();pending={seq:s,edits:structuredClone(edits),etikett,start,begar:start};state.start=start;loop();return s;},
  waitFor(s){return state.klar>=s&&state.senaste?Promise.resolve(state.senaste):new Promise(res=>{const f=p=>p.seq>=s?res(p):waiters.push(f);waiters.push(f);});},
  status(){return {seq:state.seq,klar:state.klar,kompilerar:state.kompilerar||running,grundKlar:state.grundKlar,senaste:state.senaste&&{...state.senaste,rader:undefined},kvalitet:state.kvalitet};},
  rader(){return state.senaste?.rader||[];},
  async uppvarmning(){try{await ensureGrund();}catch(e){log({typ:'uppvarmning_fel',fel:e.message});}},
  // Kvalitetskontroll: egen process, så att redigering inte väntar. Kör diagnostik.py:s funktion på senaste kompilerade plan.
  async kvalitetskontroll(){
   if(state.kvalitet.kor)return {redan:true};
   state.kvalitet={kor:true,startad:Date.now(),senaste:state.kvalitet.senaste};
   const start=performance.now(),forSeq=state.klar;
   (async()=>{
    let res;
    try{
     await ensure();
     const fil=`plan-q${forSeq}-${Date.now()}.json`;
     const sp=await main.send({id:'sp',cmd:'spara_plan',fil});
     if(!sp.ok)throw Error(sp.fel);
     const d=proc('kvalitet');await d.ready;
     const r=await d.send({id:'q',cmd:'diagnostik',plan:fil});
     await d.send({cmd:'stang'}).catch(()=>{});setTimeout(()=>d.p.kill(),500);
     if(!r.ok)throw Error(r.fel);
     res={ok:true,forSeq,ms:performance.now()-start,diagnostikMs:r.diagnostikMs,importMs:d.importMs,bildtrohetFlaggad:r.bildtrohetFlaggad,status:r.bildtrohetStatus,varningar:r.varningar,fil:r.fil,kvalitet:r.kvalitet};
    }catch(e){res={ok:false,forSeq,ms:performance.now()-start,fel:String(e.message||e)};}
    log({typ:'kvalitetskontroll',...res});
    state.kvalitet={kor:false,senaste:res};
   })();
   return {startad:true,forSeq};
  },
  stang(){try{main?.p.kill();}catch{}},
 };
}
