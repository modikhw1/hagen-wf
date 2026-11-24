"""Lager 3, allmän version: recept + råsekvenser -> scenpaket/2 med märkt epistemik.

Ändringar mot `forvarld_karna/scen_brygga.py` (hash i `../original_kopia/SHA256_kalla.txt`), var och en prövad i `../prov/`:
- C2: kamerans lutning behålls. Rotationen byggs ur tagningens uppmätta lodlinje (gravitationen i kameraramen) och
  rumshjärnans riktning, i stället för `Euler(90, 0, yaw)` som kastade pitch och roll.
- C1: ingen kamerahöjdsklämma (0,92 m) och ingen kroppsförflyttning som bryter bildläget. Kamerahöjden kommer ur Lager 1:s
  fysiska ledtrådar och ur möbler som syns i flera tagningar (samsyn). Kroppar flyttas bara längs kamerans strålar.
- A2: R25 är borttagen. Kamerans rörelse inom tagningen mäts i bakgrunden (`kamera_bana.py`); kroppen behåller sin rörelse.
- A3: inga efterhandsflyttar som döljer fel (`_dra_in_dolda_ben_bakom_massiv_disk`, R1-döljning av möbler). Grindarna
  mäter slutpaketet. Fotkontakt-IK rör bara fötter som inte syns.
- Synlighet per led och ruta (sedd / skymd / utanför bild) och tillstånd per person och tagning (HEL, DEL, EXTREMITET,
  UTANFOR). Leder utan bildstöd är `antagen` och ritas grått; en person vars bål inte syns ritas bara med de leder som syns.
- Väggar som ingen tagning sett ritas inte (zon 3, okänt); allt antaget listas i `antaganden`.
"""
from __future__ import annotations

import datetime
import json
import math
import pathlib
import subprocess
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[3]
sys.path.insert(0, str(HIT))

import grindar  # noqa: E402
import kamera_bana  # noqa: E402
from obs_motor import kamerapunkter, leder  # noqa: E402
from rotation import mat_till_quat, quat_xyzw  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

F = np.diag([1.0, -1.0, -1.0])
LEDER_T1 = [
    "c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
    "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
    "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    "l_upleg", "l_lowleg", "l_foot", "l_ball", "r_upleg", "r_lowleg", "r_foot", "r_ball",
]
HARLEDD = {"l_hand_mitt": ("l_index1", "l_pinky1"), "r_hand_mitt": ("r_index1", "r_pinky1")}
BENLEDER = {"l_upleg", "l_lowleg", "l_foot", "l_ball", "r_upleg", "r_lowleg", "r_foot", "r_ball"}
KARNA = ("c_head", "c_neck", "l_uparm", "r_uparm", "c_spine2")
ARMAR = ("l_lowarm", "l_wrist", "l_hand_mitt", "r_lowarm", "r_wrist", "r_hand_mitt")
FOTLED_OVER_GOLV, TA_OVER_GOLV = 0.065, 0.02
SENSOR_MM = 36.0
ROLL_FARG = ["#4c8bf5", "#e06c75", "#98c379", "#d19a66", "#c678dd", "#56b6c2"]


def _r(x, n=4):
    return [round(float(v), n) for v in x]


def _n(v):
    return v / (np.linalg.norm(v) + 1e-12)


def R_ur_lod(u_cv: np.ndarray, yaw_deg_recept: float) -> np.ndarray:
    """Kamera->värld (Blender) ur gravitationen i kameraramen och rumshjärnans riktning (rotation[2] i receptet)."""
    u_b = _n(F @ u_cv)
    f_b = np.array([0.0, 0.0, -1.0])
    fh = _n(f_b - (f_b @ u_b) * u_b)
    rh = _n(np.cross(fh, u_b))
    R_tilt = np.vstack([rh, fh, u_b])
    th = math.radians(yaw_deg_recept + 90.0) - math.pi / 2
    c, s = math.cos(th), math.sin(th)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return Rz @ R_tilt


