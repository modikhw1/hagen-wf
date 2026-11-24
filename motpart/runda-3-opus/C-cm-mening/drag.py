"""Lagliga drag på scenpaket/2. Inget generativt, ingen spegling. Paketet in, ett nytt paket ut.

Varje drag har två delar:
  plan(K, **a)  -> dict(effekter, foljder, platshallare, visa)  eller Avslag(skäl) om draget inte går
  gor(P, K, **a) -> nytt paket
`plan` körs först, så att K5-vakten (bar.vakt) kan pröva effekterna innan något ändras.

Kategorier:
  tidslinje   ta_bort_tagning, flytta_tagning, hall_sista, korta_tagning, ta_bort_segment, tempo_segment, upprepa_segment
  föremål     ta_bort_objekt, byt_objekt, lagg_till_objekt, flytta_objekt, byt_foremal_i_hand
  plats       byt_miljo, flytta_interaktion
  kamera      kamera_stabilisera, kamera_narmare, kamera_lins
  kropp       sta_still, ga_med_attityd (Argons syntes, märkt platshållare)

Kroppsdrag ärver attityden bara i den meningen att originalets egen rörelse återanvänds (omsamplad,
upprepad eller med låst förflyttning). Ingen led flyttas för att uttrycka en känsla. Allt som inte är
originalets rörelse märks 'platshallare'.
"""
from __future__ import annotations

import copy
import hashlib
import math
import pathlib
import sys

import numpy as np

ROT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROT / "byggsten/brygga"))
from rotation import quat_till_mat, mat_till_quat  # noqa: E402

OVERGANG = 6  # rutor som blandas vid en skarv (upprepning)


class Avslag(Exception):
    """Draget går inte att göra på det här paketet. Skälet visas för CM."""


# ============================================================================ hjälp

def kopia(P):
    """Kopia där rörelsens rutlistor delas tills ett drag byter ut dem (deepcopy av hela paketet tar 30–100 ms)."""
    n = {k: v for k, v in P.items()}
    n["objekt"] = [copy.deepcopy(o) for o in P["objekt"]]
    n["tagningar"] = copy.deepcopy(P["tagningar"])
    n["rorelse"] = {pid: [{k: v for k, v in s.items()} for s in sp] for pid, sp in P["rorelse"].items()}
    for k in ("personer", "rum", "mening", "tidsbas", "trohet"):
        n[k] = copy.deepcopy(P.get(k))
    n["beslut"] = list(P.get("beslut", []))
    return n


def tagning(P, tid):
    t = next((t for t in P["tagningar"] if t["id"].lower() == str(tid).lower()), None)
    if t is None:
        raise Avslag(f"tagningen {tid} finns inte (klippet har {', '.join(x['id'] for x in P['tagningar'])})")
    return t


def objekt(P, oid):
    o = next((o for o in P["objekt"] if o["id"] == oid), None)
    if o is None:
        raise Avslag(f"föremålet {oid} finns inte i förvärlden")
    return o


def spar_array(sp):
    R = sp["rutor"]
    U = np.array([r[0] for r in R], dtype=float)
    X = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3)
    return U, X  # mm


def spar_rutor(U, X):
    return [[int(u)] + [int(round(c)) for c in x.reshape(-1)] for u, x in zip(U, X)]


def _q_lerp(q0, q1, w):
    q0, q1 = np.array(q0, float), np.array(q1, float)
    if np.dot(q0, q1) < 0:
        q1 = -q1
    q = (1 - w) * q0 + w * q1
    return q / (np.linalg.norm(q) + 1e-12)


def kamera_vid(t, s):
    """Kamerans pose vid (flyttal) ruta s: [x,y,z,qw,qx,qy,qz,lins]. Linjär mellan nycklar."""
    ks = t["kamera"]["nycklar"]
    if t["kamera"].get("statisk") or len(ks) == 1:
        return list(ks[0][1:])
    us = [k[0] for k in ks]
    if s <= us[0]:
        return list(ks[0][1:])
    if s >= us[-1]:
        return list(ks[-1][1:])
    i = int(np.searchsorted(us, s, side="right")) - 1
    a, b = ks[i], ks[i + 1]
    w = (s - a[0]) / max(1e-9, b[0] - a[0])
    pos = [(1 - w) * a[j] + w * b[j] for j in (1, 2, 3)]
    q = _q_lerp(a[4:8], b[4:8], w)
    lins = (1 - w) * a[8] + w * b[8]
    return pos + [float(x) for x in q] + [lins]


def _kalla_ruta(src):
    return src[1] if isinstance(src, tuple) else src


def _pose(U, X, src):
    """Pose vid källa src: flyttal (interpolation) eller ('mix', s1, s2, w)."""
    if isinstance(src, tuple):
        _, s1, s2, w = src
        a, b = _pose(U, X, s1), _pose(U, X, s2)
        if a is None or b is None:
            return a if b is None else b
        return (1 - w) * a + w * b
    if src < U[0] - 0.5 or src > U[-1] + 0.5:
        return None
    s = min(max(src, U[0]), U[-1])
    i = int(np.searchsorted(U, s, side="right")) - 1
    i = max(0, min(i, len(U) - 1))
    if i == len(U) - 1 or U[i] == s:
        return X[i]
    w = (s - U[i]) / max(1e-9, U[i + 1] - U[i])
    return (1 - w) * X[i] + w * X[i + 1]


