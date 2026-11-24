import fs from 'node:fs';import path from 'node:path';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const OUT=path.resolve('forvarld/varld'),IM=path.join(OUT,'bilder');
const browser=await chromium.launchPersistentContext(path.join(OUT,'browser-profile-v5'),{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true,viewport:{width:1160,height:950},args:['--disable-background-networking','--disable-component-update','--no-first-run','--disable-extensions','--disable-gpu-sandbox','--autoplay-policy=no-user-gesture-required']});
const page=browser.pages()[0],errors=[],externals=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});await page.route('**/*',r=>{if(r.request().url().startsWith('http://127.0.0.1:5195/')||r.request().url().startsWith('data:'))return r.continue();externals.push(r.request().url());return r.abort();});
async function shot(file,f,options={}){await page.evaluate(async({f,options})=>{await __WORLD__.seek(f,options);__WORLD__.draw();__WORLD__.renderer.getContext().finish();},{f,options});fs.writeFileSync(path.join(IM,file),Buffer.from((await page.evaluate(()=>__WORLD__.png())).split(',')[1],'base64'));}
try{
 await page.goto('http://127.0.0.1:5195/');await page.waitForFunction(()=>window.__WORLD__?.ready,null,{timeout:30000});await page.evaluate(()=>__WORLD__.reset());
 const M=await page.evaluate(()=>__WORLD__.manifest);
 for(const s of M.scenes){const f=Math.floor((s.source[0]+s.source[1])/2);await shot(s.id+'-ps2.png',f,{plate:true});await shot(s.id+'-layered.png',f,{plate:false,layers:true});await shot(s.id+'-changed.png',f,{plate:false,layers:true,cameraChanged:true});}
 for(const [name,f] of [['s1',36],['s2',93],['s3',142],['s5',268],['s6',309]]){for(const [mode,live,hands] of [['fused',false,false],['projected',true,false],['live',true,true]]){await shot(name+'-'+mode+'.png',f,{plate:false,layers:true,live,hands});await shot(name+'-'+mode+'-changed.png',f,{plate:false,layers:true,live,hands,cameraChanged:true});}}
 for(const sid of ['s1','s7'])for(const bid of ['a_s1','b_s3']){
  await page.evaluate(()=>__WORLD__.reset());await page.evaluate(async({sid,bid})=>{const b=__WORLD__.manifest.backdrops.find(b=>b.id===bid);await __WORLD__.applyEdits([{id:crypto.randomUUID(),op:'byt_miljo',ursprung:{typ:'cm'},scen:sid,rum:{kalla:'bank',tillgang_id:bid,ord:[],beskrivning:b.label}}]);},{sid,bid});
  const s=M.scenes.find(s=>s.id===sid);await shot(`venue-${sid}-${bid}.png`,Math.floor((s.source[0]+s.source[1])/2),{plate:false,layers:true,cameraChanged:true});
 }
 await page.evaluate(()=>__WORLD__.reset());
 const performanceRows=[];
 for(const live of [false,true]){await page.evaluate(live=>__WORLD__.seek(268,{plate:false,layers:true,live,hands:true,cameraChanged:true}),live);performanceRows.push(await page.evaluate(async live=>{const values=[];for(let i=0;i<120;i++){await new Promise(requestAnimationFrame);const t=performance.now();__WORLD__.draw();__WORLD__.renderer.getContext().finish();values.push(performance.now()-t);}values.sort((a,b)=>a-b);return{live,renderFinishMedianMs:values[59],renderFinishP95Ms:values[113]};},live));}
 await page.evaluate(()=>__WORLD__.seek(0,{plate:false,layers:true,live:true}));await page.click('#play');await page.waitForTimeout(3500);await page.click('#play');
 const playback=await page.evaluate(()=>{const a=__WORLD__.rafTimes.slice(-120).sort((a,b)=>a-b);return{medianMs:a[59],p95Ms:a[113],fps:120000/a.reduce((a,b)=>a+b,0)};});
 fs.writeFileSync(path.join(OUT,'v5-measurements.json'),JSON.stringify({performanceRows,playback,loadMs:await page.evaluate(()=>__WORLD__.loadMs),gpu:await page.evaluate(()=>__WORLD__.gpu),errors,externals},null,2));console.log(JSON.stringify({performanceRows,playback,errors,externals},null,2));await page.evaluate(()=>__WORLD__.reset());
}finally{await browser.close();}
