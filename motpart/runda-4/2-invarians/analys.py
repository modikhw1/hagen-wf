"""Steg 2: fryst referenstransform (A3) och förutbestämd dom (A4). Läser ref_mat.jsonl (R:s C) och test_mat.jsonl.
Inga trösklar här är nya; alla står i FORREGISTRERING.md. Tolkningar av oklara punkter står i AVVIKELSER.md (skrivna före testmätningen).
  python analys.py --lage test|dry   (dry använder dry_test_mat.jsonl och duplicerar klipp till 12 för att öva kodvägarna)
"""
import argparse, json, sys, math
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from falt import FALT, T2_19, uttag

HER = Path(__file__).parent


def jsonl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------- A3: viktad ECDF-transform, fryst på R ----------
class Transform:
    def __init__(self, ref_rader):
        """ref_rader: [{'id','konto','v':{falt:val}}] för R:s C-versioner. Varje konto har lika total vikt, fördelad lika över kontots klipp
        med giltigt värde för fältet; vikterna normaliseras över giltiga konton för just fältet."""
        self.par = {}
        self.nk = len({r["konto"] for r in ref_rader})
        for j in FALT:
            val = [(r["konto"], r["v"][j]) for r in ref_rader if r["v"].get(j) is not None]
            kk = sorted({k for k, _ in val})
            if len(kk) < 30:
                self.par[j] = {"kalibrerad": False, "giltiga_konton": len(kk)}
                continue
            per = defaultdict(int)
            for k, _ in val:
                per[k] += 1
            x = np.array([v for _, v in val], dtype=float)
            w = np.array([1.0 / per[k] for k, _ in val])
            w = w / w.sum()
            F = np.array([w[x < v].sum() + 0.5 * w[x == v].sum() for v in x])
            mu = float((w * F).sum())
            sd = float(math.sqrt((w * (F - mu) ** 2).sum()))
            self.par[j] = {"kalibrerad": sd > 0, "giltiga_konton": len(kk), "mu": mu, "sigma": sd, "xs": x, "w": w,
                           "min": float(x.min()), "max": float(x.max()), "median": float(np.median(x)), "konstant": sd == 0}

    def F(self, j, v):
        p = self.par[j]
        x, w = p["xs"], p["w"]
        return float(w[x < v].sum() + 0.5 * w[x == v].sum())

    def z(self, j, v):
        p = self.par[j]
        if v is None or not p.get("kalibrerad"):
            return None
        return (self.F(j, v) - p["mu"]) / p["sigma"]

    def utanfor(self, j, v):
        p = self.par[j]
        return v is not None and "min" in p and (v < p["min"] or v > p["max"])


def ladda_ref():
    rader = []
    for r in jsonl(HER / "ref_mat.jsonl"):
        if r.get("c_rc") != 0 or not r.get("e28"):
            continue
        v, st = uttag(r)
        rader.append({"id": r["id"], "konto": r["konto"], "v": v, "st": st})
    return rader


# ---------- förtest av transformen ----------
def fortest(T, ref, testrader):
    """Permutera R och testtabellens radordning 100 ggr (rng 202611204): alla z skiljer högst 1e-12 efter återställning av id-ordning.
    Lägg till en kopia av en testvariant utan att passa om: tidigare z oförändrade."""
    rng = np.random.default_rng(202611204)
    bas = {(t["id"], t["variant"]): {j: T.z(j, t["v"].get(j)) for j in FALT} for t in testrader}
    maxd = 0.0
    for _ in range(100):
        pr = [ref[i] for i in rng.permutation(len(ref))]
        pt = [testrader[i] for i in rng.permutation(len(testrader))]
        T2 = Transform(pr)
        for t in pt:
            for j in FALT:
                a, b = bas[(t["id"], t["variant"])][j], T2.z(j, t["v"].get(j))
                if (a is None) != (b is None):
                    maxd = max(maxd, 1e9)
                elif a is not None:
                    maxd = max(maxd, abs(a - b))
    res = {"permutation_max_avvikelse": maxd, "permutation_ok": maxd <= 1e-12}
    # tillägg av en testkopia utan ompassning: z hänger bara på Transform(ref); kontrolleras mot en andra, orörd beräkning
    ny = [t for t in testrader] + [dict(testrader[0], variant=testrader[0]["variant"] + "_kopia")]
    d2 = max((abs(bas[(t["id"], t["variant"])][j] - T.z(j, t["v"].get(j))) for t in ny if (t["id"], t["variant"]) in bas for j in FALT if bas[(t["id"], t["variant"])][j] is not None), default=0.0)
    res["tillagg_kopia_max_avvikelse"] = d2
    res["tillagg_kopia_ok"] = d2 == 0.0
    return res


