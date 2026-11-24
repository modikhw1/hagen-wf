# Rapport, spår B (runda 3): allmän kedja till `scenpaket/2`, fryst och prövad mot hold-out

19 nov kväll (avbrutet av kvoten 22:53) och 20 nov förmiddag. Inga generativa anrop. Det enda betalda är Modal för kropp och djup på hold-out, efter ägarens godkännande via koordinatorn (§3.1). Skrivet i `B-nasta-klipp/`. Utanför den mappen: ingestens cache för hold-out under `scen/3d/ingest/ut/<klipp-id>-tagningar/` (nya mappar), fps-rättningen i `scen/3d/ingest/flera/ingest_flera.py` med säkerhetskopia, och ingestens egna skrivningar till `flera/budget.json` och `scen/3d/kontrakt/ut/fore_regler/`. Egna mått i den här rapporten är diagnos, inte dom.

## Läget i korthet

- **Koden är fryst** 2026-11-20 10:41:27. Den sammanslagna hashen är `7d79302318ec35c10d9d3f644f028746962b667da121a59d8a911d11675fe6c0`, och hash per fil står i `FRYST.md`. Före frysningen rättades tre tysta fel: renderingen, G6/G3-summan och felinjektionens typjämförelse (`KORLOGG.md` §3).
- **Hold-out:** den frysta kedjan kördes en gång per klipp efter ingesten (lokalt plus Modal, 26 tagningar). sabai, faros_7540 och pitaspot gick igenom med exit 0. **faros_7511 (15 tagningar) avbröts efter mer än 30 minuter i Lager 2 och är inte utvärderad.** Mot A:s facit ligger faros_7540 r73 **10,8 cm under** facit (telefonpriorn ensam ligger 0,6 cm under), och sabai och pitaspot ligger inom sina ordningsgränser. Kamerahöjden är `antagen` i alla hold-out-tagningar. Ingesten rättades efter frysningen (fps), och rättningen rör inte `karna/`. Modal kostade 1,27 USD enligt timrapporten, som ännu inte innehöll den sista timmen (§3.1).
- **K4 faller som 1:1-krav.** Det som håller är att koden saknar klippkod och klippnamn, att den gick från ingest till `scenpaket/2` på 3 av 4 osedda klipp utan handpåläggning, och att den aldrig påstår "matt" kamerahöjd utan golv. Det som fäller är:
  - ett klipp blev inte klart (skalbarhet)
  - kamerahöjden ligger längre från facit än en ren prior
  - golv har gjorts om till bord (faros_7540 S2)
  - fötter svävar (faros_7540 S3) och kroppar faller sönder i lemmar (sabai S1)
  - en person saknas i närbild (pitaspot S2)
  - skivhöjden märks "matt" fast den är antagen (§5).

## 1. Rättat jämfört med `forvarld_karna/`, med motprov

Motproven kördes 10:39–10:41 före frysningen: `prov/motprov.py`, resultat i `prov/motprov.json`, utskrift i `prov/motprov_logg.txt`. "Före" är Argons lagrade paket `forvarld_karna/ut/<namn>/paket.json`, och "efter" är B:s paket (innehållet är detsamma i `ut/<klipp>/` och `ut/regr5/<klipp>/`). Alla grindtal nedan är räknade med B:s grindar efter rättningen den 20 nov, om inget annat sägs. Ordningen i varje cell är notan / guacamole / gelato / a-sketch.