def _komprimera(fr):
    fr = sorted(set(fr))
    ut = []
    for f in fr:
        if ut and f == ut[-1][1]:
            ut[-1][1] = f + 1
        else:
            ut.append([f, f + 1])
    return ut


def bygg_om_tidslinje(P, block, notis):
    """block: [(tagnings-id, [källa per ny ruta], märkning)]. Bygger nya tagningar, rörelse, kameror,
    synlighet och rum, och skriver en tidskarta (ny ruta -> gammal ruta) som medielagret kan följa."""
    n = kopia(P)
    gamla_t = {t["id"]: t for t in P["tagningar"]}
    N_gammal = P["tidsbas"]["antal_rutor"]
    nya_t, ny_rorelse, tidskarta, karta_ny_till_gammal = [], {pid: [] for pid in P["rorelse"]}, [], []
    s0 = 0
    for tid, src, mark in block:
        t = copy.deepcopy(gamla_t[tid])
        L = len(src)
        t["ut"] = [s0, s0 + L]
        if t["kamera"].get("statisk") or len(t["kamera"]["nycklar"]) == 1:
            t["kamera"]["nycklar"] = [[s0] + list(t["kamera"]["nycklar"][0][1:])]
        else:
            nyck = []
            for j, s in enumerate(src):
                if j % 2 == 0 or j == L - 1:
                    if isinstance(s, tuple):
                        a, b = kamera_vid(gamla_t[tid], s[1]), kamera_vid(gamla_t[tid], s[2])
                        w = s[3]
                        pose = [(1 - w) * x + w * y for x, y in zip(a[:3], b[:3])] + list(_q_lerp(a[3:7], b[3:7], w)) + [(1 - w) * a[7] + w * b[7]]
                    else:
                        pose = kamera_vid(gamla_t[tid], s)
                    nyck.append([s0 + j] + [round(float(v), 5) for v in pose])
            t["kamera"]["nycklar"] = nyck
        if mark:
            t["markering"] = mark
        nya_t.append(t)
        for pid, sp in P["rorelse"].items():
            for spar in sp:
                if spar["tagning"] != tid:
                    continue
                U, X = spar_array(spar)
                Un, Xn = [], []
                for j, s in enumerate(src):
                    x = _pose(U, X, s)
                    if x is not None:
                        Un.append(s0 + j)
                        Xn.append(x)
                if Un:
                    ny = {k: v for k, v in spar.items()}
                    ny["rutor"] = spar_rutor(Un, np.array(Xn))
                    ny["ut"] = [Un[0], Un[-1] + 1]
                    ny_rorelse[pid].append(ny)
        tidskarta.append(dict(tagning=tid, ny=[s0, s0 + L], kalla=[round(float(_kalla_ruta(s)), 2) for s in src], markering=mark,
                              blandade=[j for j, s in enumerate(src) if isinstance(s, tuple)]))
        karta_ny_till_gammal += [_kalla_ruta(s) for s in src]
        s0 += L
    N = s0
    n["tagningar"] = nya_t
    n["rorelse"] = {pid: sp for pid, sp in ny_rorelse.items() if sp}
    n["tidsbas"]["antal_rutor"] = N
    for o in n["objekt"]:
        if o["synlig_ut"] == [[0, N_gammal]]:
            o["synlig_ut"] = [[0, N]]
        else:
            vis = [j for j, s in enumerate(karta_ny_till_gammal) if any(a <= round(s) < b for a, b in o["synlig_ut"])]
            o["synlig_ut"] = _komprimera(vis) or []
    n["objekt"] = [o for o in n["objekt"] if o["synlig_ut"]]
    kvar = {t["id"] for t in nya_t}
    for r in n["rum"]:
        par = [(t["id"], t["ut"]) for t in nya_t if t["id"] in r["tagningar"]]
        r["tagningar"] = [p[0] for p in par]
        r["ut"] = [p[1] for p in par]
    if n.get("trohet"):
        n["trohet"] = {k: v for k, v in n["trohet"].items() if k.split(":")[0] in kvar}
    for pid in list(n["personer"].keys()):
        if pid not in n["rorelse"]:
            n["personer"].pop(pid)
    n["tidskarta"] = tidskarta
    n["beslut"].append(dict(regel="C_tidslinje", notis=notis, rutor_fore=N_gammal, rutor_efter=N))
    return n


def _block_alla(P):
    return [(t["id"], list(range(t["ut"][0], t["ut"][1])), None) for t in P["tagningar"]]


def personer_endast_i(P, tid):
    return [pid for pid, sp in P["rorelse"].items() if {s["tagning"] for s in sp} == {tid}]


def _segment_tagning(P, a, b):
    t = next((t for t in P["tagningar"] if t["ut"][0] <= a < t["ut"][1]), None)
    if t is None:
        raise Avslag(f"rutorna {a}–{b} ligger utanför klippet")
    return t, max(a, t["ut"][0]), min(b, t["ut"][1])


