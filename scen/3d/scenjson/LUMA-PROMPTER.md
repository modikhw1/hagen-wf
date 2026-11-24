# Luma-prov: följer modellen en beordrad ändring?

Ändringen är densamma i alla varianter: **kameran 1,0 m bakåt** (samma höjd och riktning) och **personen vriden 20° åt sin egen högra sida**. Vi mäter resultatet med `matt_andring.py`, som kör SAM och jämför med originalet.

Referensbild i alla varianter: `../lasformat/luma-paket/indata/bild/S1.png` respektive `S4.png`.
Spara som `utfall/a/S1.png`, `utfall/b/S4.png` och så vidare. Skriv krediterna i `../lasformat/luma-paket/logg.md`.

**Kör S4 först.** Där läser mätverktyget guidebilden rätt (avståndet 0,85 m mot beordrade 0,82). S1-guiden är svagare: bordet skymmer, och SAM läste bara cirka 5–9° av vridningen.

Grundregel (först i varje prompt):
```
Keep the same people, same clothes, same pose except the requested turn, same room, same light, same lens. Realistic photo.
```

## a) Siffror

S4:
```
Scene in meters (x right, y up, z forward from camera; origin on the floor under the camera). Camera at height 1.59 m, vertical field of view 53 degrees. The waiter stands 1.73 m from the camera, eyes at 1.76 m height, facing the camera turned 10 degrees. Table at x -0.66, z 2.63; chair at x 0.37, z 1.58.
Change: move the camera to z = -1.0 (one meter straight back, same height and direction). Rotate the waiter 20 degrees to his own right around his vertical axis. Everything else unchanged.
```

S1:
```
Scene in meters (x right, y up, z forward from camera; origin on the floor under the camera). Camera at height 1.45 m, vertical field of view 53 degrees. The woman sits 1.1 m from the camera, eyes at 1.08 m height, facing the camera turned 10 degrees. Table between camera and her, top at 0.8 m height, center z 0.67.
Change: move the camera to z = -1.0 (one meter straight back, same height and direction). Rotate the woman 20 degrees to her own right around her vertical axis. Everything else unchanged.
```

## b) Ord

S4:
```
The camera steps back about one meter, same height, same direction, so we see more of the room around him. The waiter turns about 20 degrees to his own right. Everything else unchanged.
```

S1:
```
The camera steps back about one meter, same height, same direction, so we see more of the table and room. The woman turns about 20 degrees to her own right in her seat. Everything else unchanged.
```

## c) Guidebild

Ladda upp guidebilden som **andra referens**, efter originalbilden:
- S4: `guide/S4_blockout.png`
- S1: `guide/S1_blockout.png`

```
The second image is a 3D layout guide of the new camera position and the person's new orientation. Match its camera distance, framing and the person's turn exactly. Use the first image for everything that should look real: the people, faces, clothes, food and room.
```

Djupvarianterna (`guide/S*_djup.png`) är reserv om Luma inte förstår blockouten.

## d) JSON som bilaga (bara S4)

Bifoga `bilaga/S4_scen_och_andring.json` tillsammans med originalbilden. Prompt efter grundregeln:
```
The attached JSON describes the approximate real-world layout of this photo in meters and a change to apply. Apply the change exactly: new camera position and the waiter's turn. Keep everything else from the photo.
```

## c+d) Guidebild och JSON tillsammans (valfri femte körning, S4)

Bifoga originalbilden, `guide/S4_blockout.png` och JSON-bilagan. Prompt efter grundregeln:
```
The JSON describes the scene in meters and the change. The second image shows the result layout from the new camera. Match the layout and the turn; take the look of people, clothes and room from the first image.
```

Spara som `utfall/d/S4.png` och `utfall/cd/S4.png`.
