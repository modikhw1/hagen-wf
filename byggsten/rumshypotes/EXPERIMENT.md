# Experiment: rumshjärnan (video till rumsrecept till Jutsu)

Överlämningsnoter, skrivna 17 nov 2026. Det här är ett experiment, inte en del av kedjan. Den som ärver det ska kunna fortsätta, eller lägga ned det med goda skäl, utan att läsa chatten där det byggdes.

Mappen är `byggsten/rumshypotes/`. Byggstenarnas regler gäller (`byggsten/README.md`): mappen talar med kedjan via filer, läser kedjans utdata men skriver bara här.

---

## 1. Frågan

Kan man ur klippt, stående inomhusvideo (LeTrends 2000+ klipp) få fram rummets planlösning, alltså var möbler, personer, väggar och kameror står i meter? Och kan man göra det med **allmänna regler och en resonerande hjärna** som sätter hypoteser och river dem när ett senare klipp motsäger dem, i stället för med fotogrammetri eller en agent som återskapar varje scen för hand?

Resultatet ska vara ett **recept** (JSON med osäkerhet) som 3D Jutsu bygger på några sekunder.

Ursprunget är ägarens uppdrag, ordagrant i [UPPDRAG.md](UPPDRAG.md). Under arbetet gav ägaren två styrningar som väger tyngre än uppdragstexten:

1. **Allmänna regler söks.** Ägaren tänkte sig en tvådimensionell översikt där sannolikheten skärps ju mer av klippet som går att läsa. En hjärna som drar slutsatser och sätter hypoteser som prövas och bryts. "Om jag ville ha en codex/claude som återskapar varje scen i 20 min per scen, hade jag bett om det."
2. **Avstånden i rummet räcker inte.** Ägaren var inte nöjd med distanserna och frågade hur djupläsningen påverkar tolkningen (steg 5 nedan).

Testklippet är **notan** (`scen/3d/ingest/ut/notan-tagningar`), som har stresstestets form:
- A och B i motbilder (s1, s3, s6 respektive s2, s5)
- servitören C ensam med en dörr bakom sig (s4)
- avslöjandet i s7, en vidvinkel från A:s bord där B syns sitta vid ett eget bord längre bort

---

## 2. Läget i korthet

| del | läge |
|---|---|
| Jutsus konventioner | **Klar och verifierad.** [../jutsu/KONVENTIONER.md](../jutsu/KONVENTIONER.md): egen projektion mot Blender 0,0007 px, mot renderade pixlar under 1 px. |
| Schema (Pydantic) | **Klart.** Observationer in, recept (SceneTelemetry) ut. |
| Hjärnan | **Fungerar.** På syntetisk data med facit går alla åtta kriterier i stresstestet igenom. |
| Recept till Jutsu | **Klart och deterministiskt.** Bygger och renderar på 2,5–15 s, 0 credits. |
| Fas 1–2 ur riktig video | **Fungerar** för klipp som gått genom kedjans ingest, plus en VLM- och en Modal-körning per klipp. |
| Notan, slutsats | **Rätt:** A och B vid olika bord, P 1,00 i s7, inget påhittat extra rum. |
| Notan, geometri | **Inte bra.** Närfältet stämmer (bordsskivor cirka 0,72 m), men A–B blir 6,8 m mot väntade 3–4 m, och rummet 7,7 × 8 m bestäms av typstorleken. |
| Notan, förlopp | **Instabilt.** Den tidiga tron på ett gemensamt bord kommer och går med små regeländringar. |

**Bedömning:** Arkitekturen och resonemanget håller. Den svaga punkten är indata: metriskt djup i närbilder och länkar mellan klipp som saknar gemensamma unika saker. Där krävs mer arbete innan det går att lita på avstånd i riktiga klipp.

---

## 3. Arkitekturen

```
kedjans ingest (SAM 3D Body, MoGe, rum.json)  ┐
modal_djup.py (MoGe utan personmask, Modal)    ├─► obs_ingest.py ─► Observationer (obs.json)
las_vlm.py (Gemini: ljus, rumsnycklar, föremål)┘                        │
syntet.py (facit och simulerade observationer) ─────────────────────────┤
                                                                        ▼
                         hjarna.py: klipp för klipp, hypoteser × regler, beam 8, delning, omprövning
                                                                        │
                    karta.py (2D-karta per klipp) · logg (LOGG.md) · recept.py (SceneTelemetry)
                                                                        │
                                       jutsu_adapter.py ─► bpy-skript ─► 3D Jutsu (eller lokal Blender)
```

