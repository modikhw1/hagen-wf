// Kontroll av statusraden och kvalitetsknappen i den riktiga sidan. Kräver att server.mjs körs.
import path from 'node:path';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const OUT=path.resolve('forvarld/varld');
const browser=await chromium.launchPersistentContext(path.join(OUT,'browser-profile-v5'),{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true,viewport:{width:1160,height:950},args:['--no-first-run','--disable-gpu-sandbox']});
try{
 const page=browser.pages()[0],errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5195/');await page.waitForFunction(()=>window.__WORLD__?.ready,null,{timeout:30000});
 await page.evaluate(()=>__WORLD__.reset());await page.evaluate(()=>__WORLD__.kompilering());
 const t0=Date.now();
 await page.evaluate(()=>__WORLD__.edit('text'));
 const during=await page.textContent('#kompStatus');
 await page.evaluate(()=>__WORLD__.kompilering());
 console.log('direkt efter ändring :',during);console.log('när kompileringen klar:',await page.textContent('#kompStatus'));
 await page.click('#quality');const q0=Date.now();
 await page.waitForFunction(()=>/klar på|misslyckades/.test(document.getElementById('qualStatus').textContent),null,{timeout:200000});
 console.log('kvalitetsrad:',await page.textContent('#qualStatus'),`(väntat ${Math.round((Date.now()-q0)/1000)} s)`);
 await page.screenshot({path:path.join(OUT,'bilder/snabb-status.png'),clip:{x:0,y:0,width:1160,height:200}});
 await page.evaluate(()=>__WORLD__.reset());console.log('sidfel',errors.length,errors.slice(0,2));
}finally{await browser.close();}
