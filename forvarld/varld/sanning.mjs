// Sanningskontroll: vad webbläsarens reducerare visar jämfört med den kompilerade planen för samma regi.
// Ren funktion utan I/O. `plan` är sammanfattningen från kompilator_demon.py, `grund` samma för en regi utan edits.
import {initial,apply,timeline,sourceMap} from './edits.mjs';
import {stativMatt} from './stativ.mjs';

const near=(a,b,t=1e-6)=>Math.abs(a-b)<=t;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function runs(list){const out=[];for(const t of list){if(out.length&&out.at(-1)[1]===t)out.at(-1)[1]=t+1;else out.push([t,t+1]);}return out;}
const norm=t=>String(t??'').replace(/\s*\n\s*/g,' ').trim();

// Måtten kommer från samma beräkning som viewer.js använder för visningen.
export const webbKamera=stativMatt;
function planKamera(plan,grund,sc){
 // sc = scenens rad i planen. Jämför mot grundplanens kamera för samma källrutor (samma rum, samma uppmätta bana).
 const n=plan.renderkamera.nycklar,g=grund.renderkamera.nycklar;if(n.length!==plan.antal_rutor)return null;
 const frames=[];for(let f=sc.ut[0];f<sc.ut[1];f++)frames.push(f);if(!frames.length)return null;
 // grundplanens index för samma källruta (grundplanen har identiteten ut = källa)
 const srcOf=f=>{const row=plan.tidskarta.find(r=>r.ut[0]<=f&&f<r.ut[1]);return row.kalla[0]+(f-row.ut[0]);};
 const T=m=>[m[0][3],m[1][3],m[2][3]],d=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
 const mid=frames[Math.floor(frames.length/2)];const gk=g[srcOf(mid)],pk=n[mid];
 const lens=pk.lins_mm/gk.lins_mm;let spread=0;const t0=T(pk.matris);for(const f of frames)spread=Math.max(spread,d(T(n[f].matris),t0));
 return {lens_mm:pk.lins_mm,lens_faktor:lens,forskjutning_m:d(T(pk.matris),T(gk.matris)),rorelse_i_scenen_m:spread};
}

