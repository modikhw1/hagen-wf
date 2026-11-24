import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {routeChat,logEvent,countCalls} from './chat.mjs';
import {initial,apply,sourceMap,timeline} from './edits.mjs';
import {skapaKompilator} from './kompilator.mjs';
const OUT=path.dirname(fileURLToPath(import.meta.url)), ROOT=path.resolve(OUT,'../..');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.bin':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.mp4':'video/mp4','.m4a':'audio/mp4'};
const readManifest=()=>JSON.parse(fs.readFileSync(path.join(OUT,'paket/notan/manifest.json'),'utf8'));
const json=(res,value)=>{res.setHeader('Content-Type','application/json; charset=utf-8');res.end(JSON.stringify(value));};
async function body(req,max=1500000){const chunks=[];let n=0;for await(const chunk of req){n+=chunk.length;if(n>max)throw Error('För stor begäran.');chunks.push(chunk);}return Buffer.concat(chunks);}
let busy=false;
// Snabbvägen: en långlivad Pythonprocess kompilerar varje godkänd regi i bakgrunden (kompilator.mjs).
const kompilator=skapaKompilator({OUT,ROOT,M:readManifest(),baseRegi:JSON.parse(fs.readFileSync(path.join(OUT,'pipeline/base-regi.json'),'utf8'))});
kompilator.uppvarmning();
process.on('exit',()=>kompilator.stang());process.on('SIGINT',()=>{kompilator.stang();process.exit(0);});
const server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost');
  if(!['127.0.0.1:5195','localhost:5195'].includes(req.headers.host))throw Error('Ogiltig lokal värd.');
  if(req.method==='POST'&&req.headers.origin&&!['http://127.0.0.1:5195','http://localhost:5195'].includes(req.headers.origin))throw Error('Enbart lokala förfrågningar.');
  if(req.method==='GET'&&url.pathname==='/api/status')return json(res,{callsUsed:countCalls(),budget:600});
  if(req.method==='POST'&&url.pathname==='/api/kompilera'){const i=JSON.parse(await body(req));return json(res,{seq:kompilator.submit(i.edits||[],i.etikett)});}
  if(req.method==='GET'&&url.pathname==='/api/kompilering'){
   const want=Number(url.searchParams.get('seq')||0);
   if(url.searchParams.get('vanta')&&want){const t0=Date.now();while(kompilator.status().klar<want&&Date.now()-t0<25000)await new Promise(r=>setTimeout(r,25));}
   return json(res,kompilator.status());
  }
  if(req.method==='GET'&&url.pathname==='/api/kompilering/rader')return json(res,kompilator.rader());
  if(req.method==='POST'&&url.pathname==='/api/kvalitetskontroll')return json(res,await kompilator.kvalitetskontroll());
  if(req.method==='GET'&&url.pathname==='/api/kvalitet')return json(res,kompilator.status().kvalitet);
  if(req.method==='POST'&&url.pathname==='/api/chat')return json(res,await routeChat(JSON.parse(await body(req)),readManifest()));
  if(req.method==='POST'&&url.pathname==='/api/event'){logEvent(JSON.parse(await body(req)));return json(res,{ok:true});}
  if(req.method==='POST'&&url.pathname==='/api/regi'){
   const input=JSON.parse(await body(req)),M=readManifest();let state=initial(M);for(const e of input.edits||[input])state=apply(state,e,M);return json(res,{state,sourceFrames:sourceMap(state),timeMap:timeline(state),browserPreview:true});
  }
  if(req.method==='POST'&&url.pathname==='/api/backdrop'){
   const bytes=await body(req,8*1024*1024),type=req.headers['content-type'];let ext=null;
   if(type==='image/png'&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))ext='png';
   if(type==='image/jpeg'&&bytes[0]===255&&bytes[1]===216)ext='jpg';
   if(type==='image/webp'&&bytes.toString('ascii',0,4)==='RIFF'&&bytes.toString('ascii',8,12)==='WEBP')ext='webp';
   if(!ext)throw Error('Använd PNG, JPEG eller WebP, högst 8 MB.');
   const id='upload_'+crypto.randomUUID(),dir=path.join(OUT,'paket/backdrops');fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,id+'.'+ext),bytes);
   const b={id,url:'/paket/backdrops/'+id+'.'+ext,label:path.basename(url.searchParams.get('name')||'Egen bild').slice(0,100),source:'upload',kind:'okänd',horizon:.52,floor:.8,status:'assumed',assumption:'CM supplied image; horizon .52 and floor .8 assumed. Original person/table coordinate frame retained; image stretched to portrait.'};
   const M=readManifest();M.backdrops.push(b);M.provenance.assumed.push(b.assumption);fs.writeFileSync(path.join(OUT,'paket/notan/manifest.json'),JSON.stringify(M,null,2));logEvent({type:'upload',backdrop:b});return json(res,b);
  }
  if(req.method==='POST'&&url.pathname==='/api/compile'){
   if(busy){res.writeHead(409);return res.end('Compile in progress');}busy=true;
   const start=performance.now();
   try{
    let body='';for await(const chunk of req){body+=chunk;if(body.length>100000)throw Error('Payload too large');}
    const input=JSON.parse(body),base=JSON.parse(fs.readFileSync(path.join(OUT,'pipeline/base-regi.json')));
    // Endpoint accepts a full regi document or a single edit in the regi schema.
    const regi=input.schema_version?input:{...base,edits:[input]};
    fs.writeFileSync(path.join(OUT,'pipeline/edit-regi.json'),JSON.stringify(regi,null,2));
    const py=spawn(path.join(ROOT,'scen/.venv/Scripts/python.exe'),['-B',path.join(ROOT,'scen/3d/kontrakt/kompilera.py'),path.join(OUT,'pipeline/kalla.json'),path.join(OUT,'pipeline/edit-regi.json'),path.join(OUT,'pipeline/edited-plan.json')],{cwd:ROOT,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1'}});
    let log='';py.stdout.on('data',b=>log+=b);py.stderr.on('data',b=>log+=b);
    const code=await new Promise((r,j)=>{py.on('exit',r);py.on('error',j);});
    fs.writeFileSync(path.join(OUT,'pipeline/compile.log'),log);
    if(code!==0)throw Error(log);
    const p=JSON.parse(fs.readFileSync(path.join(OUT,'pipeline/edited-plan.json')));
    const answer={compileAndIoMs:performance.now()-start,timeMap:p.tidskarta,sourceFrames:p.kallrutor,scenes:p.scener.map(s=>({id:s.id,ut:s.ut,kalla:s.kalla})),text:p.skarmtext,applied:p.tillampat,rejected:p.ej_tillampat,warnings:p.varningar};
    fs.writeFileSync(path.join(OUT,'pipeline/last-result.json'),JSON.stringify(answer,null,2));
    res.setHeader('Content-Type','application/json');res.end(JSON.stringify(answer));
   }finally{busy=false;}
   return;
  }
  if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405);return res.end();}
  const pathname=decodeURIComponent(url.pathname);
  const base=pathname.startsWith('/three/')?path.join(ROOT,'video/node_modules/three'):OUT;
  const rel=pathname.startsWith('/three/')?pathname.slice(7):pathname==='/'?'index.html':pathname.slice(1);
  const file=path.resolve(base,rel);
  if(!file.startsWith(base+path.sep))throw Error('Outside allowed static root');
  const stat=fs.statSync(file);if(!stat.isFile())throw Error('Not a file');
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.setHeader('Cache-Control','no-store');res.setHeader('Accept-Ranges','bytes');
  const range=req.headers.range;
  if(range){const [a,b]=range.replace('bytes=','').split('-');const start=Number(a),end=b?Math.min(Number(b),stat.size-1):stat.size-1;res.writeHead(206,{'Content-Range':`bytes ${start}-${end}/${stat.size}`,'Content-Length':end-start+1});fs.createReadStream(file,{start,end}).pipe(res);}
  else{res.setHeader('Content-Length',stat.size);fs.createReadStream(file).pipe(res);}
 }catch(e){res.writeHead(400,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify({error:e.message}));}
});
server.listen(5195,'127.0.0.1',()=>console.log('Förvärld: http://127.0.0.1:5195'));
