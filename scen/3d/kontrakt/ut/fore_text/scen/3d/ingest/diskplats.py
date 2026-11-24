"""Diskrum med gemensamma sidor och kameraställen. Metrisk skala är osäker."""
import copy
import math
import numpy as np
from rumsmall import las, ankare, rz

F=np.diag([1.,-1.,-1.])


def moblera(plats,sem,tagningar):
    desc=sem.data['plats']['beskrivning'].lower()
    val='glass_disk' if 'glass' in desc or 'gelato' in desc else 'chark_disk' if 'chark' in desc or 'slakter' in desc else 'servering_disk'
    m,sha=las(val);m=copy.deepcopy(m);observations=[];cams=[]
    # Samma roll står på samma sida även om modellens ankartyp är fel.
    # a:s kund är märkt sta_bakom i modellen, men roll och beskrivning anger kundsida.
    for t in tagningar:
        V=t['V'];G=t['G'];pobs=[]
        for pid,pp in t['personer'].items():
            role=next((b['person'] for b in t['semantik_beslut'] if b.get('spar_id')==pid and 'person' in b),None)
            if not role:continue
            S=dict(np.load(t['mapp']/f'sekvens_{pid}.npz'));ix=np.flatnonzero(S['inom'])
            if not len(ix):continue
            body=(np.einsum('nij,nj->ni',V['kam_R'][ix],S['cam_t'][ix]+S['pose'][ix,1,:3]/100@F)+V['kam_C'][ix])@G.T
            cam=V['kam_C'][ix]@G.T
            customer=sem.personer[role]['roll']=='customer'
            vec=np.median(cam-body,axis=0);dist=float(np.linalg.norm(vec[:2]))
            pobs.append(dict(pid=pid,role=role,S=S,ix=ix,body=body,cam=cam,customer=customer,distance=dist,vec=vec))
        observations.append(dict(t=t,p=pobs))
    distances=[p['distance'] for o in observations for p in o['p'] if p['distance']>.1]
    # Minsta kropp–kamera-avstånd begränsar diskdjupet. Ingen skalning av personer.
    half=float(np.clip(min(distances or [1.6])*.25,.18,.65));depth=min(.65,half*1.3)
    disk=next(d for d in m['delar'] if d['id']=='disk');disk['matt_m'][1]=depth
    for a in disk['ankare']:
        if a['id']=='sta_bakom':a['pos_m']=[0,-half,0]
        if a['id']=='kundsida':a['pos_m']=[0,half,0]
    anchors=ankare(m);anc={a['id']:a for a in anchors};bindings=[];camera_bindings=[];wristcues=[];rests=[]
    for ob in observations:
        t=ob['t'];reg=next(r for r in plats['tagningar'] if r['id']==t['id']);M=np.eye(4)
        if ob['p']:
            best=max(ob['p'],key=lambda p:len(p['ix']));aid='kundsida' if best['customer'] else 'sta_bakom';target=anc[aid]
            wanted=-math.pi/2 if best['customer'] else math.pi/2
            yaw=wanted-math.atan2(best['vec'][1],best['vec'][0]);R=rz(yaw)
            median=np.median(best['body'],axis=0);translation=np.array(target['pos_m'])-R@median
            # Golv är inte synligt i dessa utsnitt. Kamerahöjd är en reservprior.
            old=np.array(reg['till_plats']['matris']);translation[2]=old[2,3]
            M[:3,:3]=R;M[:3,3]=translation
            for p in ob['p']:
                aid='kundsida' if p['customer'] else 'sta_bakom'
                bindings.append(dict(tagning=t['id'],ingest_id=p['pid'],roll=p['role'],ankare=aid,hallning='star',status='modellbedomd',avstand_till_ankare_m=float(np.linalg.norm((np.median(p['body'],axis=0)@R.T+translation)[:2]-np.array(anc[aid]['pos_m'][:2])))))
                from pathlib import Path
                import json
                names=json.loads((Path(__file__).parent/'mhr_ledernamn.json').read_text());wr=[names.index(n) for n in ['l_wrist','r_wrist']]
                S=p['S'];ix=p['ix'];xx=[]
                for f in ix:
                    x=(S['pose'][f,wr,:3]/100@F+S['cam_t'][f])@t['V']['kam_R'][f].T+t['V']['kam_C'][f]
                    xx.append((x@t['G'].T)@R.T+translation)
                xx=np.array(xx);window=max(6,round(t['meta']['fps']*.3))
                for side in range(2):
                    for start in range(max(0,len(xx)-window+1)):
                        seg=xx[start:start+window,side]
                        if np.ptp(seg[:,2])<=.03 and np.linalg.norm(np.ptp(seg[:,:2],axis=0))<=.08 and abs(np.median(seg[:,1]))<half+.3:
                            wristcues.append(dict(tagning=t['id'],sida=side,rutor=[int(ix[start]),int(ix[start+window-1])+1],hojd_m=float(np.median(seg[:,2]))))
            rests.append(dict(tagning=t['id'],rest_xy_m=bindings[-1]['avstand_till_ankare_m']))
        else:
            # Produktnärbild utan kropp: samma ram som närmaste föregående tagning.
            previous=next((r for r in reversed(plats['tagningar'][:plats['tagningar'].index(reg)]) if r['id'] in [x['tagning'] for x in rests]),None)
            M=np.array(previous['till_plats']['matris']) if previous else M
        reg['till_plats']=dict(yaw_rad=float(math.atan2(M[1,0],M[0,0])),translation_m=M[:3,3].tolist(),skala=1.,matris=M.tolist())
        reg['kvalitet'].update(metod='diskankare',status='antagen',kommentar='Bäckenets XY till rollens disksida; kropp–kamera-riktning bestämmer yaw. Kamerahöjd/golv är reservprior, ingen skala. Samma disk används i alla tagningar.')
        camera=(t['V']['kam_C']@t['G'].T)@M[:3,:3].T+M[:3,3]
        setup=next((s['id'] for s in sem.data['kamerauppstallningar'] if t['id'] in s['tagningar']),t['id'])
        side='kamera_personal' if ob['p'] and ob['p'][0]['customer'] else 'kamera_kund'
        camera_bindings.append(dict(tagning=t['id'],setup=setup,ankare=side+'_'+setup,pos_m=np.median(camera,axis=0).tolist(),status='antagen',metod='POV vid motpartens sida av disken; lokala kamerarörelser behålls. Sidval från semantik, läge från rekonstruerad kamera.'))
    # Ett kameraankare per uppställning; enskilda tagningar behåller sin mätta offset.
    for aid in dict.fromkeys(b['ankare'] for b in camera_bindings):
        p=np.median([b['pos_m'] for b in camera_bindings if b['ankare']==aid],axis=0)
        anchors.append(dict(id=aid,typ='annat',etikett=aid,pos_m=p.tolist(),riktning_rad=-math.pi/2 if 'kund' in aid else math.pi/2,status='antagen',metod='Median av rekonstruerade kameraställen i modellbedömd uppställning.',hojd_m=float(p[2]),osakerhet_m=None,del='disk'))
    cues=[c for c in wristcues if .65<c['hojd_m']<1.5]
    evidence=min(cues,key=lambda x:x['hojd_m']) if cues else None
    height=float(np.clip(evidence['hojd_m'],.85,1.2)) if evidence else 1.0
    disk['matt_m'][2]=height
    for d in m['delar']:
        if d['id']=='monter':d['pos_m']=[0,depth*.2,height-.3];d['matt_m'][1]=depth*.9
    fit=dict(status='antagen',metod='Personankare och gemensam disk; kamera–kroppsavstånd begränsar djupet. Ingen bildmatchad 3D-rekonstruktion av disken.',yaw_rad=0.,translation_m=[0,0,0],skala=1.,rms_m=float(np.sqrt(np.mean([r['rest_xy_m']**2 for r in rests]))) if rests else 0.,residualer=rests)
    heightfit=dict(status='antagen' if evidence else 'mall',hojd_m=height,evidens=evidence,antal_stabila_fonster=len(cues),evidens_rest_m=float(evidence['hojd_m']-height) if evidence else None,
                   metod='Stilla handled är uppmätt; att handen vilar på disken är antaget. Prior 85–120 cm. Utan sådan cue behålls mallens 100 cm.')
    plats.update(ankare=anchors,bindningar=bindings,kamera_bindningar=camera_bindings,objekt=[],vaggar=[],utelamnade=[])
    plats['rumsmall']=dict(id=m['id'],sha256=sha,status='mall',fiktiv=m['fiktiv'],passning=fit,justeringar=[],passningsevidens=[],delar=m['delar'],ankare=anchors,antaganden=m['antaganden'],texturprojektion=None,hojdpassning=[heightfit])
    plats['mallbeslut']=dict(status='antagen',vald=val,venue_kod='disk_kassa',mapping='Vår mapping: disk_kassa → lokal_disk_kassa; semantisk specialisering till '+val,rest_m=fit['rms_m'],hojdpassning=heightfit,orsak='Personernas sidor kommer från redan sparad semantik. Rumsmått är mallvärden; de är inte mätta ur källan.')
