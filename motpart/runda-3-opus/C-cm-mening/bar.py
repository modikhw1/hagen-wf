"""Liggaren och relevansen (K5): vad bär klippet, och vad händer med det om en ändring görs.

bygg_barlista(K) slår ihop de källor som finns för klippet till en lista av poster:
  relevans   Geminis läsning (bar / ramar / brus), cachad vid ingest
  liggare    mening.bar / mening.ramar / mening.tillfalligt (stark modell vid ingest)
  ryggrad    takter märkta 'ryggrad' i formatkortet (byggsten/hand)
  källa      scenfunktion (punchline, vändning) och vem som talar (härledd, svagast)
  paket      det som finns i förvärlden men inte nämns: roll 'okand'
Varje post bär sina källor och en referens in i paketet (personer, objekt, tagningar, rutor, medie-id).

vakt(K, poster, effekter) prövar en planerad ändring mot listan:
  ta bort något som bär            -> STOPP med motfråga ("Meningen bärs av …")
  byta eller flytta något som bär  -> VARNING (ändringen görs, varningen visas)
  ta bort något som ramar          -> VARNING
  bryta en förutsättning i liggaren för en händelse som bär (STRIPS-kedja) -> STOPP
Ingen ändring passerar tyst förbi en post som bär: antingen står den i varningen eller så stoppas den.
"""
from __future__ import annotations

import re
import unicodedata

