"""Uppdrag 0029: före- och efterbilder (och korta filmer där tiden är poängen) för gelato-meningar som gick hela vägen.
Bygger scen.blend ur planen med oförändrade scen/3d/ingest/mhr_rig.py, gör objekt med yta glas genomskinliga
(scen/3d/gennedbrytning/s_glas_blender.py), renderar rutor och ställer före | efter sida vid sida. Film: utrutor a–b, före och efter
bredvid varandra med samma tidsaxel i utdata, och originalets källruta under.
Kör: scen/.venv/Scripts/python.exe forvarld/gelato/bild.py <ut-mapp> <namn> [<namn> ...]
"""
import sys
sys.dont_write_bytecode = True
import json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DIR = Path(__file__).resolve().parent; ROOT = DIR.parent.parent
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
RIG = ROOT / 'scen/3d/ingest/mhr_rig.py'; FORSTA = ROOT / 'scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1'
GLAS = ROOT / 'scen/3d/gennedbrytning/s_glas_blender.py'
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)


def bygg(out, namn):
    out = Path(out).resolve(); d = out / 'bild' / namn; plan = out / 'plan' / f'{namn}.json'
    if not (d / 'scen.blend').exists():
        d.mkdir(parents=True, exist_ok=True); P = json.load(open(plan, encoding='utf-8'))
        with open(d / 'blender.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(RIG), '--',
                            str(FORSTA), P['kallvideo'], '--plan', str(plan), '--ut', str(d), '--tillat-flaggad'], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
        glas = sorted({o['id'] for o in P['objekt'] if o.get('yta') == 'glas'})
        if glas:
            with open(d / 'glas.log', 'w', encoding='utf-8') as f:
                subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '--factory-startup', '--python-exit-code', '1', '--python', str(GLAS), '--', ','.join(glas)],
                               cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    return d


def rutor(out, namn, a, b):
    d = bygg(out, namn); saknas = [u for u in range(a, b) if not (d / f'r{u:04d}.png').exists()]
    if saknas:
        with open(d / f'r{a}_{b}.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '-o', str(d / 'r####'), '-F', 'PNG', '-s', str(min(saknas)), '-e', str(max(saknas)), '-a'],
                           cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    return [d / f'r{u:04d}.png' for u in range(a, b)]


def original(plan, u, cache={}):
    import cv2
    key = plan['kallvideo']
    if key not in cache: cache[key] = cv2.VideoCapture(key)
    c = cache[key]; c.set(cv2.CAP_PROP_POS_FRAMES, plan['kallrutor'][u]); ok, f = c.read()
    return Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) if ok else None


def ark(out, namn, par, rubrik, skala=.4):
    """par: [(före-utruta, efter-utruta, text)], en rad per par: original(före) | före | efter."""
    pb = json.load(open(out / 'plan' / 'bas.json', encoding='utf-8')); pe = json.load(open(out / 'plan' / f'{namn}.json', encoding='utf-8'))
    rader = []
    for fu, eu, txt in par:
        a = Image.open(rutor(out, 'bas', fu, fu + 1)[0]).convert('RGB'); b = Image.open(rutor(out, namn, eu, eu + 1)[0]).convert('RGB'); o = original(pb, fu)
        w, h = int(a.width * skala), int(a.height * skala); bild = [x.resize((w, h)) for x in (o, a, b) if x is not None]
        rad = Image.new('RGB', (len(bild) * (w + 8), h + 34), '#e8e4db'); dr = ImageDraw.Draw(rad)
        for i, x in enumerate(bild): rad.paste(x, (i * (w + 8), 30))
        dr.text((4, 4), f'{txt}   original (källruta {pb["kallrutor"][fu]}) | före (utruta {fu}) | efter (utruta {eu}, källruta {pe["kallrutor"][eu]})', fill='black', font=FONT)
        rader.append(rad)
    W = max(r.width for r in rader); H = sum(r.height for r in rader) + 40
    A = Image.new('RGB', (W, H), '#e8e4db'); ImageDraw.Draw(A).text((4, 6), f'{namn}: {rubrik}', fill='black', font=FONT); y = 40
    for r in rader: A.paste(r, (0, y)); y += r.height
    A.save(out / 'bild' / f'{namn}_fore_efter.jpg', quality=88); print(namn, 'ark klar', flush=True)


def film(out, namn, a, b, rubrik, skala=.45):
    """Före (bas) och efter i samma utdatatid a–b, med efterplanens märke (läst, overgang, omsamplad, upprepning) per ruta."""
    import cv2, numpy as np
    pb = json.load(open(out / 'plan' / 'bas.json', encoding='utf-8')); pe = json.load(open(out / 'plan' / f'{namn}.json', encoding='utf-8'))
    nb, ne = len(pb['kallrutor']), len(pe['kallrutor']); fa = rutor(out, 'bas', min(a, nb - 1), min(b, nb)); fe = rutor(out, namn, a, min(b, ne))
    marke = {}
    for d in pe['scener']:
        for x in d.get('handlingsrutor') or []:
            for u in range(*x['ut']): marke[u] = x['marke']
    W, H = int(1080 * skala), int(1920 * skala); v = cv2.VideoWriter(str(out / 'bild' / f'{namn}_film.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (2 * W + 8, H + 60))
    for i in range(b - a):
        u = a + i; ram = Image.new('RGB', (2 * W + 8, H + 60), '#e8e4db'); dr = ImageDraw.Draw(ram)
        if i < len(fa): ram.paste(Image.open(fa[i]).convert('RGB').resize((W, H)), (0, 0))
        if i < len(fe): ram.paste(Image.open(fe[i]).convert('RGB').resize((W, H)), (W + 8, 0))
        dr.text((4, H + 6), f'före: utruta {u}' + (f', källruta {pb["kallrutor"][u]}' if u < nb else ' (slut)'), fill='black', font=FONT)
        dr.text((W + 12, H + 6), f'efter: utruta {u}' + (f', källruta {pe["kallrutor"][u]}, {marke.get(u, "läst")}' if u < ne else ' (slut)'), fill='black', font=FONT)
        dr.text((4, H + 32), f'{namn}: {rubrik}', fill='black', font=FONT)
        v.write(cv2.cvtColor(np.array(ram), cv2.COLOR_RGB2BGR))
    v.release(); print(namn, 'film klar', flush=True)


if __name__ == '__main__':
    out = DIR / sys.argv[1]
    for namn in sys.argv[2:]: bygg(out, namn); print(namn, 'byggd', flush=True)
