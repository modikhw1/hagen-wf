"""rum_gammal.py — prövar Argons bugg 1-rättningar på den GAMLA kedjan: byggsten/rumshypotes/hjarna.py
på den gamla notan-observationen byggsten/rumshypotes/ut/notan/obs.json.

Frågan: räcker det att vidga grinden i _expandera (Argons "FIX Bugg 1a", samma formel) eller att byta
kamerainitieringen i _barn (Argons "FIX Bugg 1b", ordagrant överförd) för att den gamla hjärnan ska
knyta S7:s förgrundsbord/burk till A:s bord och burk? Ingen fil i byggsten/ ändras; hjarna.py läses
som text och patchas i minnet (varje patch måste träffa exakt en gång).

    python rum_gammal.py --variant bas|grind|ingen_grind|grind_nya_priser|barn|grind_barn|grind_barn_nfev12
Resultat: rum_ut/gammal/<variant>.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time
import types

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
RH = ROT / "byggsten/rumshypotes"
sys.path.insert(0, str(RH))

import regler  # noqa: E402,F401  (byggsten/rumshypotes/regler.py)
from telemetri import Observationer  # noqa: E402

NL = "\n"


def rader(*r):
    return NL.join(r) + NL


GAMMAL_GRIND = rader(
    "                        grind = 3 * d.djup_m.s + 1.0",
    '                        a = [x for x in a if x[0] != "finns" or np.linalg.norm(h.x["ent"][x[1]] - pv) < grind]',
)
NY_GRIND = rader(  # samma formel som forvarld_karna/rums_pussel.py:920
    '                        sig_ank = max((sigma_max(h.kov["ent"][eid]) for _i, (typ, eid) in zip(iu, uk)',
    '                                       if typ == "finns" and eid in h.kov.get("ent", {})), default=0.0)',
    '                        a = [x for x in a if x[0] != "finns" or np.linalg.norm(h.x["ent"][x[1]] - pv) < '
    '3 * d.djup_m.s + 1.0 + 2.0 * (sig_ank + (sigma_max(h.kov["ent"][x[1]]) if x[1] in h.kov.get("ent", {}) else 0.0))]',
)
INGEN_GRIND = rader("                        a = list(a)")

# Argons "FIX Bugg 1b" (rums_pussel.py:710-724 och 746-769) överförd ordagrant till den gamla _barn
GAMMAL_KAMERA = rader(
    "    pos = []",
    "    for d, (typ, eid) in zip(o.detektioner, komb):",
    '        if typ == "finns":',
    '            pos.append(x["ent"][eid] - d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R))',
    "    if k == 0:",
    "        c = np.zeros(2)",
    "    elif pos:",
    "        c = np.mean(pos, axis=0)",
)
NY_KAMERA = rader(
    "    pos, vikter = [], []",
    "    for d, (typ, eid) in zip(o.detektioner, komb):",
    '        if typ == "finns":',
    '            p_cam = x["ent"][eid] - d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R)',
    '            s_ent = sigma_max(h.kov["ent"][eid]) if eid in h.kov.get("ent", {}) else 2.0',
    "            pos.append(p_cam)",
    "            vikter.append(1.0 / (s_ent ** 2 + d.djup_m.s ** 2 + 0.02))",
    "    if k == 0:",
    "        c = np.zeros(2)",
    "    elif pos:",
    "        c = np.average(np.array(pos), axis=0, weights=np.array(vikter))",
)
GAMMAL_NYA_SAKER = rader("    # nya saker")
KLUSTERFLYTT = rader(
    "    har_fast_ankare = any(",
    '        typ == "finns" and eid in h.kov.get("ent", {}) and sigma_max(h.kov["ent"][eid]) < 0.8',
    "        for _, (typ, eid) in zip(o.detektioner, komb)",
    "    )",
    "    if har_fast_ankare:",
    "        flyttade_kluster = set()",
    "        for d, (typ, eid) in zip(o.detektioner, komb):",
    '            if typ == "finns" and eid in h.kov.get("ent", {}) and sigma_max(h.kov["ent"][eid]) >= 1.0:',
    "                p_obs = c + d.djup_m.v * _riktning(th - d.bearing_deg.v * D2R)",
    '                p_old = h.x["ent"][eid]',
    "                delta = p_obs - p_old",
    "                if np.linalg.norm(delta) > 0.3 and eid not in flyttade_kluster:",
    '                    for eid2, p2 in list(h.x["ent"].items()):',
    '                        s2 = sigma_max(h.kov["ent"][eid2]) if eid2 in h.kov.get("ent", {}) else 0.0',
    "                        if s2 >= 1.0 and np.linalg.norm(p2 - p_old) < 2.2:",
    '                            x["ent"][eid2] = p2 + delta',
    "                            flyttade_kluster.add(eid2)",
    '                    for kk, cam_old in list(h.x["cam"].items()):',
    '                        sc = math.sqrt(max(np.linalg.eigvalsh(h.kov["cam"][kk][:2, :2]).max(), 0.0)) if kk in h.kov.get("cam", {}) else 0.0',
    "                        if sc >= 1.0 and np.linalg.norm(cam_old[:2] - p_old) < 2.8:",
    '                            x["cam"][kk][:2] = cam_old[:2] + delta',
    "    # nya saker",
)
BARN = [(GAMMAL_KAMERA, NY_KAMERA), (GAMMAL_NYA_SAKER, KLUSTERFLYTT)]
NFEV12 = [("passning = _los(c, obs, k + 1, max_nfev=8)", "passning = _los(c, obs, k + 1, max_nfev=12)")]
NYA_PRISER = {"mugg": 0.4, "kopp": 0.4, "glas": 0.4, "bricka": 0.4, "burk": 3.2, "flaska": 3.2, "bonaqua": 3.5}

VARIANTER = {
    "bas": dict(patch=[]),
    "grind": dict(patch=[(GAMMAL_GRIND, NY_GRIND)]),
    "ingen_grind": dict(patch=[(GAMMAL_GRIND, INGEN_GRIND)]),
    "grind_nya_priser": dict(patch=[(GAMMAL_GRIND, NY_GRIND)], foremal=NYA_PRISER),
    "barn": dict(patch=BARN),
    "grind_barn": dict(patch=[(GAMMAL_GRIND, NY_GRIND)] + BARN),
    "grind_barn_nfev12": dict(patch=[(GAMMAL_GRIND, NY_GRIND)] + BARN + NFEV12),
    "grind_barn_nfev12_priser": dict(patch=[(GAMMAL_GRIND, NY_GRIND)] + BARN + NFEV12, foremal=NYA_PRISER),
}


def kalla():
    return (RH / "hjarna.py").read_text(encoding="utf-8")


def ladda(patchar):
    src = kalla()
    for g, n in patchar:
        c = src.count(g)
        if c != 1:
            raise SystemExit(f"PATCH MISSAR ({c}): {g[:80]!r}")
        src = src.replace(g, n)
    mod = types.ModuleType("hjarna_ab")
    mod.__file__ = str(RH / "hjarna.py")
    sys.modules["hjarna_ab"] = mod
    exec(compile(src, "hjarna.py<ab>", "exec"), mod.__dict__)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="bas", choices=list(VARIANTER))
    ap.add_argument("--kontroll", action="store_true", help="kontrollera bara att patcharna träffar")
    a = ap.parse_args()
    if a.kontroll:
        src = kalla()
        for n, v in VARIANTER.items():
            print(n, [src.count(g) for g, _ in v["patch"]])
        return
    v = VARIANTER[a.variant]
    hj = ladda(v["patch"])
    if v.get("foremal"):
        hj.FOREMAL_PRIS = v["foremal"]
    obs = Observationer.model_validate_json((RH / "ut/notan/obs.json").read_text(encoding="utf-8"))
    t0 = time.time()
    hist = hj.kor(obs)
    rad = hj.logg(hist, obs)
    sek = time.time() - t0
    h = hist[-1].stråle[0]
    K = len(obs.klipp)
    s7 = obs.klipp[-1]
    assoc_s7 = {d.id: h.assoc[(K - 1, d.id)] for d in s7.detektioner}
    sedd = {}
    for (k, did), eid in h.assoc.items():
        sedd.setdefault(eid, set()).add(obs.klipp[k].klipp)
    pos = {e: h.x["ent"][e] for e in h.ents}
    av = round(math.dist(pos["A"], pos["B"]), 3) if "A" in pos and "B" in pos else None
    ut = dict(variant=a.variant, sek=round(sek, 1), tro=rad[-1]["tro"], P=rad[-1]["sannolikhet"],
              assoc_s7=assoc_s7, sedd={e: sorted(s) for e, s in sorted(sedd.items())},
              n_bord=sum(1 for e in h.ents.values() if e.klass == "bord"), avstand_A_B=av,
              osak_B=[r["osakerhet_m"].get("B") for r in rad],
              tro_per_tagning=[(r["klipp"], r["tro"], r["sannolikhet"]) for r in rad])
    d = HIT / "rum_ut" / "gammal"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{a.variant}.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ut, ensure_ascii=False))


if __name__ == "__main__":
    main()
