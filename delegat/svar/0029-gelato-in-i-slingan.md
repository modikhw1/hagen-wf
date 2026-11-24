---
id: 0029
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**Källan.** [kalla_0029.json](../../scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/kalla_0029.json) (revision 6) byggs i tre steg, och varje steg skriver en ny källa:
1. `kalla_foremal.py` (provskeden och disken blir props, s1+s2 en grupp)
2. `kalla_generering.py` (ny)
3. `kalla_mening.py` (ny)

Specarna ligger i `forvarld/gelato/spec_*.json`. S1 har nu:
- **Kroppen** ur Dreamina, med sitt ursprung: video, prompt, inställningar, tidsavbildning, roträttning och kamerans mått, allt med sha256.
- **Renderbanan** ur 0028.
- **Scenbygget:** disken med tråg och glasfront, bänken, kunden som platshållare och skedens fäste.
- **Mening:** 9 segment och 11 relevansposter. h9 är rättad till `luta_sig` mot kunden (märkt `rattad`), och kundens hand är tillagd som `bar`.

Bas-planen ur källan har samma renderkamera som `s_scen5` (största skillnad 1e-16).

| Förs in | Inflyttad i kedjan eller indata |
|---|---|
| kroppen (rot, tidspassning) | indata: sekvensen ur `gennedbrytning/`, ursprunget i källan; stegen flyttas in som kedja i 0030 |
| kameran | indata (`renderbana`); kompilatorn läser den (inflyttad läsning) |
| disk, tråg, glas, kund, fäste | indata (`scenbygge`); kompilatorn lägger in den (inflyttad), byggarna (`s_scen.py`, `r_sked2.py`) kvar |
| mening | inflyttad: `kalla_mening.py` |

**Regin.** `ta_bort_handling`, `tempo_handling` och `upprepa_handling` i `regi.schema.json` och `kompilera.py`. Kompilatorn skriver omsamplade kopior av sekvens och värld, så `mhr_rig.py` bygger oförändrad, med handfäste och stöd.
- **Märkning:** övergångar (6 rutor), omsamplade rutor och upprepningar är märkta i planen (`handlingsrutor`, `tidskarta`) och tysta.
- **`byt_prop`** når skeden i handen: den blir gul och märks `kaka`.
- **`kontrollera.py`** varnar "Meningen bärs av X" (eller "ramar") när en edit tar bort, byter eller skär i något som bär. Editen går igenom. Planen får `mening.varningar`.
- **Prov:** 8 nya i `test_tillstand_0029.py`.

**Jev** (`forvarld/gelato/prov.mjs`). Två villkor: med handlingsspår och relevans i tillståndet (`ut/`) och utan (`ut_utan/`). Familjerna är Notans frysta plus `handling.andra`.

| # | Mening | Jev med mening | Jev utan | Väntat | Nådde (med / utan) | Saknas |
|---|---|---|---|---|---|---|
| 1 | Hoppa över när hon skopar | handling, ta_bort **h3** | handling, inga segment | ta_bort h3 | **bild** / stannade | – |
| 2 | Gör skopandet långsammare | handling, långsammare **h3** ×2 | inga segment | tempo h3 | **film** / stannade | – |
| 3 | Två smakprov | handling, upprepa h8 ×2 | inga segment | h3–h8 ×2 | **film** (bara h8) / stannade | Jev väljer ett segment, inte förloppet |
| 4 | Byt glassen mot en kaka | prop, **saknas** | prop, provsked → kaka | sked eller prov | avvisad / **bild** | "innehållet i handen" (glassen på skeden) |
| 5 | Ta bort disken | prop, disk_A ta_bort | samma | samma + varning | **bild + varning** "ramar" / samma | disken är `ramar`, inte `bar` |
| 6 | Stabilisera kameran | stativ s2 | stativ s2 | s1 | tillämpad, s2 / samma | rätt scen (inåkningen är i s1) |
| 7 | En sekund längre i slutet | s2 +1 s håll | samma | håll eller h9 | **film** (30 hållna rutor) / samma | – |
| 8 | Hon ler efter kunden fått det | person.uttryck | samma | stanna med skäl | stannade (ingen väg) | mimik |
| 9 | Kunden tar emot med andra handen | handling, ta_bort **h8** | person.rorelse A | stanna med skäl | **fel bild** (h8 borttagen, varning: bär) / avvisad | kunden som person att casta |
| 10 | Foodtruck och stå still | plats.byt glass_disk | samma | stanna, båda delar | avvisad (ankaret) / samma | foodtruck-mall, rörelse; Jev fann bara plats |

**Bilder och filmer:**
- [m1](../../forvarld/gelato/ut/bild/m1_fore_efter.jpg): h3 är borta. Utruta 31 är mitt i övergången (hon rätar på sig), och h6 kommer 32 rutor tidigare.
- [m2](../../forvarld/gelato/ut/bild/m2_film.mp4): hon skopar fortfarande i utruta 100, där originalet redan står.
- [m3](../../forvarld/gelato/ut/bild/m3_film.mp4): hon räcker fram en gång till, märkt upprepning, och kundens arm följer med.
- [m4](../../forvarld/gelato/ut_utan/bild/m4_fore_efter.jpg): skeden blir gul i h6.
- [m5](../../forvarld/gelato/ut/bild/m5_fore_efter.jpg): hon böjer sig ned i tomma luften. Bänken och kunden står kvar.
- [m6](../../forvarld/gelato/ut/bild/m6_film.mp4): stativet gäller s2, där kameran knappt rör sig, så bilden är nästan som före. Skeden ur s1 hänger kvar i luften i utruta 161 (en brist i fästets synlighet, inte i stativet).
- [m7](../../forvarld/gelato/ut/bild/m7_film.mp4): källruta 251 hålls i 30 rutor.
- [m9](../../forvarld/gelato/ut/bild/m9_fore_efter.jpg): h8 är borttagen, och det är fel tolkning.

