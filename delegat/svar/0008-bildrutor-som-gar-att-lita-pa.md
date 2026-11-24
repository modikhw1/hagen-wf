---
id: 0008
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
Arbetsfördelningen håller: Gemini säger **vad**, en segmenterare säger **var**, och en geometrisk korskontroll fångar de felen som återstår. Segmenteraren (Grounding DINO + SAM 2 på Modal) träffar de avlästa kanterna inom 0–1 promille av bildhöjden där Gemini låg 66–177 promille fel, och spridningen för vågen över S8–S11 halveras (0,92 → 0,42 m). Bordet över S6–S9 och S11 går från 2,32 till 0,32 m när en felidentifiering (S9) flaggas bort av en överlappskontroll.

### Del A: korskontroll utan modell (`korskontroll.md`)
Homografi (SIFT + MAGSAC, personer maskade) för över rutan mellan tagningar som delar kameraplats. Väntat fel för ett föremål nära kameran beräknat ur planens kamerabaslinje: 13 px (S6–S7), 130–220 px (S8–S10) vid bakgrundsplanet på 2,6 m.
| element | par | inliers | IoU | max kantavstånd px | väntat fel px |
|---|---|---|---|---|---|
| disk_C Gemini | S6↔S7 | 596 | **0,21 / 0,19** | 390 / 377 | 13 |
| disk_C avläst rätt kant | S6↔S7 | 596 | **0,93 / 0,84** | 15 / 39 | 13 |
| vågen Gemini | S8↔S10 | 246 | 0,99 / 0,94 | 6 / 33 | 167 |
| vågen Gemini | S8→S9 / S9→S8 | 64 / 51 | 0,70 / 0,23 | 66 / 427 | 220 |
| disk_C, S8↔S9 | | 64 / 51 | 0,0 | 249 / 398 | 130 |
| S11 mot S8, S9, S10 (båda elementen) | | 11–13 | – | – | ingen koppling |
**Kontrollen pekar ut S6 mot S7** (IoU 0,2, kant 380 px mot väntade 13 px) och bekräftar de rättade rutorna. Den kan inte kontrollera S11, som saknar koppling (SIFT 11–13 inliers), och S8–S9 är otydligt (väntat fel 130–220 px, lika stort som avvikelsen).

### Del B: segmentering (Modal, `seg_resultat.json`, `jamfor.md`)
Grounding DINO base + SAM 2.1 hiera-large, prompter `butcher counter. electronic scale. piece of raw meat. white paper.` (namnen ur deklarationen), 4 nyckelbilder per tagning (44 bilder), rutan ur SAM-masken, median över tiden. Bilder med båda rutorna ritade: `bilder/rutor_S6..S11.jpg` (gult/blått Gemini, grönt segmenterare).
| element, tagn | Gemini | segmenterare | avläst kant | fel Gemini / segm. (promille) |
|---|---|---|---|---|
| disk_C S6 | [693,718,933,1000] | [871,0,999,998] | topp 870 | −177 / **+1** |
| disk_C S7 | [790,0,999,997] | [875,0,999,998] | topp 875 | −85 / **0** |
| vågen S8 | [256,0,989,943] | [265,0,939,877] | höger 877 (vågarmen) | +66 / **0** |
| vågen S11 | [457,161,710,570] (bara displayen) | [450,0,982,559] (hela apparaten) | – | IoU 0,34 |
| vågen S9, S10 | [472,0,936,856], [260,0,999,999] | [447,0,934,855], [266,0,989,933] | – | IoU 0,94, 0,91 |
| disk_C S9 | [757,0,1000,1000] | [447,0,934,855] = **vågrutan** | – | felidentifiering |
Avlästa kanter är mina egna avläsningar på ögat ur 0001. `disk_A` fick rutor i S1–S4 (S1 [611,4,867,998], S2 [584,0,872,672], S3 [791,0,999,134], S4 [812,0,999,368]), men S1 ser ut att täcka papperet och inte disken: rutorna är inte kontrollerade. I S9 syns disken knappt, och modellen letade då upp vågen. Överlappskontroll mellan element (bord- och vågruta med IoU ≥ 0,7) flaggar S9.

### Del C: effekt på lyften (utan kompilering; spridning i m, före/efter)
| mått | Gemini (0004) | segmenterare |
|---|---|---|
| disk_C S6,S7,S8,S9,S11 | 2,32 | 1,86 med S9, **0,32** utan den flaggade S9 |
| disk_C S7,S8,S9,S11 (jfr 0004: 0,54) | 0,54 | 1,82 med S9, 0,32 utan |
| vågen S8–S11 (jfr 0004: 0,92) | 0,92 | **0,42** |

## Bedömning (högst fem rader)
1. **Rutorna bör komma från segmenteraren** (Geminis namn som prompt), inte från Geminis `box_2d`, och SAM-masken bär mer (till exempel diskens ovansida som polygon). Det kostar cirka 62 GPU-sekunder för 44 bilder.
2. **Kontroller som ska stoppa en felaktig ruta:** (a) överlappskontroll mellan element, så att bord ≈ våg flaggas (S9); (b) homografiöverföring mellan tagningar som delar kameraplats, som skiljer 0,2 från 0,9 i IoU för S6–S7; (c) elementet som inte syns ska ge `null`.
3. S11 saknar koppling och kan inte korskontrolleras. Där bär bara segmentering och överlappskontrollen.

## Ändrade eller nya filer
`scen/3d/ingest/rutprov/`: `korskontroll.py` (+ `.json/.md`), `modal_segmentera.py`, `seg_resultat.json`, `jamfor.py` (+ `jamfor.json/.md`), `bilder/rutor_S6..S11.jpg`, `modal_kor1.log` (misslyckad första körning) och `modal_kor2.log`. Inget installerades i `scen/.venv`.

## Kontroll mot "Klart när"
- [x] Del A: tabell med IoU och kantavstånd, och svar på om felen pekas ut (S6–S7 ja, S11 går inte att kontrollera).
- [x] Del B: Gemini, segmenterare och avläst kant per element och tagning, och en bild per tagning S6–S11.
- [x] Del B: `disk_A` fick rutor i S1–S4, men de är inte kontrollerade.
- [x] Del C: spridningstabell före och efter.
- [x] Bedömning i högst fem rader.

## Avvikelser
- **Modal-kostnad:** körningen tog 61,7 GPU-sekunder (98 s väggtid). Det blir cirka 0,01–0,02 USD enligt Modals listpris (L4 eller T4), långt under taket 1,00 USD. Den första körningen föll i uppstarten (torch 2.5 räckte inte för transformers, nu torch 2.6). Jag kunde inte läsa den exakta faktureringen från min session.
- **Licenser:** Grounding DINO (`IDEA-Research/grounding-dino-base`) och SAM 2.1 (`facebook/sam2.1-hiera-large`) anges som Apache-2.0 på modellkorten, och `transformers` är Apache-2.0. Jag har inte gjort någon juridisk granskning.
- Grounding DINO returnerar delfraser som `piece` och `white paper`. Jag matchar elementen på delsträng (`counter`, `scale`). `disk_A` och `disk_C` fick samma prompt, så S1–S4 gäller `disk_A` och S5–S11 `disk_C`.
