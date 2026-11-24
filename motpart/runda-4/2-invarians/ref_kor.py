"""Steg 2, referensmätning: gör C för varje klipp i R (144 st), mät med E28/E30/E37, spara råvärden, radera C. Inga testklipp berörs.
Återupptar: hoppar över id som redan finns i ref_mat.jsonl. Avbryter vid <5 GB ledigt."""
import json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pathlib import Path
from recept import *
import mat_adapter as M
HER = Path(__file__).parent
SRC = Path(r"C:\Users\praiseworthy\Downloads\letrend-r4")
UT = HER / "ref_mat.jsonl"
man = {json.loads(l)["id"]: json.loads(l) for l in (HER.parent/"1-datagrund/manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
refs = json.loads((HER/"urval_las.json").read_text(encoding="utf-8"))["reference_ids"]
klar = {json.loads(l)["id"] for l in UT.read_text(encoding="utf-8").splitlines() if l.strip()} if UT.exists() else set()
todo = [i for i in refs if i not in klar]
ARB = M.W / "arb"; ARB.mkdir(parents=True, exist_ok=True)
batcher, cur, d = [], [], 0.0
for i in todo:
    cur.append(i); d += man[i]["langd_s"]
    if d >= 150: batcher.append(cur); cur, d = [], 0.0
if cur: batcher.append(cur)
print(f"{len(todo)} klipp, {len(batcher)} batchar", flush=True)
label = "ref"
M.bygg_trad(label)
for b, ids in enumerate(batcher):
    free = shutil.disk_usage(str(M.W)).free
    if free < 5e9: print("AVBRYT: ledigt", free, flush=True); sys.exit(3)
    filer, kmd = {}, {}
    for i in ids:
        C = ARB / f"{M.stem(i,'C')}.mkv"
        argv = c_cmd(SRC / f"{i}.mp4", C); rc, err = kor(argv)
        kmd[i] = {"argv": argv, "rc": rc, "stderr": err[-500:]}
        if rc == 0: filer[M.stem(i, "C")] = C
        else: print("C-FEL", i, err[-300:], flush=True)
    logg = []
    ut, tider = M.kor_batch(label, filer, logg)
    with UT.open("a", encoding="utf-8") as f:
        for i in ids:
            s = M.stem(i, "C")
            row = {"id": i, "konto": i.rsplit("-", 1)[0], "variant": "C", "c_rc": kmd[i]["rc"], "e28": ut.get(s, {}).get("e28"), "e30": ut.get(s, {}).get("e30"), "e37": ut.get(s, {}).get("e37"),
                   "c_storlek": filer[s].stat().st_size if s in filer else None}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    for p in filer.values(): p.unlink()
    print(f"batch {b+1}/{len(batcher)} klar {tider} ledigt {free/1e9:.1f} GB", flush=True)
print("KLART", flush=True)
