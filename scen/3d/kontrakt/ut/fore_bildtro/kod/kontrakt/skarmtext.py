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

FONTER = ['georgia.ttf','georgiab.ttf','timesbd.ttf','times.ttf','arialbd.ttf','arial.ttf']
FONTROT = Path('C:/Windows/Fonts')


def mask(img, red=False):
    b,g,r=cv2.split(img)
    if red=='black':
        grey=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        bottom=cv2.morphologyEx(grey,cv2.MORPH_BLACKHAT,np.ones((13,13),np.uint8))
        return ((grey<110)&(bottom>35)).astype('uint8')*255
    if red is True:return ((r>130)&(r>g*1.5)&(r>b*1.5)).astype('uint8')*255
    grey=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Ljus text med lokal kontrast. Kakel och reflexer får också utslag;
    # den kända teckenformen och tidskontinuiteten måste ge stöd.
    top=cv2.morphologyEx(grey,cv2.MORPH_TOPHAT,np.ones((13,13),np.uint8))
    return ((grey>150)&(top>35)).astype('uint8')*255


def glyph(text,font,size):
    f=ImageFont.truetype(str(FONTROT/font),size)
    scratch=Image.new('L',(1,1));box=ImageDraw.Draw(scratch).multiline_textbbox((0,0),text,font=f,spacing=round(size*.15),align='center')
    im=Image.new('L',(max(1,round(box[2]-box[0])),max(1,round(box[3]-box[1]))),0)
    ImageDraw.Draw(im).multiline_text((-box[0],-box[1]),text,font=f,fill=255,spacing=round(size*.15),align='center')
    return np.asarray(im),f


