# Vägen: var vi står och vart nästa steg leder

Skriven av orkestratorn 2026-11-13 kväll. Läs efter `malbild.md`. Målbilden säger vad förvärlden ska vara. Den här filen säger var på vägen varje uppdrag ligger, så att uppdragstagaren kan avgöra själv vad som är viktigt när uppdraget inte säger det.

## Produkten i en mening
En CM skriver "hoppa över när hon skopar" eller "flytta det till en foodtruck", och förvärlden visar inom någon sekund en ändrad, trovärdig version av klippet, för vilket klipp som helst som har tagits in.

## Slingan som ska fungera
1. **Ingest** bryter ned klippet till en källa (`scen/3d/kontrakt/kalla.schema.json`): rum, möbler, föremål, personer, kropp per tagning, kamera, och nu också mening (relevans och handlingsspår).
2. **Jev** läser källan som tillstånd och översätter CM:s mening till en regi (`regi.schema.json`) på under en sekund.
3. **Kompilatorn** (`kontrakt/kompilera.py`) gör källa + regi till en plan, och **renderingen** gör planen till bild.

Den slingan finns och fungerar på b-tilltal (`forvarld/btilltal/`, svar 0014 och 0016): tio meningar, fyra går hela vägen till bild. De andra stannade på begrepp som källan saknade, inte på geometri.

## Var vi står (13 nov kväll)
- **Kroppen** går nu att få hel ur en generering (Dreamina, tidspassad, roten rättad i 0027). Det är gjort för en tagning, gelato S1, med skript under `scen/3d/gennedbrytning/`.
- **Meningen** finns i två nya former, båda prövade på gelato S1: relevanslistan (`relevans/`, 0025) och handlingsspåret (`handling/S1/handling.json`, 0024). Sju till åtta av nio segment är sanna i scenen.
- **Scenen** kring kroppen (disk med tråg, sked, bakgrund, kund som platshållare) finns, men bara i kopior under `gennedbrytning/`, utanför källan.
- **Ingenting av detta når slingan än.** Jev kan inte se handlingsspåret, kompilatorn kan inte hoppa över ett segment, och gelato har ingen källa med den nya kroppen.

## Läget 13 nov sent (efter 0028–0030)
- Gelato är i slingan (`kalla_0029.json`): "hoppa över när hon skopar", "långsammare" och "en sekund längre" når bild. Kedjan för den generativa nedbrytningen körs med ett kommando (`gennedbrytning/kedja.py`). b-tilltal och guacamole har handlingsspår och relevans i källan.
- Allt som stannade, stannade på att tillståndet **beskriver** handlingar men inte vet vad de **betyder**: vad handen bär, vem som tar emot, vilka handlingar som hör ihop, vad som får ändras. Jev varierar också mellan körningar.
- **Ägarens beslut 13 nov sent: liggaren.** Intelligensen ligger i en liggare som en stark modell skriver vid ingest (roller, förvillkor och effekt, förlopp, vad som bär meningen, frihetsgrader och spridning). Jev väljer bara bland lagliga ändringar som liggaren har räknat ut, och säger `ingen_passar` annars; då tar en stark modell den långsamma vägen. Utförandet har tre nivåer: direkt i 3D, rörelseredigering, ny generering. Förebilder: Smart Objects (UE5, The Sims), GOAP/HTN, motion warping. Uppdrag 0031 (gelato, "ge glassen med andra handen") och 0032 (b-tilltal, guacamole).

## Nästa steg, i ordning (skrivet före 0028–0030, steg 1–3 är gjorda)
1. **Stäng 0027** (kamerahöjden). Liten sak, men bilden måste bära det mätningen säger.
2. **Gelato S1 in i slingan (0029).** Det nya ska in i källan, regin ska kunna verka på handlingar, och Jev ska få gelato-meningar. Det här är steget som gör dagens arbete till produkt. Det viktigaste uppdraget just nu.
3. **Bredd (0030).** Samma ingest på fler tagningar och klipp utan handpåläggning: en körbar kedja i stället för skript per steg, relevans och handlingsspår på b-tilltal och guacamole, och den genererade kroppen där ägarens Dreamina-svar finns.
4. **Sedan, inte nu:** kunden och andra personer ur egen generering, mimik, miljöbyte, rörelsebibliotek, och träning av förvärlden på många permutationer.

## Hur ett uppdrag vägs
- Ger det här mening åt en ändring senare? Ett mått som blir bättre men som ingen CM-mening kan använda är lågt prioriterat.
- Gäller det nästa klipp? En lösning skriven för glass är ett prov, inte ett steg.
- Når det slingan? Det som stannar i en kopia under `gennedbrytning/` är ett experiment tills det står i källan.
- Ser man det? Ett påstående som är sant i mätningen men inte i bilden är inte klart.

## Ägarens besked 13 nov kväll (gäller före allt ovan om nivåer)
- Generativ video är **bara** till för att återskapa originalet 1:1 vid ingest. Aldrig alternativa versioner. "Nivå 3, ny generering" som utförande av en CM-ändring är struken.
- Jevs ändringar ska vara blixtsnabba ändringar i 3D utan generativ AI. Kroppen ska anpassa sig i sin helhet (byta arm = bålen roteras, nytt sätt att skopa), vilket kräver en kroppsbunden intelligens: en kontroller tränad på rörelsedata. Liggaren ger mål, kontrollern ger rörelse, Jev väljer. De tusen analyserade klippen kan bli kontrollerns träningsdata. Uppdrag 0034 (kroppen) och 0035 (1:1-återskapning).
