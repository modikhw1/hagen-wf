# Luma mot original: hur läser vår kedja Lumas bilder? (11 nov 2026)

Material: de sex Luma-nyckelbilderna i linjeteckning (S1–S6, `luma/d-dialog-notan/gemini_skikt/`, vattenmärket borttaget) mot originalrutorna på samma tid i `klipp/d-dialog-notan.mp4` (rutorna 36, 110, 167, 213, 277 och 308). Lumas realistiska omstilisering och djupvarianter finns bara som miniatyrer på 120×213 px (`luma/ark/`). De är för små för att mäta på, och Luma-krediterna är slut. Luma-videorna finns inte på disk.

Verktyg: `forbered.py` (par-video, YOLO-pose, Depth Anything V2 Small) och `jamfor.py`. SAM 3D Body kördes på Modal med `ingest/modal_sam3db.py`: 12 bilder på 29 s, ungefär 0,5 s per bild. Föremålen lästes med Gemini 3.5 Flash-Lite, där svaren för Luma-bilderna var cachade sedan 7 nov.

## Mätt

| | S1 | S2 | S3 | S4 servitör | S5 | S6 |
|---|---|---|---|---|---|---|
| Kroppsdrift 2D, SAM (% av kroppshöjd) | 4,3 | 2,3 | 7,5 | 1,4 | 4,4 | 11,5 |
| Pose 3D, ledavvikelse (cm) | 2,6 | 2,0 | 5,3 | 2,6 | 3,3 | 5,7 |
| Längd SAM, Luma / original (m) | 1,31 / 1,28 | 1,41 / 1,37 | 1,32 / 1,25 | **1,75 / 1,76** | 1,40 / 1,38 | 1,31 / 1,24 |
| Avstånd till kamera (m) | 1,46 / 1,50 | 1,40 / 1,38 | 1,46 / 1,50 | 1,77 / 1,79 | 1,39 / 1,37 | 1,46 / 1,50 |
| Djup, rangkorrelation Luma–original | 0,97 | 0,88 | 0,92 | 0,94 | 0,87 | 0,92 |
| Personer funna (YOLO), Luma / original | 1/1 | 1/1 | 1/1 | 1/3 | 1/1 | 1/1 |

Sittande personers längd är höjden på den sittande kroppen, inte den stående längden. Bildpanel: `panel.jpg`, där röda punkter visar Luma och gröna originalet.

## Vad det betyder

- **Kroppen läses lika bra ur Lumas teckning som ur originalet.** SAM 3D Body ger samma kroppsform, samma avstånd (±4 cm) och samma längd. Linjeteckningen förvirrar alltså inte modellen.
- **Där siffrorna skiljer sig har Luma ändrat rörelsen, inte läsningen.** I alla A-tagningar (S1, S3, S6) har Luma gett kvinnan samma knäppta händer, medan hon i originalet gestikulerar med öppna händer. S6 avviker 11,5 %. Det är precis "egna beslut" av videomodellen, och SAM-jämförelsen fångar dem.
- **Servitören är 1,75–1,76 m enligt SAM i båda bilderna.** 1,90 m i dagens kedja kommer alltså från golvsteget, inte från kroppsläsningen. Det stöder slutsatsen att felet sitter i vår mätning av rummet.
- **Rummet är tydligare hos Luma.** Bakgrundsgästerna är borta (S4: 3 personer blir 1), och Gemini hittar fler rumsdrag i teckningarna: fönster, lampor, brickor, pommes, sås. Djupordningen är densamma som originalets (0,87–0,97).
- **Föremålen:** Luma bytte hamburgare mot pizza som promptat, men lade också till pizzabitar och fönster som inte finns i originalet (S2). Teckningen ger fler föremål att läsa, men en del är påhittade.
- **Fötterna:** Luma behöll originalets beskärning, så servitörens fötter syns inte heller där. Breddad bild prövades aldrig med Luma.

## Inte prövat

MoGe-rummet, COLMAP och hela kedjan över tid (Luma gav bara nyckelbilder här), samt de realistiska Luma-varianterna i full upplösning.
