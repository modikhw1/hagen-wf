"""Golvbeslut av befintliga mätningar. Inga ingeststeg eller nätanrop.

Intervall för möbler och knävinkel är uttryckliga priorer. Ett modellgolv
är en djupskattning, inte en oberoende inmätning av meterskalan.
"""
import numpy as np
from pathlib import Path
import json

TOLERANS_M = .10  # Egen diagnostisk tolerans mellan cues, inte ett mätkrav.
PRIORER = dict(bord_m=[.72, .76], sits_m=[.43, .48],
               backen_over_sits_m=[.02, .15], kamera_m=[1.20, 1.70],
               kna_sankning_m=[0., .12])


def cue(namn, varde, spridning, familj, direkt=False, **extra):
    return dict(cue=namn, varde_m=float(varde), spridning_m=float(spridning),
                intervall_m=[float(varde-spridning), float(varde+spridning)],
                familj=familj, direkt=bool(direkt), **extra)


def kombinera(cues, tolerans=TOLERANS_M):
    """Median per familj; kamerans prior används bara om annan evidens saknas.

    En familj med många bilder får inte fler röster. Avvikare avvisas och
    loggas; även en avvisad avvikare ger en synlig konfliktflagga.
    """
    cues = [dict(c) for c in cues]
    bra = [c for c in cues if c.get('anvandbar', True) and c['familj'] != 'kamera']
    if not bra: bra = [c for c in cues if c.get('anvandbar', True)]
    if not bra:
        return dict(status='antagen', orsak='Ingen användbar cue.', varde_m=None,
                    spridning_m=None, spann_m=None, konflikt=True, cues=cues)
    fam = {f: float(np.median([c['varde_m'] for c in bra if c['familj']==f])) for f in {c['familj'] for c in bra}}
    mitt = float(np.median(list(fam.values())))
    selected = []
    for c in cues:
        ok = c in bra and abs(c['varde_m']-mitt) <= tolerans+c['spridning_m']
        c['anvand'] = ok
        c['beslut'] = ('använd' if ok else 'kameraprior endast sista utväg' if c['familj']=='kamera' and c not in bra
                       else c.get('orsak', 'avvisad: avvikare mot robust familjemedian'))
        if ok: selected.append(c)
    if not selected: selected = [min(bra, key=lambda c: abs(c['varde_m']-mitt))]
    family = [np.median([c['varde_m'] for c in selected if c['familj']==f]) for f in {c['familj'] for c in selected}]
    value = float(np.median(family))
    direct = [c for c in selected if c['direkt']]
    measured = len({c['familj'] for c in direct}) >= 2 and np.ptp([c['varde_m'] for c in direct]) <= tolerans
    span = float(np.ptp([c['varde_m'] for c in bra]))
    spread = float(max([abs(c['varde_m']-value)+c['spridning_m'] for c in selected]))
    return dict(varde_m=value, spridning_m=spread, spann_m=span, konflikt=span>tolerans,
                tolerans_m=tolerans, status='uppmatt' if measured else 'antagen',
                orsak=('Direkta oberoende cues överens.' if measured else
                       'Endast kamerahöjdens prior finns.' if all(c['familj']=='kamera' for c in selected) else
                       'Modellskattningar och/eller kroppsställning och möbelpriorer; direkta oberoende mätningar saknas.'), cues=cues)


def fotkontroll(d, pid, meta):
    """MHR70: knä 11/12, vrist 13/14, tå/häl 15–20. Masken är en UNION.

    Därför krävs även personens egen ruta. Synlighet på en annan persons
    mask räcker inte. Bara sparade tillförlitliga rutor räknas.
    """
    d=Path(d); masks=np.load(d/'masker.npy', mmap_mode='r') if (d/'masker.npy').exists() else None
    palfile=d/f'palitlig_{pid}.json';pal=json.loads(palfile.read_text(encoding='utf-8')) if palfile.exists() else {}
    rows=[];accepted=[];points=[]
    for f in sorted((d/'kropp'/str(pid)).glob('*.npz')):
        i=int(f.stem)
        with np.load(f) as b:
            kp=b['pred_keypoints_2d'];bb=b['bbox'];sides=[];knees=[]
            for ids in ([11,13,15,16,17],[12,14,18,19,20]):
                q=kp[ids];inside=(q[:,0]>=max(0,bb[0]))&(q[:,0]<min(meta['bredd'],bb[2]))&(q[:,1]>=max(0,bb[1]))&(q[:,1]<min(meta['hojd'],bb[3]))
                hit=np.zeros(len(ids),bool)
                if masks is not None:
                    xx=np.clip((q[:,0]*masks.shape[2]/meta['bredd']).astype(int),0,masks.shape[2]-1)
                    yy=np.clip((q[:,1]*masks.shape[1]/meta['hojd']).astype(int),0,masks.shape[1]-1)
                    hit=masks[i,yy,xx].astype(bool)&inside
                # Knä och vrist samt två av tå/hälpunkterna måste stödjas.
                sides.append(bool(hit[0] and hit[1] and hit[2:].sum()>=2))
                knees.append(bool(hit[0] and pal.get(str(i),True)))
            ok=any(sides) and pal.get(str(i),True)
            rows.append(dict(ruta=i,anvandbar=bool(ok),sidor=sides,synliga_knan=knees,
                             fotpunkter_i_bbox=int(((kp[13:21,1]>=bb[1])&(kp[13:21,1]<bb[3])&(kp[13:21,0]>=bb[0])&(kp[13:21,0]<bb[2])).sum())))
            if ok: accepted.append(i)
    return dict(ingest_id=str(pid),rutor=len(rows),anvandbara_rutor=accepted,per_ruta=rows,
                orsak='Mask + egen bbox + knä/vrist/tå eller häl + tillförlitlighet krävs. Ingests 13–14 är vrist, inte knä. Fötter utanför dessa stöd används inte som mätning.')


