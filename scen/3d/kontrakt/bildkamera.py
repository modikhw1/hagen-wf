"""Passa slutkameran mot originalets 2D-läsning utan att flytta kroppar.

Gäller bara deklarerade rum. Golv, platser, sitthöjder och kamerans z lämnas
orörda. Per scen får en gemensam xy-förskjutning, yaw, pitch, roll och lins
ändras. En kamera som redan ligger inom bildtrohetens gränser bevaras exakt.
"""
import copy
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from trohet import (KP, LED, envelope, iou, las_sekvens, ruta, synliga_par,
                     slutbild_statistik)


def _rx(a):
    c,s=math.cos(a),math.sin(a);return np.array([[1.,0,0],[0,c,-s],[0,s,c]])


def _rz(a):
    c,s=math.cos(a),math.sin(a);return np.array([[c,-s,0],[s,c,0],[0,0,1.]])


def _kamera(key, p):
    """Ny world_from_camera. p = dx, dy, yaw(värld), pitch/roll(lokalt), log(linsskala)."""
    M=np.array(key['matris'],float);N=M.copy();N[:3,3]+=[p[0],p[1],0.]
    N[:3,:3]=_rz(p[2])@M[:3,:3]@_rx(p[3])@_rz(p[4])
    return N,float(key['lins_mm']*math.exp(p[5]))


def _projicera(x, key, p, w, h, sensor=36.):
    M,lins=_kamera(key,p);c=(np.asarray(x)-M[:3,3])@M[:3,:3]
    fok=lins/sensor*w
    return c[...,:2]/(-c[...,2:3])*[fok,-fok]+[w/2,h/2]


def _matt(obs, keys, p, w, h):
    offset=[];skala=[];ious=[]
    for o in obs:
        uv=_projicera(o['x'],keys[o['u']],p,w,h);target=o['target']
        offset.extend(np.linalg.norm(uv-target,axis=1));a,b=envelope(uv),envelope(target)
        skala.append(float((a[3]-a[1])/max(float(b[3]-b[1]),1.)));ious.append(iou(a,b))
    return slutbild_statistik(offset,skala,ious,h)


def _optimera(obs, keys, w, h, undre=None, ovre=None):
    """Ren optimeringskärna, även användbar i syntetiska prov."""
    lo=np.array(undre if undre is not None else [-3.,-3.,-math.pi/6,-math.pi/6,-math.pi/6,math.log(.5)])
    hi=np.array(ovre if ovre is not None else [ 3., 3., math.pi/6, math.pi/6, math.pi/6,math.log(2.)])
    def rest(p):
        r=[]
        for o in obs:
            r.extend(((_projicera(o['x'],keys[o['u']],p,w,h)-o['target'])/h).ravel())
        # Svag, dimensionslös prior gör den minsta ändringen entydig utan att dölja ett bildfel.
        r.extend((p/np.array([3.,3.,math.pi/6,math.pi/6,math.pi/6,math.log(2.)])*1e-4).tolist())
        return np.asarray(r)
    start=np.minimum(np.maximum(np.zeros(6),lo+1e-12),hi-1e-12)
    return least_squares(rest,start,bounds=(lo,hi),method='trf',loss='soft_l1',f_scale=.01,max_nfev=160).x


def _observationer(plan, scen):
    w0=plan['kallbild_bredd'];h0=plan['kallbild_hojd'];w=plan['utdata']['bredd'];h=plan['utdata']['hojd'];scale=np.array([w/w0,h/h0])
    obs=[];roller=set()
    for pm in scen['personer']:
        if pm.get('narvaro'):continue
        s=las_sekvens(pm['rorelse']);v=dict(np.load(scen['varld']));folder=Path(pm['rorelse']).parent
        pid=str(pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]);roller.add(pm['id'])
        for u in range(*scen['ut']):
            f=scen['lokal_start']+u-scen['ut'][0];raw=folder/'kropp'/pid/f'{f:04d}.npz'
            if not s['inom'][f] or not raw.exists():continue
            with np.load(raw) as b:
                ok=synliga_par(bool(s['ben_synliga'][f]) if 'ben_synliga' in s else True)
                obs.append(dict(u=u,x=ruta(scen,pm,f,True,(s,v))[LED][ok],target=b['pred_keypoints_2d'][KP][ok]*scale))
    return obs,sorted(roller)


