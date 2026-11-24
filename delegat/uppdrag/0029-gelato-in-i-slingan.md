---
id: 0029
titel: Gelato S1 in i slingan: mening i källan, regi på handlingar, Jev på gelato-meningar
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0028
tillåten_skrivning: [scen/3d/kontrakt/, scen/3d/gennedbrytning/, forvarld/gelato/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0028.** Läs `delegat/kontext/malbild.md` och `vagen.md` först.

## Varför
Allt sedan 12 nov (0017–0028) har gett gelato S1 en bättre kropp, en scen kring den och två nya sätt att säga vad som händer: relevanslistan och handlingsspåret. Inget av det når produkten. En CM kan i dag inte skriva något till förvärlden som använder det. Slingan Jev → regi → kompilator → bild finns, men bara för b-tilltal, och där stannade sex av tio meningar på begrepp som källan saknade (svar 0014, 0016).

Det här uppdraget är bron. När det är klart ska en CM kunna skriva "hoppa över när hon skopar" om gelato, och se resultatet. Det är också det första provet på om handlingsspåret bär som tillstånd för Jev, vilket var 0024:s öppna fråga ("Hur `handling.json` ska in i källan och tillståndet blir ett eget uppdrag när formen har visat sig bära"). Formen har visat sig bära: sju till åtta av nio segment är sanna i scenen.

## Mål
1. Gelato har en källa (`kalla.json`) där S1 är den nya scenen: kroppen ur Dreamina-genereringen med rättad rot, disken med tråg på sin mätta plats, skeden i handen, bakgrunden och kunden som antagen platshållare. Relevanslistan och handlingsspåret är en del av källan.
2. Regin kan verka på handlingar, inte bara på tagningar och föremål.
3. Tio gelato-meningar, skrivna i förväg, går genom Jev och kompilatorn. Före- och efterbilder visar vad som gick.

## Att göra

### 1. Källan
- Utgå från hur b-tilltal fick sin källa (`kontrakt/kalla_bygg.py`, `kalla_foremal.py`, `ut/b-tilltal-ravara_n06-hand/kalla_0016.json`) och hur gelato byggs i dag (`ingest/ut/kand-kennysgelato-tagningar/`, `kontrakt/ut/` för gelato).
- För in det nya från `gennedbrytning/` utan att kopiera skript in i kedjan i onödan. Där en kopia under `gennedbrytning/` gör något kedjan borde göra (roträttningen, handfästet ur genereringen, möbelns läge med samspelet som villkor, tråget som form, tidspassningen), flytta in det som en funktion i kedjan med prov. Säg för varje sak: inflyttad, eller kvar som indata ur `gennedbrytning/` och varför.
- **Kroppens ursprung** ska stå i källan: vilken generering, vilken tidsavbildning, vilken roträttning. Det är det som gör att en senare ändring kan be om en ny generering i stället för att lappa.
- **Mening i källan.** Utöka schemat med valfria fält, bakåtkompatibelt som i 0016:
  - `semantik.handling` per tagning: segmenten ur `handling.json` (rutor, vem, handling, kroppsdel, föremål, mål, kontakt, hållning, kamera, källa).
  - `semantik.relevans` per klipp: meningen i en mening, och posterna med roll (`bar`, `ramar`, `brus`) och behandling.
  - Rätta det 0024 och 0026 hittade: h9 är "lutar sig mot kunden", inte "står". Kundens hand ska finnas i relevanslistan (den missades i 0025), som `bar`.
- Bakåtkompatibelt: notan, bar, guacamole och b-tilltal ska ge plan med samma sha256 före och efter, med tom cache, som i 0016.

### 2. Regin på handlingar
Nya, små och allmänna operationer i `regi.schema.json` och `kompilera.py`. Inte skrivna för glass. Förslag, ändra om något bättre visar sig:
- `ta_bort_handling` (segment-id): segmentets rutor tas bort ur tagningen. Övergången mellan segmentet före och efter löses enklast möjligt (korsövertoning av kroppen över några rutor, eller håll), och märks i planen. Det är en förvärld, inte slutrendering.
- `tempo_handling` (segment-id, faktor): segmentet spelas långsammare eller snabbare. Tidsavbildningen från 0026 (`t_tid`) visar att genereringen har fler rutor än källan, så långsammare kan ta rutor ur genereringen i stället för att dubblera.
- `upprepa_handling` (segment-intervall, antal): segmenten spelas igen i följd. Märk att andra varvet är samma rörelse.
- `byt_foremal` finns redan (0016, köttbit mot ost). Pröva att den når föremålet i handen i gelato.
- Kontrollen (`kontrollera.py`): en edit som tar bort eller byter en post med relevansroll `bar` ska gå igenom, men planen ska bära en varning: "meningen bärs av X". Det är där relevanslistan gör nytta i slingan: Jev och CM får veta när en ändring river idén.

### 3. Jev och meningarna
- Meningarna står i `delegat/bilagor/0029/meningar.json`. Skrivna före körningen, ändras inte. Kopiera dem till `forvarld/gelato/meningar.json`.
- Kör dem som i `forvarld/btilltal/prov.mjs` (Jev-nyckeln i `app/.env.local`; skriv aldrig ut den). Gör en gelato-variant under `forvarld/gelato/`, rör inte `forvarld/btilltal/`.
- Tillståndet till Jev ska innehålla handlingsspåret och relevanslistan i kort form. Mät tillståndets storlek och Jevs tid som i 0016. Säg om handlingsspåret gjorde routningen bättre: kör meningarna också med ett tillstånd utan handling och relevans, och jämför Jevs val.
- Före- och efterbild (eller kort film där tiden är poängen, som för tempo) för varje mening som går till bild.

## Gränser
- Ta före-kopior av den kod i kedjan som ändras (`kontrakt/ut/fore_0029/kod/`), som tidigare.
- Testsviten: redovisa antal före och efter. Åtta prov faller redan i baslinjen (svar 0016); säg om det är samma åtta.
- Ingen ny bild- eller videogenerering. Jev: högst 0,05 dollar. Gateway: högst 0,10 dollar (Flash) om en mening måste tolkas. Modal: bara om en befintlig läsning måste köras om, högst 0,30 dollar.
- Rör inte `app/`, `video/` eller `forvarld/btilltal/`.
- Egna trösklar är diagnos, inte krav.

## Klart när
- `kalla.json` för gelato med den nya S1, mening i schemat, och bakåtkompatibiliteten visad med sha256.
- De tre nya regi-operationerna med prov, och varningen för `bar`.
- Tabell över de tio meningarna: Jevs val med och utan mening i tillståndet, väntat utfall, vad som nåddes (kompilerad, tillämpad, bild), och vad som saknas.
- Bilder eller korta filmer för de meningar som gick.
- Tillståndets storlek och Jevs mediantid.
- Tillägg i `PIPE.md` och överst i `NASTA.md`.
- Bedömning i högst åtta rader: bär handlingsspåret som tillstånd, vilket begrepp saknas nu mest, och vad som är nästa steg mot fler klipp.

## Leveransform
`delegat/svar/0029-gelato-in-i-slingan.md` enligt mallen, högst cirka 90 rader.
