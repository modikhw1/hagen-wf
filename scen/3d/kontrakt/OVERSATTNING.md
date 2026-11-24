# Översättning: kontraktet mot de tre andra modellerna

Kontraktet (`kalla.json`, `regi.json`) är utgångspunkten. Tabellerna visar vad varje fält i harnessen, hagen-ui och den gamla scenmotorn blir i kontraktet, och tvärtom. "Ingen motsvarighet" betyder att fältet inte kan uttryckas på andra sidan utan att något går förlorat eller byggs till.

Sökvägar till hagen-ui är relativa till `C:\Users\praiseworthy\Desktop\hagen-ui\artifacts\api-server\src\lib\`. Radnummer gäller koden som den såg ut 9 nov 2026.

## (a) Harnessens scenplan mot kalla och regi

Källor: `video/format/h-scener.mjs` (`scenplan`, rad 19–32), `video/format/h-anpassa8.mjs` (schema, rad 30–45), exempel `data/format/harness/pass6/scenplaner.json`.

### Fält

| Harness | Blir | Anmärkning |
|---|---|---|
| `beats[].nr` | `semantik.beats[].nr` | |
| `beats[].funktion` | `beats[].funktion`, och `scener[].funktion` när beatet motsvarar en scen | Samma sju värden. |
| `beats[].bar` (`karna`, `stod`, `fri`) | `beats[].bar`, `scener[].bar` | |
| `beats[].vad` | `beats[].vad` | |
| `beats[].bunden` (v5-kortet) | `beats[].bunden` | Värden: produkt, lokal, person, trend, redigering. |
| `beats[].atgard` | `regi.edits[]`, en eller flera operationer med `ursprung.typ = harness-forslag` | Se verbtabellen. Åtgärden lagras aldrig i kalla. |
| `beats[].skal` | `ursprung.harness.skal` | |
| `beats[].omrendera` | ingen egen post | Härleds: sant för byt_produkt, byt_lokal, frontfigur, eget_tal, forenkla. |
| `omrendera`, `karnaRor`, `risk`, `sammanfattning` | ingen motsvarighet | Sammanfattning per klipp. Räknas om ur regin. |
| beats saknar tider | `beats[].scen` är `null` tills en scen är bunden | Ingen kod binder beat till tidsintervall i dag. |
| `scener[].vad` (h-anpassa8) | `lagg_till_scen`/`byt_miljo` fritext, eller `ursprung.harness.skal` | Kundens version av scenen, inte källans. |
| `scener[].bild` | `byt_miljo.rum.beskrivning` | |
| `scener[].replik` | `byt_replik.text` eller `lagg_till_replik.text` | Bara satt om repliken bär skämtet. |
| `aterbruk` (premiss, ryggrad, bada) | `ramar`: ryggrad = `bevara_beats: ["alla"]` och `tillat_retiming: false`, premiss = repliker låsta | Tolkning, inte exakt. |
| `tight` | `ramar.tillat_retiming`, `max_talfaktor` | Fritext utan tider i harnessen. |
| `tillat[]` | `tillat` per post | Villkorad tolerans: förlagans drag får vara kvar men tvingas inte. |
| `undvik[]` | `flagga` (`allvar: risk`) per post | Ingen maskinkontroll finns, bara en synlig markering. |
| `karna` | `semantik.intention.karna` | |
| `titel`, `brief`, `ratt_om` | ingen motsvarighet | Text till kunden, påverkar inte rendering. |
| e4-lagrets `krok`, `vandning` | `intention.krok.finns`, `intention.vandning.finns` | `kalla = modellbedomd`. |

### Verb

| `atgard` | Operation | Anmärkning |
|---|---|---|
| `behall` | ingen operation | Beatet listas i `ramar.bevara_beats`. |
| `byt_produkt` | `byt_prop` (eller `lagg_till_prop` om produkten saknas) | |
| `byt_lokal` | `byt_miljo` | |
| `frontfigur` | `casta` | Roll och utseende väljs av CM. |
| `eget_tal` | `byt_replik` eller `lagg_till_replik` | Texten skriver CM. Harnessen anger bara verbet. |
| `forenkla` | `forenkla` | |
| `fritt` | `fri_scen` | `platshallare` eller `stryk`. |
| `risk` | `flagga` | |
| `byt` (bara h-anpassa8) | `byt_prop`, `byt_miljo` eller `casta` | Verbet anger inte vad som byts. CM väljer. |
| `tillat` (bara h-anpassa8) | `tillat` | |

Exempel på ett harnessförslag i regin:

```json
{"id": "e7", "op": "casta", "person": "1",
 "ursprung": {"typ": "harness-forslag", "godkand_av_cm": null, "tid": null,
  "harness": {"atgard": "frontfigur", "beat_nr": 2, "funktion": "uppbyggnad",
   "skal": "Blondin tar rollen: ...", "kalla_fil": "data/format/harness/pass6/scenplaner.json"}},
 "kundroll": {"id": "PLATSHALLARE:roll_1", "namn": null}, "utseende": {}, "rost": null}