| fel | i originalet | i `karna/` | motprov: före → efter | status |
|---|---|---|---|---|
| **C1** kamerahöjdsklämma och kappa-skalning | `scen_brygga.py:338` klämmer kameran till 0,92 m; kappa skalar om kropparna | `obs_motor.hojd_och_hallning` (rad 311–406): kamerahöjd, hållning och möbelklass prövas tillsammans som hypoteser (telefonprior 1,35 ± 0,35, MoGe-golv, synliga fötter, skivor som matbord/disk/bardisk/monter, sittande/stående bäcken). Ingen klämma. Personlig strålskala inom 0,88–1,12 (`STATUR_SKALA`) behåller bildläget | kamerans z: 0,92–1,26 / 1,01–1,12 / 0,92–1,30 / 1,15–1,38 m → 1,30–1,51 / 1,25–1,49 / 1,41–1,73 / 1,10–1,78 m. Bålens bildläge mot SAM:s egen projektion, median per bildhöjd: 0,011 / 0,077 / 0,049 / 0,000 → 0,000 på alla fyra. **Det "efter"-värdet följer av konstruktionen** (kroppen ligger på SAM:s stråle) och är inget oberoende bevis. Oberoende: G7 (kärnleder mot YOLO-ruta och mask) FEL 1 / 2 / 2 / 1 → 0 / 1 / 0 / 0 | rättat i den meningen att klämman är borta. Men höjden blir `antagen` i 20/20 utvecklingstagningar (§4 och §5) |
| **C2** pitch/roll kastas | `scen_brygga.py:254`: alla kameror vågräta | `fokal.py` (lodlinje ur vertikal försvinningspunkt och MoGe-normaler, med sigma och källa), och `scen_brygga` bär full rotation i kvaternionen | pitch/roll är 0,0/0,0 i alla 20 tagningar före. Efter: pitch −9,9…−1,4 / −0,4…+9,6 / −47,1…−20,6 / −32,4…−2,1°, roll −2,0…+1,7 / −1,6…+0,1 / −5,0…−3,4 / −17,2…+13,1°. G8 (lodlinje mot vertikal försvinningspunkt) FEL 3 / 1 / 1 / 0 → 0 / 0 / 0 / 0 | rättat |
| **A2** R25 flyttar kroppsrörelse till kameran | R25-beslut i paketet: 1 / 0 / 1 / 4 | R25 borttagen; `kamera_bana.py` skattar kamerans bana ur bakgrunden (SIFT utanför personmasken) | R25-beslut 1 / 0 / 1 / 4 → 0. G9 (kamera stilla mot bakgrunden) FEL 1 / 0 / 1 / 2 → 0 / 0 / 0 / 1 (a-sketch s2) | rättat. G9 kunde bara prövas med felinjektion på notan och guacamole (3/3) |
| **A3** grindar som inte kan larma | originalets grindar med felinjektion på originalpaketen: G2 svävande fot 0/3, 0/3, 0/2, 0/3; G7 0/3, 0/3, 0/2, 0/3; G8/G9 finns inte; G6 0/2 i gelato | `grindar.py` omskriven (G7 mot oberoende 2D, nya G8/G9), `mutation.py` med felinjektion per grind | B:s grindar, felinjektion på B:s paket (larm/provade): G2 svävande 1/1 notan (övriga utan kandidat), G3 1/1, 2/2, –, 1/1; G4 3/3, 3/3, 2/2, 3/3; G5 3/3, 3/3, 1/1, 3/3; **G6 3/3, 3/3, 0/2, 1/3**; G7 2/3, 2/3, 1/2, 2/3; G8 3/3, 3/3, 1/1, 2/2; G9 3/3, 3/3, –, –; G1 3/3, 3/3, 2/2, 3/3 | delvis. G6 är svag (gelato 0/2, a-sketch 1/3), och G7 missar var tredje injektion |
| A3, tillägg 20 nov | – | `grindar.py`: G6/G3 gav `np.bool_` och räknades inte i `sammanfatta`. `mutation.py`: `is True`/`is False` | logg4:s `GRINDAR.md` visar **FEL** i G6-kolumnen men `G6_skymning: 0` i summan. Efter rättningen: 1 / 2 / 0 / 2 (`ut/regr5/*/paket_grindar.json`) | rättat före frysningen |
| **A6** mappnamn, `bonaqua`, fokaltabell | grep efter klippnamn i `forvarld_karna/`: 44 träffar. Ett påhittat namn (`notan-tagningar-v2`) gav notans fokal 983,7 ur tabellen (`prov/a6_namnprov.json`) | inga namnuppslag, ingen tabell per klipp; `"bonaqua"` borttagen | grep i `karna/*.py` efter alla utvecklings- och hold-out-namn, id och konton: 0 träffar (träffarna på "bar" är variabeln `bar` och möbelklasserna `bardisk`/`barstol`). Lager 1 med den **frysta** koden på en omdöpt kopia av gelatos ingest gav samma `obs.json` som under det riktiga namnet; bara `klipp_id` skiljer (`prov/namnprov_fryst/logg.txt`) | rättat |
| **C3** `grindar.mat` mäter en person | rader med originalets grindar: 7 / 4 / 2 / 7 för 8 / 5 / 2 / 6 person-tagningar | en rad per (tagning, person) | 8 / 5 / 2 / 6 rader för 8 / 5 / 2 / 6 person-tagningar | rättat |

