# Rörelseprior och rörelsebibliotek: licensrevy för "mottagaren"

Datum: 2026-11-11. Syfte: ta SAM 3D Bodys brusiga per-bildruta-skattningar (MHR) och göra dem till naturlig mänsklig rörelse, i en kommersiell produkt. Ingen juridisk rådgivning.

Förklaring. **[V]** = läst i primärkälla (LICENSE-fil, README, HF-kort, licenssida) under denna körning. **[S]** = bara sekundärkälla eller sökträff, primärsidan gick inte att nå. **[O]** = inte verifierat. "Dom" = min bedömning.

## 1. Grunden vi står på

| Sak | Licens | Källa |
|---|---|---|
| MHR (modell, kod) | Apache-2.0 [V]. Har verktyg för MHR<->SMPL/SMPL-X-konvertering (`tools/mhr_smpl_conversion`). | https://raw.githubusercontent.com/facebookresearch/MHR/main/LICENSE , https://github.com/facebookresearch/MHR |
| SAM 3D Body (kod + checkpoints) | "SAM License" (19 nov 2025) [V]. Royalty-free, worldwide, får användas/modifieras/distribueras. Förbjudna ändamål: militär, ITAR, kärnvapen, spionage. Terminerar om man stämmer Meta. Härledda verk äger man själv. Ingen non-commercial-klausul. Checkpoints gatade på HF (`sam-license`). | https://raw.githubusercontent.com/facebookresearch/sam-3d-body/main/LICENSE , https://huggingface.co/facebook/sam-3d-body-dinov3 |
| SAM 3D Body-dataset (HF) | `sam-license` [V]. Annoteringar över 3DPW, COCO, EgoExo4D m.fl. De underliggande bilddatasetens egna villkor ej bedömda [O]. | https://huggingface.co/datasets/facebook/sam-3d-body-dataset |
| Momentum (IK, solvers, pymomentum) | MIT [V] | https://github.com/facebookresearch/momentum |
| SMPL / SMPL-X | Endast icke-kommersiell forskning/utbildning/konstnärliga projekt. "Any other use, in particular any use for commercial purposes, is prohibited." Förbjuder också att träna kommersiella AI-system med mjukvaran. Kommersiell licens via Meshcapade, kontakt smpl@max-planck-innovation.de [V] | https://smpl.is.tue.mpg.de/modellicense.html |
| AMASS | Endast icke-kommersiellt. **Förbjuder uttryckligen att datasetet används för att träna metoder/nätverk för kommersiellt bruk.** Får inte vidaredistribueras. Kommersiell licens: ps-license@tue.mpg.de [V] | https://amass.is.tue.mpg.de/license.html |

Dom: MHR + SAM 3D Body är rena för oss. Smutsen kommer via (a) SMPL-beroende och (b) modellvikter tränade på AMASS. Punkt (b) är den lömska: MIT-kod med AMASS-tränade vikter är ändå tvivelaktig kommersiellt, eftersom AMASS-licensen går på själva träningen.

## 2. Meshcapade, kommersiell SMPL-väg

Primärsidorna (meshcapade.com/assets/body-models, Notion-sidan) gav 403 respektive tomt innehåll. Siffrorna är därför **[S]** från sökträffar som återger sidorna, och de två källorna **säger emot varandra**.

- Body-models-sidan (enligt sökresumé): Micro 1 500 EUR/år kommersiellt (0 för R&D), SME 25 000 EUR/år (R&D 7 500), Enterprise på förfrågan. Micro = EU-definitionen. 30 dagars utvärdering. Sidan ska säga att licensen inte tillåter kommersialisering av produkter utvecklade med modellerna (formulering oklar, [S]).
- Notion-sidan (enligt sökresumé): Micro (<=10 anställda, <=2 M EUR omsättning) 5 000 EUR kommersiellt, 1 500 R&D. Priser höjs årligen.
- Dom: räkna med 1 500 till 5 000 EUR/år för Micro, bekräfta med Meshcapade. Frågor att ställa: (1) täcker licensen SMPL-X, (2) täcker den vikter som tredje part tränat på AMASS (troligen nej, det är AMASS-licensen), (3) AMASS kommersiellt kräver eget avtal med MPI (ps-license@tue.mpg.de, pris okänt).
- Försök själv: https://meshcapade.com/assets/body-models , https://meshcapade.notion.site/The-SMPL-Model-Licenses-2144560e54388085af5eff111fcdf266

## 3. Alternativ

"Rent?" = kan vi använda kommersiellt utan avtal (dom byggd på verifierade fakta). Passform avser MHR-riggen.

