"""Steg 2: grindar. Mäter om ett scenpaket går att lita på innan det byggs.

Grindarna följer Jutsus ordning (form, proportion, djup, kontakt, kamerablick), men är mätta
mot vår data i stället för bedömda för ögat:

  G1 rum        varje synligt objekt hör till ett rum som gäller tagningen; en persons hemplats är ledig
                när personen sitter någon annanstans
  G2 golv       fötterna ligger inte under golvet (median per tagning)
  G3 säte       sittande bäcken ligger 2–20 cm över sitsen
  G4 genom      andel rutor där en led ligger inne i en möbel
  G5 i bild     andel leder inom bilden, och personens höjd i bild
  G6 skymning   möbler närmare kameran som täcker personens överkropp

Kör: scen/.venv/Scripts/python.exe byggsten/brygga/grindar.py byggsten/brygga/ut/notan/paket.json [fler paket]
Skriver <paket>_grindar.json och en jämförelsetabell i markdown till stdout.
"""
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rotation import quat_till_mat  # noqa: E402

GRANS = dict(golv_m=-0.05, sate_min_m=0.02, sate_max_m=0.20, genom_andel=0.10, ibild_andel=0.70, skymning_andel=0.30)
FOT = ("l_foot", "r_foot", "l_ball", "r_ball")
OVERKROPP = ("c_neck", "c_head", "l_uparm", "r_uparm", "c_spine2")


def horn(o):
    p = np.array(o["pos"]); m = np.array(o["matt"]) / 2; rz = o["rot"][2]
    R = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    s = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    return (s * m) @ R.T + p


def inne(x, o, krymp=0.01):
    p = np.array(o["pos"]); m = np.array(o["matt"]) / 2 - krymp; rz = o["rot"][2]
    R = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    lok = (np.asarray(x) - p) @ R
    return (np.abs(lok) <= m).all(axis=-1)


def synlig(o, u): return any(a <= u < b for a, b in o["synlig_ut"])


def kamera(t, u):
    ks = t["kamera"]["nycklar"]; k = max((k for k in ks if k[0] <= u), key=lambda k: k[0], default=ks[0])
    return np.array(k[1:4]), quat_till_mat(k[4:8]), k[8]


def proj(x, kam, W, H, sensor):
    C, R, lins = kam; c = (np.asarray(x) - C) @ R; d = -c[..., 2]
    fok = lins / sensor * W
    return c[..., :2] / np.maximum(d[..., None], 1e-6) * [fok, -fok] + [W / 2, H / 2], d


def ruta_box(uv):
    return np.array([uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max()])


