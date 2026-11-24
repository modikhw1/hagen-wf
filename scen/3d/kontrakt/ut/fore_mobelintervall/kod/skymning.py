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
# Delkontroll (10 nov, jämn-passet): tunna skenor skymde höften i b S8-S10 men utgjorde << 2 % av alla maskprov, så totalgränsen såg dem inte.
# Varje kroppsdel (närmaste MHR70-punkt) har därför egen gräns: över 10 % av delens maskprov (minst 8 prov) skymda = konflikt. Egna val.
DEL_GRANS = .10
DEL_MIN = 8
BLOCK = 16   # lådor per gång i konflikt(); begränsar arbetsminnet
DELAR = ['huvud', 'overkropp', 'hoft', 'armar_hander', 'ben_fotter']


def delkod(i):
    """MHR70-index -> delindex i DELAR."""
    i = np.asarray(i); k = np.full(i.shape, 1)
    k[i <= 4] = 0; k[(i == 9) | (i == 10)] = 2; k[((i >= 7) & (i <= 8)) | ((i >= 21) & (i <= 62))] = 3; k[((i >= 11) & (i <= 20))] = 4
    return k


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


def boxdjup_flera(origin, rays, objs):
    """boxdjup för flera lådor på en gång (rad per låda). Samma räkneuttryck som boxdjup, med lådan som första axel."""
    n=len(objs);ang=np.array([o.get('rotation_rad',[0,0,0])[2] for o in objs],float);c,s=np.cos(ang),np.sin(ang)
    R=np.zeros((n,3,3));R[:,0,0]=c;R[:,0,1]=-s;R[:,1,0]=s;R[:,1,1]=c;R[:,2,2]=1.
    pos=np.array([o['pos_m'] for o in objs],float);half=np.array([o['matt_m'] for o in objs],float)/2
    o_=np.matmul((origin-pos)[:,None,:],R)[:,0,:];d=np.matmul(rays[None],R)
    safe=np.where(np.abs(d)>1e-12,d,1e-12)
    lo=(-half-o_)[:,None,:]/safe;hi=(half-o_)[:,None,:]/safe
    enter=np.maximum(np.minimum(lo,hi).max(axis=2),0.)
    leave=np.maximum(lo,hi).min(axis=2)
    return np.where(leave>=enter,enter,np.inf)


_TRAFF={}   # (rutnyckel, art, kamera) -> {lådnyckel: packade bitar}; speglas på disk i datacache (grupp skymning_traff)


_LADNYCKEL={}   # id(objekt) -> (objekt, nyckel); gäller en mat()/forvarm()-körning


def _ladnyckel(o):
    m=_LADNYCKEL.get(id(o))
    if m is not None and m[0] is o:return m[1]
    import hashlib
    r=o.get('rotation_rad',[0,0,0])[2]
    k=hashlib.sha1(repr((tuple(float(x) for x in o['pos_m']),float(r),tuple(float(x) for x in o['matt_m']))).encode()).hexdigest()[:20]
    _LADNYCKEL[id(o)]=(o,k)
    return k


def konflikt(uv, depth, key, w, h, objects, rut=None):
    """Vilka maskprov som skyms av vilken låda. Med rut=(rutnyckel, art) minns den träffbitarna per låda, kamera och ruta.

    Svaret är samma som utan minne: det som minns är en rad per (ruta, person, kamera, lådans geometri)."""
    origin,rays=stralar(np.asarray(uv),key,w,h);limit=np.asarray(depth)-DJUPMARGINAL_M;out={}
    if rut is None:
        for i in range(0,len(objects),BLOCK):
            part=objects[i:i+BLOCK]
            for o,row in zip(part,boxdjup_flera(origin,rays,part)):out[o['id']]=row<limit
        return out
    import datacache
    ck=datacache.nyckel(dict(v=1,rut=rut,m=key['matris'],l=key['lins_mm'],dm=DJUPMARGINAL_M,kod=_kodid()))
    ent=_TRAFF.get(ck)
    if ent is None:
        ent=datacache.hamta_npz('skymning_traff',ck) or {}
        if len(_TRAFF)>4000:_TRAFF.clear()
        _TRAFF[ck]=ent
    names=[_ladnyckel(o) for o in objects];saknas=[i for i,n in enumerate(names) if n not in ent]
    if saknas:
        part_all=[objects[i] for i in saknas]
        for i in range(0,len(part_all),BLOCK):
            part=part_all[i:i+BLOCK]
            for o,row in zip(part,boxdjup_flera(origin,rays,part)):ent[_ladnyckel(o)]=np.packbits(row<limit)
        datacache.spara_npz('skymning_traff',ck,ent)
    n=len(uv)
    for o,nm in zip(objects,names):out[o['id']]=np.unpackbits(ent[nm],count=n).astype(bool)
    return out


