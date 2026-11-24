// The same deterministic state reducer is used by browser and server. No I/O.
export const clone=x=>structuredClone(x);
export function initial(M){
 return {scenes:M.scenes.map(s=>({id:s.id,origin:s.id,a:s.source[0],b:s.source[1],sound:true,camera:null,venue:null,props:{foreground:s.layers?.foreground?{asset:s.id+':foreground',visible:true}:null,nearForeground:s.layers?.nearForeground?{asset:s.id+':nearForeground',visible:true}:null},texts:clone(M.text.filter(t=>t.scen===s.id))})),cast:{},lines:{}};
}
// Kontraktets standard för en ny text (skarmtext.py:edit) och för stativkamerans synvinkel (kompilera.py:kameranycklar: fov 40 grader om CM inte anger någon).
export const TEXT_STANDARD={box:[46,737,484,80],stil:{font:'arialbd.ttf',storlek_px:30,justering:'vanster',farg:'#ffffff',kontur_farg:'#000000',kontur_px:2}};
export const STATIV_FOV_STANDARD=40;
export function stativLins(M,camera){const fov=camera.fov_grader??STATIV_FOV_STANDARD;return 1024/576*M.cameras.sensor_bredd_mm/(2*Math.tan(fov*Math.PI/360));}
export function timeline(state){let f=0;return state.scenes.map(s=>{const r={...s,ut:[f,f+s.b-s.a]};f=r.ut[1];return r;});}
export function sourceMap(state){return state.scenes.flatMap(s=>Array.from({length:s.b-s.a},(_,i)=>s.a+i));}
export function propId(M,s,name){return M.cardBindings?.[s.origin]?.[name]||`${s.origin}:${name}`;}
export function apply(state,e,M){
 const n=clone(state),s=n.scenes.find(s=>s.id===e.scen),need=()=>{if(!s)throw Error('Scenen finns inte: '+e.scen);return s;};
 if(e.op==='ta_bort_scen'){need();if(n.scenes.length===1)throw Error('Sista scenen kan inte tas bort.');n.scenes=n.scenes.filter(x=>x!==s);}
 else if(e.op==='trimma_scen'){need();if(e.lage==='stracka'||e.tid)throw Error('Tidssträckning/händelseankare saknar förhandsvisning.');let a=e.start_s==null?s.a:Math.round(e.start_s*M.fps),b=e.slut_s==null?s.b:Math.round(e.slut_s*M.fps);if(!(s.a<=a&&a<b&&b<=s.b)||(a===s.a&&b===s.b))throw Error('Tom, oförändrad eller för stor trimning.');if(e.lage==='replik_sakert'&&M.lines.some(r=>(r.ord?.length?r.ord:[r]).some(w=>[a/M.fps,b/M.fps].some(t=>w.start_s<t&&t<w.slut_s))))throw Error('Trimningen skulle klippa ett ord.');s.a=a;s.b=b;if(s.camera){s.cameraSource=[a,b];s.cameraHiddenProps=Object.entries(s.props).filter(([,p])=>p&&!p.visible).map(([name])=>propId(M,s,name));}}
 else if(e.op==='flytta_scen'||e.op==='duplicera_scen'){
  need();if(e.op==='flytta_scen'&&e.efter===s.id)throw Error('Kan inte flytta efter sig själv.');
  if(e.efter&&!n.scenes.some(x=>x.id===e.efter))throw Error('Scenen efter finns inte.');
  let x=s;if(e.op==='duplicera_scen'){if(n.scenes.some(x=>x.id===e.ny_id))throw Error('Scen-id finns redan.');x=clone(s);x.id=e.ny_id;x.sound=e.med_ljud;x.texts=x.texts.map(t=>({...t,id:t.id.split('@')[0]+'@'+x.id}));}else n.scenes.splice(n.scenes.indexOf(s),1);
  const after=e.efter||(e.op==='duplicera_scen'?s.id:null);n.scenes.splice(after?n.scenes.findIndex(x=>x.id===after)+1:0,0,x);
 }
 else if(e.op==='skarmtext'){
  need();const i=s.texts.findIndex(t=>t.id===e.skarmtext_id);
  if(e.atgard==='ta_bort'){if(i<0)throw Error('Texten finns inte.');s.texts.splice(i,1);}
  else{if(e.atgard==='byt'&&i<0||e.atgard==='lagg_till'&&i>=0)throw Error('Ogiltigt text-id.');let t=i>=0?s.texts[i]:{id:e.skarmtext_id,scen:s.id,text:'',ut:[s.a,s.b],box:clone(TEXT_STANDARD.box),stil:clone(TEXT_STANDARD.stil)};if(e.text!=null)t.text=e.text;if(e.box)t.box=clone(e.box);if(e.stil&&typeof e.stil==='object')Object.assign(t.stil,e.stil);if(e.start_s!=null)t.ut[0]=Math.round(e.start_s*M.fps);if(e.slut_s!=null)t.ut[1]=Math.round(e.slut_s*M.fps);if(i<0)s.texts.push(t);}
 }
 else if(e.op==='casta'){if(!M.scenes.some(s=>s.person.person===e.person))throw Error('Personen finns inte.');if(Object.entries(e.utseende).some(([k,v])=>k!=='troja_farg'&&v!=null)||e.rost)throw Error('Bara helkroppston och rollnamn kan förhandsvisas.');n.cast[e.person]={...n.cast[e.person],color:e.utseende.troja_farg||n.cast[e.person]?.color,role:e.kundroll.namn};}
 else if(e.op==='renderkamera'){need();if(!['stativ','folj_uppmatt'].includes(e.lage))throw Error('Bara uppmätt/stativkamera i detta paket.');const person=M.scenes.find(x=>x.id===s.origin).person.person;if(e.mal&&!(e.mal.typ==='person'&&e.mal.id===person))throw Error('Kameramålet finns inte i scenens kroppspaket.');s.camera=e.lage==='stativ'?clone(e):null;s.cameraSource=[s.a,s.b];s.cameraHiddenProps=Object.entries(s.props).filter(([,p])=>p&&!p.visible).map(([name])=>propId(M,s,name));}
 else if(e.op==='byt_miljo'){if(!M.backdrops?.some(b=>b.id===e.rum.tillgang_id))throw Error('Bakgrunden finns inte i paketbanken.');const selected=e.scen==='alla'?n.scenes:[need()];for(const x of selected)x.venue=e.rum.tillgang_id;}
 else if(['ta_bort_prop','byt_prop','lagg_till_prop'].includes(e.op)){
  const selected=e.scen==='alla'?n.scenes:[need()];let changed=false;
  for(const x of selected){let name=['foreground','nearForeground'].find(k=>propId(M,x,k)===(e.prop||e.ny_id));if(!name||!x.props[name]){if(e.scen==='alla')continue;throw Error('Inget separat kort finns för detta föremål.');}
   let p=x.props[name];if(e.op==='ta_bort_prop'){if(!p.visible)throw Error('Kortet är redan dolt.');p.visible=false;}
   else if(e.op==='lagg_till_prop'){if(p.visible)throw Error('Kortet visas redan.');p.visible=true;}
   else {if(!M.scenes.some(s=>Object.entries(s.layers||{}).some(([k])=>k===e.ny_typ)))throw Error('Korttypen finns inte.');const asset=e.tillgang_id||p.asset;if(!M.scenes.some(s=>asset===s.id+':'+e.ny_typ&&s.layers?.[e.ny_typ]))throw Error('Kortbilden finns inte.');p.asset=asset;p.visible=true;}changed=true;
  }if(!changed)throw Error('Inget befintligt kort träffades.');
 }
 else if(e.op==='byt_replik'){const r=M.lines.find(r=>r.id===e.replik);if(!r)throw Error('Repliken finns inte.');if(e.tidspolicy!=='samma_lucka')throw Error('Tal som förlänger scenen kräver offlinearbete.');n.lines[e.replik]=e.text;for(const x of n.scenes)for(const t of x.texts)if(t.typ==='undertext'&&t.replik===e.replik)t.text=e.text;}
 else throw Error('Operationen kan inte visas ännu: '+e.op);
 return n;
}
export function describe(e){const sn=e.scen==='alla'?'alla scener':e.scen;switch(e.op){
 case 'renderkamera':return `Kameran i ${sn}: ${e.lage==='stativ'?'stativ':'uppmätt'}, ${e.inramning==='nara'?'närmare '+(e.mal?.id||'personen'):e.inramning==='hel'?'vidare':'samma utsnitt'}`;
 case 'skarmtext':return `Text i ${sn}: ${e.atgard==='ta_bort'?'borttagen':e.text!=null?'”'+e.text+'”':'ändrad stil'}`;
 case 'casta':return `${e.person}: ${e.utseende.troja_farg||e.kundroll.namn} (helkroppston)`;
 case 'byt_miljo':return `Bakgrund i ${sn}: ${e.rum.beskrivning||e.rum.tillgang_id}`;
 case 'ta_bort_scen':return `${sn} borttagen`;
 case 'trimma_scen':return `${sn} trimmad till ${e.start_s??'början'}–${e.slut_s??'slutet'} s på källklockan`;
 case 'flytta_scen':return `${sn} flyttad ${e.efter?'efter '+e.efter:'först'}`;
 case 'duplicera_scen':return `${sn} kopierad som ${e.ny_id}${e.med_ljud?' med ljud':' utan ljud'}`;
 case 'ta_bort_prop':return `Kort ${e.prop} dolt i ${sn} (bord och mat tillsammans)`;
 case 'lagg_till_prop':return `Kort ${e.ny_id} visas i ${sn}`;
 case 'byt_prop':return `Kort ${e.prop} bytt till ${e.tillgang_id} i ${sn}`;
 case 'byt_replik':return `${e.replik}: ”${e.text}” — undertexten byts (som i planen); talet syntetiseras i ett eget steg, här tystas originaltalet och munnen fryses`;
 default:return e.op;}}
