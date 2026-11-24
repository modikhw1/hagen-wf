"""Uppdrag 0014: en stillbild före och efter för de ändringar som gick hela vägen genom snabbvägen.
Bygger scen.blend ur planen med oförändrade scen/3d/ingest/mhr_rig.py (utan --render), renderar en ruta,
lägger planens skärmtext över med textmalning.rita och ställer före | efter sida vid sida.
Kör: scen/.venv/Scripts/python.exe forvarld/btilltal/bild.py
"""
import sys
sys.dont_write_bytecode = True
import json, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DIR = Path(__file__).resolve().parent; ROOT = DIR.parent.parent; OUT = DIR / (sys.argv[1] if len(sys.argv) > 1 else 'ut')   # 0016: ut_0016
sys.path.insert(0, str(ROOT / 'scen/3d/kontrakt'))
from textmalning import rita
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
RIG = ROOT / 'scen/3d/ingest/mhr_rig.py'; FORSTA = ROOT / 'scen/3d/ingest/ut/b-tilltal-ravara-tagningar/S1'
# ändring: (planfil, utruta före, utruta efter, rubrik)
PAR = {'m1': (239, 239, 'Ta bort scen 5 (utruta 239: s5 före, s6 efter)'),
       'm3': (447, 447, 'Byt "Vægt:" till "Rigtig vægt:" i s11 (utruta 447)'),
       'm4': (278, 278, 'Gå närmare Lærke i s6 (utruta 278)')}
if OUT.name == 'ut_0016':
    PAR = {'m2': (30, 30, 'Låt Morten gissa före Mads (utruta 30)'),
           'm5': (357, 357, 'Ta bort vågen (utruta 357, s9)'),
           'm6': (278, 278, 'Byt köttbiten mot en ost (utruta 278, s6)'),
           'm9': (469, 490, 'Gör slutet en sekund längre (före: sista rutan 469; efter: hållen ruta 490)')}


def bygg(namn):
    d = OUT / 'bild' / namn; plan = OUT / 'plan' / f'{namn}.json'
    if not (d / 'scen.blend').exists():
        d.mkdir(parents=True, exist_ok=True)
        with open(d / 'blender.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(RIG), '--',
                            str(FORSTA), json.load(open(plan, encoding='utf-8'))['kallvideo'], '--plan', str(plan), '--ut', str(d)],
                           cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    return d


def ruta(namn, u):
    d = bygg(namn); png = d / f'r{u:04d}.png'
    if not png.exists():
        with open(d / f'r{u}.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '-o', str(d / 'r####'), '-F', 'PNG', '-f', str(u)],
                           cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    plan = json.load(open(OUT / 'plan' / f'{namn}.json', encoding='utf-8'))
    im = Image.new('RGBA', Image.open(png).size, (232, 228, 219, 255)); im.alpha_composite(Image.open(png).convert('RGBA'))
    w, h = im.size; sx = w / plan['kallbild_bredd']; sy = h / plan['kallbild_hojd']; dr = ImageDraw.Draw(im)
    for t in plan.get('skarmtext', []):
        if t['ut'][0] <= u < t['ut'][1]: rita(dr, t, sx, sy)
    scen = next(s['id'] for s in plan['scener'] if s['ut'][0] <= u < s['ut'][1])
    return im.convert('RGB'), scen


def main():
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    for m, (fu, eu, rub) in PAR.items():
        (a, sa), (b, sb) = ruta('bas', fu), ruta(m, eu)
        w, h = a.size; ark = Image.new('RGB', (2 * w + 12, h + 60), '#e8e4db'); dr = ImageDraw.Draw(ark)
        dr.text((6, 6), f'{m}: {rub}', fill='black', font=font)
        ark.paste(a, (0, 32)); ark.paste(b, (w + 12, 32))
        dr.text((6, h + 36), f'före ({sa})', fill='black', font=font); dr.text((w + 18, h + 36), f'efter ({sb})', fill='black', font=font)
        ark.save(OUT / 'bild' / f'{m}_fore_efter.png'); print(m, 'klar', flush=True)


if __name__ == '__main__':
    main()
