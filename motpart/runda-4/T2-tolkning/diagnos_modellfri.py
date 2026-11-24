"""T2-diagnos (20 nov 2026): bär modellfria mått klippets identitet, och vad händer med den
när två klipp blandas (medelpunkt) jämfört med när de byter värden dimension för dimension?

Inga modellanrop. Läser bara befintliga filer. Skriver bara diagnos_modellfri.json bredvid sig.
Kör från repo-roten:
  scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/T2-tolkning/diagnos_modellfri.py

Typ = (strategi, tilltal) ur formatkortet (byggsten/hand/ut/rum.jsonl), dvs en LLM-läsning.
Modellfria mått: e28/tek.jsonl (ffmpeg, rörelse, ljud), e30/tal.jsonl (Silero VAD), e37/personer.jsonl (YOLOv8n).
Jämförelse: de LLM-lästa fingrarna i rum.jsonl (f: ensemble, ord, produkt, poang_*, vandning).

Allt är diagnos. Inga trösklar här är ägarens.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROT = Path(__file__).resolve().parents[3]
UT = Path(__file__).resolve().parent / 'diagnos_modellfri.json'
RNG = np.random.default_rng(20261120)


def jsonl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(x) for x in f if x.strip()]


def konto(i):
    return i.rsplit('-', 1)[0]


rum = {r['id']: r for r in jsonl(ROT / 'byggsten/hand/ut/rum.jsonl') if not r.get('handkodad')}
tek = {r['id']: r for r in jsonl(ROT / 'data/format/e28/tek.jsonl')}
tal = {r['id']: r for r in jsonl(ROT / 'data/format/e30/tal.jsonl')}
pers = {r['id']: r for r in jsonl(ROT / 'data/format/e37/personer.jsonl')}

TEK = ['langd', 'takt', 'skott_median', 'skott_max_andel', 'skott_cv', 'forsta_byte', 'rorelse',
       'rorelse_kvot', 'ljud_andel', 'pauser', 'lufs', 'lra']
TAL = ['tal_andel', 'tal_segment', 'tal_per_s', 'forsta_tal']
LLM = ['ensemble', 'ord', 'produkt', 'poang_i_ord', 'poang_i_sak', 'poang_i_klipp', 'poang_i_person', 'vandning']


def modellfri(i):
    t, s, p = tek.get(i), tal.get(i), pers.get(i)
    if not (t and s and p):
        return None
    v = [t.get(k) for k in TEK] + [s.get(k) for k in TAL]
    a = p.get('antal') or []
    if not a:
        return None
    v += [float(np.mean(a)), float(np.mean([x >= 1 for x in a])), float(np.mean([x >= 2 for x in a]))]
    if any(x is None for x in v):
        return None
    return [float(x) for x in v]


def llm(i):
    f = rum[i]['f']
    v = [f.get(k) for k in LLM]
    return None if any(x is None for x in v) else [float(x) for x in v]


ids, X, L, Y, G = [], [], [], [], []
for i, r in rum.items():
    m, l = modellfri(i), llm(i)
    if m is None or l is None or not r.get('strategi'):
        continue
    ids.append(i)
    X.append(m)
    L.append(l)
    Y.append(f"{r['strategi']}|{r['tilltal']}")
    G.append(konto(i))
X, L = np.array(X), np.array(L)
# rangtransform per kolumn (robust mot skeva mått), sedan z
def rangz(A):
    R = np.argsort(np.argsort(A, axis=0), axis=0).astype(float)
    return (R - R.mean(0)) / (R.std(0) + 1e-9)
Xz, Lz = rangz(X), rangz(L)
typer = [t for t, n in Counter(Y).items() if n >= 30]
behall = np.array([y in typer for y in Y])
Y = np.array(Y)
G = np.array(G)
ids = np.array(ids)

NAMN_MF = TEK + TAL + ['personer_medel', 'andel_minst_en', 'andel_minst_tva']


def knn_konto_ut(F, y, g, k=7):
    """kNN där grannar från samma konto aldrig räknas (konto hålls undan)."""
    D = ((F[:, None, :] - F[None, :, :]) ** 2).sum(-1)
    samma = g[:, None] == g[None, :]
    D[samma] = np.inf
    ratt = 0
    for a in range(len(F)):
        nn = np.argsort(D[a])[:k]
        pred = Counter(y[nn]).most_common(1)[0][0]
        ratt += pred == y[a]
    return ratt / len(F)


def eta2(F, y):
    ut = []
    for j in range(F.shape[1]):
        v = F[:, j]
        tot = ((v - v.mean()) ** 2).sum()
        mel = sum((y == t).sum() * (v[y == t].mean() - v.mean()) ** 2 for t in set(y))
        ut.append(float(mel / tot))
    return ut


res = {'n_klipp': int(len(ids)), 'n_klipp_typ_ge_30': int(behall.sum()), 'typer': {t: int((Y == t).sum()) for t in typer},
       'konton': int(len(set(G)))}
Fm, Fl, y, g = Xz[behall], Lz[behall], Y[behall], G[behall]
bas = Counter(y).most_common(1)[0][1] / len(y)
res['typ_ur_grannar'] = {
    'majoritet': round(bas, 3),
    'modellfritt_19_matt': round(knn_konto_ut(Fm, y, g), 3),
    'llm_fingrar_8': round(knn_konto_ut(Fl, y, g), 3),
    'bada': round(knn_konto_ut(np.hstack([Fm, Fl]), y, g), 3),
}
res['eta2_per_matt_modellfritt'] = dict(sorted(zip(NAMN_MF, [round(x, 3) for x in eta2(Fm, y)]), key=lambda x: -x[1]))
res['eta2_per_finger_llm'] = dict(sorted(zip(LLM, [round(x, 3) for x in eta2(Fl, y)]), key=lambda x: -x[1]))


# Kontot (ytan, "etniciteten") ur närmaste granne, modellfritt: andel där närmaste granne är samma konto
def konto_nn(F, g):
    D = ((F[:, None, :] - F[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(D, np.inf)
    nn = D.argmin(1)
    return float((g[nn] == g).mean())


slump_konto = sum((c / len(g)) * ((c - 1) / (len(g) - 1)) for c in Counter(g).values())
res['konto_ur_narmaste_granne'] = {'slump': round(slump_konto, 3), 'modellfritt': round(konto_nn(Fm, g), 3),
                                   'llm_fingrar': round(konto_nn(Fl, g), 3)}


# Mush-provet: par av klipp med olika typ. Medelpunkt mot korsning (varje dimension tas helt från A eller B).
# Mått: (1) typens tydlighet = andel av k grannar som har samma typ som den vanligaste bland dem,
#       (2) stöd = avstånd till närmaste verkliga klipp, delat med medianen av verkliga klipps NN-avstånd,
#       (3) särprägel = avstånd till mitten av alla klipp (lägre = mer genomsnittlig),
#       (4) kan man fortfarande se vem den kom ifrån: närmaste ändpunkt i de dimensioner som inte byttes.
F = Fm
D_rr = ((F[:, None, :] - F[None, :, :]) ** 2).sum(-1)
np.fill_diagonal(D_rr, np.inf)
nn_med = float(np.median(np.sqrt(D_rr.min(1))))
mitt = F.mean(0)


def profil(p, utan=(), k=15):
    d = ((F - p) ** 2).sum(1)
    d[list(utan)] = np.inf  # ändpunkterna själva räknas inte som stöd
    nn = np.argsort(d)[:k]
    c = Counter(y[nn]).most_common(1)[0]
    return {'tydlighet': c[1] / k, 'stod': float(np.sqrt(d[nn[0]])) / nn_med, 'sarpragel': float(np.sqrt(((p - mitt) ** 2).sum()))}


rader = defaultdict(list)
for _ in range(600):
    a, b = RNG.choice(len(F), 2, replace=False)
    if y[a] == y[b]:
        continue
    A, B = F[a], F[b]
    M = (A + B) / 2
    mask = RNG.random(len(A)) < 0.5
    C = np.where(mask, A, B)
    # Vald korsning: bland 64 slumpade masker där 30-70 % av dimensionerna byts, den som har bäst stöd.
    # Det är en sökning efter en kompromiss som finns i banken, inte en ny generering.
    bast = None
    for _ in range(64):
        m = RNG.random(len(A)) < RNG.uniform(0.3, 0.7)
        if not (0.3 <= m.mean() <= 0.7):
            continue
        q = np.where(m, A, B)
        pr = profil(q, utan=(a, b))
        if bast is None or pr['stod'] < bast[1]['stod']:
            bast = (q, pr)
    for namn, p in (('A', A), ('medel', M), ('korsning', C)):
        for k, v in profil(p, utan=(a, b)).items():
            rader[f'{namn}_{k}'].append(v)
    if bast:
        for k, v in bast[1].items():
            rader[f'vald_korsning_{k}'].append(v)
res['mush_prov'] = {k: {'median': round(float(np.median(v)), 3), 'medel': round(float(np.mean(v)), 3)} for k, v in sorted(rader.items())}
res['mush_prov']['andel_stod_som_verkligt_klipp'] = {n: round(float(np.mean(np.array(rader[f'{n}_stod']) <= 1.0)), 3) for n in ('A', 'medel', 'korsning', 'vald_korsning')}
res['mush_prov']['par'] = len(rader['A_stod'])
res['mush_prov']['nn_median_verkliga'] = round(nn_med, 3)
res['not'] = ('Typ är en LLM-läsning (formatkortet). Modellfria mått är 19 mått ur e28/e30/e37. '
              'kNN med k=7 och grannar från samma konto bortplockade. Mush-provet är ett räkneexempel i ett '
              '19-dimensionellt mätrum, inte en perceptuell dom.')
UT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(res, ensure_ascii=False, indent=1))
