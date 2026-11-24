"""Begränsa stabiliseringens bildförskjutning med redan sparade kroppsrutor.

Detta verifierar projektion mot kroppsestimatorn, inte mot en mänsklig
annotering. Skymda ben återställs aldrig från råmodellens gissning.
"""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

F = np.diag([1., -1., -1.])


def skydda(s, folder, pid):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'kontrakt'))
    from trohet import KP, LED
    names=json.loads((Path(__file__).parent/'mhr_ledernamn.json').read_text())
    lower=np.array([i for i,n in enumerate(names) if any(t in n for t in ('upleg','lowleg','foot','ball','toe'))])
    palfile=Path(folder)/f'palitlig_{pid}.json'
    pal=json.loads(palfile.read_text()) if palfile.exists() else {}
    logs=[]
    base=s.get('cam_t_fore_golv',s['cam_t']).copy()
    floor_delta=s['cam_t']-base
    for f in np.flatnonzero(s['inom']):
        raw=Path(folder)/'kropp'/str(pid)/f'{f:04d}.npz'
        if not raw.exists() or not pal.get(str(f),True):continue
        with np.load(raw) as b:
            target=b['pred_keypoints_2d'][KP]
            reliable=np.ones(len(KP),bool)
            if not s['ben_synliga'][f]:reliable[2:6]=False
            pose=s['pose'][f].copy();rawpose=pose.copy()
            rawpose[:,:3]=b['pred_joint_coords']@F*100
            # Råmodellens rotationsmatriser är i MHR-modellens axlar.
            rawpose[:,3:7]=Rotation.from_matrix(b['pred_global_rots']).as_quat()
            if not s['ben_synliga'][f]:
                shift=rawpose[1,:3]-pose[1,:3]
                rawpose[lower,:3]=pose[lower,:3]+shift
                rawpose[lower,3:7]=pose[lower,3:7]
            rawt=b['pred_cam_t'];focal=float(b['focal_length']);box=b['bbox']
            # Sex pixlar eller 1,5 % av personhöjden, den snävare gränsen.
            # En signalvakt för filtrering, inte en ändrad kvalitetsgräns.
            bound=min(6.,.015*max(float(box[3]-box[1]),1.))
            def err(weight):
                x=(weight*pose[LED,:3]+(1-weight)*rawpose[LED,:3])/100@F
                x+=weight*base[f]+(1-weight)*rawt
                uv=x[:,:2]/x[:,2:]*focal
                # Bildcentrum hämtas ur metadata; bbox är personens ruta.
                meta=json.loads((Path(folder)/'meta.json').read_text())
                uv += [meta['bredd']/2,meta['hojd']/2]
                return float(np.percentile(np.linalg.norm(uv-target,axis=1)[reliable],90))
            before=err(1.);weight=1.
            if before>bound:
                lo,hi=0.,1.
                for _ in range(12):
                    mid=(lo+hi)/2
                    if err(mid)<=bound:lo=mid
                    else:hi=mid
                weight=lo
                new=weight*pose+(1-weight)*rawpose
                for j in range(len(pose)):
                    new[j,3:7]=Slerp([0,1],Rotation.from_quat([rawpose[j,3:7],pose[j,3:7]]))([weight]).as_quat()[0]
                s['pose'][f]=new
                s['cam_t'][f]=weight*base[f]+(1-weight)*rawt+floor_delta[f]
                if 'cam_t_fore_golv' in s:s['cam_t_fore_golv'][f]=s['cam_t'][f]-floor_delta[f]
            logs.append(dict(ruta=int(f),stabil_andel=weight,p90_fore_px=before,p90_efter_px=err(weight),grans_px=bound))
    return dict(status='uppmatt',metod='Bildbegränsad blandning av stabil och sparad råpose samt cam_t. Kvaternioner interpoleras på rotationsgruppen. Dolda ben behåller stabil pose relativt bäckenet. Inga nya kroppsanrop.',
                begransning='Egenprojektion mot estimatorns sparade 2D-punkter; inget oberoende mått på anatomisk eller visuell riktighet.',rutor=logs)
