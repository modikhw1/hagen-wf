"""Fables läsning av tilltalsklippens kärna (strategi tilltal, till kameran): tre slutna fält.

  grepp    vad talaren gör med tittarens uppmärksamhet
  motpart  vem talaren vänder sig till eller spelar mot
  last     vad som bär intresset

Underlag: kortets kärna (en mening, skriven av Gemini). Läst en gång av Fable 5.2, 14 nov 2026.
Stabilitet mäts på tvillingar (temavektorer, cos >= TVILLING), som i lasning.py.
Skriver in fälten i ut/lasning.json bredvid sketchläsningen, och ut/lasning2_prov.json.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
TVILLING = 0.93

GREPP = {'Q': 'svarar_pa_fraga', 'P': 'provsmakar', 'T': 'visar_tillagning', 'L': 'guidar', 'U': 'utmanar_publiken',
         'E': 'annonserar', 'B': 'bakom_kulisserna', 'S': 'tycker_till', 'K': 'krok_som_vander', 'X': 'annat'}
MOTPART = {'t': 'tittaren', 'k': 'kollega', 'g': 'gast_eller_forbipasserande', 'c': 'kommentar'}
LAST = {'p': 'produkten', 'm': 'manniskan', 'i': 'iden', 'e': 'erbjudandet'}
FALT = ['grepp', 'motpart', 'last']


def main():
    ids = json.loads((UT / 'lasning2_ids.json').read_text())
    L = {}
    for n in (1, 2):
        for rad in (HERE / f'lasning2_fable_{n}.txt').read_text().split():
            i, kod = rad.split(':')
            g, m, l = kod.split(',')
            L[ids[int(i)]] = {'grepp': GREPP[g], 'motpart': MOTPART[m], 'last': LAST[l]}
    assert len(L) == len(ids), (len(L), len(ids))

    t = np.load(UT / 'tema.npz')
    tid = [str(x) for x in t['ids']]
    V = t['V'][[tid.index(i) for i in ids]]
    S = V @ V.T
    par = [(a, b) for a in range(len(ids)) for b in range(a) if S[a, b] >= TVILLING]
    stab = {}
    for f in FALT:
        c = Counter(x[f] for x in L.values())
        slump = sum((n / len(ids)) ** 2 for n in c.values())
        po = float(np.mean([L[ids[a]][f] == L[ids[b]][f] for a, b in par]))
        stab[f] = {'lika': round(po, 3), 'slump': round(slump, 3), 'kappa': round((po - slump) / (1 - slump), 3)}
    rapport = {'antal': len(L), 'fordelning': {f: dict(Counter(x[f] for x in L.values()).most_common()) for f in FALT},
               'tvillingar': {'troskel': TVILLING, 'par': len(par),
                              'olika_konton': sum(ids[a].rsplit('-', 1)[0] != ids[b].rsplit('-', 1)[0] for a, b in par),
                              'stabilitet': stab}}
    (UT / 'lasning2_prov.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')

    alla = json.loads((UT / 'lasning.json').read_text(encoding='utf-8'))
    for i, x in L.items():
        alla.setdefault(i, {}).update(x)
    (UT / 'lasning.json').write_text(json.dumps(alla, ensure_ascii=False, indent=0), encoding='utf-8')
    print(json.dumps(rapport, ensure_ascii=False))


if __name__ == '__main__':
    main()
