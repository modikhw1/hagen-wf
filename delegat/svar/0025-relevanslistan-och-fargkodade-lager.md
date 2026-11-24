---
id: 0025
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
Svaren för 0023 och 0024 är skrivna, båda med status `blockerat` av fal-saldot. Det som väntar på saldo är utpekat där: `k2s`, `k2sn` och mätningen av skeden. Ägaren har sedan dess skaffat Dreamina, och därför ligger ett körklart paket för 0023 i `scen/3d/gennedbrytning/d_video/dreamina-paket/`.

Alla sökvägar nedan utgår från `scen/3d/gennedbrytning/`.

### Del A, relevanslistan
Allt ligger i [relevans/RELEVANS.md](../../scen/3d/gennedbrytning/relevans/RELEVANS.md): tabellen över underlaget, jämförelsen, stabiliteten och de åtta raderna om var steget hör hemma. `relevans/<klipp>/relevans.json` och `korning_1..3.json` finns för båda klippen. Steget (`relevans_steg.py`) kör Gemini 2.5 Flash genom gatewayen. Gratisnivån nekar Pro och 3.x. De sex körningarna kostade 0,09 USD.

- **Underlaget:**
  - Gelato har appens bedömning (`data/analys`, sållning, e5), men deklarationens relevansfält är tomt.
  - Guacamole saknar appdata men har semantik och ett ifyllt relevansfält.
- **Gelato mot ägarens läsning:**
  - **Träffar:** disken (alltid `ramar`), en enklare bakgrund (`ramar`, förenklad form), skeden (bakas in) och handen (en av tre körningar som egen post).
  - **Missar:** kundens hand, i alla tre körningarna. Vad hon bär kommer heller inte med. "Hon bakom disken" finns bara som `samspel`.
  - **Onödigt:** skärmtexter som `bar`, och den stora skopan ur S2.
- **Guacamole mot ägarens läsning:**
  - **Träffar:** baren (`bar` två av tre gånger).
  - **Missar:** mobilen saknas en gång och blir "meny" två gånger. "Meny" kommer ur deklarationens relevansfält. Att han tittar på mobilen kan formen inte uttrycka.
- **Stabilitet:** meningen, personerna och möblernas roller är stabila. Id-namnen, indelningen i hand och föremål, och kamerans roll skiftar.

### Del B, färgkodade föremålslager
18 bilder gjordes genom Codex, i tur och ordning: V1–V4 för gelato 0, 55 och 112 och guacamole 0, plus A-bild och "rum utan disk".
- **Varför i tur och ordning:** `codex_bild.py` tål inte parallella körningar, eftersom den tar den nyaste bilden och den nyaste sessionen.
- **Kvot:** femtimmarsfönstret gick från 0 till 49 % och veckan från 5 till 13 %. Kvoten räckte, så `gpt-paket/` behövdes inte.
- **Segmenteraren** fick en egen maskvariant (`fargkod/modal_seg_mask.py`, samma modeller och trösklar) och tog 13 GPU-sekunder.
- **Kontaktblad:** `fargkod/blad_<klipp>_<ruta>.jpg` och `blad_disk_och_rum_000.jpg`.
- **Mått:** [fargkod/matt.md](../../scen/3d/gennedbrytning/fargkod/matt.md).

| | Färgen avläsbar | Bilden kvar (utanför tonen, ändrat >40) | Mot segmenteraren |
|---|---|---|---|
| **V1, ton på plats** | ett fält per föremål (1 del, 99–100 %) | 0,3–14 % (mest ruta 55), kant p90 2–9 promille | disk 112: IoU 0,95. Skeden och mobilen hittas av V1 men inte av segmenteraren: den tog terminalen för "phone" |
| **V2, id-karta** | samma som V1, personen i egen färg (IoU 0,82–0,97) | — | samma som V1 |
| **V3, ett föremål** | glassdisken hel och kompletterad i 0, 55 och 112; rummet utan disk visar golvet och bakre bänken | — | **baren omritad helt** (ett annat hörn): oanvändbar |
| **V4, ton på tom scen** | ett fält per föremål | 20–30 % ändrat; hyllor blir flytande fragment | stolen dyker upp (kompletterad) |

- **Över rutor:** samma ton per id i alla rutor. Diskens form följer kameran. I ruta 55 lämnar V1 glassen i tråget ofärgad, men det gör inte ruta 0.
- **In i 3D** (`fargkod/disk_3d.py`, `mobellyft.los` oförändrad, kopia av n06-hand):
  - **Ruta 112:** alla källor ger samma läge, 0,23–0,26 m bort från henne.
  - **Ruta 0:** färgmaskerna flyttar disken 0,57 m mot henne. Samspelet i 0024 pekade åt samma håll men kortare: 0,15–0,4 m. Segmenteraren ger 1,3 m, eftersom den bara fångade en del av disken.
  - **Ruta 55:** strålen når inte ytan.
  - **Slutsats:** en ruta räcker inte. Lyftet behöver flera rutor, eller samspelet som villkor.
