# MENING – Claude runda 1: A2 (R25), A4 (visuell rubrik), Lager 4 och visuell sanning

19 nov 2026. Allt nedan går att köra om. Inget i `forvarld_karna/` eller `byggsten/` är ändrat; koden importeras och läses.

```powershell
$env:PYTHONIOENCODING="utf-8"; cd motpart\runda-1-claude
..\..\scen\.venv\Scripts\python.exe mening_rubrik.py    # A4: rubrik + överlägg      -> mening_ut/mening_rubrik_*.json|md, mening_overlagg_*.png
..\..\scen\.venv\Scripts\python.exe mening_r25.py       # A2: syntet + riktiga klipp -> mening_ut/mening_r25*.json|png
..\..\scen\.venv\Scripts\python.exe mening_attityd.py   # Lager 4: stabilitet, arv, fysik, tid -> mening_ut/mening_attityd.json
..\..\scen\.venv\Scripts\python.exe mening_render.py    # Blender 5.2 headless       -> mening_ut/mening_blender/, mening_render_*.png
```

## 0. Sammanfattning

| id | påstående (Argon) | resultat | status |
|---|---|---|---|
| A2 | R25 separerar kamera från kropp med "0 px avvikelse" | "0 px" är en identitet: kropp och kamera flyttas lika mycket. På riktiga klipp har R25 slagit till på 6 tagningar. På 3 av dem står kameran i stort sett still enligt bakgrunden (asketch S1, S7 och notan S7), så kroppens rörelse har flyttats till en kamera som inte rör sig. I syntetiska tester med facit ger R25 upp till 151 px fel i var rummet hamnar i bild (395 px vid panorering), samtidigt som kroppen ligger rätt i bild. En prototyp som skattar kamerarörelsen med PnP mot bakgrunden och MoGe-djup (R25c) hamnar inom 2 cm och 2.3 px i alla fyra scenarier. | **fallit** (prototyp finns) |
| A4 | Visuellt verifierat i Blender | Med en rubrik i 4 kriterier över 21 person-tagningar får 6 noll på hållning, 10 på möbel, 4 på utsnitt och 9 på kontakt. Sittande och flera stående personer står i djup huk i 3D med knät 0.12–0.29 m över golvet. | **fallit** |
| L4-a | `AttitydProfil` (26.4°, 0.54) är en stabil personegenskap | `lutning_deg` tål brus (±0.1–0.8°) men drar med sig kamerans pitch: `scen_brygga.py:254` kastar receptets pitch och roll. Korrigerat blir gelato A 36.2° → 19.7° och guacamole A 26.4° → 23.2°. `slapphet` och stiletiketten slår om redan vid 5 mm extra ledbrus och mellan 1-sekundsfönster inom samma tagning. | **delvis** |
| L4-b | `ga_med_attityd` bevarar attityden | Lutningen bevaras eftersom ryggraden kopieras. Per tagning byter etiketten i 2 av 3 tagningar. Gången glider: fötterna rör sig 0.28–0.49 m/s i stödfas, och personen går på stället under sista halvsekunden. Gångriktningen skiljer upp till 19° mellan tagningarna. | **delvis** |
| L4-c | `byt_hand` = spegling + bålvridning, fysiskt rimligt | Ingen bålvridning finns: ryggraden ändras 0.000 m. Spegelplanet ur dolda höfter ligger 9.9° fel (p90 14.5°), så axellederna flyttas 8.8 cm. Den nya handen räcker fram smakprovet 0.62 m från originalets mål. | **fallit** |
| L4-d | < 50 ms i kod, < 250 ms med Jev | Inte uppmätt i `forvarld_karna`, där ingen tidtagning finns. Uppmätt här tar `manipulera_scen` 531–684 ms (median), och Jev-routningen är inte inkopplad. | **fallit** |

## 1. A4 – visuell rubrik

### 1.1 Definition (upprepbar)

Varje person i varje tagning får 0 (fel), 1 (delvis), 2 (rätt) eller – (ej tillämpbart) på fem kriterier. Den automatiska delen ligger i `mening_rubrik.py`. Den visuella delen är min bedömning av `jamforelse.png` plus de nya överläggen, där paketets projektion ritas på originalrutan.

