// Free-tier credential stays only in memory. No coordinates requested or accepted.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(here,'../../../..');
const spec=JSON.parse(fs.readFileSync(path.resolve(here,'../../scen3d.json'),'utf8'));
const line=fs.readFileSync(path.join(repo,'video/.env.local'),'utf8').split(/\r?\n/).find(x=>x.startsWith('GEMINI_API_KEY_GRATIS='));
if(!line)throw Error('Free-tier credential unavailable');
const key=line.slice(line.indexOf('=')+1).trim().replace(/^['"]|['"]$/g,'');
const model='gemini-3.5-flash-lite';
if(process.argv.includes('--sheets')) {
  const events=[];const prompts=[];const started=Date.now();
  for(const shot of spec.shots){
    const prompt=`Inspect these eight timestamped SOURCE frames of ${shot.id}, main actor ${shot.actors[0].id}. Return JSON {events:[{shot,actor,type,side,object,startSec,endSec,description,confidence,uncertain}]}. Source seconds are printed above each frame. Exact shot bounds ${shot.source.inSec} to ${shot.source.outSec}. Types: seated, standing, hold, touch_table, hand_on_hip, gaze, gesture. Only semantics and timing, NO coordinates. Use anatomical Left/Right; front-facing image-right = actor Left. Distinguish hands vs elbows touching table: do not call hands hovering above it touch_table. Objects: B:burger, B:fry, C:terminal. Record holding over whole shot if continuous. For seated/standing lower body is inferred if hidden: say so. Gaze target semantic only. Include uncertainty and do not infer precise sub-frame transitions from eight stills.`;
    const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':key},body:JSON.stringify({contents:[{role:'user',parts:[{inline_data:{mime_type:'image/jpeg',data:fs.readFileSync(path.join(here,`gt/sheets/${shot.id}.jpg`)).toString('base64')}},{text:prompt}]}],generationConfig:{responseMimeType:'application/json',temperature:.1,maxOutputTokens:4500}}),signal:AbortSignal.timeout(120000)});
    if(!response.ok)throw Error(`Gemini free-tier HTTP ${response.status}`);
    const body=await response.json(); const result=JSON.parse(body.candidates[0].content.parts.map(x=>x.text||'').join(''));
    events.push(...result.events);prompts.push(prompt);console.log(shot.id,result.events.length,'events');
  }
  fs.writeFileSync(path.join(here,'gt/events-sheets.json'),JSON.stringify({model,runtime_s:(Date.now()-started)/1000,prompts,events},null,2));
  process.exit(0);
}
const prompt=`Observe this source video frame-by-frame. Return JSON {events:[{shot,actor,type,side,object,startSec,endSec,description,confidence,uncertain}]} with source-absolute seconds, not shot-relative. Only semantics and time windows; NEVER coordinates, boxes or pose estimates. Types: seated, standing, hold, touch_table, hand_on_hip, gaze, gesture. Anatomical Left/Right of the actor, not image left/right; use unknown if ambiguous. Identify props using IDs where possible: B:burger, B:fry, C:terminal, A:burger, A:cup. The main actor is A (woman) in S1/S3/S6, B (seated man) in S2/S5/S7, C (standing server) in S4. Include whole-shot sitting/standing, visible object holding/contact transitions, and gaze direction. Distinguish observed contacts from occluded inferred ones. Times must stay inside these exact shot ranges: ${JSON.stringify(spec.shots.map(s=>({shot:s.id,startSec:s.source.inSec,endSec:s.source.outSec})))}. No prose outside JSON.`;
const started=Date.now();
const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':key},body:JSON.stringify({contents:[{role:'user',parts:[{inline_data:{mime_type:'video/mp4',data:fs.readFileSync(path.join(repo,'scen/klipp/d-dialog-notan.mp4')).toString('base64')}},{text:prompt}]}],generationConfig:{responseMimeType:'application/json',temperature:.1,maxOutputTokens:10000}}),signal:AbortSignal.timeout(180000)});
if(!response.ok)throw Error(`Gemini free-tier HTTP ${response.status}`);
const body=await response.json();
const result=JSON.parse(body.candidates[0].content.parts.map(x=>x.text||'').join(''));
fs.mkdirSync(path.join(here,'gt'),{recursive:true});
fs.writeFileSync(path.join(here,'gt/events-gemini.json'),JSON.stringify({model,runtime_s:(Date.now()-started)/1000,prompt,...result},null,2));
console.log(`Saved ${result.events.length} semantic events.`);