### Begreppen
- **Observation per klipp** (`telemetri.KlippObs`):
  - kamera: hfov, höjd, pitch, roll
  - detektioner: klass, nyckel, unik, bearing och djup med sigma, vändning, pose, blick, relationerna "vid" och "på", amodal
  - väggar: fotpunktens bearing och avstånd
  - Manhattan-vinkel, ljusets bearing, takhöjd, rumsnycklar
  - fri yta (strålar) och ett grovt djupnät (32 × 18) med skala
- **Hypotes** (`hjarna.Hyp`): en uppsättning val om vad observationerna är.
  - vilket bord är detta (befintligt eller nytt)
  - samma rum eller annat
  - har personen flyttat
- **Lösning:** givet valen löses lägena (kameror, saker, rumsgränser, ljusets azimut) som minsta kvadrat, med reglerna som residualer.
  - Jacobian per term ger 0,2–0,5 s per lösning.
  - Osäkerheten kommer ur samma lösning (Laplace) och blir ellipser och zoner.
- **Poäng** i nats: passning + struktur (Occam) + rum (rumsnycklar) + synlighet (det som borde synas men saknas).
- **Sökning:**
  - Varje klipp expanderar de åtta bästa hypoteserna. Fas 1 löser alla barn snabbt (8 iterationer), fas 2 löser de 24 bästa fullt.
  - Generiska kopplingar grindas kring den förväntade platsen när kameran går att förankra i unika saker.
  - Strålen behåller den bästa hypotesen för varje kärntro.
  - Efter varje klipp prövas att dela gamla kopplingar (`_dela`, R20).
- **Kärntro:** vilka roller som sitter vid samma bord, plus flyttar och rum (`karna`). Sannolikheten är softmax över varje kärntros bästa hypotes. Ett byte loggas som omprövning vid P ≥ 0,75 och annars som vacklan. Loggen visar vad den gamla tron hade kostat, de största motsägelserna och vad som hade krävts för att rädda den.
- **Ramen:** hjärnans egen, där första kameran står i origo. Receptet flyttar rummets mitt till origo. Blender-ram: Z upp, meter, euler XYZ i grader.

### Reglerna (`regler.py`, 21 stycken; talen är egna startvärden, inga krav)
- **R1 Strålen:** monokulärt djup är skarpt i sidled och osäkert i djup.
- **R2 Manhattan:** kamerans vridning modulo 90°, bara när koncentrationen R ≥ 0,6.
- **R3 Ljuset:** fast riktning i rummet. Bara sidan används (vänster, höger, bakifrån), med sigma 45°.
- **R4 Identitet:** unika personer och generiska möbler som kandidater.
- **R5 Occam:**
  - rollernas bord 1,5 nats
  - bakgrundsbord 0,3 (R16)
  - föremål efter typ: mugg 0,3, märkt burk 2,5 (R17)
- **R6 Blicken:** ger riktning, aldrig avstånd. Blickpar härleds ur motbilder.
- **R7 Synlighet:**
  - prövas i bildplanet mot det kalibrerade djupnätet
  - personer räknas om de inte är tydligt skymda
  - bara saker med sigma ≤ 0,5 m räknas
- **R8 Fri yta.**
- **R9 Väggar.**
- **R10 Samma rum:** rumsnycklar väger mot ett nytt rum (6 nats).
- **R11 Kontakt:** "vid" 0,75 ± 0,15 m, "på" 0,30 m.
- **R12 Stillhet:** en osedd flytt kostar 6 nats.
- **R13 Kollision:** bord minst 1,0 m isär, personer minst 0,5 m. Kameran står inte i en person.
- **R14 Golvet.**
- **R15 Bordet framför en sittande person** förankras 0,55 m framför personen.
- **R16 Många bord** (se R5).
- **R17 Föremålens identitet** (se R5).
- **R18 Kameran över en synlig bordsskiva:** minst 0,86 m.
- **R19 Kroppen är linjalen:** MoGe-djupets skala per tagning kalibreras mot SAM-kroppen.
- **R20 Gamla kopplingar prövas om:** delning.
- **R21 Golvet som linjal:** affin djuprättning bara där golvet syns över minst 1 m djup.
- **Mjuka ledtrådar** (Manhattan, ljus, blick, väggar) har robust kostnad (mjuk L1).

---

## 4. Filer

