"""Mät textens lokala bildmatchning; ingen OCR eller oberoende sanningsdata."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from textarbete import jsonfil
from textmalning import rita
from skarmtext import mask

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]
sys.path.insert(0,str(HIT/'semantik'))
from sem_gemensamt import KLIPP


def granska(clip,folder):
    p=json.loads((HIT/f'ut/{clip}/{folder}/plan.json').read_text(encoding='utf-8'))
    cap=cv2.VideoCapture(str(ROT/'scen/klipp'/KLIPP[clip]['video']))
    w,h=p['kallbild_bredd'],p['kallbild_hojd'];rows=[]
    for t in p.get('skarmtext',[]):
        # Mitt i textens synlighet, före eventuella regibyten.
        u=(t['ut'][0]+t['ut'][1]-1)//2;f=p['kallrutor'][u]
        cap.set(1,f);ok,img=cap.read()
        if not ok:continue
        out=Image.new('RGBA',(w,h));rita(ImageDraw.Draw(out),t,1.,1.)
        rgba=np.asarray(out);positive=rgba[:,:,3]>180
        if not positive.any():continue
        yy,xx=np.nonzero(positive);x,y=int(xx.min()),int(yy.min());bw,bh=int(xx.max()-x+1),int(yy.max()-y+1)
        mode=True if t['stil']['farg'].lower()=='#ff1020' else 'black' if t['stil']['farg'].lower()=='#000000' else False
        mm=mask(img,mode).astype('float32')/255
        # Text med kontur utvärderas med själva teckenfärgen; konturen är bakgrund.
        rgb=rgba[:,:,:3];color=np.array([int(t['stil']['farg'][i:i+2],16) for i in (1,3,5)])
        glyph=positive & (np.abs(rgb.astype(int)-color).max(axis=2)<30)
        tpl=glyph[y:y+bh,x:x+bw].astype('float32')
        if tpl.sum()<5:continue
        neg=(cv2.dilate(tpl,np.ones((3,3),np.uint8))>0)&~(tpl>0)
        kernel=tpl/tpl.sum()-.5*neg/max(1,neg.sum())
        radius=12;left=max(0,x-radius);top=max(0,y-radius)
        candidate=mm[top:min(h,y+bh+radius),left:min(w,x+bw+radius)]
        if candidate.shape[0]<bh or candidate.shape[1]<bw:continue
        scores=cv2.matchTemplate(candidate,kernel.astype('float32'),cv2.TM_CCORR)
        _,score,_,loc=cv2.minMaxLoc(scores)
        rows.append(dict(id=t['id'],scen=t['scen'],text=t['text'],ruta=f,
                         lokal_forskjutning_px=[left+loc[0]-x,top+loc[1]-y],matchning=score,
                         antagen_box=t['ursprung'].get('typ')=='antagen',
                         konfidens=t['konfidens']))
    cap.release()
    return dict(klipp=clip,metod='Lokal färg-/teckenmatchning inom ±12 px vid varje texts mittruta. Fontskillnad och bildbakgrund påverkar måttet; ingen oberoende OCR- eller tidsnoggrannhet.',
                texter=rows,
                median_abs_forskjutning_px=np.median(np.abs([r['lokal_forskjutning_px'] for r in rows]),axis=0).tolist() if rows else [],
                p90_abs_forskjutning_px=np.percentile(np.abs([r['lokal_forskjutning_px'] for r in rows]),90,axis=0).tolist() if rows else [],
                median_matchning=float(np.median([r['matchning'] for r in rows])) if rows else None)


if __name__=='__main__':
    jsonfil(HIT/'ut/fore_text/textgranskning.json',[granska(c,d) for c,d in [('b','tom2'),('kenny','tom2'),('a','tom2'),('notan','text_redigerad')]])