def identitet(V, ids):
    """N0 mot C, C2 (samma fil, ny extraktion) mot C, Cr (ny C-kodning) mot C, N0r mot N0: exporterade råfält ska vara identiska."""
    brott, n = [], 0
    for i in ids:
        for a, b in [("N0", "C"), ("C2", "C"), ("Cr", "C"), ("N0r", "N0")]:
            if a in V[i] and b in V[i]:
                n += 1
                for j in FALT:
                    if V[i][a].get(j) != V[i][b].get(j):
                        brott.append({"id": i, "par": f"{a} vs {b}", "falt": j, a: V[i][a].get(j), b: V[i][b].get(j)})
    return {"jamforelser": n, "brott": brott}


# ---------- A4 ----------
NN = ["N1", "N2", "N3", "N4", "N5"]


def dom_T(j, V, ids, st, T):
    klass, eps, fakt, hf = FALT[j]
    per = {}
    for i in ids:
        v = V[i]
        c, p = v.get("C", {}).get(j), v.get("P", {}).get(j)
        ns = {n: v.get(n, {}).get(j) for n in NN}
        rad = {"C": c, "P": p, **ns}
        giltigN = all(x is not None for x in ns.values()) and c is not None
        t = max(abs(x - c) for x in ns.values()) if giltigN else None
        pp = abs(p - c) if (p is not None and c is not None) else None
        q = (t / pp) if (t is not None and pp is not None and pp > eps) else None
        rad.update({"t": t, "p": pp, "q": q, "positivt_okanslig": (pp is not None and pp <= eps)})
        tecken_fel, storlek_fel = False, False
        if pp is not None and pp > eps and klass in ("Ttid", "Ttat"):
            ok = (p - c) < 0 if klass == "Ttid" else (p - c) > 0
            tecken_fel = not ok
            stabilt = True if hf is None else (v.get("C", {}).get(hf) is not None and v.get("C", {}).get(hf) == v.get("P", {}).get(hf))
            if stabilt and ok:
                storlek_fel = abs(p - fakt * c) > max(eps, 0.10 * abs(c * (fakt - 1)))
        rad.update({"tecken_fel": tecken_fel, "storlek_fel": storlek_fel, "teknisk_over_eps": (t is not None and t > eps)})
        zc, zp = T.z(j, c), T.z(j, p)
        zn = [T.z(j, x) for x in ns.values()]
        if zc is not None and zp is not None and all(x is not None for x in zn):
            zt, zpp = max(abs(x - zc) for x in zn), abs(zp - zc)
            rad["z_q"] = (zt / zpp) if zpp > 0 else None
        rad["giltig_for_grind"] = bool(giltigN and pp is not None and pp > eps and not tecken_fel and not storlek_fel)
        per[i] = rad
    gil = [r for r in per.values() if r["giltig_for_grind"]]
    qs = [r["q"] for r in per.values() if r["q"] is not None]
    c4 = 0
    for i in ids:
        v = V[i]
        saknat = any(v.get(x, {}).get(j) is None and v.get("C", {}).get(j) is not None for x in NN + ["P"])
        rutor = j.startswith("e37") and any(st[i].get(x, {}).get("e37_rutor", 6) < 6 for x in ["C"] + NN)
        if saknat or rutor:
            c4 += 1
    v1 = len(gil) < 8
    v2 = (len(qs) > 0 and float(np.median(qs)) >= 0.5) or sum(1 for q in qs if q >= 1) >= 3
    v3 = sum(1 for r in per.values() if r["teknisk_over_eps"]) >= 3 or sum(1 for r in per.values() if r["tecken_fel"]) >= 3
    v4 = c4 >= 2
    out = {"klass": klass, "eps": eps, "n_giltiga_for_grind": len(gil), "median_q": float(np.median(qs)) if qs else None,
           "n_q_ge_1": sum(1 for q in qs if q >= 1), "n_q_ge_05": sum(1 for q in qs if q >= 0.5), "n_q_definierad": len(qs),
           "n_teknisk_over_eps": sum(1 for r in per.values() if r["teknisk_over_eps"]), "n_tecken_fel": sum(1 for r in per.values() if r["tecken_fel"]),
           "n_storlek_fel": sum(1 for r in per.values() if r["storlek_fel"]), "n_positivt_okanslig": sum(1 for r in per.values() if r["positivt_okanslig"]),
           "n_nytt_saknat_eller_rutor": c4, "villkor": {"1_underlag": v1, "2_kvot": v2, "3_teknisk_eller_tecken": v3, "4_otillforlitligt": v4}, "per_klipp": per}
    if v2 or v3 or v4:
        out["dom"] = "FÄLLD"
        out["skal"] = [k for k, b in out["villkor"].items() if b and not k.startswith("1")]
    elif v1:
        out["dom"] = "FÄLLD (otillräckligt känsligt/underlag, villkor 1)"
        out["skal"] = ["1_underlag"]
    else:
        out["dom"] = "KLARAD"
        out["skal"] = []
        if klass == "Tq":
            out["anm"] = "T? får inte kallas semantiskt validerat av detta"
    return out


