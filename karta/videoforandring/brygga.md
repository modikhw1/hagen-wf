# Bryggan: motorns mätning ↔ analysen av riktiga klipp

3D-motorns tal måste betyda samma sak som analysens tal för riktiga klipp, annars betyder steg 7 i 3D något annat än 7 i biblioteket. Bryggan mäter det, rättar det som går att rätta och säger öppet vad som inte håller ännu.

Öppna `localhost:5180/#brygga`. Kör med `npm run brygga` (allt), `-- --tolka` (tolka om från rådata) eller `-- --rapport` (bara jämförelsen).

## Hur

För varje manus (nu de tio verkligheterna av "Nonna smakar"):

1. **Rendera** bildrutorna i Edge, 360×640 i 10 fps, och koda dem till video (`data/brygga/video/`).
2. **Analysera videon med exakt samma pipeline som biblioteket** (`analys/pipeline.mjs`: Mät, Se och Tolka).
3. **Motorns egen syn** (`src/forandring/motor/syn.js`): det Se-steget skulle ha sett, räknat ur 3D-scenen. Det omfattar 33 MediaPipe-punkter ur skelettet, ansiktsrutor (bara när ansiktet är vänt mot kameran), händer, COCO-saker och kamerans transform från täta punkter på rummets ytor. Allt går genom **samma tolkning**.
4. **Jämför** (`brygga/jamfor.mjs`):
   - per ruta: punkter, kamera utanför övergångar, personer och händer
   - per scen: alla egenskaper, plus motiv och kamera på rutor där båda ser samma sak
5. **Korrektion** (`data/brygga/korrektion.json`): `analys ≈ a + b · motor`, bara där r ≥ 0,5 och n ≥ 20.

## Vad bryggan hittade och rättade

Varje punkt nedan är ett fel i analysen eller motorn som bryggan visade. De flesta gäller också riktiga klipp.

| Fynd | Rättelse |
|---|---|
| Tonade övergångar och whip blev inte scengränser (styrka under 0,3) | Se v4 jämför också rutorna ±0,5 s; `overgang` delar scener |
| Objektdetektorn såg inte dockorna som personer, och storlek skiljde inte riktiga från falska kroppar i biblioteket | Ansiktsdetektor (BlazeFace full range) som andra bevis för en person |
| Kameran: alla stora avvikelser hade låg inlier-andel | Tillförlitlighetsgräns: inl ≥ 0,4 och minst 30 punkter (5 % bortfall i biblioteket) |
| Platta ytor gav för få punkter att följa i renderingen | Lokalen har textur: kakel, trä, puts, tegel, tavlor, hylla |
| Motivets rörelse hade ett brusgolv (stativ: motorn 0,004, analysen 0,15) | Baslinje på 3 rutor med kamerans rörelse dragen genom varje steg |
| Följningen bytte mellan personer, så falska rörelsespikar uppstod | Hopp högst 0,12 och liknande storlek; orimlig fart (>0,6) räknas som avbrott |
| "Okänd" räknades som "stilla" i medel | Okänt är `null`; medel och täckning bara över kända rutor |
| Närbilder blev "objekt" när Pose inte såg kroppen | Ansiktets storlek ger närbild eller extrem närbild |
| Motorns egen kamera blev okänd i närbilder | Täta bakgrundspunkter på alla texturerade ytor |

## Läget (31 okt 2026)

**Håller:**
- kameran per scen: r 0,91, lutning 0,93
- kameran per ruta: dx r 0,82, dy r 0,82, skala r 0,71
- scengränser: 90 %
- motivets rörelse där båda ser personen: r 0,62, lutning 0,79
- tilt, roll, stilla, följer, närhet (`utsnitt_nara`), avstånd från mitten och vridning

**Håller inte ännu:**

| Egenskap | Varför | Vad som rättar det |
|---|---|---|
| Personer, händer, utsnitt per typ, storlek | Analysen ser dockorna i 44 % av rutorna (Pose 62 %, ansikte 42 %, COCO 12 %), framför allt inte i närbilder | Realistiska avatarer på samma skelett, med licens som tillåter kommersiellt bruk |
| Pan och zoom per scen | Följande närbilder där personen fyller bilden: analysen tappar bakgrunden och säger "stilla" | Delvis en verklig gräns. Mer textur hjälper. Riktiga klipp har mer bakgrund |
| Dynamik, montage, händernas fart | Ingen variation i de tio manusen | Uttrycksrummet: fler manus med hopp, inskott och handrörelser |

## Vad det betyder för nästa steg

- **Uttrycksrummet** (tusentals varianter mätta med motorns syn) kan placeras på scenografi-vertikalen med de giltiga egenskaperna, översatta med korrektionen. Det gäller framför allt kameran, som bär vertikalen.
- Egenskaper som inte är giltiga får inte styra urvalet för motorns varianter förrän bryggan håller för dem.
- Avatarerna är nästa stora förbättring av bryggan, inte av mätningen.