| fil | rader | vad |
|---|---|---|
| `UPPDRAG.md` | | ägarens uppdrag, ordagrant |
| `README.md` | | arbetsloggen steg för steg (steg 2–5), med siffror |
| `EXPERIMENT.md` | | den här filen |
| `telemetri.py` | 195 | schemat: `Observationer`, `KlippObs`, `Djupgrid`, `Recept` (= `SceneTelemetry`), `Nod`, `Zon` |
| `regler.py` | 78 | reglernas tal (`R`), `FOREMAL_PRIS`, `REGLER_TEXT` |
| `hjarna.py` | 869 | hypoteser, residualer, lösning, poäng, beam, grindning, delning, kärntro, logg |
| `recept.py` | 146 | hjärnans tro till receptet: typmått, vändning, zoner, väggar, takhöjd med prior |
| `karta.py` | 169 | 2D-karta per klipp: fri yta, ellipser, zoner, alternativ hypotes, facit |
| `jutsu_adapter.py` | 255 | recept till deterministiskt bpy-skript: färg efter källa, kameror, markörer, tidslinje, renderingar |
| `kor.py` | 167 | hela flödet för `syntet` eller en `obs.json` |
| `syntet.py` | 181 | diner med facit (6 × 10 m, borden 5 m isär), brus, `--delat` som kontroll |
| `test_stresstest.py` | 128 | uppdragets kriterier C1–C4, B1–B3 och determinism |
| `obs_ingest.py` | 473 | Fas 1–2 ur kedjans ingest, med kalibrering mot kroppen |
| `las_vlm.py` | 97 | Gemini 3.5 Flash via ägarens proxy, ett anrop per tagning, cache |
| `modal_djup.py` | 113 | MoGe-2 utan personmask och med egen FOV, en ruta per tagning |

Utdata (`ut/`):
- `syntet/`, `fro_3/`, `fro_11/` och `kontroll_delat/`: syntetiska körningar
- `notan/obs.json`, `recept.json`, `LOGG.md`, `karta_*.png` och `jutsu_bygg.py`
- `notan/vlm/S*.json`: VLM-cache
- `notan/djup/S*.npz` och `modell.json`: MoGe utan mask
- `notan/jutsu/original_mot_jutsu.png`: jämförelsen, revision 3

Relaterat utanför mappen:
- [../jutsu/KONVENTIONER.md](../jutsu/KONVENTIONER.md), [../jutsu/hello_konventioner.py](../jutsu/hello_konventioner.py) och [../jutsu/LOGG.md](../jutsu/LOGG.md) (test 04)

---

## 5. Köra

```bash
# syntetiskt, med facit och kriterier
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py syntet
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py syntet --delat          # kontroll: delat bord
scen/.venv/Scripts/python.exe byggsten/rumshypotes/test_stresstest.py

# riktigt klipp (kräver kedjans ingest i scen/3d/ingest/ut/<klipp>)
scen/.venv/Scripts/python.exe byggsten/rumshypotes/las_vlm.py scen/3d/ingest/ut/notan-tagningar --ut byggsten/rumshypotes/ut/notan/vlm
scen/.venv/Scripts/modal.exe run byggsten/rumshypotes/modal_djup.py --ingest scen/3d/ingest/ut/notan-tagningar --ut byggsten/rumshypotes/ut/notan/djup --fokal 983.7
scen/.venv/Scripts/python.exe byggsten/rumshypotes/obs_ingest.py scen/3d/ingest/ut/notan-tagningar --vlm byggsten/rumshypotes/ut/notan/vlm --djup byggsten/rumshypotes/ut/notan/djup --ut byggsten/rumshypotes/ut/notan/obs.json
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py byggsten/rumshypotes/ut/notan/obs.json --ut byggsten/rumshypotes/ut/notan
```

Bygget i Jutsu sker via MCP:
- Klistra in `ut/<klipp>/jutsu_bygg.py` i `scene_builder_3d_run_python`, med `revision` och `expectedSceneSequence` ur senaste query.
- Bilderna hämtas med `scene_builder_3d_get_artifact`.
- Skriptet bygger om allt med `hagen_rh`, så det kan köras igen på samma projekt.

Miljön:
- `scen/.venv`, Python 3.12, med pydantic 2.14 installerat (`uv pip install`). numpy, scipy, cv2 och matplotlib fanns redan.
- Modal 1.6.3 är inloggat.
- PYTHONIOENCODING=utf-8 behövs i Windows-konsolen.

---

## 6. Utfall

