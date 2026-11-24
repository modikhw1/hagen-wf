"""Router: en CM-mening till rätt nivå, och där det går till ett lagligt drag. Deterministisk, ingen modell.

Nivåer, prövade i den här ordningen:
  typbyte        "gör om det till en sketch där …": stoppas (ryggradens del 1: typen ärvs)
  medie          skärmtext, ljud, repliker, B-roll, montage, manus/utseende: till spår D ("ej i detta spår")
  ryggrad        struktur: tagningar bort, ordning, längd, kontrast (tidslinjen i paketet; byggsten/hand för takter)
  scen.handling  en handling inne i en tagning: hoppa över, tempo, upprepa (liggarens händelser ger rutorna)
  scen.kamera    stabilisera, närmare, tätare, vidare
  scen.plats     byt miljö (platshållare), flytta en interaktion till en annan möbel
  scen.foremal   ta bort, byta, lägga till, flytta rekvisita; byta produkten i handen
  scen.kropp     stå kvar (låst förflyttning), gå i stället för att sitta (Argons syntes, platshållare);
                 hand, hållning och känsla: ärligt nej (kräver kroppsvägen)
  oklar          motfråga med alternativ
Utfall: drag (ett eller flera), nej (med skäl), motfraga (med alternativ), typbyte, medie.

Ordlistor för personer och föremål byggs per klipp ur källorna (liggare, relevans, källans roller, receptets
nycklar, ryggradens platser). Allmänna svenska ord för roller, möbler och miljöer står här. Inget klippnamn.

Var en språkmodell skulle behövas: när ingen regel träffar (utfallet "motfraga" med regel 'ingen_regel'),
vid omskrivningar som reglerna inte känner, och för att knyta pronomen när flera personer passar.
Se README.md (avsnittet Router) för kostnad.
"""
from __future__ import annotations

import re

from bar import norm, stam, tokens, fold

TAL = {"en": 1, "ett": 1, "två": 2, "tre": 3, "fyra": 4, "fem": 5, "sex": 6, "sju": 7, "åtta": 8, "nio": 9, "tio": 10, "halv": 0.5, "dubbelt": 2}
ORDNING = {"första": 0, "andra": 1, "tredje": 2, "fjärde": 3, "femte": 4, "sjätte": 5, "sjunde": 6, "åttonde": 7, "sista": -1}

GENRE = ["sketch", "tilltal", "talking head", "provsmakning", "tutorial", "recept", "intervju", "utmaning", "monolog", "vlogg",
         "reklam", "matlagning", "tillagning", "unboxing", "mukbang", "dans", "meme", "challenge", "pratar in i kameran", "pratar till kameran"]

ROLLORD = {
    "personal": ["servitör", "servitris", "personal", "expedit", "bartender", "anställd", "kypare", "barista", "kock", "kassör", "server", "waiter", "staff", "säljare"],
    "kund": ["kund", "gäst", "besökare", "customer", "guest"],
    "kvinna": ["kvinna", "tjej", "dam", "flicka", "woman", "hon", "henne"],
    "man": ["man", "kille", "herre", "pojke", "han", "honom"],
}
PRONOMEN = {"hon": "kvinna", "henne": "kvinna", "han": "man", "honom": "man"}

MILJO = ["glassbar", "foodtruck", "food truck", "uteservering", "terrass", "bar", "kök", "restaurang", "café", "kafé", "pizzeria",
         "park", "gata", "butik", "bageri", "matsal", "strand", "kontor", "pub", "hamburgerbar", "kiosk", "food court", "marknad", "lokal"]

VERB_RAM = {  # CM:s verb -> liggarens ram (allmänt)
    "skopa": ["skopa"], "skopar": ["skopa"], "skopandet": ["skopa"], "skopande": ["skopa"],
    "räcka": ["rakna_fram", "racka_fram", "ge"], "räcker": ["rakna_fram", "racka_fram", "ge"], "ge": ["ge"], "ger": ["ge"], "servera": ["ge"],
    "svara": ["tala"], "svarar": ["tala"], "säga": ["tala"], "säger": ["tala"], "fråga": ["tala"], "frågar": ["tala"], "prata": ["tala"], "pratar": ["tala"],
    "luta": ["luta_sig"], "lutar": ["luta_sig"], "äta": ["ata"], "äter": ["ata"], "väga": ["vaga"], "väger": ["vaga"], "vägningen": ["vaga"],
    "gissa": ["gissa"], "gissar": ["gissa"], "gissningen": ["gissa"], "lyfta": ["lyfta"], "lyfter": ["lyfta"], "hålla": ["halla"], "håller": ["halla"],
    "titta": ["titta"], "tittar": ["titta"], "reagera": ["reagera"], "reagerar": ["reagera"],
}

KANSLA = ["le", "ler", "leende", "leer", "glad", "gladare", "ledsen", "arg", "argare", "förvånad", "uttråkad", "blyg", "stolt", "nervös", "stressad",
          "upprörd", "sur", "förvirrad", "trött", "generad", "skäms", "skamsen", "förälskad", "nöjd", "irriterad", "rädd", "lycklig", "allvarlig", "allvarligare"]
POSE = ["armarna i kors", "armar i kors", "korsade armar", "händerna i fickorna", "rak i ryggen", "titta ner", "tittar ner", "titta upp", "titta på",
        "tittar på", "halta", "haltar", "vifta", "viftar", "peka", "pekar", "luta sig", "sätta sig", "sätt dig", "ställa sig", "nicka", "nickar",
        "skaka på huvudet", "blicken", "dansa", "hoppa upp", "springa", "springer", "lägga ifrån sig", "lägger ifrån sig", "ta emot"]
