# Förvärldens Kärna (`forvarld_karna`) — Långsiktig Arkitektur & Avskiljning

**Skapad:** 18 nov 2026 av Argon  
**Syfte:** En renodlad, kompromisslös avskiljning i `hagen-wf` som samlar den grundläggande förståelsen av LeTrend, obducerar tidigare sidospår (`scen/3d/`, `forvarld/`, `byggsten/`) och etablerar den långsiktiga, självbärande pipelinen från råvideo till en semantiskt manipulerbar 3D-förvärld.

---

## 1. Grundläggande Förståelse: LeTrend, Kreativ Bricolage & Förvärlden

### 1.1 Affärs- och produktkärnan
LeTrend (`../hagen-ui`) bygger på **kreativ bricolage**:
1. **Riktigt innehåll som råvara:** Ungdomar och kreatörer laddar upp *riktiga* videoklipp (TikTok/Reels i 9:16). Det är det autentiska samspelet, tajmingen, rummet och mänskliga rörelser som gör att innehållet fungerar.
2. **Harnessen som kompass:** Genom systematisk dataiteration och feedback har en *innehållsharness* (`video/format/`, `data/format/`) tränats fram. Den vet **varför** ett klipp fungerar (premiss, krok, vändning, takter, vad som bär poängen) och hur det förhåller sig till en specifik verksamhets (kunds) linje, fas och produktionsförmåga.
3. **Content Managerns (CM) verktyg:** CM ska effektivt kunna planera och strukturera contentplaner för verksamheter. När ett referensklipp väljs ur banken behöver CM kunna forma om det till kundens verklighet (*"byt glassen mot våra burgare"*, *"flytta första scenen till bardisken"*, *"låt henne räcka fram med andra handen mot kollegan"*) och få ut ett tydligt, trovärdigt visuellt manus/förhandsvisning.

### 1.2 Varför 1:1 och varför "Förvärlden"?
Målet är **1:1-återskapning utan generativ AI i analys- och manipulationsledet**:
- **Generativ video ljuger om struktur:** Mätningarna i `scen/3d/` visade att när en videomodell (Wan, Luma, Seedance) ombeds ändra en scen direkt i pixelrummet hittar den på nya rum, byter händer, ändrar produkter och tappar den komiska tajmingen.
- **Förvärlden som mellansteg:** Förvärlden är en **lättviktig, blocky 3D-värld** som fångar originalklippets sanna fysik och struktur:
  - Kamerans position, vinkel, brännvidd (FOV), rörelse och hårda klipp (`shots`).
  - Lokalens sannolika 3D-layout (golvplan, väggar, bord, diskar, dörrar, ljuskällor).
  - Personernas identitet, placering, synlighet och kroppsrörelser över tid (riggade skelett + ansikts-/blickriktning + föremål i hand).
  - Tidslinjens repliker, ljudöverlägg och takter.
- **Inbakad mening (semantisk manipulation utan omgenerering):** När förvärlden bär både *geometri* och *mening* (affordanser, avsikter, takter och kontaktvillkor) kan en semantisk ändring som *"låt tjejen byta hand när hon interagerar med sin kollega"* beräknas **direkt i 3D-riggen och rumsmodellen på några sekunder** – utan att en generativ AI behöver gissa om hela videon.
- **Generativ AI först som valfritt slutfilter:** Först när förvärlden (originalklippets komponenter + CM:s semantiska ändringar) är låst och verifierad, kan dess 3D-sketch skickas som styrning till en stiliserad slutrendering (t.ex. PS2-grafik, Seedream/Seedance eller direkt som visuellt 3D-storyboard för kunden).

---

## 2. Obduktion av Tidigare Försök: Vad fungerade och vad körde fast?

Under två veckor har arbete bedrivits i tre huvudgrenar (`scen/3d/`, `forvarld/`, `byggsten/`). Här är den tekniska domen över vad som ska **bevaras** och vad som ska **lämnas bakom oss**.

