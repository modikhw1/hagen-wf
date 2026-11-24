# Video-till-video som "läsbarhetsöversättning": alternativ, licenser, kostnad

Datum 2026-11-11. Ren research, inga körningar. Märkning: **[V]** verifierat i primärkälla (modellkort, repo, officiell prisssida), **[S]** sekundärkälla, **[O]** overifierat eller min egen uppskattning. Inget pris eller licens är angivet ur minnet.

Ägarens tillägg (11 nov): stilisering är bara ett slutrenderval. Läsbart format = realistiskt och datarikt (ansikten, uttryck, mat intakta); förenkla bara det som stör läsningen (stök, kameraskak, beskärning). Format A väger tyngst, B/C är bara bakgrundsförenkling. Rankingen nedan utgår från det.

## 1. Wan VACE och Wan-familjen

| Modell | Kod / vikter | Kapacitet | Gräns | Källa |
|---|---|---|---|---|
| Wan2.1-VACE 1.3B / 14B | Apache-2.0 (repo och modellkort) [V] | R2V, V2V, masked V2V; uppgiftsnamn Move/Swap/Reference/Expand/Animate-Anything, depth, inpaint (bbox) [V]. Pose och outpaint nämns inte uttryckligen i README [V], men "Expand" = utvidgning | ~81 bildrutor, 480p (1.3B) resp. 480p/720p (14B), export 16 fps [V]. RIFLEx fungerar inte med VACE, så ~81 rutor är taket [S] | https://github.com/ali-vilab/VACE , https://huggingface.co/Wan-AI/Wan2.1-VACE-14B |
| Wan2.2 VACE-Fun A14B (Alibaba PAI) | Apache-2.0 [V] | Canny, depth, pose, MLSD, trajectory; referensbild + kontrollvideo; subjektstyrd video [V] | Tränad på 81 rutor, 16 fps, upplösning 512/768/1024 [V]. ~64 GB vikter och ~60 GB disk [V]; "~60 GB VRAM" officiellt, offload/fp8 ned mot 12 GB listas [V/S] | https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B |
| Wan2.2-Animate 14B | Apache-2.0 [V] | Animation (bild imiterar rörelse) och Replacement (byter ut personen i videon, relighting-LoRA). Förbehandling krävs [V] | Ingen VRAM- eller tidssiffra i texten [V]. Community: artefakter, ansiktsdrift och bakgrundsbrus efter ~5 s [S] | https://huggingface.co/Wan-AI/Wan2.2-Animate-14B |
| Wan-Animate-2 (aug 2026) | Apache-2.0 [V] | End-to-end, text-styrd kameravinkel skild från drivande video (relevant för "låst kamera / vidare bild"), Base 40 steg / Distillation 10 steg, 24 fps | Standard tunat för 8x A800, 720p; 480p testat på 2x A800 [V]. ComfyUI-stöd ej klart [V]. Kräver LLM-bildtext före körning | https://github.com/Wan-Video/Wan-Animate-2 |
| Wan 2.5 / 2.6 / 2.7 | Ingen öppen vikt hittad: Wan-AI på HF och Wan-Video på GitHub visar inget 2.5-2.7 [V]. Sidor som påstår "Apache-2.0 2.7" är SEO-källor och motsägs [S] | Wan 2.7 videoedit finns som API (se 3) | | https://huggingface.co/Wan-AI , https://github.com/Wan-Video |

Min bedömning [O, analys]: VACE styr med djup/pose från originalet. Då återskapas hela bilden, och ansikten och maträtter blir det modellen hittar på. För ägarens krav (datarikt) är det bättre att köra **masked V2V**: behåll originalpixlarna för personer (SAM2-mask), låt VACE bara generera bakgrund, utökad bildyta (outpaint/"Expand") och bort-stökad miljö. Det ska testas, jag har inte hittat någon rapport som visar det.