def fotkontakt_dolda(X: np.ndarray, sedd: np.ndarray, golv: float = 0.0) -> int:
    """R3 endast för fötter utan bildstöd: fot under golvet lyfts med 2-leds-IK. Synliga fötter rörs inte."""
    ix = {n: i for i, n in enumerate(LEDER_T1)}
    n = 0
    for s in ("l", "r"):
        h, k, f, b = ix[f"{s}_upleg"], ix[f"{s}_lowleg"], ix[f"{s}_foot"], ix[f"{s}_ball"]
        L1 = float(np.median(np.linalg.norm(X[:, k] - X[:, h], axis=1)))
        L2 = float(np.median(np.linalg.norm(X[:, f] - X[:, k], axis=1)))
        for t in range(len(X)):
            if sedd[t, f]:
                continue
            mal = golv + FOTLED_OVER_GOLV
            if X[t, f, 2] >= mal - 0.01:
                continue
            H, K, Ft = X[t, h].copy(), X[t, k].copy(), X[t, f].copy()
            F2 = Ft.copy()
            F2[2] = mal
            dist = min(float(np.linalg.norm(F2 - H)), L1 + L2 - 1e-4)
            u = (F2 - H) / max(float(np.linalg.norm(F2 - H)), 1e-6)
            a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2 * max(dist, 1e-6))
            hh = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
            bv = (K - H) - np.dot(K - H, u) * u
            bv = bv / np.linalg.norm(bv) if np.linalg.norm(bv) > 1e-6 else np.array([0.0, -1.0, 0.0])
            X[t, k] = H + u * a + bv * hh
            X[t, f] = H + u * dist
            X[t, b] = X[t, b] + (X[t, f] - Ft)
            X[t, b, 2] = max(X[t, b, 2], golv + TA_OVER_GOLV)
            n += 1
    return n


def hojd_samsyn(obs: Observationer, recept: Recept, matning: dict) -> tuple[dict, list]:
    """Möbler som syns i flera tagningar är en gemensam linjal: skivans höjd över golvet är densamma i alla tagningar.
    Varje tagnings kamerahöjd vägs ihop med (skivhöjd ur de andra tagningarna - skivans höjd relativt kameran)."""
    hc = {k.klipp: (k.kamera.hojd_m.v, k.kamera.hojd_m.s) for k in obs.klipp}
    det = {d.id: (k.klipp, d) for k in obs.klipp for d in k.detektioner}
    logg = []
    for n in recept.noder:
        if n.klass != "bord" or not n.kallor:
            continue
        rel = {}
        for did in n.kallor:
            if did in det and det[did][1].hojd_m is not None:
                sid, d = det[did]
                rel[sid] = (d.hojd_m.v - hc[sid][0], 0.03)
        if len(rel) < 2:
            continue
        nya = {}
        for sid, (r_k, s_r) in rel.items():
            andra = [(hc[o][0] + r_o, math.hypot(hc[o][1], s_o)) for o, (r_o, s_o) in rel.items() if o != sid]
            w = [1 / s ** 2 for _, s in andra]
            T = sum(v * wi for (v, _), wi in zip(andra, w)) / sum(w)
            sT = (1 / sum(w)) ** 0.5
            kand = T - r_k
            s_k = math.hypot(sT, s_r)
            h0, s0 = hc[sid]
            w0, w1 = 1 / s0 ** 2, 1 / s_k ** 2
            nya[sid] = ((h0 * w0 + kand * w1) / (w0 + w1), (1 / (w0 + w1)) ** 0.5)
            logg.append(dict(mobel=n.id, tagning=sid, fore=round(h0, 3), ur_mobel=round(kand, 3), efter=round(nya[sid][0], 3),
                             sigma=round(nya[sid][1], 3)))
        hc.update(nya)
    return hc, logg


def _box_inne(uv, box, marg=0.08):
    x0, y0, x1, y1 = box
    mw, mh = (x1 - x0) * marg, (y1 - y0) * marg
    return (uv[..., 0] >= x0 - mw) & (uv[..., 0] <= x1 + mw) & (uv[..., 1] >= y0 - mh) & (uv[..., 1] <= y1 + mh)


def projicera(X, R, C, f, W, H):
    """X (…,3) i världen -> (u, v) och djup genom en Blender-kamera (R kamera->värld, C läge)."""
    c = (X - C) @ R
    d = -c[..., 2]
    uv = c[..., :2] / np.maximum(d[..., None], 1e-6) * np.array([f, -f]) + np.array([W / 2.0, H / 2.0])
    return uv, d


