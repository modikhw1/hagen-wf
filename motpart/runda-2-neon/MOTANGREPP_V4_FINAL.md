# MOTANGREPP V4 (SLUTPAKET TILL OPUS RUNDA 3) — Intentionalitet på `0..1`-skalan, Verkliga Virtuella Sensorer, 49-videors Destillation (`v1→v3.2`) & Blind-Agent-Konvergens i Blender 5.2 (`v6→v7`)

19 nov 2026. Komplett slutpaket i `motpart/runda-2-neon/`, redo att lämnas direkt till Opus i Runda 3. **0 filer utanför `motpart/runda-2-neon/` är rörda.** Samtliga 7 experiment nedan är körda på repots riktiga data (49 unika TikTok-videor från 6 riktiga restauranger, 11 verkliga genererade GPT-Image/Gemini virtuell-sensor-bilder varav samtliga nya Codex-anrop verifierade med `hel: true`, 3 helt blinda subagenter och 4 huvudlösa Blender 5.2-renderingar). Alla bilder är visuellt granskade och alla svagheter/regressioner redovisas öppet.

---

## 0. Helhetsöversikt — De 7 körda bevisen som fäller Opus Runda 1-paradigm

| Exp | Fråga som besvarades | Körd metod & datamängd | Hårdaste uppmätta utfall | Visuellt granskad bild + data |
|---|---|---|---|---|
| **Exp 1** | Stämde Argons, Opus eller vår egen Runda 2-rumsanalys mot fysisk verklighet? | Oberoende fysiska standardankare direkt i pixlarna (`0 %` SAM/MoGe): fokalfri bordsratio, 33 cl Bonaqua, 750 ml flaska, GN 1/3 glasskantin, M21-dörr | **0 av 5 rätt i gamla paradigmet:** `notan` fokal `+39,3 %` teleinflation (`3,53 m` mot GT `2,30 m`) och tak `-0,88 m`; `guacamole` missade tvånivåsbaren (`0,77 m` mot `1,11 m`); `gelato` Opus P2-kamera **`0,711 m` inuti disken**; `asketch` kollapsad till `2,50 × 2,50 m`. | [djup_gt_bevis.png](djup_gt_bevis.png) · [JSON](djup_ground_truth_audit.json) |
| **Exp 2** | Kan flera klipp från samma kund bygga ett växande `LokalMinne` och amortera ingest-tiden? | Tvåstegs Hybrid `LokalMinne` (`YOLO11n-seg` + offline `CLIP ViT-B-32` + `RootSIFT/USAC_MAGSAC`) på 24 riktiga TikToks (3 restauranger) + `3 447` korspar | **`0,00 %` Z1-FPR / `0,203 %` Z2-FPR**, klättrar `50 % → 60,7–73,4 %` med ärliga platåer på mat-/köks-/hemmaklipp, **~45× snabbare varm CPU-relokalisering (`6,6 s` vs `300 s`)**. Upptäckte ärligt **takeaway-påsefällan** ([check_cs_v2.jpg](djup_gt_ramar/check_cs_v2.jpg)). | [djup_lokal_minne_v2_bevis.png](djup_lokal_minne_v2_bevis.png) · [JSON](djup_lokal_minne_v2.json) |
| **Exp 3** | Hur bryter man `24°`-röret, hanterar osynliga väggar och kroppar som lämnar scenen? | Bildproxy `λ = 1,0×→2,5×`, `K=3` epistemisk 3-zonslösare + 2 felinjektioner, `YOLO11n-pose` på `5 330` riktiga person-rutor | Knivskarp fasövergång vid **`λ = 1,8×`**; `K=3` dödar enstaka `+2,4 m` hallucination (`1,84→0,05 m`); Klipp #2 kör över delad 3-frö-bias med **`-91,1 %`**; **`99,8 %` av 5 330 riktiga TikTok-rutor saknar synlig helkropp!** | [djup_epistemisk_geometri.png](djup_epistemisk_geometri.png) · [JSON](djup_extremitet_och_okunskap.json) |
| **Exp 4** | Fungerar ägarens 2-bilds virtuella djupsensor och tvärmodell-extremiteter på riktiga pixlar? | 5 verkliga genereringar på `guacamole` (Steg A tom scen, Steg B GPT Image Turbo-djup, Gemini + GPT `1,8×` extremiteter) mätta mot verklig `MoGe` & hold-out `S3/S4` | Steg A drift **`1,17 px`**, 2-bilds diff-SNR **`8,01×`**; GPT Turbo-djup har **`0 %` hål** (MoGe `24,5 %` NaN-hål + felvänt tak!), **`97,4 %` kantalignering** och **`2,32×` skarpare barsteg**; vrister **`0,005 → 0,970`** (`0→100 %` golvkontakt!); barhöjd ur B = **`0,87 / 1,11 m`** (exakt!). | [djup_v4_komplett_bevis.png](djup_v4_komplett_bevis.png) · [djup_v4_sensor_bevis.png](djup_v4_sensor_bevis.png) · [JSON](djup_v4_full_sensor_audit.json) |
| **Exp 5 + 5B** | Kan `N`-klipps-serien ge `GT_N` så vi optimerar `v1→v2→v3→v3.1→v3.2` att behöva färre klipp? | **49 unika riktiga TikToks från 6 restauranger** (`215` tagningar, `2 141` rutor), `19 164` kors-restaurang CLIP-par, `6 388` RANSAC-par, 5 slumpordningar | **`44,7 %` (`958/2 141`) av råa rutor avvisas av rörelseoskärpegrinden** före img-gen; **`v3.1` slår både `v1` och `v2` monotont** (`AUC 5,9→15,8→19,6 %`, `k=7: 21,7→46,8→57,4 %`, `20,8 %` slipper img-gen) vid **`0 / 6 388` Z1-FP**, **`0,153 %` Z2-FPR** (lägre än `v2`!) och **`0` påselänkar**! Ärlig varning för `v3.2` korrelerad röstning (`4,26 %` FPR). | [djup_v31_destillation_bevis.png](djup_v31_destillation_bevis.png) · [djup_v1_v2_v3_bevis.png](djup_v1_v2_v3_bevis.png) · [JSON](djup_v31_destillation.json) |
| **Exp 6** | Vad är optimal `0..1`-prompt & trade-off mellan *Naken Zero-LLM* vs *Regisserad* för RoomAnalysis vs Seedance? | 6 verkliga Codex GPT-Image-anrop (`6/6 hel=True`) över **både `guacamole` (bar) och `gelato` (glassbar)** + generalisering av 2-bilds djupkarta till genomskinlig glassmonter | Exakt `0..1`-Paretofront uppmätt: `0.35` Regi RoomAnalysis kapar brus **`-60 %`** (`7,9×` renare arkitekturlinjer), `0.45` **Naken Zero-LLM** når chockerande **`81–100 %`** lokalidentitet utan LLM-steg, `0.55` Regi Prod ger **`96 %`** identitet & `2,25 px` lås; **`gelato` 2-bilds djupkarta** har **`0 %` hål** (MoGe `15,1 %` NaN!), **`99,2 %` kantpassning** och **`4,53×` skarpare glaskant**! | [djup_v5_prompt_ab_bevis.png](djup_v5_prompt_ab_bevis.png) · [JSON](djup_v5_prompt_audit.json) |
| **Exp 7** | Kan en helt blind agent återskapa verklig 3D-lokal med vår regelpipe och konvergera `v6 → v7`? | **3 helt blinda subagenter** (`Blind A` råbild, `Blind B` Regelpipe `v6`, `Blind C` Regelpipe `v7`) + **4 verkliga Blender 5.2-renderingar** mot dolt fysiskt facit | Monoton felfallskurva på 7 fysiska mått: **Opus `29,7 cm` (MAX `67 cm`) → Argon `21,0 cm` → Blind A `11,1 cm` → Blind B (`v6`) `9,9 cm` → Blind C (`v7`) `4,1 cm` (`-86,2 %` mot Opus, MAX `16 cm`, `0,0°` vFOV-fel!)** + **Blind C fångade autonomt `4/4` generativa hallucinationer** (inkl. spegelreflekterade spökkantiner i glaset!). | [djup_blind_blender_bevis.png](djup_blind_blender_bevis.png) · [JSON](djup_blind_konvergens.json) |

