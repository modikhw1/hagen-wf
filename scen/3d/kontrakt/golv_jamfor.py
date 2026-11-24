"""Källa | förra tro-renderingen | golvbeslut, två rutor per scen."""
import cv2
from PIL import Image,ImageDraw,ImageFont
from gemensamt import HIT,ladda

UT=HIT/'ut/notan';ROOT=HIT.parents[2]


def main():
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for edited in (False,True):
        folder=UT/'golv_jamforelse'/('redigerad' if edited else '')
        folder.mkdir(parents=True,exist_ok=True)
        new='golv_redigerad' if edited else 'golv_tom';old='tro_redigerad' if edited else 'tro_tom'
        p=ladda(UT/new/'plan.json');prev=ladda(UT/old/'plan.json')
        mapping={f:i for i,f in enumerate(p['kallrutor'])};before={f:i for i,f in enumerate(prev['kallrutor'])}
        cap=cv2.VideoCapture(str(ROOT/'scen/klipp/d-dialog-notan.mp4'))
        for si,frames in enumerate([[10,60],[80,105],[120,160],[180,240],[260,275],[300,320],[350,375]],1):
            sheet=Image.new('RGB',(864,1100),'#e8e4db');draw=ImageDraw.Draw(sheet)
            for row,f in enumerate(frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();assert ok
                imgs=[Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))]
                for name,mp in [(old,before),(new,mapping)]:
                    imgs.append(Image.open(UT/f'{name}/render/f{mp[f]:04d}.png').convert('RGB') if f in mp else Image.new('RGB',(576,1024),'#ddd8ce'))
                for col,(label,img) in enumerate(zip(['Källa','Före golvbeslut','Nytt golvbeslut'],imgs)):
                    draw.text((288*col+4,550*row+5),f'S{si} ruta {f} · {label}',fill='black',font=font)
                    sheet.paste(img.resize((288,512)),(288*col,550*row+32))
                    if col>0 and f not in mapping:draw.text((288*col+30,550*row+220),'Bortklippt av regi',fill='black',font=font)
            sheet.save(folder/f's{si}.png')
        cap.release()


if __name__=='__main__':main()
