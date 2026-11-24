# Kontrakt: kalla.json och regi.json

Kontraktet beskriver ett analyserat referensklipp (`kalla.json`) och vad en CM ändrar för en kund (`regi.json`), så att resultatet kan renderas om i Blender. Det finns för att harnessen (`video/`), scenmotorn (`scen/3d/`) och produkten (`hagen-ui`) i dag inte pratar med varandra: ingen av dem kan läsa den andras klippbeskrivning eller ändringar. Kontraktet formas av det som fungerar här i hagen-wf. hagen-uis modell är ett översättningsmål (se `OVERSATTNING.md`), inte en begränsning.

Kontraktet har två scheman och ett ifyllt exempel för barklippet i `../ingest/ut/bar/`. Ett lokalt byggflöde finns nu; se avsnittet `plan.json` sist i filen.

## Filerna

| Fil | Innehåll |
|---|---|
| `kalla.schema.json`, `regi.schema.json` | JSON Schema 2020-12. `description` på varje egenskap, `enum` där ordförrådet är slutet. |
| `exempel/bar/kalla.json` | Barklippet, byggt ur de verkliga filerna. Pekare har hash. |
| `exempel/bar/regi.json` | Fem redigeringar en CM rimligen gör. |
| `OVERSATTNING.md` | Tre tabeller: harness, hagen-ui, `scen3d.json` och `op.py` mot kontraktet. |
| `kontrollera.py` | Validerar exemplen mot schemana utan paket, och kontrollerar id-referenser och hashar. |

Kontroll: `scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py` (exit 0 = klart).

## Två filer, två lager

`kalla.json` är fryst och uppmätt. Den redigeras aldrig, bara fylls på (då ökar `revision`). Den har två lager:

- **`semantik`**: vad klippet är. Scener, beats, repliker med ordtider, personer, rekvisita, rum, intention. Fält som saknas är `null` eller en tom lista. `additionalProperties: false`.
- **`matning`**: bara pekare (sökväg, `sha256`, format) till filer som ingest redan skriver, plus koordinatsystem och enheter, plus `kvalitet`. Där står per uppgift om den är `uppmatt`, `antagen`, `modellbedomd` eller `saknas`, med känd osäkerhet (skala, brännvidd, golv) och vilket steg som skulle ge det som saknas.

`regi.json` är en ordnad lista redigeringar mot en kalla (`klipp_id`, `sha256`, `revision`). Mål anges med semantiska id (scen, person, prop, replik), aldrig bildrutor. Tid är sekunder på källklockan. Ett id som börjar med `PLATSHALLARE:` finns inte i kalla än. Regin har också `utdata` (vad som levereras) och `ramar` (vad som måste bevaras).

Regler: kalla.json:s sökvägar är relativa till mappen där filen ligger. Bildrutor förekommer bara i `matning` (till exempel `rutor_inom`). Halvöppna intervall `[start, slut)`. Egenskaper i det semantiska lagret använder harnessens svenska ordförråd utan diakritiker, och ingests namn där vi pekar på ingests filer.

## Fält: kalla.json

| Fält | Typ | Betydelse |
|---|---|---|
| `schema_version`, `revision` | sträng, heltal | `kalla/1`. Revision ökar när semantiken fylls på. |
| `klipp` | objekt | `id` (harnessens id), `konto`, `sha256` för källvideon, `video` (sökväg, mått, ljud), `beskrivning`. |
| `tidsbas` | objekt | `fps_taljare`, `fps_namnare`, `antal_rutor`, `langd_s`, `regel`. |
| `semantik.scener[]` | lista | `id`, `start_s`, `slut_s`, `funktion`, `bar`, `syfte`, `miljo`, `personer`, `kamera`, `segmentering`. |
| `semantik.beats[]` | lista | `id`, `nr`, `scen`, `funktion`, `bar`, `vad`, `bunden`. Som `h-scener.mjs`, utan åtgärd. |
| `semantik.repliker[]` | lista | `id`, `talare`, `sprak`, `text`, `start_s`, `slut_s`, `i_bild`, `scen`, `ord[]` (ord, tider, sannolikhet), `kalla`. |
| `semantik.personer[]` | lista | `id` (ingests person-id), `roll`, `beskrivning`, `roll_kalla`. |
| `semantik.props[]` | lista | `id`, `typ`, `etikett`, `agare`, `stod`, `faste` (person, led, hand), `rum_ref`. |
| `semantik.rum[]` | lista | `id`, `typ`, `beskrivning`, `vaggar`, `fasta`. Geometrin ligger i `rum.json`. |
| `semantik.skarmtext[]`, `ljud` | lista, objekt | Skärmtext med tider. Ljudets art: tal, musik, trendljud. |
| `semantik.intention`, `serie` | objekt | `karna`, `krok`, `vandning`, `payoff` (finns, vad, scen). Serieposition är valfri (`null`). |
| `matning.koordinater` | objekt | Värld, kropp, kamera, rum, bild: axlar, enheter, kvaternionsordning, skala. |
| `matning.kameror[]` | lista | `spar_colmap`, `spar_metrisk` (pekare), `fokal_px`, `statisk`, registrerade rutor, fel. Aldrig redigerbar. |
| `matning.personer[]` | lista | Pekare till `sekvens_<id>.npz`, synlighet, pålitlighet, kontakt. Rutor i bild och antal kända rutor. |
| `matning.rum[]`, `masker[]`, `korlogg` | listor | Pekare till `rum.json`, `masker.npy`, `personer.json`, `tider.json`. |
| `matning.kvalitet[]` | lista | `post`, `status`, `metod`, `osakerhet`, `saknas_steg`, `kalla_fil`. |

