"""Del 1 (metod_yolo_oberoende.py):
Granskar hur oberoende och tillförlitlig Claudes "oberoende 2D-sanning" (SAM-2D, YOLO personer.json, YOLO masker.npy)
faktiskt är över samtliga 5 klipp (de 4 + hold-out b-tilltal).

Mäter:
1. Prompt-kopplingen mellan SAM-2D och YOLO: hur exakt matchar SAM:s indata-`bbox` i `kropp/<spår>/<ruta>.npz`
   YOLO-rutan i `personer.json`? (Kvantifierar hur icke-oberoende G7a och G7b är av varandra.)
2. Fall där YOLO har fel (missad detektion, beskuren ruta vid bildkant, bakgrunds-/förgrundsperson i union-masken
   `masker.npy`, avskuret huvud vid övre bildkant) och därmed gör att Claudes G7b/G7c/G7e eller H7_2d
   ANTINGEN falskt fäller en 2D-korrekt projektion (nativ T1!) ELLER missar ett fel.
3. Kör G7-oberoende och H7_2d på det NATIVA SAM-skelettet (0 px kedjefel från scen_brygga!) för alla 32 spår
   (21 i de 4 klippen + 11 i b-tilltal) för att avslöja hur ofta Claudes "oberoende" mått fäller en helt
   oförvrängd 2D-projektion p.g.a. YOLO-fel!
4. Sparar bildbevis `metod_yolo_fel.png` på de tydligaste fallen.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_yolo_oberoende.py
"""
from __future__ import annotations

import json
import pathlib
import sys

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

ALLA_KLIPP = {
    **G7.KLIPP,
    "btilltal": "scen/3d/ingest/ut/b-tilltal-ravara-tagningar",
}


def las_paket_och_obs(namn: str):
    if namn == "btilltal":
        p_fil = HIT / "metod_btilltal_ut/paket.json"
        o_fil = R1 / "rum_ut/med_dekl/btilltal/obs.json"
    else:
        p_fil = ROT / "forvarld_karna/ut" / namn / "paket.json"
        o_fil = ROT / "forvarld_karna/ut" / namn / "obs.json"
    return json.loads(p_fil.read_text(encoding="utf-8")), json.loads(o_fil.read_text(encoding="utf-8"))


