// Short verification only: two chat sentences (four Jev calls), no compiler.
import fs from 'node:fs';import path from 'node:path';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const O=path.resolve('forvarld/varld');
const browser=await chromium.launchPersistentContext(path.join(O,'browser-profile-resume'),{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true,viewport:{width:1160,height:950},args:['--disable-background-networking','--disable-component-update','--no-first-run','--disable-extensions','--autoplay-policy=no-user-gesture-required']});
const result={errors:[],external:[],chat:[],render:[],subtitles:[]};
if(process.argv.includes('--no-chat'))result.chat=JSON.parse(fs.readFileSync(path.join(O,'resume-check.json'),'utf8')).chat;
try{
 const page=browser.pages()[0];
 page.on('pageerror',e=>result.errors.push(e.stack));page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());});
 await page.route('**/*',r=>{const u=r.request().url();if(u.startsWith('http://127.0.0.1:5195/')||u.startsWith('data:'))return r.continue();result.external.push(u);return r.abort();});
 await page.goto('http://127.0.0.1:5195/');await page.waitForFunction(()=>window.__WORLD__?.ready);
 result.loadMs=await page.evaluate(()=>__WORLD__.loadMs);result.gpu=await page.evaluate(()=>__WORLD__.gpu);
 if(!process.argv.includes('--no-chat'))for(const sentence of ['Byt undertexten i scen 1 till "Vem betalar?".','Byt bakgrunden i scen 1 till glassbar S1.']){
  await page.evaluate(()=>__WORLD__.reset());const row=await page.evaluate(s=>__WORLD__.chat(s),sentence);
  result.chat.push({sentence,totalMs:row.totalMs,applied:!!row.applied,ops:row.response.edits?.map(e=>e.op),message:row.response.message});
  await page.evaluate(()=>__WORLD__.undo());
  if(await page.evaluate(()=>__WORLD__.regi().edits.length))throw Error('Undo left edits behind');
 }
 await page.evaluate(()=>__WORLD__.reset());
 // Real moving playback: gl.finish per rAF includes submission and video upload,
 // but the browser video decoder is asynchronous and is not separately timed.
 for(const live of [false,true]){
  const row=await page.evaluate(async live=>{
   await __WORLD__.seek(240,{plate:false,layers:true,live,hands:true,cameraChanged:true});
   document.getElementById('play').click();const times=[],states=[];let start=performance.now();
   for(let i=0;i<75;i++){await new Promise(requestAnimationFrame);const t=performance.now();__WORLD__.draw();__WORLD__.renderer.getContext().finish();times.push(performance.now()-t);states.push(__WORLD__.liveState());}
   const wall=performance.now()-start;__WORLD__.pause();times.sort((a,b)=>a-b);
   return {live,count:times.length,renderFinishMedianMs:times[37],renderFinishP95Ms:times[71],fps:75000/wall,liveFrames:states.filter(s=>s.enabled).length,distinctSourceFrames:new Set(states.map(s=>s.sourceFrame)).size};
  },live);result.render.push(row);
 }
 for(const f of [36,93,142,213,268,309,360]){
  await page.evaluate(async f=>{await __WORLD__.seek(f,{plate:false,layers:true,live:true,cameraChanged:true});__WORLD__.textLayer(false);},f);
  const st=await page.evaluate(()=>__WORLD__.liveState());if(!st.enabled)throw Error('Live disabled at '+f);
  fs.writeFileSync(path.join(O,`bilder/no-source-text-${f}.png`),Buffer.from((await page.evaluate(()=>__WORLD__.png())).split(',')[1],'base64'));
  result.subtitles.push(st);await page.evaluate(()=>__WORLD__.textLayer(true));
 }
 // One changed line checks lower-face fallback and mixed audio mute without TTS.
 await page.evaluate(async()=>{__WORLD__.reset();const r=__WORLD__.manifest.lines.find(r=>r.talare==='B');await __WORLD__.applyEdits([{id:'resume_line',op:'byt_replik',ursprung:{typ:'cm'},replik:r.id,text:'Ny replik',sprak:'sv',rost:{motor:null,rost_id:null,stil:null},tidspolicy:'samma_lucka',max_talfaktor:null}]);await __WORLD__.seek(Math.round((r.start_s+r.slut_s)*15),{plate:false,layers:true,live:true});});
 result.changedLine={muted:await page.evaluate(()=>document.getElementById('audio').muted),state:await page.evaluate(()=>__WORLD__.liveState())};
 fs.writeFileSync(path.join(O,'bilder/changed-line.png'),Buffer.from((await page.evaluate(()=>__WORLD__.png())).split(',')[1],'base64'));
 await page.evaluate(()=>__WORLD__.reset());result.calls=await(await fetch('http://127.0.0.1:5195/api/status')).json();
 fs.writeFileSync(path.join(O,'resume-check.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,subtitles:result.subtitles.map(s=>({frame:s.frame,enabled:s.enabled})),changedLine:{muted:result.changedLine.muted}},null,2));
 if(result.errors.length)throw Error('Browser errors');
}finally{await browser.close();}
