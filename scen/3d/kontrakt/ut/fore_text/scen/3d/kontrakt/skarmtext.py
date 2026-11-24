"""Skärmtext: källpixlar till redigerbara lager och lokal 2D-komposition.

Ingen OCR eller modell hämtas. Kända strängar söks som teckenmallar i
färgmasker; osäkra träffar får uttryckligt antagen placering.
"""
import copy
import difflib
import json
import re
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTER = ['timesbd.ttf','times.ttf','arialbd.ttf','arial.ttf']
FONTROT = Path('C:/Windows/Fonts')


def mask(img, red=False):
    b,g,r=cv2.split(img)
    if red:return ((r>130)&(r>g*1.5)&(r>b*1.5)).astype('uint8')*255
    grey=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Ljus text med lokal kontrast. Kakel och reflexer får också utslag;
    # den kända teckenformen och tidskontinuiteten måste ge stöd.
    top=cv2.morphologyEx(grey,cv2.MORPH_TOPHAT,np.ones((13,13),np.uint8))
    return ((grey>150)&(top>35)).astype('uint8')*255


def glyph(text,font,size):
    f=ImageFont.truetype(str(FONTROT/font),size)
    box=f.getbbox(text);im=Image.new('L',(max(1,box[2]-box[0]),max(1,box[3]-box[1])),0)
    ImageDraw.Draw(im).text((-box[0],-box[1]),text,font=f,fill=255)
    return np.asarray(im),f


