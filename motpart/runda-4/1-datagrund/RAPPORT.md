# Runda 4, steg 1: datagrund (20 nov 2026)

## Resultat i en mening
200 av 200 urvalsklipp är hämtade i källans egen bildtakt med ljud, 0 misslyckade, 0 ersatta, 575 MB totalt. Ingen mätning eller analys av innehåll är gjord.

## Urvalsregel och fördelning
Fullständig regel i `URVAL.md` (skrevs före hämtningen), skript `urval.py`, frö 20261120, resultat `urval.json`.
- Population: de 2 703 klipp med lokala mått (e28/tek) som också finns i e15 (typ, konto, visningar) och i `letrend-e13`, 5–60 s, med kontomedian. Efter bortfall 2 398. Runda 3:s hold-out (4 id) utesluten.
- Strata: typ (5 × 40) × utfall (70 vinnare över 1,65 × kontots median, 70 förlorare under 0,61 ×, 60 mitten) × längd (69 kort under 15 s, 70 mellan, 61 lång över 30 s). 96 konton, högst 4 per konto.
- Utvecklingsklippen (notan, guacamole, gelato, a-sketch, b-tilltal, duepiani, spanjorskan): **inga medtagna och ingen räknad separat.** Repot har ingen nyckel från utvecklingsnamnen till `<konto>-<videoid>`. Urvalet innehåller dock klipp från kontot `spanjorskansthlm`, vilket syns i kontaktkartan, men det är inte säkert att något av dem är utvecklingsklippet.

## Hämtning
- `hamta.py` (yt-dlp 2026.10.26 via uvx, sekventiellt, 2–4 s paus, återupptagbart, avbrott vid under 6 GB ledigt eller över 2 GB totalt). Logg `hamta.logg.txt`, försök i `manifest_hamtning.jsonl`.
- 200 ok, 0 misslyckade (inga borttagna, geoblockerade eller felande klipp), ingen reserv användes. Ett klipp (`brelbar-7579314927551253782`) hämtades först som manuellt prov med samma kommando och format och räknas som `fanns` i loggen.
- Plats: `C:\Users\praiseworthy\Downloads\letrend-r4\<konto>-<videoid>.mp4`. Inget befintligt raderat, `letrend-e13` orört.
- Ledigt diskutrymme: före 10 572 226 560 byte (9,85 GiB), efter 10 003 955 712 byte (9,32 GiB). Filerna: 575 MB. Se `disk_fore.txt` och `disk_efter.txt`.

## Kontroll per fil (`kontroll.py`, `manifest.jsonl`)
ffprobe, sha256, storlek, ljud och längd per fil. Längd mot `klipp.jsonl` (heltalssekunder): alla 200 inom 1 s (median 0,46 s, max 0,99 s), alltså ingen avvikelse utöver avrundning. Alla 200 har ljudspår.

| mått | fördelning |
|---|---|
| bildtakt (avrundad) | 30: 160, 60: 22, 25: 6, 24: 2, 29: 3, 50: 3, 31: 1, 54: 1, 56: 1, 59: 1. Lägsta 24, alltså över kravet 8. |
| upplösning | 1080×1920: 128, 720×1280: 35, 576×1024: 25, övriga (720×1282, 720×1272, 540×960, 480×854, 720×720, 576×1022, 540×962): 12 |
| codec | HEVC 181, H.264 19 |
| total storlek | 575 MB (medel 2,9 MB per klipp) |

## Avvikelser mot uppdraget (öppet redovisade)
1. **Höjdgränsen 720 hölls inte.** 128 klipp är 1080×1920 och 25 är 576×1024. Formatfiltret `height<=720` passerade eftersom TikToks format anges efter kortsidan eller i andra etiketter än den verkliga höjden (provklippet valde formatet `h264_540p` som var 576×1024). Jag har inte omkodat eller hämtat om. Skälet att jag lät det stå: kravets syfte var att hålla storlek och diskutrymme, och totalen blev 575 MB. Högre upplösning skadar inte rörelsemätning, men måtten blir inte jämförbara pixel för pixel mellan klipp utan en gemensam nedskalning, och 22 klipp har 50–60 bilder/s. Behöver ägaren 720 som gräns går det att hämta om med `-S "res:720"` (cirka 1 GB mindre än 1080p-delen), men det är ett val jag inte gjorde.
2. **HEVC i 181 klipp.** Vissa verktyg (äldre OpenCV, webbläsare) kan inte avkoda det. ffmpeg klarar det, och kontaktkartan gjordes med det.
3. Typ och utfall i urvalet är hämtade ur e15 (språkmodellens typetikett och visningar), inte nymätta.

## Kontaktkartan (`kontaktkarta_40.jpg`, `kontaktkarta_tat.jpg`, skript `kontaktkarta.py`, bildlistor i `.txt`)
- **40 slumpade klipp, en ruta ur mitten (frö 20261121):** allt är stående 9:16-restaurang- och matinnehåll: personer som talar till kameran, kök, mat i närbild, text på bild, ett par POV-klipp med överlagd text. Variationen är stor (belysning, lokal, typ). En ruta är nästan svart (mörk lokal eller övergång) och en ruta har svarta fält upptill och nedtill (troligen det kvadratiska klippet 720×720, ej verifierat mot rutan). Den första versionen av kartan blev trasig (olika bredd på rutorna, bara första rutan syntes) och gjordes om med fast ruta 180×320.
- **Tätt samplat (3 klipp, 8 rutor med 0,25 s mellanrum, sekund 3–5):** rörelsen syns nu. Rad 2 (`brunchoteket`) visar en person som tar en tugga, lyfter bruschettan mot kameran och sänker den, och rad 3 (`blubnan.liljeholm`) har en klippgräns och en person som bär en bricka. Rad 1 (`spanjorskansthlm`) visar en gående person över en fast bakgrund efter ett klipp från ett annat inslag. Mot dagens 240p/2 bilder per sekund, där rutorna ligger 0,5 s isär med låg upplösning, går nu gester, steg och klippgränser att följa. Jag har inte mätt rörlighet, bara tittat.

## Kända svagheter
- Urvalet är stratifierat på e15:s typ och på utfall relativt kontomedian med mina egna gränser (±0,5 i log), inte på ägarens krav, och 146 klipp utan kontomedian föll bort.
- Klippen som fanns i e13 är de som gick att hämta då, så "borttagna klipp" är redan bortgallrade ur populationen och 0 misslyckade säger inget om hur många som är borta på sikt.
- Spanjorskan och övriga utvecklingsklipp är inte identifierade via id (se ovan).
- Blandade bildtakter (24–60) och upplösningar (480p–1080p) måste normaliseras innan rörelsemått jämförs.
- Hämtningen är en ögonblicksbild från 20 nov: räknare (visningar) ändras, men urvalet bygger på de gamla värdena.
