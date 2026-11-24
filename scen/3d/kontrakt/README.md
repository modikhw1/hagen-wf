# Kontrakt: kalla.json och regi.json

Kontraktet beskriver ett analyserat referensklipp (`kalla.json`) och vad en CM ändrar för en kund (`regi.json`), så att en upplöst plan kan visas och exporteras. Den interaktiva visaren och det planerade slututseendet flyttas till webbläsaren; Blender används för ingest/export. Det befintliga Blender-renderflödet finns kvar. Det finns för att harnessen (`video/`), scenmotorn (`scen/3d/`) och produkten (`hagen-ui`) i dag inte pratar med varandra: ingen av dem kan läsa den andras klippbeskrivning eller ändringar. Kontraktet formas av det som fungerar här i hagen-wf. hagen-uis modell är ett översättningsmål (se `OVERSATTNING.md`), inte en begränsning.

Kontraktet har två scheman och ett ifyllt exempel för barklippet i `../ingest/ut/bar/`. Ett lokalt byggflöde finns nu; se avsnittet `plan.json` sist i filen.

## GOLV2: kroppens meter, platsens golv (10 nov kväll, gäller före äldre golvtext nedan)

Beslut: `GOLV2.md`. Logg, mätning och återupptagning: `GOLV2-LOGG.md`.

- Kroppen behåller den skattade kamerarumsrörelsen: världspunkt = R·(F·pose/100 + cam_t) + C, sedan scenens `till_plats`. Alla läsare går via `../ingest/metrisk.py`, som för äldre sekvenser tar `cam_t_fore_golv` (annars `cam_t_fore_kontakt`) och `pose_fore_kontakt`. Inga filer på disk skrivs om.
- Ingen kamera flyttas för att dölja golvfel: mätkamerans nycklar ligger på rummets kamera (avståndet redovisas per person i `kvalitet.golv2_3d`, ska vara 0).
- `golvmatning.for_plan` (anropas av `kompilera`, cache `ut/cache/golv2`) löser platsens golv vid kompilering: tagningar som är kopplade med accepterad bildmatchning bildar en grupp med gemensam höjd (matchningens höjdrest återställs mot registreringen före det gamla golvsteget); varje grupp får ett golv ur den starkaste cue-familjen (synlig fot med låg vertikal fart > sits mot identifierad sitstyp > djupgolv > handled/bord > antagen kamerahöjd 1,45 m). Kroppsräckvidd röstar aldrig. En röst per person och tagning. Alla cues sparas med rest och skäl. Synlig fot märks `modellbedomd`, sits och kamerahöjd `antagen`.
- Höjd överförs mellan kamerastationer bara från accepterad bildmatchning (kvarvarande lutning ≤ 2 grader och fri rigid rest ≤ 0,15 m, plats.py:s egna gränser); i en kedja ackumuleras resterna. Ingen notan-matchning klarar gränsen i dag, så varje tagning har eget, antaget golv; resten står under `registrering_hojd`. Total Z-flytt sparas som `z_flytt_m`, så en ny behandling börjar från basregistreringen.
- Sits räknas bara med semantikens hållning `sitter` OCH identifierad sitstyp (mallens deltyp via bundet ankare); stolsprioren gäller bara `stol`.
- Synlig fot räknas per sida och tillförlitlig ruta, med låg vertikal fart för just den sidan.
- Källa utan platsreferens (t.ex. bar): `golvmatning.lokalt_golv` (cache `golv2_lokal`) sätter golvet i tagningens ram; en ensam identitetsplats ger samma golv.
- Kontakt flyttar inte längre kropp eller pose; den är diagnostik.
- Mätning före/efter: `engang/golv2_mat.py` och `engang/golv2_jamfor.py`, resultat i `ut/golv2/jamforelse.md`. Oförändrat bildfel visar att projektionen är hel, inte att golvet är rätt; sulornas höjd och bilder från flyttad kamera prövar golvet.
- Tagning utan synlig golvkontakt får i `kvalitet.md` texten ”Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt.” Tabellen ”GOLV2: kropp och rum” visar per person kamerahöjd, kamerans avstånd till rummets kamera, modellens fotrest och synlig fotrest.
- `tropassning` flyttar stol och följbord i XY till personens medianbäcken (antaget; kroppen flyttas inte).
- Stativkamerans nyckel har `mal_m` (målpunkten) så att webben kan räkna samma avstånd.
- Bakgrundsskala: den enda tillåtna operationen är `metrisk.skala_bakgrund` (kamerans translation och bakgrundspunkter tillsammans kring samma origo, aldrig kroppens cam_t). Ingen ny skala väljs i dag.

## Nytt klipp: från mp4 till film (kort lista)

Kör från projektroten med `scen/.venv/Scripts/python.exe` och `PYTHONIOENCODING=utf-8`. Ett tungt steg i taget (16 GB minne). `<I>` = `scen/3d/ingest/ut/<namn>-tagningar`.

