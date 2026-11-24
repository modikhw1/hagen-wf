<!-- Ägarens uppdrag, inklistrat i chatten 17 nov 2026. Ordagrant. -->
# UPPDRAG: Probabilistisk Video-till-Jutsu Greyboxing & Rumstelemetri-motor

## 1. Bakgrund & Övergripande Mål
Du ska designa, implementera och verifiera en autonom pipeline som analyserar vanlig, ostrukturerad och klippt video (inklusive handhållen eller statisk vertikal 9:16-video från sociala medier/sketcher) och extraherar **parametrisk, semantisk rumstelemetri** – möbelplacering, väggar, fönster, takhöjd, människors positioner, ljuskällor och kameraposer – för att sedan bygga upp en redigerbar 3D-greybox-scen i **Jutsu** via **Higgsfield MCP**.

### Kärnfilosofi (Vad detta INTE är)
Detta är **inte** traditionell fotogrammetri, NeRF, Gaussian Splatting eller ren punktmolnsrekonstruktion (t.ex. enbart VGGT/SfM). Punktmoln ger visuell geometri där det finns parallax och bildöverlapp, men kollapsar vid hårda kameraklipp, statiska kameror och avsaknad av överlappande vyer.

Ditt system ska istället fungera som en **resonerande 3D-artist som "greyboxar" en scen under osäkerhet**:
1. Scenen byggs upp som en **Scene Hypothesis Graph (SHG)** – en levande hypotes med parametriska primitiver (plan, boxar, cylindrar, kameror, ljusvektorer) snarare än miljoner råa punkter.
2. Systemet ska kombinera **metrisk datorseende-geometri** med **semantiskt och logiskt rumsresonemang** (t.ex. ljusriktning, takmönster, antropometriska skalankare, spegelvändning vid 180°-klipp).
3. Systemet ska aktivt hantera **osäkerhet och icke-monoton omprövning (belief revision)**: när sena videoklipp motsäger en tidig rumshypotes ska motorn kunna riva upp och rita om sin scen-graf snarare än att krascha eller felaktigt anta att det är "ett annat rum".
4. Slutresultatet ska realiseras direkt i **Jutsu** genom **Higgsfield MCP**, åtföljt av strukturerad telemetri-JSON med konfidensintervall.

---

## 2. Steg 0: Discovery & Adapter mot Higgsfield MCP / Jutsu
Innan du skriver någon produktionskod för 3D-export ska du:
1. Inspektera och lista alla tillgängliga verktyg, resurser och scheman i **Higgsfield MCP** (inklusive eventuella Jutsu-kommandon för scenhantering, primitiver, transformationer, material/färgkodning, kameror, belysning och viewport/render-export).
2. Dokumentera Jutsus exakta konventioner:
   - Koordinatsystem (Y-up vs Z-up, höger- vs vänsterhänt).
   - Enhetsskala (meter, centimeter etc.).
   - Rotationsordning (Euler XYZ/YXZ eller Quaternions).
   - Vilka primitiver/noder som stöds (cuboids, planes, cylinders, groups/collections, cameras, lights, labels/metadata).
   - Huruvida Jutsu via MCP stödjer rendering/screenshot av en virtuell kameravy (kritiskt för Fas 5: Re-projektionsverifiering).
3. Bygg en ren, frikopplad **Jutsu Scene Adapter** (`jutsu_adapter.py`) som översätter vårt interna, motor-oberoende telemetri-schema (`SceneTelemetry`) till deterministiska MCP-anrop mot Jutsu. Om MCP saknar stöd för vissa metadata-fält (t.ex. osäkerhetsellipsoider), implementera dem som visuella hjälpnoder i greyboxen (t.ex. halvtransparenta bounding-zoner eller färgkodade ankare).

---

## 3. Systemarkitektur (5-stegs Hybridpipeline)

### Fas 1: Video-dekomponering & Kinematisk Analys
- Extrahera bildrutor och identifiera hårda kameraklipp (`shot boundaries`).
- Klassificera varje klipp (`shot_i`) som:
  - **Static / Zero-parallax** (stativ eller minimal rörelse).
  - **Dynamic / Parallax-capable** (kamerapanorering/translation).
- Välj representativa nyckelrutor per klipp samt detektera om personer/objekt rör sig mellan rutor i samma klipp (för att inte blanda ihop objekt-motion med kamera-parallax).

