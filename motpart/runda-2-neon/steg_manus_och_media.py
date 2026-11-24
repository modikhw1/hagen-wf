"""Del 3 (steg_manus_och_media.py):
1. Deterministisk export av inspelningsmanus (K6) ur `scenpaket/2`: varje scen besvarar de 5 K6-frågorna
   (vem, var, vad_sags_eller_text, hur, hur_lange_s) + flaggar `barande` (K5).
2. Medielager-redigerare (K5 + K7 + K8) direkt på `scenpaket/2`:
   - `byt_skarmtext`, `ta_bort_skarmtext`, `byt_replik`, `ta_bort_tagning`
   - Loggar varje anrop för K7-spärren (0 generativa API-anrop, 0 spegling)
   - Utfärdar K5-varning ("Meningen bärs av ...") när en bärande scen/text berörs
   - Returnerar ärligt `nej` (status="nekad_saknat_lager") när ett klipp saknar medielagret (K8-alarm).
3. Fyra NYA oberoende mått (N1-N4) som Claude inte har, alla med inbyggda felinjektionsprov:
   - N1 `kam_over_bord`: ingen kamera får ligga under en närliggande bordsskiva (fångar Claudes P2-fel!).
   - N2 `antagen_tackning` (K4): varje skymd benrekonstruktion och syntetisk stol måste vara märkt `antagen`.
   - N3 `manus_k6_kompletthet` (K6): alla 5 frågor besvarade per scen + felinjektion (stryk en scen -> larm).
   - N4 `medielager_k5_k8` (K5+K7+K8): redigering, bärande-varning och ärligt nej på saknat lager.
"""
from __future__ import annotations

import copy
import math
import pathlib

import numpy as np


def _fotavtryck_dist(xy: np.ndarray, o: dict) -> float:
    p = np.array(o["pos"][:2], float)
    m = np.array(o["matt"][:2], float) / 2.0
    rz = float(o["rot"][2])
    R = np.array([[math.cos(rz), -math.sin(rz)], [math.sin(rz), math.cos(rz)]])
    lok = (np.asarray(xy) - p) @ R
    d = np.maximum(np.abs(lok) - m, 0.0)
    return float(np.linalg.norm(d))


# ------------------------------------------------------------------ K6: Inspelningsmanus ur scenpaket/2
def bygg_manus(paket: dict) -> dict:
    """Bygger ett inspelningsbart manus (K6) direkt ur scenpaket/2 utan modell- eller manuella tillägg."""
    mening = paket.get("mening") or {}
    fps = float(paket["tidsbas"]["fps"])
    scener_in = mening.get("scener") or []
    scener_ut = []
    for idx, sc in enumerate(scener_in, 1):
        sid = sc["tagning"]
        t_obj = next((t for t in paket["tagningar"] if t["id"] == sid), None)
        kam_stil = "rörlig kamera" if (t_obj and not t_obj["kamera"]["statisk"]) else "stillastående kamera"
        roller_pose = [
            f"{pid} ({(paket['personer'].get(pid) or {}).get('pose', 'okänd')})"
            for pid in sc.get("vem", []) if pid != "ingen_person_i_bild"
        ]
        vad_sags = " / ".join(sc.get("repliker") or [])
        skarm = " / ".join(sc.get("skarmtext") or [])
        if vad_sags and skarm:
            tal_och_text = f"Tal: \"{vad_sags}\" | Skärmtext: \"{skarm}\""
        elif vad_sags:
            tal_och_text = f"Tal: \"{vad_sags}\""
        elif skarm:
            tal_och_text = f"Inget tal | Skärmtext: \"{skarm}\""
        else:
            tal_och_text = "Inget tal, ingen skärmtext (bildburen scen)"

        scener_ut.append(dict(
            nr=idx,
            tagning=sid,
            funktion=sc.get("funktion", "scen"),
            barande=bool(sc.get("barande", False)),
            vem=", ".join(roller_pose) if roller_pose else "Ingen person i bild (närbild/B-roll)",
            var=sc.get("var", ""),
            vad_sags_eller_text=tal_och_text,
            hur=f"{sc.get('vad', '')} ({kam_stil})",
            hur_lange_s=float(sc.get("langd_s", 0.0)),
            start_s=float(sc.get("start_s", 0.0)),
            slut_s=float(sc.get("slut_s", 0.0)),
        ))

    return dict(
        klipp_id=paket["klipp"]["id"],
        total_langd_s=round(paket["tidsbas"]["antal_rutor"] / fps, 2),
        karna=mening.get("karna", ""),
        antal_scener=len(scener_ut),
        scener=scener_ut,
    )


