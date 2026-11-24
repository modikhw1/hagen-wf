"""T1, diagnos (inte krav): hur ser ett rum av lokala mått ut, utan att någon språkmodell läser videon?

Läser bara (inga anrop, inga skrivningar utanför stdout):
  data/format/e28/tek.jsonl       17 tekniska mått per klipp (ffmpeg på 2 bilder/s-kopior)
  data/format/e30/tal.jsonl       talmått (Silero VAD)
  data/format/e37/personer.jsonl  YOLOv8n personer i 6 rutor
  data/format/e15/klipp.jsonl     konto och sållningstyp

Frågor:
  1. Hur många effektiva riktningar har rummet (deltagandekvot, antal axlar för 80 %)?
  2. Är riktningarna gemensamma? Axlar från halva kontona mot den andra halvans egna (som E15).
  3. Mush-provet: en rak 50/50-blandning av två klipp mot en "rutt" som bara flyttar de två mått
     där klippen skiljer mest. Hur ofta hamnar mellanläget utanför det riktiga klippen täcker
     (avstånd till 5 närmaste riktiga klipp över 95:e percentilen för riktiga klipp)?
     Inom samma typ och mellan typer.

Kör: scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/T1-tolkning/lokalrum.py
"""
import json
from pathlib import Path

import numpy as np

ROT = Path(__file__).resolve().parents[3]
D = ROT / 'data' / 'format'


def jl(p):
    with open(p, encoding='utf-8') as f:
        return {r['id']: r for r in (json.loads(x) for x in f if x.strip())}


tek, tal, pers, meta = (jl(D / 'e28/tek.jsonl'), jl(D / 'e30/tal.jsonl'),
                        jl(D / 'e37/personer.jsonl'), jl(D / 'e15/klipp.jsonl'))
TEK = ['langd', 'byten', 'takt', 'skott_median', 'skott_max', 'skott_max_andel', 'skott_cv', 'forsta_byte',
       'byten_3s', 'rorelse', 'rorelse_2s', 'rorelse_kvot', 'ljud_andel', 'pauser', 'forsta_ljud', 'lufs', 'lra']
TAL = ['tal_andel', 'tal_segment', 'tal_per_s', 'forsta_tal']
NAMN = TEK + TAL + ['pers_medel', 'pers_minst1', 'pers_minst2']

ids, X, konto, typ = [], [], [], []
for i in sorted(set(tek) & set(tal) & set(pers)):
    a, b, p = tek[i], tal[i], pers[i]['antal']
    # "första X" saknas när X aldrig händer (inget tal, inget byte). Då sätts det till klippets längd,
    # annars faller klipp utan tal bort och urvalet lutar mot talklipp.
    L = a.get('langd') or b.get('langd')
    fyll = lambda k, v: (L if v is None and k.startswith('forsta') else v)
    rad = [fyll(k, a.get(k)) for k in TEK] + [fyll(k, b.get(k)) for k in TAL] + [
        float(np.mean(p)), float(np.mean([x >= 1 for x in p])), float(np.mean([x >= 2 for x in p]))]
    if any(v is None for v in rad):
        continue
    ids.append(i); X.append(rad)
    konto.append(i.rsplit('-', 1)[0]); typ.append((meta.get(i) or {}).get('typ'))
X = np.array(X, float)
# skeva mått på log-skala, sedan rang-normalisering så att ingen enhet dominerar
for j, k in enumerate(NAMN):
    if k in ('langd', 'byten', 'skott_median', 'skott_max', 'forsta_byte', 'rorelse', 'rorelse_2s', 'pauser',
             'tal_segment', 'forsta_tal', 'forsta_ljud', 'lra'):
        X[:, j] = np.log1p(np.clip(X[:, j], 0, None))
Z = (X - X.mean(0)) / (X.std(0) + 1e-9)
n, d = Z.shape
konto, typ = np.array(konto), np.array(typ, dtype=object)
print(f'klipp {n}, mått {d}, konton {len(set(konto))}, med typ {sum(t is not None for t in typ)}')

