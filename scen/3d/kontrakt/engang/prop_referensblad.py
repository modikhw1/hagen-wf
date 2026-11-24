"""Bildbevis för manuellt avlästa produktregioner, före byggning."""
import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

H=Path(__file__).resolve().parents[1]
refs=json.loads((H/'prop_referenser.json').read_text(encoding='utf-8'))
for clip in ['b','kenny','a','notan']:
    path=H/'ut'/clip/'kalla_jamn.json';k=json.loads(path.read_text(encoding='utf-8'));cap=cv2.VideoCapture(str((path.parent/k['klipp']['video']['sokvag']).resolve()));imgs=[]
    w=k['klipp']['video']['bredd'];h=k['klipp']['video']['hojd']
    for sc in k['semantik']['scener']:
        kam=next(x for x in k['matning']['kameror'] if x['id']==sc['kamera']);off=kam['kalla_ruta0'];n=round((sc['slut_s']-sc['start_s'])*k['tidsbas']['fps_taljare']/k['tidsbas']['fps_namnare'])
        tile=Image.new('RGB',(440,420),'#ddd')
        for i,f in enumerate([n//3,2*n//3]):
            cap.set(1,off+f);ok,im=cap.read()
            if not ok:continue
            im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));dr=ImageDraw.Draw(im)
            for name,scenes in refs[clip].items():
                if sc['id'] not in scenes:continue
                b=scenes[sc['id']][i]
                if b is None:continue
                box=[b[0]*w,b[1]*h,b[2]*w,b[3]*h];dr.rectangle(box,outline='#00ff40',width=4);dr.text(box[:2],name,fill='#00ff40')
            im.thumbnail((218,390));tile.paste(im,(i*220,25));ImageDraw.Draw(tile).text((i*220,2),f'{clip} {sc["id"]} f{f}',fill='black')
        imgs.append(tile)
    cap.release()
    for start in range(0,len(imgs),6):
        sheet=Image.new('RGB',(1320,840),'#ddd')
        for i,im in enumerate(imgs[start:start+6]):sheet.paste(im,((i%3)*440,(i//3)*420))
        p=H/f'ut/prop_granskning/regioner_v2_{clip}_{start//6}.jpg'
        if p.exists():raise FileExistsError(p)
        sheet.save(p)