### 2.1 Det som lämnas bakom oss (Lapptäcket i `scen/3d/`)
`scen/3d/` växte till över 40 skript där varje kantfall på ett enskilt klipp (`notan`, `gelato`, `guacamole`, `b-tilltal`) löstes med en ny klipp-specifik patch:
1. **Handskrivna rumsmallar (`deklaration.json`):** Systemet krävde att rummet deklarerades i förväg (eller gissades av Gemini i 5 rundor med reparationsloopar). Ändå glömde kompilatorn rumsgiltighet per tagning, vilket gav massiva spökblock mitt i bild (`byggsten/jutsu/BUGG-BLOCK.md`).
2. **SAM 3D Body i fritt fall:** SAM 3D Body läser leder kamerarelativt per bildruta.
   - När kameran rörde sig (`gelato S1`) hamnade kamerans åkning som bakåtgående rotförflyttning i kroppen.
   - När ben och fötter skymdes av bord eller bildkant gissade modellen fötter 25 cm under golvet (`notan S7`) eller 35 cm framför bäckenet.
   - I stället för en enhetlig fysikalisk kameralösare + kontakt-IK lades 10–15 efterbehandlingsskript (`handsyn.py`, `trostod.py`, `tagning.py`, `aterflytt`, hårdkodade rutor i `c_ingest.py`) ovanpå varandra.
3. **Klippspecifika strängersättningar:** I `byggsten/jutsu/guacamole_pipeline.py` byggdes scenen genom `source.replace('ut/notan/...', 'ut/guacamole-dialog/...')` på ett annat klipps skript. Det är motsatsen till en generell abstraktion.

### 2.2 De fyra guldkornen som vi tar med oss in i `forvarld_karna`
Ur experimenten i `byggsten/` finns fyra genuint starka, modulära komponenter som – när de rättas och kopplas ihop – bildar hela lösningen:

| Ursprung | Vad som faktiskt fungerar | Varför det bär framåt |
|---|---|---|
| **1. Rumshjärnan** (`byggsten/rumshypotes/`) | Probabilistisk 2D/3D-pussellösare (`hjarna.py`, `telemetri.py`, `regler.py`) som läser tagning för tagning, använder kroppen som metrisk linjal (R19), håller en beam av hypoteser och gör *belief revision* när ett sent klipp (`notan S7`) avslöjar rumsstrukturen. | Ersätter handskrivna deklarationer med en allmän matematisk slutledningsmotor. (Kräver dock tre specifika buggrättningar för cross-shot-länkning och avstånd; se avsnitt 3). |
| **2. Bryggan & T1-armaturen** (`byggsten/brygga/`) | `scenpaket/1`, kvalitetsgrindarna **G1–G7** (`grindar.py`) och **T1-armaturen** i `emit_bpy.py` (26 ben med fasta benlängder, fotkontakt-IK R3, huvudriktning ur MHR-rotation, bakade rotationsnycklar i 30 KB kod) som körs identiskt i lokal Blender 5.2 och gratis i **Higgsfield 3D Jutsu**. | Löser både kroppens representation, GLB/Blender-kompatibilitet och automatisk verifiering mot originalet. |
| **3. Innehållsryggraden & Regibordet** (`byggsten/hand/`) | `ryggrad.py`, `anpassa.py`, `tillstand.py` och `forstand.py`. Kopplar 1 480 formatkort till ett klipps takter, mallplatser och "fingrar" (räckvidd inom typen mot en kunds linje), med Jev (< 250 ms) för kända drag och Förståndet som kompilerar nya recept till lärda drag. | Är bryggan direkt in i `hagen-ui` och CM:s faktiska arbetsflöde. |
| **4. Två sinnen & Kropp med minne** (`byggsten/hjarna/UTMANING.md` + `0039/0044`) | Distinktionen mellan **Upphovets sinne** (M3–M2: premiss, kontrast, vändning, takter) och **Karaktärens sinne** (M1–M0: mål, prioriteringar, kontaktvillkor kring originalets rörelse som minne). | Förklarar hur mening bakas in i 3D-scenen så att målet består medan kroppen räknar om medlen. |

---

## 3. Varför 3D-rumspusslet (`rumshypotes`) missade avstånden på riktig video — och lösningen

