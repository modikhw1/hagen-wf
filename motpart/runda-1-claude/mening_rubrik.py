"""A4: Visuell rubrik per tagning/person – automatisk del + överlägg mot originalrutan.

Kör:  scen/.venv/Scripts/python.exe motpart/runda-1-claude/mening_rubrik.py

Kriterier (0 = fel, 1 = delvis, 2 = rätt, None = ej tillämpbart):
  H  hållning     mätt klass (sitter/står/går/huk/oklar) ur höft-, lår- och knävinklar + bäckenhöjd + fart,
                  jämförd med etiketten i paketet (pose) och för manipulerade paket med det påstådda målet.
  M  möbel        varje bord som obs.json säger syns i tagningen ska synas i renderingen (synlig_ut + i bild).
                  Bord i bild med underkant > 0.25 m utan stöd = "svävande skiva" (max 1).
  U  utsnitt      oberoende 2D-evidens: trackerns personruta (personer.json) och personmasken (masker.npy)
                  mot paketets projektion genom paketets kamera. Mäter IoU, mittförskjutning, andel
                  överkroppsleder i masken och andel rutor där kroppen "hålls kvar" utan detektion (kand=False).
  K  kontakt      om obs.json säger att personen är "vid" ett bord: handledernas höjd mot skivan när handen
                  är över skivan, samt andel rutor med handled inne i skivan.
"""
from __future__ import annotations

import json

import cv2
import numpy as np

import mening_gemensamt as G

BEN = [("c_spine0", "c_spine1"), ("c_spine1", "c_spine2"), ("c_spine2", "c_spine3"), ("c_spine3", "c_neck"),
       ("c_neck", "c_head"), ("c_head", "nasa_mal")]
for s in "lr":
    BEN += [("c_spine3", f"{s}_clavicle"), (f"{s}_clavicle", f"{s}_uparm"), (f"{s}_uparm", f"{s}_lowarm"),
            (f"{s}_lowarm", f"{s}_wrist"), (f"{s}_wrist", f"{s}_hand_mitt"), ("c_spine0", f"{s}_upleg"),
            (f"{s}_upleg", f"{s}_lowleg"), (f"{s}_lowleg", f"{s}_foot"), (f"{s}_foot", f"{s}_ball")]
