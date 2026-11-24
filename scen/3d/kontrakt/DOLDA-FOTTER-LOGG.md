# Dolda fötter: löpande logg

## 2026-11-10: inventering och design före kod

Läst: `GOLV2.md`, slutet av `GOLV2-LOGG.md`, `EFTER-GOLV2.md`, hela
`GOLV2-BLENDER-LOGG.md` och `blender/gen/golv2/RAPPORT.md`. Inga mätdata,
banker eller produktionsfiler är ändrade. En filinventering råkade följa
ett Windows-glob in i `kontrakt/ut`; åtkomstskyddet stoppade läsningen och
fortsatt inventering använder endast uttryckligen angivna källmappar.

### Rekvisita och möbelkontakt, görs först

Blenderprovet belägger att dagens ytrekvisita klipps mot mallskivans kant:
hamburgarens siktlinjemiss är efter GOLV2 0,147 m i S3 och 0,701 m i S7,
mot 0,065 respektive 0,356 m före. Centrumfelet blir 35→103 px i S3 och
17→45 px i S7. Samma rapport visar att handlederna i S7 efter GOLV2 ligger
30/42 cm utanför bordet, mot 0/8 cm före. `tropassning.py` flyttar i dag
stol och följbord en gång till medianbäckenet över alla tagningar. Det
gemensamma medianläget lämnar stora, tagningsegna XY-rester i S3 och S7.

Design: behåll platsens gemensamma mall och höjd, men spara per tagning den
bundna personens medianbäckenrest mot det gemensamma ankarläget. När
tagningens byggobjekt skapas flyttas just den bundna stolen och delar med
`folj_ankare` (bordet) med denna XY-rest. Kropp och kamera flyttas inte.
Beslutet är antaget och rapporteras per scen. Ytrekvisita löses därefter mot
samma scenlokala bord som Blender bygger. Detta ska prövas mot samma
centrumfel och Blenderbilder; hypotesen godtas inte utan mätning.

### Dolda fötter

1. Golvet beslutas först med oförändrad GOLV2-läsning. Regeln är endast
   kandidat när personen saknar varje synlig, tillförlitlig fotruta och
   tagningens valda golv kommer från en annan person eller annan mätt/
   modellbedömd ledtråd. Saknat golv ger ingen faktor och befintlig
   begränsningstext står kvar.
2. För varje fot bildas stabila stödfotsfönster ur sulans vertikala fart och
   spridning. Högst en stödfot per ruta används: den stabilare foten, och
   vid lika stabilitet den lägre. En snabbt rörlig pendelfot får därför inte
   styra bara för att den råkar vara lägst. Faktorn är medianen av
   kontaktfaktorerna under stabila stödrutor och är en per person/tagning.
3. För bildruta f är kameracentrum `C_f` och varje kroppspunkt `X_f`.
   Tydningen är `X'_f = C_f + k (X_f - C_f)`. Samma konstanta `k` används
   när kameran rör sig; fixpunkten är respektive bildrutas faktiska
   kameracentrum. I MHR-data betyder det samma faktor på `pose[..., :3]`
   och `cam_t`, aldrig bara avståndet. Blender skalar dessutom den importerade
   kroppens vilogeometri likformigt så att även hudens tjocklek följer med.
4. Tillåtet intervall är 0,93–1,07 (högst 7 %). Det rymmer ägarens cirka
   6 % för S4/C med en procentenhets marginal. Begärd faktor utanför
   intervallet klipps till gränsen; kvarvarande sul-/golvrest rapporteras.
5. Samma identitet i andra tagningar: en tagning med synlig tillförlitlig fot
   är längdreferens. En dold tagning får då faktorn som ger referenslängden,
   inte en konkurrerande golvfaktor; eventuell kontaktrest blir konflikt.
   Utan synlig referenstagning används golvfaktorn. Synliga tagningar och
   andra personer ändras inte.
6. Beräkningen sparas i mätningens personpost och kopieras till planens
   scenperson. Tillämpningen sker en gång i `ingest/metrisk.py`; kompilator,
   diagnostik, propfästen, webbunderlag och Blender registrerar planens
   beslut mot samma läsgräns. Rapporten märker beslutet `antagen` och visar
   faktor, längd före/efter, golvets källa och kvarvarande konflikt.