| kriterium | automatiskt mått | gräns 2 / 1 |
|---|---|---|
| **H** hållning | Lårets vinkel mot horisontalplanet, knävinkel, knähöjd, bäckenhöjd, fart och nettosträcka ger klassen sitter/står/går/huk/oklar, som jämförs med `pose` | klassen = etiketten / oklar |
| **M** möbel | Bord som `obs.json` säger syns i tagningen ska vara synliga (`synlig_ut`) och ligga i bild (>1 % av ytan). En skiva med underkant >0.25 m utan stöd räknas som svävande. | alla finns och ingen svävar / finns men svävar |
| **U** utsnitt | Mäts mot **oberoende 2D**: trackerns ruta (`personer.json`) och personmasken (`masker.npy`) jämförs med paketets projektion genom paketets kamera. Mätvärden: IoU, mittfel, andel överkroppsleder i masken och andel rutor där kroppen hålls kvar utan detektion (`kand=False`). | IoU ≥0.6, mask ≥0.7 och <10 % hållna / IoU ≥0.35 och mask ≥0.4 |
| **K** händer/kontakt | Om obs säger "vid bord": handledens avstånd till skivan när handen är över den, samt handled inne i skivan | <0.08 m och <5 % inne / <0.20 m |
| **P** manipulation | Gör manipulationen det som påstods? Mäts i avsnitt 3. | – |

Kända svagheter i den automatiska delen: IoU straffar ben som döljs av bord i originalet (höjdkvot 1.4–2.4 för sittande), och när båda rutorna klipps till hela bilden blir IoU missvisande (gelato S2, asketch S3–S4). Mask- och "hållen"-måtten fångar de fallen. H mäter 3D-posen även där benen inte syns i bild.

### 1.2 Betyg per ruta (V = visuellt, A = automatiskt)

Bilder: `mening_ut/mening_overlagg_<klipp>.png`. Överst finns originalrutan med trackerruta (grön), personmask (gul), paketets T1-skelett och möbler (orange/rosa) genom paketets kamera. Nederst finns Argons rendering.

| ruta | H V/A | M V/A | U V/A | K V/A | motivering (visuellt) |
|---|---|---|---|---|---|
| guacamole S1 A | 0/0 | 0/0 | 1/1 | 0/1 | Originalet visar A på barstol med underarmarna på disken. Renderingen visar djup huk med knät 0.21 m över golvet och knävinkel 81°. Bardisken i förgrunden är dold av R1. Huvud och bål ligger rätt i överlägget, men benen projiceras genom disken. |
| guacamole S2 B | 1/0 | 1/1 | 1/1 | 1/2 | Överkroppen är ungefär rätt. 3D-benen står i huk: knävinkel 95°, bäcken 0.66 m. Disken ligger rätt i bild men skivan sitter 0.78 m upp, medan en bardisk brukar vara 1.0–1.1 m. |
| guacamole S3 A | 0/0 | 1/1 | 1/1 | 2/2 | Huk igen. Disken syns men svävar som skiva med A:s ben under. Händerna vilar på skivan (0.07 m). |
| guacamole S4 B | 0/0 | 0/0 | 1/1 | 0/1 | Originalet visar B stående och lutad mot disken. Renderingen visar djup knäböj med knävinkel 76° och knät 0.19 m över golvet. Disken saknas (R1, 30 % skymning). |
| guacamole S4 A | 0/0 | 0/0 | 1/0 | 0/2 | Liten i vänsterkanten som i originalet, men på huk och utan disk. |
| gelato S1 A | 1/2 | 1/1 | 0/0 | 1/1 | Originalet tittar ned i disken under kraftig inåkning och tiltning. Paketets kamera är vågrät och kroppen lutar 36° (19.7° efter pitchkorrektion). IoU 0.26 och mittfel 27 % av bildhöjden. |
| gelato S2 A | 0/2 | 0/0 | 0/0 | 0/0 | Originalet visar bara en arm från höger. 62.5 % av rutorna saknar detektion, och posen är frusen från ruta 60 (`sekvens_5.npz`, `kand`). Renderingen visar en hel rygg. |
| asketch S1 A | 1/2 | 0/0 | 1/1 | 0/1 | A lutar sig fram över glasdisken (personens höjd i bild ×1.65, bakgrundsskala 0.99–1.00). R25 har gjort lutningen till 0.82 m kamerainåkning. Disken är dold av R1. |
| asketch S2 B | 2/2 | 1/– | 2/2 | 2/– | Disken nederst i originalet är inte modellerad, och obs hittade ingen disk. |
| asketch S3 B | 0/2 | 0/– | 0/0 | 0/– | Närbild av kebabspett och en handske. 77.6 % av rutorna saknar detektion. Renderingen visar en hel kropp. |
| asketch S4 B | 1/2 | 0/– | 1/2 | 0/– | Profilbild där B arbetar vid bänken. Bänken saknas. Kameran panorerar 32° (R25c), men R25 lade 0.27 m translation. |
| asketch S5 B | 2/2 | 1/1 | 1/1 | 1/1 | B:s ben syns ovanför disklisten, men de är dolda i originalet. Kameran rör sig kraftigt (skala ×2.5). |
| asketch S6 – | – | 1/0 | – | – | Originalet är en närbild av mat. Renderingen visar ett tomt hörn med diskkant. |
| asketch S7 A | 2/2 | 0/0 | 1/1 | 1/1 | Profilen och den utsträckta armen stämmer. Disken saknas. |
| notan S1 A | 1/0 | 2/1 | 2/2 | 1/1 | Bord, burk och mugg ligger rätt i bild (överlägget). 3D-benen är i huk med knät 0.20 m över golvet, men de döljs av bordet. |
| notan S2 B | 1/0 | 0/0 | 2/2 | 0/1 | bord_2 är dolt av R1, så B:s ben och sits syns i förgrunden. |
| notan S3 A | 1/0 | 2/1 | 2/1 | 1/0 | Som S1. |
| notan S4 C | 2/2 | 1/0 | 2/2 | 1/– | C stämmer. Gästens bord är dolt (R1). |
| notan S4 gäst | 2/2 | 0/0 | 1/1 | 0/– | Sitter, men 35 % av rutorna saknar detektion och bordet saknas. |
| notan S5 B | 1/0 | 2/1 | 2/2 | 1/2 | Bord och mugg stämmer. Burgaren hålls upp i originalet men inte i renderingen. |
| notan S6 A | 1/0 | 2/1 | 1/1 | 1/2 | Som S1. |
| notan S7 B | 2/0 | 1/0 | 0/0 | 2/1 | Hållningen och den lyfta armen stämmer. B ligger ändå 20 % av bildhöjden för lågt (se 1.3). |

