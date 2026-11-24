"""Längdbevarande stöd för uttryckligen dolda ben. Inga uppmätta handleder flyttas.

Benmått kommer från personens poser, inte den generiska FBX-viloposen.
Överkropp och bäcken skyddas. Dolda ben får personens konstanta medianmått.
"""
import json
import math
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ingest'))
from kroppsstod import NAMN, IX, BEN, rikta, quat, qmul

FORALDER=np.array(json.loads((Path(__file__).parent/'tro_rigg.json').read_text(encoding='utf-8'))['foralder'])
SATE_INTERVALL_M=(.43,.48)  # Prior: vanlig restaurangstol, inte mätt sittyta.
SULA_M=.12                # Antagen säker fotledshöjd; faktisk hud kontrolleras i Blender.


def matt(poser):
    """Personmått: median led–förälder i de befintliga mätposerna, meter."""
    p=np.asarray(poser)[...,:3]/100
    lengths=np.zeros(len(NAMN))
    for j in BEN:
        lengths[j]=np.median(np.linalg.norm(p[:,j]-p[:,FORALDER[j]],axis=-1))
    return lengths.tolist()


def sitt_hojd(hip, mjukdel=.11):
    onskad=hip-mjukdel
    return dict(hojd_m=float(np.clip(onskad,*SATE_INTERVALL_M)),onskad_m=float(onskad),
                intervall_m=list(SATE_INTERVALL_M),inom_intervall=bool(SATE_INTERVALL_M[0]<=onskad<=SATE_INTERVALL_M[1]),
                backen_over_sits_m=float(hip-np.clip(onskad,*SATE_INTERVALL_M)),backen_over_sits_prior_m=[.02,.15],
                backenstod_inom_prior=bool(.02<=hip-np.clip(onskad,*SATE_INTERVALL_M)<=.15),
                status='antagen',metod='Mätt MHR root minus antagen överhöjd 11 cm, begränsad av sitsprior 43–48 cm. Root är inte en mätt sittyta; faktisk överhöjd och rest loggas. Bäckenet flyttas aldrig.')


def enhet(v, reserv):
    n=np.linalg.norm(v)
    return v/n if n>1e-10 else np.array(reserv,float)


