"""Fryser meningslistorna och facitförslagen innan routern skrivs (spår C, runda 3).

Kör en gång:  scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\frys.py
Skriver meningar/frysta.json, facit/facit_forslag.json och meningar/manifest.json (sha256 för allt).

Ingen mening här är skriven av byggaren av spår C. Källa och författare står per mening.
Facit är byggarens FÖRSLAG, skrivet före första körningen. Ägaren dömer.
  godta: utfall som byggaren räknar som rätt. utford = ändringen görs, nej = ärligt nej, motfråga
         eller stopp med skäl, medie = routas till medielagret (spår D), typbyte = stopp för byte av typ.
  kraver_varning: rätt bara om K5-vakten varnar eller stoppar.
  op: väntat drag när utford godtas (kontrolleras mot systemets drag).
"""
import hashlib
import json
import pathlib
import datetime

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[2]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def las(rel):
    return json.loads((ROT / rel).read_text(encoding="utf-8"))


KALLOR = {
    "gelato_0031": dict(fil="forvarld/gelato/meningar_0031.json", forfattare="orkestratorn (Fable) 13 nov; nr 11 är ägarens (0031)", paket="gelato"),
    "btilltal": dict(fil="forvarld/btilltal/meningar.json", forfattare="orkestratorn 12 nov (före första körningen)", paket="btilltal"),
    "notan_jevprov": dict(fil="forvarld/jevprov/meningar.json", forfattare="orkestratorn 10 nov (facit 'familj' skrivet före Jev)", paket="notan"),
    "guac_0032": dict(fil="forvarld/guacamole/ut_0032/meningar.json", forfattare="uppdragstagaren 0032, före första Jev-körningen", paket="guacamole"),
    "regibord_14nov": dict(fil="byggsten/hand/ut/regi/bord-20261114-180404/logg.json", forfattare="okänd: inskrivna i regibordet 14 nov (chickiiburger = notans tvilling); finns inte som assistenttext i någon av 56 sessionsloggar. Knappfraser (FRAS) är bortplockade", paket="notan"),
    "hand_regi": dict(fil="byggsten/hand/README.md", forfattare="Fable 14 nov (regi-passet gelato_bar, README rad 189-190)", paket="gelato"),
    "agare_exempel": dict(fil="karta/helhet.md", forfattare="ägarens exempelmeningar 10 nov, återgivna av assistent [Äb] (karta/helhet.md:22)", paket="gelato"),
    "lage_argon": dict(fil="LAGE.md", forfattare="Argon (LAGE.md:15), exempel på CM-manipulation", paket=None),
    "fable_kropp": dict(fil="byggsten/hand/ut/regi/bord-20261116-185002/logg.json", forfattare="Fable 16 nov (inskrivet via webbläsarverktyg, sessionslogg a4ca74e3…:1900)", paket="gelato"),
}


def meningar():
    ut = []
    g = las(KALLOR["gelato_0031"]["fil"])
    for m in g["meningar"]:
        ut.append(dict(id=f"g{m['nr']}", kalla="gelato_0031", text=m["text"], paket="gelato", original_facit=m.get("vantat")))
    b = las(KALLOR["btilltal"]["fil"])
    for m in b["meningar"]:
        ut.append(dict(id=f"b{m['nr']}", kalla="btilltal", text=m["text"], paket="btilltal", original_facit=m.get("tema")))
    n = las(KALLOR["notan_jevprov"]["fil"])
    for m in n["utv"] + n["test"]:
        ut.append(dict(id=f"n_{m['id']}", kalla="notan_jevprov", text=m["mening"], paket="notan",
                       original_facit=f"{m['familj']} (stöds idag: {m['stods_idag']})" + (f"; {m['not']}" if m.get("not") else "")))
    q = las(KALLOR["guac_0032"]["fil"])
    for m in q["meningar"]:
        ut.append(dict(id=f"q{m['nr']}", kalla="guac_0032", text=m["text"], paket="guacamole", original_facit=m.get("vantat")))
    for i, t in enumerate(["Byt ordning på takt 3 och 4, punchlinen måste sluta med vidvinkeln",
                           "Ändra så att det bara är en karaktär"], 1):
        ut.append(dict(id=f"r{i}", kalla="regibord_14nov", text=t, paket="notan", original_facit=None))
    for i, t in enumerate(["gör skillnaden mellan portionerna större", "ta bort Vs-skylten och musikbytet"], 1):
        ut.append(dict(id=f"h{i}", kalla="hand_regi", text=t, paket="gelato",
                       original_facit=["kontrast_upp (utfört på ryggraden)", "takt3_stryk (utfört, följd: vändningen är borta)"][i - 1]))
    for i, t in enumerate(["gör klippet längre", "stabilisera kameran", "gör att kvinnan ler efter att hon fått maten",
                           "ändra bakgrunden till en foodtruck och gör henne stillastående"], 1):
        ut.append(dict(id=f"a{i}", kalla="agare_exempel", text=t, paket="gelato", original_facit=None))
    ut.append(dict(id="l1", kalla="lage_argon", text="låt kunden gå genom lokalen fram till bardisken med samma slappa attityd i stället för att sitta",
                   paket="guacamole", original_facit="ga_med_attityd (Argon)"))
    ut.append(dict(id="l2", kalla="lage_argon", text="låt henne skopa och räcka fram med andra handen", paket="gelato",
                   original_facit="byt_hand (Argon, spegling)"))
    for i, t in enumerate(["hon ska vara blyg och titta ner när hon räcker fram skeden",
                           "hon ska vara stolt och rak i ryggen när hon räcker fram skeden"], 1):
        ut.append(dict(id=f"f{i}", kalla="fable_kropp", text=t, paket="gelato", original_facit="scenlagret (Jev, 16 nov)"))
    return ut


