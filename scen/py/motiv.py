"""Rörelsebiblioteket: fönster om 16 bildrutor (1,6 s vid 10 fps) per spårad person ur bankklippen.
Normaliseras (axelmitt, kroppsskala), klustras med k-means till K motiv, och kalibreras mot klipp som hålls utanför.

Närhet: score = 100 * (1 - 0.2 * d / d90). d = avstånd till närmaste verkliga fönster i träningsdelen,
d90 = 90:e percentilen av samma avstånd för osedda verkliga fönster. 80 = lika nära som 90 % av verkliga rörelser.

Skriver data/bibliotek/motiv.json (motiven) och data/bibliotek/referens.json (urval för närhet i webbläsaren).
"""
import json, glob, random, sys
from pathlib import Path
import numpy as np

ROT = Path(__file__).resolve().parent.parent
K = int(sys.argv[1]) if __name__ == "__main__" and len(sys.argv) > 1 else 24
T = 16
LED = [0, 5, 6, 7, 8, 9, 10, 11, 12]  # näsa, axlar, armbågar, handleder, höfter
NAMN_LED = ["nasa", "v_axel", "h_axel", "v_armbage", "h_armbage", "v_hand", "h_hand", "v_hoft", "h_hoft"]
random.seed(7); np.random.seed(7)


def normalisera(kps):
    """kps: T x 17 x 3 (x, y, conf) -> (T x 9 x 2 pose, T x 3 rörelse [dx, dy, dskala], mask T x 9)"""
    kps = np.array(kps, dtype=float)
    ax = (kps[:, 5, :2] + kps[:, 6, :2]) / 2
    axb = np.linalg.norm(kps[:, 5, :2] - kps[:, 6, :2], axis=1)
    nax = np.linalg.norm(kps[:, 0, :2] - ax, axis=1)
    sk = np.maximum(axb, nax * 1.4)
    sk = np.where(sk < 1e-3, np.nan, sk)
    sk = np.nan_to_num(sk, nan=np.nanmedian(sk) if np.isfinite(np.nanmedian(sk)) else 0.1)
    pose = (kps[:, LED, :2] - ax[:, None, :]) / sk[:, None, None]
    mask = kps[:, LED, 2] > 0.4
    # fyll i saknade leder med medel av synliga i fönstret, annars en vilopose
    vila = np.array([[0, -0.8], [-0.5, 0], [0.5, 0], [-0.6, 0.7], [0.6, 0.7], [-0.6, 1.3], [0.6, 1.3], [-0.35, 1.6], [0.35, 1.6]])
    for j in range(len(LED)):
        m = mask[:, j]
        if m.any():
            pose[~m, j] = pose[m, j].mean(0)
        else:
            pose[:, j] = vila[j]
    rel = np.zeros((len(kps), 3))
    rel[1:, :2] = np.diff(ax, axis=0) / sk[1:, None]
    rel[1:, 2] = np.diff(np.log(sk))
    return pose, rel, mask


def vektor(pose, rel):
    return np.concatenate([pose.reshape(len(pose), -1), rel * 12], axis=1).ravel()  # rörelsen viktas upp