export function sanning(edits,M,plan,grund){
 let state=initial(M);for(const e of edits)state=apply(state,e,M);
 const tl=timeline(state),rows=[],add=(falt,status,webblasare,kompilerad,anm)=>rows.push({falt,status,webblasare,kompilerad,...(anm?{anm}:{})});
 // 1. Tillämpade edits
 const ok=new Set(plan.tillampat.map(e=>e.id)),rej=new Map(plan.ej_tillampat.map(e=>[e.id,e.orsak]));
 for(const e of edits){
  if(ok.has(e.id))add(`edit ${e.op} ${e.id.slice(0,8)}`,'stammer','tillämpad','tillämpad');
  else add(`edit ${e.op} ${e.id.slice(0,8)}`,'ej_tillampad_av_kontraktet','tillämpad',rej.get(e.id)||'saknas i planen');
 }
  // 2. Scener: ordning, ut- och källintervall
 const ws=tl.map(s=>[s.id,s.ut,[s.a,s.b]]),ps=plan.scener.map(s=>[s.id,s.ut,s.kalla]);
 add('scenordning',same(ws.map(x=>x[0]),ps.map(x=>x[0]))?'stammer':'skiljer',ws.map(x=>x[0]).join(' '),ps.map(x=>x[0]).join(' '));
 const bad=[];ws.forEach((w,i)=>{const p=ps[i];if(!p||!same(w[1],p[1])||!same(w[2],p[2]))bad.push(`${w[0]}: webb ut${JSON.stringify(w[1])} källa${JSON.stringify(w[2])}, plan ${p?`ut${JSON.stringify(p[1])} källa${JSON.stringify(p[2])}`:'saknas'}`);});
 add('sceners ut-/källintervall',bad.length?'skiljer':'stammer',`${ws.length} scener`,bad.length?bad.join('; '):`${ps.length} scener`);
 const wr=runs(sourceMap(state));
 add('källrutornas ordning',same(wr,plan.kallrutor_intervall)?'stammer':'skiljer',`${state.scenes.length?sourceMap(state).length:0} rutor ${JSON.stringify(wr).slice(0,80)}`,`${plan.antal_rutor} rutor ${JSON.stringify(plan.kallrutor_intervall).slice(0,80)}`);
 const sb=tl.map((s,i)=>s.sound!==(plan.tidskarta[i]?.ljud)?`${s.id}`:null).filter(Boolean);
 add('ljud per scen (på/av)',sb.length?'skiljer':'stammer',tl.map(s=>+s.sound).join(''),plan.tidskarta.map(r=>+r.ljud).join(''),sb.length?'skiljer i '+sb.join(','):'');
 // 3. Text
 const wt=tl.flatMap(s=>s.texts.map(t=>({k:s.id+'/'+t.id,text:norm(t.text),a:t.ut[0],b:t.ut[1],box:t.box,px:t.stil?.storlek_px}))),pt=plan.skarmtext.map(t=>({k:t.scen+'/'+t.id,text:norm(t.text),a:Math.round(t.start_s*M.fps),b:Math.round(t.slut_s*M.fps),box:t.box,px:t.stil?.storlek_px}));
 const wk=wt.map(t=>t.k).sort(),pk=pt.map(t=>t.k).sort();
 add('textlager: vilka texter finns',same(wk,pk)?'stammer':'skiljer',wk.join(','),pk.join(','));
 for(const field of ['text','a','b','box','px']){
  const diffs=[];for(const w of wt){const p=pt.find(x=>x.k===w.k);if(p&&!same(w[field],p[field]))diffs.push(`${w.k}: webb ${JSON.stringify(w[field])}, plan ${JSON.stringify(p[field])}`);}
  add(`text.${field==='a'?'start (ruta)':field==='b'?'slut (ruta)':field==='px'?'storlek_px':field}`,diffs.length?'skiljer':'stammer',`${wt.length} texter`,diffs.length?diffs.join('; ').slice(0,300):'lika');
 }
 // 4. Kamera
 for(const s of tl.filter(s=>s.camera)){
  const w=webbKamera(M,s),sc=plan.scener.find(x=>x.id===s.id);if(!sc||!ok.has(s.camera.id)){add(`kamera ${s.id}`,'ej_tillampad_av_kontraktet',JSON.stringify(w),'inte i planen');continue;}
  const p=planKamera(plan,grund,sc);
  if(!p){add(`kamera ${s.id}`,'ej_jamforbar','stativ',  'plan saknar kameranycklar');continue;}
  add(`kamera ${s.id}: brännvidd`,near(w.lens_faktor,p.lens_faktor,.02)?'stammer':'skiljer',`×${w.lens_faktor.toFixed(3)} (${w.lens_mm.toFixed(1)} mm)`,`×${p.lens_faktor.toFixed(3)} (${p.lens_mm.toFixed(1)} mm)`);
  add(`kamera ${s.id}: förskjutning från uppmätt`,near(w.forskjutning_m,p.forskjutning_m,.03)?'stammer':'skiljer',`${w.forskjutning_m.toFixed(3)} m`,`${p.forskjutning_m.toFixed(3)} m`,'avstånd mellan uppmätt kamera och stativkamera i meter; riktningen jämförs inte (olika koordinatramar)');
  add(`kamera ${s.id}: stilla under scenen`,p.rorelse_i_scenen_m<.005?'stammer':'skiljer','0 m (stativ)',`${p.rorelse_i_scenen_m.toFixed(3)} m`);
 }
 // 5. Kort/föremål
 for(const s of tl)for(const [name,p] of Object.entries(s.props)){
  if(!p)continue;const id=M.cardBindings?.[s.origin]?.[name]||`${s.origin}:${name}`;
  const base=initial(M).scenes.find(x=>x.id===s.id)?.props[name];const changed=!p.visible||(base&&p.asset!==base.asset);if(!changed)continue;
  const hit=edits.find(e=>['ta_bort_prop','byt_prop'].includes(e.op)&&(e.prop===id)&&(e.scen===s.id||e.scen==='alla'));
  const tillamp=hit&&ok.has(hit.id);
  const tg=hit?.op==='byt_prop'?(plan.tillgangar||[]).find(t=>t.id===id&&t.tillgang.id===p.asset):null;
  if(tillamp&&tg){add(`föremål ${id} i ${s.id}`,'stammer',`kort ${p.asset}`,`${tg.tillgang.id} (${tg.tillgang.kalla}, geometri ${tg.tillgang.geometri})`,'planen bär samma tillgång; 3D-geometri för kortet är inte byggd');continue;}
  add(`föremål ${id} i ${s.id}`,tillamp?'stammer_semantiskt':'ej_tillampad_av_kontraktet',p.visible?`byte till ${p.asset}`:'dolt (2D-kort: bord och mat)',tillamp?(plan.tillampat.find(e=>e.id===hit.id).andring||'tillämpad'):(rej.get(hit?.id)||'saknas'),tillamp?'samma id och scen, men olika sak: webben döljer ett fotokort, planen tar bort 3D-lådan med samma id':'');
 }
 // 6. Miljö
 for(const s of tl.filter(s=>s.venue)){
  const hit=edits.filter(e=>e.op==='byt_miljo'&&(e.scen===s.id||e.scen==='alla')).at(-1);
  const lb=(plan.lokalbyte||[]).find(x=>x.scen===s.id);
  if(hit&&ok.has(hit.id)&&lb){add(`miljö ${s.id}`,lb.tillgang_id===s.venue?'stammer':'skiljer',s.venue,`${lb.tillgang_id} (${lb.kalla}, geometri ${lb.geometri})`,'planen bär samma lokal; ingen plats är byggd av plåten');continue;}
  add(`miljö ${s.id}`,hit&&ok.has(hit.id)?'stammer_semantiskt':'ej_tillampad_av_kontraktet',s.venue,hit&&ok.has(hit.id)?'tillämpad':(rej.get(hit?.id)||'saknas'),hit&&ok.has(hit.id)?'':'webbens bakgrunder är plåtar ur klippen; kontraktets platsbank har andra id');
 }
 // 7. Rollnamn/helkroppston
 for(const [person,c] of Object.entries(state.cast)){
  const p=plan.personer.find(x=>x.id===person);
  if(c.color)add(`helkroppston ${person}`,p&&norm(p.farg).toLowerCase()===c.color.toLowerCase()?'stammer':'skiljer',c.color,p?.farg??'saknas');
  if(c.role)add(`rollnamn ${person}`,p&&p.roll===c.role?'stammer':'skiljer',c.role,p?.roll??'saknas');
 }
 // 8. Repliker
 for(const [id,text] of Object.entries(state.lines)){
  const t=(plan.tal||[]).find(x=>x.replik===id||x.id===id);
  add(`replik ${id}`,t?(norm(t.text)===norm(text)?'stammer':'skiljer'):'ej_jamforbar',text,t?t.text:'snabbvägen ger ingen talrad (tal syntetiseras inte)');
 }
 const c={stammer:0,stammer_semantiskt:0,skiljer:0,ej_tillampad_av_kontraktet:0,ej_jamforbar:0};for(const r of rows)c[r.status]=(c[r.status]||0)+1;
 const avvikelser=rows.filter(r=>!['stammer','stammer_semantiskt'].includes(r.status));
 return {rader:rows,antal:c,avvikelser,avvikelserN:avvikelser.length,jamforda:rows.length};
}