---

## 1. Experiment 6 — `0..1`-skalan, Intentionalitet & Naken (Zero-LLM) vs Regisserad Trade-off

Repots egen förankring för `0..1`-abstraktionen sitter i [scen/3d/PIPE.md](../../scen/3d/PIPE.md#L41-L44) (*bär / sätter / stryks*), [delegat/bilagor/0025/agarens-lasning.md](../../delegat/bilagor/0025/agarens-lasning.md) (*"Meningen ska lysa igenom utan all detalj"*), [scen/3d/gennedbrytning/relevans/RELEVANS.md](../../scen/3d/gennedbrytning/relevans/RELEVANS.md) och [scen/3d/lasformat/luma-paket/README.md](../../scen/3d/lasformat/luma-paket/README.md#L50-L53) (*`naken`* vs *`regisserad`*).

Det avgörande strategiska misstaget i tidigare körningar var att skicka **samma** bildprompt utan tydlig **intentionalitet** för vad nästa steg i pipen faktiskt behöver. I [djup_v5_prompt_ab.py](djup_v5_prompt_ab.py) och [djup_v5_prompt_audit.py](djup_v5_prompt_audit.py) testade vi båda rutterna och båda intentionaliteterna på **både bardisk (`guacamole S4`) och glassbar (`gelato S1`)** med `6/6` verifierade `hel: true` Codex GPT-Image-anrop ([djup_v5_prompt_ab_bevis.png](djup_v5_prompt_ab_bevis.png)):

### 1.1 Uppmätt `0..1`-Paretofront (objektiva maskinmått, noll tyckande)

| Lokal & variant (`0..1`-nivå) | Kantbrus (`Canny %`) | Brusreduktion mot `1.0` | Långa arkitekturlinjer (`>= 45 px`, LSD) | Pixel-lås (drift px) | CLIP `P(rätt lokal)` | CLIP `P(tom låda)` | CLIP `P(klotter/text)` | Rätt användningsfall i LeTrend |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`guac` 1.0 (Råbild)** | `9,9 %` | `0 %` | `6,9 %` | `0,0` | `0,015` | `0,000` | **`0,984`** | Endast sanningsskydd & ansikts-/matpixlar |
| **`guac` Regi `0.35` (RoomAnalysis)** | **`3,9 %`** | **`-60,6 %`** | **`54,3 %`** *(7,9×!)* | *(matt yta → kantlås)* | `0,110` | **`0,885`** | `0,000` | **Intentionalitet I (`RoomAnalysis`):** renast tänkbara CAD-plan för djup/planpassning — *men* för avskalad för Seedance! |
| **`guac` Naken `0.45` (Zero-LLM!)** | `4,8 %` | `-51,5 %` | `37,4 %` *(5,4×)* | *(matt yta)* | **`0,809`** | `0,009` | `0,000` | **Bästa Zero-LLM-kompromiss!** Ingen LLM-kostnad före; behöll tvånivåsbaren autonomt, städade kablar/kvitton! |
| **`guac` Regi `0.55` (Produktion)** | `7,7 %` | `-22,2 %` | `15,5 %` *(2,2×)* | **`2,25 px`** | **`0,962`** | `0,000` | `0,000` | **Intentionalitet II (`Good-Enough` / Seedance):** omisskännligt kundens bar utan skräp, redo för animering! |
| **`gelato` 1.0 (Råbild)** | `6,8 %` | `0 %` | `15,0 %` | `0,0` | `0,997` | `0,000` | `0,003` | — |
| **`gelato` Naken `0.45` (Zero-LLM!)** | `7,5 %` | `+10 %` *(glassvirvlar kvar)* | `34,1 %` *(2,3×)* | **`2,26 px`** | **`1,000`** | `0,000` | `0,000` | Fungerar autonomt men lämnade halvätna glassvirvlar & hittade på gasspis bakom personal! |
| **`gelato` Regi `0.40` (RoomAnalysis)** | **`5,2 %`** | **`-23,5 %`** | **`52,8 %`** *(3,5×)* | *(matt yta)* | **`0,998`** | `0,000` | `0,000` | **Exakt `0.40` Sweet Spot:** prydliga pastellkantiner + knivskarp glasmonter = tydlig glassdisk utan visuellt brus! |

### 1.2 Generalisering av 2-bilds Virtuell Djupsensor till genomskinlig glassmonter (`gelato S1`)
Tidigare kunde en skeptiker (Opus) hävda att vår 2-bilds Turbo-djupkarta bara fungerade på en ogenomskinlig bardisk (`guacamole`). Vi körde exakt samma 2-bildsmetod på **en kraftigt reflekterande glassmonter i glas** ([v5_gelato_regi_05_djup.png](djup_v5_prompt_ab/v5_gelato_regi_05_djup.png)) och mätte mot Argons verkliga `MoGe` (`kand-kennysgelato-tagningar/S1/rum/depth/0078.npz`):
- **Argons `MoGe`:** **`15,1 %` NaN/inf-hål** rakt genom glaset och suddig glaskant (`p98 = 0,0121`), vilket drar ned Spearman-korrelationen till `0,265` eftersom monokulär `MoGe` förväxlar spegelreflektioner i glaset med glasskantinerna.
- **GPT Image 2-bilds Virtuell Djupsensor:** **`0,0 %` hål**, **`99,2 %` Canny-kantalignering** mot den städade scenen och **`4,53×` skarpare horisontell glaskant (`p98 = 0,0549`)** med tydlig djupseparering mellan varje enskild GN 1/3-kantin, nyskyddshyllan och bakre arbetsbänken!

### 1.3 Ärlig dom om Trade-offen: *Naken (Zero-LLM)* vs *Regisserad (LLM-brief)*
- **Rutt A (`Naken 0.45` Zero-LLM)** överraskade kraftigt: en enda lokal-agnostisk prompt utan förgående LLM klarade **både** att behålla tvånivåsbaren i `guacamole` (`P(bar) = 0,81`, `-52 %` brus) och glasmontern i `gelato` (`P(glassdisk) = 1,00`, `2,26 px` drift). **Rekommenderad standard för bulk-ingest i steg 1** där hastighet och enkelhet styr!
- **Rutt B (`Regisserad 0.35 / 0.55`)** slår `Naken` markant när man vill ha **extrem planrenhet** (`54 %` långa linjer i `0.35` för `RoomAnalysis`) eller **varumärkes-/lokaltrohet** (`96 %` identitet i `0.55` för Seedance-produktion) — och tar bort glasskladd som `Naken` lämnade kvar.
- **Gemensam svaghet som *båda* rutterna lider av:** I utrymmet som tidigare skymdes bakom en borttagen person (bakom personalen i `gelato S1`) hittar img-gen på troliga men falska prylar (en 4-lågors gasspis + köksfläkt i en glassbar!), och i `guac 0.35` stängde den kundsidan med en platt vägg. **Därför är vår Regel 6 (korskontroll mot råbilden + `Z1/Z2/Z3`-märkning) obligatorisk oavsett prompt!**

---

## 2. Experiment 5B — Komplett 49-videors Destillationsloop (`v1 → v2 → v3.1 → v3.2`)

Efter att Experiment 5 avslöjade `v3`:s övermaskningsbugg (där `YOLOWorld` råkade maskera fasta menytavlor i `anettesrestaurang` och bakbarsflaskor i `babulsofficial`) byggde och körde vi hela **`v3.1` + `v3.2`** över **alla 49 unika TikTok-videor (6 restauranger, 19 164 kors-restaurangpar, 5 slumpordningar)** i [djup_v31_49vid_bevis.py](djup_v31_49vid_bevis.py) ([djup_v31_destillation_bevis.png](djup_v31_destillation_bevis.png)):

| Generation | Vad som ändrades | Z1 FP (`6 388` korspar) | Z2 FPR (`19 164` korspar) | Falska hemma-länkar (`K#2`) | `AUC` (`k=1..7`) | `R_gt` vid `k=7` | Slipper img-gen `k >= 4` | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **`v1`** | Ren RootSIFT + personmask | **0** | — | 0 | `5,9 %` | `21,7 %` | `7,0 %` | Baslinje |
| **`v2`** | + Hybrid CLIP + COCO-80 | **0** | `0,157 %` | 0 | `15,8 %` | `46,8 %` | `17,8 %` | Bra steg |
| **`v3`** *(Exp 5)* | + Suddgrind + oskyddad `YOLOWorld` | **0** | `0,163 %` | 0 | `13,1 %` *(regression!)* | `38,9 %` | `10,1 %` | **Fångad av `GT_N`!** |
| **`v3.1`** *(Exp 5B)* | **Fix:** nedre-förgrunds `YOLOWorld` (`y>40%`) + Dual-CLIP | **0** | **`0,153 %`** *(lägst!)* | **0** | **`19,6 %`** *(3,3× `v1`!)* | **`57,4 %`** | **`20,8 %`** | **SÄKER PRODUKTIONSVINNARE** |
| **`v3.2`** *(Exp 5B)* | + 2-klipps flervyröstning vid `p99.2` | **0** | **`4,257 %`** *(för hög!)* | `1` | `30,7 %` | `78,3 %` | `31,3 %` | **Kräver Z1/djup-veto** (visar att mörka restauranger bryter oberoende-antagandet i CLIP!) |

**Tre avgörande insikter ur 49-videorsloopen:**
1. **`v3.1` slår ut både `v1` och `v2` monotont i varje enskilt steg `k = 1..7` vid *lägre* FPR (`0,153 %` vs `0,157 %`)** — och når på `k=6` (`34,0 %`) högre täckning än `v1` når efter 7+ klipp (`21,7 %`) och lyfter `anettesrestaurang` (`0 → 71,4 %`), `babulsofficial` (`0 → 57,9 %`), `blackstonesteakhouse` (`57,1 → 71,4 %`), `fratelli` (`54,2 → 66,7 %`) och `chickenstreet` (`56,2 → 68,8 %`).
2. **Rörelseoskärpegrinden sorterar bort `44,7 %` (`958/2 141`) av råa TikTok-rutor** innan en enda krona img-gen körs.
3. **Nattklubbs-/mörkerkänslighet (`blubnan.liljeholm`):** Vid 6-restaurangers ultrastrikta globala `p99.85`-tröskel (`0,9175`) och 6 tagningar/klipp föll `blubnan` precis under tröskeln (`0,905–0,916`), medan 7 tagningar/klipp i Exp 2 låste skogstapeten med 28 F-inliers — vilket visar att adaptiv tagningstäthet (`6–10` ankare vid mörka klipp) hör hemma i nästa iteration (`v3.3`).

---

## 3. Experiment 7 — Verklig Blind-Agent-Konvergensloop (`Råbild → v6 → v7`) i Blender 5.2

För att testa ägarens slutgiltiga sanningsprov — *"kan vi blint ge en annan agent vår regelpipe och iterera tills rekonstruktionen liknar vår optimerade version?"* — körde vi **tre helt fristående, lässkyddade blinda subagenter** (utan tillgång till någon rapport eller facit) på `guacamole_S4` + `gelato_S1` och renderade resultaten direkt i **Blender 5.2** ([djup_blind_eval.py](djup_blind_eval.py), [djup_blender_scen_render.py](djup_blender_scen_render.py), **[djup_blind_blender_bevis.png](djup_blind_blender_bevis.png)**):

| System (alla utvärderade mot samma 7 fysiska mått) | `guac` arbetsbänk (`0,90 m`) | `guac` kopparbar (`1,11 m`) | `guac` barstol (`0,75 m`) | `guac` A↔B (`1,73 m`) | `gelato` kantin (`0,88 m`) | `gelato` glas (`1,20 m`) | `gelato` kam (`1,38 m`) | **MAE (cm)** | **MAX (cm)** | `gel` vFOV-fel | Fångade img-gen-halluc. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Argon (`forvarld_karna`)** | `0,78` | `0,78` | `0,45` | `1,73` | `0,72` | `0,72` | `1,30` | **`21,0 cm`** | `48 cm` | `1,0°` | `0` |
| **Opus R1 (`RUM` / `P2`)** | `0,77` | `0,77` | `0,45` | `1,73` | `0,72` | `0,72` | **`0,711`** | **`29,7 cm`** | **`67 cm`** | `1,0°` | `0` |
| **Blind A (Enbart råbild)** | `0,88` | `1,13` | `0,75` | `1,25` | `0,90` | `1,31` | `1,51` | `11,1 cm` | `48 cm` | `15,0°` | `0` |
| **Blind B (`Regelpipe v6` + sensorer)** | **`0,90`** | **`1,10`** | **`0,75`** | `1,25` | `0,95` | `1,26` | `1,45` | `9,9 cm` | `48 cm` | `3,0°` | `0` *(svalde gasspis!)* |
| **Blind C (`Regelpipe v7` + Regel 5–7)** | **`0,89`** | **`1,14`** | **`0,78`** | **`1,57`** | **`0,88`** | **`1,22`** | **`1,42`** | **`4,1 cm`** *(**-86,2 %** vs Opus!)* | **`16 cm`** | **`0,0°`** | **`4 / 4` fångade!** |

**Det som hände i `v6 → v7`-iterationen bevisar kraften i generella regler (0 klippspecifik kod):**
- **`Regel 5` (3D-diagonal `sqrt(tvärs² + längs²)` i stället för bara disktjocklek):** flyttade `guacamole A↔B` från `1,25 m` till **`1,57 m`** (kapade felet med `67 %`).
- **`Regel 6` (Korskontrollera RoomAnalysis mot råbilden — förkasta nyuppdykande prylar i skymda zoner):** gjorde att den helt blinda agenten `Blind C` **autonomt identifierade och förkastade 4 av 4 verkliga generativa hallucinationer**:
  1. den påhittade **4-lågors gasspisen** bakom personalen i `gelato`,
  2. den påhittade **köksfläkten** som ersatte polkagrisarna i `gelato`,
  3. **extra raden spök-glasskantiner till höger i `gelato`** (som GPT Image råkade tolka som riktiga kantiner ur en **spegelreflektion i sidoglaset** — en subtil fälla som inte ens stod i vår prompt!), och
  4. den **falska krämvita väggen** som `guac 0.35` slöt kundsidan med (avslöjad genom att jämföra mot råbilden + djupblå Turbo-djupkarta!).
- **`Regel 7` (Kanonisk `+Y_cam`-väggnamngivning + `Zon 3` öppna horisonter):** eliminerade namngivningskonflikten mellan `Blind A` och `Blind B` och tog bort alla påhittade slutna lådväggar i Blender 5.2 ([djup_blind_blender_bevis.png](djup_blind_blender_bevis.png) Panel 1–4).

---

## 4. Formell utmaning till Opus i Runda 3 (Falsifieringsvillkor `V1–V7`)

Vi lämnar detta paket till Opus utan ett enda ord säljsnack — bara körbara skript, JSON-filer, visuellt granskade bilder och falsifierbara påståenden. Om Opus vill slå tillbaka i Runda 3 räcker det inte att leta decimalbuggar i gamla `forvarld_karna/`; Opus måste falsifiera eller slå oss på:

1. **`V1` (Fysisk skala):** Bygg en helautomatisk skalvakt som slår `4,1 cm` MAE över `notan`/`guacamole`/`gelato` utan att hårdkoda klippnamn eller `f=984 px`.
2. **`V2` (49-videors `LokalMinne`):** Slå `v3.1`:s `AUC = 19,6 %` / `k=7 = 57,4 %` över samma 6 restauranger och 5 slumpordningar **vid `0 / 6 388` Z1-FP, `<= 0,15 %` Z2-FPR och `0` påselänkar på `chickenstreet K#2`** (och bevisa ett säkert geometriskt veto för `v3.2` så dess `4,26 %` FPR faller under `0,2 %`).
3. **`V3` (Virtuell Djupsensor vs Monokulärt djup):** Visa en ren monokulär djupmodell (utan 2-bilds negativ borttagning) som slår GPT Images **`0 %` hål, `97,4–99,2 %` kantalignering och `2,3×–4,5×` skarpare möbelsteg** på både `guacamole S4` och `gelato S1`.
4. **`V4` (Tvärmodell-djupkonsensus):** Kör Steg B-djupkartan på *både* Gemini `S1_ext_s1` och GPT `S1_ext_s2` och mät om djup-/plan-variansen ($\sigma_{\text{depth}}$) skarpt skiljer `Z2` (tvånivåsbar + barstol) från `Z3` (matsal vs tequilavalv) där rå RGB-varians föll.
5. **`V5` (Blind konvergens på hold-out `notan` + `asketch` + `b-tilltal`):** Testa vår exakta `Regelpipe v7` på en ny blind agent över de övriga 3 klippen (`notan`, `asketch`, `b-tilltal`) för att verifiera att `v7` generaliserar utan överanpassning till `guacamole`/`gelato`.
6. **`V6` (Intentionalitetsstyrning i produktion):** Pröva `v5_guac_regi_06_prod.png` (`0.55`) vs `v5_guac_naken_04.png` (`0.45`) som faktisk referensbild in i Seedance/Blender — vilken ger bäst balans mellan semantisk redigerbarhet, originaltrohet och noll LLM-overhead?
7. **`V7` (Kroppslivscykel):** Implementera 4-stegs livscykel (`Hel / Del / Hand+2D-mediaplan / Object Permanence`) i `scen_brygga` så att de `99,8 %` icke-helkroppsrutorna hanteras utan spökbålar eller svävande fötter.
