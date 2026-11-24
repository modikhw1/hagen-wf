import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const OUT=path.dirname(fileURLToPath(import.meta.url)), ROOT=path.resolve(OUT,'../..');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.bin':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.mp4':'video/mp4','.m4a':'audio/mp4'};
let busy=false;
const server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost');
  if(req.method==='POST'&&url.pathname==='/api/regi'){
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
 }catch(e){res.writeHead(400,{'Content-Type':'text/plain; charset=utf-8'});res.end(String(e.stack||e));}
});
server.listen(5195,'127.0.0.1',()=>console.log('Förvärld: http://127.0.0.1:5195'));
