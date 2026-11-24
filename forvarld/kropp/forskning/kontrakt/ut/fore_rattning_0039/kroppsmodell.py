"""FORSKNING (0039): kedjans steg `kroppsmodell`. En frihetsgrad ur liggaren -> mål (mal.json, GRANSSNITT-form) -> MaskedMimic på Modal
-> ny MHR-sekvens och plan, märkta licens: forskning.

  scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/kroppsmodell.py <mal.json> <ut-namn> [--utan-modal <mm.npz>]
Kräver "licens": "forskning" i mal.json; utan den vägrar steget (AMASS-tränade vikter får inte bli standardväg).
"""
import json, subprocess, sys, time, os
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[3]; PY = ROOT / 'scen/.venv/Scripts/python.exe'
sys.path.insert(0, str(HIT)); import mhr_smpl as M


def vikter(n, a, b, ramp):
    w = np.zeros(n)
    for f in range(n):
        if a <= f < b: w[f] = 1
        elif a - ramp <= f < a: w[f] = (f - a + ramp) / ramp
        elif b <= f < b + ramp: w[f] = 1 - (f - b + 1) / ramp
    return w


def main():
    mf = Path(sys.argv[1]); namn = sys.argv[2]; K = json.loads(mf.read_text(encoding='utf-8')); t0 = time.time()
    if K.get('licens') != 'forskning': sys.exit('kroppsmodell: mal.json saknar "licens": "forskning"; MaskedMimic SMPL är AMASS-tränad och får inte gå in utan flaggan')
    ut = HIT / 'ut' / namn; ut.mkdir(parents=True, exist_ok=True)
    z = dict(np.load(ROOT / K['kalla_rorelse'])); V = np.load(ROOT / K['varld']); u = M.till_smpl(z, V); S = M.fk_smpl(u['G'], u['rot']); n = len(S)
    kroppar = sorted({m['kroppsdel'] for m in K['mal']}); mal = np.zeros((n, len(kroppar), 3)); w = np.zeros((n, len(kroppar)))
    for m in K['mal']:
        k = kroppar.index(m['kroppsdel']); ww = vikter(n, *m['rutor'], K.get('ramp_rutor', 8)); ny = ww > w[:, k]
        mal[ny, k] = S[ny, M.SN.index(m['kalla_kroppsdel'])]; w[:, k] = np.maximum(w[:, k], ww)
    np.savez(ut / 'ref.npz', G=u['G'].astype(np.float32), rot=u['rot'].astype(np.float32), fps=K.get('fps', 29.97), mal_namn=np.array(kroppar), mal=mal.astype(np.float32), mal_vikt=w.astype(np.float32))
    (ut / 'villkor.json').write_text(json.dumps(dict(villkor=K['villkor'], steg=n - 2), ensure_ascii=False), encoding='utf-8')
    mm = ut / 'mm.npz'
    if '--utan-modal' in sys.argv: mm = Path(sys.argv[sys.argv.index('--utan-modal') + 1])
    else:
        r = subprocess.run([str(PY), '-m', 'modal', 'run', str(HIT / 'modal_mm.py'), '--inn', str(ut / 'ref.npz'), '--villkor', str(ut / 'villkor.json'), '--ut', str(mm)],
                           cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'), capture_output=True, text=True)
        (ut / 'modal.log').write_text(r.stdout + r.stderr, encoding='utf-8')
        if r.returncode: sys.exit(f'Modal föll; se {ut / "modal.log"}')
    subprocess.run([str(PY), str(HIT / 'efter_mm.py'), str(mm), namn], cwd=ROOT, check=True, env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    print('KROPPSMODELL_KLAR', namn, round(time.time() - t0, 1), 's')


if __name__ == '__main__': main()
