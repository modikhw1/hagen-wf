r"""Spår C: kör CM-meningar genom router -> K5-vakt -> drag på scenpaket/2 -> förhandsvisning, och mäter.

Kör (från repots rot):
  $env:PYTHONIOENCODING="utf-8"
  scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py            # allt
  scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py --larmprov # bara K7:s larmprov
  scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py --holdout  # routerns nivåval på holdouten

Skriver till ut/: resultat.json, RESULTAT.md, latens.json, k7_logg.jsonl, k7_larmprov.json, barlistor/, paket/,
blind/ (bilder i slumpad ordning) och blind_nyckel/nyckel.json (dold nyckel, separat mapp).
Inga betalda anrop: K7-vakten spärrar nät och underprocesser under hela körningen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import statistics
import sys
import textwrap
import time

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[2]
sys.path.insert(0, str(HIT))
sys.path.insert(0, str(ROT / "motpart/runda-3-opus/A-domare/matt"))
sys.path.insert(0, str(ROT / "byggsten/brygga"))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import bar  # noqa: E402
import drag  # noqa: E402
import forhand  # noqa: E402
import k7  # noqa: E402
import kallor  # noqa: E402
import router  # noqa: E402

import os  # noqa: E402

UT = pathlib.Path(os.environ.get("C_UT", str(HIT / "ut")))  # C_UT: annan utmapp (används för körningen under A:s K7-vakt)
PAKET = {
    "gelato": ROT / "forvarld_karna/ut/gelato/paket.json",
    "guacamole": ROT / "forvarld_karna/ut/guacamole/paket.json",
    "notan": ROT / "forvarld_karna/ut/notan/paket.json",
    "asketch": ROT / "forvarld_karna/ut/asketch/paket.json",
}
INGEST_UTAN_PAKET = {"btilltal": "b-tilltal-ravara-tagningar"}
B_UT = ROT / "motpart/runda-3-opus/B-nasta-klipp/ut"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ============================================================================ klipp (ingestsidan, får ta tid)

_HAND = {}


def hand_tillstand(K):
    """Ryggradens tillstånd ur byggsten/hand (bara för klipp med ryggrad i banken)."""
    if not K.ryggrad:
        return None
    if "mod" not in _HAND:
        sys.path.insert(0, str(ROT / "byggsten/hand"))
        import tillstand  # noqa: E402
        _HAND["mod"] = tillstand
    return _HAND["mod"].fran_ryggrad(K.bank_id)


def ladda(namn, paket_fil=None, ingest=None):
    t0 = time.perf_counter()
    K = kallor.Klipp(paket_fil, namn=namn, ingestnamn=ingest)
    K.namn = namn
    K.poster = bar.bygg_barlista(K)
    K.L = router.Lexikon(K)
    K.hand = hand_tillstand(K)
    K.laddning_ms = round((time.perf_counter() - t0) * 1000, 1)
    (UT / "barlistor").mkdir(parents=True, exist_ok=True)
    (UT / "barlistor" / f"{namn}.json").write_text(json.dumps(dict(klipp=K.kort(), poster=bar.som_json(K.poster)), ensure_ascii=False, indent=1), encoding="utf-8")
    return K


# ============================================================================ medielagret (spår D)

def medie_mal(K, text, lager, typ):
    n = bar.norm(text)
    tok = {s for s in bar.stammar(n) if len(s) >= 2} - bar.STOPPORD - {"text", "texten", "ta", "bort", "byt", "och", "skylten", "skylt"}
    mal = []
    if lager == "skarmtext":
        kand = [p for p in K.poster if p["typ"] in ("text",) or (p["typ"] == "liggare" and p["ref"]["medie"])]
        mal = [p for p in kand if tok & {s for s in bar.stammar(p["namn"]) if len(s) >= 2}]
        if not mal and typ == "tar_bort" and bar.re.search(r"(texterna|undertext\w*|all text)", n):
            mal = kand
    elif lager == "repliker":
        if bar.re.search(r"\bsista\b", n) and K.repliker:
            mal = [p for p in K.poster if p["id"] == f"replik:{K.repliker[-1]['id']}"]
        elif bar.re.search(r"\bförsta\b", n) and K.repliker:
            mal = [p for p in K.poster if p["id"] == f"replik:{K.repliker[0]['id']}"]
        else:
            mal = [p for p in K.poster if p["typ"] == "replik"]
    medie = sorted({m for p in mal for m in p["ref"]["medie"]})
    return medie


def medie_till_D(begaran):
    f = ROT / "motpart/runda-3-opus/D-medielager/medielager/grans_c.py"
    if f.exists():
        sys.path.insert(0, str(f.parent))
        import grans_c  # noqa: E402
        return grans_c.hantera(begaran)
    return dict(status="ej_i_detta_spar", skal="Medielagret byggs i spår D. Gränssnittet står i C-cm-mening/README.md; D har inte anslutit än.")


# ============================================================================ bevarande (A:s mått) och diagnos

def nyckla(P):
    """Listor med id blir ordböcker, så att A:s sökvägsjämförelse inte larmar på förskjutna index."""
    Q = dict(P)
    Q["objekt"] = {o["id"]: o for o in P["objekt"]}
    Q["tagningar"] = {t["id"]: {**t, "personer": {p["id"]: p for p in t["personer"]}} for t in P["tagningar"]}
    Q["rorelse"] = {pid: {s["tagning"]: s for s in sp} for pid, sp in P["rorelse"].items()}
    Q.pop("beslut", None)
    Q.pop("tidskarta", None)
    return Q


def rackvidd(op, args, K):
    a = args
    m = {
        "ta_bort_objekt": [f"objekt/{a.get('oid')}", f"objekt/{a.get('oid')}:*", "tagningar/*/personer/*/ankare", "personer/*/hemplats"],
        "byt_objekt": [f"objekt/{a.get('oid')}/*"],
        "lagg_till_objekt": [f"objekt/{a.get('pa')}:pa:*"],
        "flytta_objekt": [f"objekt/{a.get('oid')}/*"],
        "byt_foremal_i_hand": [f"objekt/{a.get('person')}:hand:*"],
        "byt_miljo": ["objekt/golv/farg", "objekt/vagg*/farg", "rum/*", "miljo", "miljo/*"],
        "flytta_interaktion": [f"rorelse/{a.get('person')}/{a.get('tid')}/*", f"tagningar/{a.get('tid')}/kamera/*", f"tagningar/{a.get('tid')}/personer/*"],
        "kamera_stabilisera": ["tagningar/*/kamera/*"] if not a.get("tagningar") else [f"tagningar/{t}/kamera/*" for t in a["tagningar"]],
        "kamera_narmare": [f"tagningar/{a.get('tid')}/kamera/*"],
        "kamera_lins": ["tagningar/*/kamera/nycklar/*/8"],
        "sta_still": [f"rorelse/{a.get('person')}/{a.get('tid')}/rutor/*"],
        "ga_med_attityd": [f"rorelse/{a.get('person')}/*", "tagningar/*/kamera/*", "tagningar/*/personer/*", f"objekt/stol_{a.get('person')}",
                           f"objekt/stol_{a.get('person')}/*", f"personer/{a.get('person')}/*", "mening/*"],
    }
    return m.get(op)


def bevarande_tidslinje(P, N):
    """För drag på tidslinjen: varje ny ruta med heltalskälla ska ha exakt originalets pose (genom tidskartan)."""
    avv, antal = 0.0, 0
    gamla = {(pid, s["tagning"]): s for pid, sp in P["rorelse"].items() for s in sp}
    for blk in N.get("tidskarta", []):
        for pid, sp in N["rorelse"].items():
            for s in sp:
                if s["tagning"] != blk["tagning"] or (pid, s["tagning"]) not in gamla:
                    continue
                Ug, Xg = drag.spar_array(gamla[(pid, s["tagning"])])
                idx = {int(u): i for i, u in enumerate(Ug)}
                for r in s["rutor"]:
                    j = r[0] - blk["ny"][0]
                    if j in set(blk.get("blandade", [])):
                        continue  # deklarerad skarv (upprepning): ny pose med avsikt, räknas inte som läckage
                    if 0 <= j < len(blk["kalla"]):
                        src = blk["kalla"][j]
                        if abs(src - round(src)) < 1e-6 and int(round(src)) in idx:
                            d = np.abs(np.array(r[1:]) - Xg[idx[int(round(src))]].reshape(-1)).max()
                            avv = max(avv, float(d))
                            antal += 1
    return dict(utfall="bevarad" if avv <= 1.0 else "lackage", max_avvikelse_mm=avv, kontrollerade_rutor=antal,
                matt="tidskartan: heltalsrutor jämförda med originalets pose (blandade/interpolerade rutor räknas inte)")


def diagnos(P, N, dd, K):
    ut = {}
    if all(drag.KATEGORI.get(d["op"]) == "tidslinje" for d in dd):
        ut["bevarande"] = bevarande_tidslinje(P, N)
    else:
        mon = []
        for d in dd:
            r = rackvidd(d["op"], d["args"], K)
            if r is None:
                mon = None
                break
            mon += r
        if mon is not None:
            import bevarande as A_bev
            res = A_bev.jamfor(A_bev.platta(nyckla(P)), A_bev.platta(nyckla(N)), mon, 0.001)
            ut["bevarande"] = dict(utfall=res["utfall"], antal_inom=res["antal_inom"], antal_utanfor=res["antal_utanfor"],
                                   utanfor_per_grupp=res["utanfor_per_grupp"], rackvidd=mon, matt="A-domare/matt/bevarande.py (jamfor), tol 0.001")
    try:
        import grindar
        fore, efter = grindar.sammanfatta(grindar.mat(P)), grindar.sammanfatta(grindar.mat(N))
        ut["grindar"] = dict(fore=fore, efter=efter, notis="byggsten/brygga/grindar.py: egna mått, diagnos")
    except Exception as e:  # B:s paket har egna grindar
        ut["grindar"] = dict(fel=f"{type(e).__name__}: {e}"[:200])
    return ut


# ============================================================================ en mening

def klass(sys_utfall):
    return {"utford": "utford", "utford_ryggrad": "utford", "stopp": "nej", "nej": "nej", "motfraga": "nej", "typbyte": "typbyte",
            "medie": "medie", "ej_korbar": "ej_korbar"}[sys_utfall]


def kor_mening(m, K, vakt, facit):
    vakt.mening_id = m["id"]
    res = dict(id=m["id"], text=m["text"], klipp=K.namn, kalla=m.get("kalla"))
    t0 = time.perf_counter()
    r = vakt.anrop("router.tolka", router.tolka, m["text"], K, K.L)
    t_route = time.perf_counter()
    res["router"] = {k: v for k, v in r.items() if k not in ("delar",)}
    if r.get("delar"):
        res["router"]["delar"] = [{k: v for k, v in d.items()} for d in r["delar"]]
    res["niva"] = r["niva"]
    effekter, plan_info, dd = [], [], []
    sys_utfall, skal = None, []
    P = K.paket
    N = None
    ryg = None

    def ryggrad(dragnamn, param=None):
        if K.hand is None:
            return dict(utfort=False, stopp="klippet har ingen ryggrad i banken (byggsten/hand)")
        n, logg = vakt.anrop(f"ryggrad.{dragnamn}", _HAND["mod"].tillampa, K.hand, dragnamn, K.ryggrad, param)
        return logg

    if r["utfall"] == "typbyte":
        sys_utfall, skal = "typbyte", [r["skal"], r.get("forslag", "")]
    elif r["utfall"] in ("nej", "motfraga"):
        sys_utfall = r["utfall"]
        skal = [r.get("skal") or r.get("fraga")]
        res["alternativ"] = r.get("alternativ")
        if r.get("skulle_gora"):
            res["skulle_gora"] = r["skulle_gora"]
    elif r["utfall"] == "medie":
        medie = medie_mal(K, m["text"], r["lager"], r["typ"])
        effekter = [dict(typ=r["typ"], mal=dict(medie=medie), beskrivning=f"{r['lager']}: {r['typ']}")] if medie else []
        v = vakt.anrop("bar.vakt", bar.vakt, K, K.poster, effekter)
        res["k5"] = v
        begaran = dict(klipp=K.namn, ingest=K.ingestnamn, mening=m["text"], lager=r["lager"], typ=r["typ"], mal=medie,
                       k5=v, tidskarta=None)
        res["medie_svar"] = vakt.anrop("medie.till_D", medie_till_D, begaran)
        sys_utfall = "stopp" if v["niva"] == "stopp" else "medie"
        skal = v["stopp"] if v["niva"] == "stopp" else [res["medie_svar"].get("skal")]
    elif r["utfall"] == "ryggrad":
        ryg = ryggrad(r["ryggrad_drag"])
        res["ryggrad"] = ryg
        if ryg.get("utfort"):
            sys_utfall = "utford_ryggrad"
            skal = ryg.get("andrat", []) + ryg.get("foljder", []) + ["syns inte i förvärlden: ändringen ligger på ryggradsnivå (byggsten/hand)"]
        else:
            sys_utfall, skal = "nej", [ryg.get("stopp")]
    elif r["utfall"] == "drag_plan":
        v = vakt.anrop("bar.vakt", bar.vakt, K, K.poster, r["effekter"])
        res["k5"] = v
        if v["niva"] == "stopp":
            sys_utfall, skal = "stopp", v["stopp"]
        elif r.get("fraga"):
            sys_utfall, skal = "motfraga", [r["fraga"]]
            res["alternativ"] = r.get("alternativ")
        else:
            sys_utfall, skal = "nej", [r.get("skal")]
    elif r["utfall"] == "drag":
        dd = r["drag"]
        if r.get("ryggrad_drag"):
            ryg = ryggrad(r["ryggrad_drag"], r.get("ryggrad_param"))
            res["ryggrad"] = ryg
        if P is None:
            sys_utfall, skal = "ej_korbar", ["klippet har ingen förvärld (paket saknas); routningen och K5 redovisas, ändringen kan inte göras"]
        elif not dd:
            sys_utfall = "utford_ryggrad" if (ryg or {}).get("utfort") else "nej"
            skal = [r.get("not_") or "inget att ändra i förvärlden"]
        else:
            try:
                for d in dd:
                    pf, _ = drag.DRAG[d["op"]]
                    pl = vakt.anrop(f"drag.plan.{d['op']}", pf, K, **d["args"])
                    plan_info.append(pl)
                    effekter += pl["effekter"]
                v = vakt.anrop("bar.vakt", bar.vakt, K, K.poster, effekter)
                res["k5"] = v
                if v["niva"] == "stopp":
                    sys_utfall, skal = "stopp", v["stopp"]
                else:
                    N = P
                    for d in dd:
                        _, gf = drag.DRAG[d["op"]]
                        N = vakt.anrop(f"drag.{d['op']}", gf, N, K, **d["args"])
                    sys_utfall = "utford"
                    skal = [e["beskrivning"] for e in effekter]
            except drag.Avslag as e:
                sys_utfall, skal = "nej", [f"Går inte: {e}"]
            except k7.K7Brott:
                raise
            except Exception as e:
                sys_utfall, skal = "nej", [f"Draget kraschade och utfördes inte: {type(e).__name__}: {e}"[:300]]
                res["krasch"] = True
                N = None
    t_klar = time.perf_counter()
    res["utfall"] = sys_utfall
    res["skal"] = [s for s in skal if s]
    res["foljder"] = [f for pl in plan_info for f in pl["foljder"]]
    res["platshallare"] = [p for pl in plan_info for p in pl["platshallare"]]
    res["drag"] = [dict(op=d["op"], args=d["args"], kategori=drag.KATEGORI.get(d["op"])) for d in dd] if sys_utfall == "utford" else []
    res["ms"] = dict(mening_till_andring=round((t_klar - t0) * 1000, 2), tolkad_till_andring=round((t_klar - t_route) * 1000, 2),
                     router=round((t_route - t0) * 1000, 2))
    if N is not None:
        t1 = time.perf_counter()
        res["diagnos"] = diagnos(P, N, dd, K)
        res["ms"]["diagnos"] = round((time.perf_counter() - t1) * 1000, 1)
        mapp = UT / "paket" / f"{m['id']}__{K.namn}"
        mapp.mkdir(parents=True, exist_ok=True)
        (mapp / "paket_efter.json").write_text(json.dumps(N, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        res["paket_efter"] = str((mapp / "paket_efter.json").relative_to(ROT))
        res["_N"] = N
        res["_visa"] = plan_info[0].get("visa") if plan_info else None
    res["bedomning"] = bedom(res, facit)
    return res


def bedom(res, f):
    if f is None:
        return dict(klass="utan_facit")
    s = klass(res["utfall"])
    godta = f["godta"]
    ut = dict(facit=godta, system=s, kraver_varning=f.get("kraver_varning", False))
    if s == "ej_korbar":
        ut["klass"] = "ej mätbar (paket saknas)"
        return ut
    varnad = (res.get("k5") or {}).get("niva") in ("varning", "stopp")
    if s == "utford":
        oper = [d["op"] for d in res["drag"]] + ([res["router"].get("ryggrad_drag")] if res["router"].get("ryggrad_drag") else [])
        strikt = (not f.get("op")) or any(f["op"] in (o or "") for o in oper)
        # Facit skrevs innan dragen hade namn. Alias (tillagda efter första körningen, redovisas i RAPPORT.md):
        alias = {"byt_foremal": ["byt_foremal_i_hand", "byt_objekt"], "kontrast": ["kontrast_upp", "kontrast_ned"]}
        op_ok = strikt or any(a in oper for a in alias.get(f.get("op"), []))
        ut["op_strikt"] = strikt
        if "utford" not in godta:
            ut["klass"] = "fel, men varnat" if varnad else "tyst fel"
        elif not op_ok:
            ut["klass"] = "tyst fel"
            ut["not"] = f"väntat drag {f['op']}, fick {oper}"
        elif f.get("kraver_varning") and not varnad:
            ut["klass"] = "tyst fel"
            ut["not"] = "det som bär rördes utan varning"
        else:
            ut["klass"] = "rätt utförd"
    elif s in ("nej", "typbyte"):
        ut["klass"] = "ärligt nej/motfråga" if ("nej" in godta or "typbyte" in godta) else "ärligt nej/motfråga (miss: facit ville " + "/".join(godta) + ")"
    elif s == "medie":
        ut["klass"] = "routad till medielagret (D)" if "medie" in godta else "ärligt nej/motfråga (felroutad till D)"
    return ut


# ============================================================================ förhandsvisning (blind)

FONT = None


def _font(n):
    return forhand._font(n)


def _vald_ruta(P, visa):
    if isinstance(visa, dict):
        if visa.get("objekt"):
            o = next((o for o in P["objekt"] if o["id"] == visa["objekt"]), None)
            if o and o["synlig_ut"]:
                for t in P["tagningar"]:
                    a, b = t["ut"]
                    if any(x < b and y > a for x, y in o["synlig_ut"]) and t["personer"]:
                        return (a + b) // 2
                return (o["synlig_ut"][0][0] + o["synlig_ut"][0][1]) // 2
        if visa.get("tagning"):
            t = next(t for t in P["tagningar"] if t["id"].lower() == visa["tagning"].lower())
            return (t["ut"][0] + t["ut"][1]) // 2
        if visa.get("rutor"):
            return (visa["rutor"][0] + visa["rutor"][1]) // 2
        if visa.get("person"):
            sp = P["rorelse"].get(visa["person"], [])
            if sp:
                return (sp[0]["ut"][0] + sp[0]["ut"][1]) // 2
    t = P["tagningar"][0]
    return (t["ut"][0] + t["ut"][1]) // 2


def bild_par(K, P, N, visa, rubrik):
    """Ger (bild_före, bild_efter, original) i samma format. Remsa för tidslinjedrag, annars en ruta."""
    if visa == "remsa":
        rf, re_ = forhand.jamnt(P, 6), forhand.jamnt(N, 6)
        a = forhand.remsa(P, rf)
        b = forhand.remsa(N, re_)
        org = Image.new("RGB", a.size)
        for i, u in enumerate(rf):
            org.paste(forhand.original_ruta(K, u, (135, 240)), (i * 135, 0))
        return a, b, org, "remsa"
    u = _vald_ruta(P, visa)
    a = forhand.rita(P, u)
    b = forhand.rita(N, u)
    return a, b, forhand.original_ruta(K, u), "ruta"


def komponera(mening, org, A, B, form):
    W = 810
    rubrik = textwrap.wrap(f"Mening: {mening}", 70)
    h0 = 22 * len(rubrik) + 14
    fr = "Vilken av A och B gör det meningen ber om? Är resten oförändrat?"
    if form == "ruta":
        img = Image.new("RGB", (W, h0 + 480 + 30), (250, 250, 250))
        for i, (bild, lab) in enumerate(((org, "Original"), (A, "A"), (B, "B"))):
            img.paste(bild, (i * 270, h0))
            ImageDraw.Draw(img).text((i * 270 + 6, h0 + 4), lab, fill=(255, 255, 0), font=_font(20))
        y = h0 + 480
    else:
        img = Image.new("RGB", (W, h0 + 3 * 262 + 30), (250, 250, 250))
        for i, (bild, lab) in enumerate(((org, "Original (före)"), (A, "A"), (B, "B"))):
            y0 = h0 + i * 262
            ImageDraw.Draw(img).text((6, y0), lab, fill=(0, 0, 0), font=_font(16))
            img.paste(bild.resize((810, 240)) if bild.size[0] != 810 else bild, (0, y0 + 20))
        y = h0 + 3 * 262
    d = ImageDraw.Draw(img)
    for i, rad in enumerate(rubrik):
        d.text((8, 6 + 22 * i), rad, fill=(0, 0, 0), font=_font(18))
    d.text((8, y + 6), fr, fill=(60, 60, 60), font=_font(15))
    return img


def skapa_blind(resultat, K_av, seed=20261119):
    (UT / "blind").mkdir(parents=True, exist_ok=True)
    (UT / "blind_nyckel").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    poster = []
    korbara = [r for r in resultat if r.get("_N") is not None]
    for r in korbara:
        K = K_av[r["klipp"]]
        t0 = time.perf_counter()
        a, b, org, form = bild_par(K, K.paket, r["_N"], r.get("_visa"), r["text"])
        r["ms"]["forhandsvisning"] = round((time.perf_counter() - t0) * 1000, 1)
        poster.append(dict(id=r["id"], klipp=r["klipp"], text=r["text"], fore=a, efter=b, org=org, form=form, typ="andring"))
    # K2:s felinjektion: två trasiga förhandsvisningar
    ruta = [p for p in poster if p["form"] == "ruta"]
    kontroller = []
    if len(ruta) >= 2:
        k1, k2 = rng.sample(ruta, 2)
        kontroller.append(dict(id=f"KONTROLL_saknas_{k1['id']}", klipp=k1["klipp"], text=k1["text"], fore=k1["fore"], efter=k1["fore"].copy(),
                               org=k1["org"], form="ruta", typ="kontroll: ändringen saknas"))
        K = K_av[k2["klipp"]]
        res2 = next(r for r in korbara if r["id"] == k2["id"] and r["klipp"] == k2["klipp"])
        N2 = drag.kopia(res2["_N"])
        andra = [o for o in N2["objekt"] if o["typ"] not in ("golv",)]
        bort = rng.choice(andra)
        N2["objekt"] = [o for o in N2["objekt"] if o is not bort]
        for t in N2["tagningar"]:
            for kk in t["kamera"]["nycklar"]:
                kk[8] = round(kk[8] * 1.15, 3)
        u = _vald_ruta(K.paket, res2.get("_visa"))
        kontroller.append(dict(id=f"KONTROLL_annat_{k2['id']}", klipp=k2["klipp"], text=k2["text"], fore=k2["fore"], efter=forhand.rita(N2, u),
                               org=k2["org"], form="ruta", typ=f"kontroll: något annat ändrat ({bort['id']} borttaget, brännvidd ×1,15)"))
        import bevarande as A_bev
        mon = rackvidd(res2["drag"][0]["op"], res2["drag"][0]["args"], K) or []
        bev = A_bev.jamfor(A_bev.platta(nyckla(K.paket)), A_bev.platta(nyckla(N2)), mon, 0.001)
        kontroller[-1]["bevarande_larmar"] = dict(utfall=bev["utfall"], antal_utanfor=bev["antal_utanfor"], grupper=bev["utanfor_per_grupp"])
    alla = poster + kontroller
    rng.shuffle(alla)
    nyckel = dict(seed=seed, regel="Bilderna i ut/blind/ har A och B i slumpad ordning. Den här filen är nyckeln; öppna den efter domen.", par=[])
    for i, p in enumerate(alla, 1):
        efter_ar_A = rng.random() < 0.5
        A, B = (p["efter"], p["fore"]) if efter_ar_A else (p["fore"], p["efter"])
        namn = f"par_{i:03d}.png"
        komponera(p["text"], p["org"], A, B, p["form"]).save(UT / "blind" / namn)
        nyckel["par"].append(dict(bild=namn, id=p["id"], klipp=p["klipp"], typ=p["typ"], efter="A" if efter_ar_A else "B",
                                  **({"bevarande_larmar": p["bevarande_larmar"]} if "bevarande_larmar" in p else {})))
    (UT / "blind_nyckel" / "nyckel.json").write_text(json.dumps(nyckel, ensure_ascii=False, indent=1), encoding="utf-8")
    (UT / "blind" / "LAS_MIG.md").write_text(
        "# Blind dom (K2-förberedelse)\n\nVarje bild visar originalets ruta och två förhandsvisningar, A och B, i slumpad ordning. "
        "En av dem är före ändringen och en efter. För varje bild:\n\n1. Vilken av A och B gör det meningen ber om? (eller: ingen)\n"
        "2. Är resten av bilden oförändrat mellan A och B?\n\nTvå bilder är avsiktligt trasiga (felinjektion): i en saknas ändringen, i en har något annat ändrats. "
        "Nyckeln ligger i `../blind_nyckel/nyckel.json`. Öppna den efter domen.\n\nFörhandsvisningen är en kontrollbild med lådor och streckfigurer genom paketets kamera, "
        "inte en rendering av slutlooken.\n", encoding="utf-8")
    return nyckel


# ============================================================================ körningen

def las_meningar():
    fr = json.loads((HIT / "meningar/frysta.json").read_text(encoding="utf-8"))
    F = json.loads((HIT / "facit/facit_forslag.json").read_text(encoding="utf-8"))["facit"]
    byg = json.loads((HIT / "meningar/byggaren.json").read_text(encoding="utf-8"))
    return fr["meningar"], F, byg["meningar"]


def kontrollera_frysning():
    man = json.loads((HIT / "meningar/manifest.json").read_text(encoding="utf-8"))
    ok = dict(frysta=sha(HIT / man["frysta"]["fil"]) == man["frysta"]["sha256"],
              facit=sha(HIT / man["facit"]["fil"]) == man["facit"]["sha256"],
              byggaren=sha(HIT / man["byggaren"]["fil"]) == man["byggaren"]["sha256"])
    return ok


def percentil(x, p):
    x = sorted(x)
    if not x:
        return None
    k = (len(x) - 1) * p
    f = int(k)
    c = min(f + 1, len(x) - 1)
    return round(x[f] + (x[c] - x[f]) * (k - f), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--larmprov", action="store_true")
    ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--utan-bilder", action="store_true")
    a = ap.parse_args()
    UT.mkdir(parents=True, exist_ok=True)
    if a.larmprov:
        res = k7.larmprov(UT / "k7_larmprov_logg.jsonl")
        (UT / "k7_larmprov.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    if a.holdout:
        return kor_holdout()
    frys = kontrollera_frysning()
    print("frysning:", frys)
    meningar, F, byg = las_meningar()
    logg = UT / "k7_logg.jsonl"
    if logg.exists():
        logg.unlink()
    K_av = {}
    laddning = {}
    for namn, f in PAKET.items():
        K_av[namn] = ladda(namn, f)
        laddning[namn] = K_av[namn].laddning_ms
    for namn, ing in INGEST_UTAN_PAKET.items():
        K_av[namn] = ladda(namn, None, ing)
        laddning[namn] = K_av[namn].laddning_ms
    # spår B:s paket, när de finns
    b_klipp = {}
    if B_UT.exists():
        for p in sorted(B_UT.glob("*/paket.json")):
            ing = p.parent.name
            for namn, f in PAKET.items():
                kk = K_av[namn]
                if kk.ingestnamn == ing:
                    bnamn = f"{namn}(B)"
                    K_av[bnamn] = ladda(bnamn, p, ing)
                    laddning[bnamn] = K_av[bnamn].laddning_ms
                    b_klipp[namn] = bnamn
    resultat = []
    with k7.Vakt(logg) as vakt:
        for m in meningar:
            K = K_av[m["paket"]]
            resultat.append(kor_mening(m, K, vakt, F.get(m["id"])))
            if m["paket"] in b_klipp:
                resultat.append(kor_mening(dict(m, id=m["id"] + "@B"), K_av[b_klipp[m["paket"]]], vakt, F.get(m["id"])))
        for m in byg:
            K = K_av[m["paket"]]
            fa = dict(godta=m["godta"], op=m.get("op"), kraver_varning=m.get("kraver_varning", False))
            r = kor_mening(dict(m, kalla="byggaren"), K, vakt, fa)
            r["skriven_av_byggaren"] = True
            resultat.append(r)
            if m["paket"] in b_klipp:
                r = kor_mening(dict(m, id=m["id"] + "@B", kalla="byggaren"), K_av[b_klipp[m["paket"]]], vakt, fa)
                r["skriven_av_byggaren"] = True
                resultat.append(r)
        k7_sammanfattning = dict(brott=vakt.brott, natanslutningar=vakt.natanslutningar, underprocesser=vakt.underprocesser, anrop=len(vakt.rader))
    # felinjektion: tidslinjens bevarandemått ska larma när en pose ändras utanför skarven
    prov = {}
    for r in resultat:
        if r.get("_N") is not None and r["drag"] and r["drag"][0]["kategori"] == "tidslinje":
            N2 = drag.kopia(r["_N"])
            pid = next(iter(N2["rorelse"]))
            sp = N2["rorelse"][pid][0]
            rut = [list(x) for x in sp["rutor"]]
            rut[len(rut) // 2][1] += 50  # 5 cm på en led i en ruta
            sp["rutor"] = rut
            K = K_av[r["klipp"]]
            prov = dict(drag=r["id"], utan_fel=bevarande_tidslinje(K.paket, r["_N"]), med_fel=bevarande_tidslinje(K.paket, N2),
                        injektion=f"{pid}, första spåret, mittrutan, första koordinaten +50 mm")
            break
    (UT / "bevarande_prov.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    nyckel = None
    if not a.utan_bilder:
        nyckel = skapa_blind(resultat, K_av)
    for r in resultat:
        r.pop("_N", None)
        r.pop("_visa", None)
    (UT / "resultat.json").write_text(json.dumps(dict(frysning=frys, laddning_ms=laddning, k7=k7_sammanfattning, resultat=resultat),
                                                  ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sammanstall(resultat, laddning, k7_sammanfattning, nyckel)


def sammanstall(resultat, laddning, k7s, nyckel):
    lat = {}
    for r in resultat:
        if r["utfall"] == "ej_korbar":
            continue
        niva = r["niva"].split("+")[0].split(".")[0] if not r["niva"].startswith("scen") else r["niva"].split("+")[0]
        lat.setdefault(niva, dict(mening=[], tolkad=[], forhand=[]))
        lat[niva]["mening"].append(r["ms"]["mening_till_andring"])
        lat[niva]["tolkad"].append(r["ms"]["tolkad_till_andring"])
        if "forhandsvisning" in r["ms"]:
            lat[niva]["forhand"].append(r["ms"]["forhandsvisning"])
    latens = {n: dict(antal=len(v["mening"]), median_mening_ms=percentil(v["mening"], 0.5), p90_mening_ms=percentil(v["mening"], 0.9),
                      median_tolkad_ms=percentil(v["tolkad"], 0.5), p90_tolkad_ms=percentil(v["tolkad"], 0.9),
                      median_forhand_ms=percentil(v["forhand"], 0.5), p90_forhand_ms=percentil(v["forhand"], 0.9)) for n, v in lat.items()}
    alla = [r["ms"]["mening_till_andring"] for r in resultat if r["utfall"] != "ej_korbar"]
    latens["alla"] = dict(antal=len(alla), median_mening_ms=percentil(alla, 0.5), p90_mening_ms=percentil(alla, 0.9), max_ms=max(alla))
    latens["laddning_per_klipp_ms"] = laddning
    (UT / "latens.json").write_text(json.dumps(latens, ensure_ascii=False, indent=1), encoding="utf-8")
    rader = ["# Resultat, spår C (genererad av kor.py)", "", f"K7: {k7s}", "",
             "| id | klipp | mening | nivå | utfall | K5 | bedömning | ms |", "|---|---|---|---|---|---|---|---|"]
    for r in resultat:
        k5 = (r.get("k5") or {}).get("niva", "–")
        rader.append(f"| {r['id']} | {r['klipp']} | {r['text'][:60]} | {r['niva']} | {r['utfall']} | {k5} | {r['bedomning'].get('klass')} | {r['ms']['mening_till_andring']} |")
    (UT / "RESULTAT.md").write_text("\n".join(rader) + "\n", encoding="utf-8")
    print("\n".join(rader[:4]))
    print(json.dumps(latens, ensure_ascii=False, indent=1))


# ============================================================================ holdout: routerns nivåval

def kor_holdout():
    man = json.loads((HIT / "holdout/manifest.json").read_text(encoding="utf-8"))
    f = ROT / man["fil"]
    assert sha(f) == man["sha256"], "holdouten har ändrats sedan den hashades"
    rh = sha(HIT / "router.py")
    if "router_sha256" not in man:
        man["router_sha256"] = rh
        man["router_frusen"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        (HIT / "holdout/manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    assert man["router_sha256"] == rh, "routern har ändrats efter frysningen"
    mapp = json.loads((HIT / "holdout/mappning.json").read_text(encoding="utf-8"))["mappning"]
    d = json.loads(f.read_text(encoding="utf-8"))
    K = kallor.Klipp(None, namn=d.get("klipp"), ingestnamn="__saknas__")
    K.poster = []
    L = router.Lexikon(K)
    import fnmatch
    ut, ratt = [], 0
    for m in d["meningar"]:
        text = m.get("text") or m.get("mening")
        facit = m.get("facit") or []
        facit = facit if isinstance(facit, list) else [facit]
        ok_niv = set()
        for fd in facit:
            for k, v in mapp.items():
                if fnmatch.fnmatchcase(fd, k):
                    ok_niv |= set(v)
        t0 = time.perf_counter()
        r = router.tolka(text, K, L)
        ms = (time.perf_counter() - t0) * 1000
        niv = r["niva"].split("+")[0]
        if r["utfall"] == "typbyte":
            niv = "typbyte"
        if r["utfall"] == "medie":
            niv = "medie"
        traff = niv in ok_niv
        ratt += traff
        ut.append(dict(id=m.get("id"), text=text, facit_drag=facit, godtagna_nivaer=sorted(ok_niv), router_niva=niv, router_utfall=r["utfall"],
                       regel=r["regel"], ratt=traff, ms=round(ms, 2)))
    res = dict(router_sha256=rh, antal=len(ut), ratt_niva=ratt, andel=round(ratt / max(1, len(ut)), 3), meningar=ut)
    (UT / "holdout_resultat.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "meningar"}, ensure_ascii=False))
    for x in ut:
        print(("OK " if x["ratt"] else "-- ") + f"{x['id']}: {x['text'][:60]} | facit {x['facit_drag']} -> {x['router_niva']} ({x['router_utfall']}, {x['regel']})")


if __name__ == "__main__":
    main()
