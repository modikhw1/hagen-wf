---
id: 0016
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

## Resultat
m2, m5, m6 och m9 går nu hela vägen till en bild som visar det som begärdes. För m2 gäller det att scenerna flyttats som grupp, som uppdraget anger. Inga av de fyra meningarna har ändrats. Kedjan för själv över vågen, köttbiten och scengrupperna till källan (`kontrakt/kalla_foremal.py`, `n06-hand/kalla_0016.json`, revision 4). Notan, Notan med lokalbyte, bar och guacamole ger plan med samma sha256 före och efter ändringen, med tom cache per variant ([bakatkompatibel.py](../../forvarld/btilltal/bakatkompatibel.py)). Jev: 32 anrop, 105 006 inputtokens, cirka 0,004 USD.

| # | Jevs val 0014 → 0016 | Väntat | 0014 kom till | 0016 kom till | Saknas fortfarande |
|---|---|---|---|---|---|
| 1 | ta_bort s5 → samma | samma | bild ✔ | tillämpad (bild som 0014) | – |
| 2 | flytta s3 efter s2 → **flytta grupp_B först** | grupp_B först | no-op | **bild ✔** | tavlan visar Mads före Morten; r3 korsar gruppkanten och redovisas |
| 3 | st79 byt → samma | samma | bild ✔ | tillämpad | radbrytning |
| 4 | s6, C, nära → samma | samma | bild ✘ | tillämpad, bild ✘ | utsnitt per tagning |
| 5 | saknas → **vag, ta_bort**, alla* | vag, alla | ej tillämpad | **bild ✔** | – |
| 6 | saknas → **kottbit, byt, "ost"** | kottbit → ost | ej tillämpad | **bild ✔** (gul platshållare) | ostens form (stilisering) |
| 7 | lägg till efter s4 → efter grupp_C | ny person | avvisad (schema) | avvisad ensam: `efter` grupp gäller inte lagg_till_scen | person att casta, scenmall |
| 8 | glass_disk → samma | samma | avvisad | avvisad (ankaret staplats_A) | ankare som roller |
| 9 | s11 +1,0 s → samma, nu `hall_sista` | samma | regin kastades | **bild ✔** (30 hållna rutor) | – |
| 10 | C, s2 → samma | A, s2 | avvisad (schema) | avvisad ensam: rörelse stöds inte | rörelsebibliotek; Jev valde fel person |

\* Första svaret var s8. Omfattningsfrågan fick tillägget "välj alla scener om meningen inte själv nämner en scen", och då blev svaret alla. Det första svaret ligger i `ut_0016/forsta_omfattning/`. m6:s nya typ tas ur meningen ("mot en ost") på samma sätt som ny text tas ur citat; Jev väljer bara "meningens".

**Bilder** (`forvarld/btilltal/ut_0016/bild/`):
- [m2](../../forvarld/btilltal/ut_0016/bild/m2_fore_efter.png): Morten öppnar klippet. Tavlan visar ändå "Mads: 2,400 / Morten:", alltså fel ordning, eftersom tavlan inte ingår i uppdraget.
- [m5](../../forvarld/btilltal/ut_0016/bild/m5_fore_efter.png): vågens låda är borta i s9 och Lærke syns bakom disken. Det stämmer.
- [m6](../../forvarld/btilltal/ut_0016/bild/m6_fore_efter.png): det Lærke håller har samma läge och mått men är gult och märkt platshållare. Det stämmer.
- [m9](../../forvarld/btilltal/ut_0016/bild/m9_fore_efter.png): ruta 490 håller Lærkes sista lästa ruta (466) med köttbiten. Källans tre sista rutor är olästa, så den hållna bilden visar mer av henne än källans sista ruta. Det stämmer.

**Tillståndets storlek och tid:** 24 → 27 rader och 3 872 → 4 257 tecken. Mediantal inputtokens per anrop gick från 3 027 till 3 285. Jevs mediantid per mening gick från 523 till 535 ms och maxtiden från 679 till 734 ms. Routningen har alltså inte blivit långsam.