1. Lägg klippet i `scen/klipp/<namn>.mp4`.
2. Billiga steg, sedan stopp: `scen/3d/ingest/flera/ingest_flera.py scen/klipp/<namn>.mp4 <I> --semantiskt`. Delar i tagningar, spårar personer lokalt. Finns ingen `semantik.json` skriver det ut kommandona i steg 3 och stannar före betald kropp.
3. **Människa, nätanrop (Gemini):** `scen/3d/kontrakt/semantik/semantik_ingest.py <I>/semantik_klipp.json`, sedan `ordtider_klipp.py <I>/semantik_klipp.json` (lokal Whisper). Granska `<I>/semantik/semantik.json`: vilka spår som är vem, vilka som är `ej_personer`.
4. Förhandsvisa kostnaden: samma kommando som i 2 med `--granska-budget` (visar vilka tagningar som kör kropp och hur många personrutor; skriver inget). Kör sedan utan flaggan: kamerans brännvidd prövas (`ingest/regler.py`), arm/förbipasserande tas bort och dubbletter slås ihop innan betald kropp, kropp körs bara för det som ändrats. `--regler` gör samma sak på ett klipp som redan är ingestat. Taket för ett uppdrag är `--uppdragstak` (standard 1500 personrutor), allt bokförs i `scen/3d/ingest/flera/budget.json`.
5. Plats: `scen/3d/ingest/plats.py <I> --video scen/klipp/<namn>.mp4` (semantiken hittas i `<I>/semantik/`; utan semantik krävs `--scen3d` med handroller).
6. Kalla, regi, plan, ljud, Blender, film, kvalitetssida och jämförelseblad i ett svep: `scen/3d/kontrakt/kor_klipp.py <namn> <I> scen/klipp/<namn>.mp4 --bygg-kalla [--regi regi.json] [--undermapp tom] [--tillat-flaggad]`. Utdata i `scen/3d/kontrakt/ut/<namn>/<undermapp>/` (`film.mp4`, `kvalitet.md`, `blad/s<n>.png`, `tider.json`). Utan `--tillat-flaggad` vägrar renderingen när bildtrohetskontrollen flaggar en scen.
7. Granska `kvalitet.md` och bladen (källa | render). Det som kräver en människa: steg 3, bedömning av vilka scener som går att visa, och regin.

Beslut och deras ursprung: `antagen` (med skäl), `uppmatt`, `modellbedomd` (modell, promptversion och konfidens) eller från mall. Brännvidd, kort kamerabana, endast överkropp, hållning och malltyp följer reglerna i `scen/3d/ingest/regler.py` och `semantik_plats.py`; tomt rumsteg betyder okänt rum.

## Vilka filer som är pipelinen

Alla `.py` direkt i denna mapp utom tester och de som ligger i `engang/`. Engångsskript som bara användes för att ta fram ett resultat ligger i `engang/` (se dess README); de importeras inte av något här.

| Fil | Roll |
|---|---|
| **Pipelinen, i den ordning data flödar** | |
| `kor_klipp.py` | Ingång. Från färdig ingest till film: bygger kalla, kompilerar, bygger ljud, kör Blender, lägger på text, skriver `kvalitet.md` och blad. |
| `kalla_bygg.py`, `kalla_flera.py`, `kalla_plats.py` | Bygger `kalla.json` ur ingestens mappar (en eller flera tagningar) och platsfilen. |
| `kalla_handelser.py`, `handelser.py` | Lokala händelser med ursprung/konfidens; tidsankare på källklockan och förekomster efter scenredigering. Se `HANDELSER.md`. |
| `proptid.py` | Ordnade propändringar över delar av en scen. Hand-/ytfästen löses sedan av `propplan.py`. |
| `../ingest/kallstatus.py` | Varnar direkt när ingest ändrar mätfiler som ett känt källmanifest hashlåser. |
| `kalla_prop.py`, `prop_referenser.json` | Lokal komplettering med props: sparad semantik, avlästa källregioner, handledsfästen och märkta yt-/djupantaganden. Se `PROPS.md`. |
| `propbank.py`, `propplan.py` | Parametriska former med greppunkt; upplösta hand-/yt-/kamerafästen, regi och propdiagnostik. Blenderdel i `../ingest/prop_blender.py`. |
| `kompilera.py` | `kalla.json` + `regi.json` till upplöst `plan.json`. Full diagnostik som standard; `--snabb` för redigering med bevarade byggbeslut. |
| `diagnostik.py` | Full kvalitetskontroll av en sparad snabb plan. Validerar underlaget och skriver till en ny utfil. |
| `datacache.py` | Beständig, atomiskt skriven cache för kroppsmått, höjdpassning och skymningsbeslut i `ut/cache/`. |
| `gemensamt.py` | JSON-läsning/skrivning och import av `kontrollera.py`. Delas av nästan alla. |
| `kvalitet.py` | Skriver `kvalitet.md` bredvid planen. Trösklarna är våra egna. |
| `trohet.py`, `trostod.py`, `trosula.py`, `tropassning.py` | Bildtrohet mot kroppsestimatorns 2D-punkter, längdbevarande benstöd, fotsula och bordshöjd ur stilla handleder. `tro_rigg.json` och `tro_fothud.npz` är deras data. |
| `kroppmatt.py` | Oberoende silhuett mot YOLO-mask, darr och täckning. |
| `golvmatning.py`, `skymning.py`, `skymning_disk.py` | Golvbeslut ur befintliga mätningar och skymningsdiagnos mot mallens lådor. |
| `skarmtext.py`, `textenheter.py`, `textmalning.py`, `textreferens.py`, `textarbete.py` | Skärmtext: lokalisering och tid ur källrutor, redigering, ritning och 2D-komposition. `textreferens.py` läser de granskade referenserna i `textreferenser/`; `textarbete.py` är säkerhetskopia och radslut. |
| `tal.py`, `bygg_ljud.py` | Talsyntes (Piper) och ljudspår enligt tidskartan. |
| **Kontroller och verktyg som är värda att behålla** | |
| `kalla_omhasha.py` | Ny manifestkopia eller uttrycklig `--uppdatera` med originalbackup och ändringslogg. Ändrat händelseunderlag måste mätas om. |
| `kontrollera.py` | Validerar exemplen mot schemana (exit 0 = klart). |
| `verifiera_text.py` | Kör de fyra standardkontrollerna efter varandra och loggar väggtid. Skriver i `ut/fore_text/`. |
| `regression_text.py` | Färsk kompilering av notan och bar mot sparade planer. Skriver i `ut/fore_text/`. |
| `textgranska.py` | Mäter textlagrets bildmatchning mot källrutor. Ingen oberoende sanning. |
| `verifiera_korning.py`, `verifiera_blender.py` | Startar egna bakgrunds-Blender och skriver bygg-, render- och scenbevis. `verifiera_blender.py` körs bara inne i Blender. |
| `verifiera_golv.py`, `golv_jamfor.py`, `golv_sammanfatta.py` | Golvfaserna för notan: nya filmer, jämförelseblad och rapport. Skriver aldrig över äldre mappar. `golv_sammanfatta.py` har fasta siffror i texten. |
| `verifiera_tro.py`, `tro_granska_blender.py`, `tro_jamfor.py` | Trohetsfilmer, kontroll av byggd scen och jämförelseblad. |
| `verifiera_mall.py`, `mall_migrera.py` | Mallprovet. `mall_migrera.py` är en engångsmigrering som provet ändå importerar. |
| `bygg_lokalbank.py`, `mallbank_bygg.py`, `tro_export_rigg.py` | Generatorer för data som pipelinen läser: lokalmallarna i `rumsmall/`, grundbanken och `tro_rigg.json`. Kör bara när filerna ska göras om. |
| **Tester** | |
| `test_flode.py`, `test_rumsmall.py`, `test_regler.py`, `test_text_disk.py`, `test_kroppmatt.py`, `test_props.py`, `test_handelser.py`, `test_snabb.py` | `python -m unittest test_flode test_rumsmall test_regler test_text_disk test_kroppmatt test_props test_handelser` i denna mapp (ca 5 minuter). Dessutom `semantik/test_semantik.py` och `bro/test_bro.py`. |


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