VAGT = ["roligare", "bättre", "snyggare", "proffsigare", "känns inte", "mer som", "mer vår", "mer energi", "mer liv", "tråkig", "fräschare", "coolare"]


def _har(n, ordlista):
    return next((o for o in ordlista if re.search(rf"(?<![\wåäö]){re.escape(o)}(?![\wåäö])", n)), None)


# ============================================================================ ordlistor per klipp

class Lexikon:
    def __init__(self, K):
        self.K = K
        P = K.paket or {}
        self.pers = {}  # pid -> {roller:set, namn:set}
        pids = list((P.get("personer") or {}).keys()) or [p.get("id") for p in K.kalla_personer if p.get("id")]
        for pid in pids:
            self.pers[pid] = dict(roller=set(), namn=set())
        for kp in K.kalla_personer:
            pid = kp.get("id")
            if pid in self.pers:
                self._roll(pid, kp.get("roll") or "")
        for e in (K.liggare or {}).get("entiteter", []):
            if e["typ"] == "person" and e["id"] in self.pers:
                self._roll(e["id"], e.get("namn") or "")
                forsta = re.split(r"[ (]", (e.get("namn") or "").strip())[0]
                if forsta and forsta[0].isupper():
                    self.pers[e["id"]]["namn"].add(norm(forsta))
        for post in (K.relevans or {}).get("poster", []):
            if post.get("typ") == "person":
                ref = post.get("ref") or post.get("id")
                if ref in self.pers:
                    self._roll(ref, post.get("namn") or "")
        # föremål: paketets objekt + det som bara finns i läsningarna
        self.foremal = []  # dict(ord=set(stammar), ref=('objekt',oid)|('hand',[(pid,tid)])|('produkt',namn)|('last',namn), namn)
        nyc = K.foremals_nycklar()
        for o in P.get("objekt", []):
            if o["typ"] in ("golv", "vagg"):
                continue
            namn = (nyc.get(o["id"]) or o["typ"]).replace("foremal:", "")
            ord_ = set(tokens(namn)) | {stam(t) for t in tokens(namn)}
            if o["typ"] == "bord":
                ord_ |= {"bord", "disk", "bardisk", "glassdisk", "bänk", "disken", "bordet", "monter", "montern"}
            if o["typ"] == "stol":
                ord_ |= {"stol", "pall", "barstol"}
            if o["typ"] == "dorr":
                ord_ |= {"dörr", "dörren"}
            self.foremal.append(dict(ord=ord_, ref=("objekt", o["id"]), namn=namn, typ=o["typ"]))
        hand = []
        for post in (K.relevans or {}).get("poster", []):
            if post.get("typ") == "foremal_i_hand":
                pid = next((p for p in self.pers if p.lower() in [x.lower() for x in post.get("samspel", [])]), None) or (pids[0] if len(pids) == 1 else None)
                for tid in post.get("tagningar", []):
                    if pid:
                        hand.append((pid, tid.lower()))
                self.foremal.append(dict(ord=set(tokens(post.get("namn", ""))) | {stam(t) for t in tokens(post.get("namn", ""))},
                                         ref=("hand", [(pid, t.lower()) for t in post.get("tagningar", [])]), namn=post.get("namn"), typ="foremal_i_hand"))
            elif post.get("typ") in ("foremal", "mobel") and not any(norm(post.get("namn", "")) in norm(f["namn"]) for f in self.foremal):
                self.foremal.append(dict(ord=set(tokens(post.get("namn", ""))) | {stam(t) for t in tokens(post.get("namn", ""))},
                                         ref=("last", post.get("namn")), namn=post.get("namn"), typ=post.get("typ")))
        self.hand_tillfallen = hand
        for e in (K.liggare or {}).get("entiteter", []):
            if e["typ"] in ("foremal", "innehall") and not e.get("kalla_ref", "") in [f["ref"][1] for f in self.foremal if f["ref"][0] == "objekt"]:
                nm = e.get("namn") or e["id"]
                self.foremal.append(dict(ord=set(tokens(nm)) | {stam(t) for t in tokens(nm)}, ref=("last", nm), namn=nm, typ=e["typ"]))
        self.produkt = [p["har"] for p in (K.ryggrad or {}).get("platser", []) if p.get("typ") == "produkt"]
        for pr in self.produkt:
            self.foremal.append(dict(ord=set(tokens(pr)) | {stam(t) for t in tokens(pr)}, ref=("produkt", pr), namn=pr, typ="produkt"))

    def _roll(self, pid, text):
        n = norm(text)
        for roll, ordl in ROLLORD.items():
            if any(re.search(rf"(?<![\wåäö]){re.escape(o)}", n) for o in ordl if o not in ("hon", "henne", "han", "honom")):
                self.pers[pid]["roller"].add(roll)
        for t in tokens(text):
            if len(t) >= 4:
                self.pers[pid]["namn"].add(t)

    # -------------------------------------------------------------- personer
    def personer_i(self, text: str) -> list[str]:
        """Personer som en textbit pekar på. Namn går före roll, roll före pronomen."""
        n = norm(text)
        tok = tokens(n)
        ut = []
        for pid, d in self.pers.items():
            if any(nm in tok or stam(nm) in [stam(t) for t in tok] for nm in d["namn"] if nm[0:1].isalpha() and len(nm) >= 3 and not nm in ("person", "kund", "personal")):
                ut.append(pid)
        if ut:
            return ut
        for roll in ("personal", "kund", "kvinna", "man"):
            ordl = [o for o in ROLLORD[roll] if o not in PRONOMEN]
            if any(fold(stam(t)).startswith(fold(o)) for o in ordl for t in tok):
                kand = [pid for pid, d in self.pers.items() if roll in d["roller"]]
                if kand:
                    return kand
                if roll in ("kvinna", "man"):
                    # kön är okänt för alla som saknar det: de är kandidater, inte uteslutna
                    okand = [pid for pid, d in self.pers.items() if not ({"kvinna", "man"} & d["roller"])]
                    if okand:
                        return okand
                return ["?" + roll]
        for t in tok:
            if t in PRONOMEN:
                if len(self.pers) == 1:
                    return list(self.pers)
                kand = [pid for pid, d in self.pers.items() if PRONOMEN[t] in d["roller"]]
                if kand:
                    return kand
        return []

    # -------------------------------------------------------------- föremål
    def foremal_i(self, fras: str) -> list[dict]:
        """Föremål som en nominalfras pekar på. Svenska sammansättningar: huvudordet sist (disken -> glassdisk)."""
        tok = [t for t in tokens(fras) if t not in ("en", "ett", "den", "det", "de", "lite", "alla", "hela")]
        if not tok:
            return []
        st = [stam(t) for t in tok]
        traff = []
        for f in self.foremal:
            for s in st:
                if len(s) < 3:
                    continue
                if s in f["ord"] or any(w.endswith(s) and len(s) >= 4 for w in f["ord"]) or any(fold(w) == fold(s) for w in f["ord"]):
                    traff.append(f)
                    break
        # objekt i paketet går före läsningarnas namn när båda träffar samma ord
        if any(f["ref"][0] == "objekt" for f in traff):
            traff = [f for f in traff if f["ref"][0] in ("objekt",)] + [f for f in traff if f["ref"][0] != "objekt"]
        return traff


