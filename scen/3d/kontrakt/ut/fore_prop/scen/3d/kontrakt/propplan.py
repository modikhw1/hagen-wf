"""Upplöst rekvisita med handfäste, kamerahand och stöd på mallens ytor.

Alla nycklar ligger på utdataklockan. Samma matriser används i Blender och
i kvalitetsmåttet. En okänd placering ger ingen byggd geometri.
"""
import copy
import json
from itertools import product
from pathlib import Path
import numpy as np
from propbank import hamta
from trohet import IX, ruta_pose, projicera
from kroppmatt import rotation

def fran_kalla(p, sid):
    r=p.get('rekonstruktion')
    if not r: return None
    s=next((s for s in r['scener'] if s['scen']==sid),None)
    if s is None: return None
    return dict(id=p['id'],namn='prop:'+p['id'],typ='rekvisita',prop_typ=p['typ'],
                pos_m=None,rotation_rad=[0,0,0],matt_m=r['bank']['matt'],farg='#e2ac46',top_slope=0,
                propdata=copy.deepcopy(s),ursprung=copy.deepcopy(r['ursprung']),bank=copy.deepcopy(r['bank']))

def byt(o, typ, matt=None):
    b=hamta(typ)
    o.update(prop_typ=typ,bank=b,namn='prop:'+typ+':'+o['id'])
    # Produktbyte ändrar formen men behåller uppmätt utsträckning och greppplats
    # om CM inte begär en ny storlek.
    if matt is not None: o['matt_m']=[matt[0],matt[2],matt[1]];o['matt_explicit']=True
    o['edit']=dict(typ='cm',metod='Propbyte i regi.',fiktiv=b.get('fiktiv',False))

def ny(e):
    b=hamta(e['typ']); f=e.get('faste')
    o=dict(id=e['ny_id'],namn='prop:'+e['ny_id'],typ='rekvisita',prop_typ=e['typ'],pos_m=None,
           rotation_rad=[0,0,0],matt_m=b['matt'],farg='#e2ac46',top_slope=0,bank=b,
           propdata=dict(lage='hand' if f else 'explicit',hallare=f['person'] if f else None,
                         led=f['led'] if f else None,hand=f.get('hand') if f else None,bildregioner=[],ursprung={}),
           ursprung=dict(typ='cm',metod='Tillägg i regi, mått från bank om CM inte anger mått.'))
    if e.get('matt_m') is not None:
        o['matt_m']=[e['matt_m'][0],e['matt_m'][2],e['matt_m'][1]];o['matt_explicit']=True
    return o

def sikt(key, uv, w, h):
    m=np.array(key['matris']); f=key['lins_mm']/36*w
    return m[:3,3],m[:3,:3]@np.array([(uv[0]-w/2)/f,-(uv[1]-h/2)/f,-1.])

def vid_djup(key,uv,depth,w,h):
    c,r=sikt(key,uv,w,h);return c+r*depth

def handmatris(scen,pm,f,data=None):
    pose,q,t=ruta_pose(scen,pm,f,True,data)
    return pose,q,t

def fast_i_hand(pos, rot, offset, grip):
    """Propens rot: greppunkten träffar handens lokala offset exakt."""
    return np.asarray(pos)+np.asarray(rot)@(np.asarray(offset)-np.asarray(grip))

def bounds(o, key, w,h):
    pts=[];M=np.array(key['matris']);size=np.array(o['matt_m'])
    for d in o['bank']['delar']:
        center=np.array(d['pos'])*size; extent=np.array(d['matt'])*size/2
        pts.extend([center+extent*v for v in product([-1,1],repeat=3)])
    pts=np.array(pts)@M[:3,:3].T+M[:3,3]
    camera=np.array(key['kamera']['matris'])
    z=(pts-camera[:3,3])@camera[:3,:3]
    if (z[:,2]>=-.01).any():return None
    uv=projicera(pts,key['kamera'],w,h)
    return np.r_[uv.min(0),uv.max(0)].tolist()

