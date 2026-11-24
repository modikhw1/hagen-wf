# Process: köpa, låna eller bygga rörelse ur video (9 nov 2026)

**Problemet:** den gamla kedjan (MediaPipe-punkter → egen IK och retargeting i three.js → X Bot) ger wobbliga och onaturliga figurer. Varje steg var egenbyggt, och felen staplades på varandra: punkterna jagades i stället för att leden roterades, det fanns ingen städning av rörelsen och ingen ansiktsrigg.

**Princip framåt:** återanvänd färdiga ramverk. Bygg bara limmet mellan dem.

## Kandidater

| Väg | Vad | Kostnad | Lokalt? | Kropp / händer / ansikte | Kommersiellt | Status |
|---|---|---|---|---|---|---|
| **BlendCap** (Blender-tillägg, Arcomade) | Video → rigg i Blender. Retargetar till Rigify, Auto-Rig Pro, CloudRig och Mixamo. Har FK/IK och BVH-efterbehandling (fotglidning). | 60 USD engång | Ja, offline. Har ett läge som bara kräver CPU (långsamt). Cirka 11 GB modeller. | ja / ja / ja | Ja enligt FAQ:n. Kräver godkännande av Metas SAM-licens, så modellen är sannolikt SAM 3D Body. | Behöver köpas (ägaren beslutar) |
| **SAM 3D Body + MHR** (Meta) | Människomesh ur en bild, i den färdiga riggen MHR (skelett, mesh, korrigerande former, ansiktsformer) | Gratis | Kräver i praktiken CUDA; CPU okänt | ja / ja / delvis | MHR har Apache 2.0. SAM-licensen anges som kommersiell men är inte OSI-godkänd. | Spärrad på HF (manuellt godkännande), så den kräver ägarens HF-konto |
| **Molnmocap** (DeepMotion, QuickMagic, Rokoko Vision) | Uppladdad video → FBX | Gratisnivåer, cirka 9–15 USD/mån | Nej, materialet lämnar datorn | ja / delvis / delvis | Ja (betalnivåer) | Behöver konto |
| **Öppen egenbyggd kedja** (Codex C: MediaPipe + MotionBERT + MPFB2/MakeHuman CC0 + egen städning) | Bygg av fria delar | 0 kr plus Codex-tid | Ja, CPU | ja / ja / ja (MPFB2 + ARKit) | Ja om delarna väljs rätt (RTMW-vikterna har kommersiell begränsning) | Pågår, fungerar som jämförelsebas |
| GVHMR / WHAM (SMPL) | Värld- och kamerakorrekt kropp | 0 kr | CUDA | ja / nej / nej | **Nej** (SMPL och GVHMR är icke-kommersiella) | Förkastad |

## Experimentet "rigga före indata"

- **A, retargeting efteråt** (gammalt): en punktmodell jagas med IK på en främmande rigg. Förlust i varje led.
- **B, inbyggd parametrisk rigg:** rörelsemodellen ger direkt parametrar för den rigg figuren använder (MHR eller SMPL-liknande). Ingen retargeting, och proportioner och ansiktsformer hänger ihop. Figurmallar byggs på samma rigg en gång, och sedan byts bara mesh och textur.
- **C, färdig retargeting i verktyget** (BlendCap → Rigify/Mixamo): verktyget sköter mappningen, inklusive FK/IK och fotlåsning.
- **Mått** (samma för alla): återprojektionsfel i px mot 2D-punkter, skakighet, fotglidning, gesttoppar inom ±1 bildruta och en visuell bedömning sida vid sida ("samma framträdande?").

## Kamera

Blenders inbyggda camera solver (libmv) är gratis och lokal, med personen maskad med YOLO-seg. Första lösningen gav 3,9 px fel med en lucka i bildrutorna 31–60. Tätare detektering pågår, och målet är under 1 px.

## Processlärdomar (löpande)

