"""Öppningsbara granskningsöversikter; filmer och befintliga blad ändras inte."""
import json
import sys
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

H=Path(__file__).resolve().parents[1]

def kor(clip,run,prefix):
    folder=H/'ut'/clip/run;p=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
    dest=H/'ut/prop_granskning';dest.mkdir(exist_ok=True)
    sources=cv2.VideoCapture(p['kallvideo']);movie=cv2.VideoCapture(str(folder/'film.mp4'));sheets=[]
    for sc in (p.get('scener') or p['matkamera']['scener']):
        a,b=sc['ut'];canvas=Image.new('RGB',(552,1036),'#ddd');draw=ImageDraw.Draw(canvas);draw.text((5,2),f'{sc["id"]} {run}: källa | render',fill='black')
        for i,u in enumerate([a+(b-a)//3,a+2*(b-a)//3]):
            for j,(cap,f) in enumerate([(sources,p['kallrutor'][u]),(movie,u)]):
                cap.set(1,f);ok,im=cap.read()
                if ok:
                    im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));im.thumbnail((270,480));canvas.paste(im,(j*282,28+i*504))
        sheets.append(canvas)
    sources.release();movie.release()
    paths=[]
    for off in range(0,len(sheets),4):
        canvas=Image.new('RGB',(600,1100),'#ddd')
        for i,im in enumerate(sheets[off:off+4]):
            im=im.copy();im.thumbnail((295,545));canvas.paste(im,((i%2)*300,(i//2)*550))
        path=dest/f'{prefix}_{clip}_{off//4}.jpg'
        if path.exists():raise FileExistsError(path)
        canvas.save(path);paths.append(str(path))
    return paths

if __name__=='__main__': print('\n'.join(kor(*sys.argv[1:])))