### 3A. Lärda priors / denoisers / video-till-världsrörelse

| Alternativ | Gör | Kodlicens | Vikter / träningsdata | Djup och rykte | Passform | Rent? |
|---|---|---|---|---|---|---|
| **WHAM** | Video -> SMPL-rörelse i världskoordinater, fotkontakt | MIT [V] https://raw.githubusercontent.com/yohanshin/WHAM/main/LICENSE | SMPL krävs (registrering) [V]. AMASS-träning [O exakt] | CVPR 2024, 1,2k stjärnor | SMPL, retarget SMPL->MHR | Nej utan SMPL- + AMASS-avtal |
| **GVHMR** | Video -> världsjordad SMPL-rörelse (gravity-view) | Egen licens: "educational, research and non-profit purposes only", modifieringar får ej användas kommersiellt, kommersiellt: xwzhou@zju.edu.cn [V] https://raw.githubusercontent.com/zju3dv/GVHMR/main/LICENSE | Tränad med bl.a. 3DPW/RICH/EMDB [V], SMPL | SIGGRAPH Asia 2024, TPAMI 2026, 2,3k stjärnor | SMPL | Nej, kräver avtal med ZJU + SMPL |
| **TRAM** | Video -> SMPL-rörelse + kamerarörelse (SLAM) | MIT [V] https://github.com/yufu-wang/tram | SMPL krävs; DPVO/DROID-SLAM egna villkor [O] | 1,2k stjärnor [V]; ECCV 2024 [O] | SMPL | Delvis, SMPL-beroende |
| **RoHM** | Diffusion som rekonstruerar/avbrusar rörelse, fyller luckor (dolda ben) | **CC-BY-NC** för kod, checkpoints, data [V] https://github.com/sanweiliti/RoHM | SMPL-X, tränad på AMASS [V] | CVPR 2024, 401 stjärnor | SMPL-X | Nej |
| **HuMoR** | Rörelse-VAE som prior vid test-time-optimering | MIT [V] https://github.com/davrempe/humor | SMPL+H, tränad på AMASS [V] | ICCV 2021, 580 stjärnor, äldre | SMPL+H | Nej (AMASS) |
| **PHC** | Fysiksimulerad humanoid-tracking, fixar fotglid | BSD-3-Clause-Clear [V] https://raw.githubusercontent.com/ZhengyiLuo/PHC/master/LICENSE (README hänvisar dock till IsaacGym/UHC/SMPL-X-licenser) | Tränad på AMASS-delmängd, 11 313 sekv. [V]; Isaac Gym krävs | ICCV 2023, 1,3k stjärnor | SMPL, tung simulatorstack | Nej (AMASS + SMPL) |
| **GENMO / GEM** (NVlabs) | Enhetlig skattning + generering (video, text, 2D) | "NVIDIA OneWay Noncommercial License" [V] https://github.com/NVlabs/GENMO | SMPL | 542 stjärnor | SMPL | Nej |
| **PhysPT** | Fysikmedveten transformer ovanpå kinematisk rekonstruktion | Ingen repo hittad [S] | SMPL | CVPR 2024 | SMPL | Ej tillgänglig |
| **MotionBERT** | Förtränad rörelsekodare, 2D (H36M-17) -> 3D | Apache-2.0 [V] https://github.com/Walter0807/MotionBERT | Förträningsdata ej verifierad [O] | ICCV 2023, 1,5k stjärnor | Eget skelett, inte MHR | Oklart |
| Övrigt 2025-26 (t.ex. VideoMDM) | Dök upp i sökning, ej granskade | [O] | [O] | | | Ej bedömt |

Dom: ingen publicerad "video -> MHR-rörelse"-denoiser hittades. Ingen av de lärda priorerna är kommersiellt ren; alla bygger på SMPL och/eller AMASS. Den AMASS-fria vägen är att träna om på rena data (se 3B).

### 3B. Rörelsebibliotek för retrieval / motion matching