### Syntetiskt (facit känt)
- Tron är "ett bord" i s2–s6 (P 0,58–0,81) och blir "två bord" i s7 (P 0,90–0,99). Räddningen "annat rum" prövas och förkastas.
- Avståndet mellan borden blev 4,87 m mot facit 5,0 m. Rummet blev 5,9 × 9,7 m mot 6 × 10 m. A, B och borden hamnade 0,2–0,45 m fel. C hamnade i en zon längs väggen.
- Andra brusfrön (3 och 11) gav samma förlopp. Kontrollen med verkligt delat bord behöll "ett bord" (P 0,96–0,99).
- **Förbehåll:** observationerna är simulerade i samma format som hjärnan väntar sig, med rena identiteter och gaussiskt brus. Det visar att resonemanget fungerar, inte att Fas 1–2 gör det.

### Notan (riktig video)
- **Kostnad:**
  - Gemini 0,13 USD (proxyn överskattar)
  - Modal cirka 5 s GPU, några cent
  - Jutsu 0 credits
- **Tid:** hjärnan 80–270 s beroende på regler; Jutsu 2,5–15 s.
- **Mätt per tagning:**

| tagning | s1 | s2 | s3 | s4 | s5 | s6 | s7 |
|---|---|---|---|---|---|---|---|
| skala kropp/MoGe | 0,73 | 0,54 | 0,71 | 0,95 | 0,62 | 0,72 | 1,21 |
| MoGe:s egen FOV | 40,8° | 41,0° | 41,0° | 41,0° | 41,3° | 39,7° | 42,5° |
| bordsskivans höjd efter skala (m) | 0,76 | 0,61 | 0,81 | (0,54, golvfit förkastad) | 0,66 | 0,85 | 0,82 |

- **Slutsatsen i s7 blev rätt i alla körningar efter steg 3:** två bord, inget nytt rum.
- **Geometrin, senaste körningen:** A–B 6,8 m. s7:s förgrundsbord och burk blir kopior i stället för A:s bord och burk, så rummets typstorlek styr avståndet.
- **Jämförelse mot originalet** (`ut/notan/jutsu/original_mot_jutsu.png`, revision 3, ett recept före de två sista ändringarna):
  - A:s närbilder stämmer: A mitt i bild bakom sitt bord, med burk och mugg till vänster.
  - B:s närbilder och s4 stämmer i stort.
  - I s7 satt gästen från s4 bredvid B. Det felet är borta i senare recept, vilket kontrollerades genom projektion, inte rendering.
- **Jutsu-projekt** (privata, ägarens konto):
  - `byggsten-jutsu-konventioner-hello` (`5cadca4b-9f72-446e-84f8-5be3b16a4845`)
  - `byggsten-rumshypotes-syntet-diner` (`a5c74483-075c-4a6e-869e-7dfd0ac134ac`, revision 2)
  - `byggsten-rumshypotes-notan` (`bccf1509-c901-4ef3-ba19-4e41c58988e7`, revision 3)

---

## 7. Fynd att ta med sig (gäller utanför experimentet)

1. **MoGe-2:s metriska skala är inte förankrad per tagning.** Den drar avstånden mot cirka 2 m: närbilder blir för långt bort och fjärran för nära. Kroppen (SAM 3D Body med rätt fokal) är det trovärdiga skalankaret i närbilder.
2. **Kedjans `modal_rum.py` maskar bort personerna** och kör med fast FOV. Då går djupet inte att kalibrera mot kroppen. `modal_djup.py` gör samma körning utan mask.
3. **Fokalen:** försvinningspunkterna (984 px, 32,6°) och MoGe:s egen skattning (cirka 41°) skiljer 22 %. Bordshöjden i s1 talar för 984. Det är en enda punkt och bör prövas på fler klipp.
4. **Två nära ankare räcker inte för en affin djuprättning.** Kropp och bord på 0,8–1,2 m bestämmer inte lutningen, och fjärran kollapsar. Bara golvet över ett djupspann gör det. Närbilder har sällan golv, så fjärran djup i närbilder är i praktiken oförankrat.
5. **Kroppens rygg ger fel lodlinje för sittande personer**, eftersom de lutar sig framåt (28° fel i s1). Normalerna på bordsskivor och golv ger rätt lodlinje.
6. **Manhattan ur normaler:** en tagning med låg koncentration (R < 0,6) har ingen tydlig rät vinkel och ska inte räknas. A:s tagningar i notan har R 0,35–0,45.
7. **Synlighet är den skarpaste ledtråden mot fel hypoteser, och den farligaste.** Med hoptryckt djup byter den tecken, och saker med osäkert läge ger falska straff. Kräv kalibrerat djup och väl känt läge.
8. **Strålsökning utan omprövning låser fast gamla misstag.** Delning av gamla kopplingar (R20) behövs för att en sen evidens ska kunna rätta en tidig koppling.
9. **Gemini via proxyn:** `gemini-2.5-flash` ger 404; använd `google/gemini-3.5-flash`. Färgnamn (vit eller beige) och märken på muggar varierar mellan tagningar, så de duger bara som grova nycklar.
10. **Jutsu:**
    - Markörer med kamera styr kameran vid rendering, så de måste lossas innan man renderar en vald kamera.
    - `sensor_fit` AUTO ger fel bildvinkel i stående format.
    - `camera.angle_y` följer inte upplösningen.
    - `CONTAINER_UNAVAILABLE` är tillfälligt; gör om.

