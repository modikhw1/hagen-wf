"""Källa | tidigare mall | ny tom regi, samma två källrutor per scen."""
from pathlib import Path
import json
import cv2
from PIL import Image,ImageDraw,ImageFont

HIT=Path(__file__).resolve().parent;UT=HIT/'ut/notan';ROOT=HIT.parents[2]


def main():
    out=UT/'tro_jamforelse';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    cap=cv2.VideoCapture(str(ROOT/'scen/klipp/d-dialog-notan.mp4'))
    p=json.loads((UT/'tro_tom/plan.json').read_text(encoding='utf-8'))
    mapping={f:i for i,f in enumerate(p['kallrutor'])}
    for si,frames in enumerate([[10,60],[80,105],[120,160],[180,240],[260,275],[300,320],[350,375]],1):
        sheet=Image.new('RGB',(864,1100),'#e8e4db');draw=ImageDraw.Draw(sheet)
        for row,f in enumerate(frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
            assert ok,f
            imgs=[Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)),
                  Image.open(UT/f'mall_tom/render/f{f:04d}.png').convert('RGB'),
                  Image.open(UT/f'tro_tom/render/f{mapping[f]:04d}.png').convert('RGB')]
            for col,(label,img) in enumerate(zip(['Källa','Tidigare mall','Ny, tom regi'],imgs)):
                draw.text((288*col+4,550*row+5),f'S{si} ruta {f} · {label}',fill='black',font=font)
                sheet.paste(img.resize((288,512)),(288*col,550*row+32))
        sheet.save(out/f's{si}.png')
    cap.release()


if __name__=='__main__':main()
