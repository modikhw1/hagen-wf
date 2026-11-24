# Färgkodat föremål över tid (0025, rörelse): paket för hand

fal-saldot är slut, så paketet körs för hand. Det kan köras i Ray 3.2 på fal när saldot är påfyllt, eller i Dreamina om modellen tar källvideo och nyckelbilder.

## Indata
- `1_kalla_gelato_S1.mp4`: originalet, 148 rutor, 29,97 fps.
- `nyckel_V1_ruta000.png`, `055`, `112`: variant V1 (ton på plats). Disken är grön #00C853, bakgrunden blå #2962FF och skeden gul #FFD600. Personen och resten är orörda.

## Inställningar
- **Ray 3.2 video-to-video (fal):**
  - `keyframes` = de tre bilderna, `keyframe_indexes` = [0, 55, 112]
  - `resolution` 540p, `duration` 5s, `edit_strength` adhere_1
  - kostnad cirka 0,15 USD
- **Dreamina:** samma tre bilder på 0,00, 1,84 och 3,74 s, källvideon som rörelsereferens, 9:16, 5 s.

## Prompt (engelska)
```
Keep this exact video: the same woman, the same movements, the same camera motion, frame by frame.
Only recolour, in every frame: the ice-cream display counter (glass, metal frame, tubs and front panel) in flat pure green #00C853,
the background behind her (back wall, shelves, back counter, machines, ceiling) in flat pure blue #2962FF,
and the small tasting spoon in her hand in flat pure yellow #FFD600. Flat colour with no texture or shading, exact outlines.
Do not change anything else: not her, not the customer's hand, not the on-screen text.
```

## Därefter
- Svaret sparas som `svar/fargkod_S1.mp4`.
- Tonen trösklas per ruta med samma avstånd som i `../matt.py`. Den gula maskens tyngdpunkt per ruta blir skedens bana i bild, och den gröna maskens kanter per ruta följer disken under kamerans rörelse.

## Vad som alls rör sig
- **Rör sig:** skeden och smakprovet (i hennes hand), kundens hand (gelato, cirka ruta 109–132) och mobilen (guacamole, i hans händer). Alla rör sig med en hand och bakas in i personens lager. Kundens hand saknar person och står utanför listan.
- **Står still:** disken, bakgrunden, baren, stolen och väggen. För dem räcker en ruta, och kamerans rörelse ger resten.