## 2. Utvecklingsresultat (notan, guacamole, gelato, a-sketch)

Regressionen kördes en gång till 20 nov med tom cache (`ut/regr5/<klipp>/`, kommandon i `KORLOGG.md` §2). Exit 0 på alla fyra. `obs.json`, `matning.json`, `recept.json` och `paket.json` (utom tidsstämpeln) är byte-identiska med logg4 från 19 nov. Kedjan är alltså deterministisk med `PYTHONHASHSEED=0`.

| klipp | tagningar | person-tagningar (tillstånd) | Lager 2 sluttro | fokal | grindar FEL (av rader) |
|---|---|---|---|---|---|
| notan | 7 | 8 (DEL 7, HEL 1) | P = 0,90 | mätt (VP, 942,6 px) | G6 1 (s4 D) av 8 |
| guacamole | 4 | 5 (DEL 4, EXTREMITET 1) | P = 0,57 | mätt | G5 1 (s2 B), G6 2 (s1/s3 A), G7 1 (s4 C) av 5 |
| gelato | 2 | 2 (DEL 1, UTANFOR 1) | P = 0,99 | mätt | 0 av 2 |
| a-sketch | 7 | 6 (DEL 5, UTANFOR 1) | P = 1,00 | **antagen** i 7/7 | G3 1, G4 2 (s5 B 0,12; s7 A 0,28), G6 2, G9 1 av 7 |

Kontaktkartor (original till vänster, förvärlden till höger, tre rutor per tagning): `ut/regr5/notan-tagningar/kontaktkarta_1.png`, `_2.png`, `ut/regr5/e-dialog-guacamole-tagningar/kontaktkarta.png`, `ut/regr5/kand-kennysgelato-tagningar/kontaktkarta.png`, `ut/regr5/a-sketch-servering-tagningar/kontaktkarta_1.png`, `_2.png`. Grått i renderingen är leder utan bildstöd (`antagen`). Det här såg jag själv i nedskalade kopior:

- **notan:** A och B ligger på rätt plats och i rimlig storlek i S1–S3, S5 och S6. Bordet är en brun skiva där bordet står. B:s armar i S2 och S5 följer inte originalet: han håller upp en pommes, men renderingens armar hänger ut åt sidorna. I S4 är D:s ben gråa (antagna) fast jeansen syns ned till knäna i originalet. De sittande gästerna, som i originalet sitter längst till vänster, syns i renderingen bara som en liten mörk form vid D:s höft, troligen C, delvis bakom väggen. I S4 står en vägg strax bakom D, medan rummet i originalet fortsätter flera meter bakåt med gäster och fönster. Det är troligen en vägg på fel avstånd. I S7 sitter B cirka en åttondel av bildbredden till höger om originalet. Väggarna är släta grå plan. Inga svävande fötter syns.
- **guacamole:** A vid bardisken i S1/S3 ligger på rätt sida men lite för långt åt höger och för liten. **I S2 r25 ritas bara ett rött armfragment mitt i luften.** Kroppen ligger utanför bildens högra kant, medan bartenderns huvud och bål syns tydligt i originalet, ungefär vid tre fjärdedelar av bredden (stämmer med G5-felet). Även i r5 och r45 ligger huvudet vid högerkanten. S4: B står på ungefär rätt plats, och C:s hand är en grön bit till vänster.
- **gelato:** I S1 r16 och r78 ligger kvinnan bakom montern ungefär rätt. I S1 r140 är hon för stor och för långt åt höger. I S2 r18/r48 finns ingen person, som i originalet (UTANFOR). S2 r86 är rätt placerad. Montern är bruna lådor. Lodlinjen (−30 och −35° enligt kontaktkartans text) motsvarar originalets nedåtblick mot montern.
- **a-sketch:** I S1, S2 och S4 är placeringen grovt rätt. **I S3 r15 står C mitt till höger med armen ut åt vänster, medan kvinnan i originalet står till vänster om mitten.** I S5 hänger en grå (antagen) underkropp ner genom disken. **I S7 skär diskskivan genom bålen i brösthöjd** (G4 0,28), och kvinnan ligger till höger om sin plats i originalet. S6 och närbilderna på mat har ingen person, som i originalet.

Huvudets läge mot YOLO-rutans mitt, i bildbredder (eget diagnosmått, `prov/huvud_mot_box.py`, utdata i `prov/huvud_mot_box_regr5.txt`): oftast inom ±0,05. Störst är a-sketch s3 C +0,28, guacamole s2 B +0,12, gelato s1 A +0,12, gelato s2 A −0,13, guacamole s4 C −0,12 och notan s2 B +0,12. Felet har inget enhetligt tecken, så det är inget enkelt teckenfel. Blender och grindarna använder samma kamera (`emit_bpy.py:83` `sensor_fit="HORIZONTAL"`, `grindar.py:75–80`), så avvikelsen finns i paketet och inte bara i bilden.

## 3. Hold-out

Efter frysningen gjordes tre saker, på ägarens godkännande som kom via koordinatorns meddelande (jag har inte sett det direkt från ägaren): fps-felet i ingesten rättades, kropp och djup kördes på Modal, och därefter kördes den **frysta** kedjan en gång per klipp. **Ingesten rättades efter frysningen, och rättningen rör inte `karna/`.** Hashen var oförändrad vid varje kedjestart (`holdout/logg/kedja_*.txt`). Facitintervallen läste jag före frysningen, eftersom uppdraget sa det. Ingen kodändring i `karna/` hänger ihop med dem (`FRYST.md`). Kommandon står i `KORLOGG.md` §6, §9 och §10.

### 3.1 Ingest