## Flera tagningar, tal och ljud (notan)

Klipp som består av flera tagningar (`scen/klipp/d-dialog-notan.mp4`, sju tagningar, tre roller, svenskt tal) går genom samma kedja. Reproducera, från projektroten med `scen/.venv/Scripts/python.exe`:

```
scen/3d/kontrakt/kalla_bygg.py scen/3d/ingest/ut/notan-tagningar scen/3d/kontrakt/exempel/notan/kalla.json --video scen/klipp/d-dialog-notan.mp4
scen/3d/kontrakt/kompilera.py scen/3d/kontrakt/exempel/notan/kalla.json scen/3d/kontrakt/exempel/notan/regi.json scen/3d/kontrakt/ut/notan/plan.json
scen/3d/kontrakt/bygg_ljud.py scen/3d/kontrakt/ut/notan/plan.json scen/3d/kontrakt/ut/notan/redigerad/ljud.wav scen/3d/kontrakt/ut/notan/redigerad/ljud_rapport.json
blender -b --factory-startup --python-exit-code 1 --python scen/3d/ingest/mhr_rig.py -- scen/3d/ingest/ut/notan-tagningar/S1 scen/klipp/d-dialog-notan.mp4 --plan scen/3d/kontrakt/ut/notan/plan.json --ut scen/3d/kontrakt/ut/notan/redigerad --ljud scen/3d/kontrakt/ut/notan/redigerad/ljud.wav --render
```

`kalla_bygg.py` går in i flerklippsläget (`kalla_flera.py`) när mappen saknar `meta.json` men har undermappar `S1`, `S2`, ... Scenerna är tagningarna och deras bildintervall, varje scen har egen kamera (`kam_s1`), eget rum (`rum_s1`) och egna personsekvenser. Ingest-id är per tagning ("1" i nästan alla mappar), så `matning.personer[]` har `scen` och `ingest_id` och `person` är klippnivåns roll (A, B, C). Rollerna och beaten kommer från den handkalibrerade `scen3d.json` (status `antagen`, inte mätt); beat översätts till harnessens `funktion` (hook = krok, build-up = uppbyggnad, turn = vandning, punchline = punchline, payoff = avslut) och `reaction` får null. Ordtider kommer från `scen/3d/data/ordtider.json`. Körloggen (`tider.json`) hashlåses inte eftersom den skrivs om vid varje ingest-körning.

Schemaändringar (alla valfria fält, bars kalla är oförändrad): `matning.personer[].scen` och `.ingest_id`, `matning.kameror[].kalla_ruta0` (källruta som mätningens ruta 0 motsvarar), `semantik.props[].scen`, och `roll_kalla` har fått värdet `scen3d`.

Kompilatorn ger en plan med nycklarna `scener` (egna mätfiler per scen) och `tal`. `byt_replik` löses till en röstinstruktion med lucka i utdatatid. Policyn `samma_lucka` jämför den nya textens längd i normaltempo (Piper, brus 0, deterministisk) med originaltextens: högst 3 % längre är `passar`, upp till `max_talfaktor` (1,15) är `stracks` med angiven procent, mer är `nekad` och hamnar i `ej_tillampat`. En replik som scenedits klipper mitt i, eller som ligger i en tyst eller bortklippt scen, byts inte. `forlang_scen` och andra språk än svenska stöds inte.

`bygg_ljud.py` bygger ljudspåret: originalljudet enligt tidskartan, och i varje ersatt lucka (plus 40 ms) tas originalet bort helt och den syntetiserade repliken läggs in med nivå efter originalets RMS. Tal och bakgrundsljud är inte separerade, så rumsljudet i luckan försvinner också. Syntesen är Piper via `../roster.py` med cache i `ut/notan/tal_cache`. Munnen följer inte den nya texten. `mhr_rig.py --plan` med `scener` bygger tagningarna i följd i en tidslinje (egen gravitation, kamera och rum per scen, färg per roll över alla scener, en renderkamera) och muxar med `--ljud` ett mp4 (`film.mp4`). Tagningarna ligger i olika världssystem och är inte registrerade mot varandra.

