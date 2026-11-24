"""Fables läsning av sketchkortens kärna: fyra slutna fält som metadatan saknar.

Underlag: bara kortets kärna (en mening, skriven av Gemini Flash 3.8). Ingen video.
Läst av Fable 5.2 den 14 nov 2026, en gång, i tre omgångar (lasning_fable_1..3.txt).

Fälten:
  mekanik  typen av skämt
  relation vem som spelar mot vem
  offer    vem det går ut över
  insats   vad som står på spel mellan dem

Stabilitet mäts på tvillingar: kort från olika klipp med nästan samma kärna (temavektorer, cos >= TVILLING).
Läsaren visste inte vilka som var tvillingar. Kör efter tema.py.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
TVILLING = 0.93

MEKANIK = {'K': 'kontrast', 'A': 'avslojande', 'B': 'bokstavligt', 'E': 'eskalering', 'F': 'fasad',
           'O': 'overdrift', 'S': 'satt_pa_plats', 'M': 'missforstand', 'I': 'igenkanning', 'X': 'ingen'}
RELATION = {'pg': 'personal_mot_gast', 'gp': 'gast_mot_personal', 'pp': 'personal_sinsemellan',
            'cp': 'chef_och_personal', 'gg': 'gaster_sinsemellan', 'p1': 'personal_ensam', 'x': 'annan'}
OFFER = {'p': 'personal', 'g': 'gast', 'c': 'chef', 'i': 'ingen'}
INSATS = {'b': 'betalning', 's': 'service', 'm': 'mat', 'u': 'uppmarksamhet', 'v': 'vila', 'r': 'regler', 'i': 'ingen'}
FALT = ['mekanik', 'relation', 'offer', 'insats']

NOTAN = {'mekanik': 'avslojande', 'relation': 'gaster_sinsemellan', 'offer': 'gast', 'insats': 'betalning'}


def main():
    ids = json.loads((UT / 'lasning_ids.json').read_text())
    L = {}
    for n in (1, 2, 3):
        for rad in (HERE / f'lasning_fable_{n}.txt').read_text().split():
            i, kod = rad.split(':')
            m, r, o, v = kod.split(',')
            L[ids[int(i)]] = {'mekanik': MEKANIK[m], 'relation': RELATION[r], 'offer': OFFER[o], 'insats': INSATS[v]}
    assert len(L) == len(ids), (len(L), len(ids))
    L['d-dialog-notan'] = NOTAN

    rapport = {'antal': len(L), 'fordelning': {f: dict(Counter(x[f] for x in L.values()).most_common()) for f in FALT}}

    t = np.load(UT / 'tema.npz')
    tid = [str(x) for x in t['ids']]
    ix = [tid.index(i) for i in ids]
    V = t['V'][ix]
    S = V @ V.T
    np.fill_diagonal(S, 0)
    par = [(a, b) for a in range(len(ids)) for b in range(a) if S[a, b] >= TVILLING]
    konton = lambda i: i.rsplit('-', 1)[0]
    stab = {}
    for f in FALT:
        lika = [L[ids[a]][f] == L[ids[b]][f] for a, b in par]
        # slumpnivå: andel lika bland alla par
        c = Counter(x[f] for i, x in L.items() if i in ids)
        slump = sum((n / len(ids)) ** 2 for n in c.values())
        po = float(np.mean(lika)) if lika else None
        stab[f] = {'lika': round(po, 3) if lika else None, 'slump': round(slump, 3),
                   'kappa': round((po - slump) / (1 - slump), 3) if lika else None}
    rapport['tvillingar'] = {'troskel': TVILLING, 'par': len(par),
                             'par_mellan_olika_konton': sum(konton(ids[a]) != konton(ids[b]) for a, b in par),
                             'stabilitet': stab,
                             'oeniga_exempel': [{'a': ids[a], 'b': ids[b], 'la': L[ids[a]], 'lb': L[ids[b]]}
                                                for a, b in par if L[ids[a]] != L[ids[b]]][:12]}

    (UT / 'lasning.json').write_text(json.dumps(L, ensure_ascii=False, indent=0), encoding='utf-8')
    (UT / 'lasning_prov.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in rapport.items() if k != 'tvillingar'}, ensure_ascii=False))
    print(rapport['tvillingar']['par'], rapport['tvillingar']['par_mellan_olika_konton'], rapport['tvillingar']['stabilitet'])


if __name__ == '__main__':
    main()