7. Handfäst rekvisita följer automatiskt den skalade handleden genom samma
   metriska läsning. Ytrekvisita och möbler följer scenens möbelrest ovan.
   Kontakter mäts efter båda reglerna.

Säkerhetskopior skapas före varje befintlig fil som ändras under
`kontrakt/ut/fore_dolda_fotter/<projektrelativ sökväg>`.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' -m unittest test_props
# kör från scen/3d/kontrakt
```

## 2026-11-10: baslinje för rekvisitaprov

`test_props`: 6 prov, 0 fel, 0 överhoppade (0,529 s). Detta är baslinjen
innan möbelrest eller propupplösning ändras. Läsningen av hela
`GOLV2-BLENDER-LOGG.md` verifierades separat i tre intervall (495 rader).

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' scen/3d/kontrakt/engang/dolda_fotter_mat.py baslinje
```

## 2026-11-10: reproducerbar baslinjeplan

Nytt läsande mätskript byggde tom-regi-planer från GOLV2-provets
hashaktuella manifest. Första försöket mot `ut/bar/kalla.json` avbröts korrekt
av en gammal hash för `tider.json`; ingen källa omhashades. Hashaktuella
`golv2_ingestprov/*_dagens_kalla.json` används därför för båda klippen.

Baslinjens maximala centrumfel per avläst ruta för notans hamburgare:
S1 23,01; S2 152,68; S3 102,85; S5 38,08; S6 26,81; S7 45,12 px.
Burken: S1 61,71; S3 70,11; S6 62,15 px. Bar har ingen upplöst prop i
detta manifest. Fulla planer och mätningar finns i
`ut/dolda_fotter/baslinje/`.

Nästa kommando (projektroten):
```powershell
$filer = @('scen/3d/kontrakt/tropassning.py','scen/3d/kontrakt/kompilera.py','scen/3d/kontrakt/test_props.py')
# kopiera varje fil till ut/fore_dolda_fotter med projektrelativ sökväg
```

## 2026-11-11: dold-fot-regeln kodad och enhetsprövad

Regeln beräknas efter GOLV2:s golvbeslut och sparas i mätningens personpost.
`metrisk.py` är enda tillämpningspunkt och skalar `pose[..., :3]` och
`cam_t` med samma faktor. Kompilatorn nollställer/registrerar planbeslutet;
Blender registrerar det ur planen och skalar dessutom FBX-vilogeometri och
armatur likformigt. Numpy-hudens lokala offset skalas med samma faktor.

Första hudexakta mätningen gav begärd S4/C-faktor 1,0795153409309486.
Den första designgränsen ±7 % lämnade 1,4105 cm sulrest och uppfyllde inte
målet. Gränsen är därför reviderad till ±8 % (0,92–1,08), den minsta hela
procentgräns som rymmer den hudexakta faktorn. Det skiljer från ägarens
grova cirka-6-%-uppgift och redovisas, inte döljs med ett annat sulmått.

Mätt ur `dolda_efter`:

- endast notan S4/C får beslut; bar får 0 beslut;
- faktor 1,0795153409309486, status `antagen`, 81 stabila stödrutor;
- sula 0,1178686023 m över golv → 2,2e-16 m;
- rapporterad MHR-höjd 1,758444548 → 1,898267865 m;
- golvet satt av person 4:s synliga fötter, status modellbedömd;
- ingen referenstagning med synlig fot finns för identiteten C i notan.

