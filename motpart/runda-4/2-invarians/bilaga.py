"""Adapterbilagor (nya loggar, inte befintliga extraktorfält): E28:s scen-/tystnadslogg och E30:s faktiska VAD-intervall.
Samma ffmpeg-kommandorad som e28-tek.mjs och samma avkodning/anrop som e30_tal.py; extraktorerna ändras inte. Konsistens mot extraktorernas egna fält kontrolleras av anroparen.
"""
import re, subprocess, shutil, json
import numpy as np

FF = shutil.which("ffmpeg") or "ffmpeg"


def e28_logg(f):
    argv = [FF, "-hide_banner", "-nostats", "-i", str(f), "-vf", "select='gte(scene,0)',metadata=print", "-af", "silencedetect=n=-35dB:d=0.3,ebur128=framelog=quiet", "-f", "null", "-"]
    log = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    t = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", log)][1:]
    sc = [float(m) for m in re.findall(r"lavfi\.scene_score=([0-9.]+)", log)][1:]
    tyst = [[float(a), float(b)] for a, b in re.findall(r"silence_start: ([0-9.]+)[\s\S]*?silence_end: ([0-9.]+)", log)]
    m = re.search(r"Duration: (\d+):(\d+):([0-9.]+)", log)
    dur = sum(float(v) * k for v, k in zip(m.groups(), (3600, 60, 1))) if m else None
    return {"argv": argv, "dur": dur, "scen": [[a, b] for a, b in zip(t, sc)], "byten_t": [a for a, b in zip(t, sc) if b > 0.3], "tystnad": tyst}


def e30_vad(f):
    import torch
    from silero_vad import load_silero_vad, get_speech_timestamps
    torch.set_num_threads(2)
    raw = subprocess.run([FF, "-v", "quiet", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, timeout=120).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    dur = len(x) / 16000
    if dur < 0.5:
        return {"dur": dur, "vad": []}
    seg = get_speech_timestamps(torch.from_numpy(x), load_silero_vad(onnx=True), sampling_rate=16000, return_seconds=True, min_silence_duration_ms=300)
    return {"dur": dur, "vad": [[s["start"], s["end"]] for s in seg]}
