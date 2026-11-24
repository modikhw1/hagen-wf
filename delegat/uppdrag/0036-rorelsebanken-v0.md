---
id: 0036
titel: Rörelsebanken v0 och motion matching mot liggarens mål, med hel spegling som första datautökning
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0034
tillåten_skrivning: [forvarld/kropp/, scen/3d/gennedbrytning/, scen/3d/kontrakt/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0035.** Läs `delegat/kontext/vagen.md` först.

## Varför
0034 bevisade ägarens poäng i siffror: kroppen nådde målen (1–2 cm), men utan kunskap om hur människor rör sig blev det en vriden, stel kropp med en arm tvärs över bröstet. Rekommendationen var en egen rörelsebank med motion matching och inlärd IK, tränad på våra egna klipp, eftersom AMASS och de förtränade kontrollerna inte får användas kommersiellt. Det här är steg 1 och första provet av steg 2.

Orkestratorns iakttagelse, att pröva: **att spegla en arm är fel, men att spegla hela kroppen är rätt.** En helt speglad tagning är en naturlig vänsterhänt människa som gör samma sak: bål, höft, huvud och båda armar följer med, och fötterna byter sida. Det är standard som datautökning i motion matching. För "andra handen" kan banken alltså innehålla svaret redan: originalets hela rörelse, speglad, ställd så att handen når kundens hand och tråget. Det dubblar dessutom banken gratis.

Ägarens långsiktiga tråd: de tusen analyserade klippen blir banken. Det här uppdraget ska också säga vad det kostar att komma dit.

## Mål
1. En bank i ett fast format, byggd ur kedjans utdata, med liggarens händelser som etiketter.
2. Motion matching mot liggarens mål, plus en kort IK som landar handen, prövad på "andra handen".
3. Ett mått på vad banken behöver för att växa till hundratals och tusentals klipp.

## Att göra
1. **Formatet** (`forvarld/kropp/BANK.md`): per post MHR-sekvens i världsram efter roträttning, fotkontakter, handens föremål, kvalitetsflagga per segment (ur kedjans kontroll), och etiketter ur liggaren (ram, roll, kroppsdel, mål, förlopp). Hel spegling som egen post, märkt `speglad`.
2. **Bygg v0** ur det som finns: gelato S1 (Dreamina, rättad), b-tilltal och guacamole där kedjan har kroppar, plus speglingarna. Säg exakt hur många segment och sekunder banken har per ram (`ge`, `skopa`, `luta_sig`, `tala` …).
3. **Matchningen.** Frågan är liggarens mål ur `GRANSSNITT.md` (kroppsdel, mål per tid, kontakter). Hitta de segment i banken som bäst passar per fönster, ställ dem på plats (rot och riktning mot målet), blanda mjukt vid fönsterkanter, och landa handen med en kort IK eller optimeringen ur 0034 som sista steg med små ändringar.
4. **"Andra handen" igen.** Samma mått som 0034 (handled till målet, bålens vridning, armbågen, höger arm) och en film bredvid 0034:s prov. Titta själv på h3, h6, h8: ser det ut som en vänsterhänt människa som skopar och ger?
5. **En mening till, för att se att det är allmänt**: guacamole, "titta på servitören hela tiden" (huvud och blick), eller b-tilltal m10, "armarna i kors när han gissar", om banken har något som liknar. Säg rakt om banken är för liten.
6. **Vägen till tusen klipp** (högst en sida i `BANK.md`): vad finns lokalt (`data/analys`, `data/bank`, videofiler), vad kostar det per klipp att få 3D-rörelse genom kedjan (läsning direkt ur originalet där kroppen syns, mot genererad återskapning där den inte gör det), vilka segment som duger utan generering, och ett förslag på första omgång (till exempel 50 klipp) med pris och tid.

## Gränser
- Ingen generativ video eller bild, ingen LLM som modellerar rörelsen.
- Modal: bara om befintliga läsningar måste köras om, högst 1,00 dollar. Ingen massläsning av nya klipp i det här uppdraget; punkt 6 är en beräkning.
- Paket får installeras i `scen/.venv` eller eget venv under `forvarld/kropp/`, med version i svaret.
- Inga data med icke-kommersiell licens (AMASS med flera) i banken. CMU bara om licensen bekräftas, och då med källan angiven.
- Rör inte `app/`, `video/`.

## Klart när
- `BANK.md` med formatet, v0:s innehåll och vägen till tusen klipp.
- Banken v0 på disk.
- "Andra handen" med matchning: mått, film, och tre rader om vad en betraktare ser.
- Den andra meningen, eller ett rakt besked om att banken är för liten.
- Bedömning i högst sex rader: håller motion matching som väg, och vad är nästa steg.

## Leveransform
`delegat/svar/0036-rorelsebanken-v0.md` enligt mallen, högst cirka 70 rader.