def kompilera_scenpaket(ingest: pathlib.Path, obs: Observationer, recept: Recept, matning: dict, ut_mapp: pathlib.Path,
                        steg: int = 1, cache: pathlib.Path | None = None) -> pathlib.Path:
    IX = leder()
    N, fps = recept.rutor, recept.fps
    W, H = obs.klipp[0].kamera.bild_px
    golv_z = 0.0
    beslut, antaganden = [], []
    hc_ny, samsyn_logg = hojd_samsyn(obs, recept, matning)
    for r in samsyn_logg:
        beslut.append(dict(regel="R_hojd_samsyn", **r))

    kam_map = {c.klipp: c for c in recept.kameror}
    nod_av_det = {}
    for n in recept.noder:
        for did in (n.kallor or []):
            nod_av_det[did] = n
    tagningar, rorelse, personer_meta, synlighet = [], {}, {}, {}
    kroppar: dict[str, dict[str, np.ndarray]] = {}
    sedd_per: dict[str, dict[str, np.ndarray]] = {}
    roll_ordning = []

    for k_obs in obs.klipp:
        sid = k_obs.klipp
        S = sid.upper()
        S_dir = ingest / S
        a0, b0 = k_obs.rutor
        cam_nod = kam_map.get(sid)
        if cam_nod is None:
            beslut.append(dict(regel="R_tagning_utan_kamera", tagning=sid, orsak="rumshjärnan placerade tagningen i ett annat rum"))
            continue
        m = matning["tagningar"][S]
        f_px, kappa = float(m["f_px"]), float(m["kappa"])
        u_cv = np.array(m["lodlinje"]["u_opencv"])
        R_ref = R_ur_lod(u_cv, cam_nod.rotation[2])
        h_c, h_s = hc_ny[sid]
        C_ref = np.array([cam_nod.position[0], cam_nod.position[1], h_c])
        lins_mm = round(SENSOR_MM * f_px / W, 3)
        T = b0 - a0

        bana = None
        bf = cache / f"bana_{S}.npz" if cache else None
        if bf is not None and bf.exists():
            z = np.load(bf, allow_pickle=True)
            bana = dict(statisk=bool(z["statisk"]), R_rel=z["R_rel"], C_rel=z["C_rel"], info=json.loads(str(z["info"])))
        else:
            b = kamera_bana.kamerabana(S_dir, ingest / "klipp" / f"{S}.mp4", f_px, kappa, W, H, T, int(m["ref_ruta"]))
            info = {k: v for k, v in b.items() if k not in ("R_rel", "C_rel")}
            if "R_rel" not in b:
                b["R_rel"] = np.tile(np.eye(3), (T, 1, 1)); b["C_rel"] = np.zeros((T, 3))
            bana = dict(statisk=b["statisk"], R_rel=b["R_rel"], C_rel=b["C_rel"], info=info)
            if bf is not None:
                bf.parent.mkdir(parents=True, exist_ok=True)
                np.savez(bf, statisk=b["statisk"], R_rel=b["R_rel"], C_rel=b["C_rel"], info=json.dumps(info, default=str))
        if bana["statisk"]:
            Rt = np.tile(R_ref, (T, 1, 1))
            Ct = np.tile(C_ref, (T, 1))
        else:
            Rt = np.einsum("ij,njk->nik", R_ref, bana["R_rel"][:T])
            Ct = C_ref[None] + bana["C_rel"][:T] @ R_ref.T
        beslut.append(dict(regel="R25c_kamerabana_ur_bakgrund", tagning=sid, **{k: v for k, v in bana["info"].items() if k != "orsak"}, statisk_beslut=bana["statisk"]))

        pf = S_dir / "personer.json"
        boxar = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else {}
        M = np.load(S_dir / "masker.npy") if (S_dir / "masker.npy").exists() else None
        tagn_personer = []
        kroppar[sid], sedd_per[sid] = {}, {}
        pers_mat = {p["spar"]: p for p in m["personer"]}
        for d in [d for d in k_obs.detektioner if d.klass == "person"]:
            spar = d.spar
            fil = S_dir / f"sekvens_{spar}.npz"
            if not fil.exists():
                continue
            q = np.load(fil)
            pm = pers_mat.get(spar, {})
            s_i = float(pm.get("s", 1.0))
            if d.unik:
                pid = d.nyckel.split(":")[1]
            else:
                nod = nod_av_det.get(d.id)
                pid = f"{nod.id}" if nod is not None else f"gast_{sid}_{spar}"
            if pid not in roll_ordning:
                roll_ordning.append(pid)
            J = kamerapunkter(q, kappa, s_i)  # (Tq, 127, 3) Blenders kameraram
            nq = len(J)
            fi = np.minimum(np.arange(T), nq - 1)
            Jw = np.einsum("tij,tkj->tki", Rt, J[fi]) + Ct[:, None, :]
            hi = IX["c_head"]
            X = np.zeros((T, len(LEDER_T1), 3))
            for j, nm in enumerate(LEDER_T1):
                if nm == "huvud_upp" or nm == "nasa_mal":
                    continue
                kall = HARLEDD.get(nm, (nm,))
                X[:, j] = Jw[:, [IX[c] for c in kall]].mean(axis=1)
            for t in range(T):
                Mh = Rt[t] @ quat_xyzw(q["pose"][fi[t], hi, 3:7]) @ quat_xyzw(q["rest"][hi, 3:7]).T
                X[t, LEDER_T1.index("huvud_upp")] = Jw[t, hi] + Mh @ np.array([0.0, 0.10, 0.0])
                X[t, LEDER_T1.index("nasa_mal")] = Jw[t, hi] + Mh @ np.array([0.0, 0.03, 0.12])

            # synlighet per led och ruta: i bild, i egen YOLO-ruta, i personmasken, detekterad; ben kräver ben_synliga
            uv, dj = np.zeros((T, len(LEDER_T1), 2)), np.zeros((T, len(LEDER_T1)))
            for t in range(T):
                uv[t], dj[t] = projicera(X[t], Rt[t], Ct[t], f_px, W, H)
            ibild = (uv[..., 0] >= 0) & (uv[..., 0] < W) & (uv[..., 1] >= 0) & (uv[..., 1] < H) & (dj > 0.05)
            sedd = np.zeros((T, len(LEDER_T1)), bool)
            kand = q["kand"].astype(bool)[fi]
            ben = q["ben_synliga"].astype(bool)[fi]
            bx = boxar.get(spar, {})
            for t in range(T):
                b = bx.get(str(t))
                if b is None or not kand[t]:
                    continue
                inb = _box_inne(uv[t], b)
                ok = ibild[t] & inb
                if M is not None and t < len(M):
                    mh, mw = M[t].shape
                    ui = np.clip((uv[t, :, 0] * mw / W).astype(int), 0, mw - 1)
                    vi = np.clip((uv[t, :, 1] * mh / H).astype(int), 0, mh - 1)
                    import cv2
                    md = cv2.dilate(M[t].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
                    ok &= md[vi, ui]
                if not ben[t]:
                    ok &= np.array([nm not in BENLEDER for nm in LEDER_T1])
                sedd[t] = ok
            kix = [LEDER_T1.index(n) for n in KARNA]
            aix = [LEDER_T1.index(n) for n in ARMAR]
            bix = [LEDER_T1.index(n) for n in LEDER_T1 if n in BENLEDER]
            hix = [LEDER_T1.index("c_head"), LEDER_T1.index("c_neck")]
            karna_sedd = sedd[:, hix].any(axis=1) & (sedd[:, kix].sum(axis=1) >= 2)
            arm_sedd = sedd[:, aix].any(axis=1)
            ben_sedd = sedd[:, bix].mean(axis=1) >= 0.5
            tillst = np.where(karna_sedd & ben_sedd, "HEL", np.where(karna_sedd, "DEL", np.where(arm_sedd, "EXTREMITET", "UTANFOR")))
            vals, cnt = np.unique(tillst, return_counts=True)
            huvudtillstand = str(vals[np.argmax(cnt)])

            n_ik = fotkontakt_dolda(X, sedd, golv_z)
            if n_ik:
                beslut.append(dict(regel="R3_fotkontakt_dolda_fotter", person=pid, tagning=sid, rutor=int(n_ik),
                                   orsak="Fot utan bildstöd under golvet lyfts till fotledshöjd (2-leds-IK). Synliga fötter rörs inte."))
            kroppar[sid][pid] = X
            sedd_per[sid][pid] = sedd

            led_andel = {nm: round(float(sedd[:, j].mean()), 2) for j, nm in enumerate(LEDER_T1)}
            ben_status = {}
            for j, nm in enumerate(LEDER_T1):
                ben_status[nm] = "sedd" if sedd[:, j].mean() >= 0.5 else ("utanfor_bild" if (~ibild[:, j]).mean() >= 0.5 else "antagen")
            synlighet[f"{sid}:{pid}"] = dict(tillstand=huvudtillstand,
                                             tillstand_andel={str(v): round(int(c) / T, 2) for v, c in zip(vals, cnt)},
                                             led_andel_sedd=led_andel, led_status=ben_status)
            # per ruta: bitmask över T1-leder (RLE: bara rutor där masken ändras)
            bits = (sedd * (1 << np.arange(len(LEDER_T1)))).sum(axis=1)
            rle = [[int(a0 + t), int(bits[t])] for t in range(T) if t == 0 or bits[t] != bits[t - 1]]
            rutor_int = [[a0 + t] + [int(round(c * 1000)) for c in X[t].reshape(-1)] for t in range(0, T, steg)]
            if (T - 1) % steg:
                rutor_int.append([a0 + T - 1] + [int(round(c * 1000)) for c in X[T - 1].reshape(-1)])
            rorelse.setdefault(pid, []).append(dict(tagning=sid, ut=[a0, b0], rutor=rutor_int, spar=spar,
                                                    synlig_bitmask_rle=rle, tillstand=huvudtillstand,
                                                    skala_s=s_i, skala_kalla=pm.get("s_kalla")))
            ankare = f"stol_{pid}" if d.pose == "sittande" else None
            tagn_personer.append(dict(id=pid, ankare=ankare, spar=spar, tillstand=huvudtillstand))
            personer_meta.setdefault(pid, dict(roll=pid, farg=ROLL_FARG[len(personer_meta) % len(ROLL_FARG)], hemplats=ankare,
                                               pose=d.pose or "staende", unik=bool(d.unik),
                                               status=dict(identitet="antagen" if not d.unik else "utseende+proportioner",
                                                           hallning=(d.status or {}).get("hallning"))))
        # kameranycklar
        if bana["statisk"]:
            nycklar = [[a0] + _r(Ct[0]) + _r(mat_till_quat(Rt[0]), 5) + [lins_mm]]
        else:
            idx = list(range(0, T, 2)) + ([T - 1] if (T - 1) % 2 else [])
            nycklar = [[a0 + t] + _r(Ct[t]) + _r(mat_till_quat(Rt[t]), 5) + [lins_mm] for t in idx]
        tagningar.append(dict(id=sid, ut=[a0, b0], personer=tagn_personer,
                              kamera=dict(statisk=bool(bana["statisk"]), nycklar=nycklar,
                                          hojd=dict(v=round(h_c, 3), s=round(h_s, 3), status=m["kamerahojd"]["status"],
                                                    matt_andel=m["kamerahojd"]["matt_andel"]),
                                          lodlinje=m["lodlinje"], fokal_px=round(f_px, 1),
                                          fokal_status=matning["fokal"]["tagningar"][S]["status"])))
        if m["kamerahojd"]["status"] == "antagen":
            antaganden.append(dict(vad=f"kamerahöjd {sid}", varde=round(h_c, 3), sigma=round(h_s, 3),
                                   kalla=[l["namn"] for l in m["kamerahojd"]["ledtradar"]]))
        if m["lodlinje"]["status"] == "antagen":
            antaganden.append(dict(vad=f"lodlinje {sid}", varde=[m["lodlinje"]["pitch"], m["lodlinje"]["roll"]], kalla=m["lodlinje"]["kalla"]))

    # --- rum och möbler ---
    objekt = []
    x0, x1, y0, y1 = recept.rum.granser
    th = recept.rum.takhojd_m
    golv_matt = any(l["matt"] and "golv" in l["namn"].lower() for S in matning["tagningar"].values() for l in S["kamerahojd"]["ledtradar"])
    objekt.append(dict(id="golv", bas="golv", typ="golv", pos=_r([(x0 + x1) / 2, (y0 + y1) / 2, -0.02]), rot=[0.0, 0.0, 0.0],
                       matt=_r([x1 - x0, y1 - y0, 0.04]), farg="#3d3832", status="observed" if golv_matt else "amodal_inferred",
                       epistemik="Z2_harledd", rum="gemensamt", synlig_ut=[[0, N]]))
    for v in recept.rum.vaggar:
        if v.geometry_source != "observed":
            antaganden.append(dict(vad=f"vägg {v.sida}", varde=round(v.lage_m, 3), kalla="rumshjärnans låda; ingen tagning såg väggen",
                                   epistemik="Z3_okand", ritas=False))
            continue
        if v.sida in ("W", "E"):
            pos, matt = [v.lage_m, (y0 + y1) / 2, th / 2], [0.08, y1 - y0, th]
        else:
            pos, matt = [(x0 + x1) / 2, v.lage_m, th / 2], [x1 - x0, 0.08, th]
        objekt.append(dict(id=f"vagg_{v.sida}", bas=f"vagg_{v.sida}", typ="vagg", pos=_r(pos), rot=[0.0, 0.0, 0.0], matt=_r(matt),
                           farg="#8a8275", status="observed", epistemik="Z1_sedd", rum="gemensamt", synlig_ut=[[0, N]],
                           evidence_shots=v.evidence_shots))

    lw, rw = LEDER_T1.index("l_wrist"), LEDER_T1.index("r_wrist")
    staende_vid: dict[str, bool] = {}
    for k in obs.klipp:
        for d in k.detektioner:
            if d.klass == "person" and d.vid and d.pose == "staende" and d.vid in nod_av_det:
                staende_vid[nod_av_det[d.vid].id] = True
    bord_topp = {}
    for n in recept.noder:
        if n.klass == "person":
            continue
        pos, matt = list(n.position), list(n.dimensions)
        rot = [round(math.radians(a), 4) for a in n.rotation]
        status = n.geometry_source
        if n.klass == "bord":
            hc_old = {k.klipp: k.kamera.hojd_m.v for k in obs.klipp}
            if n.topp_m is not None:
                # skivhöjden i receptet bär varje tagnings gamla kamerahöjd; räkna om med samsynens kamerahöjder
                det = {d.id: (k.klipp, d) for k in obs.klipp for d in k.detektioner}
                vals = [det[i][1].hojd_m.v - hc_old[det[i][0]] + hc_ny[det[i][0]][0] for i in (n.kallor or []) if i in det and det[i][1].hojd_m]
                topp, topp_kalla = float(np.median(vals)) if vals else n.topp_m.v, "MoGe-skiva + kamerahöjd (matt)"
            else:
                arm = []
                for sid in n.evidence_shots:
                    for pid, X in kroppar.get(sid, {}).items():
                        sd = sedd_per[sid][pid]
                        z = np.where(sd[:, lw], X[:, lw, 2], np.where(sd[:, rw], X[:, rw, 2], np.nan))
                        if np.isfinite(z).sum() > 5:
                            arm.append(float(np.nanpercentile(z, 25)))
                if arm:
                    topp, topp_kalla = float(np.median(arm)) - 0.02, "synliga handleder (härledd)"
                else:
                    topp, topp_kalla = 0.75, "matbordsprior 0,75 m (antagen)"
                    antaganden.append(dict(vad=f"skivhöjd {n.id}", varde=0.75, kalla="prior"))
            topp = float(np.clip(topp, 0.3, 1.5))
            bord_topp[n.id] = topp
            disk = staende_vid.get(n.id, False)
            if disk:
                matt[2] = topp
                pos[2] = topp / 2.0
            else:
                matt[2] = 0.05
                pos[2] = topp - 0.025
            status = f"läge {n.geometry_source}; höjd: {topp_kalla}; mått i plan antagna"
        objekt.append(dict(id=n.id, bas=n.id, typ=n.klass, pos=_r(pos), rot=rot, matt=_r(matt),
                           farg="#8c6239" if n.klass == "bord" else "#5c6370", status=status,
                           epistemik="Z1_sedd" if n.geometry_source == "observed" else "Z2_harledd",
                           rum="gemensamt", synlig_ut=[[0, N]], evidence_shots=n.evidence_shots))

    # stolar för sittande: läge under bäckenet, höjd ur bordet (skiva - 0,30) eller stolprior 0,46 (antagen)
    for sid, kp in kroppar.items():
        tg = next(t for t in tagningar if t["id"] == sid)
        for p in tg["personer"]:
            if not p["ankare"]:
                continue
            X = kp[p["id"]]
            b = np.median(X[:, LEDER_T1.index("c_spine0")], axis=0)
            vid = next((d.vid for k in obs.klipp if k.klipp == sid for d in k.detektioner if d.klass == "person" and d.spar == p["spar"]), None)
            bn = nod_av_det.get(vid).id if vid in nod_av_det else None
            sits = (bord_topp[bn] - 0.30) if bn in bord_topp else 0.46
            kalla = f"skiva {bn} - 0,30 m" if bn in bord_topp else "stolprior 0,46 m"
            sid_stol = p["ankare"]
            if any(o["id"] == sid_stol for o in objekt):
                continue
            objekt.append(dict(id=sid_stol, bas=sid_stol, typ="stol", pos=_r([b[0], b[1], sits - 0.025]), rot=[0.0, 0.0, 0.0],
                               matt=_r([0.42, 0.42, 0.05]), farg="#6b5344", status=f"antagen ({kalla})", epistemik="Z2_harledd",
                               rum="gemensamt", synlig_ut=[[0, N]]))
            antaganden.append(dict(vad=f"stol {sid_stol}", varde=round(sits, 3), kalla=kalla))

    rum_lista = [dict(id="huvudrum", tagningar=[t["id"] for t in tagningar], ut=[t["ut"] for t in tagningar],
                      platser=[o["id"] for o in objekt], status="observed", beskrivning=recept.tro, regel="rumshjärnans lösning")]
    fok = matning["fokal"]["klipp"]
    if fok["status"] == "antagen":
        antaganden.append(dict(vad="fokal", varde=fok["v"], sigma=fok["s"], kalla=fok["kalla"]))
    for e in matning["identitet"]["logg"]:
        if e.get("status") == "antagen":
            antaganden.append(dict(vad="identitet", varde=e["slog_ihop"], kalla=f"utseendeavstånd {e['avstand']} nära tröskeln"))

    paket = dict(
        schema="scenpaket/2",
        klipp=dict(id=obs.klipp_id, video=str(ingest)),
        tidsbas=dict(fps=fps, antal_rutor=N, regel="Rutor är sanning; sekunder = ruta / fps. Intervall [a, b)."),
        bild=dict(bredd=W, hojd=H, sensor_mm=SENSOR_MM),
        koordinater="Blender: Z upp, meter; kvaternion (w,x,y,z); kroppens leder i heltal mm.",
        golv_z=golv_z, rum=rum_lista, huvudrum="huvudrum", objekt=objekt, tagningar=tagningar, personer=personer_meta,
        leder=LEDER_T1, rorelse_steg=steg, rorelse=rorelse, synlighet=synlighet,
        skala=dict(fokal=fok, kamerahojd={t["id"]: t["kamera"]["hojd"] for t in tagningar}),
        antaganden=antaganden,
        mening=dict(repliker=[], roller=personer_meta, rum_relationer={"tro": recept.tro}),
        beslut=beslut,
        regler="B-nasta-klipp: R25c_kamerabana_ur_bakgrund, R_hojd_samsyn, R3_fotkontakt_dolda_fotter, T1_armatur_ur_recept",
        proveniens=dict(skapad=datetime.datetime.now().isoformat(timespec="seconds"), av="motpart/runda-3-opus/B-nasta-klipp/karna/scen_brygga.py"),
    )
    ut_mapp.mkdir(parents=True, exist_ok=True)
    paket["trohet"] = {}
    rader = grindar.mat(paket, ingest)
    for r in rader:
        if "G7_trohet" in r:
            paket["trohet"][f"{r['tagning']}:{r['person']}"] = r["G7_trohet"]
    paket_fil = ut_mapp / "paket.json"
    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    grindar.skriv_rapport(paket, rader, ut_mapp)
    py = str(ROT / "scen/.venv/Scripts/python.exe")
    subprocess.run([py, str(HIT / "emit_bpy.py"), str(paket_fil), "--kropp", "t1"], cwd=str(ROT), check=True)
    return paket_fil