KANTER = [(0, 1), (0, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]


# ------------------------------------------------------------------ H: hållning
def hallning(paket: dict, X: np.ndarray, U: list[int], sid: str, pid: str) -> dict:
    L = G.ix(paket)
    golv = paket.get("golv_z", 0.0)
    fps = float(paket["tidsbas"]["fps"])
    h_backen = X[:, L["c_spine0"], 2] - golv
    lar_v, kna_v = [], []
    for s in "lr":
        v = X[:, L[f"{s}_lowleg"]] - X[:, L[f"{s}_upleg"]]
        lar_v.append(np.degrees(np.arcsin(np.clip(-v[:, 2] / (np.linalg.norm(v, axis=-1) + 1e-9), -1, 1))))
        kna_v.append(G.vinkel(X[:, L[f"{s}_upleg"]], X[:, L[f"{s}_lowleg"]], X[:, L[f"{s}_foot"]]))
    lar = np.mean(lar_v, axis=0)          # 90° = lodrätt lår (stående), 0° = vågrätt lår (sittande/huk)
    kna = np.mean(kna_v, axis=0)          # 180° = rakt knä
    huvud = X[:, L["c_head"], 2] - golv
    if len(X) > 4:
        xy = X[:, L["c_spine0"], :2]
        k = 5
        xy_s = np.array([xy[max(0, i - k):i + k + 1].mean(0) for i in range(len(xy))])
        du = np.maximum(np.diff(np.array(U)), 1) / fps
        fart = float(np.median(np.linalg.norm(np.diff(xy_s, axis=0), axis=-1) / du))
        nettosträcka = float(np.linalg.norm(xy_s[-1] - xy_s[0]))
    else:
        fart, nettosträcka = 0.0, 0.0
    t = G.tagning(paket, sid)
    ank = next((p.get("ankare") for p in t["personer"] if p["id"] == pid), None)
    sate = next((o for o in paket["objekt"] if o["id"] == ank), None)
    sate_gap = None
    if sate is not None:
        sate_gap = float(np.median(X[:, L["c_spine0"], 2]) - (sate["pos"][2] + sate["matt"][2] / 2))
    m_lar, m_kna, m_h = float(np.median(lar)), float(np.median(kna)), float(np.median(h_backen))
    kna_h = float(np.median(np.minimum(X[:, L["l_lowleg"], 2], X[:, L["r_lowleg"], 2]) - golv))
    if fart > 0.25 and nettosträcka > 0.4 and m_lar > 50:
        klass = "går"
    elif m_lar >= 55 and m_kna >= 140 and m_h > 0.7:
        klass = "står"
    elif m_lar < 40 and 60 <= m_kna <= 135 and sate_gap is not None and 0.0 <= sate_gap <= 0.25 and kna_h >= 0.30:
        klass = "sitter"
    elif m_kna < 115 and kna_h < 0.30 and m_h < 0.75:
        # knät nära golvet med böjda knän: djup huk/knäböj (även om ett säte placerats under bäckenet)
        klass = "huk"
    else:
        klass = "oklar"
    return dict(klass=klass, lar_deg=round(m_lar, 1), kna_deg=round(m_kna, 1), backen_h_m=round(m_h, 3), kna_h_m=round(kna_h, 3),
                huvud_h_m=round(float(np.median(huvud)), 3), fart_m_s=round(fart, 3), netto_m=round(nettosträcka, 3),
                sate_gap_m=None if sate_gap is None else round(sate_gap, 3))


ETIKETT = {"sittande": "sitter", "staende": "står", "gaende": "går"}


def h_poang(klass: str, etikett: str) -> int:
    mal = ETIKETT.get(etikett, etikett)
    if klass == mal:
        return 2
    if klass == "oklar":
        return 1
    return 0


# ------------------------------------------------------------------ M: möbel
def mobel(paket: dict, obs: dict, sid: str, mitt: int) -> dict:
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    k_obs = next(c for c in obs["klipp"] if c["klipp"] == sid)
    forvantade = sum(1 for d in k_obs["detektioner"] if d["klass"] == "bord")
    kam = G.kamera(paket, sid, mitt)
    i_bild, svavar, dolda = [], [], []
    for o in paket["objekt"]:
        if o["typ"] not in G.BORD_TYP:
            continue
        uv, d = G.proj(paket, grindar_horn(o), kam)
        framfor = (d > 0.05).all()
        bx = np.array([uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max()])
        kb = G.klipp_box(bx, W, H)
        yta_i = max(0.0, kb[2] - kb[0]) * max(0.0, kb[3] - kb[1])
        syns_geom = bool(framfor and yta_i > 0.01 * W * H)
        syns = syns_geom and any(a <= mitt < b for a, b in o["synlig_ut"])
        if syns:
            i_bild.append(o["id"])
            if o["pos"][2] - o["matt"][2] / 2 > 0.25:
                svavar.append(o["id"])
        elif syns_geom:
            dolda.append(o["id"])
    if forvantade == 0:
        p = None if not i_bild else 1
    elif len(i_bild) < forvantade:
        p = 0
    elif svavar:
        p = 1
    else:
        p = 2
    return dict(forvantade_bord=forvantade, bord_i_bild=i_bild, dolda_av_R1=dolda, svavande=svavar, poang=p)


def grindar_horn(o):
    return G.grindar.horn(o)


# ------------------------------------------------------------------ U: utsnitt mot oberoende 2D
def utsnitt(paket: dict, X: np.ndarray, U: list[int], sid: str, pid: str) -> dict:
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    L = G.ix(paket)
    t = G.tagning(paket, sid)
    a0 = t["ut"][0]
    sp_id = G.spar_id_for_person(paket, sid, pid)
    if sp_id is None:
        return dict(poang=None, notis="inget spår")
    rutor = G.detektorrutor(paket, sid, sp_id)
    kand = G.kand(paket, sid, sp_id)
    M = G.masker(paket, sid)
    ok_ix = [L[n] for n in G.grindar.OVERKROPP]
    ious, mitt_fel, hojd_kvot, i_mask = [], [], [], []
    for u, x in zip(U, X):
        lf = u - a0
        uv, d = G.proj(paket, x, G.kamera(paket, sid, u))
        if lf in rutor:
            db = G.klipp_box(rutor[lf], W, H)
            # skelettets ruta + huvudradie (~0.11 m) projicerad på bäckenets djup, klippt till bilden
            fok = W * G.kamera(paket, sid, u)[2] / paket["bild"]["sensor_mm"]
            pad = 0.11 * fok / max(float(np.median(d)), 0.2)
            pb = np.array([uv[:, 0].min() - pad, uv[:, 1].min() - pad, uv[:, 0].max() + pad, uv[:, 1].max() + pad * 0.3])
            pb = G.klipp_box(pb, W, H)
            ious.append(G.iou(pb, db))
            mitt_fel.append(np.linalg.norm(((pb[:2] + pb[2:]) - (db[:2] + db[2:])) / 2) / H)
            hojd_kvot.append((pb[3] - pb[1]) / max(db[3] - db[1], 1.0))
        if M is not None and lf < len(M):
            m = np.asarray(M[lf])
            mh, mw = m.shape
            m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            p = uv[ok_ix]
            inne = (p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H) & (d[ok_ix] > 0)
            if inne.any():
                qi = (p[inne] * [mw / W, mh / H]).astype(int)
                i_mask.append(float(m[qi[:, 1], qi[:, 0]].mean()) * inne.mean())
            else:
                i_mask.append(0.0)
    n_tagn = t["ut"][1] - a0
    halls = None if kand is None else round(float(1.0 - kand[:n_tagn].mean()), 3)
    med_iou = float(np.median(ious)) if ious else 0.0
    med_mask = float(np.median(i_mask)) if i_mask else 0.0
    if not ious:
        p = 0
    elif med_iou >= 0.6 and med_mask >= 0.7 and (halls or 0) < 0.1:
        p = 2
    elif med_iou >= 0.35 and med_mask >= 0.4:
        p = 1
    else:
        p = 0
    return dict(spar=sp_id, rutor_med_detektion=len(ious), iou_median=round(med_iou, 3),
                iou_p10=round(float(np.percentile(ious, 10)), 3) if ious else None,
                mittfel_bildhojd=round(float(np.median(mitt_fel)), 3) if mitt_fel else None,
                hojdkvot=round(float(np.median(hojd_kvot)), 2) if hojd_kvot else None,
                overkropp_i_mask=round(med_mask, 3), andel_rutor_utan_detektion=halls, poang=p)


# ------------------------------------------------------------------ K: händer/kontakt
def kontakt(paket: dict, obs: dict, X: np.ndarray, sid: str, pid: str) -> dict:
    L = G.ix(paket)
    k_obs = next(c for c in obs["klipp"] if c["klipp"] == sid)
    vid = any(d["klass"] == "person" and str(d.get("nyckel", "")).endswith(f":{pid}") and d.get("vid") for d in k_obs["detektioner"])
    bord = [o for o in paket["objekt"] if o["typ"] in G.BORD_TYP]
    if not vid or not bord:
        return dict(vid_bord=vid, poang=None)
    bast = None
    for o in bord:
        p = np.array(o["pos"])
        m = np.array(o["matt"]) / 2
        R = G.rz(np.degrees(o["rot"][2]))
        topp = p[2] + m[2]
        dz_alla, inne_alla, over = [], [], []
        for s in "lr":
            w = X[:, L[f"{s}_wrist"]]
            lok = (w - p) @ R
            ovan = (np.abs(lok[:, 0]) <= m[0] + 0.15) & (np.abs(lok[:, 1]) <= m[1] + 0.15)
            dz_alla.append(np.where(ovan, np.abs(w[:, 2] - topp), np.inf))
            inne_alla.append((np.abs(lok) <= m - 0.01).all(-1))
            over.append(ovan)
        dz = np.min(dz_alla, axis=0)
        andel_over = float(np.mean(np.any(over, axis=0)))
        inne = float(np.mean(np.any(inne_alla, axis=0)))
        med = float(np.median(dz[np.isfinite(dz)])) if np.isfinite(dz).any() else None
        kand = dict(bord=o["id"], hand_over_skiva_andel=round(andel_over, 2),
                    hand_till_skiva_m=None if med is None else round(med, 3), handled_i_skiva_andel=round(inne, 3))
        if bast is None or (med is not None and (bast["hand_till_skiva_m"] is None or med < bast["hand_till_skiva_m"])):
            bast = kand
    med = bast["hand_till_skiva_m"]
    if med is None:
        p = 0
    elif med < 0.08 and bast["handled_i_skiva_andel"] < 0.05:
        p = 2
    elif med < 0.20:
        p = 1
    else:
        p = 0
    return dict(vid_bord=True, **bast, poang=p)


# ------------------------------------------------------------------ överlägg
def rita_overlagg(paket: dict, sid: str, u: int, fil_namn: str, extra_render=None) -> None:
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    t = G.tagning(paket, sid)
    a0 = t["ut"][0]
    fr = G.bildruta(paket, sid, u - a0)
    if fr is None:
        return
    fr = cv2.resize(fr, (W, H))
    bild = (fr * 0.75).astype(np.uint8)
    kam = G.kamera(paket, sid, u)
    L = G.ix(paket)
    M = G.masker(paket, sid)
    if M is not None and u - a0 < len(M):
        m = cv2.resize(np.asarray(M[u - a0]).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(bild, cnts, -1, (0, 255, 255), 2)
    for o in paket["objekt"]:
        if o["typ"] in ("golv", "vagg") or not any(a <= u < b for a, b in o["synlig_ut"]):
            continue
        uv, d = G.proj(paket, G.grindar.horn(o), kam)
        if (d <= 0.05).any():
            continue
        farg = (40, 140, 255) if o["typ"] == "bord" else (200, 120, 255)
        for i, j in KANTER:
            cv2.line(bild, tuple(int(v) for v in uv[i]), tuple(int(v) for v in uv[j]), farg, 2)
    for p in t["personer"]:
        sp = G.spar_for(paket, p["id"], sid)
        if sp is None:
            continue
        U, X = G.X_av(sp)
        i = int(np.argmin([abs(x - u) for x in U]))
        uv, d = G.proj(paket, X[i], kam)
        hx = paket["personer"][p["id"]].get("farg", "#bbbbbb")
        farg = tuple(int(hx[k:k + 2], 16) for k in (5, 3, 1))
        for a, b in BEN:
            if d[L[a]] > 0 and d[L[b]] > 0:
                cv2.line(bild, tuple(int(v) for v in uv[L[a]]), tuple(int(v) for v in uv[L[b]]), farg, 3)
        sp_id = G.spar_id_for_person(paket, sid, p["id"])
        if sp_id:
            r = G.detektorrutor(paket, sid, sp_id).get(u - a0)
            if r is not None:
                cv2.rectangle(bild, (int(r[0]), int(r[1])), (int(r[2]), int(r[3])), (80, 255, 80), 2)
    cv2.putText(bild, f"{sid.upper()} f={u} overlagg", (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    th, tw = 512, 288
    kol = [cv2.resize(bild, (tw, th))]
    if extra_render is not None and extra_render.exists():
        r = cv2.imread(str(extra_render))
        if r is not None:
            kol.append(cv2.resize(r, (tw, th)))
    return np.vstack(kol)


def kor() -> dict:
    resultat = {}
    for klipp in G.KLIPP:
        obs = G.las_obs(klipp)
        for version in [None, "ga_med_attityd", "byt_hand"]:
            f = G.KARNA / "ut" / klipp / (f"manip_{version}" if version else "") / "paket.json"
            if not f.exists():
                continue
            paket = G.las_paket(klipp, version)
            namn = klipp + ("/" + version if version else "")
            kolumner = []
            for t in paket["tagningar"]:
                sid = t["id"]
                a0, b0 = t["ut"]
                mitt = (a0 + b0) // 2
                rad_m = mobel(paket, obs, sid, mitt)
                for p in t["personer"]:
                    pid = p["id"]
                    sp = G.spar_for(paket, pid, sid)
                    if sp is None:
                        continue
                    U, X = G.X_av(sp)
                    h = hallning(paket, X, U, sid, pid)
                    etikett = paket["personer"][pid].get("pose", "staende")
                    h["etikett"] = etikett
                    h["poang"] = h_poang(h["klass"], etikett)
                    resultat[f"{namn}:{sid}:{pid}"] = dict(
                        H=h, M=rad_m, U=utsnitt(paket, X, U, sid, pid), K=kontakt(paket, obs, X, sid, pid))
                if not t["personer"]:
                    resultat[f"{namn}:{sid}:-"] = dict(H=None, M=rad_m, U=None, K=None)
                ren = G.KARNA / "ut" / klipp / (f"manip_{version}" if version else "") / "lokal" / f"kontroll_{sid}_{mitt:03d}.png"
                k = rita_overlagg(paket, sid, mitt, None, ren)
                if k is not None:
                    kolumner.append(k)
            if kolumner:
                cv2.imwrite(str(G.UT / f"mening_overlagg_{klipp}{'_' + version if version else ''}.png"), np.hstack(kolumner))
    G.spara_json("mening_rubrik_auto.json", resultat)
    return resultat


if __name__ == "__main__":
    res = kor()
    print("| ruta | H klass (etikett) | lår° | knä° | bäcken m | knä-h m | M bord i bild/förv. | U IoU | U mask | U utan det. | K hand–skiva m | H | M | U | K |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, r in res.items():
        if r["H"] is None:
            print(f"| {k} | – | | | | {len(r['M']['bord_i_bild'])}/{r['M']['forvantade_bord']} | | | | | – | {r['M']['poang']} | – | – |")
            continue
        h, m, u, kk = r["H"], r["M"], r["U"], r["K"]
        print(f"| {k} | {h['klass']} ({h['etikett']}) | {h['lar_deg']} | {h['kna_deg']} | {h["backen_h_m"]} | {h["kna_h_m"]} | "
              f"{len(m['bord_i_bild'])}/{m['forvantade_bord']}{' svävar' if m['svavande'] else ''} | {u.get('iou_median')} | "
              f"{u.get('overkropp_i_mask')} | {u.get('andel_rutor_utan_detektion')} | {kk.get('hand_till_skiva_m')} | "
              f"{h['poang']} | {m['poang']} | {u.get('poang')} | {kk.get('poang')} |")
