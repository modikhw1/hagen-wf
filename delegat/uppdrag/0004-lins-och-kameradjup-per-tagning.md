---
id: 0004
titel: Spåra varför linsen är ett reservvärde och mät vad en riktig lins gör med residualerna
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0001
tillåten_skrivning: [scen/3d/kontrakt/ut/diag_0004/]
---

## Mål
Det ska vara känt varifrån varje tagnings brännvidd kommer, varför den i `b-tilltal-ravara` hamnar på reservvärdet 64 mm (FOV 31,4°) i alla tagningar utom S5, vilket värde som är rimligt, och hur mycket av oenigheten mellan tagningarna som försvinner med det värdet.

## Bakgrund
Svar 0001 (`delegat/svar/0001-granska-flerbildspassning.md`, Del B) visar att alla kameror har yaw 90°, höjd 1,40 m och lins 64 mm, och att 64 mm är reservformeln i `scen/3d/kontrakt/kompilera.py:184` (`max(bredd, höjd)` som fokal). Klippen är mobilfilmade i stående format. En mobils huvudkamera har normalt 60–75° vertikal FOV, alltså ungefär dubbelt så vid. Är linsen fel med en faktor två blir alla lyft ur bildrutor fel i sidled och djup, och det skulle förklara att högerkanten i S8 och S11 "inte kan nås".

Samtidigt säger `scen/3d/NASTA.md` ("Att lita på") att slutkameran projicerar lederna 1–5 px från originalet. Lins och avstånd kan alltså kompensera varandra för personen men inte för möblerna bredvid. Det ska redas ut, inte antas.

## Underlag
- `scen/3d/kontrakt/kompilera.py` (rad 184 och uppströms), `kontrakt/bildkamera.py`, `kontrakt/kamerafakta.py` om den finns
- Ingestens kroppsläsning (SAM 3D Body / MHR) ger en egen kameramodell per ruta. Leta i `scen/3d/ingest/` och `scen/3d/kroppsbank/` efter var fokal eller FOV läses och om den förs vidare till `kalla.json`/`plan.json`.
- Monokulärt djup används redan för lästa avstånd (PIPE, "märkt `last`"). Se om den modellen också ger intrinsik.
- Mätskripten från 0001: `scen/3d/kontrakt/ut/diag_0001/` (`lyft.py`, `kamerabehov.py`). Återanvänd genom import eller kopia till den nya mappen.
- Varför S5 har 146 mm: det är samma tagning som har den misstänkta läsningen 3,67 m.

## Gränser
- Bara nya filer i `tillåten_skrivning`. Inga ändringar i kedjans kod; rättningen blir ett eget uppdrag när orsaken är känd.
- Inga nätverksanrop behövs. Lokala modellkörningar som redan finns i venv är tillåtna om de behövs för att läsa intrinsik ur nyckelbilder.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Datavägen för brännvidden är beskriven med fil och rad från ingest till `plan.json`, och stället där det mätta värdet tappas (eller aldrig finns) är utpekat.
- En tabell per tagning: reservvärdet, det värde ingestens kroppsläsare eller djupmodell anger om det finns, och ett värde skattat ur bilden på minst ett oberoende sätt (till exempel personens kända proportioner mot läst avstånd, eller kakelfogarnas försvinningspunkter).
- Omräkning utan kompilering: lyften ur 0001 (tabell 6) körda igen med rimlig lins och med kameradjupet anpassat så att personen ligger kvar i bild. Samma tabell, före och efter, i meter.
- Svar på frågan: räcker rätt lins för att S8, S9 och S11 ska bli överens om `disk_C` och vågen, eller återstår fel i bildrutorna och kameralösningen?
- Förslag på rättning i högst fem rader: var linsen ska komma ifrån i kedjan och vad som ska gälla när den saknas.

## Leveransform
`delegat/svar/0004-lins-och-kameradjup-per-tagning.md` enligt mallen, högst cirka 70 rader. Skript och tabeller i `scen/3d/kontrakt/ut/diag_0004/`.
