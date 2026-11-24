"""Steg 2, uppgift 1: verifiera sha256 mot manifest.jsonl för alla 200 klipp, arkivera ffprobe för de 156 som används (12 test + 144 R)."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROT = Path(__file__).resolve().parents[3]
SRC = Path(r"C:\Users\praiseworthy\Downloads\letrend-r4")
man = [json.loads(l) for l in (ROT/"motpart/runda-4/1-datagrund/manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
urv = json.loads((Path(__file__).parent/"urval_las.json").read_text(encoding="utf-8"))
bruk = {x["id"] for x in urv["step2"]} | set(urv["reference_ids"])
out, fel = {}, []
for m in man:
    f = SRC/f'{m["id"]}.mp4'
    if not f.exists(): fel.append((m["id"], "saknas")); continue
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    if h != m["sha256"]: fel.append((m["id"], "sha256 avviker", h)); continue
    if m["id"] in bruk:
        p = subprocess.run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(f)],capture_output=True,text=True,encoding="utf-8").stdout
        out[m["id"]] = json.loads(p)
print("klipp i manifest:", len(man), "fel:", fel)
print("arkiverade ffprobe:", len(out), "av förväntade", len(bruk), "saknade", bruk-set(out))
(Path(__file__).parent/"ffprobe_kallor.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
