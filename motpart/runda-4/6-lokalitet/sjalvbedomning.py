"""Självbedömning för Ls: vilka tagningar riskerar att inte vara god nog, ur mått pipen redan har.

Varför: L8 dömde "hög" på tagningar som facit underkände. Vid 200–500 klipp behövs en egen signal för vad som går att lita
på och vad som ska granskas. Mått per tagning (ingen domare används som indata): skärpa (Laplace), ljus (medelvärde),
kamerarörelse (L9), personandel, texturerade trianglar, förkastade ytor, antal SAM 3-föremål, fyllnadstillit.
Etikett: domarnas god nog för Ls (ja/delvis = 1, nej = 0), majoritet över tillgängliga prov med samma Ls-version.
Prövning: lämna-ett-klipp-utanför (hela klipp hålls ute), enkel regel + logistisk regression; rapporterar träff och
hur mycket som flaggas. usage: python sjalvbedomning.py <nyckelfil> <domfil> [<nyckelfil> <domfil> ...]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
KLIPP = ['duepiani', 'spanjorskan', '08burgerkebab', 'babasburgers', 'kennysgelato2.0', 'blackstone', 'fratelli', 'chickenstreet']


def matt():
    rader = {}
    for k in KLIPP:
        rep = json.loads((HERE / 'ut' / k / 'struktur_rapport.json').read_text(encoding='utf-8'))
        lok = json.loads((HERE / 'ut' / k / 'lokalitet.json').read_text(encoding='utf-8'))['tagningar']
        plan = json.loads((HERE / 'ut' / 'rumshjarna' / k / 'plan.json').read_text(encoding='utf-8'))['tagningar']
        for sid, r in rep.items():
            org = cv2.imread(str(HERE / 'ut' / 'rumshjarna' / k / f'{sid}_orig.png'), cv2.IMREAD_GRAYSCALE)
            if org is None:
                continue
            t = lok.get(sid, {}); km = t.get('kamerarorelse') or {}
            rader[f'{k}/{sid}'] = {
                'skarpa': float(np.log10(cv2.Laplacian(org, cv2.CV_64F).var() + 1)), 'ljus': float(org.mean() / 255),
                'rorelse': float(np.log1p(km.get('grader', 0) or 0)) if isinstance(km, dict) else 0.0,
                'person': float(plan.get(sid, {}).get('personandel', 0)), 'textur': float(r.get('texturerade_trianglar', 0)),
                'forkastade': float(len(r.get('forkastade', []))), 'foremal': float(np.log1p(r.get('sam3_foremal', 0) or 0)),
                'vaggar': float(r.get('vaggar', 0)), 'L8_hog': float((t.get('tillforlitlighet') or {}).get('dom') == 'hög')}
    return rader


def etiketter(par):
    rost = {}
    for nfil, dfil in par:
        nyc = json.loads(Path(nfil).read_text()); d = json.loads(Path(dfil).read_text(encoding='utf-8')); d = d if isinstance(d, list) else d.get('tagningar', d)
        for x in d:
            ls = 'X' if nyc[x['tagning']]['X'] == 'Ls' else 'Y'
            v = x.get('god_nog_' + ls)
            if v in ('ja', 'delvis', 'nej'):
                rost.setdefault(x['tagning'], []).append(1 if v in ('ja', 'delvis') else 0)
    return {t: int(np.mean(v) >= 0.5) for t, v in rost.items()}


def main(argv):
    par = list(zip(argv[0::2], argv[1::2])); M = matt(); Y = etiketter(par)
    ids = [t for t in M if t in Y]; namn = list(next(iter(M.values())).keys())
    X = np.array([[M[t][n] for n in namn] for t in ids]); y = np.array([Y[t] for t in ids]); klipp = np.array([t.split('/')[0] for t in ids])
    print(f'{len(ids)} tagningar, god nog (ja/delvis) {y.sum()}, nej {len(y) - y.sum()}')
    for j, n in enumerate(namn):  # enskilda måtts samband med utfallet
        a, b = X[y == 1, j], X[y == 0, j]
        print(f'  {n:10s} god {a.mean():6.3f}  nej {b.mean():6.3f}')
    def anpassa(Xt, yt, lam=1.0, steg=3000):  # logistisk regression med L2 (numpy), standardiserade mått
        mu, sd = Xt.mean(0), Xt.std(0) + 1e-9; Z = (Xt - mu) / sd; w = np.zeros(Z.shape[1]); b0 = 0.0
        for _ in range(steg):
            p_ = 1 / (1 + np.exp(-(Z @ w + b0))); w -= 0.3 * (Z.T @ (p_ - yt) / len(yt) + lam * w / len(yt)); b0 -= 0.3 * (p_ - yt).mean()
        return mu, sd, w, b0

    def prob(m, Xe):
        mu, sd, w, b0 = m
        return 1 / (1 + np.exp(-(((Xe - mu) / sd) @ w + b0)))
    pred = np.zeros(len(y))
    for k in np.unique(klipp):  # lämna ett klipp utanför
        tr, te = klipp != k, klipp == k
        pred[te] = prob(anpassa(X[tr], y[tr]), X[te]) if len(np.unique(y[tr])) > 1 else y[tr].mean()
    for tro in (0.4, 0.5, 0.6):
        flagg = pred < tro
        fn = int(((~flagg) & (y == 0)).sum()); tp = int((flagg & (y == 0)).sum())
        print(f'tröskel {tro}: flaggar {flagg.sum()}/{len(y)}, fångar {tp}/{(y == 0).sum()} av nej, släpper {fn} nej utan flagga')
    base = (X[:, namn.index('L8_hog')] == 1)
    print(f'L8 hög: {base.sum()} tagningar, varav nej {int((base & (y == 0)).sum())}')
    m = anpassa(X, y)
    vikt = sorted(zip(namn, m[2]), key=lambda x: -abs(x[1])); print('vikter (standardiserade):', [(n, round(float(v), 2)) for n, v in vikt])
    ut = {'ids': ids, 'pred_lokal': dict(zip(ids, [round(float(p), 3) for p in pred])), 'vikter': [(n, float(v)) for n, v in vikt]}
    (HERE / 'ut' / 'sjalvbedomning.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