Visuellt utfall: av 21 person-tagningar har 13 minst en nolla. De 8 utan nolla är guacamole S2, asketch S2 och S5 samt notan S1, S3, S4 C, S5 och S6. Bara notan-tagningarna ser ut som originalet i bild, och de sittande där står ändå på huk bakom bordet (knät 0.17–0.22 m över golvet).

### 1.3 Tre orsaker som rubriken pekar ut, med belägg

1. **Kamerans pitch och roll kastas bort.** `scen_brygga.py:254` bygger `R_cam = _euler_xyz_till_mat(90.0, 0.0, cam_nod.rotation[2])` och ignorerar `recept.json` `rotation[0]` (90+pitch) och `rotation[1]` (roll). Alla 20 kameror i de fyra paketen är därför vågräta (kvaternion med w=x, y=z). Kroppen lyfts genom samma vågräta kamera, så kroppen själv projiceras rätt. Kamerans lutning hamnar i stället som en framåtlutning i kroppen och som felplacerade möbler i bild. Exempel: gelato S1 (pitch −18°, klämd i `obs_motor.py:161–165`), asketch (alla −15 till −18°) och notan S7 (−10.6°).
2. **Kamerahöjden kläms.** `scen_brygga.py:338` sätter `ny_cz = max(0.92, …)`, och `z_kropp = z_skift - z_kam_delta` flyttar då kroppen relativt kameran. För andra personen i en tagning gäller rad 344 `z_kropp = z_skift` helt utan kamerakompensation. `X_RA_2D` räknas efter förflyttningen (rad 355–374), så G7 kan inte se felet. I notan S7 ligger kameran på 0.92 m mot receptets 1.24 m, och mittfelet är 0.20 bildhöjder (IoU 0.16).
3. **Ben genereras utan bildstöd.** `utsnitt_1.json` säger `endast_overkropp: true` för samtliga guacamole-tagningar. Ändå ligger sittande och stående personer med knät 0.12–0.29 m över golvet. Det syns inte i originalvinkeln, men blir synligt så fort bordet döljs (R1) eller en manipulation flyttar kroppen.

