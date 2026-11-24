"""0036: andra_handen_matchad.mp4 — original | 0034 (optimering) | 0036 (matchning ur banken v0 + kort IK), med remsa."""
import sys, json
sys.dont_write_bytecode = True
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'forvarld/gelato')); import bild
O = Path(__file__).resolve().parent / 'ut'; pb = json.load(open(O / 'plan/bas.json', encoding='utf-8'))
fe = bild.rutor(O, 'efter', 0, 156); fm = bild.rutor(O, 'matchad', 0, 156)
K = json.load(open(ROOT / 'scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/kalla_0033.json', encoding='utf-8')); seg = K['semantik']['handling'][0]['segment']
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20); W, H = 360, 640
v = cv2.VideoWriter(str(O / 'andra_handen_matchad.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (3 * W + 16, H + 70))
for u in range(156):
    r = Image.new('RGB', (3 * W + 16, H + 70), '#1c1c1c'); d = ImageDraw.Draw(r)
    for i, im in enumerate((bild.original(pb, u), Image.open(fe[u]).convert('RGB'), Image.open(fm[u]).convert('RGB'))): r.paste(im.resize((W, H)), (i * (W + 8), 0))
    for x in seg: d.rectangle([x['rutor'][0] * r.width / 156, H + 6, x['rutor'][1] * r.width / 156 - 2, H + 28], fill='#3a6' if x['id'] in ('h3', 'h6', 'h7', 'h8') else '#666'); d.text((x['rutor'][0] * r.width / 156 + 3, H + 8), x['id'], fill='white', font=F)
    d.line([u * r.width / 156, H + 2, u * r.width / 156, H + 32], fill='white', width=3)
    d.text((6, H + 40), f'ruta {u}   original | 0034 optimering | 0036 matchning ur banken v0 + kort IK', fill='white', font=F)
    v.write(cv2.cvtColor(np.array(r), cv2.COLOR_RGB2BGR))
v.release(); print('FILM_KLAR')
