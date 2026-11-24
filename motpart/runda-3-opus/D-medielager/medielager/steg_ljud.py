# -*- coding: utf-8 -*-
"""Tal och musik som tidslinje. Körs i scen/.venv (faster-whisper med KB-whisper small, silero-vad).

- Tal: KB-whisper small (lokalt, från scen/3d/cache/whisper, läses bara) på mixen, ordtider på.
  Andra läsare: silero-vad på mixen. Var de skiljer sig sparas.
- Musik: ur separationens kurvor (steg_separation). Ett 0,5 s-fönster räknas som musik när
  trummor+bas ligger över MUSIK_DB relativt mixens topp. Brus i en lokal ger lite bas och slagverk.
  Musik i klippet = minst 20 % av fönstren. Trösklar är mina (diagnos).
- Sångrisk: röststammen är aktiv i fönster där whisper inte hittar tal, samtidigt som musik spelar.
  Då kan "ta bort musiken" lämna sång kvar i talstammen.
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

from .gemensamt import WHISPER_SMALL, ljud_wav

MUSIK_DB = -35.0
ROST_DB = -30.0
MUSIK_ANDEL = 0.20

_modell = None


def _whisper():
    global _modell
    if _modell is None:
        from faster_whisper import WhisperModel
        snap = next(Path(WHISPER_SMALL).iterdir())
        _modell = WhisperModel(str(snap), device="cpu", compute_type="int8")
    return _modell


def _las16k(wav):
    import wave
    with wave.open(str(wav), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    return x


def transkribera(wav):
    # Ljudet skickas som array: PyAV-versionen i scen/.venv tar inte faster-whispers filargument.
    seg, info = _whisper().transcribe(_las16k(wav), beam_size=1, word_timestamps=True, vad_filter=True,
                                      condition_on_previous_text=False)
    ut = []
    for s in seg:
        ord_ = [dict(o=w.word.strip(), fran=round(w.start, 2), till=round(w.end, 2), p=round(w.probability, 2))
                for w in (s.words or [])]
        ut.append(dict(fran=round(s.start, 2), till=round(s.end, 2), text=s.text.strip(),
                       logprob=round(s.avg_logprob, 3), ingen_tal=round(s.no_speech_prob, 3), ord=ord_))
    return ut, dict(sprak=info.language, sprak_p=round(info.language_probability, 3))


def vad(wav):
    import torch
    from silero_vad import load_silero_vad, get_speech_timestamps
    m = load_silero_vad()
    a = torch.from_numpy(_las16k(wav))
    ts = get_speech_timestamps(a, m, sampling_rate=16000, return_seconds=True)
    return [dict(fran=round(t["start"], 2), till=round(t["end"], 2)) for t in ts]


def _intervall(flaggor, fs):
    ut, start = [], None
    for i, f in enumerate(list(flaggor) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            ut.append(dict(fran=round(start * fs, 2), till=round(i * fs, 2)))
            start = None
    return ut


def tal_lasning(video, cache_fil=None):
    """Whisper + VAD på mixen. Cachas i cache_fil (återskapbar)."""
    if cache_fil and Path(cache_fil).exists():
        return json.loads(Path(cache_fil).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        wav = ljud_wav(video, Path(td) / "mix16k.wav")
        segment, sprak = transkribera(wav)
        vad_seg = vad(wav)
    tal_s = sum(s["till"] - s["fran"] for s in segment)
    tal = dict(modell="KBLab/kb-whisper-small (faster-whisper int8, beam 1, CPU)", **sprak,
               segment=segment, sekunder=round(tal_s, 2),
               vad=dict(modell="silero-vad 6.2", segment=vad_seg,
                        sekunder=round(sum(v["till"] - v["fran"] for v in vad_seg), 2)))
    if cache_fil:
        Path(cache_fil).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_fil).write_text(json.dumps(tal, ensure_ascii=False), encoding="utf-8")
    return tal


def ljud(video, sep_json, langd, cache_fil=None):
    ut = dict(tal=tal_lasning(video, cache_fil))
    segment = ut["tal"]["segment"]
    if sep_json and Path(sep_json).exists():
        sep = json.loads(Path(sep_json).read_text(encoding="utf-8"))
        k = sep["kurvor_db"]
        fs = sep["fonster_s"]
        db = np.array(k["drums_bass"])
        voc = np.array(k["vocals"])
        musik = db > MUSIK_DB
        andel = float(musik.mean()) if musik.size else 0.0
        # sångrisk: röst aktiv, musik aktiv, ingen whisper-text i fönstret
        tal_flagga = np.zeros_like(musik)
        for s in segment:
            tal_flagga[int(s["fran"] / fs):int(np.ceil(s["till"] / fs))] = True
        rost = voc > ROST_DB
        sang = rost & musik & ~tal_flagga
        ut["musik"] = dict(
            finns=bool(andel >= MUSIK_ANDEL), andel_fonster=round(andel, 3), intervall=_intervall(musik, fs),
            sang_risk=round(float(sang.sum() / max(1, (rost & musik).sum())), 3),
            regel=f"fönster {fs} s; musik när trummor+bas > {MUSIK_DB} dB rel. mixens topp; "
                  f"finns när >= {int(MUSIK_ANDEL*100)} % av fönstren",
            stammar=dict(tal=sep["tal"], musik=sep["musik"], modell=sep["modell"]))
    else:
        ut["musik"] = dict(finns=None, skal="ingen separation")
    return ut


if __name__ == "__main__":
    print(json.dumps(ljud(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, None), ensure_ascii=False)[:3000])
