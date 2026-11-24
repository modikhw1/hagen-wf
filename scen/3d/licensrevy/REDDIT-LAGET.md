# Reddit-läget, 11 nov 2026: vad utövare byggt för liknande problem (nov 2025 till nov 2026)

## Metod och begränsningar (läs först)

- WebSearch ger nästan aldrig reddit.com direkt (`site:reddit.com` gav noll träffar), och WebFetch blockerar old.reddit.com. Enda väg som fungerade: sökningar med frasen `reddit.sentinel-team.org ...`, en tredjepartsspegel med ögonblicksbilder av trådar. Alla trådar nedan är lästa där.
- **Datum är osäkra.** Speglingens "N dagar före bilden" är inkonsekventa (flera ger datum i 2025 för trådar vars ID och snapshot visar 2026). Jag anger därför snapshot-datum som övre gräns och uppskattar postdatum från Reddit-ID:t. Allt ligger inom 12-månadersfönstret, men exakt dag är ungefärlig.
- Snapshots fångar bara en del av kommentarerna. Poäng är poäng vid snapshot.
- Täckning är tunn: inga trådar hittade om foot sliding specifikt, SMPL/AMASS-licensgnäll (utom en), SAM 3D Objects, Gaussian splatting från telefonvideo, motion matching eller Wonder Studio/Move One/Rokoko på Reddit. Det betyder "hittades inte", inte "finns inte".
- Märkning: **[TRÅD]** = vad tråden säger. **[TOLKNING]** = min läsning.

## Fynd per tråd

### 1. SAM 3D Body

**Humanoid Gaussian Splats with SAM 3D Body and WAN 2.2 VACE** (r/StableDiffusion, u/Erant, ca 19 jan 2026, 89 poäng, 13 kommentarer)
https://reddit.com/r/StableDiffusion/comments/1qgrtzc/humanoid_gaussian_splats_with_sam_3d_body_and_wan/
- [TRÅD] Byggde Gaussian-splats av människor: SAM 3D Body-mesh renderas till depth- och OpenPose-kontrollvideor, matas in i Wan VACE för att generera konsistenta vyer från flera höjder, kameraparametrar återvinns ur depthvyerna, sedan splatting (Brush). Körs på 4070 Ti 12 GB. Fork: github.com/Erant/sam-3d-body.
- [TRÅD] Kritik: SAM 3D tränad på snäv data, "struggles to output diverse bodies" (u/hsadg, 6 poäng); en annan säger att bristen på diversitet gör det svårt för kreativt arbete. Hög/låg vinkel såg "unfinished" ut.
- [TOLKNING] Mesh som kontrollsignal till videomodell är en etablerad mönsterbit, även för SAM 3D Body. Kroppsdiversitet är en känd svaghet.

**SAM3DBody-cpp, realtid i C++ utan Python** (r/computervision, u/_AmmarkoV_, ca maj 2026, 336 poäng, 25 kommentarer)
https://reddit.com/r/computervision/comments/1tm7fv0/sam3dbodycpp_realtime_3d_fullbody_pose_hands_in_c/
- [TRÅD] YOLO11m-pose, DINOv3-ViT-H, MHR-decoder, LBS i C. ca 120 ms/frame för två personer på 3090. Utdata: 70 nyckelpunkter (MHR-70), mesh, kameratranslation och brännvidd. Annan kommentator: Fast-SAM-3D-Body (TensorRT) ger ca 10 fps på 3090.
- [TRÅD] u/johnnySix (6 poäng): önskar mer tillåtande licens, "företaget tillåter det inte". u/soylentgraham: anklarna mappas mot fötterna, skalan kan vara fel, readme visar ingen djup- eller golvplanshantering.
- [TOLKNING] Per-frame-modell utan golvplan/skala bekräftas som problem av utomstående. Licensfrågan kring SAM-licensen är en reell blockerare för vissa företag, relevant att verifiera för oss.

