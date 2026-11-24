# Urval, runda 4 steg 1 (skrivet före hämtning, 20 nov 2026)

Filer: `urval.py` (skript), `urval.json` (200 valda + reserver per stratum). Återskapas med
`scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/1-datagrund/urval.py` (frö **20261120**, läser bara).

## Population
De klipp som har lokala mått (`data/format/e28/tek.jsonl`, 2 703 rader) **och** rad i `data/format/e15/klipp.jsonl` (typ, konto, visningar) **och** en lokal kopia i `~/Downloads/letrend-e13/`. Bortfall före urval:

| orsak | antal |
|---|---|
| saknas i e15 (ingen typ) | 42 |
| saknar visningar eller kontot har färre än 10 klipp i e15 (ingen kontomedian) | 146 |
| lokal längd utanför 5–60 s (diskbudgeten) | 113 |
| runda 3:s hold-out | 4 |
| **kvar** | **2 398** |

## Uteslutet (hold-out)
`motpart/runda-3-opus/A-domare/holdout_lista.txt`: `sabai.soong-7474616203366108439`, `faros_shipandterrace-7540756212032326934`, `faros_shipandterrace-7511394441094008086`, `thepitaspot-7680489103195917590`. De fyra är de enda hold-out-klippen i `data/format/kontroll/klipp/` (117 råvideor i mappen, listan pekar ut 4). Urvalet kontrollerar mot listan i koden. Övriga 113 klipp i kontrollmappen är inte hold-out och kan ingå.

## Strata och regel
- **Typ** (5, ur e15): matporr_och_process, direkt_tilltal, relaterbar_sketch, annat, vardens_provsmakning. Kvot 40 per typ (200 / 5). Formatkortens typ (1 480 kort) täcker bara en delmängd av de 2 703; e15-typen finns för alla 2 661 som finns i båda.
- **Utfall** = log(klippets visningar / kontots median i e15), konton med minst 10 klipp. Vinnare: över +0,5 (över 1,65 × kontots median). Förlorare: under −0,5 (under 0,61 ×). Annars mitten. Per typ: 14 vinnare, 14 förlorare, 12 mitten. Gränserna är mina val för att få tydliga ändar, inte ägarens krav.
- **Längd** (lokal längd i tek): kort under 15 s, mellan 15–30 s, lång över 30 s. Inom varje typ och utfall varvas längdklasserna.
- **Konto**: högst 6 per konto (utfall: högst 4). Bland en cells kandidater väljs ett från det konto som hittills har minst valda (slumpad oavgjort).
- Inom varje cell (typ, utfall, längd) är kandidaterna slumpordnade med fröet. `reserv` i `urval.json` är resten av cellens ordning, och en misslyckad hämtning ersätts av **nästa i samma cell** (med kontotaket), aldrig av handplockat.

## Utfall av urvalet (före hämtning)
200 klipp från 96 konton (högst 4 per konto). Typ 5 × 40. Utfall: 70 vinnare, 70 förlorare, 60 mitten. Längd: 69 kort, 70 mellan, 61 lång. Summa lokal längd 4 623 s (77 min), alltså runt 1 GB vid TikToks vanliga bitrate (uppskattning, mäts efteråt).

## Utvecklingsklippen (notan, guacamole, gelato, a-sketch, b-tilltal, duepiani, spanjorskan)
**Ingen identifierad och därför ingen medtagen.** Repot har ingen nyckel från utvecklingsnamnen till `<konto>-<videoid>` i banken: de kommer från separata nedladdningar (ssstik-filer i `~/Downloads`) och rå-cacher i `scen/3d/ingest/ut/`, utan id. Jag gissar inte. Konton med liknande namn (duepiani, gelatonova, kennysgelato2.0) kan ingå i urvalet som vanliga klipp, men räknas då inte som utvecklingsklipp. Ägaren eller en agent som vet ids kan lägga till dem som egen grupp.

## Kända svagheter i urvalet
- Utfall relativt kontomedian ignorerar när klippet lades ut och kontots storlek; 146 klipp utan kontomedian är bortfallna.
- Urvalet är begränsat till 5–60 s och till klipp som e13 en gång kunde hämta (borttagna klipp finns inte i populationen, men kan ha försvunnit sedan).
- Ingen kontroll av att typen i e15 stämmer; den är en språkmodells etikett.
