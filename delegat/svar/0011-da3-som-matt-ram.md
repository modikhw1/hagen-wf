---
id: 0011
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
DA3 (Apache 2.0) ger fokal och kameragrupper ungefär som VGGT, och dessutom meter, men metern är inte användbar än (spridning 40 % mellan bildurval), och golv och disk gick inte att passa som plan. Personplatserna i den gemensamma ramen ger en användbar ordningsstorlek (männen 0,2–0,3 m ifrån varandra) men med stor spridning. Ramen uppfyller alltså inte kravet "under cirka 10 %".

**Licens (kontrollerad mot Hugging Face i dag):** `depth-anything/DA3-BASE` och `depth-anything/DA3METRIC-LARGE` är båda `apache-2.0` (metadata och modellkortets tabell), och repot ByteDance-Seed/Depth-Anything-3 är Apache-2.0. Modellkortet listar DA3-LARGE, DA3-GIANT och DA3NESTED som CC BY-NC 4.0; de kördes inte. Samma två Apache-modeller och Modal-volym som `3d/rumsbank/modal_da3.py`.

**Körning:** samma 45 nyckelbilder som 0006 (3 bildurval × b-tilltal 11 + guacamole 4), men var och en både med personer och med personerna gråmaskade (ingestens masker, dilaterade 15 px): 12 körningar, 90 bilder. A100-80GB, 13,8 GPU-sekunder för modellerna, 47 s väggtid. Faktisk faktura kunde jag inte läsa; uppskattning under 0,10 USD. Gelato kördes inte.

### Fokal per tagning (px, median över tre urval, med personer / maskade)
| tagn | DA3 med | DA3 maskad | VGGT | försvinningspunkter | reserv |
|---|---|---|---|---|---|
| b S1–S4 | 1 144–1 162 | 1 152–1 165 | 1 072–1 088 | 908–1 056 | 1 024 |
| b S5 | 1 120 | 1 176 | 1 160 | 904 (COLMAP 2 335) | |
| b S6, S7 | 1 154, 1 143 | 1 174, 1 162 | 1 094, 1 121 | 1 039, – | |
| b S8, S9, S10 | **1 609, 1 821, 1 610** (urval 1 293–2 057) | **1 234, 1 235, 1 250** | 1 407, 1 648, 1 415 | 1 529, 1 154, 1 753 | |
| b S11 | 1 256 | 1 187 | 1 312 | 1 304 | |
| guacamole S1–S4 | 989, 1 013, 968, 955 | – | S1/S2 1 100, S3/S4 770 | klippvärde 750 | |
**Guacamole:** DA3 ger **ingen skillnad i zoom** mellan S1/S2 och S3/S4 (955–1 013 px), så VGGT:s uppdelning 1 100 mot 770 bekräftas inte. **b S8–S10:** med personer 1 300–2 060, men maskade 1 234–1 250. Den höga fokalen i S8–S10 beror alltså delvis på att den stora vågen och personen dominerar bilden, och är inte ett säkert mått på zoom. Övriga tagningar ligger på 1 120–1 180 px (S5 stöder återigen att 2 335 är fel).

### Kameragrupper (avstånd i DA3:s metriska enheter, tre urval; rotation)
SIFT-grupperna kommer ut som nära (S6–S7 0,10–0,29 m, 2–3°; S1–S2 0,06–0,35 m, 2–11°; S3–S4 0,10–0,19 m, 4–12°; S8–S10 0,008–0,27 m, 1–36°; guacamole S1–S3 0,59–0,61 m, 0,1–0,7° men 0,6 m är längre än de andra grupperna). Spridningen mellan urval är stor (S8–S10: 0,008 till 0,27 m och 1,3° till 36°), så korta baslinjer är inte pålitliga i meter.

### Skala
DA3 ger en skala per körning (`depth_z` i meter): b 1,42–2,22 (med personer 1,42 / 1,42 / 1,95), guacamole 1,71–3,24. **Spridningen mellan bildurval är cirka 40 % för b och 30–45 % för guacamole**, alltså långt över 10 %. Kontroll mot en känd storlek: guacamole-facit säger 1,73 m mellan bäckenen (S4); DA3 ger 1,05–1,29 m, det vill säga 25–40 % för litet. Diskhöjd och personlängd kunde jag inte mäta (se planen nedan; kroppen är beskuren i alla tagningar).