- **Lokalt** (10:42–10:55): tagningsdelning med `ingest_flera.py --endast-dela`, YOLO-personer och COLMAP med `holdout/lokal_ingest.py`. Det sistnämnda är samma stegfunktioner som `ingest_klipp.py --till kamera`, men utan säkerhetskopian till `scen/3d/kontrakt/`.
- **fps-fel i faros_7511, rättat i ingesten:** källan anger `r_frame_rate` 60/1, men den verkliga frekvensen (`avg_frame_rate`) är 5604/187 ≈ 29,97. `ingest_flera.fps_rat` läste den angivna, så varje ruta dubblerades (937 rutor i stället för 467). Rättningen gäller alla klipp: den angivna frekvensen behålls om den stämmer med medelfrekvensen inom 1 %, annars används medelfrekvensen. Diff och säkerhetskopia (`ingest_flera.py.fore_fps.bak`) står i `KORLOGG.md` §9.1. Kontrollen `holdout/fps_kontroll.json` visar samma fps som förut för alla andra 8 delade klipp, och deras rutantal är oförändrat. Den gamla mappen heter nu `…-tagningar.fel_60fps`. Omdelningen gav 469 rutor mot källans 467: S1 fick 88 i stället för 86, eftersom ffmpeg dubblerar två rutor där tidsstämplarna är oregelbundna. Tagningarna efter S1 ligger därför 2 rutor senare än i originalet.
- **Modal** (`holdout/kor_modal.sh`, 11:08–12:07): ingestens eget kommando, `ingest_flera.py … --till rum --total 6300 --uppdrag holdout-runda3-B-2026-11-20 --uppdragstak 2800`. Budgeten behövde 3 502 + 2 739 = 6 241, så marginalen var 59 personrutor. Utfall: 26/26 tagningar klara med exit 0, och `budget.json` står på 6 241 med 26 poster. **Körningen var sekventiell:** ett klipp i taget och en tagning i taget, med en Modal-app per tagning och steg. Jag valde det eftersom `budget.json` läses en gång per process och skrivs över, så parallella klipp hade tappat poster. Inom en tagning skickas kroppsjobben i satser om 40 via `map`, men jag har inte sett hur många containrar Modal faktiskt startade. Väggtiden blev cirka 1 timme, mot de 35 minuter jag uppskattade för parallella klipp.
- **Kostnad:** **1,27 USD** enligt Modals timrapport kl. 12:28 (`holdout/kostnad.py`, `holdout/logg/kostnad.jsonl`). Fördelning: A10G 1,00, A100-40GB 0,08, L40S 0,05, L4 0,02, CPU/minne/nät 0,12. **L4 står först i reservlistan, men Modal körde nästan allt på A10G.** Siffran täcker bara timmen 10–11 UTC. Pitaspots sista cirka 10 minuter (11:00–11:07 UTC) hade ännu inte kommit in. Månadssammanfattningen ökade med 0,87 USD mellan 11:31 och 12:27 (`holdout/logg/kostnad_summary.txt`), så slutsumman blir troligen 1,5–2,5 USD. Den behöver läsas igen med `holdout/kostnad.py` när timrapporten har satt sig. Det är långt under taket på 15 USD. Månaden täcks av krediter (debiterat 0,00 USD).

### 3.2 Den frysta kedjan, en gång per klipp

| klipp | utfall | tid | tagningar | person-tagningar (tillstånd) | identiteter | Lager 2 | grindar FEL (av rader) |
|---|---|---|---|---|---|---|---|
| sabai | körd, exit 0 | 2 min | 6 | 7 (DEL 5, EXTREMITET 2) | 5 (A–E) för i praktiken 2 personer; servitören är C i S2/S5/S6 | P = 0,93 | G4 1, G7 1 (s1 B, spökandel 0,32), G9 2 av 7 |
| faros_7540 | körd, exit 0 | 1,5 min | 3 | 6 (HEL 3, DEL 2, UTANFOR 1) | 5 (A–E) för 2 män | P = 0,88 | G2 2 (s3 A 0,32 m, E 0,24 m över golvet), G4 3 (s2 C 0,97) av 6 |
| faros_7511 | **avbruten efter > 30 min i Lager 2 (15 tagningar), ej utvärderad** | Lager 1 8 min (SIFT-gruppering 6,5 min), Lager 2 24 min när den stoppades | 15 | – | – | – | – |
| pitaspot | körd, exit 0 | 1,5 min | 2 | 3 (DEL 3) | 2 | P = 0,99 | G3 1, G4 2 (s2 A 0,54), G6 1 av 3 |