**Production 3D body reconstruction without SMPL, MHR + Anny** (r/computervision, u/clad_you, ca slutet mars 2026, 1 poäng)
https://reddit.com/r/computervision/comments/1s7uqwh/production_3d_body_reconstruction_without_smpl/ (blogg: https://clad.you/blog/posts/body-pipeline/)
- [TRÅD] Tvåmannateam, virtuell provning. Lämnade SMPL pga icke-kommersiell licens och oklar underlicensiering via Meshcapade (köpt av Epic). SAM 3D Body för bild, egen MHR-till-Anny-konverterare, mått enligt ISO 8559-1. ca 0,09 USD per kropp på L4. BWH-fel ca 5-8 cm före tuning. En kommentator går också MHR-vägen och utforskar video.
- [TOLKNING] Närmaste rena "licensflykt från SMPL till MHR"-berättelse jag hittade. Anny (Naver) är ett alternativ att granska licensmässigt; min sökning antyder Apache 2.0 men det är ej verifierat mot repot.

**re-exploring monocular mocap for football in light of CVPR26** (r/computervision, ca feb-jun 2026, 34 poäng, 2 kommentarer)
https://reddit.com/r/computervision/comments/1uck0r5/reexploring_monocular_mocap_for_football_in_light/
- [TRÅD] Frågar efter praktisk ansats för okontrollerad video med ocklusion. Enda svaret: "mycket data", resultaten svaga utan egen träning.
- [TOLKNING] Lite värde, men bekräftar att ingen färdig lösning för svår video syns på Reddit.

### 2. Video till mocap från en kamera (GVHMR m.fl.)

**ComfyUI Video to MotionCapture + Blender-automation (wip)** (r/StableDiffusion, ca 18 feb 2026, 165 poäng, 18 kommentarer)
https://reddit.com/r/StableDiffusion/comments/1r7u51w/comfyui_video_to_motioncapture_using_comfyui_and/ (repo AKASubaz/ComfyUI-Video2MotionCapture)
- [TRÅD] GVHMR -> SMPL-parametrar -> riggad FBX, retarget till Mixamo/UE-mannequin/egen karaktär via buntad Blender-automation.
- [TRÅD] Kritik: u/Eisegetical "output looks very inaccurate", ber om överlägg mot originalplåten. UE-retarget ser fel ut (u/Odd-Mirror-2412). Annan nod "dampens motion".
- [TOLKNING] Utövare efterfrågar överlagringsbevis; vi bör själva mäta mot plåten.

**[Update] ComfyUI-MotionCapture: moving camera support + SMPL viewer** (r/comfyui, u/ant_drinker, ca 26 feb 2026, 186 poäng, 21 kommentarer)
https://reddit.com/r/comfyui/comments/1rer6ls/update_comfyuimotioncapture_moving_camera_support/ (github.com/PozzettiAndrea/ComfyUI-MotionCapture)
- [TRÅD] GVHMR-baserat, nu med rörlig kamera och kameratrajektoria. Författaren: trajektorian är "imperfect", DPVO fungerar inte, enkel visuell odometri är användbar. Beroendeproblem: 30+ GB, "comfy-env" kör sudo, röda noder efter import.
- [TOLKNING] Handhållen kamera är fortfarande det svaga ledet även här. Samma ansats som vår COLMAP, men sämre.

**Mocap Surgeon, video-till-3D-mocap och cleanup-nod** (r/comfyui, u/shamomylle, ca 1 maj 2026, 93 poäng, 20 kommentarer)
https://reddit.com/r/comfyui/comments/1sztd11/mocap_surgeon_videoto3d_motion_capture_and/
- [TRÅD] MediaPipe -> 3D-OpenPose-rigg, jitterfilter med reglage, manuell korrigering med gizmo, onion-skinning, bake till .glb. "Still early and rough."
- [TOLKNING] Folk bygger faktiskt ett manuellt rensningssteg ovanpå brusig mocap i stället för att lita på modellen. Samma behov som vårt jitter/foot-sliding.

**Live Motion Capture custom node** (r/comfyui, ca feb 2026, 130 poäng) https://reddit.com/r/comfyui/comments/1qujri1/live_motion_capture_custom_node_experimental/
- [TRÅD] Webbkamera/MediaPipe -> OpenPose för ControlNet. Låg relevans (2D-pose).

**Motion capture tools** (r/generativeAI, ca apr 2026, 1 poäng) https://reddit.com/r/generativeAI/comments/1sl7pyr/motion_capture_tools/
- [TRÅD] Botsvar listar DeepMotion (upp till 8 personer, gratisnivå), Rokoko Vision ("struggles with overlapping performers"), Wan Animate, Viggle. En kommentator marknadsför Dollars MONO (lokal, FBX).
- [TOLKNING] Svagt underlag, delvis reklam.