## Fält: regi.json

| Fält | Betydelse |
|---|---|
| `kalla` | `klipp_id`, `sha256`, `revision`. Regin gäller bara den kalla den skrevs mot. |
| `kund` | Valfri: kundens id och namn. |
| `edits[]` | Varje post har `id`, `op`, `ursprung` och `kommentar`, plus operationens egna fält. |
| `ursprung` | `cm`, eller `harness-forslag` med `harness` (verb `atgard`, `beat_nr`, `funktion`, `skal`, `kalla_fil`) och `godkand_av_cm`. |
| `utdata` | `fps_taljare`, `fps_namnare`, `bredd`, `hojd`, `stil_ref`, `ljudpolicy`, `render_backend`. |
| `ramar` | `bevara_beats`, `bevara_klippoffset_s`, `tillat_retiming`, `max_talfaktor`. |

## Operationerna och vad de kostar

Steg: **tal** (röstsyntes, ordtider, munkurva), **tidslinje** (scenordning, tidskarta, ljudmontage), **rorelse** (nyckling, kontakt), **rum**, **utseende**, **prop**, **kamera**, **bygg** (Blender-bygget), **rendera**. Kostnad enligt Codex-analysen (avsnitt 4 och 5): *data* = bara data ändras (bygg och rendera körs ändå), *liten/medel/stor* = ny kod, *ny* = ny inspelning eller GPU. Uppmätt: barklippets bygge och rendering 36,7 s, Piper 0,4–0,6 s per ändrad replik (varm).

| Op | Körs om | MHR-kedjan i dag | Gamla kedjan |
|---|---|---|---|
| `byt_replik`, `lagg_till_replik` | tal, (tidslinje), bygg, rendera | medel: `mhr_rig.py` läser aldrig `expr` och muxar originalljud | data för svensk förhandsvisning, liten för export, liten–medel för andra språk |
| `casta` | utseende, (tal), bygg, rendera | liten för färg, medel för annan kompatibel rigg, stor för origad karaktär | data, plus ombakning |
| `byt_miljo` | rum, (kontakt), bygg, rendera | data om rummet ges som `rum.json`-objekt, medel för att välja och passa kundlokal, ny för ny plats | data för primitiva set |
| `byt_prop`, `lagg_till_prop`, `flytta_prop`, `ta_bort_prop` | prop, bygg, rendera | data för statiska lådor via `rum.objects`, medel för grepp i hand | data för stödda typer |
| `ta_bort_scen`, `duplicera_scen`, `flytta_scen`, `fri_scen` | tidslinje, bygg, rendera | medel: ingen scenmontering finns | data, liten om en aktörs sista scen tas bort |
| `lagg_till_scen` | tidslinje, rorelse, bygg, rendera | medel, ny om ny prestation behövs | data vid återanvänd rörelse |
| `trimma_scen` | tidslinje, bygg, rendera | medel: kropp, kamera och ljud ska omsamplas ihop | data för pauser, medel för icke-linjär tid |
| `skarmtext` | bygg, rendera | liten–medel (egen bedömning, Codex täcker det inte) | data i spelaren |
| `renderkamera` | kamera, bygg, rendera | liten–medel: `kam_R`/`kam_C` styr i dag både kamera och personer | data |
| `rorelse` | rorelse, tidslinje, bygg, rendera | medel, stor med retargeting, ny om rörelsen saknas | inget bibliotek, bara återanvänd tagning |
| `uttryck` | rorelse (ansikte), bygg, rendera | medel: uttryck är inte inkopplade | data (`humor`) |
| `forenkla` | kamera eller tidslinje, bygg, rendera | ärver från `renderkamera` och scenoperationerna | data |
| `tillat`, `flagga`, `satt_intention`, `satt_serieposition` | inget | data: ändrar bara kontroller och status | |

