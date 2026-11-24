"""kontakt/1: sittande kroppar till golvet längs kamerans strålar (för Ls).

Mätning 21 nov (paket_L): stående har fötterna på cirka 0,08 m i alla klipp (L2b). Sittande ligger mellan -0,36 och +0,28 m,
dvs. under golvet eller svävande. En lodrät flytt skulle få dockan att glida av personen i originalkameran. Därför
skalas kroppen kring kamerans centrum: J' = C + s (J - C). Projektionen behålls exakt; bara avstånd och storlek ändras
(samma monokulära tvetydighet som L2b löser med fotkontakt för stående). s väljs så att den lägsta foten (median över
spåret) hamnar på 0,08 m. s begränsas till [0,75; 1,33]; utanför flaggas spåret som opålitligt och lämnas orört.
Skriver ut/<k>/paket_Ls.json (paket_L med justerade sittande kroppar) och kontakt_rapport.json. usage: python kontakt_sittande.py <nyckel...>
"""
from __future__ import annotations
import copy, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FOT_Z, SMIN, SMAX = 0.08, 0.75, 1.33


def main(nyckel):
    out = HERE / 'ut' / nyckel; p = json.loads((out / 'paket_L.json').read_text(encoding='utf-8'))
    st = json.loads((out / 'struktur.json').read_text(encoding='utf-8'))['tagningar'] if (out / 'struktur.json').is_file() else {}
    ix = {n: i for i, n in enumerate(p['leder'])}; fot = [ix['l_foot'], ix['r_foot']]
    ny = copy.deepcopy(p); rapport = {}
    for pid, info in p['personer'].items():
        if info.get('pose') != 'sittande':
            continue
        for si, seg in enumerate(p['rorelse'].get(pid, [])):
            sid = seg['tagning']; fil = out / 'struktur_in' / f'{sid}.npz'
            if not fil.is_file():
                continue
            C = np.load(fil)['C'].astype(float)
            M4 = np.array(st[sid]['transform']) if st.get(sid, {}).get('transform') else np.eye(4)
            Cw = (M4 @ np.r_[C, 1.0])[:3]  # kamerans centrum i paketets världsram
            rader = [r for r in seg['rutor'] if len(r) == 1 + 3 * len(p['leder'])]
            if not rader:
                continue
            J = np.array([r[1:] for r in rader], float).reshape(len(rader), -1, 3) / 1000.0
            zf = float(np.median(J[:, fot, 2].min(axis=1)))
            if abs(zf - Cw[2]) < 0.2:
                continue
            s = (FOT_Z - Cw[2]) / (zf - Cw[2])
            post = {'fot_fore': round(zf, 3), 'kamera_z': round(float(Cw[2]), 3), 's': round(float(s), 3)}
            if not (SMIN <= s <= SMAX):
                post['beslut'] = 'opålitligt spår (skala utanför spannet), orört'
                ny['personer'][pid].setdefault('status', {})['kontakt'] = 'opålitlig'
            else:
                for r in ny['rorelse'][pid][si]['rutor']:
                    if len(r) != 1 + 3 * len(p['leder']):
                        continue
                    a = np.array(r[1:], float).reshape(-1, 3) / 1000.0
                    a = Cw + s * (a - Cw)
                    r[1:] = [int(round(v)) for v in (a * 1000.0).ravel()]
                post['beslut'] = 'skalad längs strålarna'; post['fot_efter'] = FOT_Z
                ny['personer'][pid].setdefault('status', {})['kontakt'] = 'fötter på golvet (skala längs strålen)'
            rapport[f'{pid}/{sid}'] = post
    (out / 'paket_Ls.json').write_text(json.dumps(ny, ensure_ascii=False), encoding='utf-8')
    (out / 'kontakt_rapport.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print(nyckel, json.dumps(rapport, ensure_ascii=False))


if __name__ == '__main__':
    for k in sys.argv[1:]:
        main(k)