def _handelser_i(K, a, b):
    return [e["id"] for e in (K.liggare or {}).get("handelser", []) if e["rutor"][0] < b and e["rutor"][1] > a]


# ============================================================================ tidslinje

def plan_ta_bort_tagning(K, tid):
    P = K.paket
    t = tagning(P, tid)
    if len(P["tagningar"]) == 1:
        raise Avslag("klippet har bara en tagning")
    borta = personer_endast_i(P, t["id"])
    rep = [r["id"] for r in K.repliker if (r.get("scen") or "").lower() == t["id"].lower()]
    return dict(effekter=[dict(typ="tar_bort", mal=dict(tagningar=[t["id"]], rutor=[tuple(t["ut"])], personer=borta,
                                                       handelser=_handelser_i(K, *t["ut"]), medie=rep),
                               beskrivning=f"tagning {t['id']} tas bort")],
                foljder=([f"{', '.join(borta)} finns bara i {t['id']} och försvinner ur klippet"] if borta else [])
                + ([f"repliker {', '.join(rep)} ligger i {t['id']}: ljud och text följer med bort (medielagret, spår D)"] if rep else []),
                platshallare=[], visa="remsa")


def gor_ta_bort_tagning(P, K, tid):
    t = tagning(P, tid)
    return bygg_om_tidslinje(P, [b for b in _block_alla(P) if b[0] != t["id"]], f"tagning {t['id']} borttagen")


def plan_flytta_tagning(K, tid, till):
    P = K.paket
    t = tagning(P, tid)
    ids = [x["id"] for x in P["tagningar"]]
    if not (0 <= till < len(ids)):
        raise Avslag("ny plats i ordningen finns inte")
    if ids.index(t["id"]) == till:
        raise Avslag(f"{t['id']} ligger redan där")
    lo, hi = sorted((ids.index(t["id"]), till))
    berorda = ids[lo:hi + 1]
    return dict(effekter=[dict(typ="flyttar_ordning", mal=dict(tagningar=berorda, rutor=[tuple(tagning(P, x)["ut"]) for x in berorda]),
                               beskrivning=f"{t['id']} flyttas till plats {till + 1}")],
                foljder=["repliker och text följer sina tagningar (tidskartan går till medielagret)"], platshallare=[], visa="remsa")


def gor_flytta_tagning(P, K, tid, till):
    t = tagning(P, tid)
    b = _block_alla(P)
    i = [x[0] for x in b].index(t["id"])
    blk = b.pop(i)
    b.insert(till, blk)
    return bygg_om_tidslinje(P, b, f"{t['id']} flyttad till plats {till + 1}")


def plan_hall_sista(K, sek=1.0):
    P = K.paket
    sist = P["tagningar"][-1]
    n = int(round(sek * K.fps))
    return dict(effekter=[dict(typ="lagger_till", mal=dict(tagningar=[sist["id"]]), beskrivning=f"sista rutan hålls {sek} s")],
                foljder=[f"sista bilden står still i {n} rutor (stillbild, ingen ny rörelse)", "ljud och text i slutet: medielagret (spår D)"],
                platshallare=["hållen sista ruta (stillbild)"], visa="remsa")


def gor_hall_sista(P, K, sek=1.0):
    n = int(round(sek * K.fps))
    b = _block_alla(P)
    tid, src, _ = b[-1]
    b[-1] = (tid, src + [src[-1]] * n, f"sista rutan hålls {n} rutor")
    return bygg_om_tidslinje(P, b, f"slutet förlängt {sek} s")


def plan_korta_tagning(K, tid, andel=0.5):
    P = K.paket
    t = tagning(P, tid)
    a, b = t["ut"]
    L = b - a
    q = int(round(L * (1 - andel) / 2))
    bort = (a + q, b - q)
    if bort[1] - bort[0] < 4:
        raise Avslag(f"{t['id']} är för kort att korta")
    return dict(effekter=[dict(typ="tar_bort", mal=dict(rutor=[bort], handelser=_handelser_i(K, *bort)), beskrivning=f"mitten av {t['id']} tas bort ({bort[0]}–{bort[1]})")],
                foljder=[f"hopp i bilden mitt i {t['id']} (hårt klipp inom tagningen)", "repliker i det borttagna: medielagret"],
                platshallare=[], visa="remsa")


def gor_korta_tagning(P, K, tid, andel=0.5):
    t = tagning(P, tid)
    a, b = t["ut"]
    q = int(round((b - a) * (1 - andel) / 2))
    blk = [(x[0], (list(range(a, a + q)) + list(range(b - q, b))) if x[0] == t["id"] else x[1],
            f"mitten borttagen ({a + q}–{b - q})" if x[0] == t["id"] else None) for x in _block_alla(P)]
    return bygg_om_tidslinje(P, blk, f"{t['id']} kortad")