## plats: en plats för alla tagningar (kalla/1, valfria fält)

Ett klipp utspelar sig på en eller flera **platser**. En plats äger EN värld (meter, +Z upp, golv), rummets geometri (golv, väggar, sammanslagna objekt) och **ankare**: namngivna ställen (`stol_A`, `bordskant_A`, `staplats_C`) med läge och riktning. Varje scen pekar på en plats (`plats_id`), har en transform från tagningens egen Blender-värld in i platsen, och personerna är bundna till ankare per scen (`bindningar`: A sitter vid `stol_A`). Tagningarna är alltså kameror i platsen; rummet tillhör platsen, inte tagningen. Ingest-steget `scen/3d/ingest/plats.py` skriver `plats.json` (hashlåst pekare i kalla); `kalla_bygg.py` läser den om den finns (`--plats`, eller `<ingestmapp>/plats/plats.json` i flerklippsfallet).

| Var | Fält |
|---|---|
| `semantik.platser[]` | `id`, `typ`, `beskrivning`, `ankare[]` (`id`, `typ` = sate/bordskant/staplats/annat, `etikett`), `objekt[]` |
| `semantik.scener[]` | `plats_id`, `bindningar[]` (`person`, `ankare`, `hallning`, `status`) |
| `semantik.props[]` | `plats_id`: `rum_ref` är objektets id i platsen |
| `matning.platser[]` | `fil` (plats.json), `koordinater`, `golv`, `ankare[]` (`pos_m`, `riktning_rad`, `hojd_m`, `status`, `osakerhet_m`), `registreringar[]` per scen: `till_plats` (`yaw_rad`, `translation_m`, `skala`, `matris`), `metod` (identitet, matchning, landmark, antagande), `status`, `skala_status`, `residual_m`, `kommentar` |

Äldre kalla utan platser gäller som förr (barexemplet är oförändrat). Ytor och väggar har ett reserverat fält `textur: null` i plats.json, så att källbildens bakgrund senare kan projiceras på dem från tagningens kamera; ingenting texturerar än.

Kompilatorn bygger platsens rum en gång (`plan.objekt`, varje objekt med `synlig_ut` över hela utdata när det är oförändrat i alla scener) och lägger varje scens personer och kamera i platsen med `plan.scener[].till_plats` (4×4). `plan.plats[]` har golv, ankare och vilka scener som hör dit. `mhr_rig.py --plan` bygger rummet en gång och placerar personerna med transformen; utan `--plan` är beteendet oförändrat. Skala utom 1,0 stöds inte av byggaren.

**Platsbyte (`byt_miljo`, mot en plats med ankare).** `rum = {kalla: "bank", tillgang_id: <plats-id>}` hämtar platsen från platsbanken (`plats_bank/<id>.json`, eller `--platsbank`). Ersättningsplatsen behöver bara ha ankare med samma namn (eller de som `ankare[{fran, till}]` kopplar ihop). Scenens transform räknas om så att scenens första bundna person (i person-id-ordning) hamnar på motsvarande ankare, med dess riktning; kameran följer med personen, så bildutsnittet mot personen bevaras. Saknas platsen i banken, har scenen ingen plats, eller har ingen bunden person ett motsvarande ankare, hamnar editen i `ej_tillampat` med orsak (atomiskt för alla valda scener). `rum.kalla` ord/upload/neutral stöds inte (ingen plats finns att byta till). Testplatsen `plats_bank/fiktiv_lokal.json` är **påhittad** (ingen kund, ingen mätning). Provkörning: `exempel/notan/regi_byt_lokal.json`.

Mätning, antaganden och per-tagning-kvalitet för notan står i `scen/3d/ingest/ut/notan-tagningar/plats/plats_matt.json` och `plats.md`.
 
## Rumsmall: möbler efter layout

`rumsmall/` är den enda mallbanken: ett restaurangbord för två, notans två separata bord, en bar och en fiktiv kundlokal. Schemat beskriver golv, vägg, bord, stol, bardisk, hylla, fönster och lampa med mått, material och lokala stödankare. Tal märks `mall`, påhittade lokaler även `fiktiv: true`. Modellreferens och ytprojektion reserveras. `plats_bank/fiktiv_lokal.json` är en bakåtpekare.

Välj med `hand.json` → `rumsmall` eller `plats.py --rumsmall <id>`. Annars väljer flera tagningar restaurang för två sittankare, bar i övriga fall. Äldre ensamma tagningar kräver uttryckligt mallval. Namn, typ och riktning styr rigid passning med skala 1 och golvet låst. Varje ankares avstånds- och vinkelfel samt viktad RMS sparas före lokal anpassning. Stolar och bord fästs sedan till uppmätta ankare, med justeringarna redovisade. Djupfragment sparas endast som evidens.

Källans valfria `rumsmall_id` och mätdelens `rumsmall` refererar till den passade instansen i hashlåst `plats.json`. Regins `byt_miljo` (harnessens `byt_lokal`) accepterar `rum.rumsmall_id` eller `tillgang_id`; bindningar följer namn och typ. Saknat eller feltypat ankare nekar bytet.

`mhr_rig.py --plan` bygger möblerna en gång. Sitt/ståankare stöder bara ben med `ben_synliga=false`; ryggrad, armar, huvud och synliga ben skyddas. Saknad flagga betyder skyddad. `stod_rapport.json` anger leder, rutor och benlängdsändringar. Ingest saknar finare synlighetsdata. Okända obundna personer kräver en ledig mallsits inom 0,35 m (antagen tolerans), annars utelämnas de med skäl. Utan plan används den tidigare byggvägen.

