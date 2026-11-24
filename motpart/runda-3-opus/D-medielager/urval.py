# -*- coding: utf-8 -*-
"""Stratifierat urval av 20 bankklipp för K8. Körs en gång; utfallet skrivs till urval.json.

Regel (skriven före dragningen):
  pool     = alla .mp4 i data/format/kontroll/klipp/ (de enda bankklippen med råvideo lokalt, 117 st)
  utesluts = spår A:s fyra hold-out-klipp och deras konton (så att inget hold-out-klipp används som
             kundmaterial före utvärderingen), samt utvecklingsklippet som koden prövades på under bygget
  strata   = bankens befintliga läsning l2 i byggsten/hand/ut/klipp.jsonl (Gemini, inte min bedömning):
             montage  : l2.montage == True
             sketch   : l2.typ == relaterbar_sketch            (och inte montage)
             tilltal  : l2.typ == direkt_tilltal               (och inte montage)
             visning  : l2.typ in {matporr_och_process, vardens_provsmakning}  (och inte montage)
  dragning = per stratum: random.Random(FRO + stratumindex).shuffle(sorted(ids)); ta i tur och ordning,
             högst ett klipp per konto inom stratumet och högst två per konto totalt, tills 5 är tagna.
Hold-out-klippen körs sedan separat med fryst kod (se HOLDOUT.md).
"""
import json
import random
from pathlib import Path

D = Path(__file__).resolve().parent
ROT = D.parents[2]
FRO = 20261119
PER = 5
STRATA = ["sketch", "tilltal", "visning", "montage"]
UTVECKLING = ["lilla.pixel-7600074418387242262"]


def main():
    holdout = [r.strip() for r in (D.parent / "A-domare" / "holdout_lista.txt").read_text(encoding="utf-8").splitlines() if r.strip()]
    hold_konton = {h.rsplit("-", 1)[0] for h in holdout}
    pool = sorted(p.stem for p in (ROT / "data/format/kontroll/klipp").glob("*.mp4"))
    L2 = {}
    for rad in open(ROT / "byggsten/hand/ut/klipp.jsonl", encoding="utf-8"):
        r = json.loads(rad)
        L2[r["id"]] = r.get("l2") or {}
    def stratum(k):
        l2 = L2.get(k) or {}
        if l2.get("montage") is True:
            return "montage"
        return {"relaterbar_sketch": "sketch", "direkt_tilltal": "tilltal",
                "matporr_och_process": "visning", "vardens_provsmakning": "visning"}.get(l2.get("typ"))
    behorig = [k for k in pool if k not in holdout and k.rsplit("-", 1)[0] not in hold_konton and k not in UTVECKLING]
    per_s = {s: sorted(k for k in behorig if stratum(k) == s) for s in STRATA}
    totalt = {}
    urval = []
    for i, s in enumerate(STRATA):
        ids = list(per_s[s])
        random.Random(FRO + i).shuffle(ids)
        tagna, konton = [], set()
        for k in ids:
            konto = k.rsplit("-", 1)[0]
            if konto in konton or totalt.get(konto, 0) >= 2:
                continue
            tagna.append(k)
            konton.add(konto)
            totalt[konto] = totalt.get(konto, 0) + 1
            if len(tagna) == PER:
                break
        urval += [dict(klipp=k, stratum=s, video=f"data/format/kontroll/klipp/{k}.mp4") for k in tagna]
    ut = dict(fro=FRO, regel=__doc__.strip(), pool=len(pool), behoriga=len(behorig),
              per_stratum_tillgangliga={s: len(v) for s, v in per_s.items()}, utvecklingsklipp=UTVECKLING,
              holdout=[dict(klipp=h, video=f"data/format/kontroll/klipp/{h}.mp4", stratum=stratum(h)) for h in holdout],
              urval=urval)
    (D / "urval.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    for u in urval:
        print(u["stratum"], u["klipp"])
    print({s: len(v) for s, v in per_s.items()}, len(behorig))


if __name__ == "__main__":
    main()