# Byggarens facitförslag. Skrivet 19 nov innan router.py och drag.py fanns.
F = dict
FACIT = {
    "g1": F(godta=["nej"], kraver_varning=True, kommentar="Skopandet ger smakprovet som räcks fram (bär). Ryggraden 14 nov: takt 1 skyddad. Fables förväntan 13 nov var att utföra (ta_bort_handling h3): ägaren avgör."),
    "g2": F(godta=["utford"], op="tempo_segment", kommentar="Tempo på skopandets rutor, faktor > 1. Originalrörelsen omsamplas."),
    "g3": F(godta=["utford"], op="upprepa_segment", kommentar="Förloppet servera upprepas. Kopierad rörelse, inte ett nytt förlopp (UTMANING A3): platshållare."),
    "g4": F(godta=["utford"], kraver_varning=True, op="byt_foremal", kommentar="Produkten byts (ryggradens plats [produkt]). Greppet (skopa) står kvar: varning."),
    "g5": F(godta=["utford", "nej"], kraver_varning=True, op="ta_bort_objekt", kommentar="Disken ramar meningen och hon lutar sig mot den: varning krävs om den tas bort."),
    "g6": F(godta=["utford"], op="kamera_stabilisera", kommentar="Kameran i s1 rör sig i paketet (R25)."),
    "g7": F(godta=["utford"], op="hall_sista", kommentar="Håll sista rutan 1 s."),
    "g8": F(godta=["nej"], kommentar="Ansikte och mimik finns inte i förvärlden; känsla kräver databuren stil."),
    "g9": F(godta=["nej"], kommentar="Kunden är inte läst i förvärlden."),
    "g10": F(godta=["nej"], kommentar="'Stå still' är ägarens öppna fråga (karta/helhet.md:80): motfråga. Miljöbytet ensamt vore en platshållare."),
    "g11": F(godta=["nej"], kommentar="Andra handen kräver kroppsbunden rörelsemodell; spegling är struken (K7)."),
    "b1": F(godta=["utford"], op="ta_bort_tagning", kommentar="S5 bär inget ensamt (C finns i S5–S11)."),
    "b2": F(godta=["utford", "nej"], op="flytta_tagning", kommentar="Liggaren: ordningen mellan Mads och Morten är tillfällig."),
    "b3": F(godta=["medie"], kommentar="Skärmtext: spår D."),
    "b4": F(godta=["utford", "nej"], op="kamera_narmare", kommentar="Lærke = C enligt liggaren."),
    "b5": F(godta=["nej"], kraver_varning=True, kommentar="Vågen avgör (bär)."),
    "b6": F(godta=["utford"], kraver_varning=True, op="byt_foremal", kommentar="Köttbiten bär; byte på funktion med varning."),
    "b7": F(godta=["nej"], kommentar="En ny kropp kan inte skapas utan generering."),
    "b8": F(godta=["utford", "nej"], op="byt_miljo", kommentar="Miljöbyte är en platshållare (etikett och färg), rummets form läses inte om."),
    "b9": F(godta=["utford"], op="hall_sista"),
    "b10": F(godta=["nej"], kommentar="Ny hållning kräver rörelsemodell."),
    "n_u1": F(godta=["utford", "nej"], op="kamera_stabilisera", kommentar="Kamerorna står i stort sett still; R25 har lagt rörelse i s7."),
    "n_u2": F(godta=["nej", "utford"], op="hall_sista", kommentar="Vagt: motfråga eller håll slutet."),
    "n_u3": F(godta=["nej"], kommentar="Mimik saknas; ingen mat i förvärlden."),
    "n_u4": F(godta=["nej"], kommentar="'Stillastående' oklart (hon sitter redan): motfråga."),
    "n_u5": F(godta=["medie"]),
    "n_u6": F(godta=["medie"]),
    "n_u7": F(godta=["medie", "nej"], kommentar="Kläder hör till manus och inspelning, inte dockan."),
    "n_u8": F(godta=["medie"]),
    "n_u9": F(godta=["nej"]),
    "n_u10": F(godta=["utford"], op="ta_bort_tagning", kommentar="Servitören finns bara i s4."),
    "n_t1": F(godta=["nej", "utford"], op="kamera_stabilisera", kommentar="Kameran i s1 står redan still: ärligt nej är rätt, stabilisering ofarlig."),
    "n_t2": F(godta=["utford", "nej"], op="kamera_narmare", kommentar="Sista repliken och dess talare ur källan."),
    "n_t3": F(godta=["nej"]),
    "n_t4": F(godta=["utford", "nej"], op="sta_still", kommentar="Låst förflyttning är en kinematisk platshållare."),
    "n_t5": F(godta=["utford", "nej"], op="byt_miljo"),
    "n_t6": F(godta=["utford"], op="byt_foremal"),
    "n_t7": F(godta=["utford", "nej"], op="korta_tagning"),
    "n_t8": F(godta=["medie"]),
    "n_t9": F(godta=["medie"]),
    "n_t10": F(godta=["medie"]),
    "n_t11": F(godta=["nej", "utford"], kraver_varning=True, op="flytta_tagning", kommentar="Avslöjandet bär genom att komma sist: varning eller motfråga."),
    "n_t12": F(godta=["medie", "nej"]),
    "n_t13": F(godta=["nej"], kommentar="Ingen mat i förvärlden (burk och muggar)."),
    "n_t14": F(godta=["nej"]),
    "n_t15": F(godta=["medie", "nej"]),
    "n_t16": F(godta=["utford", "nej"], op="byt_miljo"),
    "n_t17": F(godta=["nej"]),
    "n_t18": F(godta=["medie"]),
    "n_t19": F(godta=["medie"]),
    "n_t20": F(godta=["typbyte"], kommentar="Sketch till tilltal: byter typ."),
    "q1": F(godta=["nej"]),
    "q2": F(godta=["nej"]),
    "q3": F(godta=["utford", "nej"], op="tempo_segment", kommentar="Text och ljud måste följa med (spår D)."),
    "r1": F(godta=["nej", "utford"], op="flytta_tagning", kommentar="'Takt 3 och 4' är ryggradens takter, inte tagningar: motfråga är rimlig."),
    "r2": F(godta=["nej"], kraver_varning=True, kommentar="Två främlingar bär poängen."),
    "h1": F(godta=["utford", "nej"], op="kontrast", kommentar="Ryggradens kontrastratt; i scenlagret finns ingen stor portion att skala."),
    "h2": F(godta=["nej", "medie"], kraver_varning=True, kommentar="Vs och musikbytet bär vändningen."),
    "a1": F(godta=["nej", "utford"], op="hall_sista"),
    "a2": F(godta=["utford"], op="kamera_stabilisera"),
    "a3": F(godta=["nej"]),
    "a4": F(godta=["nej"]),
    "l1": F(godta=["utford", "nej"], op="ga_med_attityd", kommentar="Bara som märkt kinematisk platshållare (glider, runda 1 MENING §3.2)."),
    "l2": F(godta=["nej"], kommentar="Spegling struken (K7)."),
    "f1": F(godta=["nej"]),
    "f2": F(godta=["nej"]),
}


def main():
    ms = meningar()
    saknas = [m["id"] for m in ms if m["id"] not in FACIT]
    assert not saknas, saknas
    (HIT / "meningar").mkdir(exist_ok=True)
    (HIT / "facit").mkdir(exist_ok=True)
    fm = HIT / "meningar" / "frysta.json"
    fm.write_text(json.dumps(dict(kallor=KALLOR, meningar=ms), ensure_ascii=False, indent=1), encoding="utf-8")
    ff = HIT / "facit" / "facit_forslag.json"
    ff.write_text(json.dumps(dict(av="byggaren av spår C (Claude Opus 5.5), 19 nov, före router.py",
                                  regel="Förslag, inte ägarens facit. Ägaren dömer.", facit=FACIT), ensure_ascii=False, indent=1), encoding="utf-8")
    manifest = dict(tid=datetime.datetime.now().isoformat(timespec="seconds"),
                    kallfiler={k: dict(fil=v["fil"], sha256=sha(ROT / v["fil"])) for k, v in KALLOR.items()},
                    frysta=dict(fil="meningar/frysta.json", sha256=sha(fm)),
                    facit=dict(fil="facit/facit_forslag.json", sha256=sha(ff)),
                    antal=len(ms))
    (HIT / "meningar" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
