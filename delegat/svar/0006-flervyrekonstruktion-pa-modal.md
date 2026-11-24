---
id: 0006
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
VGGT-1B (Meta) på Modal ger bra brännvidd och rotationer men inte en metrisk ram. **Brännvidd:** S1–S7 kommer ut på cirka 1 070–1 120 px, nära det oberoende 900–1 050 i 0004, och S5 på 1 160 px i stället för COLMAP:s 2 335 (alltså stöd för att avvisa S5:s värde enligt 0009). **Relativ pose:** de fyra grupperna som SIFT mätte (0002) kommer ut med små förflyttningar och rotationer som stämmer med SIFT. **Skala och plan:** inte uppnått (personavstånd ger ±35–50 % mellan tagningar, och golv och disk gick inte att passa som plan med mitt enkla höjdhistogram).

**Körning:** `facebook/VGGT-1B`, 3 olika bildurval (12–88 % av tagningen: 20, 50, 80 %) × 11 tagningar för b-tilltal, och 3 × 4 för guacamole: 45 nyckelbilder, ingen hel video. A100-80GB, 5,2 GPU-sekunder för själva modellen. **Personerna maskades inte** (jag behöll dem som anknytning för skala; det avviker från uppdraget). Faktisk Modal-kostnad kunde jag inte läsa ur min session: containern var uppe ett par minuter inklusive modellhämtning, vilket med A100-pris blir under cirka 0,15 USD, långt under taket 1,00.

### Brännvidd per tagning (px i originalupplösning, median över de tre urvalen; vertikal FOV; reserv 1 024 px = 53,1°)
| tagn | VGGT px (vFOV) | spridning mellan urval | 0004 försvinningspunkter |
|---|---|---|---|
| S1–S4 | 1 072–1 088 (50,4–51,1°) | 17–34 px | 908–1 056 |
| S5 | **1 160 (47,7°)** | 18 | 904 (COLMAP 2 335) |
| S6, S7 | 1 094, 1 121 (50,2°, 49,1°) | 41, 37 | 1 039, – |
| S8, S9, S10 | **1 407, 1 648, 1 415 (40,0°, 34,5°, 39,8°)** | 64, 91, 101 | 1 529, 1 154, 1 753 |
| S11 | 1 312 (42,6°) | 18 | 1 304 |
| guacamole S1, S2 | 1 101, 1 089 (49,9°, 50,4°) | 25, 10 | klippvärde 750 (0009) |
| guacamole S3, S4 | **783, 764 (66,4°, 67,6°)** | 24, 5 | |
Två oberoende metoder (försvinningspunkter och VGGT) ger för S8–S11 en längre brännvidd än reservvärdet, vilket pekar på att S8–S10 verkligen har en annan zoom, eller är dåligt bestämda (brant nedåtfilmade). Guacamole S1 och S3 delar plats (SIFT) men får olika fokal i VGGT, så klippet kan ha rörlig zoom, och 0009:s klippvärde 750 stämmer bara med S3 och S4.

### Relativ pose (normerad mot medianavståndet mellan alla kameror; `analys.md/json`)
| par | VGGT avstånd (3 urval) | rotation | SIFT (0002) |
|---|---|---|---|
| S6–S7 | 0,017 / 0,041 / 0,012 | 2,2 / 2,2 / 1,4° | 2,3° |
| S8–S10 | 0,06 / 0,07 / 0,14 | 1,9 / 1,6 / 5,8° | 0,6° |
| S3–S4 | 0,02 / 0,04 / 0,04 | 6–9° | 5,7° |
| S1–S2 | 0,02 / 0,02 / 0,00 | 4,4–5,2° | 3,6° |
| S8–S9 | 0,16–0,28 | 12–27° | roterad 7–17° |
| S9–S10 | 0,14–0,27 | 12–28° | svag koppling |
| guacamole S1–S3 | 0,026 (cv 1 %) | 6,0–6,2° | 13,3° (E), 5° (H) |
Alla fyra SIFT-grupper och guacamole S1–S3 kommer ut som nästan samma plats, med rotationer som stämmer. Riktningen på de små förflyttningarna är instabil (50–100° spridning), vilket är väntat för så korta baslinjer. Mellan uppställningar är avstånden stabila mellan urvalen (cv 5–25 %).

