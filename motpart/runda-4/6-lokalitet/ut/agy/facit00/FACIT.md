# Visuellt facit för 0.0 (38 tagningar) mot L8-domen

Oberoende bedömning av original, `0°`, `35°`, `35°f` och `50°h` för samtliga 38 tagningar i 5 klipp. Detaljer per tagning ligger i `facit.json`. Endast **6/38 (16 %)** är `god_nog: ja`, **11/38 (29 %)** `delvis` och **21/38 (55 %)** `nej`.

## 1. Korstabell: L8-dom mot `god_nog`

| L8-dom | `ja` | `delvis` | `nej` | Summa |
| --- | ---: | ---: | ---: | ---: |
| `hög` | 3 | 2 | 5 | **10** |
| `medel` | 1 | 7 | 9 | **17** |
| `konflikt` | 2 | 1 | 5 | **8** |
| `låg` | 0 | 1 | 1 | **2** |
| `okänd` | 0 | 0 | 1 | **1** |
| **Summa** | **6** | **11** | **21** | **38** |

L8 har svag urskiljning för visuell användbarhet: bara 30 % av `hög` (3/10) är `ja`, medan 50 % av `hög` (5/10) och 53 % av `medel` (9/17) är `nej`.

## 2. Kategorier rangordnade efter frekvens och allvarlighet

Vikt = `2 × fel + brist` (max 76):

| Rang | Kategori | `fel` | `brist` | `ok` | Brister (`fel+brist`) | Vikt |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | **Objekt** | 22 | 16 | 0 | 38/38 (100 %) | 60 |
| 2 | **Rum** | 20 | 17 | 1 | 37/38 (97 %) | 57 |
| 3 | **Skala** | 8 | 15 | 15 | 23/38 (61 %) | 31 |
| 4 | **Kropp** | 12 | 5 | 21 | 17/38 (45 %) | 29 |
| 5 | **Golv och kontakt** | 10 | 3 | 25 | 13/38 (34 %) | 23 |
| 6 | **Kamera** | 2 | 10 | 26 | 12/38 (32 %) | 14 |

**Kamera** är pipens starkaste länk (68 % `ok`), medan **objekt** och **rum** brister i nästan varje tagning (ofta `fel` i 35°/50° trots hygglig 0°-bild).

## 3. Avvikelser: L8 säger `hög` men bilden är dålig — och tvärtom

**L8 = `hög`, men bilden är `nej` (5) eller `delvis` (2):**
- `duepiani s1` (`nej`), `duepiani s3` (`nej`), `08burgerkebab s7` (`nej`): `rumshjarna_fyllnad` avvisades och lämnade 4 281–5 232 grå antagna celler över halva scenen (plus jättepolygon i 50° i `s7` och kapad tallrik i `s3`). L8 straffar inte avvisad fyllnad eftersom `bildtackning` exkluderar personytan.
- `08burgerkebab s3` (`nej`): alla 6 signaler ger stöd, men mörka bakväggen försvinner i 35°/50°, matkärlen smulas sönder och vänster hand sticker rakt ned i maten.
- `08burgerkebab s4` (`nej`): 96 % täckning döljer att salladsdisk, kyl och hyllor splittras i skärvor och att skalan (1,51) sänker bänkhöjden till 0,49 m.
- `08burgerkebab s1`, `s10` (`delvis`): kamera/golv/vägg bär, men handhållna föremål raderas eller skärs av dockans hand/bröstkorg och löses upp i 35°.
- *(Blind fläck i `medel`)*: `08burgerkebab s8` (rörelseoskarpt svep → platt bildskiva + skräpdocka) och 6 sittande tagningar (`spanjorskan s1`, `babasburgers s1/s2/s5/s8/s11`) samt `kennysgelato2.0 s1` (helt fel pose) får `medel` trots `nej`.

**Tvärtom — L8 varnar (`konflikt`/`medel`/`låg`), men bilden är `ja` eller `delvis`:**
- `duepiani s5` (`konflikt` → `ja`): renaste 35°-köket i hela materialet; fälls enbart av 0,43 m avvikelse mot bullrig personyteskala medan fotkontakten (1,05) stämmer.
- `duepiani s6` (`konflikt` → `ja`): solid köksgeometri och god pose; L2c flaggar 40 % handkollision trots visuellt rimligt grepp kring burken.
- `duepiani s12` (`konflikt` → `delvis`): helt rak horisont (−9,3°), men `vittne_vp` falsklarmar med −59,4° på köksarkitektur; övriga signaler är gröna.
- `duepiani s7` (`medel` → `ja`): stabilt kök och god pose; hålls nere av 5,2° VP-avvikelse.
- `spanjorskan s2` (`låg` → `delvis`): L8 straffar med rätta 15,9°/43 % kamerarörelse, men mittrutans bordsplan och huvudrätt är plana och renare än många `medel`-närbilder.

## 4. De fem vanligaste felen i avläsningen (pipens steg)

1. **Fragmenterade 3D-ytor och förlorade objekt (`MoGe-djup` + djupsprångsklippning + `OneFormer-segmentering`):** Kluttriga diskar, restaurangbord, genomskinligt glas/plast och handhållna kärl faller sönder i lösa skärvor i 35°/50°. `OneFormer` slår ihop kärl med spis/vägg eller felklassar mat/panna som person.
2. **Sittande/beskurna kroppar skär in i mat och svävar utan stöd (`SAM 3D Body` + `golvplan` + `skala via personyta` + `L2c handkontakt`):** Utan synliga fötter saknar sittande personer stol- och golvstöd; bordshöjder rasar (0,00–0,59 m), både antagna cyanben och solida knän borrar rakt genom tallrikar/burgare, och `L2c`-djupflytt förvärrar ofta ben- och handkollisioner trots "0 % kollision".
3. **Grå hål bakom personer, 0°-spöksiluetter och tvärprojicerade helrum (`Rumshjärna V2`-grind + `L3d`-personmask + projektiv texturering i `L7`):** Avvisad fyllnad ger stora grå sjok utan L8-larm. Snäva kroppskapslar lämnar spöksiluetter av hår och vida plagg på bakgrundsduken, och i sammanslagna rum (`L7`, 50°) projiceras levande personpixlar rakt på en annan tagnings väggnät.
4. **Undertexter, 2D-grafik och rörelseoskärpa före 3D-stegen (`undertextmask` + `MoGe-djup` + `L9`):** Undertextmaskning stansar grå rektanglar rakt genom mat i närbilder, ocentrerad grafik blir kvar i scenen, och rörelseoskarpa svep kollapsar djupet till en platt skiva som ändå lurar `vittne_vp` och täckningsmåttet.
5. **Skaldrift, felposer och falska vittnen (`yolo11n-pose`/`SAM 3D Body` + `skala via fotkontakt` + `vittne_vp`):** Ovanliga poser (liggande) och bakgrundspersoner bakom glas ger helt fel docka eller svävande miniatyrer trots lågt 2D-restfel; bullrigt MoGe-golv drar ut fotkontaktsskalan till 1,5–1,7×, och `vittne_vp` kan falsklarma grovt i ögonhöjdsbilder samtidigt som branta närbilder saknar ankring.
