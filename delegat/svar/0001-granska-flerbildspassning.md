---
id: 0001
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
**A. Går att köra på: ja. Går att lita på: nej.** Ändringarna importeras, ger inga undantag och skriver bara till planen i minnet. Det jag körde var `mobellyft.los` och `foremallyft.los` på en `deepcopy` av `n06-fler/narvaro/plan.json`, utan kompilering. Följdrättelsens punkt 1 fungerar: `disk_C` är nu `flyttad` där planen sa `bevarad`. Punkterna 2 och 3 saknas. Slutläget `[1,87; 0,91]` ger ändå 716–1133 px RMS på S6, S8 och S11 och lägger bordet 4 cm in i S9:s kamera.

**B. Problemet ligger i indatat, inte i passningen.** Fyra av fem `disk_C`-boxar är fel eller går inte att reproducera. Kamerorna är lösta med reservvärden och är därför inte heller inbördes pålitliga. Detaljer i tabellerna: [tabeller.md](../../scen/3d/kontrakt/ut/diag_0001/tabeller.md).

### Del A, rad för rad
| Fil:rad | Bedömning | Kommentar |
|---|---|---|
| boxpassning.py:154–159, 125–137 | färdig | Lådan bakom en kamera ger ett bundet straff och `anvand: false` per tagning (följdrättelse 1). Straffet är konstant, så det saknar gradient. |
| boxpassning.py:112–123 | färdig | Startpunkten hålls framför alla kameror (1 mm). Kravet 0,30 m kontrolleras inte här utan i mobellyft. |
| boxpassning.py:82–83, 143–146, 90–93 | **ofullständig** | En helt beskuren box ger `ValueError` utan `try`. Då avbryts hela passningen (`mobellyft.py:233` ger `bevarad`) i stället för att den tagningen hoppas över. |
| boxpassning.py:87–94 | **ofullständig** | `tillforlitligast` väljer boxen med flest obeskurna kanter. Det blev S6, som är fel box. Startläget blev `[2,785; 0,906]` och slutläget `[1,871; 0,906]`, alltså 0,9 m i x. |
| boxpassning.py:163, 180 | ofullständig | Gränsen ±20 m släpper fram `y = 3,04`, det vill säga bakom personen (y 1,36), innan klämningen drar tillbaka. `lyckad` mäter bara den obegränsade passningen. |
| mobellyft.py:97–111 | färdig | `_enbildslage` ger startvärde. Den tar boxmitten i x även när sidorna är beskurna (`foremallyft.py:41`), vilket spelar liten roll för ett startvärde. |
| mobellyft.py:131–169 | **ofullständig** | Vid lokal konflikt (S9: 0,77 m till person, 0,90 krävs) tas kamerans nedre gräns bort (145–147). Reservvägen (153–156) använder bara personvillkor. Resultat: kameramarginal **−0,04 m**, `granskonflikt: true`. |
| mobellyft.py:114–128 | fel (lågt) | Dubblett av `boxpassning.py:97`, men utan skyddet `a@a > 1e-12`. |
| mobellyft.py:196–214 | färdig | Startfel fångas (199–201), `framfor_alla_kameror` används, och alla tagningar loggas per post. |
| foremallyft.py:105–111 | **saknas** | Följdrättelse 2 (ersättningsstöd) är inte gjord. `kottbit` är fortfarande `bevarad`. |
| test_snabb.py | **saknas** | Fortfarande 19 test. Inget täcker bakom-kameran, start framför kameror eller ersättningsstöd (följdrättelse 3). |

### Del B
Kameror i den gemensamma ramen (planens världskoordinater): se tabell 1. Kort sagt:
- **Samma kameradata i alla tre planerna** (`mobel2`, `skymning`, `fler`).
- **Alla `bildkamera`-poster är `bevarad`.** Inget har lösts om.
- **Yaw 90°, höjd 1,40 m och lins 64 mm gäller för alla tagningar utom S5.** S5 har 146 mm. 64 mm är 1024·36/576, alltså reservformeln i `kompilera.py:184` (`max(bredd, höjd)` som fokal), inte ett mätt värde. Då är FOV 31,4°.
- **S8–S11 delar deklarerad kamera `kamera_4` (y 0,069)** men har y 0,21 / 0,59 / 0,09 / 0,20 (pitch −17,5 / −17,4 / −11,1 / −7,5).

