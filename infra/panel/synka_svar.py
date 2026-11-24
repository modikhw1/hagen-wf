"""Synkar ägarens svar tillbaka till repot och kopplar varje svar till O-lagrets id via nyckel.json (INFRA.md §4)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]


def synka(base_url: str, pass_id: str, ut_rot: Path, token: str | None) -> dict:
    hdrs = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(f"{base_url.rstrip('/')}/api/export/{pass_id}", headers=hdrs)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    mapp = ut_rot / pass_id
    mapp.mkdir(parents=True, exist_ok=True)
    (mapp / "meta.json").write_text(json.dumps(data["meta"], ensure_ascii=False, indent=2), encoding="utf-8")
    (mapp / "svar.json").write_text(json.dumps(data["svar"], ensure_ascii=False, indent=2), encoding="utf-8")
    (mapp / "svar.logg.jsonl").write_text(data.get("logg_jsonl") or "", encoding="utf-8")
    if data.get("nyckel"):
        (mapp / "nyckel.json").write_text(json.dumps(data["nyckel"], ensure_ascii=False, indent=2), encoding="utf-8")

    # Koppla svar med olager_id och variant (ordagranna kommentarer bevarade)
    nyck_map = {p["id"]: p for p in (data.get("nyckel") or {}).get("par", [])}
    kopplade = []
    for s in data["svar"]:
        k = nyck_map.get(s.get("par"), {})
        kopplade.append({
            "tid": s.get("tid"),
            "session": s.get("session"),
            "par": s.get("par"),
            "olager_id": k.get("olager_id") or k.get("klipp"),
            "variant": k.get("variant"),
            "kontroll": k.get("kontroll"),
            "svar": {kk: vv for kk, vv in s.items() if kk not in ("par", "tid", "session", "pass_id")},
        })
    (mapp / "kopplade_svar.json").write_text(json.dumps(kopplade, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"pass_id": pass_id, "antal_svar": len(data["svar"]), "mapp": str(mapp)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pass_id")
    ap.add_argument("--url", default=os.environ.get("PANEL_URL", "http://127.0.0.1:5191"))
    ap.add_argument("--token", default=os.environ.get("PANEL_TOKEN"))
    ap.add_argument("--ut", type=Path, default=ROT / "motpart/runda-4/panel_svar")
    a = ap.parse_args()
    print(json.dumps(synka(a.url, a.pass_id, a.ut, a.token), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
