# Uppdrag: granska väljaren (prioritering av objekt per tagning) och skriv dess rapport

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Svara på svenska. Ändra ingen kod. Skriv bara de två filerna under Leverans.

## Varför

Ägaren vill ha en "väljare" som per scen tar fram de objekt som BÄST och med MINST rörighet förmedlar vad scenen är: personen, det hon håller, det som kännetecknar platsen och inredningen. Regibordet ska sedan kunna förenkla scenen eller lägga tyngd på det viktiga. `rumshjarna/valjare.py` (läs docstringen) bygger en rangordning på egna signaler: hand, kropp, återkomst över tagningar i samma rum, bildposition, skärpa, en liten semantisk prior och V3-röst. Resultatet ligger i `ut/rumshjarna/<klipp>/valjare.json` med `rangordning` och `minsta_mangd` per tagning, och varje val har skäl. Ingen har ännu kontrollerat om valen stämmer med vad en människa ser som scenens mening.

## Material

- Klipp: `duepiani`, `spanjorskan`, `08burgerkebab`, `babasburgers`, `kennysgelato2.0`.
- Väljarens utdata: `ut/rumshjarna/<klipp>/valjare.json`.
- Originalrutor: `ut/rumshjarna/<klipp>/<sid>_orig.png`, för tagningar där personen syns. För övriga tagningar räcker väljarens etiketter och skäl. Bedöm bara tagningar som har en bild.

## Uppgift

1. För varje tagning med originalruta: titta på bilden och skriv själv ned scenens mening i en mening och de 3–5 viktigaste elementen. Jämför med väljarens `minsta_mangd` och topp 5. Markera: rätt, saknas (viktigt men inte valt) och brus (valt men oviktigt).
2. Hitta mönster i felen. Gäller de signalvikter, OneFormer-etiketter (fel klass, sammanslagna instanser), att handen saknas, att rum och objekt blandas ihop eller något annat?
3. Föreslå allmänna förbättringar, inga klippspecifika.

## Leverans

- `ut/agy/rumshjarna/valjare_granskning.json`: en post per granskad tagning `{klipp, sid, mening, viktigast: [...], valjarens_minsta: [...], ratt: [...], saknas: [...], brus: [...]}`.
- `rumshjarna/VALJARE_RAPPORT.md`: metodens kärna i 5 rader, träffsäkerhet (andel tagningar där minsta mängden täcker meningen), de värsta fallen, felmönster och förslag. Max 70 rader.

Sista raden i ditt svar: `KLAR` eller `BLOCKERAD: <orsak>`.
