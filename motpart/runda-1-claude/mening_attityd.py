"""Lager 4: mätbar stabilitet i AttitydProfil, attitydarv i ga_med_attityd, fysik i byt_hand och tidsbudget.

Kör:  scen/.venv/Scripts/python.exe motpart/runda-1-claude/mening_attityd.py

Allt anropar forvarld_karna/mening_motor.py oförändrad (import), på kopior av paketen i minnet.
"""
from __future__ import annotations

import copy
import json
import math
import statistics
import time

import numpy as np

import mening_gemensamt as G
import mening_motor as MM  # forvarld_karna/mening_motor.py (läses, ändras inte)

RNG = np.random.default_rng(11)
FALT = ("lutning_deg", "slapphet", "hand_fart_m_s", "gest_topp_m_s", "uppmarksamhet", "aktiv_hand", "stil_etikett", "kontakt_armar")


def profil_for_rutor(paket: dict, pid: str, sid: str, rutor: list) -> dict:
    p = {k: v for k, v in paket.items() if k != "rorelse"}
    p["rorelse"] = {pid: [dict(tagning=sid, rutor=rutor)]}
    return MM.extrahera_attitydprofil(p)[pid]["per_tagning"][sid]


def med_brus(rutor: list, sigma_m: float) -> list:
    if sigma_m == 0:
        return rutor
    A = np.array(rutor, dtype=float)
    A[:, 1:] += RNG.normal(0, sigma_m * 1000, A[:, 1:].shape)
    return [[int(r[0])] + [int(round(v)) for v in r[1:]] for r in A]