**faros_7511:** kedjan startade 11:56:05, och Lager 1 var klart 12:04:15 (`obs.json` och `matning.json` skrevs). Lager 2 (`rums_pussel.kor`) arbetade utan utskrift i 24 minuter och 2 819 s CPU-tid, och stoppades 12:28:08 på ägarens beslut via koordinatorn. Det finns alltså inget `recept.json` och inget `paket.json`. **Det här är ett K4-fynd om skalbarhet.** Lager 2 är en strålsökning som löser en minstakvadratpassning (`_los`, upp till 120 utvärderingar) för varje kandidat över alla tagningar hittills, så kostnaden växer ungefär kvadratiskt med antalet tagningar. Utvecklingsklippen hade högst 7 tagningar och 1–2 minuter i Lager 2. Ett verkligt klipp med 15 korta tagningar går inte igenom på rimlig tid.

### 3.3 Mätning mot A:s facit (`holdout_jamfor.py`, oförändrat)

Påståendet byggs ur paketen med `holdout/pastaende_fran_paket.py` (kamerans z vid facitrutan, minus `golv_z`) och ligger i `holdout/pastaende_B_holdout.json`. Utfallet ligger i `holdout/jamforelse_B_holdout.json`: 1 utanför, 5 inom, 1 saknas, inga epistemikvarningar (B säger aldrig "matt" där golvet inte syns).

| klipp, ruta (tagning) | B | status | facit | utfall | baslinje: telefonprior 1,35 |
|---|---|---|---|---|---|
| faros_7540 r73 (s1) | 1,248 m | antagen (mätandel 0,44) | 1,36–1,61 | **utanför, 10,8 cm** | utanför, 0,6 cm |
| faros_7511 r0 | – | – | 1,39–1,70 | **saknas** (kedjan avbruten) | utanför, 4,1 cm |
| sabai r222 (s6) | 1,572 m | antagen | gränser 0,95–1,97 | inom gränserna | inom |
| sabai r0 (s1) | 1,153 m | antagen | inga gränser | – | – |
| pitaspot r212 (s1) | 1,706 m | antagen | > 0,70 | inom gränserna | inom |
| pitaspot r744 (s2) | 1,427 m | antagen | > 0,70 | inom gränserna | inom |

**På det enda klipp med metrologifacit som kördes ligger B längre från facit än telefonpriorn ensam** (10,8 mot 0,6 cm). Orsaken syns i `matning.json`: synliga fötter ger 1,44 m, alltså inom facit, men MoGe-golvplanet ger 0,56 m och drar ned summan. I sabai och pitaspot är facit bara ordningsgränser, och dem passerar både B och priorn.

### 3.4 Kontaktkartor (sett själv i nedskalade kopior)

`ut/<klipp-id>-tagningar/kontaktkarta.png`. Grått är leder utan bildstöd.

- **sabai:** servitören framifrån i S2, S5 och S6 ligger på rätt plats och i rimlig storlek. **S1 är värst.** I r7 svävar A:s huvud uppe till höger medan två blå lemmar ligger på bordsskivan, en sönderfallen kropp. I r67 står en liten figur ovanpå bordet, och gästen i förgrunden till höger (stor i originalet) saknas. I S3 och S4 (närbilder på tallrikar, EXTREMITET) svävar fristående armbitar (brun respektive lila). Kamerahöjden spretar mellan tagningarna (0,89–2,01 m) i samma lokal.
- **faros_7540:** i S1 ligger båda männen rätt, och A:s upplyfta arm i r68 följer originalet. Men en brun skiva svävar i huvudhöjd över A, ett bord från en annan tagning. **I S2 (nedåtblick −41°) har golvet blivit en "matbordsskiva" på 0,6 m som täcker båda männens underkroppar** (G4 0,97). Den höjer också kamerahöjden till 1,91 m. I S3 svävar fötterna 0,24–0,32 m över golvet.
- **pitaspot:** i S1 ligger de två sittande männen på rätt sida om varandra bakom bordet, i rimlig storlek. **I S2 r20 fyller mannen halva originalbilden i närbild, men renderingen är tom.** I S2 r101/r181 går bordet genom A:s kropp (G4 0,54). Väggen är grå i stället för grön.

### 3.5 Andel `antagen` (hold-out)