Bisak: `grindar.mat` skriver över `rad["G2_golv"…]` för varje person i tagningen (`byggsten/brygga/grindar.py:84–132`). I tvåpersonstagningar betygsätts därför bara den sist listade personen.

## 2. A2 – R25 mot en person som faktiskt rör sig

### 2.1 Vad R25 gör (`scen_brygga.py:380–390`)

Om bäckenets XY-spann är större än 0.18 m för den första och enda personen dras den lågpassfiltrerade driften bort från kroppen och läggs med omvänt tecken på kamerans position. Kamerans orientering ändras aldrig. Eftersom `X'-C' = X-C` blir projektionen exakt densamma, och `X_RA_2D` räknas före R25, så "0 px / IoU 1.000" gäller per definition. Möblerna flyttas däremot inte med. Det som ändras i bild är alltså rummet bakom personen.

### 2.2 Syntetiskt, facit känt (`mening_r25.py`, del 1)

Kroppen är en riktig T1-pose (notan C), ledbruset 1 cm och punktbruset i bakgrunden 0.5 px. R25 är exakt samma kod som i paketet och använder `scen_brygga._mjuk_bana`.

| scenario | sanning kropp / kamera | R25 kropp / kamera | R25: rummets 2D-fel | R25c kropp / kamera | R25c: rummets 2D-fel |
|---|---|---|---|---|---|
| a. går 1.8 m i sidled, stilla kamera | 1.80 / 0.00 m | **0.12 / 1.67 m** | **151 px** | 1.80 / 0.004 m | 0.2 px |
| b. inåkning 0.8 m mot stilla person | 0.00 / 0.80 m | 0.06 / 0.76 m | 30 px | 0.03 / 0.81 m | 1.8 px |
| c. panorering 15° som följer gående | 1.80 / 0 m, 15° | **0.007 / 0 m, 0°** (R25 slår inte till) | **395 px** | 1.80 / 0.017 m, 14.9° | 0.3 px |
| d. går 1.5 m mot kameran | 1.50 / 0.00 m | **0.09 / 1.39 m** | 43 px | 1.48 / 0.003 m | 0.0 px |

Kroppens 2D-fel är 2–3 px (bruset) i alla varianter, så R25:s "0 px" bevisar ingenting om separationen. Bild: `mening_ut/mening_r25_syntet_a.png`. Sanningen och R25 visas sida vid sida i ruta 0, 30 och 59. Personen står still i bild, och i R25-varianten glider bordet ur bild.

### 2.3 Riktiga klipp (`mening_r25.py`, del 2)

Bakgrundens rörelse mäts ur videorutorna. Lucas–Kanade spårar punkter utanför personmask och textmask, punkterna lyfts till 3D med MoGe-djup (var 6:e ruta) och kameran skattas med PnP + RANSAC per ruta (R25c). Den enklare R25b använder bara en 2D-likhet och klarar inte inåkning lika bra (scenario b: 0.93 m mot sanna 0.80 m).

| tagning | R25 slog till | R25 drift | R25c kamera: förflyttning / panorering / tiltning | personens höjd i bild | bedömning |
|---|---|---|---|---|---|
| gelato S1 | ja | 1.09 m | 1.06 m / 13° / **30°** | ×2.35 | Kameran rör sig, men 30° tiltning och 13° panorering kan inte uttryckas i R25 |
| asketch S1 | ja | 0.82 m | **0.08 m / 3° / 1°** | ×1.65 | **Fel.** A lutar sig fram och bakgrunden står still |
| asketch S7 | ja | 0.47 m | **0.05 m / 3° / 3°** | ×1.61 | **Fel.** Samma mönster |
| notan S7 | ja | 0.26 m | **0.001 m / 0.1° / 0°** | ×1.18 | **Fel.** Stativ. B sitter, men beslutstexten säger "stod vid sin plats" |
| asketch S4 | ja | 0.27 m | 0.47 m / **32°** / 12° | ×1.00 | Panorering modellerad som translation |
| asketch S5 | ja | 0.56 m | 1.41 m / 9° / 22° | ×1.11 | Osäker: skala ×2.5 kan vara digital zoom, och R25c antar fast fokal |
| gelato S2, asketch S3 | nej | – | 0.25–2.4 m / 53–84° | – | R25 ser inget eftersom posen är frusen eller personen saknas. R25c:s värden är osäkra (PnP i 77–79 % av rutorna) |
| guacamole S1–S4, notan S1–S6 | nej | – | <0.01 m / <0.3° | – | Överens: stilla kamera |

