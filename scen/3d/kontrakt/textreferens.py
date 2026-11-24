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
        x,y,bw,bh=ref['box'];mode=ref['mask'];outlined=mode=='outlined';mode=False if mode in ('white','outlined') else True if mode=='red' else 'black'
        template=mask(img,mode)[y:y+bh,x:x+bw]
        for other in ref.get('referensrutor',[]):
            cap.set(1,other);ok,extra=cap.read()
            if ok:
                othermask=mask(cv2.resize(extra,size),mode)[y:y+bh,x:x+bw]
                template=cv2.bitwise_and(template,cv2.dilate(othermask,np.ones((3,3),np.uint8)))
        count,labels,stats,_=cv2.connectedComponentsWithStats(template)
        cleaned=np.zeros_like(template)
        for label in range(1,count):
            _,_,cw,ch,area=stats[label]
            if 2<=cw<=(bw if outlined else 60) and 7<=ch<=60 and area>=8:cleaned[labels==label]=255
        if np.count_nonzero(cleaned)>30 and not outlined:template=cleaned
        positive=template>0;negative=(cv2.dilate(template,np.ones((5,5),np.uint8))>0)&~positive
        selfscore=max(.1,1.-.5*float(np.mean(mask(cv2.resize(img,size),mode)[y:y+bh,x:x+bw][negative]>0)))
        cap.set(1,a);scores=[]
        for f in range(a,b):
            ok,img=cap.read()
            if not ok:break
            mm=mask(cv2.resize(img,size),mode).astype('float32')/255
            pad=8;candidate=mm[max(0,y-pad):min(mm.shape[0],y+bh+pad),max(0,x-pad):min(mm.shape[1],x+bw+pad)]
            kernel=positive.astype('float32')/max(1,positive.sum())-.5*negative.astype('float32')/max(1,negative.sum())
            score=float(cv2.minMaxLoc(cv2.matchTemplate(candidate,kernel.astype('float32'),cv2.TM_CCORR))[1])/selfscore;scores.append(score)
        visible=np.array(scores)>=ref.get('grans',.7)
        for gap in (1,2,3):
            for i in range(1,len(visible)-gap):
                if visible[i-1] and visible[i+gap]:visible[i:i+gap]=True
        edge=np.diff(np.r_[False,visible,False].astype(int));intervals=[(int(s),int(e)) for s,e in zip(np.where(edge==1)[0],np.where(edge==-1)[0]) if e-s>=2]
        if ref.get('synlighet_rutor'):
            intervals=[(max(a,s)-a,min(b,e)-a) for s,e in ref['synlighet_rutor'] if max(a,s)<min(b,e)]
        for start,end in intervals:
            out.append(dict(id=f'st{len(out)+1}',scen=ref['scen'],text=ref['text'],start_s=(a+start)/fps,slut_s=(a+end)/fps,kalla='modell',typ='undertext' if ref.get('replik') else 'overlay',replik=ref.get('replik'),
                box=[v/scale for v in ref.get('ritbox',ref['box'])],stil=dict(font=ref['font'],storlek_px=ref['storlek_px']/scale,justering='center',farg=ref['farg'],kontur_farg=ref['kontur_farg'],kontur_px=ref['kontur_px']/scale),
                ursprung=dict(typ='uppmatt',metod='Box och radbrytning avlästa i angiven källruta; exakt pixelmask mäter när samma text syns. Ingen OCR.',referens_fil=str(p),referensruta=ref['referensruta'],stil=dict(typ='antagen',orsak='Närmaste installerade font; färg och kontur avlästa i källrutan.'),text=refs['textursprung']),konfidens=float(np.clip(np.median(np.array(scores)[visible]),0,1))))
        logs.append(dict(scen=ref['scen'],text=ref['text'],referensruta=ref['referensruta'],box=ref['box'],intervall=[[a+s,a+e] for s,e in intervals],scores=scores,grans=ref.get('grans',.7),metod='Granskad källpixelreferens; andel färgträffar i tecken minus 0,5 gånger träffar i deras närmaste omgivning. Högst tre rutors kontrastbortfall fylls.'))
        if ref.get('synlighetsmetod'):
            logs[-1]['metod']=ref['synlighetsmetod']
            for t in out:
                if t['scen']==ref['scen'] and t['text']==ref['text']:t['ursprung']['synlighet']=ref['synlighetsmetod']
    cap.release();return out,logs
