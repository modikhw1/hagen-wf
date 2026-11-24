Bygg scen-JSON v0 och guidebilder för ett prov: kan en bildmodell (Luma) flytta kameran och vrida en person enligt en beordrad ändring, och följer den bäst siffror i text, ord eller en renderad guidebild? Arbetet sker i C:\Users\praiseworthy\Desktop\hagen-wf. Skriv bara i den nya mappen scen/3d/scenjson/. Ändra ingen befintlig kod och inga befintliga data.

## Idén
Varje keyframe får en scen-JSON: en uppskattning av hur scenen ser ut i verkligheten, i meter. Den är inte en exakt mätning, utan en rimlig och konsekvent iscensättning som förklarar bilden. Skalan sätts av människokroppen: SAM 3D Body ger avståndet kamera–person stabilt (±4 cm mellan Luma-bild och original i dagens prov) och en rimlig kroppslängd. En ändring görs i JSON:en (t.ex. kameran 1,0 m bakåt, personen vriden 20°), renderas som guide från den nya kameran, och vi mäter sedan med SAM om bildmodellens utfall faktiskt gjorde ändringen. Mätningen är målet: beordrad ändring mot uppmätt ändring.

## Keyframes
Notan, klipp `scen/klipp/d-dialog-notan.mp4` (576x1024, 30 fps):
- S1: ruta 36. Kvinnan sitter vid bord, mot kameran, gestikulerar. Fötterna syns inte.
- S4: ruta 213. Servitören står. Fötterna syns inte i originalet.
Originalrutorna finns också som `scen/3d/lasformat/luma-paket/indata/bild/S1.png` och `S4.png`.

Befintliga data att bygga på (läs, ändra inte):
- SAM 3D Body på exakt dessa rutor: `scen/3d/lasformat/luma-paket/poang/kropp/p/0000.npz` (S1) och `0001.npz` (S4), fokal 1024 px. Index i `poang/index.json`.
- Hela tagningarna: `scen/3d/ingest/ut/notan-tagningar/S1/` och `S4/` (personer.json, masker.npy, kropp/, sekvens_*.npz, rum/, rum.json, varld.npz, kamera/golv). S1-tagningen är rutorna 0–72 och S4 171–255 i hela klippet; kontrollera tidsmappningen i meta.json/tider.json.
- Servitörens ben och fötter: Wan-breddat klipp `scen/3d/lasformat/ut/A/` (SAM-läsning med synliga ben, längd 1,734 m) och rapporten `scen/3d/lasformat/RAPPORT.md`.
- Rummet: MoGe-djup och moln i `scen/3d/ingest/ut/notan-tagningar/S*/rum/`, Gemini-detektioner där. Rummet läses ur ORIGINALET (Wan-bakgrunden var instabil).
- Blender 5.2 finns i C:\Program Files\Blender Foundation\Blender 5.2\ (kör i bakgrund: `blender.exe -b -P skript.py -- args`). MHR-kroppen kan nycklas med `scen/3d/blender/mhr_blender.py` (läs hur den används i `scen/3d/ingest/ingest_klipp.py`, steg blender).
- Läs `scen/3d/ingest/README.md` och `scen/3d/kontrakt/README.md` för konventioner. Observera: GOLV2-arbetet i kontrakt/ är fryst och dess svit är inte grön; bygg inte vidare på det.

## Del 1: scen-JSON v0
En fil per keyframe: `scen/3d/scenjson/S1.json`, `S4.json`. Föreslaget schema (förbättra gärna, men håll det enkelt och dokumentera i README):
- `version`: "scen/0.1"; `kalla`: klipp, ruta, tid.
- `koordinater`: meter, högerhänt, y upp. Origo på golvet rakt under kameran, z framåt längs kamerans horisontella blickriktning, x åt höger.
- `kamera`: position [0, h, 0], pitch, roll (grader), fokal_px, bild_px, fov_grader.
- `skala`: ankare (kroppen via SAM-avstånd och MHR-längd), osäkerhet i ord och siffra.
- `golv`: hur golvet bestämts (MoGe-plan skalat så att MoGe-djupet på personens pixlar stämmer med SAM-avståndet; för S1, där golvet är skymt, får antagandet sitthöjd/stolsits användas, märkt `antagen`).
- `personer[]`: id, roll, `ogon`, `huvud`, `hoft`, `fotter` (synliga eller härledda; för servitören från Wan-läsningen), `riktning_grader` (vridning runt y, 0 = vänd mot kameran), `langd_m`, `pose_kalla` (fil + ruta så att exakt pose kan återskapas).
- `mobler[]` och `foremal[]`: bord, stolar, disk som lådor (centrum, storlek, vridning); nyckelföremål (mugg, burk, hamburgare, terminal/mobil) som punkter eller små lådor. Grovt räcker.
- `vaggar[]`: plan eller lådor där MoGe ger stöd.
- `kvalitet`: per fält `matt`, `harledd` eller `antagen`.

