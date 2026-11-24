"""Läsbar diagnos bredvid varje upplöst plan. Trösklarna är våra egna."""
from pathlib import Path
import numpy as np


def komplettera(plan, platser):
    from skymning import los
    from golvmatning import undersok
    import plats
    floors={i:pl['golv']['matning'] for i,pl in platser.items() if 'matning' in pl['golv']}
    if not floors:
        # Även äldre källor utan platsreferens får diagnostik. Ingen planändring.
        folder=Path(plan['matning']['kameror'][0]['spar_metrisk']['sokvag']).parent
        t=plats.ladda_tagning(folder.name,folder)
        floors['ensam']=undersok([t],{t['id']:dict(M=np.eye(4))},{(t['id'],pid):pid for pid in t['personer']})
        floors['ensam']['tillampad']=False
    plan['kvalitet']['golv_skala']=floors
    for s in plan.get('scener') or plan['matkamera']['scener']:
        for pm in s['personer']:
            if not pm.get('stod') or pm.get('skyddade_knan'):continue
            pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
            vis=next((v for f in floors.values() for v in f['fotsynlighet']
                      if v['ingest_id']==pid and (v['tagning'].lower()==s['id'].lower() or len(floors)==1 and len(f['per_tagning'])==1)),None)
            if vis:
                protected={str(v['ruta']):v['synliga_knan'] for v in vis['per_ruta'] if any(v.get('synliga_knan',[]))}
                if protected:pm['skyddade_knan']=protected
    plan['kvalitet']['skymning']=los(plan)
    from trostod import NAMN,BEN
    overrides=[]
    for s in plan.get('scener') or plan['matkamera']['scener']:
        for pm in s['personer']:
            if not pm.get('stod'):continue
            with np.load(pm['rorelse']) as seq:
                a=s['lokal_start'];b=a+s['ut'][1]-s['ut'][0]
                n=int((~seq['ben_synliga'][a:b]&seq['inom'][a:b]).sum()) if 'ben_synliga' in seq else 0
            names=[NAMN[i] for i in BEN] if n else []
            protected=pm.get('skyddade_knan',{})
            for side_index,side in enumerate('lr'):
                if protected and all(protected.get(str(i),[False,False])[side_index] for i in range(a,b)):
                    names=[name for name in names if not name.startswith(side+'_upleg')]
            overrides.append(dict(scen=s['id'],person=pm['id'],rutor=n,leder=names,
                                  skyddade_knalagen_rutor=sum(sum(v) for v in protected.values()),
                                  antagande='Dold benpose och hudens sula; fasta mått i ändrade segment. Synligt lår/knäläge behåller uppmätt längdvariation. Bäcken och överkropp skyddas.'))
    plan['kvalitet']['ledersattningar']=overrides


def skriv(plan, fil):
    q=plan['kvalitet'];occ=q.get('skymning',{});floors=q.get('golv_skala',{})
    rows=['# Kvalitet', '',
          'Detta är egna diagnostiska trösklar: bildfel median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal. Bra betyder att dessa kontroller passerar. Granska betyder osäkra antaganden eller konflikt. Dålig betyder att bildfelet passerar gränsen.', '',
          '| Scen | Bildfel median/p90 px | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |',
          '|---|---|---|---|---|---|']
    for sid in dict.fromkeys(r['scen'] for r in q['bildtrohet']['personer']):
        people=[r for r in q['bildtrohet']['personer'] if r['scen']==sid]
        err='/'.join(f'{max(p.get(k,0) for p in people):.2f}' for k in ('median_px','p90_px'))
        f=next(iter(floors.values()),None);shot=None
        if f:shot=next((s for s in f['per_tagning'] if s['tagning'].lower()==sid.lower()),f['per_tagning'][0])
        decision=shot['beslut'] if shot else {};spread=decision.get('spridning_m');span=decision.get('spann_m')
        fs=decision.get('status','saknas');conflict=decision.get('konflikt',True);scale=f.get('skala',{}) if f else {}
        applied=f.get('tillampad',False) if f else False
        floorlabel=f'{fs}, ±{spread*100:.1f} cm; spann {span*100:.1f} cm' if spread is not None else 'saknas'
        floorlabel+=f'; skala 1,0 {scale.get("status","saknas")}'
        if not applied:floorlabel+='; golv endast granskat'
        bef=[r for r in occ.get('fore',{}).get('per_del',[]) if r['scen']==sid];aft=[r for r in occ.get('efter',{}).get('per_del',[]) if r['scen']==sid]
        oc=f'{max([r["andel"] for r in bef] or [0])*100:.1f} → {max([r["andel"] for r in aft] or [0])*100:.1f} %'
        overrides=[r for r in q.get('ledersattningar',[]) if r['scen']==sid]
        joints='; '.join(f'{r["person"]}: {len(r["leder"])} i {r["rutor"]} rutor' for r in overrides) or '0'
        bad=any(r['flaggad'] for r in people);reasons=[]
        if bad:reasons.append('bildfel')
        if fs!='uppmatt':reasons.append('golv antaget')
        if conflict:reasons.append('golvcues oense')
        if scale.get('overens') is False:reasons.append('skalprior oense')
        actions=[r for r in occ.get('atgarder',[]) if r['scen']==sid]
        if actions:reasons.append('mall utelämnad: '+', '.join(r['del_id'] for r in actions))
        if any(r['flaggad'] for r in aft):reasons.append('skymningsrest')
        status='dålig' if bad else 'granska' if reasons else 'bra'
        rows.append(f'| {sid} | {err} | {floorlabel} | {joints} | {oc} | {status}: {", ".join(reasons) or "diagnostiken passerar"} |')
    rows+=['', 'Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.', '',
           'Skymning är provandel av källmask inom personrutan, med närmaste MHR70-punkts djup; ingen exakt hudarea. Var sjätte och sista rutan kontrolleras före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.']
    Path(fil).with_name('kvalitet.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
