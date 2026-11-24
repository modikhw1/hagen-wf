import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {chromium} from '../../app/node_modules/playwright-core/index.mjs';
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../..'),IM=path.join(OUT,'bilder');fs.mkdirSync(IM,{recursive:true});
const gate=spawnSync(path.join(ROOT,'scen/.venv/Scripts/python.exe'),['-B','-c',"import sys;sys.path.insert(0,'forvarld/varld');from export import wait_heavy;wait_heavy()"],{cwd:ROOT,encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1'}});if(gate.status!==0)throw Error(gate.stderr);
const executablePath=process.env.CHROME_PATH||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe');
const profile=path.join(OUT,'browser-profile');
const browser=await chromium.launchPersistentContext(profile,{executablePath,headless:true,viewport:{width:1000,height:850},args:['--disable-background-networking','--disable-component-update','--no-first-run','--disable-extensions','--disable-gpu-sandbox','--autoplay-policy=no-user-gesture-required',...(process.argv.includes('--software')?['--use-angle=swiftshader','--enable-unsafe-swiftshader']:[])]});
const page=browser.pages()[0]||await browser.newPage(),errors=[],requests=[];
page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));
await page.route('**/*',route=>{const u=route.request().url();return u.startsWith('http://127.0.0.1:5195/')||u.startsWith('data:')?route.continue():route.abort();});
const writeData=(name,data)=>fs.writeFileSync(path.join(IM,name),Buffer.from(data.split(',')[1],'base64'));
try{
 const nav=performance.now();await page.goto('http://127.0.0.1:5195/');
 await page.waitForFunction(()=>window.__WORLD__?.ready,{timeout:60000});await page.waitForTimeout(1000);
 console.log('READY',await page.evaluate(()=>({gpu:__WORLD__.gpu,loadMs:__WORLD__.loadMs})),errors);
 if(errors.length)throw Error(errors.join('\n'));
 if(process.argv.includes('--smoke')){await page.screenshot({path:path.join(IM,'viewer-smoke.png')});writeData('smoke.png',await page.evaluate(()=>__WORLD__.png()));}
 else{
  const manifest=await page.evaluate(()=>__WORLD__.manifest);
  const report={date:new Date().toISOString(),executablePath,loadMs:await page.evaluate(()=>__WORLD__.loadMs),navigationToReadyMs:performance.now()-nav,errors,edits:[],externalRequests:[]};
  for(const s of manifest.scenes){
   const f=Math.floor((s.ut[0]+s.ut[1])/2);await page.evaluate(f=>__WORLD__.seek(f,{plate:true}),f);
   writeData(s.id+'-ps2.png',await page.evaluate(()=>__WORLD__.png()));
   writeData(s.id+'-source.png',await page.evaluate(()=>{const c=document.createElement('canvas');c.width=576;c.height=1024;c.getContext('2d').drawImage(document.querySelector('video'),0,0,576,1024);return c.toDataURL();}));
   await page.evaluate(f=>__WORLD__.seek(f,{plate:false}),f);writeData(s.id+'-room.png',await page.evaluate(()=>__WORLD__.png()));console.log('CAPTURED',s.id,f);
  }
  for(const [j,scene] of [manifest.scenes[0],manifest.scenes[1],manifest.scenes[3],manifest.scenes[5]].entries()){
   const a=Math.floor((scene.ut[0]+scene.ut[1])/2)-2;
   for(let k=0;k<4;k++){await page.evaluate(f=>__WORLD__.seek(f,{plate:true}),a+k);writeData(`motion-${j+1}-${k}.png`,await page.evaluate(()=>__WORLD__.png()));}
  }
  await page.evaluate(()=>__WORLD__.seek(25,{plate:true}));
  report.ps2=await page.evaluate(()=>__WORLD__.benchmark(180));
  await page.evaluate(()=>document.getElementById('ps2').checked=false);
  report.plain=await page.evaluate(()=>__WORLD__.benchmark(60));
  await page.evaluate(()=>__WORLD__.reset());
  for(const name of ['tint','text','camera','pipeline']){
   await page.evaluate(()=>__WORLD__.seek(25,{plate:true}));
   await page.click('#'+name);
   await page.waitForFunction(n=>__WORLD__.measurements.some(m=>m.edit===n)||document.getElementById('status').textContent.startsWith('Error:'),name,{timeout:180000});
   const status=await page.locator('#status').textContent();if(status.startsWith('Error:'))throw Error(status);
   report.edits.push(await page.evaluate(n=>__WORLD__.measurements.find(m=>m.edit===n),name));
   fs.writeFileSync(path.join(OUT,'measurements.json'),JSON.stringify(report,null,2));console.log('EDIT',report.edits.at(-1));
   await page.screenshot({path:path.join(IM,`edit-${name}.png`)});
  }
  await page.evaluate(()=>__WORLD__.reset());
  // Playback run measures presented requestAnimationFrame cadence, with sound + source.
  await page.click('#play');await page.waitForTimeout(3500);await page.click('#play');
  report.playback=await page.evaluate(()=>{const a=__WORLD__.rafTimes.slice(-120).sort((a,b)=>a-b);return{medianRafMs:a[Math.floor(a.length/2)],p95RafMs:a[Math.floor(a.length*.95)],approxFps:1000/(a.reduce((x,y)=>x+y,0)/a.length)};});
  if(!process.argv.includes('--no-mp4')){
   const dir=path.join(IM,'film-rutor');fs.mkdirSync(dir,{recursive:true});
   for(let f=0;f<180;f++){await page.evaluate(f=>__WORLD__.seek(f,{plate:true}),f);fs.writeFileSync(path.join(dir,String(f).padStart(4,'0')+'.png'),Buffer.from((await page.evaluate(()=>__WORLD__.png())).split(',')[1],'base64'));if(f%30===0)console.log('VIDEO',f);}
  }
  report.externalRequests=requests.filter(u=>/^https?:/.test(u)&&!u.startsWith('http://127.0.0.1:5195/'));
  fs.writeFileSync(path.join(OUT,'measurements.json'),JSON.stringify(report,null,2));console.log('REPORT',JSON.stringify(report,null,2));
 }
}finally{await browser.close();}
