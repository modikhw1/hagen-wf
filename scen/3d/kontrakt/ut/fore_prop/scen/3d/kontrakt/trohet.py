"""Bildtrohet i numpy, med samma leder, stöd och kamera som Blender bygger.

70-punktsmodellen blandar hudpunkter och leder. Bara exakt motsvarande
riggleder jämförs här; en näsa är exempelvis ingen huvudled. Dolda ben
redovisas separat, eftersom de uttryckligen ersätts av stödets antagande.
"""
import json
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent
RIGG = json.loads((HIT/'tro_rigg.json').read_text(encoding='utf-8'))
NAMN = RIGG['namn']
IX = {n:i for i,n in enumerate(NAMN)}
F = np.diag([1., -1., -1.])
# SAM:s MHR70: dessa punkter är riggleder, inte hudregressioner.
PAR = [(5,'l_uparm'), (6,'r_uparm'), (9,'l_upleg'), (10,'r_upleg'),
       (11,'l_lowleg'), (12,'r_lowleg')]
for start, sida in ((21,'r'), (42,'l')):
    PAR += [(start+i, sida+'_'+n) for i,n in enumerate(
        ['thumb_null','thumb3','thumb2','thumb1','index_null','index3','index2','index1',
         'middle_null','middle3','middle2','middle1','ring_null','ring3','ring2','ring1',
         'pinky_null','pinky3','pinky2','pinky1','wrist_twist'])]
KP = np.array([p[0] for p in PAR]); LED = np.array([IX[p[1]] for p in PAR])
GRANS = dict(median_px=20., p90_px=40., median_bboxandel=.04,
             p90_bboxandel=.08, bbox_iou=.65)


def gravitation(v):
    u = v['upp']/np.linalg.norm(v['upp']); c = u[2]
    if c < -1+1e-10: return F.copy()
    x,y,z = np.cross(u,[0.,0.,1.]); k = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+k+k@k/(1+c)


def projicera(x, key, bredd, hojd, sensor=36.):
    m = np.array(key['matris']); c = (np.asarray(x)-m[:3,3])@m[:3,:3]
    fok = key['lins_mm']/sensor*bredd
    return c[...,:2]/(-c[...,2:3])*[fok,-fok]+[bredd/2,hojd/2]


def ruta_pose(scen, pm, f, stod=True, data=None):
    """Den byggda posen (efter stöd) i modellrum (cm) samt rotationen q och förflyttningen t till planens värld."""
    from trostod import begransa
    if data is None:
        s = dict(np.load(pm['rorelse'])); v = dict(np.load(scen['varld']))
    else:s,v=data
    m = np.array(pm.get('till_plats',scen.get('till_plats',np.eye(4))))
    g = m[:3,:3]@gravitation(v); q = g@v['kam_R'][f]@F
    t = g@(v['kam_C'][f]+v['kam_R'][f]@s['cam_t'][f])+m[:3,3]
    pose = s['pose'][f]
    if stod and pm.get('stod'):
        pose,_ = begransa(pose,q,t,pm['stod'],s['ben_synliga'][f] if 'ben_synliga' in s else None,
                          pm.get('benlangder_m'),skyddade_knan=pm.get('skyddade_knan',{}).get(str(f)))
    return pose,q,t


def ruta(scen, pm, f, stod=True, data=None):
    pose,q,t = ruta_pose(scen,pm,f,stod,data)
    return pose[:,:3]/100@q.T+t


def iou(a,b):
    lo=np.maximum(a[:2],b[:2]); hi=np.minimum(a[2:],b[2:]); inter=np.maximum(hi-lo,0).prod()
    union=np.maximum(a[2:]-a[:2],0).prod()+np.maximum(b[2:]-b[:2],0).prod()-inter
    return float(inter/max(union,1e-12))


def envelope(uv):
    return np.r_[uv.min(0),uv.max(0)]


def statistik(err,andel,ious):
    if not len(err): return dict(status='saknas',flaggad=True)
    r=dict(median_px=float(np.median(err)), p90_px=float(np.percentile(err,90)),
           median_bboxandel=float(np.median(andel)),p90_bboxandel=float(np.percentile(andel,90)),
           bbox_iou=float(np.median(ious)),punkter=len(err))
    r['flaggad']=any(r[k]>v for k,v in GRANS.items() if k!='bbox_iou') or r['bbox_iou']<GRANS['bbox_iou']
    return r


