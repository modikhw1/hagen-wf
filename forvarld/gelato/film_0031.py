"""0031: andra_handen.mp4 — original | före (bas) | efter (speglad hand, nivå 1 med IK), med remsa (segment och utförd_niva_1)."""
import sys, json
sys.dont_write_bytecode = True
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent)); import bild
O = Path(__file__).resolve().parent / 'ut_0031/hand'; pb = json.load(open(O / 'plan/bas.json', encoding='utf-8')); pe = json.load(open(O / 'plan/m11.json', encoding='utf-8'))
fa = bild.rutor(O, 'bas', 0, 156); fe = bild.rutor(O, 'm11', 0, 156)
K = json.load(open(Path(__file__).resolve().parents[2] / 'scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/kalla_0031.json', encoding='utf-8'))
seg = K['semantik']['handling'][0]['segment']; sp = pe['scener'][0]['spegling']; F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
W, H = 360, 640; v = cv2.VideoWriter(str(O.parent / 'andra_handen.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (3 * W + 16, H + 90))
for u in range(156):
    ram = Image.new('RGB', (3 * W + 16, H + 90), '#1c1c1c'); dr = ImageDraw.Draw(ram)
    for i, im in enumerate((bild.original(pb, u), Image.open(fa[u]).convert('RGB'), Image.open(fe[u]).convert('RGB'))): ram.paste(im.resize((W, H)), (i * (W + 8), 0))
    g = next((x for x in seg if x['rutor'][0] <= u < x['rutor'][1]), None); ik = [x['namn'] for x in sp['ik'] if x['ut'][0] <= u < x['ut'][1]]
    for x in seg: dr.rectangle([x['rutor'][0] * ram.width / 156, H + 8, x['rutor'][1] * ram.width / 156 - 2, H + 30], fill='#3a6' if x['id'] in ('h3', 'h6', 'h7', 'h8') else '#666'); dr.text((x['rutor'][0] * ram.width / 156 + 3, H + 10), x['id'], fill='white', font=F)
    dr.line([u * ram.width / 156, H + 4, u * ram.width / 156, H + 34], fill='white', width=3)
    dr.text((6, H + 40), f'ruta {u}  {g["id"] + " " + g["handling"]["varde"] if g else ""}   original | före | efter: speglad hand (utförd_niva_1){"  IK: " + ",".join(ik) if ik else ""}', fill='white', font=F)
    dr.text((6, H + 64), '"Gör att kvinnan ger glassen med andra handen" -> fg_hand=vanster (liggaren)', fill='#ddd', font=F)
    v.write(cv2.cvtColor(np.array(ram), cv2.COLOR_RGB2BGR))
v.release(); print('FILM_KLAR')
