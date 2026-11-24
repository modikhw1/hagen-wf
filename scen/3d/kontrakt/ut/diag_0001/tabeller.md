## Tabell 1. Lösta kameror (gemensam ram = planens världskoordinater, rummets yaw -3,06°)
| tagn | x m | y m | z m | yaw° | pitch° | roll° | FOV° (lins) | deklarerad kamera | m till person C |
|---|---|---|---|---|---|---|---|---|---|
| S1 | -0.02 | 0.25 | 1.40 | 90.0 | -8.6 | 0.0 | 31.4 (64 mm) | kamera_1 | 1.12 |
| S2 | -0.08 | 0.22 | 1.40 | 90.0 | -5.0 | 0.1 | 31.4 (64 mm) | kamera_1 | 1.15 |
| S3 | 0.05 | -0.01 | 1.40 | 90.0 | -7.8 | 0.4 | 31.4 (64 mm) | kamera_1 | 1.38 |
| S4 | -0.12 | -0.05 | 1.40 | 90.0 | -3.1 | -0.5 | 31.4 (64 mm) | kamera_1 | 1.41 |
| S5 | 1.98 | -2.26 | 1.40 | 88.1 | -4.7 | -8.3 | 14.1 (146 mm) | kamera_2 | 3.63 |
| S6 | 2.17 | -0.26 | 1.40 | 90.0 | -2.2 | 0.5 | 31.4 (64 mm) | kamera_3 | 1.62 |
| S7 | 2.17 | -0.18 | 1.40 | 90.0 | -2.8 | -0.0 | 31.4 (64 mm) | kamera_3 | 1.54 |
| S8 | 2.05 | 0.21 | 1.40 | 90.0 | -17.5 | 0.6 | 31.4 (64 mm) | kamera_4 | 1.15 |
| S9 | 2.16 | 0.59 | 1.40 | 89.8 | -17.4 | 1.0 | 31.4 (64 mm) | kamera_4 | 0.77 |
| S10 | 2.18 | 0.09 | 1.40 | 90.1 | -11.1 | -1.1 | 31.4 (64 mm) | kamera_4 | 1.27 |
| S11 | 2.37 | 0.20 | 1.40 | 90.0 | -7.5 | -0.0 | 31.4 (64 mm) | kamera_4 | 1.15 |

## Tabell 2. disk_C lyft ur EN tagnings box (ren geometri, ingen klämning), avstånd på golvet till tre referenser
Referenser: fit = obegränsad robust passning mot alla fem boxar [1.871, 3.037]; slut = vad `mobellyft.los` ger nu efter klämning [1.871, 0.906]; med = median av lyften utan S6 [2.169, 1.042].
| tagn | box [ymin,xmin,ymax,xmax] | lyft x,y | m till fit | m till slut | m till med | fit-rms px | använda kanter |
|---|---|---|---|---|---|---|---|
| S6 | [693, 718, 933, 1000] | 2.79, 2.96 | 0.92 | 2.25 | 2.02 | 332 | vanster,topp,botten |
| S7 | [790, 0, 999, 997] | 2.17, 0.98 | 2.08 | 0.31 | 0.06 | 205 | topp |
| S8 | [724, 0, 1000, 862] | 2.02, 0.78 | 2.27 | 0.19 | 0.31 | 287 | hoger,topp |
| S9 | [757, 0, 1000, 1000] | 2.17, 1.10 | 1.96 | 0.36 | 0.06 | 402 | topp |
| S11 | [736, 0, 1000, 846] | 2.31, 1.23 | 1.86 | 0.54 | 0.23 | 153 | hoger,topp |
Grupper (fullänk, 0,3 m): [['S7', 'S11', 'S9'], ['S6'], ['S8']]
disk_A: inga boxar (detektionen gav tom lista trots att uppsättningen säger S1–S4); ingen lyft möjlig.

