"""Compose only saved captures. No video encoding, Blender or upstream imports."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
O=Path('forvarld/varld');D=O/'bilder';M=json.loads((O/'paket/notan/manifest.json').read_text(encoding='utf8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
def sheet(rows,columns,output,size=(288,512),crop=None):
    w,h=size;out=Image.new('RGB',(len(columns)*w,len(rows)*(h+46)),'#eeeeee');draw=ImageDraw.Draw(out)
    for i,(stem,label) in enumerate(rows):
        for j,(suffix,title) in enumerate(columns):
            im=Image.open(D/f'{stem}-{suffix}.png').convert('RGB')
            if crop:im=im.crop(crop)
            im=im.resize(size,Image.Resampling.NEAREST);x=j*w;y=i*(h+46)
            out.paste(im,(x,y+46));draw.text((x+6,y+4),title,font=font,fill='black');draw.text((x+6,y+25),label,font=small,fill='black')
    out.save(D/output)

columns=[('source','Källa'),('ps2','Live + medianplåt'),('layered','Live + mallrum'),('changed','Live + ändrad kamera')]
for s in M['scenes']:
    f=sum(s['source'])//2;sheet([(s['id'],f"{s['id']} · ruta {f}")],columns,s['id']+'.png',size=(288,512))
overview=Image.new('RGB',(1152,1116),'#ccc')
for i,s in enumerate(M['scenes']):
    im=Image.open(D/(s['id']+'.png')).resize((576,279),Image.Resampling.NEAREST);overview.paste(im,((i%2)*576,(i//2)*279))
ImageDraw.Draw(overview).text((588,870),'Källa | live + plåt | live + mall | ny kamera\nTre plana live-kort, ingen fingergeometri.\nText täcks bort från källprojektionen.\nHål och kanter kvarstår vid ny kamera.',font=font,fill='black',spacing=12)
overview.save(D/'oversikt.png')

details=json.loads((O/'detail-captures.json').read_text())
# Review first close shot and the shot with an accepted held-object candidate.
face=[r for r in details if r['scene']==M['scenes'][0]['id']]
held=next((s for s in M['scenes'] if any(h['accepted'] for h in s['live']['held'])),M['scenes'][0])
hands=[r for r in details if r['scene']==held['id']]
beforeafter=[('source','Källa'),('fused','Före: frusen textur'),('live','Efter: live'),('changed','Efter: ny kamera')]
sheet([(r['stem'],f"{r['scene']} · samma ruta {r['frame']}") for r in face],beforeafter,'ansikte-fore-efter.png',size=(288,370),crop=(110,170,470,630))
sheet([(r['stem'],f"{r['scene']} · samma ruta {r['frame']}") for r in hands],beforeafter,'hand-fore-efter.png',size=(288,350),crop=(130,470,576,1010))
sheet([(f'venue-{sid}',sid) for sid in [M['scenes'][0]['id'],M['scenes'][-1]['id']]], [('a_s1','Snabbmatsdisk'),('b_s3','Charkbutik')], 'miljobyten.png')
# Chat images were captured in the original ten-sentence check, before live fix.
sheet([('chat-world','Tidigare chattprov; se chat-measurements.json')],[('1','Kamera'),('3','Ny text'),('9','Glassbar')],'chatt-tre-exempel.png')
no_text=Image.new('RGB',(224*7,420),'#eee');draw=ImageDraw.Draw(no_text)
for i,f in enumerate([36,93,142,213,268,309,360]):
    im=Image.open(D/f'no-source-text-{f}.png').convert('RGB').resize((224,398),Image.Resampling.NEAREST);no_text.paste(im,(224*i,22));draw.text((224*i+3,2),f'Ruta {f}, textlager av',font=small,fill='black')
no_text.save(D/'undertextkontroll.png')
print('Saved overview, face/hand before-after, venue/chat strips and source-text audit.')
