---
id: 0004
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
**Linsen är inte huvudorsaken till oenigheten.** 1024 px (64 mm) ligger nära det jag mäter oberoende ur bilderna för S1–S6, 900–1050 px. Ett fokalbyte till 700–900 px flyttar lyften högst 0,11 m och minskar spridningen mellan S8, S9 och S11 bara från 0,54 till 0,47 m. **S5 är den enda tagningen med mätt fokal** (COLMAP: 11 av 16 rutor, 0,08 px, ej statisk): 2 335 px (146 mm). Mitt oberoende estimat ger cirka 900 px, men svagt (3 kandidater). De går inte ihop och jag kan inte avgöra vilket som gäller. Avståndet till kroppen skalar med fokalen (3,63 m vid 2 335 px, cirka 1,6 m vid 1 024), så S5:s misstänkta 3,67 m hänger på just det värdet.

### Datavägen, fil och rad
1. `ingest/ingest_klipp.py:96–121`: COLMAP på halv upplösning (`w//2`), `fokal_px = cam.params[0]*2`. Ett resultat finns för S1–S5, S9 och S10 (725–4 337 px) och saknas för S6–S8 och S11 (`colmap_fokal_px: null`).
2. `ingest/regler.py:8–17` (`kamerabeslut`): faller något krav (registrerade rutor ≥ 8, andel ≥ 0,5, fel ≤ 1 px, f inom 0,5–2,5 × längsta sidan) blir `fokal_px = max(bredd, höjd)` = 1024, status `antagen`. **Här tappas de uppmätta värdena.** Tio av elva tagningar (alla utom S5) faller på rutorna och andelen (COLMAP registrerar 2–3 av 12–24 rutor, `statisk: true`), och S3, S4, S9 och S10 dessutom på intervallet.
3. `ingest_klipp.py:130`: `fokal = beslut['fokal_px']` skickas som `cam_int` till SAM 3D Body (`ingest/modal_sam3db.py:49`). **Kroppsmodellen mäter ingen fokal.** `focal_length` i `kropp/*.npz` är en ekot av indatat (S6: 1024.0), så det är inget oberoende värde. `pred_cam_t` skalar med det.
4. `ingest/sekvens_stabil.py:45` tar medianen till `sekvens_*.npz['fokal']`, och `ingest/plats.py:153` för vidare `fokal_px`.
5. `kontrakt/kompilera.py:183–184`: `lins_mm = fokal * 36 / bredd`. 1024 → 64 mm, 2 335 → 146 mm. Någon `kamerafakta.py` finns inte, och `kvalitet.kamerakalibrering` är en tom lista i planen.
6. Ingen annan källa till intrinsik hittades. Reservvärdet är alltså en gissning i alla tagningar utom S5, och det loggas bara som `antagen`.

### Tabell per tagning (px; 16 px = 1 mm i planens 36 mm-sensor)
| tagn | reserv/använd | kropp (eko) | COLMAP rå | oberoende (försvinningspunkter, median, antal) |
|---|---|---|---|---|
| S1 | 1024 | 1024 | 1618 | 966 (3) |
| S2 | 1024 | 1024 | 725 | 908 (3) |
| S3 | 1024 | 1024 | 2656 | 923 (9, spridning 544–1228) |
| S4 | 1024 | 1024 | 4337 | 1056 (6) |
| S5 | **2335** | 2335 | 2335 (godkänd) | **904** (3, svag: 11–13 inliers) |
| S6 | 1024 | 1024 | – | 1039 (8) |
| S7 | 1024 | – | – | inget giltigt |
| S8 | 1024 | 1024 | – | 1529 (3, brant pitch, osäker) |
| S9 | 1024 | 1024 | 3436 | 1154 (2) |
| S10 | 1024 | 1024 | 3435 | 1753 (3, osäker) |
| S11 | 1024 | 1024 | – | 1304 (7) |