def fonster_ur(spar):
    """alla fönster om T bildrutor per spår-id, inom en och samma scen"""
    ut = []
    sc = spar["scener"]
    for s in sc:
        bs = [b for b in spar["bilder"] if s["start"] <= b["t"] < s["slut"]]
        spar_id = {}
        for k, b in enumerate(bs):
            for p in b["p"]:
                if p["id"] is None: continue
                spar_id.setdefault(p["id"], []).append((k, p))
        for pid, lst in spar_id.items():
            # sammanhängande följder
            run = [lst[0]]
            for x in lst[1:] + [(None, None)]:
                if x[0] is not None and x[0] == run[-1][0] + 1:
                    run.append(x); continue
                for st in range(0, len(run) - T + 1, T // 2):
                    w = run[st:st + T]
                    kps = [q[1]["kp"] for q in w]
                    if np.mean([np.mean([kk[2] > 0.4 for kk in np.array(k_)[[5, 6]]]) for k_ in kps]) < 0.6:
                        continue  # för lite överkropp syns
                    ut.append({"t": bs[w[0][0]]["t"], "pid": pid, "kps": kps,
                               "box_h": float(np.median([q[1]["box"][3] - q[1]["box"][1] for q in w]))})
                if x[0] is not None: run = [x]
    return ut


if __name__ == "__main__":
    filer = sorted(glob.glob(str(ROT / "data" / "bank" / "*" / "spar.json")))
    klipp = [Path(f).parent.name for f in filer]
    random.shuffle(klipp)
    hall = set(klipp[: max(4, len(klipp) // 5)])
    X, info = [], []
    for f in filer:
        namn = Path(f).parent.name
        for w in fonster_ur(json.load(open(f))):
            pose, rel, mask = normalisera(w["kps"])
            X.append(vektor(pose, rel)); info.append({"klipp": namn, "t": w["t"], "hall": namn in hall, "box_h": w["box_h"],
                                                     "pose": pose, "rel": rel})
    X = np.array(X); hm = np.array([i["hall"] for i in info])
    Xtr, Xho = X[~hm], X[hm]
    print("fönster", len(X), "träning", len(Xtr), "osedda", len(Xho), "klipp", len(klipp))

    # k-means (numpy)
    C = Xtr[np.random.choice(len(Xtr), K, replace=False)]
    for it in range(60):
        d = ((Xtr[:, None, :] - C[None]) ** 2).sum(-1); lab = d.argmin(1)
        C2 = np.array([Xtr[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(K)])
        if np.allclose(C, C2): break
        C = C2

    def nn(Q, R):
        out = []
        for i in range(0, len(Q), 256):
            d = np.sqrt(((Q[i:i + 256, None, :] - R[None]) ** 2).sum(-1)); out.append(d.min(1))
        return np.concatenate(out)

    d_ho = nn(Xho, Xtr)
    d90 = float(np.percentile(d_ho, 90))
    poang = lambda d: np.clip(100 * (1 - 0.2 * d / d90), 0, 100)
    print("d90", round(d90, 3), "osedda: median poäng", round(float(np.median(poang(d_ho))), 1), "andel >=80", round(float((poang(d_ho) >= 80).mean()), 3))

    # namnge motiv ur geometri: drag som avviker mot fördelningen över alla träningsfönster (percentiler)
    Ptr = [i for i in info if not i["hall"]]
    def drag(pose, rel):
        return {"hand_y": pose[:, 5:7, 1].mean(), "hand_v": np.abs(np.diff(pose[:, 5:7], axis=0)).sum(-1).mean(),
                "rx": rel[:, 0].sum(), "rs": rel[:, 2].sum(), "nasa_y": pose[:, 0, 1].mean(), "hand_x": np.abs(pose[:, 5:7, 0]).mean(),
                "kropp_v": np.abs(rel[:, :2]).sum(-1).mean()}
    DR = [drag(i["pose"], i["rel"]) for i in Ptr]
    pct = {k: (np.percentile([d[k] for d in DR], 20), np.percentile([d[k] for d in DR], 80)) for k in DR[0]}
    motiv = []
    for k in range(K):
        idx = np.where(lab == k)[0]
        if len(idx) == 0: continue
        pose = np.mean([Ptr[i]["pose"] for i in idx], 0); rel = np.mean([Ptr[i]["rel"] for i in idx], 0)
        m = {q: float(np.median([DR[i][q] for i in idx])) for q in DR[0]}
        delar = []
        if m["rx"] > pct["rx"][1]: delar.append("går_åt_höger")
        if m["rx"] < pct["rx"][0]: delar.append("går_åt_vänster")
        if m["rs"] > pct["rs"][1]: delar.append("närmar_sig")
        if m["rs"] < pct["rs"][0]: delar.append("drar_sig_undan")
        if m["hand_y"] < pct["hand_y"][0]: delar.append("händer_högt")
        if m["hand_y"] > pct["hand_y"][1]: delar.append("armar_nere")
        if m["hand_v"] > pct["hand_v"][1]: delar.append("gestikulerar")
        if m["nasa_y"] > pct["nasa_y"][1]: delar.append("böjd_framåt")
        if m["hand_x"] > pct["hand_x"][1]: delar.append("armar_ut")
        if m["kropp_v"] < pct["kropp_v"][0] and m["hand_v"] < pct["hand_v"][0]: delar.append("står_stilla")
        if not delar: delar.append("håller_fram" if m["hand_y"] < np.mean(pct["hand_y"]) else "neutral")
        motiv.append({"id": f"m{k:02d}", "namn": "+".join(delar), "antal": int(len(idx)),
                      "klipp": len(set(Ptr[i]["klipp"] for i in idx)),
                      "pose": np.round(pose, 3).tolist(), "rel": np.round(rel, 4).tolist(),
                      "spridning": round(float(np.sqrt(((Xtr[idx] - C[k]) ** 2).sum(-1)).mean()), 3)})
    motiv.sort(key=lambda m: -m["antal"])

    # negativa kontroller
    rng = np.random.default_rng(1)
    def kontroll(namn, f):
        ps = []
        for i in rng.choice(np.where(hm)[0], 120):
            pose, rel = f(info[i]["pose"].copy(), info[i]["rel"].copy())
            ps.append(vektor(pose, rel))
        sc = poang(nn(np.array(ps), Xtr)); return {"namn": namn, "median": round(float(np.median(sc)), 1), "andel_80": round(float((sc >= 80).mean()), 3)}
    def snabb(p, r, f):
        idx = np.clip((np.arange(T) * f).astype(int), 0, T - 1); return p[idx], r[idx] * f
    kontroller = [
        kontroll("osedd_verklig", lambda p, r: (p, r)),
        kontroll("speglad", lambda p, r: (p[:, [0, 2, 1, 4, 3, 6, 5, 8, 7]] * [-1, 1], r * [-1, 1, 1])),
        kontroll("baklänges", lambda p, r: (p[::-1], -r[::-1])),
        kontroll("halv_fart", lambda p, r: snabb(p, r, 0.5)),
        kontroll("dubbel_fart", lambda p, r: snabb(p, r, 2.0)),
        kontroll("brus_lätt", lambda p, r: (p + rng.normal(0, 0.08, p.shape), r)),
        kontroll("brus_kraftigt", lambda p, r: (p + rng.normal(0, 0.4, p.shape), r)),
        kontroll("leder_byta", lambda p, r: (p[:, rng.permutation(9)], r)),
        kontroll("teleport", lambda p, r: (p, r + np.r_[np.zeros((8, 3)), np.tile([[0.5, 0, 0]], (8, 1))])),
    ]
    for k in kontroller: print(k)

    (ROT / "data" / "bibliotek").mkdir(exist_ok=True)
    json.dump({"T": T, "fps": 10, "leder": NAMN_LED, "d90": round(d90, 4), "k": K, "klipp_trani": len(klipp) - len(hall),
               "kontroller": kontroller, "motiv": motiv}, open(ROT / "data" / "bibliotek" / "motiv.json", "w", encoding="utf-8"), ensure_ascii=False)
    # kontext: utsnittsklass ur personens boxhöjd (nära / halv / hel); närheten villkoras på samma klass
    kl = lambda h: "nara" if h > 0.85 else ("halv" if h > 0.5 else "hel")
    ktr = np.array([kl(i["box_h"]) for i in info])[~hm]; kho = np.array([kl(i["box_h"]) for i in info])[hm]
    sel = rng.choice(len(Xtr), min(1500, len(Xtr)), replace=False)
    d_sub = nn(Xho, Xtr[sel]); d90s = float(np.percentile(d_sub, 90))
    d90k = {}
    for k_ in ("nara", "halv", "hel"):
        a_, b_ = Xho[kho == k_], Xtr[sel][ktr[sel] == k_]
        d90k[k_] = round(float(np.percentile(nn(a_, b_), 90)), 4) if len(a_) >= 5 and len(b_) >= 5 else round(d90s, 4)
        print("kontext", k_, "träning", int((ktr[sel] == k_).sum()), "osedda", len(a_), "d90", d90k[k_])
    json.dump({"d90": round(d90s, 4), "d90_kontext": d90k, "dim": int(X.shape[1]), "kontext": ktr[sel].tolist(),
               "X": np.round(Xtr[sel], 3).ravel().tolist()},
              open(ROT / "data" / "bibliotek" / "referens.json", "w"), separators=(",", ":"))
    print("motiv", len(motiv)); [print(m["id"], m["antal"], m["klipp"], m["namn"]) for m in motiv]