Praktiska begränsningar som slår mot era klipp:
- 81 rutor vid 16 fps ≈ 5 s. Era klipp är 6-15 s vid 30 fps. Måste omsamplas till 16 fps och delas i segment med överlapp, sedan interpoleras tillbaka. Segmentskarvar är en driftrisk [O].
- Kameraskak: djupkontroll från originalet för med sig skaket. Stabilisera (klassiskt) före, annars blir "låst kamera" inte låst [O].
- Identitetsdrift: Reddit-speglar jan 2026 rapporterar att VACE drifter i likhet och ger "mushy" detalj, att Animate ger bättre kontroll; allt anekdotiskt, inga benchmarks [S]. 1.3B-modellens 720p är "generellt mindre stabil", kör 480p [S, Runpod].

## 2. Andra motion-bevarande video-redigerare

| Alternativ | Pris (primär om [V]) | Gränser | Licens / EU | Passar läsbarhetsformat? |
|---|---|---|---|---|
| Runway Aleph 2 (`aleph2`) | 28 krediter/s, min 56 krediter/gen, 1 kredit = $0,01, alltså $0,28/s, 6 s ≈ $1,68 [V] https://docs.dev.runwayml.com/guides/pricing/ | Max indatalängd ej angiven [V]; 30 s/1080p enligt sekundär [S] | API-villkor ej läsna [O]. EU-tillgänglighet ej verifierad [O] | Instruktionsredigering, bra på "städa bort", sämre på exakt utvidgning av bildyta [O] |
| Luma Ray3.2 video-to-video | 720p: 360 krediter per 5 s, 540p 240, 1080p 720; HDR x2 [V] https://lumalabs.ai/api/pricing . Kreditpris i USD anges inte där [V]; FAQ-siffran 1,08 för 720p antyder ca $0,003/kredit (min inferens) [O] | Källa max 30 s; bildformat tas från källan; `image_ref` avvisas vid video_edit, alltså ingen referensbild [V] | Kommersiella villkor ej lästa [O] | Ingen referensbild, ingen utvidgning, men starkt på ljus/miljö [O] |
| Kling O1 edit (via fal) | $0,168/s, 3-10 s in, "bevarar rörelsestruktur och kamerarörelse" [V] https://fal.ai/models/fal-ai/kling-video/o1/video-to-video/edit ; Standard-nivån $0,126/s [S] | Indata 720-2160 px, max 200 MB [V] | Villkor/EU ej verifierade [O] | Bra bakgrundsbyte; behåller originalets kameraskak [V-text] |
| Wan 2.7 videoedit (Alibaba Model Studio, endast API) | $0,10/s 720p, $0,15/s 1080p (Singapore) [V] https://www.alibabacloud.com/help/en/model-studio/model-pricing | 2-10 s in, MP4/MOV ≤100 MB, upp till 4 referensbilder, 1-5 min körtid, 9:16 stöds [V] https://www.alibabacloud.com/help/en/model-studio/wan-video-editing-api-reference | Inte öppen vikt (se 1). Modell-Studio-villkor och EU-dataflöde ej lästa [O] | Instruktion + referensbild; ingen mask eller djupkontroll dokumenterad. Ändrar kläder/stil, utvidgning okänd [O] |
| Wan 2.1 VACE (Alibaba, `wan2.1-vace-plus`) | $0,10/s 720p, 50 s gratis kvot [V] samma prissida | | | Samma som VACE, hostad |
| LTX-2 / 2.5 V2V med IC-LoRA | fal LTX-2 19B v2v: $0,0018 per megapixel (bredd x höjd x rutor); 121 rutor 1280x720 = $0,20 [V] https://fal.ai/models/fal-ai/ltx-2-19b/video-to-video . 576x1024x144 rutor ≈ 85 MP ≈ $0,15 (min uträkning) | Förbehandlare depth/canny/pose på fal [S] | LTX-2.x Community License: gratis kommersiellt under $10 M årsintäkt, över kräver avtal; ingen territoriebegränsning i kortet [V] https://huggingface.co/Lightricks/LTX-2.5 ; fulltext LICENSE-2_x ej läst [O] | Billigast och snabbast hostat; kvalitet/motion-fidelity i detta bruk oprövad [O] |
| Seedance 2.0 edit | Officiellt ModelArk-pris ej laddat [O]; återförsäljare $0,056-0,112/s för 2.0-nivåer men oklart om de gäller edit [S] | | BytePlus: Seedance 2.5-API inte tillgängligt i USA [S] | Ni betalar redan ~9 400 krediter/6 s; ej iterationsbart |
| MiniMax H3 Max Recast (fal, nykomling) | $0,30/s 768p, $0,45/s 1080p [S, fal-listning via sök] | Byter personer mot referensfoton; tolkas för en person med synligt ansikte [S] | Okänt [O] | Fel verktyg: byter personer, restaurangscener har flera |
| HunyuanVideo-familjen | | | Tencent Hunyuan Community License utesluter EU, Storbritannien och Sydkorea [S, flera källor] https://huggingface.co/tencent/HunyuanVideo/commit/a4ed25a99d7eb9cf21e12f5fd8052d266f2105fc . Ingen edit-modell hittad. | **Utesluts** om bolaget eller användningen är i EU |