---

## 8. Kända brister och risker

- **Överanpassning.** Reglerna R15–R21, priserna och synlighetsgränserna justerades medan notan kördes. De är skrivna som allmänna regler, men bara prövade på ett riktigt klipp. Varje regeländring flyttade notans förlopp. Lita inte på något tal förrän fler klipp körts.
- **Länkar mellan klipp utan unika saker är sköra.** Hjärnan väljer hellre kopior av ett bord och en burk (cirka 2,8 nats) än att böja svaga vinklar. Ingen ledtråd jämför bildinnehåll mellan klipp.
- **Fjärran i närbilder går inte att förankra.** Väggar bakom personen bär stor sigma, och rummets storlek styrs då av typstorleken (8 m).
- **Delgrafer som knappt är förankrade** (s4: C, gäst, bakgrundsbord, dörr) kan landa i andra klipps synfält och ge falska straff. Synlighetsstraffet ligger efter lösningen, inte i den.
- **Personer är statiska** inom ett klipp och mellan klipp, utom vid en dyr flytt. Rörelse inom ett klipp hanteras inte.
- **Höjder** kommer ur klassens typmått. Kamerans höjd och pitch tas ur observationen och optimeras inte.
- **Fas 1–2 kräver kedjans ingest.** Råvideo utan ingest stöds inte.
- **Tid:** 80–270 s per klipp med sju tagningar. Kombinatoriken växer med antalet klipp och generiska saker.
- **Takhöjden** (2,2 m i notan) är för låg och bör inte litas på.
- **Bara notan.** Guacamole, b-tilltal och gelato är inte körda.

---

## 9. Om någon ska gräva vidare: förslag i ordning

1. **Kör två eller tre klipp till** (guacamole, b-tilltal, gelato) utan att röra reglerna. Det avgör om reglerna är allmänna eller anpassade efter notan. Om resultatet är dåligt ska regeltalen kalibreras på flera klipp samtidigt, inte på ett.
2. **Identitetsevidens mellan klipp** (bildlikhet). Jämför bord, burk och vägg mellan tagningar med bildsärdrag (till exempel DINOv2 på utklipp) eller en parvis VLM-fråga, och gör en kopia dyr när likheten är hög. Det borde knyta s7 till A:s bord och ge A–B cirka 3–4 m.
3. **Breddade rutor som ny observation.** `scen/3d/lasformat/luma-paket/utfall` har F2 för S1 och S4 och videon V1 för S4: originalramen oförändrad i mitten, omgivningen genererad. Golv och fötter syns där. Ta in dem som genererade observationer med större sigma. De ger golvlinjal (R21) och kamerahöjd.
4. **Synlighet in i lösningen** (mjuk residual i stället för straff efteråt), så att löst förankrade delgrafer flyttas ur fel synfält.
5. **Snabbare residualer.** Vektorisera termerna, så att hjärnan klarar fler klipp och tagningar.
6. **Rendera och granska** varje nytt recept mot originalet (`kor.py` skriver skriptet; jämförelsen görs som i `ut/notan/jutsu/`). AGENTS.md kräver det innan en scen kallas klar.

**Om man hellre lägger ned:** det som går att återanvända var för sig är konventionerna (`../jutsu/KONVENTIONER.md`), Jutsu-adaptern, receptformatet och fynden i avsnitt 7. Hjärnan är fristående och importeras inte av något annat.

---

## 10. Beslut och vem som fattade dem

| beslut | av |
|---|---|
| Uppdraget, steg för steg och fråga före bygge | ägaren (CLAUDE.md, arbetssatt.md) |
| Allmänna regler, hjärna och recept i stället för agent per scen | ägaren, 17 nov |
| Notan som testklipp | ägaren ("Ja, notan") |
| Avstånden före bildlikheten | ägaren |
| S7 får användas som bevis för var B sitter i s1–s6. Det går emot deklaration 0.7, men deklarationen är inte ändrad. | uppdraget; ett vägval för notan som ägaren inte uttryckligen har avgjort |
| Försvinningspunkternas fokal som metrisk referens | jag; öppen fråga |
| Alla regeltal | jag; startvärden |
