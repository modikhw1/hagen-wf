---
id: 0002
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
Bakgrunden räcker för att mäta **vilka tagningar som delar kameraplats**, men inte för att mäta avstånd eller hur uppställningar förhåller sig till varandra. Inom en uppställning ger SIFT 100–540 inliers. Mellan uppställningar ger den 14–125, och det går inte att skilja från slump eller kakelalias (se nollkontrollen).

**Metod.** OpenCV 5.0 SIFT (3000 särdrag/ruta, CLAHE) och förhållandetest 0,8. Fyra bildrutor per tagning (12–88 % av tagningen), alla 4×4 rutpar per tagningspar, bästa paret redovisas. Personerna maskas med ingestens `masker.npy` (dilaterad 25 px). Överlägget maskas med en rektangel i b-tilltal, och matchningar med mindre än 2 px förflyttning kastas. Modeller: homografi (MAGSAC, 3 px), fundamentalmatris (MAGSAC, 1,5 px), essentiell matris plus `recoverPose` med **antagen** fokal 1024 px (ingen mätt lins; se nedan). Trösklarna är egen diagnos, inte krav. Skalan är okänd i monokulär matchning.

**Nollkontroll.** Samma körning mellan b-tilltal-tagningarna och guacamole-klippet, där inget kan överlappa: F-inliers max per par ligger mellan **10 och 38** (median 20, p90 27). Allt under cirka 40 är därför inte skiljt från slump.

### Matris, b-tilltal (11 tagningar, 55 par): F-inliers (homografins inliers)
Hela matrisen finns i [b_par.md](../../scen/3d/ingest/bakgrund_prov/b_par.md). De par som sticker ut:
| par | match | F (H) | förklarande modell | rotation | förflyttningsriktning (kamerans xyz, tecken okänt) |
|---|---|---|---|---|---|
| S6–S7 | 610 | **543 (511)** | homografi | 2,3° | (−0,30; 0,20; −0,93), mest längs blickaxeln |
| S8–S10 | 412 | **348 (300)** | homografi | 0,6° | (0,70; −0,07; −0,72) |
| S3–S4 | 222 | 125 (93) | homografi | 5,7° | (−0,19; −0,54; −0,82) |
| S1–S2 | 160 | 80 (63) | homografi | 3,6° | (0,10; 0,34; 0,93) |
| S8–S9 | 206 | 102 (48) | essentiell | 16,7° (7° via homografi) | (0,34; 0,00; −0,94) |
| S9–S10 | 99 | 73 (61) | homografi | 1,1° | – |
| övriga par mellan uppställningar | 36–213 | 14–104 | – | rotation **inte meningsfull** (upp till 176°) | – |

Med den antagna fokalen 1024 px är rotationerna för de starka paren stabila när fokalen varieras till 700 och 1400 px: S6–S7 2,2–2,3°, S8–S10 0,5–0,6°, S3–S4 4,6–7,0°. S8–S9 varierar 6,4–16,7° och S9–S10 1,1–9,3° (svagare par). Alla intervall finns som `R_grader_per_fokal` i `b_par.json`. Förflyttningen är mest längs blickaxeln. Det stämmer med 0001, där kameradjupet är den sämst bestämda parametern.

### Matris, guacamole (4 tagningar)
Bara **S1–S3 sticker ut: 385 match, F 332 (H 218), rotation 13,3 enligt essentiell matris** (varierar 10,7–23,8° med fokalen, 5° via homografi). Övriga par ligger på 26–38, alltså inom nollkontrollen.

### Facit mot mätningen
| Påstående (ägarens läsning/deklarationen) | Utfall |
|---|---|
| b: S1 och S2 delar plats (kamera_A) | **bekräftas** (80/63) |
| b: S3 och S4 delar plats (kamera_B) | **bekräftas** (125/93) |
| b: S6 och S7 delar plats (kamera_D) | **bekräftas** starkast (543/511) |
| b: S8–S11 delar plats (kamera_E) | **delvis**: S8–S10 och S9–S10 ja. S8–S9 ja men roterad. **S11 hänger inte ihop** med S8, S9 eller S10 (38, 17, 46), vilket varken bekräftar eller motsäger |
| b: de två männen på ungefär samma ställe (S1/S2 mot S3/S4) | **inget sagt**: F 20–31, inom nollkontrollen. S1 och S2 visar bara rosa kakel, S3 och S4 ett fönster |
| b: samma lokal, Lærke i en vinkel mot vågen (S5 mot S8–S11) | **inget sagt**: S5 har F 14–35 mot alla andra |
| g: S1 och S3 (båda A vid `stol_A`) delar plats | **bekräftas** (332/218) |
| g: S2 och S4 samma station | **inget sagt** (F 26), vilket stämmer med deklarationens "inte belagd" |

Varning: kaklet i b-tilltal är repetitivt. S4–S11 ger F 104 (H 79) trots olika uppställningar och roller, vilket är kakelalias och inte en bevisad koppling. Jag tolkar inga par under cirka 125 som överlapp.

## Bedömning (högst fem rader)
1. **Värt att bygga in för frågan "samma kameraplats?"** per par, före deklarationen. Lösaren skulle få: `delar_plats: [[S1,S2],[S3,S4],[S6,S7],[S8,S9,S10]]` med F/H-tal, och att S5 och S11 saknar mätbar koppling.
2. Spåret **ger inte avstånd** (okänd skala, och homografin från en plan vägg döljer förflyttning). Det ersätter inte hörnavstånden. För skala krävs kakelstorlek eller diskhöjd (ägarens beslut).
3. Mellan uppställningar behövs en starkare matchare (LoFTR eller COLMAP, ej installerade). Den väntas ge fler tillförlitliga par, men det är ett eget beslut om installation.

## Ändrade eller nya filer
`scen/3d/ingest/bakgrund_prov/`:
- `matcha.py`: hela mätningen. Körs med `python -B -I matcha.py <ingestmapp> <prefix>`.
- `b_par.json`, `b_par.md`, `b_nollkontroll.json`, `g_par.json`, `g_par.md`: matriser och nollkontroll.
- `b_match_S6_S7.jpg`, `b_match_S8_S10.jpg`, `b_match_S3_S4.jpg`, `g_match_S1_S3.jpg` (+ `g_match_S1_S2.jpg`, `g_match_S2_S3.jpg`, de svagare paren) och `b_maskprov.jpg`, `g_maskprov.jpg`: ritade matchningar och maskkontroll. Ritat är de 120 första inliers.

## Kontroll mot "Klart när"
- [x] Matris över tagningspar per klipp med matchningar, inlier-andel (`inl_andel_F` i json), modell: b och g.
- [x] Relativ rotation och förflyttningsriktning för par med överlapp, med skalan uttryckligen okänd.
- [x] Jämförelse mot facit: tabellen ovan.
- [x] Bedömning i högst fem rader.
- [x] Tre ritade par (S6–S7, S8–S10, g S1–S3) plus S3–S4.

## Avvikelser
- Fokalen 1024 px är planens reservvärde (se 0001), inte mätt. Rotationerna är därför indikativa.
- Överläggsmasken i b-tilltal är en fast rektangel (x 9–92 %, y 47–75 %). Guacamole kördes utan, med bara nollförflyttningsfiltret.
- `tagningar.json` för b-tilltal innehåller en byte (0xf6) som inte är UTF-8. Jag läste den med `errors='replace'` och ändrade inget.
