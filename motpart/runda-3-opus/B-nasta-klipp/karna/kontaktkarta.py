"""Kontaktkarta för ägarens dom: tre rutor per tagning (10 %, 50 %, 90 %), originalet bredvid förvärldens rendering.

Grått i renderingen = kroppsdel utan bildstöd (`antagen`). Text i rutan: tagning, ruta, personernas tillstånd.
"""
from __future__ import annotations

import json
import pathlib

import cv2
import numpy as np

TW, TH = 216, 384


def _ruta(mp4, ix, W, H):
    cap = cv2.VideoCapture(str(mp4))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(ix))
    ok, img = cap.read()
    cap.release()
    if not ok or img is None:
        return np.zeros((TH, TW, 3), np.uint8)
    return cv2.resize(img, (TW, TH))


def _text(im, s, y, farg=(255, 255, 255)):
    cv2.putText(im, s, (5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 3)
    cv2.putText(im, s, (5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, farg, 1)


def bygg(paket_fil: pathlib.Path, ingest: pathlib.Path, lokal: pathlib.Path, ut: pathlib.Path, max_rader: int = 6) -> list[pathlib.Path]:
    P = json.loads(paket_fil.read_text(encoding="utf-8"))
    W, H = P["bild"]["bredd"], P["bild"]["hojd"]
    rader = []
    for t in P["tagningar"]:
        a0, b0 = t["ut"]
        T = b0 - a0
        celler = []
        for u in sorted({a0 + int(round(.1 * (T - 1))), (a0 + b0) // 2, a0 + int(round(.9 * (T - 1)))}):
            o = _ruta(ingest / "klipp" / f"{t['id'].upper()}.mp4", u - a0, W, H)
            rf = lokal / f"kontroll_{t['id']}_{u:04d}.png"
            r = cv2.resize(cv2.imread(str(rf)), (TW, TH)) if rf.exists() else np.zeros((TH, TW, 3), np.uint8)
            _text(o, f"{t['id'].upper()} original r{u - a0}", 14)
            _text(r, f"{t['id'].upper()} forvarld r{u - a0}", 14, (120, 220, 255))
            till = ", ".join(f"{p['id']}:{p.get('tillstand', '')}" for p in t["personer"])
            _text(r, till[:34], 30, (200, 255, 200))
            kam = t["kamera"]
            _text(r, f"h={kam['hojd']['v']:.2f} {kam['hojd']['status']} f={kam['fokal_px']:.0f}", TH - 22)
            _text(r, f"{'stilla' if kam['statisk'] else 'rorlig'} lod {kam['lodlinje']['pitch']:.0f}/{kam['lodlinje']['roll']:.0f}", TH - 8)
            celler.append(np.hstack([o, r, np.full((TH, 6, 3), 40, np.uint8)]))
        while len(celler) < 3:
            celler.append(np.zeros_like(celler[0]))
        rader.append(np.hstack(celler))
    filer = []
    for i in range(0, len(rader), max_rader):
        bild = np.vstack([np.vstack([r, np.full((6, r.shape[1], 3), 40, np.uint8)]) for r in rader[i:i + max_rader]])
        f = ut if len(rader) <= max_rader else ut.with_name(f"{ut.stem}_{i // max_rader + 1}{ut.suffix}")
        cv2.imwrite(str(f), bild)
        filer.append(f)
    return filer
