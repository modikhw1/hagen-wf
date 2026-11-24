# Sammanställning: Blint parvis prov (54 tagningar)

## 1. Utfall per kategori (antal tagningar)

| Kategori | X bäst | Y bäst | Lika | Totalt |
| :--- | :---: | :---: | :---: | :---: |
| **1. Från originalkameran (`original`)** | 20 | 12 | 22 | 54 |
| **2. Rummet vid vridning (`rum`)** | 25 | 28 | 1 | 54 |
| **3. Föremålen vid vridning (`foremal`)** | 20 | 21 | 13 | 54 |
| **4. Helhet för att regissera om (`helhet`)** | 25 | 27 | 2 | 54 |

## 2. God nog som utgångspunkt för omregissering

| Omdöme | X (`god_nog_X`) | Y (`god_nog_Y`) |
| :--- | :---: | :---: |
| **Ja** | 1 | 4 |
| **Delvis** | 22 | 13 |
| **Nej** | 31 | 37 |
| **Totalt** | 54 | 54 |

## 3. Analys av de två metoderna (slumpade som X/Y)

Eftersom X och Y har slumpats per tagning fördelar sig vinsterna jämnt (~50/50) mellan bokstäverna X och Y, men varje par ställer två tydligt skilda rekonstruktionssätt mot varandra:

### Vanligaste fel i vardera metod
- **Djup-mesh direkt ur originalbilden:**
  - Saknar ett slutet golv-/bordsplan; golvet tar slut vid bildkanten eller spricker upp i långa svarta revor och taggiga grå skärvor.
  - Lämnar stora svarta eller grå ocklusionshål i väggar, bänkar och mitt i maten (ofta även där överlagrad text suttit), och tappar helt förgrundsbord i halvbilder (t.ex. `babasburgers`).
  - Originalpersonen (och text/sedlar) ligger kvar som ett platt "spökavtryck" på bakgrundsväggen bakom den blå dockan.
- **Plan-/boxmodell med inpainting och separata objekt:**
  - I komplexa rum (särskilt kök med fläktkåpa och rostfria bänkar som i `duepiani` och `08burgerkebab`) ersätts inredningen av grova enfärgade lila/bruna/grå klossar, och enorma utdragna tak- eller väggskivor skymmer hela kameran vid 50° vridning.
  - Inpaintingen raderar ibland personer som inte fått någon docka (`fratelli/s4`, `s5`) så att väskor och pizzabitar svävar fritt, eller täcker över mat med platta beige/grå polygoner (`duepiani/s10`, `babasburgers/s7`).

### Vad den bättre i varje par fortfarande gör fel
- **Burna föremål** (tallrikar, pizzor på papper, frigolitlådor i händer) saknar antingen 3D-volym och försvinner vid vridning, eller får långa vertikala "kjolar" ned till golvet.
- **2D-grafik i videon** (undertexter, 200-kronorssedlar, skyltrutor) tolkas som fysiska 3D-hinder som antingen stansar grå hål i maten eller bildar svävande block.
- **Bordsföremål vid bildkant** (glas, bestick, dippsåser) kapas, plattas ut mot bordsblockets sidor eller sväljs av bordsplanet.