- **Rörelse:** fal är tomt. Därför ligger [fargkod/video-paket/LAS-MIG.md](../../scen/3d/gennedbrytning/fargkod/video-paket/LAS-MIG.md) klart, med V1-nyckelbilder vid 0, 55 och 112, prompt och inställningar för Ray 3.2 eller Dreamina. Det som rör sig är bara det som hålls i handen (skeden, mobilen, kundens hand). Möblerna står still, och för dem räcker en ruta.

### Del C
[relevans/UTANFOR-OCH-REDIGERING.md](../../scen/3d/gennedbrytning/relevans/UTANFOR-OCH-REDIGERING.md):
- Gelato S1 har huvudet utanför bild i rutorna 38–91 och är helt borta i ruta 52.
- b-tilltal är delvis utanför i 82–100 % av rutorna.
- Kundens hand försvinner helt i kedjan.
- `data/analys` har `hopp`, `inskott`, `zoomryck` och scener under 0,6 s. I våra klipp finns ingen sådan händelse. Fyra provkroppar är namngivna i filen.

## Bedömning
- **Vilka föremål avgörs först,** av relevanslistan. Färgen görs bara för `bar` och `ramar`.
- **Segmenteraren räcker för det som syns helt och har ett tydligt namn** (personer, väggen, disken i ruta 112). Den är billig: sekunder per ruta.
- **Bildmodellen behövs för tre saker:** det lilla i handen (skeden, mobilen), det skymda (diskens framsida, rummet bakom disken) och en gemensam namngivning över rutor.
- **Regel:** segmenteraren först. V1 där segmenteraren missar ett listat föremål eller ger låg IoU mot V1. V3 bara för möbler som skyms av personen.
- **Variant:** V1, eftersom den håller layouten. V2 bara när personen också ska ha ett id. V4 inte.
- **Pris:** cirka 3 % av femtimmarsfönstret per bild, alltså cirka 10–15 % per tagning för tre till fem nyckelrutor (V1 plus V3 för en möbel). Det motsvarar cirka 1–2 % av veckan.
- **Orkestratorns hypotes håller till största delen.** Avvikelsen är att färgkodningen också behövs för små föremål i handen som syns, eftersom segmenteraren förväxlar dem.

## Ändrade eller nya filer
Under `scen/3d/gennedbrytning/`:
- **`relevans/`:** `relevans_steg.py`, `utanfor.py`, `RELEVANS.md`, `UTANFOR-OCH-REDIGERING.md`, `utanfor.json`, samt per klipp `relevans.json`, `korning_1..3.json`, `prompt_1..3.txt` och `underlag.json`.
- **`fargkod/`:** `kor_codex.py`, `modal_seg_mask.py`, `matt.py`, `disk_3d.py`, `palett.json`, `prompter/`, `codex/` (18 bilder med `.codex.json`), `seg/`, `rutor/`, `matt.json`, `matt.md`, `disk_3d.json`, blad och `video-paket/`.
- **`STRATEGI.md`:** "Steg 0: relevanslistan" och tre rader i "Prövat hittills".
- **Utanför tillåten skrivning, men inom 0023:s:** `d_video/dreamina-paket/`, efter ägarens besked om Dreamina.

## Kontroll mot "Klart när"
- [x] Svar för 0023 och 0024, där det som väntar på fal är utpekat.
- [x] `relevans.json` med tre körningar per klipp, och jämförelsen.
- [x] Underlagstabellen och raderna om var i kedjan.
- [x] Kontaktblad per ruta (V1–V4) och måtten.
- [x] Bedömningen.
- [x] Disken i en kopia av planen.
- [x] Rörelsedelen paketerad (fal tomt).
- [x] `gpt-paket/` behövdes inte, eftersom kvoten räckte.
- [x] `UTANFOR-OCH-REDIGERING.md`.
- [x] `STRATEGI.md`.

## Avvikelser
- **Gemini 2.5 Flash i stället för en starkare modell,** eftersom gratisnivån nekar de andra. Gateway totalt 0,09 USD här och 0,017 USD i 0024.
- **Segmenteraren i en egen maskvariant** (ny fil). Kedjans `modal_segmentera.py` sparar bara rutornas mått. Modal-kostnaden är under cirka 0,05 USD.
- **Skärmtext och kamera färgades inte,** fast listan gav dem `bar`. De är inte föremål i rummet.
- **Kundens hand färgades inte,** eftersom den saknas i listan. Det är listans miss, och den står i jämförelsen.
- **Punkt 2 ur 0024 är gjord som V3** (bara disken, rummet utan disk) i ruta 0. Indata åt GPT i `luma-agaren/gpt/NASTA-BILDER.md` behövs därför bara för skeden.