**Ägarens läsning:** männen på ungefär samma ställe (S1/S2 mot S3/S4): VGGT ger stabilt avstånd 0,47–0,49 (cv 5–8 %), 12–24 gånger längre än inom grupperna, och rotation 16–27°. Alltså **inte samma plats** enligt modellen, men skalan i meter är okänd. Lærke i en vinkel mot vågen (S5 mot S8–S11): avstånd 0,6–0,82 (cv 7–11 %), rotation 14–39° (minst mot S8 och S10), vilket är förenligt med en vinkel mot vågen men inte beviset för det.
**Med rimlig säkerhet:** vilka som delar plats, och att de ligger i skilda uppställningar (stabilt över tre bildurval). **Gissning:** baslinjernas riktning, och alla avstånd i meter.

### Skala, rum och topdown
- **Skala:** personens avstånd (planens läsning) mot VGGT:s djup vid personmasken ger 3,1–3,4 m per modellenhet, men med spridning mellan tagningarna på 27–49 % (cv). Någon andra storlek (diskhöjd) kunde jag inte kontrollera: modellens punktmängd gav ett platt höjdhistogram, så golv och diskens ovansida gick inte att skilja ut med den enkla metoden. Mitt försök är därför inte ett svar på om planen i dag stämmer.
- **Topdown-bilder:** `bilder/topdown_b_q50.png` och `topdown_e_q50.png` (kameror som pilar, punktmängd på golvet). De är grova.
- **Guacamole-kontrollen:** modellen säger samma som SIFT, S1 och S3 delar plats (0,026 mot 0,5–1,3 för övriga par).

## Licens
VGGT-1B och koden i `facebookresearch/vggt` ligger under Metas VGGT-licens för icke-kommersiell forskning. Det är ägarens beslut om resultatet bär. Ett kommersiellt gångbart alternativ att undersöka är Depth Anything 3 (Apache 2.0; en Modal-volym `hagen-rumsbank-da3-apache` finns redan i kontot). Jag har inte prövat det här.

## Bedömning (högst fem rader)
1. Kan bli kedjans **kontroll av lins och kameragrupper** före deklarationen: fokal inom cirka 10 % för S1–S7, stöd för SIFT-grupperna, och ett tredje oberoende vittne mot S5:s 2 335.
2. Är **inte ännu den mätta ramen** (PIPE 6b): skalan är oanvändbar (±35–50 %), planen gick inte att passa, och riktningar för korta baslinjer är gissning.
3. Beslut för ägaren: licensen, och om en andra känd storlek (diskhöjd eller kakelmått) ska mätas för att få meter.

## Ändrade eller nya filer
`scen/3d/ingest/flervy_prov/`: `modal_vggt.py`, `vggt_resultat.pkl` (rådata), `analys.py`, `analys.json`, `bilder/topdown_b_q50.png`, `bilder/topdown_e_q50.png`, `modal_kor1.log`. Inget installerades i `scen/.venv`.

## Kontroll mot "Klart när"
- [x] FOV per tagning bredvid reservvärdet och 0004:s värde, med spridning mellan bildrutor/urval.
- [x] Relativ pose per par mot SIFT-facit och ägarens läsning, med uttalad säkerhet.
- [~] Skala: skalfaktor ur personavstånd (cv 27–49 %), men ingen andra storlek.
- [~] Rummet: golv och disk gick inte att passa som plan med mitt enkla försök.
- [x] Guacamole som kontroll.
- [x] Topdown-bild per klipp (grov).
- [x] Bedömning i högst fem rader.

## Avvikelser
- Personerna maskades inte (jag behöll dem för skalanknytning).
- Bildurvalen är tre tidpunkter per tagning i stället för olika fyra bilder, så "samma pose efter omkörning" är mätt mot tre urval.
- `fokal` för S8–S10 är i båda mina oberoende metoder högre än reservvärdet men svagt bestämd (brant nedåtfilmat), så det är en indikation och inget mått.
