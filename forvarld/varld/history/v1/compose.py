import os
os.environ['PYTHONIOENCODING']='utf-8'
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess
OUT=Path.cwd()/'forvarld/varld';IM=OUT/'bilder'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
P=json.loads((OUT/'paket/notan/manifest.json').read_text(encoding='utf8'))
for s in P['scenes']:
    f=sum(s['ut'])//2;sheet=Image.new('RGB',(1152,735),'#eeeeee');d=ImageDraw.Draw(sheet)
    for j,(suffix,label) in enumerate([('source','Källa'),('ps2','PS2 · plåt + uppmätt synlighetsmask'),('room','PS2 · möblerad mall (ingen mask)')]):
        im=Image.open(IM/f"{s['id']}-{suffix}.png").convert('RGB').resize((384,683),Image.Resampling.NEAREST)
        sheet.paste(im,(j*384,52));d.text((j*384+8,8),label,font=small,fill='black')
        d.text((j*384+8,29),f"{s['id']} · källruta {f} · {f/30:.2f} s",font=small,fill='black')
    sheet.save(IM/f"{s['id']}.png")
overview=Image.new('RGB',(1152,1472),'#ccc')
for i in range(7):
    im=Image.open(IM/f's{i+1}.png').resize((576,368),Image.Resampling.NEAREST);overview.paste(im,((i%2)*576,(i//2)*368))
ImageDraw.Draw(overview).text((590,1160),'Källa | PS2 + plåt | PS2 + mall\nSamtliga sju scener, 30 fps\nMasken är bildbaserad skymning.\nMallvyn visar den fria 3D-scenen.',font=font,fill='black',spacing=12)
overview.save(IM/'oversikt.png')
for j,si in enumerate([0,1,3,5],1):
    s=P['scenes'][si];a=sum(s['ut'])//2-2;strip=Image.new('RGB',(1152,550),'#eee');d=ImageDraw.Draw(strip)
    for k in range(4):
        im=Image.open(IM/f'motion-{j}-{k}.png').resize((288,512),Image.Resampling.NEAREST);strip.paste(im,(k*288,38));d.text((k*288+8,8),f"{s['id']} · ruta {a+k} · {(a+k)/30:.3f} s",font=small,fill='black')
    strip.save(IM/f'rorelse-{j}.png')
frames=IM/'film-rutor'
if frames.exists() and len(list(frames.glob('*.png')))>=180:
    subprocess.run(['ffmpeg','-y','-v','error','-threads','2','-framerate','30','-i',str(frames/'%04d.png'),'-i',str(OUT/'paket/notan/audio.m4a'),'-t','6','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac',str(IM/'ps2-6s.mp4')],check=True)
print('Composed seven comparisons, overview and four motion strips.')