def main():
    prompt_iou_lista = []
    prompt_maxdiff_px = []
    nativ_granskning = []
    yolo_problem_rutor = []  # (klipp, sid, pid, f, skäl, uv_nat, yb, im_path)

    for namn, ing_rel in ALLA_KLIPP.items():
        paket, obs = las_paket_och_obs(namn)
        ingest = ROT / ing_rel
        W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
        L = paket["leder"]
        LI = {n: i for i, n in enumerate(L)}
        over_ix = [LI[n] for n in G7.OVER]
        karna_ix = [LI[n] for n in G7.KARNA]
        hix = LI["c_head"]

        for t in paket["tagningar"]:
            if not t["personer"]:
                continue
            sid = t["id"]
            a0, b0 = t["ut"]
            ok_obs = next(k for k in obs["klipp"] if k["klipp"] == sid)
            tg = G7.Tagning(ingest, ok_obs, t, L)
            for p in t["personer"]:
                pid = p["id"]
                spar = tg.spar_for[pid]
                sp = next(x for x in paket["rorelse"][pid] if x["tagning"] == sid)
                q_seq = tg.seq(spar)
                kand = q_seq["kand"] if "kand" in q_seq else None

                # Testa NATIVA T1-projektionen (0 px scen_brygga-fel!) mot Claudes G7b/G7c/G7e och H7_2d
                n_rutor = len(sp["rutor"])
                ib_nat, im_nat, ib_over_nat, h7_nat = [], [], [], []
                spok_nat = 0
                yolo_saknas_men_synlig = 0
                huvud_beskuret_topp = 0
                multi_mask_rutor = 0
                prompt_match_exakt = 0
                prompt_tot = 0
                exempel_f = []

                for r in sp["rutor"]:
                    f = r[0] - a0
                    uv_nat, ben, f_sam = tg.nativ_t1(spar, f, W, H)
                    tg._mask_f = min(f, (tg.mask.shape[0] - 1) if tg.mask is not None else 0)
                    yb = tg.yolo(spar, f)
                    raw = tg.raw(spar, f)

                    # 1. Prompt-koppling: är SAM:s raw["bbox"] bokstavligen YOLO:s ruta?
                    if raw is not None and yb is not None:
                        prompt_tot += 1
                        sb = raw["bbox"].reshape(-1)[:4]
                        diff = float(np.max(np.abs(sb - yb)))
                        prompt_maxdiff_px.append(diff)
                        prompt_iou_lista.append(G7.iou(sb, yb))
                        if diff <= 1.5:
                            prompt_match_exakt += 1

                    # 2. Kolla multi-person kontaminering i union-masken (t.ex. förbipasserande eller arm)
                    if tg.mask is not None and f < tg.mask.shape[0] and yb is not None:
                        mk = np.asarray(tg.mask[f]).astype(np.uint8)
                        mh, mw = mk.shape
                        # Pixlar i masken utanför personens egen YOLO-ruta (+10% marginal)
                        x0 = max(0, int((yb[0] - 0.1 * (yb[2] - yb[0])) / W * mw))
                        x1 = min(mw, int((yb[2] + 0.1 * (yb[2] - yb[0])) / W * mw))
                        y0 = max(0, int((yb[1] - 0.1 * (yb[3] - yb[1])) / H * mh))
                        y1 = min(mh, int((yb[3] + 0.1 * (yb[3] - yb[1])) / H * mh))
                        utanfor = mk.copy()
                        utanfor[y0:y1, x0:x1] = 0
                        if utanfor.sum() > 20:
                            multi_mask_rutor += 1

                    # 3. Testa nativ projektion mot G7b, G7c, G7e, H7_2d
                    in_img_k = (uv_nat[karna_ix, 0] >= 0) & (uv_nat[karna_ix, 0] < W) & (uv_nat[karna_ix, 1] >= 0) & (uv_nat[karna_ix, 1] < H)
                    in_img_o = (uv_nat[over_ix, 0] >= 0) & (uv_nat[over_ix, 0] < W) & (uv_nat[over_ix, 1] >= 0) & (uv_nat[over_ix, 1] < H)
                    if yb is not None:
                        m = G7.GRANS["marginal"] * (yb[3] - yb[1])
                        ybm = yb + [-m, -m, m, m]
                        ir_k = (uv_nat[karna_ix, 0] >= ybm[0]) & (uv_nat[karna_ix, 0] <= ybm[2]) & (uv_nat[karna_ix, 1] >= ybm[1]) & (uv_nat[karna_ix, 1] <= ybm[3])
                        ir_o = (uv_nat[over_ix, 0] >= ybm[0]) & (uv_nat[over_ix, 0] <= ybm[2]) & (uv_nat[over_ix, 1] >= ybm[1]) & (uv_nat[over_ix, 1] <= ybm[3])
                        if in_img_k.any():
                            ib_nat.append(float(ir_k[in_img_k].mean()))
                            im_val = float(tg.maskvarde(uv_nat[karna_ix], W, H)[in_img_k].mean())
                            im_nat.append(im_val)
                            if im_val < 0.75 and len(exempel_f) < 2:
                                exempel_f.append((f, f"nativ_imask={im_val:.2f}"))
                        if in_img_o.any():
                            ib_over_nat.append(float(ir_o[in_img_o].mean()))

                        # H7_2d-test på NATIVT huvud (exakt som grind_harda.py:285-293)
                        kand_boxes = [np.array(v[str(f)], float) for v in tg.spar.values() if str(f) in v]
                        hu, hv = uv_nat[hix]
                        traff = False
                        for b in kand_boxes:
                            bw, bh = b[2] - b[0], b[3] - b[1]
                            if b[0] - 0.15 * bw <= hu <= b[2] + 0.15 * bw and b[1] - 0.15 * bh <= hv <= b[1] + 0.5 * bh:
                                traff = True
                        h7_nat.append(traff)
                        if not traff:
                            if yb[1] <= 5:
                                huvud_beskuret_topp += 1
                            if len(exempel_f) < 3:
                                exempel_f.append((f, f"H7_nativ_MISS(y1={yb[1]:.0f},hv={hv:.0f},mid={(yb[1]+0.5*(yb[3]-yb[1])):.0f})"))
                    else:
                        if in_img_o.mean() >= 0.5 and tg.maskvarde(uv_nat[over_ix], W, H)[in_img_o].mean() < 0.2:
                            spok_nat += 1
                        if kand is not None and f < len(kand) and bool(kand[f]):
                            yolo_saknas_men_synlig += 1

                ib_m = round(float(np.mean(ib_nat)), 3) if ib_nat else None
                im_m = round(float(np.mean(im_nat)), 3) if im_nat else None
                ibo_m = round(float(np.mean(ib_over_nat)), 3) if ib_over_nat else None
                h7_m = round(float(np.mean(h7_nat)), 3) if h7_nat else None
                spok_a = round(spok_nat / max(n_rutor, 1), 3)
                # Flaggar Claudes G7/H7 på det NATIVA skelettet (där scen_brygga-felet = 0)?
                g7b_f = ib_m is not None and ib_m < 0.80
                g7c_f = im_m is not None and im_m < 0.80
                g7e_f = spok_a > 0.20
                h7_f = h7_m is not None and h7_m < 0.70

                rad = dict(
                    klipp=namn, tagning=sid, person=pid, spar=spar, rutor=n_rutor,
                    rutor_yolo=len(ib_nat),
                    prompt_exakt_match=f"{prompt_match_exakt}/{prompt_tot}",
                    nativ_i_box_karna=ib_m, nativ_i_mask_karna=im_m, nativ_i_box_overkropp=ibo_m,
                    nativ_H7_huvud_i_spar=h7_m, nativ_spok_andel=spok_a,
                    huvud_beskuret_topp_rutor=huvud_beskuret_topp,
                    multi_mask_utanfor_egen_ruta_rutor=multi_mask_rutor,
                    claudes_ref_giltig_stanger_av_G7c=bool(im_m is not None and im_m < 0.90),
                    nativ_faller_H7=h7_f,
                    nativ_faller_G7b_utan_refskydd=g7b_f,
                    nativ_faller_G7c_utan_refskydd=g7c_f,
                    nativ_faller_G7e=g7e_f,
                    exempel=exempel_f,
                )
                nativ_granskning.append(rad)
                if h7_f or g7c_f or (im_m is not None and im_m < 0.90) or (h7_m is not None and h7_m < 0.90):
                    yolo_problem_rutor.append((namn, sid, pid, spar, rad, ingest, paket, obs))

    # Rita bildbevis på de tydligaste YOLO-felen (där nativt skelett sitter rätt men YOLO-ruta/mask missar eller fäller)
    paneler = []
    valda = [x for x in yolo_problem_rutor if x[4]["nativ_faller_H7"] or (x[4]["nativ_i_mask_karna"] is not None and x[4]["nativ_i_mask_karna"] < 0.90) or (x[4]["nativ_H7_huvud_i_spar"] is not None and x[4]["nativ_H7_huvud_i_spar"] < 0.90)]
    for namn, sid, pid, spar, rad, ingest, paket, obs in valda[:8]:
        W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
        L = paket["leder"]; LI = {n: i for i, n in enumerate(L)}
        t = next(x for x in paket["tagningar"] if x["id"] == sid)
        ok_obs = next(k for k in obs["klipp"] if k["klipp"] == sid)
        tg = G7.Tagning(ingest, ok_obs, t, L)
        f = rad["exempel"][0][0] if rad["exempel"] else (t["ut"][1] - t["ut"][0]) // 2
        cap = cv2.VideoCapture(str(ingest / "klipp" / f"{sid.upper()}.mp4"))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(f))
        ok, im = cap.read()
        cap.release()
        if not ok or im is None:
            continue
        im = cv2.resize(im, (W, H))
        if tg.mask is not None and f < tg.mask.shape[0]:
            mk = cv2.resize(np.asarray(tg.mask[f]).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
            cnt, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(im, cnt, -1, (0, 255, 255), 2)
        yb = tg.yolo(spar, f)
        if yb is not None:
            cv2.rectangle(im, (int(yb[0]), int(yb[1])), (int(yb[2]), int(yb[3])), (0, 255, 0), 3)
            # rita H7:s övre halva-linje
            ymid = int(yb[1] + 0.5 * (yb[3] - yb[1]))
            cv2.line(im, (int(yb[0]), ymid), (int(yb[2]), ymid), (0, 165, 255), 2)
        uv_nat, _, _ = tg.nativ_t1(spar, f, W, H)
        for nm in G7.KARNA:
            pt = uv_nat[LI[nm]]
            cv2.circle(im, (int(pt[0]), int(pt[1])), 6, (255, 0, 255), -1)
        hc = uv_nat[LI["c_head"]]
        cv2.circle(im, (int(hc[0]), int(hc[1])), 12, (0, 0, 255), 3)
        cv2.putText(im, f"{namn} {sid}:{pid} f={f}", (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
        cv2.putText(im, f"nat H7={rad['nativ_H7_huvud_i_spar']} im={rad['nativ_i_mask_karna']}", (8, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (120, 255, 255), 2)
        paneler.append(cv2.resize(im, (288, 512)))
    if paneler:
        cv2.imwrite(str(HIT / "metod_yolo_fel.png"), np.hstack(paneler))

    samman = dict(
        antal_spar_totalt=len(nativ_granskning),
        prompt_sam_vs_yolo_rutor=len(prompt_iou_lista),
        prompt_iou_median=round(float(np.median(prompt_iou_lista)), 4) if prompt_iou_lista else None,
        prompt_maxdiff_median_px=round(float(np.median(prompt_maxdiff_px)), 3) if prompt_maxdiff_px else None,
        prompt_maxdiff_p90_px=round(float(np.percentile(prompt_maxdiff_px, 90)), 3) if prompt_maxdiff_px else None,
        antal_spar_dar_nativ_faller_H7=sum(r["nativ_faller_H7"] for r in nativ_granskning),
        antal_spar_dar_ref_stanger_av_G7c=sum(r["claudes_ref_giltig_stanger_av_G7c"] for r in nativ_granskning),
        antal_spar_dar_nativ_faller_G7e=sum(r["nativ_faller_G7e"] for r in nativ_granskning),
        antal_spar_med_multi_mask_kontaminering=sum(r["multi_mask_utanfor_egen_ruta_rutor"] > 0 for r in nativ_granskning),
    )
    print("=== YOLO & SAM-2D OBEROENDE-AUDIT (32 spår över 5 klipp) ===")
    print(json.dumps(samman, ensure_ascii=False, indent=2))
    print("\nSpår med YOLO-problem på NATIVA skelettet (0 px scen_brygga-fel):")
    for r in nativ_granskning:
        if r["nativ_faller_H7"] or r["claudes_ref_giltig_stanger_av_G7c"] or r["nativ_faller_G7e"] or (r["nativ_H7_huvud_i_spar"] is not None and r["nativ_H7_huvud_i_spar"] < 0.90):
            print(f"  {r['klipp']}:{r['tagning']}:{r['person']} nativ_H7={r['nativ_H7_huvud_i_spar']} "
                  f"nativ_imask={r['nativ_i_mask_karna']} nativ_ibox={r['nativ_i_box_karna']} "
                  f"nativ_spok={r['nativ_spok_andel']} multi_mask_rutor={r['multi_mask_utanfor_egen_ruta_rutor']}/{r['rutor']} "
                  f"ex={r['exempel'][:2]}")

    (HIT / "metod_yolo_oberoende.json").write_text(
        json.dumps(dict(sammanfattning=samman, per_spar=nativ_granskning), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print("Sparade:", HIT / "metod_yolo_oberoende.json")


if __name__ == "__main__":
    main()
