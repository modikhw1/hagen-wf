"""rum_namnprov.py — visar att Lager 1 hämtar klippspecifik data via mappnamn (A6).

obs_motor._modell_semantik() matchar ingest-mappens namn mot scen/3d/kontrakt/semantik/ut/<namn>/
(prefix "<namn>-", likhet, eller delsträng om namnet har minst 3 tecken). obs_motor._fokal() matchar
mot nycklarna i scen/3d/kontrakt/ut/fore_fokal_0009/fyra_klipp.json med startswith.
Här provas påhittade, icke-existerande klippnamn: får de ett annat klipps roller/fokal?
Inga filer skrivs utanför rum_ut/.
"""
from __future__ import annotations

import json
import pathlib
import sys

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
sys.path.insert(0, str(ROT / "forvarld_karna"))
import obs_motor  # noqa: E402

FALSKA = [
    "a-dialog-kafe-tagningar",     # nytt klipp vars namn råkar börja på "a-"
    "b-ny-kund-tagningar",
    "kennys-burgare-tagningar",    # innehåller "kenny"
    "bonotanical-tagningar",       # innehåller "notan"
    "notan-tagningar-v2",
    "z-helt-okant-tagningar",
]

ut = {}
for n in FALSKA:
    p = ROT / "motpart/runda-1-claude/rum_ut/finns_inte" / n   # finns inte: ingen egen semantik.json
    sem = obs_motor._modell_semantik(p)
    fk = obs_motor._fokal(p)
    roller = None
    if sem:
        roller = {pp["id"]: [s["tagning"] for s in pp.get("spar", [])] for pp in sem.get("personer", [])}
    ut[n] = dict(
        semantik_klipp=(sem or {}).get("klipp"),
        semantik_roller=roller,
        fokal_px=round(fk[0], 1) if fk else None,
    )
    print(n, "->", json.dumps(ut[n], ensure_ascii=False))
(HIT / "rum_ut").mkdir(exist_ok=True)
(HIT / "rum_ut" / "namnprov.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
