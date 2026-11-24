"""Från färdig ingest till film: kalla.json -> plan.json -> ljud -> Blender -> film.mp4 -> kvalitet.md och jämförelseblad (källa | render).

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kor_klipp.py <klippnamn> <ingestmapp> <video.mp4> [--regi regi.json] [--undermapp tom] [--bygg-kalla]

Utdata: scen/3d/kontrakt/ut/<klippnamn>/<undermapp>/ (plan.json, film.mp4, kvalitet.md, blad/s<n>.png, tider.json).
kalla.json byggs en gång till ut/<klippnamn>/kalla.json (--bygg-kalla; källbyggaren vägrar skriva över). Utan --regi används en tom regi.
Ingen körning skriver över en befintlig undermapp. Blender hittas som i ingest_klipp.py. Ett tungt steg i taget.
"""
import argparse
import ast
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

from gemensamt import HIT, ladda, skriv
from kompilera import kompilera

ROT = HIT.parents[2]
INGEST = HIT.parent / 'ingest'


def blender():
    tree = ast.parse((INGEST / 'ingest_klipp.py').read_text(encoding='utf-8'))
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'BLENDER' for x in n.targets): return ast.literal_eval(n.value)
    raise ValueError('BLENDER saknas i ingest_klipp.py')


def blad(plan, video, d, bildmapp):
    """Två rutor per scen: källa till vänster, render till höger. Rutan väljs vid en tredjedel och två tredjedelar av scenen."""
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
    cap = cv2.VideoCapture(str(video)); (d / 'blad').mkdir(exist_ok=True)
    kart = {f: i for i, f in enumerate(plan['kallrutor'])}
    for s in plan['scener']:
        a, b = s['ut']; rutor = [a + (b - a) // 3, a + 2 * (b - a) // 3]
        if b - a < 2: rutor = [a]
        celler = []
        for u in rutor:
            cap.set(cv2.CAP_PROP_POS_FRAMES, plan['kallrutor'][u]); ok, k = cap.read()
            r = cv2.imread(str(bildmapp / f'f{u:04d}.png'))
            if not ok or r is None: continue
            k = Image.fromarray(cv2.cvtColor(k, cv2.COLOR_BGR2RGB)); r = Image.fromarray(cv2.cvtColor(r, cv2.COLOR_BGR2RGB)).resize(k.size)
            celler.append((u, k, r))
        if not celler: continue
        w, h = celler[0][1].size; sc = 480 / h; w, h = int(w * sc), 480
        ark = Image.new('RGB', (2 * w + 12, len(celler) * (h + 24) + 28), '#e8e4db'); dr = ImageDraw.Draw(ark)
        dr.text((6, 4), f'{s["id"]}   källa | render', fill='black', font=font)
        for i, (u, k, r) in enumerate(celler):
            y = 28 + i * (h + 24); ark.paste(k.resize((w, h)), (0, y)); ark.paste(r.resize((w, h)), (w + 12, y))
            dr.text((6, y + h + 3), f'utruta {u}, källruta {plan["kallrutor"][u]}', fill='black', font=font)
        ark.save(d / 'blad' / f'{s["id"]}.png')


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('klipp'); p.add_argument('ingest'); p.add_argument('video')
    p.add_argument('--regi'); p.add_argument('--undermapp', default='tom'); p.add_argument('--bygg-kalla', action='store_true')
    p.add_argument('--semantik'); p.add_argument('--tillat-flaggad', action='store_true', help='rendera även när bildtrohetskontrollen flaggar; kvalitet.md visar vilka scener'); p.add_argument('--hoppa-render', action='store_true'); a = p.parse_args()
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    ut = HIT / 'ut' / a.klipp; d = ut / a.undermapp; video = Path(a.video).resolve(); tider = {}
    if d.exists(): raise FileExistsError(d)
    d.mkdir(parents=True)

    def kor(namn, args, logg):
        t = time.perf_counter()
        with open(logg, 'w', encoding='utf-8') as f: r = subprocess.run(args, cwd=ROT, env=os.environ, stdout=f, stderr=subprocess.STDOUT)
        tider[namn] = round(time.perf_counter() - t, 1); skriv(d / 'tider.json', tider); print(namn, tider[namn], 's', 'exit', r.returncode, flush=True)
        if r.returncode: raise RuntimeError('Se ' + str(logg))
    kalla = ut / 'kalla.json'
    if a.bygg_kalla and not kalla.exists():
        kor('kalla', [sys.executable, str(HIT / 'kalla_bygg.py'), str(Path(a.ingest).resolve()), str(kalla), '--video', str(video)] + (['--semantik', a.semantik] if a.semantik else []), d / 'kalla.log')
    regi = Path(a.regi).resolve() if a.regi else None
    if not regi:
        K = ladda(kalla); 
        regi = d / 'regi.json'; skriv(regi, {'$schema': 'regi.schema.json', 'schema_version': 'regi/1', 'kalla': dict(klipp_id=K['klipp']['id'], sha256=K['klipp']['sha256'], revision=K['revision']), 'kund': None, 'skapad': None, 'edits': [],
                           'utdata': dict(fps_taljare=K['tidsbas']['fps_taljare'], fps_namnare=K['tidsbas']['fps_namnare'], bredd=K['klipp']['video']['bredd'], hojd=K['klipp']['video']['hojd'], stil_ref=None, ljudpolicy='blandat_duckad', render_backend='blender_mhr'),
                           'ramar': dict(bevara_beats=[], bevara_klippoffset_s=None, tillat_retiming=True, max_talfaktor=1.15)})
    t = time.perf_counter(); plan = kompilera(kalla, regi); skriv(d / 'plan.json', plan)
    from trohet import rapport
    rapport(plan, d / 'plan.json'); tider['kompilering'] = round(time.perf_counter() - t, 1); skriv(d / 'tider.json', tider)
    if a.hoppa_render: return
    kor('ljud', [sys.executable, str(HIT / 'bygg_ljud.py'), str(d / 'plan.json'), str(d / 'ljud.wav'), str(d / 'ljud_rapport.json')], d / 'ljud.log')
    forsta = next(iter(sorted(Path(a.ingest).glob('S*/varld.npz'), key=lambda q: int(q.parent.name[1:])))).parent
    exe = blender()
    kor('bygg_render', [exe, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(INGEST / 'mhr_rig.py'), '--', str(forsta), str(video),
                        '--plan', str(d / 'plan.json'), '--ut', str(d), '--ljud', str(d / 'ljud.wav'), '--render'] + (['--tillat-flaggad'] if a.tillat_flaggad else []), d / 'blender.log')
    blad(plan, video, d, d / 'render'); print('klart', d)


if __name__ == '__main__': main()