## Vad en kompilator skulle göra

1. Läsa kalla, kontrollera att `sha256` och `revision` stämmer mot regin och att varje pekare i `matning` har rätt hash.
2. Validera regin mot schemat och att alla id finns i kalla (eller är nya via `lagg_till_*`).
3. Tillämpa redigeringarna i ordning på en intern scenplan: utdatascener med källintervall och tidskarta, personer med roll och utseende, rum, rekvisita, renderkameror och repliker med röst.
4. Räkna ut vilka steg som är ogiltiga per op (tabellen ovan) och köra bara dem. Kontrollera `ramar` (taltakt, klippoffset, låsta beats) och varna eller stoppa.
5. Lämna planen till byggaren (`mhr_rig.py`) och röstsyntesen. Aldrig skriva tillbaka till kalla.

## Ursprunglig gaplista

Listan nedan beskriver läget före byggflödet. Källbyggaren, kompilatorn, scenmontage, lådrekvisita och separat renderkamera är nu implementerade i den omfattning som anges sist i filen. Övriga luckor kvarstår.

- Något som skriver `kalla.json`. Exemplet byggdes med ett engångsskript ur ingest-mappen och harnessens lager.
- Semantiska scener, beats och `funktion`/`bar` för ett MHR-klipp. Barklippet har bara en detekterad scen, och harnessens v5-kort och scenplan saknas för det.
- Transkript och ordtider per klipp. `ordtider.py` gäller ett enda klipp (`d-dialog-notan`, svenska). Barklippet har inget.
- Källfilens sökväg och hash i ingests utdata. Exemplet matchade videon på mått.
- Roll per person (vem som är bartendern) och serieposition.
- En läsare av `regi.json` i någon byggare, och en kompilator.
- En renderkamera skild från rekonstruktionskameran i `mhr_rig.py`.
- Ansiktsuttryck och läppar i MHR-kedjan. Ändrad replik överlever bara i den gamla kedjans förhandsvisning.
- Ett rörelsebibliotek kopplat till MHR-riggen, med rotjustering och blandning.
- Scenmontage i MHR-kedjan. Ingest antar en sammanhängande tagning, och klipp inuti en tagning hanteras inte.
- Rekvisitans stöd och grepp, och omräkning av kontakt när möbler byts.
- Lokalbanken som rumskälla (`byt_lokal`): kundens lokal till passande rum.
- Skärmtext: läsning ur källan och rendering i Blender.
- Gemensam tid. Ljud mappas linjärt, `source.knots` ignoreras, fps avrundas i Blender.

## plan.json: lokal byggplan, version plan/1

Kör från projektroten med `scen/.venv/Scripts/python.exe`:

```
scen/3d/kontrakt/kalla_bygg.py scen/3d/ingest/ut/bar scen/3d/kontrakt/ut/bar/kalla.json
scen/3d/kontrakt/kompilera.py scen/3d/kontrakt/ut/bar/kalla.json scen/3d/kontrakt/exempel/bar/regi.json scen/3d/kontrakt/ut/bar/plan.json
```

Källbyggaren vägrar skriva över en befintlig utfil. `--video` anger källvideon; annars används `meta.json` eller, för äldre ingest, en unik matchning på videomått som märks **antagen**. Lokal analys, sållning, e4 och v5 läses utan nätanrop. Okända uppgifter lämnas tomma och beskrivs under `kvalitet`. Alla skillnader mot exemplet sparas i `kalla.skillnader.json`; `--jamfor` väljer ett annat jämförelseunderlag. `ordlista.json` innehåller bara fasta formatbeskrivningar, inga mätvärden. Nya ingest-mappar får `kallvideo` och `kallvideo_sha256` i metadata. Äldre oförändrade metadata lämnas byte-identiska eftersom rummets cache hashar hela filen.