def _xy_granser(plan, sid, key):
    """Deklarerad kamera-xy: tal är hårt, [min,max] är tillåtet intervall; annars ±3 m."""
    dekl=next((p.get('deklarerat',{}) for p in plan.get('plats',[]) if sid in p.get('scener',[])),{})
    xy=(dekl.get('kamera_xy_m') or {}).get(sid);lo=[-3.,-3.];hi=[3.,3.]
    if not xy:return lo,hi,'fri (ingen deklarerad xy)'
    cur=np.array(key['matris'])[:2,3]
    for i,n in enumerate(('x_m','y_m')):
        v=xy.get(n)
        if v is None:continue
        if isinstance(v,(list,tuple)):lo[i],hi[i]=float(v[0])-cur[i],float(v[1])-cur[i]
        else:lo[i],hi[i]=float(v)-cur[i]-1e-10,float(v)-cur[i]+1e-10
    return lo,hi,'deklarerad xy/intervall'


def los(plan):
    """Lös och skriv ``kvalitet.bildkamera``. Returnerar rapporten eller None på gamla vägen."""
    if not plan.get('plats') or not any(p.get('deklarerat') for p in plan['plats']):return None
    w=plan['utdata']['bredd'];h=plan['utdata']['hojd'];keys=plan['renderkamera']['nycklar'];poster=[]
    for scen in plan.get('scener') or plan['matkamera']['scener']:
        obs,roller=_observationer(plan,scen)
        if not obs:
            poster.append(dict(scen=scen['id'],status='saknas',roller=roller,orsak='inga jämförbara 2D-rutor'));continue
        p0=np.zeros(6);fore=_matt(obs,keys,p0,w,h);xylo,xyhi,xyregel=_xy_granser(plan,scen['id'],keys[scen['ut'][0]])
        lo=[*xylo,-math.pi/6,-math.pi/6,-math.pi/6,math.log(.5)];hi=[*xyhi,math.pi/6,math.pi/6,math.pi/6,math.log(2.)]
        p=_optimera(obs,keys,w,h,lo,hi);efter=_matt(obs,keys,p,w,h)
        # Bilden måste först vara flaggad. Minst 10 % och 2 px förbättring krävs;
        # annars är ändringen bara överpassning av estimatorbrus.
        vinst=fore.get('medel_offset_px',0)-efter.get('medel_offset_px',0)
        tillampa=bool(fore.get('flaggad') and vinst>=max(2.,.1*fore['medel_offset_px']) and efter['bbox_iou']>=fore['bbox_iou']-.01)
        if tillampa:
            for u in range(*scen['ut']):
                M,lins=_kamera(keys[u],p);keys[u]['matris']=M.tolist();keys[u]['lins_mm']=lins
        poster.append(dict(scen=scen['id'],status='andrad' if tillampa else 'bevarad',roller=roller,
                           orsak=('slutbilden förbättrades över miniminivån' if tillampa else 'startkameran är inom gränserna' if not fore.get('flaggad') else 'kandidatens förbättring var för liten'),
                           xy_regel=xyregel,kamerahojd_bunden=True,fore=fore,efter=efter if tillampa else fore,
                           kandidat=efter,justering=dict(dx_m=float(p[0]),dy_m=float(p[1]),yaw_grader=math.degrees(p[2]),pitch_grader=math.degrees(p[3]),roll_grader=math.degrees(p[4]),linsfaktor=math.exp(p[5]))))
    rapport=dict(status='lost',metod='Gemensam slutkamera per scen: xy, yaw, pitch, roll och lins mot samma rollers 2D-leder; kamerans z och alla kroppar orörda. Kamera inom bildtrohetens gränser bevaras exakt.',scener=poster)
    plan['kvalitet']['bildkamera']=copy.deepcopy(rapport)
    return rapport