# 1. effektiva riktningar
ev = np.linalg.eigvalsh(np.cov(Z.T))[::-1]
pr = ev.sum() ** 2 / (ev ** 2).sum()
k80 = int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.8) + 1)
print(f'1. deltagandekvot {pr:.2f}, axlar för 80 %: {k80} av {d}')

# 2. gemensamma axlar, halva kontona mot andra halvan (10 slumpade delningar)
rng = np.random.default_rng(20261120)
uk = np.array(sorted(set(konto)))
kvot = []
for _ in range(10):
    h = set(rng.choice(uk, len(uk) // 2, replace=False))
    m = np.array([k in h for k in konto])
    A, B = Z[m] - Z[m].mean(0), Z[~m] - Z[~m].mean(0)
    Va = np.linalg.svd(A, full_matrices=False)[2][:k80]
    Vb = np.linalg.svd(B, full_matrices=False)[2][:k80]
    kvot.append(((B @ Va.T) ** 2).sum() / ((B @ Vb.T) ** 2).sum())
print(f'2. axlar från halva kontona förklarar {np.mean(kvot):.3f} (min {np.min(kvot):.3f}) av andra halvans egna, k={k80}')

# 3. mush-provet
def knn5(Q, ref, skip_self=False):
    out = np.empty(len(Q))
    for s in range(0, len(Q), 512):
        dd = ((Q[s:s + 512, None, :] - ref[None, :, :]) ** 2).sum(-1)
        if skip_self:
            for r in range(dd.shape[0]):
                dd[r, s + r] = np.inf
        out[s:s + 512] = np.sqrt(np.sort(dd, 1)[:, :5]).mean(1)
    return out

real = knn5(Z, Z, skip_self=True)
grans = np.quantile(real, 0.95)
print(f'3. riktiga klipp: 5-NN-avstånd median {np.median(real):.2f}, 95:e percentilen {grans:.2f}')
harTyp = np.array([t is not None for t in typ])
idx = np.where(harTyp)[0]
for etikett, villkor in (('samma typ', True), ('olika typ', False)):
    par = []
    while len(par) < 1500:
        a, b = rng.choice(idx, 2, replace=False)
        if (typ[a] == typ[b]) == villkor and konto[a] != konto[b]:
            par.append((a, b))
    par = np.array(par)
    A, B = Z[par[:, 0]], Z[par[:, 1]]
    mitt = (A + B) / 2
    rutt = A.copy()
    for r in range(len(par)):
        j = np.argsort(-np.abs(B[r] - A[r]))[:2]
        rutt[r, j] = B[r, j]
    # 4. särprägel: avstånd från rummets mitt (Mahalanobis i whitenat rum), och vilken typ närmaste
    #    riktiga klipp har. En blandning som drar mot mitten är "typisk" men har tappat det som skilde.
    W = np.linalg.cholesky(np.linalg.inv(np.cov(Z.T)))
    norm = lambda Q: np.linalg.norm(Q @ W, axis=1)
    sarA, sarB = norm(A), norm(B)
    for namn, Q in (('rak 50/50', mitt), ('rutt, två mått mot B', rutt)):
        u = knn5(Q, Z) > grans
        sar = norm(Q) / np.minimum(sarA, sarB)
        nn = np.array([int(np.argmin(((Z - q) ** 2).sum(1))) for q in Q])
        tA = np.mean([typ[n_] == typ[a] for n_, a in zip(nn, par[:, 0])])
        tB = np.mean([typ[n_] == typ[b] for n_, b in zip(nn, par[:, 1])])
        print(f'   {etikett:9s} {namn:22s} utanför täckningen: {u.mean():5.1%} | '
              f'särprägel mot svagaste ändpunkt, median {np.median(sar):.2f} | '
              f'närmaste riktiga klipp har A:s typ {tA:.0%}, B:s typ {tB:.0%} (n {len(Q)})')
