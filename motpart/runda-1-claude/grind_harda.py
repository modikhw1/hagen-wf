"""Härdade grindar (H-serien) för scenpaket/2 – motförslag till byggsten/brygga/grindar.py.

Princip: en grind får bara mäta något som efterbehandlingen i scen_brygga.py inte redan har
tvingat fram. Därför jämför H-grindarna paketet mot oberoende underlag när det finns:
  - obs.json      (Lager 1: kamerahöjd/pitch, personetikett, bäring, pose, vid-relation)
  - recept.json   (Lager 2: vilka tagningar ett objekt är observerat i)
  - personer.json (ingestens 2D-spår per ruta, oberoende av 3D-lyftet)
och mäter varje (tagning, person) för sig, i varje ruta, i stället för en rad per tagning
och mitten-/medianvärden.

Grindar (ok=False räknas som fel, ok=None = kan inte mätas, redovisas):
  H1_objekt    objekt som recept/obs säger är observerat i tagningen finns och är synligt där
  H2_golv      andel rutor med fot under golvet (inte median)  + svävande stående kropp
  H3_sate      sittande: stol finns, bäckenet ligger över sitsens fotavtryck, rimlig sitthöjd
  H3_hallning  kroppen har den hållning etiketten säger (sittande: lår nära vågrätt, knä i sitthöjd;
               stående: bäckenet i benlängds höjd – fångar "på huk" som R3-IK kan skapa)
  H4_genom     genomträngning mot alla fysiska objekt oavsett synlig_ut (inkl. väggar), leder + punkter längs benen
  H5_ibild     andel rutor med överkroppen i bild (inte bara mittrutan)
  H7_2d        projicerat huvud ligger i övre halvan av ett oberoende 2D-spår (personer.json)
  H8_skelett   benlängder konstanta inom spåret och mellan personens tagningar
  H9_identitet projicerad bäring mot obs-detektionens bäring för samma etikett
  H10_kamera   kamerahöjd och pitch mot obs-mätningen (sigma ur obs)
  H11_vid      person som obs säger står/sitter vid ett bord har ett bord inom räckhåll och i armhöjd
  H12_kontinuitet  bäckenet hoppar inte (hastighet mellan rutor)
  H13_stod     föremål vilar på en bordsskiva eller på golvet
  H14_djup     kamera -> person (vågrätt) stämmer med obs-detektionens djup_m
  H15_vridning kroppens vändning (axellinjen) mot obs-detektionens vridning_deg

Kör:  scen/.venv/Scripts/python.exe motpart/runda-1-claude/grind_harda.py [klipp ...]
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
sys.path.insert(0, str(ROT / "byggsten/brygga"))
import grindar as G  # noqa: E402  (återanvänder proj/inne/kamera/horn – ändras inte)

INGEST = {
    "guacamole": "e-dialog-guacamole-tagningar",
    "gelato": "kand-kennysgelato-tagningar",
    "asketch": "a-sketch-servering-tagningar",
    "notan": "notan-tagningar",
}

# Gränser. Varje gräns anges med sin motivering; marginal mot baslinjen redovisas i GRINDAR-MUTATION.md.
GRANS_H = dict(
    golv_m=-0.05, golv_andel=0.10,          # samma golvgräns som G2, men andel rutor i stället för median
    svav_m=0.15, svav_andel=0.25,           # stående: lägsta led > 15 cm över golvet i >25 % av rutorna
    sate_xy_m=0.10, sate_andel=0.80,        # bäcken inom sitsens fotavtryck + 10 cm i >=80 % av rutorna
    sate_min_m=0.02, sate_max_m=0.20,       # som G3
    sitthojd=(0.30, 0.85),                  # sitsens överyta: låg stol .. barstol
    lar_sitt_max_deg=45.0, kna_sitt_min_m=0.30,  # sittande på stol: lår nära vågrätt och knä i sitthöjd
    backen_sta_min=0.90,                    # stående: bäckenhöjd / (lår+skenben); normalt ~1.1, på huk < 0.8
    genom_andel=0.10,
    ibild_led=0.70, ibild_andel=0.90,
    huvud_andel=0.70,                       # 2D: andel rutor där projicerat huvud ligger i övre halvan av ett 2D-spår
    ben_cv_max=0.05, ben_kvot_max=0.12,     # benlängd: variationskoefficient inom spår, avvikelse mellan spår
    baring_min_deg=6.0, baring_sigma=4.0,   # |Δbäring| <= max(6°, 4σ)
    kamera_sigma=3.0,                       # |Δhöjd|, |Δpitch| <= 3σ ur obs
    vid_m=0.80,                             # horisontellt avstånd bäcken/handled -> bordets fotavtryck
    vid_topp=(-0.30, -0.15),                # bordsskivan mellan (bäcken - 0.30) och (nacke - 0.15): armar kan vila där
    stod_m=0.05,                            # föremål: botten högst 5 cm från bordsskiva/golv som bär det
    djup_sigma=3.0, djup_min_m=0.30,
    vridning_sigma=3.0, vridning_min_deg=60.0,  # axellinjens vändning mot obs vridning_deg (σ = 20°)        # kamera->bröst vågrätt avstånd mot obs djup_m: |Δ| <= max(3σ, 0.30 m)
    hopp_m_s=8.0,                           # bäckenhastighet mellan rutor (sprint ~8 m/s; baslinjens max 6.1)
)
OVERKROPP = G.OVERKROPP
BEN = [("c_spine0", "c_spine2"), ("c_spine2", "c_neck"), ("c_neck", "c_head"),
       ("l_clavicle", "l_uparm"), ("l_uparm", "l_lowarm"), ("l_lowarm", "l_wrist"),
       ("r_clavicle", "r_uparm"), ("r_uparm", "r_lowarm"), ("r_lowarm", "r_wrist"),
       ("l_upleg", "l_lowleg"), ("l_lowleg", "l_foot"), ("r_upleg", "r_lowleg"), ("r_lowleg", "r_foot")]
FYSISKA = ("bord", "stol", "foremal", "dorr", "vagg")


# ----------------------------------------------------------------------------- kontext
def las_kontext(klipp: str, obs=None, recept=None) -> dict:
    """Oberoende underlag för klippet. obs/recept kan skickas in (läge b: muterade indata)."""
    ut = ROT / "forvarld_karna/ut" / klipp
    if obs is None:
        obs = json.loads((ut / "obs.json").read_text(encoding="utf-8"))
    if recept is None:
        recept = json.loads((ut / "recept.json").read_text(encoding="utf-8"))
    ing = ROT / "scen/3d/ingest/ut" / INGEST[klipp]
    spar = {}
    for k in obs["klipp"]:
        f = ing / k["klipp"].upper() / "personer.json"
        spar[k["klipp"]] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return dict(klipp=klipp, obs=obs, recept=recept, spar2d=spar)


# ----------------------------------------------------------------------------- hjälp
def _X(spar):
    n = len(spar["rutor"])
    return np.array([r[1:] for r in spar["rutor"]], float).reshape(n, -1, 3) / 1000.0, [r[0] for r in spar["rutor"]]


def _fotavtryck_avstand(xy, o):
    """Horisontellt avstånd från punkter (N,2) till objektets roterade fotavtryck (0 inuti)."""
    p = np.array(o["pos"][:2]); m = np.array(o["matt"][:2]) / 2; rz = o["rot"][2]
    R = np.array([[math.cos(rz), -math.sin(rz)], [math.sin(rz), math.cos(rz)]])
    lok = (np.asarray(xy) - p) @ R
    d = np.maximum(np.abs(lok) - m, 0.0)
    return np.linalg.norm(d, axis=-1)


def _iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = w * h
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / max(u, 1e-9)


def _pitch_deg(q):
    R = G.quat_till_mat(q)
    fram = R @ np.array([0.0, 0.0, -1.0])
    return math.degrees(math.asin(max(-1.0, min(1.0, fram[2]))))


def _det_for(kl_obs, pid, alla_pid):
    """obs-detektion för etiketten pid i tagningen. 'okand' tilldelas den enda person som inte har egen etikett."""
    dets = [d for d in kl_obs["detektioner"] if d["klass"] == "person"]
    d = next((d for d in dets if d["nyckel"] == f"person:{pid}"), None)
    if d is not None:
        return d
    egna = {f"person:{q}" for q in alla_pid}
    rest = [d for d in dets if d["nyckel"] not in egna]
    return rest[0] if len(rest) == 1 else None


# ----------------------------------------------------------------------------- mätning
def mat(paket: dict, ktx: dict) -> list[dict]:
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    L = {n: i for i, n in enumerate(paket["leder"])}
    golv = paket.get("golv_z", 0.0)
    obj = paket["objekt"]
    bas = {o["id"]: o for o in obj if ":" not in o["id"]}
    obs_k = {k["klipp"]: k for k in ktx["obs"]["klipp"]}
    rec_noder = {n["id"]: n for n in ktx["recept"]["noder"]}
    g = GRANS_H
    rader = []

    # benlängder per person över alla spår (för H8 mellan tagningar)
    ben_med = {}
    for pid, spl in paket["rorelse"].items():
        for sp in spl:
            X, _ = _X(sp)
            ben_med[(pid, sp["tagning"])] = np.array([np.median(np.linalg.norm(X[:, L[b]] - X[:, L[a]], axis=1)) for a, b in BEN])

    for t in paket["tagningar"]:
        sid = t["id"]; a0, b0 = t["ut"]; mitt = (a0 + b0) // 2
        kl = obs_k.get(sid)
        # ---- H1 per tagning: observerade objekt finns och syns
        saknas = []
        for nid, n in rec_noder.items():
            if n["klass"] in ("person",) or sid not in (n.get("evidence_shots") or []):
                continue
            o = bas.get(nid)
            if o is None:
                saknas.append(f"{nid}:saknas")
            elif not G.synlig(o, mitt):
                saknas.append(f"{nid}:dold")
        # ---- H10 per tagning: kamera mot obs
        h10 = dict(ok=None)
        if kl is not None:
            nk = t["kamera"]["nycklar"]
            z = float(np.median([k[3] for k in nk])); pit = float(np.median([_pitch_deg(k[4:8]) for k in nk]))
            hv, hs = kl["kamera"]["hojd_m"]["v"], kl["kamera"]["hojd_m"]["s"]
            pv, ps = kl["kamera"]["pitch_deg"]["v"], kl["kamera"]["pitch_deg"]["s"]
            dz, dp = (z - hv) / hs, (pit - pv) / ps
            h10 = dict(ok=bool(abs(dz) <= g["kamera_sigma"] and abs(dp) <= g["kamera_sigma"]),
                       hojd_m=round(z, 3), obs_hojd=hv, dz_sigma=round(dz, 2), pitch=round(pit, 1), obs_pitch=pv, dp_sigma=round(dp, 2))
        # ---- H13 per tagning: föremål vilar på ett bord eller på golvet
        svavar = []
        for o in obj:
            if o["typ"] != "foremal" or not G.synlig(o, mitt):
                continue
            botten = o["pos"][2] - o["matt"][2] / 2
            bar = abs(botten - golv) <= g["stod_m"]
            for b in obj:
                if b["typ"] == "bord" and _fotavtryck_avstand(np.array([o["pos"][:2]]), b)[0] == 0.0:
                    bar = bar or abs(botten - (b["pos"][2] + b["matt"][2] / 2)) <= g["stod_m"]
            if not bar:
                svavar.append(o["id"])
        h13 = dict(ok=not svavar, svavar=svavar) if any(o["typ"] == "foremal" for o in obj) else dict(ok=None)
        bas_rad = dict(tagning=sid, H1_objekt=dict(ok=not saknas, fel=saknas), H10_kamera=h10, H13_stod=h13)

        spar_i_t = [(pid, sp) for pid, spl in paket["rorelse"].items() for sp in spl if sp["tagning"] == sid]
        if not spar_i_t:
            rader.append(dict(bas_rad, person=None))
            continue
        alla_pid = [pid for pid, _ in spar_i_t]
        for pid, sp in spar_i_t:
            X, U = _X(sp)
            T = len(U)
            pinfo = next((p for p in t["personer"] if p["id"] == pid), {})
            pose = (paket["personer"].get(pid) or {}).get("pose")
            det = _det_for(kl, pid, alla_pid) if kl else None
            pose_t = (det or {}).get("pose") or pose
            rad = dict(bas_rad, person=pid, pose=pose_t)

            # H2 golv: andel rutor under golvet + svävande stående
            fot = X[:, [L[n] for n in G.FOT if n in L], 2].min(axis=1)
            under = float((fot < golv + g["golv_m"]).mean())
            lagst = X[:, :, 2].min(axis=1)
            svav = float((lagst > golv + g["svav_m"]).mean()) if pose_t == "staende" else 0.0
            rad["H2_golv"] = dict(ok=bool(under <= g["golv_andel"] and svav <= g["svav_andel"]),
                                  under_andel=round(under, 3), svav_andel=round(svav, 3))

            # H3 hållning: lårvinkel och knähöjd (sittande), bäckenhöjd/benlängd (stående)
            vink = []
            for s_ in ("l", "r"):
                v = X[:, L[f"{s_}_lowleg"]] - X[:, L[f"{s_}_upleg"]]
                vink.append(np.degrees(np.arcsin(np.clip(np.abs(v[:, 2]) / np.maximum(np.linalg.norm(v, axis=1), 1e-6), 0, 1))))
            lar = float(np.median(np.mean(vink, axis=0)))
            kna = float(np.median((X[:, L["l_lowleg"], 2] + X[:, L["r_lowleg"], 2]) / 2) - golv)
            benl = float(np.median(np.linalg.norm(X[:, L["l_lowleg"]] - X[:, L["l_upleg"]], axis=1))
                         + np.median(np.linalg.norm(X[:, L["l_foot"]] - X[:, L["l_lowleg"]], axis=1)))
            bkv = float((np.median(X[:, L["c_spine0"], 2]) - golv) / max(benl, 1e-6))
            if pose_t == "sittande":
                ok_h = lar <= g["lar_sitt_max_deg"] and kna >= g["kna_sitt_min_m"]
            elif pose_t == "staende":
                ok_h = bkv >= g["backen_sta_min"]
            else:
                ok_h = None
            rad["H3_hallning"] = dict(ok=ok_h, lar_deg=round(lar, 1), kna_z=round(kna, 3), backen_benlangd=round(bkv, 3))

            # H3 säte (bara sittande)
            if pose_t == "sittande":
                ank = pinfo.get("ankare") or f"stol_{pid}"
                st = bas.get(ank)
                if st is None or st.get("typ") != "stol":
                    rad["H3_sate"] = dict(ok=False, fel=f"sittande utan stol ({ank})")
                else:
                    topp = st["pos"][2] + st["matt"][2] / 2
                    hoj = float(np.median(X[:, L["c_spine0"], 2]) - topp)
                    dxy = _fotavtryck_avstand(X[:, L["c_spine0"], :2], st)
                    inom = float((dxy <= g["sate_xy_m"]).mean())
                    ok3 = (g["sate_min_m"] <= hoj <= g["sate_max_m"]) and inom >= g["sate_andel"] and g["sitthojd"][0] <= topp <= g["sitthojd"][1]
                    rad["H3_sate"] = dict(ok=bool(ok3), backen_over_sits_m=round(hoj, 3), inom_sits=round(inom, 2), sitthojd=round(topp, 3))
            else:
                rad["H3_sate"] = dict(ok=None)

            # H4 genomträngning mot alla fysiska objekt, oavsett synlig_ut. Leder + 3 punkter per ben,
            # så att en tunn skiva (6–14 cm) mellan två leder inte slinker igenom.
            P = np.concatenate([X] + [X[:, [L[a] for a, _ in BEN]] * (1 - f) + X[:, [L[b] for _, b in BEN]] * f
                                      for f in (0.25, 0.5, 0.75)], axis=1)
            nb = len(BEN)
            undantag = [L[n] for n in ("c_spine0", "l_upleg", "r_upleg")]
            undantag += [X.shape[1] + k * nb + i for k in range(3) for i, (a, b) in enumerate(BEN)
                         if (a, b) in (("c_spine0", "c_spine2"), ("l_upleg", "l_lowleg"), ("r_upleg", "r_lowleg"))]
            traff = np.zeros(T, bool); vem = {}
            for o in obj:
                if o["typ"] not in FYSISKA:
                    continue
                ins = G.inne(P, o)
                if o["id"] == pinfo.get("ankare"):
                    ins[:, undantag] = False
                h = ins.any(axis=1)
                if h.any():
                    vem[o["id"]] = round(float(h.mean()), 3)
                traff |= h
            rad["H4_genom"] = dict(ok=bool(traff.mean() <= g["genom_andel"]), andel=round(float(traff.mean()), 3),
                                   varst=sorted(vem.items(), key=lambda kv: -kv[1])[:3])

            # H5 i bild i alla rutor, H7 2D mot ingestens spår, H9 bäring
            ok_ix = [L[n] for n in OVERKROPP]
            ibild = []; ious = []; huvud_i = []; baringar = []
            spar2d = ktx["spar2d"].get(sid, {})
            hix = L["c_head"]
            for i, u in enumerate(U):
                kam = G.kamera(t, u)
                uv, d = G.proj(X[i], kam, W, H, S)
                inn = (uv[:, 0] >= 0) & (uv[:, 0] <= W) & (uv[:, 1] >= 0) & (uv[:, 1] <= H) & (d > 0)
                ibild.append(inn[ok_ix].mean() >= g["ibild_led"])
                c = (X[i, L["c_spine2"]] - kam[0]) @ kam[1]
                baringar.append(math.degrees(math.atan2(c[0], max(-c[2], 1e-6))))
                lok = str(u - a0)
                kand = [np.array(v[lok], float) for v in spar2d.values() if lok in v]
                if kand:
                    hu, hv = uv[hix]
                    traff = False
                    for b in kand:
                        bw, bh = b[2] - b[0], b[3] - b[1]
                        if d[hix] > 0 and b[0] - 0.15 * bw <= hu <= b[2] + 0.15 * bw and b[1] - 0.15 * bh <= hv <= b[1] + 0.5 * bh:
                            traff = True
                    huvud_i.append(traff)
                    if (d > 0).all():
                        box = G.ruta_box(uv)
                        ious.append(max(_iou(box, b) for b in kand))
            andel_ibild = float(np.mean(ibild))
            rad["H5_ibild"] = dict(ok=bool(andel_ibild >= g["ibild_andel"]), andel_rutor=round(andel_ibild, 3))
            if huvud_i:
                ah = float(np.mean(huvud_i))
                rad["H7_2d"] = dict(ok=bool(ah >= g["huvud_andel"]), huvud_i_spar=round(ah, 3),
                                    iou_info=round(float(np.median(ious)), 3) if ious else None, rutor=len(huvud_i))
            else:
                rad["H7_2d"] = dict(ok=None, notis="inget 2D-spår i tagningen")
            if det is not None:
                db = float(np.median(baringar)) - det["bearing_deg"]["v"]
                tol = max(g["baring_min_deg"], g["baring_sigma"] * det["bearing_deg"]["s"])
                rad["H9_identitet"] = dict(ok=bool(abs(db) <= tol), d_baring_deg=round(db, 1), tol=tol, obs=det["nyckel"])
            else:
                rad["H9_identitet"] = dict(ok=False, fel=f"ingen obs-detektion för {pid} i {sid}")

            # H8 skelett: inom spår + mot personens övriga tagningar
            bl = np.stack([np.linalg.norm(X[:, L[b]] - X[:, L[a]], axis=1) for a, b in BEN], axis=1)
            cv = float((bl.std(axis=0) / np.maximum(np.median(bl, axis=0), 1e-6)).max())
            andra = [v for (q, s), v in ben_med.items() if q == pid and s != sid]
            kvot = 0.0
            if andra:
                ref = np.median(np.array(andra), axis=0)
                kvot = float(np.max(np.abs(ben_med[(pid, sid)] / np.maximum(ref, 1e-6) - 1)))
            rad["H8_skelett"] = dict(ok=bool(cv <= g["ben_cv_max"] and kvot <= g["ben_kvot_max"]), cv_max=round(cv, 3), kvot_max=round(kvot, 3))

            # H11 vid: obs säger "vid bord" -> ett bord observerat i tagningen inom räckhåll och i armhöjd
            if det is not None and det.get("vid"):
                bord = [bas[n] for n, nn in rec_noder.items() if nn["klass"] == "bord" and sid in (nn.get("evidence_shots") or []) and n in bas]
                if not bord:
                    rad["H11_vid"] = dict(ok=False, fel="obs: vid bord, men inget bord i paketet")
                else:
                    pkt = X[:, [L["c_spine0"], L["l_wrist"], L["r_wrist"]], :2].reshape(-1, 2)
                    avst = {o["id"]: float(np.median(np.sort(_fotavtryck_avstand(pkt, o).reshape(T, 3), axis=1)[:, 0])) for o in bord}
                    nb = min(avst, key=avst.get); ob = bas[nb]
                    topp = ob["pos"][2] + ob["matt"][2] / 2
                    lo = float(np.median(X[:, L["c_spine0"], 2])) + g["vid_topp"][0]
                    hi = float(np.median(X[:, L["c_neck"], 2])) + g["vid_topp"][1]
                    rad["H11_vid"] = dict(ok=bool(avst[nb] <= g["vid_m"] and lo <= topp <= hi), bord=nb, avstand_m=round(avst[nb], 3),
                                          topp_z=round(topp, 3), armhojd=[round(lo, 3), round(hi, 3)])
            else:
                rad["H11_vid"] = dict(ok=None)

            # H14 djup: kamera -> bröst (vågrätt) mot obs-detektionens djup_m
            if det is not None:
                dd = [float(np.linalg.norm((X[i, L["c_spine2"]] - G.kamera(t, u)[0])[:2])) for i, u in enumerate(U)]
                dm = float(np.median(dd)); dv, ds = det["djup_m"]["v"], det["djup_m"]["s"]
                tol = max(g["djup_sigma"] * ds, g["djup_min_m"])
                rad["H14_djup"] = dict(ok=bool(abs(dm - dv) <= tol), djup_m=round(dm, 3), obs=dv, tol=round(tol, 3))
            else:
                rad["H14_djup"] = dict(ok=None)

            # H15 vridning: kroppens vändning mot kameran (axellinjen) mot obs-detektionens vridning_deg
            if det is not None and det.get("vridning_deg"):
                vv = []
                for i, u in enumerate(U):
                    ax = X[i, L["r_uparm"]] - X[i, L["l_uparm"]]
                    fr = np.cross(ax, [0.0, 0.0, 1.0])[:2]
                    mk = (G.kamera(t, u)[0] - X[i, L["c_spine2"]])[:2]
                    vv.append(math.atan2(fr[0] * mk[1] - fr[1] * mk[0], fr[0] * mk[0] + fr[1] * mk[1]))
                medel = math.degrees(math.atan2(np.mean(np.sin(vv)), np.mean(np.cos(vv))))
                dv = (medel - det["vridning_deg"]["v"] + 180.0) % 360.0 - 180.0
                tol = max(g["vridning_sigma"] * det["vridning_deg"]["s"], g["vridning_min_deg"])
                rad["H15_vridning"] = dict(ok=bool(abs(dv) <= tol), d_vridning_deg=round(dv, 1), tol=tol)
            else:
                rad["H15_vridning"] = dict(ok=None)

            # H12 kontinuitet: bäckenets hastighet mellan sparade rutor
            fps = paket["tidsbas"]["fps"]
            if T > 1:
                du = np.maximum(np.diff(U), 1) / fps
                v = np.linalg.norm(np.diff(X[:, L["c_spine0"]], axis=0), axis=1) / du
                vmax = float(v.max())
                rad["H12_kontinuitet"] = dict(ok=bool(vmax <= g["hopp_m_s"]), vmax_m_s=round(vmax, 2))
            else:
                rad["H12_kontinuitet"] = dict(ok=None)
            rader.append(rad)
    return rader


H_GRINDAR = ["H1_objekt", "H2_golv", "H3_sate", "H3_hallning", "H4_genom", "H5_ibild", "H7_2d",
             "H8_skelett", "H9_identitet", "H10_kamera", "H11_vid", "H12_kontinuitet", "H13_stod", "H14_djup", "H15_vridning"]
PER_TAGNING = ("H1_objekt", "H10_kamera", "H13_stod")


def sammanfatta(rader) -> dict:
    """Fel per grind. H1/H10 är per tagning och räknas en gång per tagning."""
    ut = {}
    for k in H_GRINDAR:
        if k in PER_TAGNING:
            sett = {}
            for r in rader:
                sett[r["tagning"]] = r.get(k, {}).get("ok")
            ut[k] = sum(1 for v in sett.values() if v is False)
        else:
            ut[k] = sum(1 for r in rader if r.get(k, {}).get("ok") is False)
    return ut


def main():
    klipp = sys.argv[1:] or list(INGEST)
    for k in klipp:
        p = json.loads((ROT / "forvarld_karna/ut" / k / "paket.json").read_text(encoding="utf-8"))
        rader = mat(p, las_kontext(k))
        print(f"\n### {k}  fel per H-grind: {sammanfatta(rader)}")
        for r in rader:
            fel = {kk: {x: y for x, y in r[kk].items() if x != "ok"} for kk in H_GRINDAR if r.get(kk, {}).get("ok") is False}
            print(f"  {r['tagning']} {r.get('person')}: " + ("ok" if not fel else json.dumps(fel, ensure_ascii=False)))


if __name__ == "__main__":
    main()