### Fas 2: Lokal Metrisk Extraktion per Klipp ("Sub-scene Islands")
Varje sammanhängande klipp behandlas initialt som en lokal geometrisk ö (`SubScene_i`) med ett lokalt koordinatsystem:
1. **Kameraintrinsik & Orientering:**
   - Estimera FOV / fokaldistans och kamerans pitch/roll via flyktpunktsanalys (vanishing points på raka linjer i tak, väggar, fönster, bord) kombinerat med monokulära djup/kamera-prediktorer.
   - Var explicit med att vertikal 9:16-beskärning och digital zoom ger hög FOV-osäkerhet.
2. **Metriskt Djup & Skalkalibrering (Semantic Scale Anchors):**
   - Använd monokulär metrisk djupestimering (för statiska klipp) eller multi-view/VGGT/MASt3R (endast inom sammanhängande klipp med bevisad parallax).
   - Kalibrera absolut metrisk skala (meter) mot detekterade kända objektklasser:
     - **Människor (antropometri):** Stående person (~1.70–1.85 m), sittande överkropp/huvudstorlek, höft-till-axel-mått.
     - **Arkitektur & Möbler:** Standardbord (~0.72–0.76 m högt), standardstolar (~0.45 m sitthöjd), dörrkarmar (~2.00–2.10 m höga).
     - **Mikro-ankare (om synliga):** Dryckesburkar (~0.115 m), standardmuggar, mobiltelefoner.
   - Beräkna golv-till-bord-och-tak-relationer där vertikal kedja syns (t.ex. golv → stolsben → bordsskiva → person → tak).
3. **Amodal Completion (Dold Geometri):**
   - När bara ovansidan av ett bord eller överkroppen av en sittande person syns i bild ska modellen sluta sig till hela 3D-bounding-boxen ner till det estimerade golvplanet (`floor_plane`), med tydlig markering av vad som är *observerat* vs. *amodal-kompletterat*.

### Fas 3: Cross-Cut Registration & Resonerande Grafmotor ("Hypotesmotorn")
Detta är kärnan i systemet. Eftersom klipp i redigerad video ofta saknar överlappande pixlar måste motorn koppla ihop `SubScene_1..N` i en global **Scene Hypothesis Graph (SHG)**:
1. **Cross-Shot Invariants (Tvärgående ledtrådar):**
   - **Ljus- och fönstervektorer:** Spåra riktningen på starkt dagsljus/skuggfall. Om Klipp A har fönster på *höger* sida och Klipp B har starkt fönsterljus in från *vänster* sida indikerar det en ~180° motriktad orientering längs samma rumsaxel.
   - **Arkitektoniska mönster:** Matcha takstruktur (betong, ventilationsdon, rörriktning, skenbelysning), väggfärger, golvmaterial och glaspartier för att avgöra om klipp tillhör samma rum även när möbelöverlapp saknas.
   - **Blickaxlar & POV-separation:** Skilj strikt på **blickaxel (orientering)** och **kameraposition (translation)**. Två karaktärer kan titta rakt mot varandra längs samma axel (180° motbilder) *utan* att kameran stod vid den andres bord – kameran kan ha flyttats längs axeln mellan tagningarna.
2. **Multi-modal Hypoteshantering (Top-K Beam Search):**
   - När ett klipp delar rumsstil men saknar geometriska ankare till huvudscenen (t.ex. en tredje person som står vid en bakre dörr), ska motorn **inte** chansa fram en enda falsksäker position. Den ska behålla de K mest sannolika positioneringshypoteserna (eller definiera en sannolikhetszon / konfidensradie) baserat på ljusvektor, takriktning och synligt djup bakom personen.
3. **Belief Revision (Non-monotonic Reasoning):**
   - När ett nytt klipp avslöjar nya bevis (t.ex. en sen vidvinkel som visar att två personer som antogs sitta vid samma bord faktiskt sitter 5 meter isär vid två separata bord), ska grafmotorn trigga en global omvärdering:
     - Utvärdera konkurrerande förklaringar: *"Är det ett annat rum?"* vs. *"Är det samma rum där tidigare närbilder hade flyttad kameraposition?"*
     - Väg in gemensamma objekt (t.ex. samma burk/mat/väggfärg/ljusriktning/personer) för att förhindra det klassiska felet att klassa slutavslöjandet som ett nytt rum.

