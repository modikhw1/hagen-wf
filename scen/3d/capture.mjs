// Dependency-free Chrome DevTools harness. Called by verifiera.py.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const [url,outDir,jobsPath,portText]=process.argv.slice(2),port=Number(portText||9223);
const profile=path.resolve(outDir,'chrome-profile');try{fs.rmSync(profile,{recursive:true,force:true});}catch{}fs.mkdirSync(profile,{recursive:true});   // ny profil varje gång: ingen gammal JS ur cachen
const errorLog=fs.openSync(path.join(outDir,'chrome.log'),'w');
const chrome=spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',['--headless=new','--mute-audio','--no-sandbox','--disable-gpu-sandbox','--no-first-run','--no-default-browser-check',`--user-data-dir=${profile}`,`--remote-debugging-port=${port}`,'--remote-allow-origins=*','--disable-extensions','--use-angle=swiftshader','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-networking','--disable-component-update','--disable-features=Translate','--window-size=576,1024','about:blank'],{windowsHide:true,stdio:['ignore','ignore',errorLog]});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,next=0;const pending=new Map(),errors=[],requests=[];
try{
 let pages;for(let i=0;i<100;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.length)break;}catch{}await sleep(100);}
 if(!pages?.length)throw Error('Chrome did not start');const page=pages.find(p=>p.type==='page'&&p.url==='about:blank');if(!page)throw Error('No capture tab');ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=e=>j(e.error||e);});
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p.reject(m.error);else p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);else if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);};
 ws.onclose=e=>{for(const p of pending.values())p.reject(Error(`CDP closed ${e.code}: ${e.reason}`));};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++next;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async(expression,userGesture=false)=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.setBlockedURLs',{urls:['https://*','http://*/*']});// localhost is re-enabled below via only HTTPS blocking
 await send('Network.setBlockedURLs',{urls:['https://*']});
 await send('Emulation.setDeviceMetricsOverride',{width:576,height:1024,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url});
 let ready=false;for(let i=0;i<600;i++){ready=await evaluate('!!window.__SCEN3D__?.ready');if(ready)break;if(errors.length)throw Error(JSON.stringify(errors));await sleep(100);}
 if(!ready)throw Error('Player readiness timeout');
 const jobs=JSON.parse(fs.readFileSync(jobsPath,'utf8')),results=[];
 for(const job of jobs){
  if(job.ui){await evaluate("document.body.classList.remove('capture')");await send('Emulation.setDeviceMetricsOverride',{width:1200,height:900,deviceScaleFactor:1,mobile:false});}
  const start=performance.now();const data=await evaluate(job.catalog?'window.__SCEN3D__.catalog()':`window.__SCEN3D__.setFrame(${job.t},${JSON.stringify({variant:job.variant||'procedural',mask:!!job.mask,cam:job.cam||null,orbit:job.orbit,rigMode:job.rigMode})})`);
  if(job.file){const image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,clip:{x:0,y:0,width:job.ui?1200:576,height:job.ui?900:1024,scale:1}});fs.writeFileSync(path.join(outDir,job.file),Buffer.from(image.data,'base64'));}
  if(job.ui){await evaluate("document.body.classList.add('capture')");await send('Emulation.setDeviceMetricsOverride',{width:576,height:1024,deviceScaleFactor:1,mobile:false});}
  results.push({...job,data,seconds:(performance.now()-start)/1000});
  if(job.file)process.stdout.write(job.file+'\n');
 }
 const smoke={};
 if(process.env.SCEN_SMOKE==='1'){
  const before=await evaluate('window.__frame.revision');const specPath=path.resolve('scen/3d/scen3d.json'),original=fs.readFileSync(specPath,'utf8');
  try{const edited=JSON.parse(original);edited.props.find(o=>o.id==='A:can').transform.position[0]+=.123;fs.writeFileSync(specPath,JSON.stringify(edited,null,2));await sleep(1400);smoke.hotReload=await evaluate(`({revision:window.__frame.revision,can:window.__SCEN3D__.getSpec().props.find(p=>p.id==='A:can').transform.position[0],renderedCan:window.__frame.objects['A:can'].position[0]})`);smoke.hotReload.before=before;}finally{fs.writeFileSync(specPath,original);await sleep(1400);}
  await evaluate("location.hash='t=1.2&mode=mask&cam=S1&capture=1'");await sleep(250);const a=await send('Page.captureScreenshot',{format:'png'});await sleep(400);const b=await send('Page.captureScreenshot',{format:'png'});smoke.hashFrozen=a.data===b.data;smoke.hashState=await evaluate('window.__frame');
  smoke.audio=await evaluate("new Promise(resolve=>{const a=new Audio('data/source-audio.m4a');a.onloadedmetadata=()=>resolve({duration:a.duration});a.onerror=()=>resolve({error:true});})");
  await evaluate("document.getElementById('audio').checked=true;document.getElementById('audio').dispatchEvent(new Event('change'));document.getElementById('play').click()",true);await sleep(600);smoke.playAdvanced=await evaluate('window.__frame.t>1.2');smoke.audioSync=await evaluate('({audio:window.__SCEN3D__.audioState(),sceneTime:window.__frame.audioTime})');await evaluate("document.getElementById('play').click()");
 }
 fs.writeFileSync(path.join(outDir,'capture-results.json'),JSON.stringify({results,smoke,errors,requests,externalRequests:requests.filter(u=>/^https?:/.test(u)&&!u.startsWith(new URL(url).origin))},null,2));
 await send('Browser.close');ws.close();
}finally{if(ws?.readyState===1)ws.close();chrome.kill();}
