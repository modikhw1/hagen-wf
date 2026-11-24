"""Samma källrutor bredvid tidigare platsrum och de tre mallfilmerna."""
import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw,ImageFont

HIT=Path(__file__).resolve().parent;UT=HIT/'ut/notan';ROOT=HIT.parents[2]
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)


def main():
    d=UT/'mall_jamforelse';d.mkdir(exist_ok=True);cap=cv2.VideoCapture(str(ROOT/'scen/klipp/d-dialog-notan.mp4'))
    planer={n:json.loads((UT/n/'plan.json').read_text(encoding='utf-8')) for n in ('mall_tom','mall_redigerad','mall_byt_lokal')}
    kartor={n:{f:i for i,f in enumerate(p['kallrutor'])} for n,p in planer.items()}
    samples=[[10,60],[80,105],[120,160],[180,240],[260,275],[300,320],[350,375]]
    for si,frames in enumerate(samples,1):
        sheet=Image.new('RGB',(288*5,550*2),'#e8e4db');draw=ImageDraw.Draw(sheet)
        for row,f in enumerate(frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
            if not ok:raise ValueError(f)
            imgs=[Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))]
            old=UT/'plats_tom/render'/f'f{f:04d}.png';imgs.append(Image.open(old).convert('RGB'))
            for name in planer:
                u=kartor[name].get(f)
                imgs.append(Image.open(UT/name/'render'/f'f{u:04d}.png').convert('RGB') if u is not None else None)
            for col,(name,img) in enumerate(zip(['Källa','Tidigare platsrum','Mall, tom regi','Mall, redigerad','Fiktiv kundlokal'],imgs)):
                x=col*288;y=row*550
                draw.text((x+5,y+4),f'S{si} ruta {f} · {name}',font=FONT,fill='black')
                if img is None:draw.text((x+10,y+200),'Scenen bortklippt',font=FONT,fill='black')
                else:sheet.paste(img.resize((288,512)),(x,y+32))
        sheet.save(d/f's{si}.png')
    cap.release()


if __name__=='__main__':main()