### Fas 4: Global Geometrisk Optimering & Fysikaliska Constraints
Innan scenen byggs i Jutsu ska den valda SHG-hypotesen passera en global constraint-lösare:
- **Gemensamt golvplan:** Tvinga alla möbler och stående personer till `floor = 0` (inga svävande eller nedsjunkna objekt trots lutningsfel i enskilda klipp).
- **Kollisionsfrihet:** Inga väggar, pelare eller solida möbler får överlappa varandra eller blockera verifierade siktlinjer mellan kameror och deras motiv.
- **Konfidenskodning i Telemetrin:** Varje nod i `SceneTelemetry` ska ha:
  - `position: [x, y, z]`, `rotation: [rx, ry, rz]`, `dimensions: [w, d, h]`
  - `position_variance` / `confidence_score (0.0–1.0)`
  - `evidence_shots: [shot_ids]`
  - `geometry_source: "observed" | "amodal_inferred" | "relational_hypothesis"`

### Fas 5: Closed-Loop Re-projektionsverifiering
Om Jutsu via Higgsfield MCP tillåter kamerarendering/viewport-capture (eller via en lättviktig intern projektionsverifierare som speglar Jutsu-kameran):
- Ställ virtuella kameror i den byggda Jutsu-scenen för varje klipp (`Cam_shot_1..N`).
- Projicera tillbaka 3D-bounding-boxarna till 2D-bildplanet.
- Jämför reprojicerad storlek, position och horisontlinje mot videons verkliga detektioner.
- Kör en iterativ optimeringsloop (t.ex. Nelder-Mead / L-BFGS / VLM-guided refinement) för att justera FOV och djupavstånd längs axeln tills reprojektionsfelet minimeras.

---

## 4. Sannolika Dependencies & Teknisk Stack
Föreslå, verifiera och installera lämplig delmängd beroende på tillgänglig hårdvara (GPU/CPU):
- **Video & Bildbehandling:** `ffmpeg-python`, `opencv-python`, `scenedetect` (`PySceneDetect`), `pillow`, `numpy`, `scipy`.
- **Metriskt Djup & 3D-geometri:**
  - Monokulärt metriskt djup + intrinsics: `depth-pro` (Apple), `unidepth`, eller `metric3d` (v2).
  - Multi-view inom sammanhängande klipp (valfritt/komplement): `vggt`, `dust3r` / `mast3r`.
  - Geometri & optimering: `trimesh`, `open3d`, `scikit-learn` (RANSAC för plan/linje-fit), `shapely` (2D-golvplan och kollisionstest).
- **Semantisk & Antropometrisk Detektion:**
  - Objektdetektion/segmentering: `ultralytics` (YOLO) eller `groundingdino` + `sam2` (för bord, stolar, muggar, burkar, dörrar, fönster).
  - 3D Human Pose / Body priors: `mediapipe`, `mmpose` / `rtmpose` eller `4D-Humans` / `SMPLer-X` för att extrahera höjd och sittande/stående orientering.
- **Resonerande Hjärna & Data-validering:**
  - Multimodal VLM-integration (via API/runtime) med strikt strukturerad output (`pydantic` v2) för SHG-byggande och hypotesprövning.
- **MCP-klient & Jutsu-koppling:**
  - Officiell `mcp` Python/TypeScript SDK för kommunikation med **Higgsfield MCP**.

---

## 5. Kända Problem & Fallgropar Du Måste Lösa Explicit
Din design och testsvit måste adressera följande sex problem:
1. **Zero-Parallax på Statiska Tagningar:** Förlita dig aldrig på att SfM/VGGT ger djup när kameran står still. Fall tillbaka smidigt på monokulärt djup + semantiska skalankare.
2. **FOV vs. Distance-tvetydighet:** En bred lins nära objektet och en smal lins längre bort kan ge snarlika perspektiv. Använd kända objektstorlekar + reprojektionskontroll för att bryta tvetydigheten.
3. **Kuleshov- / Klippningsfällan ("Absurdist Distance"):** Anta aldrig permanent att två personer som har 180°-motbilder sitter vid samma bord. Separera alltid `sightline_axis` från `inter_object_distance` tills båda objekten observeras i samma ruta eller binds ihop via gemensam bakgrundsgeometri.
4. **Disconnected Sub-Graphs:** Hantera klipp som bevisligen är i samma rum (via tak/ljus) men saknar gemensamma golv- eller möbelankare, genom att representera deras placering med explicita osäkerhetszoner istället för att hitta på exakt precision.
5. **Prop Continuity Breaks:** Rekvisita på ett bord kan flyttas eller tas bort mellan tagningar för att ge fri siktlinje. Låt inte en enskild saknad mugg eller flyttad påse välta matchningen av hela bordet om bordskant och kvarvarande ankare (t.ex. en burk på rätt relativ sida) stämmer.
6. **Golv- och Lutningsdrift:** Små vinkelfel i kamerans pitch blir stora höjdfel på 5–8 meters avstånd. Lås allt till det globala golvplanet.