I `byggsten/rumshypotes/EXPERIMENT.md` noterades att rumshjärnan drog rätt logisk slutsats på `notan` (två bord i samma rum, P = 1.00 i `S7`), men fick avståndet mellan A och B till **6,8 m** i stället för verkliga **~3,3 m**, eftersom förgrundsbordet och burken i `S7` behandlades som *nya kopior* (`bord_4`, `foremal_5`) i stället för A:s bord (`bord_1`) och A:s burk (`foremal_1`).

En källkodsanalys av `obs_ingest.py` och `hjarna.py` visar att detta **inte** berodde på att pusselidén är fel, utan på **fyra konkreta, matematiska buggar i implementeringen**:

1. **Bugg 1 — Kovarariansblind grindning i `_expandera` (`hjarna.py:670–671`):**
   - Före `S7` har `A`:s delgraf (`A, bord_1, burk`) och `B`:s delgraf (`B, bord_2`) aldrig synts i samma bild. De är två *frikopplade delgrafer* vars inbördes avstånd bara hålls av en svag rumsprior, med en uppmätt osäkerhet på **$\sigma = 5,43\text{ m}$** (`LOGG.md:35`).
   - När `S7` kommer in ser kameran både `B` (unik person) och A:s bord + burk i förgrunden. `_expandera` placerar först kameran `c0` utifrån `B`:s gamla, osäkra position.
   - Därefter kastar rad 671 bort alla kopplingar till befintliga objekt `x[1]` (`bord_1`, `foremal_1`) om `norm(h.x["ent"][x[1]] - pv) >= 3 * d.djup_m.s + 1.0` ($\approx 1,8\text{ m}$) — **utan att ta hänsyn till osäkerheten i `c0` ($\sigma_B = 5,43\text{ m}$) och `x[1]` ($\sigma_{\text{ent}}$)!**
   - *Följd:* Hypotesen att förgrundsbordet i `S7` är `bord_1` slängdes bort av grinden *innan* minsta-kvadrat-lösaren ens fick pröva att flytta ihop delgraferna!

2. **Bugg 2 — Förlorad `pa`-relation i 2D vs 3D (`obs_ingest.py:410`):**
   - För att avgöra om ett föremål (t.ex. `bonaqua_burk_gul`) står på ett bord mätte `obs_ingest.py` det euklidiska **3D-avståndet** `np.linalg.norm(bord_id[kand] - p) < 1.0`.
   - Men `bord_id[kand]` hade förankrats via R15 i personens 3D-kamerapunkt `pp["p"]` (axelhöjd/brösthöjd), medan burkens punkt `p` låg nere på bordsskivan! Därför misslyckades testet i `S1`, så `S1:f1` (burken) fick `"pa": null` i `S1`, medan den fick `"pa": "S7:t1"` i `S7`. När man mäter vågrätt avstånd i `(x, z)`-planet knyts burken och muggen direkt till `bord_1` i alla tagningar.

3. **Bugg 3 — Låst orientering när `S1` saknar Manhattan-läsning (`hjarna.py:638–645`):**
   - `S1` hade låg koncentration av vertikala väggnormaler ($R < 0,6$), så `manhattan_deg` blev `None`. Klipp 0 låstes ändå till `yaw = +90°`, vilket tvingade in ljusets världsazimut `alfa` i ett skevt läge. När `S7` sedan hade både `manhattan_deg` och `ljus_bearing_deg` valde `_yaw_alternativ` bara *en* av de fyra Manhattan-riktningarna, som låg 90°–180° fel mot `S1`:s blickaxel.

4. **Bugg 4 — Avsaknad av visuell ankarmatchning (Cross-Shot Visual Re-ID) mellan klipp:**
   - Precis som en människa ser att den gula Bonaqua-burken på det bruna träbordet i `S1` är samma burk och bord som i vänster nederkant av `S7`, ska `obs_ingest` extrahera visuella signaturer (färg-/texturhistogram och DINO/SIFT-särdrag i utklippsrutan) och ge hög kopplingsbelöning när två tagningar visar samma distinkta rekvisita på samma bord.

---

## 4. Målarkitekturen i `forvarld_karna` (De 4 Lagren)

All ny utveckling sker i denna mapp (`forvarld_karna/`) enligt fyra strikt separerade lager som kommunicerar via typade Pydantic/JSON-scheman:

```
RÅVIDEO / INGEST-DATA
  │
  ▼  [Lager 1: obs_motor.py]
OBSERVATIONER (obs.json)
  • Kameraintrinsik (fokal ur flyktpunkter/MoGe, lodlinje ur horisontella ytor)
  • Kropp som metrisk linjal (R19: SAM-leder kalibrerar MoGe-djupet per tagning)
  • Horisontell 2D-projektion för möbler och 'på'-relationer + visuella objektnycklar
  │
  ▼  [Lager 2: rums_pussel.py]
RUMSLÖSNING & RECEPT (recept.json)
  • Kovariansmedveten Beam Search + Minsta-kvadrat-optimering (Manhattan, Ljus, Blick, Stråle, Synlighet)
  • Icke-monoton omprövning (Belief Revision) + Delgraf-sammanslagning när vidvinkel binder ihop rummet
  • Utdata: Globalt rum (golv z=0), möbler, kameror per tagning och tidslinjegiltighet (berättat vs avslöjat rum)
  │
  ▼  [Lager 3: scen_brygga.py & emit_bpy.py]
FÖRVÄRLDSPAKET (scenpaket.json) & 3D-SCEN (Blender / 3D Jutsu)
  • Lyfter in kropparnas 3D-rörelsesekvenser i rummets koordinatram med bevarad 2D-kameratrohet
  • Fysikalisk kontakt-IK (R3: fötter mot golv z=0, sittande mot stol, lugnade dolda händer)
  • T1-armatur (26 ben, bakade kvaternioner, blickriktning) + Grindar G1–G7
  • Deterministisk bpy-kod för lokal Blender 5.2 och Higgsfield 3D Jutsu (0 credits)
  │
  ▼  [Lager 4: mening_motor.py]
SEMANTISK MANIPULATION (Ryggrad + Två Sinnen)
  • Upphovets sinne (takter, kontrast, kundens linje ur formatkort)
  • Karaktärens sinne (mål, prioriteringar, hand-/platsbyte direkt i 3D-paketet utan generativ AI)
```

---

## 5. Katalogstruktur i `forvarld_karna/`

| Fil | Ansvar |
|---|---|
| `ARKITEKTUR.md` | Detta dokument: systemförståelse, obduktion och arkitekturkontrakt. |
| `schema.py` | Pydantic-scheman för `Observationer`, `Recept` (`SceneTelemetry`) och `Scenpaket`. |
| `regler.py` | Fysikaliska, geometriska och strukturella regler (R1–R22) med kalibrerbara vikter. |
| `obs_motor.py` | Lager 1: Extraherar kalibrerade observationer, horisontella `pa`/`vid`-relationer och visuella föremålsankare ur ett klipps tagningar. |
| `rums_pussel.py` | Lager 2: Den korrigerade, kovariansmedvetna rumshjärnan som löser 2D/3D-layout, kameror och omprövningar över klipp. |
| `scen_brygga.py` | Lager 3: Förenar rumslösningen med T1-kroppsriggar, kontakt-IK, rumsgiltighet per tagning, kvalitetsgrindar (G1–G7) och Blender/Jutsu-skript. |
| `mening_motor.py` | Lager 4: Destillerar ut kroppens `AttitydProfil` (slapphet, lutning, tempo, blickfokus) vid ingest, bygger den sammansatta Jev-ytan och utför blixtsnabb semantisk manipulation med attitydarv (t.ex. sittande $\rightarrow$ gående med samma slappa sätt + kompositionslås). |
| `verifiera.py` | Kör hela kedjan på testklippen (`syntet`, `notan`, `guacamole`, `b-tilltal`) och verifierar avstånd, reprojektion och grindar. |

---

## 5.5 Kalibrering av Långsiktig Plan: Hur Harnessen, Attitydmotorn, Jev och Seedance Talar Samma Språk

För att `hagen-wf` inte ska bli en samling isolerade sidospår gäller följande arkitektoniska arbetsfördelning i produkten (`../hagen-ui`):