| klipp | leder sedda / antagna / utanför bild | kamerahöjd `antagen` | lodlinje mätt | fokal | objekt Z1 / Z2 | poster i `antaganden` |
|---|---|---|---|---|---|---|
| sabai | 40 % / 26 % / 34 % | 6/6 | 3/6 | antagen 6/6 (783 px) | 3 / 3 | 12 |
| faros_7540 | 72 % / 23 % / 5 % | 3/3 | 3/3 | antagen 3/3 (692 px) | 4 / 4 | 5 |
| pitaspot | 58 % / 13 % / 29 % | 2/2 | 2/2 | antagen 2/2 (783 px) | 1 / 3 | 8 |
| faros_7511 | – | – | – | – | – | – |

## 4. Andel `antagen` per klipp (utveckling)

`prov/andel_antagen.py`, resultat i `prov/andel_antagen_regr5.json`. Leder räknas per (person, tagning, led).

| klipp | leder sedda / antagna / utanför bild | kamerahöjd `antagen` | lodlinje mätt | fokal | objekt Z1 sedda / Z2 härledda | poster i `antaganden` |
|---|---|---|---|---|---|---|
| notan | 60 % / 21 % / 19 % | 7/7 | 7/7 | mätt 7/7 | 4 / 6 | 9 |
| guacamole | 55 % / 17 % / 28 % | 4/4 | 4/4 | mätt 4/4 | 7 / 3 | 6 |
| gelato | 25 % / 52 % / 23 % | 2/2 | 2/2 | mätt 2/2 | 1 / 3 | 6 |
| a-sketch | 40 % / 28 % / 32 % | 7/7 | 7/7 | antagen 7/7 | 4 / 5 | 10 |

Hold-out: se §3.5.

## 5. Svagt

1. **Hold-out:** 3 av 4 körda. Ett klipp med 15 tagningar avbröts i Lager 2 efter mer än 30 minuter, och sökningen skalar ungefär kvadratiskt med antalet tagningar (§3.2). Den enda mätbara kamerahöjden ligger 10,8 cm utanför facit (§3.3). Identiteterna splittras: 5 identiteter för 2 personer i både sabai och faros_7540.
2. **Kamerahöjden är `antagen` i 20/20 utvecklingstagningar.** Den bestäms i praktiken av möbelklassens prior: matbord 0,75 ± 0,03, disk 0,92 ± 0,04, bardisk 1,08 ± 0,05, monter 1,22 ± 0,06 (`obs_motor.py:295`). Dessa sigma är snävare än mätningarna, så de dränker synliga fötter (notan s4 har `matt_andel` 0,3). Den redovisade sigman (0,03–0,06 m i notan) räknar priorer som oberoende mätningar och tar inte med osäkerheten i valet av hypotes. Den är för liten.
3. **Skivhöjden märks "matt" fast den är antagen** (upptäckt efter frysningen och inte rättat). `scen_brygga.py:372` skriver fast `"MoGe-skiva + kamerahöjd (matt)"`, men kamerahöjden är antagen. Höjderna blir i praktiken klassens prior: notan S1–S6 som `disk` ger 0,91–0,95 m, guacamole `bardisk` 1,07–1,11 m och `monter` 1,22–1,34 m. Notans bord ser ut som ett vanligt matbord. Det här bryter mot K4-kravet att allt antaget ska märkas `antagen`.
4. **Sidoförskjutning i paketet** på upp till 0,28 bildbredder (§2), utan enhetligt tecken. G7 fångar det inte. Personrutorna är ofta 0,6–1,0 bildbredder breda (armar och bord ingår), och grinden kräver bara att kärnlederna ligger inom rutan med 5 % marginal.
5. **Spökfragment och genomträngning:** armfragment utan kropp (guacamole s2 r25), antagen underkropp genom disken (a-sketch s5) och disk genom bålen (a-sketch s7). D:s synliga ben i notan s4 är märkta antagna, alltså för strikt synlighet.
6. **G6 larmar svagt** (gelato 0/2, a-sketch 1/3), och **G7 missar** var tredje injektion. C1:s "0 efter" mot SAM är konstruerat och inte oberoende.
7. **Väggar:** släta plan, och i notan S4 står en vägg närmare än rummet i originalet. Alla fyra väggar i notan är märkta `Z1_sedd`. Det har jag inte kunnat pröva mot något facit.
8. **Ingestens delning:** i faros_7511 har alla 15 tagningsfiler dubblerade rutor, 60 fps i stället för 29,97 (§3.1). B:s kedja tar bildfrekvensen ur första tagningens `meta.json` (`obs_motor.py:622`) och jämför den inte med källvideon. Den skulle alltså ta 60 fps och 937 rutor som sanning. Det har jag läst i koden, inte kört.
9. **Det trubbiga hold-out-måttet:** telefonpriorn ensam hamnar inom 4,1 cm av facit (§3.3), och B är sämre än priorn på faros_7540.
10. **Påhittade och felplacerade ytor på hold-out:** golvet blev ett matbord (faros_7540 S2), en skiva svävar i huvudhöjd (faros_7540 S1), och bordet går genom kroppen (pitaspot S2). MoGe-golvplanet gav 0,56 m kamerahöjd i faros_7540 S1, när synliga fötter gav 1,44 m.