def plan_ta_bort_segment(K, a, b, vad=""):
    t, a, b = _segment_tagning(K.paket, a, b)
    return dict(effekter=[dict(typ="tar_bort", mal=dict(rutor=[(a, b)], handelser=_handelser_i(K, a, b)), beskrivning=f"{vad} tas bort ({a}–{b})")],
                foljder=[f"hårt klipp i {t['id']} där {vad} var"], platshallare=[], visa="remsa")


def gor_ta_bort_segment(P, K, a, b, vad=""):
    t, a, b = _segment_tagning(P, a, b)
    blk = [(x[0], [s for s in x[1] if not (a <= s < b)] if x[0] == t["id"] else x[1], f"{vad} borttaget" if x[0] == t["id"] else None) for x in _block_alla(P)]
    return bygg_om_tidslinje(P, blk, f"segment {a}–{b} borttaget")


def plan_tempo_segment(K, a, b, faktor=1.5, vad=""):
    t, a, b = _segment_tagning(K.paket, a, b)
    return dict(effekter=[dict(typ="andrar_tid", mal=dict(rutor=[(a, b)], handelser=_handelser_i(K, a, b)), beskrivning=f"{vad} tar {faktor}× så lång tid")],
                foljder=[f"originalets rörelse omsamplad ({faktor}×), interpolerad mellan lästa rutor", "tal och musik under segmentet följer inte med: medielagret (spår D)"],
                platshallare=[], visa="remsa")


def gor_tempo_segment(P, K, a, b, faktor=1.5, vad=""):
    t, a, b = _segment_tagning(P, a, b)
    nytt = list(np.linspace(a, b, int(round((b - a) * faktor)), endpoint=False))
    blk = []
    for x in _block_alla(P):
        if x[0] == t["id"]:
            src = [s for s in x[1] if s < a] + [float(s) for s in nytt] + [s for s in x[1] if s >= b]
            blk.append((x[0], src, f"{vad} {faktor}×"))
        else:
            blk.append(x)
    return bygg_om_tidslinje(P, blk, f"tempo {faktor}× på {a}–{b}")


def plan_upprepa_segment(K, a, b, antal=2, vad=""):
    t, a, b = _segment_tagning(K.paket, a, b)
    return dict(effekter=[dict(typ="lagger_till", mal=dict(rutor=[(a, b)], handelser=_handelser_i(K, a, b)), beskrivning=f"{vad} {antal} gånger")],
                foljder=[f"samma rörelse upprepas ({antal}×) med en blandad skarv på {OVERGANG} rutor: en kopia, inte ett nytt förlopp"],
                platshallare=["upprepad originalrörelse (kopia)"], visa="remsa")


def gor_upprepa_segment(P, K, a, b, antal=2, vad=""):
    t, a, b = _segment_tagning(P, a, b)
    blk = []
    for x in _block_alla(P):
        if x[0] != t["id"]:
            blk.append(x)
            continue
        fore = [s for s in x[1] if s < b]
        efter = [s for s in x[1] if s >= b]
        seg = list(range(a, b))
        src = list(fore)
        for _ in range(antal - 1):
            skarv = [("mix", float(b - 1), float(a), (k + 1) / (OVERGANG + 1)) for k in range(OVERGANG)]
            src += skarv + seg
        blk.append((x[0], src + efter, f"{vad} ×{antal}"))
    return bygg_om_tidslinje(P, blk, f"upprepning {antal}× av {a}–{b}")


# ============================================================================ föremål

FARGER = ["#c0392b", "#27ae60", "#2980b9", "#8e44ad", "#d35400", "#16a085", "#f1c40f", "#7f8c8d"]


def _farg(namn):
    return FARGER[int(hashlib.sha1(namn.encode("utf-8")).hexdigest(), 16) % len(FARGER)]


def plan_ta_bort_objekt(K, oid):
    P = K.paket
    o = objekt(P, oid)
    if o["typ"] in ("golv", "vagg"):
        raise Avslag("golv och väggar tas inte bort; byt miljön i stället")
    ank = [(t["id"], p["id"]) for t in P["tagningar"] for p in t["personer"] if p.get("ankare") == oid]
    foljder = []
    if ank:
        foljder.append(f"{', '.join(f'{p} i {t}' for t, p in ank)} sitter eller står vid {oid}: kroppen ändras inte och blir utan stöd (läs om kroppen: kroppsvägen)")
    if o["typ"] == "bord":
        foljder.append("händer och armbågar som vilar mot skivan vilar mot ingenting (kinematiken räknas inte om)")
    return dict(effekter=[dict(typ="tar_bort", mal=dict(objekt=[oid]), beskrivning=f"{oid} tas bort")],
                foljder=foljder, platshallare=[], visa=dict(objekt=oid))


def gor_ta_bort_objekt(P, K, oid):
    n = kopia(P)
    n["objekt"] = [o for o in n["objekt"] if o["id"] != oid and not o["id"].startswith(oid + ":")]
    for t in n["tagningar"]:
        for p in t["personer"]:
            if p.get("ankare") == oid:
                p["ankare"] = None
    for pid, info in n["personer"].items():
        if info.get("hemplats") == oid:
            info["hemplats"] = None
    n["beslut"].append(dict(regel="C_ta_bort_objekt", objekt=oid))
    return n