def los(plan):
    """Kör efter kropp/stöd och skymningsbeslut; ändrar aldrig deras data."""
    w=plan['kallbild_bredd'];h=plan.get('kallbild_hojd',round(w*plan['utdata']['hojd']/plan['utdata']['bredd']))
    report=[]
    for o in plan.get('props',[]):
        sc=next(s for s in plan['scener'] if s['id']==o['scen']);p=o['propdata'];a,b=sc['ut'];refs=p.get('bildregioner',[])
        keys=plan['renderkamera']['nycklar']; mode=p['lage']; reasons=[]; o['nycklar']=[]
        pm=next((x for x in sc['personer'] if x['id']==p.get('hallare')),None)
        fref=refs[0]['lokal_ruta'] if refs else sc['lokal_start'];uref=a+fref-sc['lokal_start']
        uref=int(np.clip(uref,a,b-1)); center=np.mean(np.array(refs[0]['box_px']).reshape(2,2),0) if refs else None
        size=np.array(o['matt_m'],float); R0=np.eye(3); offset=np.zeros(3);grip=np.array(o['bank']['grepp'])
        data=(dict(np.load(pm['rorelse'])),dict(np.load(sc['varld']))) if pm else None
        h0=None; rr0=None; pos=None; depth=None; track={};surface=None
        if mode=='hand' and pm and p.get('led') in IX:
            pose,q,t=handmatris(sc,pm,fref,data);j=IX[p['led']];h0=pose[j,:3]/100@q.T+t;rr0=q@rotation(pose[j,3:7])
            cam=np.array(keys[uref]['matris']);depth=-float(((h0-cam[:3,3])@cam[:3,:3])[2])
            if center is not None:
                dest=vid_djup(keys[uref],center,depth,w,h)
                offset=dest-h0
            else: reasons.append('CM-fäste utan uppmätt bildregion; bankens greppunkt används.')
        elif mode=='kamera_hand':
            folder=Path(sc['varld']).parent;f=folder/'personer_matning.json'
            track=json.loads(f.read_text()).get(p.get('spar_id'),{}) if f.exists() else {}
            depth=.65
            if not track: reasons.append('Förgrundsspårets boxar saknas; ingen kamerahand byggs.')
        elif mode=='yta' and center is not None:
            # Bara verkliga mallskivor med synlighet i scenen är tillåtna stöd.
            candidates=[x for x in plan['objekt'] if ('skiva' in x['id']) and x['synlig_ut'][0]<=uref<x['synlig_ut'][1]
                        and (x['id'].startswith('bord') if p.get('yta')=='bord' else x['id'].startswith('disk'))]
            best=None;c,ray=sikt(keys[uref],center,w,h)
            for surf in candidates:
                z=surf['pos_m'][2]+surf['matt_m'][2]/2
                if abs(ray[2])<1e-8:continue
                d=(z-c[2])/ray[2]
                if d<=0:continue
                pt=c+ray*d;yaw=surf['rotation_rad'][2];cy,sy=np.cos(yaw),np.sin(yaw);rz=np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])
                local=rz.T@(pt-np.array(surf['pos_m']));limit=np.maximum(np.array(surf['matt_m'][:2])/2-.02,0)
                clipped=np.clip(local[:2],-limit,limit);dist=np.linalg.norm(local[:2]-clipped)
                if best is None or dist<best[0]:best=(dist,surf,pt,d,rz,local,clipped)
            if best:
                dist,surface,pos,depth,R0,local,clipped=best
                if dist>.001:
                    reasons.append(f'Siktlinjen missar mallskivan med {dist:.3f} m. Placeringen begränsad till dess kant, antagen; se bildfelet.')
                    local[:2]=clipped;pos=np.array(surface['pos_m'])+R0@local
                o['yta_id']=surface['id']
            else: reasons.append('Ingen synlig mallskiva framför kameran; position saknas och föremålet utelämnas.')
        elif mode=='explicit' and o.get('pos_m') is not None:pos=np.array(o['pos_m'])
        else:reasons.append('Ingen mätbar position eller giltigt handfäste; ingen geometri uppfinns.')
        if depth is not None and depth>0 and refs and not o.get('matt_explicit'):
            width=refs[0]['box_px'][2]-refs[0]['box_px'][0];focal=keys[uref]['lins_mm']/36*w
            scale=width*depth/focal/max(size[0],1e-9);size*=scale
        o['matt_m']=size.tolist();grip=np.array(o['bank']['grepp'])*size/np.array(o['bank']['matt'])
        if surface is not None:pos[2]=surface['pos_m'][2]+surface['matt_m'][2]/2-grip[2]
        for u in range(a,b):
            f=sc['lokal_start']+u-a;M=np.eye(4);visible=True
            if mode=='hand' and h0 is not None:
                pose,q,t=handmatris(sc,pm,f,data);j=IX[p['led']];R=q@rotation(pose[j,3:7])@rr0.T
                hp=pose[j,:3]/100@q.T+t
                # Första kalibreringen ger propens rot, inte dess grepppunkt.
                M[:3,:3]=R;M[:3,3]=fast_i_hand(hp,R,offset+grip,grip)
                visible=bool(data[0]['inom'][f])
            elif mode=='kamera_hand' and track:
                known=sorted(int(i) for i in track);nearest=min(known,key=lambda i:abs(i-f));box=np.array(track[str(nearest)])
                uv=np.array([(box[0]+box[2])/2,box[1]+.12*(box[3]-box[1])])
                if center is not None:
                    box0=np.array(track[str(min(known,key=lambda i:abs(i-fref)))]);uv0=np.array([(box0[0]+box0[2])/2,box0[1]+.12*(box0[3]-box0[1])]);uv+=center-uv0
                cam=np.array(keys[u]['matris']);M[:3,:3]=cam[:3,:3]@np.diag([1,-1,-1]);M[:3,3]=vid_djup(keys[u],uv,depth,w,h)
                o['kamerahand']=dict(djup_m=depth,status='antagen',metod='Hand vid förgrundsboxens övre del; underarm till bildens underkant, kamerafäst. Ingen uppmätt anatomi.')
            elif pos is not None:M[:3,:3]=R0;M[:3,3]=pos
            else:continue
            o['nycklar'].append(dict(ut=u,matris=M.tolist(),synlig=visible))
        o['byggd']=bool(o['nycklar']);o['antaganden']=reasons
        comparisons=[]
        for ref in refs:
            u=a+ref['lokal_ruta']-sc['lokal_start'];key=next((x for x in o['nycklar'] if x['ut']==u),None)
            bb=bounds(o,dict(key,kamera=keys[u]),w,h) if key else None
            target=np.array(ref['box_px']);diff=None;ratio=None
            if bb:
                built=np.array(bb);diff=float(np.linalg.norm((built[:2]+built[2:]-target[:2]-target[2:])/2));ratio=float((built[2]-built[0])/max(target[2]-target[0],1))
            comparisons.append(dict(kallruta=ref['kallruta'],kalla_box_px=ref['box_px'],byggd_box_px=bb,centrumfel_px=diff,breddkvot=ratio))
        report.append(dict(scen=sc['id'],prop=o['id'],typ=o['prop_typ'],byggd=o['byggd'],lage=mode,
                           faste=dict(person=p.get('hallare'),led=p.get('led')),yta=o.get('yta_id'),matt_m=o['matt_m'],
                           jamforelse=comparisons,ursprung=p.get('ursprung'),antaganden=reasons))
    plan['kvalitet']['props']=report

