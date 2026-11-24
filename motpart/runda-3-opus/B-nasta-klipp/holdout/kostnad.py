"""Modal-kostnad i dag (UTC-dygn), totalt, per app och per resurs. Kostnadsvakt för hold-out-körningen (tak 15 USD).

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\holdout\\kostnad.py [--tak 12]

Exit 3 om summan i dag är större än --tak. Debiteringen kan släpa efter (timupplösning), så siffran är en undre gräns
tills den har satt sig.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys
from collections import defaultdict

ROT = pathlib.Path(__file__).resolve().parents[4]
MODAL = ROT / "scen" / ".venv" / "Scripts" / "modal.exe"


def idag() -> dict:
    start = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    r = subprocess.run([str(MODAL), "billing", "report", "--start", start, "-r", "h", "--show-resources", "--json"],
                       capture_output=True, text=True, encoding="utf-8", env={"PYTHONIOENCODING": "utf-8", **__import__("os").environ})
    rader = json.loads(r.stdout or "[]")
    tot, per_app, per_res = 0.0, defaultdict(float), defaultdict(float)
    for x in rader:
        c = float(x.get("cost") or 0)
        tot += c
        per_app[x.get("description", "?")] += c
        per_res[x.get("resource", x.get("resource_type", "?"))] += c
    return dict(start_utc=start, totalt_usd=round(tot, 4), per_app={k: round(v, 4) for k, v in per_app.items()},
                per_resurs={k: round(v, 4) for k, v in per_res.items()}, rader=len(rader))


if __name__ == "__main__":
    tak = float(sys.argv[sys.argv.index("--tak") + 1]) if "--tak" in sys.argv else 12.0
    k = idag()
    k["tid"] = dt.datetime.now().strftime("%H:%M:%S")
    print(json.dumps(k, ensure_ascii=False))
    sys.exit(3 if k["totalt_usd"] > tak else 0)