Bilder: `mening_ut/mening_r25_verklig_{gelato_s1,asketch_s1,asketch_s7,notan_s7}.png` visar bakgrundsflödet (gröna pilar), trackerrutan och banorna ovanifrån. `mening_ut/mening_rutor_{gelato,asketch}_s1.png` visar råa rutor: i gelato S1 åker kameran in och tiltar ned, i asketch S1 står fönsterkarmen still medan A lutar sig in.

### 2.4 Förslag: ersätt R25 med R25c

1. Skatta kamerans 6-DOF-bana per tagning ur bakgrunden (punkter utanför `masker.npy`, 3D ur `rum/depth/*.npz`, PnP med RANSAC, ny förankring var 6:e ruta). Allt underlag finns redan i ingest-cachen.
2. Lägg kroppen i världen som `R_t · c_cam(t) + C_t`. Kroppen behåller då sin egen rörelse, och ingen tröskel som 0.18 m behövs.
3. Gör R25c:s antaganden till grindar: fast fokal (zoom ger skala utan parallax), statisk bakgrund och tillräckligt med bakgrundspunkter (PnP-andel <0.9 ska flaggas).
4. Mät 2D-trohet för **rummet**, inte bara för kroppen. Bordets hörn ska jämföras mot MoGe-normalernas diskkant (`counter_edges.json` finns) per ruta.

Begränsningar: R25c är prototypat i `mening_r25.py` men inte inlyft i `scenpaket/2`. På riktiga klipp saknas facit, så valideringen vilar på syntet plus konsistens (stillastående klipp ger ≈0). MoGe-skalan och paketets κ-skalning är inte avstämda mot varandra.

## 3. Lager 4

### 3.1 Är `AttitydProfil` stabil? (`mening_attityd.py` → `stabilitet`, `pitch`)

| person, tagning | lutning° bas | +5/+10/+20 mm brus (medel ± sd) | 1 s-fönster min–max | slapphet bas → +5 mm | etikett bas → +5 mm brus |
|---|---|---|---|---|---|
| guac A S1 | 24.3 | 24.5±0.1 / 24.5±0.2 / 24.9±0.4 | 23.9–24.4 | 0.54 → 0.47 | slapp → **energisk** |
| guac A S3 | 28.0 | 28.0±0.2 / 28.1±0.2 / 28.3±0.5 | 27.8–28.0 | 0.52 → 0.47 | energisk → energisk |
| guac A S4 | 26.9 | 27.0±0.1 / 27.1±0.2 / 27.1±0.4 | 26.3–28.2 | 0.58 → 0.51 | slapp → **energisk** |
| guac B S4 | 13.0 | 13.0±0.2 / 13.2±0.5 / 13.6±0.7 | **5.8–21.8** | 0.21 → 0.21 | energisk |
| gelato A S1 | 36.2 | 36.4±0.4 / 37.0±0.5 / 38.7±0.8 | **28.6–79.5** | 0.54 → 0.54 | slapp (+20 mm: båda) |
| gelato A S2 | 12.9 | 12.8±0.1 / … | 12.9–12.9 (frusen pose) | 0.49 → 0.37 | fokuserad → **energisk** |

- `lutning_deg` tål ledbrus. Den rör sig ändå med kameran: i gelato S1 spänner 1-sekundsfönstren 28.6–79.5° eftersom kameran tiltar 30° under tagningen och paketets kamera inte kan tilta.
- Med receptets pitch och roll återinsatta (`v_korr = R_sann R_niv^T v`) blir guacamole A 21.2/19.7/28.8° (medel 23.2° mot 26.4°), gelato A S1 19.7° (mot 36.2°), asketch B S5 1.9° (mot 17.9°) och notan A ~24° (mot ~32°). Receptets pitch är dessutom klämd vid ±18° och har σ 3°. Lutningen går alltså inte att skilja från kameran med nuvarande kedja.
- `slapphet` väger in handledsfart (rad 83–89), och farten räknas som `diff/dt`. 5 mm ledbrus vid 30 fps ger +0.3 m/s, vilket räcker för att ändra etiketten (gräns 0.52) i 3 av 6 fall. Tröskeln ligger inom bruset: guac A S3 får 0.52 → "energisk", så samma person bär två etiketter.
- `kontakt_armar` är sann för alla sittande per definition (rad 108), oavsett vad armarna gör.
- `attityd_leder` innehåller `"c_ spine3"` med mellanslag (rad 125). Leden finns inte i `leder`, så en konsument som slår upp namnet får ingen träff.

