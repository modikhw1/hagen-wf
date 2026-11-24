"""rum_ablation.py — ablation och känslighet för Lager 1–2 utan att röra forvarld_karna/.

Källkoden i forvarld_karna/obs_motor.py och rums_pussel.py läses som text, en namngiven variant
tillämpar exakta strängbyten (varje byte måste träffa exakt en gång, annars avbryts körningen)
och/eller byter regelkonstanter, och modulen körs från minnet. Inga filer i forvarld_karna/ ändras.

    python rum_ablation.py --klipp notan --variant bas
    python rum_ablation.py --klipp notan --alla --parallell 4          # alla varianter, en process var
    python rum_ablation.py --lista

Resultat: en JSON-fil per variant i rum_ut/ablation/<klipp>/<variant>.json.
Lager 2-varianter utan obs-patch återanvänder obs.json från rum_ut/med_dekl/<klipp>/ (eller --obs).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import subprocess
import sys
import time
import types

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
KARNA = ROT / "forvarld_karna"
sys.path.insert(0, str(KARNA))
sys.path.insert(0, str(ROT / "byggsten/rumshypotes"))
sys.path.insert(0, str(KARNA))

import regler  # noqa: E402  (forvarld_karna/regler.py)
from schema import Observationer  # noqa: E402

KLIPP = {
    "guacamole": ("scen/3d/ingest/ut/e-dialog-guacamole-tagningar", None, None),
    "gelato": ("scen/3d/ingest/ut/kand-kennysgelato-tagningar", None, None),
    "asketch": ("scen/3d/ingest/ut/a-sketch-servering-tagningar", None, None),
    "notan": ("scen/3d/ingest/ut/notan-tagningar", "byggsten/rumshypotes/ut/notan/vlm",
              "byggsten/rumshypotes/ut/notan/djup"),
    "btilltal": ("scen/3d/ingest/ut/b-tilltal-ravara-tagningar", None, None),
}

# ------------------------------------------------------------------ patchar (exakta textbyten)
P_GRIND_GAMMAL = [(
    "grind = 3 * d.djup_m.s + 1.0 + 2.0 * (sig_ank + sig_x)",
    "grind = 3 * d.djup_m.s + 1.0",
)]
P_GRIND_UTAN = [(  # ingen grind alls: alla befintliga kandidater prövas
    "if np.linalg.norm(h.x[\"ent\"][x[1]] - pv) < grind:",
    "if True:",
)]
P_KAMERA_MEDEL = [(
    "c = np.average(np.array(pos), axis=0, weights=w_arr)",
    "c = np.mean(np.array(pos), axis=0)",
)]
P_KLUSTERFLYTT_AV = [("    if har_fast_ankare:\n        flyttade_kluster", "    if False:\n        flyttade_kluster")]
P_YAW_EN = [("            return ordnade[:2]\n        return ordnade[:1]", "            return ordnade[:1]\n        return ordnade[:1]")]
P_R22_AV = [("            struktur -= 4.0 * (len(bords) - 1)", "            struktur -= 0.0 * (len(bords) - 1)")]
P_R24_AV = [("            if d.vridning_deg is not None and h.ents[e].unik:\n                k0_phi",
             "            if False:\n                k0_phi")]
P_DELAR_KAMERA_AV_L2 = [
    ("        if o.delar_kamera_med:\n            j = next((jj for jj in range(k) if obs.klipp[jj].klipp == o.delar_kamera_med and h.rum_av.get(jj) == r), None)",
     "        if False:\n            j = None"),
    ("    if o.delar_kamera_med:\n        j = next((jj for jj in range(k) if obs.klipp[jj].klipp == o.delar_kamera_med), None)\n        if j is not None and j in h.x.get(\"cam\", {}):",
     "    if False:\n        j = None\n        if False:"),
]
P_NFEV8 = [("passning = _los(c, obs, k + 1, max_nfev=12)", "passning = _los(c, obs, k + 1, max_nfev=8)")]

# obs_motor
O_PA_3D = [(
    "                kand = min(bord_id, key=lambda k: np.linalg.norm(_hor_xy(t, bord_id[k]) - _hor_xy(t, p)))\n"
    "                if np.linalg.norm(_hor_xy(t, bord_id[kand]) - _hor_xy(t, p)) < 0.95:",
    "                kand = min(bord_id, key=lambda k: np.linalg.norm(bord_id[k] - p))\n"
    "                if np.linalg.norm(bord_id[kand] - p) < 1.0:",
)]
O_PERSON_ROT = [("ut.append(dict(spar=s, roll=roll, p=bal_p,", "ut.append(dict(spar=s, roll=roll, p=ct_med,")]
O_LJUS_60 = [("ljus = M(v=85.0, s=40.0)", "ljus = M(v=60.0, s=45.0)"), ("ljus = M(v=-85.0, s=40.0)", "ljus = M(v=-60.0, s=45.0)")]
O_SIFT_AV = [("delar_kamera_med=sift_koppling.get(S.lower()),", "delar_kamera_med=None,")]
O_R15_SIKT = [("rikt = fram_hor if float(fram_hor @ sikt_hor) > -0.2 else sikt_hor", "rikt = sikt_hor")]
O_KLAMP_AV = [(
    "        self.u = _n(u_clamp)",
    "        self.u = _n(u_raw)",
)]


def _skal(txt_gammal, txt_ny_fmt, faktorer=(0.7, 1.3)):
    """Känslighetsvarianter: ersätt en literal med faktor × värdet."""
    return {f: [(txt_gammal, txt_ny_fmt(f))] for f in faktorer}


VARIANTER: dict[str, dict] = {
    "bas": {},
    # --- Argons fyra "buggrättningar" återställda en i taget (Lager 2)
    "L2_grind_gammal": dict(pussel=P_GRIND_GAMMAL),
    "L2_grind_ingen": dict(pussel=P_GRIND_UTAN),
    "L2_kamera_medel": dict(pussel=P_KAMERA_MEDEL),
    "L2_klusterflytt_av": dict(pussel=P_KLUSTERFLYTT_AV),
    "L2_bugg1_hel_gammal": dict(pussel=P_GRIND_GAMMAL + P_KAMERA_MEDEL + P_KLUSTERFLYTT_AV),
    "L2_yaw_en": dict(pussel=P_YAW_EN),
    "L2_R22_av": dict(pussel=P_R22_AV),
    "L2_R24_av": dict(pussel=P_R24_AV),
    "L2_delar_kamera_av": dict(pussel=P_DELAR_KAMERA_AV_L2),
    "L2_nfev8": dict(pussel=P_NFEV8),
    "L2_alla_rattningar_av": dict(pussel=P_GRIND_GAMMAL + P_KAMERA_MEDEL + P_KLUSTERFLYTT_AV + P_YAW_EN + P_R22_AV),
    # --- konstanter som ändrades mellan byggsten/rumshypotes och forvarld_karna
    "K_foremal_gamla": dict(foremal={"mugg": 0.3, "kopp": 0.3, "glas": 0.3, "bricka": 0.3, "burk": 2.5, "flaska": 2.5}),
    "K_utan_bonaqua": dict(foremal={k: v for k, v in regler.FOREMAL_PRIS.items() if k != "bonaqua"}),
    "K_vid_075": dict(R={"vid_avstand_m": 0.75}),
    "K_alla_gamla": dict(R={"vid_avstand_m": 0.75},
                         foremal={"mugg": 0.3, "kopp": 0.3, "glas": 0.3, "bricka": 0.3, "burk": 2.5, "flaska": 2.5}),
    # --- Lager 1-rättningar återställda (obs byggs om)
    "L1_pa_3d": dict(obs=O_PA_3D),
    "L1_person_rot": dict(obs=O_PERSON_ROT),
    "L1_ljus_60": dict(obs=O_LJUS_60),
    "L1_sift_av": dict(obs=O_SIFT_AV),
    "L1_r15_sikt": dict(obs=O_R15_SIKT),
    "L1_klamp_av": dict(obs=O_KLAMP_AV),
    "L1_alla_gamla": dict(obs=O_PA_3D + O_PERSON_ROT + O_LJUS_60),
    "X_ljus60_yaw_en": dict(obs=O_LJUS_60, pussel=P_YAW_EN),
    # deklarationsfri utan modellsemantik: bara obs_motor._geometrisk_reid_och_pose (SIFT + knävinkel)
    "G_geometrisk_reid": dict(obs=[("    sem = _modell_semantik(ingest)", "    sem = None")], utan_dekl=True),
    "G_semantik_utan_dekl": dict(obs=[], utan_dekl=True, tvinga_obs=True),
    # så nära den gamla kedjan som går i ny kod: Lager 1-rättningar + Lager 2-rättningar + konstanter tillbaka
    "X_allt_gammalt": dict(obs=O_PA_3D + O_PERSON_ROT + O_LJUS_60 + O_R15_SIKT + O_SIFT_AV,
                           pussel=P_GRIND_GAMMAL + P_KAMERA_MEDEL + P_KLUSTERFLYTT_AV + P_YAW_EN + P_R22_AV + P_R24_AV
                           + P_DELAR_KAMERA_AV_L2 + P_NFEV8,
                           R={"vid_avstand_m": 0.75},
                           foremal={"mugg": 0.3, "kopp": 0.3, "glas": 0.3, "bricka": 0.3, "burk": 2.5, "flaska": 2.5}),
    "X_ljus60_bugg1_gammal": dict(obs=O_LJUS_60, pussel=P_GRIND_GAMMAL + P_KAMERA_MEDEL + P_KLUSTERFLYTT_AV),
}

# --- känslighet ±30 % på konstanter som inte finns i regler.py (Lager 2)
for f, p in _skal("grind = 3 * d.djup_m.s + 1.0 + 2.0 * (sig_ank + sig_x)",
                  lambda f: f"grind = 3 * d.djup_m.s + 1.0 + {2.0 * f:.3f} * (sig_ank + sig_x)").items():
    VARIANTER[f"S_grindfaktor_{f}"] = dict(pussel=p)
for f, p in _skal("struktur -= 4.0 * (len(bords) - 1)", lambda f: f"struktur -= {4.0 * f:.3f} * (len(bords) - 1)").items():
    VARIANTER[f"S_R22straff_{f}"] = dict(pussel=p)
for f, p in _skal("if abs(wrap(ordnade[1] - ll - h.x[\"alfa\"])) < 70.0 * D2R or o.manhattan_deg.s > 8.0:",
                  lambda f: f"if abs(wrap(ordnade[1] - ll - h.x[\"alfa\"])) < {70.0 * f:.3f} * D2R or o.manhattan_deg.s > {8.0 * f:.3f}:").items():
    VARIANTER[f"S_yawgrans_{f}"] = dict(pussel=p)
for f in (0.7, 1.3):
    VARIANTER[f"S_klusterradie_{f}"] = dict(pussel=[
        ("if s2 >= 1.0 and np.linalg.norm(p2 - p_old) < 2.2:", f"if s2 >= 1.0 and np.linalg.norm(p2 - p_old) < {2.2 * f:.3f}:"),
        ("if sc >= 1.0 and np.linalg.norm(cam_old[:2] - p_old) < 2.8:", f"if sc >= 1.0 and np.linalg.norm(cam_old[:2] - p_old) < {2.8 * f:.3f}:"),
    ])
    VARIANTER[f"S_R24sigma_{f}"] = dict(pussel=[("s_vr = 35.0 * D2R", f"s_vr = {35.0 * f:.3f} * D2R")])
    # regelkonstanter i regler.py
    for nyckel in ("vid_avstand_m", "sigma_vid_m", "sigma_pa_m", "pris_entitet", "pris_bakgrundsbord", "sigma_ljus_deg",
                   "sigma_blick_deg", "p_miss_fast", "p_miss_foremal", "bord_minsta_avstand_m", "rum_typ_m"):
        VARIANTER[f"S_R_{nyckel}_{f}"] = dict(R={nyckel: regler.R[nyckel] * f})
    VARIANTER[f"S_foremalpris_{f}"] = dict(foremal={k: v * f for k, v in regler.FOREMAL_PRIS.items()})
    # Lager 1-konstanter (obs byggs om)
    VARIANTER[f"S_L1_pa_{f}"] = dict(obs=[("_hor_xy(t, p)) < 0.95:", f"_hor_xy(t, p)) < {0.95 * f:.3f}:")])
    VARIANTER[f"S_L1_vidsitt_{f}"] = dict(obs=[("_hor_xy(t, pp[\"p\"])) < 1.6:", f"_hor_xy(t, pp[\"p\"])) < {1.6 * f:.3f}:")])
    VARIANTER[f"S_L1_vidsta_{f}"] = dict(obs=[("_hor_xy(t, pp[\"p\"])) < 1.35:", f"_hor_xy(t, pp[\"p\"])) < {1.35 * f:.3f}:")])
    VARIANTER[f"S_L1_r15_{f}"] = dict(obs=[("ankare[i] = pp[\"p\"] + 0.55 * rikt", f"ankare[i] = pp[\"p\"] + {0.55 * f:.3f} * rikt")])
    VARIANTER[f"S_L1_bearing35_{f}"] = dict(obs=[("abs(t.hor(q)[0] - pb) < 35 or", f"abs(t.hor(q)[0] - pb) < {35 * f:.2f} or")])
    VARIANTER[f"S_L1_skivapx_{f}"] = dict(obs=[("if nedre.sum() < 25000:", f"if nedre.sum() < {int(25000 * f)}:"),
                                                ("if skiva_mask.sum() < 15000:", f"if skiva_mask.sum() < {int(15000 * f)}:")])
    VARIANTER[f"S_L1_ljus85_{f}"] = dict(obs=[("ljus = M(v=85.0, s=40.0)", f"ljus = M(v={85.0 * f:.2f}, s=40.0)"),
                                               ("ljus = M(v=-85.0, s=40.0)", f"ljus = M(v={-85.0 * f:.2f}, s=40.0)")])
    VARIANTER[f"S_L1_klamp_{f}"] = dict(obs=[
        ("np.clip(u_raw[0], -math.sin(math.radians(8)), math.sin(math.radians(8)))",
         f"np.clip(u_raw[0], -math.sin(math.radians({8 * f:.2f})), math.sin(math.radians({8 * f:.2f})))"),
        ("min(u_raw[1], -math.cos(math.radians(18)))", f"min(u_raw[1], -math.cos(math.radians({18 * f:.2f})))"),
        ("np.clip(u_raw[2], -math.sin(math.radians(18)), math.sin(math.radians(18)))",
         f"np.clip(u_raw[2], -math.sin(math.radians({18 * f:.2f})), math.sin(math.radians({18 * f:.2f})))"),
    ])
    # fokalen: notans 983.7 px är en klippspecifik tabell; MoGe skattar ~41° (se EXPERIMENT.md 7.3)
    VARIANTER[f"S_L1_fokal_{f}"] = dict(obs=[("f_sann, f_sig = (fk[0], fk[1]) if fk else (None, None)",
                                               f"f_sann, f_sig = (fk[0] * {f}, fk[1]) if fk else (None, None)")])


def ladda(modnamn: str, kalla: pathlib.Path, patchar):
    src = kalla.read_text(encoding="utf-8")
    for gammal, ny in patchar or []:
        n = src.count(gammal)
        if n != 1:
            raise SystemExit(f"PATCH MISSAR ({n} träffar) i {kalla.name}: {gammal[:90]!r}")
        src = src.replace(gammal, ny)
    mod = types.ModuleType(modnamn)
    mod.__file__ = str(kalla)
    sys.modules[modnamn] = mod
    exec(compile(src, f"{kalla}<{modnamn}>", "exec"), mod.__dict__)
    return mod


def matt(rec, sek):
    noder = {n.id: n for n in rec.noder}
    bord = {i: n.evidence_shots for i, n in noder.items() if n.klass == "bord"}
    foremal = {i: n.evidence_shots for i, n in noder.items() if n.klass == "foremal"}
    pos = {i: n.position for i, n in noder.items()}
    avst = {}
    for a, b in (("A", "B"), ("A", "C"), ("B", "C")):
        if a in pos and b in pos:
            avst[f"{a}-{b}"] = round(math.dist(pos[a][:2], pos[b][:2]), 3)
    osak_B = [r.osakerhet_m.get("B") for r in rec.logg] if rec.logg else []
    return dict(tro=rec.tro, P=rec.sannolikhet, n_bord=len(bord), bord=bord, foremal=foremal, avstand=avst,
                tro_per_tagning=[(r.klipp, r.tro, round(r.sannolikhet, 3)) for r in rec.logg],
                osak_B=osak_B, conf={i: n.confidence_score for i, n in noder.items() if n.klass in ("bord", "person")},
                sek=round(sek, 1))


def kor_variant(klipp: str, namn: str, obs_fil: pathlib.Path | None):
    v = VARIANTER[namn]
    t0 = time.time()
    if v.get("obs") or v.get("tvinga_obs"):
        om = ladda("obs_motor_ab", KARNA / "obs_motor.py", v.get("obs"))
        ing, vlm, djup = KLIPP[klipp]
        obs = om.bygg(ROT / ing, (ROT / vlm) if vlm else None, (ROT / djup) if djup else None,
                      utan_deklaration=bool(v.get("utan_dekl")))
    else:
        fil = obs_fil or (HIT / "rum_ut" / "med_dekl" / klipp / "obs.json")
        obs = Observationer.model_validate_json(fil.read_text(encoding="utf-8"))
    rp = ladda("rums_pussel_ab", KARNA / "rums_pussel.py", v.get("pussel"))
    if v.get("R"):
        rp.R = {**regler.R, **v["R"]}
    if v.get("foremal") is not None:
        rp.FOREMAL_PRIS = dict(v["foremal"])
    t1 = time.time()
    hist = rp.kor(obs)
    rader = rp.logg(hist, obs)
    rec = rp.bygg_recept(hist, obs, rader)
    m = matt(rec, time.time() - t1)
    m["roller"] = {k.klipp: [(d.nyckel, d.pose, d.vid) for d in k.detektioner if d.klass == "person"] for k in obs.klipp}
    m.update(variant=namn, klipp=klipp, obs_ombyggd=bool(v.get("obs")), tot_sek=round(time.time() - t0, 1))
    return m, obs, rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipp", default="notan")
    ap.add_argument("--variant", action="append", default=[])
    ap.add_argument("--alla", action="store_true")
    ap.add_argument("--filter", default=None, help="prefix, t.ex. L2_ eller S_")
    ap.add_argument("--parallell", type=int, default=1)
    ap.add_argument("--obs", default=None)
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--spara", action="store_true", help="spara obs.json/recept.json för varianten")
    ap.add_argument("--etikett", default="", help="suffix på resultatfilen (t.ex. hashfrö)")
    a = ap.parse_args()
    if a.lista:
        kallor = {"obs": (KARNA / "obs_motor.py").read_text(encoding="utf-8"),
                  "pussel": (KARNA / "rums_pussel.py").read_text(encoding="utf-8")}
        for n, v in VARIANTER.items():
            fel = [f"{typ}:{g[:50]!r}x{kallor[typ].count(g)}" for typ in ("obs", "pussel")
                   for g, _ in v.get(typ, []) if kallor[typ].count(g) != 1]
            print(n, "OK" if not fel else f"PATCHFEL {fel}")
        return
    namn = list(VARIANTER) if a.alla else a.variant
    if a.filter:
        namn = [n for n in namn if n.startswith(a.filter) or n == "bas"]
    utd = HIT / "rum_ut" / "ablation"
    utd.mkdir(parents=True, exist_ok=True)
    if len(namn) > 1 or a.parallell > 1:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        kö, igang = list(namn), []
        while kö or igang:
            while kö and len(igang) < a.parallell:
                n = kö.pop(0)
                cmd = [sys.executable, str(pathlib.Path(__file__)), "--klipp", a.klipp, "--variant", n]
                if a.obs:
                    cmd += ["--obs", a.obs]
                igang.append((n, subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)))
            for n, p in list(igang):
                if p.poll() is not None:
                    out = p.stdout.read().decode("utf-8", "replace")
                    print(out.strip().splitlines()[-1] if out.strip() else f"{n}: (ingen utdata)", flush=True)
                    if p.returncode != 0:
                        print(f"FEL i {n}:\n{out[-2000:]}", flush=True)
                    igang.remove((n, p))
            time.sleep(0.5)
        return
    n = namn[0]
    m, obs, rec = kor_variant(a.klipp, n, pathlib.Path(a.obs) if a.obs else None)
    d = utd / a.klipp
    d.mkdir(parents=True, exist_ok=True)
    m["etikett"] = a.etikett
    m["PYTHONHASHSEED"] = os.environ.get("PYTHONHASHSEED")
    (d / f"{n}{a.etikett}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.spara:
        d = utd / a.klipp / f"{n}{a.etikett}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "obs.json").write_text(obs.model_dump_json(indent=1), encoding="utf-8")
        (d / "recept.json").write_text(rec.model_dump_json(indent=1), encoding="utf-8")
    print(json.dumps({k: m[k] for k in ("variant", "tro", "P", "bord", "avstand", "sek")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