Oberoende metod (`vp.py`): linjesegment (LSD) i kakelfogar och dörr- och fönsterkanter, personerna och överlägget maskade, RANSAC på två till tre försvinningspunkter, f² = −(v₁−c)·(v₂−c). Över alla tagningar: 47 kandidater, **median 1 017 px, kvartiler 914–1 301**. S1–S6 ger 900–1 050. S8–S10 är brant nedåtfilmade och nära, så skattningen där är dåligt konditionerad och jag litar inte på de höga värdena. Egen tolerans (1,8°), ingen kravnivå.

### Omräkning utan kompilering
Kameran flyttas längs blicken så att personens bröst (1,05 m) hamnar på samma bildrad och storlek (avstånd × f_ny/f_gammal, pitch räknas om, höjd och yaw hålls). Lyft ur varje tagnings box, meter på golvet (`lins_tabeller.md`):
| fokal | spridning disk_C S8,S9,S11 | spridning vågen S8–S11 | vågen S11 från mediankluster |
|---|---|---|---|
| 1024 (före) | 0,54 | 0,92 | 0,68 |
| 900 | 0,50 | 0,83 | 0,61 |
| 780 | 0,47 | 0,76 | 0,55 |
| 700 | 0,46 | 0,71 | 0,51 |

Lyften flyttas mellan 1024 och 780 px: disk_C S7 0,01, S8 0,03, S9 0,04, S11 0,05 m. Vågen S8 0,09, S9 0,01, S10 0,11, S11 0,07 m. S6 flyttas 0,33 m men ligger fortfarande 1,6 m ifrån (fel box, se 0001). Med mindre fokal hamnar S9 dessutom ännu närmare personen (0,58 m).

**Svar på frågan: räcker rätt lins? Nej.** S8, S9 och S11 blir inte överens. Felet ligger kvar i bildrutorna och kameralösningen, enligt 0001:
- Högerkanten (S8 862, S11 846) kräver 4,0–5,9 m djup för en 2 m lång disk för fokalerna 700–1024, så den kan inte vara dess ände. I S8 sammanfaller x1 862 (497 px) med vågarmens högra kant i nyckelbilden (avläst på ögat).
- S11-vågboxen täcker bara displayen. S9:s kamera är 0,4–0,5 m för långt fram.

## Förslag på rättning (högst fem rader)
1. Fokal är en parameter per klipp (samma telefon), inte per tagning: ett värde ur de oberoende skattningarna (här cirka 1 000 px) i stället för 1024 som tyst reservvärde, loggat med osäkerhet (±100 px).
2. Låg reprojektionsfel räcker inte för att godkänna en COLMAP-fokal (`regler.py:8` säger det själv). Kontrollera den mot en oberoende skattning (S5: 2 335 mot cirka 900) och mot klippets övriga värde, och markera `antagen` när de går isär tills någon mätt andra källa finns.
3. Skriv `fokal_px`, `fokal_status` och `fokal_kalla` per tagning till `plan.json` (`kvalitet.kamerakalibrering` är i dag tom), så att nästa steg kan se att värdet är gissat.

## Ändrade eller nya filer
`scen/3d/kontrakt/ut/diag_0004/`: `lins.py` (+ `lins_resultat.json`, `lins_tabeller.md`), `vp.py` (+ `vp_resultat.json`, `vp_tabell.md`). Inget annat skrevs. Skripten kördes med `python -B -I`.

## Kontroll mot "Klart när"
- [x] Datavägen med fil och rad, och stället där värdet tappas: `regler.py:8–17`.
- [x] Tabell per tagning: reserv, kroppsläsare (är ett eko) och ett oberoende värde.
- [x] Omräkning av lyften före och efter, i meter.
- [x] Svar på frågan om rätt lins räcker: nej.
- [x] Förslag på rättning i högst fem rader.

## Avvikelser
- "Före och efter, samma tabell som 0001" är inte rakt av gjord. 0001:s referens var `los()`-slutläget, och här jämförs med medianen av lyften. Jag redovisar spridningen och hur långt varje lyft flyttas av fokalbytet.
- Försvinningspunktsskattningen är grov, och i S7 gav den inget giltigt värde. Den visar nivå, inte ett exakt värde. Kakelaliasen i b-tilltal kan påverka linjeklustren.
