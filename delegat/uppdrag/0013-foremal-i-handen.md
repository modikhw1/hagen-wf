---
id: 0013
titel: Föremål i handen: fäste per ruta, från deklaration till film
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0012
tillåten_skrivning: [scen/3d/ingest/deklaration_till_hand.py, scen/3d/ingest/mhr_rig.py, scen/3d/ingest/rum_uppsattning.py, scen/3d/ingest/rum_rutor.py, scen/3d/ingest/test_deklaration.py, scen/3d/kontrakt/, scen/3d/ingest/ut/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Mål
Ett föremål som deklarationen säger hålls av en person följer den personens hand genom tagningen i den renderade filmen, visat på köttbiten i `b-tilltal-ravara` och provskeden i `kand-kennysgelato`.

## Bakgrund
Luckan har kommit igen i varje klipp: det som bär handlingen hålls ofta i handen (`scen/3d/PIPE.md`, Öppet 6: "föremål i hand är den lucka som kommer igen"). Formatet har fältet `halls_av`, och uppsättningssteget fyller det, men inget byggs. Enligt `scen/3d/kontrakt/ut/foremal_logg/LOGG.md`: "`halls_av` kräver vald handled/handmatris per ruta i planen och ett tidsvarierande fäste i `ingest/mhr_rig.py`". Sedan 0009 byggs köttbiten som en låda på disken, vilket är en byggplats och inte det som syns.

Läs också `scen/3d/PIPE.md`, avsnittet "Händer utan bildstöd": handens läge är inte alltid belagt i bild, och det ska synas i utdata när fästet vilar på en hand utan stöd.

Kör efter 0012 (samma filer i `kontrakt/`).

## Att göra
1. **Vilken hand, när.** Per ruta: vilken hand som håller föremålet och under vilka rutor. Källor i ordning: segmenterarens mask för föremålet (`rum_rutor.py`, mask per nyckelbild) mot handledernas projektion i samma ruta; saknas mask används deklarationens `halls_av` med närmaste hand. Rutor där föremålet inte syns i handen: föremålet visas inte, eller ligger på sitt stöd om deklarationen har ett.
2. **Fästet.** Föremålet följer handens matris ur kroppens rigg, med en fast förskjutning i handens ram. Förskjutningen bestäms ur maskens tyngdpunkt relativt handleden i de rutor där båda syns, median över tagningen.
3. **Storlek.** Ur maskens utsträckning på handens djup, inom deklarerat intervall. Enkel form (låda eller ellipsoid) räcker; formen hör till stiliseringen, som kommer sist.
4. **Genom kedjan.** `hand.json` → `plats.json` → `plan` → byggaren, på samma sätt som `:pa:`-föremål går i dag, med eget id-mönster (`<roll>:hand:<id>`). Skymningskontrollen ska inte stryka ett föremål för att det ligger framför den hand som håller det.
5. **Två händer och överlämning.** Hålls föremålet av två händer: fäst vid den ena och redovisa. Byter det hand eller person mellan tagningar: ett fäste per tagning. Inom en tagning: redovisa att det hände, bygg det inte nu.

## Gränser
- Bara filerna i `tillåten_skrivning`. Baslinje av ändrad kod först till `kontrakt/ut/fore_hand_0013/kod/`. I `ut/` bara nya varianter.
- Modal för segmentering förhandsgodkänt, tak 0,50 dollar. Gateway bara om gelatos uppsättning saknar `halls_av`, tak 0,20 dollar.
- Ingen ny kroppsläsning. Händernas kvalitet är den ingesten har.
- Ändra inget medan test, kompilering eller rendering kör. Tom cache.
- Planer utan `halls_av` (notan, guacamole) ska vara oförändrade. Visa det.
- Egna trösklar är diagnos. Redovisa dem.

## Klart när
- Tester gröna med antal, nya prov för punkterna 1, 2 och 4.
- b-tilltal, variant `n06-hand`: per tagning där köttbiten syns, avståndet i slutkameran mellan föremålets projicerade mitt och maskens tyngdpunkt, i promille av bildhöjden, för minst tre rutor per tagning.
- Film för b-tilltal och gelato med sökvägar. Titta på minst en bild per tagning och beskriv: sitter föremålet i handen, är det rimligt stort, skymmer det rätt.
- Hur många rutor fästet vilar på en hand utan bildstöd, per tagning.
- Tillägg i `PIPE.md` (formatet och datavägen) och överst i `NASTA.md`.

## Leveransform
`delegat/svar/0013-foremal-i-handen.md` enligt mallen, högst cirka 70 rader.
