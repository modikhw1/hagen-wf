# rumshypotes: rummet ur klippt video, som hypotes

Sedan 17 nov 2026. Uppdraget står ordagrant i [UPPDRAG.md](UPPDRAG.md). **Det här är ett experiment att ärva: börja i [EXPERIMENT.md](EXPERIMENT.md).**

**Vad:** en rumshjärna som läser ett klipp i taget och tänker som någon som står i lokalen: vad säger den här tagningen, och vad säger den tillsammans med de förra, om rummets mått, var sakerna står och var kameran stod? Den drar slutsatser, håller flera hypoteser samtidigt och river upp dem när evidensen kräver det. Allt räknas ovanifrån i 2D, med sannolikhet som skärps ju mer klippet går att läsa. Ut kommer ett **recept** som Jutsu bygger på några sekunder. Ingen agent behöver återskapa scenen för hand.

Reglerna är allmänna och gäller alla inomhusklipp, inte notan särskilt.

## Flödet
```
video ─(Fas 1–2: obs_ingest.py + las_vlm.py)─► observationer per klipp   telemetri.Observationer
   kamera (fov, höjd, pitch) · detektioner (stråle + djup ± sigma) · väggar · Manhattan · ljus · fri yta · rumsnycklar
                                   │
                         hjarna.py ▼  klipp för klipp: hypoteser × regler, beam 8, omprövning
                   2D-karta per klipp · hypoteslogg med skäl
                                   │
                         recept.py ▼  SceneTelemetry: noder, kameror, rum, ljus, osäkerhet, logg
                                   │
                  jutsu_adapter.py ▼  ett deterministiskt bpy-skript
                         3D Jutsu (2–3 s, 0 credits) eller lokal Blender
```

## Kör
```bash
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py syntet                 # stresstestet med facit
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py syntet --delat         # kontroll: A och B vid samma bord
scen/.venv/Scripts/python.exe byggsten/rumshypotes/las_vlm.py scen/3d/ingest/ut/notan-tagningar --ut byggsten/rumshypotes/ut/notan/vlm
scen/.venv/Scripts/python.exe byggsten/rumshypotes/obs_ingest.py scen/3d/ingest/ut/notan-tagningar --vlm byggsten/rumshypotes/ut/notan/vlm --ut byggsten/rumshypotes/ut/notan/obs.json
scen/.venv/Scripts/python.exe byggsten/rumshypotes/kor.py byggsten/rumshypotes/ut/notan/obs.json --ut byggsten/rumshypotes/ut/notan
scen/.venv/Scripts/python.exe byggsten/rumshypotes/test_stresstest.py            # uppdragets kriterier
```
Utdata hamnar i `ut/<namn>/`: `karta_<klipp>.png`, `karta_tidslinje.png`, `LOGG.md`, `recept.json`, `jutsu_bygg.py` och `jamforelse.json` (bara med facit). `jutsu_bygg.py` klistras in i `scene_builder_3d_run_python`.

## Hur hjärnan tänker
- **En hypotes är en uppsättning val** om vad observationerna är:
  - vilket bord en detektion av ett bord är (ett befintligt eller ett nytt)
  - om klippet hör till samma rum
  - om en person har flyttat
- **Givet valen** löses lägena (kameror, saker, väggar, ljusets riktning) som minsta kvadrat, med reglerna som residualer. Osäkerheten per sak kommer ur samma lösning (Laplace) och ritas som ellipser.
- **Poängen**, i nats, är summan av fyra delar:
  - passning
  - struktur (Occam)
  - rum (delade rumsnycklar)
  - synlighet (det som borde synas men saknas)
- **De åtta bästa** lever vidare till nästa klipp (beam).
- **En omprövning** loggas när den bästa hypotesen inte längre härstammar från den förra tron. Loggen säger vad den gamla tron hade kostat, vilka observationer som motsade den, och vad som hade krävts för att rädda den.