def plan_byt_objekt(K, oid, ny):
    o = objekt(K.paket, oid)
    nyc = K.foremals_nycklar().get(oid) or o["typ"]
    return dict(effekter=[dict(typ="byter", mal=dict(objekt=[oid], namn=[nyc]), beskrivning=f"{oid} ({nyc}) byts mot {ny}")],
                foljder=[f"samma plats och mått; formen är en låda märkt '{ny}' (platshållare)"],
                platshallare=[f"{ny}: låda med etikett"], visa=dict(objekt=oid))


def gor_byt_objekt(P, K, oid, ny):
    n = kopia(P)
    o = next(o for o in n["objekt"] if o["id"] == oid)
    o["byte_fran"] = K.foremals_nycklar().get(oid) or o["typ"]
    o["etikett"] = ny
    o["farg"] = _farg(ny)
    o["form_status"] = "platshallare"
    n["beslut"].append(dict(regel="C_byt_objekt", objekt=oid, ny=ny))
    return n


def plan_lagg_till_objekt(K, etikett, pa):
    st = objekt(K.paket, pa)
    if st["typ"] not in ("bord",):
        raise Avslag(f"{pa} är ingen yta att ställa något på")
    return dict(effekter=[dict(typ="lagger_till", mal=dict(objekt=[pa]), beskrivning=f"{etikett} ställs på {pa}")],
                foljder=["ingen i scenen rör föremålet (ingen handling knyts till det)"],
                platshallare=[f"{etikett}: låda 12×12×12 cm"], visa=dict(objekt=pa))


def gor_lagg_till_objekt(P, K, etikett, pa):
    n = kopia(P)
    st = next(o for o in n["objekt"] if o["id"] == pa)
    rz = st["rot"][2]
    # en fri punkt på skivan: en tredjedel in från mitten längs skivans långa sida
    dx = st["matt"][0] / 3
    pos = [st["pos"][0] + dx * math.cos(rz), st["pos"][1] + dx * math.sin(rz), st["pos"][2] + st["matt"][2] / 2 + 0.06]
    nid = f"{pa}:pa:{etikett.replace(' ', '_')}"
    n["objekt"].append(dict(id=nid, bas=nid, typ="foremal", pos=[round(v, 4) for v in pos], rot=[0.0, 0.0, rz], matt=[0.12, 0.12, 0.12],
                            farg=_farg(etikett), status="tillagd_platshallare", rum=st.get("rum", "gemensamt"),
                            synlig_ut=copy.deepcopy(st["synlig_ut"]), etikett=etikett, form_status="platshallare"))
    n["beslut"].append(dict(regel="C_lagg_till_objekt", objekt=nid, pa=pa))
    return n


def plan_flytta_objekt(K, oid, till):
    o = objekt(K.paket, oid)
    m = objekt(K.paket, till)
    if m["typ"] != "bord":
        raise Avslag(f"{till} är ingen yta")
    return dict(effekter=[dict(typ="flyttar", mal=dict(objekt=[oid]), beskrivning=f"{oid} flyttas till {till}")],
                foljder=["händer som höll eller rörde föremålet följer inte med"], platshallare=[], visa=dict(objekt=oid))


def gor_flytta_objekt(P, K, oid, till):
    n = kopia(P)
    o = next(o for o in n["objekt"] if o["id"] == oid)
    m = next(o for o in n["objekt"] if o["id"] == till)
    o["pos"] = [m["pos"][0], m["pos"][1], m["pos"][2] + m["matt"][2] / 2 + o["matt"][2] / 2]
    o["synlig_ut"] = copy.deepcopy(m["synlig_ut"])
    n["beslut"].append(dict(regel="C_flytta_objekt", objekt=oid, till=till))
    return n


def plan_byt_foremal_i_hand(K, person, gammalt, nytt, rutor, sida="r"):
    if person not in K.personer():
        raise Avslag(f"{person} finns inte i förvärlden")
    return dict(effekter=[dict(typ="byter", mal=dict(namn=[gammalt], personer=[]), beskrivning=f"{gammalt} i {person}s hand byts mot {nytt}")],
                foljder=[f"{person}s rörelse ändras inte: greppet för {gammalt} står kvar (ett nytt grepp kräver kroppsvägen)",
                         "produkten byts också på ryggradsnivå (mallens plats [produkt])"],
                platshallare=[f"{nytt}: låda i {person}s hand ({'höger' if sida == 'r' else 'vänster'})"],
                visa=dict(person=person, rutor=list(rutor)))


