# Luma-paket: vilket utseende läser vår kedja bäst, och håller det över tid?

Frågan gäller **video**. Att SAM 3D Body läser en enskild bild vet vi redan (`../luma/RAPPORT.md`). Det okända är om en videomodell kan göra om ett klipp så att vår kedja läser det **säkrare över tid** (mindre skak, synliga fötter, tydligt rum) **utan att lämna klippet** (samma gester, samma tajmning, samma personer).

Stillbilderna i steg 1 är bara ett billigt sätt att välja kandidater. Domen kommer i steg 2.

Skriv kostnaden i krediter för varje körning i `logg.md`, så att vi ser vad stegen kostar i appen.

---

## Steg 1: stillbilder (välj format)

**Indata:** `indata/bild/S1.png` … `S6.png` är originalrutor ur notan. S1 ligger inne i klippet `S1.mp4` och S4 inne i `S4.mp4`.

**Börja med S1 och S4.** S1 är kvinnan som gestikulerar och testar om gester hålls. S4 är servitören vars fötter inte syns och testar breddning och golv. Kör de tre bästa formaten på S2, S3, S5 och S6 först när vi har sett resultatet.

**Spara som:** `utfall/bild/<format>/S1.png`, till exempel `utfall/bild/F2/S4.png`. Om du gör flera försök: `S4_b.png`, `S4_c.png`.

**I appen:** ladda upp bilden som referens eller bild att ändra, och klistra in prompten. Behåll 9:16. Om appen har **Reframe** eller utvidgning, använd det för F2 och skriv det i loggen.

Alla prompter börjar med samma grundregel, som du klistrar in först:

```
Keep this exact moment: same people, same pose, same hand and finger positions, same head angle, same facial expression, same camera position and lens. Do not add or remove people or objects unless told below.
```

| Format | Vad det prövar | Prompt (efter grundregeln) |
|---|---|---|
| **F1** städat realistiskt | Bättre läsning utan att något stiliseras | `Clean realistic photo of the same scene. Remove burned-in subtitles and all text. Remove background guests and passers-by. Even, soft light, sharp focus, no motion blur. Faces, hands and food stay exactly as they are.` |
| **F2** breddat, hel kropp | Fötter och golv syns, vilket ger golv och längd | `Zoom out: show a wider view of the same moment so the full body is visible from head to feet, including the floor, table legs and chair legs. Everything inside the original frame stays unchanged; only add what is outside it. Realistic, same light.` |
| **F3** djupbild | Läser MoGe och djupet rummet bättre? | `Render this exact scene as a depth map: near surfaces bright white, far surfaces black, smooth grey gradients in between. No textures, no colors, no text. Keep every shape and edge in place.` |
| **F4** skyltdocka | Läser SAM en mindre mänsklig figur säkrare eller sämre? | `Replace each person with a smooth matte light-grey mannequin in exactly the same pose, same proportions and same hand positions. Keep the room, table and food realistic.` |
| **F5** rumsskal med rutgolv | Golvplan och skala | `Same view, same room, but empty of people. Simplify the room to clean surfaces: walls, floor, tables, chairs and counter as simple solid shapes. Put a black-and-white checkerboard on the floor with 50 cm squares, following the floor's perspective.` |
| **F6** färgade ytor (segmentering) | Masker och föremål | `Same scene as a flat-color segmentation image: each person one solid distinct color, floor one color, walls one color, tables one color, each food item and cup its own solid color. No shading, no texture, sharp edges.` |
| **F7a** sidovy | Var personer och bord står i djupled | `The same moment seen from the side, camera turned 90 degrees around the scene at the same height. Same people, same poses, same table and objects. Realistic.` |
| **F7b** ovanifrån | Layout: bord, personer, väggar | `The same moment seen from directly above, like a floor plan photo. Show where each person, table, chair and wall is. Realistic.` |

F3, F6, F7a och F7b är mätverktyg, inte slututseenden. Om Luma vägrar eller blir konstig i något format, skriv det i loggen och gå vidare. Ett format som inte fungerar är också ett svar.

---

## Steg 2: video (det egentliga provet)

> **Ersatt 11 nov av `STEG2-VIDEO.md`.** Texten nedan är kvar som historik.

Kör först när steg 1 är poängsatt. Vi väljer då 1–3 format. Troliga kandidater är F1, F2 och F4 eller F5, men poängen avgör.

**Indata:** `indata/video/S1.mp4` (2,4 s) och `indata/video/S4.mp4` (2,8 s). Använd **Modify Video** med starkast följsamhet, alltså läget som håller sig närmast originalet om appen har en sådan skala (t.ex. "Adhere").

**Två varianter per format**, för att se om Luma klarar sig själv eller behöver hjälp med scenförståelse (den roll Gemini ska ha):

- **naken:** grundregeln plus formatets prompt, men med "moment" utbytt mot "clip": `Keep this exact clip: same people, same movements and gestures frame by frame, same timing, same camera. ...`
- **regisserad:** samma, plus scenbeskrivningen nedan, som först klistras in. (Jag har skrivit den för hand i dag; senare skriver Gemini den.)

S1, regisserad:
```
Scene: woman with long brown hair, black cardigan with white buttons, seated at a black table facing the camera, talking, annoyed and questioning, gesturing with open hands. On the table: a white paper cup with a red logo, a yellow drink can, a burger in paper, fries in a box, a small sauce cup. Behind her: restaurant with tall windows and ceiling ducts. Her hands move a lot; keep every gesture.
```

S4, regisserad:
```
Scene: a waiter with a black cap worn backwards, black t-shirt and black trousers stands in a restaurant, holding a phone or card terminal at waist height, listening awkwardly and glancing to the side. Restaurant: tables and chairs, a door at the back right, ceiling ducts and round pendant lamps, guests seated at the left. He stands on the floor; his feet are just below the frame.
```

**Spara som:** `utfall/video/<format>-naken/S1.mp4` och `utfall/video/<format>-regisserad/S1.mp4`.

**Budget:** 1–3 format × 2 varianter × 2 klipp = 4–12 körningar. Börja med ett format på S4 i båda varianterna. Om något av de två ser ut att hålla klippet, fortsätt.

---

## Vad jag mäter när utfallen ligger här

- **Bild (steg 1):**
  - Kroppsdrift mot originalet med SAM 3D Body.
  - SAM:s längd och avstånd.
  - Djupets rangkorrelation mot originalet.
  - Föremål som Gemini hittar jämfört med originalet: missade och påhittade.
  - I F2: om fötter och golv blir läsbara och om servitörens längd stämmer.
  - I F7: om placeringen stämmer med originalets SAM och MoGe.
- **Video (steg 2):**
  - SAM 3D Body på varje ruta, jämfört med originalets sekvens (`ingest/ut/notan-tagningar/S1` och `S4`): gester, rotbana och tajmning.
  - Skak och fotglidning med `vakt.py`.
  - Om formatet håller sig stabilt mellan rutorna, till exempel att rutgolvet inte flyter.
  - Naken mot regisserad: hjälper scenbeskrivningen?

Ett utfall som läses bättre men driver från originalet räknas som underkänt.
