"""One-shot v5 source migration; preserved v4 sources are in history/v4."""
from pathlib import Path
import json
O=Path('forvarld/varld')
v=(O/'history/v4/viewer.js').read_text(encoding='utf8')
v="import {initial,apply,timeline,sourceMap,describe,propId} from './edits.mjs';\n"+v
v=v.replace("const M=await (await fetch(url+'manifest.json')).json();", "const M=await (await fetch(url+'manifest.json')).json();\nlet state=initial(M),edits=[],transactions=[],chatPending=null;\nconst baseRegi=await (await fetch('/pipeline/base-regi.json')).json();")
v=v.replace("const local=sf-l.s.source[0],isTripod", "const current=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);\n const local=sf-l.s.source[0],isTripod")
v=v.replace("plate=$('plate').checked&&!isTripod;", "plate=$('plate').checked&&!isTripod&&!current.venue&&!Object.values(current.props).some(p=>p&&(!p.visible||p.asset.split(':')[0]!==current.origin));")
v=v.replace("tinted&&x.s.person.person==='A'?'#80a8ff':'#ffffff'", "state.cast[x.s.person.person]?.color||(tinted&&x.s.person.person==='A'?'#80a8ff':'#ffffff')")
v=v.replace("if(l.cards.foreground&&!plate&&$('layers').checked){l.cards.foreground.visible=true;}", "if(l.cards.foreground&&!plate&&$('layers').checked&&current.props.foreground?.visible){l.cards.foreground.visible=true;}")
v=v.replace("if(l.cards.nearForeground&&!plate&&$('layers').checked){l.cards.nearForeground.visible=true;}", "if(l.cards.nearForeground&&!plate&&$('layers').checked&&current.props.nearForeground?.visible){l.cards.nearForeground.visible=true;}")
v=v.replace("world.background=plate?l.plate:new THREE.Color('#8b8d91');room.visible=!plate;", "world.background=current.venue?backdropTextures.get(current.venue):plate?l.plate:new THREE.Color('#8b8d91');room.visible=!plate&&!current.venue;\n for(const name of ['foreground','nearForeground'])if(l.cards[name]&&current.props[name]){const asset=current.props[name].asset.split(':');l.cards[name].material.uniforms.map.value=loaded.find(x=>x.s.id===asset[0])?.cards[asset[1]]?.material.userData.originalMap||l.cards[name].material.userData.originalMap;}")
v=v.replace("const ts=texts.filter(t=>t.ut[0]<=frame&&frame<t.ut[1]);", "const cur=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);const ts=(cur?.texts||[]).filter(t=>t.ut[0]<=sourceFrame()&&sourceFrame()<t.ut[1]);")
v=v.replace("const time=sourceFrame()/30;", "const time=sourceFrame()/30;const cur=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);audio.muted=!cur?.sound||M.lines.some(r=>state.lines[r.id]!=null&&r.start_s<=time&&time<r.slut_s);")
a=v.index('async function edit(name)')
b=v.index("for(const name of ['ps2'",a)
v=v[:a]+'''function regi(){return {...baseRegi,skapad:new Date().toISOString(),edits:structuredClone(edits)};}
function rebuild(){sourceFrames=sourceMap(state);$('scrub').max=sourceFrames.length-1;frame=Math.min(frame,sourceFrames.length-1);tripod.clear();for(const s of state.scenes)if(s.camera?.lage==='stativ'){
 const l=loaded.find(l=>l.s.id===s.origin),key=tripodKey(l);if(s.camera.inramning==='nara')key.lins_mm*=1.12;if(s.camera.inramning==='hel')key.lins_mm*=.88;if(s.camera.fov_grader)key.lins_mm=1024/576*M.cameras.sensor_bredd_mm/(2*Math.tan(s.camera.fov_grader*Math.PI/360));tripod.set(s.id,key);
 }textKey='';$('editList').replaceChildren(...edits.map(e=>{const li=document.createElement('li');li.textContent=describe(e);return li;}));$('regiJson').textContent=JSON.stringify(regi(),null,2);$('undo').disabled=!transactions.length;localStorage.setItem('notan-regi-v5',JSON.stringify({edits,transactions}));syncMedia(true);}
async function event(data){await fetch('/api/event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
async function applyEdits(batch,{start=performance.now(),chatId=null}={}){
 pause();let next=state;for(const e of batch)next=apply(next,e,M);transactions.push({count:batch.length,chatId});edits.push(...structuredClone(batch));state=next;rebuild();
 const e=batch[0],scene=state.scenes.find(s=>s.id===e.scen||e.op==='casta'&&loaded.find(l=>l.s.id===s.origin).s.person.person===e.person||e.op==='byt_replik'&&M.lines.find(r=>r.id===e.replik)?.scen===s.origin);
 if(scene)frame=timeline(state).find(s=>s.id===scene.id).ut[0]+Math.floor((scene.b-scene.a)/2);syncMedia(true);
 const result=await mark('regi',start,{ops:batch.map(e=>e.op)});await event({type:'kept',chatId,edits:batch,timing:result});return result;
}
async function undo(){pause();const t=transactions.pop();if(!t)return;edits.splice(-t.count);state=initial(M);for(const e of edits)state=apply(state,e,M);rebuild();await mark('undo');await event({type:'undid',chatId:t.chatId});}
function say(text,who='world'){const row=document.createElement('div');row.className='message '+who;row.textContent=text;$('messages').append(row);row.scrollIntoView({block:'nearest'});return row;}
async function chat(sentence){const start=performance.now();say(sentence,'cm');$('send').disabled=true;
 try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sentence,edits,currentScene:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1])?.id,pending:chatPending})});const response=await r.json();if(!r.ok)throw Error(response.error||'Serverfel');chatPending=response.pending||null;
 const row=say(response.message);let applied=null;
 if(response.edits){applied=await applyEdits(response.edits,{start,chatId:response.id});row.textContent=response.message+` · ${Math.round(applied.clickToNextRafMs)} ms`;}
 if(response.choices){for(const choice of response.choices){const b=document.createElement('button');b.textContent=choice.label;b.onclick=async()=>{try{const result=await applyEdits(choice.edits,{chatId:response.id});row.replaceChildren(document.createTextNode(choice.label+` · ${Math.round(result.clickToNextRafMs)} ms`));await event({type:'picked',chatId:response.id,alternative:choice.id});}catch(e){say(e.message);}};row.append(b);}}
 window.__WORLD__.lastChat={sentence,response,applied,totalMs:applied?.clickToNextRafMs||performance.now()-start};return window.__WORLD__.lastChat;
 }catch(e){say(e.message);throw e;}finally{$('send').disabled=false;}}
async function edit(name){const common={id:crypto.randomUUID(),ursprung:{typ:'cm'}};if(name==='camera')return applyEdits([{...common,op:'renderkamera',scen:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]).id,kamera_id:common.id,lage:'stativ',inramning:'nara',mal:null}]);if(name==='text')return applyEdits([{...common,op:'skarmtext',scen:'s1',skarmtext_id:'st1',atgard:'byt',text:'Vem bjuder på middag?'}]);if(name==='tint')return applyEdits([{...common,op:'casta',person:'A',kundroll:{id:'A',namn:'kvinna'},utseende:{troja_farg:'#80a8ff'}}]);if(name==='pipeline')return applyEdits([{...common,op:'ta_bort_scen',scen:'s2'}]);}
$('play').onclick=togglePlay;$('scrub').oninput=e=>{pause();seek(Number(e.target.value));};
for(const name of ['tint','text','camera','pipeline'])$(name).onclick=()=>edit(name).catch(e=>say(e.message));
$('undo').onclick=undo;
$('reset').onclick=()=>{pause();edits=[];transactions=[];state=initial(M);frame=0;tripod.clear();tinted=false;textEdited=false;chatPending=null;rebuild();draw();event({type:'reset'});};
$('chatForm').onsubmit=e=>{e.preventDefault();const sentence=$('sentence').value.trim();if(sentence){$('sentence').value='';chat(sentence).catch(()=>{});}};
$('download').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(regi(),null,2)],{type:'application/json'}));a.download='regi.json';a.click();URL.revokeObjectURL(a.href);};
async function upload(file){if(!file)return;const r=await fetch('/api/backdrop?name='+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':file.type},body:file});const b=await r.json();if(!r.ok)throw Error(b.error);M.backdrops.push(b);const tex=await loader.loadAsync(b.url);tex.colorSpace=THREE.NoColorSpace;backdropTextures.set(b.id,tex);const row=say('Bilden är sparad lokalt som '+b.label+'.');const button=document.createElement('button');button.textContent='Använd i aktuell scen';button.onclick=()=>applyEdits([{id:crypto.randomUUID(),op:'byt_miljo',ursprung:{typ:'cm'},scen:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]).id,rum:{kalla:'upload',tillgang_id:b.id,ord:[],beskrivning:b.label}}]).catch(e=>say(e.message));row.append(button);}
$('upload').onchange=e=>upload(e.target.files[0]).catch(e=>say(e.message));$('chatPanel').ondragover=e=>e.preventDefault();$('chatPanel').ondrop=e=>{e.preventDefault();upload(e.dataTransfer.files[0]).catch(e=>say(e.message));};
''' +v[b:]
v=v.replace("const loadMs=performance.now()-boot;", "const loadMs=performance.now()-boot;\ntry{const saved=JSON.parse(localStorage.getItem('notan-regi-v5'));if(saved){for(const e of saved.edits)state=apply(state,e,M);edits=saved.edits;transactions=saved.transactions;}}catch{state=initial(M);edits=[];transactions=[];}rebuild();")
v=v.replace("ready:true,manifest:M", "ready:true,applyEdits,undo,chat,regi,getState:()=>structuredClone(state),manifest:M")
v=v.replace("isTripod=tripod.has(l.s.id)","isTripod=tripod.has(current.id)").replace("tripod.get(l.s.id)","tripod.get(current.id)")
v=v.replace("const target=new THREE.WebGLRenderTarget", "const backdropTextures=new Map();\nfor(const b of M.backdrops||[]){const t=await loader.loadAsync(b.url);t.colorSpace=THREE.NoColorSpace;backdropTextures.set(b.id,t);}\nfor(const l of loaded)for(const card of Object.values(l.cards))card.material.userData.originalMap=card.material.uniforms.map.value;\nconst target=new THREE.WebGLRenderTarget")
(O/'viewer.js').write_text(v,encoding='utf8')
h=(O/'history/v4/index.html').read_text(encoding='utf8')
h=h.replace('Regi → kompilator: ta bort s2','Ta bort s2 direkt')
h=h.replace('<button id="reset">','<button id="undo">Ångra</button><button id="download">Spara regi.json</button><button id="reset">')
h=h.replace('<div id="views">','<main><div id="views">')
h=h.replace('<p id="status">', '''<section id="chatPanel"><h3>Prata med världen</h3><p>Skriv en ändring. Släpp en bild här för en ny bakgrund. Allt sparas lokalt.</p><div id="messages" aria-live="polite"></div><form id="chatForm"><input id="sentence" placeholder='Exempel: kom närmare B i scen 7' autocomplete="off" required><button id="send">Ändra</button></form><label>Bakgrundsbild <input id="upload" type="file" accept="image/png,image/jpeg,image/webp"></label><h4>Gjorda ändringar</h4><ol id="editList"></ol><details><summary>Regi JSON</summary><pre id="regiJson"></pre></details></section></main><p id="status">''')
h=h.replace('</style>','main{display:flex;gap:24px;align-items:flex-start}#chatPanel{width:430px;background:#292e31;padding:16px;border-radius:8px}#messages{max-height:330px;overflow:auto}.message{padding:10px;margin:8px 0;background:#394447;border-radius:6px;white-space:pre-wrap}.cm{background:#21434d}#sentence{width:310px}pre{font-size:11px;white-space:pre-wrap}#editList{padding-left:24px}h4{margin-bottom:8px}@media(max-width:1050px){main{flex-wrap:wrap}} </style>')
(O/'index.html').write_text(h,encoding='utf8')
