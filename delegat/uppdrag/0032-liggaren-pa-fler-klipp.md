---
id: 0032
titel: Liggaren på b-tilltal och guacamole, blint, och som steg i kedjan
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0031
tillåten_skrivning: [scen/3d/kontrakt/, scen/3d/gennedbrytning/, forvarld/liggare/, forvarld/btilltal/ut_0032/, forvarld/guacamole/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0031.** Läs `delegat/kontext/vagen.md` först.

## Varför
En liggare skriven för glass bevisar inget. Två klipp med helt annan mening visar om schemat är allmänt:
- **b-tilltal** bärs av tal och gissningar: tre personer gissar vad en köttbit väger, och vågen avgör. Handlingsspåret uttryckte inget av det, och därför nådde ingen mening fler bilder i 0030. En liggare där `gissa` är en händelse med talat innehåll, och `väga` en händelse som avgör, borde bära det.
- **guacamole** bärs av blick och uppmärksamhet: han tittar på mobilen i stället för på den andra. Det missades blint i både 0025 och 0030. Uppmärksamhet som fakta (`tittar_på(A, mobil)` i stället för `tittar_på(A, B)`) är just det en liggare kan säga och ett spår inte kan.

Dessutom: Jev varierar mellan körningar med samma tillstånd. Det måste mätas och hanteras innan förvärlden kan lita på Jev.

## Mål
1. Liggare för b-tilltal och guacamole, framtagna blint med prompten ur 0031, kontrollerade mekaniskt.
2. Liggaren som steg i kedjan (`kedja.py`), efter mening och före källa.
3. b-tilltals tio meningar mot liggaren, fem körningar var, och en regel för hur Jevs variation hanteras.

## Att göra
1. **Blint.** Kör prompten ur 0031 utan ändring på b-tilltal och guacamole, med den starka modellen (du själv, enligt prompten) och med Flash. Öppna `delegat/bilagor/0025/agarens-lasning.md` först efteråt. Fångar liggaren mobilen och blicken, och gissningarna och vågen? Behövde prompten eller schemat ändras för att det skulle gå: säg vad, och kör om blint efter ändringen.
2. **Kontrollen** ur 0031 på båda. Luckor i förvillkor och effekt redovisas.
3. **Kedjan.** Ett steg `liggare` i `kedja.py` som skriver liggaren, kör kontrollen och för in referensen i källan. Leverantören (stark modell via API eller Flash) är en parameter. Finns ingen API-nyckel för en stark modell, ska steget stanna rent med ett paket (prompt plus underlag) som en människa eller en agent kan köra, som Dreamina-steget gör.
4. **b-tilltal, meningarna.** De tio ur `forvarld/btilltal/meningar.json`, fem körningar var, med Jev-ytan ur liggaren. Skriv i `forvarld/btilltal/ut_0032/`. Jämför med 0016 och 0030. Särskilt: m2 ("Låt Morten gissa före Mads") är en ändring av ordningen mellan två gissningar, vilket liggaren nu kan säga.
5. **Jevs variation.** Pröva enkla sätt och välj ett: majoritet av tre anrop, temperatur eller motsvarande om API:t har det, eller att ytan bara visar de alternativ som är lagliga i just den scenen. Mät tid och kostnad. Skriv regeln i `PIPE.md`.
6. **Guacamole, tre meningar** skrivna av dig före körningen, som rör blicken och mobilen (till exempel "låt honom lägga ifrån sig mobilen när hon kommer", "låt honom titta på henne hela tiden"). Spara dem innan Jev körs. Mot liggaren, fem körningar. Utförande behövs inte, bara Jevs val och spridningen.

## Gränser
- Före-kopior, testsvit före och efter, bakåtkompatibelt med sha256, som i 0031.
- Ingen ny bild- eller videogenerering. Jev: högst 0,10 dollar. Gateway: högst 0,30 dollar (Flash). Modal och Codex: nej.
- Rör inte `app/`, `video/`, `forvarld/gelato/`, eller `forvarld/btilltal/` utanför `ut_0032/`.
- Schemat ur 0031 får utökas, inte göras om. Varje tillägg ska vara allmänt.

## Klart när
- Liggare för b-tilltal och guacamole, blint, med jämförelse mot ägarens läsning och kontrollens utfall.
- `liggare`-steget i kedjan.
- b-tilltal: tio meningar × fem körningar, mot 0016 och 0030.
- Regeln för Jevs variation, med tid och kostnad.
- Guacamoles tre meningar med Jevs val och spridning.
- Bedömning i högst åtta rader: är schemat allmänt, vad behövde läggas till, och var står slingan nu för tre klipp.

## Leveransform
`delegat/svar/0032-liggaren-pa-fler-klipp.md` enligt mallen, högst cirka 80 rader.