Lokalt slutprov: `scen/.venv/Scripts/python.exe scen/3d/kontrakt/verifiera_mall.py`. Det hittar Blender via `ingest_klipp.py`, startar egna bakgrundsprocesser, bygger ljud och tre filmer i nya `ut/notan/mall_*` samt två översikter per lokal. Ingen öppen Blender-session används. Tidmätning ligger i `tider_mall.json`, och exakt kroppsstöd i respektive byggmapp.

## Bildtrohet och längdbevarande stöd, 10 november

`kompilera.py` mäter nu bildtrohet med numpy och sparar `kvalitet.bildtrohet` i planen samt `*_trohet.json/.md` bredvid CLI-planen. `matkamera` bevarar kameran före regins kameraändringar. Exakta par mellan MHR70 och de byggda rigglederna jämförs med kroppsestimatorns sparade 2D-punkter: median/p90 i källpixlar och bboxandel samt IoU mellan samma leders omslutningar. Dolda ben och utelämnade personer redovisas separat. Hudpunkter som näsa/öron är inte riggleder och räknas inte som sådana. Egna diagnostiska gränser är 20/40 px, 4/8 % och IoU 0,65; de har marginal över de goda notanscenerna och bars befintliga stabiliseringsrest. En flaggad plan kräver `mhr_rig.py --tillat-flaggad` för diagnostisk rendering.

(Upphävt av GOLV2, se nedan: kamerakompensationen för golvstegets `cam_t`-skala är borttagen ur `kompilera.py`. Kroppen läses i stället utan skalan.)

`trostod.py` ersätter stödet i planer med `benlangder_m`: konstanta personmått är medianer av de befintliga posernas ledavstånd, gemensamma över personens scener. Den generiska `rest` är inte personens anatomiska vilopose. Endast uttryckligen dolda ben ändras; bäcken, överkropp och handleder skyddas exakt. Överkroppens redan varierande ledavstånd kan därför inte samtidigt låsas till generisk `rest`. Stolen får sitshöjd 0,35–0,65 m (antaget mallintervall), efter mätt bäcken minus mallens mjukdel. För korta ben får hänga. Stående stöd väljer knäböjning och nåbar golvpunkt före ändring av bäcken. `trosula.py` beräknar faktisk fothud med lokala FBX-benvikter, med 0,1 mm säkerhetsmarginal. Uppmätta riggdata finns i `tro_rigg.json` och `tro_fothud.npz`; exporten använder en egen Blender-bakgrundsprocess.

`tropassning.py` passar bord till lägsta stilla handledsfönster över minst 12 rutor (antaget: högst 3 cm höjdvariation och 8 cm XY-spann). Bordintervallet 0,65–1,05 m är antaget. Handledshöjden är mätt; att stillheten betyder bordkontakt är ett osäkert antagande och skyddade handleder flyttas aldrig. Planen redovisar fönster, klippning mot intervallet och handledsgap per person/scen. Dessa passningar ligger bara i planen; hashlåsta ingestfiler ändras inte.

Slutprov: `verifiera_tro.py`, `tro_granska_blender.py` och `tro_jamfor.py`. Resultat och granskning finns i `ut/notan/tro_rapport.md`, filmer i `tro_tom/` och `tro_redigerad/`, blad i `tro_jamforelse/`. Äldre mappar bevaras. Bars byggdata är oförändrade; planen har nya diagnostikfält.

## Golvcues och synlighet, fortsatt uppföljning 10 november

`plats.py` prövar fötter med egen bbox, unionmask och benpunkter, djupgolv, fasta benmått, möbelpriorer och sist kamerahöjd. Värde, antaget felintervall, användning och avvisningsskäl sparas per tagning och poolat i `golv.matning`. Ett gemensamt golv får olika kamerahöjder via tagningarnas Z-transform. Cuespann över 10 cm flaggas. `uppmatt` kräver överensstämmande direkta oberoende cues; annars står `antagen` och skälet. Skala 1,0 prövas mot möbelavstånd och djupets sparade skalkontroll men kroppar skalas aldrig om för att tvinga priorerna att passa. En ensam tagning får diagnostik men behåller sitt gamla golv; endast `--tillampa-golv` aktiverar alternativet.

De tidigare breda möbelintervallen ovan ersätts i planpassningen av uttryckliga priorer: bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm. Root är ingen inmätt sittyta. Handledsrester och klippning mot priorerna redovisas. Dolda knän får sjunka så att fötterna når utan bensträckning. Maskverifierade synliga lår och knälägen skyddas även när ingest markerar vristerna som dolda; deras ursprungliga mätvariation behålls, medan ändrade segment har fasta personmått. Den gamla synlighetskommentaren kallade felaktigt MHR70 13–14 för knän; de är vrister.

`skymning.py` testar mallådor mot synliga källmaskprov med sparat kroppsdjup och mätkameran. Det är en uppskattad provandel, inte exakt hudarea. Över 2 % med 5 cm djupmarginal utelämnas konfliktande mallinstans i just scenen när skyddade ankare och saknade fotavtrycksintervall hindrar en underbyggd justering. Omvänd skymning rapporteras bara. CLI-kompilering och `trohet.rapport(plan, planfil)` skriver alltid `kvalitet.md` bredvid planen: bildfel, golv/skala, spridning, ledändringar, skymning och bra/granska/dålig med skäl. Trösklarna är egna diagnostiska val. Lokalt prov: `verifiera_golv.py`, därefter `golv_jamfor.py` och `golv_sammanfatta.py`; se `ut/notan/golv_rapport.md`.

## Textlager och lokalkoder (lokalt, utan nya modelljobb)

`kalla.semantik.skarmtext[]` kan nu ha `typ` (overlay/undertext), `replik`, `box` (X/Y/bredd/höjd i källpixlar), `stil` (font, storlek, justering, färg och kontur), `ursprung` och `konfidens`. Tiderna är halvöppna på källklockan. `skarmtext` i regi använder den befintliga operationen med `lagg_till`, `byt` eller `ta_bort`; box och stil kan också ändras. Planen får upplösta `ut`-intervall. En lyckad `byt_replik` ersätter texten i alla undertexter som pekar på repliken. Nekade talbyten påverkar inte undertexten.