## 6. Vad ägaren behöver döma

1. **Kontaktkartorna för utvecklingsklippen**, original bredvid förvärld:
   - `motpart/runda-3-opus/B-nasta-klipp/ut/regr5/notan-tagningar/kontaktkarta_1.png` och `kontaktkarta_2.png`
   - `motpart/runda-3-opus/B-nasta-klipp/ut/regr5/e-dialog-guacamole-tagningar/kontaktkarta.png`
   - `motpart/runda-3-opus/B-nasta-klipp/ut/regr5/kand-kennysgelato-tagningar/kontaktkarta.png`
   - `motpart/runda-3-opus/B-nasta-klipp/ut/regr5/a-sketch-servering-tagningar/kontaktkarta_1.png` och `kontaktkarta_2.png`

   Frågan är om kroppar, kamera och bord är trogna nog för att bygga vidare på, och om det jag pekar ut i §2 och §5 stämmer.
2. **Hold-out-kontaktkartorna**, original bredvid förvärld:
   - `motpart/runda-3-opus/B-nasta-klipp/ut/sabai.soong-7474616203366108439-tagningar/kontaktkarta.png`
   - `motpart/runda-3-opus/B-nasta-klipp/ut/faros_shipandterrace-7540756212032326934-tagningar/kontaktkarta.png`
   - `motpart/runda-3-opus/B-nasta-klipp/ut/thepitaspot-7680489103195917590-tagningar/kontaktkarta.png`

   Stämmer det jag pekar ut i §3.4? faros_7511 saknar paket, eftersom Lager 2 avbröts.
3. **Skivhöjd och kamerahöjd** (§5 punkt 2–3): ska rättningen (märkning plus bredare möbelpriorer) göras som en ny version i en separat mapp, efter hold-out-körningen med den frysta koden?
4. **Hold-out-måttet:** räcker kamerahöjd i två klipp, när priorn ensam hamnar inom 4 cm? Spår A föreslår själv fler märkta rutor och möbelhöjder (`A-domare/RAPPORT.md`, "Inte hunnet").

## Filer

`FRYST.md` (hash), `KORLOGG.md` (kommandon och ändringar 20 nov), `README.md` (körning och format), `ut/regr5/` (utveckling), `prov/motprov.json`, `prov/andel_antagen_regr5.json`, `prov/namnprov_fryst/`, `holdout/` (påståenden, jämförelser, `lokal_ingest.py`, `kor_modal.sh`, `kostnad.py`, `fps_kontroll.py`, loggar), `ut/<klipp-id>-tagningar/` (hold-out-paket).
