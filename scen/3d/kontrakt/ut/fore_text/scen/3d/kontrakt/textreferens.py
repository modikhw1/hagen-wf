"""Granskade källrutor kompletterar fontsökning där typsnittet saknas lokalt."""
import copy
import json
from pathlib import Path
import cv2
import numpy as np


def las(k,video):
    p=Path(__file__).parent/'textreferenser'/(k['klipp']['id']+'.json')
    if not p.exists():return None
    from skarmtext import mask
    refs=json.loads(p.read_text(encoding='utf-8'));fps=k['tidsbas']['fps_taljare']/k['tidsbas']['fps_namnare']
    w,h=k['klipp']['video']['bredd'],k['klipp']['video']['hojd'];scale=refs['matbredd']/w
    cap=cv2.VideoCapture(str(video));out=[];logs=[]
    for ref in refs['texter']:
        sc=next(s for s in k['semantik']['scener'] if s['id']==ref['scen']);a=round(sc['start_s']*fps);b=round(sc['slut_s']*fps)
        cap.set(1,ref['referensruta']);ok,img=cap.read()
        if not ok:raise ValueError('Källreferensen kan inte läsas.')
        size=(refs['matbredd'],round(h*scale));img=cv2.resize(img,size)
        x,y,bw,bh=ref['box'];mode=ref['mask'];mode=False if mode=='white' else True if mode=='red' else 'black'
        template=mask(img,mode)[y:y+bh,x:x+bw]
        cap.set(1,a);scores=[]
        for f in range(a,b):
            ok,img=cap.read()
            if not ok:break
            candidate=mask(cv2.resize(img,size),mode)[y:y+bh,x:x+bw]
            score=float(cv2.matchTemplate(candidate,template,cv2.TM_CCOEFF_NORMED)[0,0]);scores.append(score)
        visible=np.array(scores)>=ref.get('grans',.5)
        for gap in (1,2,3):
            for i in range(1,len(visible)-gap):
                if visible[i-1] and visible[i+gap]:visible[i:i+gap]=True
        edge=np.diff(np.r_[False,visible,False].astype(int));intervals=[(int(s),int(e)) for s,e in zip(np.where(edge==1)[0],np.where(edge==-1)[0]) if e-s>=2]
        for start,end in intervals:
            out.append(dict(id=f'st{len(out)+1}',scen=ref['scen'],text=ref['text'],start_s=(a+start)/fps,slut_s=(a+end)/fps,kalla='modell',typ='undertext' if ref.get('replik') else 'overlay',replik=ref.get('replik'),
                box=[v/scale for v in ref.get('ritbox',ref['box'])],stil=dict(font=ref['font'],storlek_px=ref['storlek_px']/scale,justering='center',farg=ref['farg'],kontur_farg=ref['kontur_farg'],kontur_px=ref['kontur_px']/scale),
                ursprung=dict(typ='uppmatt',metod='Box och radbrytning avlästa i angiven källruta; exakt pixelmask mäter när samma text syns. Ingen OCR.',referens_fil=str(p),referensruta=ref['referensruta'],stil=dict(typ='antagen',orsak='Närmaste installerade font; färg och kontur avlästa i källrutan.'),text=refs['textursprung']),konfidens=float(np.median(np.array(scores)[visible]))))
        logs.append(dict(scen=ref['scen'],text=ref['text'],referensruta=ref['referensruta'],box=ref['box'],intervall=[[a+s,a+e] for s,e in intervals],scores=scores,grans=ref.get('grans',.5),metod='Granskad källpixelreferens; korrelation i samma region, med högst tre rutors kontrastbortfall.'))
    cap.release();return out,logs
