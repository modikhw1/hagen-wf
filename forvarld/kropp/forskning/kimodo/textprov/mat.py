"""Mått per prov ur ut/<variant>.npz (4 prov, y upp, start mot +Z). Skriver matt.csv, matt.md och prov.csv.
  ../../../../../scen/.venv/Scripts/python.exe -X utf8 mat.py"""
import json, csv, itertools
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parent; U = HIT / 'ut'
SK = json.loads((U / 'skelett.json').read_text(encoding='utf-8')); N = SK['namn']; ix = N.index; FPS = SK['fps']
KROPP = [i for i, n in enumerate(N) if not any(f in n for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'End', 'Eye', 'Jaw'))]


def golv(v): return np.stack([v[..., 0], v[..., 2]], -1)


def vinkel(a, b):  # tecknad vinkel a->b i golvplanet, grader
    return np.degrees(np.arctan2(a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0], (a * b).sum(-1)))


def matt(P):
    T = len(P)
    hoft = golv(P[:, ix('LeftLeg')] - P[:, ix('RightLeg')]); ogon = golv(P[:, ix('LeftEye')] - P[:, ix('RightEye')])
    vrid = np.abs(vinkel(hoft, ogon))
    fram = np.stack([-hoft[:, 1], hoft[:, 0]], -1); fram /= np.linalg.norm(fram, axis=-1, keepdims=True)  # vinkelrät mot höftlinjen
    if (fram[0] * golv(P[0, ix('LeftEye')] - P[0, ix('Head')])[None]).sum() < 0: fram = -fram
    def framlut(a, b):  # lutning framåt (grader) av a->b mot lodlinjen, i sagittalplanet
        v = P[:, b] - P[:, a]; f = (golv(v) * fram).sum(-1); return np.degrees(np.arctan2(f, v[:, 1]))
    nick = framlut(ix('Neck1'), ix('HeadEnd')) - framlut(ix('Hips'), ix('Neck1'))   # huvudet relativt bålen
    axel = (P[:, [ix('LeftArm'), ix('RightArm')], 1].mean(1) - P[:, ix('Neck1'), 1]) * 100
    bal = framlut(ix('Hips'), ix('Chest'))
    hand = P[:, [ix('LeftHand'), ix('RightHand')], 1].mean(1)
    Q = P[:, KROPP]; steg = np.linalg.norm(np.diff(Q, axis=0), axis=-1)
    return dict(vrid_max=vrid.max(), vrid_slut=vrid[-5:].mean(), nick_max=nick.max(), nick_slut=nick[-5:].mean(),
                axel_slut=axel[-5:].mean(), axel_sank=axel[:5].mean() - axel.min(), bal_slut=bal[-5:].mean(), bal_max=bal.max(),
                hand_start=hand[:5].mean(), hand_slut=hand[-5:].mean(), hand_min=hand.min(),
                rorelse=steg.sum(), fart=steg.mean() * FPS)


def spridning(Ps):  # medelavstånd mellan proven, höftrelativa kroppsleder, cm
    R = [P[:, KROPP] - P[:, :1] for P in Ps]
    return np.mean([np.linalg.norm(a - b, axis=-1).mean() for a, b in itertools.combinations(R, 2)]) * 100


def main():
    V = json.loads((U / 'varianter.json').read_text(encoding='utf-8')); rader, prov = [], []
    for v in V:
        Ps = np.load(U / f"{v['namn']}.npz")['posed_joints']; M = [matt(P) for P in Ps]
        for i, m in enumerate(M): prov.append({'variant': v['namn'], 'prov': i, **{k: round(float(x), 3) for k, x in m.items()}})
        r = {'variant': v['namn'], 'w': v['w']}
        for k in M[0]:
            a = np.array([m[k] for m in M]); r[k] = round(float(a.mean()), 2); r[k + '_sd'] = round(float(a.std()), 2)
        r['spridning_cm'] = round(float(spridning(Ps)), 1); rader.append(r)
    with open(HIT / 'matt.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rader[0])); w.writeheader(); w.writerows(rader)
    with open(HIT / 'prov.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0])); w.writeheader(); w.writerows(prov)
    kol = [('vrid_max', 'vrid max°', 0), ('vrid_slut', 'vrid slut°', 0), ('nick_max', 'nick max°', 0), ('axel_sank', 'axelsänk cm', 1), ('bal_slut', 'bål slut°', 0),
           ('hand_start', 'hand start m', 2), ('hand_slut', 'hand slut m', 2), ('hand_min', 'hand min m', 2), ('rorelse', 'rörelse m', 0), ('fart', 'fart m/s', 2)]
    ut = ['| variant | w | ' + ' | '.join(k[1] for k in kol) + ' | spridn cm |', '|' + '---|' * (len(kol) + 3)]
    for r in rader:
        ut.append(f"| {r['variant']} | {r['w']:g} | " + ' | '.join(f"{r[k]:.{d}f}±{r[k + '_sd']:.{d}f}" for k, _, d in kol) + f" | {r['spridning_cm']} |")
    (HIT / 'matt.md').write_text('\n'.join(ut) + '\n', encoding='utf-8'); print('\n'.join(ut))


if __name__ == '__main__': main()
