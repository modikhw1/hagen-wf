# Sammanställning: blint parvis prov (54 tagningar)

## 1. Fördelning X / Y / lika per kategori

| Kategori | X bäst | Y bäst | Lika | Totalt |
| :--- | :---: | :---: | :---: | :---: |
| **1. Från originalkameran (`original`)** | 19 | 6 | 29 | 54 |
| **2. Rummet vid vridning (`rum`)** | 15 | 38 | 1 | 54 |
| **3. Föremålen vid vridning (`foremal`)** | 10 | 26 | 18 | 54 |
| **4. Helhet för att regissera om (`helhet`)** | 15 | 37 | 2 | 54 |

*(Observera att X och Y är slumpade per tagning. I 51 av 54 tagningar vinner den metod som bygger rummet med hela plan/boxar, städar bort personer ur bakgrunden och separerar bord/föremål, över den råa djupmeshen.)*

## 2. God nog som utgångspunkt för omregissering

| Bedömning | X (antal) | Y (antal) | Totalt (X + Y) |
| :--- | :---: | :---: | :---: |
| **Ja** | 3 | 6 | 9 |
| **Delvis** | 7 | 24 | 31 |
| **Nej** | 44 | 24 | 68 |
| **Summa** | 54 | 54 | 108 |

## 3. Vanligaste fel i X och Y (och i den sämre metoden)

- **Den sämre metoden per tagning (rå djupmesh):**
  - **Söndertrasat rum vid vridning:** Golv, bänkar och väggar spricker upp i taggiga skärvor och stora svarta eller grå hål där personer eller förgrundsobjekt skymt sikten.
  - **Saknat golv och bord:** I närbilder och restaurangscener svävar dockor och bordsskivor som tunna skal i tomma intet utan golvplan eller bordsben.
  - **2D-spöken av personer och text:** Originalpersonen ligger kvar projicerad på väggen/bänken bakom den blå dockan, och pålagd 2D-text lämnar grå rektangulära hål mitt i maten.

## 4. Vad den bättre metoden fortfarande gör fel

- **Dubblerade föremål från originalkameran (`0°`):** När tallrikar, stekpannor eller läskburkar lyfts ut som egna 3D-objekt ligger de ibland kvar även i bakgrundstexturen eller hamnar på fel djup, vilket ger synliga dubbelkopior (t.ex. `duepiani/s4–s7`, `duepiani/s9–s10`, `spanjorskan/s1`).
- **Skymmande tak- och väggplan i `50h°` (och ibland `35°`):** Stora solida tak-, fläkt- eller väggplan hamnar ibland framför kameran vid kraftig vridning och täcker sikten (t.ex. `duepiani/s5–s7`, `duepiani/s12`, `08burgerkebab/s7`, `fratelli/s5`).
- **2D-grafik tolkas som 3D-hinder:** Pålagda grafikobjekt i videon (som 200-kronorssedeln i `babasburgers/s1` eller textskylten i `blackstone/s1`) byggs som solida 3D-kuber/skärmar mitt i rummet.
- **Grova bänkboxar och extruderade ”kjolar”:** Frilagda matlådor som hålls i händerna får ibland långa enfärgade vertikala kanter nedåt (`08burgerkebab/s1`, `fratelli/s3`), och komplicerade bänkar (t.ex. salladsbuffén i `08burgerkebab/s4–s7`) blir grova enfärgade klossar som kan dölja kantinerna.
