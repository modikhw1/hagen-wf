"""Automatisk klippdetektering (tagningsgränser) för ett källklipp.

Mått: medel av absolut HSV-skillnad mellan på varandra följande bildrutor (samma mått som PySceneDetects ContentDetector;
PySceneDetect finns i scen/.venv men en enda fast tröskel räcker inte: snabb rörelse i skisserna ger 20-40 i hela segment,
medan en riktig hård klippning ger 45-75 mot en grannskapsnivå på 2-15). Därför två villkor, båda måste gälla:
  1. poang >= TROSKEL (absolut, standard 20) och lokalt maximum,
  2. poang >= KVOT * median(poäng i rutorna +-8 runt, utan själva rutan)  (standard 2,5): ett hopp mot sitt grannskap, inte ihållande rörelse,
  3. kontroll <= 1,5 * poang: skillnaden ruta i-2 mot i+1 är lika stor som hoppet, dvs bildbytet består (en blixt eller en enstaka
     ruta ger liten 'kontroll' och förkastas; gränsen listas då under 'forkastade').
Gränsen är den FÖRSTA bildrutan i den nya tagningen. Klippet N-1 (sista rutan) och ruta 1 (andra rutan) flaggas 'kant': en tagning på
en ruta är nästan alltid en övertoning eller ett slutkort, inte en tagning.

Kör:  scen/.venv/Scripts/python.exe scen/3d/ingest/flera/klippgrans.py <klipp.mp4> [--troskel 20] [--kvot 3] [--facit 73,114,...]
Skriver JSON på stdout.
"""
import sys, json, argparse
import numpy as np, cv2

TROSKEL = 20.0; KVOT = 2.5; KONTROLL = 1.5

def poang_per_ruta(klipp):
    cap = cv2.VideoCapture(str(klipp)); prev = None; sc = [0.0]; sm = []
    while True:
        ok, f = cap.read()
        if not ok: break
        h = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.int16); sm.append(cv2.resize(h.astype(np.uint8), (96, 160), interpolation=cv2.INTER_AREA).astype(np.int16))
        if prev is not None: sc.append(float(np.abs(h - prev).mean()))
        prev = h
    return np.array(sc), sm

def hitta(klipp, troskel=TROSKEL, kvot=KVOT):
    sc, sm = poang_per_ruta(klipp); N = len(sc); ok_, bort = [], []
    for i in range(1, N):
        if sc[i] < troskel * .5: continue
        if sc[i] < sc[i - 1] or (i + 1 < N and sc[i] < sc[i + 1]): continue
        gr = np.concatenate([sc[max(1, i - 8):i], sc[i + 1:i + 9]]); med = float(np.median(gr)) if len(gr) else 0.0
        kontroll = float(np.abs(sm[max(0, i - 2)] - sm[min(N - 1, i + 1)]).mean())
        d = dict(ruta=i, poang=round(float(sc[i]), 1), grann_median=round(med, 1), kvot=round(float(sc[i] / (med + 1e-3)), 1), kontroll=round(kontroll, 1))
        if i <= 1 or i >= N - 1: d['kant'] = True
        (ok_ if sc[i] >= troskel and sc[i] >= kvot * med and kontroll <= KONTROLL * sc[i] and sc[i] >= 0.5 * kontroll else bort).append(d)
    return N, ok_, [b for b in bort if b['poang'] >= troskel], sc

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('klipp'); p.add_argument('--troskel', type=float, default=TROSKEL); p.add_argument('--kvot', type=float, default=KVOT); p.add_argument('--facit', default=None)
    x = p.parse_args(); N, g, bort, sc = hitta(x.klipp, x.troskel, x.kvot)
    r = dict(N=N, troskel=x.troskel, kvot=x.kvot, granser=g, forkastade=bort, max_poang_utan_gräns=round(float(max([s for i, s in enumerate(sc) if i not in {d['ruta'] for d in g}] or [0])), 1))
    if x.facit:
        f = [int(v) for v in x.facit.split(',')]; fu = [d['ruta'] for d in g]
        r['traff'] = [v for v in f if v in fu]; r['miss'] = [v for v in f if v not in fu]; r['falska'] = [v for v in fu if v not in f]
    print(json.dumps(r, ensure_ascii=False))
