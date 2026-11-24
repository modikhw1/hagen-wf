# E15: bäddar in klipptexterna lokalt (multilingual-e5-small, CPU). Kör med scen/.venv:
#   ../scen/.venv/Scripts/python.exe format/e15_badda.py [falt ...]
# Standardfält: "innehall" (sållningens mening) och "text" (mening + bildtext).
# Resultat: data/format/e15/vek-<falt>.npy (float32, normerade) i samma ordning som klipp.jsonl.
import json, sys, time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

E = Path(__file__).resolve().parents[2] / "data" / "format" / "e15"
kalla = sys.argv[1] if len(sys.argv) > 1 else "klipp.jsonl"
rader = [json.loads(l) for l in (E / kalla).read_text(encoding="utf-8").splitlines() if l.strip()]
falt = sys.argv[2:] or ["innehall", "text"]
tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
modell = AutoModel.from_pretrained("intfloat/multilingual-e5-small").eval()
torch.set_num_threads(8)


def badda(texter, sats=64):
    ut = []
    for i in range(0, len(texter), sats):
        b = tok(["query: " + t for t in texter[i:i + sats]], padding=True, truncation=True, max_length=192, return_tensors="pt")
        with torch.no_grad():
            h = modell(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float()
        v = (h * m).sum(1) / m.sum(1)
        ut.append(torch.nn.functional.normalize(v, dim=-1).numpy().astype("float32"))
        if (i // sats) % 20 == 0:
            print(f"  {i}/{len(texter)}", flush=True)
    return np.concatenate(ut)


for f in falt:
    t0 = time.time()
    if f == "text":
        texter = [(r.get("innehall", "") + " " + r.get("bildtext", "")).strip() or "tom" for r in rader]
    else:
        texter = [str(r.get(f) or "tom") for r in rader]
    v = badda(texter)
    np.save(E / f"vek-{Path(kalla).stem}-{f}.npy", v)
    print(f, v.shape, f"{time.time() - t0:.0f} s", flush=True)
