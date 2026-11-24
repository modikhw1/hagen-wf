# Biblioteket: lokal analys av riktiga klipp

Grunden som videoförändringen ska stå på. Riktiga klipp (just nu 26 från ssstik i `Downloads`) bryts ned lokalt till scener, komposition, kroppar och rörelse, och granskas mot videon. Rättelserna är facit när analysens gränser kalibreras, på samma sätt som hagen-ui kalibrerade scengränserna på 26 klipp.

Öppna `localhost:5180/#bibliotek`.

## Köra

```
cd app
npm run analysera -- "C:/Users/praiseworthy/Downloads"   # Mät + Se + Tolka för nya klipp
npm run analysera -- --tolka                             # bara Tolka om, från rådata (sekunder)
npm run test:analys                                      # reglerna i tolka.mjs
```

## Tre steg

| Steg | Var | Vad | Kostnad |
|---|---|---|---|
| **Mät** | `analys/mat.mjs` | ffprobe: längd. ffmpeg `select=gt(scene,…)`: klippkandidater med styrka (samma filter som hagen-ui). Bildrutor i 10 fps | sekunder |
| **Se** | `analys/runner.js` i Edge headless | MediaPipe Pose Landmarker (33 punkter i bild och 3D, upp till 4 personer). OpenCV.js: kamerarörelse ur bakgrunden (personerna maskas bort) och ORB-likhet före/efter varje klippkandidat | cirka 1,5× klippets längd |
| **Tolka** | `analys/tolka.mjs` | Rena funktioner: klipptyp, scener, utsnitt, placering, vridning, kameraord, aktivitet | millisekunder |

Mät och Se sparas som rådata i `data/ra/`, så Tolka kan köras om när gränserna ändras.

## Vad analysen ger per scen

- **Klipptyp:** scenbyte, hoppklipp (samma uppställning), zoomryck (samma uppställning, inzoomad), inskott (kortare än 0,5 s), svag kandidat. Hoppklipp, zoomryck och inskott är **dynamik**, inte nya scener.
- **Utsnitt** ur huvudpersonens synliga punkter: total, halvtotal, halvbild, nära, extrem, eller objekt när ingen person syns.
- **Placering** (vänster, mitten, höger), storlek och **vridning** mot kameran (framifrån, snett, profil; bakifrån är osäkert i MediaPipe).
- **Kameraord** där 2D räcker: pan, tilt, in/ut, roll, handhållen, följer. Pan och truck går inte att skilja utan djup.
- **Aktivitet** i bildhöjder per sekund, för kamera och motiv (personernas punkter med kamerans rörelse bortdragen). Det är samma slags mått som motorn i `#v` använder, så riktiga klipp och varianter kan jämföras.

## Gränser och var de kommer ifrån

Alla ligger i `GRANSER` i `tolka.mjs` och sparas i varje analys.

- `HARD 0,3`: hagen-uis tröskel för klipp.
- `SAMMA_ANDEL 0,08`: satt efter tre klipp. Riktiga scenbyten gav 0,03–0,04, hoppklipp 0,11–0,25.
- `ZOOMRYCK 0,05` (|ln skala|), `MIN_SCEN 0,5 s`.
- Brusgolv per ruta (`BRUS`): mätt på stativklipp.

De kalibreras mot rättelserna. Nästa steg är en rapport som räknar hur ofta analysen och granskningen är överens per gräns.

## Rättelser

I inspektören:
- Klicka på ett klipp i tidslinjen för att byta typ.
- Lägg till ett missat scenbyte vid spelhuvudet.
- Byt utsnitt per scen och skriv en anteckning.

Allt sparas i `data/rattelser/<id>.json` tillsammans med analysens version.

## Stacken och hagen-ui

- ffmpeg följer hagen-uis kontrakt: `FFMPEG_PATH`/`FFPROBE_PATH`, annars PATH (Docker i produktion). Reserv här: `ffmpeg-static`.
- Mät och Tolka är Node utan webbläsare och kan flyttas in i hagen-uis ingest-worker. Se kräver en webbläsare (MediaPipe och OpenCV körs i WASM/WebGL); i workern blir det Playwright med Chromium, eller MediaPipe för Python om workern får Python.
- Spelaren i hagen-ui är egen (`decision.own-scene-player`); här används en vanlig `<video>` med analysen ritad ovanpå.

## Kända begränsningar

- MediaPipe ser kroppar, inte händer eller ansiktsuttryck i detalj. Närbilder på händer och mat blir "objekt".
- Text i bild kan ge falsk likhet över ett klipp när texten ligger kvar.
- Kamerarörelsen är 2D. Djup (dolly mot zoom, truck mot pan) kräver 3D-rekonstruktion, till exempel GVHMR, som behöver CUDA och inte går på den här datorn.
