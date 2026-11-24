"""FORSKNING: urval bland rörelsekandidater. Spärren först (sparr.py), sedan rangordning av de godkända. Ingen språkmodell.

  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/kimodo/urval.py <namn...> [--vridning] [--leder hand_V,hand_H,huvud_yaw] [--ut fil.json]
  <namn>: 'trofe2' -> mm/ut/mening_<namn>/sekvens.npz, eller en .npz-sökväg. 'alla' = varje mm/ut/mening_*. 'original' = kontroll.

Tydlighet (a): hur mycket kandidaten skiljer sig från originalet i de mått meningen rör, medelvärde av |kandidat - original|
över rutorna, delat med en skala (SKALA) så att olika enheter väger lika. Mjukhet (b): originalets ryck / kandidatens ryck
(95-percentil, bäcken, händer, huvud), medel, kapat vid 2. Poäng = tydlighet + VIKT_MJUK * mjukhet. Underkända rangordnas inte.
"""
import json, sys, time
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; sys.path.insert(0, str(HIT)); import sparr as S  # noqa: E402

SKALA = dict(hand_V=10.0, hand_H=10.0, huvud_yaw=15.0, huvud=10.0, bal=10.0)   # cm resp. grader som räknas som 1 tydlig enhet
VIKT_MJUK = 0.5
LEDER_STD = ('hand_V', 'hand_H', 'huvud_yaw')   # "låter köttbiten sjunka medan han tittar bort åt sidan"
RYCK = ('root', 'l_wrist', 'r_wrist', 'c_head')


def bedom(namn, k, o, leder, vridning):
    T = min(len(k), len(o)); k, o = k[:T], o[:T]
    sp = S.sparr(k, o, vridning=vridning); rk, ro = S.matt(k, golvniva=S.golv(o))['ruta'], S.matt(o)['ruta']
    diff = {l: float(np.mean(np.abs(rk[f'hand_{l[-1]}_cm' if l.startswith('hand_') else l] - ro[f'hand_{l[-1]}_cm' if l.startswith('hand_') else l]))) for l in leder}
    tyd = float(np.mean([diff[l] / SKALA.get(l, 1.0) for l in leder]))
    mjuk = float(np.mean([min(2.0, sp['original'][f'ryck95_{n}'] / max(sp['matt'][f'ryck95_{n}'], 1e-6)) for n in RYCK]))
    return dict(namn=namn, rutor=T, godkand=sp['godkand'], skal=sp['skal'], tydlighet=round(tyd, 3), mjukhet=round(mjuk, 3),
                poang=round(tyd + VIKT_MJUK * mjuk, 3), skillnad={l: round(v, 1) for l, v in diff.items()}, matt=sp['matt'])


def main(argv):
    leder, vridning, ut, namn = list(LEDER_STD), False, None, []
    it = iter(argv)
    for a in it:
        if a == '--vridning': vridning = True
        elif a == '--leder': leder = next(it).split(',')
        elif a == '--ut': ut = Path(next(it))
        else: namn.append(a)
    if 'alla' in namn:
        namn.remove('alla'); namn += sorted(p.name[len('mening_'):] for p in (S.MM / 'ut').glob('mening_*') if (p / 'sekvens.npz').exists())
    t, o = S.las_original(); rader = []
    for n in namn:
        try: k = o if n == 'original' else S.las_kandidat(n, t)
        except Exception as e: print(f'{n}: kunde inte läsas ({e})'); continue
        rader.append(bedom(n, k, o, leder, vridning))
    rader.sort(key=lambda r: (not r['godkand'], -r['poang']))
    m = lambda r: r['matt']
    print(f"leder: {', '.join(leder)}   vridning begärd: {vridning}   original: knä {S.matt(o)['median']['kna_V']:.0f}°, bål {S.matt(o)['median']['bal']:.0f}°, huvud {S.matt(o)['median']['huvud']:.0f}°")
    print(f"{'#':>2} {'kandidat':<28}{'spärr':<7}{'poäng':>6}{'tyd':>6}{'mjuk':>6}  " + ''.join(f'{l:>10}' for l in leder) + f"{'knä V/H':>10}{'bål':>5}{'huvud':>6}  skäl")
    for i, r in enumerate(rader, 1):
        print(f"{i if r['godkand'] else '-':>2} {r['namn']:<28}{'ok' if r['godkand'] else 'STOPP':<7}{r['poang']:>6.2f}{r['tydlighet']:>6.2f}{r['mjukhet']:>6.2f}  "
              + ''.join(f"{r['skillnad'][l]:>10.1f}" for l in leder) + f"{m(r)['kna_V']:>5.0f}/{m(r)['kna_H']:<4.0f}{m(r)['bal']:>5.0f}{m(r)['huvud']:>6.0f}  "
              + '; '.join(s.split(' (')[0] for s in r['skal']))
    ut = ut or HIT / 'urval' / f"urval_{time.strftime('%Y%m%d_%H%M%S')}.json"; ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(json.dumps(dict(leder=leder, vridning=vridning, grans=S.GRANS, skala=SKALA, vikt_mjuk=VIKT_MJUK, rader=rader,
                                  not_='Diagnosgränser, inte ägarens krav.'), ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'sparat: {ut}')


if __name__ == '__main__':
    main(sys.argv[1:])
