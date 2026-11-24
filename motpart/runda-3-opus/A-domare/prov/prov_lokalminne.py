# -*- coding: utf-8 -*-
"""Prövning av LokalMinne-facit GT_VIS (motpart/runda-2-neon/djup_hard_gt_vis_eval.py).

Fråga: är GT_VIS oberoende? Det är handmärkt av samma part som byggde matcharen, efter att
matcharens fel setts. Motprov: en blind märkare (subagent som bara såg anonymiserade kontaktark,
lokalminne_blind/konto_*.jpg, gjorda av spår A direkt ur videorna) märker zonerna själv.
Vi mäter (1) parvis samstämmighet och Cohens kappa mellan GT_VIS och den blinda märkningen,
(2) om predikterade par finns (gt_vis_kopia_pred_pairs.json): precision/recall för v1..v3.2
mot båda facit.

Kör: python prov_lokalminne.py -> prov_lokalminne.json
"""
from __future__ import annotations

import ast
import itertools
import json
from pathlib import Path

HIT = Path(__file__).resolve().parent
ROT = HIT.parents[3]
SRC = ROT / "motpart/runda-2-neon/djup_hard_gt_vis_eval.py"


def las_gt_vis() -> dict:
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    for n in tree.body:
        if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "GT_VIS_ZONES":
            return ast.literal_eval(n.value)
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "GT_VIS_ZONES" for t in n.targets):
            return ast.literal_eval(n.value)
    raise RuntimeError("GT_VIS_ZONES saknas")


def par(zoner: dict[int, set]) -> dict[tuple[int, int], bool]:
    n = sorted(zoner)
    return {(i, j): bool(set(zoner[i]) & set(zoner[j])) for i, j in itertools.combinations(n, 2)}


def kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def main():
    gt = las_gt_vis()
    nyckel = json.loads((HIT / "lokalminne_blind_nyckel.json").read_text(encoding="utf-8"))
    blind_raw = json.loads((HIT / "lokalminne_blind/blind_zoner.json").read_text(encoding="utf-8"))
    blind = {nyckel[k]: {int(i): set(v["zoner"]) for i, v in d.items()} for k, d in blind_raw.items()}
    ut = {"per_konto": {}}
    alla_a, alla_b = [], []
    for acc, z in gt.items():
        pa = par(z)
        pb = par(blind[acc])
        k = sorted(set(pa) & set(pb))
        a = [pa[x] for x in k]; b = [pb[x] for x in k]
        alla_a += a; alla_b += b
        ut["per_konto"][acc] = {
            "par": len(k), "sanna_GT_VIS": sum(a), "sanna_blind": sum(b), "bada_sanna": sum(x and y for x, y in zip(a, b)),
            "samstammighet": round(sum(x == y for x, y in zip(a, b)) / max(1, len(k)), 3),
            "kappa": None if kappa(a, b) is None else round(kappa(a, b), 3),
            "bara_GT_VIS": [list(x) for x in k if pa[x] and not pb[x]],
            "bara_blind": [list(x) for x in k if pb[x] and not pa[x]],
        }
    ut["totalt"] = {"par": len(alla_a), "sanna_GT_VIS": sum(alla_a), "sanna_blind": sum(alla_b),
                    "bada_sanna": sum(x and y for x, y in zip(alla_a, alla_b)),
                    "samstammighet": round(sum(x == y for x, y in zip(alla_a, alla_b)) / len(alla_a), 3),
                    "kappa": round(kappa(alla_a, alla_b), 3)}
    pp = HIT / "gt_vis_kopia_pred_pairs.json"
    if pp.exists():
        pred = json.loads(pp.read_text(encoding="utf-8"))
        res = {}
        for ver in ("v1", "v2", "v31", "v32"):
            for namn, facit in (("GT_VIS", gt), ("blind", blind)):
                tp = fp = fn = 0
                for acc in pred:
                    p = {(a, b) for a, b, _ in pred[acc][ver]}
                    s = {x for x, v in par(facit[acc]).items() if v}
                    tp += len(p & s); fp += len(p - s); fn += len(s - p)
                res[f"{ver}_{namn}"] = {"TP": tp, "FP": fp, "FN": fn,
                                       "precision": round(tp / max(1, tp + fp), 3), "recall": round(tp / max(1, tp + fn), 3)}
        ut["pred_mot_facit"] = res
        ut["pred_konton_klara"] = sorted(pred)
    (HIT / "prov_lokalminne.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in ut.items() if k != "per_konto"}, ensure_ascii=False, indent=1))
    for acc, r in ut["per_konto"].items():
        print(f"{acc:22s} par={r['par']:3d} GT_VIS={r['sanna_GT_VIS']:3d} blind={r['sanna_blind']:3d} båda={r['bada_sanna']:3d} kappa={r['kappa']}")


if __name__ == "__main__":
    main()