1. **Ingest är en engångsinsats — Live-manipulering för CM måste ske på millisekunder:**
   - När ett klipp först laddas ner/analyseras får ingesten ta tid för att lösa rumspusslet (`rums_pussel.py`), kamerakompositionen och kroppens basrörelse.
   - **Blender och SAM 3D Body är verktyg vid ingest/verifiering, inte flaskhalsar i CM:s live-vy.** När ingesten är klar bor hela klippet i ett ~100 KB `scenpaket/2` (`paket.json`) som kan ritas och manipuleras direkt i webbläsaren (Three.js/WebGL som i `byggsten/hand/bord/`).

2. **Isolera kroppens rörelse & attityd från SAM 3D Bodys råa ledbrus (`mening_motor.py`):**
   - SAM 3D Body ger råa 3D-koordinater ruta för ruta, men förstår varken attityd eller hur en person rör sig om manuset ändras från att sitta vid ett bord till att gå genom lokalen.
   - Därför destillerar `mening_motor.py` vid ingest ut en **`AttitydProfil`** per person och takt:
     - **Hållning & Tonus (`slapphet`, `lutning_deg`):** Sitter/står personen slappt framåtlutad (`slapp_avslappnad`, som kunden A i `guacamole` med ~25° rygglutning) eller upprätt och alert (`energisk_utatriktad`, som bartendern B)?
     - **Tempo, Gestomfång & Blickfokus (`hand_fart_m_s`, `uppmarksamhet`):** Hur snabbt och yvigt rör sig händerna, och hur låst är blicken mot kamera/motpart (signaturerna ur `0042`)?
     - **Fysisk stil-prompt för Kimodo / procedur-motor (`kimodo_stil_prompt`):** Neutral fysisk beskrivning av rörelsestilen så att antingen vår snabba lokala kinematiska stil-syntes (< 50 ms) eller Kimodo-SOMA-RP (kommersiell NVIDIA Open Model License) kan generera nya handlingar (gå genom köket, stå vid disken, byta hand/prop) **med exakt samma mänskliga attityd**.

3. **Hedra originalets kamerakomposition — detaljerna bärs av Seedance i slutsteget:**
   - Förvärldens primära uppgift är att **hedra originalets kamerarörelse, utsnitt, komposition och timing** medan CM (via **Jev** på < 250 ms eller Förståndet/LLM) anpassar innehållet efter kundens harness (`byggsten/hand/`).
   - När en semantisk ändring flyttar en person (t.ex. från sittande till att gå genom rummet), låser `mening_motor.py` kamerans tracking/komposition mot personens nya bana så att utsnittet består, och slutresultatet skickas som 3D-styrning till **Seedance** (eller illustrativ PS2/sketch-render) som fyller i de visuella ytdetaljerna.

---

## 6. Verifierat Genombrott (18 nov 2026 — `verifiera.py`)

När de matematiska och geometriska felen rättades i `obs_motor.py` och `rums_pussel.py` — plus allmän möbeldetektion ur MoGe-ytnormaler, bålens 3D-ledposition i stället för MHR-fotorigo, bröstriktad bordsförankring vid sidovyer, flerpersons-identifikation per tagning och SIFT-kameragruppering (`R23–R24`) — går nu **fyra helt olika riktiga videoklipp** samt de syntetiska stresstesterna igenom samma motor utan klippspecifik kod:

### 6.1 `notan` (7 tagningar, S1–S7: 180°-motbilder + avslöjande vidvinkel)
| Mått på riktig video (`notan`, S1–S7) | Gammal `byggsten/rumshypotes` | Ny `forvarld_karna` (`ut/notan/recept.json`) |
|---|---|---|
| **`bord_1` (A:s bord) kopplat över tagningar** | `['s1', 's3', 's6']` (missade `s7`, skapade `bord_4`) | **`['s1', 's3', 's6', 's7']`** (`conf = 0.812`) |
| **`bord_2` (B:s bord) kopplat över tagningar** | `['s2', 's5']` | **`['s2', 's5', 's7']`** (`conf = 0.618`) |
| **`foremal_1` (gul Bonaqua-burk) kopplat** | `['s1', 's3', 's6']` (skapade kopian `foremal_5` i `s7`) | **`['s1', 's3', 's6', 's7']`** (`conf = 0.802`) |
| **`foremal_4` (B:s Max-mugg) kopplat** | Ej kopplad till `s7` | **`['s5', 's7']`** (`conf = 0.578`) |
| **Osäkerhet ($\sigma$) för B före $\rightarrow$ efter `s7`** | `5.43 m → 3.18 m` (förblev obunden!) | **`2.90 m → 0.30 m`** (låst längs siktaxeln!) |
| **Skattat avstånd A $\leftrightarrow$ B** | `6.80 m` (styrt av rumsprior) | **`2.85 m`** (A vid `y = -0.15`, B vid `y = -2.99` längs samma axel `x ≈ -1.9`) |