def dom_G(j, V, ids, st):
    klass, eps, _, _ = FALT[j]
    per, gil = {}, 0
    for i in ids:
        v = V[i]
        c = v.get("C", {}).get(j)
        diff = {n: (None if (c is None or v.get(n, {}).get(j) is None) else abs(v[n][j] - c) > eps) for n in NN}
        per[i] = {"C": c, **{n: v.get(n, {}).get(j) for n in NN}, "N6": v.get("N6", {}).get(j), "over_eps": diff}
        if c is not None and all(v.get(n, {}).get(j) is not None for n in NN):
            gil += 1
    if gil < 8:
        return {"klass": klass, "eps": eps, "n_giltiga": gil, "dom": "EJ PRÖVAT (<8 giltiga klipp)", "per_klipp": per}
    perN = {n: sum(1 for i in ids if per[i]["over_eps"][n]) for n in NN}
    union = sum(1 for i in ids if any(per[i]["over_eps"][n] for n in NN))
    n6 = sum(1 for i in ids if per[i]["C"] is not None and per[i]["N6"] is not None and abs(per[i]["N6"] - per[i]["C"]) > eps)
    return {"klass": klass, "eps": eps, "n_giltiga": gil, "over_eps_per_N": perN, "over_eps_union": union, "N6_over_eps_sekundart": n6,
            "dom": "FÄLLD" if union >= 3 or any(x >= 3 for x in perN.values()) else "KLARAD", "per_klipp": per}


def dom_L(j, V, ids):
    eps = FALT[j][1]
    per, gil = {}, 0
    for i in ids:
        v = V[i]
        c = v.get("C", {}).get(j)
        rad, avv = {"C": c}, {}
        for n in NN:
            x = v.get(n, {}).get(j)
            rad[n] = x
            if c is None or x is None:
                avv[n] = None
            elif j == "e28.lufs" and n in ("N3", "N4"):
                avv[n] = abs((x - c) - (-6.0 if n == "N3" else -12.0)) > eps
            else:
                avv[n] = abs(x - c) > eps
        rad["avviker"], rad["N6"] = avv, v.get("N6", {}).get(j)
        per[i] = rad
        if c is not None and all(v.get(n, {}).get(j) is not None for n in NN):
            gil += 1
    if gil < 8:
        return {"klass": "L", "eps": eps, "n_giltiga": gil, "dom": "EJ PRÖVAT (<8 giltiga klipp)", "per_klipp": per}
    perN = {n: sum(1 for i in ids if per[i]["avviker"][n]) for n in NN}
    union = sum(1 for i in ids if any(per[i]["avviker"][n] for n in NN))
    return {"klass": "L", "eps": eps, "n_giltiga": gil, "avviker_per_N": perN, "avviker_union": union,
            "dom": "FÄLLD" if union >= 3 or any(x >= 3 for x in perN.values()) else "KLARAD", "per_klipp": per}