BORD_ORD = ("disk", "bord", "bänk", "counter", "monter")
STOL_ORD = ("stol", "pall", "barstol", "säte")
DORR_ORD = ("dörr", "entré", "ingång")
STOPPORD = {"att", "och", "den", "det", "med", "som", "för", "från", "till", "över", "under", "inte", "ett", "en"}
BAKGRUND_ORD = ("bakgrund", "miljö", "butik", "lokal", "rum", "vägg", "inredning", "slaktar", "restaurang", "bar")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    return re.sub(r"[^\wåäöæøü ]+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in re.split(r"[\s_\-:/]+", norm(s).replace("_", " ")) if t]


def stam(t: str) -> str:
    """Grov svensk stam: tar bort bestämd form och plural (disken -> disk, burken -> burk, muggarna -> mugg)."""
    for suf in ("arna", "erna", "orna", "arne", "en", "et", "na", "ar", "er", "or", "n", "t"):
        if len(t) > len(suf) + 2 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def fold(s: str) -> str:
    """å/ä -> a, ö -> o, æ -> a, ø -> o: liggarens ramnamn är skrivna utan diakritiska tecken."""
    return s.translate(str.maketrans("åäöæøü", "aaoaou"))


def stammar(s: str) -> set[str]:
    return {stam(t) for t in tokens(s)} | set(tokens(s))


def ord_traff(namn: str, ordlista) -> bool:
    n = norm(namn)
    return any(o in n for o in ordlista)


def _overlapp(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


# ---------------------------------------------------------------------------------------------- bärlistan

def _ny_post(pid, namn, typ, roll, kalla, varfor=None, **ref):
    return dict(id=pid, namn=namn, typ=typ, roll=roll, kallor=[kalla], varfor=varfor,
                ref=dict(personer=set(ref.get("personer", ())), objekt=set(ref.get("objekt", ())),
                         tagningar=set(ref.get("tagningar", ())), rutor=list(ref.get("rutor", ())),
                         medie=set(ref.get("medie", ())), handelser=set(ref.get("handelser", ())),
                         entiteter=set(ref.get("entiteter", ())), utanfor_paket=ref.get("utanfor_paket", False)))


def objekt_for_namn(K, namn: str, typ_hint: str | None = None, tagningar=None) -> list[str]:
    """Allmän koppling från ett namn ('Glassdisk', 'gul Bonaqua-burk') till paketets objekt-id."""
    P = K.paket
    if not P:
        return []
    objs = P["objekt"]
    nycklar = K.foremals_nycklar()
    st = stammar(namn)
    kand = []
    if ord_traff(namn, BORD_ORD) or typ_hint == "bord":
        kand = [o["id"] for o in objs if o["typ"] == "bord"]
    elif ord_traff(namn, STOL_ORD) or typ_hint == "stol":
        kand = [o["id"] for o in objs if o["typ"] == "stol"]
        # stol_A <-> 'stol A', 'barstol_A'
        for o in kand[:]:
            agare = o.split("_", 1)[-1].lower()
            if agare and (agare in tokens(namn)):
                kand = [o]
                break
    elif ord_traff(namn, DORR_ORD):
        kand = [o["id"] for o in objs if o["typ"] == "dorr"]
    else:
        for o in objs:
            nyc = nycklar.get(o["id"]) or o.get("etikett") or ""
            if o["typ"] in ("golv", "vagg"):
                continue
            nst = stammar(nyc.replace("foremal:", ""))
            if st & nst and len(max(st & nst, key=len)) >= 3:
                kand.append(o["id"])
    if len(kand) > 1 and tagningar:
        tut = [t["ut"] for t in P["tagningar"] if t["id"].lower() in {x.lower() for x in tagningar}]
        filt = [oid for oid in kand if any(_overlapp(iv, u) > 0 for o in objs if o["id"] == oid for iv in o["synlig_ut"] for u in tut)]
        kand = filt or kand
    return kand


def _person_ref(K, post) -> list[str]:
    pers = K.personer()
    ref = post.get("ref") or post.get("id")
    for kand in (ref, post.get("id"), (post.get("id") or "")[-1:].upper()):
        if kand in pers:
            return [kand]
    return []


def _handelse_index(K):
    lg = K.liggare or {}
    return {e["id"]: e for e in lg.get("handelser", [])}, {e["id"]: e for e in lg.get("entiteter", [])}, {f["id"]: f for f in lg.get("forlopp", [])}


def _liggare_ref(K, text: str):
    """Översätter en rad ur liggarens mening ('e6.sak=glass_prov', 'f_servera före f_egen', 'st1', 'disken') till referenser."""
    H, E, F = _handelse_index(K)
    ref = dict(personer=set(), objekt=set(), tagningar=set(), rutor=[], medie=set(), handelser=set(), entiteter=set())
    ord_ = re.findall(r"[A-Za-zÅÄÖåäöæøÆØ_0-9]+", text)
    for w in ord_:
        if w in H:
            e = H[w]
            ref["handelser"].add(w)
            if e.get("rutor"):
                ref["rutor"].append(tuple(e["rutor"]))
            for roll, v in (e.get("roller") or {}).items():
                if v in K.personer():
                    ref["personer"].add(v)
        if w in F:
            ref["rutor"].append(tuple(F[w]["rutor"]))
            ref["handelser"].update(F[w].get("handelser", []))
        if w in E:
            ent = E[w]
            ref["entiteter"].add(w)
            if ent["typ"] == "person" and w in K.personer():
                ref["personer"].add(w)
            elif ent["typ"] == "text":
                ref["medie"].add(w)
            elif ent["typ"] in ("mobel", "foremal", "plats"):
                ref["objekt"].update(objekt_for_namn(K, ent.get("namn") or w))
    if not any(ref.values()):
        # fri text: 'disken', 'bakgrunden', 'slaktarbutiken'
        if ord_traff(text, BORD_ORD):
            ref["objekt"].update(objekt_for_namn(K, text, "bord"))
        elif ord_traff(text, BAKGRUND_ORD):
            ref["objekt"].add("rum")
    return ref


def bygg_barlista(K) -> list[dict]:
    poster: dict[str, dict] = {}

    def lagg(p):
        nyckel = p["id"]
        if nyckel in poster:
            gammal = poster[nyckel]
            gammal["kallor"] += p["kallor"]
            rang = {"bar": 3, "ramar": 2, "tillfalligt": 1, "brus": 0, "okand": -1}
            if rang.get(p["roll"], -1) > rang.get(gammal["roll"], -1):
                gammal["roll"] = p["roll"]
            for k, v in p["ref"].items():
                if isinstance(v, set):
                    gammal["ref"][k] |= v
                elif isinstance(v, list):
                    gammal["ref"][k] += v
        else:
            poster[nyckel] = p

    # 1. relevans (alla körningar räknas för stabilitet; den valda styr rollen)
    rel = K.relevans or {}
    alla_korningar = [d for _, d in K.relevans_korningar]
    for post in rel.get("poster", []):
        typ = post.get("typ")
        tagn = [t.lower() for t in post.get("tagningar", [])]
        ref = dict(tagningar=tagn)
        if typ == "person":
            ref["personer"] = _person_ref(K, post)
        elif typ in ("mobel", "foremal"):
            ref["objekt"] = objekt_for_namn(K, post.get("namn") or post["id"], tagningar=tagn)
            if not ref["objekt"]:
                ref["utanfor_paket"] = True
        elif typ in ("foremal_i_hand", "kroppsdel"):
            ref["utanfor_paket"] = True
            ref["personer"] = [p for p in K.personer() if p.lower() in [x.lower() for x in post.get("samspel", [])]]
        elif typ == "text":
            ref["medie"] = [post["id"]]
        elif typ == "bakgrund":
            ref["objekt"] = ["rum"]
        elif typ == "kamera":
            ref["objekt"] = ["kamera"]
        elif typ == "handling":
            ref["personer"] = [post["vem"]] if post.get("vem") in K.personer() else []
        roll = {"bar": "bar", "ramar": "ramar", "brus": "brus"}.get(post.get("roll"), "okand")
        stab = [next((q.get("roll") for q in d.get("poster", []) if norm(q.get("namn", "")) == norm(post.get("namn", ""))), None) for d in alla_korningar]
        p = _ny_post(f"rel:{post['id']}", post.get("namn") or post["id"], typ, roll,
                     f"relevans ({rel.get('modell', '?')}), roll i {len(alla_korningar)} körningar: {stab}", post.get("varfor"), **ref)
        lagg(p)

    # 2. liggaren
    lg = K.liggare or {}
    men = lg.get("mening") or {}
    for roll, rader in (("bar", men.get("bar", [])), ("ramar", men.get("ramar", [])), ("tillfalligt", men.get("tillfalligt", []))):
        for rad in rader:
            ref = _liggare_ref(K, rad)
            p = _ny_post(f"lig:{rad}", rad, "liggare", roll, "liggare (stark modell vid ingest)", men.get("poang"), **ref)
            lagg(p)

    # 3. ryggraden: takter som är ryggrad (ingen tid i formatkortet: kopplas till liggarens händelser via verbet)
    ryg = K.ryggrad or {}
    H, _, _ = _handelse_index(K)
    takter = ryg.get("takter", [])
    N = (K.paket or {}).get("tidsbas", {}).get("antal_rutor") or max([e["rutor"][1] for e in H.values()] or [1])
    tilldelning = {}
    for hid, e in H.items():
        delar = [fold(stam(x)) for x in tokens(e.get("ram", "")) if len(x) >= 3]
        delar = [d[:-1] if d[-1] in "aeiouy" and len(d) >= 3 else d for d in delar]   # äta/äter, skopa/skopar
        traff = [i for i, t in enumerate(takter)
                 if any(fold(w).startswith(d) for d in delar for w in tokens(t["vad"]) if len(w) >= 3 and w not in STOPPORD)]
        if traff:
            mitt = (e["rutor"][0] + e["rutor"][1]) / 2 / N
            tilldelning[hid] = min(traff, key=lambda i: abs((i + 0.5) / len(takter) - mitt))
    for i, t in enumerate(takter):
        if t.get("bar") != "ryggrad":
            continue
        hand = {h for h, j in tilldelning.items() if j == i}
        rutor = [tuple(H[h]["rutor"]) for h in hand]
        p = _ny_post(f"ryg:takt{t['nr']}", f"takt {t['nr']}: {t['vad']}", "takt", "bar",
                     "ryggrad (formatkortet, byggsten/hand)", "ryggradstakt: utan den är det ett annat klipp", rutor=rutor, handelser=hand)
        lagg(p)
    for pl in ryg.get("platser", []):
        lagg(_ny_post(f"ryg:plats:{pl['plats']}", f"{pl['plats']} = {pl['har']}", "plats_i_mallen", "tillfalligt",
                      "ryggrad (mallens plats: byts mot kundens)", "platser i mallen är det som byts", utanfor_paket=True))

    # 4. källan: scenfunktion och talare (svagast, härledd)
    for sc in K.kalla_scener:
        if sc.get("funktion") in ("punchline", "vandning"):
            lagg(_ny_post(f"scen:{sc['id']}", f"{sc['id']} ({sc['funktion']})", "scen", "bar",
                          "källans scenfunktion (modelläsning, antagen)", sc.get("syfte") or f"scenen är klippets {sc['funktion']}",
                          tagningar=[sc["id"]], personer=[p for p in sc.get("personer", []) if p in K.personer()]))
    if not K.relevans and not K.liggare:
        talare = {r.get("talare") for r in K.repliker}
        for pid in K.personer():
            if pid in talare:
                lagg(_ny_post(f"talare:{pid}", f"{pid} (talar i repliker)", "person", "bar",
                              "härledd: personen bär dialogen (ingen relevansläsning finns)", "talar", personer=[pid]))
    # repliker knutna till tagningar: en tagning som tas bort tar med sig sina repliker (medielagret)
    for r in K.repliker:
        lagg(_ny_post(f"replik:{r['id']}", f"replik {r['id']} ({r.get('talare')}): {r.get('text', '')[:40]}", "replik", "ramar",
                      "källans repliker (ljud och text hör till medielagret)", "det som sägs", tagningar=[r.get("scen")], medie=[r["id"]]))

    # 5. paketet: det som finns men inte nämns
    if K.paket:
        tackta_p = set().union(*(p["ref"]["personer"] for p in poster.values())) if poster else set()
        tackta_o = set().union(*(p["ref"]["objekt"] for p in poster.values())) if poster else set()
        for pid in K.personer():
            if pid not in tackta_p:
                lagg(_ny_post(f"paket:{pid}", f"person {pid}", "person", "okand", "paketet (ingen läsning av vad personen betyder)", None, personer=[pid]))
        for o in K.paket["objekt"]:
            if o["typ"] in ("golv", "vagg") or o["id"] in tackta_o:
                continue
            nyc = K.foremals_nycklar().get(o["id"])
            lagg(_ny_post(f"paket:{o['id']}", f"{o['id']} ({nyc or o['typ']})", o["typ"], "okand", "paketet (ingen läsning av vad föremålet betyder)", None, objekt=[o["id"]]))
    return list(poster.values())


def som_json(poster):
    ut = []
    for p in poster:
        q = dict(p)
        q["ref"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in p["ref"].items()}
        ut.append(q)
    return ut


# ---------------------------------------------------------------------------------------------- vakten

def _traffar(post, eff, K):
    """Rör effekten posten? Ger (berörd: bool, helt_borta: bool)."""
    r = post["ref"]
    typ, mal = eff["typ"], eff.get("mal") or {}
    if mal.get("namn"):
        st = {s for nm in mal["namn"] for s in stammar(nm) if len(s) >= 3} - STOPPORD - {"text", "texten"}
        pst = {s for s in stammar(post["namn"]) if len(s) >= 3} - STOPPORD
        if st & pst or any(a.endswith(b) or b.endswith(a) for a in st for b in pst if min(len(a), len(b)) >= 4):
            return True, typ == "tar_bort"
    if mal.get("objekt") and (r["objekt"] & set(mal["objekt"])):
        return True, typ == "tar_bort"
    if mal.get("personer") and (r["personer"] & set(mal["personer"])) and typ in ("tar_bort", "andrar_rorelse"):
        if typ == "tar_bort":
            return True, True
        # rörelse: berör bara om rutorna överlappar postens rutor (eller posten saknar rutor)
        if r["rutor"] and mal.get("rutor"):
            return any(_overlapp(a, b) > 0 for a in r["rutor"] for b in mal["rutor"]), False
        return post["typ"] in ("person", "handling"), False
    if mal.get("medie") and (r["medie"] & set(mal["medie"])):
        return True, typ == "tar_bort"
    if mal.get("tagningar"):
        mt = {t.lower() for t in mal["tagningar"]}
        if r["tagningar"] and r["tagningar"] <= mt and typ == "tar_bort":
            return True, True
        if r["tagningar"] & mt and typ == "tar_bort" and post["typ"] in ("scen", "replik"):
            return True, True
        if r["tagningar"] & mt and typ in ("tar_bort", "flyttar_ordning"):
            return True, False
    if mal.get("rutor") and r["rutor"]:
        if any(_overlapp(a, b) > 0 for a in r["rutor"] for b in mal["rutor"]):
            if typ == "tar_bort":
                # helt borta om hela postens intervall ryms i det borttagna
                helt = all(any(b[0] <= a[0] and a[1] <= b[1] for b in mal["rutor"]) for a in r["rutor"])
                return True, helt
            return True, False
    if mal.get("handelser") and (r["handelser"] & set(mal["handelser"])):
        return True, typ == "tar_bort"
    return False, False


def _strips(K, borttagna: set[str]) -> list[str]:
    """Om en händelse tas bort: vilka senare händelser förlorar en förutsättning som bara den gav?"""
    lg = K.liggare or {}
    H = lg.get("handelser", [])
    fakta = set(lg.get("starttillstand", []))
    brott = []
    for e in H:
        if e["id"] in borttagna:
            continue
        for f in e.get("forvillkor", []):
            if f not in fakta:
                givare = [x["id"] for x in H if f in (x.get("effekt") or {}).get("lagg_till", [])]
                if givare and all(g in borttagna for g in givare):
                    brott.append(f"{e['id']} ({e['ram']}) kräver {f}, som bara {', '.join(givare)} ger")
        eff = e.get("effekt") or {}
        fakta |= set(eff.get("lagg_till", []))
        fakta -= set(eff.get("ta_bort", []))
    return brott


def vakt(K, poster, effekter) -> dict:
    """effekter: [{typ: tar_bort|byter|flyttar|andrar_tid|andrar_rorelse|flyttar_ordning|lagger_till, mal: {...}, beskrivning}]"""
    stopp, varning, info = [], [], []
    borttagna_h = set()
    for eff in effekter:
        for p in poster:
            berord, helt = _traffar(p, eff, K)
            if not berord:
                continue
            rad = f"{p['namn']} [{p['roll']}; {p['kallor'][0]}]" + (f": {p['varfor']}" if p.get("varfor") else "")
            if p["roll"] == "bar":
                if eff["typ"] == "flyttar_ordning" and p["typ"] == "liggare" and re.search(r"\b(före|sist|först|ordning)\b", p["namn"]):
                    stopp.append("Ordningen bär meningen: " + rad)
                elif eff["typ"] == "tar_bort" and helt:
                    stopp.append("Meningen bärs av " + rad)
                    borttagna_h |= p["ref"]["handelser"]
                else:
                    varning.append(f"Ändringen ({eff['typ']}) rör något som bär: " + rad)
            elif p["roll"] == "ramar":
                if eff["typ"] == "tar_bort":
                    varning.append("Det som ramar meningen försvinner: " + rad)
                else:
                    info.append(f"{eff['typ']} rör det som ramar: " + rad)
            elif p["roll"] == "tillfalligt":
                info.append("Tillfälligt enligt källan (får ändras): " + rad)
            elif p["roll"] == "okand":
                info.append("Okänd betydelse (ingen läsning): " + rad)
        if eff["typ"] == "tar_bort":
            borttagna_h |= set((eff.get("mal") or {}).get("handelser", []))
    if borttagna_h and K.liggare:
        for b in _strips(K, borttagna_h):
            bar_h = {h for p in poster if p["roll"] == "bar" for h in p["ref"]["handelser"]}
            hid = b.split(" ")[0]
            (stopp if hid in bar_h else varning).append("Liggarens kedja bryts: " + b)
    stopp, varning, info = (list(dict.fromkeys(x)) for x in (stopp, varning, info))
    niva = "stopp" if stopp else ("varning" if varning else "fri")
    return dict(niva=niva, stopp=stopp, varning=varning, info=info)
