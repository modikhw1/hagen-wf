// Same explicitly authorized free-tier detector as scen/sprak/gemini_bild.mjs,
// with native fetch because this Windows curl's Schannel cannot acquire credentials.
// Credentials stay in memory, never in output or files. Only the free-tier key is read.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const [image,out,context]=process.argv.slice(2),root=path.dirname(fileURLToPath(import.meta.url));
const envText=fs.readFileSync(path.resolve(root,'../../video/.env.local'),'utf8');
const line=envText.split(/\r?\n/).find(s=>s.startsWith('GEMINI_API_KEY_GRATIS='));
if(!line)throw Error('Free-tier credential unavailable');
const key=line.slice(line.indexOf('=')+1).trim().replace(/^['"]|['"]$/g,'');
const model='gemini-3.5-flash-lite';const start=performance.now();
const schema={type:'OBJECT',properties:{saker:{type:'ARRAY',items:{type:'OBJECT',properties:{etikett:{type:'STRING'},box_2d:{type:'ARRAY',items:{type:'INTEGER'},description:'[ymin,xmin,ymax,xmax] 0-1000'},osaker:{type:'BOOLEAN'},kommentar:{type:'STRING'}},required:['etikett','box_2d','osaker','kommentar']}}},required:['saker']};
const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':key},body:JSON.stringify({contents:[{role:'user',parts:[{inline_data:{mime_type:'image/jpeg',data:fs.readFileSync(image).toString('base64')}},{text:context+' Rutformat [ymin,xmin,ymax,xmax] 0–1000. Markera osaker=true vid otydlig eller skymd kant och förklara kort.'}]}],generationConfig:{responseMimeType:'application/json',responseSchema:schema,temperature:.1,maxOutputTokens:4000}}),signal:AbortSignal.timeout(180000)});
if(!response.ok)throw Error(`Free-tier detector HTTP ${response.status}`);
const body=await response.json();if(!body.candidates?.[0]?.content?.parts)throw Error('Detector returned no content');
const data=JSON.parse(body.candidates[0].content.parts.map(p=>p.text||'').join(''));
fs.writeFileSync(out,JSON.stringify({model,ms:performance.now()-start,source:path.basename(image),...data},null,2));
console.log(path.basename(image),data.saker.length,'source prop boxes');