# ---------- grann-diagnos (endast negativ) ----------
def grannar(T, ref, V, ids, k=5):
    felt = T2_19
    ok = [j for j in felt if T.par[j].get("kalibrerad")]
    med = {j: float(np.median([T.z(j, r["v"][j]) for r in ref if r["v"].get(j) is not None])) for j in ok}

    def vec(v):
        z, ind = [], []
        for j in felt:
            val = v.get(j) if j in ok else None
            zz = T.z(j, val) if val is not None else None
            z.append(med.get(j, 0.0) if zz is None else zz)
            ind.append(1.0 if zz is None else 0.0)
        return np.array(z), np.array(ind)

    R = [(r["id"], *vec(r["v"])) for r in ref]

    def nn(vz, vi):
        d = sorted(((float(np.linalg.norm(np.concatenate([vz - rz, vi - ri]))), rid) for rid, rz, ri in R), key=lambda x: (x[0], x[1]))
        return d[:k]

    ut = {}
    for i in ids:
        rad = {}
        for n in ["C"] + NN + ["P"]:
            if n not in V[i]:
                continue
            z, ind = vec(V[i][n])
            g = nn(z, ind)
            rad[n] = {"norm": float(np.linalg.norm(z)), "granne_id": [x[1] for x in g], "avstand": [round(x[0], 4) for x in g]}
        if "C" in rad:
            for n in NN + ["P"]:
                if n in rad:
                    rad[n]["kvar_av_5"] = len(set(rad[n]["granne_id"]) & set(rad["C"]["granne_id"]))
        ut[i] = rad
    byter = {n: sum(1 for i in ids if n in ut[i] and ut[i][n].get("kvar_av_5", 5) <= 2) for n in NN}
    union = sum(1 for i in ids if any(n in ut[i] and ut[i][n].get("kvar_av_5", 5) <= 2 for n in NN))
    return {"falt": felt, "per_klipp": ut, "klipp_med_minst_3_bytta_per_N": byter, "klipp_med_minst_3_bytta_union": union,
            "dom": "FÄLLD som stabilt granninstrument" if union >= 3 else "KLARAD (ej fälld)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lage", required=True)
    a = ap.parse_args()
    ref = ladda_ref()
    T = Transform(ref)
    ts = jsonl(HER / ("test_mat.jsonl" if a.lage == "test" else "dry_test_mat.jsonl"))
    if a.lage == "test":
        ids = [x["id"] for x in json.loads((HER / "urval_las.json").read_text(encoding="utf-8"))["step2"]]
    else:
        ids = sorted({t["id"] for t in ts})
    rader, V, st = [], defaultdict(dict), defaultdict(dict)
    for t in ts:
        v, s = uttag(t)
        V[t["id"]][t["variant"]] = v
        st[t["id"]][t["variant"]] = s
        rader.append({"id": t["id"], "variant": t["variant"], "v": v})
    if a.lage == "dry":
        basids = list(ids)
        for k in range(len(basids), 12):
            src = basids[k % len(basids)]
            nid = f"{src}#{k}"
            V[nid], st[nid] = V[src], st[src]
            ids.append(nid)
    res = {"lage": a.lage, "n_ref_klipp": len(ref), "n_ref_konton": T.nk,
           "referensfalt": {j: {k: v for k, v in p.items() if k not in ("xs", "w")} for j, p in T.par.items()}}
    res["utanfor_stod"] = [{"id": t["id"], "variant": t["variant"], "falt": j, "varde": t["v"][j]} for t in rader for j in FALT if T.utanfor(j, t["v"].get(j))]
    res["fortest"] = fortest(T, ref, rader)
    res["identitet"] = identitet(V, ids)
    res["stopp_instrument"] = (not res["fortest"]["permutation_ok"]) or (not res["fortest"]["tillagg_kopia_ok"]) or bool(res["identitet"]["brott"])
    dom = {}
    for j, (klass, *_r) in FALT.items():
        dom[j] = dom_T(j, V, ids, st, T) if klass in ("Ttid", "Ttat", "Tq") else dom_L(j, V, ids) if klass == "L" else dom_G(j, V, ids, st)
    res["dom"] = dom
    res["grannar"] = grannar(T, ref, V, ids)
    out = HER / ("analys_resultat.json" if a.lage == "test" else "dry_analys_resultat.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("stopp_instrument:", res["stopp_instrument"], "| fortest:", res["fortest"])
    print("identitetsbrott:", len(res["identitet"]["brott"]))
    for j, d in dom.items():
        print(f"{j:24s} {d['klass']:5s} {d['dom']}")
    print("grannar:", res["grannar"]["dom"], res["grannar"]["klipp_med_minst_3_bytta_per_N"])


if __name__ == "__main__":
    main()