Avstånd på golvet (m) mellan lyft ur just den tagningens box och slutläget (tabell 6; ingen kolumn betyder att rutan saknas):
| tagn | kamera x,y | disk_C | disk_A | vågen (obeskuret / klämt) |
|---|---|---|---|---|
| S1–S4 | −0,12…0,05 , −0,05…0,25 | – | ingen box | – |
| S5 | 1,98 , −2,26 | – | – | – |
| S6 | 2,17 , −0,26 | **2,25** | – | – |
| S7 | 2,17 , −0,18 | 0,31 | – | – |
| S8 | 2,05 , 0,21 | 0,19 | – | 0,27 / 0,27 |
| S9 | 2,16 , 0,59 | 0,36 | – | 0,18 / 0,16 |
| S10 | 2,18 , 0,09 | – | – | 0,26 / 0,26 |
| S11 | 2,37 , 0,20 | 0,54 | – | **0,65** / 0,18 |

**Grupper (0,3 m, fullänk):** disk_C {S7, S9, S11}, {S8} (0,31 från medianen), {S6} (2,0 m bort). Vågen {S8, S10} medan S9 och S11 hamnar 0,4–0,9 m bortom bordets bakkant. Klämningen i `foremallyft` pressar ihop alla fyra till y 0,73–0,83 och döljer oenigheten.

**Orsak per avvikare:**
- **S6, fel bildruta.** Boxen `[693,718,933,1000]` ligger på kassadelen längst ned till höger. Bordsytan i nyckelbilden börjar vid cirka 0,87 av höjden (avläst på ögat). Med övre kant 870 blir lyftet `[2,18; 0,65]`.
- **S7, fel bildruta.** Övre kant 790 mot cirka 875 i bilden ger y 0,98 mot 0,68. Det är 0,3 m, bara ur boxen. Rättade S6 och S7 stämmer inom 0,04 m, och y 0,65–0,68 ligger nära bordet i planen.
- **S8, S11, deklarationens topologi eller lins.** Högerkanten (x1 862 och 846) kan inte nås. Ett 2 m långt bord på 0,5–0,9 m djup har sin högra ände långt utanför bild med FOV 31,4°. Kantpassningen går i golvet (−4 m) i `kamerabehov.py`.
- **S9, fel kameralösning.** y 0,59 mot 0,09–0,21 i de tre andra `kamera_4`-tagningarna, 0,77 m till personen och kameran 4 cm inne i bordet. Vågboxarna i S8 och S9 kräver oberoende y ≈ −0,17.
- **S11 (vågen), fel bildruta.** Boxen täcker bara displayen (y 457–710, x0 161 trots beskuren vänsterkant). I S8–S10 täcker boxen hela apparaten.
- **disk_A, ingen box.** Detektionen gav `[]` trots S1–S4. Den gamla S1-rutan ger bara övre kant och kräver kamera 0,47 m längre bak.

**Rekommendation:**
1. Blandning: möblerna i en gemensam ram (x ≈ 2,2, y ≈ 0,66–0,73 ur de rättade S6 och S7), kameradjup och lins per tagning. Ren placering per tagning är sämre (2,25 m i S6, upp till 0,9 m i S9).
2. Boxarna i S6, S7 och S11 behöver kontrolleras innan någon passning, och en helt beskuren box ska hoppas över.
3. Det som avgör: lins och kameraavstånd mätt ur fasta bakgrundsdrag som syns i S6–S10 (kakelplattor, dörrens runda fönster). Det är PIPE Öppet 6b och ger lins och djup utan person.

## Ändrade eller nya filer
- `scen/3d/kontrakt/ut/diag_0001/kameror.py` (+ `kameror.json`): kameror per tagning.
- `…/lyft.py` (+ `lyft_fler.json`): lyft per tagning och passning.
- `…/kamerabehov.py` (+ `kamerabehov_fler.json`): hur långt varje kamera behöver flyttas.
- `…/sammanfatta.py` → `tabeller.md`: alla sex tabellerna, plus `los()` på minneskopia.
- Inget annat skrevs. Skripten kördes med `python -B -I` (inga `.pyc`).

## Kontroll mot "Klart när"
- [x] Del A, fil och rad per ändring: tabellen ovan.
- [x] Del B, tabell per tagning S1–S11 med kamera och meter: tabell 1 och 6. Disk_A: inga boxar.
- [x] Del B, grupper (0,3 m) och troligaste orsak per avvikare: ovan.
- [x] Rekommendation i högst fem rader: ovan.

## Avvikelser
- Jag tittade på nyckelbilderna för S6–S11 (`%TEMP%\rum_detektera_*.jpg`, skrivskyddat). Kanternas lägen är avlästa på ögat och ska kontrolleras mot mätning.
- "Passat läge" är inte entydigt: den obegränsade passningen `[1,87; 3,04]` är meningslös (bakom personen). Jag använde därför `los()`-resultatet (efter klämning) och medianen utan S6 som referenser. Båda finns i `tabeller.md`.
- `kottbit` (inslagspapper som stöd) togs inte med. Den ingick inte i uppdraget och är oförändrat obyggd.
