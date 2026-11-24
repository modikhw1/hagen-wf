"""FORSKNING (0039): lokalt kommando mot den varma kroppstjänsten (tjanst.py). Ett varv ska ta under en minut.

Från projektroten:
  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/kropp.py kor <villkor.json> [<villkor2.json> ...] [--inn <ref.npz>] [--tyst]
  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/kropp.py diag            alla ut/diag_*.json parallellt
  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/kropp.py ping            väcker en container

Varje villkorsfil körs i en egen container, parallellt. Den lokala kor_mm.py skickas med, så ändringar i den gäller direkt.
Skriver ut/raw_<namn>.npz och ut/logg_<namn>.txt, och en rad per körning: tid, rothöjd över tid, fel mot referensen.
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import modal
HIT = Path(__file__).resolve().parent; UT = HIT / 'ut'
sys.path.insert(0, str(HIT)); import mhr_smpl as M
VISA = ('MM_KLAR', 'KLART_TIDIGT', 'NORM_SUMMA', 'DIAG_LAGE', 'Traceback', 'Error', 'error:')


def folj(raw, ref):
    d = dict(np.load(raw, allow_pickle=True)); r = dict(np.load(ref, allow_pickle=True))
    S = M.fk_smpl(r['G'].astype(float), r['rot'].astype(float)); pos = d['pos'].astype(float); k = min(len(pos), len(S) - 1)
    P = pos[:k] - d['skift'][None, None]; R = S[1:1 + k]; P = P - np.r_[(P[0, 0] - R[0, 0])[:2], 0.]
    e = np.linalg.norm(P - R, axis=-1) * 100
    return dict(medelfel_cm=round(float(e.mean()), 1), fel_over_tid_cm=[round(float(x), 1) for x in e.mean(1)[::max(1, k // 6)]])


def en(vf, inn, kod, tyst):
    f = modal.Function.from_name('hagen-mm-tjanst', 'kor'); namn = Path(vf).stem; V = json.loads(Path(vf).read_text(encoding='utf-8')); t0 = time.time()
    try:
        r = f.remote(Path(inn).read_bytes(), json.dumps(V), kod)
    except Exception as e:
        return namn, f'ANROPET FÖLL {type(e).__name__}: {str(e)[:200]}'
    s = round(time.time() - t0, 1)
    (UT / f'logg_{namn}.txt').write_text(r['stdout'] + '\n--- STDERR ---\n' + r['stderr'], encoding='utf-8')
    rader = [f"{namn}: {'ok' if r['ok'] else 'FEL'}  väggtid {s} s, i container {r['s']} s"]
    if r['npz']:
        raw = UT / f'raw_{namn}.npz'; raw.write_bytes(r['npz']); d = np.load(raw, allow_pickle=True); z = d['pos'][:, 0, 2] - d['skift'][2]
        rader.append('  rothöjd m: ' + ' '.join(f'{z[i]:.2f}' for i in range(0, len(z), max(1, len(z) // 9))))
        if V.get('diag') != 'exempel':
            try: rader.append('  mot referensen: ' + json.dumps(folj(raw, inn), ensure_ascii=False))
            except Exception as e: rader.append(f'  folj föll: {e}')
    if not tyst or not r['ok']:
        rader += ['  ' + l[:230] for l in (r['stdout'] + r['stderr']).splitlines() if any(v in l for v in VISA)][-8:]
        if not r['ok']: rader += ['  ' + l[:230] for l in r['stderr'].splitlines()[-12:]]
    return namn, '\n'.join(rader)


def main():
    a = sys.argv[1:]; cmd = a[0] if a else 'hjalp'
    if cmd == 'ping':
        t0 = time.time(); print(modal.Function.from_name('hagen-mm-tjanst', 'ping').remote(), f'({time.time() - t0:.1f} s)'); return
    inn = a[a.index('--inn') + 1] if '--inn' in a else str(UT / 'ref_orig.npz'); tyst = '--tyst' in a
    if cmd == 'diag': filer = sorted(str(p) for p in UT.glob('diag_*.json'))
    elif cmd == 'kor': filer = [x for i, x in enumerate(a[1:], 1) if not x.startswith('--') and a[i - 1] != '--inn']
    else: print(__doc__); return
    kod = (HIT / 'kor_mm.py').read_text(encoding='utf-8'); t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        for namn, text in ex.map(lambda v: en(v, inn, kod, tyst), filer): print(text, flush=True)
    print(f'ALLT {time.time() - t0:.1f} s, {len(filer)} körningar')


if __name__ == '__main__': main()