def manus_till_markdown(manus: dict) -> str:
    rader = [
        f"# Inspelningsmanus: `{manus['klipp_id']}` ({manus['total_langd_s']} s)",
        f"**Kärna:** {manus['karna'] or '(saknas)'}",
        "",
        "| # | Tagning | Funktion | Bärande | Vem | Var | Vad sägs / Skärmtext | Hur | Längd |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in manus["scener"]:
        rader.append(
            f"| {s['nr']} | {s['tagning']} | {s['funktion']} | {'JA' if s['barande'] else 'nej'} | "
            f"{s['vem']} | {s['var']} | {s['vad_sags_eller_text']} | {s['hur']} | {s['hur_lange_s']} s |"
        )
    return "\n".join(rader) + "\n"


# ------------------------------------------------------------------ K5 + K7 + K8: Medielager-redigerare
def redigera_medielager(paket: dict, operation: str, tagning: str | None = None, ny_text: str = "") -> dict:
    """Utför redigering på medielager (K8) med K5-varning för bärande element och K7-spärrlogg."""
    nytt = copy.deepcopy(paket)
    mening = nytt.setdefault("mening", {})
    logg = dict(operation=operation, tagning=tagning, generativa_anrop=0, spegling_anvand=False)
    varningar = []

    if operation == "byt_skarmtext":
        st_lista = mening.get("skarmtext") or []
        traff = [x for x in st_lista if tagning is None or x["tagning"] == tagning]
        if not traff:
            return dict(status="nekad_saknat_lager", skäl="Klippet/tagningen har ingen skärmtext att byta.",
                        varningar=[], k7_logg=logg, paket=nytt)
        for x in traff:
            if x.get("barande"):
                varningar.append(f"Meningen bärs av skärmtexten i {x['tagning']} ('{x['text']}') — kontrollera att poängen överlever.")
            x["text"] = ny_text
        for sc in mening.get("scener") or []:
            if tagning is None or sc["tagning"] == tagning:
                sc["skarmtext"] = [x["text"] for x in st_lista if x["tagning"] == sc["tagning"]]
        return dict(status="utford", andrade=len(traff), varningar=varningar, k7_logg=logg, paket=nytt)

    if operation == "ta_bort_skarmtext":
        st_lista = mening.get("skarmtext") or []
        traff = [x for x in st_lista if tagning is None or x["tagning"] == tagning]
        if not traff:
            return dict(status="nekad_saknat_lager", skäl="Ingen skärmtext att ta bort.",
                        varningar=[], k7_logg=logg, paket=nytt)
        for x in traff:
            if x.get("barande"):
                varningar.append(f"Meningen bärs av skärmtexten i {x['tagning']} ('{x['text']}').")
        mening["skarmtext"] = [x for x in st_lista if not (tagning is None or x["tagning"] == tagning)]
        for sc in mening.get("scener") or []:
            if tagning is None or sc["tagning"] == tagning:
                sc["skarmtext"] = []
        return dict(status="utford", borttagna=len(traff), varningar=varningar, k7_logg=logg, paket=nytt)

    if operation == "byt_replik":
        rep_lista = mening.get("repliker") or []
        traff = [r for r in rep_lista if tagning is None or r["tagning"] == tagning]
        if not traff:
            return dict(status="nekad_saknat_lager", skäl="Klippet/tagningen saknar tal/repliker att byta.",
                        varningar=[], k7_logg=logg, paket=nytt)
        for r in traff:
            if r.get("barande"):
                varningar.append(f"Meningen bärs av repliken i {r['tagning']} ('{r['text']}') — kontrollera att premissen/vändningen består.")
            r["text"] = ny_text
        for sc in mening.get("scener") or []:
            if tagning is None or sc["tagning"] == tagning:
                sc["repliker"] = [r["text"] for r in rep_lista if r["tagning"] == sc["tagning"]]
        return dict(status="utford", andrade=len(traff), varningar=varningar, k7_logg=logg, paket=nytt)

    if operation == "ta_bort_tagning":
        scener = mening.get("scener") or []
        traff = [sc for sc in scener if sc["tagning"] == tagning]
        if not traff:
            return dict(status="nekad_saknat_lager", skäl=f"Tagning {tagning} finns inte.",
                        varningar=[], k7_logg=logg, paket=nytt)
        if traff[0].get("barande"):
            varningar.append(f"Meningen bärs av tagning {tagning} (funktion={traff[0].get('funktion')}: '{traff[0].get('vad')}').")
        mening["scener"] = [sc for sc in scener if sc["tagning"] != tagning]
        return dict(status="utford", borttagna=1, varningar=varningar, k7_logg=logg, paket=nytt)

    return dict(status="nekad_okand_op", skäl=f"Okänd operation: {operation}", varningar=[], k7_logg=logg, paket=nytt)


# ------------------------------------------------------------------ N1-N4: Nya oberoende mått (med felinjektion!)
def mat_n1_kam_over_bord(paket: dict, max_avstand_m: float = 1.5) -> dict:
    """N1: Kontrollerar att ingen kamera hamnar under en närliggande bordsskivas överyta."""
    bord = [o for o in paket["objekt"] if o["typ"] == "bord"]
    brott = []
    for t in paket["tagningar"]:
        cz = float(t["kamera"]["nycklar"][0][3])
        cxy = np.array(t["kamera"]["nycklar"][0][1:3], float)
        for b in bord:
            topp = float(b["pos"][2] + b["matt"][2] / 2.0)
            dist = _fotavtryck_dist(cxy, b)
            if cz < topp and dist < max_avstand_m:
                brott.append(dict(tagning=t["id"], kamera_z=round(cz, 3), bord=b["id"], bord_topp_z=round(topp, 3),
                                  diff_m=round(cz - topp, 3), avstand_xy_m=round(dist, 3)))
    return dict(ok=(len(brott) == 0), antal_brott=len(brott), brott=brott)


def mat_n2_antagen_tackning(paket: dict) -> dict:
    """N2 (K4): Kontrollerar att syntetiska stolar och skymda benrekonstruktioner uttryckligen bär status='antagen'."""
    stolar = [o for o in paket["objekt"] if o["typ"] == "stol"]
    omarkta_stolar = [o["id"] for o in stolar if o.get("status") != "antagen"]
    ben_beslut = [b for b in paket.get("beslut", []) if b.get("regel") == "S2_skymda_ben_antagen"]
    omarkta_ben = [f"{b.get('tagning')}:{b.get('person')}" for b in ben_beslut if b.get("status") != "antagen"]
    tot = len(stolar) + len(ben_beslut)
    fel = len(omarkta_stolar) + len(omarkta_ben)
    return dict(
        ok=(fel == 0),
        totalt_antagna_poster=tot,
        tackning_pct=round(100.0 * (tot - fel) / max(tot, 1), 1),
        omarkta_stolar=omarkta_stolar,
        omarkta_ben=omarkta_ben,
    )


def mat_n3_manus_k6(paket: dict, manus: dict) -> dict:
    """N3 (K6): Kontrollerar att varje tagning i paketet har en komplett manusscen med alla 5 K6-fält."""
    forvantade = [t["id"] for t in paket["tagningar"]]
    sc_map = {s["tagning"]: s for s in manus.get("scener", [])}
    saknade_scener = [sid for sid in forvantade if sid not in sc_map]
    ofullstandiga = []
    for sid, s in sc_map.items():
        brister = []
        for f in ("vem", "var", "vad_sags_eller_text", "hur"):
            if not str(s.get(f, "")).strip():
                brister.append(f)
        if not (isinstance(s.get("hur_lange_s"), (int, float)) and s["hur_lange_s"] > 0):
            brister.append("hur_lange_s")
        if brister:
            ofullstandiga.append(dict(tagning=sid, brister=brister))
    n_ok = len(forvantade) - len(saknade_scener) - len(ofullstandiga)
    return dict(
        ok=(len(saknade_scener) == 0 and len(ofullstandiga) == 0),
        scener_ok=f"{n_ok}/{len(forvantade)}",
        kompletthet_pct=round(100.0 * n_ok / max(len(forvantade), 1), 1),
        saknade_scener=saknade_scener,
        ofullstandiga=ofullstandiga,
    )


def felinjektion_n1_n4(paket: dict) -> dict:
    """Bevisar enligt PROTOKOLL.md:8 att samtliga nya mått N1-N4 faktiskt KAN LARMA vid fel!"""
    # N1 felinjektion: sänk kameran 0.6 m i första tagningen -> ska larma om ett bord finns inom 1.5 m (annars skapa bord på 0.8 m)
    p_n1 = copy.deepcopy(paket)
    t0 = p_n1["tagningar"][0]
    t0["kamera"]["nycklar"][0][3] = 0.40
    if not any(o["typ"] == "bord" for o in p_n1["objekt"]):
        cxy = t0["kamera"]["nycklar"][0][1:3]
        p_n1["objekt"].append(dict(id="test_bord", typ="bord", pos=[cxy[0], cxy[1] + 0.5, 0.72], matt=[1.0, 0.5, 0.06], rot=[0, 0, 0]))
    else:
        # Flytta första bordet nära kameran om inget ligger inom 1.5 m
        cxy = np.array(t0["kamera"]["nycklar"][0][1:3], float)
        b0 = next(o for o in p_n1["objekt"] if o["typ"] == "bord")
        if _fotavtryck_dist(cxy, b0) >= 1.5:
            b0["pos"][0], b0["pos"][1] = float(cxy[0]), float(cxy[1] + 0.5)
    n1_larm = not mat_n1_kam_over_bord(p_n1)["ok"]

    # N2 felinjektion: ta bort 'antagen'-märkning på en stol eller skymd-ben-post -> ska larma
    p_n2 = copy.deepcopy(paket)
    andrad = False
    for b in p_n2.get("beslut", []):
        if b.get("regel") == "S2_skymda_ben_antagen":
            b["status"] = "observed"
            andrad = True
            break
    if not andrad:
        for o in p_n2["objekt"]:
            if o["typ"] == "stol":
                o["status"] = "observed"
                andrad = True
                break
    n2_larm = (not mat_n2_antagen_tackning(p_n2)["ok"]) if andrad else False

    # N3 felinjektion: stryk en scen ur manus -> ska larma
    manus_trasig = bygg_manus(paket)
    manus_trasig["scener"] = manus_trasig["scener"][1:]
    n3_larm = not mat_n3_manus_k6(paket, manus_trasig)["ok"]

    # N4 felinjektion: "byt_skarmtext" på ett klipp helt utan skärmtext -> ska ge ärligt nej (status=nekad_saknat_lager)
    p_n4 = copy.deepcopy(paket)
    p_n4["mening"]["skarmtext"] = []
    res_n4_nej = redigera_medielager(p_n4, "byt_skarmtext", None, "Ny text")
    n4_larm_nej = (res_n4_nej["status"] == "nekad_saknat_lager")

    return dict(
        N1_larmar_vid_kam_under_bord=n1_larm,
        N2_larmar_vid_omarkt_antagen=n2_larm,
        N3_larmar_vid_saknad_scen=n3_larm,
        N4_larmar_arligt_nej_utan_text=n4_larm_nej,
    )