def rapportrader(plan):
    rows=['','## Rekvisita','',
          'Byggd betyder geometri i planen, inte att föremålet säkert är synligt framför alla möbler. Regionerna är manuellt avlästa i källbilden (±2,5 % av bildmåttet); ingen objektsegmentering. Centrumfel och breddkvot använder bankformens projicerade omslutning i renderkameran på provrutorna. Lägre fel efter regionpassning är inte oberoende bevis. Handrörelse kommer från befintliga handledsleder; grepp, djup, ythöjd och dolda sidor är antagna. Källa, RGB, konfidens och alla provrutor finns i kalla och plan.', '',
          '| Scen | Prop / typ | Byggd | Fäste / yta | Centrumfel px / breddkvot (provrutor) | Antaganden |',
          '|---|---|---|---|---|---|']
    for r in plan.get('kvalitet',{}).get('props',[]):
        values='; '.join('saknas' if x['centrumfel_px'] is None else f"{x['centrumfel_px']:.1f} / {x['breddkvot']:.2f}" for x in r['jamforelse']) or 'ingen mätregion'
        place=r.get('yta') or str(r['faste']) if r['lage']!='kamera_hand' else 'kamerahand, djup antaget 0,65 m'
        rows.append(f"| {r['scen']} | {r['prop']} / {r['typ']} | {'ja' if r['byggd'] else 'NEJ'} | {place} | {values} | {'; '.join(r['antaganden']) or r['lage']+': grepp och mått delvis antagna, se kalla'} |")
    return rows