# ---- Per källruta och person: allt som inte beror på kamera, regi eller lådor. Beständigt i datacache (grupp skymning_ruta).
_RUTOR={}
_KODID={}


_KODNU=[None]


def _kodid():
    """Innehållshash av denna fil. mat() och forvarm() räknar om den en gång per anrop (filstämpel styr)."""
    import datacache
    return _KODNU[0] or datacache.kodnyckel([__file__])


def _rutdel(raw, maskfile, f, w, h, masksig):
    """(uv, djup vid närmaste led, kroppsdel, dolda ledpunkter med djup) för en person och källruta."""
    import datacache
    key=datacache.nyckel(dict(v=1,kod=_kodid(),w=w,h=h,f=f,raw=datacache.signatur([raw]),mask=masksig))
    d=_RUTOR.get(key)
    if d is not None:return d,key
    d=datacache.hamta_npz('skymning_ruta',key)
    if d is None:
        with np.load(raw) as data:
            kp=data['pred_keypoints_2d'];depth=data['pred_keypoints_3d'][:,2]+data['pred_cam_t'][2];bb=data['bbox']
        mask=np.load(maskfile,mmap_mode='r')[f];mh,mw=mask.shape
        yy,xx=np.nonzero(mask);uv=np.c_[(xx+.5)*w/mw,(yy+.5)*h/mh]
        inside=(uv[:,0]>=bb[0])&(uv[:,0]<=bb[2])&(uv[:,1]>=bb[1])&(uv[:,1]<=bb[3]);uv=uv[inside][::3]
        if len(uv):
            nearest=np.argmin(((uv[:,None]-kp[None])**2).sum(axis=2),axis=1);dep=depth[nearest];delar=delkod(nearest)
        else:dep=depth[:0];delar=np.zeros(0,int)
        q=kp[:21];in_image=(q[:,0]>=0)&(q[:,0]<w)&(q[:,1]>=0)&(q[:,1]<h)
        mx=np.clip((q[:,0]*mw/w).astype(int),0,mw-1);my=np.clip((q[:,1]*mh/h).astype(int),0,mh-1)
        hidden=in_image&~mask[my,mx].astype(bool)
        d=dict(uv=uv,dep=dep,delar=delar,qh=q[hidden],qd=depth[:21][hidden])
        datacache.spara_npz('skymning_ruta',key,d)
    if len(_RUTOR)>8000:_RUTOR.clear()
    _RUTOR[key]=d
    return d,key


def _synliga(plan, u):
    full=[0,len(plan['kallrutor'])]
    return [o for o in plan['objekt'] if o.get('status')=='mall' and o.get('deltyp') not in ('golv','vagg','fonster','lampa')
            and o.get('synlig_ut',full)[0]<=u<o.get('synlig_ut',full)[1]]


def forvarm(plan):
    """Räknar och sparar rutdelen och träffbitarna för varje källruta (inte bara var tredje) i planens scener.

    Därefter väljer ett nytt tidsurval (trimning, borttagning, flytt, kopia) bara bland färdiga rutor. Ger antal rutor."""
    import datacache
    _KODNU[0]=None;_KODNU[0]=datacache.kodnyckel([__file__]);_LADNYCKEL.clear()
    w=plan['kallbild_bredd'];h=plan['kallbild_hojd'];n=0;sigs={}
    for scene in plan.get('scener') or plan['matkamera']['scener']:
        a,b=scene['ut']
        for u in range(a,b):
            objects=_synliga(plan,u);key=plan['matkamera']['nycklar'][u]
            f=scene['lokal_start']+u-a if plan.get('scener') else plan['kallrutor'][u]
            for pm in scene['personer']:
                folder=Path(pm['rorelse']).parent;pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
                raw=folder/'kropp'/str(pid)/f'{f:04d}.npz';maskfile=folder/'masker.npy'
                if not raw.exists() or not maskfile.exists():continue
                if folder not in sigs:sigs[folder]=datacache.signatur([maskfile])
                P,rk=_rutdel(raw,maskfile,f,w,h,sigs[folder])
                if len(P['uv']):konflikt(P['uv'],P['dep'],key,w,h,objects,(rk,'f'))
                if len(P['qh']):konflikt(P['qh'],P['qd'],key,w,h,objects,(rk,'q'))
                n+=1
    return n


