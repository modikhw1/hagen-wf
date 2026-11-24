---
id: 0016
titel: Det kedjan redan vet ska in i tillståndet: föremål som namngivna objekt, scengrupper, och håll sista rutan
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0014
tillåten_skrivning: [forvarld/btilltal/, scen/3d/kontrakt/, scen/3d/ingest/deklaration_till_hand.py, scen/3d/ingest/test_deklaration.py, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Mål
Fyra av de tio meningarna i 0014 som stannade går hela vägen till en bild som visar det som begärdes: m5 (ta bort vågen), m6 (byt köttbiten mot en ost), m2 (låt Morten gissa före Mads) och m9 (gör slutet en sekund längre).

## Bakgrund
`delegat/svar/0014-b-tilltal-i-forvarlden.md`. Ingen mening stannade på geometri. Jev routade alla tio till rätt familj. Stoppen låg i att tillståndet och regin saknar begrepp som kedjan redan har i sin egen data:
- Vågen och köttbiten finns i deklarationen och i planen (`:pa:`-objekt, `plan.handforemal`) men inte i källans `semantik.props`, så Jev har inget att välja.
- "Mortens gissning" är två tagningar (s3+s4). Deklarationen vet vem som är i vilken tagning, men regin flyttar en scen åt gången.
- Tiden kan inte gå utanför källintervallet, och en ogiltig edit kastar hela regin.

Kör efter 0015 om den ligger före; uppdragen rör olika filer.

## Att göra
1. **Föremål till källan.** Allt som deklarationen bygger (på möbel eller i hand) blir en namngiven prop i `kalla.semantik.props` med id, typ, var den finns (stöd eller roll och hand), och i vilka scener den syns. Görs av kedjan, inte för hand: härled ur `plan.plats[].deklarerat.foremal` och `plan.handforemal`.
2. **Ta bort och byt.** `ta_bort` på en sådan prop ska ta bort den i alla dess former (kopior per kameragrupp, handfäste, `:pa:`-barn). `byt` till en typ som inte finns: behåll plats, fäste och storleksklass, byt etikett och färg, och märk att formen är en platshållare. Formen hör till stiliseringen.
3. **Scengrupper.** Härled grupper ur deklarationen: intilliggande tagningar med samma roll i bild hör ihop ("A:s gissning" = s1+s2). Lägg dem i tillståndet som enheter Jev kan välja, och låt flytt och borttag gälla gruppen. En replik som korsar en gruppgräns (m1 i 0014) ska följa med sin grupp eller redovisas.
4. **Håll sista rutan.** En tidsoperation som förlänger en scen förbi källans slut genom att hålla sista rutan (kropp, föremål och text står still). Märk i planen att rutorna är hållna och inte lästa.
5. **En ogiltig edit kastar bara sig själv**, med skäl, inte hela regin.
6. **Kör om de tio meningarna** oförändrade (`forvarld/btilltal/meningar.json`) genom samma väg, och rätta `prov.mjs` byggfel för m7 och m10 så att de stannar där de verkligen stannar.

## Gränser
- Bara filerna i `tillåten_skrivning`. Baslinje av ändrad kod i `scen/3d/kontrakt/` först till `scen/3d/kontrakt/ut/fore_tillstand_0016/kod/`. Ändra inte `forvarld/varld/` eller `forvarld/jevprov/`; behövs deras kod, kopiera till `forvarld/btilltal/`.
- Schemaändringar i källa och regi ska vara bakåtkompatibla: Notans och guacamoles befintliga källor och regier ska gå igenom oförändrade. Visa det, och kör kontraktets tester.
- Skärmtexten som tavla (punkt 2 i 0014:s lista) ingår **inte**. m2 räknas som klar när scenerna flyttats som grupp; redovisa vad tavlan då visar fel.
- Jev-anrop förhandsgodkända, tak 0,10 dollar. Ingen rendering utöver en stillbild före och efter per mening.
- Ändra inget medan test eller kompilering kör. Tom cache.

## Klart när
- Tester gröna med antal, nya prov för punkterna 1–5.
- Samma tabell som i 0014, före och efter, för alla tio meningarna.
- Före- och efterbild för m2, m5, m6 och m9, med en rad om bilden visar det som begärdes.
- Tillståndets storlek (rader och tokens) före och efter, och Jevs mediantid per mening. Tillståndet får inte växa så att routningen blir långsam; redovisa.
- Tillägg i `PIPE.md` (vad kedjan nu för över till källan) och överst i `NASTA.md`.

## Leveransform
`delegat/svar/0016-foremal-och-scengrupper-i-tillstandet.md` enligt mallen, högst cirka 70 rader.