### 6.2 Fler riktiga klipp genom samma motor (`guacamole`, `gelato`, `asketch`)
| Klipp | Tagningar & Utmaning | Sluttro & Sannolikhet | Resultat i `forvarld_karna` |
|---|---|---|---|
| **`guacamole`** (`e-dialog-guacamole-tagningar`) | 4 tagningar (S1–S4): YOLO gav `objects=[]` i alla rutor; tvåpersonsvinkel i S4 där både kund A (sitter) och personal B (står) syns på varsin sida av bardisken. | **`A och B vid samma bord` (`P = 0.98`)** (8.3 s) | Bardisken `bord_1` detekteras ur MoGe-normalerna och kopplas ihop över **alla fyra tagningar `['s1', 's2', 's3', 's4']`** (`conf = 0.76`) mitt emellan A (`['s1', 's3', 's4']`) och B (`['s2', 's4']`), avstånd `1.15 m`. `CAM_s1` och `CAM_s3` låsta via SIFT; `CAM_s4` placerad i barens öppning. |
| **`gelato`** (`kand-kennysgelato-tagningar`) | 2 tagningar (S1–S2): 1 person bakom glassdisk (`objects=[]`), 90° kameravinkelbyte där bara ~40 % av rummet syns och lutande frontglas störde lodlinjen. | **`A vid eget bord` (`P = 1.00`)** (0.5 s) | Glassdisken `bord_1` och person `A` kopplas ihop i **`['s1', 's2']`** (`conf = 0.74–0.80`) utan dubblettbord. `CAM_s1` framifrån (`-0.2°`) och `CAM_s2` från sidan längs disken (`+63.0°`). Observerad sidovägg + 3 streckade antagna väggar. |
| **`asketch`** (`a-sketch-servering-tagningar`) | 7 tagningar (S1–S7): Kund A och personal B över glasdisk + köksbänk + extrem B-roll-närbild utan person i S6 + 14 000 m MoGe-outlier i `rum.json`. | **`A vid eget bord; B vid eget bord` i 1 rum (`P = 0.86`)** (8.7 s) | Outlier-väggen på 14 km filtreras bort; S6 kraschar inte utan knyts till bänken `bord_2` (`['s5', 's6']`), medan kundsidans glasdisk `bord_1` knyts till `['s1', 's7']`. `CAM_s1/s7` och `CAM_s2/s5` bildar 180°-motbildspar. |
| **Syntetiskt stresstest** | 7 tagningar: Två bord (5.0 m) + Kontroll (Delat bord) | **`P = 0.99` / `P = 1.00`** (8–9 s) | Alla 8 acceptanskriterier godkända (`4.87 m` mot facit `5.00 m`). |

### 6.3 Lager 3 (`scen_brygga.py`) — Direktkompilering till `scenpaket/2`, T1-armaturer, G1–G7 & Blender 5.2-rendering

Genom att lyfta in råsekvenserna (`S*/sekvens_*.npz`) direkt i rumshjärnans kameror i `recept.json` (med bålcentrerad fokalskalning $\kappa$, gemensam höjdkalibrering enligt R18, R3 fotkontakt-IK, `R25_separera_kamerarorelse`, kontaktkalibrerade 14 cm diskskivor och sits-skivor under sittande personers bäcken) har hela kedjan frigjorts från gamla `scen/3d/kontrakt/plan.json` och verifierats med **0 fel på samtliga sju kvalitetsgrindar (G1–G7)** samt renderats i lokal Blender 5.2 mot originalrutorna:

