// Konkret steg efter det frysta testet: enbart val bland slutna, lagliga alternativ.
import fs from 'node:fs';
import path from 'node:path';
import {ROOT,OUT,K,DATA,read,write,api} from './prov.mjs';
const config=read(path.join(OUT,'fryst.json'));
const sem=K.semantik;
const schema=read(path.join(ROOT,'scen/3d/kontrakt/regi.schema.json'));
const q=(instructions,criteria)=>({type:'choice',instructions,criteria});
const sceneOptions=Object.fromEntries(sem.scener.map(s=>[s.id,`${s.id}: ${s.funktion??'okänd funktion'}, ${s.personer.join(', ')}, ${s.start_s}–${s.slut_s} s`]));
const lineOptions=Object.fromEntries(sem.repliker.map(r=>[r.id,`${r.id}, ${r.talare}, ${r.scen}: ${r.text}`]));
const personOptions=Object.fromEntries(sem.personer.filter(p=>['A','B','C'].includes(p.id)).map(p=>[p.id,`${p.id}: ${p.roll}`]));
const rooms=fs.readdirSync(path.join(ROOT,'scen/3d/kontrakt/rumsmall')).filter(n=>n.endsWith('.json')&&!['rumsmall.schema.json','lokalkoder.json'].includes(n)).map(n=>read(path.join(ROOT,'scen/3d/kontrakt/rumsmall',n)));
const base=()=>({schema_version:'regi/1',kalla:{klipp_id:K.klipp.id,sha256:K.klipp.sha256,revision:K.revision},edits:[],utdata:{fps_taljare:30,fps_namnare:1,bredd:576,hojd:1024,stil_ref:null,ljudpolicy:'original',render_backend:'blender_mhr'},ramar:{bevara_beats:[],bevara_klippoffset_s:null,tillat_retiming:false,max_talfaktor:1.15}});
const cases=[
  {id:'t1',family:'kamera.stabilisera',questions:{scen:q('Vilken enda scen avses med början?',sceneOptions),person:q('Vilken person är kamerans mål där?',personOptions),lage:q('Välj kamerans läge för att minska skakning.',Object.fromEntries(schema.$defs.renderkamera.properties.lage.enum.map(x=>[x,x])))},build:a=>[{op:'renderkamera',scen:a.scen,kamera_id:'jev_t1',lage:a.lage,mal:{typ:'person',id:a.person,punkt:'huvud'}}]},
  {id:'t2',family:'kamera.utsnitt',questions:{replik:q('Vilken replik är den sista grejen han säger?',lineOptions),person:q('Vem säger den sista grejen?',personOptions),scen:q('Vilken scen ska få närmare kamera?',sceneOptions),inramning:q('Vilket utsnitt önskas?',Object.fromEntries(schema.$defs.renderkamera.properties.inramning.enum.filter(Boolean).map(x=>[x,x])))},build:a=>[{op:'renderkamera',scen:a.scen,kamera_id:'jev_t2',lage:'stativ',inramning:a.inramning,mal:{typ:'person',id:a.person,punkt:'huvud'}}]},
  {id:'t5',family:'plats.byt',questions:{rum:q('Vilken verklig mall i banken motsvarar begärd lokal?',Object.fromEntries(rooms.map(r=>[r.id,r.beskrivning]))),scen:q('Vilken omfattning gäller ett platsbyte för klippet?',{alla:'Alla scener',...sceneOptions})},build:a=>[{op:'byt_miljo',scen:a.scen,rum:{kalla:'bank',tillgang_id:a.rum,rumsmall_id:a.rum,ord:[],beskrivning:null}}]},
  {id:'t11',family:'scen.ordning',questions:{scen:q('Vilken scen anges som punchline i källan?',sceneOptions),efter:q('Var ska den valda scenen placeras för att börja med den?',{forst:'Först, före alla andra scener',...sceneOptions})},build:a=>[{op:'flytta_scen',scen:a.scen,efter:a.efter==='forst'?null:a.efter}]},
  {id:'t13',family:'prop.andra',questions:{prop:q('Vilket befintligt prop-id är maten som ska tas bort? Välj saknas om inget beskriver mat. Gissa inte ett bord.',{...Object.fromEntries(sem.props.map(p=>[p.id,p.typ+' '+p.etikett])),saknas:'Ingen mat är identifierad bland källans props'}),scen:q('Vilken omfattning gäller att ta bort maten från bordet?',{alla:'Alla scener',...sceneOptions})},build:a=>[{op:'ta_bort_prop',scen:a.scen,prop:a.prop==='saknas'?'PLATSHALLARE:mat':a.prop}]},
];
// Valet täcker kamera, rumsbank, ordning och befintliga props; t13 prövar uttryckligen saknat mål.
const selected=[];
for(const c of cases) {
  const item=DATA.test.find(t=>t.id===c.id);
  const route=read(path.join(OUT,'rutter',`test-1-${c.id}-b.json`));
  if(!route.families.includes(c.family)) {selected.push({id:c.id,mening:item.mening,route,skipped:'Den frysta routningen valde en annan familj; ingen ändring byggs.'});continue;}
  const res=await api('konkret-'+c.id,config.state+'\nCM: '+item.mening,c.questions);
  const a=Object.fromEntries(Object.entries(res.raw.answers).map(([k,v])=>[k,v.choice]));
  const regi=base();regi.edits=c.build(a).map((e,i)=>({id:'jev_'+c.id+'_'+i,ursprung:{typ:'cm'},...e}));
  write(path.join(OUT,'konkret',c.id,'regi.json'),regi);
  selected.push({id:c.id,mening:item.mening,routing_strategy:'b',routing_run:1,route:{families:route.families,parts:route.parts},answers:a,edits:regi.edits,selection_ms:res.ms,input_tokens:res.raw.usage.input_tokens,note:c.id==='t13'?'PLATSHALLARE:mat är schemats explicita markör för saknat mål, inte ett påhittat identifierat prop.':null});
}
write(path.join(OUT,'konkret','val.json'),selected);
console.log(JSON.stringify(selected,null,2));