def gor_byt_foremal_i_hand(P, K, person, gammalt, nytt, rutor, sida="r"):
    n = kopia(P)
    a, b = rutor
    L = {nm: i for i, nm in enumerate(P["leder"])}
    pos = []
    for sp in P["rorelse"].get(person, []):
        U, X = spar_array(sp)
        m = (U >= a) & (U < b)
        if m.any():
            pos.append(np.median(X[m, L[f"{sida}_hand_mitt"]], axis=0) / 1000)
    if not pos:
        raise Avslag(f"{person} syns inte i rutorna {a}–{b}")
    p = np.mean(pos, axis=0)
    nid = f"{person}:hand:{nytt.replace(' ', '_')}"
    n["objekt"].append(dict(id=nid, bas=nid, typ="foremal", pos=[round(float(v), 4) for v in p], rot=[0.0, 0.0, 0.0], matt=[0.07, 0.07, 0.05],
                            farg=_farg(nytt), status="tillagd_platshallare", rum="gemensamt", synlig_ut=[[int(a), int(b)]],
                            etikett=nytt, byte_fran=gammalt, form_status="platshallare",
                            faste=dict(person=person, led=f"{sida}_hand_mitt", not_emit="emit_bpy följer inte fästet; förhandsvisningen gör det")))
    n["beslut"].append(dict(regel="C_byt_foremal_i_hand", person=person, gammalt=gammalt, nytt=nytt, rutor=[int(a), int(b)]))
    return n


# ============================================================================ plats

MILJOFARG = {"golv": "#5b4a3a", "vagg": "#9aa5a8"}


def plan_byt_miljo(K, miljo):
    return dict(effekter=[dict(typ="byter", mal=dict(objekt=["rum"]), beskrivning=f"miljön byts till {miljo}")],
                foljder=["rummets form, möbler, kroppar och kamera är kvar; bara etikett och färger byts",
                         "en ny lokal måste skannas eller byggas för att synas på riktigt"],
                platshallare=[f"miljö '{miljo}': etikett och färg på golv och väggar"], visa=dict(rum=True))


def gor_byt_miljo(P, K, miljo):
    n = kopia(P)
    h = int(hashlib.sha1(miljo.encode("utf-8")).hexdigest(), 16)
    for o in n["objekt"]:
        if o["typ"] == "golv":
            o["farg"] = "#%02x%02x%02x" % (60 + h % 60, 50 + (h >> 8) % 60, 40 + (h >> 16) % 60)
        elif o["typ"] == "vagg":
            o["farg"] = "#%02x%02x%02x" % (150 + (h >> 4) % 90, 140 + (h >> 12) % 90, 120 + (h >> 20) % 90)
    for r in n["rum"]:
        r["miljo"] = miljo
        r["beskrivning"] = f"{r.get('beskrivning', '')} [miljö: {miljo}, platshållare]"
    n["miljo"] = dict(namn=miljo, status="platshallare")
    n["beslut"].append(dict(regel="C_byt_miljo", miljo=miljo))
    return n


def _rotz(rz):
    return np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])


def _narmaste_bord(P, pid, tid):
    L = {nm: i for i, nm in enumerate(P["leder"])}
    sp = next((s for s in P["rorelse"].get(pid, []) if s["tagning"] == tid), None)
    if sp is None:
        raise Avslag(f"{pid} syns inte i {tid}")
    U, X = spar_array(sp)
    c = np.median(X[:, L["c_spine2"], :2], axis=0) / 1000
    bord = [o for o in P["objekt"] if o["typ"] == "bord"]
    if not bord:
        return None, c
    return min(bord, key=lambda o: np.linalg.norm(np.array(o["pos"][:2]) - c)), c


def plan_flytta_interaktion(K, person, tid, till):
    P = K.paket
    t = tagning(P, tid)
    mal = objekt(P, till)
    kalla, c = _narmaste_bord(P, person, t["id"])
    if kalla is None:
        raise Avslag(f"{person} står inte vid något bord i {tid}")
    if kalla["id"] == till:
        raise Avslag(f"{person} är redan vid {till} i {tid}")
    andra = [p["id"] for p in t["personer"] if p["id"] != person]
    return dict(effekter=[dict(typ="flyttar", mal=dict(personer=[person], tagningar=[t["id"]]), beskrivning=f"{person} i {t['id']} flyttas från {kalla['id']} till {till}")],
                foljder=[f"{person} och kameran i {t['id']} flyttas och vrids lika mycket: kompositionen mot personen och bordet är densamma, bakgrunden byts"]
                + ([f"{', '.join(andra)} i samma tagning följer inte med"] if andra else []),
                platshallare=[], visa=dict(tagning=t["id"]))


