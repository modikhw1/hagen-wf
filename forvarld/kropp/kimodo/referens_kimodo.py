"""0040: referens för Kimodo ur mal.json (GRANSSNITT-form): originalet i SOMA (lokala rotationer, rot), vänster hands mål och vikt per ruta."""
import json, sys
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[2]; sys.path.insert(0, str(HIT)); sys.path.insert(0, str(HIT.parent / 'forskning/mm'))
import mhr_soma as K
from kroppsmodell import vikter

TILL_SOMA = {'L_Hand': 'LeftHand', 'R_Hand': 'RightHand'}


def bygg(malf, ut):
    M = json.loads(Path(malf).read_text(encoding='utf-8')); z = dict(np.load(ROOT / M['kalla_rorelse'])); V = np.load(ROOT / M['varld'])
    u = K.till_soma(z, V); S = K.fk_soma(u['G'], u['rot']); n = len(S); mal = np.zeros((n, 3)); w = np.zeros(n)
    for m in M['mal']:
        ww = vikter(n, *m['rutor'], M.get('ramp_rutor', 8)); ny = ww > w; mal[ny] = S[ny, K.SN.index(TILL_SOMA[m['kalla_kroppsdel']])]; w = np.maximum(w, ww)
    np.savez(ut, lok=u['lok'].astype(np.float32), rot=u['rot'].astype(np.float32), mal=mal.astype(np.float32), mal_vikt=w.astype(np.float32))
    return u


if __name__ == '__main__': bygg(sys.argv[1], sys.argv[2]); print('ok')
