"""Kontaktblad per tagning: några bildrutor med varje uppmätt spår inritat vid sin uppmätta box och märkt "S3:1".

Märkningen är det som binder modellens svar till mätningen: "spår S3:1" betyder nyckel "1" i S3/personer.json.
Läser tagningsklippen (ingest/ut/<klipp>/klipp/S<n>.mp4) och personer.json. Skriver bara det som anropas med ut=.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/kontaktblad.py <klipp> [--ut <mapp>]
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import klipp_vagar, tagningar, sparlista, tc  # noqa: E402

# Färgerna betyder inget mellan tagningar: de delas ut i ordning per tagning.
PALETT = [(40, 40, 230), (230, 120, 20), (30, 170, 30), (200, 30, 200), (20, 190, 220), (120, 120, 120)]   # BGR
CELL_H = 512
KOLUMNER = 3
MAX_RUTOR = 6


def valj_rutor(N, n=MAX_RUTOR):
    if N <= n: return list(range(N))
    return sorted({round(i * (N - 1) / (n - 1)) for i in range(n)})


def text(img, s, org, skala=0.55, farg=(255, 255, 255), bakgrund=(0, 0, 0), tjocklek=1):
    (w, h), bas = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, skala, tjocklek)
    x, y = org
    cv2.rectangle(img, (x, y - h - 3), (x + w + 4, y + bas + 1), bakgrund, -1)
    cv2.putText(img, s, (x + 2, y), cv2.FONT_HERSHEY_SIMPLEX, skala, farg, tjocklek, cv2.LINE_AA)


def blad(shot, spar):
    """Ett kontaktblad (BGR-bild) för en tagning. Returnerar (bild, vilka lokala rutor som valdes)."""
    cap = cv2.VideoCapture(str(shot['klippfil']))
    if not cap.isOpened(): raise SystemExit(f'Kan inte öppna {shot["klippfil"]}')
    rutor = valj_rutor(shot['N']); s = CELL_H / shot['hojd']; cw = round(shot['bredd'] * s)
    ordning = {sid: i for i, sid in enumerate(sorted(spar, key=lambda x: (len(x), x)))}
    celler = []
    for f in rutor:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, img = cap.read()
        if not ok: raise SystemExit(f'{shot["id"]}: kan inte avkoda ruta {f}')
        img = cv2.resize(img, (cw, CELL_H), interpolation=cv2.INTER_AREA)
        for sid, sp in spar.items():
            b = sp['boxar'].get(f)
            if b is None: continue
            x0, y0, x1, y1 = [round(v * s) for v in b]; farg = PALETT[ordning[sid] % len(PALETT)]
            cv2.rectangle(img, (x0, y0), (x1 - 1, y1 - 1), farg, 3)
            text(img, f'{shot["id"]}:{sid}', (max(2, x0 + 3), min(CELL_H - 8, max(y0 + 18, 20))), 0.6, (255, 255, 255), farg, 2)
        glob = shot['start'] + f
        text(img, f'{shot["id"]} ruta {glob} ({tc(glob, shot["fps"])})', (3, 16), 0.5, (0, 255, 255), (0, 0, 0), 1)
        celler.append(img)
    cap.release()
    while len(celler) % KOLUMNER: celler.append(np.zeros_like(celler[0]))
    rader = [np.hstack(celler[i:i + KOLUMNER]) for i in range(0, len(celler), KOLUMNER)]
    return np.vstack(rader), rutor


def spartabell(shot, spar):
    """Textrader som beskriver spåren i en tagning (uppmätta siffror; engelska eftersom de går in i modellens prompt)."""
    rader = []
    for sid, sp in spar.items():
        if sp['forsta'] is None:
            rader.append(f'  {shot["id"]}:{sid}  no boxes'); continue
        rader.append(f'  {shot["id"]}:{sid}  box present in {sp["rutor_med_box"]} of {shot["N"]} frames (source frames {shot["start"] + sp["forsta"]}..{shot["start"] + sp["sista"]}), '
                     f'median box height {sp["hojd_andel"]:.0%} and width {sp["bredd_andel"]:.0%} of the frame, '
                     f'median centre ({sp["mitt_x"]:.2f}, {sp["mitt_y"]:.2f}) of the frame (x right, y down), touching the frame edge in {sp["kantandel"]:.0%} of its frames')
    return rader


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('klipp'); a.add_argument('--ut')
    x = a.parse_args()
    v = klipp_vagar(x.klipp); ut = Path(x.ut) if x.ut else v['ut'] / 'blad'
    ut.mkdir(parents=True, exist_ok=True)
    for sh in tagningar(v['ingest']):
        sp = sparlista(sh); bild, rutor = blad(sh, sp)
        cv2.imwrite(str(ut / f'{sh["id"]}.jpg'), bild, [cv2.IMWRITE_JPEG_QUALITY, 82])
        print(sh['id'], 'rutor', rutor, 'spår', list(sp), bild.shape)
        for r in spartabell(sh, sp): print(r)


if __name__ == '__main__':
    main()
