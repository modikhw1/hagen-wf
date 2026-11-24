# Licensrevy: rum, objekt och tillgångar (2026-11-11)

Kommersiell produkt (klipp åt restauranger, caféer, barer). Förvärld per klipp i Blender. Allt som har en käll-URL är läst i primärkälla (HF-modellkort, LICENSE-fil, officiell sida) vid revyn. "Bedömning" är min tolkning. Det som inte gick att läsa är markerat **ej verifierat**. Inget juridiskt utlåtande.

## 0. Tre fällor som gäller flera verktyg
1. **Vikt-licens skiljer sig från kod-licens.** MIT-kod kan ha CC-BY-NC-vikter (SpatialLM, Pi3, DA3 Large). Läs alltid modellkortet.
2. **Träningsdata.** TRELLIS-500K är kuraterad från Objaverse(XL), ABO, 3D-FUTURE, HSSD och Toys4k (TRELLIS README). Avtalet för 3D-FRONT/3D-FUTURE säger "scientific research purpose only" och förbjuder kommersialisering samt att använda resultat för "providing external services" (se avsnitt 4). Modellkortet för TRELLIS säger MIT och nämner inte datalicenserna. **Bedömning:** juridiskt grått. Gäller alla modeller tränade på dessa set.
3. **Geografi.** Hunyuan3D gäller inte i EU, UK, Sydkorea (avsnitt 2).

## 1. Rum- och scenförståelse

| Verktyg | Gör | Kod | Vikter | Källa | Anseende | Passar oss |
|---|---|---|---|---|---|---|
| MoGe / MoGe-2 | Monokulär punktkarta; MoGe-2 ger metrisk skala | MIT (DINOv2-delen Apache 2.0) | MIT på moge-2-vitl, moge-2-vitl-normal, moge-2-vits-normal (HF-fält). vitb-normal ej kontrollerad | github.com/microsoft/MoGe ; huggingface.co/Ruicheng/moge-2-vitl | 3,1k stjärnor, Microsoft | Bra, redan i bruk. Metrisk skala finns men är opålitlig från en kamera |
| Depth Anything V2 | Relativt djup | Apache-2.0 | **Small Apache-2.0. Base, Large, Giant CC-BY-NC-4.0** | github.com/DepthAnything/Depth-Anything-V2 | Stor adoption | Endast Small (Base är också NC) |
| Depth Anything 3 | Multivy-geometri, djup | ej angiven på README | **Giant, Large, Nested: CC BY-NC 4.0. Base, Small, Metric-Large, Mono-Large: Apache 2.0** | github.com/ByteDance-Seed/Depth-Anything-3 (README) | Nytt, ByteDance Seed | Small/Base/Metric-Large kommersiellt OK. Testa DA3METRIC-LARGE |
| Depth Pro | Metriskt djup, skarpa kanter | Apples sample-licens | **apple-amlr: licens "exclusively for Research Purposes", exkluderar "product development or use in any commercial product or service"** | huggingface.co/apple/DepthPro/raw/main/LICENSE | Apple | **Förbjuden** utan avtal med Apple |
| VGGT | Feed-forward kameror, djup, punkter | VGGT License v1 med AUP | **VGGT-1B: cc-by-nc-4.0. VGGT-1B-Commercial: "licensed for commercial use, with the exception of military applications"** (gated, tagg vggt-aup-license). Fulltext för Commercial gav 401, ej läst | huggingface.co/facebook/VGGT-1B-Commercial ; huggingface.co/facebook/VGGT-1B | Meta | Bra COLMAP-komplement via Commercial-varianten, efter läst fulltext |
| MapAnything | Metrisk feed-forward-rekonstruktion, 12+ uppgifter | Apache 2.0 | **map-anything: CC-BY-NC 4.0. map-anything-apache: Apache 2.0** ("only difference is the training data composition and resulting license terms") | github.com/facebookresearch/map-anything ; huggingface.co/facebook/map-anything-apache | Meta | Mycket intressant. Träningsdata för Apache-varianten är inte dokumenterad på kortet |
| Pi3 / Pi3X | Feed-forward geometri | BSD-3 | **CC BY-NC 4.0, "Strictly Non-Commercial"** | github.com/yyfz/Pi3 | | Förbjuden |
| DUSt3R / MASt3R | Parvis 3D, matchning | **CC BY-NC-SA 4.0** | samma | github.com/naver/mast3r (LICENSE) ; github.com/naver/dust3r (LICENSE) | Naver, mycket använd | Förbjuden utan Naver-avtal |
| Metric3D (v2) | Metriskt djup + normaler | BSD-2 | **ej angiven** (HF JUGGHM/Metric3D saknar kort). README hänvisar "commercial inquiries" till författarna | github.com/YvanYin/Metric3D | | Oklart. Fråga författarna skriftligen |
| UniDepth | Metriskt djup | **CC BY-NC 4.0** | HF-sidan visar inget licensfält | github.com/lpiccinelli-eth/UniDepth (LICENSE) | ETH | Förbjuden |
| SpatialLM 1.0 / 1.1 | Punktmoln till väggar, dörrar, fönster, lådor (59 möbelkategorier i 1.1) | Pointcept-delen Apache 2.0; repots LICENSE.txt ej läst | **1.0: SceneScript-encoder CC-BY-NC-4.0. 1.1: vikter CC-BY-NC-4.0** (HF-fält cc-by-nc-4.0). Qwen-bas Apache 2.0, Llama-bas Llama 3.2 | github.com/manycore-research/SpatialLM ; huggingface.co/manycore-research/SpatialLM1.1-Qwen-0.5B | 5,1k stjärnor, Manycore | Exakt rätt uppgift (layout + lådor), men **NC**. Kontakta Manycore för kommersiell licens |
| SAM 3D Objects | Maskerat objekt till 3D med pose och layout; flerobjekt-notebook | SAM License | SAM License (Meta, 19 nov 2025) | github.com/facebookresearch/sam-3d-objects ; huggingface.co/facebook/sam-3d-objects | 7,7k stjärnor, Meta | Se avsnitt 2 |
| SpatialGen | Layout-styrd inomhusgenerering | MIT | SD 2.1-härledd (CreativeML Open RAIL++-M). FLUX-LoRA är FLUX.1-dev Non-Commercial | github.com/manycore-research/SpatialGen | 426 stjärnor | Kräver egen 3D-layout, dataset ej släppt. Hög risk |
| SceneGen | En bild till flera objekt | MIT | startar från TRELLIS-checkpoint, tränad/utvärderad på 3D-FUTURE | github.com/Mengmouxu/SceneGen | 522 stjärnor | Forskning, datarisk (fälla 2) |
| InSpace | 360-panorama till rum + möbelmeshar | MIT, men README: "non-commercial, academic research purposes only" | | github.com/naver/inspace | 24 stjärnor | Kräver 360-bild. Förbjuden |
| 3D-RE-GEN | En bild till objekt + bakgrund, 4-DoF-justering mot golv | ingen kod länkad | | arxiv.org/abs/2512.17459 | Preprint dec 2025 | Intressant arkitektur, ej användbar nu |

