// Separat kontroll efter att originalets hashkontroll stoppat kompileringen.
// Källans semantik och Jevs val bevaras. Ingen ny modellfråga ställs.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {ROOT,OUT,K,read,write,hash} from './prov.mjs';
const base=path.join(ROOT,'scen/3d/kontrakt/exempel/notan');
const k=structuredClone(K);const changed=[];const paths=[];
function walk(o,p='') {
  if(Array.isArray(o)){o.forEach((v,i)=>walk(v,p+'['+i+']'));return;}
  if(!o||typeof o!=='object')return;
  if(typeof o.sokvag==='string') {
    const absolute=path.resolve(base,o.sokvag);
    paths.push({field:p+'.sokvag',from:o.sokvag,to:absolute});o.sokvag=absolute;
    if(o.sha256&&fs.existsSync(absolute)) {
      const h=crypto.createHash('sha256').update(fs.readFileSync(absolute)).digest('hex');
      if(h!==o.sha256)changed.push({field:p+'.sha256',from:o.sha256,to:h});
      o.sha256=h;
    }
  }
  for(const [key,v] of Object.entries(o))walk(v,p? p+'.'+key:key);
}
walk(k);
write(path.join(OUT,'konkret/kalla_diagnostisk.json'),k);
write(path.join(OUT,'konkret/diagnostiska_skillnader.json'),{original_semantics_hash:hash(K.semantik),diagnostic_semantics_hash:hash(k.semantik),changed_hashes:changed,relocated_paths:paths,reason:'Originalets hashvärden avser äldre mätfiler. Detta är en separat diagnostik mot befintliga mätfiler, inte godkänd kompilering av originalet.'});
for(const id of ['t1','t2','t5','t11','t13']) {
  const regi=read(path.join(OUT,'konkret',id,'regi.json'));
  if(id==='t13')regi.edits[0].kommentar='Maten saknar prop-id i den angivna källan. Jev valde saknas; PLATSHALLARE är avsiktligt olöst. Endast denna kommentar tillagd i diagnostikrundan.';
  write(path.join(OUT,'konkret',id,'diagnostisk/regi.json'),regi);
  write(path.join(OUT,'konkret',id,'diagnostisk_latt/regi.json'),regi);
}
console.log(JSON.stringify({updated_hashes:changed.length,paths:paths.length,same_semantics:hash(K.semantik)===hash(k.semantik)}));