### Golv och diskyta (RANSAC, gravitation okänd, b S6–S11, personpunkter borttagna)
Golvplanet fick bara 8–11 % av punkterna som inliers och lutar 11–23° mot kamerornas uppvektor. Diskytan (parallell inom 10°) hamnade 0,08–0,47 m ovanför golvplanet (deklarerat 0,82–0,97 m), och vinkeln mellan planen var 4–10°. **Inget av detta duger som mätning.** Golvet syns knappt i tagningarna, så planen går inte att skilja från vägg- och diskpunkter med den metoden. Diskens framkant i golvkoordinater togs därför inte fram.

### Personplatser i den gemensamma ramen (b, DA3 med personer, bildurval q20 / q50 / q80)
| avstånd (m) | q20 | q50 | q80 |
|---|---|---|---|
| A (S1,S2) – B (S3,S4) | 0,19 | 0,25 | 0,28 |
| A – C (S6–S11) | 0,53 | 0,73 | 0,31 |
| B – C | 0,46 | 0,89 | 0,50 |
| C S5 – C S6–S11 (samma person, samma plats) | 0,12 | 0,51 | 0,14 |
Männen på ungefär samma ställe (0,2–0,3 m) **stämmer med ägarens läsning och är stabilt** (spridning 0,09 m). Avståndet till Lærke varierar 0,3–0,9 m och samma plats för Lærke (S5 mot S6–S11) varierar 0,12–0,51 m, så felet i ramen är 0,1–0,5 m. Gissningen 2,3 eller 4,1 m mellan hörnen får alltså ingen mätning här, och DA3 pekar på att personerna står betydligt närmare varandra (under 1 m). Guacamole A–B: 1,05–1,29 m (facit 1,73 m).

### Med och utan personmask
Fokal: S1–S7 ändras under 3 %, S8–S10 med 25–30 % (maskad lägre, 1 234–1 250), guacamole inte tolkad. Skalan ändrar sig inte konsekvent (b q50: 1,42 mot 2,02 maskad). Masken stabiliserar alltså fokalen i de tagningar där personen eller vågen dominerar, men inte skalan.

## Bedömning (högst fem rader)
1. **Kan inte ännu vara kedjans mätta ram.** Fokalen duger som kontroll (inom cirka 15 % av VGGT och försvinningspunkterna för 8 av 11 tagningar i b, och bekräftar att S5:s 2 335 är fel), men skalan varierar 40 % mellan bildurval och planen gick inte att passa.
2. Det som går att ge Gemini som **givet** (i stället för gissat): fokal per klipp ur DA3 + försvinningspunkter, kameragrupper ur SIFT (0010), och att männen står inom cirka 0,3 m från varandra. Avståndet till Lærke och alla meter bör vara hypotes med spridning.
3. För meter krävs en bättre ankarstorlek än den modellen själv ger (diskhöjd eller kakelmått mätt av ägaren), och en plansökning som tar hänsyn till att golvet knappt syns.

## Ändrade eller nya filer
`scen/3d/ingest/flervy_prov/`: `modal_da3.py`, `da3_resultat.pkl`, `analys_da3.py`, `analys_da3.json`, `modal_da3.log`. Inget installerades i `scen/.venv`. Topdown-bild i meter togs inte fram (ramen är för osäker).

## Kontroll mot "Klart när"
- [x] Fokal per tagning för b och guacamole bredvid VGGT, försvinningspunkter och reserv; guacamole S1/S2 mot S3/S4 och b S8–S10 besvarade. Gelato kördes inte.
- [x] Kameragrupper mot SIFT-facit.
- [~] Skala i meter: mätt per körning men spridning 30–45 % (över 10 %); diskhöjd och personlängd gick inte att mäta.
- [~] Golvplan och diskyta: RANSAC kördes men planen blev inte tillförlitliga (inliers 8–11 %).
- [x] Personplatser i gemensam ram med spridning.
- [x] Med och utan personmask.
- [ ] Topdown-bild i meter: inte gjord.
- [x] Bedömning i högst fem rader.

## Avvikelser
- Personlängd mättes inte: huvud och golv syns aldrig i samma tagning. Skalan kontrollerades i stället mot guacamole-facit (1,73 m).
- Gelato kördes inte (taket räckte, men jag prioriterade 0010).
- Jag använde samma RANSAC-parametrar (tolerans 3 cm, 1 500 iterationer) för alla körningar; fler iterationer eller en riktad plansökning kan ge bättre plan.