- **MCP-anrop som tar mer än ~2 min får timeout**, men Blender fortsätter köra. Dela tunga steg i korta anrop (`kamera_track.py` är byggt så) och spara tillståndet i `bpy.app.driver_namespace`.
- **Lös inte kameran med fler än ~300 spår.** Buntjusteringen och valet av nyckelrutor i libmv körs på en kärna. Med 1 243 spår tog lösningen över 15 min (första lösningen, 202 spår, tog 12 s). Standard är därför cirka 25 välfördelade och långa spår per 15-rutefönster, med ett tak på cirka 300.
- **Spara .blend före långa operationer**, så att en kraschad eller hängd GUI inte tar med sig trackingen.
- **Dubbelarbete:** Codex C började bygga en egen reservlösning för kameran när `kamera.json` dröjde. Lägg delade beroenden först, eller låt en part äga dem.
- **Fråga om licenser i förväg.** Codex C stannade på frågan om RTMW-vikterna (kommersiell begränsning) i ett läge där den inte kunde få svar. Uppdragstexten ska säga vad som gäller, till exempel "forskningsjämförelse tillåten, märk som ej kommersiellt godkänd".
- **Kamera: COLMAP (pycolmap 4.2, BSD) med standardinställningar slog handtrimmat libmv.** På 122 bildrutor (var tredje, 540×960, personen maskad) registrerades 119 med 1,02 px återprojektionsfel och 1 758 punkter, på 6 min och utan trimning. Libmv gav som bäst 2,6 px efter en timmes trimning, och var instabilt (17–188 px vid omlösning). **Beslut:** COLMAP är standardverktyget för kameran, och Blender importerar resultatet. Libmv används bara för snabba fall med stativ eller enkel panorering.

## Resultat av experimentet "rigga före indata" (9 nov kväll)

- **SAM 3D Body (ViT-H) + MHR fungerade** efter ett par CPU-patchar i Metas kod (hårdkodade `.cuda()`). Detectron2 behövs inte, eftersom personrutan kommer från YOLO och kamerans fokal från COLMAP.
- Utdata per bildruta: 127 globala ledställningar, 18 439 hörn, 72 uttryckskoefficienter, 45 formparametrar och 108 handparametrar.
- **MHR:s egna FBX-filer (`lod3.fbx`, Apache 2.0) har exakt samma 127 leder i samma ordning** (föräldrastrukturen är identisk). Rörelsen sätts därför direkt på riggen, utan retargeting och utan IK: en spegling (kamerarummet = diag(1, −1, −1) · modellrummet), cm → m och en konstant korrigering per ben från viloläget. Ledfelet är 0 mm.
- Bildruta 150, renderad genom SAM 3D Bodys kamera (2 154 px, vilket stämmer med COLMAP:s 1 077 px vid halv upplösning): kroppen, gesten, hållningen och huvudet ligger på källan, och figuren ser ut som en människa. Se `sam3db/jamfor_150.jpg`.
- **Flaskhalsen är CPU:n:** 592 s per bildruta (med Blender som konkurrerade om CPU). Hela klippet tar cirka 60 h, eller cirka 10–20 h för var tredje bildruta. På GPU tar det cirka 0,3 s per bildruta. **Beslut som behövs:** GPU-hyra (under 1 USD för klippet) eller CPU över natten (gratis, pågår: `sam3db/kor_alla.py`, kan återupptas, grovt till fint).
- **Slutsats:** ett färdigt ramverk (SAM 3D Body + MHR) med inbyggd rigg ersätter det mesta av vår egen kedja (MediaPipe → IK → X Bot) och det Codex C byggde (MediaPipe + MotionBERT + retargeting till MPFB2). Det egna arbetet krymper till lim och tidsutjämning.

## Genombrott (9 nov 18:15): hela klippet via SAM 3D Body + MHR på Modal