**Bedömning:** Väggavstånd och golv/tak löses bäst med MoGe-2 plus egen plananpassning (RANSAC). För lådor och möbelklasser finns ingen ren öppen modell. SpatialLM är närmast men NC. Rena kommersiella val: MoGe-2 (MIT), MapAnything-apache, VGGT-Commercial, DA3 Small/Base/Metric.

## 2. Bild/text till 3D-objekt

| Verktyg | Kod | Vikter | Villkor (verifierat) | Anseende | Passar |
|---|---|---|---|---|---|
| TRELLIS (v1, image-large) | MIT; submoduler (diffoctreerast, modifierad Flexicubes) kan ha andra licenser | MIT (HF-fält) | Träningsdata: se fälla 2 | 14,2k stjärnor, Microsoft | Bra för tallrik, dryck, enstaka föremål |
| TRELLIS.2-4B | MIT (repo LICENSE) | MIT (HF) | Mesh med PBR, minst 24 GB VRAM, 512 till 1536 voxlar | Microsoft | Bäst kvalitet bland rena licenser, kräver 24 GB |
| Hunyuan3D 2.0 / 2.1 | Tencent Community License | samma | **"DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA"**; över 1 miljon MAU kräver licens från Tencent (efter eget gottfinnande); får inte användas för att förbättra andra AI-modeller; Hongkong-lag. Läst i båda LICENSE-filerna (huggingface.co/tencent/Hunyuan3D-2.1 och Hunyuan3D-2) | 2.1: 4,4k stjärnor; 10 GB VRAM shape, 29 GB shape+textur | **Utesluts** om ni eller kunderna verkar i EU/UK |
| SAM 3D Objects | SAM License | SAM License | "royalty-free limited license". Texten **tar inte uttryckligen ställning till kommersiell användning**. Förbud mot krigs-/exportkontrollerade användningar och omvänd ingenjörskonst. Dokumenterad output är gaussian splat (PLY), mesh ej bekräftad. Gated | 7,7k stjärnor | Bra pose/layout. Be Meta bekräfta kommersiell användning skriftligen |
| Stable Fast 3D / SPAR3D | Stability Community License | samma | Gratis kommersiellt upp till 1 000 000 USD årsintäkt, över det Enterprise-licens från Stability (stability.ai/enterprise). SPAR3D-kortet är internt motsägande om gränsen ("or more"). Fulltext-LICENSE gav 401 | Stability | OK under tröskeln. Läs fulltext vid avtal |
| TripoSR | MIT (Tripo AI & Stability AI) | ej separat kontrollerad | | | Snabb, lägre kvalitet |
| TripoSG | MIT | MIT (HF VAST-AI/TripoSG) | | VAST-AI | Ren licens, bra form. Textur separat |
| Step1X-3D | ej kontrollerad | Apache-2.0 (HF stepfun-ai/Step1X-3D) | | StepFun | Ren licens, värt test |