# ============================================================================ resultat

def _r(utfall, niva, regel, **k):
    return dict(utfall=utfall, niva=niva, regel=regel, **k)


def nej(niva, regel, skal, **k):
    return _r("nej", niva, regel, skal=skal, **k)


def motfraga(niva, regel, fraga, alternativ=None, **k):
    return _r("motfraga", niva, regel, fraga=fraga, alternativ=alternativ or [], **k)


def drag(niva, regel, op, **args):
    return _r("drag", niva, regel, drag=[dict(op=op, args=args)])


# ============================================================================ hjälp

def _tagning_nr(K, n: str):
    m = re.search(r"\b(?:scen|tagning|klipp|bild)\s*(?:nummer\s*|nr\.?\s*)?(\d+)\b", n)
    if m:
        return f"s{int(m.group(1))}"
    m = re.search(r"\b(första|andra|tredje|fjärde|femte|sjätte|sjunde|åttonde|sista)\s+(?:scenen|tagningen|klippet|bilden)\b", n)
    if m and K.paket:
        i = ORDNING[m.group(1)]
        ids = K.tagningar()
        return ids[i] if -len(ids) <= i < len(ids) else None
    return None


def _person_tagningar(K, pid):
    return [s["tagning"] for s in (K.paket or {}).get("rorelse", {}).get(pid, [])]


def _sista_replik(K):
    return K.repliker[-1] if K.repliker else None


def _handelser(K, verb_ord, pid=None):
    lg = K.liggare or {}
    ramar = set()
    for w in verb_ord:
        ramar |= set(VERB_RAM.get(w, []))
        if not VERB_RAM.get(w):
            for k, v in VERB_RAM.items():
                if w.startswith(k[:5]) and len(w) >= 5:
                    ramar |= set(v)
    ut = [e for e in lg.get("handelser", []) if e["ram"] in ramar and (pid is None or (e.get("roller") or {}).get("agent") == pid)]
    return ut


def _tal(n):
    m = re.search(r"\b(\d+(?:[.,]\d+)?|en|ett|två|tre|fyra|fem|halv)\s+sekund", n)
    if not m:
        return None
    g = m.group(1).replace(",", ".")
    return float(g) if g[0].isdigit() else TAL[g]


def _antal(n):
    m = re.search(r"\b(två|tre|fyra|fem|\d+)\s+(gånger|smakprov|portioner|stycken|st)\b", n)
    if m:
        g = m.group(1)
        return int(g) if g.isdigit() else TAL[g]
    if re.search(r"\b(en gång till|upprepa|igen)\b", n):
        return 2
    return None


def _split(n):
    """Delar en sammansatt mening där höger led börjar med ett nytt imperativ ('… och låt henne stå still')."""
    m = re.search(r"\s+och\s+(?=(låt|gör|ta|byt|lägg|flytta|ändra|ställ|visa|ha|sätt)\b)", n)
    if m:
        return [n[: m.start()].strip(), n[m.end():].strip()]
    return [n]


# ============================================================================ reglerna

def r_typbyte(n, K, L):
    typ = norm((K.ryggrad or {}).get("typ") or "")
    if re.search(r"\b(gör om|förvandla|omvandla|bygg om)\b.*\b(till|som)\b", n) or re.search(r"\bbyt(a)? upplägg", n) \
            or re.search(r"\b(gör|skapa|ta fram) en (annan )?version där\b", n) or re.search(r"\b(som|till) en \w+ (i stället|istället)\b", n):
        g = _har(n, GENRE)
        if g and g in typ:
            return None
        if g or "version där" in n or "upplägg" in n:
            return _r("typbyte", "typbyte", "typbyte", skal=f"Meningen byter klippets typ ({g or 'upplägget'})"
                      + (f"; klippet är '{typ}'" if typ else "") + ". Typen ärvs (ryggradens del 1), så det görs inte här.",
                      forslag="Behåll typen och ändra inom den, eller välj ett annat klipp i banken med den typen.")
    return None