Ingen OCR finns i den använda venv:en. `skarmtext.py` söker kända strängar i färg-/kontrastmasker. `textreferenser/` innehåller redovisade pixelreferenser när den generiska fontsökningen inte räcker: manuellt avlästa boxar och radbrytningar, därefter synlighet mätt ruta för ruta. Font är närmaste installerade font, alltså en approximation. Misslyckad lokalisering får en uttryckligen antagen standardbox. Tal och kg på samma rad får gemensam synlighet; den samhörigheten märks antagen.

`kor_klipp.py` gör transparenta PNG-textlager med Pillow och lägger dem över renderingen med ffmpeg som sista 2D-steg. Samma filter skriver film och bladens PNG-rutor. Det är enklare än Blender-kompositorn eftersom PNG-sekvens och tidskarta redan finns; texten behöver ingen 3D-nyckling och skyms inte av möbler. `render/` är utan text, `textlager/` har alpha och `komposit/` är de färdiga rutorna.

`rumsmall/lokalkoder.json` är vår egen mapping för alla sex `lokal[]`-koder i kundlinjerna. `bygg_lokalbank.py` skapar parametriska mallar av befintliga deltyper. Chark-, glass- och serveringsdisk är specialiseringar av disk/kassa. `fiktiv_mandisk` är en helt påhittad miljö för miljöbytesprovet. Personal och kund står på motsatta ankare; `kamera_bindning` binder scenens kamera till ett ankare med bibehållen lokal kamerarörelse. Ett miljöbyte kan flytta kamerans och personens ankare var för sig.

Bildskyddet i ingest begränsar hur mycket stabiliseringen får flytta den sparade kroppens tillförlitliga 2D-observationer. Det är fortfarande egenprojektion mot kroppsestimatorn, inte ett oberoende riktighetsmått. Diagnostikens trösklar i `trohet.py` är oförändrade. Lokala ändringar och säkerhetskopior för textarbetet finns i `ut/fore_text/`; ingen betald kroppskörning behövs för dessa ändringar.

Bakgrundsvertikaler mäts lokalt med OpenCV och grupperas per kamerauppställning; osäkra flyktpunkter avvisas och ärvda riktningar märks antagna. Regeln för kort kamerabana nollar bara translationen och behåller uppmätt rotation. `textreferenser/disksidor.json` redovisar de källrutor där kameran faktiskt står på personalsidan. `diskprojektion.py` redovisar rest mot avlästa diskkanter; diskhöjd och kontakt är fortfarande osäkra.

`oppen_mitt` är en mallapproximation av en monter med öppen mitt: ram och låg sockel av befintliga låddelar, utan renderat glas. Vid skymningskonflikt prövas enstaka ramdelar före hela disken; samma gräns på 2 % gäller. Det kan ge en alltför gles disk och ersätter inte källans möbelgeometri. Se den visuella slutbedömningen i `ut/fore_text/rapport.md`; godkänd egenprojektion betyder inte en färdig kundfilm.


## Kvalitetssidan efter 10 nov (jämn-passet): vad siffrorna betyder och inte betyder

- **Avvikelse från estimatorns 2D** (förr "bildfel") är avståndet mellan de byggda ledernas projektion och kroppsestimatorns EGNA 2D-punkter. Den är inte oberoende: det gamla bildskyddet passade mot samma punkter, så p90 låg på 6,0 px av konstruktion. Dessutom är 42 av de 48 mätta punkterna fingerleder, så siffran säger lite om kroppens läge. En scen kan inte bli bättre än "granska" på den siffran ensam, och den ger aldrig "dålig" ensam.
- **Silhuett-IoU mot källans personmask** (`kroppmatt.py`) är den oberoende kontrollen: hudnätet (MHR lod1, skinnat med de byggda lederna i numpy, kontrollerat mot modellens utdata, medelfel < 1 mm) projiceras i den spårade kameran och jämförs med YOLO11-seg-masken (en annan modell än estimatorn) inom personens egen spårruta, på alla rutor där masken finns, även de opålitliga. Redovisas som IoU, IoU synlig (nätet klippt vid maskens nedersta rad, för skymmande disk), tyngdpunktsfel i andel av bildhöjden och en referens-IoU för estimatorns egna hörn mot samma mask. Den **underskattar** IoU (masken har kläder, hår och hållna föremål; nätet är en naken standardkropp; masken är grov, 4 px per maskpixel; fingrar saknas) och kan **överskatta** när en stor kropp täcker en liten mask i en trång ruta. Referens-IoU för rå estimat ligger på 0,58–0,80 i b, så gränserna sattes under det.
- **Darr** = medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd och rå estimatorpose. Mäter tremor och verklig acceleration tillsammans; en snabb gest ger också darr.
- **Täckning** = rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen, med orsak till uteblivna rutor: personen ej spårad (ej i bild), opålitlig ruta (under 35 % av kroppspunkterna i bild eller 15 % i masken), rådata saknas. Opålitliga rutor hoppas över i avvikelsemåttet men INTE i silhuettmåttet.
- **Betyg.** Våra egna gränser (`kvalitet.GRANSER_KROPP`), satta i förväg: IoU synlig bra ≥ 0,65, dålig < 0,50; tyngdpunktsfel p90 > 3 % granska, > 6 % dålig; darr byggd > 1,5 granska, > 3,0 dålig; täckning under 60 % granska. Ingen gräns är avstämd mot ett krav från ägaren eller justerad för att scener ska passera.
- **Kamerabana**: `kamerabana_rimlig` (ingest/regler.py) flaggar en metrisk bana med p90-fart > 5 m/s, maxfart > 15 m/s eller sträcka > 5 m/s × scenens längd (egna gränser för en handhållen mobil inomhus).