**Tillståndets storlek och tid:**
- **Storlek:** 10 rader och 991 tecken utan mening, 13 rader och 2 323 tecken med.
- **Inputtokens per anrop (median):** 1 192 utan och 1 730 med.
- **Jevs mediantid per mening:** 501 ms utan och 602 ms med. Maxtiden är 536 och 1 068 ms; med mening blir det ett anrop till för segmentet.
- **Kostnad:** 92 anrop och 170 329 inputtokens, cirka 0,007 USD inklusive provversionerna. Gatewayen användes inte. Modal användes inte.

**Bakåtkompatibelt**, tom cache, före-kod ur `kontrakt/ut/fore_0029/kod/`: samma sha256 för Notan, Notan med lokalbyte, bar, guacamole, b-tilltal 0016 och gelatos gamla källa (`forvarld/gelato/ut_kompat/{bas,ny}.json`).

**Tester:** 232 före och 240 efter. Samma åtta fel som i 0016 (`ut_kompat/tester_fore.log`, `tester_efter.log`).

## Bedömning
- **Handlingsspåret bär som tillstånd.** Med spåret når två av tre handlingsmeningar rätt bild. Utan spåret når ingen.
- **Jev hittar familjen även utan spåret,** men inte segmentet.
- **Segmentvalet är svagt:** h3 0,53 mot h8 0,35. Det krävde ett eget anrop och ingen `saknas`-utväg.
- **Meningen i tillståndet drog två svar fel:** m4 och m9. Jev letar handlingar där meningen gäller en person eller ett innehåll.
- **Begreppet som saknas mest:** "vad handen bär" (glassen på skeden, provet). Kakan, de två smakproven och kunden med andra handen stannar alla där.
- **Därefter saknas:** kunden som person, och följd eller förlopp som enhet ("räck fram igen" = h3–h8).
- **Nästa mot fler klipp:** samma spår och relevans på b-tilltal och guacamole (0030, påbörjat). Jevs segmentfråga ska prövas där innan den byggs vidare.

## Ändrade eller nya filer
- **Ändrade**, med före-kopior i `scen/3d/kontrakt/ut/fore_0029/kod/`: `kompilera.py`, `kontrollera.py`, `kalla.schema.json`, `regi.schema.json`, `scen/3d/PIPE.md` och `scen/3d/NASTA.md`.
- **Nya i kontrakt:** `kalla_generering.py`, `kalla_mening.py`, `test_tillstand_0029.py`, `ut/kand-kennysgelato_n06-hand/kalla_0029*.json` och `s1_renderbana_kalla_0029_gen.npz`.
- **Nya i `forvarld/gelato/`:** `prov.mjs`, `kompilera.py`, `bild.py`, `rendera_0029.py`, `bakatkompatibel.py`, `meningar.json` (kopia), `spec_*.json`, `ut/`, `ut_utan/`, `ut_hand/` (handskrivna provregier m1–m6), `ut_forsta/` och `ut_kompat/`.

## Kontroll mot "Klart när"
- [x] `kalla.json` med ny S1 och mening, bakåtkompatibel med sha256.
- [x] Tre regi-operationer med prov, och varningen för `bar`.
- [x] Tabell över tio meningar, med och utan mening.
- [x] Bilder och filmer för de meningar som gick.
- [x] Storlek och mediantid.
- [x] PIPE och NASTA.
- [x] Bedömning.

## Avvikelser
- **Källan heter `kalla_0029.json`, inte `kalla.json`.** Befintliga filer skrivs aldrig över; gamla `kalla.json` är revision 3.
- **Ny familj `handling.andra`** utöver Notans frysta, tillgänglig i båda villkoren. Tillståndet har också en handskriven rad om att kunden är platshållare, i båda villkoren.
- **Jevs segmentfråga ändrades tre gånger efter första körningen;** meningarna är oförändrade. Alla svar finns sparade:
  - `ut_forsta/`: en oavsiktlig körning när jag laddade modulen
  - `ut/forsta_*`, `andra_*`, `tredje_*` och `fjarde_segmentfraga/`
  - De gav h1, h1, `saknas` och `saknas` för m1. Tabellen visar den femte formen: ett eget anrop utan `saknas`. Det här är anpassning efter testmeningarna, och bör prövas blint på b-tilltal i 0030.
- **Disken som prop** kommer ur relevanslistan (`mobler_som_props`), eftersom gelatos semantik saknade props.
- **Trimning efter en handlingsändring i samma scen** stöds inte än. Den avvisas med skäl.
- **Tid:** cirka 40 minuter, 18:29–19:09 (`tidslogg-0028-0029.log`).
