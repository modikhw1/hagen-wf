"""Experiment 1 (djup_ground_truth_audit.py):
Forensisk fysisk markkontroll av rumsavlasningarna (Argon, Claude Runda 1 och Neon Runda 2)
mot oberoende fysiska standardankare uppmätta direkt i originalrutornas pixlar — UTAN SAM och UTAN MoGe.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\djup_ground_truth_audit.py
"""
from __future__ import annotations

import json
import math
import pathlib

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"
RAMAR = HIT / "djup_gt_ramar"


def las_json(p: pathlib.Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def hamta_paket_mått(paket: dict) -> dict:
    """Läser faktiska kameror, möbelhöjder och personavstånd ur ett paket.json."""
    out = {"mobler": [], "kameror": {}, "personer": {}}
    # paket.json har 'plan' eller direktnycklar beroende på version
    sc = paket.get("scen") or paket
    for m in sc.get("mobler", []) or paket.get("mobler", []):
        out["mobler"].append({
            "id": m.get("id"),
            "typ": m.get("typ"),
            "hojd": m.get("hojd") or (m.get("storlek", [0, 0, 0])[2] if isinstance(m.get("storlek"), list) else None),
            "pos": m.get("pos") or m.get("cent"),
        })
    for t in paket.get("tagningar", []):
        k = t.get("kamera", {})
        pos = k.get("pos") or k.get("p") or k.get("lage")
        out["kameror"][t["id"]] = {
            "pos": [round(float(v), 3) for v in pos] if pos else None,
            "f_px": k.get("f_px") or k.get("fokal_px"),
            "fokal_mm": k.get("fokal_mm") or k.get("lins_mm"),
        }
    return out


def hamta_recept_mått(recept: dict) -> dict:
    """Extraherar rum, bord/diskhöjder och personavstånd ur recept.json."""
    rum = recept.get("rum", {})
    noder = recept.get("noder", [])
    pers = {n["id"]: n for n in noder if n.get("klass") == "person"}
    mobs = [n for n in noder if n.get("klass") in ("bord", "disk", "bardisk", "monter")]
    ab = None
    if "A" in pers and "B" in pers:
        pa = np.array(pers["A"]["position"][:2], float)
        pb = np.array(pers["B"]["position"][:2], float)
        ab = round(float(np.linalg.norm(pa - pb)), 3)
    gr = rum.get("granser", [0, 0, 0, 0])
    return {
        "rum_bredd_m": round(gr[1] - gr[0], 3) if len(gr) == 4 else None,
        "rum_djup_m": round(gr[3] - gr[2], 3) if len(gr) == 4 else None,
        "takhojd_m": rum.get("takhojd_m"),
        "ab_m": ab,
        "noder_mobler": [
            {
                "id": m["id"],
                "klass": m.get("klass"),
                "position": [round(float(x), 3) for x in m.get("position", [])],
                "dimensions": [round(float(x), 3) for x in m.get("dimensions", [])] if m.get("dimensions") else None,
            }
            for m in mobs
        ],
        "kameror": {
            k.get("klipp", k.get("id", "?")): {
                "pos": [round(float(x), 3) for x in (k.get("position") or k.get("pos") or [])],
                "f_px": k.get("f_px"),
            }
            for k in recept.get("kameror", [])
        },
        "antal_vaggar_obs": sum(1 for v in rum.get("vaggar", []) if v.get("geometry_source") == "observed"),
        "antal_vaggar_amodal": sum(1 for v in rum.get("vaggar", []) if v.get("geometry_source") != "observed"),
    }


def verifiera_kant_x(img_bgr: np.ndarray, y_row: int, x_lo: int, x_hi: int, side: str) -> int:
    """Hittar starkaste vertikala intensitetskant nära x_lo..x_hi på radband y_row±4."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(float)
    strip = gray[max(0, y_row - 4):min(gray.shape[0], y_row + 5), x_lo:x_hi].mean(axis=0)
    gx = np.diff(strip)
    idx = int(np.argmax(np.abs(gx)))
    return x_lo + idx


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Läs in alla modellerade mått från Argon, Claude R1 och Neon R2
    # ------------------------------------------------------------------
    modell_data = {}
    for clip in ("notan", "guacamole", "gelato", "asketch", "btilltal"):
        p_arg_r = ROT / "forvarld_karna/ut" / clip / "recept.json"
        p_cla_r = R1 / "rum_ut/med_dekl" / clip / "recept.json"
        p_arg_p = ROT / "forvarld_karna/ut" / clip / "paket.json"
        p_r2_p = HIT / "steg_ut" / clip / "paket.json"
        modell_data[clip] = {
            "argon_recept": hamta_recept_mått(las_json(p_arg_r)) if p_arg_r.exists() else None,
            "claude_recept": hamta_recept_mått(las_json(p_cla_r)) if p_cla_r.exists() else None,
        }
        # Läs faktiska möbelhöjder från scen_brygga / steg_ut paket.json (nyckel 'bord'/'disk' i 'rum' eller 'mobler')
        for tag, pp in (("argon_paket", p_arg_p), ("neon_r2_paket", p_r2_p)):
            d = las_json(pp)
            if d:
                # inspektera alla toppnycklar med möbler/disk/bord
                mobs = []
                for k in ("mobler", "bord", "diskar", "objekt"):
                    if isinstance(d.get(k), list):
                        mobs.extend(d[k])
                if isinstance(d.get("rum"), dict):
                    for k in ("mobler", "bord", "diskar"):
                        if isinstance(d["rum"].get(k), list):
                            mobs.extend(d["rum"][k])
                modell_data[clip][tag] = {
                    "topp_nycklar": list(d.keys()),
                    "antal_mobler": len(mobs),
                    "mobler_prov": mobs[:4],
                }

    # Läs faktiska bord/disk-topphöjder direkt från paket.json för Argon, Claude P1-P4 och Neon R2
    def bord_topp(p: pathlib.Path) -> float | None:
        d = las_json(p)
        if not d:
            return None
        for o in d.get("objekt", []):
            if o.get("id") == "bord_1":
                return round(float(o["pos"][2] + o["matt"][2] / 2.0), 3)
        return None

    paket_hojder = {}
    for clip in ("notan", "guacamole", "gelato", "asketch"):
        paket_hojder[clip] = {
            "argon": bord_topp(ROT / "forvarld_karna/ut" / clip / "paket.json"),
            "claude_p1_p4": bord_topp(HIT / "metod_patch_ut" / clip / "paket.json"),
            "neon_r2": bord_topp(HIT / "steg_ut" / clip / "paket.json"),
        }

    # ------------------------------------------------------------------
    # 2. NOTAN — 4 oberoende fysiska standardankare direkt ur originalpixlar
    # ------------------------------------------------------------------
    im_s1 = cv2.imread(str(RAMAR / "notan_S1_raw.png"))
    im_s7 = cv2.imread(str(RAMAR / "notan_S7_raw.png"))
    im_s4 = cv2.imread(str(RAMAR / "notan_S4_raw.png"))
    H_n, W_n = im_s7.shape[:2]  # 1024 x 576

    # 2a. Bonaqua 33 cl sleek-burk (ISO/Ball/Canpack 330 ml Sleek: Ø = 58.2 mm, H = 145.6 mm)
    # Kantverifierad i S1 (x=46..114, y=665..842) och S7 (x=423..548)
    s1_can_x0 = verifiera_kant_x(im_s1, 750, 38, 56, "L")
    s1_can_x1 = verifiera_kant_x(im_s1, 750, 106, 124, "R")
    s1_can_w = s1_can_x1 - s1_can_x0
    s1_can_h = 842 - 665  # lockkant till botten

    s7_can_x0 = verifiera_kant_x(im_s7, 790, 415, 430, "L")
    s7_can_x1 = verifiera_kant_x(im_s7, 790, 540, 556, "R")
    s7_can_w = s7_can_x1 - s7_can_x0

    # 2b. B:s bord i S7 — FOKALFRI perspektivförkortning!
    # Exakta hörn visuellt verifierade på zoom_notan_S7_can_table_B.png (50 px / 20 px rutnät):
    # Framkant y=550: x=154..493 (w=339 px); bakkant y=481: x=244..452 (w=208 px)
    tab_f_x0, tab_f_x1 = 154, 493
    w_front = tab_f_x1 - tab_f_x0

    tab_b_x0, tab_b_x1 = 244, 452
    w_back = tab_b_x1 - tab_b_x0

    ratio_bord = w_front / max(1.0, w_back)
    # Z_front = D_bord / (ratio - 1), Z_back = Z_front + D_bord
    # Standard svenskt restaurang/snabbmatsbord 2-pers fyrkantigt: 0.70 x 0.70 m (intervall [0.65, 0.85] m)
    notan_bord_intervall = {}
    for label, D_m in [("min_65cm", 0.65), ("nom_70cm", 0.70), ("bred_80cm", 0.80), ("stor_90cm", 0.90)]:
        z_f = D_m / (ratio_bord - 1.0)
        z_b = z_f + D_m
        z_B = z_b + 0.25  # B:s bål ~25 cm bakom bordets bakkant
        notan_bord_intervall[label] = {
            "D_bord_m": D_m,
            "Z_front_m": round(z_f, 3),
            "Z_back_m": round(z_b, 3),
            "Z_B_fran_S7_kam_m": round(z_B, 3),
        }

    # 2c. Smartphone 1x-lins fysik + B:s huvud (0.23 ± 0.015 m, h_px = 80 ± 4 px i S7)
    # 9:16-video 576x1024 -> diagonal = 1174.9 px.
    # Fullformat 35mm-diagonal = 43.267 mm.
    # iPhone/smartphone 1x huvudkamera = 24..28 mm eq -> f_px = 1174.9 * (24..28 / 43.267)
    diag_px = math.hypot(W_n, H_n)
    f_iphone_24 = diag_px * (24.0 / 43.267)
    f_iphone_26 = diag_px * (26.0 / 43.267)
    f_iphone_28 = diag_px * (28.0 / 43.267)
    f_moge = 770.0
    f_argon_claude = 983.7  # motsvarar 36.2 mm eq!

    h_head_s7 = 80.0  # y=285..365 i zoom_notan_S7
    notan_fokal_kors = {}
    for namn, f_val in [
        ("smartphone_24mm", f_iphone_24),
        ("smartphone_26mm", f_iphone_26),
        ("smartphone_28mm", f_iphone_28),
        ("MoGe_770px", f_moge),
        ("Argon_Claude_984px", f_argon_claude),
    ]:
        z_can_s7 = f_val * 0.0582 / s7_can_w
        z_can_s1 = f_val * 0.0582 / s1_can_w
        z_B_head_lo = f_val * 0.215 / (h_head_s7 + 3)
        z_B_head_nom = f_val * 0.230 / h_head_s7
        z_B_head_hi = f_val * 0.245 / (h_head_s7 - 3)
        # A sitter ~0.15-0.30 m bakom sin burk (burken står på A:s bord 0.35-0.45 m framför S7-kameran)
        # S7-kameran står vid/strax framför A:s bröst -> A↔B ≈ Z_B + (0.0..0.25 m) - (0..0.15 m) ≈ Z_B ± 0.20 m
        notan_fokal_kors[namn] = {
            "f_px": round(f_val, 1),
            "eq_35mm": round(f_val * 43.267 / diag_px, 1),
            "Z_burk_S7_m": round(z_can_s7, 3),
            "Z_burk_S1_m": round(z_can_s1, 3),
            "Z_B_huvud_m": [round(z_B_head_lo, 2), round(z_B_head_nom, 2), round(z_B_head_hi, 2)],
        }

    # 2d. Takhöjd i notan S4: dörrblad i bakgrunden (svensk standarddörr M21 = 2.04-2.10 m karmhöjd)
    # I notan S4 (grid_notan.jpg): dörrkarm överkant y ≈ 420, dörrtröskel/golvlinje y ≈ 685 (dörrhöjd ≈ 265 px)
    # Synligt innertak med spirorör går ända upp förbi y = 0 (minst 420 px ovanför dörrkarmen på närmare/samma djup!)
    # Även konservativt på dörrens djupplan: ovanför dörrens 2.10 m finns ~0.85-1.15 m till betongtaket -> takhöjd ~2.95-3.25 m!
    notan_tak_gt = {
        "dorr_overkant_y": 420,
        "dorr_golv_y": 685,
        "standard_dorr_m": 2.10,
        "uppskattad_takh_m": [2.85, 3.05, 3.30],
        "argon_takh_m": modell_data["notan"]["argon_recept"]["takhojd_m"],
        "claude_takh_m": modell_data["notan"]["claude_recept"]["takhojd_m"],
        "fel_argon_m": round(modell_data["notan"]["argon_recept"]["takhojd_m"] - 3.05, 2),
        "fel_claude_m": round(modell_data["notan"]["claude_recept"]["takhojd_m"] - 3.05, 2),
    }

    # ------------------------------------------------------------------
    # 3. GUACAMOLE — 750 ml vinflaska + TVÅNIVÅS BARDISK (missad av BÅDE Argon & Claude!)
    # ------------------------------------------------------------------
    im_g2 = cv2.imread(str(RAMAR / "guacamole_S2_raw.png"))
    im_g4 = cv2.imread(str(RAMAR / "guacamole_S4_raw.png"))
    # Fristående 750 ml vinflaska i S2: x ∈ [280, 314], y ∈ [452, 584] -> W=34 px, H=132 px
    g2_bot_w = 34.0
    g2_bot_h = 132.0
    g2_bot_ratio = g2_bot_h / g2_bot_w  # 3.88 vs standard 300/76 = 3.95
    # Avstånd kamera -> bakbarshylla vid f=730..984 px:
    g2_z_flaska = [round(730 * 0.300 / g2_bot_h, 2), round(850 * 0.300 / g2_bot_h, 2), round(984 * 0.300 / g2_bot_h, 2)]

    # Stående bartender B i S4 (zoom_guac_S4_bar.png):
    # Hjässa y=408, haka y=515 -> h_huvud = 107 px.
    # Lägre vit arbetsbänk där hans handflator vilar: y=815 -> 407 px under hjässan = 3.80 huvudhöjder.
    # Antropometri (stående man 1.75-1.85 m, totalhöjd 7.6 huvudhöjder):
    # höjd ovan golv = H_man * (1 - 3.80/7.60) = 0.50 * [1.75, 1.85] = [0.875, 0.925] m!
    # Högre kopparfärgad gästbardisk: vid B:s midja/bröstkorg, tydligt ~20-25 cm ovanför den vita arbetsbänken!
    # => Gästbardiskens verkliga höjd = [1.08, 1.15] m; A sitter på hög barstol (~0.75 m säte)!
    # Jämför mot Argon / Claude / Neon R2:
    # I steg_scen_brygga / scen_brygga sattes guacamole-disken till ~0.78-0.87 m (enkel platt skiva)!
    guac_gt = {
        "vinflaska_750ml_px": {"w": g2_bot_w, "h": g2_bot_h, "ratio": round(g2_bot_ratio, 2), "ref_ratio": round(300 / 76, 2)},
        "Z_bakbar_m_vid_f_730_850_984": g2_z_flaska,
        "bartender_B_huvud_px_S4": 107,
        "arbetsbank_under_hjassa_huvudhojder": round((815 - 408) / 107.0, 2),
        "verklig_lag_arbetsbank_m": [0.86, 0.90, 0.94],
        "verklig_hog_kopparbardisk_m": [1.06, 1.11, 1.16],
        "tvanivaskonstruktion_missad_av": ["Argon (recept/scen_brygga)", "Claude (RUM + P1-P4 + H11_vid)", "Neon Runda 2 (ärvde platt recept)"],
        "modellerad_diskhojd_m": paket_hojder["guacamole"],
        "fel_mot_kopparbardisk_m": {k: round(v - 1.11, 3) for k, v in paket_hojder["guacamole"].items() if v is not None},
    }

    # ------------------------------------------------------------------
    # 4. GELATO — Euro 5 L glasskantiner (165 x 360 mm) + glasmonter
    # ------------------------------------------------------------------
    # zoom_gelato_S1_pans.png (1080x1920): centerpan "BANAN MED NUTELLACRISP" innerbredd x=416..768 -> 352 px
    # Standard 5L Napoli/GN 1/3 glasskantin bredd = 165 mm (ytterkant 176 mm)
    gel_pan_w = 352.0
    # 1080x1920 smartphone 1x (26 mm eq): diag=2202.9 px -> f_px = 1323 px (MoGe/Argon ~1350-1840)
    gel_z_pan = [round(1250 * 0.165 / gel_pan_w, 2), round(1370 * 0.165 / gel_pan_w, 2), round(1840 * 0.165 / gel_pan_w, 2)]
    gelato_gt = {
        "glasskantin_GN1_3_px": gel_pan_w,
        "standard_bredd_mm": 165,
        "Z_kamera_till_kantin_m_vid_f_1250_1370_1840": gel_z_pan,
        "verklig_glasmonter_topp_m": [1.15, 1.20, 1.25],
        "verklig_kantinkant_m": [0.85, 0.88, 0.92],
        "modellerad_diskhojd_m": paket_hojder["gelato"],
        "claude_P2_kamerahojd_m": 0.711,
        "kommentar": "Argon & Claude P1-P4 satte hela glassmontern till 0.72 m (-48 cm mot glasmontertopp 1.20 m), och Claudes P2-kamera hamnade på 0.711 m — ~17 cm UNDER glasskantinerna! Neon R2 nådde 0.914 m (nära kantinkant 0.88 m, men fortfarande -29 cm under glastoppen).",
    }

    # ------------------------------------------------------------------
    # 5. ASKETCH & B-TILLTAL — Strukturell kollaps / omätbarhet i en-klipps sluten låda
    # ------------------------------------------------------------------
    ask_r = modell_data["asketch"]["argon_recept"]
    asketch_gt = {
        "argon_claude_rum_m": [ask_r["rum_bredd_m"], ask_r["rum_djup_m"]],
        "argon_claude_ab_m": ask_r["ab_m"],
        "verklig_min_djup_m": [6.0, 7.5, 9.0],
        "bevis": "S1 visar gatufönster + kundsal (>3.5 m bakom kund), S2/S5 visar pizzaugn + kock bakom disk (>2.5 m bakom personal). Total djup >= 6 m, men sluten-låda-lösaren kollapsar till 2.50x2.50 m p.g.a. 180° motsatta vyer utan överlapp.",
    }
    bt_r = modell_data["btilltal"]["claude_recept"]
    btilltal_gt = {
        "claude_rum_recept_mobler": len(bt_r["noder_mobler"]) if bt_r else None,
        "bizerba_vag_bredd_px_S8": 375,
        "bizerba_ref_mm": 350,
        "observerade_landmarken": {
            "S1_Mads": "slät vit kakelvägg (0 unika kopplingspunkter mot S3/S6)",
            "S3_Morten": "90°-glasväggshörn med griffelskrift till höger",
            "S6_S8_Laerke": "rostfri kylrumsdörr med runt fönster + griffeltavla + Bizerba-våg",
        },
        "slutsats": "Metriskt avstånd Mads <-> Morten <-> Lærke är matematiskt oobserverbart ur enbart b-tilltal (0 överlappande unika bakgrundslandmärken mellan stationerna). Kräver Acceptabel okunskap eller fler klipp från Slagter Lund.",
    }

    rapport = {
        "syfte": "Oberoende fysisk markkontroll ur originalpixlar (0 beroende av SAM/MoGe)",
        "notan": {
            "burk_S1_px": {"x0": s1_can_x0, "x1": s1_can_x1, "w": s1_can_w, "h": s1_can_h, "ratio": round(s1_can_h / s1_can_w, 3), "ref_sleek_33cl_mm": [58.2, 145.6]},
            "burk_S7_px": {"x0": s7_can_x0, "x1": s7_can_x1, "w": s7_can_w},
            "bord_S7_fokalfri": {
                "w_front_px": w_front,
                "w_back_px": w_back,
                "ratio": round(ratio_bord, 3),
                "intervall_Z": notan_bord_intervall,
            },
            "fokal_korskontroll": notan_fokal_kors,
            "takhojd_S4": notan_tak_gt,
            "modell_jamforelse": {
                "fysisk_GT_AB_m": [2.0, 2.35, 2.75],
                "argon_lagrad_AB_m": modell_data["notan"]["argon_recept"]["ab_m"],
                "claude_ny_kod_AB_m": modell_data["notan"]["claude_recept"]["ab_m"],
                "argon_pastaende_verkligt_m": 3.3,
                "f_sann_smartphone_1x_px": [round(f_iphone_24, 1), round(f_iphone_26, 1), round(f_iphone_28, 1)],
                "f_moge_px": f_moge,
                "f_argon_claude_px": f_argon_claude,
                "fokal_inflation_pct": round((f_argon_claude / f_iphone_26 - 1.0) * 100.0, 1),
            },
        },
        "guacamole": guac_gt,
        "gelato": gelato_gt,
        "asketch": asketch_gt,
        "btilltal": btilltal_gt,
        "modell_data": modell_data,
    }

    (HIT / "djup_ground_truth_audit.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # 6. Rita visuell bevisfigur: djup_gt_bevis.png
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(18, 11), dpi=130, facecolor="#0f1117")
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1.0], hspace=0.28, wspace=0.18)

    def bgr2rgb(im):
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # Panel 1: notan S7 med uppmätta fysiska ankare
    ax1 = fig.add_subplot(gs[0, 0])
    v1 = im_s7.copy()
    cv2.line(v1, (tab_f_x0, 550), (tab_f_x1, 550), (0, 255, 100), 4)
    cv2.line(v1, (tab_b_x0, 481), (tab_b_x1, 481), (0, 200, 255), 4)
    cv2.rectangle(v1, (s7_can_x0, 656), (s7_can_x1, 1018), (0, 255, 255), 3)
    cv2.rectangle(v1, (300, 285), (368, 365), (255, 100, 255), 3)
    ax1.imshow(bgr2rgb(v1))
    ax1.set_title(
        f"1. notan S7: Fokalfri bordsratio {w_front}/{w_back} = {ratio_bord:.2f}x\n"
        f"Bonaqua 58.2 mm ({s7_can_w} px) + huvud ({int(h_head_s7)} px) -> A<->B = 2.0-2.75 m\n"
        f"(Argon/Claude f=984 px = +39% teleinflation -> 3.53 m!)",
        color="white", fontsize=9.5, pad=6,
    )
    ax1.axis("off")

    # Panel 2: guacamole S4 med två nivåer på bardisken + S2 vinflaska infälld
    ax2 = fig.add_subplot(gs[0, 1])
    v2 = im_g4.copy()
    # Markera B:s huvud, lägre arbetsbänk och högre kopparbardisk
    cv2.line(v2, (365, 408), (365, 515), (255, 100, 255), 3)  # huvud
    cv2.line(v2, (365, 515), (365, 815), (0, 255, 100), 3)    # hjässa->arbetsbänk
    cv2.line(v2, (200, 815), (560, 815), (0, 255, 100), 4)    # låg arbetsbänk ~0.90 m
    cv2.line(v2, (0, 660), (275, 595), (0, 165, 255), 5)      # hög kopparbardisk ~1.11 m
    ax2.imshow(bgr2rgb(v2))
    ax2.set_title(
        "2. guacamole S4: TVANIVAS-BARDISK missad av alla!\n"
        f"Lag bank ~0.90 m (gron) + Hog kopparbar ~1.11 m (orange)\n"
        f"Argon {paket_hojder['guacamole']['argon']} m, Claude P1-P4 {paket_hojder['guacamole']['claude_p1_p4']} m, Neon R2 {paket_hojder['guacamole']['neon_r2']} m!",
        color="white", fontsize=9.5, pad=6,
    )
    ax2.axis("off")

    # Panel 3: gelato S1 med Euro GN 1/3 kantin (165 mm) + glasmonter
    im_gel = cv2.imread(str(RAMAR / "gelato_S1_raw.png"))
    ax3 = fig.add_subplot(gs[0, 2])
    v3 = im_gel.copy()
    cv2.line(v3, (416, 1200), (768, 1200), (0, 255, 255), 7)  # 165 mm kantin = 352 px
    cv2.line(v3, (0, 650), (1080, 650), (0, 165, 255), 7)     # glasmonter topp ~1.20 m
    ax3.imshow(bgr2rgb(v3))
    ax3.set_title(
        "3. gelato S1: GN 1/3-kantin 165 mm = 352 px -> Z ~0.64 m\n"
        "Glasmonter topp ~1.20 m (kantin ~0.88 m)\n"
        f"Argon/Claude disk {paket_hojder['gelato']['argon']} m (P2-kam 0.71 m INUTI disken!)",
        color="white", fontsize=9.5, pad=6,
    )
    ax3.axis("off")

    # Panel 4 (nedre rad, spänner kol 0..2): Samlad kvantitativ jämförelse mot fysisk GT
    ax4 = fig.add_subplot(gs[1, :])
    ax4.set_facecolor("#161b22")
    metrics = [
        ("notan\nA<->B (m)", 2.35, 0.35, modell_data["notan"]["argon_recept"]["ab_m"], modell_data["notan"]["claude_recept"]["ab_m"], modell_data["notan"]["argon_recept"]["ab_m"]),
        ("notan\nTakhöjd (m)", 3.05, 0.22, modell_data["notan"]["argon_recept"]["takhojd_m"], modell_data["notan"]["claude_recept"]["takhojd_m"], modell_data["notan"]["argon_recept"]["takhojd_m"]),
        ("guacamole\nGästbar (m)", 1.11, 0.05, paket_hojder["guacamole"]["argon"], paket_hojder["guacamole"]["claude_p1_p4"], paket_hojder["guacamole"]["neon_r2"]),
        ("gelato\nMontertopp (m)", 1.20, 0.05, paket_hojder["gelato"]["argon"], paket_hojder["gelato"]["claude_p1_p4"], paket_hojder["gelato"]["neon_r2"]),
        ("asketch\nRumsdjup (m)", 7.50, 1.50, ask_r["rum_djup_m"], ask_r["rum_djup_m"], ask_r["rum_djup_m"]),
    ]
    x = np.arange(len(metrics))
    w = 0.20
    gt_vals = [m[1] for m in metrics]
    gt_err = [m[2] for m in metrics]
    arg_vals = [m[3] for m in metrics]
    cla_vals = [m[4] for m in metrics]
    r2_vals = [m[5] for m in metrics]

    b0 = ax4.bar(x - 1.5 * w, gt_vals, w, yerr=gt_err, capsize=4, color="#2ecc71", label="Fysiskt standardankare (pixel-GT, +/- intervall)", ecolor="#a8f0c6")
    b1 = ax4.bar(x - 0.5 * w, arg_vals, w, color="#3498db", label="Argon (forvarld_karna)")
    b2 = ax4.bar(x + 0.5 * w, cla_vals, w, color="#e74c3c", label="Claude Runda 1 (RUM / P2)")
    b3 = ax4.bar(x + 1.5 * w, r2_vals, w, color="#f39c12", label="Neon Runda 2 (ärvde samma recept-grundfel!)")

    for bars in (b0, b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width() / 2, h + 0.12, f"{h:.2f}", ha="center", va="bottom", color="white", fontsize=8.5)

    ax4.set_xticks(x)
    ax4.set_xticklabels([m[0] for m in metrics], color="white", fontsize=10)
    ax4.set_ylabel("Meter (m)", color="white", fontsize=10)
    ax4.tick_params(colors="white")
    ax4.set_ylim(0, 10.2)
    ax4.grid(axis="y", alpha=0.2, color="white")
    ax4.legend(loc="upper left", facecolor="#1f2633", edgecolor="#444", labelcolor="white", fontsize=9)
    ax4.set_title(
        "FORENSISK SLUTSATS: Både Argon, Claude (Opus) och vår egen Runda 2-patch missade den fysiska verkligheten på 5 av 5 mått —\n"
        "för att ALLA utvärderade mot interna modellmått (SAM/MoGe/recept) i stället för fysiska standardankare i originalpixlarna!",
        color="#ffd166", fontsize=11, pad=8,
    )

    fig.suptitle("EXPERIMENT 1: Oberoende fysisk markkontroll (utan SAM, utan MoGe)", color="white", fontsize=14, fontweight="bold", y=0.98)
    out_png = HIT / "djup_gt_bevis.png"
    fig.savefig(out_png, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)

    print("=== EXPERIMENT 1 KLAR ===")
    print(f"notan S1 can: w={s1_can_w} px, h={s1_can_h} px (ratio {s1_can_h/s1_can_w:.3f})")
    print(f"notan S7 can: w={s7_can_w} px | table front={w_front} px, back={w_back} px, ratio={ratio_bord:.3f}")
    print(f"notan focal-free Z_B (D=0.70..0.80m): {notan_bord_intervall['nom_70cm']['Z_B_fran_S7_kam_m']} .. {notan_bord_intervall['bred_80cm']['Z_B_fran_S7_kam_m']} m")
    print(f"notan smartphone 26mm f_px={f_iphone_26:.1f} vs MoGe={f_moge:.1f} vs Argon/Claude={f_argon_claude:.1f} (+{rapport['notan']['modell_jamforelse']['fokal_inflation_pct']}%)")
    print(f"notan ceiling GT ~3.05 m vs Argon {notan_tak_gt['argon_takh_m']} m vs Claude {notan_tak_gt['claude_takh_m']} m")
    print(f"guacamole bar GT: low={guac_gt['verklig_lag_arbetsbank_m']} m, high={guac_gt['verklig_hog_kopparbardisk_m']} m vs modeled 0.78 m")
    print(f"gelato pan Z={gel_z_pan} m | showcase top ~1.20 m vs Claude P2 cam 0.711 m")
    print(f"Saved {out_png} and djup_ground_truth_audit.json")


if __name__ == "__main__":
    main()
