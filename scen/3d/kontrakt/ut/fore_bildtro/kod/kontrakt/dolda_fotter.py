"""Antagen likformig kroppsskala när ingen egen fot mäter ett belagt golv."""
from __future__ import annotations

from pathlib import Path
import numpy as np

GRANS = (0.92, 1.08)
F = np.diag([1., -1., -1.])


def berattigad(synlig_tillforlitlig_fot, golv_kallor):
    return not bool(synlig_tillforlitlig_fot) and bool(golv_kallor)


def begransa_faktor(faktor):
    return float(np.clip(float(faktor),*GRANS))


def _langd(pose, frames):
    """Robust MHR-höjd i modellens lodräta Y-led, före/efter faktor."""
    return float(np.median(np.ptp(np.asarray(pose)[frames, :, 1] / 100., axis=1)))


def _golv_kallor(shot, eget_ingest_id):
    selected=[c for c in shot.get('beslut',{}).get('cues',[]) if c.get('anvand')]
    other=[c for c in selected if str(c.get('ingest_id',''))!=str(eget_ingest_id)]
    if shot.get('beslut',{}).get('status') not in ('uppmatt','modellbedomd') or not other:return []
    return [dict(cue=c['cue'],familj=c['familj'],status=c.get('status',shot['beslut']['status']),
                 ingest_id=c.get('ingest_id'),varde_m=c['varde_m']) for c in other]


def _stabila_stodfaktorer(t, M, pid, floor):
    """En stabil stödfot per ruta; pendelfoten får aldrig vinna på lägsta Z."""
    from metrisk import las
    from trosula import per_fot
    S=las(t['mapp']/f'sekvens_{pid}.npz',beslut={})
    frames=np.flatnonzero(S['inom']);V=t['V'];G=M[:3,:3]@t['G']
    if len(frames)<5:return None
    q=np.einsum('ij,njk,kl->nil',G,V['kam_R'][frames],F)
    cam=V['kam_C'][frames]@G.T+M[:3,3]
    trans=(V['kam_C'][frames]+np.einsum('nij,nj->ni',V['kam_R'][frames],S['cam_t'][frames]))@G.T+M[:3,3]
    soles=np.empty((len(frames),2))
    for j,f in enumerate(frames):
        pair=per_fot(S['pose'][f],q[j],trans[j]);soles[j]=[pair['l'],pair['r']]
    speed=np.full_like(soles,np.inf)
    speed[1:]=np.abs(np.diff(soles,axis=0))
    stable=np.zeros_like(soles,dtype=bool);half=2
    for j in range(half,len(frames)-half):
        if np.all(np.diff(frames[j-half:j+half+1])==1):
            stable[j]=np.ptp(soles[j-half:j+half+1],axis=0)<=.025
    chosen=[]
    for j in range(len(frames)):
        sides=np.flatnonzero(stable[j]&(speed[j]<=.012))
        if not len(sides):continue
        side=int(sides[np.argmin(speed[j,sides])])
        if len(sides)==2 and abs(speed[j,0]-speed[j,1])<.002:side=int(np.argmin(soles[j]))
        den=soles[j,side]-cam[j,2]
        if abs(den)<1e-8:continue
        factor=(floor-cam[j,2])/den
        if np.isfinite(factor) and .5<factor<1.5:
            chosen.append((j,side,float(factor)))
    if len(chosen)<5:return None
    factors=np.array([x[2] for x in chosen]);required=float(np.median(factors))
    return dict(S=S,frames=frames,cam=cam,soles=soles,chosen=chosen,required=required,
                spridning=float(np.percentile(factors,90)-np.percentile(factors,10)),
                langd=_langd(S['pose'],frames))


def besluta(ts, reg, roles, prov, matning, scenes, floor=0.):
    """Beräkna och fäst beslut; ändrar inga arrayer eller filer på disk."""
    visibility={(v['tagning'],str(v['ingest_id'])):v for v in prov.get('fotsynlighet',[])}
    shots={s['tagning']:s for s in prov.get('per_tagning',[])}
    scene_by_tag={r['tagning']:r['scen'] for p in matning.get('platser',[]) for r in p['registreringar']}
    observations=[]
    for t in ts:
        shot=shots[t['id']]
        for pid in t['personer']:
            role=roles[t['id'],pid];vis=visibility.get((t['id'],str(pid)),{})
            seen=bool(vis.get('anvandbara_rutor'))
            sources=_golv_kallor(shot,pid)
            entry=dict(tagning=t['id'],scen=scene_by_tag.get(t['id']),ingest_id=str(pid),person=role,
                       synlig_tillforlitlig_fot=seen,golv_satt_av=sources)
            if not berattigad(seen,sources):
                observations.append(entry);continue
            support=_stabila_stodfaktorer(t,reg[t['id']]['M'],pid,floor)
            if support is None:
                entry.update(status='ej_tillampad',orsak='Ingen stabil stödfotsperiod kunde skiljas från gång/pendelfot.')
            else:entry['stod']=support
            observations.append(entry)
    visible_lengths={}
    for o in observations:
        if not o['synlig_tillforlitlig_fot']:continue
        t=next(t for t in ts if t['id']==o['tagning']);pid=o['ingest_id']
        from metrisk import las
        S=las(t['mapp']/f'sekvens_{pid}.npz',beslut={});frames=np.flatnonzero(S['inom'])
        if len(frames):visible_lengths.setdefault(o['person'],[]).append((o['tagning'],_langd(S['pose'],frames)))
    reports=[]
    for o in observations:
        support=o.pop('stod',None)
        if support is None:
            if not o['synlig_tillforlitlig_fot'] and o['golv_satt_av']:
                reports.append(dict(o,status=o.get('status','ej_tillampad'),orsak=o.get('orsak','Stabil stödperiod saknas.')))
            continue
        refs=[x for x in visible_lengths.get(o['person'],[]) if x[0]!=o['tagning']]
        required=support['required'];method='golvkontakt under stabil stödperiod'
        if refs:
            reference=float(np.median([x[1] for x in refs]));wanted=reference/support['langd']
            method='längd från annan tagning med synlig, tillförlitlig fot'
        else:reference=None;wanted=required
        applied=begransa_faktor(wanted)
        residuals=[]
        for j,side,_ in support['chosen']:
            residuals.append(support['cam'][j,2]+applied*(support['soles'][j,side]-support['cam'][j,2])-floor)
        report=dict(o,status='antagen',tillampad=bool(abs(applied-1.)>1e-12),faktor=applied,
                    begard_faktor=float(wanted),golvfaktor=float(required),faktor_grans=list(GRANS),
                    grans_traffad=bool(abs(applied-wanted)>1e-12),metod=method,
                    stabila_stodrutor=len(support['chosen']),faktorspridning_p10_p90=support['spridning'],
                    langd_fore_m=support['langd'],langd_efter_m=support['langd']*applied,
                    referenslangd_m=reference,referenstagningar=[x[0] for x in refs],
                    sula_fore_m=float(np.median([support['soles'][j,s]-floor for j,s,_ in support['chosen']])),
                    sula_efter_m=float(np.median(residuals)),
                    kvarstaende_konflikt=bool(abs(np.median(residuals))>.01),
                    orsak='Likformig skala kring varje bildrutas kameracentrum; kropp och avstånd tillsammans. Aldrig mätning.')
        reports.append(report)
        for pm in matning['personer']:
            if pm.get('scen') in (None,o['scen']) and str(pm.get('ingest_id',pm['person']))==o['ingest_id'] and pm['person']==o['person']:
                pm['dolda_fotter']=dict(report)
    prov['dolda_fotter']=reports
    return reports
