"""Stöd från mallankare, endast för ben som ingest markerat osynliga.

Indata är MHR:s globala poser. Ingen translation av hela kroppen görs:
rygg, armar och huvud kopieras byte för byte, även när bäckenet ändras.
Saknad synlighetsflagga betyder skyddad, aldrig rätt att gissa.
"""
import json
import math
from pathlib import Path
import numpy as np

NAMN = json.loads((Path(__file__).parent/'mhr_ledernamn.json').read_text(encoding='utf-8'))
IX = {n:i for i,n in enumerate(NAMN)}
MALL_TALED_OVER_GOLV_M = .025   # Mallvärde: tåledens höjd för en enkel sula.
BEN = [i for i,n in enumerate(NAMN) if n.startswith(('l_upleg','r_upleg','l_lowleg','r_lowleg','l_foot','r_foot','l_talocrural','r_talocrural','l_subtalar','r_subtalar','l_transversetarsal','r_transversetarsal','l_ball','r_ball'))]


def rikta(a,b):
    a=a/max(np.linalg.norm(a),1e-12); b=b/max(np.linalg.norm(b),1e-12)
    v=np.cross(a,b); c=float(np.clip(a@b,-1,1))
    if c < -1+1e-8:
        v=np.cross(a,[1.,0,0] if abs(a[0])<.8 else [0.,1,0]);v/=np.linalg.norm(v)
        return 2*np.outer(v,v)-np.eye(3)
    x,y,z=v; K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+K+K@K/max(1+c,1e-12)


def quat(R):
    # Egen matris -> xyzw, även för en halv rotation; kräver inget scipy i Blender.
    K=np.array([[R[0,0]-R[1,1]-R[2,2],R[1,0]+R[0,1],R[2,0]+R[0,2],R[2,1]-R[1,2]],
                [R[1,0]+R[0,1],R[1,1]-R[0,0]-R[2,2],R[2,1]+R[1,2],R[0,2]-R[2,0]],
                [R[2,0]+R[0,2],R[2,1]+R[1,2],R[2,2]-R[0,0]-R[1,1],R[1,0]-R[0,1]],
                [R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1],np.trace(R)]])/3
    _,v=np.linalg.eigh(K);q=v[:,-1]
    return q if q[3]>=0 else -q


def qmul(a,b):
    return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]


def begransa(pose,Q,T,ankare,ben_synliga=None):
    """Bevara synliga ben helt. Returnera ny modellpose och granskningsdata.

    Stolsitsen bär låren; höftleden ligger mallens mjukdelsmått över sitsen.
    Vrist och tå har mallens sulhöjd över golv. Benlängderna från MHR behålls
    i låret; underbenets ändring mäts eftersom bildens skala kan vara fel.
    """
    rapport=dict(leder=[],orsak='Synliga ben eller saknad synlighetsflagga: oförändrat.')
    if ben_synliga is None or bool(ben_synliga) or ankare is None: return pose.copy(),rapport
    if ankare['typ'] not in ('sate','staplats','sta_bakom'): return pose.copy(),rapport
    P=pose.copy(); X=pose[:,:3]/100@Q.T+T; Y=X.copy(); floor=ankare['pos_m'][2]
    f=np.array([math.cos(ankare['riktning_rad']),math.sin(ankare['riktning_rad']),0.])
    root=IX['root']; seated=ankare['typ']=='sate'
    if seated:
        # X/Y följer uppmätt rörelse; endast osynligt bäcken sänks till stolstödet.
        Y[root,2]=floor+ankare['sate_hojd_m']+ankare.get('backen_over_sate_m',.11)
        delta=Y[root]-X[root]
        Y[BEN]+=delta
    vrid={}; langd=[]
    for sida in 'lr':
        up,low,foot,ball=[IX[sida+'_'+s] for s in ('upleg','lowleg','foot','ball')]
        h=X[up];k=X[low];a=X[foot];la=np.linalg.norm(k-h)
        h2=Y[up]
        if seated:
            k2=h2+f*la   # låret ligger horisontellt på sitsen
            a2=k2.copy();a2[2]=floor+ankare.get('fotled_over_golv_m',.065)
        else:
            a2=a.copy();a2[2]=floor+ankare.get('fotled_over_golv_m',.065)
            d=a2-h2;L=np.linalg.norm(d);lb=np.linalg.norm(a-k)
            # Stående knä i originalplanet. Överskriden räckvidd redovisas nedan.
            u=d/max(L,1e-9);n=k-h-((k-h)@u)*u
            if np.linalg.norm(n)<1e-8:n=f
            n/=np.linalg.norm(n);c=np.clip((la*la+L*L-lb*lb)/(2*la*max(L,1e-9)),-1,1)
            k2=h2+la*(c*u+math.sqrt(max(0.,1-c*c))*n)
        ru=rikta(k-h,k2-h2);rl=rikta(a-k,a2-k2)
        toe=X[ball]-a;target=f*np.linalg.norm(toe);target[2]=MALL_TALED_OVER_GOLV_M-ankare.get('fotled_over_golv_m',.065)
        rf=rikta(toe,target)
        for j in BEN:
            name=NAMN[j]
            if not name.startswith(sida+'_'):continue
            if 'upleg' in name: origin,dest,r=h,h2,ru
            elif 'lowleg' in name: origin,dest,r=k,k2,rl
            else: origin,dest,r=a,a2,rf
            Y[j]=dest+r@(X[j]-origin);vrid[j]=r
        langd.append(dict(sida=sida,underben_fore_m=float(np.linalg.norm(a-k)),underben_efter_m=float(np.linalg.norm(a2-k2))))
    changed=BEN+([root] if seated else [])
    for j in changed:
        P[j,:3]=Q.T@(Y[j]-T)*100
        if j in vrid:P[j,3:7]=qmul(quat(Q.T@vrid[j]@Q),pose[j,3:7])
    rapport=dict(leder=[NAMN[j] for j in sorted(changed)],orsak='Ingest ben_synliga=false; '+('sittankare ger sits, lår och golvkontakt.' if seated else 'ståankare ger golvkontakt.'),
                 backen_z_m=float(Y[root,2]),sate_z_m=floor+ankare.get('sate_hojd_m',0),fotled_z_m=[float(Y[IX[s+'_foot'],2]) for s in 'lr'],
                 underben=langd,overkropp_max_andring=0.,status='antagen',matt_kalla='Stödets höjder från mall, benlängder från MHR.')
    return P,rapport