Kontroll: rendera JSON:en (kropp + lådor + golvrutnät) från ORIGINALKAMERAN och lägg över originalrutan. Kroppen ska ligga på personen (silhuett-IoU mot masken), golv och bord ska linjera ungefär. Spara `kontroll_S1.jpg`, `kontroll_S4.jpg` och siffrorna i README.

## Del 2: ändringen och guidebilderna
Samma ändring för båda keyframes, så att proven går att jämföra:
- Kameran flyttas 1,0 m bakåt (z −1,0) på samma höjd och med samma blickriktning.
- Huvudpersonen vrids 20° åt sin egen högra sida (runt sin egen lodlinje genom höften), pose i övrigt oförändrad.
Skriv den ändrade scenen som `S1_andrad.json`, `S4_andrad.json` med ett fält `andring` som beskriver exakt vad som ändrats.

Rendera från den nya kameran, 576x1024:
- `guide/S1_blockout.png`: enkel grå blockout (MHR-kropp i ljusgrått, möbler som lådor, golv med rutnät 0,5 m, väggar), inget ljus- eller stiltrick.
- `guide/S1_djup.png`: djupbild i samma stil som Lumas F3 (nära ljust, långt mörkt).
- Samma för S4.
- Rendera också samma två från ORIGINALKAMERAN (`guide/S1_blockout_orig.png` osv.), som referens.
Där den nya kameran ser yta som originalet inte visade (bakom kameran, utanför bild) räcker golv och närmaste väggar ur JSON:en; skriv i README vad som är påhittat.

## Del 3: mätverktyget
Skriv `matt_andring.py`: tar en utfallsbild (valfri upplösning nära 9:16) och en keyframe, kör SAM 3D Body via `scen/3d/ingest/modal_sam3db.py` (samma sätt som `scen/3d/lasformat/luma-paket/poang.py` gör, fokal 1024 efter skalning till 576x1024), och rapporterar:
- uppmätt förändring av avståndet kamera–person (beordrat +1,0 m, plus den geometriska effekten av att personen vrids, som du räknar ut ur JSON:en),
- uppmätt vridning av personen relativt kameran (beordrat 20°), ur SAM:s global_rot jämfört med originalets,
- posedrift i övrigt (Procrustes, som i poang.py),
- en enkel dom: följde / delvis / följde inte, med gränserna skrivna i README som diagnos, inte som krav.
Prova verktyget på guidebilderna själva (blockout från ny kamera bör mätas nära beordrad ändring om SAM läser blockouten; om SAM inte läser blockouten, skriv det) och på originalbilden (bör ge noll ändring). Det kalibrerar verktyget innan Luma-utfall finns.

## Del 4: promptpaket för Luma
Skriv `scen/3d/scenjson/LUMA-PROMPTER.md` med tre varianter per keyframe, som ägaren kör i Luma-webbappen med originalbilden som referens:
- a) siffror: grundregeln + scen-JSON (förkortad till det väsentliga) + ändringen i siffror.
- b) ord: grundregeln + ändringen i ord ("the camera steps back about one meter; she turns about 20 degrees to her right").
- c) guide: grundregeln + guidebilden (blockout eller djup, välj den som SAM läste bäst i del 3) som andra referens + kort text.
Grundregeln: "Keep the same people, same clothes, same pose except the requested turn, same room, same light, same lens. Realistic." Utfallen ska sparas i `scen/3d/scenjson/utfall/<a|b|c>/S1.png` osv.

## Ramar
- Python: scen/.venv/Scripts/python.exe med PYTHONIOENCODING=utf-8. Ingen python i PATH. Modal: scen/.venv/Scripts/modal.exe.
- Modal-kostnad: högst 2 USD totalt. Logga i `budget.json`.
- Skriv filer som UTF-8 med LF. Skicka aldrig filinnehåll genom PowerShell-pipe.
- Sök inte rekursivt genom scen/3d/kontrakt/ut/.
- Skriv `scen/3d/scenjson/README.md` löpande (schema, hur värdena tagits fram, kontrollsiffror, vad som är antaget). Kvoten kan ta slut mitt i; det som står där ska vara användbart.

## Rapport
Kort, på svenska, för en ägare som inte läser kod: hur väl stämmer scen-JSON:en med originalbilden (kontrollbilderna), vad är mätt och vad antaget, hur väl läser mätverktyget guidebilderna, och vad som inte hann bli klart.
