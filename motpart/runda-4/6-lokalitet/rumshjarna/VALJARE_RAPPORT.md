# Granskning av väljaren (`rumshjarna/valjare.py`)

## Metodens kärna (5 rader)
1. Delar OneFormer-instanser (`>=0,05 %` av bilden) i fyra separata klasser: `person`, `objekt`, `rum` (golv/tak/vägg/utomhus) och `overlagg` (centrerad vit skärmtext).
2. Ger varje instans ett viktat medel över de signaler som finns tillgängliga (`hand` 0,30 för objekt, `kropp` 0,30 för person, `aterkomst` L7 0,20, `bild` storlek+centrering 0,20, Laplace-`skarpa` 0,12, `semantik`-prior 0,10, `v3`-essens 0,08).
3. Halverar `hand` för stödytor/stora ytor (`>1 m` eller `>15 %`), kvartar 3D-hand utan 2D-stöd och multiplicerar osäkra OneFormer-segment (`<0,75`) med `0,8`.
4. Bygger `minsta_mangd` i rollordning: huvudperson(er) (`>=0,8 x bäst`) -> upp till 2 `i_handen` (`>=0,5`) -> 1 `platsmarkor` (L7 `>=0,5`) -> `fokus` (bästa objekt) -> `stod` (`>=0,75 x bästa`, max 4 objekt totalt) -> 1 `rumsankare`.
5. Resultatet skrivs per tagning i `ut/rumshjarna/<klipp>/valjare.json` utan klippspecifika konstanter eller GPU-anrop.

## Träffsäkerhet (38/38 tagningar med originalruta)
- **Täcker scenens kärnmening:** **18/38 (47 %)** — varav endast **6/38 (16 %)** är både heltäckande och helt brusfria.
- **Delvis:** **11/38 (29 %)** (oftast person + rum rätt, men handhållet föremål/handling saknas eller grovt brus stör).
- **Missar kärnmotivet helt:** **9/38 (24 %)**.

| Klipp | Kod-SHA | Täcker | Delvis | Missar | Notering |
|---|---|---:|---:|---:|---|
| `duepiani` | `f2257228` (ny) | 4/12 | 7/12 | 1/12 | 5/12 saknar handhållna ingredienser; `s8` 99,6 % `wall` |
| `spanjorskan` | `8c8cf427` (äldre) | 1/3 | 0/3 | 2/3 | `s1`/`s3` saknar tapasmaten; bakgrundsgäst + 0,1 % glas valda |
| `08burgerkebab` | `8c8cf427` (äldre) | 6/11 | 3/11 | 2/11 | `s2` saknar kebabspett; `s3` 0,4 % flaska slår pommesburk |
| `babasburgers` | `8c8cf427` (äldre) | 7/11 | 1/11 | 3/11 | `s1` sedel `i_handen`; `s6`/`s7`/`s9` mat blir `wall`/`table` |
| `kennysgelato2.0` | `f2257228` (ny) | 0/1 | 0/1 | 1/1 | 0,2 % pappkartong = `fokus`; presentpapper + skylt borta |

## De värsta fallen
- **`duepiani s8` & `babasburgers s6`:** Rena matnärbilder (pasta i stekpanna resp. dippsåser, chili cheese och Fanta) blir **99,6 %** resp. **91,8 % `wall`** i OneFormer → 0 resp. 1 perifert objekt kvar.
- **`kennysgelato2.0 s1`:** Rött presentpapper felklassas som `bed#9` (`sc=0,51`, `skarpa=0,046`), skylten sväljs av `wall#1` och 40,9 % schackgolv förlorar mot 23,3 % vägg; en **0,2 % pappkartong** (`box#5`) blir `fokus`.
- **`spanjorskan s3` & `s1`:** I `s3` ger falsk `i_handen` på ett stående vinglas (`0,900`) en `0,75`-gräns (`0,675`) som slår ut både bord (`17,7 %`) och all tapasmat (`food#41`/`#33`); i `s1` tar en bakgrundsgästs hand (`0,1 % glass#19`) plats från charkbrädan (`8,2 %`).
- **`babasburgers s1` & `s7`:** Digital 200-kr-sedel (skärmöverlägg) blir `painting#21 [i_handen]` och en 0,9 % stol slår ut bordet (`s1`); i `s7` slukas cheeseburgaren (`73,2 %`) i `table#2` och faller bort.
- **`08burgerkebab s2` & `s3`:** Kebabspettet sväljs i `wall#1` (`s2`); i `s3` har pommesburken i handen `2D=50 %` och `3D=0,00 m`, men halveras av falsk `stor yta` + `skarpa=0` och slås ut av en 0,4 % hörnflaska (`bottle#2`).
- **`duepiani s4–s7, s9`:** Alla fem handhållna ingredienser (högrev, röd slev, pepparburk, pastaskål, persilja) sväljs helt av `wall`/`stove`/`person`.