# ------------------------------------------------------------------ 1. stabilitet
def stabilitet(klipp: str, pid: str) -> dict:
    paket = G.las_paket(klipp)
    ut = {}
    for sp in paket["rorelse"][pid]:
        sid = sp["tagning"]
        R = sp["rutor"]
        bas = profil_for_rutor(paket, pid, sid, R)
        rad = dict(bas={k: bas[k] for k in FALT}, n_rutor=len(R))
        # (a) brus: SAM 3D Body-liknande jitter per led och ruta
        for s in (0.005, 0.01, 0.02):
            v = [profil_for_rutor(paket, pid, sid, med_brus(R, s)) for _ in range(20)]
            rad[f"brus_{int(s * 1000)}mm"] = {
                k: [round(float(np.mean([x[k] for x in v])), 3), round(float(np.std([x[k] for x in v])), 3)]
                for k in ("lutning_deg", "slapphet", "hand_fart_m_s", "gest_topp_m_s")}
            rad[f"brus_{int(s * 1000)}mm"]["etiketter"] = sorted({x["stil_etikett"] for x in v})
            rad[f"brus_{int(s * 1000)}mm"]["aktiv_hand"] = sorted({x["aktiv_hand"] for x in v})
        # (b) 1 s-fönster inom tagningen
        fps = float(paket["tidsbas"]["fps"])
        w = int(round(fps))
        fon = [profil_for_rutor(paket, pid, sid, R[i:i + w]) for i in range(0, max(1, len(R) - w + 1), max(1, w // 2))]
        rad["fonster_1s"] = {k: [round(float(min(x[k] for x in fon)), 3), round(float(max(x[k] for x in fon)), 3)]
                             for k in ("lutning_deg", "slapphet", "hand_fart_m_s")}
        rad["fonster_1s"]["etiketter"] = sorted({x["stil_etikett"] for x in fon})
        # (c) glesare sampling (rorelse_steg 2 och 3)
        for steg in (2, 3):
            x = profil_for_rutor(paket, pid, sid, R[::steg])
            rad[f"steg_{steg}"] = {k: x[k] for k in ("lutning_deg", "slapphet", "hand_fart_m_s", "stil_etikett")}
        ut[sid] = rad
    return ut


# ------------------------------------------------------------------ 2. kamerapitch som störfaktor i lutning_deg
def pitch_korrigerad_lutning(klipp: str, pid: str) -> dict:
    """scen_brygga.py:254 bygger R_cam = Euler(90, 0, rz) och kastar receptets pitch/roll.
    Kroppen lyfts genom den nivellerade kameran, så kamerans verkliga lutning hamnar i kroppen.
    Korrigering för riktningar: v_korr = R_sann @ R_niv^T @ v."""
    paket = G.las_paket(klipp)
    rec = json.loads((G.KARNA / "ut" / klipp / "recept.json").read_text(encoding="utf-8"))
    kam = {c["klipp"]: c for c in rec["kameror"]}
    L = G.ix(paket)
    ut = {}
    for sp in paket["rorelse"][pid]:
        sid = sp["tagning"]
        _, X = G.X_av(sp)
        rx_, ry_, rz_ = kam[sid]["rotation"]
        R_niv = G.euler_xyz(90.0, 0.0, rz_)
        R_sann = G.euler_xyz(rx_, ry_, rz_)
        Rk = R_sann @ R_niv.T
        v = X[:, L["c_neck"]] - X[:, L["c_spine0"]]
        vk = v @ Rk.T
        lut = lambda vv: float(np.median(np.degrees(np.arccos(np.clip(vv[:, 2] / np.linalg.norm(vv, axis=-1), -1, 1)))))
        ut[sid] = dict(pitch_recept_deg=round(rx_ - 90.0, 2), roll_recept_deg=round(ry_, 2),
                       lutning_paket_deg=round(lut(v), 1), lutning_pitchkorr_deg=round(lut(vk), 1))
    return ut


# ------------------------------------------------------------------ 3. ga_med_attityd: bevaras attityden? fysik i gången?
def ga_med_attityd_matning() -> dict:
    bas = G.las_paket("guacamole")
    man = G.las_paket("guacamole", "ga_med_attityd")
    pb = MM.extrahera_attitydprofil(bas)["A"]
    pm = MM.extrahera_attitydprofil(man)["A"]
    L = G.ix(man)
    jfr = {}
    for sid in pb["per_tagning"]:
        a, b = pb["per_tagning"][sid], pm["per_tagning"][sid]
        jfr[sid] = {k: [a[k], b[k]] for k in FALT}
    gang = {}
    fps = float(man["tidsbas"]["fps"])
    for sp in man["rorelse"]["A"]:
        sid = sp["tagning"]
        U, X = G.X_av(sp)
        _, Xo = G.X_av(G.spar_for(bas, "A", sid))
        dt = 1.0 / fps
        # benlängder (T1-armaturen i emit_bpy använder FASTA medianlängder – varierande längder går inte att följa)
        lar = np.linalg.norm(X[:, L["l_lowleg"]] - X[:, L["l_upleg"]], axis=-1)
        sken = np.linalg.norm(X[:, L["l_foot"]] - X[:, L["l_lowleg"]], axis=-1)
        lar_o = np.linalg.norm(Xo[:, L["l_lowleg"]] - Xo[:, L["l_upleg"]], axis=-1)
        sken_o = np.linalg.norm(Xo[:, L["l_foot"]] - Xo[:, L["l_lowleg"]], axis=-1)
        # fotglidning: horisontell fotfart när foten är i stödfas (lägsta 30 % av fothöjden)
        glid = []
        for s in "lr":
            f = X[:, L[f"{s}_foot"]]
            v = np.linalg.norm(np.diff(f[:, :2], axis=0), axis=-1) / dt
            z = f[1:, 2]
            stod = z <= np.percentile(z, 30)
            glid.append(float(np.median(v[stod])))
        backen = X[:, L["c_spine0"], :2]
        bv = np.linalg.norm(np.diff(backen, axis=0), axis=-1) / dt
        # fötter som svänger fast bäckenet står still (sista 0.5 s)
        n_slut = int(0.5 * fps)
        fot_slut = max(float(np.ptp(X[-n_slut:, L[f"{s}_foot"], 0])) + float(np.ptp(X[-n_slut:, L[f"{s}_foot"], 1])) for s in "lr")
        backen_slut = float(np.linalg.norm(backen[-1] - backen[-n_slut]))
        # balans: bålens/huvudets horisontella läge mot fötternas mittpunkt
        mitt_fot = (X[:, L["l_foot"], :2] + X[:, L["r_foot"], :2]) / 2
        tp = (X[:, L["c_spine2"], :2] + X[:, L["c_neck"], :2] + X[:, L["c_spine0"], :2]) / 3
        huvud = X[:, L["c_head"], :2]
        # armlängd (fast?) och knävinkel
        ua = np.linalg.norm(X[:, L["l_lowarm"]] - X[:, L["l_uparm"]], axis=-1)
        gang[sid] = dict(
            lar_m_median_min_max=[round(float(np.median(lar)), 3), round(float(lar.min()), 3), round(float(lar.max()), 3)],
            skenben_m_median_min_max=[round(float(np.median(sken)), 3), round(float(sken.min()), 3), round(float(sken.max()), 3)],
            original_lar_skenben_m=[round(float(np.median(lar_o)), 3), round(float(np.median(sken_o)), 3)],
            fot_stodfas_fart_m_s=[round(x, 3) for x in glid],
            backen_fart_median_m_s=round(float(np.median(bv)), 3),
            backen_netto_m=round(float(np.linalg.norm(backen[-1] - backen[0])), 3),
            sista_05s_fotsving_m=round(fot_slut, 3), sista_05s_backen_m=round(backen_slut, 3),
            balans_bal_fram_om_fotmitt_m=round(float(np.median(np.linalg.norm(tp - mitt_fot, axis=-1))), 3),
            huvud_fram_om_fotmitt_m=round(float(np.median(np.linalg.norm(huvud - mitt_fot, axis=-1))), 3),
            overarm_std_mm=round(float(np.std(ua) * 1000), 1),
            fotlyft_max_m=round(float(max(np.ptp(X[:, L["l_foot"], 2]), np.ptp(X[:, L["r_foot"], 2]))), 3),
        )
    # gångriktning: blickriktningen c_head -> nasa_mal i XY (rad 242–244 i mening_motor.py)
    riktning = {}
    for sp in bas["rorelse"]["A"]:
        sid = sp["tagning"]
        _, Xo = G.X_av(sp)
        bl = np.median(Xo[:, L["nasa_mal"], :2] - Xo[:, L["c_head"], :2], axis=0)
        riktning[sid] = round(math.degrees(math.atan2(bl[1], bl[0])), 1)
    return dict(profil_bas=dict(lutning=pb["lutning_deg"], slapphet=pb["slapphet"], stil=pb["stil_etikett"]),
                profil_manip=dict(lutning=pm["lutning_deg"], slapphet=pm["slapphet"], stil=pm["stil_etikett"]),
                per_tagning=jfr, gang=gang, gangriktning_world_deg=riktning)


# ------------------------------------------------------------------ 4. byt_hand: fysisk rimlighet
def byt_hand_matning() -> dict:
    bas = G.las_paket("gelato")
    man = G.las_paket("gelato", "byt_hand")
    L = G.ix(bas)
    ut = {}
    for sp in bas["rorelse"]["A"]:
        sid = sp["tagning"]
        U, Xo = G.X_av(sp)
        _, Xm = G.X_av(G.spar_for(man, "A", sid))
        # spegelplanets normal ur höfterna (som koden) vs ur nyckelbenen
        n_hoft = Xo[:, L["r_upleg"]] - Xo[:, L["l_upleg"]]
        n_hoft[:, 2] = 0
        n_hoft /= np.linalg.norm(n_hoft, axis=-1, keepdims=True)
        n_ax = Xo[:, L["r_clavicle"]] - Xo[:, L["l_clavicle"]]
        n_ax[:, 2] = 0
        n_ax /= np.linalg.norm(n_ax, axis=-1, keepdims=True)
        plan_vinkel = np.degrees(np.arccos(np.clip(np.abs((n_hoft * n_ax).sum(-1)), -1, 1)))
        # axelfäste: var hamnar de nya nyckelbenen relativt de gamla (bålen är oförändrad)?
        fl = np.linalg.norm(Xm[:, L["l_clavicle"]] - Xo[:, L["l_clavicle"]], axis=-1)
        fr = np.linalg.norm(Xm[:, L["r_clavicle"]] - Xo[:, L["r_clavicle"]], axis=-1)
        fu = np.linalg.norm(Xm[:, L["l_uparm"]] - Xo[:, L["l_uparm"]], axis=-1)
        # bålvridning: ändras ryggraden alls?
        bal = [L[n] for n in ("c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head")]
        bal_diff = float(np.abs(Xm[:, bal] - Xo[:, bal]).max())
        # aktiv hand: rutan där högerhanden når längst från bålen (horisontellt)
        rach = np.linalg.norm(Xo[:, L["r_wrist"], :2] - Xo[:, L["c_spine2"], :2], axis=-1)
        i = int(np.argmax(rach))
        mal_fel = float(np.linalg.norm(Xm[i, L["l_wrist"]] - Xo[i, L["r_wrist"]]))
        # handens sidoförskjutning (längs kroppens sidled) – speglingen flyttar målet 2x sidoavståndet
        lat = float(np.dot(Xo[i, L["r_wrist"]] - Xo[i, L["c_spine2"]], n_hoft[i]))
        # passiv arm: armbågens höjd före/efter
        armb_fore = float(np.median(Xo[:, L["l_lowarm"], 2]))
        armb_efter = float(np.median(Xm[:, L["r_lowarm"], 2]))
        # disk: genomträngning före/efter för händer
        disk = next(o for o in man["objekt"] if o["typ"] == "bord")
        inne_o = float(G.grindar.inne(Xo[:, [L["l_wrist"], L["r_wrist"]]], disk).any(axis=1).mean())
        inne_m = float(G.grindar.inne(Xm[:, [L["l_wrist"], L["r_wrist"]]], disk).any(axis=1).mean())
        ut[sid] = dict(
            spegelplan_hoft_vs_axlar_deg_median_p90=[round(float(np.median(plan_vinkel)), 1), round(float(np.percentile(plan_vinkel, 90)), 1)],
            nyckelben_flytt_m_median_max=[round(float(np.median(np.r_[fl, fr])), 3), round(float(np.max(np.r_[fl, fr])), 3)],
            axelled_flytt_m_median=round(float(np.median(fu)), 3),
            ryggrad_max_andring_m=round(bal_diff, 4),
            maxracknings_ruta=int(U[i]),
            ny_hand_till_gammalt_mal_m=round(mal_fel, 3),
            gammal_hand_sidled_fran_bal_m=round(lat, 3),
            passiv_armbage_z_fore_efter_m=[round(armb_fore, 3), round(armb_efter, 3)],
            handled_i_disk_andel_fore_efter=[round(inne_o, 3), round(inne_m, 3)],
        )
    return ut


# ------------------------------------------------------------------ 5. tidsbudget
def tid(f, n=15):
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        t.append((time.perf_counter() - t0) * 1000)
    return dict(median_ms=round(statistics.median(t), 2), max_ms=round(max(t), 2))


def tidsbudget() -> dict:
    ut = {}
    for klipp, op in (("guacamole", "ga_med_attityd"), ("gelato", "byt_hand")):
        f = G.KARNA / "ut" / klipp / "paket.json"
        txt = f.read_text(encoding="utf-8")
        paket = json.loads(txt)
        prof = MM.extrahera_attitydprofil(paket)
        ut[klipp] = dict(
            paket_kb=round(len(txt.encode("utf-8")) / 1024, 1),
            json_las=tid(lambda: json.loads(txt)),
            extrahera_attitydprofil=tid(lambda: MM.extrahera_attitydprofil(paket)),
            bygg_jev_yta=tid(lambda: MM.bygg_jev_yta(paket, prof)),
            deepcopy=tid(lambda: copy.deepcopy(paket)),
            grindar_mat=tid(lambda: G.grindar.mat(paket)),
            manipulera_scen_totalt=tid(lambda: MM.manipulera_scen(paket, op, "A")),
        )
    return ut


if __name__ == "__main__":
    res = dict(
        stabilitet=dict(guacamole_A=stabilitet("guacamole", "A"), guacamole_B=stabilitet("guacamole", "B"),
                        gelato_A=stabilitet("gelato", "A")),
        pitch=dict(guacamole_A=pitch_korrigerad_lutning("guacamole", "A"), guacamole_B=pitch_korrigerad_lutning("guacamole", "B"),
                   gelato_A=pitch_korrigerad_lutning("gelato", "A"), asketch_B=pitch_korrigerad_lutning("asketch", "B"),
                   notan_A=pitch_korrigerad_lutning("notan", "A")),
        ga_med_attityd=ga_med_attityd_matning(),
        byt_hand=byt_hand_matning(),
        tid=tidsbudget(),
    )
    G.spara_json("mening_attityd.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))