```

## (b) Kalla och regi mot hagen-ui

Källor: `timeline/types.ts`, `timeline/ops.ts`, `timeline/rails.ts`, `customer-card/index.ts`. hagen-ui lagrar ett löst tillstånd per scen (`TimelineOverrides`), kontraktet lagrar en ordnad logg. hagen-ui har ingen mätning och ingen rendering.

### Kalla mot `TimelineBase`

| Kontrakt | hagen-ui | Skillnad |
|---|---|---|
| `klipp.id` | `TimelineBase.conceptId` (`types.ts:60`) | |
| `tidsbas.langd_s` | `durationSec` (`types.ts:61`) | hagen-ui har ingen fps eller ruttid. |
| `scener[]` | `scenes: Scene[]` (`types.ts:33`) | hagen-uis scen motsvarar ungefär ett beat. |
| `scener[].start_s`, `slut_s` | `Scene.start`, `end` (`types.ts:36–37`) | Samma enhet, sekunder. |
| `scener[].segmentering` | `boundarySource` (`types.ts:38`, `cut`/`word`/`model`) | Delvis: `klippdetektering` är `cut`, `harness` är `model`. |
| `scener[].funktion` | `Scene.role` (`types.ts:40`, `SceneRole` rad 18) | Se rolltabell nedan. |
| `scener[].bar` | ingen motsvarighet | |
| `scener[].syfte` | `Scene.purpose` (`types.ts:42`) | |
| `scener[].miljo` | `Scene.setting` (`types.ts:44`) | hagen-ui har en fri text, kontraktet ett id. |
| `scener[].personer`, `kamera` | ingen motsvarighet | `direction.framing` (`types.ts:49`) är fri text. |
| `beats[]` | ingen motsvarighet | hagen-ui har ingen skild beatnivå. |
| `repliker[]` | `Scene.speech.lines: SpeechLine[]` (`types.ts:29`, `:47`) | `speakerId`, `text`, `words`, `locked`. |
| `repliker[].ord[]` | `Word` (`types.ts:25`) | `w`/`start`/`end`/`speakerId`. Ingen `sannolikhet`. |
| `repliker[].sprak`, `i_bild` | ingen motsvarighet | hagen-ui lagrar inte språk eller om talaren syns. |
| `personer[]` | `TimelineBase.speakers` (`types.ts:64`) | `{id, label, locked}`. Ingen roll eller beskrivning. |
| `props[]` | `Scene.direction.props` (`types.ts:49`) | Bara en lista namn. Inget stöd, fäste eller mått. |
| `rum[]` | `Scene.picture.venue` (`types.ts:46`, `source`: bank/upload/words/neutral) | Ingen geometri. |
| `skarmtext[]` | `Scene.screenText` (`types.ts:48`, `ScreenText` rad 26) | |
| `ljud` | `speech.duckOriginal` (`types.ts:47`), `mechanic` (`types.ts:66`) | Delvis. |
| `intention` | ingen motsvarighet | `TimelineBase.intent` (`types.ts:68`) betyder syfte A/B/C, inte krok/vändning. |
| `serie` | ingen motsvarighet | |
| `matning.*` | ingen motsvarighet | hagen-ui har inga mätfiler. |

| `funktion` | `SceneRole` |
|---|---|
| krok | hook |
| uppbyggnad | setup |
| vandning | turn |
| punchline | payoff |
| avslut | outro |
| visning, tilltal | `other` (ingen motsvarighet) |

### Regi mot `TimelineOverrides`, `TimelineOp` och `CustomerCard`

| Kontrakt | hagen-ui | Skillnad |
|---|---|---|
| `kalla.revision` | `TimelineOverrides.baseVersion` (`types.ts:82`) | hagen-ui har ingen hash av källan. |
| `edits[]` (logg) | `scenes`, `added`, `order` (`types.ts:83–86`) | Lagrat tillstånd mot logg. `reset` (`ops.ts:204`) har ingen motsvarighet eftersom en logg kan kortas. |
| `byt_replik`, `lagg_till_replik` | `set` med `path: 'speech'` (`ops.ts:109`, `FIELD_PATHS` `types.ts:75`) | `set` ersätter hela fältet. Röst och tidspolicy ryms bara i `LineVoice` (`types.ts:28`). |
| `casta` | `cast` (`ops.ts:198`): `speakerId` till `roleId` | `utseende` och `rost` saknar motsvarighet. |
| `casta.kundroll` | `CardRole` (`customer-card/index.ts:49`) | `id`, `name` finns. `epithet` och `wantsOnCamera` förs inte över. |
| `byt_miljo` | `set` med `path: 'picture'` eller `'setting'` (`ops.ts:109`) | `picture.venue` (`types.ts:46`) bär källan men ingen geometri. |
| `byt_miljo.rum.ord`, `tillgang_id` | `CustomerCard.venue.words`, `assetIds` (`customer-card/index.ts:60`) | |
| `byt_prop`, `lagg_till_prop`, `ta_bort_prop`, `flytta_prop` | `set` med `path: 'direction'` (`ops.ts:109`) | Bara text. |
| `ta_bort_scen` | `remove` (`ops.ts:174`) | |
| `lagg_till_scen` | `sample` (`ops.ts:188`), `added` (`types.ts:85`) | hagen-ui lånar en scen från ett annat klipp. |
| `duplicera_scen` | `duplicate` (`ops.ts:166`) | |
| `flytta_scen` | `move` (`ops.ts:180`) | |
| `trimma_scen` | `trim` (`ops.ts:120`) | `lage` (replikssäker, klipp, sträck) saknas. |
| `skarmtext` | `set` med `path: 'screenText'` (`ops.ts:109`) | |
| `satt_intention` | `set-intent` (`ops.ts:249`) | Annan betydelse, se ovan. |
| `ramar` | `Rail` (`rails.ts:27`): order, rhythm, hook, sound, mechanic, intent | Delvis: order = `bevara_beats`, rhythm = `bevara_klippoffset_s`, `max_talfaktor`, hook = krok, sound = `ljudpolicy`. Upplåsning (`unlock`, `ops.ts:219`) har ingen motsvarighet. |
| `renderkamera`, `rorelse`, `uttryck`, `forenkla`, `tillat`, `fri_scen`, `flagga`, `satt_serieposition`, `utdata` | ingen motsvarighet | hagen-ui renderar inte. |
| ingen motsvarighet | `split` (`ops.ts:130`), `merge` (`ops.ts:154`), `lock`/`unlock`, `set-truths` (`ops.ts:242`) | Kontraktet delar inte scener. Kalla är fryst. |
| ingen motsvarighet | `CustomerCard.tone`, `never`, `lens` (`customer-card/index.ts:61–62`) | Kundkontext, inte redigeringar. `never` liknar harnessens `undvik`. |

## (c) Kalla och regi mot `scen3d.json` och `op.py`

Källor: `scen/3d/scen3d.json`, `scen/3d/op.py`. `scen3d.json` blandar frusna mätningar med redigeringar. Kontraktet delar dem, som `FRON-1.5.md` föreslår (frö 2). Operationen `normalisera` (`op.py:118`) fryser redan källkamerorna per tagning, vilket är samma uppdelning i liten skala.

### Fält

| Kontrakt | `scen3d.json` | Anmärkning |
|---|---|---|
| `klipp.video`, `tidsbas` | `source` {clip, fps, width, height, duration} (`scen3d.json:9`) | |
| `scener[]` | `shots[]` (`scen3d.json:1000`): `id`, `source.inSec/outSec`, `duration`, `beat` | Tagningar står i utdataordning med lokal tid. Scener står på källklockan. `shots[].beat` är engelska ("hook", "build-up", rad 1056, 1248), harnessen är svensk. |
| `personer[]` | `actors[]` (`scen3d.json:419`): `id` (A, B, C), `role`, `look`, `motion.ref` | `role` är en beskrivning (woman/man), inte en kundroll. |
| `props[]` | `props[]` (`scen3d.json:604`) med `semantic` {owner, label, kind}, `support`, `attach` | Gamla kedjan har stöd och fäste, MHR-kedjan inte. |
| `rum[]` | `set[]` (`scen3d.json:17`): primitiva lådor | |
| `matning.kameror[]` | `shots[].source.camera` (fryst källkamera) och `shots[].ingest` (utsnitt, avstånd, objektiv) | Gamla kedjan har en kamera per tagning, MHR-kedjan en per ruta. |
| `repliker[]` | `dialogue[]` (`scen3d.json:2200`, och per tagning): `speaker`, `text`, `start`, `end`, `words[{w,start,end}]`, `timing` | `p` (sannolikhet) tappas i scen3d. `talare_i_bild`/`utanfor_bild` i `shots[].ingest` blir `i_bild`. |
| `matning.personer[]`, `koordinater` | `motion-*.json` (MediaPipe) | Annan mätning än MHR. |
| `regi.edits[]` | `editLog[]` (`scen3d.json:2496`): `{phase, op, args, vad, by}` | `op.py` loggar efter att ha ändrat, kontraktet loggar före. |
| `utdata` | `audio`, `audioMode`, fast 30 fps och 576x1024 | |
| `ramar.max_talfaktor` | `--tal-max 1.15` i `langd` (`op.py:243`) | |

### Operationer

| Kontrakt | `op.py` | Skillnad |
|---|---|---|
| `byt_replik` | `op_replik` (`op.py:353`) | Replik efter nummer, inte id. Fartvarning vid > 15 %. |
| `lagg_till_replik` | ingen motsvarighet | Gamla kedjan byter bara text i befintlig lucka. |
| `casta` | `op_casting` (`op.py:367`), `op_utseende` (`op.py:392`) | Rollnamn, röst, färg. |
| `byt_miljo` | ingen motsvarighet | `byt_lokal` är markerat Saknas i `SYFTE.md`. `set[]` ändras för hand. |
| `byt_prop` | `op_byt` (`op.py:162`) | |
| `flytta_prop` | `op_flytta` (`op.py:143`), `op_rotera` (`op.py:158`) | |
| `ta_bort_prop` | `op_dolj` (`op.py:172`) | Döljer, tar inte bort. |
| `lagg_till_prop` | ingen motsvarighet | |
| `ta_bort_scen` | `op_ta_bort` (`op.py:273`) | Aktörens sista scen kan bryta importen. |
| `lagg_till_scen` | `op_lagg_till_aktor` (`op.py:287`) | Lägger till en aktör i en tagning, inte en ny tagning. |
| `duplicera_scen` | `op_duplicera` (`op.py:268`) | Tyst som standard. |
| `flytta_scen` | `op_flytta_tagning` (`op.py:278`) | |
| `trimma_scen` | `op_langd` (`op.py:243`) | `lage`: replik, trim, stretch. Kontraktets `replik_sakert`, `klipp_slut`, `stracka`. |
| `renderkamera` | `op_kamera` (`op.py:196`), `op_dolly` (`op.py:177`), `op_zoom` (`op.py:184`), `op_orbit` (`op.py:188`) | |
| `uttryck` | `op_humor` (`op.py:387`) | Samma fem förinställningar. |
| `rorelse` | ingen motsvarighet | Bara `op_spegla` (`op.py:379`), `op_intensitet` (`op.py:382`) och per aktör `motion.ref`. |
| `forenkla` | ta-bort och statisk kamera (SYFTE.md) | Ingen enskild operation. |
| `skarmtext`, `tillat`, `fri_scen`, `flagga`, `satt_*` | ingen motsvarighet | |
| ingen motsvarighet | `op_vand` (`op.py:312`), `op_titta` (`op.py:317`), `op_intensitet` | Kroppsvändning och blick. Kontraktet har dem inte, de kan läggas som parametrar i `rorelse`. |
