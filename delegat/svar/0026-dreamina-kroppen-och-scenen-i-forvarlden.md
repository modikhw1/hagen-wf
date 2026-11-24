---
id: 0026
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
Alla sökvägar under `scen/3d/gennedbrytning/`.

**1. Tiden** (`t_tid.py`, utfall i `d_video/dreamina/tid.json` och `tid.jpg`). Dreamina-utfallet har 193 rutor, och läsningen läggs på källans 148 rutor.
- **Metod:** DTW över kamera-oberoende drag: bålens lutning, handledernas läge i bållängder och armbågens vinkel.
- **Steglängd:** minst ett och högst tre steg. Med noll steg frös kroppen i platåer på 30 rutor (`tid_minsteg0.*`).
- **Slut:** fritt.
- **Ut:** `d_video/dreamina_t/`, 148 rutor som kedjan tar emot.

| Mot källan | DTW | linjär |
|---|---|---|
| Lutningens korrelation | 0,88 | 0,81 |
| Handen lägst i h3 (källan: 55) | 58 | 49 |
| Armen halvvägs fram (källan: 90) | 90 | 95 |
| Lutningen halvvägs ned (källan: 14) | 15 | 14 |

- **Tempot** (genereringsrutor per källruta): h1 1,38, h3 1,08, h5 2,67, h6 1,58, h8 1,37. Modellen drog ut stillheten mer än rörelsen.
- **"Armen längst fram" ligger på en platå** och duger inte som vändpunkt. Halvvägspunkten används i stället.

**2. Kroppen** (`h_kontroll.py`, `h2_extra.py`)

| | dagens | a | k | k2 | **Dreamina, tidspassad** |
|---|---|---|---|---|---|
| Hela kroppen i bild | — | 48/148 | 148 | 124 | **148** |
| Benlängd (spridning) | 0,75 (4,8 %) | 0,82 (6,6 %) | 0,82 (1,8 %) | 0,81 (4,6 %) | 0,76 (3,3 %) |
| Rotens hopp, max | 16,5 cm | 4,1 | 2,0 | 4,2 | 12,7 (en ruta) |
| Bålens och höftens största hopp | 7,3 / 8,9° | 2,9 / 3,8 | 3,1 / 2,4 | 2,6 / 2,0 | 2,7 / 4,5 |
| Överkroppen i originalets ram, median och p90 | — | 15,8 / 61,6 | 14,8 / 79,7 | 15,9 / 57,0 | 22,0 / 63,9 |
| Lutningens korrelation; största lutning i 40–70 | 1; 85° | 0,99; 58° | 0,40; 27° | 0,98; 61° | 0,88; **82°** |
| Kontrollen | — | nej | nej | nej (kropp i bild, ben) | **nej (ben 3,3 %, rot 13 cm, p90 64)** |

- **Huvudet är avskuret** i 48 genereringsrutor, motsvarande källrutorna 22–69, med en rak kant precis där källans bildkant går. Läsaren hittar på ett huvud som följer lugnt: huvudpunktens hopp är 1,7 px per ruta mot 1,3 i övrigt. Det lappas inte, och prompten i omgång 2 tar hand om det.
- **Kameran glider.** Fotlinjen flyttar sig från 1121 till 892 px mellan 4 och 7 s, och axelbredden minskar 13 %. Kameran tippar och ser henne uppifrån; hon blir inte större.
- **Handens djup i h3–h4:** handleden går 0,56 m under höften, mot 0,55 i dagens läsning. I scenen landar fingertoppen 0,56 m över golvet, det vill säga i ett 0,35 m djupt tråg.
- **Förvärlden:** [g_forvarld/dreamina/tre_bredvid.mp4](../../scen/3d/gennedbrytning/g_forvarld/dreamina/tre_bredvid.mp4). Hon står upprätt där dagens sitter på huk, och böjer sig ned i rutorna 30–70. Slutet ligger för nära kameran, samma inversfel som i k och k2.

**3. Scenen** (`s_scen.py`, `s_scen/plan.json` och `scen.json`, kopia av n06-hand, kedjans kod oförändrad)
- **Disken:**
  - **Källor**, flytt mot henne: färgmasken V1/V2 i ruta 0 säger +0,57 m, V1/V2 och segmenteraren i ruta 112 säger −0,23 respektive −0,26 m. Ruta 55 gick inte, eftersom strålen inte når ytan.
  - **Val:** tråget som villkor. Fingertoppens lägsta punkt (planruta 29, 0,555 m) ska ligga minst 0,10 m innanför bakkanten.
  - **Utfall:** flytt **0,33 m**, till (0,09; 0,91). Det ligger inom samspelets 0,15–0,4 m från 0024.
  - **Synlighet:** disken syns nu i S1. I n06-hand syns den bara i S2.
