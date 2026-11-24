# STEG-PATCH (Del 3, Neon runda 2): KOPIA av forvarld_karna/scen_brygga.py med S1-S5.
# Generera om med motpart/runda-2-neon/steg_bygg_patch.py; originalet är orört.
"""Lager 3 (scen_brygga.py): Kompilerar Rumshjärnans Recept + Råsekvenser direkt till Scenpaket med T1-armaturer & G1–G7 Grindar.

Fundamentala mekanismer (utan beroende av gamla `scen/3d/kontrakt/plan.json`):
1. Kamerarörelse-separation (`separera_kamerarorelse`):
   SAM 3D Body ger kroppens translation i kameraramen (`cam_t_ra`). När kameran åker in eller panorerar
   inom en tagning (t.ex. 70 cm inåkning i Gelato S1), hamnar kamerarörelsen annars som falsk rotglidning
   i kroppen. Vi separerar bäckenets lågfrekventa horisontella drift delta_xy(f) och flyttar över den
   till kamerans nycklar `CAM_s*` (`statisk=False`). Eftersom x'(f) - C'(f) == x(f) - C(f) i varje ruta,
   bevaras 2D-projektionen till 100,0 % samtidigt som personen står stadigt i 3D-rummet och kameran rör sig!
2. Fysikalisk möbelvolym & Kontaktkalibrerad höjd:
   - Om en stående roll arbetar vid bordet/disken (t.ex. bartender i Guacamole, expedit i Gelato/A-sketch)
     byggs möbeln som en **massiv disk ner till golvet** whose överyta kalibreras mot personernas vilande
     underarmar/händer, och där gissade dolda ben hålls bakom diskens frontyta.
   - Om bara sittande roller finns vid bordet (t.ex. Notan) byggs en bordsskiva i sitthöjd.
3. Fysikalisk Kontakt-IK (R3):
   - Fötter under golvet (z < 0) lyfts till golvet med 2-leds-IK.
   - Sittande personer får en stolsits (`stol_<pid>`) direkt under bäckenet (G3 säte).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import math
import pathlib
import subprocess
import sys

import numpy as np

ROT = pathlib.Path(__file__).resolve().parents[2]   # STEG-PATCH: kopian bor i motpart/runda-2-neon/
HIT = ROT / "forvarld_karna"
sys.path.insert(0, str(ROT / "motpart/runda-1-claude"))
sys.path.insert(0, str(HIT))
sys.path.insert(0, str(ROT / "byggsten/brygga"))

import grindar  # noqa: E402
from rotation import mat_till_quat, quat_xyzw  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

F = np.diag([1.0, -1.0, -1.0])
LEDER_T1 = [
    "c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
    "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
    "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    "l_upleg", "l_lowleg", "l_foot", "l_ball", "r_upleg", "r_lowleg", "r_foot", "r_ball",
]
HARLEDD = {
    "l_hand_mitt": ("l_index1", "l_pinky1"),
    "r_hand_mitt": ("r_index1", "r_pinky1"),
}
FOTLED_OVER_GOLV, TA_OVER_GOLV = 0.065, 0.02
ROLL_FARG = {
    "A": "#4c8bf5",
    "B": "#e06c75",
    "C": "#98c379",
    "person_4": "#d19a66",
}


def _euler_xyz_till_mat(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    rx, ry, rz = math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def _r(x, n=4):
    return [round(float(v), n) for v in x]


def _intervall_minus(iv, bort):
    ut = [list(iv)]
    for c, d in bort:
        ny = []
        for a, b in ut:
            if d <= a or c >= b:
                ny.append([a, b])
                continue
            if a < c:
                ny.append([a, c])
            if d < b:
                ny.append([d, b])
        ut = ny
    return [x for x in ut if x[1] > x[0]]


def _mjuk_bana(arr: np.ndarray, fonster: int = 9) -> np.ndarray:
    """Lågpassfiltrerar en (T, D)-bana med glidande medelvärde för mjuk kamerarörelse."""
    if len(arr) <= 3 or fonster <= 1:
        return arr.copy()
    k = min(fonster, len(arr))
    ut = np.empty_like(arr)
    halv = k // 2
    for i in range(len(arr)):
        a, b = max(0, i - halv), min(len(arr), i + halv + 1)
        ut[i] = arr[a:b].mean(axis=0)
    return ut


def fotkontakt(X: np.ndarray, leder: list[str], golv: float = 0.0) -> dict[str, int]:
    """R3: Fot under golvet lyfts till golvet, knät räknas om med 2-leds-IK och fasta benlängder."""
    ix = {n: i for i, n in enumerate(leder)}
    andrade = {}
    for s in ("l", "r"):
        if not all(f"{s}_{n}" in ix for n in ("upleg", "lowleg", "foot")):
            continue
        h, k, f = ix[f"{s}_upleg"], ix[f"{s}_lowleg"], ix[f"{s}_foot"]
        b = ix.get(f"{s}_ball")
        L1 = float(np.median(np.linalg.norm(X[:, k] - X[:, h], axis=1)))
        L2 = float(np.median(np.linalg.norm(X[:, f] - X[:, k], axis=1)))
        n = 0
        for t in range(len(X)):
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
            if b is not None:
                X[t, b] = X[t, b] + (X[t, f] - Ft)
                X[t, b, 2] = max(X[t, b, 2], golv + TA_OVER_GOLV)
            n += 1
        if n:
            andrade[s] = n
    return andrade


def _dra_in_dolda_ben_bakom_massiv_disk(X: np.ndarray, leder: list[str], disk_obj: dict, golv: float = 0.0) -> int:
    """När en person står/sitter vid en disk/bord (där ben/höfter är skymda eller når över kanten) kan SAM 3D Body
    placera höfter, knän eller underarmar precis inuti diskvolymen. Denna funktion håller kroppen utanför disklådan."""
    ix = {n: i for i, n in enumerate(leder)}
    p = np.array(disk_obj["pos"], dtype=float)
    m = np.array(disk_obj["matt"], dtype=float) / 2.0 + 0.02
    rz = disk_obj["rot"][2]
    R = np.array([[math.cos(rz), -math.sin(rz), 0.0], [math.sin(rz), math.cos(rz), 0.0], [0.0, 0.0, 1.0]])
    sp2 = ix["c_spine2"]
    arm_leder = {
        ix[n] for n in ("l_lowarm", "r_lowarm", "l_wrist", "r_wrist", "l_hand_mitt", "r_hand_mitt", "l_index1", "r_index1")
        if n in ix
    }
    andrade = 0

    for t in range(len(X)):
        bal_lok = (X[t, sp2] - p) @ R
        for j in range(X.shape[1]):
            lok = (X[t, j] - p) @ R
            if (np.abs(lok) <= m).all():
                if j in arm_leder and lok[2] >= 0.0:
                    # Händer/underarmar som vilar på eller sträcker sig över disken lyfts till precis ovanpå skivan
                    lok[2] = m[2] + 0.015
                elif abs(bal_lok[1]) / max(m[1], 1e-6) >= abs(bal_lok[0]) / max(m[0], 1e-6):
                    sida_y = 1.0 if bal_lok[1] >= 0 else -1.0
                    lok[1] = sida_y * (m[1] + 0.025)
                else:
                    sida_x = 1.0 if bal_lok[0] >= 0 else -1.0
                    lok[0] = sida_x * (m[0] + 0.025)
                X[t, j] = p + (lok @ R.T)
                if j in (ix.get("l_foot"), ix.get("r_foot")):
                    X[t, j, 2] = max(X[t, j, 2], golv + FOTLED_OVER_GOLV)
                andrade += 1
    return andrade


def _trohet_mot_2d(
    X: np.ndarray,
    X_ra_2d: np.ndarray,
    C_per_ruta: np.ndarray,
    R_cam: np.ndarray,
    f_px: float,
    W: int,
    H: int,
) -> dict:
    """Beräknar 2D-reprojektionstrohet (G7) med stöd för rörlig kamera C_per_ruta (T, 3)."""
    c = (X - C_per_ruta[:, None, :]) @ R_cam
    d = np.maximum(-c[..., 2], 1e-4)
    uv = c[..., :2] / d[..., None] * np.array([f_px, -f_px]) + np.array([W / 2.0, H / 2.0])
    diff = np.linalg.norm(uv - X_ra_2d, axis=-1)
    medel_px = float(np.median(diff))
    ious = []
    for t in range(len(uv)):
        b1 = np.array([uv[t, :, 0].min(), uv[t, :, 1].min(), uv[t, :, 0].max(), uv[t, :, 1].max()])
        b2 = np.array([X_ra_2d[t, :, 0].min(), X_ra_2d[t, :, 1].min(), X_ra_2d[t, :, 0].max(), X_ra_2d[t, :, 1].max()])
        lo = np.maximum(b1[:2], b2[:2])
        hi = np.minimum(b1[2:], b2[2:])
        inter = float(np.maximum(hi - lo, 0.0).prod())
        union = float(np.maximum(b1[2:] - b1[:2], 0.0).prod() + np.maximum(b2[2:] - b2[:2], 0.0).prod() - inter)
        ious.append(inter / max(union, 1e-9))
    iou_med = float(np.median(ious))
    andel = medel_px / max(float(H), 1.0)
    return dict(
        offset_bildhojd=round(andel, 4),
        skala=1.0,
        iou=round(iou_med, 3),
        flaggad=bool(andel > 0.03 or iou_med < 0.65),
        rutor=len(uv),
    )



def _rekonstruera_skymda_ben(
    X: np.ndarray,
    leder: list[str],
    pose_etikett: str,
    ben_synliga_arr: np.ndarray,
    golv: float = 0.0,
) -> dict:
    """S2: Rekonstruerar skymda ben (där ben_synliga==False) utan att röra överkroppen (c_spine0 och uppåt).
    Bevarar konstanta anatomiska benlängder per person (H8 CV ~ 0) och undviker SAM:s skymda huk (knä 0.14-0.22 m).
    """
    ix = {n: i for i, n in enumerate(leder)}
    T = len(X)
    mask_skymd = ~np.asarray(ben_synliga_arr, dtype=bool)
    n_skymd = int(mask_skymd.sum())
    if n_skymd == 0:
        return dict(andrade_rutor=0, status="observed")

    # Mät personens egna medianlängder för lår och skenben (begränsade till realistiskt vuxenspann)
    l1_l = np.linalg.norm(X[:, ix["l_lowleg"]] - X[:, ix["l_upleg"]], axis=-1)
    l1_r = np.linalg.norm(X[:, ix["r_lowleg"]] - X[:, ix["r_upleg"]], axis=-1)
    l2_l = np.linalg.norm(X[:, ix["l_foot"]] - X[:, ix["l_lowleg"]], axis=-1)
    l2_r = np.linalg.norm(X[:, ix["r_foot"]] - X[:, ix["r_lowleg"]], axis=-1)
    L1_raw = float(np.median(np.r_[l1_l, l1_r]))
    L2_raw = float(np.median(np.r_[l2_l, l2_r]))
    L1 = float(np.clip(L1_raw, 0.36, 0.46))
    L2 = float(np.clip(L2_raw, 0.36, 0.45))

    # Mjuk horisontell framåtriktning ur axellinjen (oberoende av skymda höfter!)
    ax_all = X[:, ix["r_uparm"]] - X[:, ix["l_uparm"]]
    ax_all[:, 2] = 0.0
    ax_med = np.median(ax_all, axis=0)
    if np.linalg.norm(ax_med) < 1e-4:
        ax_med = np.array([1.0, 0.0, 0.0])
    hoger = ax_med / (np.linalg.norm(ax_med) + 1e-9)
    fram = np.cross(hoger, np.array([0.0, 0.0, 1.0]))
    fram[2] = 0.0
    fram = fram / (np.linalg.norm(fram) + 1e-9)
    # Kontrollera tecken mot blickriktningen (c_head -> nasa_mal) så att knäna pekar framåt, inte bakåt!
    blick = np.median(X[:, ix["nasa_mal"], :2] - X[:, ix["c_head"], :2], axis=0)
    if float(fram[:2] @ blick) < 0.0:
        fram = -fram
        hoger = -hoger

    hoft_bredd = float(np.clip(0.5 * np.median(np.linalg.norm(X[:, ix["r_upleg"], :2] - X[:, ix["l_upleg"], :2], axis=-1)), 0.08, 0.13))
    fot_z_mal = golv + FOTLED_OVER_GOLV
    ta_z_mal = golv + TA_OVER_GOLV

    for t in range(T):
        if not mask_skymd[t]:
            continue
        sp0 = X[t, ix["c_spine0"]].copy()
        for sida, tecken in (("l", -1.0), ("r", +1.0)):
            hoft = sp0 + hoger * (tecken * hoft_bredd) + np.array([0.0, 0.0, -0.04])
            if pose_etikett == "sittande":
                # Vågrätt / lätt sluttande lår (~12°), knä >= 0.36 m, skenben rakt/lätt indraget till golv med exakt L2
                dz_lar = -L1 * math.sin(math.radians(12.0))
                kna_z = max(0.36, min(hoft[2] + dz_lar, fot_z_mal + L2 - 0.005))
                dz_faktisk = kna_z - hoft[2]
                hor_lar = math.sqrt(max(L1 ** 2 - dz_faktisk ** 2, 1e-4))
                kna = np.array([hoft[0] + fram[0] * hor_lar, hoft[1] + fram[1] * hor_lar, kna_z])
                dz_sken = kna_z - fot_z_mal
                if dz_sken <= L2:
                    hor_sken = math.sqrt(max(L2 ** 2 - dz_sken ** 2, 0.0))
                    fot = np.array([kna[0] - fram[0] * 0.5 * hor_sken, kna[1] - fram[1] * 0.5 * hor_sken, fot_z_mal])
                    # Exakt normering till L2
                    v_sk = fot - kna
                    if np.linalg.norm(v_sk) > 1e-6:
                        # Behåll z om möjligt via horisontell cirkelskärning
                        fot = np.array([kna[0] - fram[0] * hor_sken, kna[1] - fram[1] * hor_sken, fot_z_mal])
                else:
                    fot = kna + np.array([0.0, 0.0, -L2])
            else:
                # Stående bakom disk: ben nästan raka ned mot golvet med lätt naturlig knäböj (exakta L1, L2)
                hojd_till_fot = max(hoft[2] - fot_z_mal, 0.10)
                if hojd_till_fot >= L1 + L2 - 0.005:
                    # Bäcken högt nog för raka ben; behåll benlängd L1+L2 och låt fot nå golv eller sväva minimalt
                    eff_L1, eff_L2 = L1, L2
                    kna = hoft + np.array([0.0, 0.0, -eff_L1]) + fram * 0.015
                    kna = hoft + (kna - hoft) / np.linalg.norm(kna - hoft) * eff_L1
                    fot = kna + np.array([0.0, 0.0, -eff_L2])
                else:
                    # 2-leds-IK rakt ned till fot på golvet med lätt framåtböjt knä
                    dist = min(hojd_till_fot, L1 + L2 - 1e-4)
                    a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2.0 * max(dist, 1e-6))
                    hh = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
                    kna = hoft + np.array([0.0, 0.0, -a]) + fram * hh
                    fot = hoft + np.array([0.0, 0.0, -dist])
            ta = np.array([fot[0] + fram[0] * 0.12, fot[1] + fram[1] * 0.12, max(ta_z_mal, fot[2] - 0.045)])
            X[t, ix[f"{sida}_upleg"]] = hoft
            X[t, ix[f"{sida}_lowleg"]] = kna
            X[t, ix[f"{sida}_foot"]] = fot
            X[t, ix[f"{sida}_ball"]] = ta

    return dict(andrade_rutor=n_skymd, totalt_rutor=T, andel=round(n_skymd / max(T, 1), 3),
                L1=round(L1, 3), L2=round(L2, 3), status="antagen")


def _ladda_exakt_semantik(ingest: pathlib.Path, semantik_fil: pathlib.Path | None = None) -> dict | None:
    """S5: Läser semantik.json ENBART via explicit sökväg eller direkt inuti ingest-mappen (aldrig delsträngsmatchning)."""
    kandidater = []
    if semantik_fil is not None:
        kandidater.append(pathlib.Path(semantik_fil))
    kandidater.append(ingest / "semantik/semantik.json")
    for k in kandidater:
        if k.exists():
            raw = json.loads(k.read_text(encoding="utf-8"))
            return raw.get("data", raw)
    return None



def _bygg_mening_och_medielager(
    ingest: pathlib.Path,
    semantik_fil: pathlib.Path | None,
    tagningar: list[dict],
    personer_meta: dict,
    recept: Recept,
    fps: float,
) -> dict:
    """S5: Lyfter in semantikens repliker, skärmtext, scenfunktioner och bärande kärna direkt i scenpaket/2."""
    sem = _ladda_exakt_semantik(ingest, semantik_fil)
    if sem is None:
        return dict(repliker=[], skarmtext=[], scener=[], karna="", sammanfattning="",
                    roller=personer_meta, rum_relationer={"tro": recept.tro}, semantik_kalla=None)

    kl_info = sem.get("klipp") or {}
    karna = kl_info.get("karna", "")
    samman = kl_info.get("sammanfattning", "")
    plats_txt = (sem.get("plats") or {}).get("typ") or (sem.get("plats") or {}).get("beskrivning") or recept.tro

    # Mappa semantikens P1/P2/P3 -> paketets A/B/C
    p_till_roll = {f"P{i+1}": chr(ord("A") + i) for i in range(6)}
    tagn_map = {t["id"]: t for t in tagningar}
    tagn_sem = {str(x.get("tagning", "")).lower(): x for x in (sem.get("tagningar") or [])}

    repliker = []
    for r in (sem.get("repliker") or []):
        sid = str(r.get("tagning", "")).lower()
        t_obj = tagn_map.get(sid)
        a_ruta = int(round(float(r.get("start_s", 0.0)) * fps))
        if t_obj is not None:
            a_ruta = max(t_obj["ut"][0], min(a_ruta, t_obj["ut"][1] - 1))
        funktion = (tagn_sem.get(sid) or {}).get("funktion", "")
        repliker.append(dict(
            id=r.get("id", f"r_{len(repliker)+1}"),
            talare=p_till_roll.get(r.get("talare", ""), r.get("talare", "")),
            tagning=sid,
            text=r.get("text", ""),
            start_s=float(r.get("start_s", 0.0)),
            slut_s=float(r.get("slut_s", 0.0)),
            a=a_ruta,
            barande=bool(funktion in ("krok", "vandning", "punchline")),
        ))

    skarmtext = []
    for idx, st in enumerate(sem.get("skarmtext") or []):
        sid = str(st.get("tagning", "")).lower()
        funktion = (tagn_sem.get(sid) or {}).get("funktion", "")
        txt = st.get("text", "")
        bar = bool(funktion in ("krok", "vandning", "punchline") or "vs" in txt.lower())
        skarmtext.append(dict(id=f"st_{idx+1}", tagning=sid, text=txt, barande=bar, funktion=funktion))

    scener = []
    for t in tagningar:
        sid = t["id"]
        a0, b0 = t["ut"]
        ts = tagn_sem.get(sid, {})
        funktion = ts.get("funktion") or "scen"
        sc_rep = [r for r in repliker if r["tagning"] == sid]
        sc_txt = [x for x in skarmtext if x["tagning"] == sid]
        scener.append(dict(
            tagning=sid,
            ut=[a0, b0],
            start_s=round(a0 / fps, 2),
            slut_s=round(b0 / fps, 2),
            langd_s=round((b0 - a0) / fps, 2),
            vem=[p["id"] for p in t["personer"]] or ["ingen_person_i_bild"],
            var=plats_txt,
            funktion=funktion,
            vad=ts.get("vad") or f"Tagning {sid}",
            repliker=[r["text"] for r in sc_rep],
            skarmtext=[x["text"] for x in sc_txt],
            barande=bool(funktion in ("krok", "vandning", "punchline")),
        ))

    return dict(
        karna=karna,
        sammanfattning=samman,
        tal_finns=bool(kl_info.get("tal_finns", bool(repliker))),
        sprak=kl_info.get("sprak", "okand"),
        repliker=repliker,
        skarmtext=skarmtext,
        scener=scener,
        roller=personer_meta,
        rum_relationer={"tro": recept.tro},
        semantik_kalla=str(semantik_fil) if semantik_fil else str(ingest / "semantik/semantik.json"),
    )


def kompilera_scenpaket(
    klipp_namn: str,
    ingest: pathlib.Path,
    obs: Observationer,
    recept: Recept,
    ut_mapp: pathlib.Path,
    steg: int = 1,
    semantik_fil: pathlib.Path | None = None,
) -> pathlib.Path:
    IX = {
        n: i
        for i, n in enumerate(
            json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"]
        )
    }
    N = recept.rutor
    fps = recept.fps
    W, H = obs.klipp[0].kamera.bild_px
    sensor_mm = 36.0
    golv_z = 0.0
    beslut = []

    kam_map = {c.klipp: c for c in recept.kameror}
    tagningar = []
    rorelse: dict[str, list] = {}
    personer_meta: dict[str, dict] = {}
    trohet_map: dict[str, dict] = {}
    sittande_backen: dict[str, list[np.ndarray]] = {}
    alla_kroppspunkter_per_tagn: dict[str, dict[str, np.ndarray]] = {}
    alla_u_per_tagn: dict[str, dict[str, list[int]]] = {}

    import obs_motor
    fk = obs_motor._fokal(ingest)

    for k_obs in obs.klipp:
        sid = k_obs.klipp
        S_dir = ingest / sid.upper()
        a0, b0 = k_obs.rutor
        cam_nod = kam_map.get(sid)
        if cam_nod is None:
            continue

        C_world = np.array(cam_nod.position, dtype=float)
        R_cam = _euler_xyz_till_mat(cam_nod.rotation[0], cam_nod.rotation[1], cam_nod.rotation[2])  # STEG S1
        q_cam = mat_till_quat(R_cam)
        hfov_rad = math.radians(cam_nod.hfov_deg)
        lins_mm = round(sensor_mm / (2.0 * math.tan(hfov_rad / 2.0)), 2)
        f_px = lins_mm / sensor_mm * W

        df_lista = sorted(glob.glob(str(S_dir / "rum/depth/*.npz")))
        K_mat = np.load(df_lista[0])["intrinsics"]
        f_kedja = float(K_mat[0, 0] * W)
        f_sann = fk[0] if fk else f_kedja
        kappa = f_sann / f_kedja

        p_dets = [d for d in k_obs.detektioner if d.klass == "person"]
        p_fil = S_dir / "personer.json"
        sp_map = json.loads(p_fil.read_text(encoding="utf-8")) if p_fil.exists() else {}
        spar_lista = sorted(sp_map, key=lambda s: -len(sp_map[s]))

        tagn_personer = []
        alla_kroppspunkter_per_tagn[sid] = {}
        alla_u_per_tagn[sid] = {}
        kam_bana_per_ruta = None

        for idx_p, d_pers in enumerate(p_dets):
            if idx_p >= len(spar_lista):
                break
            spar_id = spar_lista[idx_p]
            seq_fil = S_dir / f"sekvens_{spar_id}.npz"
            if not seq_fil.exists():
                continue

            pid = d_pers.nyckel.split(":")[-1] if (d_pers.nyckel and ":" in d_pers.nyckel) else d_pers.id
            if pid == "okand":
                p_nod = next(
                    (
                        n for n in recept.noder
                        if n.klass == "person" and not str(n.nyckel).endswith((":A", ":B", ":C")) and sid in n.evidence_shots
                    ),
                    None,
                )
                pid = p_nod.id if p_nod else f"gast_{sid}"

            ankare_stol = f"stol_{pid}" if d_pers.pose == "sittande" else None
            tagn_personer.append(dict(id=pid, ankare=ankare_stol))
            personer_meta.setdefault(
                pid,
                dict(
                    roll=pid,
                    farg=ROLL_FARG.get(pid, "#bbbbbb"),
                    hemplats=ankare_stol,
                    pose=d_pers.pose or "staende",
                ),
            )

            q_seq = np.load(seq_fil)
            n_seq = len(q_seq["pose"])
            # STEG S1: exakt pinhole-djupskalning f_px/f_sam (bevarar bålens 2D-läge och 3D-strålriktning)
            djup_skala = np.array([1.0, 1.0, f_px / float(q_seq["fokal"])])
            ben_synl_raw = q_seq["ben_synliga"] if "ben_synliga" in q_seq.files else np.ones(n_seq, bool)
            kand_raw = q_seq["kand"] if "kand" in q_seq.files else np.ones(n_seq, bool)
            har_synliga_ben = float(np.mean(ben_synl_raw)) >= 0.30
            kallor = [
                HARLEDD.get(n, (n,)) if n not in ("huvud_upp", "nasa_mal") else ("c_head",)
                for n in LEDER_T1
            ]

            U, XS, X_RA_2D, BEN_S = [], [], [], []
            raw_fots, raw_backen = [], []
            sp2_ix = IX["c_spine2"]
            for u in range(a0, b0):
                f_ix = min(u - a0, n_seq - 1)
                if not bool(kand_raw[f_ix]):
                    continue
                pose_f = q_seq["pose"][f_ix]
                ct_raw = q_seq["cam_t_ra"][f_ix]
                bal_m = pose_f[sp2_ix, :3] / 100.0
                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala
                alla_w = (c_cam @ R_cam.T) + C_world
                raw_fots.append(min(alla_w[IX["l_foot"], 2], alla_w[IX["r_foot"], 2]))
                raw_backen.append(alla_w[IX["c_spine0"], 2])
            med_fot_z = float(np.median(raw_fots)) if raw_fots else 0.0
            med_backen_z = float(np.median(raw_backen)) if raw_backen else 0.55

            # STEG S1: Flytta bara kamera + kropp tillsammans när faktisk kroppshöjd avviker från fysiskt spann.
            # Flytta ALDRIG kameran efter hallucinerade skymda SAM-fötter när ben_synliga == False!
            z_skift = 0.0
            if d_pers.pose == "staende":
                if har_synliga_ben and med_fot_z > 0.08:
                    z_skift = -(med_fot_z - FOTLED_OVER_GOLV)
                elif not har_synliga_ben:
                    if med_backen_z < 0.78:
                        z_skift = 0.86 - med_backen_z
                    elif med_backen_z > 1.12:
                        z_skift = 0.96 - med_backen_z
            elif d_pers.pose == "sittande":
                mal_backen_z = float(sittande_backen[pid][0][2]) if pid in sittande_backen else 0.55
                if abs(med_backen_z - mal_backen_z) > 0.12:
                    z_skift = mal_backen_z - med_backen_z
            z_kropp = 0.0
            if idx_p == 0 and z_skift != 0.0:
                # Håll kamera+kropp ihop (z_kropp=0) men begränsa skiftet till <= 2.5*sigma från obs-höjd (min 0.78 m)
                obs_h = float(k_obs.kamera.hojd_m.v)
                obs_s = float(k_obs.kamera.hojd_m.s)
                ny_cz = float(np.clip(C_world[2] + z_skift, max(0.78, obs_h - 2.4 * obs_s), obs_h + 2.4 * obs_s))
                C_world[2] = ny_cz
                q_cam = mat_till_quat(R_cam)
                beslut.append(dict(regel="S1_kamera_hojd_kalibrering", person=pid, tagning=sid,
                                   kamera_z=round(ny_cz, 3), obs_hojd=obs_h, z_skift_onskad=round(z_skift, 3)))
            # För idx_p > 0: aldrig okompenserad z_kropp som bryter 2D-projektionen!

            # STEG S3: Filtrera bort spökrutor (kand == False) utom om hela tagningen saknar kand
            giltiga_u = [u for u in range(a0, b0) if bool(kand_raw[min(u - a0, n_seq - 1)])]
            if not giltiga_u:
                giltiga_u = [a0]
            n_spok_bort = (b0 - a0) - len(giltiga_u)
            if n_spok_bort > 0:
                beslut.append(dict(regel="S3_kand_spokfilter", person=pid, tagning=sid,
                                   borttagna_rutor=n_spok_bort, kvar_rutor=len(giltiga_u),
                                   orsak="Rutor utan bilddetektion (kand=False) filtreras bort för att undvika spökkroppar."))

            for u in giltiga_u:
                if (u - a0) % steg and u != giltiga_u[-1]:
                    continue
                f_ix = min(u - a0, n_seq - 1)
                pose_f = q_seq["pose"][f_ix]
                ct_raw = q_seq["cam_t_ra"][f_ix]
                bal_m = pose_f[sp2_ix, :3] / 100.0
                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala
                alla_w = (c_cam @ R_cam.T) + C_world
                if z_kropp != 0.0:
                    alla_w[:, 2] += z_kropp
                BEN_S.append(bool(ben_synl_raw[f_ix]))

                hi = IX["c_head"]
                Mh = R_cam @ quat_xyzw(pose_f[hi, 3:7]) @ quat_xyzw(q_seq["rest"][hi, 3:7]).T
                harl = {
                    "huvud_upp": alla_w[hi] + Mh @ np.array([0.0, 0.10, 0.0]),
                    "nasa_mal": alla_w[hi] + Mh @ np.array([0.0, 0.03, 0.12]),
                }
                t1_pts = np.array([
                    harl[n] if n in harl else alla_w[[IX[q] for q in k]].mean(axis=0)
                    for n, k in zip(LEDER_T1, kallor)
                ])
                XS.append(t1_pts)
                U.append(u)

                c_ra = (t1_pts - C_world) @ R_cam
                d_ra = np.maximum(-c_ra[:, 2], 1e-4)
                uv_ra = c_ra[:, :2] / d_ra[:, None] * np.array([f_px, -f_px]) + np.array([W / 2.0, H / 2.0])
                X_RA_2D.append(uv_ra)

            X = np.array(XS)
            X_RA_2D_arr = np.array(X_RA_2D)

            # --- Punkt 4: Separera kamerarörelse (inåkning/panorering) från falsk rotglidning i kroppen! ---
            sp0_t1 = LEDER_T1.index("c_spine0")
            if idx_p == 0 and len(p_dets) == 1 and len(X) > 5:
                backen_xy = X[:, sp0_t1, :2]
                ankare_xy = np.median(backen_xy, axis=0)
                drift_span = float(np.linalg.norm(backen_xy.max(axis=0) - backen_xy.min(axis=0)))
                if drift_span > 0.18:
                    # Lågpassfiltrerad glidning i XY kommer från kamerans rörelse, inte från att en person vid ett bord/disk glider
                    delta_xy = _mjuk_bana(backen_xy - ankare_xy, fonster=9)
                    delta_3d = np.column_stack([delta_xy, np.zeros(len(X))])
                    X = X - delta_3d[:, None, :]
                    kam_bana_per_ruta = C_world[None, :] - delta_3d
                    beslut.append(dict(
                        regel="R25_separera_kamerarorelse",
                        person=pid,
                        tagning=sid,
                        drift_m=round(drift_span, 3),
                        orsak=(
                            f"Bäckenet gled {drift_span:.2f} m i kameraramen medan {pid} stod vid sin plats; "
                            f"driften överfördes till CAM_{sid} (inåkning/panorering) med 0 px 2D-avvikelse."
                        ),
                    ))

            # STEG S2: Rekonstruera skymda ben anatomiskt (märkt antagen) utan att ändra synlig överkropp!
            skymd_info = _rekonstruera_skymda_ben(X, LEDER_T1, d_pers.pose or "staende", np.array(BEN_S, bool), golv_z)
            if skymd_info["andrade_rutor"] > 0:
                beslut.append(dict(regel="S2_skymda_ben_antagen", person=pid, tagning=sid, **skymd_info,
                                   orsak="Underkropp saknar bildstöd (ben_synliga=False); ben rekonstruerade anatomiskt utan att röra överkroppen."))
            C_arr = kam_bana_per_ruta if kam_bana_per_ruta is not None else np.tile(C_world, (len(X), 1))
            andr = fotkontakt(X, LEDER_T1, golv_z)
            if andr:
                beslut.append(dict(
                    regel="R3_fotkontakt",
                    person=pid,
                    tagning=sid,
                    rutor=andr,
                    orsak="Fot under golvet lyfts till fotledshöjd och knät räknas om med 2-leds-IK.",
                ))

            if d_pers.pose == "sittande":
                sittande_backen.setdefault(pid, []).append(np.median(X[:, sp0_t1, :], axis=0))

            alla_kroppspunkter_per_tagn[sid][pid] = X
            alla_u_per_tagn[sid][pid] = U
            trohet_map[f"{sid}:{pid}"] = _trohet_mot_2d(X, X_RA_2D_arr, C_arr, R_cam, f_px, W, H)

            rutor_int = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X)]
            rorelse.setdefault(pid, []).append(dict(
                tagning=sid,
                ut=[int(min(U)), int(max(U)) + 1] if U else [a0, b0],
                rutor=rutor_int,
            ))

        if kam_bana_per_ruta is not None and p_dets:
            pid0 = list(alla_u_per_tagn[sid].keys())[0]
            U0 = alla_u_per_tagn[sid][pid0]
            nycklar = [
                [int(u)] + _r(c_u) + _r(q_cam, 5) + [lins_mm]
                for u, c_u in zip(U0[::2], kam_bana_per_ruta[::2])
            ]
            if nycklar[-1][0] != U0[-1]:
                nycklar.append([int(U0[-1])] + _r(kam_bana_per_ruta[-1]) + _r(q_cam, 5) + [lins_mm])
            tagningar.append(dict(
                id=sid,
                ut=[a0, b0],
                personer=tagn_personer,
                kamera=dict(statisk=False, nycklar=nycklar),
            ))
        else:
            nyckel_rad = [a0] + _r(C_world) + _r(q_cam, 5) + [lins_mm]
            tagningar.append(dict(
                id=sid,
                ut=[a0, b0],
                personer=tagn_personer,
                kamera=dict(statisk=True, nycklar=[nyckel_rad]),
            ))

    # --- 2. Rumsobjekt (Golv, Väggar, Kontaktkalibrerade Bord/Massiva Diskar, Stolar, Föremål) ---
    objekt = []
    x0, x1, y0, y1 = recept.rum.granser
    th = recept.rum.takhojd_m
    objekt.append(dict(
        id="golv", bas="golv", typ="golv",
        pos=_r([(x0 + x1) / 2, (y0 + y1) / 2, -0.02]),
        rot=[0.0, 0.0, 0.0],
        matt=_r([x1 - x0, y1 - y0, 0.04]),
        farg="#3d3832", status="observed", rum="gemensamt", synlig_ut=[[0, N]],
    ))

    for v in recept.rum.vaggar:
        if v.geometry_source != "observed":
            continue
        if v.sida in ("W", "E"):
            pos = [v.lage_m, (y0 + y1) / 2, th / 2]
            matt = [0.08, y1 - y0, th]
        else:
            pos = [(x0 + x1) / 2, v.lage_m, th / 2]
            matt = [x1 - x0, 0.08, th]
        objekt.append(dict(
            id=f"vagg_{v.sida}", bas=f"vagg_{v.sida}", typ="vagg",
            pos=_r(pos), rot=[0.0, 0.0, 0.0], matt=_r(matt),
            farg="#8a8275", status=v.geometry_source, rum="gemensamt", synlig_ut=[[0, N]],
        ))

    for pid, backen_lista in sittande_backen.items():
        b_med = np.median(np.array(backen_lista), axis=0)
        sits_topp = max(0.35, float(b_med[2]) - 0.10)
        sits_tjock = 0.05
        objekt.append(dict(
            id=f"stol_{pid}", bas=f"stol_{pid}", typ="stol",
            pos=_r([b_med[0], b_med[1], sits_topp - sits_tjock / 2.0]),
            rot=[0.0, 0.0, 0.0],
            matt=_r([0.42, 0.42, sits_tjock]),
            farg="#6b5344", status="antagen", rum="gemensamt", synlig_ut=[[0, N]],
        ))

    # Avgör vilka bord som är massiva bardiskar/serveringsdiskar vs vanliga matbord,
    # och kalibrera överytans höjd mot personernas vilande armbågar/handleder!
    har_staende_huvudroll = any(
        pm.get("pose") == "staende" and pid in ("A", "B")
        for pid, pm in personer_meta.items()
    )
    lw_ix, rw_ix = LEDER_T1.index("l_wrist"), LEDER_T1.index("r_wrist")
    la_ix, ra_ix = LEDER_T1.index("l_lowarm"), LEDER_T1.index("r_lowarm")

    for n in recept.noder:
        if n.klass == "person":
            continue
        pos = list(n.position)
        matt = list(n.dimensions)
        rot_rad = [round(math.radians(a), 4) for a in n.rotation]
        syn_intervall = [[0, N]]

        if n.klass == "bord":
            # Mät armbågs-/handledshöjd i tagningarna där detta bord syns
            arm_zs = []
            for sid in n.evidence_shots:
                for pid, X in alla_kroppspunkter_per_tagn.get(sid, {}).items():
                    z_low = np.minimum(
                        np.minimum(X[:, la_ix, 2], X[:, ra_ix, 2]),
                        np.minimum(X[:, lw_ix, 2], X[:, rw_ix, 2]),
                    )
                    arm_zs.append(float(np.percentile(z_low, 25)))
            topp_z = float(np.clip(np.median(arm_zs) - 0.02, 0.72, 0.96)) if arm_zs else 0.74

            if har_staende_huvudroll:
                # Bardisk / Glassdisk / Serveringsdisk: 14 cm tjock skiva i armbågs-/handledshöjd som syns tydligt
                # som förgrunds-/mellandisk utan att täcka >30 % av bröstkorgen i G6!
                matt[0] = max(matt[0], 1.45)
                matt[1] = 0.44
                skiva_tjock = 0.14
                pos[2] = topp_z - skiva_tjock / 2.0
                matt[2] = skiva_tjock
                ob_temp = dict(pos=pos, matt=matt, rot=rot_rad)
                for sid in n.evidence_shots:
                    for pid, X in alla_kroppspunkter_per_tagn.get(sid, {}).items():
                        n_flytt = _dra_in_dolda_ben_bakom_massiv_disk(X, LEDER_T1, ob_temp, golv_z)
                        if n_flytt:
                            for sp in rorelse.get(pid, []):
                                if sp["tagning"] == sid:
                                    U_sp = [r[0] for r in sp["rutor"]]
                                    sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U_sp, X)]
            else:
                skiva_tjock = 0.06
                pos[2] = topp_z - skiva_tjock / 2.0
                matt[2] = skiva_tjock

        ob_cand = dict(
            id=n.id, bas=n.id, typ=n.klass,
            pos=_r(pos), rot=rot_rad, matt=_r(matt),
            farg="#8c6239" if (n.klass == "bord" and har_staende_huvudroll) else ("#9c7a54" if n.klass == "bord" else ("#e5c07b" if n.klass == "foremal" else "#5c6370")),
            status=n.geometry_source, rum="gemensamt", synlig_ut=syn_intervall,
        )

        bort_iv = []
        for t in tagningar:
            sid = t["id"]
            a0, b0 = t["ut"]
            mitt = (a0 + b0) // 2
            kam = grindar.kamera(t, mitt)
            for pid, X in alla_kroppspunkter_per_tagn.get(sid, {}).items():
                ins = grindar.inne(X, ob_cand)
                if ins.any(axis=1).mean() > 0.05:
                    # Om det var en massiv disk som fortfarande nuddade en bål-/armled, gör den till tjock skiva (0.16 m) i stället för att dölja den!
                    if n.klass == "bord" and ob_cand["matt"][2] > 0.25:
                        topp = ob_cand["pos"][2] + ob_cand["matt"][2] / 2.0
                        ob_cand["matt"][2] = 0.14
                        ob_cand["pos"][2] = round(topp - 0.07, 4)
                        ins = grindar.inne(X, ob_cand)
                    if ins.any(axis=1).mean() > 0.05:
                        if sid in (n.evidence_shots or []):
                            beslut.append(dict(
                                regel="S3_kollision_rapporterad",
                                objekt=n.id, person=pid, tagning=sid,
                                andel=round(float(ins.any(axis=1).mean()), 3),
                                orsak=f"{n.id} är observerat i {sid} och behålls synligt; kollision rapporteras ärligt.",
                            ))
                        else:
                            bort_iv.append([a0, b0])
                            beslut.append(dict(
                                regel="R1_kollisionsskydd",
                                objekt=n.id, person=pid, tagning=sid,
                                orsak=f"{n.id} ej observerat i {sid} och överlappar {pid}; döljs.",
                            ))
                            break
                mid_ix = len(X) // 2
                uv, d_k = grindar.proj(X[mid_ix], kam, W, H, sensor_mm)
                ok_ix = [LEDER_T1.index(nm) for nm in grindar.OVERKROPP if nm in LEDER_T1]
                ob_box = grindar.ruta_box(uv[ok_ix])
                oyta = max(1.0, (ob_box[2] - ob_box[0]) * (ob_box[3] - ob_box[1]))
                pd = float(np.median(d_k))
                huv, dd = grindar.proj(grindar.horn(ob_cand), kam, W, H, sensor_mm)
                if not (dd <= 0.05).any() and np.median(dd) < pd - 0.1:
                    ov = grindar.overlapp(grindar.ruta_box(huv), ob_box) / oyta
                    if ov > 0.25:
                        if sid in (n.evidence_shots or []):
                            beslut.append(dict(
                                regel="S3_skymning_rapporterad",
                                objekt=n.id, person=pid, tagning=sid, tackning=round(float(ov), 3),
                                orsak=f"{n.id} är observerat i {sid} och behålls synligt (täckning {round(ov*100)}%).",
                            ))
                        else:
                            bort_iv.append([a0, b0])
                            beslut.append(dict(
                                regel="R1_skymningsskydd",
                                objekt=n.id, person=pid, tagning=sid,
                                orsak=f"{n.id} ej observerat i {sid} och skymmer {round(ov*100)}%; döljs.",
                            ))
                            break

        if bort_iv:
            ob_cand["synlig_ut"] = [iv for s in ob_cand["synlig_ut"] for iv in _intervall_minus(s, bort_iv)]
        if ob_cand["synlig_ut"]:
            objekt.append(ob_cand)

    rum_lista = [dict(
        id="huvudrum",
        tagningar=[t["id"] for t in tagningar],
        ut=[t["ut"] for t in tagningar],
        platser=[o["id"] for o in objekt],
        status="observed",
        beskrivning=recept.tro,
        regel="Rumshjärnans lösta 3D-rum",
    )]

    paket = dict(
        schema="scenpaket/2",
        klipp=dict(id=klipp_namn, video=str(ingest)),
        tidsbas=dict(fps=fps, antal_rutor=N, regel="Rutor är sanning; sekunder = ruta / fps. Intervall [a, b)."),
        bild=dict(bredd=W, hojd=H, sensor_mm=sensor_mm),
        koordinater="Blender: Z upp, meter; kvaternion (w,x,y,z); kroppens leder i heltal mm.",
        golv_z=golv_z,
        rum=rum_lista,
        huvudrum="huvudrum",
        objekt=objekt,
        tagningar=tagningar,
        personer=personer_meta,
        leder=LEDER_T1,
        rorelse_steg=steg,
        rorelse=rorelse,
        trohet=trohet_map,
        mening=_bygg_mening_och_medielager(ingest, semantik_fil, tagningar, personer_meta, recept, fps),
        beslut=beslut,
        regler="forvarld_karna: R1_rum_och_skymning, R3_fotkontakt, R25_separera_kamerarorelse, T1_armatur_ur_recept",
        proveniens=dict(
            skapad=datetime.datetime.now().isoformat(timespec="seconds"),
            av="forvarld_karna/scen_brygga.py",
        ),
    )

    # STEG S4: Trohet mot oberoende 2D (g7_oberoende) på slutpaketet + en grindrad per (tagning, person)
    import g7_oberoende
    obs_d = json.loads(obs.model_dump_json())
    for r in g7_oberoende.mat_paket(klipp_namn, paket, obs_d, ingest=ingest):
        paket["trohet"][f"{r['tagning']}:{r['person']}"] = dict(
            metod="g7_oberoende", led_med=r["led_med"], led_p90=r["led_p90"], i_box=r["i_box"], iou=r["iou"],
            i_mask=r["i_mask"], spok_andel=r["spok_andel"], flaggad=r["flaggad"], skal=r["skal"])
    ut_mapp.mkdir(parents=True, exist_ok=True)
    paket_fil = ut_mapp / "paket.json"
    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # --- 3. Kör Kvalitetsgrindar G1–G7 (per person) ---
    rader = g7_oberoende.grindar_per_person(paket)
    samman = grindar.sammanfatta(rader)
    (ut_mapp / "paket_grindar.json").write_text(
        json.dumps(
            dict(granser=grindar.GRANS, sammanfattning=samman, rader=rader),
            ensure_ascii=False,
            indent=1,
            default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o),
        ),
        encoding="utf-8",
    )

    tecken = lambda v: "–" if v is None else ("ok" if v else "**FEL**")
    md = [
        f"# Grindrapport: {klipp_namn} (`scenpaket/2`)",
        f"Fel per grind: `{json.dumps(samman, ensure_ascii=False)}`",
        "",
        "| tagning | person | G1 rum | G2 golv | G3 säte | G4 genom | G5 i bild | G6 skymning | G7 trohet |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rader:
        g1 = r["G1_rum"]
        g2 = r.get("G2_golv", {})
        g3 = r.get("G3_sate", {})
        g4 = r.get("G4_genom", {})
        g5 = r.get("G5_ibild", {})
        g6 = r.get("G6_skymning", {})
        g7 = r.get("G7_trohet", {})
        md.append(
            f"| {r['tagning']} | {r.get('person','')} | {tecken(g1['ok'])} {', '.join(g1['fel'])} "
            f"| {tecken(g2.get('ok'))} {g2.get('fot_z_m','')} "
            f"| {tecken(g3.get('ok'))} {g3.get('backen_over_sits_m','')} "
            f"| {tecken(g4.get('ok'))} {g4.get('andel','')} "
            f"| {tecken(g5.get('ok'))} {g5.get('overkropp','')} "
            f"| {tecken(g6.get('ok'))} {g6.get('tackning','') or ''} "
            f"| {tecken(g7.get('ok'))} {g7.get('iou','')} |"
        )
    (ut_mapp / "GRINDAR.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # --- 4. Generera lokal_bygg.py och jutsu_bygg.py ---
    py = str(ROT / "scen/.venv/Scripts/python.exe")
    emit = str(ROT / "byggsten/brygga/emit_bpy.py")
    subprocess.run([py, emit, str(paket_fil), "--kropp", "t1"], cwd=str(ROT), check=True)
    subprocess.run([py, emit, str(paket_fil), "--kropp", "t1", "--jutsu", "--jutsu-steg", "3", "--jutsu-tol", "15"], cwd=str(ROT), check=True)

    return paket_fil


def exportera_recept_bpy(recept_fil: pathlib.Path, ut_fil: pathlib.Path) -> pathlib.Path:
    sys.path.insert(0, str(ROT / "byggsten/rumshypotes"))
    from jutsu_adapter import skript as recept_till_jutsu_bpy
    rec = Recept.model_validate_json(recept_fil.read_text(encoding="utf-8"))
    kod = recept_till_jutsu_bpy(rec)
    ut_fil.parent.mkdir(parents=True, exist_ok=True)
    ut_fil.write_text(kod, encoding="utf-8")
    return ut_fil


def rendera_och_jamfor(ut_mapp: pathlib.Path, ingest: pathlib.Path) -> pathlib.Path | None:
    import cv2

    blender_exe = pathlib.Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not blender_exe.exists():
        return None
    lokal_dir = ut_mapp / "lokal"
    lokal_dir.mkdir(parents=True, exist_ok=True)
    paket_fil = ut_mapp / "paket.json"
    skript_fil = ut_mapp / "lokal_bygg.py"

    subprocess.run(
        [str(blender_exe), "-b", "--factory-startup", "--python", str(skript_fil), "--", str(paket_fil), str(lokal_dir)],
        cwd=str(ROT),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    paket = json.loads(paket_fil.read_text(encoding="utf-8"))
    kolumner = []
    th, tw = 512, 288

    for t in paket["tagningar"]:
        sid = t["id"]
        a0, b0 = t["ut"]
        u = (a0 + b0) // 2
        lokal_f = u - a0
        ren_fil = lokal_dir / f"kontroll_{sid}_{u:03d}.png"
        if not ren_fil.exists():
            continue
        ren_im = cv2.imread(str(ren_fil))
        if ren_im is None:
            continue
        ren_im = cv2.resize(ren_im, (tw, th))

        vid_fil = ingest / "klipp" / f"{sid.upper()}.mp4"
        orig_im = np.zeros((th, tw, 3), dtype=np.uint8)
        if vid_fil.exists():
            cap = cv2.VideoCapture(str(vid_fil))
            cap.set(cv2.CAP_PROP_POS_FRAMES, lokal_f)
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                orig_im = cv2.resize(frame, (tw, th))

        cv2.putText(orig_im, f"{sid.upper()} orig (f={u})", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(ren_im, f"{sid.upper()} forvarld_karna", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 220, 120), 2)
        kolumner.append(np.vstack([orig_im, ren_im]))

    if not kolumner:
        return None
    jamf = np.hstack(kolumner)
    ut_bild = ut_mapp / "jamforelse.png"
    cv2.imwrite(str(ut_bild), jamf)
    return ut_bild