**Bedömning:** TRELLIS.2 eller TRELLIS v1 för nyckelobjekt, TripoSG och Step1X-3D som licensrena komplement. Hunyuan3D bort på grund av territoriet.

## 3. Tillgångsbibliotek

| Källa | Licens (verifierat) | Kommersiellt | Notis |
|---|---|---|---|
| Poly Haven | Allt CC0, ingen kredit krävs. API har separata villkor, ToS 3.2 förbjuder scraping | Ja | polyhaven.com/license. Mat-täckning **ej verifierad** |
| ambientCG | CC0 | Ja | docs.ambientcg.com/license. Mest PBR-material |
| Kenney | Spelassets CC0 | Ja | kenney.nl/support. Mat-/restaurangpaket ej omnämnda, verifiera i katalogen |
| Poly Pizza | Per modell, mest CC-BY, en del CC0 | CC-BY kräver kredit | Endast sekundär källa (sökresultat). Officiell policysida hittades inte |
| BlenderKit (nu Blendkit, blendkit.com via 301) | Royalty Free eller CC0. Scener byggda av deras modeller får inte säljas på andra 3D-marknader. AI nämns inte | Ja, med villkor | blendkit.com/docs/licenses/licensing-faq/ |
| Sketchfab | Per modell. Standard tillåter kommersiellt, CC BY-NC gör det inte, kredit krävs utom CC0. Sedan 21 nov 2023 kan NoAI-tagg inte sättas på nya CC-uppladdningar | Filtrera på CC0, CC-BY, Standard | help.sketchfab.com/en/articles/16152217 ; sketchfab.com/blogs/community/restricting-generative-ai-use-of-free-models |
| Objaverse | Helheten ODC-By. Per objekt: CC-BY ca 721k, CC-BY-NC ca 25k, CC-BY-NC-SA ca 52k, CC-BY-SA ca 16k, CC0 ca 3,5k | Filtrera bort NC och SA | huggingface.co/datasets/allenai/objaverse |
| Objaverse-XL | Helheten ODC-By, 42 olika licensvärden, många utan licens (null). Kod Apache-2.0 | Endast med känd licens | huggingface.co/datasets/allenai/objaverse-xl ; github.com/allenai/objaverse-xl |
| Fab / Quixel | Standard (Personal/Professional) eller CC-BY per listning | Efter licens | fab.com/o/ai-info. Standard-EULA ej läst. Påståendet att Megascans nu tillåter AI-träning kommer från sökresultat, ej primärkälla |
| Betalda butiker (TurboSquid, CGTrader, Renderhub m.fl.) | ej undersökta | | Matpaket finns (t.ex. "Pizzeria Kit" på Renderhub i sökträff). Läs EULA per butik |

**Bedömning:** Mat är den verkliga luckan. Poly Haven och Kenney verifierades inte för mat. Förslag: gå igenom katalogerna manuellt, köp ett par matpaket med tydlig kommersiell EULA, generera resten med TRELLIS från egna foton.

## 4. Procedurella och genererade interiörer

