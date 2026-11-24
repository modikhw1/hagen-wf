"""Grindar för scenpaket/2, mätta på slutpaketet, en rad per (tagning, person). Egna mått: diagnos, inte krav.

Ändringar mot `byggsten/brygga/grindar.py`:
- C3: en rad per (tagning, person). Originalet skapade en rad per tagning och skrev över G2–G7 för varje person, så
  bara den sist listade personen granskades.
- A1/A3: G7 mäts mot oberoende 2D ur ingesten (personens egen YOLO-ruta i `personer.json` och personmasken
  `masker.npy`), på slutpaketets leder, i stället för att läsa ett lagrat `trohet`-fält som var paketets egen projektion.
- G2 larmar också för svävande synliga fötter (> 0,15 m över golvet), inte bara för fötter under golvet.
- G8 (ny): kamerans lodlinje mot den vertikala försvinningspunkten i originalrutan.
- G9 (ny): kamerans rörelse i paketet mot bakgrundens rörelse i originalet (stilla bakgrund + åkande kamera, eller tvärtom).
- Synlighet: när paketet bär `synlighet` mäts G2 och G4 bara på leder med bildstöd; antagna leder redovisas separat.
- `mutation.py` visar att varje grind kan larma (felinjektion), annars räknas inte "0 fel".
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rotation import quat_till_mat  # noqa: E402

GRANS = dict(golv_m=-0.05, svav_m=0.15, sate_min_m=0.02, sate_max_m=0.20, genom_andel=0.10, ibild_andel=0.70,
             skymning_andel=0.30, g7_box=0.80, g7_mask=0.70, g7_spok=0.20, g8_deg=5.0)
FOT = ("l_foot", "r_foot", "l_ball", "r_ball")
OVERKROPP = ("c_neck", "c_head", "l_uparm", "r_uparm", "c_spine2")
KARNA2D = ("c_head", "c_neck", "l_uparm", "r_uparm")


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


def synlig(o, u):
    return any(a <= u < b for a, b in o["synlig_ut"])


def kamera_vid(t, u):
    """Kamerans läge, rotation och lins i ruta u, linjärt interpolerad mellan nycklar (som Blender LINEAR)."""
    ks = t["kamera"]["nycklar"]
    if len(ks) == 1 or t["kamera"].get("statisk", True):
        k = ks[0]
        return np.array(k[1:4]), quat_till_mat(k[4:8]), k[8]
    us = [k[0] for k in ks]
    if u <= us[0]:
        k = ks[0]; return np.array(k[1:4]), quat_till_mat(k[4:8]), k[8]
    if u >= us[-1]:
        k = ks[-1]; return np.array(k[1:4]), quat_till_mat(k[4:8]), k[8]
    i = int(np.searchsorted(us, u, side="right")) - 1
    a, b = ks[i], ks[i + 1]
    w = (u - a[0]) / max(b[0] - a[0], 1e-9)
    C = (1 - w) * np.array(a[1:4]) + w * np.array(b[1:4])
    qa, qb = np.array(a[4:8]), np.array(b[4:8])
    if qa @ qb < 0:
        qb = -qb
    q = (1 - w) * qa + w * qb
    q /= np.linalg.norm(q)
    return C, quat_till_mat(list(q)), a[8]


def proj(x, kam, W, H, sensor):
    C, R, lins = kam
    c = (np.asarray(x) - C) @ R
    d = -c[..., 2]
    fok = lins / sensor * W
    return c[..., :2] / np.maximum(d[..., None], 1e-6) * [fok, -fok] + [W / 2, H / 2], d


def ruta_box(uv):
    return np.array([uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max()])


def overlapp(a, b):
    w = max(0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


def _sedd_matris(spar, n_led, U):
    """Bitmask (RLE) -> (len(U), n_led) bool; None om paketet saknar synlighet."""
    rle = spar.get("synlig_bitmask_rle")
    if not rle:
        return None
    us = [r[0] for r in rle]
    out = np.zeros((len(U), n_led), bool)
    for i, u in enumerate(U):
        j = max(0, int(np.searchsorted(us, u, side="right")) - 1)
        b = rle[j][1]
        out[i] = [(b >> k) & 1 for k in range(n_led)]
    return out


_BAK_CACHE: dict = {}
_VP_CACHE: dict = {}


def bakgrundsrorelse(mp4: Path, masker: np.ndarray | None, W: int, H: int, N: int):
    """Bakgrundens likhetstransform över tagningen (LK utanför personmasken). Returnerar spann i px, grader och skala."""
    nyckel = (str(mp4), N)
    if nyckel in _BAK_CACHE:
        return _BAK_CACHE[nyckel]
    cap = cv2.VideoCapture(str(mp4))
    gra = []
    for _ in range(N):
        ok, img = cap.read()
        if not ok:
            break
        gra.append(cv2.cvtColor(cv2.resize(img, (288, int(288 * H / W))), cv2.COLOR_BGR2GRAY))
    cap.release()
    if len(gra) < 3:
        return None
    h, w = gra[0].shape
    A = np.eye(3)
    sp = []
    for t in range(1, len(gra)):
        m = np.ones((h, w), np.uint8)
        if masker is not None and t - 1 < len(masker):
            pm = cv2.resize(masker[t - 1].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            m[cv2.dilate(pm, np.ones((15, 15), np.uint8)) > 0] = 0
        p0 = cv2.goodFeaturesToTrack(gra[t - 1], maxCorners=300, qualityLevel=0.01, minDistance=6, mask=m)
        M3 = np.eye(3)
        if p0 is not None and len(p0) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gra[t - 1], gra[t], p0, None, winSize=(21, 21), maxLevel=3)
            ok = st.ravel() == 1
            if ok.sum() >= 12:
                Mx, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.0)
                if Mx is not None:
                    M3[:2] = Mx
        A = M3 @ A
        sp.append(A.copy())
    sp = np.array(sp)
    k = W / 288.0
    tx, ty = sp[:, 0, 2] * k, sp[:, 1, 2] * k
    sk = np.sqrt(np.abs(np.linalg.det(sp[:, :2, :2])))
    rot = np.degrees(np.arctan2(sp[:, 1, 0], sp[:, 0, 0]))
    res = dict(skift_px=float(np.hypot(tx.max() - tx.min(), ty.max() - ty.min())), rot_deg=float(np.ptp(rot)),
               skala=float(sk.max() / max(sk.min(), 1e-6)))
    _BAK_CACHE[nyckel] = res
    return res


def mat(paket, ingest: Path | None = None, g8_g9: bool = True):
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    L = {n: i for i, n in enumerate(paket["leder"])}
    golv = paket.get("golv_z", 0.0)
    rum = {r["id"]: r for r in paket["rum"]}
    huvud = paket.get("huvudrum")
    obj = paket["objekt"]
    bas = {o["id"]: o for o in obj if ":" not in o["id"]}
    rader = []
    for t in paket["tagningar"]:
        a0, b0 = t["ut"]
        mitt = (a0 + b0) // 2
        sid = t["id"]
        fel = []
        for o in obj:
            if not synlig(o, mitt):
                continue
            R = o.get("rum", "gemensamt")
            if R not in ("gemensamt", huvud) and sid not in rum.get(R, {}).get("tagningar", []):
                fel.append(o["id"].split(":")[0])
        g1 = dict(ok=not fel, fel=sorted(set(fel)))
        # G8 och G9 per tagning
        g8 = dict(ok=None, notis="ej mätt")
        g9 = dict(ok=None, notis="ej mätt")
        S_dir = ingest / sid.upper() if ingest else None
        mp4 = ingest / "klipp" / f"{sid.upper()}.mp4" if ingest else None
        if g8_g9 and ingest is not None and mp4.exists():
            import fokal as FOK
            C0, R0, lins = kamera_vid(t, mitt)
            f = lins / S * W
            masker = np.load(S_dir / "masker.npy") if (S_dir / "masker.npy").exists() else None
            vk = (str(mp4), mitt - a0)
            if vk not in _VP_CACHE:
                img = FOK.las_ruta(mp4, mitt - a0, W, H)
                _VP_CACHE[vk] = FOK.forsvinningspunkter(img, masker[mitt - a0] if masker is not None and mitt - a0 < len(masker) else None) if img is not None else []
            vp = FOK.upp_ur_vp(_VP_CACHE[vk], f, W, H) if _VP_CACHE[vk] else None
            if vp is not None and vp[1] >= 15:
                u_b = R0.T @ np.array([0.0, 0.0, 1.0])
                u_cv = np.array([u_b[0], -u_b[1], -u_b[2]])
                vinkel = math.degrees(math.acos(min(1.0, float(abs(u_cv @ vp[0])))))
                g8 = dict(ok=bool(vinkel <= GRANS["g8_deg"]), vinkel_deg=round(vinkel, 2), vp_stod=int(vp[1]))
            else:
                g8 = dict(ok=None, notis="ingen vertikal försvinningspunkt")
            bak = bakgrundsrorelse(mp4, masker, W, H, b0 - a0)
            ks = t["kamera"]["nycklar"]
            Cs = np.array([k[1:4] for k in ks])
            Rs = [quat_till_mat(k[4:8]) for k in ks]
            k_trans = float(np.linalg.norm(Cs.max(0) - Cs.min(0))) if len(ks) > 1 else 0.0
            k_rot = max((math.degrees(math.acos(float(np.clip((np.trace(Rs[0].T @ r) - 1) / 2, -1, 1)))) for r in Rs), default=0.0)
            if bak is not None:
                bak_stilla = bak["skift_px"] < 0.02 * W and bak["rot_deg"] < 0.7 and bak["skala"] < 1.02
                bak_ror = bak["skift_px"] > 0.08 * W or bak["skala"] > 1.06 or bak["rot_deg"] > 3
                kam_ror = k_trans > 0.10 or k_rot > 2.0
                ok = not ((bak_stilla and kam_ror) or (bak_ror and not kam_ror))
                g9 = dict(ok=bool(ok), bakgrund=dict(skift_px=round(bak["skift_px"], 1), rot_deg=round(bak["rot_deg"], 2),
                                                     skala=round(bak["skala"], 3)),
                          kamera=dict(trans_m=round(k_trans, 3), rot_deg=round(k_rot, 2)))
        personer_i = [x for pid, v in paket["rorelse"].items() for x in v if x["tagning"] == sid]
        if not personer_i:
            rader.append(dict(tagning=sid, person=None, G1_rum=g1, G8_lodlinje=g8, G9_kamerarorelse=g9))
        for spar in personer_i:
            pid = next(k for k, v in paket["rorelse"].items() if spar in v)
            rad = dict(tagning=sid, person=pid, G1_rum=g1, G8_lodlinje=g8, G9_kamerarorelse=g9)
            X = np.array([r[1:] for r in spar["rutor"]], float).reshape(len(spar["rutor"]), -1, 3) / 1000
            U = [r[0] for r in spar["rutor"]]
            sedd = _sedd_matris(spar, X.shape[1], U)
            fot_ix = [L[n] for n in FOT if n in L]
            # G2 golv: synliga fötter (eller alla, om paketet saknar synlighet)
            if sedd is not None:
                fm = sedd[:, fot_ix].any(axis=1)
                antagen_fot = float(np.median(X[:, fot_ix, 2].min(axis=1)))
                if fm.sum() >= 3:
                    fot = float(np.median(X[fm][:, fot_ix, 2].min(axis=1)))
                    rad["G2_golv"] = dict(ok=bool(golv + GRANS["golv_m"] <= fot <= golv + GRANS["svav_m"]), fot_z_m=round(fot, 3),
                                          sedda_rutor=int(fm.sum()), antagna_fotter_z_m=round(antagen_fot, 3))
                else:
                    rad["G2_golv"] = dict(ok=None, notis="inga synliga fötter", antagna_fotter_z_m=round(antagen_fot, 3))
            else:
                fot = float(np.median(X[:, fot_ix, 2].min(axis=1)))
                rad["G2_golv"] = dict(ok=bool(golv + GRANS["golv_m"] <= fot <= golv + GRANS["svav_m"]), fot_z_m=round(fot, 3),
                                      notis="paketet saknar synlighet; alla fötter mäts")
            ank = next((p.get("ankare") for p in t["personer"] if p["id"] == pid), None)
            sate = bas.get(ank)
            if sate and sate.get("typ") == "stol":
                topp = sate["pos"][2] + sate["matt"][2] / 2
                hoj = float(np.median(X[:, L["c_spine0"], 2]) - topp)
                rad["G3_sate"] = dict(ok=bool(GRANS["sate_min_m"] <= hoj <= GRANS["sate_max_m"]), backen_over_sits_m=round(hoj, 3))
            else:
                rad["G3_sate"] = dict(ok=None, notis=f"ankare {ank} är inget säte")
            undantag = {L[n] for n in ("c_spine0", "l_upleg", "r_upleg") if n in L}
            traff = np.zeros(len(U), bool)
            traff_ant = np.zeros(len(U), bool)
            vem = {}
            for o in obj:
                if o["typ"] in ("golv", "vagg"):
                    continue
                vis = np.array([synlig(o, u) for u in U])
                if not vis.any():
                    continue
                ins = inne(X, o)
                if sate and o["id"].split(":")[0] == ank:
                    ins[:, list(undantag)] = False
                if sedd is not None:
                    h = (ins & sedd).any(axis=1) & vis
                    traff_ant |= (ins & ~sedd).any(axis=1) & vis
                else:
                    h = ins.any(axis=1) & vis
                if h.any():
                    vem[o["id"]] = round(float(h.mean()), 3)
                traff |= h
            rad["G4_genom"] = dict(ok=bool(traff.mean() <= GRANS["genom_andel"]), andel=round(float(traff.mean()), 3),
                                   varst=sorted(vem.items(), key=lambda kv: -kv[1])[:3],
                                   antagna_leder_andel=(round(float(traff_ant.mean()), 3) if sedd is not None else None))
            i = int(np.argmin([abs(u - mitt) for u in U]))
            kam = kamera_vid(t, U[i])
            uv, d = proj(X[i], kam, W, H, S)
            ok_ix = [L[n] for n in OVERKROPP if n in L]
            inn = (uv[:, 0] >= 0) & (uv[:, 0] <= W) & (uv[:, 1] >= 0) & (uv[:, 1] <= H) & (d > 0)
            till = spar.get("tillstand")
            if till in ("EXTREMITET", "UTANFOR"):
                rad["G5_ibild"] = dict(ok=None, notis=f"tillstånd {till}: bålen ritas inte", overkropp=round(float(inn[ok_ix].mean()), 2))
            else:
                rad["G5_ibild"] = dict(ok=bool(inn[ok_ix].mean() >= GRANS["ibild_andel"]), overkropp=round(float(inn[ok_ix].mean()), 2))
            ob = ruta_box(uv[ok_ix]); oyta = max(1.0, (ob[2] - ob[0]) * (ob[3] - ob[1])); pd = float(np.median(d))
            tack = {}
            for o in obj:
                if o["typ"] in ("golv", "vagg") or not synlig(o, U[i]):
                    continue
                huv, dd = proj(horn(o), kam, W, H, S)
                if (dd <= 0.05).any() or np.median(dd) >= pd - 0.1:
                    continue
                ov = overlapp(ruta_box(huv), ob) / oyta
                if ov > 0.02:
                    tack[o["id"].split(":")[0]] = round(max(tack.get(o["id"].split(":")[0], 0), ov), 2)
            vst = max(tack.values(), default=0)
            # bool(): vst kan vara np.float64, och np.bool_ räknades inte som fel (`is False`) i sammanfatta/mutation (rättat 20 nov)
            rad["G6_skymning"] = dict(ok=bool(vst <= GRANS["skymning_andel"]), tackning=tack)
            rad["G7_trohet"] = g7_oberoende(paket, t, spar, X, U, ingest)
            rader.append(rad)
    return rader


def g7_oberoende(paket, t, spar, X, U, ingest):
    """Kärnleder (huvud, hals, axlar) genom paketets kamera mot personens egen YOLO-ruta och personmasken."""
    if ingest is None or not spar.get("spar"):
        return dict(ok=None, notis="ingen ingest eller inget spår-id")
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    L = {n: i for i, n in enumerate(paket["leder"])}
    sid = t["id"].upper()
    a0 = t["ut"][0]
    pf = ingest / sid / "personer.json"
    if not pf.exists():
        return dict(ok=None, notis="personer.json saknas")
    boxar = json.loads(pf.read_text(encoding="utf-8")).get(str(spar["spar"]), {})
    M = np.load(ingest / sid / "masker.npy") if (ingest / sid / "masker.npy").exists() else None
    kix = [L[n] for n in KARNA2D if n in L]
    i_box, i_mask, spok, n_box = [], [], 0, 0
    rendera_bal = spar.get("tillstand") not in ("EXTREMITET", "UTANFOR")
    for x, u in zip(X, U):
        lok = u - a0
        kam = kamera_vid(t, u)
        uv, d = proj(x[kix], kam, W, H, S)
        ibild = (uv[:, 0] >= 0) & (uv[:, 0] < W) & (uv[:, 1] >= 0) & (uv[:, 1] < H) & (d > 0)
        b = boxar.get(str(lok))
        mk = None
        if M is not None and lok < len(M):
            mh, mw = M[lok].shape
            ui = np.clip((uv[:, 0] * mw / W).astype(int), 0, mw - 1)
            vi = np.clip((uv[:, 1] * mh / H).astype(int), 0, mh - 1)
            mk = M[lok][vi, ui] & ibild
        if b is not None:
            n_box += 1
            x0, y0, x1, y1 = b
            mw_, mh_ = 0.05 * (x1 - x0), 0.05 * (y1 - y0)
            inb = (uv[:, 0] >= x0 - mw_) & (uv[:, 0] <= x1 + mw_) & (uv[:, 1] >= y0 - mh_) & (uv[:, 1] <= y1 + mh_) & ibild
            if ibild.any():
                # bara leder som paketet lägger i bild jämförs; leder utanför bild kan inte ligga i en ruta som klipps av bildkanten
                i_box.append(float(inb[ibild].mean()))
                if mk is not None:
                    i_mask.append(float(mk[ibild].mean()))
            else:
                kant = x0 <= 2 or y0 <= 2 or x1 >= W - 2 or y1 >= H - 2
                if not kant:
                    i_box.append(0.0)  # YOLO ser hela personen i bild, paketet lägger bålen utanför
                    if mk is not None:
                        i_mask.append(0.0)
        elif rendera_bal and ibild.mean() >= 0.5 and (mk is None or mk.mean() < 0.2):
            spok += 1
    if not i_box:
        return dict(ok=None, notis="inga YOLO-rutor för spåret", spok_rutor=spok)
    ib, im = float(np.mean(i_box)), (float(np.mean(i_mask)) if i_mask else None)
    sp = spok / max(1, len(U))
    ok = ib >= GRANS["g7_box"] and (im is None or im >= GRANS["g7_mask"]) and sp <= GRANS["g7_spok"]
    return dict(ok=bool(ok), i_box=round(ib, 3), i_mask=(round(im, 3) if im is not None else None), spok_andel=round(sp, 3),
                rutor_med_box=n_box, metod="oberoende 2D: YOLO-ruta + personmask (ingest), slutpaketets leder")


GRINDLISTA = ["G1_rum", "G2_golv", "G3_sate", "G4_genom", "G5_ibild", "G6_skymning", "G7_trohet", "G8_lodlinje", "G9_kamerarorelse"]


def sammanfatta(rader):
    fel = lambda v: v is not None and not bool(v)  # noqa: E731  (np.bool_ räknas också)
    ut = {}
    for k in GRINDLISTA:
        if k in ("G1_rum", "G8_lodlinje", "G9_kamerarorelse"):
            sett = {}
            for r in rader:
                sett[r["tagning"]] = r.get(k, {}).get("ok")
            ut[k] = sum(1 for v in sett.values() if fel(v))
        else:
            ut[k] = sum(1 for r in rader if fel(r.get(k, {}).get("ok")))
    ut["rader"] = len(rader)
    return ut


def skriv_rapport(paket, rader, ut_mapp: Path):
    samman = sammanfatta(rader)
    (ut_mapp / "paket_grindar.json").write_text(json.dumps(dict(granser=GRANS, sammanfattning=samman, rader=rader), ensure_ascii=False,
                                                           indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)),
                                                encoding="utf-8")
    tecken = lambda v: "–" if v is None else ("ok" if v else "**FEL**")  # noqa: E731
    md = [f"# Grindrapport: {paket['klipp']['id']} (egna mått, diagnos)", f"Fel per grind: `{json.dumps(samman, ensure_ascii=False)}`", "",
          "| tagning | person | tillstånd | G1 | G2 golv | G3 säte | G4 genom | G5 | G6 | G7 i_box/i_mask/spök | G8 lod° | G9 kamera |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rader:
        g = {k: r.get(k, {}) for k in GRINDLISTA}
        till = next((x.get("tillstand") for v in paket["rorelse"].values() for x in v if x["tagning"] == r["tagning"] and r["person"] in paket["rorelse"] and x in paket["rorelse"][r["person"]]), "")
        md.append(f"| {r['tagning']} | {r.get('person') or ''} | {till or ''} | {tecken(g['G1_rum'].get('ok'))} "
                  f"| {tecken(g['G2_golv'].get('ok'))} {g['G2_golv'].get('fot_z_m', '')} "
                  f"| {tecken(g['G3_sate'].get('ok'))} {g['G3_sate'].get('backen_over_sits_m', '')} "
                  f"| {tecken(g['G4_genom'].get('ok'))} {g['G4_genom'].get('andel', '')} "
                  f"| {tecken(g['G5_ibild'].get('ok'))} | {tecken(g['G6_skymning'].get('ok'))} "
                  f"| {tecken(g['G7_trohet'].get('ok'))} {g['G7_trohet'].get('i_box', '')}/{g['G7_trohet'].get('i_mask', '')}/{g['G7_trohet'].get('spok_andel', '')} "
                  f"| {tecken(g['G8_lodlinje'].get('ok'))} {g['G8_lodlinje'].get('vinkel_deg', '')} "
                  f"| {tecken(g['G9_kamerarorelse'].get('ok'))} |")
    (ut_mapp / "GRINDAR.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return samman
