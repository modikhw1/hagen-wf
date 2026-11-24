"""Billig skymningsdiagnos: källmaskens synliga pixlar mot mallens lådor.

Kroppsdjup interpoleras med närmaste MHR70-punkt. Det är en approximation,
inte renderad hud-IoU. Bara tydliga förgrundsträffar (>5 cm) räknas.
Maskerna är personunioner; egen bbox begränsar sammanblandning.
"""
import copy
from pathlib import Path
import numpy as np

GRANS = .02  # Egen diagnostisk gräns: 2 % av maskproven.
DJUPMARGINAL_M = .05


def stralar(uv, key, w, h):
    M=np.array(key['matris']);f=key['lins_mm']/36*w
    local=np.c_[(uv[:,0]-w/2)/f,-(uv[:,1]-h/2)/f,-np.ones(len(uv))]
    return M[:3,3],local@M[:3,:3].T


def boxdjup(origin, rays, obj):
    """Strålparametern är kamerans positiva Z-djup, även för sneda strålar."""
    a=obj.get('rotation_rad',[0,0,0])[2];c,s=np.cos(a),np.sin(a)
    R=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
    o=(origin-np.array(obj['pos_m']))@R;d=rays@R
    half=np.array(obj['matt_m'])/2
    safe=np.where(np.abs(d)>1e-12,d,1e-12)
    lo=(-half-o)/safe;hi=(half-o)/safe
    enter=np.maximum(np.minimum(lo,hi).max(axis=1),0.)
    leave=np.maximum(lo,hi).min(axis=1)
    return np.where(leave>=enter,enter,np.inf)


def konflikt(uv, depth, key, w, h, objects):
    origin,rays=stralar(np.asarray(uv),key,w,h)
    return {o['id']:boxdjup(origin,rays,o)<np.asarray(depth)-DJUPMARGINAL_M for o in objects}


def mat(plan, prov=None):
    w=plan['kallbild_bredd'];h=plan['kallbild_hojd'];out=[];reverse=[]
    scenes=plan.get('scener') or plan['matkamera']['scener']
    for scene in scenes:
        count={};total=0;rev_hidden=0;rev_empty=0;frames=[]
        a,b=scene['ut'];indices=sorted(set(range(a,b,6))|{b-1})
        for u in indices:
            objects=[o for o in plan['objekt'] if o.get('status')=='mall' and o.get('deltyp') not in ('golv','vagg','fonster','lampa')
                     and o.get('synlig_ut',[0,len(plan['kallrutor'])])[0]<=u<o.get('synlig_ut',[0,len(plan['kallrutor'])])[1]]
            key=plan['matkamera']['nycklar'][u]
            f=scene['lokal_start']+u-a if plan.get('scener') else plan['kallrutor'][u]
            for pm in scene['personer']:
                folder=Path(pm['rorelse']).parent;pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
                raw=folder/'kropp'/str(pid)/f'{f:04d}.npz';maskfile=folder/'masker.npy'
                if not raw.exists() or not maskfile.exists():continue
                with np.load(raw) as data:
                    kp=data['pred_keypoints_2d'];depth=data['pred_keypoints_3d'][:,2]+data['pred_cam_t'][2];bb=data['bbox']
                mask=np.load(maskfile,mmap_mode='r')[f];mh,mw=mask.shape
                yy,xx=np.nonzero(mask);uv=np.c_[(xx+.5)*w/mw,(yy+.5)*h/mh]
                inside=(uv[:,0]>=bb[0])&(uv[:,0]<=bb[2])&(uv[:,1]>=bb[1])&(uv[:,1]<=bb[3]);uv=uv[inside][::3]
                if len(uv):
                    nearest=np.argmin(((uv[:,None]-kp[None])**2).sum(axis=2),axis=1)
                    hits=konflikt(uv,depth[nearest],key,w,h,objects);total+=len(uv)
                    if prov is not None:
                        for group in {o['id'].split(':')[0] for o in objects if o.get('oppen_mitt')}:
                            prov.append(dict(scen=scene['id'],grupp=group,hits={o['id']:hits[o['id']] for o in objects if o['id'].split(':')[0]==group}))
                    for obj in objects:
                        group=obj['id'].split(':')[0]
                        # Samma möbeldels skiva och ben får inte dubbelräknas.
                        if group not in count:count[group]=[0,0]
                    for group in {o['id'].split(':')[0] for o in objects}:
                        combined=np.logical_or.reduce([hits[o['id']] for o in objects if o['id'].split(':')[0]==group])
                        count[group][0]+=int(combined.sum());count[group][1]+=len(uv)
                # Omvänd kontroll: saknad mask kan också vara segmenteringsfel.
                q=kp[:21];in_image=(q[:,0]>=0)&(q[:,0]<w)&(q[:,1]>=0)&(q[:,1]<h)
                mx=np.clip((q[:,0]*mw/w).astype(int),0,mw-1);my=np.clip((q[:,1]*mh/h).astype(int),0,mh-1)
                hidden=in_image&~mask[my,mx].astype(bool)
                if hidden.any():
                    hits=konflikt(q[hidden],depth[:21][hidden],key,w,h,objects)
                    covered=np.logical_or.reduce(list(hits.values())) if hits else np.zeros(int(hidden.sum()),bool)
                    rev_hidden+=int(hidden.sum());rev_empty+=int((~covered).sum())
            frames.append(u)
        out.extend(dict(scen=scene['id'],del_id=group,ockluderade_prov=n,synliga_maskprov=den,
                        andel=n/max(den,1),flaggad=n/max(den,1)>GRANS and n>=10,rutor=frames)
                   for group,(n,den) in sorted(count.items()))
        reverse.append(dict(scen=scene['id'],mojligt_dolda_punkter=rev_hidden,utan_mallstod=rev_empty,
                            andel=rev_empty/max(rev_hidden,1),status='rapport_endast',
                            osakerhet='Saknad mask är inte bevis för möbel; bbox och unionmask kan missa synliga ben. Inga nya möbler läggs till.'))
    return dict(per_del=out,omvand=reverse,grans_andel=GRANS,djupmarginal_m=DJUPMARGINAL_M,
                metod='Var sjätte ruta och sista rutan; unionmask inom egen bbox, var tredje maskpixel. Djup från närmaste sparad MHR70-punkt. Mätkamera före regi. Provandel, inte exakt hudarea.')


