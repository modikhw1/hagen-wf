# Plan efter granskningen (31 okt 2026)

Två oberoende granskningar (Claude och Codex/gpt-6-astra, `karta/videoforandring/granskning-*.md`) kom fram till samma sak: 3D-rekonstruktionen räcker inte som bas för vertikalen. Den tappar innehåll redan på 5, och världen finns bara sedd från originalkameran. Rörlighetsmodellen har noll bedömningar, och flera mått mäter fel sak.

## Vägval
**Originalvideon i 2D är basen; 3D används selektivt.** De flesta spakar för Rörlighet är 2D-operationer på originalet: omkadrering (beskärning, zoom- och panoreringsbanor), skak och stabilisering. 72 % av bibliotekets scener är filmade med stillastående kamera, så den vanligaste ändringen är just att lägga till eller ta bort kamerarörelse. Källorna har upplösning för cirka 1,6× zoom (1024 eller 1920 i höjd mot analysens 640). Fördelarna:

- 5 är exakt originalet, och 3–7 ser ut som riktiga klipp.
- Varianterna mäts med samma analys, utan dockor.
- Spakarna är exakta och isolerade.
- Bedömningarna görs på riktig video.

3D används för ny vinkel och ändrat agerande, bara där täckningen och innehållet håller.

## Steg
0. **Rätta mätfelen** som granskningen hittade:
   - energi mätt med samma tidssteg överallt
   - korsvalidering grupperad per klipp
   - versionsbundna uttrycksfiler, där gamla filer utan täckning avvisas
   - förklaring som visar exakta parametrar och råa mätändringar, och kallar spakandelarna modellens tolkning
1. **2D-lagret:** en virtuell kamera på originalvideon, med en innehållsvakt (personer och det de håller stannar i bild). Varianterna mäts med samma analys. Hastighet, ramper och klipprytm väntar, eftersom de påverkar repliker och humor och kräver lås.
2. **Acceptans med ägaren:** blind bedömning per scen av 3, 5 och 7 (2D mot 3D) på samma klipp. Innehållsfel ger veto, och sämsta scen redovisas.
3. **Kalibrering:** minst 150 par med flera bedömare. En Gemini-domare (ser video) kontrolleras mot ägarens bedömningar. Korsvalidering per klipp och konto. Kontroll att tillagt flimmer inte belönas.
4. **Banken:** urvalet ska inte straffa mat- och föremålsklipp för 2D-spåret, eftersom 2D fungerar på alla klipp.

## Sluta
- Optimera mot en ensam totalprocent.
- Massproducera kameravarianter utan kontroll.
- Behandla bättre dockor som huvudlösningen.
- Massrekonstruera innan basen bevarar klippets viktigaste innehåll.

## Läge (natten mot 1 nov 2026)
- **Steg 0 klart:**
  - energi mätt på samma sätt
  - korsvalidering per klipp (test i `modell.test.mjs`)
  - versionsbundna uttryck (`MATNING_VERSION`)
  - förklaringen visar *Ändrat* / *Mätt* / *Modellens tolkning*
- **Steg 1 byggt:**
  - virtuell kamera i `src/forandring/manus/kamera2d.js` (zoom 1–1,5×, åka in/ut, panorera, tilta, följa, stabilisera, skak; ankare mitt/huvudperson)
  - mätning i `uttryck/matning2d.js` + `kor2d.mjs`: analysens rådata transformeras genom fönstret och tolkas med samma kod; pixlarna mäts om på de beskurna rutorna; innehållsvakt för ansikten, händer och överkropp; dubbletter tas bort
  - analysens egna kameraord stämmer med spakarna ("in", "pan höger, följer", "ut, handhållen")
  - 2–3 s per scen, 174–192 uttryck per scen, varav 3–180 giltiga
- **Reglaget på originalvideon:** `#v2/<klipp>`.
- **Bedömningar på riktig video:** `#bedom2d/<klipp>`.
- **Maskindomare:** `kalibrering/domare2d.mjs`. Gemini 3 Flash ser båda varianterna som video, ~5 öre per par. Första provet: Gemini och den ohandledda modellen var överens i 3 av 7 par. Modellen behöver alltså bedömningar.
- **Känd gräns:** nedåt (lugnare än originalet) finns lite att hämta i 2D när originalet redan är stilla (72 % av scenerna). Lugnare kräver stabilisering (om originalet skakar), lugnare agerande (3D) eller andra spakar (längre tagningar, hastighet) som behöver lås för repliker och humor.

## Nästa (kräver ägaren)
1. Bedöm ~60 par i `#bedom2d/` för de tre klippen (pilarna; ↓ = lika; mellanslag = hoppa).
2. `node kalibrering/domare2d.mjs <klipp> --samma-som-manniska` dömer samma par, och överensstämmelsen visar om Gemini kan användas i skala (mål ≥ 80 %).
3. Sedan: Gemini bedömer hundratals par över bankens klipp, och modellen tränas och korsvalideras per klipp.

## Ägarens korrigering (1 nov 2026) och ny riktning
3D var inte fel tänkt. Det var meningen att hela scenen skulle vara i flux: vinkel, entréer, momentum och bakgrund. Rörlighet är **fart i iscensättningen** och inte efterbearbetning (skak, zoomeffekter). Skalan är asymmetrisk: det går alltid att bli vildare, men lugnare har ett golv. Reglaget ska kännas rätt inom appens spann och påstår ingen absolut sanning. 2D-lagret är därför mest efterbearbetning. Det behålls för tätare utsnitt och bedömningar på riktig video, men är inte huvudvägen.

Gjort:

- **Iscensättningsmått i analysen** (`tolka.mjs` `iscensattning`, version 13):
  - `andel_bild`: personernas andel av bilden
  - `momentum`: motivets rörelse i kroppslängder per sekund
  - `fard`: bålens förflyttning, spårbyten bortfiltrerade
  - `in_ut`: personer som kommer in eller går ut
  - `bakgrund`: rörelse hos personer utöver huvudpersonen

  På kebab stämmer `andel_bild` med ägarens läsning (0,58 mot 0,11 för scenen där de två är små i bild).
- **Ny vertikaldefinition** i `vertikaler.mjs`: iscensättningen bär vikten, skak och ryck har vikt 0. Gemini-domarens fråga är omskriven på samma sätt.
- **Modellerad scen** `<id>~modell` (`manus-modell.json`):
  - hela rummet byggt i 3D (sidoväggar och tak)
  - originalbilden bara på plana ytor (bakvägg, golv, föremålens fram- och ovansidor)
  - tål nya vinklar; relativa vinklar ±35° och höjd ±10°
- **Spakar i 3D:** kamera, agerande (`~a`, momentum) och en statist som går förbi i bakgrunden (`~b1`, det som händer runt personerna).
- **Spann per scen i reglaget:** golv och tak, med en tydlig rad när målet ligger utanför.

Kvar:

- Bryggan säger att motorns syn inte mäter iscensättningsmåtten som analysen (`andel_bild` r 0,41, `momentum` −0,27). Den troliga orsaken är att analysen sällan känner igen de tecknade Nonna-dockorna. Kör om bryggan med fotostil och pröva igen. Tills dess räknas måtten för 3D ur motorn direkt.
- Bedömningar på den modellerade scenen (`#bedom/<id>~modell`) och på 2D (`#bedom2d`), och därefter Gemini i skala.
- Entréer som spak, alltså att huvudpersonen kommer in i scenen. Den kräver lås så att handlingen bevaras.