**Tester:** 232 körda, 224 gröna.
- Nya prov för punkterna 1–5: 9 st i `test_tillstand_0016.py`, alla gröna. Ett av dem är ett integrationsprov på b-tilltal med grupp, våg, ost och hållning.
- Två befintliga prov skrevs om till den nya regeln i punkt 5: `test_steg11 …hela_regin` (referensfelet) och `test_handelser …stoppar_fore_bygge`. Båda är gröna. Före-kopior finns i `fore_tillstand_0016/kod/`.
- Åtta prov faller också i baslinjen: fyra i `test_rumsmall` (skymning och möbelintervall), två i `test_steg11.Skymning`, `test_flode` jämförelsen mot `ingest_klipp` och `test_flode.Plats` rummets täckning. Ingen av dem ligger i kod som 0016 rör. `Plats` och `Skymning.nytt_tidsurval` kördes mot baslinjens kod med samma fel.

## Ändrade eller nya filer
- **Ändrade** (före-kopior i `scen/3d/kontrakt/ut/fore_tillstand_0016/kod/`): `kompilera.py`, `gemensamt.py`, `kontrollera.py`, `kalla.schema.json`, `regi.schema.json`, `test_steg11.py`, `test_handelser.py`, `scen/3d/PIPE.md` och `scen/3d/NASTA.md`.
  - `kompilera.py` har nu grupper, `hall_sista`, `foremal_i_plan` och `halla_i_plan`. `gemensamt.py` avvisar en edit ensam. `kontrollera.py` godtar grupp-id och `hall_sista`.
  - Schemana har tre nya valfria fält: `semantik.scengrupper`, `prop.deklaration` och lage `hall_sista`.
- **Nya:** `scen/3d/kontrakt/kalla_foremal.py`, `test_tillstand_0016.py`, `ut/b-tilltal-ravara_n06-hand/kalla_0016.json`.
  - Under `forvarld/btilltal/`: `bakatkompatibel.py`, `ut_0016/`, `ut_hand/` (handskrivna förprov), `ut_kompat/` (sha256-jämförelse och testloggar).
  - `prov.mjs`, `kompilera.py` och `bild.py` tar nu en ut-mapp eller `PROV_0016=1`. 0014:s `ut/` är orörd.

## Kontroll mot "Klart när"
- [x] Testerna är gröna med antal, nya prov för punkterna 1–5 finns, och de åtta fel som finns i baslinjen är redovisade.
- [x] Tabell före och efter för alla tio meningar.
- [x] Före- och efterbild för m2, m5, m6 och m9.
- [x] Tillståndets storlek och Jevs mediantid.
- [x] Tillägg i PIPE.md och överst i NASTA.md.

## Avvikelser
- **Punkt 6:** prov.mjs byggfel är rättade, så m7 och m10 följer schemat. De stannar nu i kompilatorn av verkliga skäl (grupp som `efter` i `lagg_till_scen`, och att rörelse inte stöds).
- **Omfattningsfrågan för föremål är omformulerad**, men meningarna är oförändrade (se \*).
- **"Håll sista rutan" håller den sista lästa rutan**, inte källans sista ruta, eftersom S11:s tre sista rutor saknar kropp. Planen märker rutorna `hållen … inte läst`.
- **Kameragruppskopior som efterstegen lade helt inom hållningen tas bort.** Ett exempel var en `disk_C`-kopia ur S8+S10.
- **Ny regel i punkt 5:** en referensfelaktig edit kastar nu bara sig själv när kompilatorn kontrollerar med `avvisade`. `kontrollera.py` på kommandoraden avvisar fortfarande hela regin.
- **Cachen:** tom cache användes för sha256-jämförelsen och för `ut_0016`. Testsviten körde mot kontraktets vanliga cache, som nycklas på kodhash.