### Filer tillagda
| Fil | Roll |
|---|---|
| `kroppmatt.py`, `tro_hud.npz`, `tro_export_hud.py` | Silhuett, darr och täckning. `tro_hud.npz` är hudnät, trianglar, benvikter (lod1.fbx) och standardkroppens vilopose; `tro_export_hud.py` körs bara i Blender när filen ska göras om. |
| `kalla_omhasha.py` | Kopia av en kalla.json med omräknade hashar (efter omkörning av ingest-filer). `kor_klipp.py --kalla kalla_jamn.json` använder den. |
| `test_kroppmatt.py` | Tester: silhuett (egen mask ger IoU ≈ 1, förskjuten kropp flaggas), skinning mot modellen, darr, utjämning (brus, rör, luckor, trasig ruta, benlängd), kamerabana. |

### Disk och hylla (10 nov)
Mallens `bardisk` med `oppen_mitt` (monter) byggs nu som massiv underdel, bakpanel mot personalsidan, massiva gavlar, arbetsyta på personalhalvan och öppen glasfront mot kundsidan (stolpar och överkant; glaset ritas inte). Förr: tunna skenor som inte läste som en disk. En hylla med `oppen_mitt` (glasmonter på disken) är bottenplatta, takplatta och fyra stolpar. Vanlig `hylla` (bakre hylla bakom personalsidan) har bakpanel, två gavlar och fyra hyllplan. `skymning.py` kontrollerar dessutom varje kroppsdel (huvud, överkropp, höft, armar/händer, ben/fötter) mot egen gräns, 10 % av delens maskprov och minst 8 prov, var tredje ruta; en tunn skena över höften kunde förr vara < 2 % av alla prov och gick obemärkt. Konflikt löses som förut (utelämna den eller de delar som krävs i just den scenen, `antagen`, med skäl i `kvalitet.skymning.atgarder`); det finns inget måttintervall att justera inom och ankaren flyttas aldrig.

## Lokal rekvisita

Kör `kalla_prop.py` efter färdig ingest och före `kor_klipp.py --kalla kalla_prop.json`. Originalkällan skrivs aldrig över. Se `PROPS.md` för kommandon, mätning, grepp, regi, kvalitetsmått och begränsningar.

Metodtabellen i `ut/jamn_tabell/tabell.md` har rättats: dolda ben ska uteslutas, inte alla fingerleder. Alla metoder använder nu samma ledurval och medianidentitet som filmen. 2,52/5,17 px för b s1 gällde bara två axelleder; filmens 44 synliga ledpar ger 15,73/48,50 px.

## Steg 10, återupptagning med props som data

Aktuell granskning och reproducerbara kommandon finns i
`ut/aterupptagning/rapport.md`. `kalla_handelser.json` för b och notan innehåller
props och lokala händelser; övriga klipp har `kalla_prop.json`.
Nya dataresultat ligger i `ut/<klipp>/data_prop/`: regi, plan och kvalitet,
utan byggd film. Provet med den uttryckligen påhittade produkten ligger i
`ut/b/data_prop_byte/`. Händelsestyrda byten har egna data-mappar.

Planens befintliga backendnamn är fortfarande `blender_mhr`. Ingen
webbläsaradapter infördes i detta uppdrag. Propbankens former, grepppunkter,
upplösta 4×4-matriser, synlighet och händelser är data som en sådan adapter
kan läsa. `ingest/prop_blender.py` och den tidigare kamerahanden finns kvar
bakom sina befintliga gränssnitt; ingen ny Blenderbyggnad eller rendering
gjordes i återupptagningen. Gamla `tom3`, `jamn_tom` och den redan färdiga
`jamn_tom_rattad` är bevarade.

`test_plats_snapshot.py` är stöd till platsprovens historiska indata, inte
en pipelineingång. Frysta stödposer och deras ursprung beskrivs i
`testdata/README.md`. Engångsverktyg för återupptagningen ligger i `engang/`.


## Snabb kompilering vid redigering

`kompilera(kalla, regi, snabb=True)` och `kompilera.py ... --snabb` löser samma
byggplan utan bildtrohetsmätning, silhuett, darr eller övrig kvalitetsdiagnostik.
Källkontroll, filhashar, höjdpassning, knäskydd, skymningsbeslut, props och
händelseankare körs fortfarande. Snabbvägen kan därför utelämna en mallbit av
samma skäl som full kompilering. Den tar aldrig bort den kontroll som styr
geometrin. Flaggan är frivillig; `kor_klipp.py` och vanliga funktionsanrop
behåller full diagnostik som standard.

Kör från projektroten med `PYTHONIOENCODING=utf-8`:

```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kompilera.py scen/3d/kontrakt/ut/notan/kalla_handelser.json scen/3d/kontrakt/ut/notan/regi_prop_tom.json scen/3d/kontrakt/ut/notan/min_snabbplan.json --snabb
scen/.venv/Scripts/python.exe scen/3d/kontrakt/diagnostik.py scen/3d/kontrakt/ut/notan/min_snabbplan.json scen/3d/kontrakt/ut/notan/min_kontrollerade_plan.json
```

En snabb plan har `kvalitet.diagnostik: ej_kord` och
`kvalitet.bildtrohet.flaggad: true`. Den är alltså inte kvalitetsgodkänd.
Separat diagnostik använder planens lösta geometri och mätkamera; den gör inga
nya ingeststeg. Ändrade mätfiler eller video stoppar kontrollen och kräver ny
kompilering. Välj nya utfilnamn. Kompilatorns vanliga CLI kan skriva över sin
utfil; diagnostikkommandot vägrar skriva över en befintlig fil.

