"""Ingest- och O-lagerbyggare kopplad genom JobbKorare (INFRA.md §1, §3, M1, M3, M4).

All tung körning går automatiskt via infra/kor.py:
  1. Läser maskinens gränser (disk, RAM, CPU, Modal).
  2. Kör provlopp på 2 klipp, mäter sek/klipp och MB/klipp.
  3. Beslutar plats (lokal om <= 5 min och disk räcker, annars Modal-pool/varm maskin).
  4. Skriver GRIND.json och kontinuerligt FRAMSTEG.json (hjärtslag).
  5. Är helt återupptagbar per klipp-id (klara.jsonl).

Exempel:
    python infra/bygg_olager.py --kallor ~/Downloads/letrend-r4 --ut data/olager --torr
    python infra/bygg_olager.py --kallor ~/Downloads/letrend-r4 --plats modal
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROT = Path(__file__).resolve().parents[1]
if str(ROT) not in sys.path:
    sys.path.insert(0, str(ROT))

from infra.extraktorer import VarmExtraktor
from infra.kor import JobbKorare, JobbSpec
from infra.olager import bygg_klipp, ladda_repo_metadata


def main() -> int:
    ap = argparse.ArgumentParser(description="Bygg O-lager med inbyggd M4-grind (kor.py)")
    ap.add_argument("--kallor", type=Path, default=Path.home() / "Downloads" / "letrend-r4")
    ap.add_argument("--ut", type=Path, default=ROT / "data" / "olager")
    ap.add_argument("--jobbmapp", type=Path, default=ROT / "data" / "jobb" / "olager_r4")
    ap.add_argument("--plats", choices=["auto", "lokal", "modal", "varm_maskin"], default="auto")
    ap.add_argument("--torr", action="store_true", help="Kör bara provlopp och skriv ETA-grind")
    ap.add_argument("--max", dest="max_antal", type=int, default=None, help="Begränsa antal klipp (t.ex. pilot)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    mp4s = sorted(a.kallor.glob("*.mp4"))
    if a.max_antal:
        mp4s = mp4s[: a.max_antal]
    ids = [p.stem for p in mp4s]
    meta_map = ladda_repo_metadata(set(ids))
    extr_holder: dict[str, VarmExtraktor] = {}

    def kor_en(cid: str) -> dict[str, Any]:
        if "e" not in extr_holder:
            extr_holder["e"] = VarmExtraktor()
        return bygg_klipp(cid, a.kallor / f"{cid}.mp4", a.ut, extr_holder["e"], extra_meta=meta_map.get(cid), force=a.force)

    def kor_fjarr(kvar_ids: list[str], plats: str) -> list[dict[str, Any]]:
        if plats == "modal":
            import modal

            Arb = modal.Cls.from_name("hagen-infra", "VarmArbetare")
            arb = Arb()
            chunks = [kvar_ids[i : i + 8] for i in range(0, len(kvar_ids), 8)]
            ut: list[dict[str, Any]] = []
            for batch in arb.bygg_olager_chunk.map(chunks, kwargs={"force": a.force, "med_c_ref": True}):
                for r in batch:
                    ut.append({
                        "enhet": r["id"],
                        "status": "ok" if r.get("status") == "ok" else "fel",
                        "sek": r.get("sek", 0.0),
                        "kostnad_usd": 0.0005,
                        "resultat": r,
                    })
            return ut
        raise RuntimeError(f"Fjärrplats {plats} ej kopplad i denna klient")

    spec = JobbSpec(
        jobb_id=f"olager_{a.kallor.name}",
        mapp=a.jobbmapp,
        beskrivning=f"Bygg O-lager för {len(ids)} klipp ur {a.kallor}",
        provlopp_antal=2,
        min_ledigt_disk_gb=5.5,
        max_kostnad_usd=1.0,
        plats_preferens=a.plats,
        kostnad_per_enhet_usd=0.0005,
        torr=a.torr,
    )
    korare = JobbKorare(spec)
    res = korare.kor(ids, kor_en, kor_batch_fjarr=kor_fjarr, fjarr_speedup_faktor=20.0)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
