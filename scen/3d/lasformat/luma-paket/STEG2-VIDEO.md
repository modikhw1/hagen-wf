# Steg 2: Luma helklipp mot Wan (11 nov 2026)

Ersätter avsnittet "Steg 2" i `README.md`. Sammanhanget står i `../../PIPE.md`.

**Frågan:** kan Luma göra om ett helt klipp utan att lämna det (samma gester, samma tajmning, samma personer), och ger det något som Wan inte ger?

Varianterna "naken" och "regisserad" är borttagna. Alla körningar får briefen, eftersom den nu är ett eget steg i pipen.

## Indata

`indata/video/S4.mp4` (2,8 s, servitören, fötterna utanför bild) och `indata/video/S1.mp4` (2,4 s, kvinnan som gestikulerar).

## Ordning och budget

Cirka 1 050 krediter kvar. Vad en video kostar är okänt, så första körningen sätter budgeten.

| # | Arm | Klipp | Vad det svarar på |
|---|---|---|---|
| 1 | V1 breddat | S4 | Direkt mot Wan A: håller gången, syns fötterna, glider de? |
| 2 | V2 städat | S1 | Håller Luma gesterna över tid, som stillbilden gjorde? |
| 3 | V3 stiliserat | S4 | Läser kedjan en förenklad figur säkrare eller sämre? |
| 4 | V3 stiliserat | S1 | Samma fråga för händer och gester |

Skriv krediterna efter körning 1 i `logg.md`. Kostar den över 350 krediter, kör bara 1 och 2.

## I appen

Bifoga videon. Finns ett läge som utgår från en befintlig video (Modify Video, video-to-video), välj det med starkast följsamhet mot källan. Skriv i loggen vilket läge och vilken modell agenten valde. Behåll 9:16 och klippets längd.

Varje prompt består av tre delar i den här ordningen: **grundregel, brief, arm**.

### Grundregel (alltid först)

```
Use the attached video as the source and transform it. Do not generate a new video from scratch. Keep this exact clip: same people, same movements and gestures frame by frame, same mouth movements, same timing and duration, same camera position and lens, no cuts, no camera motion that is not in the source. Do not add or remove people or objects unless told below. If you cannot keep the motion exactly, say so instead of approximating.
```

### Brief S4

```
Scene: a restaurant. A waiter stands on the floor next to a table where two guests are seated just outside the frame. He wears a black cap backwards, black t-shirt and black trousers. He holds a card terminal at waist height, listens awkwardly and glances to the side.
Keep exactly: the waiter, his face, his hands, the card terminal, his posture and every shift of weight.
Keep simple: tables, chairs, the door at the back right, ceiling ducts, round pendant lamps.
Remove: guests in the background, burned-in subtitles, signs and text.
```

### Brief S1

```
Scene: the same restaurant. A woman with long brown hair and a black cardigan with white buttons sits at a black table facing the camera. She is talking, annoyed and questioning, and gestures with open hands the whole time. Her hands are never clasped and never rest.
Keep exactly: the woman, her face, both hands and every finger position, and on the table a white paper cup with a red logo, a yellow drink can, a burger in paper, fries in a box, a small sauce cup.
Keep simple: tall windows, ceiling ducts, the railing behind her.
Remove: guests in the background, burned-in subtitles, signs and text.
```

### Arm V1 breddat (S4)

```
Zoom out: show a wider view of the same clip so his full body is visible from head to feet for the whole duration, with the floor under him and the legs of nearby tables and chairs. Everything inside the original frame stays unchanged; only add what is outside it. He wears plain black sneakers and stands still on a flat floor; his feet do not slide. Realistic, same light.
```

### Arm V2 städat (S1)

```
Clean realistic version of the same clip. Even, soft light, sharp focus, no motion blur. Do not reframe. Face, hands and food stay exactly as they are in every frame.
```

### Arm V3 stiliserat (S4 och S1)

```
Restyle the clip as a simple, clean 3D animation look: smooth matte surfaces, flat even lighting, plain single-color clothes, clear body outline against an uncluttered background. Keep real human proportions, the same body size and the same hands with five visible fingers. Do not exaggerate, do not make it a cartoon. Do not reframe.
```

## Spara

`utfall/video/V1/S4.mp4`, `utfall/video/V2/S1.mp4`, `utfall/video/V3/S4.mp4`, `utfall/video/V3/S1.mp4`. Flera försök: `S4_b.mp4`. Kopiera agentens egna anmärkningar om avvikelser till `logg.md`; de är underlag för briefen.

## Vad som mäts när utfallen ligger här

Mot originalets SAM-sekvens (`../../ingest/ut/notan-tagningar/S1` och `S4`), ruta för ruta:

- **Posedrift** efter Procrustes per ruta, så att ändrad beskärning inte räknas som drift.
- **Tajmning:** förskjutningen i tid som ger minst drift, och om längden och antalet rutor stämmer.
- **Händer** för sig (S1): det var där stillbilderna drev.
- **Ben och fötter** (V1): rutor med ben i bild, fotkontakt, glidning med `vakt.py`, rå längd mot Wans 1,734 m.
- **Rum:** MoGe-djupets variation över tid mot originalets 2,4 % och Wans 23,1 %.
- **Påhittat:** extra personspår, tillagda föremål.

