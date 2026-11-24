# -*- coding: utf-8 -*-
"""Tagningar: hårda klipp och tagningslängder. Körs i scen/.venv (scenedetect, cv2).

Två detektorer: PySceneDetect AdaptiveDetector (rullande medel, tål kamerarörelse) och
ContentDetector. Ett klipp räknas om AdaptiveDetector ser det. ContentDetector
sparas bredvid som andra läsare, för att se var de är oense (diagnos, inte krav).

Per tagning sparas också en nyckelruta (mitten) och ett enkelt rörelsemått
(medelabsolut skillnad mellan rutor efter global kompensation saknas: ren rutdiff,
så kamerarörelse och motivrörelse blandas; märkt därefter).
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from .gemensamt import LAGER, probe, rel, skriv

MIN_TAGNING_S = 0.3


def _detektera(video, detektor):
    from scenedetect import open_video, SceneManager
    v = open_video(str(video))
    sm = SceneManager()
    sm.auto_downscale = True
    sm.add_detector(detektor)
    sm.detect_scenes(v, show_progress=False)
    return [(a.seconds, b.seconds) for a, b in sm.get_scene_list(start_in_scene=True)]


def tagningar(video, ut_mapp):
    import tempfile
    from scenedetect.detectors import AdaptiveDetector, ContentDetector
    from .gemensamt import ff
    m = probe(video)
    fps = m["fps"] or 30
    min_rutor = max(1, int(round(MIN_TAGNING_S * fps)))
    with tempfile.TemporaryDirectory() as td:
        # Detektorerna körs på en nedskalad kopia (180 px bred, samma rutor): samma gränser, snabbare avkodning.
        liten = Path(td) / "liten.mp4"
        ff("-i", video, "-an", "-vf", "scale=180:-2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", liten)
        a = _detektera(liten, AdaptiveDetector(min_scene_len=min_rutor))
        c = _detektera(liten, ContentDetector(min_scene_len=min_rutor))
    if not a:
        a = [(0.0, m["langd"])]
    gr_a = [s for s, _ in a[1:]]
    gr_c = [s for s, _ in c[1:]]
    oense = [round(t, 3) for t in gr_c if not any(abs(t - u) < 0.25 for u in gr_a)]

    from .gemensamt import las_rutor
    rut_mapp = Path(ut_mapp) / "rutor"
    rut_mapp.mkdir(parents=True, exist_ok=True)
    spann = [(s, min(e, m["langd"])) for s, e in a]
    prov = [list(np.linspace(s + 0.05, max(s + 0.06, e - 0.1), 9)) + [(s + e) / 2] for s, e in spann]
    alla = las_rutor(video, [t for p in prov for t in p])
    ut = []
    for i, (s, e) in enumerate(spann, 1):
        rutor = alla[10 * (i - 1):10 * i]
        # Rörelse: rutdiff mellan 9 jämnt spridda rutor inom tagningen (72x128 gråskala).
        diffs, forra = [], None
        for f in rutor[:9]:
            if f is None:
                continue
            g = cv2.cvtColor(cv2.resize(f, (72, 128)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            if forra is not None:
                diffs.append(float(np.mean(np.abs(g - forra))))
            forra = g
        f = rutor[9]
        ruta = None
        if f is not None:
            h, w = f.shape[:2]
            ruta = rut_mapp / f"t{i}.jpg"
            cv2.imwrite(str(ruta), cv2.resize(f, (270, int(270 * h / w))), [cv2.IMWRITE_JPEG_QUALITY, 82])
        rorelse = float(np.median(diffs)) if diffs else None
        ut.append(dict(id=f"t{i}", fran=round(s, 3), till=round(e, 3), langd=round(e - s, 3),
                       rutdiff=None if rorelse is None else round(rorelse, 2),
                       still=None if rorelse is None else bool(rorelse < 6.0),
                       nyckelruta=rel(ruta) if ruta else None))
    langder = [x["langd"] for x in ut]
    sammanfattning = dict(
        antal=len(ut), median_langd=round(float(np.median(langder)), 3),
        klipp_per_10s=round(10 * (len(ut) - 1) / max(m["langd"], 1e-6), 2),
        andra_lasaren_content=len(c), oense_granser=oense,
        regel="AdaptiveDetector (PySceneDetect 0.7) bär gränserna; ContentDetector är andra läsare. "
              "still = median rutdiff < 6 (av 255) på 72x128 gråskala; kamera och motiv blandas.")
    return ut, sammanfattning


if __name__ == "__main__":
    v = Path(sys.argv[1])
    ut, s = tagningar(v, LAGER / v.stem)
    print(s)
    for x in ut:
        print(x)
