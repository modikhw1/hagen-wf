# Scen-JSON v0 — Luma-prov

Status: arbete pågår. Den här mappen är fristående; inga befintliga ingest-, kontrakt- eller läsformatdata ändras.

## Syfte

Provet jämför samma beordrade förändring i två keyframes: kameran flyttas 1,0 m bakåt längs scenens z-axel och huvudpersonen vrids 20° åt sin egen högra sida runt lodlinjen genom höften. Målet är att senare jämföra beordrad och SAM 3D Body-uppmätt förändring för tre Luma-instruktioner: siffror, ord och renderad guide.

## Källmappning

| Keyframe | Helklippsruta | Tid | Lokal ruta i tagningen | Exakt SAM-fil |
|---|---:|---:|---:|---|
| S1 | 36 | 1,200 s | 36 av 0–72 | `lasformat/luma-paket/poang/kropp/p/0000.npz` |
| S4 | 213 | 7,100 s | 42 av 171–255 | `lasformat/luma-paket/poang/kropp/p/0001.npz` |

Tidsmappningen följer `meta.json`: båda tagningarna är 30 fps; S1 innehåller 73 rutor och S4 85 rutor.

## Viktiga metodval

- Meterankaret är SAM 3D Bodys `pred_cam_t` och MHR-kropp. Det är det direkta resultatet för exakt keyframe, inte den senare historiska golvskalningen.
- S4:s kroppslängd och osynliga fötter hämtas från Wan-format A: 1,734 m och sammanhängande fotkontakt. Wan används inte som rumskälla.
- Rummet kommer från originaltagningens MoGe/Gemini-underlag. Enkelbildsdjup ger stöd för bildläge och relativa djup, men inte exakt metrisk geometri.
- S1:s golv är skymt och bestäms därför med antagen kamerahöjd/sitthöjd. S4:s golv stöds av Wan-fötterna men är fortfarande en härledning mellan två bildformat.

## Schema `scen/0.1`

Alla positioner och storlekar anges i meter. Koordinatsystemet är högerhänt med x åt bildens höger, y upp och z framåt längs kamerans horisontella blickriktning. Origo ligger på golvet lodrätt under originalkameran. `kamera.position` är därför `[0, h, 0]` i originalscenen.

Huvudfält:

- `kalla`: klipp, helklippsruta, tid, lokal tagning och exakta källfiler.
- `kamera`: position, pitch/roll, fokal, bildstorlek och synfält.
- `skala`: kroppens avstånd/längd som meterankare samt numerisk och verbal osäkerhet.
- `golv`: metod, stöd och om värdet är mätt, härlett eller antaget.
- `personer`: semantisk roll, anatomiska ankare, riktning, längd och återskapningsbar posekälla.
- `mobler`, `foremal`, `vaggar`: enkla lådor, punkter eller plan. De ska förklara bilden, inte låtsas vara en laserskanning.
- `kvalitet`: status per fält (`matt`, `harledd`, `antagen`) och kort motivering.
- `andring` finns bara i de ändrade filerna och specificerar transformerna i ordning.

## Diagnosgränser för `matt_andring.py`

Gränserna är diagnostik, inte acceptanskrav för Luma:

- **följde:** avståndsfelet ≤ 0,25 m, vridfelet ≤ 8° och övrig posedrift ≤ 5 cm.
- **delvis:** avståndsfelet ≤ 0,50 m, vridfelet ≤ 15° och övrig posedrift ≤ 10 cm.
- **följde inte:** något av måtten ligger utanför gränserna för delvis, eller SAM hittar ingen användbar huvudperson.

Det geometriska avståndsmålet räknas från JSON, inte som ett blint `+1,0`: den nya kameran står 1,0 m bakåt medan personen roteras runt höften, vilket kan flytta SAM:s kroppspunkt några centimeter.

## Löpande resultat

Kontrollsiffror, guidekalibrering, antagna ytor och slutstatus fylls på när rendering och mätning är klara.

## Kalibrering av mätverktyget (orkestratorn, 11 nov, efter att Codex-kvoten tog slut)

Teckenfel rättat i `matt_andring.py`: SAM:s kamerarum har y nedåt, så vridningen fick fel tecken. Rättningen kontrollerades mot axeldjupen i S4-guiden, där vänster axel kom ~13 cm närmare kameran, alltså ~20° åt egen höger. Renderingen var rätt från början.

| Bild | Avstånd uppmätt / beordrat (m) | Vridning uppmätt / beordrad (°) | Posedrift (cm) |
|---|---|---|---|
| S4 blockout, ny kamera | 0,85 / 0,82 | 18,4 / 20 | 5,1 |
| S1 blockout, ny kamera | 0,67 / 0,56 | 5,0 / 20 | 3,7 |
| Original mot sig själv | 0 / – | 0 / – | 0 |

Verktyget mäter S4 rätt. I S1 läser SAM inte vridningen ur blockouten: bordet skymmer, och den sittande figuren visar lite av bålen. S1-resultat från Luma ska därför läsas med försiktighet. `LUMA-PROMPTER.md` skrevs av orkestratorn.

## Luma-utfall, mätta 11 nov (`matt_batch.py`, resultat i `matning/batch/resultat.json`)

Beordrat: kameran 1,0 m bakåt, vilket ger en geometrisk avståndsförändring på 0,82 m i S4 och 0,56 m i S1, samt vridning 20° åt egen höger.

| Variant | Bild | Avstånd uppmätt (m) | Vridning (°) | Posedrift (cm) |
|---|---|---|---|---|
| a siffror | S4 | 1,06 | 0,6 | 2,0 |
| a siffror | S1 | 0,82 | −4,8 | 2,0 |
| b ord | S1 | 0,02 | 10,1 | 2,7 |
| c guidebild | S4 / S1 | 0,01 / 0,08 | −0,2 / 0,1 | 0,4 / 2,5 |
| c mellansteg (agentens "Step A") | S4 / S1 | 0,01 / 0,53 | 0,8 / 4,3 | 4,8 / 2,5 |
| **d JSON-bilaga** | S4 | **1,24** | **7,2** | 2,4 |

Avståndet mäts med fast brännvidd. Om Luma zoomade ut i stället för att flytta kameran syns det som ökat avstånd också, och en enskild bild kan inte skilja de två åt säkert.
