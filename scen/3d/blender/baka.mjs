// node scen/3d/blender/baka.mjs  (no npm packages; Node >= 22)
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const OUT=path.dirname(fileURLToPath(import.meta.url)), ROOT=path.dirname(OUT), FPS=30;
const VERIFY=path.join(OUT,'verifiering');fs.mkdirSync(VERIFY,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(path.join(ROOT,'player.js'),'utf8');
const baseline=source.replace(/^import .*SCEN_BAKE_READ_ONLY\r?\n/m,'').replace('dump:options=>dumpPlayer({xbots,objects,camera,spec,shotAt},options),','');
const mime={'.js':'text/javascript','.html':'text/html','.json':'application/json','.glb':'model/gltf-binary','.m4a':'audio/mp4'};
const server=http.createServer((req,res)=>{
  try {
    const url=new URL(req.url,'http://localhost'), before=url.pathname.startsWith('/baseline/');
    let rel=decodeURIComponent(url.pathname).replace(/^\/baseline\//,'/');if(rel.endsWith('/'))rel+='index.html';
    const file=path.resolve(ROOT,'.'+rel);if(!file.startsWith(ROOT+path.sep))throw Error('Outside root');
    res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.setHeader('Cache-Control','no-store');
    if(before&&rel==='/player.js')res.end(baseline);else res.end(fs.readFileSync(file));
  }catch(e){res.writeHead(404);res.end(String(e));}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`;
const port=await new Promise(r=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>r(p));});});
const profile=fs.mkdtempSync(path.join(OUT,'chrome-bake-'));
const log=fs.openSync(path.join(OUT,'chrome-bake.log'),'w');
const chrome=spawn(process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',[
  '--headless=new','--mute-audio','--no-sandbox','--disable-gpu-sandbox','--no-first-run','--no-default-browser-check',`--user-data-dir=${profile}`,
  `--remote-debugging-port=${port}`,'--remote-allow-origins=*','--disable-extensions','--use-angle=swiftshader',
  '--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-networking','--disable-component-update',
  '--disable-features=Translate','--window-size=576,1024','about:blank'],{windowsHide:true,stdio:['ignore','ignore',log]});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,next=0;const pending=new Map(),errors=[],requests=[];
try {
  let page;
  for(let i=0;i<150;i++) {try{page=(await(await fetch(`http://127.0.0.1:${port}/json`)).json()).find(p=>p.type==='page');if(page)break;}catch{}await sleep(100);}
  if(!page)throw Error('Chrome did not start');
  ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(!p)return;clearTimeout(p.timeout);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);else if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);};
  ws.onclose=e=>{for(const p of pending.values()){clearTimeout(p.timeout);p.reject(Error(`CDP closed ${e.code}: ${p.method}`));}pending.clear();};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++next;const timeout=setTimeout(()=>{pending.delete(id);reject(Error(`CDP timeout: ${method}`));},120000);pending.set(id,{resolve,reject,timeout,method});ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  const navigate=async before=>{
    await send('Page.navigate',{url:`${origin}/${before?'baseline/':''}index.html#t=0&capture=1&avatar=xbot&ljud=original`});
    for(let i=0;i<600;i++){if(await evaluate('!!window.__SCEN3D__?.ready'))return;if(errors.length)throw Error(JSON.stringify(errors));await sleep(100);}
    throw Error('Player readiness timeout');
  };
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.setBlockedURLs',{urls:['https://*']});
  await send('Emulation.setDeviceMetricsOverride',{width:576,height:1024,deviceScaleFactor:1,mobile:false});
  console.log('Loading player');await navigate(false);console.log('Player ready');
  const spec=await evaluate('window.__SCEN3D__.getSpec()'), duration=spec.shots.reduce((a,s)=>a+s.duration,0), N=Math.round(duration*FPS);
  const times=Array.from({length:N},(_,i)=>i/FPS);
  let start=0;const boundaryTimes=spec.shots.flatMap(s=>{const a=start;start+=s.duration;return [a-1/FPS,a,a+1/FPS,start-1/FPS,start];}).filter(t=>t>=0&&t<duration);
  const timeline=await evaluate(`window.__SCEN3D__.dump({timeline:${JSON.stringify([...times,...boundaryTimes])}})`);
  const samples=spec.shots.flatMap(s=>{const ids=times.map((_,i)=>i).filter(i=>timeline.shotAt[i].shot===s.id);return [...new Set([ids[0]+2,ids[Math.floor(ids.length/2)],ids.at(-1)-2])].map(i=>({i,shot:s.id}));});
  console.log('Exporting geometry');
  const assetLength=await evaluate('(window.__bakeAssets=JSON.stringify(window.__SCEN3D__.dump({assets:true}))).length');
  let assetText='';for(let offset=0;offset<assetLength;offset+=500000)assetText+=await evaluate(`window.__bakeAssets.slice(${offset},${offset+500000})`);
  await evaluate('delete window.__bakeAssets');fs.writeFileSync(path.join(OUT,'bake-assets.json'),assetText);
  const frames=[], regression=[];
  const png=async()=>Buffer.from((await evaluate("document.querySelector('canvas').toDataURL('image/png')")).split(',')[1],'base64');
  for(let i=0;i<N;i++) {
    const f=await evaluate(`(async()=>{await window.__SCEN3D__.setFrame(${i}/30,{variant:'xbot',mask:false});return window.__SCEN3D__.dump();})()`);
    if(f.t!==i/FPS||f.audioMode!=='original'||f.errors.length)throw Error(`Invalid frame ${i}`);frames.push({i,...f});
    const sample=samples.find(s=>s.i===i);
    if(sample){
      const stem=`${sample.shot}-${String(i).padStart(3,'0')}`;
      const color=await png();fs.writeFileSync(path.join(VERIFY,`${stem}-player.png`),color);
      await evaluate(`window.__SCEN3D__.setFrame(${i}/30,{variant:'xbot',mask:true})`);
      const mask=await png();fs.writeFileSync(path.join(VERIFY,`${stem}-player-mask.png`),mask);
      regression.push({i,shot:sample.shot,color:hash(color),mask:hash(mask)});
    }
    if(i%30===0||i===N-1)console.log(`Baked ${i+1}/${N} (${f.shot})`);
  }
  // Same source served with only the read-only hook removed: pixel regression in both display modes.
  await navigate(true);
  for(const r of regression){
    await evaluate(`window.__SCEN3D__.setFrame(${r.i}/30,{variant:'xbot',mask:false})`);r.baselineColor=hash(await png());
    await evaluate(`window.__SCEN3D__.setFrame(${r.i}/30,{variant:'xbot',mask:true})`);r.baselineMask=hash(await png());
    r.pass=r.color===r.baselineColor&&r.mask===r.baselineMask;
  }
  const inputs=['scen3d.json','avatar_xbot.js','scene_runtime.js','modeller/Xbot.glb','data/motion-2.json','data/source-audio.m4a',...spec.actors.map(a=>a.motion.ref)];
  const fingerprints=Object.fromEntries([...new Set(inputs)].map(p=>[p,hash(fs.readFileSync(path.join(ROOT,p)))]));
  const bake={schema:'scen3d-bake/1',fps:FPS,N,duration,width:576,height:1024,audioMode:'original',audio:spec.audio,
    coordinateSystem:'three.js Y-up, metres; xyzw quaternions; column-major matrices; i=0 -> Blender frame 0',
    assets:'bake-assets.json',assetsSha256:hash(assetText),fingerprints,shots:timeline.shots,shotAt:timeline.shotAt,
    samples,regression,errors,externalRequests:requests.filter(u=>/^https?:/.test(u)&&!u.startsWith(origin)),frames};
  const temp=path.join(OUT,'bake.json.tmp');fs.writeFileSync(temp,JSON.stringify(bake));fs.renameSync(temp,path.join(OUT,'bake.json'));
  if(regression.some(r=>!r.pass)||errors.length||bake.externalRequests.length)throw Error('Player regression failed; see bake.json');
  console.log(`Wrote ${N} frames, ${duration}s; ${regression.length*2} unchanged player images -> ${path.join(OUT,'bake.json')}`);
  await send('Browser.close');
} finally {
  if(ws?.readyState===1)ws.close();chrome.kill();server.close();fs.closeSync(log);
  // Only this run's generated directory, checked to be inside the task directory.
  if(path.dirname(path.resolve(profile))===OUT){for(let attempt=0;attempt<10;attempt++){try{fs.rmSync(profile,{recursive:true,force:true});break;}catch{await sleep(200);}}}
}
