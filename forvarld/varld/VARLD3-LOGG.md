# Återupptagning 10 november 2026

## Ramar
Skriv bara under forvarld/. Ingen Blender, ingen kompilering eller annan körning under scen/.
Python: scen/.venv/Scripts/python.exe -B, från projektroten, PYTHONIOENCODING=utf-8.
Originalspecifikationen och sista loggsvansen är lästa. Del 5 är uppskjuten.

## Klart vid återstart
- Paket, chatt, 13 bakgrundsplåtar från tre miljötyper finns på disk.
- Tidigare tio chattprov: median 503,2 ms, max 897 ms, 20 Jev-anrop i liggaren.
- Tidigare live-bilder visar dubblerad undertext och förlust av hårkontur.
- Sparad cProfile läst utan att köra kompilatorn: 73,901 s totalt;
  kvalitet.komplettera 63,431 s, kroppmatt.matt_plan 55,427 s,
  cv2.fillPoly 27,182 s, trohet.mat 8,689 s, skymning.los 7,977 s.

## Pågår / nästa
1. Gemensam spärr för bränd källtext i live-shadern och samtliga alpha-kanaler.
2. Ta bort s5-specialfallet ur live-vägen. Kontrollera huvud/handbilder visuellt.
3. En namngiven ingång för kroppsexport och dokumenterad ombyggnadsordning.
4. Lätta lokala kontroller, högst två nya chattmeningar, kort renderprov.
5. Svenska README med verkliga mått, bilder och kvarstående fel.

## Exakta läskommandon som körts
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe -B -c "import pstats; pstats.Stats('forvarld/varld/pipeline/compile-profile.bin').sort_stats('cumulative').print_stats(24)"
```
Ingen kompilering har körts. Ingen Blender har startats.

## Slutfört i återupptagningen
- Del 1: elva reducerar-/browserfall inklusive ångra, 5,8–93,4 ms, inga browserfel.
- Del 2: två nya meningar gav rätt textbyte och miljöbyte samt fungerande ångra.
  1 416 / 631,9 ms. Fyra nya Jev-anrop; liggaren har totalt 24.
  De gamla tio proven är bevarade: lägre mittvärde 503,2 ms, vanlig median 507,4 ms,
  max 897 ms. Målet en sekund hålls inte alltid.
- Del 3: 13 plåtar från tre miljötyper verifierade. s1/s7 fångade i två miljöer.
  Uppladdning läst men inte omtestad.
- Del 4: gemensam textspärr i kroppsshader + samtliga kortmasker efter held-union.
  304 maskkontroller utan källtext. Sju bilder utan separat textlager granskade.
- Live-kort använder generisk handled/LK-kontroll i stället för s5-kod/polygon.
  Bara s5 vänster handled accepteras med slutgränserna: median 2,73 px, max 6,85 px.
  Äldre förgrundskonturer i refine.py är fortfarande klippspecifika antaganden.
- Live-huvudets hela referenskontur följer huvudleden; håret klipps inte av som förr.
- Visuell QA hittade även GPU-textur från föregående scen efter seeked. Rättat genom
  explicit VideoTexture.needsUpdate och väntan på video.seeking; alla slutbilder omtagna.
- Ny replik: frusen undre ansiktstextur via referenshuvudets transform, originalljud
  tystat i luckan. Inget nytt tal/läppsynk. Tystning kontrollerad.
- body_source.py är namngiven gräns för plan, blend, riggnamn och råa body-arrayer.
  export/refine/live/Blenderutdrag använder gränsen. Nya råfiler prioriteras före gamla.
- world-metadata.json sparar chattens repliker/kortbindningar/bakgrunder som explicit
  data. export.py återför dessa fält så att en ny export inte tappar chattmetadata.
- README omskriven på svenska, med precisa framtida ombyggnadskommandon.
- Ingen Blender, kompilering eller annan Pythonkod under scen/ kördes.

## Slutliga resultat på disk
- resume-check.json: rörlig live-render median 1,2 ms, p95 1,9 ms, cirka 60 rAF/s;
  74/75 live-rutor, 38 olika källrutor. Fruset 1,5/3,3 ms; lastbrus, ingen säker delta.
- light-verification.json: 21 regi-schemaexempel utan fel, 304 textmaskprov,
  Python-syntax OK. Inga referens-/hash-/kompilatorkontroller körda.
- Hela paket/: 17 640 844 byte (16,82 MiB), inklusive bakgrunder och schemasnapshot.
- live-export.json: sista maskpasset 15,957 s; audit per handled/scen.
- bilder/ansikte-fore-efter.png, hand-fore-efter.png, oversikt.png: omtagna och sedda.
- bilder/undertextkontroll.png, miljobyten.png: omtagna och sedda.
- Bilder visar tydligare mun/fingrar, men textdolda ytor har frusna/inpaintade remsor,
  s6 har stora hål, och ändrad kamera avslöjar plana kort och skarvar.
- Del 5 förblir uppskjuten. Ny modell och full Blenderombyggnad är inte verifierade.

## Körda kommandon (från projektroten)
```powershell
$env:PYTHONIOENCODING='utf-8'
node forvarld/varld/server.mjs
node forvarld/varld/check.mjs
scen/.venv/Scripts/python.exe -B forvarld/varld/live.py
node forvarld/varld/capture-v5.mjs
node forvarld/varld/resume-check.mjs
# Efter visuell upptäckt av gammal GPU-videoruta och rättning:
node forvarld/varld/capture-v5.mjs --pictures-only
node forvarld/varld/resume-check.mjs --no-chat
scen/.venv/Scripts/python.exe -B forvarld/varld/compose-v5.py
scen/.venv/Scripts/python.exe -B forvarld/varld/verify-light.py
```
live.py kördes två gånger under utvecklingen. Bildfångsten upprepades efter
textur-/sökfixen. Den slutliga resume-körningen återanvände chattresultaten och
anropade inte Jev igen. debug-live.mjs användes för en enskild bild utan textlager.
jsonschema saknas i venv; ingen installation gjordes. verify-light.py validerar
schemaord som faktiskt används i det lokala regi-schemat med en liten lokal validator.

## Fortsätt här
1. Vänta tills det andra jobbet levererat matchande ny plan.json + scen.blend.
2. Läs README-avsnittet ”När kropparna ... ändras”. Ingen ombyggnad körs automatiskt.
3. Peka BODY_PLAN i body_source.py på den färdiga nya planen vid behov.
4. Kör framtida export/refine/venues/live/fångst enligt README, INTE --reuse-raw
   efter kroppsbyte. Inga fler UI-migrationer med upgrade.py.
5. Kontrollera det nya riggformatet/benens namn och granska kontakt-/maskfel visuellt.
6. Minsta kompilatoroptimering finns beskriven i README; ingen ändring under scen/.
   Enbart kroppmatt-bypass sparar ~55 s men lämnar ~18 s. En full snabbflagga måste
   också skilja mått från beslut i skymning.los och skyddade_knan. Ingen sub-sekundgaranti.
7. Klipp b först när Blenderexport åter är tillåten och den nya modellen är färdig.