def gor_flytta_interaktion(P, K, person, tid, till):
    n = kopia(P)
    t = next(x for x in n["tagningar"] if x["id"].lower() == tid.lower())
    kalla, _ = _narmaste_bord(P, person, t["id"])
    mal = next(o for o in P["objekt"] if o["id"] == till)
    drz = mal["rot"][2] - kalla["rot"][2]
    R = _rotz(drz)
    p0 = np.array(kalla["pos"][:2] + [0.0])
    p1 = np.array(mal["pos"][:2] + [0.0])
    dz = (mal["pos"][2] + mal["matt"][2] / 2) - (kalla["pos"][2] + kalla["matt"][2] / 2)

    def flytta(x):
        return (x - p0) @ R.T + p1 + np.array([0, 0, dz])

    for sp in n["rorelse"][person]:
        if sp["tagning"] != t["id"]:
            continue
        U, X = spar_array(sp)
        Xm = flytta(X / 1000) * 1000
        sp["rutor"] = spar_rutor(U, Xm)
    # kameran vrids med samma z-rotation som personen, så kompositionen mot person och bord består
    nyck = []
    for k in t["kamera"]["nycklar"]:
        u, x, y, z, qw, qx, qy, qz, lins = k
        pos = flytta(np.array([x, y, z]))
        Rk = R @ quat_till_mat([qw, qx, qy, qz])
        q = mat_till_quat(Rk)
        nyck.append([u] + [round(float(v), 5) for v in pos] + [round(float(v), 6) for v in q] + [lins])
    t["kamera"]["nycklar"] = nyck
    for p in t["personer"]:
        if p["id"] == person:
            p["ankare"] = till if mal["typ"] in ("stol",) else p.get("ankare")
    n["beslut"].append(dict(regel="C_flytta_interaktion", person=person, tagning=t["id"], fran=kalla["id"], till=till, vridning_grader=round(math.degrees(drz), 1)))
    return n


# ============================================================================ kamera

def plan_kamera_stabilisera(K, tagningar=None):
    P = K.paket
    rorliga = [t["id"] for t in P["tagningar"] if not t["kamera"].get("statisk") and len(t["kamera"]["nycklar"]) > 1]
    if tagningar:
        rorliga = [t for t in rorliga if t.lower() in {x.lower() for x in tagningar}]
    if not rorliga:
        vilka = ", ".join(tagningar) if tagningar else "klippet"
        raise Avslag(f"kameran står redan still i {vilka} i förvärlden")
    return dict(effekter=[dict(typ="andrar_kamera", mal=dict(objekt=["kamera"], tagningar=rorliga), beskrivning=f"kameran står still i {', '.join(rorliga)}")],
                foljder=["kamerarörelsen som ingesten lade i kameran (R25) blir rörelse i bild i stället"], platshallare=[],
                visa=dict(tagning=rorliga[0]))


