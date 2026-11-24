import os
os.environ['PYTHONIOENCODING']='utf-8'
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess,sys
OUT=Path.cwd()/'forvarld/varld';IM=OUT/'bilder'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
P=json.loads((OUT/'paket/notan/manifest.json').read_text(encoding='utf8'))
layered='--layered' in sys.argv
columns=[('source','Källa'),('ps2','PS2 · plåt + synlighetsmask'),('layered','PS2 · mall + pappersteater'),('changed','PS2 · 12 cm åt sidan, 8 cm närmare')] if layered else [('source','Källa'),('ps2','PS2 · plåt + uppmätt synlighetsmask'),('room','PS2 · möblerad mall (ingen mask)')]
for s in P['scenes']:
    f=sum(s['ut'])//2;sheet=Image.new('RGB',(384*len(columns),735),'#eeeeee');d=ImageDraw.Draw(sheet)
    for j,(suffix,label) in enumerate(columns):
        im=Image.open(IM/f"{s['id']}-{suffix}.png").convert('RGB').resize((384,683),Image.Resampling.NEAREST)
        sheet.paste(im,(j*384,52));d.text((j*384+8,8),label,font=small,fill='black')
        d.text((j*384+8,29),f"{s['id']} · källruta {f} · {f/30:.2f} s",font=small,fill='black')
    sheet.save(IM/f"{s['id']}.png")
tilewidth=192*len(columns)
overview=Image.new('RGB',(tilewidth*2,1472),'#ccc')
for i in range(7):
    im=Image.open(IM/f's{i+1}.png').resize((tilewidth,368),Image.Resampling.NEAREST);overview.paste(im,((i%2)*tilewidth,(i//2)*368))
ImageDraw.Draw(overview).text((tilewidth+14,1140),'Källa | plåt | lager i mall | ändrad kamera\n'+'Samtliga sju scener, 30 fps\nHuvud/hår och förgrund är 2,5D-kort.\nSvarta kartytor är genomskinliga.\nStörre kamerarörelser saknar sidoytor.\nTidigare versioner: v1, v2-textur, v3-huvud' if layered else 'Källa | PS2 + plåt | PS2 + mall\nSamtliga sju scener, 30 fps\nMasken är bildbaserad skymning.',font=font,fill='black',spacing=12)
overview.save(IM/'oversikt.png')
for j,si in enumerate([0,1,3,5],1):
    s=P['scenes'][si];a=sum(s['ut'])//2-2;strip=Image.new('RGB',(1152,1100 if layered else 550),'#eee');d=ImageDraw.Draw(strip)
    for k in range(4):
        im=Image.open(IM/f'motion-{j}-{k}.png').resize((288,512),Image.Resampling.NEAREST);strip.paste(im,(k*288,38));d.text((k*288+8,8),f"{s['id']} · ruta {a+k} · {(a+k)/30:.3f} s",font=small,fill='black')
        if layered:
            im=Image.open(IM/f'motion-layered-{j}-{k}.png').resize((288,512),Image.Resampling.NEAREST);strip.paste(im,(k*288,588));d.text((k*288+8,558),'Lager + ändrad kamera',font=small,fill='black')
    strip.save(IM/f'rorelse-{j}.png')
frames=IM/'film-rutor'
if frames.exists() and len(list(frames.glob('*.png')))>=180:
    subprocess.run(['ffmpeg','-y','-v','error','-threads','2','-framerate','30','-i',str(frames/'%04d.png'),'-i',str(OUT/'paket/notan/audio.m4a'),'-t','6','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac',str(IM/'ps2-6s.mp4')],check=True)
print('Composed seven comparisons, overview and four motion strips.')
if (IM/'look-plain.png').exists():
    comparison=Image.new('RGB',(768,536),'#eee');d=ImageDraw.Draw(comparison)
    for j,(suffix,label) in enumerate([('plain','Vanlig: 576×1024 internt'),('ps2','PS2: 192×342 internt')]):
        im=Image.open(IM/f'look-{suffix}.png').convert('RGB').crop((160,150,544,630));comparison.paste(im,(j*384,56));d.text((j*384+8,8),label,font=font,fill='black');d.text((j*384+8,34),'Samma ruta 93 · utsnitt 1:1 bildpunkter',font=small,fill='black')
    comparison.save(IM/'ps2-jamforelse.png')
