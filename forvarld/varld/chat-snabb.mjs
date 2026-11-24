// Hela vägen med riktiga Jev-anrop: mening -> Jev-val -> visad ändring -> kompilerad plan. Högst 12 Jev-anrop.
// Kräver att server.mjs körs. Från projektroten: node forvarld/varld/chat-snabb.mjs
import fs from 'node:fs';import path from 'node:path';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const OUT=path.resolve('forvarld/varld'),MAX=12;
const sentences=process.argv.slice(2).length?process.argv.slice(2):['Korta scen 5 med 0,2 sekunder.','Byt undertexten i scen 1 till "Vem betalar?".','Dölj hela bord- och matkortet i scen 5.','Byt bakgrunden i scen 1 till glassbar S1.','Kom närmare B i scen 7.','Ta bort scen 2.'];
const calls=async()=>(await (await fetch('http://127.0.0.1:5195/api/status')).json()).callsUsed;
const start=await calls();
const browser=await chromium.launchPersistentContext(path.join(OUT,'browser-profile-v5'),{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true,viewport:{width:1160,height:950},args:['--disable-background-networking','--disable-component-update','--no-first-run','--disable-extensions','--disable-gpu-sandbox','--autoplay-policy=no-user-gesture-required']});
const rows=[],errors=[];
try{
 const page=browser.pages()[0];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:5195/')||r.request().url().startsWith('data:')?r.continue():r.abort());
 await page.goto('http://127.0.0.1:5195/');await page.waitForFunction(()=>window.__WORLD__?.ready,null,{timeout:30000});
 for(const sentence of sentences){
  if(await calls()-start+2>MAX){console.log('stoppar: budget',MAX);break;}
  await page.evaluate(async()=>{__WORLD__.reset();document.getElementById('messages').replaceChildren();await __WORLD__.kompilering();});
  const before=await calls();
  const r=await page.evaluate(async s=>{
   const t0=performance.now();const c=await __WORLD__.chat(s);const visad=performance.now()-t0;
   const k=await __WORLD__.kompilering();const alla=performance.now()-t0;
   return {sentence:s,ops:c.response.edits?.map(e=>e.op)||null,message:c.response.message,choices:c.response.choices?.length||0,visadMs:c.totalMs,chatSvarMs:visad,helaVagenMs:alla,
    kompilerad:k?.kompilerad,kompileraMs:k?.kompileraMs,kompilerSedanVisningMs:k?alla-c.totalMs:null,avvikelserN:k?.avvikelserN,jamforda:k?.jamforda,avvikelser:k?.avvikelser?.map(a=>`${a.status}: ${a.falt}: webb ${a.webblasare} / plan ${a.kompilerad}`),status:document.getElementById('kompStatus').textContent};
  },sentence);
  r.jevAnrop=await calls()-before;rows.push(r);console.log(JSON.stringify(r));
  if(r.ops){ // ångra och kontrollera att planen följer
   const u=await page.evaluate(async()=>{const t0=performance.now();await __WORLD__.undo();const k=await __WORLD__.kompilering();return {ms:performance.now()-t0,kompilerad:k?.kompilerad,avvikelserN:k?.avvikelserN,edits:__WORLD__.regi().edits.length};});
   r.angra=u;console.log('  ångra',JSON.stringify(u));
  }
 }
 await page.evaluate(()=>__WORLD__.reset());
}finally{await browser.close();}
const out={datum:new Date().toISOString(),jevAnropTotalt:await calls()-start,rows,errors};
fs.writeFileSync(path.join(OUT,'logg',`chatprov-snabb-${Date.now()}.json`),JSON.stringify(out,null,1));console.log('Jev-anrop totalt',out.jevAnropTotalt,'fel',errors.length);
