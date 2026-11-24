"""Streckbilder: per variant prov 0 i 6 rutor (framifrån och ovanifrån) + slutrutan för alla 4 prov framifrån.
  ../../../../../scen/.venv/Scripts/python.exe -X utf8 bild.py <ut.png> <variant> [...]"""
import sys, json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HIT = Path(__file__).resolve().parent; U = HIT / 'ut'
SK = json.loads((U / 'skelett.json').read_text(encoding='utf-8')); FAR = SK['foraldrar']; N = SK['namn']
VIS = [i for i, n in enumerate(N) if not any(f in n for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'End'))]
FARG = ['#222', '#c33', '#36c', '#3a3']


def rita(x, p, a, b, c='#222', lw=1.2):
    for j in VIS:
        f = FAR[j]
        if f >= 0: x.plot([p[j, a], p[f, a]], [p[j, b], p[f, b]], '-', c=c, lw=lw)
    h = N.index('Head'); e = N.index('LeftEye'), N.index('RightEye')
    m = p[list(e)].mean(0); x.plot([p[h, a], p[h, a] + 4 * (m[a] - p[h, a])], [p[h, b], p[h, b] + 4 * (m[b] - p[h, b])], '-', c='#e80', lw=2)  # blickriktning


def main():
    ut, namn = Path(sys.argv[1]), sys.argv[2:]; R = 6
    fig, ax = plt.subplots(2 * len(namn), R + 1, figsize=((R + 1) * 1.9, 2 * len(namn) * 2.0))
    for i, n in enumerate(namn):
        Ps = np.load(U / f'{n}.npz')['posed_joints']; P = Ps[0]; T = len(P); o = P[0, 0].copy()
        for k, t in enumerate(np.linspace(0, T - 1, R).astype(int)):
            for v, (a, b) in enumerate(((0, 1), (0, 2))):
                x = ax[2 * i + v, k]; rita(x, P[t] - o, a, b); x.set_aspect('equal'); x.axis('off')
                x.set_xlim(-0.6, 0.6); x.set_ylim((-1.05, 0.7) if v == 0 else (-0.5, 0.7))
                if k == 0: x.set_title(f"{n} {'fram' if v == 0 else 'ovan'}", fontsize=8, loc='left')
                elif v == 0: x.set_title(f'{t / SK["fps"]:.1f} s', fontsize=7)
        for v, (a, b) in enumerate(((0, 1), (0, 2))):
            x = ax[2 * i + v, R]
            for s in range(len(Ps)): rita(x, Ps[s, -1] - Ps[s, 0, 0], a, b, FARG[s], 0.9)
            x.set_aspect('equal'); x.axis('off'); x.set_xlim(-0.6, 0.6); x.set_ylim((-1.05, 0.7) if v == 0 else (-0.5, 0.7))
            if v == 0: x.set_title('slut, 4 prov', fontsize=7)
    plt.tight_layout(); fig.savefig(ut, dpi=80); print('BILD', ut)


if __name__ == '__main__': main()