def sok(frames, text, red):
    samples=list(range(0,len(frames),max(1,len(frames)//7)))
    best=(-1,None)
    for font in FONTER:
        for size in range(24,49,2):
            t,_=glyph(text,font,size)
            if t.shape[1]>=frames[0].shape[1] or t.shape[0]>=frames[0].shape[0]:continue
            for i in samples:
                m=mask(frames[i],red)
                scores=cv2.matchTemplate(m,t,cv2.TM_CCOEFF_NORMED)
                _,score,_,pos=cv2.minMaxLoc(scores)
                if score>best[0]:best=(score,dict(font=font,size=size,x=pos[0],y=pos[1],w=t.shape[1],h=t.shape[0]))
    return best


def items(k, sem, video):
    """Ett lager per känd textrad/delsträng och synligt intervall, källklocka."""
    fps=k['tidsbas']['fps_taljare']/k['tidsbas']['fps_namnare'];w=k['klipp']['video']['bredd'];h=k['klipp']['video']['hojd']
    scale=min(1.,576/w,1024/h);cap=cv2.VideoCapture(str(video));out=[];log=[]
    for entry in sem['data']['skarmtext']:
        sc=next(s for s in k['semantik']['scener'] if s['id']==entry['tagning'].lower())
        a=round(sc['start_s']*fps);b=round(sc['slut_s']*fps);frames=[]
        cap.set(cv2.CAP_PROP_POS_FRAMES,a)
        for f in range(a,b):
            ok,img=cap.read()
            if not ok:break
            frames.append(cv2.resize(img,(round(w*scale),round(h*scale))))
        if not frames:continue
        red=float(np.mean([np.mean(mask(x,True)>0) for x in frames[::max(1,len(frames)//5)]]))>.0005
        text=entry['text']
        # Listor kan byggas på med namn och värde vid olika rutor.
        if '\n' in text or re.search(r'\d,\d{3} kg',text):
            strings=[]
            for line in text.splitlines():
                match=re.match(r'([^:]+:)\s*(.*)',line)
                strings.extend([v for v in match.groups() if v] if match else [line])
        elif ' / ' in text:strings=text.split(' / ')
        elif red and text.count(',')>=2:strings=[x.strip()+',' for x in text.split(',') if x.strip()]
        else:strings=[text]
        for string in strings:
            # Pröva också radbrytningar för text som är bredare än bilden.
            options=[string]
            if len(string)>28:
                words=string.split();mid=len(words)//2
                options+=[' '.join(words[:mid]),' '.join(words[mid:])]
            found=[]
            for part in options:
                score,where=sok(frames,part,red)
                found.append((score,where,part))
            score,where,part=max(found,key=lambda x:x[0])
            assumed=score<.42 or where is None
            if assumed:
                where=dict(font='arialbd.ttf',size=30,x=round(w*scale*.08),y=round(h*scale*.72),w=round(w*scale*.84),h=60)
                intervals=[(0,len(frames))];confidence=.2
            else:
                t,_=glyph(part,where['font'],where['size']);scores=[]
                x,y=where['x'],where['y'];tw,th=where['w'],where['h']
                for img in frames:
                    m=mask(img,red);pad=5;x0=max(0,x-pad);y0=max(0,y-pad)
                    crop=m[y0:min(m.shape[0],y+th+pad),x0:min(m.shape[1],x+tw+pad)]
                    scores.append(float(cv2.minMaxLoc(cv2.matchTemplate(crop,t,cv2.TM_CCOEFF_NORMED))[1]))
                visible=np.array(scores)>=max(.38,score*.7)
                # Ett enstaka kompressionsbortfall inuti ett intervall fylls.
                for i in range(1,len(visible)-1):
                    if visible[i-1] and visible[i+1]:visible[i]=True
                edges=np.diff(np.r_[False,visible,False].astype(int));intervals=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))
                intervals=[(int(x),int(y)) for x,y in intervals if y-x>=2]
                confidence=float(np.clip(score,0,1))
            # Talad undertext binds till replik med störst textlikhet i scenen.
            lines=[r for r in k['semantik']['repliker'] if r['scen']==sc['id']]
            line=max(lines,key=lambda r:difflib.SequenceMatcher(None,r['text'].lower(),string.lower()).ratio(),default=None)
            tied=line if line and difflib.SequenceMatcher(None,line['text'].lower(),string.lower()).ratio()>.56 else None
            # Vid radbrytning: sök respektive rad, inte ett falskt helt stycke.
            rendered=part if not assumed else string
            for start,end in intervals:
                out.append(dict(id=f'st{len(out)+1}',scen=sc['id'],text=rendered,start_s=(a+start)/fps,slut_s=(a+end)/fps,kalla='modell',
                                typ='undertext' if tied else 'overlay',replik=tied['id'] if tied else None,
                                box=[where[t]/scale for t in ('x','y','w','h')],
                                stil=dict(font=where['font'],storlek_px=where['size']/scale,justering='vanster',farg='#ff1020' if red else '#ffffff',kontur_farg='#000000',kontur_px=0 if red or where['font'].startswith('times') else 2/scale),
                                ursprung=dict(typ='antagen' if assumed else 'uppmatt',metod='Reservplacering: känd sträng kunde inte lokaliseras säkert.' if assumed else 'Teckenmall i källans färg/kontrastmask, tidsföljd ruta för ruta.',text=sem['ursprung']),konfidens=confidence))
            log.append(dict(scen=sc['id'],text=string,sokt=part,score=score,antagen=assumed,intervall=[[a+x,a+y] for x,y in intervals],box=where))
    cap.release()
    return out,log


def edit(texts,e,scenes):
    sid=e['scen'];sc=next((s for s in scenes if s['id']==sid),None)
    if sc is None:raise ValueError('Textens scen saknas.')
    target=next((t for t in texts if t['id']==e['skarmtext_id']),None)
    action=e['atgard']
    if action=='lagg_till':
        if target:raise ValueError('Text-id finns redan.')
        target=dict(id=e['skarmtext_id'],scen=sid,text='',start_s=sc['start_s'],slut_s=sc['slut_s'],kalla='cm',typ='overlay',replik=None,
                    box=[46,737,484,80],stil=dict(font='arialbd.ttf',storlek_px=30,justering='vanster',farg='#ffffff',kontur_farg='#000000',kontur_px=2),
                    ursprung=dict(typ='antagen',metod='Ny text utan angiven box: standardplacering i källpixlar.'),konfidens=0.)
        texts.append(target)
    elif target is None:raise ValueError('Text-id saknas.')
    elif target['scen']!=sid:raise ValueError('Texten hör till en annan scen.')
    if action=='ta_bort':texts.remove(target);return
    if e.get('text') is not None:target['text']=e['text']
    for key in ('start_s','slut_s','box'):
        if e.get(key) is not None:target[key]=copy.deepcopy(e[key])
    if isinstance(e.get('stil'),dict):target['stil'].update(e['stil'])
    elif e.get('stil'):raise ValueError('Stil måste vara ett stilobjekt för att kunna lösas.')
    if not sc['start_s']<=target['start_s']<target['slut_s']<=sc['slut_s']:raise ValueError('Textens tid ligger utanför scenen.')
    target['ursprung']=dict(typ='cm',edit=e['id']);target['konfidens']=1.


def los(texts,scenes,intervals,tal,fps):
    result=[]
    for sc,iv in zip(scenes,intervals):
        for t in texts:
            if t['scen']!=sc['ursprung']:continue
            a=max(iv['kalla'][0],round(t['start_s']*fps));b=min(iv['kalla'][1],round(t['slut_s']*fps))
            if a>=b:continue
            x=copy.deepcopy(t);x['scen']=sc['id'];x['ut']=[iv['ut'][0]+a-iv['kalla'][0],iv['ut'][0]+b-iv['kalla'][0]]
            new=next((p for p in reversed(tal) if p['replik']==t.get('replik')),None)
            if t.get('typ')=='undertext' and new:
                x['text']=new['text'];x['ersatt_replik']=new['edit']
            result.append(x)
    return result


def kompositera(plan,d):
    """Pillow på renderade PNG, därefter ffmpeg. Ingen 3D-text eller ny Blender."""
    d=Path(d);dest=d/'komposit';dest.mkdir(exist_ok=False)
    w,h=plan['utdata']['bredd'],plan['utdata']['hojd'];sx=w/plan['kallbild_bredd'];sy=h/plan['kallbild_hojd']
    for u in range(len(plan['kallrutor'])):
        source=d/'render'/f'f{u:04d}.png';target=dest/source.name
        active=[t for t in plan.get('skarmtext',[]) if t['ut'][0]<=u<t['ut'][1]]
        if not active:shutil.copyfile(source,target);continue
        im=Image.open(source).convert('RGB');dr=ImageDraw.Draw(im)
        for t in active:
            st=t['stil'];size=max(8,round(st['storlek_px']*sy));font=ImageFont.truetype(str(FONTROT/st['font']),size)
            x,y,bw,bh=t['box'];stroke=round(st['kontur_px']*sy)
            box=font.getbbox(t['text']);tx=x*sx
            if st['justering']=='center':tx+=(bw*sx-(box[2]-box[0]))/2
            elif st['justering']=='hoger':tx+=bw*sx-(box[2]-box[0])
            # Boxens överkant avser synliga tecken, inte fontens baslinje.
            dr.multiline_text((tx-box[0],y*sy-box[1]),t['text'],font=font,fill=st['farg'],stroke_width=stroke,stroke_fill=st['kontur_farg'],spacing=round(size*.15),align={'vanster':'left','center':'center','hoger':'right'}[st['justering']])
        im.save(target)
    ff=shutil.which('ffmpeg')
    subprocess.run([ff,'-v','error','-y','-threads','2','-framerate',f"{plan['utdata']['fps_taljare']}/{plan['utdata']['fps_namnare']}",'-i',str(dest/'f%04d.png'),'-i',str(d/'ljud.wav'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','18','-c:a','aac','-shortest',str(d/'film.mp4')],check=True)
    return dest
