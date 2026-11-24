# Uppdrag: väljaren (prioritering av objekt per tagning), rumshjärna/2

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Läs först `rumshjarna/RUMSHJARNA.md` och docstringen överst i `lokalitet.py` (regler L1–L9). Svara på svenska.

## Varför

0.0 är rummet före all modifiering: rum, personer och föremål ur originalvideon som 3D (scenpaket/2 + texturerade nät per OneFormer-instans). Ägaren vill att en "väljare" ska ta fram de objekt som BÄST och med MINST rörighet förmedlar vad scenen är: personen, det hon håller, det som kännetecknar platsen och inredningen. Regibordet kan sedan förenkla scenen eller lägga tyngd på det viktiga. Bildgenerering (V3 "essens") gav en rimlig men opålitlig rangordning. Ägaren säger att prioritering kräver förståelse av videon och att man inte kan lita på bildgenereringen helt. Väljaren ska därför byggas på våra egna signaler, och V3 ska vara en röst bland flera.

## Uppgift

Skriv `rumshjarna/valjare.py <klipp>` som skriver `ut/rumshjarna/<klipp>/valjare.json`: per tagning en rangordnad lista över instanser (instans-id, etikett, grupp, poäng, skäl per signal), plus en föreslagen "minsta mängd" som täcker scenens mening.

Signaler. Använd det som redan finns. Läs `lokalitet.json`, `paket_L.json`, `nat.json` och `obs_gpu/*.npz` via `lokalitet.ladda`, inget nytt GPU-anrop.

1. Handkontakt och föremål i handen (L2c `handkontakt` i lokalitet.json, och nät-bitar nära handlederna i paketet).
2. Återkomst över tagningar i samma rum (L7 `rum_over_tagningar.grupper`). En instans vars etikett och 3D-läge återkommer i flera tagningar kännetecknar platsen.
3. Bildposition och storlek: centrering, andel av bilden. Stora strukturytor som vägg, golv och tak är rum, inte objekt. De ska finnas med men bilda en egen klass ("rum").
4. Skärpa i originalrutan (Laplacevarians inom masken) som ett tecken på fokus.
5. Semantisk prior för restauranginnehåll: mat, tallrik, glas, flaska > möbler > dekor. Håll den liten och dokumenterad.
6. V3-röst där den finns: `ut/rumshjarna/duepiani/<sid>_v3_essens.png` för s1, s4, s6 och s8. Grå-detektion finns i `rumshjarna/analys.py` (HSV, typvärde). Låg vikt.

Krav:

- Allmänt: inga klippkonstanter, och samma kod på alla fem klipp (`duepiani`, `spanjorskan`, `08burgerkebab`, `babasburgers`, `kennysgelato2.0`).
- Varje poäng bär sina skäl, så att man kan se varför något valdes.
- Rör INTE `lokalitet.py`, `hjarna.py`, `likhet.py`, `server.py` eller `app.js`, eftersom andra arbetar i dem. Bara nya filer.
- Kör med `.venv/Scripts/python.exe -I -X utf8 rumshjarna/valjare.py <klipp>` på alla fem klippen.
- Kontrollera själv mot originalrutorna (`ut/rumshjarna/<klipp>/<sid>_orig.png` finns för tagningar med person, annars ta en ruta ur `data/format/kontroll/klipp/<video>.mp4`): är topp 3 rimliga? Skriv ärligt var det blir fel.

## Leverans

- `rumshjarna/valjare.py`
- `ut/rumshjarna/<klipp>/valjare.json` för alla fem klippen
- `rumshjarna/VALJARE_RAPPORT.md`: metod, topp 3 per tagning för två klipp, var väljaren har fel, och vad som saknas för att den ska kunna styra regibordet. Max 80 rader.

Sista raden i ditt svar: `KLAR` eller `BLOCKERAD: <orsak>`.