| Klipp | G1 rum | G2 golv | G3 säte | G4 genom | G5 i bild | G6 skymning | G7 trohet | Filer & Visuell Jämförelse |
|---|---|---|---|---|---|---|---|---|
| **`guacamole`** (`S1–S4`) | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** (`IoU 0.76–0.87`) | `ut/guacamole/paket.json`<br>`ut/guacamole/GRINDAR.md`<br>`ut/guacamole/jamforelse.png` |
| **`gelato`** (`S1–S2`) | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** (`IoU 1.00`) | `ut/gelato/paket.json`<br>`ut/gelato/GRINDAR.md`<br>`ut/gelato/jamforelse.png` |
| **`asketch`** (`S1–S7`) | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** (`IoU 1.00`) | `ut/asketch/paket.json`<br>`ut/asketch/GRINDAR.md`<br>`ut/asketch/jamforelse.png` |
| **`notan`** (`S1–S7`) | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** | **0 fel** (`IoU 0.73–1.00`) | `ut/notan/paket.json`<br>`ut/notan/GRINDAR.md`<br>`ut/notan/jamforelse.png` |

### 6.4 De 4 Strukturella Härdningarna (19 nov 2026)

För att säkerställa att pipelinen inte vilar på genvägar har vi även stängt de fyra återstående strukturella svagheterna mellan ingest och semantisk manipulation:

1. **Deklarationsfri Person-Re-ID & Hållningsinferens (`obs_motor.py --utan-deklaration`):**
   - `obs_motor.py` kräver inte längre handskriven `plats/deklaration.json`. Med `--utan-deklaration` (eller när `deklaration.json` saknas, som i `gelato`) läser motorn direkt modellbedömd `semantik/1` (`P1 -> A, P2 -> B, P3 -> C` + `placeringar.hallning`) eller faller tillbaka på SIFT-kameragrupper + 3D-knävinkel (`_geometrisk_reid_och_pose`).
   - Verifierat 100 % identisk roll-, hållnings- och bordsbindning (`vid`) på samtliga 4 klipp (`guacamole`, `gelato`, `asketch`, `notan`) helt utan `deklaration.json`.
2. **Separation av Kamerarörelse från Falsk Rotglidning (`R25_separera_kamerarorelse` i `scen_brygga.py`):**
   - När kameran gör en inåkning eller panorering mot en person som står vid sin plats (t.ex. `gelato S1` där SAM 3D Body lät bäckenet glida `1.09 m` i kameraramen) separerar `R25` lågfrekvent XY-drift (`> 0.18 m`) från kroppen och flyttar över rörelsen till kameranycklar på `CAM_s*` (`statisk = False`). Fötterna står stilla bakom disken i 3D samtidigt som 2D-projektionen har **0 px avvikelse (`IoU = 1.000`)**.
3. **Kontaktkalibrerade Möbler & Underkroppsskydd (`_dra_in_dolda_ben_bakom_massiv_disk` i `scen_brygga.py`):**
   - Bords- och diskskivors höjd (`topp_z`) kalibreras direkt mot 25:e percentilen av skådespelarnas vilande armbågar/handleder i tagningarna där möbeln syns (`0.72–0.96 m`), och skymda höfter/knän hålls utanför diskvolymen så att disken kan visas i `guacamole S2/S3` och `gelato S1` med `G4_genom = 0`.
4. **Frikoppling av Kontaktbundna vs Attitydbärande Leder i Lager 4 (`mening_motor.py`):**
   - `extrahera_attitydprofil` skiljer nu på `attityd_leder` (ryggens 26.4° slappa framåtlutning, nacke, blickfokus, nyckelben) och `kontakt_leder` (`kontakt_armar = True` när underarmarna vilar på bardisken).
   - Vid semantisk ändring från sittande vid bardisken till gående genom lokalen (`ga_med_attityd` på `guacamole`) bevaras hela ryggens och huvudets slappa attityd medan underarmarna frikopplas från bordskanten till en avslappnad armpendling längs sidorna (**0 fel på samtliga grindar G1–G7** på både `guacamole/manip_ga_med_attityd` och `gelato/manip_byt_hand`).