### 3. Blockout/previs till AI-video

**I used Blender as a layout tool for AI video generation** (r/comfyui, u/waterarttrkgl, ca 5 maj 2026, 266 poäng, 40 kommentarer)
https://reddit.com/r/comfyui/comments/1t4iqrr/i_used_blender_as_a_layout_tool_for_ai_video/
- [TRÅD] Enkel Blender-layout, nycklade kameror/objekt, nyckelbilder görs fotorealistiska med bildmodell, sedan Seedance 2 (Reference to Video) med både 3D-animationen och bilderna. Kommentarer: u/leepuznowski gör samma i 3ds Max + Seedance 2.0 API och säger att Seedance ibland följer indata för exakt; u/Ooserkname gör Blender-blockouts med Higgsfield; u/JahJedi bygger LTX 2.3 Union IC; u/goazu: "useful for previs but not a production pipeline"; u/champagnepaperplanes frågar hur noggrannheten mot 3D-blockeringen säkras (obesvarat). Kritik: Seedance är betalt/ej lokalt.
- [TOLKNING] Exakt vårt slutsteg, och det är redan vanligt. Ingen mätte hur väl blockeringen hålls.

**Blender Layout -> AI Render, 1:1 Camera Tracking** (r/comfyui, samma författare, ca 1 maj 2026, 219 poäng, 26 kommentarer)
https://reddit.com/r/comfyui/comments/1sz9cf4/blender_layout_ai_render_11_camera_tracking/
- [TRÅD] Proxygeometri utan texturer, handnycklad kamera, Kling eller Seedance regenererar och bevarar kamerabanan. En kommentator (u/MedicineLate349) hävdar att Kling håller kameran närmare än Seedance; ingen testade. u/cjwidd: "inte nytt, gjort i över ett år".
- [TOLKNING] Kamerafidelitet mellan modeller är obekräftad anekdot; testa själva.

**NVIDIA Video Generation Guide: Blender 3D scene to 4K video** (r/StableDiffusion 67 poäng, 4 kommentarer; r/comfyui 13 poäng; ca 25 mars 2026)
https://reddit.com/r/StableDiffusion/comments/1s2v4u7/nvidia_video_generation_guide_full_workflow_from/
- [TRÅD] "3D Guided Generative AI Blueprint": layout i Blender, start-/slutbild från viewport, LTX-2.3 FirstFrame/LastFrame, upscaling. Kräver 16 GB+ VRAM, 64 GB RAM. Repo: github.com/NVIDIA-AI-Blueprints/3d-guided-genai-rtx.
- [TOLKNING] Detta är en officiell, sammanhängande referens för stillbild-först-varianten (inte rörelsestyrning av människor).

**Blender to ComfyUI** (r/comfyui, ca 1 maj 2026, 0 poäng) https://reddit.com/r/comfyui/comments/1szsf92/blender_to_comfyui/
- [TRÅD] u/Support_Marmoset: grova block med Hunyuan 3D -> Blender -> kameraplanering -> VACE (Uni3C som alternativ); tidigare Cascadeur-animation + depth + VACE; nu Qwen 2511 edit med multi-camera-LoRA + LTX. Wan krånglar på 12 GB.

**Wan 2.1 & 2.2 Model Comparison: VACE vs SCAIL vs MoCha vs Animate** (r/comfyui, ca 28 jan 2026, 6 poäng) https://reddit.com/r/comfyui/comments/1qptpwq/wan_21_22_model_comparison_vace_vs_scail_vs_mocha/
- [TRÅD] Wan 2.2 Animate 7,1/10 bäst balans; SCAIL 6,5 högst kvalitet men svag på flera personer; VACE 6/10 tappar textur/likhet; MoCha restriktiv. Författaren erkänner att AI formaterade/hajpade texten.
- [TOLKNING] För flerpersonsscener (vårt fall) är SCAIL-en, enligt dess egen repo, bara svagt stödd i ComfyUI. Subjektiva betyg, en användare.

**Timelapse, WAN VACE Masking** (r/StableDiffusion, ca feb 2026, 45 poäng) https://reddit.com/r/StableDiffusion/comments/1r8j2ug/ — VACE som redigeringsverktyg i Resolve/After Effects. Låg relevans.