## Reglerna (`regler.py`)
| regel | innehåll |
|---|---|
| R1 Strålen | Monokulärt djup ger ett avlångt sannolikhetsfält längs strålen: skarpt i sidled, osäkert i djup. |
| R2 Manhattan | Väggar och möbler står i rät vinkel. Varje klipp ger kamerans vridning modulo 90°. |
| R3 Ljuset | Huvudljuset har en fast riktning i rummet. Det bryter 90°- och 180°-tvetydigheten mellan klipp. |
| R4 Identitet | Samma person eller unikt föremål är samma sak. En generisk möbel är en kandidat, och valet är en hypotes. |
| R5 Occam | Färre möbler föredras tills evidensen kräver fler. |
| R6 Blicken | En blick ger riktning, aldrig avstånd (Kuleshov). |
| R7 Synlighet | Det som borde synas men saknas sänker hypotesen. Små föremål kostar lite, eftersom de flyttas. |
| R8 Fri yta | Det kameran ser igenom är tomt. Låga möbler skymmer inte. |
| R9 Väggar | Allt står inom rummet. Ett väggavstånd binder kameran mot väggen. |
| R10 Samma rum | Delade rumsnycklar (vägg, golv, tak) väger mot priset för ett nytt rum. |
| R11 Kontakt | En sittande person sitter vid ett bord, och ett föremål ligger på ett bord. |
| R12 Stillhet | Personer står kvar inom en scen. En flytt är tillåten men kostar. |
| R13 Kollision | Bord står inte i varandra, och kameran står inte i en person. |
| R14 Golvet | Allt står på z = 0 (gäller receptet). |

**Lagren:**
- Hårda regler (golv, kollision, identitet) har små sigma.
- Mätningar (stråle, väggar, Manhattan) är nästa nivå, och svaga ledtrådar (ljus, blick, typmått) den sista.
- Strukturpriset avgör mellan hypoteser som passar lika bra.

Talen är egna startvärden och inga krav. De ska kalibreras mot biblioteket.

## Utfall på den syntetiska dinern (17 nov)
Facit är ett rum på 6 × 10 m. Borden står 5 m isär längs samma axel, och servitören C står vid en dörr. Det finns sju klipp:
- s1, s3 och s6: närbilder på A
- s2 och s5: närbilder på B
- s4: C
- s7: vidvinkel från A:s bord

Observationerna har brus i djup (8–15 %), vinkel och ljus. Burken saknas i s3.

| klipp | tro | P |
|---|---|---|
| s1 | 1 bord; A vid bord_1 | 1,00 |
| s2 | 1 bord; A och B vid bord_1 | 0,81 (två bord: 0,19) |
| s3–s6 | samma | 0,58–0,63 |
| s7 | **2 bord; B vid bord_2** | 0,90 |

Omprövningen i s7, ur `ut/syntet/LOGG.md`:
- Den gamla tron hade gett −51,6 nats.
- Största motsägelserna var väggen bakom B (chi2 42), B:s stråle (35) och det bortre bordet (13).
- Att rädda tron hade krävt "s7: annat rum" plus två nya bord, vilket gav −15,5. Räddningen förkastades.

| mått mot facit | skattat | facit |
|---|---|---|
| avstånd mellan borden | 4,87 m | 5,0 m |
| rummet | 5,9 × 9,7 m | 6 × 10 m |
| A, B, bord_1, bord_2 | fel 0,2–0,45 m | |
| kameror s1–s3 och s5–s7 | fel 0,16–0,32 m | |
| C och dörren | fel 1,2–1,3 m, inom zonen (konfidens 0,02) | |

- **Stresstestet** (`test_stresstest.py`): alla åtta kriterier går igenom. Det gäller C1–C4 och golv, kollision, skala och determinism. Reprojektionen av båda borden i s7 ligger under 20 % av lådans bredd.
- **Andra brusfrön** (3 och 11): samma förlopp, och felen ligger på 0,14–0,36 m.
- **Kontrollen** (`--delat`, där A och B verkligen delar bord): hjärnan behåller "1 bord" genom alla klipp, och s7 bekräftar med P 0,92. Inget andra bord hittas på.
- **Tid:** hjärnan tar 18–28 s för sju klipp. Jutsu bygger scenen och renderar åtta bilder på 2,6 s, för 0 credits.
- **Jutsu-projekt:** `byggsten-rumshypotes-syntet-diner`, id `a5c74483-075c-4a6e-869e-7dfd0ac134ac`, revision 2.
  - Bilder: `ut/syntet/jutsu/jutsu_oversikt.png` (toppvy, s2, s4 och s7).
  - Revision 2 kördes före raden som städar bort föräldralösa data. Det är den enda skillnaden mot `ut/syntet/jutsu_bygg.py`.

## Steg 3: notan, riktig video (17 nov)