def begransa(pose,Q,T,ankare,ben_synliga=None,langder=None,_sulpass=True,skyddade_knan=None):
    rapport=dict(leder=[],orsak='Synliga ben eller saknad synlighetsflagga: oförändrat.')
    if ben_synliga is None or bool(ben_synliga) or not ankare or ankare['typ'] not in ('sate','staplats','sta_bakom'):
        return pose.copy(),rapport
    # Behåll dubbel precision: längdtestets tolerans är 0,001 mm.
    P=pose.astype(float).copy();X=pose[:,:3]/100@Q.T+T;Y=X.copy()
    floor=ankare['pos_m'][2]; seated=ankare['typ']=='sate'
    f=np.array([math.cos(ankare['riktning_rad']),math.sin(ankare['riktning_rad']),0.])
    lens=np.array(langder if langder is not None else matt(pose[None]))
    vrid={};detaljer=[];skydd=set()
    for side,sida in enumerate('lr'):
        up,low,foot,ball=[IX[sida+'_'+n] for n in ('upleg','lowleg','foot','ball')]
        # Höftens förankring i skyddat bäcken har också personens fasta mått.
        protected=bool(skyddade_knan and skyddade_knan[side])
        if protected:
            skydd.update(j for j in BEN if NAMN[j].startswith(sida+'_upleg'))
            skydd.add(low)
        Y[up]=X[up] if protected else X[IX['root']]+enhet(X[up]-X[IX['root']], [1,0,0])*lens[up]
        h=Y[up]; la,lb=lens[low],lens[foot]
        ankle=floor+ankare.get('sula_fotled_m',SULA_M)
        if protected:
            # Synligt knä och hela låret behåller uppmätta lägen. Bara
            # skymd vad/fot passas, med personens fasta vadlängd.
            k=X[low].copy();drop=min(lb,max(0.,k[2]-ankle))
            direction=enhet(np.r_[X[foot,:2]-k[:2],0.],f)
            a=k+direction*math.sqrt(max(0.,lb*lb-drop*drop));a[2]=k[2]-drop
            val='synligt knä skyddat; '+('foten hänger' if a[2]>ankle+1e-6 else 'dold fot till golv')
        elif seated:
            # Horisontellt lår är en poseprior, inte en anatomisk begränsning.
            # Sänk knät när vaden ensam inte når. Båda benlängderna är fasta.
            knee_drop=min(la,max(0.,h[2]-ankle-lb))
            k=h+f*math.sqrt(max(0.,la*la-knee_drop*knee_drop));k[2]-=knee_drop
            drop=min(lb,max(0.,k[2]-ankle))
            a=k+f*math.sqrt(max(0.,lb*lb-drop*drop));a[2]=k[2]-drop
            val='foten hänger' if a[2]>ankle+1e-6 else 'golvkontakt med böjt knä'
        else:
            # Behåll höften. Närmaste nåbara golvpunkt till uppmätt fot.
            a=X[foot].copy();a[2]=ankle
            dz=a[2]-h[2];Lmax=la+lb-1e-8;Lmin=abs(la-lb)+1e-8
            if abs(dz)>Lmax:
                # Om golvet är onåbart utan att ändra skyddat bäcken måste foten hänga.
                a=h+np.array([0.,0.,-Lmax]);val='golvet onåbart med skyddat bäcken; foten hänger'
            else:
                horizontal=a[:2]-h[:2];maxxy=math.sqrt(max(0.,Lmax*Lmax-dz*dz))
                if np.linalg.norm(horizontal)>maxxy:a[:2]=h[:2]+enhet(np.r_[horizontal,0.],f)[:2]*maxxy
                val='knäböjning; bäcken oförändrat (minst ändring av uppmätta data)'
            d=a-h;L=np.linalg.norm(d)
            if L<Lmin:a=h+enhet(d,-f)*Lmin;d=a-h;L=Lmin
            u=enhet(d,[0,0,-1]);n=X[low]-h;n=enhet(n-(n@u)*u,f)
            c=np.clip((la*la+L*L-lb*lb)/(2*la*L),-1.,1.)
            k=h+la*(c*u+math.sqrt(max(0.,1-c*c))*n)
        ru=np.eye(3) if protected else rikta(X[low]-X[up],k-h);rl=rikta(X[foot]-X[low],a-k)
        rf=rikta(X[ball]-X[foot],f)
        Y[low]=k;Y[foot]=a
        for j in BEN:
            name=NAMN[j]
            if not name.startswith(sida+'_'):continue
            if 'upleg' in name: origin,dest,r=X[up],h,ru
            elif 'lowleg' in name: origin,dest,r=X[low],k,rl
            else: origin,dest,r=X[foot],a,rf
            if j not in (up,low,foot):Y[j]=dest+r@(X[j]-origin)
            vrid[j]=r
        # Alla grenleder, även twist och fotens småleder, får fasta personmått.
        for j in BEN:
            if not NAMN[j].startswith(sida+'_') or j in (up,low,foot) or j in skydd:continue
            parent=FORALDER[j]
            Y[j]=Y[parent]+enhet(Y[j]-Y[parent],f)*lens[j]
        detaljer.append(dict(sida=sida,val=val,lar_m=float(la),vad_m=float(lb),fotled_z_m=float(Y[foot,2])))
    for j in BEN:
        if j in skydd and j not in (IX['l_lowleg'],IX['r_lowleg']):continue
        P[j,:3]=Q.T@(Y[j]-T)*100
        P[j,3:7]=qmul(quat(Q.T@vrid[j]@Q),pose[j,3:7])
    fel=max(abs(np.linalg.norm(Y[j]-Y[FORALDER[j]])-lens[j]) for j in BEN if j not in skydd)
    assert fel<1e-7,('Benlängd ändrad',fel)
    rapport=dict(leder=[NAMN[j] for j in BEN if j not in skydd or j in (IX['l_lowleg'],IX['r_lowleg'])],
                  skyddade_ledlagen=[NAMN[j] for j in sorted(skydd)],
                  orsak='Dolda bensegment får fasta personmått. Synligt lår/knäläge behåller sina mätvärden; dess befintliga längdvariation skalas inte bort. Bäcken och överkropp skyddas.',
                  benlangd_maxfel_m=float(fel),backen_z_m=float(Y[IX['root'],2]),sate_z_m=floor+ankare.get('sate_hojd_m',0),
                  fotled_z_m=[float(Y[IX[s+'_foot'],2]) for s in 'lr'],ben=detaljer,overkropp_max_andring=0.,
                  status='antagen',matt_kalla='Benlängder: median ur personens mätposer. Sulan: linjär skinning av uppmätt FBX-hud. Stödposen är antagen.')
    if _sulpass:
        from trosula import lagsta
        sole=lagsta(P,Q,T);height=ankare.get('sula_fotled_m',SULA_M)
        for _ in range(4):
            if seated and sole>=floor+1e-4 and any(b['val']=='foten hänger' for b in rapport['ben']):break
            if abs(sole-floor-1e-4)<1e-7:break
            height+=floor+1e-4-sole
            P,rapport=begransa(pose,Q,T,dict(ankare,sula_fotled_m=height),ben_synliga,langder,False,skyddade_knan)
            sole=lagsta(P,Q,T)
        rapport['sula_lagst_z_m']=sole;rapport['sula_fotled_m']=height
        rapport['sulkontakt_metod']='Uppmätt FBX-hud och benvikter i numpy; 0,1 mm antagen säkerhetsmarginal. Bäcken orört.'
        assert sole>=floor-1e-7,('Sula under golvet',sole,floor)
    return P,rapport