---

## 6. Success Criteria (Acceptanskriterier)

### A. Arkitektur & Code Quality
- [ ] **MCP Discovery & Adapter:** Agenten har inspekterat Higgsfield MCP, dokumenterat Jutsus primitiver/koordinatsystem och byggt en testad adapter som genererar giltiga Jutsu-scener utan krascher.
- [ ] **Telemetri-schema:** Pipeline exporterar validerad `SceneTelemetry` JSON med objektklasser, dimensioner, transformer, konfidensvärden (`0–1`), osäkerhetsvarians och `evidence_shots`.
- [ ] **Modularitet:** Tydlig separation mellan video/djup-extraktion, hypotesgraf-resonemang, global optimering och Jutsu-MCP-exekvering.

### B. Geometrisk & Metrisk Kvalitet i Jutsu
- [ ] **Golv- och Tyngdkraftskonsistens:** 100 % av möbler och stående personer i den slutliga Jutsu-scenen vilar på golvplanet (`|y_min - floor| < 0.02 m` eller motsvarande axel) utan att sväva eller skära genom golvet.
- [ ] **Kollisionsfrihet:** 0 olösta fysiska överlappningar mellan solida möbelprimitiver eller väggar.
- [ ] **Rimlig Metrisk Skala:** Estimerade bordshöjder (`0.65–0.85 m`), personhöjder (`1.55–2.00 m`) och rumsdimensioner håller sig inom fysiskt realistiska intervall kalibrerade mot skalankarna.
- [ ] **Färg- och Metadata-kodning i Greybox:** Jutsu-scenen skiljer visuellt (via material/färg/namngivning) på *säkert observerad geometri*, *amodal-kompletterad geometri* och *osäkra/hypotetiska zoner*.

### C. Resonerande Förmåga & Benchmark ("The Absurdist Diner Stress Test")
Bygg och kör ett utvärderingstest (syntetiskt eller mot en riktig testvideo med följande struktur):
- *Scenario:* Person A vid Bord 1 (närbild) ↔ Person B vid Bord 2 (närbild längs samma 180°-axel, ren vägg bakom) ↔ Person C stående i en tredje vinkel utan gemensamt möbelankare men med synligt tak och dörr bakom sig → Avslutande vidvinkel från Bord 1 som avslöjar att Bord 1 och Bord 2 står ~4–6 meter isär.
- **Krav för godkänt på stresstestet:**
  1. [ ] Systemet loggar sin initiala hypotes (t.ex. 1 gemensamt bord) *och* detekterar konflikten/omräkningen vid slutklippet.
  2. [ ] Systemet **avvisar** felaktig klassificering av slutklippet som "ett annat rum", och skapar istället 2 separata bord längs rätt fönster-/ljusaxel i samma Jutsu-scen.
  3. [ ] Person C:s sub-scen placeras i Jutsu med en rimlig rumsplacering baserad på tak- och ljusriktning, *explicit märkt med lägre konfidens / osäkerhetszon* jämfört med Bord 1 och Bord 2.
  4. [ ] Re-projektionschecken visar att den virtuella Jutsu-kameran i slutklippet fångar både förgrundsbordet och det avlägsna bordet inom rimlig pixelmarginal (~15–20 % av bounding-box-storlek).

---

## 7. Arbetsgång
1. **Inspektera** Higgsfield MCP och testa att skapa en minimal greybox-kub + kamera i Jutsu ("Hello World").
2. **Designa** `SceneTelemetry`-schemat i Pydantic samt hypotesgrafens datastruktur.
3. **Implementera** Fas 1–2 (shot cut + djup + objektdetektion/skalankare) på en testvideo och verifiera lokala mått.
4. **Implementera** Fas 3–4 (hypotesmotorn med belief revision + constraint-lösare).
5. **Koppla in** Jutsu-adaptern och Fas 5 (re-projektionsverifiering).
6. **Kör** hela stresstestet, generera slutlig Jutsu-scen, spara loggar över hur hypoteserna utvecklades över tidslinjen och rapportera kvarvarande felmarginaler.