Kompilatorn importerar kontrollerna i `kontrollera.py`, validerar schema, referenser, revision och hashar och tillämpar edits i ordning. Saknade mätfiler stoppar bygget. Varje edit är atomisk: om den inte kan genomföras återställs dess ändringar och orsaken skrivs i `ej_tillampat`. Inga källfiler skrivs tillbaka. Samma indata och samma absoluta filplatser ger identiska JSON-byte. Sekunder blir bildrutor genom avrundning till närmaste ruta (källans tider har 3-4 decimaler). En edit som inte ändrar något eller saknar det den behöver (till exempel `lagg_till_prop` utan `plats` eller `stod`, en trimning som ger samma intervall, en casting utan ny färg eller nytt rollnamn, en kamera som står på sitt mål) hamnar i `ej_tillampat` med orsak; en trasig edit avbryter aldrig hela kompileringen. Ett standardvärde som planen själv väljer (`fov_grader` null blir 40, `mal.punkt` null blir kropp/`c_spine2`, saknat mål blir uppmätt blickriktning) skrivs som `standardvarden` (fält, värde, orsak) i editens `andring`.

| Planfält | Innehåll |
|---|---|
| `kallrutor` | Källruta för varje utdataruta, från noll. Både kroppar och den trackade kameran samplas med denna lista. |
| `tidskarta` | Halvöppna intervall `ut` → `kalla`, samt om originalljudet ska vara med. Samma fps krävs; ingen tidssträckning. |
| `personer` | Person-id, rollnamn, helkroppsfärg `#RRGGBB` och absolut sökväg till MHR-sekvensen. |
| `objekt` | Slutliga golvplan och lådor: namn, position i meter, Eulerrotation XYZ i radianer, lokala XYZ-mått, färg, eventuell lutning på ovansidan och synligt utdataruteintervall. Allt är i Blender-världen, Z upp. Regins mått `[bredd,höjd,djup]` omvandlas till `[X,Y,Z]`. Relativa placeringar är redan uträknade. |
| `renderkamera` | En explicit 4×4-matris och lins i mm per utdataruta; även följ uppmätt bakas ut. Matrisen går från Blender-kamerans lokala koordinater till världen, blick längs −Z, Y upp. Horisontell sensor är 36 mm; regins FOV är vertikal. |
| `utdata` | Bildantal, rationell fps, pixelmått, PNG/RGBA, Workbench och 100 % upplösning. `stil_ref` och annan backend stöds inte. |
| `matning`, `kallvideo` | Mätpekare med absoluta sökvägar och befintliga hashar, samt källvideons absoluta sökväg. |
| `tillampat`, `ej_tillampat` | Edit-id, operation och ändring respektive orsak. `varningar` och `beslut` redovisar kontroller och val för förhandsvisningen. |

Stöds: trim utan tidssträckning, borttagning/flytt/duplicering av scener, rollfärg, byte/tillägg/flytt/borttagning av statiska prop-lådor samt uppmätt kamera, stativ och egna kameranycklar. Trimning med `replik_sakert` vägrar klippa kända ord; utan ordtider skyddas hela repliken. Stativets huvudmål tas från personens medianposition och utsnittet vidgas så huvudets bana och rekvisitan ryms. Trimning räknar om detta utsnitt. Halvbildens minsta höjd är 1,25 m; det är ett layoutval, ingen mätning. Propbyte/tillägg får ockragul färg så ändringen syns. Röst, andra utseendeegenskaper, tillgångsmodeller, handfästen, dolly/orbit/zoom och andra operationer listas som ej tillämpade. Bindningslösa bevarade beats, klippoffset och ändrad fps stoppar kompilering. `blandat_duckad` behåller originalljudet eftersom inget nytt tal produceras; `designade_rostar` stöds inte utan röstbygge.

Bygg i en egen bakgrunds-Blender: `blender -b --factory-startup --python-exit-code 1 --python scen/3d/ingest/mhr_rig.py -- scen/3d/ingest/ut/bar <källvideo> --plan <plan.json> --ut scen/3d/kontrakt/ut/bar/rendering --render`. `--ut` separerar utdata från ingest. Utan `--plan` behålls tidigare beteende, inklusive halv renderupplösning. Planläget behåller `kamera` som inaktiv rekonstruktionskamera och aktiverar `renderkamera`; personerna beräknas alltid ur mätkameran. PNG-sekvensen är ljudlös; tidsmappade ljudstrips finns i blend-filen.

Verifiering: `test_flode.py` testar kompilator, källbyggare och metadata-cache lokalt. `verifiera_korning.py` använder Blenders sökväg från ingest-koden och kör original, patch utan plan och patch med plan i separata bakgrundsprocesser. Loggar, scenrapporter och renderbilder hamnar under `ut/bar/`; körningen vägrar skriva över tidigare verifieringsrapporter. Ingen öppen Blender-session används.