| Dataset | Licens | Kommersiellt? | Notering |
|---|---|---|---|
| **AMASS** | Icke-kommersiellt, ingen träning för kommersiellt bruk, ingen vidaredistribution [V] https://amass.is.tue.mpg.de/license.html | Nej utan avtal | SMPL-format. Delmängderna (CMU, KIT m.fl.) har egna råformat |
| **CMU mocap** (rå) | Sekundärkällor: "free for use in research and commercial projects" [S]. Primärsidan nåddes inte (certifikatfel/404). Verifiera själv på http://mocap.cs.cmu.edu/ | Troligen ja [S], **verifiera före beslut** | Bred täckning (gå, sitta, gester, ätande m.m. [O exakt]). Hämta *råa* BVH/C3D, inte AMASS-versionen. Tredjepartskonverteringar kan ha egna villkor (4TU-FBX: CC BY-NC 4.0 [S]) |
| **100STYLE** | CC BY 4.0 [V] https://www.ianxmason.com/100style | **Ja**, med kredit ("The 100STYLE Dataset - Ian Mason") | Bara lokomotion, en aktör, 100 stilar. Inte servera/sitta/prata |
| **LaFAN1** (Ubisoft) | CC BY-NC-ND 4.0 [V] https://github.com/ubisoft/ubisoft-laforge-animation-dataset | Nej | 77 sekv., 4,6 h |
| **Bandai Namco Motiondataset 1+2** | CC BY-NC 4.0 enligt README [V] https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset (pressen sa NC-ND [S]; LICENSE-filerna gick inte att läsa) | Nej | Vardagsrörelser, bra innehåll men NC |
| **Mixamo** | Royalty-free för personliga/kommersiella projekt enligt FAQ-citat [S]. Mixamo Additional Terms (2021-06-23) förbjuder enligt sökträff träning/förbättring av ML-modeller [S, PDF:en gick inte att avkoda] https://wwwimages2.adobe.com/content/dam/cc/en/legal/servicetou/Mixamo-Addl-Terms-en_US-20210623.pdf | Retrieval/retarget som animation: sannolikt ja. Träning: nej [S] | Läs PDF:en själv |
| **ActorCore (Reallusion)** | Standardlicensen utesluter "machine learning, artificial intelligence (AI) training, fine-tuning, or model validation"; sådant kräver Enterprise License [V] https://www.reallusion.com/Content/EULA/EULA.htm | Video/bild ok; träning kräver Enterprise | Får ej extraheras som fristående tillgångar ur app |
| **Truebones** | "Royalty free ... commercial", vidareförsäljning av FBX/BVH förbjuden [S, Gumroad-sökträff]. AI-träning ej nämnt | Troligen ja för retrieval [S] | |
| **Rokoko motion dataset** | 1,6 M tillgångar, >10 000 h. Villkor ej publicerade, kontakta Rokoko [V] https://www.rokoko.com/mocap/motion-dataset | Via avtal | Pris ej publikt |
| **BONES-SEED** (Bones Studio) | Egen licens [V] https://bones.studio/info/seed-license : kommersiellt bara för "Qualifying Startups" (<1 M USD årsintäkt), anmäl inom 30 dagar vid överskridande, då upphör licensen efter 30 dagar utan kommersiellt avtal. AI-träning tillåten, men ej generativa modeller vars huvudsyfte är att producera rörelsedata som ersätter datasetet. Rådata får ej läggas på offentliga repon | Ja om vi är under 1 M USD, annars avtal | 142 220 rörelser, 288 h, 522 aktörer, SOMA-skelett (BVH) [V] |
| **HumanML3D** | Härleds från AMASS + HumanAct12; repo distribuerar ingen data, bygger lokalt från AMASS [V] https://github.com/EricGuo5513/HumanML3D ; ingen egen datalicens angiven | Dom: ärver AMASS-förbudet | |
| **Motion-X** | Åtkomst "för icke-kommersiellt bruk" via formulär [V] https://github.com/IDEA-Research/Motion-X ; delar är AMASS/GRAB | Nej | SMPL-X |
| Meta-egna rörelsedata (Nymeria, Ego-Exo4D m.fl.) | Ej undersökt | [O] | |

### 3C. Text-till-rörelse (fylla luckor)

| Modell | Kodlicens | Vikter / träningsdata | Rykte | Rent? |
|---|---|---|---|---|
| **Kimodo** (NVIDIA, 2026) | Kod Apache-2.0 [V] https://github.com/nv-tlabs/kimodo . SOMA-SEED-v1.1: **NVIDIA Open Model License**, kortet säger "ready for commercial use" [V] https://huggingface.co/nvidia/Kimodo-SOMA-SEED-v1.1 . Licensen: modeller kommersiellt användbara, du äger derivat och utdata, får ej kringgå guardrails, notis krävs vid redistribution [V] https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/ | Tränad på Bones-SEED (288 h); kortet säger "dataset license constraints adhered to". **SMPLX-RP-v1 är non-commercial research only** [V] https://huggingface.co/nvidia/Kimodo-SMPLX-RP-v1 | 4,2k stjärnor, aktivt (senaste nyhet 2026-10-15) [V] | **Ja för SOMA/G1-varianterna.** Text + begränsningar (nyckelbilder, vägpunkter). 30-leds SOMA-skelett, retarget till MHR krävs |
| **MDM** | MIT [V] https://github.com/GuyTevet/motion-diffusion-model | HumanML3D/KIT (AMASS-ärvt) | ICLR 2023, 4,1k stjärnor | Kod ja, vikter tvivelaktiga |
| **MoMask** | MIT [V] https://github.com/EricGuo5513/momask-codes | HumanML3D/KIT | CVPR 2024, 1,3k stjärnor | Kod ja, vikter tvivelaktiga |
| **T2M-GPT** | Apache-2.0 [V] https://github.com/Mael-zys/T2M-GPT | HumanML3D/KIT | CVPR 2023, 782 stjärnor | Kod ja, vikter tvivelaktiga |

