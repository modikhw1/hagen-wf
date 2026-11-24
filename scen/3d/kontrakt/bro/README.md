# Bron mellan harnessen och kontraktet

Harnessen (`video/format/`) och scenmotorn (`scen/3d/kontrakt/`) pratar inte med varandra. Bron är två små steg som översätter mellan dem. Harnessen föreslår och CM beslutar. Ingenting här ändrar `kalla.json`, schemana eller någon annan fil utanför `bro/`.

```
v5-kort ──────────────► kort_till_kalla.py ──► patch.json        (fyller kallas semantiska lager)
v5-kort + kundlinje ──► gor_scenplan.mjs ────► scenplan.json     (h-scener.mjs, scenplan(c, L))
scenplan + kalla + patch + kundlinje
                    ──► scenplan_till_regi.py ► forslag.json + regi.json
```

Språkval: Python, eftersom kalla, regi, kompilator och kontrollen är Python och bron återanvänder `kontrollera.py` utan att ändra den. Scenplanen görs med en liten Node-fil som anropar harnessens egen `scenplan()`, så regelverket finns på ett ställe.

## Kör

Från projektroten, med `scen/.venv/Scripts/python.exe`:

```
node scen/3d/kontrakt/bro/gor_scenplan.mjs <kort.json> <linje.json> <scenplan.json>
python scen/3d/kontrakt/bro/kort_till_kalla.py <kort.json> <kalla.json> <patch.json>
python scen/3d/kontrakt/bro/scenplan_till_regi.py <scenplan.json> <kalla.json> <patch.json> <linje.json> <utmapp>
python scen/3d/kontrakt/kontrollera.py <absolut sökväg till mappen med kalla.json och regi.json>
python scen/3d/kontrakt/kompilera.py <kalla.json> <regi.json> <plan.json>
python -B scen/3d/kontrakt/bro/test_bro.py
```

Alla skript vägrar skriva över en befintlig utfil. `scenplan_till_regi.py` tar också `--konto` och `--id` om scenplanen är en samlingsfil som `data/format/harness/pass6/scenplaner.json`.

## Steg 1: kort till patch (`kort_till_kalla.py`)

Kortet har 2–7 beats med `vad`, `funktion`, `bar`, `bunden` och inga tider. Kalla har tidssatta scener från klippdetektering. Antalen hänger inte ihop: i 33 klipp med både kort och analys var beats lika många som scener i 4, fler i 18 och färre i 11. Beats är därför en berättelse och scener är bildklipp, och justeringen blir en uppskattning med angiven metod.

| Metod | När | Konfidens |
|---|---|---|
| `tid` | kortets beats har `start_s` och `slut_s` (v5 har inte det) | hog |
| `enda_scen` | kalla har en scen | hog (beatet ligger i scenen, men var i den är okänt) |
| `text` | ett citat i beatets `vad` matchar en replik eller skärmtext (ordöverlapp minst 0,6, bara bästa träffen, i ordning) | hog eller medel |
| `ordning_1till1` | lika många beats som scener | medel |
| `ordning` | annars: scener fördelas jämnt på beats i ordning, mellan eventuella textankare | lag |

Patchen (`kalla-patch/1`) har:
- `semantik.beats`: `id`, `nr`, `scen`, `funktion`, `bar`, `vad`, `bunden` i kalla-schemats form. `bunden: ingen` blir `null`. `scen` sätts bara när beatet hamnar på exakt en scen.
- `justering`: per beat vilka scener, metod, konfidens och belägg.
- `semantik.scener`: `funktion`, `bar`, `syfte` per scen. Fältet sätts bara om alla beats på scenen är överens, och `syfte` bara när ett beat ligger på just den scenen med konfidens medel eller bättre. `syfte` är då kortets `vad` ordagrant. Det är vad som sker, inte ett fristående varför. Om kalla redan har ett annat värde (notan är handkalibrerad) står det under `konflikt_med_kalla`.
- `semantik.intention`: `karna` ur kortet, `krok.finns` ur `grundvarde.krok`, `vandning.finns` ur `grundvarde.vandning`, `vad` och `scen` ur beatet med den funktionen. `payoff` kommer bara från ett beat med funktion `punchline`; saknas det blir `finns` null, inte falskt.
- `serie`: alltid `null`. Kortet har ingen serieposition.

`tillampa_patch(kalla, patch)` ger en kopia av kalla med patchen ifylld. Den fyller bara null och släpper som standard bara igenom medel eller bättre. Den ökar inte `revision`; det gör den som skriver filen.

## Steg 2: scenplan till förslag (`scenplan_till_regi.py`)

Alla redigeringar får `ursprung.typ = harness-forslag`, harnessens verb, `beat_nr`, `funktion` och `skal` ordagrant, samt `godkand_av_cm = null`. `kompilera.py` tillämpar inte sådana förrän CM har satt det till `true` (rad ~275), så förslagen ändrar inget av sig själva.

