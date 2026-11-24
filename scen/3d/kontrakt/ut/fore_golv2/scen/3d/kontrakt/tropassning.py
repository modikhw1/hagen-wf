"""Passa mallens höjder mot skyddade bäcken och stilla handleder."""
import copy
import numpy as np
from trohet import gravitation, F, IX
from trostod import matt, sitt_hojd

BORD_INTERVALL_M=(.72,.76)  # Prior: vanligt restaurangbord; inte en mätning.


def _anpassa_utan_cache(k, matning, platser):
    platser=copy.deepcopy(platser);samling={};lengths={};rapport=[]
    for sk in k['semantik']['scener']:
        pl=platser.get(sk.get('plats_id'))
        if not pl or not pl.get('rumsmall'):continue
        reg=next(r for p in matning['platser'] if p['id']==sk['plats_id'] for r in p['registreringar'] if r['scen']==sk['id'])
        M=np.array(reg['till_plats']['matris'])
        kam=next(c for c in matning['kameror'] if c['id']==sk['kamera']);V=np.load(kam['spar_metrisk']['sokvag']);G=M[:3,:3]@gravitation(V)
        bindings={b['person']:b['ankare'] for b in sk.get('bindningar',[])}
        for pm in matning['personer']:
            if pm.get('scen') not in (None,sk['id']) or pm['person'] not in bindings:continue
            S=np.load(pm['rorelse']['sokvag']);indices=np.where(S['inom'])[0]
            poses=S['pose'][indices];lengths.setdefault(pm['person'],[]).append(poses)
            Q=np.einsum('ij,njk,kl->nil',G,V['kam_R'][indices],F)
            T=(V['kam_C'][indices]+np.einsum('nij,nj->ni',V['kam_R'][indices],S['cam_t'][indices]))@G.T+M[:3,3]
            X=np.einsum('nij,ntj->nti',Q,poses[:,:,:3]/100)+T[:,None]
            samling.setdefault((sk['plats_id'],bindings[pm['person']]),[]).append(dict(scen=sk['id'],person=pm['person'],x=X,rutor=indices.tolist()))
    lengths={pid:matt(np.concatenate(v)) for pid,v in lengths.items()}
    for plid,pl in platser.items():
        if not pl.get('rumsmall'):continue
        rum=pl['rumsmall'];nya=[]
        for a in rum['ankare']:
            obs=samling.get((plid,a['id']),[])
            if a['typ']!='sate' or not obs:continue
            hip=np.median(np.concatenate([o['x'][:,IX['root']] for o in obs]),axis=0)
            floor=a['pos_m'][2];fit=sitt_hojd(float(hip[2]-floor),a.get('backen_over_sate_m',.11))
            d=next(d for d in rum['delar'] if d['id']==a['del']);old=d['matt_m'][2]
            d['matt_m'][2]=fit['hojd_m'];d['hojdpassning']=fit
            for an in d['ankare']:
                if an['typ']=='sate':an['sate_hojd_m']=fit['hojd_m']
            a['sate_hojd_m']=fit['hojd_m']
            a['backen_over_sate_m']=fit['backen_over_sits_m']
            for an in d['ankare']:
                if an['typ']=='sate':an['backen_over_sate_m']=fit['backen_over_sits_m']
            seat=dict(typ='sate',ankare=a['id'],person=obs[0]['person'],backen_median_z_m=float(hip[2]),fore_m=old,**fit)
            nya.append(seat)
            # Låg, stilla handled är svag kontakt-evidens, aldrig rätt att flytta handen.
            candidates=[];allw=[]
            for o in obs:
                wrists=o['x'][:,[IX['l_wrist'],IX['r_wrist']]];allw.extend(wrists[:,:,2].flatten())
                for side in range(2):
                    w=wrists[:,side];window=12  # Antaget: minst 0,4 s vid 30 fps.
                    for start in range(max(0,len(w)-window+1)):
                        seg=w[start:start+window]
                        if np.ptp(seg[:,2])<=.03 and np.linalg.norm(np.ptp(seg[:,:2],axis=0))<=.08:
                            candidates.append(dict(scen=o['scen'],sida='l' if side==0 else 'r',lokala_rutor=[o['rutor'][start],o['rutor'][start+window-1]+1],hojd_m=float(np.median(seg[:,2]))))
            tables=[d for d in rum['delar'] if d['typ']=='bord' and d.get('folj_ankare')==a['id']]
            for table in tables:
                old=table['matt_m'][2];ev=None
                if candidates:
                    # Högre stabila lägen kan vara gester. Lägsta stabila läget är evidensen.
                    ev=min(candidates,key=lambda v:v['hojd_m']);wanted=ev['hojd_m']-floor
                    height=float(np.clip(wanted,*BORD_INTERVALL_M))
                    table['matt_m'][2]=height
                    status='antagen';method='Stilla handled är uppmätt, bordkontakt antagen. Klippt mot bordprior 72–76 cm; rest mot handled loggas. Händer och bäcken flyttas aldrig.'
                else:
                    height=old;status='mall';method='Ingen tillräckligt stilla handled; mallhöjd behålls.'
                gaps=np.array(allw)-(floor+height)
                tr=dict(typ='bord',del_id=table['id'],person=obs[0]['person'],fore_m=old,hojd_m=height,intervall_m=list(BORD_INTERVALL_M),
                        status=status,metod=method,evidens=ev,stabila_fonster=len(candidates),
                        handledsgap_m=dict(min=float(gaps.min()),median=float(np.median(gaps)),p90=float(np.percentile(gaps,90))))
                tr['evidens_rest_m']=float(ev['hojd_m']-floor-height) if ev else None
                tr['prior_konflikt']=bool(ev and abs(tr['evidens_rest_m'])>.03)
                table['hojdpassning']=tr;nya.append(tr)
                tr['per_scen']=[]
                for o in obs:
                    gap=o['x'][:,[IX['l_wrist'],IX['r_wrist']],2]-(floor+height)
                    tr['per_scen'].append(dict(scen=o['scen'],person=o['person'],
                                              min_m=float(gap.min()),median_m=float(np.median(gap)),p90_m=float(np.percentile(gap,90))))
                for an in table['ankare']:
                    if an['typ']=='bordskant':an['pos_m'][2]=height
        if nya:
            from rumsmall import ankare
            rum['ankare']=ankare(dict(delar=rum['delar'],id=rum['id']))
            rum['hojdpassning']=nya;rapport.extend(dict(plats=plid,**x) for x in nya)
    return platser,lengths,rapport


def anpassa(k, matning, platser):
    """Samma höjdpassning; beständig cache för oförändrade kroppsmätningar."""
    from pathlib import Path
    from datacache import nyckel, kodnyckel, signatur, hamta, spara
    h=Path(__file__).resolve().parent
    filer=[m['rorelse']['sokvag'] for m in matning['personer']]+[m['spar_metrisk']['sokvag'] for m in matning['kameror']]
    kod=[h/n for n in ('tropassning.py','trohet.py','trostod.py','tro_rigg.json')]+[h.parent/'ingest/kroppsstod.py',h.parent/'ingest/rumsmall.py']
    key=nyckel(dict(kod=kodnyckel(kod),scener=k['semantik']['scener'],matning=matning,platser=platser,filer=signatur(filer)))
    result=hamta('hojdpassning',key)
    if result is None:
        result=_anpassa_utan_cache(k,matning,platser)
        spara('hojdpassning',key,result)
    return tuple(result)