**Förslag:** mät lutningen i kameraramen mot `varld.npz["upp"]` eller MoGe-golvnormalen, inte mot paketets Z. Byt handledsfart mot en brusrobust storhet, till exempel bandbegränsad gestamplitud efter ett Savitzky–Golay-filter. Rapportera osäkerhet (bootstrap) per fält, och låt etiketten vara "osäker" när intervallet korsar en tröskel.

### 3.2 Bevarar `ga_med_attityd` attityden? (`ga_med_attityd`)

Profilen mätt på den manipulerade rörelsen med samma funktion:

| tagning | lutning° före → efter | slapphet | handfart m/s | etikett |
|---|---|---|---|---|
| S1 | 24.3 → 24.3 | 0.54 → 0.51 | 0.21 → 0.65 | slapp → **energisk** |
| S3 | 28.0 → 28.0 | 0.52 → 0.60 | 0.53 → 0.62 | energisk → **slapp** |
| S4 | 26.9 → 26.9 | 0.58 → 0.63 | 0.22 → 0.42 | slapp → slapp |

Lutningen är oförändrad därför att ryggraden kopieras (rad 280), och den bär med sig kamerafelet ovan. Slappheten och etiketten följer inte med per tagning. Aggregatet 0.54 → 0.58 döljer det.

Gångens fysik (`gang`):

| mått | S1 | S3 | S4 | rimligt |
|---|---|---|---|---|
| fotens fart i stödfas (v/h) | 0.28 / 0.30 m/s | 0.33 / 0.45 | 0.42 / 0.49 | ≈0 |
| bäckenets fart (median) | 0.48 m/s | 0.47 | 0.25 | – |
| fotsving sista 0.5 s / bäckenets förflyttning | 0.35 / 0.10 m | 0.40 / 0.14 | 0.27 / 0.05 | sving ≈ förflyttning |
| lårlängd min–max (orig. 0.37) | 0.35–0.40 m | 0.35–0.40 | 0.35–0.41 | konstant (T1 har fasta ben) |
| fotlyft max | 0.035 m | 0.035 | 0.035 | ~0.1 m |
| gångriktning i världen | −162.6° | −156.4° | −175.2° | samma gång i alla tagningar |

Fötterna sätts som `höft + fram·sin(fas)` (rad 330–333) och följer därför bäckenet. Det blir skridskoåkning, och i slutet går personen på stället. Varje tagning syntetiserar en egen gång med egen riktning och egen startpunkt. Ingenting binder ihop dem över klippen. Bilder: `mening_ut/mening_render_ga_med_attityd.png` (originalkameran S1/S3: början, mitt, slut) och `mening_ut/mening_render_ga_sida.png` (fast ortografisk sidokamera vinkelrätt mot gången, väggar dolda; personen förflyttas 1.16 m och riggen följer, kontrollerat i Blender). I sidovyn syns en hopsjunken gång där fötterna lyfts högst 3.5 cm. I S3 når A fram till disken, men skivan sitter i höfthöjd (topp 0.78 m mot bäcken 0.81 m). Skivhöjden kalibrerades mot den sittandes armbågar (`scen_brygga.py:517`), så manipulationen gör möbelfelet synligt.

**Förslag:** fotlåsning (stödfot fast i världen, svingfot interpolerad mellan låsta steg, stegsträcka = bäckenets förflyttning per halvcykel). Gångbanan ska planeras en gång i rummet och samplas per tagning efter tidslinjen. Mät sedan profilen på resultatet som grind (|Δlutning| < 3°, samma etikett, foten stilla < 0.05 m/s i stödfas).

### 3.3 Är `byt_hand` fysiskt rimlig? (`byt_hand`, gelato S1 ruta 145 = störst räckvidd)