def undersok(tagningar, reg, roller):
    """Alla värden i samma redan registrerade platsram, före golvbeslutet."""
    from trohet import IX, F
    from trostod import begransa, matt
    shots=[];role_obs={};visibility=[]
    for t in tagningar:
        M=reg[t['id']]['M'];floor=t['golv']['hojd_m'];old=float(floor+M[2,3]);cues=[]
        r=t['rum']['floor'];height=r.get('measured_height')
        if height is not None:
            # RANSAC använder 5 cm planavstånd; spridningen sparades inte.
            # 5 cm + lutningsosäkerhet är ett antaget felintervall, inte SEM.
            spread=.05+min(.10,abs(np.tan(np.radians(r.get('normal_angle_deg') or 0)))*.5)
            cues.append(cue('djupgolv',height+M[2,3],spread,'djup',False,
                            stodpunkter=r.get('support'),osakerhet='Antaget felintervall: 5 cm RANSAC + lutning över 0,5 m. Monokulärt modelldjup.'))
        camera_z=float(np.median((t['V']['kam_C']@t['G'].T)[:,2]))
        cues.append(cue('kamerahöjd 1,45 m',camera_z-1.45+M[2,3],.25,'kamera',False,prior=True,prior_intervall_m=PRIORER['kamera_m']))
        for pid,pp in t['personer'].items():
            S=dict(np.load(t['mapp']/f'sekvens_{pid}.npz'));frames=np.flatnonzero(S['inom']);V=t['V'];G=M[:3,:3]@t['G']
            Q=np.einsum('ij,njk,kl->nil',G,V['kam_R'][frames],F)
            T=(V['kam_C'][frames]+np.einsum('nij,nj->ni',V['kam_R'][frames],S['cam_t'][frames]))@G.T+M[:3,3]
            X=np.einsum('nij,ntj->nti',Q,S['pose'][frames,:,:3]/100)+T[:,None]
            vis=fotkontroll(t['mapp'],pid,t['meta']);visibility.append(dict(tagning=t['id'],**vis))
            usable=[j for j,f in enumerate(frames) if int(f) in vis['anvandbara_rutor']]
            if usable:
                # Tåleden + antagen 2,5 cm sula; aldrig cam_t-före/efter som två oberoende cues.
                side_by_frame={v['ruta']:v['sidor'] for v in vis['per_ruta']}
                feet=np.array([min(X[j,IX[s+'_ball'],2] for side,s in enumerate('lr') if side_by_frame[int(frames[j])][side])-.025 for j in usable])
                cues.append(cue('synliga fötter '+pid,np.median(feet),max(.03,float(np.ptp(np.percentile(feet,[10,90]))/2)),
                                'fotter',True,ingest_id=pid,rutor=len(usable),sula_prior_m=.025))
            hip=float(np.median(X[:,IX['root'],2]));role=roller[(t['id'],pid)]
            # Låg modellhöft bakom en bardisk är inte bevis för en stol.
            # Restaurangpriorer används bara där rumsteget hittat vanligt bord.
            vanligt_bord=any(o['label']=='table' for o in t['rum'].get('objects',[]))
            seated=hip-old<.82 and vanligt_bord  # Antagen klassning, inte mätt sittkontakt.
            if seated and not role.startswith('okand_'):
                # Lägsta fasta horisontella lårpose ger ett intervall, inte krav på sträckta ben.
                lengths=matt(S['pose'][frames])
                body=float(np.median(X[:,[IX['l_upleg'],IX['r_upleg']],2]))-float(np.mean([lengths[IX[s+'_foot']] for s in 'lr']))-.08-.06
                cues.append(cue('sittande ben '+role,body,.09,'kropp',False,prior=True,
                                orsak_intervall='Fast vadlängd; fotled/sula prior 8 cm, knäsänkning 0–12 cm och 3 cm posemarginal. Hela benets räckvidd är större.'))
                cues.append(cue('sitshöjd '+role,hip-.085-.455,.09,'sits',False,prior=True,
                                priorer=['sits_m','backen_over_sits_m']))
                wrists=X[:,[IX['l_wrist'],IX['r_wrist']]];stable=[]
                for side in range(2):
                    for a in range(len(frames)-11):
                        seg=wrists[a:a+12,side]
                        if np.ptp(seg[:,2])<=.03 and np.linalg.norm(np.ptp(seg[:,:2],axis=0))<=.08:
                            stable.append(dict(hojd_m=float(np.median(seg[:,2])),tagning=t['id'],sida='lr'[side],ruta=int(frames[a])))
                role_obs.setdefault(role,[]).append(dict(tagning=t['id'],hip_m=hip,stabila=stable))
            elif not seated:
                # Stående utan synlig fot ger bara räckvidd, aldrig en golvmätning.
                lengths=pp['knoglangder_cm'];reach=(lengths['lar']+lengths['underben'])/100
                cues.append(cue('stående räckvidd '+role,hip-reach-.05,.12,'kropp',False,prior=True,
                                orsak_intervall='Fast benlängd; knäböjning och höft/sula är osäkra. Inte en synlig fot.'))
        shots.append(dict(tagning=t['id'],gammalt_golv_m=old,cues=cues))
    scale=[]
    for role,obs in role_obs.items():
        stable=[c for o in obs for c in o['stabila']]
        if not stable:continue
        best=min(stable,key=lambda c:c['hojd_m'])
        for o in obs:
            shot=next(s for s in shots if s['tagning']==o['tagning'])
            local=min(o['stabila'],key=lambda c:c['hojd_m']) if o['stabila'] else None
            shot.setdefault('lokal_handledsevidens',[]).append(dict(roll=role,
                varde_m=local['hojd_m']-.74 if local else None,spridning_m=.05 if local else None,
                evidens=local,anvand_separat=False,
                orsak='Lokalt stilla läge loggas separat. Rollens lägsta stabila läge över tagningarna används som svag kontaktcue; högre lägen kan vara gester och är inte oberoende golvmätningar.'))
        hip=float(np.median([o['hip_m'] for o in obs]));difference=best['hojd_m']-hip
        scale_range=[.09/difference,.31/difference] if difference>0 else None
        scale.append(dict(roll=role,handled_minus_backen_m=difference,skala_intervall_fran_prior=scale_range,
                          skala_1_inom=bool(scale_range and scale_range[0]<=1<=scale_range[1]),
                          orsak='Bord minus sits minus bäckenöverhöjd: prior 0,09–0,31 m. MHR root är en riggled, inte en uppmätt sittyta. Stilla handled kan vara gest; detta verifierar inte en ny skala.'))
        for shot in shots:
            if any(o['tagning']==shot['tagning'] for o in obs):
                shot['cues'].append(cue('stilla handled/bord '+role,best['hojd_m']-.74,.05,'bord',False,prior=True,
                                         evidens=best,prior_intervall_m=PRIORER['bord_m'],kontakt='antagen; 3 cm handled/kontaktyta + 2 cm bordprior'))
    allc=[]
    for shot in shots:
        shot['beslut']=kombinera(shot['cues'])
        allc.extend(dict(c,tagning=shot['tagning']) for c in shot['cues'])
    pooled=kombinera(allc)
    depth_checks=[dict(tagning=t['id'],djupfaktor=t['rum'].get('scale',{}).get('depth_to_pipeline_scale'),
                       sparse_matching_multiplier=t['rum'].get('scale',{}).get('sparse_matching_multiplier'),
                       skillnad_procent=t['rum'].get('scale',{}).get('disagreement_percent'),
                       verifierad=t['rum'].get('scale',{}).get('verified',False)) for t in tagningar]
    depth_conflict=any(c['skillnad_procent'] is not None and c['skillnad_procent']>10 for c in depth_checks)
    return dict(priorer=PRIORER,per_tagning=shots,pool=pooled,fotsynlighet=visibility,
                skala=dict(varde=1.,status='antagen',behalls=True,kontroller=scale,
                           djupkontroller=depth_checks,djupkonflikt=depth_conflict,djuptolerans_procent=10.,
                           overens=False if depth_conflict else all(c['skala_1_inom'] for c in scale) if scale else None,
                           orsak='Kroppsmodellens meter behålls. Möbelpriorer prövar bara förenlighet; djupet saknar oberoende metrisk verifiering. Ingen längdskalning av kroppar.'))