def r_medie(n, K, L):
    lager = None
    if re.search(r"\b(text\w*|undertext\w*|textrad\w*|skylt\w*|rubrik\w*|textning)\b", n) or re.search(r"\bskriv\b.*\b(hörnet|skärmen|namn|överst|nederst)\b", n):
        lager = "skarmtext"
    elif re.search(r"\b(musik\w*|ljudet|ljud|låten|sången|volym\w*|ljudeffekt\w*|voiceover|speaker\w*)\b", n):
        lager = "ljud"
    elif re.search(r"\b(byt|ändra|skriv om)\b.*\breplik", n) or re.search(r"\böversätt", n) or re.search(r"\breplik\w*\b.*\bhandla om\b", n) \
            or re.search(r"\b(ska|låt \w+) säga\b", n):
        lager = "repliker"
    elif re.search(r"\b(lägg in|infoga|klipp in|visa)\b.*\b(bild|närbild|stillbild|klipp|video|film)\b\s+(på|av)\b", n):
        lager = "broll"
    elif re.search(r"\b(tätare|snabbare|lugnare|färre|fler|långsammare)\s+(klippning|klipp)\b", n) or "klipptakt" in n:
        lager = "montage"
    elif re.search(r"\bska spela\b", n) or re.search(r"\b(förkläde|kläder|klädd|tröja|keps|smink|uniform|frisyr)\b", n):
        lager = "manus"
    if not lager:
        return None
    if re.search(r"\b(ta bort|stryk|plocka bort|utan)\b", n):
        typ = "tar_bort"
    elif re.search(r"\b(lägg (på|in|till)|lägg|infoga|skriv|visa)\b", n):
        typ = "lagger_till"
    else:
        typ = "byter"
    return _r("medie", "medie", f"medie:{lager}", lager=lager, typ=typ)


def r_kontrast(n, K, L):
    if re.search(r"\b(skillnaden|kontrasten)\b.*\b(större|mindre|tydligare|mer|överdriv\w*)\b", n):
        upp = not re.search(r"\b(mindre|svagare)\b", n)
        return _r("ryggrad", "ryggrad", "kontrast", ryggrad_drag="kontrast_upp" if upp else "kontrast_ned")
    if re.search(r"\b(fler|färre) (scener|takter)\b", n):
        return _r("ryggrad", "ryggrad", "takter", ryggrad_drag="takter_upp" if "fler" in n else "takter_ned")
    return None