- **Modal (L4 med reservlista över GPU-typer):** 365 bildrutor på 123 s, 0,86–1,7 s per bildruta och container, parallellt. GPU och CPU stämmer inom 1,5 px (median). Container-start: 10 s. Checkpointen cachas i volymen `sam3db-vikter` och HF-token i secreten `huggingface`. Pending-läget första gången berodde på `gpu='L4'` utan reserv.
- **Skelettsekvens** (`sam3db/skelett_sekvens.py`): identiteten låses till medianens formparametrar, och 4 svarta rutor fylls med slerp. Skakigheten är 0,76 cm/ruta² i median (p95 1,85).
- **Blender** (`scen/3d/blender/mhr_blender.py`): import 0,5 s, nyckling av 369 bildrutor × 126 ben på 25 s (`matrix_basis` räknas direkt, utan uppdatering av scenen per ben) och Workbench-rendering på 49 s.
- **Resultat:** `jamforelse_mhr.mp4` (källa | överlägg | rendering, originalljud) och `ark_mhr.jpg`. Gesterna (klapp, öppna handflator, händer som möts), gången och huvudet följer källan genom hela klippet, utan wobbel.
- **Total tid för ett nytt klipp:** cirka 4 min (plus 6 min för COLMAP-kameran). Tidigare tog det timmar, med sämre resultat.

### Nästa steg (lim, inget nytt hjul)
1. **Världsplacering:** COLMAP-kamerans bana × SAM 3D Bodys person i kamerarummet → personen och kameran i samma värld, med skalan från kroppens meterskala. Det ger fri kamera och ett rum att bygga i.
2. **Ansikte:** 72 uttryckskoefficienter → FBX-riggens shape keys, eller MHR-mesh med uttryck.
3. **Rum:** COLMAP:s 1 758 punkter → golv och vägg, med biljardbord som lådor.
4. **Figurmallar:** samma MHR-rigg med andra mesher eller kläder. Rörelsen behöver inte göras om.
5. Tidsutjämning bara om det behövs. Den måste bevara gesttopparna (±1 bildruta).

## Världsläge (9 nov 18:25)
- `varld.py`: COLMAP-kameran (119 rutor, slerp däremellan) och SAM 3D Bodys person i kamerarummet hamnar i en metrisk värld. Skalan k = 0,117 väljs så att personens rotbana blir jämnast (0,5 cm/ruta²), och gravitationen tas från ryggens riktning. Kameran backar 1,64 m, och personen går 1,64 m.
- `mhr_blender.varld` + `nyckla_varld`: kameran och personen nycklas i samma värld (25 s). Genom den trackade kameran ligger resultatet på källan (`varld_overlay.jpg`), och från en fri vinkel hänger världen ihop: golvet under fötterna och kameran cirka 1,5 m upp. Se `mhr_varld.blend`.

## Sammanfattning av processbytet
| | Före (lördag–9 nov förmiddag) | Nu |
|---|---|---|
| Rörelse | MediaPipe-punkter → egen IK i three.js → X Bot (wobbligt) | SAM 3D Body → MHR-riggen direkt (ingen retargeting) |
| Kamera | PnP per tagning (statisk) / libmv för hand | COLMAP, standardinställningar, rörlig kamera i metrisk värld |
| Beräkning | CPU, timmar | Modal-GPU, 2 min per klipp |
| Eget kod | IK, stabilisering, ansiktsellipsoider, retargeting | Lim: spegling, korrigering per ben, skala och gravitation |
| Nästa steg | – | Codex D (startar 20.59): ett kommando per klipp, ansiktsformer, rum ur COLMAP-punkter, två personer (barklippet) |

## Replikerbarhet (9 nov 19:00): `scen/3d/ingest/ingest_klipp.py`
- Ett kommando kör hela kedjan med cache per steg. Testat på ett andra, okänt klipp (bar, två personer, rörlig kamera): cirka 6 min från noll, 1 min med cache. Se `scen/3d/ingest/README.md`.
- Problem som fångades och rättades under körningen:
  1. ByteTrack gav 8 ID:n för 2 personer. BoT-SORT med ReID (inbyggt) plus sammanslagning av fragment gav 2 stabila ID:n.
  2. Cachen återanvände kroppsresultat med gamla ID:n. Nu rensar en omkörning allt efter steget.
  3. Rotdjupet skakade när underkroppen var skymd (6,7 cm/ruta²). Utjämning utan tidsförskjutning gav 0,93.
