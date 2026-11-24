"""FORSKNING/0040: Kimodo-utfall som streckgubbar, framifrån och från sidan, för att jämföra textprompter.
  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/kimodo/streck.py <ut.png> <namn> [<namn> ...]
Läser ut/<namn>.npz (posed_joints) och ut/<namn>.bvh (leder och föräldrar)."""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HIT = Path(__file__).resolve().parent; U = HIT / 'ut'


def foraldrar(bvh):
    namn, far, stack = [], [], []
    for rad in bvh.read_text(encoding='utf-8', errors='replace').splitlines():
        o = rad.split()
        if not o: continue
        if o[0] in ('ROOT', 'JOINT'): namn.append(o[1]); far.append(stack[-1] if stack else -1); stack.append(len(namn) - 1)
        elif o[0] == 'End': stack.append(None)
        elif o[0] == '}': stack.pop()
        elif o[0] == 'MOTION': break
    return namn, far


def main():
    ut, namn = Path(sys.argv[1]), sys.argv[2:]; rutor = 6
    fig, ax = plt.subplots(2 * len(namn), rutor, figsize=(rutor * 2.2, 2 * len(namn) * 2.6))
    for i, n in enumerate(namn):
        d = np.load(U / f'{n}.npz'); P = d['posed_joints']; T, J, _ = P.shape
        ln, far = foraldrar(U / f'{n}.bvh')
        if len(far) == J + 1 and ln[0] == 'Root': far = [f - 1 for f in far[1:]]   # BVH har en extra Root före Hips
        if len(far) != J: far = [-1] * J   # okänd ordning: bara punkter
        upp = int(np.argmax(P.reshape(-1, 3).max(0) - P.reshape(-1, 3).min(0) * 0 - P[:, :, :].mean((0, 1)))) if False else 1
        ho = [k for k in range(3) if k != upp]
        # framåt = rotens medelriktning i golvplanet saknas: använd huvudaxlarna i golvplanet
        Q = P - P[:, :1].mean(0, keepdims=True)
        for k, t in enumerate(np.linspace(0, T - 1, rutor).astype(int)):
            for v, (a, b) in enumerate(((ho[0], upp), (ho[1], upp))):
                x = ax[2 * i + v, k]; p = Q[t]
                for j, f in enumerate(far):
                    if f >= 0: x.plot([p[j, a], p[f, a]], [p[j, b], p[f, b]], '-', c='#333', lw=1.2)
                x.scatter(p[:, a], p[:, b], s=2, c='#c33'); x.set_aspect('equal'); x.set_xlim(-0.8, 0.8); x.set_ylim(Q[..., upp].min() - 0.05, Q[..., upp].max() + 0.05); x.axis('off')
                if k == 0: x.set_title(f"{n} {'fram' if v == 0 else 'sida'}", fontsize=8, loc='left')
                elif v == 0: x.set_title(f'ruta {t}', fontsize=7)
    plt.tight_layout(); fig.savefig(ut, dpi=90); print('STRECK', ut)


if __name__ == '__main__': main()