| Harnessens `atgard` | Förslag | Anmärkning |
|---|---|---|
| `behall` | ingenting | beatets nr listas i `behalls_beats` |
| `eget_tal` | `byt_replik` för varje replik i beatets scener, `text: null` | Ingen text hittas på. Texten skrivs bara om planens beat bär `replik` (en sträng per replik, lika många som repliker). Utan repliker i scenen blir det en `flagga` (fraga). |
| `frontfigur` | `casta` med kundens frontfigur (`kundroll.namn` = etikett, `id` = `PLATSHALLARE:<konto>:<etikett>`) | Person = den som talar mest i scenen. Vid lika eller inga repliker `PLATSHALLARE:person_beat<n>` och kandidaterna listas. Utseendet lämnas tomt. Saknas frontfigur i linjen blir det en `flagga` (risk). |
| `byt_produkt` | `byt_prop` på props som scenens personer äger | `ny_typ` är första produkten i linjens `produkter`, övriga står som `alternativ`. Äger scenen inga props (vanligt: `agare` är oftast null) blir `prop` ett `PLATSHALLARE:`-id. |
| `byt_lokal` | `byt_miljo` per scen i beatet | Finns en mall eller plats med exakt id `<konto>` eller `<konto>_<lokaldel>` i `rumsmall/` eller `plats_bank/` används den (`rumsmall_id` respektive `tillgang_id`). Annars `kalla: ord` med linjens `lokal`-koder, `plats_saknas: true` och `mallkandidater` som tips (`bar`, `disk_kassa` till `bar_disk`, `matsal` till `restaurang_tva`). |
| `forenkla` | `forenkla` per scen med `inga_effekter`, plus `farre_personer` om scenen har fler personer än linjens `max_personer` | |
| `fritt` | `fri_scen` med `lage: stryk`, markerad `valfri` och `tillampas_som_standard: false` | I `regi.json` blir det en `flagga` (fraga), aldrig en strykning. Varnar om scenen delas med andra beats. |
| `risk` | `flagga` med `allvar: risk` | Schemat har redan `flagga`, så ingen ny operation behövs. |

Varje förslag har `konfidens` från justeringen. Är den `lag` står det i kommentaren att beatet bara är grovt placerat.

### Två filer

- `forslag.json` har alla förslag i regi-form plus extrafält under `forslag` (`behover_text`, `valfri`, `tillampas_som_standard`, `konfidens`, `varning`, `alternativ`, `kandidater`, `plats_saknas`, `mal_saknas`, `beat_nr_ovriga`). Här finns också `varningar`, `behalls_beats`, `hoppade_over`, `sammanfattning` och `standardvarden`.
- `regi.json` är det schemat kan uttrycka och validerar mot `regi.schema.json`. Skillnaden mot `forslag.json`: `byt_replik` utan text och `fri_scen` blir `flagga` (fraga), och extrafälten tas bort.

Obligatoriska fält som harnessen inte har fått standardvärden från kalla och exemplen: fps och mått ur kalla, `stil_ref` null, `ljudpolicy` original, `render_backend` blender_mhr, `ramar` utan låsta beats och `max_talfaktor` 1,15. De listas i `standardvarden`.

## Det som står kvar för CM

- Godkänna varje förslag (`godkand_av_cm`), annars tillämpas inget.
- Skriva nya repliker. Bron skriver aldrig text.
- Välja person vid `casta` när flera talar, och utseende och röst för kundens roll.
- Peka ut vilket prop som ska bytas när kalla inte vet vem som äger vad, och välja bland kundens produkter.
- Skapa kundens lokal som rumsmall om `plats_saknas` är sant.
- Avgöra `fri_scen` och `flagga`-posterna.
- Kontrollera beat-till-scen-justeringen när konfidensen är `lag`.

## Det som saknas

- Ett v5-kort för klippet. Kort finns för 1 427 klipp i banken och för fem av de sju klippen i `scen/klipp/` (kenny, interpool-7599..., och a, b, c under sina bankid), men inte för notan (`d`, finns inte i banken) och inte för interpool-7601... (barklippet). Av de fem har bara interpool-7599... (biljard) ingest som `kalla_bygg.py` kan göra kalla av utan handkalibrering; b har ingest i två tagningar, men flerklippsbyggaren läser notans handskrivna `scen3d.json`.
- Tider i kortet. Utan dem är beat till scen en uppskattning, och beats får inga egna tider.
- Serieposition per klipp.
- Kundens lokal som mall: `rumsmall/` har generiska mallar, ingen kundspecifik.
- Skiljet mellan `byt` (h-anpassa8) och `byt_produkt`/`byt_lokal` (h-scener): bron läser bara h-scener-verben. h-anpassa8:s `scener[]` har `replik` och `bild`, vilket bron använder för `replik` om det finns.
- Kompilatorn markerar `flagga` och `forenkla` som `ej_tillampat` ("Operationen stöds inte av denna byggare") även när de är godkända. Det är avsett som varningar, men de syns som ej tillämpade.

## Körda exempel i `ut/`

- `ut/biljard/`: kortet `interpooluppsala-7599643065644551446` (bank3, Flash 3.8), kalla byggd med `kalla_bygg.py` ur `scen/3d/ingest/ut/biljard`, kunden `blackstonesteakhouse`. Båda beats har `bunden: ingen`, så scenplanen blir `behall behall` och inga förslag uppstår. Patchen har två beats på en scen (`enda_scen`, hog), `bar = karna`, `funktion = null` (krok och avslut delar scen) och intentionen ifylld.
- `ut/kenny/scenplan_kebabbabes.json`: bara en scenplan (kort och linje, inget ingest finns för klippet): `behall behall forenkla behall`.
