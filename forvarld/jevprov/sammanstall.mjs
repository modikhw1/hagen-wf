// Sammanställ sparade svar utan några nätanrop.
import fs from 'node:fs';
import path from 'node:path';
import {DIR, OUT, DATA, read, write, judge, quantile} from './prov.mjs';
const rows=fs.readdirSync(path.join(OUT,'rutter')).filter(n=>n.startsWith('test-')).map(n=>({...read(path.join(OUT,'rutter',n)),run:Number(n.split('-')[1])}));
if(rows.length!==180)throw new Error(`Behöver 180 resultat, hittade ${rows.length}`);
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const pct=a=>100*mean(a.map(Number));
const sig=r=>JSON.stringify({families:[...r.families].sort(),parts:[...r.parts].sort()});
const results={frozen:read(path.join(OUT,'fryst.json')),development:read(path.join(OUT,'utveckling.json')).summary,definitions:{family:'family_pct kräver att alla valda familjer är accepterade. family_hit_pct kräver bara minst en träff. Utvecklingens frysta urval använde träffmåttet; det ändrades inte efter test.',parts:'Exakt mängd; A eller B accepteras för t3/t12/t14. Props accepteras också för t15. Ingen annan efterhandsutvidgning.',parts_any:'Minst en rätt del; tomt facit räknas rätt endast med tomt svar. Separat överlapp på de 19 icke-tomma fallen redovisas också.',oklar:'Positivt facit för t17 och t20. t20:s tillåtna scen.ordning ger rätt familj men räknas som missad oklar.',latency:'Väggtid från första anropets start till sista svaret, inklusive lokal kod och journalföring; sekventiella anrop, ingen samtidighet. Kvantiler: närmaste rang.',cost:'0,04 USD per miljon input_tokens, pris från offentliga listningar enligt uppdraget; inte från API och inte verifierat via annan nättrafik. Endast inputkostnad.',stability:'Andel av de 20 meningarna med identisk familjemängd, delmängd respektive båda i alla tre omgångarna.'},strategies:{}};
for(const strategy of ['a','b','c']) {
  const rs=rows.filter(r=>r.strategy===strategy);
  const scored=rs.map(r=>({...r,judgement:judge(r,DATA.test.find(t=>t.id===r.id))}));
  const groups=DATA.test.map(t=>scored.filter(r=>r.id===t.id).sort((a,b)=>a.run-b.run));
  const positive=scored.filter(r=>r.judgement.oklar_expected),negative=scored.filter(r=>!r.judgement.oklar_expected);
  const summary={n:rs.length,family_correct:scored.filter(r=>r.judgement.family_all).length,family_pct:pct(scored.map(r=>r.judgement.family_all)),family_hit_pct:pct(scored.map(r=>r.judgement.family)),parts_exact_pct:pct(scored.map(r=>r.judgement.parts_exact)),parts_any_pct:pct(scored.map(r=>r.judgement.parts_any)),parts_overlap_nonempty_pct:pct(scored.filter(r=>DATA.test.find(t=>t.id===r.id).delar.length).map(r=>r.judgement.parts_any)),oklar:{true_positive:positive.filter(r=>r.judgement.oklar).length,positive_n:positive.length,false_positive:negative.filter(r=>r.judgement.oklar).length,negative_n:negative.length},latency_median_ms:quantile(rs.map(r=>r.ms),.5),latency_p90_ms:quantile(rs.map(r=>r.ms),.9),under_second_pct:pct(rs.map(r=>r.ms<1000)),calls_per_sentence:mean(rs.map(r=>r.calls)),tokens_per_sentence:mean(rs.map(r=>r.input_tokens)),cost_usd_per_1000:mean(rs.map(r=>r.input_tokens))*.00004,stability:{family_pct:pct(groups.map(g=>new Set(g.map(r=>[...r.families].sort().join('|'))).size===1)),parts_pct:pct(groups.map(g=>new Set(g.map(r=>[...r.parts].sort().join('|'))).size===1)),both_pct:pct(groups.map(g=>new Set(g.map(sig)).size===1)),pairwise_both_pct:pct(groups.flatMap(g=>[sig(g[0])===sig(g[1]),sig(g[0])===sig(g[2]),sig(g[1])===sig(g[2])]))},per_run:[1,2,3].map(run=>{const g=scored.filter(r=>r.run===run);return {run,family_pct:pct(g.map(r=>r.judgement.family_all)),family_hit_pct:pct(g.map(r=>r.judgement.family)),parts_exact_pct:pct(g.map(r=>r.judgement.parts_exact)),median_ms:quantile(g.map(r=>r.ms),.5),p90_ms:quantile(g.map(r=>r.ms),.9)};}),errors:groups.filter(g=>g.some(r=>!r.judgement.family_all||!r.judgement.parts_exact||r.judgement.oklar!==r.judgement.oklar_expected)).map(g=>({id:g[0].id,mening:g[0].mening,expected:DATA.test.find(t=>t.id===g[0].id),answers:g.map(r=>({run:r.run,families:r.families,parts:r.parts,...r.judgement}))})),rows:scored};
  if(strategy==='c') {
    const good=scored.filter(r=>r.judgement.family),bad=scored.filter(r=>!r.judgement.family);
    // AUC: sannolikheten att ett fel har mindre marginal än ett rätt svar, lika ger 0,5.
    let pairs=0,wins=0;for(const e of bad)for(const g of good){pairs++;wins+=e.margin<g.margin?1:e.margin===g.margin?.5:0;}
    summary.margin={correct_n:good.length,error_n:bad.length,correct_median:quantile(good.map(r=>r.margin),.5),error_median:quantile(bad.map(r=>r.margin),.5),error_detection_auc:pairs?wins/pairs:null,bins:[[0,.25],[.25,.5],[.5,1],[1,Infinity]].map(([lo,hi])=>{const g=scored.filter(r=>r.margin>=lo&&r.margin<hi);return {lo,hi:Number.isFinite(hi)?hi:null,n:g.length,errors:g.filter(r=>!r.judgement.family).length};})};
  }
  results.strategies[strategy]=summary;
}
const calls=fs.readFileSync(path.join(OUT,'anropslogg.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
results.total_calls=calls.length;
results.calls_by_phase={size:calls.filter(c=>c.tag.startsWith('storlek')).length,development:calls.filter(c=>c.tag.startsWith('utv')).length,test:calls.filter(c=>c.tag.startsWith('test')).length,concrete:calls.filter(c=>c.tag.startsWith('konkret')).length};
const responses=calls.map(c=>read(path.join(OUT,'anrop',c.tag+'.json')));
results.total_input_tokens=responses.reduce((s,r)=>s+(r.raw?.usage?.input_tokens??0),0);
results.total_estimated_input_cost_usd=results.total_input_tokens*.04/1e6;
results.response_models=[...new Set(responses.map(r=>r.raw?.model))];
results.http_failures=responses.filter(r=>r.status!==200).map(r=>r.tag);
const compiled=path.join(OUT,'konkret','sammanfattning.json');if(fs.existsSync(compiled))results.concrete=read(compiled);
write(path.join(DIR,'resultat.json'),results);
console.log(JSON.stringify(Object.fromEntries(Object.entries(results.strategies).map(([s,r])=>[s,Object.fromEntries(Object.entries(r).filter(([k])=>!['rows','errors'].includes(k)))])),null,2));
console.log('Totalt antal anrop: '+results.total_calls);
