"""Tema som räknebart avstånd: en vektor per formatkort ur kärna + handling.

Modell: intfloat/multilingual-e5-small (öppen, körs lokalt på CPU, laddas ned en gång via transformers).
Faller tillbaka på TF-IDF över ord om modellen inte går att hämta.
Skriver ut/tema.npz (ids, vektorer, metod). Inga betalda anrop.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
MODELL = 'intfloat/multilingual-e5-small'


def texter():
    ids, tx = [], []
    for line in open(UT / 'klipp.jsonl', encoding='utf-8'):
        r = json.loads(line)
        if 'l4' in r:
            ids.append(r['id'])
            tx.append(f"{r['l4'].get('karna') or ''} {r['l4'].get('handling') or ''}".strip())
    n = json.loads((HERE / 'notan_kort.json').read_text(encoding='utf-8'))
    ids.append(n['id'])
    tx.append(f"{n['l4']['karna']} {n['l4']['handling']}")
    return ids, tx


def e5(tx):
    import torch
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODELL)
    mod = AutoModel.from_pretrained(MODELL).eval()
    ut = []
    with torch.no_grad():
        for i in range(0, len(tx), 32):
            b = tok(['query: ' + t for t in tx[i:i + 32]], padding=True, truncation=True, max_length=256, return_tensors='pt')
            h = mod(**b).last_hidden_state
            m = b['attention_mask'].unsqueeze(-1).float()
            v = (h * m).sum(1) / m.sum(1)
            ut.append(torch.nn.functional.normalize(v, dim=1).numpy())
            print(f'\r{i + 32}/{len(tx)}', end='', file=sys.stderr)
    return np.vstack(ut)


def tfidf(tx):
    docs = [re.findall(r'[a-zåäöé]{3,}', t.lower()) for t in tx]
    ordl = {}
    for d in docs:
        for w in set(d):
            ordl[w] = ordl.get(w, 0) + 1
    vok = {w: i for i, w in enumerate(w for w, n in ordl.items() if 2 <= n <= len(tx) * 0.2)}
    X = np.zeros((len(tx), len(vok)), np.float32)
    for i, d in enumerate(docs):
        for w in d:
            if w in vok:
                X[i, vok[w]] += 1
    X = np.log1p(X) * np.log(len(tx) / np.array([ordl[w] for w in vok]))
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)


if __name__ == '__main__':
    ids, tx = texter()
    try:
        V, metod = e5(tx), MODELL
    except Exception as e:  # ingen nätåtkomst eller liknande
        print('e5 gick inte:', repr(e)[:200], file=sys.stderr)
        V, metod = tfidf(tx), 'tfidf'
    np.savez_compressed(UT / 'tema.npz', ids=np.array(ids), V=V.astype(np.float32), metod=metod)
    print('\n', metod, V.shape)