def overlapp(a, b):
    w = max(0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


def mat(paket):
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    L = {n: i for i, n in enumerate(paket["leder"])}; golv = paket.get("golv_z", 0.0)
    rum = {r["id"]: r for r in paket["rum"]}; huvud = paket.get("huvudrum")
    obj = paket["objekt"]; bas = {o["id"]: o for o in obj if ":" not in o["id"]}
    rader = []
    for t in paket["tagningar"]:
        a0, b0 = t["ut"]; mitt = (a0 + b0) // 2
        # G1 rum (mitt i tagningen räcker, synlighet är styckvis konstant per tagning)
        fel = []
        for o in obj:
            if not synlig(o, mitt): continue
            R = o.get("rum", "gemensamt")
            if R not in ("gemensamt", huvud) and t["id"] not in rum[R]["tagningar"]: fel.append(o["id"].split(":")[0])
        for p in t["personer"]:
            h = paket["personer"].get(p["id"], {}).get("hemplats")
            if h and p["ankare"] and p["ankare"] != h and h in bas and synlig(bas[h], mitt): fel.append(h)
        rad = dict(tagning=t["id"], G1_rum=dict(ok=not fel, fel=sorted(set(fel))))
        for spar in (x for v in paket["rorelse"].values() for x in v if x["tagning"] == t["id"]):
            pid = next(k for k, v in paket["rorelse"].items() if spar in v)
            X = np.array([r[1:] for r in spar["rutor"]], float).reshape(len(spar["rutor"]), -1, 3) / 1000
            U = [r[0] for r in spar["rutor"]]
            fot = np.median(X[:, [L[n] for n in FOT if n in L], 2].min(axis=1))
            rad["G2_golv"] = dict(ok=bool(fot >= golv + GRANS["golv_m"]), fot_z_m=round(float(fot), 3))
            ank = next((p["ankare"] for p in t["personer"] if p["id"] == pid), None)
            sate = bas.get(ank)
            if sate and sate.get("typ") == "stol":
                topp = sate["pos"][2] + sate["matt"][2] / 2
                hoj = float(np.median(X[:, L["c_spine0"], 2]) - topp)
                rad["G3_sate"] = dict(ok=GRANS["sate_min_m"] <= hoj <= GRANS["sate_max_m"], backen_over_sits_m=round(hoj, 3))
            else:
                rad["G3_sate"] = dict(ok=None, notis=f"ankare {ank} är inget säte")
            # G4 genomträngning
            undantag = {L[n] for n in ("c_spine0", "l_upleg", "r_upleg") if n in L}
            traff = np.zeros(len(U), bool); vem = {}
            for o in obj:
                if o["typ"] in ("golv", "vagg"): continue
                vis = np.array([synlig(o, u) for u in U])
                if not vis.any(): continue
                ins = inne(X, o)
                if sate and o["id"].split(":")[0] == ank: ins[:, list(undantag)] = False
                h = ins.any(axis=1) & vis
                if h.any(): vem[o["id"]] = round(float(h.mean()), 3)
                traff |= h
            rad["G4_genom"] = dict(ok=bool(traff.mean() <= GRANS["genom_andel"]), andel=round(float(traff.mean()), 3),
                                   varst=sorted(vem.items(), key=lambda kv: -kv[1])[:3])
            # G5 i bild och G6 skymning, mitt i tagningen
            i = int(np.argmin([abs(u - mitt) for u in U])); kam = kamera(t, U[i])
            uv, d = proj(X[i], kam, W, H, S)
            ok_ix = [L[n] for n in OVERKROPP if n in L]
            inn = (uv[:, 0] >= 0) & (uv[:, 0] <= W) & (uv[:, 1] >= 0) & (uv[:, 1] <= H) & (d > 0)
            hojd = (uv[:, 1].max() - uv[:, 1].min()) / H
            rad["G5_ibild"] = dict(ok=bool(inn[ok_ix].mean() >= GRANS["ibild_andel"]), overkropp=round(float(inn[ok_ix].mean()), 2),
                                   alla_leder=round(float(inn.mean()), 2), hojd_andel=round(float(hojd), 2))
            tro = (paket.get("trohet") or {}).get(f"{t['id']}:{pid}")
            rad["G7_trohet"] = dict(ok=None if tro is None else not tro.get("flaggad"), **(tro or {"notis": "ingen trohetsmätning"}))
            ob = ruta_box(uv[ok_ix]); oyta = max(1.0, (ob[2] - ob[0]) * (ob[3] - ob[1])); pd = float(np.median(d))
            tack = {}
            for o in obj:
                if o["typ"] in ("golv", "vagg") or not synlig(o, U[i]): continue
                huv, dd = proj(horn(o), kam, W, H, S)
                if (dd <= 0.05).any() or np.median(dd) >= pd - 0.1: continue
                ov = overlapp(ruta_box(huv), ob) / oyta
                if ov > 0.02: tack[o["id"].split(":")[0]] = round(max(tack.get(o["id"].split(":")[0], 0), ov), 2)
            vst = max(tack.values(), default=0)
            rad["G6_skymning"] = dict(ok=vst <= GRANS["skymning_andel"], tackning=tack)
            rad["person"] = pid
        rader.append(rad)
    return rader


def sammanfatta(rader):
    g = ["G1_rum", "G2_golv", "G3_sate", "G4_genom", "G5_ibild", "G6_skymning", "G7_trohet"]
    return {k: sum(1 for r in rader if r.get(k, {}).get("ok") is False) for k in g}


def main():
    alla = {}
    for f in sys.argv[1:]:
        p = json.loads(Path(f).read_text(encoding="utf-8")); rader = mat(p)
        Path(f).with_name(Path(f).stem + "_grindar.json").write_text(json.dumps(dict(granser=GRANS, rader=rader), ensure_ascii=False, indent=1), encoding="utf-8")
        alla[Path(f).stem] = rader
    tecken = lambda v: "–" if v is None else ("ok" if v else "**FEL**")
    for namn, rader in alla.items():
        print(f"\n### {namn}  (fel per grind: {sammanfatta(rader)})\n")
        print("| tagning | person | G1 rum | G2 golv | G3 säte | G4 genom | G5 i bild | G6 skymning | G7 trohet |")
        print("|---|---|---|---|---|---|---|---|---|")
        for r in rader:
            g1 = r["G1_rum"]; g2 = r.get("G2_golv", {}); g3 = r.get("G3_sate", {}); g4 = r.get("G4_genom", {}); g5 = r.get("G5_ibild", {}); g6 = r.get("G6_skymning", {}); g7 = r.get("G7_trohet", {})
            print(f"| {r['tagning']} | {r.get('person','')} | {tecken(g1['ok'])} {', '.join(g1['fel'])} | {tecken(g2.get('ok'))} {g2.get('fot_z_m','')} "
                  f"| {tecken(g3.get('ok'))} {g3.get('backen_over_sits_m','')} | {tecken(g4.get('ok'))} {g4.get('andel','')} {' '.join(k.split(':')[0] for k, _ in g4.get('varst', []))} "
                  f"| {tecken(g5.get('ok'))} {g5.get('overkropp','')} | {tecken(g6.get('ok'))} {g6.get('tackning','') or ''} "
                  f"| {tecken(g7.get('ok'))} {g7.get('iou','')} |")


if __name__ == "__main__":
    main()
