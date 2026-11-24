# E35: talarbyten per klipp (Silero VAD + WavLM-SV röstvektorer), lokalt. data/format/e35/forregistrering.json
#   HF_HUB_OFFLINE=1 ../scen/.venv/Scripts/python.exe -u format/e35_talare.py   (återupptas)
# Sparar per klipp segmenttider och likheter mellan segmenten, så att tröskeln kan varieras i analysen.
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np, torch
from silero_vad import load_silero_vad, get_speech_timestamps
from transformers import AutoFeatureExtractor, WavLMForXVector

torch.set_num_threads(3)
E = Path(__file__).resolve().parents[2] / "data" / "format" / "e35"; E.mkdir(exist_ok=True); UT = E / "talare.jsonl"
FF = shutil.which("ffmpeg") or "ffmpeg"
klar = {json.loads(l)["id"] for l in UT.read_text(encoding="utf-8").splitlines() if l.strip()} if UT.exists() else set()
filer = {}
for d in [Path.home() / "Downloads" / "letrend-e34", Path.home() / "Downloads" / "letrend-e13"]:
    for f in d.iterdir():
        if f.suffix in (".mp4", ".mp3", ".m4a", ".webm") and f.stem.rsplit("-", 1)[-1].isdigit(): filer.setdefault(f.stem, f)
ids = sorted(i for i in filer if i not in klar)
vad = load_silero_vad(onnx=True)
fe = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv"); mod = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").eval()
print(f"{len(ids)} klipp att mäta", flush=True)
with UT.open("a", encoding="utf-8") as ut, torch.no_grad():
    for n, i in enumerate(ids):
        try:
            raw = subprocess.run([FF, "-v", "quiet", "-i", str(filer[i]), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, timeout=120).stdout
            x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            seg = get_speech_timestamps(torch.from_numpy(x), vad, sampling_rate=16000, return_seconds=True, min_silence_duration_ms=300) if len(x) > 8000 else []
            seg = [s for s in seg if s["end"] - s["start"] >= 0.6][:30]
            rec = {"id": i, "langd": round(len(x) / 16000, 2), "seg": [[round(s["start"], 2), round(s["end"], 2)] for s in seg], "sim": []}
            if len(seg) >= 2:
                win, ag = [], []
                for k, s in enumerate(seg):
                    a, b = int(s["start"] * 16000), int(s["end"] * 16000); L = b - a; w = 24000
                    st = [a] if L <= w * 1.5 else [a, a + (L - w) // 2]
                    for s0 in st: win.append(x[s0:min(s0 + w, b)]); ag.append(k)
                em = []
                for j in range(0, len(win), 16):
                    inp = fe(win[j:j + 16], sampling_rate=16000, return_tensors="pt", padding=True); em.append(mod(**inp).embeddings)
                em = torch.nn.functional.normalize(torch.cat(em), dim=-1).numpy(); ag = np.array(ag)
                S = np.stack([em[ag == k].mean(0) for k in range(len(seg))]); S /= np.linalg.norm(S, axis=1, keepdims=True)
                rec["sim"] = np.round(S @ S.T, 3).tolist()
            ut.write(json.dumps(rec) + "\n")
        except Exception as e:
            print("FEL", i, str(e)[:120], flush=True)
        if n % 50 == 0: ut.flush(); print(f"  {n}", flush=True)
print("klart", flush=True)
