# Steg 11: löpande logg

10 november 2026. Ingen Blender, ingen Modal, inga Jev-anrop. Rört: `scen/3d/kontrakt/` och `forvarld/varld/`. Säkerhetskopior: `ut/fore_steg11/<sökväg>` och `forvarld/varld/history/fore_steg11/`. (`kompilator.mjs` kopierades efter ändringen och återställdes ur ändringen; kopian är den ursprungliga.)

## Klart
1. Skymning per källruta (`skymning.py`, `datacache.py`): nytt tidsurval 7,0–8,7 s till 0,5–0,6 s. Plan, skymning och objekt byte för byte lika mot baslinjen för 6 trimningar, 2 borttagningar, en flytt, en kopia (`engang/steg11_jamfor.py fore efter3`).
2. Källkontroll: hashminne per filstämpel (`kontrollera.sha_fil`), modulen laddas en gång (`gemensamt.py`), schemalint en gång.
3. Tal utan syntes i snabbvägen (`kompilera.py`, `tal.py`): `ljud: vantar`, mätt/uppskattad längd märkt, `tal.syntetisera_plan` som eget steg (anropas också av `diagnostik.py`; demonen har `forvarm` och `syntetisera_tal`).
4. Unika text-id för kopierade scener (`skarmtext.py`): `st1@s1_copy`.
5. Schemafelaktig edit avvisas enskilt (`gemensamt.kontrollera(avvisade=...)`). Princip: en edit är atomisk; kalla-, huvud- och referensfel avvisar hela regin som förut.
6. Webb mot plan (`edits.mjs`, `viewer.js`, `sanning.mjs`, `chat.mjs`): text lägg till följer kontraktet (30 px, box [46,737,484,80]); stativkamerans brännvidd följer kontraktet (fov 40 grader om inget anges, ×1,374, samma för "nära" och "hel"); byt replik byter undertexten i webben; kopierade scener får samma text-id; chatten skickar `tillgang_kalla: kort` och `kalla: platta`.
   Kontraktets ×1,374 bedömdes som regel, inte fel: `fov_grader` utelämnad ger 40 grader (loggas som `standardvarden`) och inramningen görs med avstånd, inte brännvidd. Webbens ×1,12/×0,88 var en egen approximation.
7. Kort/lokal i kontraktet: `tillgang_kalla`, `rum.kalla = platta`, `tillgang` på objekt, `plan.lokalbyte`, geometri `ej_byggd`.
8. Prov: `test_steg11.py` (19 prov). Alla moduler gröna.

## Inte gjort / öppet
- Stativkamerans läge (avstånd från uppmätt kamera) skiljer fortfarande: webben flyttar 0,144 m, planen 0,50 m (nära) och 1,67 m (hel). Webben har inte målpunkten och rekvisitan som kontraktet räknar avståndet ur. Enda kvarvarande avvikelser i sanningskontrollen.
- Texter på kopierade scener kan inte redigeras med kontraktets `skarmtext` (id `st1@s1_copy` finns inte i kalla).
- Planbeslutscachen sparar en ca 1 MB fil per nytt tidsurval; ingen rensning.
- Kall start: grundkompilering med tom cache 5–10 s och `forvarm` ca 8–9 s (en gång, sedan beständigt). Kompileringar under förvärmningen köas i demonen.
- Webbens byt replik tystar fortfarande originalet i webben; talet finns först efter syntessteget. Byte i en tyst scen ändrar undertexten i webben men inte i planen.
- `ui-snabb-check.mjs` och chattprovet kördes inte (servern startades inte; sanningskontrollen använder samma kompilator).

## Kommandon (projektroten, `$env:PYTHONIOENCODING='utf-8'`)
```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg11_mata.py efter3 --forvarm
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg11_jamfor.py fore efter3
node forvarld/varld/snabb-mat.mjs sanning
# från scen/3d/kontrakt, en modul åt gången:
../../.venv/Scripts/python.exe -m unittest test_flode   (46 prov, 2 min)
... test_rumsmall test_regler test_text_disk test_kroppmatt test_props test_handelser test_snabb test_steg11 bro.test_bro
../../.venv/Scripts/python.exe semantik/test_semantik.py
```