## Felmönster
1. **Inaktuella JSON-filer (25/38 tagningar):** `spanjorskan`, `08burgerkebab` och `babasburgers` kördes med äldre kod (`8c8cf427`) utan `kropp`, `STOD`/`halls` och 2D-krav på 3D-hand — det orsakar falska `i_handen` på bord/sedel och att huvudpersoner halkar till #6–#12.
2. **OneFormer-flaskhalsar (huvudorsak till totalmissar):** Matnärbilder kollapsar till `wall`/`table` (`duepiani s8`, `babasburgers s6/s7/s9`); små handhållna objekt och skyltar/kebabspett saknar egna instanser; fläktkåpor blir `ceiling` (byter klass till `rum` och tappar L7); matlådor splittras i dubbla `tray`-dubbletter (botten+lock).
3. **Hand- och personsignaler (även i ny kod):** `hander2d` tar med **alla** personer i bild (bakgrundsgäster utlöser `i_handen` i `spanjorskan s1`); `STOR_YTA` (`>15 %` eller 3D `>1 m` från djupstänk) halverar verkligt handhållna tallrikar/burkar (`duepiani s2`, `08burgerkebab s3–s6, s11`); centrerade bakgrundsgäster klarar `0,8 x bäst`.
4. **`0,75 x obj[0]`-kollaps:** När ett handobjekt får `hand=1,0` når det `~0,85–0,90`, medan ej hållna huvudobjekt (bord, mat, grill) har `hand=0` och maxar kring `~0,55–0,65` → `0,75`-gränsen rensar bort scenens övriga bärande objekt (`spanjorskan s3`, `babasburgers s11`, `08burgerkebab s10`).
5. **Småskräpsbias i `skarpa`, `aterkomst` och `bild`:** Laplace-varians gynnar små högkontrastobjekt (0,2–1 % flaskor/kartonger/glasreflexer) framför stora släta motiv (bord, presentpapper, matlådor); 10 %-taket i `bild` (`sqrt(andel/0,10)`) låter 23 % vägg slå 41 % golv (`kennysgelato2.0 s1`); `light#6` (2,3 % taklist) vinner `platsmarkor` via L7.
6. **Tvångsval och grafiköverlägg:** `fokus` och `rumsankare` väljs utan minimiarea/poäng (ger `wall` på 0,2–2,9 % i matnärbilder och `light#1` i suddig takövergång `08burgerkebab s8`); `overlagg_mask` fångar bara centrerad vit text, inte grafiköverlägg (sedlar), men felmärkte en stol bakom text (`babasburgers s10`).

## Allmänna förbättringar
1. **Kör om med nuvarande `valjare.py` + SHA-grind:** Synka alla klipp till samma `kod_sha256` så `kropp`, `STOD` och 2D-stöd för 3D-hand gäller överallt.
2. **Skärp person- och handkoppling:** Begränsa `hander2d`/`hander3d` till valda huvudpersoner (kräv dominerande yta/djup framför `centrering` för att filtrera bakgrundsgäster). Ersätt rå 3D-utbredning i `STOR_YTA_M` med robust 5–95 %-percentil och tillåt `halls=True` även vid `andel > 15 %` när `grupp` inte är i `STOD` och två händer/hög 2D-täckning finns (närbildskärl).
3. **Frikoppla `stod` från `hand`-toppen + mångfald:** Jämför `stod`-kandidater mot bästa *icke-hållna* objektet (eller poäng utan `hand`) så att ett handobjekt inte slår ut bord, mat och utrustning. Lägg till mjuk dubblettdämpning per etikett i `stod` så två `tray`/`glass` inte bränner hela 4-objektsbudgeten.
4. **Kalibrera storlek, skärpa och miniminivåer:** Höj `bild`-taket från `10 %` till t.ex. `35–40 %` (eller log-skala); dämpa `skarpa` för små segment (`<1–2 %`); kräv minimiandel (t.ex. `>=2 %` för `platsmarkor` och `>=5 %` + rimlig poäng för `rumsankare`, samt poäng-/areagolv för `fokus`) och låt inte `dekor`-etiketter (`light`, `lamp`, `painting`) bli ensam `platsmarkor`.
5. **Uppströms skyddsnät:** Flagga tagningar där `wall/table > 80 %` eller 0 `objekt` hittas (eller där 2D-handen faller helt i `wall`/`person`) för alternativ öppenvokabulär-segmentering runt hand/centrum; komplettera `overlagg_mask` med detektion av skarpa, platta 2D-grafiköverlägg i bildplanet.
