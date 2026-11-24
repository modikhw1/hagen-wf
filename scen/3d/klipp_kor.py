"""Hela kedjan från deklarerat klipp till film, för vilket klipp som helst. Samma steg som guacamole_kor.py, utan klippspecifika värden.

    scen/.venv/Scripts/python.exe scen/3d/klipp_kor.py <klipp> prepare [--undermapp tom]
    scen/.venv/Scripts/python.exe scen/3d/klipp_kor.py <klipp> render [--undermapp narvaro]

<klipp> är videons namn i scen/klipp/ utan .mp4 (t.ex. b-tilltal-ravara). Ingest ligger i ingest/ut/<klipp>-tagningar och måste vara klar,
deklarationen i ingest/ut/<klipp>-tagningar/plats/deklaration.json. Resultat i kontrakt/ut/<klipp>/. Inga modelljobb startas här.
prepare skriver nya kalla/plan/närvaro-resultat och vägrar skriva över; render gör ljud, Blender, film, skärmtext och jämförelseblad.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
os.environ['PYTHONIOENCODING'] = 'utf-8'
ING = ROOT / 'scen/3d/ingest'
KON = ROOT / 'scen/3d/kontrakt'
sys.path[:0] = [str(KON), str(ING)]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def run(name, argv, folder):
    folder.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with (folder / (name + '.log')).open('w', encoding='utf-8') as f:
        result = subprocess.run(list(map(str, argv)), stdout=f, stderr=subprocess.STDOUT, env=os.environ)
    seconds = round(time.perf_counter() - start, 2)
    print(name, result.returncode, seconds, 's', flush=True)
    if result.returncode:
        print((folder / (name + '.log')).read_text(encoding='utf-8', errors='replace')[-2500:])
        raise SystemExit(result.returncode)
    return seconds


def prepare(klipp, I, O, VIDEO, D, undermapp, PLATS):
    assert D.exists(), f'Deklarationen saknas: {D}'
    assert not (O / 'kalla.json').exists(), 'Välj nya resultatmappar för en omkörning.'
    utan_rum = [p.parent.name for p in sorted(I.glob('S*/meta.json')) if not (p.parent / 'rum.json').exists()]
    if utan_rum: print('Varning, rum.json saknas i', utan_rum, flush=True)
    py = lambda name, file, *args: run(name, [sys.executable, file, *args], O)
    py('handsyn', ING / 'handsyn.py', I)
    py('deklaration', ING / 'deklaration_till_hand.py', I, '--deklaration', D, '--ut', PLATS)
    py('plats', ING / 'plats.py', I, '--hand', PLATS / 'hand.json', '--ut', PLATS, '--video', VIDEO)
    py('kalla', KON / 'kalla_bygg.py', I, O / 'kalla.json', '--video', VIDEO, '--plats', PLATS / 'plats.json')
    py('kompilering', KON / 'kor_klipp.py', O.name, I, VIDEO, '--undermapp', undermapp, '--hoppa-render')
    py('narvaro', KON / 'narvaro.py', O / undermapp / 'plan.json', D, O / 'narvaro/plan.json')


def render(I, VIDEO, folder):
    from kor_klipp import blender, blad
    from skarmtext import kompositera
    plan = read(folder / 'plan.json')
    times = {}
    times['ljud'] = run('ljud', [sys.executable, KON / 'bygg_ljud.py', folder / 'plan.json', folder / 'ljud.wav', folder / 'ljud_rapport.json'], folder)
    # Diagnostisk rendering, inte ett kvalitetsgodkännande. Se kvalitet.md bredvid planen.
    times['blender'] = run('blender', [blender(), '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', ING / 'mhr_rig.py', '--', I / 'S1', VIDEO, '--plan', folder / 'plan.json', '--ut', folder, '--ljud', folder / 'ljud.wav', '--render', '--tillat-flaggad'], folder)
    shutil.copy2(folder / 'film.mp4', folder / 'film_utan_text.mp4')
    images = kompositera(plan, folder)
    blad(plan, VIDEO, folder, images)
    write(folder / 'tider.json', times)
    print('Film och blad:', folder, flush=True)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('klipp'); a.add_argument('steg', choices=['prepare', 'render']); a.add_argument('--undermapp')
    a.add_argument('--deklaration', help='annan deklaration än plats/deklaration.json'); a.add_argument('--variant', help='namn på varianten: egna plats- och resultatmappar')
    a = a.parse_args()
    I = ING / f'ut/{a.klipp}-tagningar'; O = KON / f'ut/{a.klipp}' if not a.variant else KON / f'ut/{a.klipp}_{a.variant}'
    VIDEO = ROOT / f'scen/klipp/{a.klipp}.mp4'; D = Path(a.deklaration).resolve() if a.deklaration else I / 'plats/deklaration.json'
    PLATS = I / ('plats_berattat' if not a.variant else f'plats_{a.variant}')
    assert VIDEO.exists() and I.exists(), f'Saknar {VIDEO} eller {I}'
    if a.steg == 'prepare': prepare(a.klipp, I, O, VIDEO, D, a.undermapp or 'tom', PLATS)
    else: render(I, VIDEO, O / (a.undermapp or 'narvaro'))
