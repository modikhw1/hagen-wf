"""Lokal objektiv geometri-, kant- och linjemätning: rå originalruta vs Codex image-gen 'mall'-ruta."""
from __future__ import annotations

import json
from pathlib import Path
import cv2
import numpy as np

HIT = Path(__file__).resolve().parent
FALL = ["guacamole_s1", "asketch_s7", "gelato_s1"]


def grad_iou_och_shift(raw_bgr: np.ndarray, mall_bgr: np.ndarray) -> dict[str, float]:
    h, w = raw_bgr.shape[:2]
    mall_rs = cv2.resize(mall_bgr, (w, h), interpolation=cv2.INTER_AREA)

    g_raw = cv2.GaussianBlur(cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2GRAY), (5, 5), 1.2)
    g_mall = cv2.GaussianBlur(cv2.cvtColor(mall_rs, cv2.COLOR_BGR2GRAY), (5, 5), 1.2)

    # Normaliserad strukturkorrelation via gradientmagnitud (tål färgbyte, mäter geometri)
    gx_r = cv2.Sobel(g_raw, cv2.CV_32F, 1, 0, ksize=3)
    gy_r = cv2.Sobel(g_raw, cv2.CV_32F, 0, 1, ksize=3)
    mag_r = np.hypot(gx_r, gy_r)

    gx_m = cv2.Sobel(g_mall, cv2.CV_32F, 1, 0, ksize=3)
    gy_m = cv2.Sobel(g_mall, cv2.CV_32F, 0, 1, ksize=3)
    mag_m = np.hypot(gx_m, gy_m)

    # Hitta ev. global pixel-förskjutning (dx, dy) via phaseCorrelate på gradientfält
    shift, resp = cv2.phaseCorrelate(mag_r, mag_m)

    # Kantenkelhet: hur mycket bakgrundsskräp (höga Canny-kanter) som rensats bort
    e_raw = cv2.Canny(g_raw, 60, 140) > 0
    e_mall = cv2.Canny(g_mall, 60, 140) > 0
    edge_dens_raw = float(e_raw.mean())
    edge_dens_mall = float(e_mall.mean())
    kant_reduktion_pct = round((1.0 - edge_dens_mall / max(edge_dens_raw, 1e-6)) * 100.0, 1)

    # Grov struktur-överensstämmelse på nedskalad gradientkarta (utjämnar små detaljremsor)
    mr_s = cv2.GaussianBlur(mag_r, (15, 15), 4.0)
    mm_s = cv2.GaussianBlur(mag_m, (15, 15), 4.0)
    mask_r = mr_s > np.percentile(mr_s, 72)
    mask_m = mm_s > np.percentile(mm_s, 72)
    struct_iou = float(np.logical_and(mask_r, mask_m).sum() / max(1, np.logical_or(mask_r, mask_m).sum()))

    # Central person-region (mittre 40-80 % vertikalt, 20-80 % horisontellt) gradientkorrelation
    y0, y1 = int(h * 0.25), int(h * 0.80)
    x0, x1 = int(w * 0.15), int(w * 0.85)
    a = mr_s[y0:y1, x0:x1].ravel()
    b = mm_s[y0:y1, x0:x1].ravel()
    grad_corr = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 1e-6 and np.std(b) > 1e-6 else 0.0

    # Hitta dominerande horisontella/diagonala linjers vinkelspridning (HoughLinesP)
    def med_vinkel(edges: np.ndarray) -> float | None:
        lines = cv2.HoughLinesP((edges.astype(np.uint8) * 255), 1, np.pi / 180, 60, minLineLength=60, maxLineGap=14)
        if lines is None or len(lines) == 0:
            return None
        angs = []
        for x_a, y_a, x_b, y_b in lines.reshape(-1, 4):
            ang = float(np.degrees(np.arctan2(y_b - y_a, x_b - x_a)))
            if abs(ang) < 45:  # horisontella/disk-linjer
                angs.append(ang)
        return round(float(np.median(angs)), 2) if angs else None

    return {
        "raw_shape": [int(w), int(h)],
        "mall_shape": [int(mall_bgr.shape[1]), int(mall_bgr.shape[0])],
        "phase_shift_px": [round(float(shift[0]), 2), round(float(shift[1]), 2)],
        "phase_response": round(float(resp), 4),
        "edge_density_raw": round(edge_dens_raw, 4),
        "edge_density_mall": round(edge_dens_mall, 4),
        "kant_reduktion_pct": kant_reduktion_pct,
        "grova_struktur_iou": round(struct_iou, 4),
        "central_grad_corr": round(grad_corr, 4),
        "disk_vinkel_raw_deg": med_vinkel(e_raw),
        "disk_vinkel_mall_deg": med_vinkel(e_mall),
    }


def main() -> None:
    rader = {}
    par_paneler = []
    for namn in FALL:
        r_p = HIT / f"{namn}_raw.png"
        m_p = HIT / f"{namn}_mall.png"
        if not (r_p.exists() and m_p.exists()):
            rader[namn] = {"finns": False}
            continue
        raw_img = cv2.imread(str(r_p))
        mall_img = cv2.imread(str(m_p))
        if raw_img is None or mall_img is None:
            rader[namn] = {"finns": False, "fel": "Kunde inte läsa PNG"}
            continue
        stat = grad_iou_och_shift(raw_img, mall_img)
        stat["finns"] = True
        cj = HIT / f"{namn}_mall.png.codex.json"
        if cj.exists():
            meta = json.loads(cj.read_text(encoding="utf-8"))
            stat["sekunder"] = meta.get("sekunder")
            stat["hel"] = (meta.get("prompt_fram") or {}).get("hel")
        rader[namn] = stat

        # Skala till 360x640 per ruta för tydlig kontaktkarta
        rr = cv2.resize(raw_img, (360, 640))
        mm = cv2.resize(mall_img, (360, 640))
        cv2.putText(rr, f"{namn} RAW", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2)
        cv2.putText(mm, f"{namn} MALL", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (80, 235, 130), 2)
        par_paneler.append(np.hstack([rr, mm]))

    if par_paneler:
        # 2-raders / staplad sida-vid-sida kontaktkarta
        grid = np.vstack(par_paneler)
        cv2.imwrite(str(HIT / "kontakt_mall_pilot.png"), grid)

    (HIT / "matning.json").write_text(json.dumps(rader, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rader, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
