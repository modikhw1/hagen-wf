# Steg 10c – löpande logg

2026-11-10. Hela specifikationskedjan (steg10b, steg10, förlagan) läst.
Inga Blender-, Modal-, nät- eller rendersteg. Inga ändringar i forvarld,
kroppsbank eller modal_gemx.py. En tung process åt gången.
Befintliga filer kopieras före första ändringen till
ut/fore_steg10c/<sökväg från projektroten>. Radslut bevaras.

## Klart
- Tidigare körning verifierad: 131 prov, 1501,864 s testtid / 1503,4 s väggtid,
  ett AST-fel. 39 händelser i notan, 54 i b är verifierade på disk.
- Platsreferens: arkivets oförändrade solver och 507 hashlåsta historiska
  indata. Hela plats.json jämförs byte för byte. Proveniens ligger i testdata.
- AST-felets orsak var varningsanrop i logg(). Den ursprungliga loggfunktionen
  är återställd; varningen ligger vid ingeststegkörningen och i kor_jamn.
  Inget testundantag eller tolerans ändrad. AST-provet och platsprovet: 2 OK,
  27,175 s.
- Kenny: accepterad translation 0 m. Aktuell avvisad kandidat 14 307,266 m;
  gamla tider.json sade 11 693,57 m. 27 tidsloggar synkade från befintliga
  varld.npz och utsnitt, med föregående värden sparade. Ingen ingest omkörd.
- Baslinjekod fryst i ut/steg10c/baslinje. Tre edits och varje testmodul
  körs sekventiellt i egna processer. Första trimkompileringen: 68,754 s.
- Snabbväg under arbete: snabb=True / --snabb hoppar över diagnostik,
  bevarar knäskydd och skymningsbeslut och märker planen ej_kord.
  Full diagnostik är standard i funktion och hela pipelinekörningen.

## Nästa
1. Slutför och verifiera beständig cache, separat diagnostik och snabba tester.
2. Mät trim/text/prop före och efter och jämför hela byggplanen.
3. Kör samtliga moduler separat och redovisa modultider.
4. Slutför MHR-tabell, README och rapport. Inget ur bortskuret scope.

## Exakta kommandon
Alla kommandon från projektroten, med
`$env:PYTHONIOENCODING='utf-8'` och `scen/.venv/Scripts/python.exe`.
PowerShells `$OutputEncoding` sätts till UTF8 när Python får källtext via stdin.

- `scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10_platsreferens.py`
  (redan kört; vägrar skriva över referensen).
- `scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10c_synka.py`
  (redan kört; kör inte igen utan att granska loggens proveniens).
- `scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10c_mata.py fore`
  pågår. Läser fryst baslinjekod; en modul eller edit åt gången.
  Resultat och fulla loggar i ut/steg10c/fore_*.

## Snabbvägens övriga kostnader
Propfästen på handleder läser nu samma skyddade överkroppsleder direkt, utan att lösa dold ben-IK för varje prop och ruta. Fästen på benleder behåller stödet. Höjdpassning får en egen beständig cache med sina mätfiler och kod/rigg i nyckeln. Planlikhet kommer att jämföras mot den frysta baslinjen för alla tre edits, inklusive samtliga propmatriser.
Baslinje klar för edits: trim 68,754 s; text 92,594 s; prop 95,306 s. Modulmätning pågår.

## Dokumentation
README för kontrakt, ingest, testdata och engang uppdaterad. MHR-BEROENDEN.md är skriven från lokal kodläsning; första versionen har 445 referenspunkter i 77 filer (165 hårda). Inga migreringsändringar. Baslinjens test_flode pågår; inga andra testmoduler startade samtidigt.

## Lägespunkt 17:20
Baslinjen kör fortfarande test_flode i separat process (start 17:10). Tre före-edits är klara, JSON-planer sparade som fore_trim/text/prop_plan.json. Test_flode har hittills en error-markering; full feltext kommer vid modulslut. Ändra inte baslinjekopiorna.
Ny kod är syntaxgranskad men inga nya testmoduler har startats parallellt. Nästa körning efter baslinjen: `scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10c_mata.py snabb_kall trim text prop`, följt av `snabb_varm1 trim text prop` och därefter separata efter-moduler. Snabbmätningarna använder egna cachemappar per edit, så kalla och varma tider kan skiljas åt.
De nya assetläsarna för hud/fothud reagerar även i samma process på ändrad riggfil; gammalt skinunderlag får inte överleva en ogiltigförklarad mätcache. Test_snabb omfattar sju nya prov, inklusive exakt precision för handfästen. Slutlig MHR-tabell ska regenereras efter sista kodändringen.

## Fortsättning 17:30–
- Baslinjeprocessen för test_flode var död (inget steg10c_mata-barn kvar). Jag tog
  över: snabb_kall/snabb_varm1 körda. Fel i tropassning.anpassa: kodnyckeln
  pekade på kontrakt/rumsmall.py som inte finns (filen ligger i ingest/). Rättat.
- Mätt (en edit på notan, egen process): snabb kall trim 7,97 s, text 10,23 s,
  prop 10,86 s; varm (ny process, cache på disk) trim 1,19 s, text 0,95 s, prop 1,15 s.
  Före: 68,75 / 92,59 / 95,31 s.
- Planjämförelse (ut/steg10c/fore_*_plan.json mot snabb_*): endast kvalitet.* och
  varningar skiljer (13 vägar). Resten, inklusive propmatriser, identiskt.
- test_flode.test_fel_edit_ar_atomisk föll redan i baslinjen: byt_prop utan scen
  hoppar över scener där propen saknas (nya tidsmedvetna propsemantiken), så
  editen lyckas i s1. Provet nu: byt_prop med scen='s2' (där propen är borttagen)
  som den misslyckade editen. Samma kontroll av atomicitet, ingen tröskel ändrad.
- Kedjan körs i bakgrunden: efter-moduler först (efter_alla.log), sedan baslinje
  (fore_alla.log). Moduler: test_flode test_rumsmall test_regler test_text_disk
  test_kroppmatt test_props test_handelser test_snabb test_plats_snapshot
  semantik.test_semantik bro.test_bro test_rum (test_rum finns ej).

## Slut 18:05
- datacache.signatur använder abspath/os.stat i stället för resolve (resolve är
  långsamt på Windows): varm snabbkompilering 0,79 s för trim/text/prop.
- Alla moduler gröna efter ändringen (efter_*_tid.json). Baslinjens (fore_*_tid.json)
  test_flode har samma fel som före rättelsen av provet (stale prov); baslinjens
  test_snabb faller eftersom de sju proven testar ny kod. 
- MHR-BEROENDEN.md regenererad (534 punkter, 80 filer).
- semantik/test_semantik.py är ett skript, inte unittest: kör direkt (ok, 4 s).
- Kvar: inget känt. Ej gjort: separata renderingar, tom4/prop_byte/prop_tom.