**Seamless animations in Wan VACE** (r/comfyui, 273 poäng) https://reddit.com/r/comfyui/comments/ (ID oklart; snapshot-URL 1s4f1lv) — klippövergångar, ej relevant.

### 4. Övrigt
- r/vfx om automatiserad Blender-kameraspårning (ca dec 2025, 0 poäng): https://reddit.com/r/vfx/comments/1pmfouq/ — proffs sågar idén att mata ett verktyg med expertdata; Blenders inbyggda spårare nämns som för svag för svåra plan. Marginellt.
- Icke-Reddit (kontext, ej trådar): toyxyz RGBMocap (GVHMR/ExMR/PromptHMR/GEM-X med kontaktkorrigering; ExMR och GVHMR icke-kommersiella, GEM-X kommersiellt tillåten men lägre kvalitet enligt underhållaren); squall01337/mixamo-llm-mocap (GVHMR + Blender via MCP + foot-skate-QA); OnlineHMR (arXiv 2603.17355: metrisk skala från MoGe-2 med människopixlar uteslutna, EMA-utjämning). Foot-lock-tillägg i Blender: Inverse Lock Bone, Foot Flow.

## Återkommande mönster

1. **Klistrad pipeline, inte svit.** Allt som hittades är ComfyUI-noder + Blender-skript + externa API:er (Seedance/Kling). Ingen integrerad svit nämns som lösning för kamera-till-redigerbar-scen. Kommersiella sviter (Move One, Flow Studio, DeepMotion, Rokoko) nämns bara i marknadsföringsliknande kommentarer; single-camera bedöms i bloggar som "bra för blocking/previs, inte slutanimation".
2. **GVHMR/SMPL-spåret dominerar hobbyflödet** (video -> SMPL -> FBX -> Mixamo/UE-retarget). Det är SMPL-baserat och därmed licensmässigt problematiskt för kommersiell produkt. Endast en tråd (MHR+Anny) tar licensen på allvar.
3. **Mesh/skelett som kontrollsignal.** SAM 3D Body-mesh -> depth/pose-video -> Wan VACE (Erant). Konsensus i kommentarerna: 2D-pose (DWPose/OpenPose) är underlägset 3D-pose för flera personer; SCAIL och Wan Animate nämns, VACE som arbetshäst.
4. **Blender-blockout som regi, API-modell som renderare.** Seedance 2.x/Kling med blockoutvideo som referens, ofta kombinerat med genererade nyckelbilder. Populärt (200+ poäng) men utan kvantitativa mått på hur väl blockeringen hålls; "previs, inte produktion".
5. **Manuell rensning ovanpå brusig mocap** (Mocap Surgeon, foot-lock-tillägg). Ingen litar på rå modellutdata; jitter och foot sliding hanteras med filter + kontaktdetektion + IK-lås.
6. **Skala och kamera är olöst.** Rörlig kamera, golvplan och metrisk skala beskrivs som "imperfect" eller saknas.

## Direkt tillämpligt för oss [TOLKNING]

- Slutsteget (blockout som referens till Seedance/Kling) är beprövat av andra; håll jämförelsetest av kamera- och positionsfidelitet i egen regi, eftersom Reddit bara ger anekdoter.
- Erants kedja (SAM 3D Body-mesh -> depth+pose-kontroll -> VACE) bekräftar att vår MHR-utdata kan fungera som kontroll.
- Bygg egen kontaktdetektion + IK-lås + jitterfilter (som Mocap Surgeon och mixamo-llm-mocap gör) i stället för att vänta på färdig motion prior; hitta ingen tråd som lovar en MHR-prior.
- Skala: OnlineHMR-metoden (MoGe-2-djup utan människopixlar, konsekvent skalfaktor per sekvens) matchar vår stack och är värd att testa.
- Licens: kontrollera SAM License och MHR-licens själva; Reddit ger bara "ett företag vägrar" och "SMPL-flykt via MHR+Anny".

## Luckor
Ingen Reddit-tråd hittad om: foot sliding med SAM 3D Body, motion priors utan AMASS, SAM 3D Objects i praktiken, telefon-till-Gaussian-splat-rum, Wonder Studio/Move One-upplevelser, Uni3C-praktik. Rekommenderar manuell Reddit-sökning (inloggad) i r/StableDiffusion, r/comfyui, r/computervision efter dessa.
