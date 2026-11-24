"""Adapter för extraktorerna E28 (node), E30 och E37 (python). Extraktorernas kod är orörd (byte-identiska kopior, sha256 kontrolleras).
Hårdkodade sökvägar i extraktorerna lösas utan kodändring:
  - ingång: <HOME>/Downloads/letrend-e13/*.mp4  -> HOME (USERPROFILE) pekar på en scenmapp där varje mätfil ligger som hårdlänk <stem>.mp4
    (innehållet kan vara Matroska/FFV1; ffmpeg/OpenCV avgör format ur innehållet, inte ur ändelsen).
  - utgång: data/format/e28|e30|e37 relativt kopians plats -> en egen träd-mapp per körning (etikett).
  - video/analys/pipeline.mjs ersätts av en stubb som bara exporterar DATA (E28 använder bara DATA ur den).
Stem för en mätfil: <konto>~<VARIANT>-<videoid>. Ursprungs-id = konto-videoid.
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from recept import sha256

ROT = Path(__file__).resolve().parents[3]
W = Path(r"C:\Users\praiseworthy\Downloads\letrend-r4-varianter")
PY = ROT / "scen/.venv/Scripts/python.exe"
SKRIPT = {"e28": ROT/"video/format/e28-tek.mjs", "e30": ROT/"video/format/e30_tal.py", "e37": ROT/"video/format/e37_personer.py"}
VERKTYG = ROT/"video/analys/verktyg.mjs"
VIKTER = ROT/"data/format/e37/yolov8n.pt"
STUBB = "// Adapter-stubb: E28 använder endast DATA ur pipeline.mjs.\nimport path from 'node:path'\nimport { fileURLToPath } from 'node:url'\nexport const DATA = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../data')\n"

def stem(orig_id, var):
    konto, vid = orig_id.rsplit("-", 1)
    return f"{konto}~{var}-{vid}"

def unstem(s):
    kv, vid = s.rsplit("-", 1)
    konto, var = kv.rsplit("~", 1)
    return f"{konto}-{vid}", var

def bygg_trad(label):
    t = W / f"tree_{label}"
    if t.exists(): shutil.rmtree(t)
    for k, p in SKRIPT.items():
        d = t / "video/format"; d.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, d / p.name)
        assert sha256(d / p.name) == sha256(p)
    (t/"video/analys").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(VERKTYG, t/"video/analys/verktyg.mjs"); (t/"video/analys/pipeline.mjs").write_text(STUBB, encoding="utf-8")
    (t/"data/format/e37").mkdir(parents=True); shutil.copyfile(VIKTER, t/"data/format/e37/yolov8n.pt")
    assert sha256(t/"data/format/e37/yolov8n.pt") == sha256(VIKTER)
    return t

def kor_batch(label, filer, logg=None):
    """filer: {stem: Path till mätfil}. Kör E28, E30, E37 sekventiellt. Returnerar {stem: {'e28':..,'e30':..,'e37':..}}."""
    t = W / f"tree_{label}"
    if not t.exists(): bygg_trad(label)
    home = W / f"home_{label}"; dd = home / "Downloads/letrend-e13"
    if dd.exists(): shutil.rmtree(dd)
    dd.mkdir(parents=True)
    for s, p in filer.items(): os.link(p, dd / f"{s}.mp4")
    for k in ("e28", "e30", "e37"):   # tom utdata för just denna batch
        f = t/"data/format"/k/{"e28": "tek.jsonl", "e30": "tal.jsonl", "e37": "personer.jsonl"}[k]
        if f.exists(): f.unlink()
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home), PYTHONIOENCODING="utf-8", PYTHONUTF8="1", YOLO_OFFLINE="1", ULTRALYTICS_OFFLINE="1", HF_HUB_OFFLINE="1")
    tider = {}
    for k, cmd in (("e28", ["node", str(t/"video/format/e28-tek.mjs"), "--par", "1"]),
                   ("e30", [str(PY), "-I", "-X", "utf8", "-u", str(t/"video/format/e30_tal.py")]),
                   ("e37", [str(PY), "-I", "-X", "utf8", "-u", str(t/"video/format/e37_personer.py")])):
        t0 = time.time()
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(t))
        tider[k] = round(time.time() - t0, 1)
        if logg is not None: logg.append({"extraktor": k, "argv": cmd, "rc": r.returncode, "stdout": r.stdout[-3000:], "stderr": r.stderr[-1500:], "sek": tider[k]})
        if r.returncode != 0: print("EXTRAKTORFEL", k, r.returncode, r.stderr[-500:], file=sys.stderr)
    ut = {s: {} for s in filer}
    for k, fn in (("e28", "tek.jsonl"), ("e30", "tal.jsonl"), ("e37", "personer.jsonl")):
        f = t/"data/format"/k/fn
        if f.exists():
            for l in f.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    r = json.loads(l)
                    if r["id"] in ut: ut[r["id"]][k] = r
    return ut, tider
