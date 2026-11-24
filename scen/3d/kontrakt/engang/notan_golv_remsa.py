"""Den begärda jämförelsen golv_tom | jamn_tom, två fönster om åtta rutor."""
import json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

H=Path(__file__).resolve().parents[1];base=H/'ut/notan';p=json.loads((base/'jamn_tom/plan.json').read_text(encoding='utf-8'))
caps=[cv2.VideoCapture(p['kallvideo']),cv2.VideoCapture(str(base/'golv_tom/film.mp4')),cv2.VideoCapture(str(base/'jamn_tom/film.mp4'))]
out=Image.new('RGB',(1200,1602),'#ddd')
for block,sid in enumerate(['s6','s4']):
    sc=next(x for x in p['scener'] if x['id']==sid);a,b=sc['ut'];u0=a+(b-a)//3
    for row,name in enumerate(['källa','golv_tom','jamn_tom']):
        for i,u in enumerate(range(u0,u0+8)):
            cap=caps[row];cap.set(1,p['kallrutor'][u] if row==0 else u);ok,im=cap.read()
            if not ok:continue
            im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));im=im.resize((150,267));out.paste(im,(150*i,(block*3+row)*267))
        ImageDraw.Draw(out).text((5,(block*3+row)*267+3),f'{sid} {name} u{u0}',fill='yellow')
for c in caps:c.release()
path=H/'ut/prop_granskning/strip_notan_golv_jamn.png'
if path.exists():raise FileExistsError(path)
out.save(path)