def sok(frames, text, hint=None, region=None, modes=(False,True,'black')):
    samples=list(range(0,len(frames),max(1,len(frames)//3)))
    masks={(i,mode):mask(frames[i],mode) for i in samples for mode in modes}
    best=(-1,None)
    fonts=FONTER if hint is None else [hint['font']]
    sizes=range(24,49,4) if hint is None else [hint['size']-2,hint['size'],hint['size']+2]
    for font in fonts:
        for size in sizes:
            t,_=glyph(text,font,size)
            if t.shape[1]>=frames[0].shape[1] or t.shape[0]>=frames[0].shape[0]:continue
            for i in samples:
                for mode in modes:
                    source=masks[i,mode];ox=oy=0
                    if region:
                        ox,oy,x1,y1=region;source=source[oy:y1,ox:x1]
                    if source.shape[0]<t.shape[0] or source.shape[1]<t.shape[1]:continue
                    scores=cv2.matchTemplate(source,t,cv2.TM_CCOEFF_NORMED)
                    _,score,_,pos=cv2.minMaxLoc(scores);pos=(pos[0]+ox,pos[1]+oy)
                    if score>best[0]:best=(score,dict(font=font,size=size,x=pos[0],y=pos[1],w=t.shape[1],h=t.shape[0],mode=mode))
    return best


def items(k, sem, video, anvand_referenser=True):
    """Ett lager per känd textrad/delsträng och synligt intervall, källklocka."""
    from textreferens import las as referenstext
    reviewed=referenstext(k,video) if anvand_referenser else None
    if reviewed is not None:
        ref=Path(__file__).parent/'textreferenser'/(k['klipp']['id']+'.json')
        if not json.loads(ref.read_text(encoding='utf-8')).get('kompletterar'):return reviewed
        scenes={t['scen'] for t in reviewed[0]}
        rest=copy.deepcopy(sem);rest['data']['skarmtext']=[t for t in rest['data']['skarmtext'] if t['tagning'].lower() not in scenes]
        other,log=items(k,rest,video,False)
        result=reviewed[0]+other
        for i,t in enumerate(result):t['id']=f'st{i+1}'
        return result,reviewed[1]+log
    fps=k['tidsbas']['fps_taljare']/k['tidsbas']['fps_namnare'];w=k['klipp']['video']['bredd'];h=k['klipp']['video']['hojd']
    scale=min(1.,576/w,1024/h);cap=cv2.VideoCapture(str(video));out=[];log=[];cache={};hint=None
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
        strings=[piece for value in strings for piece in (value.split(' ') if re.fullmatch(r'\d[,.]\d{3} kg',value) else [value])]
        rowhint=None
        for string in strings:
            # Pröva också radbrytningar för text som är bredare än bilden.
            options=[string]
            if len(string)>18:
                words=string.split();mid=len(words)//2
                options+=[' '.join(words[:mid]),' '.join(words[mid:])]
            found=[]
            for part in options:
                score,where=cache.get(part,(None,None))
                if rowhint is not None and not string.endswith(':'):
                    region=(round(frames[0].shape[1]*.44),max(0,rowhint['y']-8),frames[0].shape[1]-20,min(frames[0].shape[0],rowhint['y']+rowhint['h']+18))
                    score,where=sok(frames,part,None,region)
                elif score is None:
                    if len(string)<4:
                        height,width=frames[0].shape[:2];region=(round(width*.32),round(height*.35),round(width*.7),round(height*.7))
                        score,where=sok(frames,part,None,region,modes=(False,))
                    else:score,where=sok(frames,part,hint)
                found.append((score,where,part))
            score,where,part=max(found,key=lambda x:x[0])
            red=where.get('mode',False) if where else False
            if where is not None and part != string:
                # Den korta strängen lokaliserar bandet. Sök sedan den HELA
                # kända texten med olika radbrytningar inom samma band.
                words=string.split();wrapped=[]
                for split in range(1,len(words)):
                    text2=' '.join(words[:split])+'\n'+' '.join(words[split:])
                    for size2 in (where['size']-2,where['size'],where['size']+2):
                        template,_=glyph(text2,where['font'],size2)
                        if template.shape[1]>=frames[0].shape[1]:continue
                        for fi in range(0,len(frames),max(1,len(frames)//4)):
                            mm=mask(frames[fi],red);y0=max(0,where['y']-size2*2);y1=min(mm.shape[0],where['y']+size2*4)
                            if y1-y0<template.shape[0]:continue
                            _,score2,_,pos=cv2.minMaxLoc(cv2.matchTemplate(mm[y0:y1],template,cv2.TM_CCOEFF_NORMED))
                            wrapped.append((score2,dict(font=where['font'],size=size2,x=pos[0],y=pos[1]+y0,w=template.shape[1],h=template.shape[0],mode=red),text2))
                if wrapped:
                    candidate=max(wrapped,key=lambda x:x[0])
                    if candidate[0]>.38 and candidate[0]>score*.65:score,where,part=candidate
            if score>.5:
                hint=where
                cache[part]=(score,where)
            incomplete=part!=string and '\n' not in part
            assumed=score<.42 or where is None or incomplete
            contextual=assumed and rowhint is not None and not string.endswith(':')
            if contextual:
                template,_=glyph(string,rowhint['font'],rowhint['size'])
                where=dict(font=rowhint['font'],size=rowhint['size'],x=round(frames[0].shape[1]*.475),y=rowhint['y'],w=template.shape[1],h=template.shape[0],mode=rowhint.get('mode',False))
                red=where['mode']
            if assumed and not contextual:
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
                for gap in (1,2,3):
                    for i in range(1,len(visible)-gap):
                        if visible[i-1] and visible[i+gap]:visible[i:i+gap]=True
                edges=np.diff(np.r_[False,visible,False].astype(int));intervals=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))
                intervals=[(int(x),int(y)) for x,y in intervals if y-x>=2]
                confidence=float(np.clip(max(scores or [0]),0,1))
            if contextual:
                confidence=min(confidence,.4)
                if not intervals:intervals=[(0,len(frames))]
                if string=='kg':where['x']=round(frames[0].shape[1]*.69)
            if string.endswith(':') and not assumed:rowhint=where
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
                                stil=dict(font=where['font'],storlek_px=where['size']/scale,justering='center' if '\n' in rendered else 'vanster',farg='#ff1020' if red is True else '#000000' if red=='black' else '#ffffff',kontur_farg='#000000',kontur_px=0 if red is True or red=='black' or where['font'].startswith(('times','georgia')) else 2/scale),
                                ursprung=dict(typ='antagen' if assumed else 'uppmatt',metod=('Reservplacering vid uppmätt radetikett; sifferkolumn vid 47,5 % av bildbredden är antagen.' if contextual else 'Reservplacering: känd sträng kunde inte lokaliseras säkert.') if assumed else 'Teckenmall i källans färg/kontrastmask, tidsföljd ruta för ruta.',text=sem['ursprung']),konfidens=confidence))
            log.append(dict(scen=sc['id'],text=string,sokt=part,score=score,antagen=assumed,kontextuell=contextual,intervall=[[a+x,a+y] for x,y in intervals],box=where))
    cap.release()
    from textenheter import samordna
    return samordna(out),log


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
    if not sc['start_s']-1e-4<=target['start_s']<target['slut_s']<=sc['slut_s']+1e-4:raise ValueError('Textens tid ligger utanför scenen.')
    target['ursprung']=dict(typ='cm',edit=e['id']);target['konfidens']=1.


def los(texts,scenes,intervals,tal,fps,w=576,h=1024):
    result=[]
    for sc,iv in zip(scenes,intervals):
        for t in texts:
            if t['scen']!=sc['ursprung']:continue
            a=max(iv['kalla'][0],round(t['start_s']*fps));b=min(iv['kalla'][1],round(t['slut_s']*fps))
            if a>=b:continue
            x=copy.deepcopy(t)
            if 'box' not in x or 'stil' not in x:
                x.setdefault('box',[.08*w,.72*h,.84*w,.12*h]);x.setdefault('stil',dict(font='arialbd.ttf',storlek_px=.03*h,justering='center',farg='#ffffff',kontur_farg='#000000',kontur_px=.002*h))
                x['ursprung']=dict(typ='antagen',metod='Äldre textpost utan plats/stil: relativ standardbox.');x['konfidens']=0.
            x['scen']=sc['id'];x['ut']=[iv['ut'][0]+a-iv['kalla'][0],iv['ut'][0]+b-iv['kalla'][0]]
            # En kopierad scen (duplicera_scen) bär kopior av texterna. Originalscenen behåller id:t; en kopia får <id>@<kopians scen-id>, stabilt oavsett ordning.
            if sc['id']!=sc['ursprung']:x['id']=f"{t['id']}@{sc['id']}"
            new=next((p for p in reversed(tal) if p['replik']==t.get('replik')),None)
            if t.get('typ')=='undertext' and new:
                x['text']=new['text'];x['ersatt_replik']=new['edit']
            result.append(x)
    return result


def kompositera(plan,d):
    """Pillow gör transparenta textlager; ffmpeg lägger dem över filmen.

    2D-lagren kräver ingen ny Blender-körning och slipper 3D-ocklusion.
    Samma ffmpeg-filter ger filmen och jämförelsebladens PNG-rutor.
    """
    from textmalning import rita
    from textarbete import backup
    d=Path(d);dest=d/'komposit';dest.mkdir(exist_ok=False)
    layers=d/'textlager';layers.mkdir(exist_ok=False)
    w,h=plan['utdata']['bredd'],plan['utdata']['hojd'];sx=w/plan['kallbild_bredd'];sy=h/plan['kallbild_hojd']
    for u in range(len(plan['kallrutor'])):
        im=Image.new('RGBA',(w,h),(0,0,0,0));draw=ImageDraw.Draw(im)
        for t in plan.get('skarmtext',[]):
            if t['ut'][0]<=u<t['ut'][1]:rita(draw,t,sx,sy)
        im.save(layers/f'f{u:04d}.png')
    ff=shutil.which('ffmpeg');rate=f"{plan['utdata']['fps_taljare']}/{plan['utdata']['fps_namnare']}"
    backup(d/'film.mp4')
    subprocess.run([ff,'-v','error','-y','-filter_complex_threads','1','-framerate',rate,'-i',str(d/'render/f%04d.png'),'-framerate',rate,'-i',str(layers/'f%04d.png'),'-i',str(d/'ljud.wav'),
        '-filter_complex','[0:v][1:v]overlay=0:0:format=rgb,format=rgb24,split=2[vfilm][vblad]',
        '-map','[vfilm]','-map','2:a:0','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','18','-c:a','aac','-shortest',str(d/'film.mp4'),
        '-map','[vblad]','-c:v','png','-threads','2','-start_number','0',str(dest/'f%04d.png')],check=True)
    return dest