### Fas 1–2
`obs_ingest.py` läser kedjans ingest (`scen/3d/ingest/ut/<klipp>/S*/`) och gäller alla klipp som gått genom `ingest_klipp.py`. Den använder bara mätningar inom en tagning.

Ur deklarationen tas bara vem som syns var och om personen sitter eller står. Rummet, borden och kamerorna i deklarationen används inte, eftersom det är de som prövas.

| observation | källa |
|---|---|
| fokal | klippets försvinningspunkter (984 px, `fyra_klipp.json`). Kedjans 1 566 och 1 169 px i S2 och S5 rättas. |
| lodlinje, lutning | bordsskivors och golvets normaler (MoGe). Kroppens rygg lutade 28° för sittande. |
| personer | SAM 3D Body, rå translation, rättad för fokalen. Kroppens storlek är skalankaret. Vändningen kommer ur axlarna. |
| bord | rum.json (MoGe). Bordet framför en sittande person förankras i personens djup (R15). |
| väggar | rum.json och vertikala ytor bakom personen |
| Manhattan | vertikala ytor modulo 90°, viktade efter yta. Sigma kommer ur koncentrationen. |
| fri yta | MoGe i ögonhöjdsbandet, personerna inräknade |
| ljus (sida), rumsnycklar, föremål, dörrar | VLM: `las_vlm.py`, Gemini 3.5 Flash via ägarens proxy, ett anrop per tagning, cache i `ut/notan/vlm/`. Totalt 0,13 USD (proxyn överskattar). |
| blick | roller i motbilder (A, B, A, B …) ser på varandra |

### Nya allmänna regler (efter vad notan visade)
- **R15 Bordet framför:** en sittande person sitter cirka 0,55 m bakom bordets mitt.
- **R16 Många bord:** ett bord utan någon av rollerna kostar bara 0,3 nats.
- **R17 Föremålens identitet:** ett nytt exemplar kostar efter typ. Muggar kostar 0,3 nats, märkta burkar 2,5.
- **R18 Kameran över bordet:** en kamera som ser en bordsskiva ovanifrån står högre än skivan.
- Personer överlappar inte (R13).
- Mjuka ledtrådar (Manhattan, ljus, blick, väggar) får robust kostnad.
- Synlighet räknas bara för saker med känt läge (sigma ≤ 0,8 m).
- Kärntron (vem som sitter med vem) jämförs med sin bästa hypotes. Ett byte under P 0,75 loggas som vacklan.

### Utfall
| klipp | kärntro | P |
|---|---|---|
| s1 | A vid eget bord | 1,00 |
| s2–s3 | A och B vid samma bord | 0,77–0,79 |
| s4–s6 | A och B vid olika bord | 0,86–0,91 |
| s7 | A och B vid olika bord | 1,00 |

- Hjärnan tar 154 s, och Jutsu bygger och renderar på 4,3 s.
  - Projekt: `byggsten-rumshypotes-notan`, id `bccf1509-c901-4ef3-ba19-4e41c58988e7`, revision 2.
  - Bild: `ut/notan/jutsu/original_mot_jutsu.png`, med originalet överst, Jutsu under och toppvyn till höger.
- **Det som stämmer mot originalet:**
  - A:s närbilder: A mitt i bild bakom sitt bord, burken och muggen till vänster i förgrunden.
  - B:s närbilder: B bakom sitt bord.
  - s4: C i mitten, gästen till vänster och dörren bakom.
  - s7: kameran vid A:s bord, med burken i förgrunden och B vid ett eget bord längre bort.
- **Det som inte stämmer:**
  - Gästen från s4 hamnar vid B:s bord och syns bredvid B i s5 och s7.
  - Rummet blir 4,4 × 5,4 m och taket 2,4 m, vilket troligen är för litet och för lågt.
  - Bytet av tro kommer redan i s4. Där kopplar den bästa fortsättningen på "samma bord" bakgrundsbordet till A:s bord och straffas för A:s muggar som inte syns. Det är en artefakt. I s7 är beslutet klart (P 1,00).