def mat(plan, stod=True):
    """Kameran före CM-edits; fel i källpixlar, även vid annan utupplösning."""
    w=plan['kallbild_bredd']; h=plan.get('kallbild_hojd',round(w*plan['utdata']['hojd']/plan['utdata']['bredd']))
    scener=plan.get('scener') or plan.get('matkamera',{}).get('scener')
    if scener is None:
        scener=[dict(id='sammanhangande',ut=[0,len(plan['kallrutor'])],lokal_start=0,
                     varld=plan['matning']['kameror'][0]['spar_metrisk']['sokvag'],personer=plan['personer'])]
    rows=[]
    for d in scener:
        for pm in d['personer']:
            s=dict(np.load(pm['rorelse']));v=dict(np.load(d['varld']));folder=Path(pm['rorelse']).parent
            pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
            palfile=folder/f'palitlig_{pid}.json';pal=json.loads(palfile.read_text()) if palfile.exists() else {}
            err=[];rat=[];ious=[];allerr=[];allrat=[];allious=[];frames=[];skipped=0
            for u in range(*d['ut']):
                f=d['lokal_start']+u-d['ut'][0] if plan.get('scener') else plan['kallrutor'][u]
                rawfile=folder/'kropp'/str(pid)/f'{f:04d}.npz'
                if not s['inom'][f] or not rawfile.exists() or not pal.get(str(f),True): skipped+=1;continue
                with np.load(rawfile) as b:
                    x=ruta(d,pm,f,stod,(s,v)); key=plan.get('matkamera',plan['renderkamera'])['nycklar'][u]
                    uv=projicera(x[LED],key,w,h); target=b['pred_keypoints_2d'][KP]
                    # Synlighetsflaggan har bara upplösning överkropp/ben.
                    reliable=np.ones(len(KP),bool)
                    if 'ben_synliga' in s and not s['ben_synliga'][f]: reliable[:6]=[True,True,False,False,False,False]
                    delta=np.linalg.norm(uv-target,axis=1);bh=max(float(b['bbox'][3]-b['bbox'][1]),1.)
                    allerr.extend(delta);allrat.extend(delta/bh);allious.append(iou(envelope(uv),envelope(target)))
                    err.extend(delta[reliable]);rat.extend(delta[reliable]/bh)
                    overlap=iou(envelope(uv[reliable]),envelope(target[reliable]));ious.append(overlap)
                    frames.append(dict(ut=u,lokal=f,median_px=float(np.median(delta[reliable])),bbox_iou=overlap))
            rows.append(dict(scen=d['id'],person=pm['id'],**statistik(err,rat,ious),
                             alla_inklusive_dolda_ben=statistik(allerr,allrat,allious),rutor=frames,utelamnade_rutor=skipped))
    return dict(status='uppmatt',metod='Exakta MHR70–riggledpar. Primärmått skyddar uppmätt överkropp; osynliga ben särredovisas. IoU mellan samma leders 2D-omslutningar, inte mellan hud och detektionsruta.',
                granser=dict(GRANS),grans_ursprung='Egna diagnostiska trösklar: marginal över S1–S5/S7 efter återställd projektion samt bars befintliga stabiliseringsrest (p90 6,7–7,1 %). Inga ägarkrav.',
                personer=rows,utelamnade_personer=[dict(scen=d['id'],**v) for d in scener for v in d.get('utelamnade',[])],
                flaggad=any(r['flaggad'] for r in rows))


def rapport(plan,fil):
    r=plan['kvalitet']['bildtrohet'];p=Path(fil)
    p.with_name(p.stem+'_trohet.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=['# Bildtrohet före regins kameraändringar','',r['metod'],'',r['grans_ursprung'],str(r['granser']),'',
          '| Scen/person | median/p90 px | median/p90 bboxandel | IoU | flaggad |','|---|---|---|---|---|']
    for x in r['personer']:
        rows.append(f"| {x['scen']}/{x['person']} | {x.get('median_px',float('nan')):.2f}/{x.get('p90_px',float('nan')):.2f} | {x.get('median_bboxandel',float('nan')):.4f}/{x.get('p90_bboxandel',float('nan')):.4f} | {x.get('bbox_iou',0):.3f} | {x['flaggad']} |")
    p.with_name(p.stem+'_trohet.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    from kvalitet import skriv
    skriv(plan,p)
