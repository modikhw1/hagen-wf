"""Kontroll av fps-rättningen i `scen/3d/ingest/flera/ingest_flera.py` (20 nov): gamla och nya `fps_rat` per källvideo.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\holdout\\fps_kontroll.py

För varje `scen/3d/ingest/ut/*/tagningar.json`: källvideons fps enligt den gamla funktionen (`ingest_flera.py.fore_fps.bak`)
och den nya. Är de lika blir delningen bitidentisk i ffmpeg-anropet (fps är det enda som ändrats). Dessutom räknas rutorna
i befintliga `klipp/S*.mp4` mot planen. Skriver `holdout/fps_kontroll.json`.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import cv2

ROT = pathlib.Path(__file__).resolve().parents[4]
FL = ROT / "scen" / "3d" / "ingest" / "flera"
sys.path.insert(0, str(FL))
sys.path.insert(0, str(FL.parent))


def ladda(fil, namn):
    import importlib.machinery
    spec = importlib.util.spec_from_file_location(namn, fil, loader=importlib.machinery.SourceFileLoader(namn, str(fil)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ny = ladda(FL / "ingest_flera.py", "flera_ny")
gammal = ladda(FL / "ingest_flera.py.fore_fps.bak", "flera_gammal")
res = []
for pj in sorted((ROT / "scen" / "3d" / "ingest" / "ut").glob("*/tagningar.json")):
    raw = pj.read_bytes()
    try:
        plan = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        plan = json.loads(raw.decode("cp1252"))
    kalla = pathlib.Path(plan.get("klipp", ""))
    rad = dict(mapp=pj.parent.name, kalla=str(kalla), finns=kalla.exists())
    if kalla.exists():
        rad["fps_gammal"] = list(gammal.fps_rat(kalla))
        rad["fps_ny"] = list(ny.fps_rat(kalla))
        rad["lika"] = rad["fps_gammal"] == rad["fps_ny"]
    fil = []
    for s in plan["tagningar"]:
        f = pj.parent / "klipp" / f"{s['id']}.mp4"
        n = int(cv2.VideoCapture(str(f)).get(cv2.CAP_PROP_FRAME_COUNT)) if f.exists() else None
        fil.append(dict(id=s["id"], plan=s["rutor"], fil=n))
    rad["rutor_plan"] = sum(x["plan"] for x in fil)
    rad["rutor_filer"] = sum(x["fil"] or 0 for x in fil)
    rad["N_kalla"] = plan.get("N")
    res.append(rad)
    print(json.dumps({k: v for k, v in rad.items() if k != "kalla"}, ensure_ascii=False), flush=True)
(pathlib.Path(__file__).parent / "fps_kontroll.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
