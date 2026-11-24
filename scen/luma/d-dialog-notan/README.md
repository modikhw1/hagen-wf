# 2,5D-skikt som går att ändra semantiskt: proof of concept (7 nov 2026)

Klipp: hampuslundgren, en dialog om notan (12,8 s, 7 tagningar). Utgångspunkten är Lumas nyckelbildrutor i linjeteckning, som en 1.0-setter. Lumas krediter är slut och Gemini kör på gratisnivån.

Uppspelare: `python -m http.server 5191` i den här mappen, öppna sedan `localhost:5191/spela25d.html`. Sidan läser `scen25d.json` varje sekund. Med `#t=8.2` fryses tiden, och med `&skikt=1` visas skiktens rutor.

## Kedjan (`py/skikt25d.py`)

| Steg | Beroende som valdes | Prövat mot | Varför |
|---|---|---|---|
| Bild per tagning | Lumas nyckelbildruta. När den saknas (S7): källan stiliserad med **ControlNet lineart-annotatorn** och mjuk ton | `cv2.pencilSketch`; lineart med tre tonsteg | pencilSketch blev mörk och smetig, och tonstegen blev blockiga. Mjuk ton på mörka ytor liknar Luma mest. |
| Vattenmärke | Union av märkesmaskerna över alla 17 Luma-bilder, ifyllt med LaMa | Mask per bild | Bokstäverna syntes inte mot ljusa ytor i enskilda bilder. |
| Semantik | **Gemini 3.5 Flash-Lite** (gratis): etikett, kategori, ruta 0–1000, kärna, var saken står | YOLO-World (fritt ordförråd) | YOLO-World missade all mat (pizza, pommes) i linjeteckning. Gemini tar 2–6 s per bild. |
| Masker | **SAM 2.1 tiny** (Ultralytics) med Geminis rutor | Ruta ∩ djup | SAM följer föremålens form. Tar ~4 s per bild på CPU. |
| Person (reserv) | YOLO11-seg | – | Används om Gemini inte ger någon person. |
| Djup | Depth Anything V2 Small | – | Rangkorrelationen mot djup ur källan är 0,88–0,96. |
| Bakgrund | **LaMa** (simple-lama) | OpenCV Telea | Telea smetade ut fläckar där personen stod. LaMa fortsätter väggar och linjer. Tar ~10 s per bild. |
| Rörelse | Källans YOLO-spår: axelmitt, skala, lutning (modulo 180°, högst ±20°) | – | YOLO byter ibland plats på vänster och höger axel, vilket gav 180°-hopp. |

Hela ombygget tar 4–5 min på CPU. Geminis svar cachas i `gemini_skikt/`.

## Datasetet (`scen25d.json`)

- `bibliotek`: personer (A, B, C) och föremål som utklipp, plus en hamburgare stiliserad ur källan, så att Lumas pizzabyte kan ångras.
- `scener[]`: id, ursprunglig tid, längd, takt, vem, replik, handling, utsnitt, kamera (start → slut: x, y, zoom), `rum` (fönster, väggar, bord, stolar med ruta och djup) samt `skikt[]`.
- `skikt[]`: typ (bakgrund, förgrund, person, föremål), roll eller klass, kärna, `fast_vid` (föremål i handen följer personen), z (djup), bild, ruta, flytt, skala, spegel, synlig, rörelse och rörelsestyrka.
- `logg[]`: varje ändring med operation, argument och tid i ms.

## Operationer (`py/scenop.py`)

Operationerna är `byt_foremal`, `flytta`, `dolj`/`visa`, `spegla`, `skala`, `kamera` (även `--mot <skikt>`), `langd`, `flytta_scen`, `duplicera`, `ta_bort_scen`, `rorelse`, `byt_person`, `lagg_till` och `angra`.

- Skikt adresseras semantiskt (`S1:burk`, `S6:A`), så operationerna överlever ett ombygge där numren ändras.
- Varje operation tar 3–16 ms, och uppspelaren visar ändringen inom 1 s.

## Prövade semantiska ändringar (`andringar.sh`, går att spela upp mot en ny bas)

| Begäran | Operationer jag valde | Resultat |
|---|---|---|
| Ångra Lumas pizzabyte hos kvinnan | `byt_foremal roll:A pizzabit → hamburgare` | Syns i S1, S3 och S6, efter rättelsen där det som ligger på en bricka blir eget skikt. |
| Punchline ska landa | `kamera S6 --mot S6:A --zoom 1.35` | Kameran åker in mot ansiktet, med parallax mellan bord och person. |
| Servitören ska titta mot henne och tagningen bli kortare | `spegla S4:C`, `langd S4 1.6` | Fungerar. |
| I kroken: bort med burken, muggen närmare henne | `dolj S1:burk`, `flytta S1:pappmugg` | Fungerar. |
| Förstärk mannens förvirring och avsluta med att kameran åker in | `rorelse S7:B 2.5`, `duplicera S7→S8`, `kamera S8 --mot S8:B 2.2` | Fungerar. |
| Servitören i bakgrunden bakom henne i punchline | `lagg_till S6 personer:C` (x 0.82, fot y 0.60, höjd 0.40, z 0.25, speglad) | Hamnar bakom henne och framför väggen, i rätt djupordning. Placeringen bestämde jag ur rummets ankare och hennes djup. |
| Kvinnans tagningar ska kännas mer stressade | `rorelse ×2` i S1, S3 och S6, kortare S1 och S3 | Fungerar. Tolkningen är min, inte inlärd. |

## Begränsningar

- **Personerna är stela utklipp.** Rörelsen är hela kroppens förflyttning, skala och lutning ur källan. Armar, ansikte och mun rör sig inte. Det skulle kräva att utklippet deformeras efter skelettet, eller fler nyckelbildrutor eller video från Luma.
- **En bild per tagning.** Allt som händer inom tagningen bärs av en enda teckning.
- **Bakgrunden bakom personerna är påhittad av LaMa**, som en slät vägg. Flyttas personen syns den ytan.
- **Stilskillnader.** Den lokala stiliseringen (S7, hamburgaren) syns jämfört med Lumas teckning.
- **Masken för mannen i S5** drar med sig bitar av hand och hamburgare.
- **Geminis etiketter varierar.** I S5 kallas samma sak än "pizzabit", än "hamburgare", eftersom Luma ritade båda.
- **Vattenmärket** tas bort utifrån en fast position. Andra format kräver en ny mask.
- **Översättningen från mening till operationer** gör jag i chatten. Den är inte en inlärd modell. Steget mot Jev vore att lära översättningen ur loggade par av mening och operationer.
