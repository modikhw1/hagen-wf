"""Ablation av form och gammal rotorientering, utan nya kroppsskattningar."""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'scen/3d/ingest'),str(ROOT/'scen/3d/kontrakt')]
import jamn_utvardera as U

folder=ROOT/'scen/3d/ingest/ut/b-tilltal-ravara-tagningar/S1'
meta=json.loads((folder/'meta.json').read_text());N=meta['N'];fps=meta['fps'];R=U.las(folder,'1',N)
pal=json.loads((folder/'palitlig_1.json').read_text());syn=json.loads((folder/'synlighet_1.json').read_text());G=U.gemensam_forberedelse(R,syn,pal,N)
median=np.median(R['S'][G['idx']],0)[None].repeat(N,0);first=R['S'][R['idx'][0]][None].repeat(N,0)
Pg,Eg=U.gammal_stab(G,N,fps);P0=np.nan_to_num(R['P']);E0=np.nan_to_num(R['E'])
Pn,En=U.ny_stab(G,N,fps);Tn=U.utjamna_t_ruta(R['T'],G,N,fps);Tg=U.gammal_t(R['T'],G,N,fps)
Pr=Pg.copy();Pr[:,U.ROT]=P0[:,U.ROT]
out={}
for name,shape,P,E,T in [('ra_per_ruta',np.nan_to_num(R['S']),P0,E0,R['T']),('ra_medianidentitet',median,P0,E0,R['T']),('gammal_medianidentitet',median,Pg,Eg,Tg),('gammal_med_ra_rot',median,Pr,Eg,Tg),('gammal_med_ra_cam_t',median,Pg,Eg,R['T']),('ny_forsta_identitet',first,Pn,En,Tn),('ny_medianidentitet',median,Pn,En,Tn)]:
    pose=U.fk(shape,P,E);xy=pose[:,U.LED,:3]@U.F/100+T[:,None];uv=xy[:,:,:2]/xy[:,:,2:3]*R['FOC'][:,None,None]+[meta['bredd']/2,meta['hojd']/2]
    err=np.linalg.norm(uv-R['KP'][:,U.KP],axis=2)
    out[name]=dict(median_p90=np.percentile(err,[50,90]).tolist(),ovre_6_median_p90=np.percentile(err[:,:6],[50,90]).tolist(),finger_median_p90=np.percentile(err[:,6:],[50,90]).tolist())
ang=(Rotation.from_euler('xyz',Pg[:,U.ROT])*Rotation.from_euler('xyz',P0[:,U.ROT]).inv()).magnitude()*180/np.pi
out['rotfel_gammal_grader']=np.percentile(ang,[50,90,100]).tolist()
out['formparametrar_max_spann']=float(np.max(np.ptp(R['S'],axis=0)))
dest=ROOT/'scen/3d/kontrakt/ut/prop_granskning/identitetsablation.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