### Kvar, i ordning efter vad det avgör
1. **Metrisk skala per tagning.** MoGe:s djup är inte förankrat, och personerna är maskade bort ur djupkartan, så djupet kan inte kalibreras mot kroppen. Därför trycks avstånd på långt håll ihop: den fria ytan blir för kort, rummet för litet och taket för lågt. Lösningen är att köra djupet med personerna kvar (eller en annan metrisk modell) och kalibrera per tagning mot SAM.
2. **Negativ evidens i bildplanet.** Projicera varje sak i tagningens kamera och jämför med djupkartan, i stället för 2D-strålar. Det skulle ta bort gästen vid B:s bord.
3. **Fler klipp** (guacamole, b-tilltal, gelato). Kalibrera reglernas tal och se om reglerna håller allmänt.
4. **Tid.** 150 s för sju tagningar. Grindningen hjälpte (417 → 110 s), och nästa steg är vektoriserade residualer.

## Steg 4: skalan per tagning (17 nov kväll)

### Vad som gjordes
- **Djup med personerna kvar.** `modal_djup.py` kör samma MoGe-2 som kedjan (samma vikter och revision) på en nyckelruta per tagning, men utan personmask. Varje ruta körs också utan fast FOV. Det tog cirka 5 s GPU-tid på Modal, alltså några cent. Utdata: `ut/notan/djup/`.
- **Skala per tagning (R19 Kroppen är linjalen).** SAM-ledernas djup (axlar och nyckelben, minus 0,10 m till kroppens yta) delas med MoGe:s djup på samma pixlar. Allt som läses ur djupet skalas sedan: väggar, fri yta, föremål, dörrar, takhöjd och kedjans bord.
- **Negativ evidens i bildplanet.** Ett grovt djupnät (32 × 18) följer med varje tagning. Hjärnan projicerar varje sak i tagningens kamera och jämför med det uppmätta djupet där.
  - En person räknas som saknad om hen inte är tydligt skymd, eftersom personer nästan alltid upptäcks när de syns.
  - Övriga saker räknas bara om kameran ser förbi platsen.
- **Gamla kopplingar prövas om (R20).** Efter varje klipp prövas att dela saker som kopplats över flera klipp. Delningen behålls om den förklarar bättre.
- **Övriga ändringar:**
  - Kedjans väggar (`rum.json`, enkelvy på maskat djup) används bara när eget kalibrerat djup saknas.
  - En Manhattan-läsning med låg koncentration (R < 0,6) räknas inte.
  - En osedd flytt kostar 6 nats.
  - Synlighet räknas bara för saker med sigma ≤ 0,5 m.

### Vad mätningen visade
| tagning | s1 | s2 | s3 | s4 | s5 | s6 | s7 |
|---|---|---|---|---|---|---|---|
| skala (kropp / MoGe) | 0,73 | 0,54 | 0,71 | 0,95 | 0,62 | 0,72 | 1,21 |
| MoGe:s egen FOV | 40,8° | 41,0° | 41,0° | 41,0° | 41,3° | 39,7° | 42,5° |

- **MoGe drar avstånden mot cirka 2 m.** Närbilder hamnar för långt bort och vidvinkeln för nära. Det var därför gästen ansågs skymd och rummet blev fel.
- **MoGe skattar själv FOV till cirka 41° i alla tagningar.** Det motsvarar en mobil i 1x på stående bildbredd. Försvinningspunkterna gav 32,6° (984 px), och den används fortfarande som metrisk referens.
  - Om 41° är rätt blir hela scenen cirka 22 % mindre.
  - Det är en öppen fråga.

### Utfall på notan (senaste körningen)
| klipp | kärntro | P |
|---|---|---|
| s2–s4 | A och B vid olika bord | 0,58–0,74 |
| s5–s7 | A och B vid olika bord | 1,00 |

- **Gästen från s4 och hens bord** hamnar bakom s7:s kamera, alltså inte längre i bild bredvid B. Det kontrollerades genom att projicera receptet i s7:s kamera, inte genom rendering.
- **Förgrundsbordet och burken i s7 blir kopior** av A:s bord och burk. Kameran i s7 knyts alltså inte till A:s bord, och avståndet mellan A och B blir 6,8 m eftersom rummets typstorlek styr det.
- **Den tidiga tron på ett gemensamt bord försvann** när den svaga Manhattan-läsningen i A:s tagningar togs bort. Med den kvar höll tron till och med s4, men länken till s7 brast ändå.
- **Jutsu:** revision 3 i `byggsten-rumshypotes-notan` och `ut/notan/jutsu/original_mot_jutsu.png` visar receptet före de två sista ändringarna (kedjans väggar och svag Manhattan). Det senaste receptet är inte renderat.
- **Syntetiska prov:** stresstestet går igenom alla åtta kriterier, kontrollen med delat bord ger P 0,99 och dinern P 0,99.

