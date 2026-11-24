# E30: tal mätt lokalt med Silero VAD, utan språkmodell. Förregistrering: data/format/e30/forregistrering.json
#   ../scen/.venv/Scripts/python.exe -u format/e30_tal.py
# Resultat: data/format/e30/tal.jsonl (återupptas)
import json, os, shutil, subprocess
from pathlib import Path
import numpy as np, torch
from silero_vad import load_silero_vad, get_speech_timestamps

torch.set_num_threads(2)
ROT = Path(__file__).resolve().parents[2] / "data" / "format"; E = ROT / "e30"; E.mkdir(exist_ok=True)
UT = E / "tal.jsonl"; DIR = Path.home() / "Downloads" / "letrend-e13"
FF = shutil.which("ffmpeg") or "ffmpeg"
klar = {json.loads(l)["id"] for l in UT.read_text(encoding="utf-8").splitlines() if l.strip()} if UT.exists() else set()
ids = sorted(f.stem for f in DIR.glob("*.mp4") if f.stem.rsplit("-", 1)[-1].isdigit() and f.stem not in klar)
mod = load_silero_vad(onnx=True)
print(f"{len(ids)} klipp att mäta", flush=True)
with UT.open("a", encoding="utf-8") as ut:
    for n, i in enumerate(ids):
        try:
            raw = subprocess.run([FF, "-v", "quiet", "-i", str(DIR / f"{i}.mp4"), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, timeout=120).stdout
            x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; dur = len(x) / 16000
            if dur < 0.5: ut.write(json.dumps({"id": i, "langd": dur, "tal_andel": 0, "tal_segment": 0, "tal_per_s": 0, "forsta_tal": None}) + "\n"); continue
            seg = get_speech_timestamps(torch.from_numpy(x), mod, sampling_rate=16000, return_seconds=True, min_silence_duration_ms=300)
            tal = sum(s["end"] - s["start"] for s in seg)
            ut.write(json.dumps({"id": i, "langd": round(dur, 2), "tal_andel": round(tal / dur, 3), "tal_segment": len(seg), "tal_per_s": round(len(seg) / dur, 3), "forsta_tal": round(seg[0]["start"], 2) if seg else None}) + "\n")
        except Exception as e:
            print("FEL", i, str(e)[:100], flush=True)
        if n % 200 == 0: ut.flush(); print(f"  {n}", flush=True)
print("klart", flush=True)