fal-flaggan: `fal-ai/wan-vace-14b`, `wan/v2.2-14b/animate/replace` och `wan-22-vace-fun-a14b/*` visar "tas bort 4 januari 2027" [V]. Bygg inte pipelinen på dem.

## 3. Kostnad per 6 s-klipp

### (a) Modal, självhostat
Modals prissida (https://modal.com/pricing) [V], per sekund: L40S $0,000542, A100-40 $0,000583, A100-80 $0,000694, H100 $0,001097, H200 $0,001261, B200 $0,001736. CPU $0,0000131/kärna, minne $0,00000222/GiB. Starter ger $30/mån gratis. (Er saldo $24,59 räcker alltså till ungefär 22 400 H100-sekunder.)

Genereringstid för 14B vid 81 rutor/480p finns ingen primärsiffra för. Spridda sekundärdata: ~85 s H100 för 33 rutor T2V 14B [S, Reddit]; ~190 s predict på Replicate för 81 rutor 480p [S]; ~4 min på H100 PCIe för Wan 2.2 14B [S, Spheron]; 1.3B ≈ 4 min på RTX 4090 [V, modellkort]. 720p kostar ca 4x tid enligt Runpod [S]. Tiderna nedan är därför **[O] uppskattningar**, mät en gång.

| Upplägg | Gen.tid (81 rutor) | Laddning + kallstart | Kostnad/körning |
|---|---|---|---|
| 1.3B, L40S, 480p | ~4 min | ~0,5 min | ca $0,15 |
| 14B, A100-80, 480p (offload) | ~6-8 min | ~1-1,5 min | ca $0,30-0,40 |
| 14B, H100, 480p | ~3-5 min | ~1 min | ca $0,25-0,40 |
| 14B, H100, 720p | ~12-20 min | ~1 min | ca $0,90-1,40 |

Kallstart: vikterna är ~28-34 GB (17B enligt HF-metadata [V], bf16 ~34 GB) plus T5 ~11 GB (min uppskattning [O]). Håll det snabbt:
1. Lägg vikter i en `modal.Volume` (Modal: ladda ner i förväg, inte vid start; Volume-läsning ~1-2 GB/s i ett Qwen-exempel, HF-nedladdning några hundra MB/s [S]) så 40 GB ≈ 20-40 s. Gör inlästa filer parallellt.
2. Kör alla tre format och alla iterationer i **en** container (`.map` eller en `@app.cls` med `@modal.enter`), så betalar ni laddning en gång.
3. Håll varm under en arbetssession: `min_containers`/`scaledown_window` (parameternamn kontrolleras mot nuvarande docs [O]). Inaktiv H100 kostar ca $3,95/tim (0,001097 x 3600).
4. GPU-minnessnapshot är **alpha**, bidrar mest till import/JIT och "kanske inte" vid vikt-laddning, `torch.compile` kan ge fel [V] https://modal.com/docs/guide/memory-snapshot . Förvänta er litet för 14B-laddning; CPU-snapshot av importer kan ge 3-10x för start [V, allmänt].
5. Bygg in alla beroenden (flash-attn) i bilden, inte vid start.

### (b) Hostade API:er (6 s, omsamplat till 16 fps vid fal)
fal debiterar per ruta vid 16 fps: 5 s vid 60 fps = 18,75 fakturerade sekunder [V] https://fal.ai/models/fal-ai/wan/v2.2-14b/animate/replace . Skicka alltså 16 fps, inte 30.

| Tjänst / modell | Pris | 6 s-klipp | Latens |
|---|---|---|---|
| fal `wan-vace-14b` (depth/pose/inpaint/outpaint/reframe) | $0,04/s 480p, $0,06 580p, $0,08 720p [V] | $0,24 / $0,36 / $0,48 | ca 1 min i exempel [V] |
| fal `wan-22-vace-fun-a14b/pose` | $0,05/s 480p, $0,075 580p, $0,10 720p [V] | $0,30 / $0,45 / $0,60 | ej angiven |
| Alibaba `wan2.1-vace-plus` 720p | $0,10/s [V] | $0,60 | ej angiven |
| Alibaba `wan2.7-videoedit` 720p | $0,10/s [V] | $0,60 | 1-5 min [V] |
| Alibaba `wan2.2-animate-mix` / `-move` | std $0,18 / $0,12 per s, pro $0,26 / $0,18 [V] | $1,08 / $0,72 (std) | ej angiven |
| WaveSpeed Wan 2.2 Animate | $0,04/s (720p $0,08/s), min 5 s fakturering [S] | $0,24-0,48 | ej angiven |
| fal LTX-2 19B v2v | $0,0018/MP [V] | ca $0,15 | ej angiven |
| fal Kling O1 edit | $0,168/s [V] | $1,01 | ej angiven |
| Runway Aleph 2 | $0,28/s [V] | $1,68 | ej angiven |
| Luma Ray3.2 V2V 720p | 360 krediter/5 s [V]; USD oklart [O] | ca $1,1-2,2 [O] | ej angiven |
| Replicate | GPU: L40S $0,000975/s, A100-80 $0,0014, H100 $0,001525 [V] https://replicate.com/pricing ; modellsidan för Animate-replace anger inget pris [V] | | |

Replicate GPU-tid är 1,4-1,8x dyrare än Modal per sekund, och modellprisen laddades inte, så jag räknar inte med dem. Latensen är sällan officiellt dokumenterad; "ca 1 min" för VACE på fal kommer från sidans exempel.

## 4. Praktikerrapporter och ComfyUI

Evidensen är tunn och mest sekundär (Reddit-speglar, guider); inga GitHub-issues kunde hämtas, så inget är "bekräftad bugg".
- VACE: "depth/pose-controlnets hanterar v2v, referensbilden driver utseendet" [S]; identitet drifter, detalj "mushy" jämfört med Animate [S]; styrka-reglaget byter likhet mot förändringsfrihet [S, Runpod]; bäst vid enkla/moderata poser, kontrollerad belysning, korta sekvenser [S, Runpod].
- Animate: artefakter och ansiktsdrift efter ~5 s, bakgrundsbrus; rekommendation: rena bakgrundsrutor, tät SAM2-mask, undvik kraftig feathering [S, Reddit mars-april 2026 via https://reddit.sentinel-team.org och https://help.scenario.com/articles/7564346085-wan-2-2-animate-models-the-essentials ].
- Arbetsflöden: officiell ComfyUI-dokumentation för VACE finns https://docs.comfy.org/tutorials/video/wan/vace [V finns, ej genomläst]; Kijai-moduler (bf16/GGUF) för Wan2.2-Fun-VACE [S]; kommuniteten rekommenderar Fun-VACE 2.2 framför VACE 2.1 [S].
- Ingen källa jämför rörelse/timing-fidelity kvantitativt. Det bör ni mäta själva (se 5).

## 5. Rekommendation

Format A (realistiskt, avstökat, låst kamera, vidare bild) väger tyngst; B/C testas bara som bakgrundsförenkling, med personerna kvar som originalpixlar.

**Verifiering (alla spår):** kör SAM 3D Body på resultatet, jämför mot originalets utdata per ruta (rotationsfel i leder, rotpositionens bana, tidsförskjutning via korskorrelation). Underkänn om driften överskrider er egen tröskel. Minns att fps-omsampling och segmentskarvar är de troligaste källorna.

**(i) Billig iteration, rangordnad**
1. fal `wan-vace-14b` 480p, ca $0,24/klipp [V pris], med depth/mask/outpaint-endpoints och referensbild. Snabbast att få svar på "fungerar masked V2V + utvidgning för A?". Tidsbegränsat: tas bort 4 jan 2027 [V], så använd bara för att välja format, inte som produktionsberoende.
2. Modal, Wan2.1 VACE 1.3B på L40S, 480p, ca $0,15/körning [O]. Behåller kontrollen över mask och segmentering och blir pipelinens skelett. Sämre kvalitet än 14B.
3. fal LTX-2 19B v2v, ca $0,15/klipp [V formel]. Som jämförelse, men licenströskeln $10 M intäkt och att IC-LoRA-kontroll är sekundärt belagd [S] gör den till tredje val.
4. Inte för iteration: Runway Aleph ($1,68), Kling O1 ($1,01), Luma, Seedance. Använd dem som referenspunkter för kvalitet vid enstaka körningar.

**(ii) Slutkörning med kvalitet**
1. Modal H100, Wan2.2 VACE-Fun A14B eller Wan2.1 VACE 14B, 720p, masked V2V med segment/överlapp, ca $1-1,4 per 5 s-segment [O]. Apache-2.0 på kod och vikter [V], inga territoriebegränsningar, full kontroll över drift-verifiering.
2. Jämförelsespår: Kling O1 ($1,01/klipp) och Wan 2.7 videoedit ($0,60/klipp) som semantiska redigerare om de ger bättre ansikts- och matdetaljer. De saknar mask/djupstyrning och bevarar kamerarörelsen, så "låst kamera" kräver stabilisering före.
3. Wan-Animate-2: intressant för text-styrd kameravinkel, men det är personersättning, kräver 2-8 A800 och är oprövat i flerpersons restaurangscener. Bara som sidoexperiment.
4. Hunyuan: uteslut om EU-användning; MiniMax Recast: fel verktyg.

**Kostnad för 3 format x 1 klipp** (skattat; EU-tillgänglighet och API-villkor för Runway/Luma/Kling är inte verifierade [O])

| Väg | En omgång (3 format) | Med ~4 försök per format |
|---|---|---|
| fal `wan-vace-14b` 480p | ca $0,72-0,75 | ca $3 |
| Modal 1.3B L40S | ca $0,45 + laddning | ca $2 |
| Modal 14B H100 480p | ca $0,75-1,2 | ca $4-5 |
| Modal 14B H100 720p slutkörning, 3 format | ca $3-4 | |
| Kling O1 som referens, 3 format | ca $3 | |

Hela testet ryms klart inom $24,59 Modal-krediten (ca 50-57 480p-körningar på H100 enligt min uppskattning). Mät riktig tid på H100 med en körning före allt annat, eftersom alla Modal-siffror är uppskattningar.

## Källor (primära markerade [V])
- https://github.com/ali-vilab/VACE [V]
- https://huggingface.co/Wan-AI/Wan2.1-VACE-14B [V]
- https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B [V]
- https://huggingface.co/Wan-AI/Wan2.2-Animate-14B [V]
- https://huggingface.co/Wan-AI/Wan2.2-Animate-2-14B , https://github.com/Wan-Video/Wan-Animate-2 [V]
- https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt [V], https://github.com/Wan-Video [V], https://huggingface.co/Wan-AI [V]
- https://modal.com/pricing [V], https://modal.com/docs/guide/memory-snapshot [V]
- https://replicate.com/pricing [V]
- https://www.alibabacloud.com/help/en/model-studio/model-pricing [V], .../wan-video-editing-api-reference [V]
- https://fal.ai/models/fal-ai/wan-vace-14b , .../wan-22-vace-fun-a14b/pose , .../wan/v2.2-14b/animate/replace , .../kling-video/o1/video-to-video/edit , .../ltx-2-19b/video-to-video [V]
- https://docs.dev.runwayml.com/guides/pricing/ [V], https://lumalabs.ai/api/pricing [V]
- https://huggingface.co/Lightricks/LTX-2.5 , https://github.com/Lightricks/LTX-2 [V]
- https://www.runpod.io/blog/the-dos-and-donts-of-vace [S]
- https://huggingface.co/tencent/HunyuanVideo/commit/a4ed25a99d7eb9cf21e12f5fd8052d266f2105fc [S, via sökträff, licenstexten ej själv öppnad]
- Reddit-speglar (reddit.sentinel-team.org), Atlas Cloud-bloggar, Picsart, WaveSpeed, Spheron, wan27.org [S]
