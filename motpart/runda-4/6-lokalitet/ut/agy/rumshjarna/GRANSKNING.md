# Visuell granskning av V2-rum mot grinden (30 tagningar)

## Korstabell: grindens dom mot visuell bedömning

| Grindens dom | `ja` | `delvis` | `nej` | Totalt |
|---|---:|---:|---:|---:|
| Släppt (`tillit: hög`) | 18 | 6 | 2 | **26** |
| Avvisad (`tillit: låg`) | 1 | 1 | 2 | **4** |
| **Totalt** | **19** | **7** | **4** | **30** |

- **Falskt släppta:** 8 av 26 (31 %) brister — **2 direkt dåliga (`nej`)** och **6 delvis användbara (`delvis`)**.
- **Falskt avvisade:** **1 av 4 (`babasburgers s1`)** är fullt användbar (`ja`); ytterligare 1 (`08burgerkebab s7`) är `delvis`.
- **Huvudmönster (oberoende vs ankare):** Bland 16 oberoende tagningar är 14 `ja` och 2 `nej` (båda korrekt fångade av grinden). Bland 14 ankarbetingade (`fas2_mot_ankare`) är bara 5 `ja`, 7 `delvis` och 2 `nej` — **samtliga 8 problemfall som grinden släppte igenom (100 %) är genererade mot ett ankare.**

## Rumsgruppernas inbördes konsistens (8 grupper)

- **God konsistens (3):** `spanjorskan {s1,s3}`, `babasburgers {s10,s11}` och `babasburgers {s1,s5,s8}` (samma bordsrad/inredning, mindre golvskillnad i `s1` samt utsnittsskift i `s5`).
- **Innehållsligt lika men ankarskador (2):** `duepiani {s1,s3}` (`s1` får 5–12 px skalfel); `duepiani {s4,s5,s6,s7,s9}` (identiska redskap/brunn, men `s6`/`s7` drar mot `s4`:s utsnitt och `s9` ärver `s4`:s bortplockade plastkantin).
- **Inkonsekventa (3):** `duepiani {s11,s12}` (induktionshäll flyttad 3–4 kakelplattor i 3D); `08burgerkebab {s1,s3}` (`s1` har fritös/hörnlist/påhittad korvgrill, `s3` bara kort stekbord); `08burgerkebab {s4,s5,s6,s7}` (`s5` kapar bänken till en gång och byter durkplåt mot klinker).

## De värsta fallen

1. **`duepiani s6` (släppt, `nej`):** Skiftade +54 px mot ankaret `s4`; efter affin registrering ligger spis, pannor, kakel och fläkt 15–30 px fel (median 20,4 px). Periodiskt kakel lurade blurrad kanttrohet (`0,61`) och plant djupfel (`0,017`).
2. **`duepiani s12` (släppt, `nej`):** Ankaret `s11` tvångskomprimerades in i ett smalare utsnitt: blå induktionshäll klistrades in 3–4 kakelplattor fel över synlig vänsterutrustning, väggar skiftar ~6–11 px och bänklådor 20–30 px (`df=0,025, tr=0,68`).
3. **`08burgerkebab s1` (släppt, `delvis`):** Synligt slätt stekbord skrevs över med påhittad korvrullgrill, en 5:e såsflaska lades till och rummet motsäger ankaret `s3` (`df=0,025, tr=0,81`).
4. **`08burgerkebab s5` (släppt, `delvis`):** Kylbänken klipptes av till en gång, golvet byttes mot klinker (mot ankaret `s4`), synliga flaskor togs bort och extra muggar/kantin lades till (`df=0,083, tr=0,81`).
5. **`duepiani s9` (släppt, `delvis`):** Ankaret `s4`:s plastkantin klonades in på tom stålbänk, medan synlig brandsläckare och slev togs bort (+13 px kantreplikering till höger).
6. **`babasburgers s5` & `duepiani s7` (släppta, `delvis`):** Kvarstående 5–20 px perspektivskifte efter affin registrering mot ankare.
7. **`babasburgers s1` (avvisad, `ja` — värsta falska avvisningen):** Knivskarp 0,9 px linjering och ren bakgrund; överlagrad 200-lapp utanför personmasken hamnade i `synl` och gav falskt djupfel `0,203`.
8. **`08burgerkebab s7` (avvisad, `delvis`) & `duepiani s10` (släppt, `ja`):** `s7` fick 18–22 px kantreplikering på tre sidor (`skala=1,027`) men avvisades bara av djupoffset; `s10` släpptes med orimlig djupskala `kz=0,365` (1380 flygpixlar) p.g.a. borttagen hållen bunke utanför personmasken.
9. **Korrekt avvisade (`nej`):** `duepiani s2` (huvudmotivet tallriken borttaget, helt annat rum) och `08burgerkebab s8` (extrem rörelseoskärpa).

## Förslag på allmänna förbättringar

### Grind och registrering
1. **Nyckelpunktsresidual och warpgräns:** Mät SIFT/ORB-median och P90-fel på synlig yta efter registrering (t.ex. median ≤ 4 px, P90 ≤ 15 px) och avvisa eller flagga stor affin skift/skala samt `BORDER_REPLICATE`-andel > 1–2 %. Fångar perspektivskift i `duepiani s6/s7/s12/s1`, `babasburgers s5` och kantränder i `08burgerkebab s7`.
2. **Lokal synlighetstrohet (rutnät):** Ersätt/komplettera global blurrad kantkorrelation med rutnät (t.ex. 4×4 block) av skarp kant-/strukturavvikelse på synlig yta så lokala överskrivningar och ankarkloning inte dränks i medelvärdet (`08burgerkebab s1/s5`, `duepiani s9/s12`).
3. **Maska text/grafik och handhållna objekt före `synl`, samt begränsa `kz`:** Exkludera detekterad överlagrad text/grafik och objekt i handkontakt ur `synl` (räddar `babasburgers s1`, hindrar fel skala i `duepiani s10`), kräv rimlig djupskala (t.ex. `0,65 ≤ kz ≤ 1,35`) och pröva robust skala+offset-djupfel.
4. **Skärpegrind före generering:** Hoppa över extremt rörelseoskarpa nyckelrutor (låg Laplacian-varians) som saknar 3D-geometri (`08burgerkebab s8`).

### Prompt och genereringsflöde
5. **Lås synliga pixlar (maskad inpainting / hård komposit):** Låt bildmodellen endast fylla en vidgad person-+textmask och behåll originalets synliga pixlar oförändrade. Eliminerar utsnittsdrift, kantreplikering och ankarkontaminering i synliga ytor.
6. **Skärp ankarprompten (`v2_konsistent_allman.txt`):** Ange uttryckligen att objekt i referensbilden som ligger utanför målbildens synfält **inte** får krympas eller flyttas in, och att lösa/tillfälliga föremål inte ska kopieras över till synliga ytor.
7. **Skydda huvudmotiv i närbild:** Hoppa över eller ändra prompt när synlig bakgrund understiger t.ex. 25 % eller när ett segmenterat förgrundsobjekt i händerna dominerar centrum (`duepiani s2`).
