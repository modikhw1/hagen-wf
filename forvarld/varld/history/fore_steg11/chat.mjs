import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {nyckel,MODELL} from '../../app/kalibrering/jev.mjs';
import {initial,apply,describe,propId} from './edits.mjs';
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../..'),LOG=path.join(OUT,'logg');fs.mkdirSync(LOG,{recursive:true});
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const frozen=read(path.join(OUT,'../jevprov/ut/fryst.json'));
const data=read(path.join(OUT,'../jevprov/meningar.json'));
const policy='Tolka CM:s mening som en redigeringsbegäran. Välj den direkta ändringen, inte följdarbete. Vaga kvalitetsönskemål utan angiven ändring kräver oklar. Flera tydliga ändringar får ha flera delar. Ingen ändring exekveras här.';
const choice=(instructions,criteria)=>({type:'choice',instructions,criteria});
const sets=[[],...data.delar.map(p=>[p]),...data.delar.flatMap((p,i)=>data.delar.slice(i+1).map(q=>[p,q]))];
const ledger=path.join(LOG,'anrop.jsonl');
export const countCalls=()=>fs.existsSync(ledger)?fs.readFileSync(ledger,'utf8').split('\n').filter(Boolean).length:0;
export function logEvent(e){fs.appendFileSync(path.join(LOG,'handelser.jsonl'),JSON.stringify({...e,time:new Date().toISOString()})+'\n');}
const margin=a=>{const sorted=Object.entries(a?.probabilities||{}).sort((a,b)=>b[1]-a[1]);return {confidence:a?.confidence??0,margin:sorted.length>1?sorted[0][1]-sorted[1][1]:0,ranking:sorted};};
async function ask(id,step,state,questions){
 if(countCalls()>=600)throw Error('Uppgiftens tak på 600 Jev-anrop är nått.');
 const key=nyckel(path.join(ROOT,'app'));if(!key)throw Error('TYPESAFE_API_KEY saknas lokalt.');
 const request={model:MODELL,state,questions},start=performance.now();
 fs.appendFileSync(ledger,JSON.stringify({id,step,time:new Date().toISOString(),number:countCalls()+1})+'\n');
 let record={id,step,request};
 try{const r=await fetch('https://api.typesafe.ai/v1/systemone',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify(request),signal:AbortSignal.timeout(15000),redirect:'error'});record.status=r.status;const raw=await r.text();try{record.answer=JSON.parse(raw);}catch{throw Error('Jev returnerade inte JSON.');}if(!r.ok)throw Error('Jev HTTP '+r.status);return record.answer.answers;}
 catch(e){record.error=e.name;throw e;}
 finally{record.ms=performance.now()-start;fs.writeFileSync(path.join(LOG,id+'-'+step+'.json'),JSON.stringify(record,null,2));}
}
const common=()=>({id:crypto.randomUUID(),ursprung:{typ:'cm'}});
export function alternatives(family,state,M,sentence,currentScene,value=null){
 const out=[],s=sentence.toLowerCase(),quoted=value??sentence.match(/["“”«»]([^"“”«»]+)["“”«»]/)?.[1];
 const add=edits=>{edits=Array.isArray(edits)?edits:[edits];try{let next=state;for(const e of edits)next=apply(next,e,M);if(JSON.stringify(next)===JSON.stringify(state))return;out.push({id:'a'+out.length,label:edits.map(describe).join('; '),edits});}catch{};};
 const scenes=state.scenes;
 if(family.startsWith('kamera.'))for(const sc of scenes){const person=M.scenes.find(x=>x.id===sc.origin).person.person;for(const framing of [null,'nara','hel']){const e={...common(),op:'renderkamera',scen:sc.id,kamera_id:'kam_'+crypto.randomUUID(),lage:'stativ',inramning:framing,mal:{typ:'person',id:person,punkt:'huvud'}};if(sc.camera?.lage===e.lage&&sc.camera?.inramning===framing)continue;add(e);}if(sc.camera)add({...common(),op:'renderkamera',scen:sc.id,kamera_id:'kam_'+crypto.randomUUID(),lage:'folj_uppmatt'});}
 else if(family==='plats.byt')for(const sid of ['alla',...scenes.map(s=>s.id)])for(const b of M.backdrops||[]){if((sid==='alla'?scenes:scenes.filter(s=>s.id===sid)).every(s=>s.venue===b.id))continue;add({...common(),op:'byt_miljo',scen:sid,rum:{kalla:b.source==='upload'?'upload':'bank',tillgang_id:b.id,ord:[],beskrivning:b.label}});}
 else if(family==='person.utseende')for(const person of [...new Set(scenes.map(s=>M.scenes.find(x=>x.id===s.origin).person.person))])for(const [name,color] of [['blå','#80a8ff'],['röd','#ef6868'],['grön','#70c090'],['original','#ffffff']]){if((state.cast[person]?.color||'#ffffff')===color)continue;add({...common(),op:'casta',person,kundroll:{id:person,namn:person},utseende:{troja_farg:color}});out.at(-1).label=person+': '+name+' helkroppston';}
 else if(family==='text.andra'){
  for(const sc of scenes){for(const t of sc.texts){add({...common(),op:'skarmtext',scen:sc.id,skarmtext_id:t.id,atgard:'ta_bort'});if(quoted)add({...common(),op:'skarmtext',scen:sc.id,skarmtext_id:t.id,atgard:'byt',text:quoted});for(const size of [22,36,44])if(size!==t.stil.storlek_px){const e={...common(),op:'skarmtext',scen:sc.id,skarmtext_id:t.id,atgard:'byt',stil:{storlek_px:size}};add(e);out.at(-1).label=`Text ${t.id} i ${sc.id}: ${size} px`;}}
   if(quoted)add({...common(),op:'skarmtext',scen:sc.id,skarmtext_id:'ny_'+crypto.randomUUID().slice(0,8),atgard:'lagg_till',text:quoted,box:[25,90,526,100]});}
  if(scenes.some(sc=>sc.texts.length))add(scenes.flatMap(sc=>sc.texts.map(t=>({...common(),op:'skarmtext',scen:sc.id,skarmtext_id:t.id,atgard:'ta_bort'}))));
 }
 else if(family==='replik.byt'&&quoted)for(const r of M.lines.filter(r=>scenes.some(s=>s.origin===r.scen))){if((state.lines[r.id]||r.text)===quoted)continue;add({...common(),op:'byt_replik',replik:r.id,text:quoted,sprak:'sv',rost:{motor:null,rost_id:null,stil:null},tidspolicy:'samma_lucka',max_talfaktor:null});}
 else if(family==='scen.ordning'){
  for(const sc of scenes){add({...common(),op:'ta_bort_scen',scen:sc.id});for(const after of [null,...scenes.map(s=>s.id)]){if(after===sc.id)continue;if(after!==null&&scenes[scenes.indexOf(sc)-1]?.id===after||after===null&&scenes[0]===sc)continue;add({...common(),op:'flytta_scen',scen:sc.id,efter:after});}add({...common(),op:'duplicera_scen',scen:sc.id,ny_id:sc.id+'_kopia_'+crypto.randomUUID().slice(0,4),efter:null,med_ljud:true});}
 }
 else if(family==='scen.langd'){for(const sc of scenes){for(const seconds of [.2,.5,1])if(sc.b-sc.a>seconds*M.fps+3)add({...common(),op:'trimma_scen',scen:sc.id,slut_s:(sc.b-Math.round(seconds*M.fps))/M.fps,lage:'klipp_slut'});add({...common(),op:'duplicera_scen',scen:sc.id,ny_id:sc.id+'_kopia_'+crypto.randomUUID().slice(0,4),efter:null,med_ljud:true});}}
 else if(family==='prop.andra')for(const sc of scenes)for(const [name,p] of Object.entries(sc.props)){if(!p)continue;const prop=propId(M,sc,name);if(p.visible){add({...common(),op:'ta_bort_prop',scen:sc.id,prop});for(const src of M.scenes.filter(x=>x.layers?.[name]))if(p.asset!==src.id+':'+name)add({...common(),op:'byt_prop',scen:sc.id,prop,ny_typ:name,tillgang_id:src.id+':'+name});}else add({...common(),op:'lagg_till_prop',scen:sc.id,ny_id:prop,typ:name,tillgang_id:p.asset});}
 // Keep valid full alternatives. Explicit scene numbers constrain without guessing intent.
 const mentioned=[...s.matchAll(/(?:scen(?:en)?\s*|\bs)(\d+)\b/g)].map(x=>'s'+x[1]);
 let filtered=out;if(mentioned.length===1)filtered=out.filter(a=>a.edits.every(e=>!e.scen||e.scen===mentioned[0]));
 // No individual food/can segmentation exists: never replace it by deleting an entire table.
 if(family==='prop.andra'&&/burk|kaffekopp|burgare|pommes|maten/.test(s)&&!/hela|kort|bord och mat/.test(s))return [];
 if(filtered.length>254)throw Error('För många giltiga val; precisera scenen.');return filtered;
}
export async function routeChat(input,M){
 const id=crypto.randomUUID(),start=performance.now(),sentence=String(input.sentence||'').trim();if(!sentence||sentence.length>2000)throw Error('Skriv 1–2000 tecken.');
 logEvent({type:'sentence',id,sentence,edits:input.edits||[],currentScene:input.currentScene});
 let state=initial(M);for(const e of input.edits||[])state=apply(state,e,M);
 const now=state.scenes.map(s=>`${s.id} (källa ${s.origin}), ${s.a/30}–${s.b/30} s; kamera ${s.camera?.lage||'uppmätt'}/${s.camera?.inramning||'original'}, bakgrund ${s.venue||'original'}; text ${s.texts.map(t=>t.id+':'+t.text).join('|')}; kort ${Object.entries(s.props).filter(([,p])=>p).map(([k,p])=>k+' '+(p.visible?'visas':'dolt')).join(',')}`).join('\n');
 const context=frozen.state+'\nAKTUELL VÄRLD (ersätter ursprungligt läge/ordning):\n'+now+'\nAKTUELL SCEN: '+input.currentScene+'\nCM: '+sentence;
 let family,parts,fa;
 if(input.pending){family=input.pending.family;parts=input.pending.parts;fa={confidence:1,probabilities:{[family]:1,other:0}};}
 else{const a=await ask(id,'familj',context,{familj:choice(policy+' Vilken ändringsfamilj passar bäst?',data.familjer),delar:choice(policy+' Vilka delar ändras direkt? Tom mängd om ingen konkret ändring kan väljas.',Object.fromEntries(sets.map((s,i)=>['p'+i,s.length?s.join(' + '):'inga delar / oklar'])))});family=a.familj.choice;fa=a.familj;parts=sets[Number(a.delar.choice?.slice(1))]||[];}
 const wish=message=>{logEvent({type:'wish',id,sentence,family,parts,message});return {id,family,parts,message,wish:true,callsUsed:countCalls()};};
 if(['oklar','ljud.andra','media.bild','person.uttryck','person.rorelse'].includes(family))return wish('Det kan världen inte göra ännu: '+(data.familjer[family]||family)+'. Önskemålet är sparat.');
 const value=input.pending?sentence.replace(/^["“”]|["“”]$/g,''):null;
 if((family==='replik.byt'||family==='text.andra'&&!/ta bort|större|mindre|textstorlek|\b\d+\s*px/i.test(sentence))&&!value&&!/["“”«»][^"“”«»]+["“”«»]/.test(sentence))return {id,family,parts,message:'Vilken exakt text vill du använda? Skriv den i nästa meddelande.',pending:{family,parts,sentence},callsUsed:countCalls()};
 const alts=alternatives(family,state,M,input.pending?.sentence||sentence,input.currentScene,value);
 if(!alts.length)return wish('Det finns inget giltigt separat mål eller någon sådan tillgång i paketet. Bord och mat är sammansatta kort. Önskemålet är sparat.');
 const criteria=Object.fromEntries(alts.map(a=>[a.id,a.label]));criteria.ingen='Inget alternativ motsvarar meningen; ställ en motfråga. Välj aldrig närmaste felaktiga sak.';
 const a=await ask(id,'konkret',context,{val:choice('Välj den fullständiga giltiga ändring som CM ber om, med rätt scen, mål och värde. Aktuell scen gäller bara när scen inte anges. Inget alternativ betyder ingen ändring. Välj ingen vid flera begärda ändringar som inte ryms i samma alternativ.',criteria)});
 const cm=margin(a.val),fm=margin(fa),low=cm.margin<.5||fm.margin<.5;
 const selected=alts.find(x=>x.id===a.val.choice);
 const response={id,family,parts,confidence:{family:fm,concrete:cm,cut:.5,scale:'Choice probability margin, not Score 0–4; heuristic, uncalibrated'},alternatives:alts,ms:performance.now()-start,callsUsed:countCalls()};
 if(!selected)return {...response,...wish('Jag hittar inget säkert giltigt val. Precisera scen, mål och ändring; önskemålet är sparat.')};
 if(low){const top=cm.ranking.filter(([id])=>id!=='ingen').slice(0,3).map(([id])=>alts.find(x=>x.id===id)).filter(Boolean);return {...response,message:'Jag är osäker. Välj ändringen:',choices:top};}
 logEvent({type:'proposed',id,edits:selected.edits});return {...response,message:selected.label,edits:selected.edits};
}
