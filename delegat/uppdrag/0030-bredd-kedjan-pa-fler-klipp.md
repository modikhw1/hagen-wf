---
id: 0030
titel: Bredd: den generativa nedbrytningen som en körbar kedja, och mening för b-tilltal och guacamole
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0029
tillåten_skrivning: [scen/3d/gennedbrytning/, scen/3d/ingest/, scen/3d/kontrakt/, forvarld/btilltal/ut_0030/, forvarld/guacamole/]
---

**Kör efter 0029.** Läs `delegat/kontext/malbild.md` och `vagen.md` först.

## Varför
Förvärlden ska gälla alla klipp som tas in, inte ett. I dag finns den generativa nedbrytningen som ett trettiotal skript under `scen/3d/gennedbrytning/`, numrerade efter i vilken ordning de skrevs (`a_`, `b_` … `t_`), med parametrar och sökvägar för gelato S1. Varje ny tagning skulle kosta en kväll med en agent. Ägaren har sagt det rakt: "Allt arbete nu är till för att effektivt få ner koncept till mallar i förvärlden."

Det här uppdraget gör två saker: kedjan blir ett steg som går att köra på en tagning med en rad, och meningslagret (relevans och handling) prövas blint på två klipp till. Det andra är det viktigaste provet av om ordförrådet är allmänt. b-tilltal är tal och gissningar utan rörelse värd namnet. Guacamole är två personer, en bar och en mobil, där blicken bär poängen. Båda skiljer sig från glass.

## Mål
1. `ingest_tagning` (namnet fritt) kör den generativa nedbrytningen för en tagning, steg för steg med cache per steg, och stannar rent där en manuell generering behövs.
2. b-tilltal och guacamole har relevanslista och handlingsspår i sina källor, framtagna utan ägarens input.
3. Där ägarens Dreamina-svar finns (guacamole S1, gelato omgång 2), är kroppen inläst genom kedjan.

## Att göra

### 1. Kedjan
- Stegen, i den ordning `STRATEGI.md` landade i: relevans → tom scen och lager (bildmodell, V1/V3-regeln ur 0025) → kamerafri källa → **generering** → tidspassning → läsning → kontroll → roträttning → handfäste → möbler med samspel → handlingsspår → in i källan.
- **Genereringen är ett utbytbart steg.** I dag finns två leverantörer: Dreamina för hand (inget API; kedjan skriver ett paket med `LAS-MIG.md` och väntar på en fil i `svar/`), och Ray 3.2 via fal (API, exakt längd, nyckelbilder på tid; nyckel men inget saldo just nu). Kedjan ska inte veta mer om leverantören än vilket paket den ska skriva och vilken fil den ska läsa.
- **Det som var gelato-specifikt** ska bli parametrar eller läsas ur deklarationen: stående mot sittande (fötter eller säte som ankare, 0027), utzoomning (guacamole 62 %), kamerans rörelse (inåkning mot nästan stilla), föremål i hand.
- Kör kedjan om på gelato S1 från början med tom cache och visa att utfallet är detsamma som 0028 (projektionsfel, h1–h9).
- Skript som blir överflödiga: lämna dem, men skriv i en `gennedbrytning/README.md` vilka som ersatts av kedjan.

### 2. Meningen på fler klipp
- **Relevansen** körs med handling som ny posttyp. 0025 missade kundens hand i alla tre körningarna och kunde inte uttrycka "han tittar på mobilen". Båda är handlingar, inte saker. Låt relevanssteget läsa handlingsspåret och ge poster av formen vem gör vad med vad, med roll. Stryk deklarationens gamla relevansfält som indata (det gav "meny" i stället för mobil).
- **Handlingsspåret** för alla tagningar i b-tilltal och guacamole, med samma ordförråd som gelato. Gränser ur mätning, namn ur modellen (Flash). Där ordförrådet inte räcker: lägg till det minsta allmänna verb som behövs, och säg vilket och varför. Guacamole behöver troligen blick som eget fält.
- **Jämför blint** mot ägarens läsning i `delegat/bilagor/0025/agarens-lasning.md` (öppna efter körningen). Träffar den nu kundens hand och mobilen?
- **In i källorna** för b-tilltal och guacamole, med schemat från 0029. Bakåtkompatibelt med sha256.
- **b-tilltal:s tio meningar** (`forvarld/btilltal/meningar.json`) körs igen genom Jev, nu med mening i tillståndet. Skriv i `forvarld/btilltal/ut_0030/`. Ändras Jevs val, och når fler meningar bild?

### 3. Ägarens genereringar
- Läs `d_video/dreamina-paket/omgang2/svar/` och `guacamole-S1/svar/`. Finns filer där, kör dem genom kedjan: kontroll, tidspassning, roträttning, in i källan. Jämför omgång 2 med första Dreamina-svaret i samma tabell som 0026.
- Finns inga, skriv det och gå vidare. Kedjan ska då stå och vänta på dem med ett kommando ägaren eller nästa uppdrag kan köra.

## Gränser
- Ta före-kopior av den kod i kedjan som ändras (`kontrakt/ut/fore_0030/kod/`).
- Testsviten före och efter, som i 0029.
- Ingen ny videogenerering. Codex: högst sex bilder (lager för guacamole om de behövs), läs kvoten först och lämna minst en tredjedel. Gateway: högst 0,30 dollar (Flash). Jev: högst 0,05 dollar. Modal: läsningar, högst 1,00 dollar.
- Rör inte `app/`, `video/`, `forvarld/btilltal/` utanför `ut_0030/`, eller `forvarld/gelato/`.
- Ordförrådet ska vara litet och allmänt.

## Klart när
- Kedjan körd på gelato S1 med tom cache, samma utfall som 0028.
- `gennedbrytning/README.md`: kedjans steg, kommandot, vad som var gelato-specifikt och nu är parameter, och vilka skript som ersatts.
- Relevans och handling i källorna för b-tilltal och guacamole, med jämförelsen mot ägarens läsning.
- b-tilltal:s tio meningar med och utan mening i tillståndet.
- Ägarens Dreamina-svar inlästa, eller kedjan redo för dem.
- Bedömning i högst åtta rader: hur mycket handpåläggning återstår per nytt klipp, och var.

## Leveransform
`delegat/svar/0030-bredd-kedjan-pa-fler-klipp.md` enligt mallen, högst cirka 90 rader.
