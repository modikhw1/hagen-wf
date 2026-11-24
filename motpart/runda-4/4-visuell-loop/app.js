import {Scen3DRenderer} from '/renderer.js';
const el=id=>document.getElementById(id);
const video=el('original');
const base=new Scen3DRenderer(el('baseline'));
const changed=new Scen3DRenderer(el('changed'));
let clip=null, variant=null, generation=0, ready=false, factor=1, renderedTime=-1;
for(const view of [base,changed]){view.setShowLabels(false);view.setShowTilltro(true);}

function draw(t){
  if(!ready)return;
  const snap=base.setTime(t);changed.setTime(t);renderedTime=t;
  el('clock').textContent=t.toFixed(2)+' s';el('seek').value=t;
  el('shot').textContent=snap.tagning_id||'—';
  for(const b of el('shots').children)b.classList.toggle('active',b.dataset.shot===snap.tagning_id);
}
function frameTick(_,metadata){if(!video.seeking)draw(video.paused?video.currentTime:metadata.mediaTime);video.requestVideoFrameCallback(frameTick);}
if(video.requestVideoFrameCallback)video.requestVideoFrameCallback(frameTick);
else video.addEventListener('timeupdate',()=>draw(video.currentTime));
video.addEventListener('seeked',()=>draw(video.currentTime));
video.addEventListener('play',()=>el('play').textContent='Pausa');
video.addEventListener('pause',()=>el('play').textContent='Spela');
video.addEventListener('error',()=>el('risk').textContent='Originalvideon kunde inte spelas. Visuell verifiering är blockerad.');
el('play').onclick=async()=>{if(video.paused){try{await video.play();}catch(e){el('risk').textContent=e.message;}}else video.pause();};
el('seek').oninput=()=>{video.currentTime=Number(el('seek').value);};

function applyLens(value){
  if(!ready)return;
  const t0=performance.now();factor=1+value/100;
  clip.package.tagningar.forEach((s,i)=>s.kamera.nycklar.forEach((k,j)=>variant.tagningar[i].kamera.nycklar[j][8]=k[8]*factor));
  changed.setTime(video.currentTime);
  el('factorText').textContent=(value>0?'+':'')+value+' %';
  el('undo').disabled=value===0;
  el('timing').textContent='Ändring → renderanrop: '+(performance.now()-t0).toFixed(1)+' ms';
}
el('lens').oninput=()=>applyLens(Number(el('lens').value));
el('undo').onclick=()=>{el('lens').value=0;applyLens(0);};
el('uncertain').onchange=()=>{for(const view of [base,changed])view.setShowTilltro(el('uncertain').checked);draw(video.currentTime);};

async function load(id){
  const token=++generation,t0=performance.now();ready=false;video.pause();
  for(const id of ['play','seek','lens','save'])el(id).disabled=true;
  const res=await fetch('/api/clip/'+encodeURIComponent(id));if(!res.ok)throw Error('Kunde inte läsa klippet');
  const data=await res.json();if(token!==generation)return;clip=data;variant=structuredClone(data.package);factor=1;
  base.loadScene(data.package);changed.loadScene(variant);
  video.src=data.video;
  await new Promise((resolve,reject)=>{video.onloadeddata=resolve;video.onerror=()=>reject(Error('Originalvideon kunde inte laddas'));video.load();});
  if(token!==generation)return;
  el('risk').textContent=data.risk;el('seek').max=data.duration;el('lens').value=0;el('factorText').textContent='0 %';el('undo').disabled=true;
  el('shots').replaceChildren();
  for(const shot of data.package.tagningar){const b=document.createElement('button');b.textContent=shot.id.toUpperCase();b.dataset.shot=shot.id;b.onclick=()=>video.currentTime=shot.ut[0]/data.package.tidsbas.fps;el('shots').append(b);}
  ready=true;draw(0);for(const id of ['play','seek','lens','save'])el(id).disabled=false;
  el('provenance').textContent=JSON.stringify({underlag:data.provenance,inventering:data.inventory,laddning_ms:data.load_ms},null,2);
  el('timing').textContent='Öppna klipp → första renderanrop: '+(performance.now()-t0).toFixed(0)+' ms';
  el('saved').textContent='';el('comment').value='';el('verdict').value='osaker';
}
el('clip').onchange=()=>load(el('clip').value).catch(e=>el('risk').textContent=e.message);
el('feedback').onsubmit=async e=>{
  e.preventDefault();el('save').disabled=true;
  const at=video.currentTime;
  try{const r=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clip:clip.id,factor,time:at,verdict:el('verdict').value,comment:el('comment').value})});const j=await r.json();if(!r.ok)throw Error(j.error);el('saved').textContent='Sparat ordagrant vid '+at.toFixed(2)+' s.';}catch(e){el('saved').textContent='Kunde inte spara: '+e.message;}finally{el('save').disabled=false;}
};
// Explicit inspection hooks for this experiment's own automated verification.
window.experiment={get ready(){return ready;},get clip(){return clip;},get factor(){return factor;},get baseline(){return base;},get changed(){return changed;},get variant(){return variant;},get renderedTime(){return renderedTime;},load,applyLens};
try{const rows=await(await fetch('/api/clips')).json();for(const r of rows)el('clip').add(new Option(r.name,r.id));el('clip').disabled=false;await load(rows[0].id);}catch(e){el('risk').textContent='Försöket kunde inte öppnas: '+e.message;console.error(e);}
