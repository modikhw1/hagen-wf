"""rum_fokal_moge.py — notan med MoGe:s egen fokal (~41° hfov ≈ 0,78 × 983,7 px; EXPERIMENT.md 7.3).

Registrerar en extra variant i rum_ablation.VARIANTER i minnet (filen ändras inte) och kör den.
Resultat: rum_ut/ablation/notan/S_L1_fokal_0.78.json
"""
import json
import pathlib
import sys

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
import rum_ablation as ra  # noqa: E402

f = 0.78
namn = f"S_L1_fokal_{f}"
ra.VARIANTER[namn] = dict(obs=[("f_sann, f_sig = (fk[0], fk[1]) if fk else (None, None)",
                                f"f_sann, f_sig = (fk[0] * {f}, fk[1]) if fk else (None, None)")])
m, obs, rec = ra.kor_variant("notan", namn, None)
m["roller"] = {k.klipp: [(d.nyckel, d.pose, d.vid) for d in k.detektioner if d.klass == "person"] for k in obs.klipp}
(HIT / "rum_ut" / "ablation" / "notan" / f"{namn}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: m[k] for k in ("variant", "tro", "P", "bord", "avstand", "sek")}, ensure_ascii=False))