def mat(plan, prov=None):
    w=plan['kallbild_bredd'];h=plan['kallbild_hojd'];out=[];reverse=[]
    import datacache;sigs={}
    _KODNU[0]=None;_KODNU[0]=datacache.kodnyckel([__file__]);_LADNYCKEL.clear()
    def masksig(folder):
        if folder not in sigs:sigs[folder]=datacache.signatur([folder/'masker.npy'])
        return sigs[folder]
    scenes=plan.get('scener') or plan['matkamera']['scener']
    for scene in scenes:
        count={};total=0;rev_hidden=0;rev_empty=0;frames=[]
        partcount={}
        a,b=scene['ut'];indices=sorted(set(range(a,b,3))|{b-1})
        for u in indices:
            objects=_synliga(plan,u)
            key=plan['matkamera']['nycklar'][u]
            f=scene['lokal_start']+u-a if plan.get('scener') else plan['kallrutor'][u]
            for pm in scene['personer']:
                folder=Path(pm['rorelse']).parent;pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
                raw=folder/'kropp'/str(pid)/f'{f:04d}.npz';maskfile=folder/'masker.npy'
                if not raw.exists() or not maskfile.exists():continue
                P,rk=_rutdel(raw,maskfile,f,w,h,masksig(folder));uv=P['uv'];delar_=P['delar']
                if len(uv):
                    hits=konflikt(uv,P['dep'],key,w,h,objects,(rk,'f'));total+=len(uv)
                    delar=delar_
                    if prov is not None:
                        for group in {o['id'].split(':')[0] for o in objects if o.get('oppen_mitt')}:
                            prov.append(dict(scen=scene['id'],grupp=group,hits={o['id']:hits[o['id']] for o in objects if o['id'].split(':')[0]==group},delar=delar))
                    for obj in objects:
                        group=obj['id'].split(':')[0]
                        # Samma möbeldels skiva och ben får inte dubbelräknas.
                        if group not in count:count[group]=[0,0]
                    for group in {o['id'].split(':')[0] for o in objects}:
                        combined=np.logical_or.reduce([hits[o['id']] for o in objects if o['id'].split(':')[0]==group])
                        count[group][0]+=int(combined.sum());count[group][1]+=len(uv)
                        pc=partcount.setdefault((scene['id'],group),np.zeros((len(DELAR),2),int))
                        for j in range(len(DELAR)):
                            sel=delar==j;pc[j,0]+=int((combined&sel).sum());pc[j,1]+=int(sel.sum())
                # Omvänd kontroll: saknad mask kan också vara segmenteringsfel.
                if len(P['qh']):
                    hits=konflikt(P['qh'],P['qd'],key,w,h,objects,(rk,'q'))
                    covered=np.logical_or.reduce(list(hits.values())) if hits else np.zeros(len(P['qh']),bool)
                    rev_hidden+=len(P['qh']);rev_empty+=int((~covered).sum())
            frames.append(u)
        for group,(n,den) in sorted(count.items()):
            pc=partcount.get((scene['id'],group),np.zeros((len(DELAR),2),int))
            worst=[dict(del_=DELAR[j],skymda=int(pc[j,0]),prov=int(pc[j,1]),andel=float(pc[j,0]/max(pc[j,1],1))) for j in range(len(DELAR)) if pc[j,0]>=DEL_MIN and pc[j,0]/max(pc[j,1],1)>DEL_GRANS]
            out.append(dict(scen=scene['id'],del_id=group,ockluderade_prov=n,synliga_maskprov=den,andel=n/max(den,1),
                            flaggad=(n/max(den,1)>GRANS and n>=10) or bool(worst),flaggade_kroppsdelar=worst,rutor=frames))
        reverse.append(dict(scen=scene['id'],mojligt_dolda_punkter=rev_hidden,utan_mallstod=rev_empty,
                            andel=rev_empty/max(rev_hidden,1),status='rapport_endast',
                            osakerhet='Saknad mask är inte bevis för möbel; bbox och unionmask kan missa synliga ben. Inga nya möbler läggs till.'))
    return dict(per_del=out,omvand=reverse,grans_andel=GRANS,djupmarginal_m=DJUPMARGINAL_M,
                metod='Var tredje ruta och sista rutan (före 10 nov var sjätte); unionmask inom egen bbox, var tredje maskpixel. Djup från närmaste sparad MHR70-punkt. Mätkamera före regi. Provandel, inte exakt hudarea.')


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