Riktmärken från Wan-rapporten, som diagnos och inte som krav: överkroppsdrift över cirka 5 px, ofullständiga ben, saknad fotkontakt eller extra personspår talar för att utfallet förkastas.

Jämförelsen med Wan är inte rak. Wan fick behålla originalets personpixlar bakom en mask, medan Luma ritar om dem. Lumas drift är alltså hela modellens drift.

## Resultat körning 1 och 2 (11 nov)

Skript: `mat_video.py` (`forbered`, SAM 3D Body på Modal, `analys`). Rådata: `mat_video/resultat.json`. Paneler: `mat_video/panel_V1_S4.jpg` och `panel_V2_S1.jpg`, där gröna punkter är originalets leder och röda utfallets.

| | V1 breddat, S4 | Wan A, S4 | V2 städat, S1 |
|---|---|---|---|
| Rutor lästa | 85/85 | 85/85 | 73/73 |
| Drift överkropp, median / p90 (px i originalets skala) | 3,4 / 4,1 | 3,0 / – | 1,3 / 1,7 |
| Pose 3D efter Procrustes (cm) | 3,7 | – | 0,5 |
| Händer 3D (cm) | 1,4 | – | 1,0 |
| Ben i bild | 85/85 (original 0/85) | 85/85 | 0/73 (skymda av bordet) |
| Rå längd (m) | 1,768 (original 1,765) | 1,734 | 1,273 sittande (original 1,268) |
| Rotskak p95 (cm) | 0,63 (original 0,74) | annat mått (bålskak 0,36 mot 0,24) | 1,85 (original 1,81) |
| Fötternas rörelse, p90 (cm/ruta) | 0,33 | 0,25 med `vakt.py`, annat mått | – |
| Tajmning | går inte att avgöra, han står nästan still | – | minst drift vid 0 rutors förskjutning |
| Personer (YOLO), utfall / original | 3 / 3 | – | 1 / 1 |

Vad det betyder:

- **Luma höll klippet i båda körningarna.** Längd, antal rutor och bildfrekvens är exakt originalets.
- **V1 är samma metod som Wan.** Luma lade originalramen oförändrad i övre mitten (skala 0,7499, spridning 0,0001 över 85 rutor) och genererade bara ytan runt om. Jämförelsen med Wan är alltså rak, tvärtemot vad som antogs ovan. Luma hamnar på samma nivå: ben i alla rutor, fötter som står still, längd som stämmer med originalets råa läsning.
- **Handledsdriften i V1 (median 8 px, p90 21 px) är troligen läsbrus, inte ändrad rörelse.** Pixlarna i originalramen är oförändrade, men personen är 25 % mindre i bild och SAM ser nu hela kroppen. Händerna i 3D skiljer 1,4 cm.
- **V2 håller gesterna.** 0,5 cm i pose och 1,0 cm i händer över 73 rutor, med öppna, rörliga händer. Det som drev i stillbilderna (knäppta händer) hände inte här.
- **V2 ger inget åt kroppsläsningen**, som redan var bra. Vinsten är en bild utan undertext för rum och föremål, och den är inte mätt.
- I V1 valde ägaren "Zoom-out only", så gäster och undertext ligger kvar. Städning och breddning i samma körning är alltså oprövat.

### V1 genom hela ingestkedjan (samma väg som Wan A)

`ingest_klipp.py … --till rum` på `utfall/video/V1/S4.mp4`, utdata i `mat_video/V1_S4/ingest/`. Sedan `room_metrics.metrics` och `vakt.py`.

| | Original | Wan A | Luma V1 |
|---|---|---|---|
| MoGe-djupets tidsvariation, median | 2,4 % | 23,1 % | **2,1 %** |
| Samma, nedre 40 % av bilden | 2,2 % | 16,6 % | 1,8 % |
| Fotkontakt, rutor (vänster / höger) | fötterna dolda | 84 | 84 / 84 |
| Fotglidning p90 (cm/ruta) | – | 0,25 | 0,40 / 0,35, 0 glidrutor |
| Bålskak p95 (cm) | 0,24 | 0,36 | 1,07 (median 0,10) |
| Servitörens lägsta fot mot valt golv | 14,7–16,3 cm över | 1,9–2,8 cm över | **24,5–26,5 cm under** |
| COLMAP | – | 0/29 | 0/29, fokal antagen |

- **Rummet är stabilt hos Luma, till skillnad från Wan.** Djupet varierar lika lite över tid som i originalet. Förbehåll: måttet räknar bara bakgrundspixlar som är giltiga i alla rutor, och de är färre här (79 000 mot 251 000 hos Wan).
- **Fötterna står still**, men något mer glidning än hos Wan.
- **Golvet stämmer inte.** Kedjan valde golv efter den sittande gästens fot (person 2 ligger −5 till +1 cm), och då hamnar servitörens fötter 25 cm under. Två personer ger alltså två golvhöjder. Orsaken är inte utredd: det kan vara gästens genererade ben, den antagna fokalen eller kedjans golvval.
- **Bålskaket är högre i toppen** (p95 1,07 cm) fast medianen är låg. Inte utrett vilka rutor.

Inte mätt: synliga sömmar, och vad V2 kostade (saknas i `logg.md`).
