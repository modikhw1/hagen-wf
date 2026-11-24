"""0033: bild för alla meningar som Jev kan utföra (liggaren, kalla_0033), och ett kontaktblad med en rad per mening. Kör: scen/.venv/Scripts/python.exe forvarld/gelato/rendera_0033.py"""
import sys, json
sys.dont_write_bytecode = True
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent)); import bild
O = Path(__file__).resolve().parent / 'ut_0033'; M = {m['nr']: m['text'] for m in json.load(open(Path(__file__).resolve().parent / 'meningar_0031.json', encoding='utf-8'))['meningar']}
T = json.load(open(Path(__file__).resolve().parent / 'ut_0031/tabell.json', encoding='utf-8'))
RAD = {1: (40, 31), 2: (100, 100), 3: (160, 160), 4: (100, 100), 5: (50, 50), 6: (60, 60), 7: (251, 281), 9: (130, 130), 11: (130, 130)}
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20); W, H = 270, 480; rader = []
pb = json.load(open(O / 'plan/bas.json', encoding='utf-8'))
for n, (fu, eu) in RAD.items():
    a = Image.open(bild.rutor(O, 'bas', fu, fu + 1)[0]).convert('RGB'); b = Image.open(bild.rutor(O, f'm{n}', eu, eu + 1)[0]).convert('RGB'); o = bild.original(pb, fu)
    r = Image.new('RGB', (3 * W + 16 + 520, H), '#e8e4db'); d = ImageDraw.Draw(r)
    for i, im in enumerate((o, a, b)): r.paste(im.resize((W, H)), (i * (W + 8), 0))
    x0 = 3 * W + 24; d.text((x0, 10), f'm{n}: {M[n]}'[:46], fill='black', font=F); d.text((x0, 40), f'Jev: {T[str(n)]["med"]} (5/5)', fill='black', font=F)
    d.text((x0, 70), f'original | före (utruta {fu}) | efter (utruta {eu})', fill='#444', font=F)
    if n == 11: d.text((x0, 100), 'nivå 1 (spegling) ser fel ut; ersätts av 0034', fill='#a00', font=F)
    if n == 9: d.text((x0, 100), 'kunden: antagen platshållare, andra armen', fill='#444', font=F)
    rader.append(r); print('m%d klar' % n, flush=True)
A = Image.new('RGB', (rader[0].width, sum(r.height + 6 for r in rader)), '#e8e4db'); y = 0
for r in rader: A.paste(r, (0, y)); y += r.height + 6
A.save(O / 'kontaktblad.jpg', quality=85); print('KONTAKTBLAD_KLAR')
