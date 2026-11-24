"""Isolera gamla filtersteg med samma 44/48 ledpar som filmens sida."""
import json
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.spatial.transform import Rotation

H=Path(__file__).resolve().parents[1];sys.path[:0]=[str(H),str(H.parent/'ingest')]
import jamn_utvardera as U

out={}
for clip,shot in [('b-tilltal-ravara-tagningar','S1'),('a-sketch-servering-tagningar','S1')]:
    folder=H.parent/'ingest/ut'/clip/shot;meta=json.loads((folder/'meta.json').read_text());N=meta['N'];fps=meta['fps']
    R=U.las(folder,'1',N);pal=json.loads((folder/'palitlig_1.json').read_text());syn=json.loads((folder/'synlighet_1.json').read_text());G=U.gemensam_forberedelse(R,syn,pal,N)
    shape=np.median(R['S'][G['idx']],0)[None].repeat(N,0);Traw=U.fyll(R['T'],N);Tg=U.gammal_t(R['T'],G,N,fps);rows=[]
    for name,stages in [('bara_ben',0),('Hampel_rad',1),('Hampel_komponent',2),('fartgrans',3),('lagpass',4),('lagpass_ra_rot',5)]:
        from contextlib import ExitStack
        with ExitStack() as stack:
            if stages<1:stack.enter_context(patch.object(U,'hampel',side_effect=lambda X,*a,**kw:(X.copy(),0)))
            if stages<2:stack.enter_context(patch.object(U,'hampel_komp',side_effect=lambda X,*a,**kw:X.copy()))
            if stages<3:stack.enter_context(patch.object(U,'fartgrans',side_effect=lambda X,*a,**kw:X.copy()))
            if stages<4:stack.enter_context(patch.object(U,'filtfilt',side_effect=lambda b,a,X,*args,**kw:X.copy()))
            P,E=U.gammal_stab(G,N,fps)
        if stages==5:P[:,U.ROT]=np.nan_to_num(R['P'])[:,U.ROT]
        pose=U.fk(shape,P,E)
        for tname,T in [('ra_cam_t',Traw),('gammal_cam_t',Tg)]:
            err=[]
            for f in G['idx']:
                xyz=pose[f,U.LED,:3]@U.F/100+T[f];uv=xyz[:,:2]/xyz[:,2:]*R['FOC'][f]+[meta['bredd']/2,meta['hojd']/2]
                delta=np.linalg.norm(uv-R['KP'][f,U.KP],axis=1);err.extend(delta[U.synliga_par(syn.get(str(f),False))])
            rows.append(dict(steg=name,translation=tname,median_px=float(np.median(err)),p90_px=float(np.percentile(err,90))))
    out[clip+'/'+shot]=rows;print(clip,json.dumps(rows,ensure_ascii=False),flush=True)
p=H/'ut/prop_granskning/stegablation.json'
if p.exists():raise FileExistsError(p)
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