def gor_kamera_stabilisera(P, K, tagningar=None):
    n = kopia(P)
    for t in n["tagningar"]:
        if t["kamera"].get("statisk") or len(t["kamera"]["nycklar"]) == 1:
            continue
        if tagningar and t["id"].lower() not in {x.lower() for x in tagningar}:
            continue
        ks = np.array(t["kamera"]["nycklar"], float)
        mitt = ks[len(ks) // 2]
        t["kamera"] = dict(statisk=True, nycklar=[[int(t["ut"][0])] + [round(float(v), 5) for v in mitt[1:]]])
    n["beslut"].append(dict(regel="C_kamera_stabilisera", tagningar=tagningar))
    return n


def _person_punkt(P, pid, tid):
    L = {nm: i for i, nm in enumerate(P["leder"])}
    sp = next((s for s in P["rorelse"].get(pid, []) if s["tagning"].lower() == tid.lower()), None)
    if sp is None:
        raise Avslag(f"{pid} syns inte i {tid}")
    U, X = spar_array(sp)
    return np.median((X[:, L["c_neck"]] + X[:, L["c_spine2"]]) / 2, axis=0) / 1000


def plan_kamera_narmare(K, tid, person, faktor=0.7):
    P = K.paket
    t = tagning(P, tid)
    _person_punkt(P, person, t["id"])
    return dict(effekter=[dict(typ="andrar_kamera", mal=dict(objekt=["kamera"], tagningar=[t["id"]]), beskrivning=f"kameran {round((1 - faktor) * 100)} % närmare {person} i {t['id']}")],
                foljder=["kameran flyttas längs linjen mot personen; vinkel och brännvidd är kvar"], platshallare=[], visa=dict(tagning=t["id"]))


def gor_kamera_narmare(P, K, tid, person, faktor=0.7):
    n = kopia(P)
    t = next(x for x in n["tagningar"] if x["id"].lower() == tid.lower())
    mal = _person_punkt(P, person, t["id"])
    for k in t["kamera"]["nycklar"]:
        c = np.array(k[1:4])
        ny = mal + (c - mal) * faktor
        k[1:4] = [round(float(v), 5) for v in ny]
    n["beslut"].append(dict(regel="C_kamera_narmare", tagning=t["id"], person=person, faktor=faktor))
    return n


def plan_kamera_lins(K, faktor, tagningar=None):
    P = K.paket
    tt = [t["id"] for t in P["tagningar"] if not tagningar or t["id"].lower() in {x.lower() for x in tagningar}]
    return dict(effekter=[dict(typ="andrar_kamera", mal=dict(objekt=["kamera"], tagningar=tt), beskrivning=("tätare" if faktor > 1 else "vidare") + " bild")],
                foljder=["brännvidden ändras; personer nära kanten kan hamna utanför bild" if faktor > 1 else "mer av rummet syns, och rummet är en blockout"],
                platshallare=[], visa=dict(tagning=tt[0]))


def gor_kamera_lins(P, K, faktor, tagningar=None):
    n = kopia(P)
    for t in n["tagningar"]:
        if tagningar and t["id"].lower() not in {x.lower() for x in tagningar}:
            continue
        for k in t["kamera"]["nycklar"]:
            k[8] = round(k[8] * faktor, 3)
    n["beslut"].append(dict(regel="C_kamera_lins", faktor=faktor))
    return n


# ============================================================================ kropp

def plan_sta_still(K, person, tid):
    P = K.paket
    t = tagning(P, tid)
    L = {nm: i for i, nm in enumerate(P["leder"])}
    sp = next((s for s in P["rorelse"].get(person, []) if s["tagning"] == t["id"]), None)
    if sp is None:
        raise Avslag(f"{person} syns inte i {t['id']}")
    U, X = spar_array(sp)
    bana = X[:, L["c_spine0"], :2] / 1000
    stracka = float(np.sum(np.linalg.norm(np.diff(bana, axis=0), axis=1)))
    spann = float(np.max(np.linalg.norm(bana - np.median(bana, axis=0), axis=1)))
    if spann < 0.10:
        raise Avslag(f"{person} förflyttar sig redan inte i {t['id']} (bäckenet rör sig högst {spann:.2f} m)")
    return dict(effekter=[dict(typ="andrar_rorelse", mal=dict(personer=[person], rutor=[tuple(t["ut"])]), beskrivning=f"{person} står kvar i {t['id']}")],
                foljder=[f"förflyttningen ({stracka:.2f} m bäckenbana) tas bort; armar, bål och huvud rör sig som i originalet",
                         "benen gör fortfarande stegrörelser på stället (kinematisk platshållare)"],
                platshallare=["låst förflyttning: originalets överkropp, benens steg kvar"], visa=dict(tagning=t["id"], person=person))


def gor_sta_still(P, K, person, tid):
    n = kopia(P)
    L = {nm: i for i, nm in enumerate(P["leder"])}
    for sp in n["rorelse"][person]:
        if sp["tagning"].lower() != tid.lower():
            continue
        U, X = spar_array(sp)
        bana = X[:, L["c_spine0"], :2]
        mitt = np.median(bana, axis=0)
        X[:, :, :2] -= (bana - mitt)[:, None, :]
        sp["rutor"] = spar_rutor(U, X)
    n["beslut"].append(dict(regel="C_sta_still", person=person, tagning=tid))
    return n


def plan_ga_med_attityd(K, person):
    P = K.paket
    info = P["personer"].get(person)
    if info is None:
        raise Avslag(f"{person} finns inte i förvärlden")
    if info.get("pose") != "sittande":
        raise Avslag(f"{person} sitter inte i originalet")
    stol = f"stol_{person}"
    return dict(effekter=[dict(typ="andrar_rorelse", mal=dict(personer=[person]), beskrivning=f"{person} går i stället för att sitta"),
                          dict(typ="tar_bort", mal=dict(objekt=[stol]), beskrivning=f"{stol} tas bort")],
                foljder=["gången är syntetiserad (mening_motor.ga_med_attityd): fötterna glider 0,28–0,49 m/s i stödfas och personen går på stället sist (runda 1, MENING.md §3.2)",
                         "ryggens lutning kopieras från den sittande; slappheten och etiketten följer inte med per tagning",
                         "varje tagning får en egen gång med egen riktning"],
                platshallare=["syntetiserad gång (Argon), inte databuren"], visa=dict(person=person))


def gor_ga_med_attityd(P, K, person):
    sys.path.insert(0, str(ROT / "forvarld_karna"))
    import mening_motor  # Argons kärna; ga_med_attityd speglar inte
    nytt, rapport = mening_motor.manipulera_scen(P, "ga_med_attityd", person)
    nytt["beslut"].append(dict(regel="C_ga_med_attityd", person=person, grindar=rapport.get("grindar_sammanfattning")))
    return nytt


# ============================================================================ register

DRAG = {}
for _namn in ["ta_bort_tagning", "flytta_tagning", "hall_sista", "korta_tagning", "ta_bort_segment", "tempo_segment", "upprepa_segment",
              "ta_bort_objekt", "byt_objekt", "lagg_till_objekt", "flytta_objekt", "byt_foremal_i_hand",
              "byt_miljo", "flytta_interaktion", "kamera_stabilisera", "kamera_narmare", "kamera_lins", "sta_still", "ga_med_attityd"]:
    DRAG[_namn] = (globals()[f"plan_{_namn}"], globals()[f"gor_{_namn}"])

KATEGORI = {"ta_bort_tagning": "tidslinje", "flytta_tagning": "tidslinje", "hall_sista": "tidslinje", "korta_tagning": "tidslinje",
            "ta_bort_segment": "tidslinje", "tempo_segment": "tidslinje", "upprepa_segment": "tidslinje",
            "ta_bort_objekt": "föremål", "byt_objekt": "föremål", "lagg_till_objekt": "föremål", "flytta_objekt": "föremål",
            "byt_foremal_i_hand": "föremål", "byt_miljo": "plats", "flytta_interaktion": "plats",
            "kamera_stabilisera": "kamera", "kamera_narmare": "kamera", "kamera_lins": "kamera", "sta_still": "kropp", "ga_med_attityd": "kropp"}
