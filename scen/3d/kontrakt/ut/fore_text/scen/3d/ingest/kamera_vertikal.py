"""Billig kameraorientering ur källans byggnadsvertikaler, utan nya kroppar."""
import json
from pathlib import Path
import cv2
import numpy as np
from vertikaler import mat


def rikta(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=float(a@b)
    if c>1-1e-12:return np.eye(3)
    if c<-1+1e-8:raise ValueError('Motsatta upp-riktningar är inte en användbar kameramätning.')
    x,y,z=v;cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+cross+cross@cross/(1+c)


def kor(ingest,semantik,backup,skriv):
    ingest=Path(ingest);sem=json.loads(Path(semantik).read_text(encoding='utf-8'))['data'];shots=[]
    for d in sorted(ingest.glob('S*'),key=lambda p:int(p.name[1:]) if p.name[1:].isdigit() else 100000):
        if not d.is_dir() or not (d/'meta.json').exists():continue
        seqs=list(d.glob('sekvens_*.npz'))
        if not seqs:continue
        seq=max(seqs,key=lambda p:int(np.load(p)['inom'].sum()));s=np.load(seq);v=dict(np.load(d/'varld.npz'));N=len(v['kam_R'])
        masks=np.load(d/'masker.npy',mmap_mode='r');cap=cv2.VideoCapture(str(ingest/'klipp'/(d.name+'.mp4')));obs=[]
        for frame in sorted(set([0,N//4,N//2,3*N//4,N-1])):
            cap.set(1,frame);ok,img=cap.read()
            r=mat(img,masks[frame],float(s['fokal'])) if ok else None
            if r:obs.append(dict(ruta=frame,**r))
        cap.release();setup=next((g['id'] for g in sem['kamerauppstallningar'] if d.name in g['tagningar']),d.name)
        shots.append(dict(d=d,V=v,N=N,obs=obs,setup=setup))
    logs=[]
    for sh in shots:
        d,V,N,obs=sh['d'],sh['V'],sh['N'],sh['obs'];base=V.get('kam_R_fore_vertikaler',V['kam_R']).copy();old_up=V.get('upp_fore_vertikaler',V['upp']).copy()
        V['kam_R_fore_vertikaler']=base;V['upp_fore_vertikaler']=old_up
        peer=[];origin='uppmatt'
        if not obs:
            peer=[o for other in shots if other['setup']==sh['setup'] and other is not sh for o in other['obs']]
            if peer:
                u=np.median([o['upp_cam'] for o in peer],axis=0);obs=[dict(ruta=N//2,upp_cam=(u/np.linalg.norm(u)).tolist())];origin='antagen'
        log=dict(tagning=d.name,setup=sh['setup'],fore_upp=old_up.tolist(),matningar=sh['obs'],status=origin if obs else 'antagen',
                 metod='Kamerans pitch/roll från källans bakgrundskanter; kroppen flyttas tillsammans med kameran. Yaw följer tidigare kamera. Kroppsprojektionen ändras inte.',
                 peer_tagningar=[o['d'].name for o in shots if o['setup']==sh['setup'] and o is not sh and o['obs']] if peer else [])
        if len(obs)==1:
            frame=obs[0]['ruta'];correction=rikta(base[frame]@np.array(obs[0]['upp_cam']),old_up);V['kam_R']=np.einsum('ij,njk->nik',correction,base)
            log['orsak']='Egen mätning i en ruta.' if not peer else 'Ingen egen säker vertikal; upp-riktning lånas från modellbedömt samma kamerauppställning. Antagen överföring.'
        elif obs:
            frames=[o['ruta'] for o in obs];up=np.array([o['upp_cam'] for o in obs]);curve=np.column_stack([np.interp(np.arange(N),frames,up[:,j]) for j in range(3)]);curve/=np.linalg.norm(curve,axis=1,keepdims=True)
            V['kam_R']=np.stack([rikta(base[f]@curve[f],old_up)@base[f] for f in range(N)])
            log['orsak']='Interpolerad upp-riktning mellan egna källrutor. Utanför mätintervallet hålls närmaste observation; interpolation är antagen.'
        else:log['orsak']='Ingen användbar byggnadsvertikal eller kameragrupp med mätning; tidigare kroppsbaserad upp-riktning behålls.'
        V['vertikalbeslut']=np.array(json.dumps(log,ensure_ascii=False));backup(d/'varld.npz');np.savez(d/'varld.npz',**V);skriv(d/'vertikaler.json',log);logs.append(log)
    return logs