## Tabell 3. Vågen lyft ur EN tagnings box (bottenmitt mot disk_C:s ovansida, z=0,9), obeskuret och klämt mot disken
Referens: obegränsad passning mot fyra boxar [2.153, 1.415]; disk_C i planen har mitt [2.2352897949472226, 0.7292386141557334] (y-spann 0.48–0.98).
| tagn | box | lyft x,y | klämd x,y | m obeskuret→fit | fit-rms px | kanter |
|---|---|---|---|---|---|---|
| S8 | [256, 0, 989, 943] | 2.04, 0.73 | 2.04, 0.73 | 0.69 | 198 | hoger,topp,botten |
| S9 | [472, 0, 936, 856] | 2.14, 1.17 | 2.12, 0.83 | 0.25 | 173 | hoger,topp,botten |
| S10 | [260, 0, 999, 999] | 2.17, 0.74 | 2.17, 0.74 | 0.68 | 42 | topp |
| S11 | [457, 161, 710, 570] | 2.26, 1.63 | 2.21, 0.83 | 0.24 | 131 | vanster,hoger,topp,botten |
Grupper (fullänk, 0,3 m): [['S10', 'S8'], ['S11'], ['S9']]
Grupper efter klämning (0,3 m): [['S10', 'S11', 'S8', 'S9']]

## Tabell 4. `mobellyft.los` på en minneskopia av n06-fler (nuvarande kod): disk_C
status=flyttad start=[2.785, 0.906] slut=[1.871, 0.906] klämd=True granskonflikt=True
| tagn | rms före px | rms efter px | kanter | centrumdjup efter m | kameramarginal m | personmarginal m (krav 0,10) | lokal konflikt |
|---|---|---|---|---|---|---|---|
| S6 | 1237 | 1133 | vanster,topp,botten | 1.17 | 0.81 | 0.10 | False |
| S7 | 52 | 4 | topp | 1.08 | 0.73 | 0.10 | False |
| S8 | 2572 | 1065 | hoger,topp | 0.70 | 0.34 | 0.10 | False |
| S9 | ej använd | 73 | topp | 0.31 | -0.04 | 0.10 | True |
| S11 | 2478 | 716 | hoger,topp | 0.70 | 0.35 | 0.10 | False |

## Kontroll: disk_C om S6/S7-boxens övre kant sätts där bordsytan syns i nyckelbilden (avläst på ögat, ca 0,87 av höjden)
S6: box [870,0,1000,1000] -> lyft x,y = 2.18, 0.65
S7: box [875,0,1000,1000] -> lyft x,y = 2.17, 0.68
Personplats C (framfor) = [2.267, 1.3590000000000002]; bordets bakkant får högst ligga 0,10 m framför personen.

## Tabell 5. `foremallyft.los` efter möbellyftet på samma minneskopia
kottbit: status=bevarad föremålet saknar byggbart objekt-id (handhållet eller trasig stöd-kedja) slut=[]
vag: status=flyttad  slut=[2.131, 0.992]
  vag S8: rms före 208 efter 105 px, kanter hoger,topp,botten
  vag S9: rms före 1672 efter 573 px, kanter hoger,topp,botten
  vag S10: rms före 48 efter 42 px, kanter topp
  vag S11: rms före 870 efter 346 px, kanter vanster,hoger,topp,botten

## Tabell 6. Samlad per tagning: avstånd på golvet (m) mellan lyft ur just den tagningens box och det slutliga läget i planen
| tagn | kamera x,y | yaw/pitch/FOV | disk_C | disk_A | vågen (obeskuret / klämt) |
|---|---|---|---|---|---|
| S1 | -0.02, 0.25 | 90/-8.6/31.4 | – | ingen box | – |
| S2 | -0.08, 0.22 | 90/-5.0/31.4 | – | ingen box | – |
| S3 | 0.05, -0.01 | 90/-7.8/31.4 | – | ingen box | – |
| S4 | -0.12, -0.05 | 90/-3.1/31.4 | – | ingen box | – |
| S5 | 1.98, -2.26 | 88/-4.7/14.1 | – | – | – |
| S6 | 2.17, -0.26 | 90/-2.2/31.4 | 2.25 | – | – |
| S7 | 2.17, -0.18 | 90/-2.8/31.4 | 0.31 | – | – |
| S8 | 2.05, 0.21 | 90/-17.5/31.4 | 0.19 | – | 0.27 / 0.27 |
| S9 | 2.16, 0.59 | 90/-17.4/31.4 | 0.36 | – | 0.18 / 0.16 |
| S10 | 2.18, 0.09 | 90/-11.1/31.4 | – | – | 0.26 / 0.26 |
| S11 | 2.37, 0.20 | 90/-7.5/31.4 | 0.54 | – | 0.65 / 0.18 |
