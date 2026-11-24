import fs from 'node:fs';
import path from 'node:path';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const OUT=path.resolve('forvarld/varld');
const browser=await chromium.launchPersistentContext(path.join(OUT,'browser-profile-v5'),{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true,viewport:{width:1160,height:950},args:['--disable-background-networking','--disable-component-update','--no-first-run','--disable-extensions','--disable-gpu-sandbox','--autoplay-policy=no-user-gesture-required']});
const page=browser.pages()[0],errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:5195/')||r.request().url().startsWith('data:')?r.continue():r.abort());
const sentences=['Stabilisera kameran i scen 1.','Kom närmare B i scen 7.','Ge A blå helkroppston.','Byt undertexten i scen 1 till "Vem betalar?".','Ta bort undertexten i scen 2.','Flytta scen 7 först.','Duplicera scen 3 med ljud.','Korta scen 5 med 0,2 sekunder.','Dölj hela bord- och matkortet i scen 5.','Byt bakgrunden i scen 1 till glassbar S1.'];
try{await page.goto('http://127.0.0.1:5195/');await page.waitForFunction(()=>window.__WORLD__?.ready,null,{timeout:30000});const rows=[];
for(const [i,sentence] of sentences.entries()){
 await page.evaluate(()=>{__WORLD__.reset();document.getElementById('messages').replaceChildren();});
 const r=await page.evaluate(s=>__WORLD__.chat(s),sentence);rows.push(r);console.log(i+1,JSON.stringify({sentence,ms:r.totalMs,op:r.response.edits?.map(e=>e.op),message:r.response.message,confidence:r.response.confidence}));
 if([1,3,9].includes(i)){await page.screenshot({path:path.join(OUT,`bilder/chat-${i}.png`)});fs.writeFileSync(path.join(OUT,`bilder/chat-world-${i}.png`),Buffer.from((await page.evaluate(()=>__WORLD__.png())).split(',')[1],'base64'));}
 fs.writeFileSync(path.join(OUT,'chat-measurements.json'),JSON.stringify({rows,errors},null,2));
}
const applied=rows.filter(r=>r.applied).map(r=>r.totalMs).sort((a,b)=>a-b);console.log('RESULT',JSON.stringify({applied:applied.length,median:applied[Math.ceil(applied.length/2)-1],worst:applied.at(-1),calls:await (await fetch('http://127.0.0.1:5195/api/status')).json(),errors}));await page.evaluate(()=>__WORLD__.reset());
}finally{await browser.close();}
