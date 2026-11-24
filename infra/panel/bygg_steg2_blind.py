"""Bygger en publicerbar blindpanel-spec för steg 2 A2 (mänsklig grind först, INFRA.md §3.5 & §4).

Kan anropas direkt av kor.py som mansklig_grind_fn innan tung automatik körs:
genererar en spec JSON för blinda C-mot-O, N1..N5-mot-C och P-mot-C-par och kan
publicera dem till den stående ägarpanelen på < 1 min.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]


def skapa_steg2_spec(
    pass_id: str,
    ut_spec: Path,
    *,
    kallor_dir: Path | None = None,
    max_klipp: int = 12,
    varianter: tuple[str, ...] = ("N1", "N3", "N5", "P"),
) -> Path:
    src = kallor_dir or (Path.home() / "Downloads" / "letrend-r4")
    urv = json.loads((ROT / "motpart/runda-4/2-invarians/urval_las.json").read_text(encoding="utf-8"))
    klipp = urv["step2"][:max_klipp]

    vf_map = {
        "N1": "",
        "N2": "scale=w='max(2,trunc(iw/4)*2)':h='max(2,trunc(ih/4)*2)':flags=lanczos",
        "N3": "",
        "N4": "",
        "N5": "fps=fps=15:start_time=0:round=near",
        "P": "setpts=(PTS-STARTPTS)/1.25",
    }
    af_map = {
        "N3": "volume=-6dB",
        "N4": "volume=-12dB",
        "P": "atempo=1.25",
    }

    par = []
    for k in klipp:
        cid = k["id"]
        fil = src / f"{cid}.mp4"
        if not fil.exists():
            continue
        for var in varianter:
            par.append({
                "olager_id": cid,
                "variant": var,
                "kontroll": "positiv_tempo_1_25x" if var == "P" else None,
                "forvantat": "snabbare" if var == "P" else "oforandrat",
                "synk": var != "P",
                "tillat_gain_komp": var in ("N3", "N4"),
                "media": {
                    "original": {"fil": str(fil), "olager_id": cid, "variant": "C"},
                    "efter": {
                        "fil": str(fil),
                        "olager_id": cid,
                        "variant": var,
                        "vf": vf_map.get(var, ""),
                        "af": af_map.get(var, ""),
                    },
                },
            })

    spec = {
        "pass_id": pass_id,
        "titel": f"Steg 2 — Blind innehållskontroll ({len(par)} par)",
        "lage": "invarians",
        "beskrivning": "Bedöm blint om innehåll, framförandetempo och energi är bevarade. För ljudnivå finns +6/+12 dB uppspelningskompensation.",
        "fro": 202611204,
        "par": par,
    }
    ut_spec.parent.mkdir(parents=True, exist_ok=True)
    ut_spec.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return ut_spec


if __name__ == "__main__":
    ut = Path(sys.argv[1]) if len(sys.argv) > 1 else (ROT / "data/panel/steg2_blind_spec.json")
    skapa_steg2_spec("steg2-invarians-blind", ut)
    print(f"Skrev {ut}")