Dom: MDM/MoMask/T2M-GPT ger 22-leds skelett utan fingrar och vikter som ärver HumanML3D/AMASS. Kimodo-SOMA är det enda hittade alternativet med uttryckligt kommersiellt vikttillstånd.

### 3D. Kroppsmodellsberoende

| Beroende | Vilka |
|---|---|
| Kräver SMPL/SMPL-X | WHAM, GVHMR, TRAM, RoHM, HuMoR, PHC, GENMO, Motion-X, HumanML3D, Kimodo-SMPLX |
| Eget skelett / rigg-agnostiskt (retarget via BVH) | Kimodo-SOMA, CMU-rå, 100STYLE, BONES-SEED, Truebones, Mixamo, Rokoko |
| MHR direkt | Momentum (IK/solvers, MIT) |

## 4. Rankad kortlista för mottagarrollen

Allt här är **dom**, byggd på de verifierade licensfakta ovan.

1. **Eget ML-fritt filter + Momentum-IK** (MIT, MHR direkt). Tidsfiltrering på lokala rotationer, fotlåsning vid kontakt, led- och benlängdsgränser, hoppdetektion och interpolation. Kommersiell väg: ingen behövs. Billigast och löser jitter/glid/leddjupp, men *skapar* ingen rörelse för gissade ben. Börja här.
2. **Kimodo-SOMA-SEED som begränsad regenerator och luckfyllare** (NVIDIA Open Model License, kommersiellt OK enligt kortet). Mata in SAM 3D Body-banorna som nyckelbilder/vägpunkter plus text ("sitter och äter") och låt modellen skapa naturlig rörelse. Retarget SOMA(30) -> MHR krävs, ingen färdig väg verifierad. Kommersiell väg: använd NVIDIA-checkpointsen, behåll licensnotisen, och fråga NVIDIA/Bones skriftligt om träningsdatans villkor (Bones-SEED: Qualifying Startup under 1 M USD, generativa modeller får ej ersätta datasetet) berör oss. Restrisk: medel.
3. **Eget bibliotek av ren mocap för motion matching**: CMU-rå (verifiera primärsidan först) + 100STYLE (CC BY 4.0, kredit) + licensierat tillskott för serverings-/sittscener (Truebones köp; Rokoko eller Bones Studio via avtal). Retarget via BVH till MHR. Undvik AMASS-versioner. Mixamo/ActorCore bara för retrieval, inte träning.
4. **WHAM/TRAM-lager för världskoordinater och fotkontakt**, bara om vi köper vägen: Meshcapade SMPL-licens (ca 1 500 till 5 000 EUR/år Micro [S]) + AMASS kommersiellt från MPI (pris okänt) + MHR<->SMPL-konvertering. Dyrare och mer juridiskt trassligt än 1-3, och tillför troligen lite över kameratrackingen vi redan har.
5. **Träna om en liten prior (HuMoR/MDM-liknande) på rena data** (CMU-rå + 100STYLE + BONES-SEED) direkt på MHR-ledrotationer. Rent från start men egen ML-insats. Gör bara om 1-3 inte räcker.

Avrådes: RoHM (CC-BY-NC), GVHMR (NC), GENMO (NC), Kimodo-SMPLX (NC), LaFAN1 (NC-ND), Bandai Namco (NC), Motion-X (NC).

## 5. Återstår att verifiera

- CMU primärsida (http://mocap.cs.cmu.edu/) nåddes inte (certifikatfel). Läs själv.
- Meshcapades priser: två källor med olika siffror, primärsidor blockerade. Be om offert.
- Mixamo Additional Terms-PDF:en (kunde ej avkodas) och Bandai Namcos LICENSE-filer.
- Kimodo-vikternas träningsdata (Bones-SEED) mot vår omsättning: fråga till NVIDIA/Bones.
- 2025-26-arbeten utöver Kimodo och GENMO (t.ex. VideoMDM) ej granskade. Meta-egna rörelsedatasets ej granskade.
