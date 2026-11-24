"""Mutationstest av kvalitetsgrindarna G1–G7 (byggsten/brygga/grindar.py) och H-serien (grind_harda.py).

Fråga: kan grindarna larma alls, och döljer efterbehandlingen i forvarld_karna/scen_brygga.py fel
innan grindarna mäter?

Läge a (rå grind):   kända fel injiceras i färdigt forvarld_karna/ut/<klipp>/paket.json.
                     Inget kompileras om; grindarna mäter det muterade paketet direkt.
Läge b (före efterbehandling): samma felklasser injiceras i det som scen_brygga läser
                     (SAM-sekvensen via np.load, obs.json, recept.json) och hela
                     kompilera_scenpaket körs (z-normalisering, R25, R3 fotkontakt, stol under
                     bäckenet, kontaktkalibrerad disk, _dra_in_dolda_ben..., R1-döljning).
                     Facit: det muterade paketet jämförs med en omutererad omkompilering. Om felet
                     finns kvar (kropp/kamera/objekt avviker) men ingen grind larmar = maskerat.
Ablation:            omutererade klipp kompileras med ett efterbehandlingssteg avstängt i taget
                     (R3, _dra_in, R1-döljning, R25) för att se vilka grindar stegen håller tysta.

Inga filer i forvarld_karna/ eller byggsten/ ändras: scen_brygga importeras och dess modulglobaler
(np.load, fotkontakt, _dra_in_dolda_ben_bakom_massiv_disk, _intervall_minus, _mjuk_bana, subprocess)
byts ut i den egna processen under en körning. Paket från läge b skrivs till en temporär katalog.

Kör (från repo-roten):
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\grind_mutation.py            # a + b + ablation
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\grind_mutation.py --lage a   # bara läge a (sekunder)
Skriver motpart/runda-1-claude/grind_resultat.json och matriser i markdown till stdout.
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import math
import multiprocessing as mp
import pathlib
import sys
import tempfile
import time
import types

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
for p in (HIT, ROT / "forvarld_karna", ROT / "byggsten/brygga"):
    sys.path.insert(0, str(p))

import grindar as G  # noqa: E402
import grind_harda as GH  # noqa: E402
from rotation import mat_till_quat, quat_xyzw, quat_till_mat  # noqa: E402

KLIPP = list(GH.INGEST)
G_GRINDAR = ["G1_rum", "G2_golv", "G3_sate", "G4_genom", "G5_ibild", "G6_skymning", "G7_trohet"]
UT_JSON = HIT / "grind_resultat.json"
TROSKEL_KVAR_M = 0.05   # facit: avvikelse mot omuterat paket som räknas som att felet finns kvar


# =============================================================================== paket-hjälp
def las_paket(klipp):
    return json.loads((ROT / "forvarld_karna/ut" / klipp / "paket.json").read_text(encoding="utf-8"))


def spar_X(sp):
    n = len(sp["rutor"])
    return np.array([r[1:] for r in sp["rutor"]], float).reshape(n, -1, 3) / 1000.0, [r[0] for r in sp["rutor"]]


def skriv_X(sp, X, U):
    sp["rutor"] = [[int(u)] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X)]


def tagning(paket, sid):
    return next(t for t in paket["tagningar"] if t["id"] == sid)


def kam_axlar_paket(t):
    """(C, R) för tagningens mittnyckel; R[:,0]=kamerans högerled, R[:,2]=bakåt (grindar.proj-konvention)."""
    a0, b0 = t["ut"]
    C, R, _ = G.kamera(t, (a0 + b0) // 2)
    return C, R


def horisontell(v):
    v = np.array(v, float); v[2] = 0.0
    return v / max(np.linalg.norm(v), 1e-9)


def Rz(theta):
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


# =============================================================================== kroppsmutationer (gemensamma)
KROPP_MUT = {
    "sank_04": "kropp 0,4 m under golvet (alla rutor)",
    "sank_04_delvis": "kropp 0,4 m under golvet i första 40 % av rutorna (mittrutan orörd)",
    "lyft_05": "kropp svävar 0,5 m över golvet",
    "vand_180": "person vänd 180° kring lodaxeln genom bröstet",
    "genom_disk": "bröstet flyttat till närmaste bords/disks mittpunkt (xy)",
    "utanfor_bild": "kropp 3 m i kamerans sidled (utanför bild)",
    "teleport": "kropp hoppar 1,5 m i sidled halvvägs i tagningen",
    "skala_15": "kropp skalad 1,5× kring bröstet",
}


def kropp_transform(namn, Xw_sp2, kam_x, bord_xy):
    """Returnerar (M (T,3,3), t (T,3)) i världsram; pivot = c_spine2 per ruta."""
    T = len(Xw_sp2)
    M = np.repeat(np.eye(3)[None], T, axis=0); t = np.zeros((T, 3))
    if namn == "sank_04":
        t[:, 2] = -0.4
    elif namn == "sank_04_delvis":
        t[: int(0.4 * T), 2] = -0.4
    elif namn == "lyft_05":
        t[:, 2] = 0.5
    elif namn == "vand_180":
        M[:] = Rz(math.pi)
    elif namn == "genom_disk":
        t[:, :2] = np.asarray(bord_xy) - np.median(Xw_sp2[:, :2], axis=0)
    elif namn == "utanfor_bild":
        t[:] = 3.0 * kam_x
    elif namn == "teleport":
        t[T // 2:] = 1.5 * kam_x
    elif namn == "skala_15":
        M[:] = 1.5 * np.eye(3)
    return M, t


def narmaste_bord(paket_obj, xy, tid=None, kraver_synlig=True):
    bord = [o for o in paket_obj if o["typ"] == "bord"]
    if kraver_synlig and tid is not None:
        syn = [o for o in bord if G.synlig(o, tid)]
        bord = syn or bord
    if not bord:
        return None
    return min(bord, key=lambda o: np.linalg.norm(np.array(o["pos"][:2]) - xy))


# =============================================================================== läge a: mål och mutationer
def mal_a(paket):
    mal = []
    spar = [(pid, i, sp["tagning"]) for pid, spl in paket["rorelse"].items() for i, sp in enumerate(spl)]
    for namn in KROPP_MUT:
        for pid, i, sid in spar:
            mal.append(dict(mut=namn, pid=pid, i=i, tagning=sid))
    # identitet: tvåpersonstagning -> byt rörelser; enpersonstagning -> etikett till annan huvudperson
    huvud = [p for p in paket["personer"] if p in ("A", "B", "C")]
    for t in paket["tagningar"]:
        ids = [p["id"] for p in t["personer"]]
        if len(ids) >= 2:
            mal.append(dict(mut="byt_id", tagning=t["id"], par=ids[:2]))
        elif len(ids) == 1:
            andra = [h for h in huvud if h != ids[0]]
            if andra:
                mal.append(dict(mut="byt_id", tagning=t["id"], par=[ids[0], andra[0]]))
    for t in paket["tagningar"]:
        if t["personer"]:
            for namn in ("kamera_1m_sida", "kamera_1m_bak", "kamera_1m_upp"):
                mal.append(dict(mut=namn, tagning=t["id"]))
    for o in paket["objekt"]:
        if o["typ"] == "bord":
            for namn in ("bord_2m", "bord_bort", "bord_svav_05"):
                mal.append(dict(mut=namn, objekt=o["id"]))
        if o["typ"] == "stol":
            for namn in ("stol_bort", "stol_05", "stol_sank_03"):
                mal.append(dict(mut=namn, objekt=o["id"]))
    # positiv kontroll för G1: ett objekt flyttas till ett rum som inte gäller någon tagning
    forsta = next((o for o in paket["objekt"] if o["typ"] not in ("golv", "vagg")), None)
    if forsta:
        mal.append(dict(mut="rum_fel", objekt=forsta["id"]))
    return mal


def mutera_a(paket, mal):
    p = copy.deepcopy(paket)
    m = mal["mut"]
    if m in KROPP_MUT:
        sp = p["rorelse"][mal["pid"]][mal["i"]]
        X, U = spar_X(sp)
        L = {n: i for i, n in enumerate(p["leder"])}
        t = tagning(p, sp["tagning"])
        _, R = kam_axlar_paket(t)
        sp2 = X[:, L["c_spine2"]]
        b = narmaste_bord(p["objekt"], np.median(sp2[:, :2], axis=0), (t["ut"][0] + t["ut"][1]) // 2)
        Mt, tt = kropp_transform(m, sp2, horisontell(R[:, 0]), b["pos"][:2] if b else sp2[0, :2])
        piv = sp2[:, None, :]
        X = np.einsum("tij,tkj->tki", Mt, X - piv) + piv + tt[:, None, :]
        skriv_X(sp, X, U)
        if b and m == "genom_disk":
            mal["bord"] = b["id"]; mal["bord_synligt"] = bool(G.synlig(b, (t["ut"][0] + t["ut"][1]) // 2))
    elif m == "byt_id":
        sid = mal["tagning"]; a, bb = mal["par"]
        t = tagning(p, sid)
        ids = [q["id"] for q in t["personer"]]
        sa = next(s for s in p["rorelse"][a] if s["tagning"] == sid)
        if bb in ids:   # två personer i bild: byt rörelserna
            sb = next(s for s in p["rorelse"][bb] if s["tagning"] == sid)
            sa["rutor"], sb["rutor"] = sb["rutor"], sa["rutor"]
        else:           # en person: fel etikett
            p["rorelse"][a].remove(sa)
            p["rorelse"].setdefault(bb, []).append(sa)
            for q in t["personer"]:
                if q["id"] == a:
                    q["id"] = bb
    elif m.startswith("kamera_1m"):
        t = tagning(p, mal["tagning"])
        _, R = kam_axlar_paket(t)
        d = {"kamera_1m_sida": horisontell(R[:, 0]), "kamera_1m_bak": horisontell(R[:, 2]), "kamera_1m_upp": np.array([0, 0, 1.0])}[m]
        for k in t["kamera"]["nycklar"]:
            k[1:4] = [round(float(v), 4) for v in np.array(k[1:4]) + d]
    elif m.startswith("bord_") or m.startswith("stol_") or m == "rum_fel":
        o = next(o for o in p["objekt"] if o["id"] == mal["objekt"])
        if m in ("bord_bort", "stol_bort"):
            p["objekt"].remove(o)
        elif m == "bord_2m":
            kroppar = np.array([spar_X(sp)[0][:, 0, :2].mean(axis=0) for spl in p["rorelse"].values() for sp in spl])
            n = kroppar[np.argmin(np.linalg.norm(kroppar - np.array(o["pos"][:2]), axis=1))]
            v = horisontell(np.r_[np.array(o["pos"][:2]) - n, 0.0])
            o["pos"] = [o["pos"][0] + 2 * v[0], o["pos"][1] + 2 * v[1], o["pos"][2]]
        elif m == "bord_svav_05":
            o["pos"][2] += 0.5
        elif m == "stol_05":
            o["pos"][0] += 0.5
        elif m == "stol_sank_03":
            o["pos"][2] -= 0.3
        elif m == "rum_fel":
            o["rum"] = "rum_fel"
            p["rum"].append(dict(id="rum_fel", tagningar=[], ut=[], platser=[o["id"]]))
    return p


# =============================================================================== grindstatus
def g_status(paket):
    try:
        rader = G.mat(paket)
    except Exception as e:  # noqa: BLE001
        return {"krasch": f"{type(e).__name__}: {e}"}, []
    st = {}
    for r in rader:
        for g in G_GRINDAR:
            st[f"{r['tagning']}|{g}"] = r.get(g, {}).get("ok", "saknas")
    return st, rader


def h_status(paket, ktx):
    try:
        rader = GH.mat(paket, ktx)
    except Exception as e:  # noqa: BLE001
        return {"krasch": f"{type(e).__name__}: {e}"}, []
    st = {}
    for r in rader:
        for g in GH.H_GRINDAR:
            if g in r:
                st[f"{r['tagning']}|{r.get('person')}|{g}"] = r[g].get("ok")
    return st, rader


def _mal_nyckel(mal, k):
    """Hör statusnyckeln k ('tagning|grind' eller 'tagning|person|grind') till mutationens målrad?"""
    delar = k.split("|")
    tg = mal.get("tagning")
    if tg is None:                       # objektmutation: alla rader berörs
        return True
    if delar[0] != tg:
        return False
    if len(delar) == 3 and mal["mut"] in KROPP_MUT:
        return delar[1] == str(mal.get("pid"))
    return True


def jamfor(bas, mut, grindar, mal):
    """Per grind: 'L' larmar (ny rad blir fel), 'F' målraden var redan fel i baslinjen (kan inte larma
    ytterligare, räknas inte i nämnaren), 'N' grinden slutade mäta (ok -> None), '' tyst, 'K' krasch.
    byt_id jämförs som antal fel per (tagning, grind) eftersom personnamnen byts."""
    if "krasch" in mut:
        return {g: "K" for g in grindar}
    ut = {}
    for g in grindar:
        bk = {k: v for k, v in bas.items() if k.endswith("|" + g)}
        mk = {k: v for k, v in mut.items() if k.endswith("|" + g)}
        if mal["mut"] == "byt_id":
            def antal(d):
                c = {}
                for k, v in d.items():
                    c[k.split("|")[0]] = c.get(k.split("|")[0], 0) + (v is False)
                return c
            cb, cm = antal(bk), antal(mk)
            larm = any(cm[t] > cb.get(t, 0) for t in cm)
        else:
            larm = any(v is False and bk.get(k) is not False for k, v in mk.items())
        if larm:
            ut[g] = "L"
            continue
        slut = any(v is True and k in mk and mk[k] in (None, "saknas") for k, v in bk.items())
        malk = [k for k in bk if _mal_nyckel(mal, k)]
        redan = bool(malk) and all(bk[k] is False for k in malk)
        ut[g] = "F" if redan else ("N" if slut else "")
    return ut


# =============================================================================== läge a: körning
def kor_lage_a():
    res = []
    for k in KLIPP:
        p = las_paket(k); ktx = GH.las_kontext(k)
        gb, _ = g_status(p); hb, _ = h_status(p, ktx)
        for mal in mal_a(p):
            pm = mutera_a(p, mal)
            gm, _ = g_status(pm); hm, _ = h_status(pm, ktx)
            res.append(dict(klipp=k, lage="a", **mal, G=jamfor(gb, gm, G_GRINDAR, mal), H=jamfor(hb, hm, GH.H_GRINDAR, mal)))
    return res


# =============================================================================== läge b: kompilering med injektion
_SB = None  # scen_brygga, importeras per process


def _sb():
    global _SB
    if _SB is None:
        import scen_brygga
        scen_brygga.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)  # hoppa över emit_bpy
        _SB = scen_brygga
        _SB._ORIG = dict(np=scen_brygga.np, fotkontakt=scen_brygga.fotkontakt,
                         dra_in=scen_brygga._dra_in_dolda_ben_bakom_massiv_disk,
                         intervall_minus=scen_brygga._intervall_minus, mjuk=scen_brygga._mjuk_bana)
    return _SB


class _NpProxy:
    """Delegerar allt till numpy, men muterar en utvald sekvens_<spår>.npz när scen_brygga läser den."""

    def __init__(self, real, mal_fil, fn):
        self._real, self._mal, self._fn = real, mal_fil, fn

    def __getattr__(self, n):
        return getattr(self._real, n)

    def load(self, path, *a, **k):
        r = self._real.load(path, *a, **k)
        if pathlib.Path(str(path)).resolve() == self._mal:
            d = {f: np.array(r[f]) for f in r.files}
            return self._fn(d)
        return r


def spar_karta(ingest, obs, rec):
    """(tagning, pid) -> spår-id, med samma regel som scen_brygga.py:266–293 (ordningsbaserad)."""
    karta = {}
    for k in obs["klipp"]:
        sid = k["klipp"]; S = ingest / sid.upper()
        dets = [d for d in k["detektioner"] if d["klass"] == "person"]
        f = S / "personer.json"
        sm = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        sl = sorted(sm, key=lambda s: -len(sm[s]))
        for i, d in enumerate(dets):
            if i >= len(sl):
                break
            if not (S / f"sekvens_{sl[i]}.npz").exists():
                continue
            pid = d["nyckel"].split(":")[-1] if (d.get("nyckel") and ":" in d["nyckel"]) else d["id"]
            if pid == "okand":
                n = next((n for n in rec["noder"] if n["klass"] == "person" and not str(n.get("nyckel")).endswith((":A", ":B", ":C"))
                          and sid in n["evidence_shots"]), None)
                pid = n["id"] if n else f"gast_{sid}"
            karta[(sid, pid)] = sl[i]
    return karta


def _kropp_fn_raw(namn, ingest, obs, rec, sid, kam_rec_rot_z, C_rec):
    """Bygger en funktion som muterar råa SAM-arrayer (pose cm i kameraram, cam_t_ra) så att kroppen
    i världen (enligt scen_brygga:322–323) transformeras med kropp_transform(namn)."""
    sb = _sb()
    import obs_motor
    W = obs["klipp"][0]["kamera"]["bild_px"][0]
    S = ingest / sid.upper()
    K = np.load(sorted(glob.glob(str(S / "rum/depth/*.npz")))[0])["intrinsics"]
    f_kedja = float(K[0, 0] * W); fk = obs_motor._fokal(ingest)
    kappa = (fk[0] if fk else f_kedja) / f_kedja
    Rc = sb._euler_xyz_till_mat(90.0, 0.0, kam_rec_rot_z)
    F = sb.F
    IX = {n: i for i, n in enumerate(json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"])}
    sp2 = IX["c_spine2"]
    a0, b0 = next(k["rutor"] for k in obs["klipp"] if k["klipp"] == sid)
    bord = [n for n in rec["noder"] if n["klass"] == "bord"]

    def fn(d):
        pose, ct = d["pose"].astype(float), d["cam_t_ra"].astype(float)
        n = min(len(pose), b0 - a0)
        bal = pose[:n, sp2, :3] / 100.0
        p_c = kappa * (bal + ct[:n] @ F.T)                   # bröstet i kameraram
        w_sp2 = p_c @ Rc.T + np.array(C_rec)                  # bröstet i världen (före z-normalisering)
        xy = np.median(w_sp2[:, :2], axis=0)
        b = min(bord, key=lambda o: np.linalg.norm(np.array(o["position"][:2]) - xy)) if bord else None
        Mt, tt = kropp_transform(namn, w_sp2, horisontell(Rc[:, 0]), b["position"][:2] if b else xy)
        for i in range(n):
            A = Rc.T @ Mt[i] @ Rc                             # världstransform uttryckt i kameraram
            rel = pose[i, :, :3] / 100.0 - bal[i]
            pose[i, :, :3] = (rel @ A.T + bal[i]) * 100.0
            if namn == "vand_180":
                for j in range(pose.shape[1]):
                    q = mat_till_quat(A @ quat_xyzw(pose[i, j, 3:7]))   # (w,x,y,z)
                    pose[i, j, 3:7] = [q[1], q[2], q[3], q[0]]
            dc = Rc.T @ tt[i]
            ct[i] = ct[i] + (dc / kappa) @ F
        d["pose"], d["cam_t_ra"] = pose, ct
        return d
    return fn


def kompilera(klipp, obs, rec, kropp=None, ablation=(), logg=None):
    """Kör scen_brygga.kompilera_scenpaket på (eventuellt muterade) obs/recept. Returnerar paket-dict."""
    sb = _sb()
    from schema import Observationer, Recept
    ingest = ROT / "scen/3d/ingest/ut" / GH.INGEST[klipp]
    O = sb._ORIG
    try:
        if kropp is not None:
            sid, pid = kropp["tagning"], kropp["pid"]
            spar = spar_karta(ingest, obs, rec)[(sid, pid)]
            cam = next(c for c in rec["kameror"] if c["klipp"] == sid)
            fn = _kropp_fn_raw(kropp["mut"], ingest, obs, rec, sid, cam["rotation"][2], cam["position"])
            sb.np = _NpProxy(O["np"], (ingest / sid.upper() / f"sekvens_{spar}.npz").resolve(), fn)
        if "R3" in ablation:
            sb.fotkontakt = lambda X, leder, golv=0.0: {}
        if "dra_in" in ablation:
            sb._dra_in_dolda_ben_bakom_massiv_disk = lambda *a, **k: 0
        elif logg is not None:
            def _rakna(X, leder, disk, golv=0.0):
                n = O["dra_in"](X, leder, disk, golv); logg.append(int(n)); return n
            sb._dra_in_dolda_ben_bakom_massiv_disk = _rakna
        if "R1" in ablation:
            sb._intervall_minus = lambda iv, bort: [list(iv)]
        if "R25" in ablation:
            sb._mjuk_bana = lambda arr, fonster=9: np.zeros_like(arr)
        o = Observationer.model_validate_json(json.dumps(obs))
        r = Recept.model_validate_json(json.dumps(rec))
        with tempfile.TemporaryDirectory() as td:
            pf = sb.kompilera_scenpaket(klipp, ingest, o, r, pathlib.Path(td))
            return json.loads(pf.read_text(encoding="utf-8"))
    finally:
        sb.np = O["np"]; sb.fotkontakt = O["fotkontakt"]; sb._dra_in_dolda_ben_bakom_massiv_disk = O["dra_in"]
        sb._intervall_minus = O["intervall_minus"]; sb._mjuk_bana = O["mjuk"]


def las_indata(klipp):
    ut = ROT / "forvarld_karna/ut" / klipp
    return (json.loads((ut / "obs.json").read_text(encoding="utf-8")),
            json.loads((ut / "recept.json").read_text(encoding="utf-8")))


def mal_b(klipp):
    obs, rec = las_indata(klipp)
    karta = spar_karta(ROT / "scen/3d/ingest/ut" / GH.INGEST[klipp], obs, rec)
    mal = []
    for namn in KROPP_MUT:
        for (sid, pid) in karta:
            mal.append(dict(mut=namn, tagning=sid, pid=pid))
    for k in obs["klipp"]:
        dets = [d for d in k["detektioner"] if d["klass"] == "person"]
        for i, d in enumerate(dets):
            mal.append(dict(mut="pose_flip", tagning=k["klipp"], det=d["id"]))
        if len(dets) >= 2:
            mal.append(dict(mut="byt_id", tagning=k["klipp"], typ="ordning"))
        elif len(dets) == 1:
            egen = dets[0]["nyckel"]
            andra = sorted({d["nyckel"] for kk in obs["klipp"] for d in kk["detektioner"]
                            if d["klass"] == "person" and d["nyckel"] not in (egen, "person:okand")})
            if andra:
                mal.append(dict(mut="byt_id", tagning=k["klipp"], typ="etikett", till=andra[0]))
    for k in obs["klipp"]:
        if any(d["klass"] == "person" for d in k["detektioner"]):
            for namn in ("kamera_1m_sida", "kamera_1m_bak", "kamera_1m_upp"):
                mal.append(dict(mut=namn, tagning=k["klipp"]))
    for n in rec["noder"]:
        if n["klass"] == "bord":
            for namn in ("bord_2m", "bord_bort", "bord_svav_05"):
                mal.append(dict(mut=namn, objekt=n["id"]))
    return mal


def mutera_b(obs, rec, mal):
    obs, rec = copy.deepcopy(obs), copy.deepcopy(rec)
    m = mal["mut"]
    kropp = None
    if m in KROPP_MUT:
        kropp = dict(mut=m, tagning=mal["tagning"], pid=mal["pid"])
    elif m == "pose_flip":
        d = next(d for k in obs["klipp"] for d in k["detektioner"] if d["id"] == mal["det"])
        d["pose"] = "staende" if d["pose"] == "sittande" else "sittande"
        mal["ny_pose"] = d["pose"]
    elif m == "byt_id":
        k = next(k for k in obs["klipp"] if k["klipp"] == mal["tagning"])
        pers = [d for d in k["detektioner"] if d["klass"] == "person"]
        if mal["typ"] == "ordning":
            ovr = [d for d in k["detektioner"] if d["klass"] != "person"]
            k["detektioner"] = ovr + pers[::-1]
        else:
            pers[0]["nyckel"] = mal["till"]
    elif m.startswith("kamera_1m"):
        c = next(c for c in rec["kameror"] if c["klipp"] == mal["tagning"])
        sb = _sb()
        Rc = sb._euler_xyz_till_mat(90.0, 0.0, c["rotation"][2])
        d = {"kamera_1m_sida": horisontell(Rc[:, 0]), "kamera_1m_bak": horisontell(Rc[:, 2]), "kamera_1m_upp": np.array([0, 0, 1.0])}[m]
        c["position"] = [float(v) for v in np.array(c["position"]) + d]
    elif m.startswith("bord_"):
        n = next(n for n in rec["noder"] if n["id"] == mal["objekt"])
        if m == "bord_bort":
            rec["noder"].remove(n)
        elif m == "bord_2m":
            pers = np.array([q["position"][:2] for q in rec["noder"] if q["klass"] == "person"])
            near = pers[np.argmin(np.linalg.norm(pers - np.array(n["position"][:2]), axis=1))]
            v = horisontell(np.r_[np.array(n["position"][:2]) - near, 0.0])
            n["position"] = [n["position"][0] + 2 * v[0], n["position"][1] + 2 * v[1], n["position"][2]]
        elif m == "bord_svav_05":
            n["position"][2] += 0.5
    return obs, rec, kropp


def facit(bas, mut):
    """Hur mycket det muterade paketet avviker från det omuterade (efter all efterbehandling)."""
    kr = 0.0; saknade = []
    for pid, spl in bas["rorelse"].items():
        for sp in spl:
            ms = next((s for s in mut["rorelse"].get(pid, []) if s["tagning"] == sp["tagning"]), None)
            if ms is None:
                saknade.append(f"{sp['tagning']}:{pid}"); continue
            Xa, Ua = spar_X(sp); Xb, Ub = spar_X(ms)
            if Ua != Ub or Xa.shape != Xb.shape:
                kr = max(kr, 9.9); continue
            kr = max(kr, float(np.median(np.linalg.norm(Xa - Xb, axis=-1))))
    ka = 0.0
    for t in bas["tagningar"]:
        tm = next((x for x in mut["tagningar"] if x["id"] == t["id"]), None)
        if tm is None:
            continue
        ca = np.array([k[1:4] for k in t["kamera"]["nycklar"]]).mean(axis=0)
        cb = np.array([k[1:4] for k in tm["kamera"]["nycklar"]]).mean(axis=0)
        ka = max(ka, float(np.linalg.norm(ca - cb)))
    ob = []
    mo = {o["id"]: o for o in mut["objekt"]}
    for o in bas["objekt"]:
        q = mo.get(o["id"])
        if q is None:
            ob.append(f"{o['id']}:saknas")
        elif np.linalg.norm(np.array(o["pos"]) - np.array(q["pos"])) > TROSKEL_KVAR_M or o["matt"] != q["matt"]:
            ob.append(f"{o['id']}:flyttad")
        elif o["synlig_ut"] != q["synlig_ut"]:
            ob.append(f"{o['id']}:synlighet")
    for oid in mo:
        if oid not in {o["id"] for o in bas["objekt"]}:
            ob.append(f"{oid}:ny")
    kvar = kr > TROSKEL_KVAR_M or ka > TROSKEL_KVAR_M or bool(ob) or bool(saknade)
    return dict(kropp_m=round(kr, 3), kamera_m=round(ka, 3), objekt=ob, saknade_spar=saknade, kvar=kvar)


_BAS_B = {}


def _bas_b(klipp):
    if klipp not in _BAS_B:
        obs, rec = las_indata(klipp)
        p = kompilera(klipp, obs, rec)
        _BAS_B[klipp] = (p, g_status(p)[0], h_status(p, GH.las_kontext(klipp, obs, rec))[0])
    return _BAS_B[klipp]


def _jobb_b(arg):
    klipp, mal = arg
    try:
        p0, gb, hb = _bas_b(klipp)
        obs, rec = las_indata(klipp)
        obs_m, rec_m, kropp = mutera_b(obs, rec, mal)
        pm = kompilera(klipp, obs_m, rec_m, kropp=kropp)
        gm, _ = g_status(pm); hm, _ = h_status(pm, GH.las_kontext(klipp, obs_m, rec_m))
        return dict(klipp=klipp, lage="b", **mal, G=jamfor(gb, gm, G_GRINDAR, mal), H=jamfor(hb, hm, GH.H_GRINDAR, mal), facit=facit(p0, pm))
    except Exception as e:  # noqa: BLE001
        return dict(klipp=klipp, lage="b", **mal, fel=f"{type(e).__name__}: {e}")


def _jobb_ablation(arg):
    klipp, abl = arg
    obs, rec = las_indata(klipp)
    logg = []
    p = kompilera(klipp, obs, rec, ablation=abl, logg=logg)
    gs, grader = g_status(p)
    hs, hrader = h_status(p, GH.las_kontext(klipp, obs, rec))
    gfel = G.sammanfatta(grader) if grader else None
    hfel = GH.sammanfatta(hrader) if hrader else None   # H1/H10/H13 räknas en gång per tagning
    return dict(klipp=klipp, ablation=list(abl), G_fel=gfel, H_fel=hfel, dra_in_leder=sum(logg) if logg else 0,
                beslut={r: sum(1 for b in p["beslut"] if b["regel"] == r) for r in sorted({b["regel"] for b in p["beslut"]})})


# =============================================================================== sammanställning
def matris(res, grindar, nyckel):
    rader = {}
    for r in res:
        if nyckel not in r:
            continue
        mrad = rader.setdefault(r["mut"], {g: dict(L=0, n=0, N=0, F=0, K=0) for g in grindar})
        for g in grindar:
            mrad[g]["n"] += 1
            v = r[nyckel][g]
            if v in ("L", "N", "F", "K"):
                mrad[g][v] += 1
    return rader


def skriv_matris(titel, rader, grindar, res=None):
    print(f"\n#### {titel}\n")
    kol = " | ".join(g.replace("_", " ") for g in grindar)
    extra = " | felet kvar efter efterbehandling | kvar men inget G-larm | kvar men inget H-larm" if res is not None else ""
    print(f"| mutation | n | {kol}{extra} |")
    print("|---|---|" + "---|" * len(grindar) + ("---|---|---|" if res is not None else ""))
    for m, gr in rader.items():
        n = next(iter(gr.values()))["n"]
        cell = []
        for g in grindar:
            c = gr[g]
            matbar = c["n"] - c["F"]
            txt = f"**{c['L']}/{matbar}**" if c["L"] else f"0/{matbar}"
            if c["F"]:
                txt += f" F{c['F']}"
            if c["N"]:
                txt += f" N{c['N']}"
            if c["K"]:
                txt += f" K{c['K']}"
            cell.append(txt)
        ex = ""
        if res is not None:
            rr = [r for r in res if r["mut"] == m and "facit" in r]
            kvar = [r for r in rr if r["facit"]["kvar"]]
            mg = [r for r in kvar if not any(v == "L" for v in r["G"].values())]
            mh = [r for r in kvar if not any(v == "L" for v in r["H"].values())]
            ex = f" | {len(kvar)}/{len(rr)} | {len(mg)}/{len(kvar)} | {len(mh)}/{len(kvar)}"
        print(f"| {m} | {n} | " + " | ".join(cell) + ex + " |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lage", default="ab", help="a, b eller ab (ablation körs med b)")
    ap.add_argument("--processer", type=int, default=max(1, min(6, (mp.cpu_count() or 2) - 1)))
    a = ap.parse_args()
    t0 = time.time()
    ut = dict(skapad=time.strftime("%Y-%m-%d %H:%M"), granser_G=G.GRANS, granser_H=GH.GRANS_H, resultat=[], ablation=[])
    if UT_JSON.exists() and a.lage != "ab":   # behåll resultat från det läge som inte körs om
        gam = json.loads(UT_JSON.read_text(encoding="utf-8"))
        ut["resultat"] = [r for r in gam.get("resultat", []) if r["lage"] not in a.lage]
        ut["ablation"] = gam.get("ablation", []) if "b" not in a.lage else []
    if "a" in a.lage:
        ut["resultat"] += kor_lage_a()
        print(f"[läge a] {sum(1 for r in ut['resultat'] if r['lage'] == 'a')} mutationer ({time.time() - t0:.1f} s)")
    if "b" in a.lage:
        jobb = [(k, m) for k in KLIPP for m in mal_b(k)]
        abl = [(k, x) for k in KLIPP for x in ((), ("R3",), ("dra_in",), ("R1",), ("R25",), ("R3", "dra_in", "R1", "R25"))]
        with mp.Pool(a.processer) as pool:
            ut["ablation"] = pool.map(_jobb_ablation, abl)
            print(f"[ablation] {len(abl)} kompileringar ({time.time() - t0:.1f} s)")
            for i, r in enumerate(pool.imap_unordered(_jobb_b, jobb, chunksize=2)):
                ut["resultat"].append(r)
                if (i + 1) % 25 == 0:
                    print(f"  [läge b] {i + 1}/{len(jobb)} ({time.time() - t0:.0f} s)", flush=True)
        fel = [r for r in ut["resultat"] if r.get("fel")]
        print(f"[läge b] {len(jobb)} mutationer, {len(fel)} körfel ({time.time() - t0:.1f} s)")
        for r in fel[:10]:
            print("   körfel:", r["klipp"], r["mut"], r.get("tagning"), r.get("pid"), r["fel"])
    UT_JSON.write_text(json.dumps(ut, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    for lage in ("a", "b"):
        rr = [r for r in ut["resultat"] if r["lage"] == lage and not r.get("fel")]
        if not rr:
            continue
        skriv_matris(f"Läge {lage}: G1–G7 (larm/n)", matris(rr, G_GRINDAR, "G"), G_GRINDAR, rr if lage == "b" else None)
        skriv_matris(f"Läge {lage}: H-serien (larm/n)", matris(rr, GH.H_GRINDAR, "H"), GH.H_GRINDAR)
    if ut["ablation"]:
        print("\n#### Ablation (omuterade klipp, ett efterbehandlingssteg av)\n")
        for r in ut["ablation"]:
            print(f"- {r['klipp']} av={r['ablation'] or 'inget'}: G={r['G_fel']} H={r['H_fel']} dra_in_leder={r['dra_in_leder']} beslut={r['beslut']}")
    print(f"\nKlart på {time.time() - t0:.0f} s -> {UT_JSON}")


if __name__ == "__main__":
    main()