def los(plan):
    """Minimera borttagna delar per scen; flytta aldrig ett uppmätt ankare.

    En del med skyddat följankare saknar mätt frihet i XY. Måttintervall
    saknas för fotavtrycket. Då är lokal utelämning ett mindre påstående
    än att hitta på nya dimensioner eller flytta ankaret.
    """
    records=[];before=mat(plan,records);actions=[];objects=plan['objekt'];new=[]
    scenes=plan.get('scener') or plan['matkamera']['scener']
    blocked={(r['scen'],r['del_id']) for r in before['per_del'] if r['flaggad']}
    from skymning_disk import valj
    parts,handled,detailactions=valj(records,blocked,GRANS);blocked-=handled
    for obj in objects:
        group=obj['id'].split(':')[0]
        if not any(g==group for _,g in blocked) and not any(id==obj['id'] for _,id in parts):new.append(obj);continue
        start,end=obj.get('synlig_ut',[0,len(plan['kallrutor'])]);intervals=[]
        for s in scenes:
            lo=max(start,s['ut'][0]);hi=min(end,s['ut'][1])
            if lo>=hi:continue
            if (s['id'],group) in blocked or (s['id'],obj['id']) in parts:continue
            if intervals and intervals[-1][1]==lo:intervals[-1][1]=hi
            else:intervals.append([lo,hi])
        for interval in intervals:
            o=copy.deepcopy(obj);o['synlig_ut']=interval;new.append(o)
    for scene,group in sorted(blocked):
        actions.append(dict(scen=scene,del_id=group,atgard='utelämnad endast i denna scen',status='antagen',
                            orsak='Minst 2 % av synliga maskprov skyms. Höjd/ankare skyddas av kroppsevidens; inget uppmätt ändringsintervall för fotavtrycket. Lokal utelämning bevarar alla ankare.'))
    actions.extend(detailactions)
    plan['objekt']=new;after=mat(plan) if actions else before
    return dict(fore=before,efter=after,atgarder=actions)
