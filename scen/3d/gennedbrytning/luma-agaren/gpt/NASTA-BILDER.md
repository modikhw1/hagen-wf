# Nästa bilder åt ägarens GPT (0023 och 0024, 13 nov)

fal-saldot är slut och Codex står still, så de här fyra bilderna behöver ägarens GPT.
- **En ny konversation per bild.** Lägg in bilderna i den ordning som står och klistra in prompten som den är.
- **Spara resultatet** i samma mapp med det namn som anges.
- **Indata** ligger färdiga under `0024/`.

Efteråt kör uppdragstagaren mätningen. Ägaren behöver inte göra något mer.

## 1. Bara disken — `0024/disk_bara/` → spara som `3_bara_disken.png`
Bild 1: `1_original_ruta000.png`. Bild 2: `2_tom_scen_ruta000.png`.

```
Image 1 and image 2 are the same photo from the same camera. Image 2 has the woman removed.
Make a third image from image 2 that keeps only the ice-cream display counter: its glass, frame, tubs, labels and the front panel.
Remove everything else and replace it with flat light grey: the back wall, the shelves, the coffee machine, the back counter, the floor, the ceiling and any on-screen text.
The counter stays exactly where it is, same size, same perspective, pixel for pixel. Do not move, redraw or tidy the counter.
Where the counter's lower front panel reaches the bottom of the frame, keep it as it is. Do not add a floor.
Same 9:16 framing.
```

## 2. Rummet utan disk — `0024/rum_utan_disk/` → spara som `2_rum_utan_disk.png`
Bild 1: `1_tom_scen_ruta000.png`.

```
Remove the ice-cream display counter from this photo: the glass, the frame, the tubs, the labels and the front panel.
Fill the area where it stood with what is behind it: the floor continuing to the back counter, the lower part of the back counter and its cabinets, at the same perspective and lighting.
Keep everything else exactly as it is, pixel for pixel: the wall, the shelves, the coffee machine, the ceiling, the camera and the framing. Same 9:16. Do not restyle, do not tidy, do not move anything.
```

## 3. Skeden i handen, ruta 0 — `0024/sked_000/` → spara som `3_isolerad_med_sked.png`
Bild 1: `1_original_ruta000.png` (originalet). Bild 2: `2_isolerad_ruta000.png` (hon isolerad, utan sked).

```
Image 2 is the woman from image 1, isolated on light grey with her whole body completed.
Change only her right hand in image 2: she holds the small tasting spoon from image 1 in her right hand, the same way and at the same angle as in image 1.
Everything else in image 2 stays exactly as it is: her position, size, pose, face, clothes, legs, feet, the grey background. Do not add the counter or anything else from image 1.
```

## 4. Skeden i handen, ruta 55 — `0024/sked_055/` → spara som `3_isolerad_med_sked.png`
Bild 1: `1_original_ruta055.png`. Bild 2: `2_isolerad_ruta055.png`.

```
Image 2 is the woman from image 1, isolated on light grey with her whole body completed.
Change only her right hand in image 2: she holds the small tasting spoon from image 1 in her right hand, the same way and at the same angle as in image 1, lowered as if scooping.
Everything else in image 2 stays exactly as it is: her position, size, pose, face, clothes, legs, feet, the grey background. Do not add the counter, the ice cream tubs or anything else from image 1.
```

## Vad som händer sedan
- **Bilderna 1–2:** `k_disk.py` mäter om diskens kanter ligger kvar mot originalet. Det som har tillkommit märks `antagen`: diskens framsida, golvet och bakre bänken.
- **Bilderna 3–4:** `e3_sked.py` passar bilderna mot originalrutan och lägger dem i den kamerafria ramen som `kamerafri_k2/nyckel/kf_000_sked.png` och `kf_055_sked.png`. De används då automatiskt av `d2_video.py k2sn`.