### Det sköra ledet nu
Länken mellan A:s närbilder och s7 bygger bara på svaga vinklar och en burk, och ingen ledtråd jämför bilderna. Hjärnan väljer hellre en kopierad burk och ett nytt bord (2,8 nats) än att böja vinklarna. Det som saknas är evidens för samma föremål mellan två klipp:
- en jämförelse av bordets och burkens utseende i tagningarna (bildlikhet, till exempel DINOv2-särdrag)
- eller en parvis fråga till VLM:en om det är samma bord

## Steg 5: avstånden (17 nov kväll)

- **Två nära ankare räcker inte.** En affin rättning (skala och förskjutning) med kroppen (cirka 1,2 m) och bordsskivan (cirka 0,8 m) gav obestämd lutning, och fjärran djup kollapsade (s3: 5,8 → 2,8 m). Bara golvet över ett djupspann bestämmer lutningen (R21).
  - Affin rättning sker nu bara där golvet syns över minst 1 m djup, och bara om fitten inte slår i sina gränser.
  - I notan uppfyller ingen tagning det: s4:s golvfit slog i gränsen. Alla tagningar har därför ren skala mot kroppen.
- **Närfältet stämmer.** Med ren skala blir bordsskivan 0,61–0,85 m över golvet (medel cirka 0,72) i s1–s3 och s5–s7. Standard är 0,72–0,76 m.
- **Fokalen:** 984 px (32,6°) står sig. I s1 ger den bordsskivan 0,76 m, medan MoGe:s egen fokal (774 px) ger 0,62 m. I de andra tagningarna gick kalibreringen inte att köra med MoGe:s egen fokal.
- **Fjärran går inte att förankra i närbilderna.** Väggarna bakom A har varken kropp eller golv på samma avstånd, och MoGe trycker ihop dem. De ligger därför kvar med stor sigma.
- **Det största avståndsfelet är länken till s7, inte djupet.** A–B blir 6,8 m och rummet 7,7 × 8,0 m, eftersom s7 inte knyts till A:s bord och rummets typstorlek då styr. s7 mäter B 3,05 m från kameran vid A:s bord, så A–B borde bli cirka 3–4 m. Det är vad bildlikheten ska lösa.

## Kända brister
1. **Fas 1–2 finns nu för klipp som gått genom kedjans ingest** (steg 3). Råvideo utan ingest stöds inte än.
2. **Talen i reglerna är gissade.** De behöver kalibreras på riktiga klipp.
3. **Kombinatoriken växer** med antalet klipp och generiska möbler. Sju klipp tar 20 s. Fler klipp kräver smartare förslag än att pröva alla kombinationer.
4. **Antaganden:**
   - Statiska tagningar och sittande eller stående personer. Rörelse inom ett klipp hanteras inte.
   - Höjder kommer ur klassens typmått och kamerans höjd ur observationen; de optimeras inte.
   - Bordens riktning kommer ur regeln att man sitter längs långsidan.
5. **Ett vägval för notan:** deklarationen 0.7 säger att S7 inte får användas som bevis för var B sitter i S1–S6. Hjärnan gör tvärtom, enligt uppdraget.

## Filer
| fil | vad |
|---|---|
| `telemetri.py` | schemat i Pydantic: `Observationer` in, `Recept` (= `SceneTelemetry`) ut |
| `regler.py` | reglerna och deras tal |
| `hjarna.py` | hypoteser, lösning, poäng, beam, omprövning och logg |
| `karta.py` | 2D-översikten per klipp och tidslinjen |
| `recept.py` | hjärnans tro i scenens ram |
| `jutsu_adapter.py` | recept till bpy (Jutsu eller lokal Blender) |
| `syntet.py` | diner med facit och simulerade observationer |
| `obs_ingest.py` | Fas 1–2 ur kedjans ingest (allmänt för ingestade klipp) |
| `las_vlm.py` | VLM per tagning: ljusets sida, rumsnycklar, föremål, dörrar |
| `modal_djup.py` | MoGe-2 utan personmask och med egen FOV, en ruta per tagning (Modal) |
| `kor.py` | hela flödet för ett observationspaket |
| `test_stresstest.py` | uppdragets kriterier |
