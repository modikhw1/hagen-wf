# Efter GOLV2: webbkameran och platsproven

10 november 2026. Uppgifterna genomförda i angiven ordning.

## Kört och verifierat

- Sanningskontroll: **15 av 15 fall utan avvikelse**, även ångra identiskt.
  Logg: `forvarld/varld/logg/sanning-2026-11-10T22-20-11-235Z.json`.
- Hela sviten, seriellt från kontrakt/: **198 prov, 0 fel, inga överhoppade**.
  Semantikskriptet gav också `alla tester ok`.
  Moduler: flode 46, rumsmall 19, regler 18, text_disk 12, kroppmatt 18,
  props 6, handelser 16, snabb 7, steg11 19, bro 34, ingest/test_rum 3.
  Loggar och tider: `ut/efter_golv2/svit/`.
- `node --test forvarld/varld/stativ-test.mjs`: **2 prov, 0 fel**.
  Bland annat 12 regier med jämförelse av alla kameranycklars hela matris,
  `mal_m` och lins mot dagens kompilator, med numerisk gräns 1e-9.
  Trim före/efter kamerabyte, explicit FOV, huvud/kropp, inget utsnitt,
  propborttagning före/efter, kopiering och återgång till uppmätt ingår.
  Pakettransformen prövas också: kamera- och målavstånd ska bevaras.
  Logg: `ut/efter_golv2/stativ-test.log`.
- Ändrade källfiler och nya referenser verifierade som UTF-8 med LF.

## Uppgift 1

Orsaken var att `viewer.js:tripodKey` alltid lade på kamerans lokala
förskjutning `(0.12, 0, -0.08)`, alltså 0,144 m. Hela utsnittsberäkningen
saknades. Att ändra brännvidden ersatte inte kompilatorns kameraflytt.

`forvarld/varld/stativ.mjs` räknar nu målpunkt, huvudets höjdoffset,
utsnittsavstånd och vidgning för personbanan och observerad rekvisita enligt
`kompilera.py:kameranycklar`. Mål uttrycks som `mal_m`. Samma modul används
av visningen och för webbens mått i sanningskontrollen. Den ändrade planens
kameraposition används inte som webbens beräknade svar. Grundplanens aktuella
metriska kroppspunkter, uppmätta kameror och observerade props förs över genom
`stativunderlag.py`, `kompilator_demon.py`, `kompilator.mjs` och en läsande
endpoint i `server.mjs`. `edits.mjs` bevarar editordningen och räknar om
utsnittet efter trimning. `viewer.js` flyttar kamera och mål till det äldre
webbpaketets ram med samma rigida transform och utan ändrad meterskala.

Rimlighetsbedömning, med uppmätta/beräknade värden:

- Hel, s1: 2,1 m bildhöjd och vertikal FOV 40° ger
  `2.1 / (2*tan(20°)) = 2.884851 m`. Standardmålet ligger 1 m framför den
  uppmätta kameran, vilket ger 1,884851 m kameraflytt.
- Nära B, s7: den uppmätta kameran ligger 3,290019 m från det höjdjusterade
  huvudmålet. Den observerade bord_A-punkten vid ungefär
  `(0.008, 0.535, 0.738)` m vidgar stativavståndet till 4,941309 m med
  kompilatorns 25 cm sido- och 20 cm höjdmarginal. Flytten blir 1,651290 m.
  Det är samma tagnings observerade förgrundsbord, inte ett godtyckligt bord
  från andra änden av platsen. Den stora flytten följer därför det avsedda
  kravet att både målbanan och den observerade rekvisitan ska rymmas.

Kompilatorn är oförändrad. Sanningskontrollens kod från `planKamera` och
framåt är identisk med säkerhetskopian: samma fält och toleranser jämförs.

## Uppgift 2: bedömning av de sex proven

| Prov | Bedömning och åtgärd |
| --- | --- |
| `BarOforandrad.test_bars_byggdata_ar_byteidentiska_med_referensen` | Samma fullständiga jämförelse av byggdata mot avsett GOLV2-beteende. Granskat gammal/ny referens: endast golvets Z, stativnycklar och samma kameranyckel i tillämpningsloggen skiljer. Inga ytterligare fält har undantagits. Jämförelsen görs nu utan unittests kostsamma stora diff; likhetskravet är oförändrat. |
| `Plats.test_tva_personer_i_samma_scen_foljer_var_sitt_ankare` | Samma ankarkontroll. Grundplanens transform är rätt utgångspunkt efter GOLV2:s golvbeslut; källans tidigare registrering är inte längre denna ram. Kravet på varje persons ankarmappning och toleransen 1e-8 kvarstår. Ingen ändring behövdes. |
| `Plats.test_platssteget_ar_deterministiskt` | Försvagat under GOLV2 genom att arkivsolver valdes. Rättat: namnet avser nu två färska processer med dagens `ingest/plats.py` och dagens mätningar. Båda hela utdatafilerna jämförs byte för byte mellan körningarna och med nya sparade referenser `testdata/plats_golv2{,_matt}.json`. Den tidigare arkivkontrollen heter nu `test_arkiverade_platssteget_fore_golv2_med_historiska_indata` och kräver explicit `--solver-fore-golv2` i snapshot-skriptet. |
| `GolvOchSkymning.test_overensstammande_cues_ar_uppmatta` | Samma krav på värde, status och frånvaro av konflikt, anpassat till avsikten att fotfamiljen väljer 0,20 m. Gamla 0,21 m var medianen mellan familjer. Ingen försvagning eller ytterligare ändring. |
| `GolvOchSkymning.test_planterad_avvikare_avvisas_och_redovisas` | Samma krav på värde/status, konflikt och explicit avvisning med orsaken avvikare. 0,20 m följer familjeprioriteten. Ingen försvagning eller ytterligare ändring. |
| `Omkorningslogg.test_slutligt_utsnittsbeslut_loggas_efter_historisk_golvregel` | Slutbeslut och logg jämfördes fortfarande, men provet hade ingen faktisk historisk golvskala. Förstärkt och namnändrat till `...loggas_aven_med_historisk_golvskala`: tre historikfall gånger True/False, med syntetisk skala 0,85 eller 1 och ett avsiktligt inaktuellt stegresultat. Hela slutfilen och loggen måste återge det nya beslutet exakt. Riktiga mätfiler rörs inte. |

Ändringar för uppgift 2 finns i `test_flode.py`, `test_plats_snapshot.py`,
`test_kroppmatt.py` och `testdata/`. Referensframtagningens kommando och
kod-/referenshashar finns i `testdata/plats_golv2.underlag.json`.
`test_rumsmall.py` granskades utan att ändras.

## Avgränsning

Inga ingest-steg, Modal, GPU eller Blender kördes. Inga verkliga
sekvens-/världsfiler eller banker ändrades. `golvmatning.py` och ingestkoden
är orörda. Ingen visuell webbläsar- eller Blendergranskning gjordes;
rimlighetsbedömningen ovan gäller geometri och scenmått, inte bildkvalitet.

Säkerhetskopior före källändringar finns under
`ut/fore_efter_golv2/<sökväg relativt projektroten>`.