- **Tråget:** bas plus fyra kanter (fram 0,20 m, övriga 0,05 m). Djupet är 0,345 m ur handens lägsta punkt (mätt).
- **Skeden:** följer handen genom `handforemal`, men hänger cirka 5 cm från fingrarna i rutorna 45–62. Fästet är mätt mot gårdagens grepp och stämmer inte med Dreamina-kroppens.
- **Bakgrunden:** väggen fanns. En bakre bänk (0,90 × 0,60 m) är tillagd, antagen.
- **Kunden:** antagen i sin helhet, som lådor och en cylinder vid kameran utanför bild. Armen möter skeden i h8 och kommer in från vänster nederkant, som i originalet.
- **Vad som behövs för att göra kunden lika bra som henne:** en egen person ur en egen generering. Antingen en motvinkel ur en annan tagning, eller en bildmodell som bygger ut kundens kropp ur handen, plus en videogenerering och en sekvens som placeras i världen. Dagens sekvensformat bär personens rörelse genom tagningens kamera, och en person utan spår i originalet kräver ett eget kameraoberoende sätt att lägga in rörelsen.

**4. Bär scenen meningen?** Filmen med remsan: [s_scen/film.mp4](../../scen/3d/gennedbrytning/s_scen/film.mp4) (`film_rutor.jpg`, `narbild.jpg`; mått i `mening.json`).

| | h1 | h2 | h3 | h4 | h5 | h6 | h7 | h8 | h9 |
|---|---|---|---|---|---|---|---|---|---|
| Påstående | lutar sig | lutar sig | handen i tråget | rätar på sig | står | handen över kanten | samma | samma, plus kontakt sked–kund | står |
| Utfall | sant | sant | **nästan** (50 %, rutorna 28–33) | sant | sant | sant | sant | sant (kontakt 100 %) | **falskt** |

- **h3:** handen når tråget först när hon har böjt sig klart, och lämnar det tidigare än i originalet.
- **h9:** hon lutar sig fortfarande mot kunden. Spårets "står" och Geminis "skeden släppt" stämmer inte.
- **De fem meningarna** före och efter: [s_scen/MENINGAR.md](../../scen/3d/gennedbrytning/s_scen/MENINGAR.md). Upprepning, tempo och innehåll som id saknas fortfarande. Skopa och mottagare har nu en plats i scenen.

**5. Paketen:**
- [omgang2/LAS-MIG.md](../../scen/3d/gennedbrytning/d_video/dreamina-paket/omgang2/LAS-MIG.md), fyra körningar:
  - 5 s
  - 5 s med en fast fotlinje i källan
  - källan nedsaktad till 8 s
  - Flera bildrutor
  - Alla prompter har tider ur handlingsspåret, huvudet uttryckligen helt, låst kamera och handen till knähöjd.
- [guacamole-S1/LAS-MIG.md](../../scen/3d/gennedbrytning/d_video/dreamina-paket/guacamole-S1/LAS-MIG.md): en person per körning (S1 = kunden). Sex saker skilde sig från gelato:
  - han sitter, med en pall
  - ramen måste zoomas ut till 62 %, och `g_forvarld` saknar den inversen
  - kameran står nästan still
  - handen nere till vänster saknas i masken
  - tiderna är inte mätta, och blicken bär betydelsen, så tidspassningen behöver huvudets riktning som drag
  - Codex nyckelbild följde prompten och inte bildens blick

## Bedömning
- **Dreamina duger som generator i ingesten.** Med tidspassningen ger den hela kroppen i alla rutor och den lutning som ligger närmast originalet. Svagheterna (huvudet, kameran, längden) är prompt- och källfrågor, inte stopp. Att den bara går för hand är en kostnad i väggtid. Ray 3.2 står kvar för exakt längd.
- **Svagaste ledet nu är rotens plats i världen genom inversen.** Kroppen hamnar för nära kameran mot slutet, i k, k2 och Dreamina. Därefter kommer handfästet för föremålet i handen, som inte följer en ny kropp.
- **In i kedjan först:**
  - disken synlig i alla tagningar där den finns
  - möbelns öppning (tråget) som form
  - möbelns läge med samspelet som villkor
  - tidspassningen som steg när generatorn inte håller längden

## Ändrade eller nya filer
Under `scen/3d/gennedbrytning/`:
- **Nya skript:** `t_tid.py`, `h2_extra.py`, `s_scen.py`, `v_mening.py`, `e4_kamerafri.py`, `p_omgang2.py`.
- **Nya mappar:** `d_video/dreamina/`, `d_video/dreamina_t/`, `g_forvarld/dreamina_t/`, `g_forvarld/dreamina/`, `samspel/dreamina*.json`, `s_scen/`, `d_video/dreamina-paket/omgang2/` och `guacamole-S1/`.
- **Ändrad:** `STRATEGI.md`, med tidspassningen, leverantörerna, scenen och fyra rader i "Prövat".

## Kontroll mot "Klart när"
Alla punkter är klara: tidsavbildningen med linjär jämförelse, tabellen och de tre måtten, tre bredvid varandra, filmen med remsan, h1–h9, meningarna, båda paketen, STRATEGI och bedömningen.

## Avvikelser
- **Kunden är en stand-in av lådor, inte en MHR-kropp.** Personsekvensen läggs in genom tagningens kamera ruta för ruta, och en antagen person utan spår skulle kräva att den kompensationen byggs. Det ändrar kedjans kod och är inte gjort.
- **Tidspassningen jämförs mot dagens läsning,** som har påhittade ben bakom disken. Därför används bara överkroppsdrag.
- **Kostnader:** Modal en läsning (193 rutor), uppskattat 0,10–0,20 USD. Codex: tre bilder; femtimmarsfönstret står nu på 59 % efter 0025 och 0026. Gateway och fal användes inte.
