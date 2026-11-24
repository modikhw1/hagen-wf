"""FORSKNING (0039): andra_handen_fyra.mp4 — original | 0034 optimering | 0036 matchning (struken) | MaskedMimic, med remsa.

  scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/film_0039.py <mm-namn>
"""
import sys, json
sys.dont_write_bytecode = True
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
HIT = Path(__file__).resolve().parent; KR = HIT.parents[1]; ROOT = HIT.parents[3]
sys.path.insert(0, str(ROOT / 'forvarld/gelato')); import bild
namn = sys.argv[1]; O = KR / 'ut'; U = HIT / 'ut'; pb = json.load(open(O / 'plan/bas.json', encoding='utf-8'))
fe = bild.rutor(O, 'efter', 0, 156); fm = bild.rutor(U, namn, 0, 156)
f36 = [KR / f'forskning/speglad_0036/bild_matchad/r{u:04d}.png' for u in range(156)]
K = json.load(open(ROOT / 'scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/kalla_0033.json', encoding='utf-8')); seg = K['semantik']['handling'][0]['segment']
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20); W, H = 300, 533; BR = 4 * W + 24
v = cv2.VideoWriter(str(U / f'andra_handen_fyra_{namn}.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (BR, H + 100))
for u in range(156):
    r = Image.new('RGB', (BR, H + 100), '#1c1c1c'); d = ImageDraw.Draw(r)
    for i, (im, rub) in enumerate(((bild.original(pb, u), 'original'), (Image.open(fe[u]), '0034 optimering'), (Image.open(f36[u]), '0036 matchning (struken)'),
                                   (Image.open(fm[u]), 'MaskedMimic (forskning)'))):
        r.paste(im.convert('RGB').resize((W, H)), (i * (W + 8), 30)); d.text((i * (W + 8) + 4, 4), rub, fill='white', font=F)
    y = H + 36
    for x in seg: d.rectangle([x['rutor'][0] * BR / 156, y, x['rutor'][1] * BR / 156 - 2, y + 22], fill='#3a6' if x['id'] in ('h3', 'h6', 'h7', 'h8') else '#666'); d.text((x['rutor'][0] * BR / 156 + 3, y + 2), x['id'], fill='white', font=F)
    d.line([u * BR / 156, y - 4, u * BR / 156, y + 26], fill='white', width=3)
    d.text((6, y + 34), f'ruta {u}   vänster hand till tråget (h3) och kundens hand (h6–h8). MaskedMimic: AMASS-tränad, bara forskning.', fill='white', font=F)
    v.write(cv2.cvtColor(np.array(r), cv2.COLOR_RGB2BGR))
v.release(); print('FILM_KLAR')
