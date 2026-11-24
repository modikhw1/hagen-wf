"""Lager 4 (mening_motor.py): Förenar Harnessen (Takter & Intention), Kroppens Attitydprofil och Snabb Semantisk Manipulation.

Designprincip (kalibrerad 19 nov 2026):
1. Ingest får ta tid; live-manipulering för en Content Manager (CM) måste vara blixtsnabb (< 50 ms i kod,
   < 250 ms med Jev-routning) och ske på menings- och kompositionsnivå, inte som rå Blender-animering.
2. Kroppen isoleras från SAM 3D Bodys råa ledbrus genom att vid ingest destillera ut en
   `AttitydProfil` per person och tagning/takt:
   - `lutning_deg` (framåtlutad/hopsjunken vs upprätt)
   - `slapphet` (0..1: hopsjunken bröstkorg, låga axlar, låg spänning vs alert/spänd)
   - `tempo` & `gest_energi` (rörelsehastighet och gestomfång i armar/händer)
   - `uppmarksamhet` (0042-signatur: blickens stabilitet mot motpart/kamera)
   - `bas_aktivitet` (`sittande`, `staende`, `gaende`) och `hand_handling` (`vilar`, `gestikulerar`, `skopar_och_ger`)
3. När CM (styrd av Harnessen i `byggsten/hand/`) ändrar scenen semantiskt — t.ex.:
   - "Låt honom gå genom lokalen fram till disken istället för att sitta, med samma slappa sätt"
   - "Stå upp vid bardisken istället för att sitta"
   - "Skopa och räck fram med andra handen"
   syntetiseras eller omformas T1-skelettets rörelse direkt i `scenpaket/2` med **ärvd attitydprofil**
   (samma slapphet, rygglutning, tempo och blickfokus), samtidigt som kamerans komposition/utsnitt
   anpassas för att hedra originalets bildspråk (redo för WebGL-preview eller Seedance-generering).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import pathlib
import subprocess
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parent
sys.path.insert(0, str(HIT))
sys.path.insert(0, str(ROT / "byggsten/brygga"))

import grindar  # noqa: E402
import scen_brygga  # noqa: E402
from rotation import mat_till_quat, quat_till_mat  # noqa: E402


# ---------------------------------------------------------------- 1. Attityd- & Meningsdestillering (Ingest -> Profil)

def extrahera_attitydprofil(paket: dict) -> dict[str, dict]:
    """Destillerar ut varje persons fysiska attityd-, energi- och hållningssignatur ur T1-rörelsen."""
    L = {n: i for i, n in enumerate(paket["leder"])}
    profiler: dict[str, dict] = {}

    for pid, spar_lista in paket.get("rorelse", {}).items():
        per_tagn = {}
        lutningar, energier, slappheter, blick_stab = [], [], [], []

        for sp in spar_lista:
            sid = sp["tagning"]
            R = sp["rutor"]
            if not R:
                continue
            X = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0

            # 1. Ryggens framåtlutning (c_spine0 -> c_neck mot vertikalen +Z)
            rygg_v = X[:, L["c_neck"]] - X[:, L["c_spine0"]]
            rygg_langd = np.linalg.norm(rygg_v, axis=-1) + 1e-9
            cos_z = np.clip(rygg_v[:, 2] / rygg_langd, -1.0, 1.0)
            lut_deg = float(np.median(np.degrees(np.arccos(cos_z))))

            # 2. Gestenergi & Tempo (handledernas hastighet i m/s)
            fps = float(paket["tidsbas"]["fps"])
            if len(X) > 1:
                dt = max(1.0, float(R[1][0] - R[0][0])) / fps
                v_l = np.linalg.norm(np.diff(X[:, L["l_wrist"]], axis=0), axis=-1) / dt
                v_r = np.linalg.norm(np.diff(X[:, L["r_wrist"]], axis=0), axis=-1) / dt
                hand_fart = float(np.median(np.maximum(v_l, v_r)))
                hand_topp = float(np.percentile(np.maximum(v_l, v_r), 85))
            else:
                hand_fart, hand_topp = 0.0, 0.0

            # 3. Slapphet / Hållningstonus (0..1):
            # Hög framåtlutning (>18°), armbågar nära/under brösthöjd och lågt tempo ger hög slapphet ("slapp/avslappnad").
            armb_rel = float(np.median(
                ((X[:, L["l_lowarm"], 2] + X[:, L["r_lowarm"], 2]) / 2.0) - X[:, L["c_spine2"], 2]
            ))
            slapp = float(np.clip(
                0.45 * min(lut_deg / 28.0, 1.0)
                + 0.35 * np.clip((-armb_rel) / 0.18, 0.0, 1.0)
                + 0.20 * (1.0 - min(hand_fart / 0.8, 1.0)),
                0.05,
                0.98,
            ))

            # 4. Blickens stabilitet / Uppmärksamhet (0042-signatur: spridning i c_head -> nasa_mal)
            blick_v = X[:, L["nasa_mal"]] - X[:, L["c_head"]]
            blick_v = blick_v / (np.linalg.norm(blick_v, axis=-1, keepdims=True) + 1e-9)
            blick_medel = np.mean(blick_v, axis=0)
            blick_konc = float(np.linalg.norm(blick_medel))  # 1.0 = helt fokuserad blick, lägre = svepande

            # 5. Aktiv hand (vilken hand rör sig mest / sträcks längst fram från bålen)
            avst_l = float(np.percentile(np.linalg.norm(X[:, L["l_wrist"], :2] - X[:, L["c_spine2"], :2], axis=-1), 85))
            avst_r = float(np.percentile(np.linalg.norm(X[:, L["r_wrist"], :2] - X[:, L["c_spine2"], :2], axis=-1), 85))
            aktiv_hand = "hoger" if avst_r >= avst_l + 0.03 else ("vanster" if avst_l >= avst_r + 0.03 else "bada")

            # 6. Kontaktbundna vs Attitydbärande leder:
            # Om armbågar/handleder hålls stilla framför bålen i disk-/bordshöjd (hand_fart < 0.22 m/s,
            # spridning i Z < 0.06 m) är underarmarna kontaktbundna till möbeln ("vilar_pa_disk")
            # och ska frikopplas till avslappnad armpendling när aktiviteten byts till gående!
            z_std_arm = float(0.5 * (np.std(X[:, L["l_wrist"], 2]) + np.std(X[:, L["r_wrist"], 2])))
            kontakt_armar = bool(
                paket["personer"].get(pid, {}).get("pose") == "sittande"
                or (hand_fart < 0.25 and z_std_arm < 0.075 and max(avst_l, avst_r) > 0.22)
            )

            etikett = (
                "slapp_avslappnad" if slapp >= 0.52
                else ("energisk_utatriktad" if hand_topp >= 0.55 else "fokuserad_lugn")
            )

            per_tagn[sid] = dict(
                lutning_deg=round(lut_deg, 1),
                slapphet=round(slapp, 2),
                hand_fart_m_s=round(hand_fart, 3),
                gest_topp_m_s=round(hand_topp, 3),
                uppmarksamhet=round(blick_konc, 3),
                aktiv_hand=aktiv_hand,
                kontakt_armar=kontakt_armar,
                attityd_leder=["c_spine0", "c_spine1", "c_spine2", "c_ spine3", "c_neck", "c_head", "l_clavicle", "r_clavicle"],
                kontakt_leder=["l_lowarm", "r_lowarm", "l_wrist", "r_wrist"] if kontakt_armar else [],
                stil_etikett=etikett,
            )
            lutningar.append(lut_deg)
            energier.append(hand_topp)
            slappheter.append(slapp)
            blick_stab.append(blick_konc)

        med_slapp = float(np.mean(slappheter)) if slappheter else 0.5
        med_lut = float(np.mean(lutningar)) if lutningar else 10.0
        med_energi = float(np.mean(energier)) if energier else 0.3
        stil = (
            "slapp_avslappnad" if med_slapp >= 0.52
            else ("energisk_utatriktad" if med_energi >= 0.55 else "fokuserad_lugn")
        )
        kimodo_prompt = (
            "A person walks slowly with a relaxed, slouched posture, slightly rounded shoulders and casual arm swing"
            if stil == "slapp_avslappnad"
            else (
                "A person moves briskly with an upright posture and expressive, energetic hand gestures"
                if stil == "energisk_utatriktad"
                else "A person moves smoothly with a focused, steady posture and controlled hand movements"
            )
        )

        profiler[pid] = dict(
            pose=paket["personer"].get(pid, {}).get("pose", "staende"),
            stil_etikett=stil,
            lutning_deg=round(med_lut, 1),
            slapphet=round(med_slapp, 2),
            gest_energi=round(med_energi, 3),
            uppmarksamhet=round(float(np.mean(blick_stab)) if blick_stab else 0.9, 3),
            kimodo_stil_prompt=kimodo_prompt,
            per_tagning=per_tagn,
        )
    return profiler


# ---------------------------------------------------------------- 2. Jev-Yta: Förenad Harness + Scen + Kropps-yta

def bygg_jev_yta(paket: dict, profiler: dict[str, dict]) -> list[dict]:
    """Bygger den samlade Jev-ytan (< 250 ms val) där varje drag förenar mening, komposition och kroppens attityd."""
    drag = []
    for pid, prof in profiler.items():
        stil = prof["stil_etikett"]
        pose = prof["pose"]
        if pose == "sittande":
            drag.append(dict(
                id=f"ga_med_attityd_{pid}",
                person=pid,
                operation="ga_med_attityd",
                beskrivning=(
                    f"Låt {pid} gå genom lokalen fram till sin plats istället för att sitta, "
                    f"med samma inlästa attityd ({stil}, lutning {prof['lutning_deg']}°, slapphet {prof['slapphet']})"
                ),
            ))
            drag.append(dict(
                id=f"sta_med_attityd_{pid}",
                person=pid,
                operation="sta_med_attityd",
                beskrivning=(
                    f"Låt {pid} stå vid bordet/disken istället för att sitta, "
                    f"med bibehållen överkroppsattityd ({stil}) och anpassad kamerakomposition"
                ),
            ))
        drag.append(dict(
            id=f"byt_hand_{pid}",
            person=pid,
            operation="byt_hand",
            beskrivning=(
                f"Låt {pid} utföra sin interaktion/gest med andra handen (inklusive bålvridning och axelkompensation)"
            ),
        ))
        drag.append(dict(
            id=f"oka_attityd_{pid}",
            person=pid,
            operation="modulera_attityd",
            faktor=1.35,
            beskrivning=f"Förstärk {pid}:s {stil}-attityd och uttryck i kroppen med 35 % (tydligare för tittaren/Seedance)",
        ))
    drag.append(dict(
        id="ingen_passar",
        operation="langsam_vag",
        beskrivning="Skicka fri text till Förståndet / Kimodo för att kompilera ett nytt sammansatt recept",
    ))
    return drag


# ---------------------------------------------------------------- 3. Attityd-ärvande Rörelse- & Kompositionsoperatorer

def _syntetisera_gang_med_attityd(
    X_orig: np.ndarray,
    U: list[int],
    leder: list[str],
    prof: dict,
    fps: float,
    golv_z: float = 0.0,
    max_dist_m: float = 1.15,
) -> tuple[np.ndarray, np.ndarray]:
    """Byter en sittande/stående sekvens mot en gående rörelse genom lokalen som ÄRVER personens attityd!

    - Attitydbärande leder (ryggens framåtlutning `c_spine0..3`, huvudets nick/blick `c_neck..nasa_mal`,
      axlarnas fall `l/r_clavicle`) ärvs direkt från `X_orig` och `prof`.
    - Kontaktbundna leder (underarmar och händer som vilade på bardisken/bordet när personen satt)
      frikopplas från bordskanten och övergår mjukt till en avslappnad, slapp armpendling längs sidorna
      med behållna mikro-gester i händerna.
    - Bäckenet lyfts till gånghöjd (med slapphetsberoende knäsvikt) och rör sig längs en mjuk gångbana
      fram till slutpositionen vid disken/bordet.
    Returnerar (X_ny, bana_delta_per_ruta).
    """
    L = {n: i for i, n in enumerate(leder)}
    T = len(X_orig)
    X = X_orig.copy()
    slapp = float(prof.get("slapphet", 0.6))

    # Gångriktning = den riktning personen vänder sig i rummet (c_head -> nasa_mal i XY-planet)
    blick_xy = np.median(X_orig[:, L["nasa_mal"], :2] - X_orig[:, L["c_head"], :2], axis=0)
    fram_xy = blick_xy / (np.linalg.norm(blick_xy) + 1e-9)
    hoger_xy = np.array([fram_xy[1], -fram_xy[0]])

    # Mät ursprungliga överarms- och underarmslängder så att frikopplad armpendling behåller exakta benlängder
    l_over_arm = float(np.median(np.linalg.norm(X_orig[:, L["l_lowarm"]] - X_orig[:, L["l_uparm"]], axis=-1)))
    l_under_arm = float(np.median(np.linalg.norm(X_orig[:, L["l_wrist"]] - X_orig[:, L["l_lowarm"]], axis=-1)))
    r_over_arm = float(np.median(np.linalg.norm(X_orig[:, L["r_lowarm"]] - X_orig[:, L["r_uparm"]], axis=-1)))
    r_under_arm = float(np.median(np.linalg.norm(X_orig[:, L["r_wrist"]] - X_orig[:, L["r_lowarm"]], axis=-1)))

    # Slapp gång har lägre kadens (~0.75 cykler/s) och lite kortare, släpigare kliv (~0.42 m/s)
    fart = 0.42 if slapp >= 0.5 else 0.62
    kadens_hz = 0.75 if slapp >= 0.5 else 1.05
    tid_s = np.array([(u - U[0]) / fps for u in U], dtype=float)
    total_tid = max(tid_s[-1], 0.1)
    dist_total = min(fart * total_tid, max_dist_m)

    # Ståhöjd för bäckenet: upprätt ~0.90 m, slapp gång ~0.82 m (mjukare knän, hopsjunken hållning)
    mal_backen_z = 0.85 - 0.05 * slapp
    orig_backen_z = float(np.median(X_orig[:, L["c_spine0"], 2]))
    lyft_z = mal_backen_z - orig_backen_z

    bana_delta = np.zeros((T, 3), dtype=float)
    for t in range(T):
        andel = tid_s[t] / total_tid
        kvar = dist_total * (1.0 - (3 * andel ** 2 - 2 * andel ** 3))
        fas = 2.0 * math.pi * kadens_hz * tid_s[t]
        stegl = 0.22 * (1.0 - andel * 0.55)

        sway = (0.032 + 0.022 * slapp) * math.sin(fas) * (1.0 - 0.5 * andel)
        bounce = -0.020 * abs(math.cos(fas)) * (1.0 - 0.5 * andel)

        xy_shift = -fram_xy * kvar + hoger_xy * sway
        z_shift = lyft_z + bounce
        delta = np.array([xy_shift[0], xy_shift[1], z_shift])
        bana_delta[t] = delta

        # 1. Flytta alla attitydbärande leder (rygg, bröstkorg, nacke, huvud, nyckelben, axlar) med gångbanan
        X[t] = X_orig[t] + delta

        # 2. Frikoppla kontaktbundna armar från disken till avslappnad, slapp armpendling längs kroppen
        # (när personen närmar sig disken i slutet av tagningen kan händerna mjukt lyftas upp mot samtalsläge)
        for sida, tecken, la_len, ua_len in (
            ("l", -1.0, l_over_arm, l_under_arm),
            ("r", +1.0, r_over_arm, r_under_arm),
        ):
            axel_p = X[t, L[f"{sida}_uparm"]].copy()
            # Armpendling går i motfas mot samma sidas ben
            fas_arm = (fas + math.pi) if sida == "l" else fas
            pendel_fram = (0.10 + 0.04 * (1.0 - slapp)) * math.sin(fas_arm) * (1.0 - 0.5 * andel)
            ut_sida = tecken * (0.05 + 0.02 * slapp)

            # Armbågen hänger naturligt nedåt/utåt från axeln med lätt framåtpendling
            v_over = np.array([
                fram_xy[0] * (0.04 + 0.5 * pendel_fram) + hoger_xy[0] * ut_sida,
                fram_xy[1] * (0.04 + 0.5 * pendel_fram) + hoger_xy[1] * ut_sida,
                -0.94,
            ])
            v_over = v_over / (np.linalg.norm(v_over) + 1e-9)
            armb_ny = axel_p + v_over * la_len

            # Underarmen har en avslappnad böjning framåt (~25-35 grader) + mikro-rörelse från originalhanden
            mikro_hand = (X_orig[t, L[f"{sida}_wrist"]] - X_orig[max(0, t - 1), L[f"{sida}_wrist"]]) * 0.5
            v_under = np.array([
                fram_xy[0] * (0.38 + 0.8 * pendel_fram) + hoger_xy[0] * ( -tecken * 0.04),
                fram_xy[1] * (0.38 + 0.8 * pendel_fram) + hoger_xy[1] * ( -tecken * 0.04),
                -0.85 + 0.15 * slapp,
            ])
            v_under = v_under / (np.linalg.norm(v_under) + 1e-9)
            wrist_gang = armb_ny + v_under * ua_len + mikro_hand

            # Behåll handens lokala orientering (wrist -> hand_mitt / index1)
            hand_off_mitt = X_orig[t, L[f"{sida}_hand_mitt"]] - X_orig[t, L[f"{sida}_wrist"]]
            hand_off_idx = X_orig[t, L[f"{sida}_index1"]] - X_orig[t, L[f"{sida}_wrist"]]

            X[t, L[f"{sida}_lowarm"]] = armb_ny
            X[t, L[f"{sida}_wrist"]] = wrist_gang
            X[t, L[f"{sida}_hand_mitt"]] = wrist_gang + hand_off_mitt
            X[t, L[f"{sida}_index1"]] = wrist_gang + hand_off_idx

        # 3. Syntetisera naturlig benpendling under bäckenet som matchar den slappa attityden
        backen_p = X[t, L["c_spine0"]].copy()
        for sida, tecken in (("l", -1.0), ("r", +1.0)):
            fas_s = fas if sida == "l" else (fas + math.pi)
            hoft_xy = backen_p[:2] + hoger_xy * (tecken * 0.10)
            hoft_z = backen_p[2] - 0.04
            X[t, L[f"{sida}_upleg"]] = np.array([hoft_xy[0], hoft_xy[1], hoft_z])

            steg_fram = stegl * math.sin(fas_s)
            fot_lyft = max(0.0, math.cos(fas_s)) * (0.035 if slapp >= 0.5 else 0.065) * (1.0 - 0.6 * andel)
            fot_xy = hoft_xy + fram_xy * steg_fram
            fot_z = golv_z + scen_brygga.FOTLED_OVER_GOLV + fot_lyft

            kna_xy = (hoft_xy + fot_xy) / 2.0 + fram_xy * (0.06 + 0.04 * slapp + 0.05 * max(0.0, math.cos(fas_s)))
            kna_z = (hoft_z + fot_z) / 2.0
            X[t, L[f"{sida}_lowleg"]] = np.array([kna_xy[0], kna_xy[1], kna_z])
            X[t, L[f"{sida}_foot"]] = np.array([fot_xy[0], fot_xy[1], fot_z])
            ta_xy = fot_xy + fram_xy * 0.13
            X[t, L[f"{sida}_ball"]] = np.array([ta_xy[0], ta_xy[1], max(golv_z + scen_brygga.TA_OVER_GOLV, fot_z - 0.04)])

    return X, bana_delta


def _byt_hand_med_balvridning(X_orig: np.ndarray, leder: list[str]) -> np.ndarray:
    """Byter aktiv hand genom att spegla armarnas banor i kroppens lokala sagittalplan och vrida bålen/axlarna."""
    L = {n: i for i, n in enumerate(leder)}
    X = X_orig.copy()
    arm_par = [
        ("l_clavicle", "r_clavicle"),
        ("l_uparm", "r_uparm"),
        ("l_lowarm", "r_lowarm"),
        ("l_wrist", "r_wrist"),
        ("l_hand_mitt", "r_hand_mitt"),
        ("l_index1", "r_index1"),
    ]
    for t in range(len(X)):
        c = X_orig[t, L["c_spine2"]].copy()
        # Kroppens lokala höger-axel ur höfterna (så att speglingen sker i kroppens eget symmetriplan)
        v_hoft = X_orig[t, L["r_upleg"]] - X_orig[t, L["l_upleg"]]
        v_hoft[2] = 0.0
        n_lat = v_hoft / (np.linalg.norm(v_hoft) + 1e-9)

        def spegla_lokalt(pt):
            rel = pt - c
            rel_s = rel - 2.0 * np.dot(rel, n_lat) * n_lat
            return c + rel_s

        for ln, rn in arm_par:
            if ln in L and rn in L:
                X[t, L[ln]] = spegla_lokalt(X_orig[t, L[rn]])
                X[t, L[rn]] = spegla_lokalt(X_orig[t, L[ln]])
    return X


def manipulera_scen(paket: dict, operation: str, person_id: str, tagning_id: str | None = None) -> tuple[dict, dict]:
    """Utför en semantisk CM-manipulation på ett `scenpaket/2` med inbakat attitydarv och kompositionslås."""
    nytt = copy.deepcopy(paket)
    profiler = extrahera_attitydprofil(nytt)
    prof = profiler.get(person_id)
    if prof is None:
        raise ValueError(f"Person {person_id} finns inte i paketet.")

    L = {n: i for i, n in enumerate(nytt["leder"])}
    fps = float(nytt["tidsbas"]["fps"])
    andrade_tagningar = []

    if operation == "ga_med_attityd":
        # 1. Ta bort personens stol (personen går nu genom lokalen istället för att sitta!)
        stol_id = f"stol_{person_id}"
        nytt["objekt"] = [o for o in nytt["objekt"] if o["id"] != stol_id]
        nytt["personer"][person_id]["pose"] = "gaende"
        nytt["personer"][person_id]["hemplats"] = None
        for t in nytt["tagningar"]:
            for p in t["personer"]:
                if p["id"] == person_id:
                    p["ankare"] = None

        # 2. Syntetisera gång med personens inlästa slappa/energiska attityd + låt kameran följa kompositionen!
        for sp in nytt["rorelse"].get(person_id, []):
            sid = sp["tagning"]
            if tagning_id and sid != tagning_id:
                continue
            R = sp["rutor"]
            U = [r[0] for r in R]
            X_orig = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
            t_obj = next(t for t in nytt["tagningar"] if t["id"] == sid)
            ensam = len(t_obj["personer"]) == 1
            # I flerpersonstagning där kameran hålls stilla för att rymma båda personerna (t.ex. S4)
            # begränsar vi gångsträckan till sista steget in mot disken (0.55 m) så att personen alltid syns i bild!
            max_d = 1.15 if ensam else 0.52
            X_ny, bana_delta = _syntetisera_gang_med_attityd(
                X_orig, U, nytt["leder"], prof, fps, nytt.get("golv_z", 0.0), max_dist_m=max_d
            )
            for ob in nytt["objekt"]:
                if ob["typ"] == "bord":
                    scen_brygga._dra_in_dolda_ben_bakom_massiv_disk(X_ny, nytt["leder"], ob, nytt.get("golv_z", 0.0))
            scen_brygga.fotkontakt(X_ny, nytt["leder"], nytt.get("golv_z", 0.0))
            sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X_ny)]

            # Om person_id är ensam huvudperson i tagningen, låt kameran följa med i en mjuk tracking-shot
            # så att originalets komposition och utsnitt hedras!
            if ensam:
                k0 = t_obj["kamera"]["nycklar"][0]
                c_bas = np.array(k0[1:4], dtype=float)
                q_bas = k0[4:8]
                lins = k0[8]
                nya_nycklar = []
                for u, d_xyz in zip(U[::3], bana_delta[::3]):
                    c_u = c_bas + d_xyz * np.array([0.85, 0.85, 1.0])
                    nya_nycklar.append([u] + [round(float(v), 4) for v in c_u] + q_bas + [lins])
                t_obj["kamera"] = dict(statisk=False, nycklar=nya_nycklar)
            andrade_tagningar.append(sid)

    elif operation == "byt_hand":
        for sp in nytt["rorelse"].get(person_id, []):
            sid = sp["tagning"]
            if tagning_id and sid != tagning_id:
                continue
            R = sp["rutor"]
            U = [r[0] for r in R]
            X_orig = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
            X_ny = _byt_hand_med_balvridning(X_orig, nytt["leder"])
            for ob in nytt["objekt"]:
                if ob["typ"] == "bord":
                    scen_brygga._dra_in_dolda_ben_bakom_massiv_disk(X_ny, nytt["leder"], ob, nytt.get("golv_z", 0.0))
            scen_brygga.fotkontakt(X_ny, nytt["leder"], nytt.get("golv_z", 0.0))
            sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X_ny)]
            andrade_tagningar.append(sid)

    # Uppdatera paketets metadata och grindkontroll
    nytt["mening"]["attityd_profiler"] = profiler
    nytt["mening"]["jev_yta"] = bygg_jev_yta(paket, profiler)
    nytt.setdefault("beslut", []).append(dict(
        regel=f"Lager4_{operation}",
        person=person_id,
        tagningar=andrade_tagningar,
        attityd_arvd=prof["stil_etikett"],
        lutning_deg=prof["lutning_deg"],
        slapphet=prof["slapphet"],
    ))

    rader = grindar.mat(nytt)
    samman = grindar.sammanfatta(rader)
    rapport = dict(
        operation=operation,
        person=person_id,
        andrade_tagningar=andrade_tagningar,
        arvd_attityd=prof,
        grindar_sammanfattning=samman,
    )
    return nytt, rapport


def kor_demo():
    """Demonstrerar attitydextraktion + semantisk manipulation på Guacamole (slapp gång) och Gelato (byt hand)."""
    for klipp, op, pid, beskrivning in (
        ("guacamole", "ga_med_attityd", "A", "A går genom lokalen fram till bardisken med samma slappa attityd"),
        ("gelato", "byt_hand", "A", "A skopar och räcker fram med vänster hand (bålvridning + ärvd lutning)"),
    ):
        bas_mapp = HIT / "ut" / klipp
        paket_fil = bas_mapp / "paket.json"
        if not paket_fil.exists():
            continue
        paket = json.loads(paket_fil.read_text(encoding="utf-8"))
        profiler = extrahera_attitydprofil(paket)
        jev_yta = bygg_jev_yta(paket, profiler)

        ut_mapp = bas_mapp / f"manip_{op}"
        ut_mapp.mkdir(parents=True, exist_ok=True)
        (bas_mapp / "attityd_och_jev.json").write_text(
            json.dumps(dict(attityd_profiler=profiler, jev_yta=jev_yta), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        nytt_paket, rapport = manipulera_scen(paket, op, pid)
        ny_paket_fil = ut_mapp / "paket.json"
        ny_paket_fil.write_text(json.dumps(nytt_paket, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

        py = str(ROT / "scen/.venv/Scripts/python.exe")
        emit = str(ROT / "byggsten/brygga/emit_bpy.py")
        subprocess.run([py, emit, str(ny_paket_fil), "--kropp", "t1"], cwd=str(ROT), check=True)
        subprocess.run([py, emit, str(ny_paket_fil), "--kropp", "t1", "--jutsu", "--jutsu-steg", "3", "--jutsu-tol", "15"], cwd=str(ROT), check=True)

        ingest = pathlib.Path(paket["klipp"]["video"])
        jamf = scen_brygga.rendera_och_jamfor(ut_mapp, ingest)

        print("=" * 76)
        print(f"LAGER 4 DEMO: {klipp} -> {op} ({beskrivning})")
        print("=" * 76)
        print(f"  Inläst Attitydprofil ({pid}): {json.dumps(profiler[pid], ensure_ascii=False)}")
        print(f"  Jev-yta ({len(jev_yta)} lagliga drag): {[d['id'] for d in jev_yta]}")
        print(f"  Grindar efter manipulation: {rapport['grindar_sammanfattning']}")
        print(f"  Renderad jämförelse: {jamf}")


if __name__ == "__main__":
    kor_demo()