| mått | S1 | S2 |
|---|---|---|
| ryggradens största ändring (bålvridning) | **0.000 m** | 0.000 m |
| spegelplan ur höfterna mot axellinjen, median / p90 | **9.9° / 14.5°** | 1.1° / 1.1° |
| nyckelbenens förflyttning, median / max | 5.6 / 13.7 cm | 1.9 / 2.0 cm |
| axelledens förflyttning (median) | **8.8 cm** | 2.0 cm |
| ny hand till originalhandens mål | **0.62 m** | 0.11 m |
| originalhandens sidoavstånd från bålen | 0.31 m | 0.06 m |

`_byt_hand_med_balvridning` speglar armkedjorna kring ett plan genom `c_spine2` med normalen tagen ur höfterna (rad 359–372). Gelato-höfterna är dolda bakom disken (`endast_overkropp`), så planet lutar och axlarna lossnar från bålen. Speglingen flyttar också målet: smakprovet räcks fram 0.62 m från där kunden tog emot det, alltså 2 × sidoavståndet. "Bålvridning och axelkompensation" (rad 196, 345, 479) finns inte i koden. Bild: `mening_ut/mening_render_byt_hand.png` visar original och byt_hand i ruta 145 genom originalkameran, framifrån och ovanifrån (ortografiskt). Framifrån och ovanifrån syns att originalhanden går ned mot disken och kunden, medan den speglade handen sträcks ut åt sidan längs disken. Genom originalkameran syns i stället den passiva armen, som nu är lyft åt sidan i axelhöjd.

**Förslag:** behåll målet (handens position vid överlämningen) och lös den andra armen med 2-leds-IK mot samma mål från den egna axeln, plus en begränsad bålrotation (≤20°) när målet ligger utanför armens räckvidd. Ta symmetriplanet ur axlarna, eller ur bålens 3D-rotation i `pose[:, 3:7]`, och inte ur dolda höfter.

### 3.4 Tidsbudget (`tid`, 15 körningar, denna dator medan andra agenter körde)

| steg | guacamole (148 KB) | gelato (108 KB) |
|---|---|---|
| `json.loads` | 16 ms | 9 ms |
| `extrahera_attitydprofil` | 49 ms | 7 ms |
| `bygg_jev_yta` | 0.01 ms (statisk lista) | 0.01 ms |
| `copy.deepcopy(paket)` | 104 ms | 33 ms |
| `grindar.mat` | 45 ms | 7 ms |
| **`manipulera_scen` totalt** | **684 ms** (max 1603) | **531 ms** (max 951) |
| Blender-rendering, headless (3–11 rutor, inkl. scenbygge) | 10–94 s, varierar med lasten | 46–57 s |

"< 50 ms i kod / < 250 ms med Jev" saknar mätning i `forvarld_karna/` (ingen tidtagning i `mening_motor.py`). Jev-ytan är en fast lista med 4 drag per person, och routningen från fri text till drag (`byggsten/hand/`) är inte inkopplad. Siffrorna ovan är medianer på en belastad maskin och kan bli lägre på en ledig. De största posterna är ändå deepcopy och Python-slingorna i operatorn och i `_dra_in_dolda_ben_bakom_massiv_disk`: ≈486 ms för guacamole, härlett som totalen minus de uppmätta delarna. De posterna beror på koden, inte på maskinlasten.

## 4. Vad som bör prövas härnäst (motprov)

| nytt påstående (Claude) | motprov som kan fälla det |
|---|---|
| C1. R25c skattar kamerans bana inom 2 cm / 2.3 px när bakgrunden är statisk och fokalen fast | Kör `mening_r25.py` med zoom, truck i sidled och rörlig bakgrund (andra personer). Felet ska då flaggas, inte döljas |
| C2. Pitch-bortfallet (`scen_brygga.py:254`) förklarar största delen av gelato S1:s utsnittsfel | Patcha in `rotation[0..1]` i en kopia och mät U igen. IoU ska stiga från 0.26. Om den inte gör det faller C2 |
| C3. Lutning mätt i kameraramen mot gravitation varierar < 3° mellan tagningar för samma person | guacamole A: S1/S3/S4. Idag ger receptkorrektionen 21/20/29°, så C3 är **oprövad** och kan falla på S4:s profilvy |
| C4. Fotlåsning ger stödfotsfart < 0.05 m/s utan att ändra den 2D-bild som CM ser | implementera och mät med `ga_med_attityd_matning` |