def r_struktur(n, K, L):
    P = K.paket
    # ordning: "börja med punchlinen", "X före Y", "byt ordning på … N och M"
    m = re.search(r"\b(byt|ändra|vänd på)\s+(plats|ordning(en)?)\s+(på|mellan)\s+(scen|tagning|takt|takterna|scenerna|tagningarna)?\s*(\d+)\s+och\s+(\d+)", n)
    if m:
        enhet = m.group(5) or ""
        a, b = int(m.group(6)), int(m.group(7))
        if enhet.startswith("takt"):
            return motfraga("ryggrad", "ordning_takt", f"Takt {a} och {b} är formatkortets takter; i förvärlden finns tagningar ({', '.join(K.tagningar())}). Menar du tagning s{a} och s{b}?",
                            [f"byt plats på s{a} och s{b}", "visa takterna mot tagningarna först"])
        return drag("ryggrad", "ordning_nr", "flytta_tagning", tid=f"s{a}", till=b - 1)
    if re.search(r"\bbörja med\s+(punchlinen|poängen|avslöjandet|slutet|vändningen)\b", n):
        sc = next((s["id"] for s in K.kalla_scener if s.get("funktion") == "punchline"), None) or (K.tagningar()[-1] if P else None)
        if sc is None:
            return nej("ryggrad", "borja_med", "ingen tagning är märkt som punchline")
        return drag("ryggrad", "borja_med", "flytta_tagning", tid=sc, till=0)
    m = re.search(r"\b(.+?)\s+(\w+\s+)?före\s+(.+)$", n)
    if m and not re.search(r"\b(skopa|räcka|ge)\b", m.group(1)):
        p1, p2 = L.personer_i(m.group(1)), L.personer_i(m.group(3))
        if p1 and p2 and p1 != p2 and len(p1) == 1 and len(p2) == 1 and not p1[0].startswith("?"):
            t1, t2 = _person_tagningar(K, p1[0]), _person_tagningar(K, p2[0])
            if not P:
                return drag("ryggrad", "fore", "flytta_tagning", tid=f"<första tagning med {p1[0]}>", till=f"<före första tagning med {p2[0]}>")
            if t1 and t2:
                ids = K.tagningar()
                return drag("ryggrad", "fore", "flytta_tagning", tid=t1[0], till=ids.index(t2[0]))
    # ta bort tagning
    if re.search(r"\b(ta bort|klipp bort|stryk|skippa|hoppa över)\b", n):
        tid = _tagning_nr(K, n)
        if tid:
            return drag("ryggrad", "ta_bort_tagning", "ta_bort_tagning", tid=tid)
        m = re.search(r"\b(?:scenen|tagningen|klippet|delen) där (.+)$", n)
        if m:
            pp = [p for p in L.personer_i(m.group(1)) if not p.startswith("?")]
            if pp:
                tt = [t for p in pp for t in _person_tagningar(K, p)]
                if len(set(tt)) == 1:
                    return drag("ryggrad", "ta_bort_tagning_dar", "ta_bort_tagning", tid=tt[0])
                if tt:
                    return motfraga("ryggrad", "ta_bort_tagning_dar", f"{pp[0]} finns i {', '.join(sorted(set(tt)))}. Vilken scen?", sorted(set(tt)))
        if re.search(r"\b(ta bort|klipp bort|stryk)\s+(slutet|början)\b", n) and P:
            tid = K.tagningar()[-1 if "slutet" in n else 0]
            return drag("ryggrad", "ta_bort_slut_borjan", "ta_bort_tagning", tid=tid)
    # längd
    sek = _tal(n)
    if sek and re.search(r"\blängre\b", n):
        if re.search(r"\b(slutet|i slutet|sista)\b", n) or "klippet" in n or "slutet" in n:
            return drag("ryggrad", "langd_slut", "hall_sista", sek=sek)
    if re.search(r"\b(gör|bli)\b.*\b(klippet|det|videon|slutet)\b.*\blängre\b", n) or re.fullmatch(r"(gör )?(klippet |det )?längre", n):
        return motfraga("ryggrad", "langre_vagt", "Längre på vilket sätt?", ["håll sista bilden 1 s (hall_sista)", "långsammare tempo i en handling", "en ny takt (kräver manus)"])
    if re.search(r"\b(korta|kortare|korta ner|korta av)\b", n):
        if P and re.search(r"\bmitten\b", n):
            mitt = K.tagning_for_ruta(P["tidsbas"]["antal_rutor"] // 2)
            return drag("ryggrad", "korta_mitten", "korta_tagning", tid=mitt, andel=0.5)
        tid = _tagning_nr(K, n)
        if tid:
            return drag("ryggrad", "korta_tagning", "korta_tagning", tid=tid, andel=0.5)
        if re.search(r"\b(slutet|början)\b", n) and P:
            return drag("ryggrad", "korta_slut", "korta_tagning", tid=K.tagningar()[-1 if "slutet" in n else 0], andel=0.5)
        return motfraga("ryggrad", "kortare_vagt", "Vilken del ska bli kortare?", K.tagningar())
    return None


def r_handling(n, K, L):
    ord_ = tokens(n)
    # hoppa över en handling
    m = re.search(r"\bhoppa över (?:när|att|då)?\s*(?:hon|han|de|\w+en)?\s*(\w+)", n)
    if m or re.search(r"\bskippa (när|att)\b", n):
        verb = [w for w in ord_ if w in VERB_RAM]
        hh = _handelser(K, verb)
        if hh:
            e = hh[0]
            return drag("scen.handling", "hoppa_over", "ta_bort_segment", a=e["rutor"][0], b=e["rutor"][1], vad=f"{e['id']} ({e['ram']})")
        if verb:
            return nej("scen.handling", "hoppa_over", f"handlingen '{verb[0]}' har inga rutor i förvärlden (ingen liggare med händelser för klippet)")
    # tempo
    m = re.search(r"\b(långsammare|snabbare|lugnare|segare|fortare)\b", n)
    if m and not re.search(r"\b(klippning|kamera)\b", n):
        faktor = 1.5 if m.group(1) in ("långsammare", "lugnare", "segare") else 1 / 1.5
        verb = [w for w in ord_ if w in VERB_RAM] or [w for w in ord_ if any(w.startswith(k[:5]) for k in VERB_RAM if len(w) >= 5)]
        pp = [p for p in L.personer_i(n) if not p.startswith("?")]
        hh = _handelser(K, verb, pp[0] if len(pp) == 1 else None) if verb else []
        if hh:
            e = hh[0]
            ovr = [x["id"] for x in hh[1:]]
            d = drag("scen.handling", "tempo", "tempo_segment", a=e["rutor"][0], b=e["rutor"][1], faktor=round(faktor, 3), vad=f"{e['id']} ({e['ram']})")
            if ovr:
                d["not"] = f"samma handling finns också i {', '.join(ovr)}: inte ändrad (fråga om den också ska bli {m.group(1)})"
            return d
        if pp and K.paket:
            tt = _person_tagningar(K, pp[0])
            if tt:
                t = next(x for x in K.paket["tagningar"] if x["id"] == tt[0])
                return drag("scen.handling", "tempo_person", "tempo_segment", a=t["ut"][0], b=t["ut"][1], faktor=round(faktor, 3), vad=f"{pp[0]} i {t['id']}")
        if verb or pp:
            return motfraga("scen.handling", "tempo", "Vilken del ska gå " + m.group(1) + "?", K.tagningar())
    # upprepa
    antal = _antal(n)
    if antal and re.search(r"\b(räck\w*|ge|ger|servera\w*|smakprov|gånger|portioner|upprepa|igen)\b", n):
        lg = K.liggare or {}
        nyckel = [w for w in ord_ if len(w) >= 5]
        fl = [f for f in lg.get("forlopp", []) if any(fold(stam(w))[:5] in fold(norm(f["syfte"])) for w in nyckel)]
        if fl:
            f = fl[0]
            return drag("scen.handling", "upprepa", "upprepa_segment", a=f["rutor"][0], b=f["rutor"][1], antal=antal, vad=f"{f['id']} ({f['syfte']})")
        return nej("scen.handling", "upprepa", "det finns inget förlopp i förvärlden att upprepa (ingen liggare med förlopp)")
    return None


def r_kamera(n, K, L):
    if re.search(r"\b(stabilisera\w*|skakar|skakig\w*|stativ|kameran stilla|stilla kamera|lugnare kamera|kameran ska stå still|sluta skaka)\b", n):
        tt = None
        if re.search(r"\b(i början|början)\b", n) and K.paket:
            tt = [K.tagningar()[0]]
        elif re.search(r"\b(i slutet|slutet)\b", n) and K.paket:
            tt = [K.tagningar()[-1]]
        elif _tagning_nr(K, n):
            tt = [_tagning_nr(K, n)]
        return drag("scen.kamera", "stabilisera", "kamera_stabilisera", tagningar=tt)
    m = re.search(r"\b(gå|kom|zooma|flytta kameran|åk)\s+(in\s+)?närmare\b(.*)$", n)
    if m:
        rest = m.group(3)
        tid = _tagning_nr(K, rest)
        pp = [p for p in L.personer_i(re.split(r"\bnär\b", rest)[0] or rest) if not p.startswith("?")]
        if re.search(r"\bnär\b.*\b(säger|sista|replik)", rest):
            r = _sista_replik(K) if re.search(r"\b(sista|slutet)\b", rest) else None
            if r:
                tid = r.get("scen")
                pp = [r.get("talare")] if r.get("talare") in L.pers else pp
        if not pp:
            if len(L.pers) == 1:
                pp = list(L.pers)
            else:
                return motfraga("scen.kamera", "narmare", "Närmare vem?", list(L.pers))
        if len(pp) > 1:
            return motfraga("scen.kamera", "narmare", "Närmare vem?", pp)
        if not tid:
            tt = _person_tagningar(K, pp[0])
            if not tt:
                return nej("scen.kamera", "narmare", f"{pp[0]} syns inte i förvärlden")
            tid = tt[0]
        return drag("scen.kamera", "narmare", "kamera_narmare", tid=tid, person=pp[0], faktor=0.7)
    if re.search(r"\b(tätare bild|tightare|mindre av lokalen|zooma in)\b", n):
        return drag("scen.kamera", "tatare", "kamera_lins", faktor=1.3)
    if re.search(r"\b(mer av lokalen|vidare bild|bredare bild|zooma ut|mer av rummet)\b", n):
        return drag("scen.kamera", "vidare", "kamera_lins", faktor=round(1 / 1.3, 4))
    return None


def r_plats(n, K, L):
    mal = None
    for pat in (r"\b(?:flytta|förlägg)\s+(?:det hela|hela klippet|allt|klippet|det|scenen)?\s*(?:till|in i|på|i)\s+(?:en |ett )?([\wåäö ]+?)$",
                r"\b(?:ändra|byt)(?: ut)?\s+(?:bakgrunden|miljön|lokalen|platsen|stället)\s+(?:till|mot)\s+(?:en |ett )?([\wåäö ]+?)$",
                r"\b(?:det ska vara|ska det vara|spela in det|vi är)\s+(?:på|i)\s+(?:en |ett )?([\wåäö ]+?)$",
                r"\bsamma sak men (?:på|i)\s+(?:en |ett )?([\wåäö ]+?)$"):
        m = re.search(pat, n)
        if m:
            mal = m.group(1).strip()
            break
    if mal:
        if L.foremal_i(mal) and not _har(mal, MILJO):
            return None  # 'flytta burken till bordet' är föremål
        return drag("scen.plats", "byt_miljo", "byt_miljo", miljo=mal)
    m = re.search(r"\b(?:spela in|gör|lägg|ta)\s+(början|slutet|första scenen|sista scenen|scen \d+)\s+vid\s+(.+)$", n)
    if m and K.paket:
        tid = K.tagningar()[0] if m.group(1) in ("början", "första scenen") else (K.tagningar()[-1] if m.group(1) in ("slutet", "sista scenen") else _tagning_nr(K, m.group(1)))
        ff = [f for f in L.foremal_i(m.group(2)) if f["ref"][0] == "objekt" and f["typ"] == "bord"]
        t = next(x for x in K.paket["tagningar"] if x["id"] == tid)
        if not t["personer"]:
            return nej("scen.plats", "flytta_interaktion", f"ingen person i {tid}")
        if not ff:
            return nej("scen.plats", "flytta_interaktion", f"det finns ingen '{m.group(2)}' i förvärlden att flytta till")
        return drag("scen.plats", "flytta_interaktion", "flytta_interaktion", person=t["personer"][0]["id"], tid=tid, till=ff[-1]["ref"][1])
    return None


def _produkt_byte(K, L, gammalt, nytt):
    """Produkten byts överallt den hålls: en platshållare i handen per tillfälle i läsningen."""
    dd = []
    for pid, tid in L.hand_tillfallen:
        t = next((x for x in (K.paket or {}).get("tagningar", []) if x["id"].lower() == tid), None)
        if t and pid in K.personer():
            dd.append(dict(op="byt_foremal_i_hand", args=dict(person=pid, gammalt=gammalt, nytt=nytt, rutor=list(t["ut"]))))
    return dd


def r_foremal(n, K, L):
    # byta
    m = re.search(r"\bbyt(?:a)?(?: ut)?\s+(.+?)\s+(?:mot|till)\s+(?:en |ett |lite )?(.+)$", n) or re.search(r"^(?:låt det vara\s+)?(?:en |ett )?(.+?)\s+i ?stället för\s+(?!att\b)(.+)$", n)
    if m:
        if "i stället för" in n or "istället för" in n:
            nytt, gammal = m.group(1), m.group(2)
        else:
            gammal, nytt = m.group(1), m.group(2)
        nytt = re.sub(r"^(en|ett|lite)\s+", "", nytt.strip())
        ff = L.foremal_i(gammal)
        if not ff:
            return nej("scen.foremal", "byt", f"det finns ingen '{gammal}' i förvärlden")
        f = ff[0]
        if f["ref"][0] == "objekt":
            return drag("scen.foremal", "byt_objekt", "byt_objekt", oid=f["ref"][1], ny=nytt)
        if f["ref"][0] in ("produkt", "hand") or (f["ref"][0] == "last" and f["typ"] in ("innehall", "foremal_i_hand")):
            dd = _produkt_byte(K, L, gammal, nytt)
            if dd:
                return _r("drag", "scen.foremal", "byt_produkt", drag=dd, ryggrad_drag="byt_produkt", ryggrad_param=nytt)
            return _r("drag", "ryggrad", "byt_produkt_ryggrad", drag=[], ryggrad_drag="byt_produkt", ryggrad_param=nytt,
                      not_="produkten byts bara på ryggradsnivå: inget föremål i hand finns i förvärlden")
        return nej("scen.foremal", "byt", f"'{f['namn']}' är läst i klippet men finns inte som föremål i förvärlden")
    # ta bort
    m = re.search(r"\b(?:ta bort|plocka bort|släng|röj undan|ta undan|ta away)\s+(.+?)(?:\s+från\s+(.+))?$", n)
    if m:
        fras = m.group(1)
        ff = L.foremal_i(fras)
        if not ff:
            pa = f" på {m.group(2)}" if m.group(2) else ""
            return nej("scen.foremal", "ta_bort", f"det finns ingen '{fras}'{pa} i förvärlden (föremål där: {', '.join(sorted({f['namn'] for f in L.foremal if f['ref'][0] == 'objekt'})) or 'inga'})")
        obj = [f for f in ff if f["ref"][0] == "objekt"]
        if obj:
            ids = sorted({f["ref"][1] for f in obj})
            if len(ids) > 1 and not re.search(r"\b(alla|allt|\w+arna|\w+erna|\w+orna)\b", fras):
                return motfraga("scen.foremal", "ta_bort", f"Det finns {len(ids)} som passar: {', '.join(ids)}. Vilken?", ids)
            return _r("drag", "scen.foremal", "ta_bort_objekt", drag=[dict(op="ta_bort_objekt", args=dict(oid=i)) for i in ids])
        return _r("drag_plan", "scen.foremal", "ta_bort_last", skal=f"'{ff[0]['namn']}' är läst i klippet men inte byggt i förvärlden",
                  effekter=[dict(typ="tar_bort", mal=dict(namn=[ff[0]["namn"]]), beskrivning=f"{ff[0]['namn']} tas bort")])
    # lägga till
    m = re.search(r"\b(?:lägg|ställ|sätt)(?: dit| till| in| fram)?\s+(?:en |ett |lite |några )?(.+?)\s+på\s+(.+)$", n)
    if m:
        st = [f for f in L.foremal_i(m.group(2)) if f["ref"][0] == "objekt" and f["typ"] == "bord"]
        if not st:
            return nej("scen.foremal", "lagg_till", f"det finns ingen '{m.group(2)}' att ställa något på")
        ids = sorted({f["ref"][1] for f in st})
        if len(ids) > 1 and K.paket:
            # bordet som syns i flest rutor (antagande, sägs i svaret)
            def langd(oid):
                o = next(o for o in K.paket["objekt"] if o["id"] == oid)
                return sum(b - a for a, b in o["synlig_ut"])
            ids = [max(ids, key=langd)]
        return drag("scen.foremal", "lagg_till", "lagg_till_objekt", etikett=m.group(1), pa=ids[0])
    # flytta föremål
    m = re.search(r"\bflytta\s+(.+?)\s+till\s+(.+)$", n)
    if m:
        a = [f for f in L.foremal_i(m.group(1)) if f["ref"][0] == "objekt" and f["typ"] == "foremal"]
        b = [f for f in L.foremal_i(m.group(2)) if f["ref"][0] == "objekt" and f["typ"] == "bord"]
        if a and b:
            return drag("scen.foremal", "flytta", "flytta_objekt", oid=a[0]["ref"][1], till=b[-1]["ref"][1])
    return None


def r_ensemble(n, K, L):
    if re.search(r"\b(en|ett) (fjärde|tredje|femte|ny|till|annan) (person|gäst|kund|kollega)\b|\bfler personer\b|\bha med en (kollega|vän|person)\b|\b(en|ett) (kollega|person) till\b", n):
        return nej("scen.kropp", "ny_person", "En ny person kräver en läst kropp; förvärlden kan inte skapa en utan generering (struken för CM:s ändringar). "
                   "På ryggradsnivån kan en kollega skrivas in i manus (byggsten/hand: personer_upp).")
    if re.search(r"\bbara (är |vara )?(en|ett) (karaktär|person|roll|skådespelare)\b|\bta bort (en |den andra )?(person|karaktär|roll)\b", n):
        andra = list(L.pers)
        return _r("drag_plan", "scen.kropp", "en_karaktar", skal="att stryka personer",
                  effekter=[dict(typ="tar_bort", mal=dict(personer=andra), beskrivning="alla utom en person tas bort")],
                  fraga="Vilken person ska vara kvar?", alternativ=andra)
    return None


def r_kropp(n, K, L):
    pp = [p for p in L.personer_i(n) if not p.startswith("?")]
    saknad = [p for p in L.personer_i(n) if p.startswith("?")]
    hand = re.search(r"\b(andra|vänster|höger|vänstra|högra)\s+hand(en)?\b", n)
    if hand:
        if saknad and not pp:
            return nej("scen.kropp", "hand_saknad_person", f"{saknad[0][1:]} finns inte i förvärlden (bara {', '.join(L.pers)} är lästa)")
        return nej("scen.kropp", "byt_hand", "Byte av hand kräver att hela kroppen anpassas (bål, grepp, steg) med en kroppsbunden rörelsemodell. "
                   "Spegling är struken (0031, 0038) och spärras av K7. Kroppsvägen (forvarld/kropp) är inte inkopplad här.")
    if re.search(r"\b(stå|står|stanna) (kvar|still)\b|\bstillastående\b|\bstå stilla\b", n):
        explicit = re.search(r"\bi ?stället för att (gå|röra sig|gå runt|gå iväg)\b", n)
        if not explicit:
            return motfraga("scen.kropp", "sta_still_oklart", "Vad betyder 'stå still' här? (Ägarens öppna fråga, karta/helhet.md:80.)",
                            ["låst förflyttning, gester och händer som i originalet (kinematisk platshållare)",
                             "helt stilla, en ny prestation (kräver rörelsemodell)"])
        if len(pp) != 1:
            return motfraga("scen.kropp", "sta_still", "Vem ska stå kvar?", list(L.pers))
        tt = _person_tagningar(K, pp[0])
        if not tt:
            return nej("scen.kropp", "sta_still", f"{pp[0]} syns inte i förvärlden")
        return drag("scen.kropp", "sta_still", "sta_still", person=pp[0], tid=tt[0])
    if re.search(r"\b(gå|går)\s+(genom|fram|in|till|över|runt)\b", n) and re.search(r"\bi ?stället för att sitta\b|\bsitta\b", n):
        if len(pp) != 1:
            return motfraga("scen.kropp", "ga", "Vem ska gå?", list(L.pers))
        return drag("scen.kropp", "ga_med_attityd", "ga_med_attityd", person=pp[0])
    k = _har(n, KANSLA)
    if k:
        if pp or re.search(r"\b(hon|han|henne|honom|kvinnan|mannen)\b", n):
            return nej("scen.kropp", "kansla", f"'{k}' är en känsla. Ansikte och mimik finns inte i förvärlden, och en känsla i kroppen kräver databuren helkroppsstil "
                       "(ledförskjutning blev 'en apa', 17 nov). Kan skrivas som regi i manus (spår D).")
        return motfraga("oklar", "kansla_utan_person", f"Vem ska vara {k}, och syns det i kroppen eller i manus?", list(L.pers))
    p = _har(n, POSE)
    if p:
        if saknad and not pp:
            return nej("scen.kropp", "pose_saknad_person", f"{saknad[0][1:]} finns inte i förvärlden")
        return nej("scen.kropp", "pose", f"'{p}' är en ny hållning eller rörelse. Den kräver en rörelsemodell (kroppsvägen); "
                   "att flytta leder för hand är en kinematisk förskjutning som ägaren har underkänt. Inte utförd.")
    return None


def r_vagt(n, K, L):
    v = _har(n, VAGT)
    if v:
        return motfraga("oklar", "vagt", f"'{v}' kan betyda flera saker. Vad ska ändras?",
                        ["tempo och längd (ryggraden)", "kamera och utsnitt", "text och ljud (medielagret)", "byt klipp i banken"])
    return None


REGLER = [r_typbyte, r_medie, r_kontrast, r_struktur, r_handling, r_kamera, r_plats, r_foremal, r_ensemble, r_kropp, r_vagt]


def tolka_del(n, K, L):
    for r in REGLER:
        ut = r(n, K, L)
        if ut is not None:
            return ut
    return motfraga("oklar", "ingen_regel", "Jag förstår inte vilken del av klippet meningen gäller. Kan du säga det med andra ord?",
                    ["struktur (scener, längd, ordning)", "föremål", "plats", "kamera", "kropp", "text och ljud"], llm_behovs=True)


def tolka(mening: str, K, L: Lexikon | None = None) -> dict:
    L = L or Lexikon(K)
    n = norm(mening).replace("istället", "i stället")
    n = re.sub(r"\s+", " ", n)
    delar = _split(n)
    res = [tolka_del(d, K, L) for d in delar]
    if len(res) == 1:
        ut = res[0]
    else:
        # sammansatt: det mest återhållsamma utfallet gäller hela meningen, delarna redovisas
        rang = {"typbyte": 5, "motfraga": 4, "nej": 3, "drag_plan": 2, "medie": 1, "drag": 0, "ryggrad": 0}
        varst = max(res, key=lambda r: rang.get(r["utfall"], 0))
        if all(r["utfall"] == "drag" for r in res):
            ut = dict(utfall="drag", niva="+".join(r["niva"] for r in res), regel="+".join(r["regel"] for r in res), drag=[d for r in res for d in r["drag"]])
        else:
            ut = dict(varst)
            ut["regel"] = "sammansatt:" + "+".join(r["regel"] for r in res)
            if varst["utfall"] in ("motfraga", "nej"):
                gor = [r for r in res if r is not varst and r["utfall"] == "drag"]
                if gor:
                    ut["skulle_gora"] = [d for r in gor for d in r["drag"]]
        ut["delar"] = res
    ut["normaliserad"] = n
    return ut
