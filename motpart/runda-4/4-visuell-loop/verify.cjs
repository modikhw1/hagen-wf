const { chromium }=require('../../../arbetsbord/prov/node_modules/playwright-core');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const out=path.join(__dirname,'ut','qa');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',args:['--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1400,height:1100}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5204',{waitUntil:'networkidle',timeout:20000});
 await page.waitForFunction(()=>window.experiment?.ready,{timeout:15000});
 const report={kind:'technical_checks_not_owner_verdict',errors,clips:[]};
 for(const key of ['duepiani','spanjorskan']){
  if(await page.locator('#clip').inputValue()!==key){await page.selectOption('#clip',key);await page.waitForFunction(k=>window.experiment?.ready&&window.experiment.clip.id===k,key);}
  const shots=await page.evaluate(()=>window.experiment.clip.package.tagningar.map(s=>({id:s.id,ut:s.ut}))),fps=await page.evaluate(()=>window.experiment.clip.package.tidsbas.fps);
  const entries=[];
  for(let i=0;i<shots.length;i++){
   const s=shots[i],t=(s.ut[0]+s.ut[1]-1)/(2*fps);
   await page.evaluate(t=>{document.querySelector('video').currentTime=t;},t);
   await page.waitForFunction(t=>!document.querySelector('video').seeking&&Math.abs(window.experiment.renderedTime-t)<.002,t);
   const snap=await page.evaluate(()=>({base:window.experiment.baseline.getSnapshot(),changed:window.experiment.changed.getSnapshot(),canvas:document.querySelector('#baseline').getBoundingClientRect().toJSON()}));
   assert.equal(snap.base.tagning_id,s.id);assert.deepEqual(snap.base,snap.changed);
   assert.ok(Math.abs(snap.canvas.width/snap.canvas.height-9/16)<.01,'aspect ratio');
   await page.locator('.views').screenshot({path:path.join(out,key+'-'+s.id+'.png')});
   entries.push({shot:s.id,time:t,snapshot:snap.base});
   if(i){
    for(const f of [s.ut[0]-1,s.ut[0]+1]){
     const at=f/fps;await page.evaluate(t=>document.querySelector('video').currentTime=t,at);
     await page.waitForFunction(t=>!document.querySelector('video').seeking&&Math.abs(window.experiment.renderedTime-t)<.002,at);
     const actual=await page.evaluate(()=>window.experiment.baseline.getSnapshot().tagning_id);
     assert.equal(actual,f<s.ut[0]?shots[i-1].id:s.id,'shot transition');
    }
   }
  }
  await page.evaluate(()=>document.querySelector('video').currentTime=.7);
  await page.waitForFunction(()=>Math.abs(window.experiment.renderedTime-.7)<.045);
  const before=await page.evaluate(()=>JSON.stringify(window.experiment.clip.package));
  await page.locator('#lens').fill('15');await page.locator('#lens').dispatchEvent('input');
  const altered=await page.evaluate(()=>({base:window.experiment.baseline.getSnapshot(),changed:window.experiment.changed.getSnapshot(),timing:document.querySelector('#timing').textContent}));
  assert.ok(Math.abs(altered.changed.kamera.lins_mm/altered.base.kamera.lins_mm-1.15)<.001);
  assert.deepEqual(altered.base.kamera.pos,altered.changed.kamera.pos);
  await page.screenshot({path:path.join(out,key+'-changed.png'),fullPage:true});
  await page.click('#undo');assert.equal(await page.evaluate(()=>JSON.stringify(window.experiment.variant)),before);
  assert.equal(await page.evaluate(()=>JSON.stringify(window.experiment.clip.package)),before);
  await page.evaluate(()=>{const v=document.querySelector('video');v.currentTime=.5;v.muted=true;v.playbackRate=1;});
  await page.click('#play');await page.waitForFunction(()=>document.querySelector('video').currentTime>1.5);
  const playback=await page.evaluate(()=>({media:document.querySelector('video').currentTime,scene:window.experiment.renderedTime,paused:document.querySelector('video').paused}));
  await page.click('#play');assert.equal(playback.paused,false);assert.ok(Math.abs(playback.media-playback.scene)<.15);
  report.clips.push({key,entries,altered,playback});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({ok:true,shots:report.clips.reduce((n,c)=>n+c.entries.length,0),clips:report.clips.map(c=>({key:c.key,playback:c.playback,change:c.altered.timing})),errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
