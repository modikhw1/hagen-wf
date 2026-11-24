"""Reproducerbara lokala steg för guacamole-provet; använder den befintliga pipen.

Kör från reporoten med scen/.venv/Scripts/python.exe denna_fil prepare|render|edit.
Ingest körs separat enligt GUACAMOLE-LOGG.md. Inga modelljobb startas här.
prepare skriver nya kalla/tom/narvaro-resultat och ska bara köras en gång.
render och edit sparar Blender, film och jämförelseblad. Flaggad kvalitet behålls.
"""
import copy
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
I = ING / 'ut/e-dialog-guacamole-tagningar'
O = KON / 'ut/e-dialog-guacamole'
VIDEO = ROOT / 'scen/klipp/e-dialog-guacamole.mp4'
D = I / 'plats/deklaration.json'
sys.path[:0] = [str(KON), str(ING)]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def run(name, argv, folder=O):
    folder.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with (folder / (name + '.log')).open('w', encoding='utf-8') as f:
        result = subprocess.run(list(map(str, argv)), stdout=f, stderr=subprocess.STDOUT, env=os.environ)
    seconds = round(time.perf_counter() - start, 2)
    print(name, result.returncode, seconds, 's', flush=True)
    if result.returncode:
        print((folder / (name + '.log')).read_text(encoding='utf-8')[-2500:])
        raise SystemExit(result.returncode)
    return seconds


def py(name, file, *args):
    return run(name, [sys.executable, file, *args])


def prepare():
    assert all((I / s / 'rum.json').exists() for s in ['S1', 'S2', 'S3', 'S4']), 'Ingest måste vara klar.'
    assert not (O / 'kalla.json').exists(), 'Välj nya resultatmappar för en omkörning.'
    py('handsyn', ING / 'handsyn.py', I)
    py('deklaration', ING / 'deklaration_till_hand.py', I)
    py('plats', ING / 'plats.py', I, '--hand', I / 'plats_berattat/hand.json', '--ut', I / 'plats_berattat', '--video', VIDEO)
    py('kalla', KON / 'kalla_bygg.py', I, O / 'kalla.json', '--video', VIDEO, '--plats', I / 'plats_berattat/plats.json')
    py('kompilering', KON / 'kor_klipp.py', 'e-dialog-guacamole', I, VIDEO, '--undermapp', 'tom_v2', '--hoppa-render')
    py('narvaro', KON / 'narvaro.py', O / 'tom_v2/plan.json', D, O / 'narvaro/plan.json')


def render(folder):
    from kor_klipp import blender, blad
    from skarmtext import kompositera
    plan = read(folder / 'plan.json')
    times = {}
    times['ljud'] = run('ljud', [sys.executable, KON / 'bygg_ljud.py', folder / 'plan.json', folder / 'ljud.wav', folder / 'ljud_rapport.json'], folder)
    # Diagnostisk rendering, inte ett kvalitetsgodkännande. Se tom/kvalitet.md.
    times['blender'] = run('blender', [blender(), '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', ING / 'mhr_rig.py', '--', I / 'S1', VIDEO, '--plan', folder / 'plan.json', '--ut', folder, '--ljud', folder / 'ljud.wav', '--render', '--tillat-flaggad'], folder)
    shutil.copy2(folder / 'film.mp4', folder / 'film_utan_text.mp4')
    images = kompositera(plan, folder)
    blad(plan, VIDEO, folder, images)
    write(folder / 'tider.json', times)
    print('Film och blad:', folder, flush=True)


def edit():
    from kompilera import kompilera
    from narvaro import lagg_narvaro
    from trohet import rapport
    folder = O / 'redigerad'
    assert not folder.exists(), 'Redigerad finns redan.'
    regi = copy.deepcopy(read(O / 'oppet_data_v2/regi.json'))
    regi['edits'] = [dict(id='narbild_punchline', op='renderkamera', ursprung=dict(typ='cm', av='Codex demonstrationsedit på användarens uppdrag'), kommentar='Visa B:s reaktion närmare i slutscenen. Kroppsläsningen återanvänds.', scen='s4', kamera_id='punchline_nara', lage='stativ', inramning='nara', mal=dict(typ='person', id='B', punkt='huvud'), fov_grader=40)]
    write(folder / 'regi.json', regi)
    plan = kompilera(O / 'kalla_oppet.json', folder / 'regi.json')
    write(folder / 'plan_fore_narvaro.json', plan)
    rapport(plan, folder / 'plan_fore_narvaro.json')
    lagg_narvaro(plan, read(D))
    write(folder / 'plan.json', plan)
    render(folder)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'render': render(O / 'narvaro')
    elif action == 'render-open': render(O / 'oppet')
    elif action == 'edit': edit()
    else: raise SystemExit('prepare | render | edit')