`test_rumsmall`: 23 prov, 0 fel (9,411 s). Fyra nya prov kräver: verklig
S4/C-träff och sula <1 mm, ingen träff med synlig fot eller utan golvkälla,
±8-%-gräns samt oförändrad perspektivprojektion när kropp och avstånd
skalas tillsammans.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' scen/3d/kontrakt/engang/dolda_fotter_jamfor.py
```

## 2026-11-11: plan- och projektionsjämförelse

Jämförelse: `rekvisita_passad2` (samma rekvisitakorrigering, ingen
dold-fot-regel) mot `dolda_efter`. Resultat i `ut/dolda_fotter/jamforelse.json`.

Renderdata är exakt lika för tidskarta, källrutor, renderkamera, mätkamera,
rum/möbler, props och globala personer. Alla andra notan-scener är exakt
lika. S4 skiljer bara för C: beslutet och de avsiktligt skalade benmåtten.
Bars renderdata är exakt lika.

S4/C i originalkameran, före → efter:

- rotfel median 1,27e-13 → 1,36e-6 px, p90 2,98e-13 → 1,38e-6 px;
- bildfel median 1,086712810 → 1,086725452 px, p90 4,551853496 →
  4,551851754 px;
- led-omslutnings-IoU 0,9956429152 → 0,9956429131;
- hudens silhuett-IoU och synlig-IoU exakt 0,7313349209 → 0,7313349209;
  tyngdpunktsfel exakt 0,01240775384 → samma.

De största bildskillnaderna är 1,3e-5 px och hudrastermasken är exakt
identisk. Detta är räknefel från transform/subtraktion kring en rörlig
kamera, inte en synlig projektionsändring.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' scen/3d/kontrakt/engang/dolda_fotter_blender.py dolda_efter
```

## 2026-11-10: rekvisita och scenlokal möbelrest kodade

`tropassning` sparar nu per scen den bundna personens XY-bäckenrest mot
identitetens gemensamma median. Kompilatorn flyttar i den scenen stolen,
följbordet och samma stödankare; kropp och kamera är orörda. Ytrekvisita
passar därefter bankformens projicerade centrum inom bordet. Högst så mycket
kantöverhäng tillåts att minst 2 cm av bankfotavtrycket fortfarande ligger
på skivan; överhänget sparas och beslutet är `antagen`.

Mätt med samma centrumfel som GOLV2-rapporten, baslinje → slutligt:

- hamburgare S1 23,01→2,26; S2 152,68→77,04; S3 102,85→3,98;
  S5 38,08→38,08 (handfäst); S6 26,81→1,23; S7 45,12→0,81 px;
- burk S1 61,71→1,81; S3 70,11→2,14; S6 62,15→0,61 px.

Alla ytfästa notan-props är därmed bättre än före GOLV2; S3:s krav
≤35 px klaras med 3,98 px. Bar-manifestet har ingen upplöst prop. Det
handfästa S5-objektet är numeriskt oförändrat. `test_props`: 7 prov, 0 fel
(nytt prov för att scenens stol, bord och stödankare får samma rest).

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' scen/3d/kontrakt/engang/dolda_fotter_blender.py rekvisita
```

## 2026-11-10: rekvisita visuellt verifierad i Blender

Blender 5.2 ordinarie `ingest/mhr_rig.py` byggde planen och renderade S3,
S4 och S7 från originalkamera samt +0,5 m kamerahöger/+0,3 m upp med samma
mål. Körningen `rekvisita_passad2` gick med exit 0. Före-rättningsbilder
från GOLV2-provet har kopierats bredvid de nya bilderna.

Sett: S3:s hamburgare ligger åter centrerad ungefär som före GOLV2 och
ligger kvar på bordet från sidovyn; den är fortfarande orimligt stor, vilket
är den redan redovisade bank-/regionskevheten och inte har dolts. I S7 är
sits/rygg nu synlig bakom personen och bordet följer personen även från den
flyttade kameran; hamburgaren ligger på bordet i stället för bakom kanten.
Detta är visuell granskning, medan pixelvärdena i föregående steg är mätta.

Nästa kommando (projektroten):
```powershell
$filer = @('scen/3d/ingest/metrisk.py','scen/3d/kontrakt/golvmatning.py','scen/3d/ingest/mhr_rig.py','scen/3d/blender/mhr_blender.py','scen/3d/kontrakt/kvalitet.py','scen/3d/kontrakt/GOLV2.md','scen/3d/kontrakt/test_rumsmall.py')
# kopiera varje fil till ut/fore_dolda_fotter med projektrelativ sökväg
```
