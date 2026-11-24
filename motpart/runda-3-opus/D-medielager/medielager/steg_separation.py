# -*- coding: utf-8 -*-
"""Källseparation: tal (röst) och musik/ljudbädd. Körs i D-medielager/.venv (Demucs 4, htdemucs, CPU).

Demucs htdemucs ger fyra stammar: drums, bass, other, vocals. Här:
- tal.wav    = vocals (kan innehålla sång om musiken har sång; se 'sang_risk')
- musik.wav  = drums + bass + other (musik och omgivningsljud; omgivning hamnar mest i other)

Aktivitetskurvor per 0,5 s (RMS i dB relativt mixens topp) sparas för vocals, drums+bass och other.
Musik skiljs från omgivningsbrus genom att drums+bass bär energi: brus i en lokal ger lite bas och
slagverk. Tröskeln är min och är diagnos.

Ljudet läses med ffmpeg (inte torchaudio). Modellvikterna hämtas en gång till torch-cachen.
Kör: python -m medielager.steg_separation <video> <ut_mapp>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 44100
FONSTER_S = 0.5


def _las(video):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "2", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32).reshape(-1, 2).T.copy()
    return x


def _skriv(p, x):
    import soundfile as sf
    sf.write(str(p), np.clip(x.T, -1, 1), SR, format="FLAC", subtype="PCM_16")


def _db(x):
    n = int(FONSTER_S * SR)
    m = x.mean(0) if x.ndim == 2 else x
    k = len(m) // n
    if k == 0:
        return np.array([])
    r = np.sqrt((m[:k * n].reshape(k, n) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r)


def separera(video, ut):
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    ut = Path(ut)
    ut.mkdir(parents=True, exist_ok=True)
    x = _las(video)
    if x.shape[1] < SR * 0.5:
        return dict(fel="för kort ljud")
    modell = get_model("htdemucs")
    modell.eval()
    ref = x.mean(0)
    mu, sd = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        s = apply_model(modell, torch.from_numpy((x - mu) / sd)[None], device="cpu", split=True, overlap=0.25,
                        progress=False)[0].numpy() * sd + mu
    namn = modell.sources  # ['drums','bass','other','vocals']
    st = {n: s[i] for i, n in enumerate(namn)}
    tal = st["vocals"]
    musik = st["drums"] + st["bass"] + st["other"]
    _skriv(ut / "tal.flac", tal)
    _skriv(ut / "musik.flac", musik)
    topp = float(np.max(_db(x))) if x.size else 0.0
    kurvor = {k: (_db(v) - topp).round(1).tolist() for k, v in
              dict(mix=x, vocals=tal, drums_bass=st["drums"] + st["bass"], other=st["other"]).items()}
    return dict(modell="demucs 4 htdemucs (CPU)", sr=SR, fonster_s=FONSTER_S, stammar=namn,
                tal="tal.flac", musik="musik.flac", kurvor_db=kurvor)


if __name__ == "__main__":
    meta = separera(sys.argv[1], sys.argv[2])
    Path(sys.argv[2], "separation.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print("ok")
