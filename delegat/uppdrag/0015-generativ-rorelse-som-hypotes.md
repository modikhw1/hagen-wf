---
id: 0015
titel: Prov: generativ video hittar på rörelsen, kedjan läser och kontrollerar den
status: utkast   # ÅTERKALLAT 22:35 av orkestratorn, ersatt av 0017. Utför inte.
från: orkestratorn (Fable), efter ägarens resonemang 12 nov kväll
datum: 2026-11-12
följer:
tillåten_skrivning: [scen/3d/genrorelse/]
---

> **Återkallat.** Uppdraget byggde på en feltolkning av ägarens resonemang (ny rörelse vid ändring). Ägaren menade nedbrytning vid ingest. Se `0017-generativ-nedbrytning-vid-ingest.md`. Utför inte detta.

## Mål
Det ska vara känt om en rörelse som inte finns i originalet kan fås fram genom att en generativ videomodell spelar ut den, och kedjan sedan läser kroppen ur det genererade klippet, kontrollerar den och sätter in den i förvärlden. Provfallet är ägarens: i `kand-kennysgelato`, "ta bort det som är innan, och låt personen räcka glassen till den andre".

## Bakgrund
Ägarens resonemang: stacken i dag (bildrutor, SAM 3D Body, deklaration) läser det som finns men kan inte anta hur en kropp fortsätter röra sig, och ett inlärt bibliotek på 1 000+ klipp kommer inte kunna det heller. En generativ videomodell kan. Den ska användas för det den är bra på och inte mer:
- Modellen **föreslår rörelse**. Det gäller som hypotes (`scen/3d/PIPE.md`, Grundregeln: original är sanning, generativt är hypotes).
- Kedjan **läser** rörelsen ur det genererade klippet med samma kroppsläsare som för original, och **kontrollerar** den (GEM-X eller `ingest/vakt.py` flaggar orealistisk rörelse).
- Rum, möbler, föremål och kameror kommer ur förvärlden, inte ur det genererade klippet.
- Två varianter av samma scen, med och utan föremål i handen, kan isolera kroppens rörelse. Bortse från föremålet i första hand.
- Nyckelbilder som styrning: vissa modeller tar start- och slutbild eller flera nyckelbilder (till exempel ruta 1, 10, 20, 30). Förvärlden kan rendera sådana, och originalet har dem.

Luma är provat förut och gav enligt ägaren en klok slutsats om rörelsen, men är begränsat och går inte att planera en kedja kring. En modell med öppna vikter på Modal vore styrbar.

## Underlag
- Tidigare generativa prov: `scen/3d/lasformat/` (`RAPPORT.md`, `luma-paket/STEG2-VIDEO.md`, `genererat_klipp/`, `mat_klipp.py`, `budget.json`), `scen/3d/UTFORSKA-rendering.md`. Läs dem först: vad kördes, vad kostade det, hur mättes det.
- Kroppsläsning på Modal: `scen/3d/ingest/modal_sam3db.py`, `ingest_klipp.py`. GEM-X: `scen/3d/kroppsbank/GEMX-LOGG.md`. Vakten: `scen/3d/ingest/vakt.py`.
- Gelato i kedjan i dag: `scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/` (svar 0013).
- Minnesnot från ägarens tidigare arbete: Seedance 2.5 finns som arbetsgång i ett annat spår (sök `seedance` och `unemployed` i `scen/`).

## Delar
**A. Inventering (inga anrop).** Vilka videomodeller går att nå härifrån i dag, med vilken styrning: startbild, start- och slutbild, flera nyckelbilder, kontrollvideo (pose eller djup), referensperson. Minst: det som redan har nyckel eller skript i repot, och en modell med öppna vikter som går att köra på Modal. Kontrollera uppgifterna mot aktuell dokumentation; modellnamn och förmågor ändras fort. Kostnad och väggtid per 5 sekunder.

**B. Ett prov, två modeller om taket räcker.** Startbild ur originalet (en ruta i gelato där personen håller skeden eller glassen), prompt på engelska som beskriver bara rörelsen: personen räcker den till någon framför kameran. Fast kamera. En körning med startbild, en med start- och slutbild om modellen tar det (slutbilden ur förvärlden med armen framsträckt, eller ur originalet om en sådan ruta finns).

**C. Läs och kontrollera.** Kör det genererade klippet genom kroppsläsaren. Kör vakten eller GEM-X på resultatet. Redovisa: håller identitet och kroppsmått över klippet (benlängder, axelbredd mot originalets läsning), står fötter och höft stilla när de ska, hur många rutor flaggas, och är handens bana rimlig (jämn, når fram, inga hopp).

**D. In i förvärlden.** Sätt den lästa rörelsen på kroppen i gelatos befintliga plan (samma rum, kamera och disk), rendera, och lägg bredvid det genererade klippet. Behövs en ändring i kedjans kod för det: gör det i en kopia under `scen/3d/genrorelse/` och beskriv vad som skulle behöva ändras på riktigt.

**E. Med och utan föremål** om taket räcker: samma körning med prompt utan föremål i handen. Skiljer sig den lästa kroppsrörelsen?

## Gränser
- Bara nya filer under `scen/3d/genrorelse/`. Ingen ändring i kedjans kod.
- Kostnadstak totalt 3,00 dollar för videogenerering och Modal tillsammans. Kontrollera pris före varje generering och kör aldrig om en generering för att "försöka igen" utan att ändra något. Räcker inte taket till alla delar: A, B med en modell, C och D går före E och den andra modellen.
- Endast enstaka bildrutor och korta genererade klipp lämnar maskinen. Inga hela originalklipp.
- Nycklar läses ur miljö eller befintliga nyckelfiler och skrivs aldrig ut. Finns ingen nyckel för en tjänst: hoppa över den och säg det, be inte om en.
- Prompter till videomodeller skrivs på engelska.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Tabellen ur del A.
- Minst ett genererat klipp, dess lästa kropp, och en renderad film ur förvärlden med den rörelsen, med sökvägar.
- Kontrollens utfall i tal (del C), och en bedömning av om vakten eller GEM-X faktiskt skiljer en bra generering från en dålig. Har du bara en generering: säg att det inte går att veta än.
- Titta på resultatet och beskriv det: ser rörelsen i förvärlden ut som den i det genererade klippet, och ser den ut som en människa som räcker fram något.
- Väggtid från prompt till rörelse i förvärlden, uppdelad per steg. Det avgör om detta kan ligga i CM:s chatt eller måste vara ett väntesteg.
- Bedömning i högst sex rader: vilken styrning (startbild, slutbild, nyckelbilder) gav mest, vad som måste finnas för att detta ska bli ett steg i kedjan, och vad som talar emot.

## Leveransform
`delegat/svar/0015-generativ-rorelse-som-hypotes.md` enligt mallen, högst cirka 80 rader, med faktisk kostnad per tjänst.
