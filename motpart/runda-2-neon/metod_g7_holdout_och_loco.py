"""Del 1 (metod_g7_holdout_och_loco.py):
1. Verifierar Claudes g7_oberoende.mat_paket på de 4 ursprungliga klippen (utan att röra runda-1-claude/).
2. Kör Leave-One-Clip-Out (LOCO) korsvalidering för G7a-tröskeln och mäter selektionsbiasen i Claudes "10 rena original"
   (som bara kommer från 2 av 4 klipp: asketch + notan; 0 från guacamole, 0 från gelato).
3. Kompilerar det osedda 11-tagningars hold-out-klippet `b-tilltal` genom oförändrad `forvarld_karna/scen_brygga.py`
   (med obs/recept från runda-1-claude/rum_ut/med_dekl/btilltal/) till `motpart/runda-2-neon/metod_btilltal_ut/`
   och mäter det med:
     - Argons G1–G7 (grindar.mat + grindar_per_person)
     - Claudes G7-oberoende + felinjektion på b-tilltal
     - Claudes H-serie (grind_harda.py)
     - Claudes automatiska rubrik (mening_rubrik.py)
     - Överläggsbilder för visuell kontroll av b-tilltal.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_g7_holdout_och_loco.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import types

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

import g7_oberoende as G7  # noqa: E402
import grind_harda as GH  # noqa: E402
import grindar as G_ORIG  # noqa: E402
import scen_brygga as SB  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

BT_INGEST = ROT / "scen/3d/ingest/ut/b-tilltal-ravara-tagningar"
BT_R1 = R1 / "rum_ut/med_dekl/btilltal"
BT_UT = HIT / "metod_btilltal_ut"


def verifiera_claudes_g7_4_klipp() -> dict:
    """Kör om g7_oberoende.mat_paket på de 4 klippen och diffar mot runda-1-claude/g7_resultat.json."""
    sparad = json.loads((R1 / "g7_resultat.json").read_text(encoding="utf-8"))["rader"]
    ny = []
    for namn in G7.KLIPP:
        paket = G7.las_json(ROT / "forvarld_karna/ut" / namn / "paket.json")
        ny += G7.mat_paket(namn, paket)
    diffar = []
    for a, b in zip(sparad, ny):
        for k in ("led_med", "led_p90", "i_box", "i_mask", "iou", "spok_andel", "flaggad", "skal"):
            if a.get(k) != b.get(k):
                diffar.append(dict(klipp=a["klipp"], tagning=a["tagning"], person=a["person"], falt=k, sparad=a.get(k), ny=b.get(k)))
    return dict(n_rader=len(ny), antal_diffar=len(diffar), diffar=diffar, rader=ny)


def loco_g7a_och_selektionsbias() -> dict:
    """Leave-One-Clip-Out för G7a + kontroll av nativ SAM-utjämning (sekvens vs rå SAM-2D)."""
    kal = json.loads((R1 / "g7_kalibrering.json").read_text(encoding="utf-8"))
    res = json.loads((R1 / "g7_resultat.json").read_text(encoding="utf-8"))["rader"]

    # 1. Fördelning av Claudes "10 rena original" per klipp
    rena_per_klipp = {}
    for k in G7.KLIPP:
        rena_per_klipp[k] = [
            f"{r['tagning']}:{r['person']}" for r in res if r["klipp"] == k and not r["flaggad"]
        ]

    # 2. Mät NATIV led_med (före scen_brygga: sekvens_*.npz med egen fokal vs rå SAM-2D)
    # Detta visar hur stort avståndet är enbart p.g.a. sekvensutjämning / T1-ledmapping, helt utan bryggfel.
    nativ_led = []
    for namn in G7.KLIPP:
        paket = G7.las_json(ROT / "forvarld_karna/ut" / namn / "paket.json")
        obs = G7.las_json(ROT / "forvarld_karna/ut" / namn / "obs.json")
        ingest = ROT / G7.KLIPP[namn]
        W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
        L = paket["leder"]
        LI = {n: i for i, n in enumerate(L)}
        for t in paket["tagningar"]:
            if not t["personer"]:
                continue
            a0 = t["ut"][0]
            ok = next(k for k in obs["klipp"] if k["klipp"] == t["id"])
            tg = G7.Tagning(ingest, ok, t, L)
            for p in t["personer"]:
                pid = p["id"]
                spar = tg.spar_for[pid]
                sp = next(x for x in paket["rorelse"][pid] if x["tagning"] == t["id"])
                e_nat = []
                for r in sp["rutor"]:
                    f = r[0] - a0
                    uv_nat, ben, _ = tg.nativ_t1(spar, f, W, H)
                    raw = tg.raw(spar, f)
                    pal = tg.palitlig(spar, f)
                    if raw is not None and pal:
                        par = G7.PAR_OVER + (G7.PAR_BEN if ben else [])
                        for nm, k_ix in par:
                            x, y = raw["kp2"][k_ix]
                            if 0 <= x < W and 0 <= y < H:
                                e_nat.append(float(np.linalg.norm(uv_nat[LI[nm]] - raw["kp2"][k_ix]) / H))
                nativ_led.append(dict(
                    klipp=namn, tagning=t["id"], person=pid,
                    nativ_led_med=round(float(np.median(e_nat)), 4) if e_nat else None,
                    nativ_led_p90=round(float(np.percentile(e_nat, 90)), 4) if e_nat else None,
                    paket_led_med=next(r["led_med"] for r in res if r["klipp"] == namn and r["tagning"] == t["id"] and r["person"] == pid),
                ))

    # 3. LOCO på de två klipp som ens har "rena" original i Claudes kalibrering (asketch vs notan),
    # samt LOCO på ALLA 4 klipp med P1-P4-patchade (eller nativa) original + injektioner.
    orig_map = {(r["klipp"], r["tagning"], r["person"]): r for r in res}
    injs = kal["injektioner"]

    loco_rena = {}
    for test_k in ("asketch", "notan"):
        train_orig = [r["led_med"] for r in res if r["klipp"] != test_k and not r["flaggad"] and r["led_med"] is not None]
        train_inj = [
            r["led_med"] for r in injs
            if r["klipp"] != test_k
            and not orig_map[(r["klipp"], r["tagning"], r["person"])]["flaggad"]
            and r["led_med"] is not None
        ]
        # Bästa mittpunktströskel mellan högsta tränings-original och lägsta tränings-injektion
        lo = max(train_orig)
        hi = min(train_inj)
        tr = 0.5 * (lo + hi)
        test_orig = [r for r in res if r["klipp"] == test_k and not r["flaggad"] and r["led_med"] is not None]
        test_inj = [
            r for r in injs
            if r["klipp"] == test_k
            and not orig_map[(r["klipp"], r["tagning"], r["person"])]["flaggad"]
            and r["led_med"] is not None
        ]
        loco_rena[test_k] = dict(
            train_klipp=[k for k in ("asketch", "notan") if k != test_k],
            train_orig_max=round(lo, 4),
            train_inj_min=round(hi, 4),
            vald_troskel=round(tr, 4),
            test_orig_fp=f"{sum(r['led_med'] > tr for r in test_orig)}/{len(test_orig)}",
            test_orig_max=round(max(r["led_med"] for r in test_orig), 4),
            test_inj_fn=f"{sum(r['led_med'] <= tr for r in test_inj)}/{len(test_inj)}",
            test_inj_min=round(min(r["led_med"] for r in test_inj), 4),
            test_djup_fn=f"{sum(r['led_med'] <= tr for r in test_inj if r['injektion'].startswith('djup'))}/{sum(1 for r in test_inj if r['injektion'].startswith('djup'))}",
        )

    # 4. Känslighet för mindre (mer realistiska) injektioner på notan/asketch (0.15 m, 0.25 m, 0.35 m i stället för bara 0.50 m)
    kurva = []
    for dist in (0.10, 0.15, 0.20, 0.25, 0.35, 0.50):
        hits_lat = hits_djup = hits_lat_yolo = hits_djup_yolo = n = 0
        for namn in ("asketch", "notan"):
            paket = G7.las_json(ROT / "forvarld_karna/ut" / namn / "paket.json")
            obs = G7.las_json(ROT / "forvarld_karna/ut" / namn / "obs.json")
            for r in res:
                if r["klipp"] != namn or r["flaggad"]:
                    continue
                n += 1
                sid, pid = r["tagning"], r["person"]
                for typ, fn in (("lat", lambda X, kam, L, d=dist: G7.inj_lateral(X, kam, L, m=d)),
                                ("djup", lambda X, kam, L, d=dist: G7.inj_djup(X, kam, L, m=d))):
                    p2 = copy.deepcopy(paket)
                    G7._forandra(p2, sid, pid, fn)
                    mr = next(x for x in G7.mat_paket(namn, p2, obs, tagningar={sid}) if x["person"] == pid)
                    y_only = bool(G7._yolo_bara(mr["skal"]))
                    if typ == "lat":
                        hits_lat += int(mr["flaggad"])
                        hits_lat_yolo += int(y_only)
                    else:
                        hits_djup += int(mr["flaggad"])
                        hits_djup_yolo += int(y_only)
        kurva.append(dict(
            fel_m=dist, n=n,
            lateral_alla=f"{hits_lat}/{n}", lateral_yolo_bara=f"{hits_lat_yolo}/{n}",
            djup_alla=f"{hits_djup}/{n}", djup_yolo_bara=f"{hits_djup_yolo}/{n}",
        ))

    return dict(rena_per_klipp=rena_per_klipp, nativ_led=nativ_led, loco_rena=loco_rena, kanslighetskurva=kurva)


def kompilera_och_mat_btilltal() -> dict:
    """Kompilerar det osedda 11-tagningars hold-out-klippet b-tilltal med oförändrad scen_brygga och mäter G, G7-oberoende och H."""
    obs_raw = json.loads((BT_R1 / "obs.json").read_text(encoding="utf-8"))
    rec_raw = json.loads((BT_R1 / "recept.json").read_text(encoding="utf-8"))
    obs = Observationer.model_validate(obs_raw)
    rec = Recept.model_validate(rec_raw)

    BT_UT.mkdir(parents=True, exist_ok=True)
    orig_sub = SB.subprocess
    SB.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)  # hoppa över emit_bpy-subprocess
    try:
        pf = SB.kompilera_scenpaket("btilltal", BT_INGEST, obs, rec, BT_UT)
    finally:
        SB.subprocess = orig_sub

    paket = json.loads(pf.read_text(encoding="utf-8"))
    g_orig_sam = G_ORIG.sammanfatta(G_ORIG.mat(paket))
    g_pp_sam = G_ORIG.sammanfatta(G7.grindar_per_person(paket))

    # G7-oberoende på b-tilltal
    g7_rader = G7.mat_paket("btilltal", paket, obs_raw, ingest=BT_INGEST)

    # Nativ led_med på b-tilltal
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    L = paket["leder"]
    LI = {n: i for i, n in enumerate(L)}
    for r in g7_rader:
        t = next(x for x in paket["tagningar"] if x["id"] == r["tagning"])
        a0 = t["ut"][0]
        ok = next(k for k in obs_raw["klipp"] if k["klipp"] == r["tagning"])
        tg = G7.Tagning(BT_INGEST, ok, t, L)
        sp = next(x for x in paket["rorelse"][r["person"]] if x["tagning"] == r["tagning"])
        e_nat = []
        for row in sp["rutor"]:
            f = row[0] - a0
            uv_nat, ben, _ = tg.nativ_t1(r["spar"], f, W, H)
            raw = tg.raw(r["spar"], f)
            pal = tg.palitlig(r["spar"], f)
            if raw is not None and pal:
                par = G7.PAR_OVER + (G7.PAR_BEN if ben else [])
                for nm, k_ix in par:
                    x, y = raw["kp2"][k_ix]
                    if 0 <= x < W and 0 <= y < H:
                        e_nat.append(float(np.linalg.norm(uv_nat[LI[nm]] - raw["kp2"][k_ix]) / H))
        r["nativ_led_med"] = round(float(np.median(e_nat)), 4) if e_nat else None

    # Felinjektion på de b-tilltal-rader som klarar G7-oberoende (hold-out-kalibrering!)
    bt_inj = []
    for r in g7_rader:
        sid, pid = r["tagning"], r["person"]
        for inj_namn, fn in G7.INJEKTIONER.items():
            p2 = copy.deepcopy(paket)
            G7._forandra(p2, sid, pid, fn)
            mr = next(x for x in G7.mat_paket("btilltal", p2, obs_raw, ingest=BT_INGEST, tagningar={sid}) if x["person"] == pid)
            bt_inj.append(dict(
                tagning=sid, person=pid, injektion=inj_namn,
                orig_flaggad=r["flaggad"], orig_led_med=r["led_med"],
                flaggad=mr["flaggad"], skal=mr["skal"],
                flaggad_yolo_bara=bool(G7._yolo_bara(mr["skal"])),
                led_med=mr["led_med"], i_box=mr["i_box"], i_mask=mr["i_mask"],
            ))

    # H-serien på b-tilltal
    spar2d = {}
    for k in obs_raw["klipp"]:
        fp = BT_INGEST / k["klipp"].upper() / "personer.json"
        spar2d[k["klipp"]] = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    ktx = dict(klipp="btilltal", obs=obs_raw, recept=rec_raw, spar2d=spar2d)
    h_rader = GH.mat(paket, ktx)
    h_sam = GH.sammanfatta(h_rader)
    h_detaljer = {}
    for hr in h_rader:
        fel = {kk: {x: y for x, y in hr[kk].items() if x != "ok"} for kk in GH.H_GRINDAR if hr.get(kk, {}).get("ok") is False}
        h_detaljer[f"{hr['tagning']}:{hr.get('person')}"] = fel

    # Rita överläggsbilder för b-tilltal (mittbild per tagning i en mosaik)
    rita_btilltal_mosaik(paket, obs_raw, g7_rader, h_detaljer)

    return dict(
        n_tagningar=len(paket["tagningar"]),
        grindar_argon=g_orig_sam,
        grindar_per_person=g_pp_sam,
        g7_oberoende=g7_rader,
        g7_injektioner=bt_inj,
        h_sammanfattning=h_sam,
        h_detaljer=h_detaljer,
        h_rader_full=h_rader,
        beslut_antal={r: sum(1 for b in paket["beslut"] if b["regel"] == r) for r in sorted({b["regel"] for b in paket["beslut"]})},
    )


def rita_btilltal_mosaik(paket: dict, obs_raw: dict, g7_rader: list[dict], h_detaljer: dict) -> None:
    """Ritar en 2-rads översiktsbild över alla 11 tagningar i b-tilltal: YOLO-ruta (grön), SAM-2D (gul), nativ T1 (cyan), paket T1 (magenta)."""
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    L = paket["leder"]
    LI = {n: i for i, n in enumerate(L)}
    BEN_PAR = [
        ("c_spine0", "c_spine1"), ("c_spine1", "c_spine2"), ("c_spine2", "c_spine3"), ("c_spine3", "c_neck"),
        ("c_neck", "c_head"), ("c_head", "huvud_upp"), ("c_spine3", "l_clavicle"), ("l_clavicle", "l_uparm"),
        ("l_uparm", "l_lowarm"), ("l_lowarm", "l_wrist"), ("c_spine3", "r_clavicle"), ("r_clavicle", "r_uparm"),
        ("r_uparm", "r_lowarm"), ("r_lowarm", "r_wrist"), ("c_spine0", "l_upleg"), ("l_upleg", "l_lowleg"),
        ("l_lowleg", "l_foot"), ("c_spine0", "r_upleg"), ("r_upleg", "r_lowleg"), ("r_lowleg", "r_foot"),
    ]
    g7_map = {(r["tagning"], r["person"]): r for r in g7_rader}
    paneler = []
    for t in paket["tagningar"]:
        sid = t["id"]
        a0, b0 = t["ut"]
        f = (b0 - a0) // 2
        ok_obs = next(k for k in obs_raw["klipp"] if k["klipp"] == sid)
        tg = G7.Tagning(BT_INGEST, ok_obs, t, L)
        cap = cv2.VideoCapture(str(BT_INGEST / "klipp" / f"{sid.upper()}.mp4"))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(f))
        ok, im = cap.read()
        cap.release()
        if not ok or im is None:
            im = np.zeros((H, W, 3), np.uint8)
        im = cv2.resize(im, (W, H))
        if tg.mask is not None and f < tg.mask.shape[0]:
            mk = cv2.resize(np.asarray(tg.mask[f]).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
            cnt, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(im, cnt, -1, (0, 180, 0), 2)
        for p in t["personer"]:
            pid = p["id"]
            spar = tg.spar_for[pid]
            sp = next(x for x in paket["rorelse"][pid] if x["tagning"] == sid)
            rr = min(sp["rutor"], key=lambda x: abs(x[0] - (a0 + f)))
            X = np.array(rr[1:], float).reshape(-1, 3) / 1000.0
            uv, _ = G7.proj(X, *G7.kamera_vid(t, rr[0]), W, H)
            uv_nat, _, _ = tg.nativ_t1(spar, f, W, H)
            yb = tg.yolo(spar, f)
            if yb is not None:
                cv2.rectangle(im, (int(yb[0]), int(yb[1])), (int(yb[2]), int(yb[3])), (0, 255, 0), 3)
            raw = tg.raw(spar, f)
            if raw is not None:
                for k_ix in [k for _, k in G7.PAR_OVER + G7.PAR_BEN] + [0]:
                    x, y = raw["kp2"][k_ix]
                    cv2.circle(im, (int(x), int(y)), 5, (0, 255, 255), -1)
            for a, b in BEN_PAR:
                pa, pb = uv_nat[LI[a]], uv_nat[LI[b]]
                cv2.line(im, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (255, 200, 0), 2)
            for a, b in BEN_PAR:
                pa, pb = uv[LI[a]], uv[LI[b]]
                cv2.line(im, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (255, 0, 255), 3)
            g7r = g7_map.get((sid, pid), {})
            hfel = list(h_detaljer.get(f"{sid}:{pid}", {}).keys())
            lbl1 = f"{sid}:{pid} lm={g7r.get('led_med')} {'FEL' if g7r.get('flaggad') else 'OK'}"
            lbl2 = "H:" + (",".join(x.split("_")[0] for x in hfel) if hfel else "OK")
            cv2.putText(im, lbl1, (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(im, lbl2, (10, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (120, 220, 255), 2)
        paneler.append(cv2.resize(im, (288, 512)))
    while len(paneler) < 12:
        paneler.append(np.full((512, 288, 3), 25, np.uint8))
    mosaik = np.vstack([np.hstack(paneler[:6]), np.hstack(paneler[6:12])])
    cv2.imwrite(str(HIT / "metod_btilltal_overlagg.png"), mosaik)


def main():
    v4 = verifiera_claudes_g7_4_klipp()
    print(f"[1] Verifiering mot runda-1-claude/g7_resultat.json: {v4['n_rader']} rader, {v4['antal_diffar']} diffar")
    loco = loco_g7a_och_selektionsbias()
    print("[2] Rena original per klipp i Claudes kalibrering:", loco["rena_per_klipp"])
    print("[2] LOCO på rena original (asketch <-> notan):", json.dumps(loco["loco_rena"], ensure_ascii=False))
    print("[2] Känslighetskurva (mindre fel):", json.dumps(loco["kanslighetskurva"], ensure_ascii=False))
    bt = kompilera_och_mat_btilltal()
    print(f"[3] Hold-out b-tilltal ({bt['n_tagningar']} tagningar):")
    print("    Argon G1-G7:", bt["grindar_argon"])
    print("    H-serien:   ", bt["h_sammanfattning"])
    print("    Beslut:     ", bt["beslut_antal"])
    for r in bt["g7_oberoende"]:
        print(f"    G7 {r['tagning']}:{r['person']} led_med={r['led_med']} (nativ={r['nativ_led_med']}) "
              f"i_box={r['i_box']}({r['i_box_ref']}) i_mask={r['i_mask']}({r['i_mask_ref']}) "
              f"spok={r['spok_andel']} kam_z={r['kamera_z']} -> {'FEL ' + '; '.join(r['skal']) if r['flaggad'] else 'OK'}")
    for k, v in bt["h_detaljer"].items():
        if v:
            print(f"    H-fel {k}: {json.dumps(v, ensure_ascii=False)}")
    rena_bt = [r for r in bt["g7_oberoende"] if not r["flaggad"]]
    inj_rena_bt = [x for x in bt["g7_injektioner"] if not x["orig_flaggad"]]
    print(f"    b-tilltal G7-oberoende: {len(rena_bt)}/{len(bt['g7_oberoende'])} OK; "
          f"injektioner på rena: {sum(x['flaggad'] for x in inj_rena_bt)}/{len(inj_rena_bt)} "
          f"(YOLO-bara: {sum(x['flaggad_yolo_bara'] for x in inj_rena_bt)}/{len(inj_rena_bt)})")
    for inj_t in ("lateral", "djup", "huk"):
        sub = [x for x in inj_rena_bt if x["injektion"].startswith(inj_t)]
        print(f"      {inj_t}: {sum(x['flaggad'] for x in sub)}/{len(sub)} (YOLO-bara {sum(x['flaggad_yolo_bara'] for x in sub)}/{len(sub)}) "
              f"led_med={[x['led_med'] for x in sub]}")

    out = dict(verifiering_4klipp=dict(n_rader=v4["n_rader"], antal_diffar=v4["antal_diffar"], diffar=v4["diffar"]),
               loco_och_bias=loco, btilltal_holdout=bt)
    (HIT / "metod_g7_holdout_och_loco.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)),
        encoding="utf-8",
    )
    print("Sparade:", HIT / "metod_g7_holdout_och_loco.json", "och", HIT / "metod_btilltal_overlagg.png")


if __name__ == "__main__":
    main()
