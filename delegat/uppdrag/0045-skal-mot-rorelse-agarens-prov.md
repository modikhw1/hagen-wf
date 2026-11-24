---
id: 0045
titel: Ägarens blinda prov: manus med skäl mot manus med rörelser
status: redo
från: orkestratorn (Opus 5.5), efter ägarens utmaning 14 nov
datum: 2026-11-14
följer: 0043
tillåten_skrivning: [byggsten/hjarna/prov/0045/]
---

**Kör efter 0043.** Läs först `byggsten/hjarna/UTMANING.md` (A4, S4) och ägarens formregler ur pass 8 (`karta/videoforandring/harness.md`, sök "Pass 8 del 1", och `video/format/h-anpassa8.mjs`).

## Varför
Produktens slutkropp är kundens personal, och manuset är produkten (ägaren 2 nov). Avsiktsriggen säger att mening ska lagras som skäl, inte som rörelse. Om det är rätt ska ett manus som ger personalen *mål och omständigheter* ("ni tror att ingen ser er när ni tar er egen portion") vara bättre än ett som ger *rörelser* ("ta en stor skopa med spaden och ät direkt"). Ägaren har redan sagt "instruera inte personlighet" och "varje scen behöver känsla, struktur och vad den kräver". Det här provet avgör om skäl är rätt språk för manuset. Om nej ska produkten bära rörelser, och S4 faller.

## Att göra
1. **Tre klipp ur 0043:** gelato, notan och guacamole. Ta två CM-ändringar per klipp ur `forvarld/*/meningar*.json`. Välj en "kroppens sätt" och en "föremål och plats".
2. **Skriv två manusversioner per ändring**, i formatet från `h-anpassa8.mjs` (scener: vad, bild, replik, åtgärd; tight, tillåt, undvik):
   - **R (rörelser):** som i dag.
   - **S (skäl):** varje scen beskriver vad personen tror, vill och prioriterar, med upphovets avsikt för takten ur 0043, och inga rörelser utöver det oundvikliga.
3. **Låst ordning och blindning** som i pass 8b: slumpa A och B per par, lås i `forregistrering.json` med prognos (vilket ägaren väljer, med skäl) innan ägaren ser något.
4. **Ägarens underlag i Miles-form** (`karta/videoforandring/miles/`, se de tidigare passen): engelska, inga tvingade ja/nej, och Miles säger inte valet. Lägg det i `byggsten/hjarna/prov/0045/`. Orkestratorn bokar passet med ägaren. Uppdragstagaren kontaktar inte ägaren.

## Gränser
- Modellanrop bara för att formulera versionerna, högst 0,20 dollar.
- Rör inte `scen/`, `forvarld/`, `app/` eller `video/`.

## Klart när
- Sex par (R och S) med låst ordning och prognos.
- Ett Miles-underlag och en prompt redo för ägaren.
- Analysskriptet förberett, så att ägarens svar kan kodas och jämföras med prognosen direkt.

## Leveransform
`delegat/svar/0045-skal-mot-rorelse-agarens-prov.md`, högst cirka 40 rader.
