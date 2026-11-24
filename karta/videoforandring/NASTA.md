# Läge och nästa steg (1 nov 2026, 00:15)

Läs först [plan.md](plan.md): vägvalet, ägarens korrigering (Rörlighet = fart i iscensättningen) och vad som är gjort. Minnesfilen `feedback-rorlighet-ar-iscensattning` sammanfattar korrigeringen.

## Klart och användbart nu (dev-servern: `cd app && npm run dev`, localhost:5180)
| Adress | Vad |
|---|---|
| `#bedom2d` | Bedömningar på riktig video: samma scen genom två virtuella kameror. **Viktigast att fylla**: ~20 par per klipp. |
| `#v2/<klipp>` | Reglaget på originalvideon (2D), med förklaring (Ändrat / Mätt / Modellens tolkning) och spann per scen. |
| `#v/<klipp>~modell` | Den modellerade 3D-scenen: rummet i 3D, originalbilden på plana ytor, spakarna kamera, agerande (`~a`) och statist i bakgrunden (`~b1`). Kräver att uttrycksrummet är mätt (se nedan). |
| `#bedom/<klipp>~modell` | Bedömningar på den modellerade scenen. |
| `#rekon/<klipp>` | Rekonstruktionen bredvid originalet (fotoprojektion, 84–88 %). |
| `#bank` | Bankens urval med Geminis sållning; ta med / ta inte med. |

Klippen: `b.b.kebab-1779386335747`, `sibylla.mlnlycke-1779209627567`, `bredangs.konditoribageri-1778864292655`.

## Stoppat 1 nov ca 00:30 (kan startas om; det som är klart hoppas över)
Läge vid stoppet: 970 bankklipp nedladdade, 547 sållade, 79 analyserade lokalt, urvalet kört på det sållade. Uttrycksrum ~modell: sibylla och bredäng klara, kebab inte påbörjad.
1. **Bankens nedladdning:** ~740 av ~1 000 förvalda klipp, sedan sållning och urval i samma kedja.
   `cd app && node bank/forurval.mjs --per-profil 20 --hamta && node bank/sallning.mjs && node bank/urval.mjs --mal 300`
2. **Lokal analys av bankurvalet:** 48 av 201.
   `cd app && node analys/kor.mjs --kallor --urval`
3. **Uttrycksrummet för de modellerade scenerna:** sibylla nästan klar; bredäng och kebab återstår (kebabs långa scen tar längst). Filen skrivs först när ett klipp är helt mätt.
   `cd app && node uttryck/kor.mjs --klipp sibylla.mlnlycke-1779209627567~modell` (likadant för de två andra)

## Nästa steg, i ordning
1. **Bedömningar** i `#bedom2d` (och `#bedom/<klipp>~modell` när uttrycksrummet finns). Utan dem är rörlighetsmodellen bara startvikter. Hittills: 2 från ägaren och 10 från Gemini.
2. **Validera Gemini-domaren** mot ägarens bedömningar på samma par:
   `node kalibrering/domare2d.mjs <klipp> --samma-som-manniska`
   Mål ≥ 80 % överens. Därefter hundratals par över banken, sedan träning och korsvalidering per klipp.
3. **Bryggan med fotostil på dockorna**, för att pröva om motorns syn mäter iscensättningsmåtten som analysen. Just nu: `andel_bild` r 0,41 och `momentum` −0,27 med tecknade dockor.
4. **2D-uttryck för bankens analyserade klipp:** `node uttryck/kor2d.mjs <id …>`. Klipp utan rekonstruktion får då ett 2D-reglage och bedömningspar.
5. **Entréer som spak i 3D**, alltså att huvudpersonen kommer in i scenen. Kräver lås så att handlingen bevaras.
6. Skyddsräcken per innehållstyp och takt ur banken, nu när den har fler klipp per typ (60/60/60 i urvalet).

## Kända gränser
- Lugnare än originalet går nästan inte att göra när originalet redan är stilla (72 % av scenerna). Spannet per scen visar det.
- Den modellerade scenens föremål är lådor och plattor i Geminis mått. Diskar som flyttats framför personerna skalas, så att de stämmer från originalets vinkel men inte från alla håll.
- Identiteter slås ihop på klädfärg; kund och personal i svart kan bli samma person.

## Not: Spline (spline.design), föreslaget av ägaren 1 nov
Gemini beskriver Spline så här: ett 3D-verktyg för webben som är lättare än three.js eller Unreal. Man animerar tillstånd (states) visuellt, till exempel A = intim närbild och B = episkt helformat, och Jev väljer vilket tillstånd scenen ska glida till beroende på reglaget.

Min bedömning, ej prövad (uppgifterna om Spline kommer från Gemini och ska kontrolleras):
- **Passar som författarverktyg för förhandsskapade scener:** mallar, standardlokaler eller tillstånd en designer bygger för hand. Jev väljer tillstånd, vilket liknar hur reglaget redan väljer uttryck i kedjan.
- **Passar sämre för det vi har byggt:** våra scener skapas automatiskt ur riktiga klipp (personer, rörelser, kamerabanor och lokal per klipp). Spline-scener skapas i redigeraren, och att bygga dem programmatiskt per klipp är troligen begränsat. Ta reda på vad runtime-API:t (`@splinetool/runtime`) tillåter: att flytta och byta objekt, variabler, events.
- **Möjlig kombination:** Spline för lokalens utseende och tillstånd (rummet, ljuset, rekvisitan), och vår motor eller rekonstruktion för personer och rörelser. Det förutsätter export eller import via glTF, eller att Spline-scenen laddas och styrs från vår kod.
- **Att kontrollera:**
  - Om Spline kan exportera eller importera glTF och three.js-kod.
  - Om mätningen (motorns syn, täckning, pixelmått) går att köra på en Spline-scen, eftersom reglaget kräver mätta uttryck.
  - Licens och pris för kommersiellt bruk i LeTrend.

## Bankurvalet kalibrerat mot ägarens bedömningar (1 nov, efter stoppet)
Ägarens 54 bedömningar i `#bank` (23 med, 13 inte, 18 osäkra) visade vad som räknas som bra träningsdata:

- rekonstruerbart (sållningens rekonbar 4,1 mot 1,9)
- personer i bild nästan hela tiden (0,98 mot 0,75)
- högre engagemang (0,74 mot 0,50)
- mest sketcher

Bort: "annat", montage, texttungt, grafiska layouter och klipp som är för knutna till en verksamhet. Matporr är sekundärt.

Min ändring dagen innan (att 2D-spåret inte skulle straffa mat och montage) gick alltså emot ägaren. Den är ersatt: `lamplighet()` och typvikter i `bank/urval.mjs`. Överensstämmelsen gick från 56 % till 72 % (26 av 36). Urvalet: 188 klipp (85 sketch, 71 direkt tilltal, 19 matporr, 12 provsmakning, 1 annat).

Kvar: de sex oenigheterna gäller **överförbarhet**, alltså om idén går att flytta till en annan verksamhet utan att tematiken ändras (ägarens kommentarer). Lägg till fältet `overforbar` (1–5 plus skäl) i Geminis sållning (`bank/sallning.mjs`), kör om den med `--om` (~1 kr för 547 klipp) och vikta in fältet i `lamplighet()`.
