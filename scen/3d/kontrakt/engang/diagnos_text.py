"""Mät projektionens felbidrag utan att köra om kropp eller ändra mätfiler."""
import json
import sys
from pathlib import Path
import numpy as np
from trohet import KP, LED, F, statistik, iou, envelope, ruta, projicera
from textarbete import jsonfil
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingest"))

HIT = Path(__file__).resolve().parent


def diagnos():
    rows = []
    for clip in ('b', 'kenny', 'a'):
        plan = json.loads((HIT/f'ut/{clip}/tom/plan.json').read_text(encoding='utf-8'))
        w,h = plan['kallbild_bredd'],plan['kallbild_hojd']
        for sc in plan['scener']:
            for pm in sc['personer']:
                folder=Path(pm['rorelse']).parent;pid=pm.get('ingest_id') or '1'
                s=dict(np.load(pm['rorelse']));v=dict(np.load(sc['varld']))
                meta=json.loads((folder/'meta.json').read_text(encoding='utf-8'))
                cam=json.loads((folder/'kamera.json').read_text(encoding='utf-8'))
                from regler import kamerabeslut
                cb=kamerabeslut(cam,meta)
                pal=json.loads((folder/f'palitlig_{pid}.json').read_text())
                errors={}; focals=[];valid=[]
                for f in range(len(s['pose'])):
                    raw=folder/'kropp'/pid/f'{f:04d}.npz'
                    if not raw.exists() or not s['inom'][f] or not pal.get(str(f),True):continue
                    with np.load(raw) as b:
                        valid.append(f);focals.append(float(b['focal_length']))
                        reliable=np.ones(len(KP),bool)
                        if not s['ben_synliga'][f]:reliable[2:6]=False
                        target=b['pred_keypoints_2d'][KP][reliable]
                        pose=s['pose'][f,LED,:3]/100
                        rawpose=b['pred_joint_coords'][LED]@F
                        ts={name:s[name][f] for name in ['cam_t','cam_t_ra','cam_t_fore_golv'] if name in s}
                        ts['raw_t']=b['pred_cam_t']
                        variants={name:(pose@F+t,float(b['focal_length'])) for name,t in ts.items()}
                        variants['raw_pose_raw_t']=(b['pred_joint_coords'][LED]+b['pred_cam_t'],float(b['focal_length']))
                        variants['fallback']=(pose@F+b['pred_cam_t'],float(max(w,h)))
                        variants['colmap']=(pose@F+b['pred_cam_t'],float(cam.get('fokal_px') or max(w,h)))
                        u=sc['ut'][0]+f-sc['lokal_start']
                        variants['plan']=None
                        for name,value in variants.items():
                            uv=projicera(ruta(sc,pm,f,True,(s,v))[LED],plan['matkamera']['nycklar'][u],w,h) if value is None else value[0][:,:2]/value[0][:,2:]*value[1]+[w/2,h/2]
                            uv=uv[reliable];delta=np.linalg.norm(uv-target,axis=1);bh=max(b['bbox'][3]-b['bbox'][1],1)
                            d=errors.setdefault(name,[[],[],[]]);d[0].extend(delta);d[1].extend(delta/bh);d[2].append(iou(envelope(uv),envelope(target)))
                rows.append(dict(klipp=clip,scen=sc['id'],person=pm['id'],ruta_antal=len(s['pose']),inom=int(s['inom'].sum()),kropp_rutor=len(list((folder/'kropp'/pid).glob('*.npz'))),bedomda=len(valid),
                                 fokal_raw=[min(focals),max(focals)] if focals else [],fokal_sekvens=float(s['fokal']),kamerabeslut=cb,
                                 kamerabana_m=float(np.linalg.norm(np.diff(v['kam_C'],axis=0),axis=1).sum()),
                                 varianter={k:statistik(*v) for k,v in errors.items()}))
    jsonfil(HIT/'ut/fore_text/diagnos_fore.json',rows)
    for r in rows:
        print(r['klipp'],r['scen'],r['person'],'f',r['fokal_raw'],'vag',round(r['kamerabana_m'],3),'inom',r['inom'],'/',r['ruta_antal'],
              {k:[round(v.get('median_px',0),2),round(v.get('p90_px',0),2)] for k,v in r['varianter'].items()})


if __name__=='__main__':diagnos()