`ut/cache/` överlever nya Pythonprocesser och är härledda data. Nyckeln tar med
relevanta mätfiler (absolut sökväg, storlek, ändrings-/skapandetid med ns),
kodhash, riggdata, geometri, kamera och tidsurval. MHR-rigg och kod
innehållshashas. Kroppsmåttet behåller dessutom högst 32 sammanfattningar i
processen. Cacheinnehållet har kontrollsumma; saknad, trasig eller oskrivbar
cache leder till omberäkning. Inga maskrutor utelämnas av cachen. Extern
ersättning av en fil måste ändra filstämpeln; bevara inte både storlek och
alla tidsstämplar vid manuell ändring. Cachemappar kan lämnas åt sidan för en
helt kall mätning. Första beräkningen av ett nytt tidsurval eller ny geometri
kan fortfarande ta längre tid än en återanvänd beräkning.

Proven som gäller edits och byggdata använder den riktiga snabbvägen.
Diagnostikalgoritmerna prövas fortsatt i `test_kroppmatt`, och `test_snabb`
kontrollerar full standardkörning, separat diagnostik, oförändrad byggplan,
cache över processgräns och ogiltigförklaring. Kör en modul åt gången från
projektroten, exempelvis:

```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10c_mata.py efter test_flode test_rumsmall test_regler test_text_disk test_kroppmatt test_props test_handelser test_snabb semantik.test_semantik bro.test_bro test_rum
```

Mätprotokoll: `ut/steg10c/`, med före/efter per modul och per edit.
Återupptagning och exakta kommandon: `STEG10C-LOGG.md`.
Modellbytesinventering: `MHR-BEROENDEN.md`; ingen SOMA-anpassning är gjord.

Uppmätt på notan (en edit, egen process, 10 november 2026): full kompilering 68,8 s (trim), 92,6 s (text), 95,3 s (prop). Snabbväg kall cache 7,5–9,5 s, varm cache 0,79 s för alla tre. Den upplösta planen är i övrigt byte för byte lika; endast `kvalitet.*` och `varningar` skiljer. Hela kontraktssviten: ca 2,5 min med varm cache, ca 5 min med kall cache (tidigare ca 26 min, mest `test_flode` och `test_text_disk`).


## Steg 11: snabbvägen under en sekund

Mätt 10 november 2026 i en långlivad process (`engang/steg11_mata.py`, tom cache vid start). Före/efter står i `STEG11-LOGG.md`.

- **Skymning per källruta.** `skymning.py` räknar allt som inte beror på kamera, regi eller lådor en gång per person och källruta (`skymning_ruta`, beständig i `datacache`), och minns träffbitarna per låda, kamera och ruta (`skymning_traff`). Lådorna räknas nu flera åt gången (`boxdjup_flera`, samma uttryck som `boxdjup`, bevisat bit för bit lika). Ett nytt tidsurval (trimning, borttagning, flytt, kopia) väljer därmed bland färdiga rutor. `skymning.forvarm(plan)` räknar alla källrutor, inte bara var tredje; webbvärldens kompilatorprocess gör det efter grundkompileringen.
- **Källkontroll.** `kontrollera.sha_fil` minns sha256 per (sökväg, storlek, ändrings- och skapandetid). Minnet är tomt i en ny process, så en kommandoradskörning hashar allt som förut. `gemensamt.kontrollmodul` laddas en gång per process (den körde förut sin CLI mot `exempel/bar` vid varje anrop), scheman lintas en gång per filstämpel, och `datacache.kodnyckel` minns innehållshash på samma sätt. Gräns: en fil som byts ut med oförändrad storlek, ändrings- och skapandetid upptäcks inte i en långlivad process.
- **Tal utan syntes.** I snabbvägen syntetiseras inget. Posten i `plan.tal` får `ljud: "vantar"`, text, lucka och `langd_kalla`: `matt` om båda längderna redan ligger i talcachen, annars `uppskattad` (originalet fyller sin lucka, den nya texten i proportion till teckenantalet). Mätt längd över gränsen nekar editen som förut. Uppskattad längd över gränsen nekar inte: editen ligger kvar med `regel: over_gransen_uppskattad` och en varning. `tal.syntetisera_plan(plan)` är det separata steget (körs också av `diagnostik.py`): det mäter, syntetiserar, sätter `ljud: "klart"` och utvärderar regeln på riktigt.
- **Unika text-id.** En kopierad scen (`duplicera_scen`) får texterna `<id>@<kopians scen-id>`; originalscenen behåller sitt id.
- **Schemafel enskilt.** Princip: en edit tillämpas helt eller inte alls (atomiskt, `test_fel_edit_ar_atomisk`). En edit som bryter regi-schemat avvisas nu som enskild edit (`ej_tillampat`, orsak med schemats felmeddelande) och resten gäller. Oförändrat avvisas hela regin vid fel i kalla, i regins huvud och vid referensfel (okänt scen-id, händelsetid).
- **Kortbyte och lokalbyte.** Schema: `byt_prop` och `lagg_till_prop` har `tillgang_kalla` (`propbank` eller `kort`); `byt_miljo.rum.kalla` har värdet `platta`. Ett kort bär `tillgang = {id, kalla, geometri}` på objektet i planen; en plåt eller uppladdad bild ger `plan.lokalbyte` (och `lokal` i scenens rad). Geometri som inte finns märks `ej_byggd`; kortets låda och scenens uppmätta rum står kvar som platshållare. `tillgang_id` utan `tillgang_kalla` och okänd `bank`-plats nekas som förut. Ingen Blender-byggnad är gjord.

Prov: `test_steg11.py`. Kör en modul åt gången.