- **Ansiktsuttryck (studie av @unemployed_corp, `unemployed_corp/uttryck/ark.jpg`):** uttrycken är regisserade arketyper som hålls per takt (självbelåtet, stolt, uttråkat), inte uppmätt mikrorörelse. Vårt lager blir därför mät → tolka → förstärk, och resultatet hamnar både i blockouten och som regi i prompten. Byggs av Codex D.
- **Regression (19:10):** biljardklippet från noll med `ingest_klipp.py`: 388 s, 119/122 kamerarutor med 0,81 px, ojämnhet 0,085 cm/ruta², och renderingen ligger på källan.
- **Känd instabilitet:** COLMAP:s fokal varierar mellan körningar (1 658 mot 2 154 px för samma klipp), eftersom SIMPLE_RADIAL-fokalen är svagt bestämd vid liten parallax. Överlägget påverkas inte (SAM 3D Body kompenserar med djupet), men världsskalan och djupet gör det. Åtgärd att pröva: korskontroll mot SAM 3D Bodys egen FOV-uppskattning (MoGe-modulen) eller mot mobilens typiska bildvinkel, eller fokalen låst över fler rutor.

## Stabilitet och skymning (9 nov 19:25), efter ägarens kritik: ingen säkring mellan rörelser, figurer flyger bakom bardisken, rummet saknas
- **`sekvens` är ombyggt** (`ingest/sekvens_stabil.py`, i MHR:s parameterrum innan skelettet räknas fram):
  - identiteten låst;
  - roten uträtad (np.unwrap);
  - Hampel-filter (±4 rutor, 3·MAD) som byter ut trasiga rutor (en person sedd bakifrån blev upp och ner). Benen och händerna räknas inte in i bedömningen;
  - skymda ben (inget knä i bild och inom personmasken) hålls från närmaste synliga ruta, eller blir stående (0) om de aldrig syns;
  - Butterworth utan tidsförskjutning: 6 Hz för kroppen, 8 Hz för händerna och ansiktet.

  Parameternamnen (204) är tolkade ur `compact_v6_1.model` och verifierade genom störning (`l_knee_bend` → led 3 osv.).
- **Nytt steg `golv`:** personen flyttas längs kamerans siktlinje (cam_t·s; utsnittet ändras inte) tills lägsta foten står på golvet, och s utjämnas (1,5 Hz). Golvet tas från synliga fötter, och annars från antagen kamerahöjd 1,45 m. I biljardklippet mättes kamerahöjden till 1,42 m, vilket bekräftar antagandet. Foten mot golvet (90:e percentilen): biljard 0,6 cm, bar 3,4 cm. Bakom bardisken står figurerna nu stilla på golvet i stället för att flyga.
- **Regression som fångades:** kriteriet "3 av 4 knän och vrister synliga" slog ut gången i biljardklippet, eftersom vristerna är beskurna. Nu räcker det att knäna syns.
- **Rummet och minimimåtten** (väggavstånd, bord, storlek och avstånd till personen) ligger hos Codex D. Uppdraget gäller bara det och startar 20.59. Uttryck och Seedance väntar tills förrenderingen är stabil.

## Spärrar, rotfix och fotkontakt (9 nov 20:40)
Se `scen/3d/ingest/README.md`, avsnittet "Spärrar och tyngd". Kort sagt: `vakt.py` mäter och `sekvens_stabil.py` har fått en kvaternionrot (vår Euler-utjämning orsakade flipparna), vridfartgräns och tillförlitlighetsgrind. `cam_t` delas i siktlinje och avstånd. `kontakt.py` gör fotkontakt med analytisk IK. Mätt före och efter på bar och biljard; maskprompt och SAM-Body4D är förkastade och motiverade där.