| Verktyg | Kod | Tillgångar / villkor | Källa | Anseende | Passar |
|---|---|---|---|---|---|
| Infinigen / Infinigen Indoors | BSD-3-Clause (Princeton) | Procedurellt i Blender. Viss kod från CC0-källor | github.com/princeton-vl/infinigen | 7,4k stjärnor | Blender-nativ, ren licens. Restaurang/café ej nämnt (bostadsrum), kräver anpassning |
| Holodeck | Apache-2.0 | Objaverse-tillgångar via objathor och gpt-4o. Objathor-kod Apache-2.0, **tillgångslicens ej angiven**, annoteringar genererade med OpenAI | github.com/allenai/Holodeck ; github.com/allenai/objathor | 582 stjärnor, CVPR 2024 | LLM-layout är god idé. Tillgångarna är Objaverse-risk |
| LayoutGPT | ej verifierad (README gav 404) | | | | Referensidé: LLM skriver layout |
| 3D-FRONT / 3D-FUTURE | | **"for scientific research purpose only"; "You shall not commercialize the data sets"; får inte använda resultat "for commercialization or providing external services"** (avtal 18 juni 2020, Tao Bao, PDF gw.alicdn.com/bao/uploaded/TB1ZJUfK.z1gK0jSZLeXXb9kVXa.pdf) | | | Förbjuden för oss |
| SpatialLM-Dataset | | Licens ej angiven | | | Ej användbar tills klargjort |

**Bedömning:** Ingen färdig restaurang-/café-generator med ren licens hittad. Mest realistiskt: egna Blender-mallar (3 till 5 rumstyper) och en LLM som väljer och placerar utifrån 2D-detektionerna. Infinigen som alternativ för procedurella delar.

## 5. Rankad shortlist med kommersiell väg

**Rum/layout**
1. MoGe-2 (MIT) plus egen plananpassning: ren.
2. MapAnything-apache, VGGT-1B-Commercial: rena efter läst fulltext (VGGT har militärförbud).
3. DA3 Small/Base/Metric-Large (Apache), DA V2 Small.
4. SpatialLM 1.1: bäst funktion, NC. Väg: licensförfrågan till Manycore Research (kontaktväg ej verifierad).
Utesluts: Depth Pro, MASt3R/DUSt3R, UniDepth, Pi3. Metric3D: fråga författarna.

**Objekt**
1. TRELLIS.2 / TRELLIS v1 (MIT, datagrått).
2. TripoSG (MIT), Step1X-3D (Apache).
3. SAM 3D Objects efter skriftligt klartecken om kommersiell användning.
4. SPAR3D/SF3D under 1 M USD omsättning.
Utesluts: Hunyuan3D (EU/UK/KR).

**Tillgångar**
1. Poly Haven, ambientCG, Kenney (CC0).
2. Blendkit (Royalty Free), Sketchfab filtrerat på CC0/CC-BY/Standard, Fab Standard.
3. Betalda matpaket med tydlig EULA.
4. Objaverse endast efter filtrering per objektlicens.

**Interiörer**
1. Egna Blender-mallar plus LLM-placering.
2. Infinigen Indoors (BSD-3) som procedurell bas.
3. Holodeck-idén men utan Objaverse-tillgångar.
Utesluts: 3D-FRONT/3D-FUTURE.

## 6. Skilt åt

**Verifierat:** alla licensfält och citat ovan som har URL. Ej läst eller misslyckad hämtning: VGGT Commercial LICENSE.txt (401), SF3D LICENSE.md (401), LayoutGPT-README (404), Apple DepthPro utöver klausulen "License Scope", Poly Pizza officiell policy, Fab Standard-EULA, MoGe-2 vitb-normal, Hunyuan3D-2mini.

**Bedömning:**
- MIT-vikter tränade på 3D-FUTURE eller Objaverse-NC-objekt är juridiskt gråa. Risken är störst för SceneGen-liknande modeller, lägre för TRELLIS.
- SAM License saknar uttryckligt kommersiellt förbud men också uttryckligt tillstånd. Skriftlig bekräftelse rekommenderas.
- Jag antar att ni verkar i Sverige, vilket gör Hunyuan3D oanvändbart.
- Stjärnantal hämtades från GitHub-sidor 2026-11-11. Commit-datum visades inte, så "underhålls" är inte kontrollerat annat än att SAM 3D Objects har en uppdatering daterad 06/02/2026.
