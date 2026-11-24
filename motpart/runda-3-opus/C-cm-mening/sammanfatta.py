"""Räknar rapportens tabeller ur ut/resultat.json, ut/holdout_resultat.json och ut/latens.json -> ut/sammanfattning.json."""
import collections
import json
import pathlib

HIT = pathlib.Path(__file__).resolve().parent
UT = HIT / "ut"

# De 21 meningarnas kategori enligt byggsten/hjarna/UTMANING.md:64-70 (g10 räknas där både som plats och kropp).
KATEGORI_21 = {
    "struktur": ["b9", "g7", "g1", "b1", "g6", "b4", "b3"],
    "föremål och plats": ["g4", "b6", "b8", "g5", "b5", "g10"],
    "kroppens sätt": ["g9", "g11", "g2", "b10"],
    "handling": ["g3", "b7", "b2"],
    "känsla": ["g8"],
}
# Före: kärnans Jev-yta (forvarld_karna/mening_motor.py:166-212) och vad manipulera_scen faktiskt utför (rad 388, 435).
FORE_21 = {
    "g11": "byt_hand_A (spegling, struken 0031/0038: K7-brott)",
    "g9": "byt_hand_A finns, men meningen gäller kunden, som inte är läst",
}


def main():
    d = json.loads((UT / "resultat.json").read_text(encoding="utf-8"))
    R = d["resultat"]
    ho = json.loads((UT / "holdout_resultat.json").read_text(encoding="utf-8"))
    lat = json.loads((UT / "latens.json").read_text(encoding="utf-8"))
    def mangd(rr):
        c = collections.Counter(r["bedomning"].get("klass") for r in rr)
        return dict(c)
    karna = [r for r in R if "@B" not in r["id"] and not r.get("skriven_av_byggaren")]
    b = [r for r in R if "@B" in r["id"] and not r.get("skriven_av_byggaren")]
    byg = [r for r in R if r.get("skriven_av_byggaren")]
    def nyckeltal(rr):
        matbara = [r for r in rr if r["utfall"] != "ej_korbar"]
        tyst = [r for r in matbara if r["bedomning"].get("klass") == "tyst fel"]
        ska = [r for r in matbara if r["bedomning"].get("facit", [None])[0] == "utford"]
        ratt_ska = [r for r in ska if r["bedomning"].get("klass") == "rätt utförd"]
        strikt_tyst = [r for r in matbara if r["bedomning"].get("klass") == "tyst fel" or
                       (r["bedomning"].get("klass") == "rätt utförd" and r["bedomning"].get("op_strikt") is False)]
        return dict(korda=len(rr), matbara=len(matbara), tyst_fel=len(tyst), tyst_fel_andel=round(len(tyst) / max(1, len(matbara)), 3),
                    tyst_fel_id=[r["id"] for r in tyst], tyst_fel_strikt=len(strikt_tyst), tyst_fel_strikt_id=[r["id"] for r in strikt_tyst],
                    ska_utforas=len(ska), ratt_utford_av_dem=len(ratt_ska), andel=round(len(ratt_ska) / max(1, len(ska)), 3),
                    missar=[r["id"] for r in ska if r["bedomning"].get("klass") != "rätt utförd"],
                    klasser=mangd(rr), utfall=dict(collections.Counter(r["utfall"] for r in rr)))
    per_kalla = {}
    for r in karna:
        per_kalla.setdefault(r.get("kalla"), []).append(r)
    per_kalla = {k: nyckeltal(v) for k, v in per_kalla.items()}
    tjugoett = {r["id"]: r for r in karna if r["id"][0] in "gb" and r["id"][1:].isdigit()}
    kat = {}
    for k, ids in KATEGORI_21.items():
        rad = {}
        for i in ids:
            r = tjugoett.get(i)
            rad[i] = dict(fore=FORE_21.get(i, "ingen_passar (inget drag i kärnans yta)"),
                          efter=f"{r['utfall']}" + (f" ({', '.join(x['op'] for x in r['drag'])})" if r and r.get("drag") else "") if r else "?",
                          klass=r["bedomning"].get("klass") if r else "?")
        kat[k] = rad
    bevar = collections.Counter((r.get("diagnos") or {}).get("bevarande", {}).get("utfall") for r in R if r.get("diagnos"))
    grind_nya = [(r["id"], {k: v for k, v in r["diagnos"]["grindar"]["efter"].items() if v > r["diagnos"]["grindar"]["fore"].get(k, 0)})
                 for r in R if r.get("diagnos") and "efter" in r["diagnos"].get("grindar", {})]
    grind_nya = [x for x in grind_nya if x[1]]
    platsh = [(r["id"], r["platshallare"]) for r in R if r.get("platshallare") and r["utfall"] == "utford"]
    krasch = [r["id"] for r in R if r.get("krasch")]
    nyckel = json.loads((UT / "blind_nyckel/nyckel.json").read_text(encoding="utf-8")) if (UT / "blind_nyckel/nyckel.json").exists() else None
    ut = dict(
        k7=d["k7"], frysning=d["frysning"],
        karnans_paket=nyckeltal(karna), b_paket=nyckeltal(b), byggarens=nyckeltal(byg), per_kalla=per_kalla,
        kategori_21=kat, holdout=dict(antal=ho["antal"], ratt=ho["ratt_niva"], andel=ho["andel"],
                                       fel=collections.Counter(f"{x['router_niva']}:{x['regel']}" for x in ho["meningar"] if not x["ratt"])),
        latens=lat, bevarande=dict(bevar), nya_grindfel=grind_nya, platshallare=platsh, krascher=krasch,
        blind=dict(antal=len(nyckel["par"]), kontroller=[p for p in nyckel["par"] if p["typ"].startswith("kontroll")]) if nyckel else None,
        stopp=[(r["id"], r["skal"][0][:160]) for r in R if r["utfall"] == "stopp"],
        varnade_utforda=[r["id"] for r in R if r["utfall"] == "utford" and (r.get("k5") or {}).get("niva") == "varning"],
    )
    (UT / "sammanfattning.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(ut, ensure_ascii=False, indent=1, default=str)[:12000])


if __name__ == "__main__":
    main()
