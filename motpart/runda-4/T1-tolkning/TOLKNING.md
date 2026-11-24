# T1: tolkning av ägarens ord 20 nov

T1, 20 nov 2026. Underlag: `motpart/runda-4/AGARENS_ORD_20NOV.md` (ordagrant, en rad: rad 3), repot, ägarens minne och ägarens Gemini-dialog 14 nov (`C:\Users\praiseworthy\Desktop\dialog.txt`, utanför repot, hänvisad från `byggsten/hand/README.md:19`). Inga betalda, generativa eller nätverksanrop. Det enda jag har kört är `lokalrum.py` i den här mappen (lokalt, numpy, läser bara `data/format/`).

Märkning: **[visat]** betyder att jag har kört eller läst det i fil. **[påstått]** betyder att en fil säger det, men jag har inte prövat det. **[antagande]** är mitt eget.

---

## 0. Kort

1. Orkestratorns läsning stämmer i stort. Den behöver rättas på tre punkter:
   - **Mellanstegen är ett prov, inte produkten.** Ägaren: "Det betyder inte att varje mellansteg mellan dem är användbar. Men det talar för pipen som 'ska' vara möjlig FÖR att effektivt, kostnadseffektivt kunna gå i olika riktningar."
   - **Båda klippen rör sig, och åt båda håll.** "re-kalibrera states i båda", "mot varandra, från varandra".
   - **Meningar avskaffas inte.** De är "bara ett exempel" på hur harnessen kan se ut, och de är expertens väg "över". Det som inte bär är ägarens *förklaringar* som träningssignal. Ägarens *val* bär.
2. Ägaren frågar rakt: **"Du har allt där?" Nej.**
   - **Finns:** materialet, nämligen cirka 13 000 klipp med metadata, 2 707 lokala kopior, lokala mått för 2 703 klipp och 1 480 formatkort. Det finns också en v0 av själva rörelsen: `byggsten/hand/rutt.py` (bron mellan två klipp över riktiga klipp) och `anpassa.py` (flytt mot en kund, klämd inom typen).
   - **Saknas:**
     - mått ur videon i användbar bildtakt (kopiorna har 2 bilder/s)
     - någon människas kalibrering av dimensionerna eller rutterna
     - en ömsesidig kompromiss
     - ett prövat mått på "mush"
     - ett sätt att utföra *tillförande* ändringar (ny lokal, ny talare) utan generering och utan den trasiga 3D-kedjan
3. Ägaren har sagt samma sak förut: vertikalerna 31 okt, "1000+ analyserade klipp … dataset" 13 nov, Gudfadern→Gump och "fingrar" 14 nov, och "miljontals axlar" 17 nov. Det nya 20 nov är **vem som dömer**. Det ska inte vara Claude, tolkande ägarens ord. Det ska vara klippbanken (det gemensamma och det som skiljer), publiken (utfall) och ägarens val.
4. **Mitt prov** (`lokalrum.py`, 0 kr):
   - 24 lokala mått utan språkmodell på 2 703 klipp har cirka 8 effektiva riktningar.
   - Riktningarna är gemensamma över konton: axlar från halva kontona förklarar 0,937 av den andra halvans egna.
   - En rak 50/50-blandning av två klipp hamnar nästan alltid inom täckningen (98 %), men tappar särprägel (0,81–0,83 av den svagaste ändpunkten). Det är mush.
   - Att flytta två mått helt mot B och låta resten stå ger särprägeln ×2,2, och 24–28 % hamnar utanför täckningen. Det är en Frankenstein-kombination.
   - **Täthet ensam belönar alltså mush.** "Utan mush" kräver två villkor, inte ett.
5. **Minsta pipe som prövar idén:** lokal ingest, rum, recept, snäppning mot riktiga klipp, utförande av det som går att utföra utan generering, ommätning och val. Tre första experiment (X1–X3) kostar 0 USD och cirka 25 minuter av ägarens tid.
6. **Bär mot detta:** essensspåret (mått, utfall, två domar), `byggsten/hand` (fingrar, rutt, anpassa), runda 3 D (medielager) och panelen i runda 4 A.
7. **Sidospår för just den här frågan:** 3D-kedjan (`forvarld_karna`, runda 3 B, arbetsbordets kropp), C:s router och grinddebatten. De kan bli förhandsvisning senare, men de ligger inte på vägen till att bevisa idén.

---

## 1. Läsning

### 1.1 Vad ägaren säger, punkt för punkt

Citaten är ur `AGARENS_ORD_20NOV.md:3`.

1. **Meningar är ett gränssnitt, inte harnessen.** "Tänk att meningar bara är ett exempel på hur harnessen i regibord/förvärld/cm-workstation kan se ut." CM:s mening är en möjlig yta. Harnessen är det som fattar besluten bakom ytan.
2. **Slingan genom Claudes förståelse har ett tak.** "Även om jag ger dig meningar, kommer din förmåga att få feedback av mig, förstå rätt kontra fel, hänga på din förståelse av innehållet." Taket har två skäl: (1) modellens träning och (2) att Claude inte kan läsa video. Även Gemini "på bästa settings/modell" måste arbetas runt.
   - Villkoret är uttalat: *om* ägarens feedback pekar mot ett glapp mellan tre saker, nämligen videoförståelse, övergripande funktionalitet och "sammansättning av hur visuell presentation i kontexten tiktok förmedlar mening".
   - Den tredje delen, hur sammansättningen bär mening, är det befolkningsgreppet ska ta.
3. **Befolkningen i stället för en läsare per klipp.** Ägaren vill ha "1000+ klipp som ingestas relativt lätt, utan en massiv overhead av produktion". En LLM som mappar allt visuellt är "sin egna superpower, men inte målet".
   - Klippen ska stå bredvid varandra: "det är vad som gör de gemensamma, det är vad som skiljer dem".
   - De ska röras "mot varandra inom de dimensionaliteterna, där de kan göra kompromisser i vad de ska 'härma'".
   - Ägaren säger "lika bra, minst lika bra". Det är ett andra sätt att tänka, inte uttryckligen ett som ersätter det första.
4. **Liknelsen har två lager.** "etniciteter … där de också har personligheter".
   - Ett drag (etniciteten) får gå helt över: den "kan brytas in till något som är som den andra".
   - Ett annat lager (personligheten) gör att varje mellanläge fortfarande är någon.
   - Kravet är alltså **inte** att dragen ska bevaras. Kravet är att ingen punkt på vägen får vara en "mush". Varje mellanläge ska vara ett sammanhängande, särskilt fall.
5. **Båda rör sig, åt båda hållen.** "re-kalibrera states i båda, tills att de rör sig mot varandra, från varandra". Ägaren frågar sedan rakt: "vad är de stegen? Du har allt där?"
6. **Rörelsen är ett prov på pipen.** "Det betyder inte att varje mellansteg mellan dem är användbar. Men det talar för pipen som 'ska' vara möjlig FÖR att effektivt, kostnadseffektivt kunna gå i olika riktningar."
   - Produktvärdet ligger i riktningarna. Exemplen: talking head eller matmontage till en annan lokal, samma manus med en kvinna i en annan scen, manusets energi långsammare, eller samma sak presenterad på ett annat sätt.
7. **Lite deterministiskt.** Ägaren pekar på sina egna exempel ("kollar man på prompten i hur jag just beskrev det") som öppna formuleringar. De behöver vara "lite deterministiska", annars blir det "för stort behov för att gå fram och tillbaka".
   - Skälet är kostnaden för iterationer, inte determinism som princip.
8. **Lovable-liknelsen.** En enkel prompt ger ett bra utfall därför att harnessen redan har en förväntan om vad användaren *typiskt* vill. Den följer också omvärlden ("vad som är trendigt") och utvecklas mot målgruppens nya viljor.
   - Harnessen respekterar innehållet och fattar "alla besluten … åt användaren".
   - Experten kan instruera "över" och tala med "den mer erfarna lyssnaren i harnessen".
   - Utan det fick användaren artikulera allt för utvecklarna. Ägaren placerar sig själv i användarens roll och Claude i utvecklarnas.
9. **Tekniken fungerar inte heller i dag:**
   - förvärlden renderar inte rätt
   - ingesten läser inte rummet rätt
   - kroppens rörelse återskapas inte likt
   - en karaktär kan inte anpassa sig till andra tillstånd och användbarheter i andra sammanhang
   - systemet förstår inte varför en modulering är framgång eller inte

### 1.2 Orkestratorns läsning prövad

| orkestratorns led | bedömning | skäl |
|---|---|---|
| Meningar och ägarens feedback räcker inte som styrsignal, eftersom modellens videoförståelse och smak är begränsad | **står, men ska skärpas** | Det som inte bär är ägarens *ord* som facit. Ägarens *val* bär. LeTrend läst ur ägarens transkript träffade 9 av 19 av ägarens val (`karta/videoforandring/essens.md:73`). "Ägarens ord, ägarens val och publikens utfall är tre olika saker" (`essens.md:391`). Ägarens smak träffar klippet som gått bäst mot kontot i 20 av 26 par (`karta/videoforandring/k1-del1.md:25`). Ord har ändå hjälpt till att *definiera* vad en dimension ska mäta: "Rörlighet = fart i iscensättningen … inte efterbearbetning" (minne `feedback-rorlighet-ar-iscensattning.md:11,15`). |
| 1000+ lätt ingestade klipp i gemensamma dimensioner | står | `AGARENS_ORD_20NOV.md:3` |
| "röra ett klipp mot ett annat" | **för smalt** | Båda klippen omkalibreras, och rörelsen går både mot och från. |
| kompromisser om vad som härmas | står | |
| distinktionerna blir inte mush | **står, men preciseras** | Ett drag får gå helt över. Det som skyddas är att varje mellanläge är ett sammanhängande, särskilt fall. Personligheten är kvar. |
| exemplen | står | |
| deterministiskt, inte öppna prompter | står | Skälet är kostnaden för att gå fram och tillbaka. Ägaren pekar på sin egen formulering som exemplet på en öppen prompt. |
| Lovable: harnessen bär förväntan, fattar beslut, följer publiken, experter instruerar "över" | står | Det saknas ett led: om systemet är outvecklat måste användaren artikulera allt. Det är just ägarens läge i dag. |
| tekniken fungerar inte | står | Fem delar, se 1.1 punkt 9. |
| (saknas hos orkestratorn) | **missat** | 1. Mellanstegen är ett prov på pipen, inte produkten (1.1 punkt 6). 2. Den raka frågan "Du har allt där?" (svar i 0 och 2). 3. Villkoret om glappet mellan videoförståelse, funktionalitet och sammansättning (1.1 punkt 2). 4. Att ingesten ska vara lätt och att en LLM som mappar allt "inte är målet". |

### 1.3 Ägaren har sagt det här förut, och det som är nytt

| när | ägaren | var |
|---|---|---|
| 31 okt–1 nov | Vertikaler: "dimensioner som ett klipp kan röra sig längs", parvis kalibrerade. Reglaget byter bara de scener som inte håller. | `video/kalibrering/vertikaler.mjs:1-2`; `karta/videoforandring/README.md:7,14` |
| 2 nov | "Bra" är relativt: mot kontot, kohorten eller banken | `karta/videoforandring/inlarning.md:128-132`; `byggsten/hjarna/PROBLEMBILD.md:269` |
| 13 nov | "det finns, och kommer finnas 1000+ analyserade klipp … det finns någon typ av dataset, bara att det inte finns en tydlig väg hur och varför det skulle lösa detta problem" | `byggsten/hjarna/PROBLEMBILD.md:245` |
| 14 nov | Gudfadern till Gump: "Det räcker inte bara med en otydlig/meshig ändring … det kräver hopp och gradvisa ändringar". "Behöver man definiera alla dimensionaliteter?" Sedan "fingrar på en hand", och frågan om distinktionerna är godtyckliga. | `~/Desktop/dialog.txt:2, 110, 195, 273` |
| 14 nov kväll | "inte en linje mellan två klipp, utan ett klipp i mitten och fingrar utåt" | `byggsten/hand/README.md:249` |
| 17 nov | "miljontals axlar som tenderar att ha en röd tråd", med begränsad feedback | minne `feedback-essens-inte-linjering.md:14` |

**Det nya den 20 nov:**
1. Claude kan inte döma, så ägarens ord som rättelse ger inget.
2. Harnessen ska bära smaken som Lovable gör, ur typiska användare och trender.
3. Determinism ska spara iterationer.
4. Ägaren säger öppet att tekniken bakom inte fungerar.

**Linjen mot handen (14 nov) är ingen motsägelse** [antagande]. Paret är provet på rummet, och handen (riktningar ut från ett klipp) är produkten. "Det talar för pipen … att kunna gå i olika riktningar" är handen.

---

## 2. Karta mot repot

### 2.1 Del för del

| ägarens del | vad som finns | visat | glapp |
|---|---|---|---|
| **1000+ klipp, lätt ingest** | 13 086 klipp med metadata (`byggsten/hand/ut/klipp.jsonl`, `wc -l`). 2 707 lokala mp4 i `~/Downloads/letrend-e13` (`ls \| wc -l`). 1 480 formatkort (`data/format/harness/bibliotek-v6.json`, fältet `antal`). Ingest v2 utan Blender: 0,0067–0,014 USD per klipp på L4 (`arbetsbord/ingest_v2/SKALNING_RAPPORT.md:22`), och utan SAM 3D Body 6,9–14,6 s (`:32`). | **[visat]** antal. **[påstått]** ingest v2: mätt på 2 klipp, skalningen till 100 är en projektion (`:42`). | **Kopiorna är 240×426 med 2 bilder/s** (`ffprobe` på `08burgerkebab-7673558402517241111.mp4`), och originalen är raderade (`karta/videoforandring/overlamning-17nov.md:66`). Rörelse, iscensättning och kamerarörelse går inte att mäta väl. Ingest v2 har spårnings- och höjdfel (`SKALNING_RAPPORT.md:50-63`). |
| **Dimensioner utan språkmodell** | `data/format/e28/tek.jsonl` (17 mått: skott, byten, rörelse, ljud, LUFS, LRA), `e30/tal.jsonl` (Silero VAD) och `e37/personer.jsonl` (YOLO), 2 703 rader vardera (`wc -l`). Per scen: 105 klipp analyserade med MediaPipe och OpenCV (`data/analys/*.json`). Egenskaperna kommer "ur analysen …, inget från en modell" (`video/kalibrering/egenskaper.mjs:1-2`). | **[visat]** Talsegment följer utfall på 744 osedda klipp, +0,128 (`essens.md:299`). Lokalt rum: 8 effektiva riktningar, gemensamma 0,937 (2.2). | **Lokalt tak:** bara talsegment håller. Personer i bild, talarbyten och en tvåaxlig poäng faller (`essens.md:371-384`). Inga mått för lokal, talare/röst, mat eller skärmtext i rummet. Talarinbäddning (WavLM) har körts i E35 (`essens.md:345`), men ligger inte i något rum. |
| **Dimensioner via läsare** (strukturerade frågor) | Sju fält ur motorn: +0,19 på replikeringen (`essens.md:103`), Argon +0,25 (`essens.md:112`). Fingrar i `byggsten/hand/ut/rum.jsonl` (1 480 kort), med regeln att ett finger bara styr om det finns belägg (`hand/README.md:317-332`). Inbäddningar: 10 911 × 384 för svag text och 2 302 motortexter (`data/format/e15/*.npy`, `np.load`). Axlarna är gemensamma, 0,93 (`essens.md:44`) och 0,84 (`essens.md:66`). | **[visat]** fält och utfall. **[visat]** 14 fingrar ger ungefär 8 oberoende riktningar (`byggsten/hand/ut/prov.json`, `effektiva_dimensioner`: deltagandekvot 9,24, 8 för 80 %). | Fri text bär högst cirka +0,1 (`essens.md:392`). Mekanik har tvillingkappa 0,45 och får inte styra (`hand/README.md:330`). Allt bygger på Geminis eller Fables text, inte på videon. Det är den beroendeform ägaren kallar "inte målet". |
| **Det gemensamma och det som skiljer** | `rutt.py`: "Handflatan bevaras: det ändpunkterna har gemensamt får inte röra sig" (`byggsten/hand/rutt.py:4`). `SKILLNAD = 0.3` avgör när ett finger räknas som en skillnad (`:30`). Ryggraden ger fingrar med kohortens p10–p90 (`hand/README.md:255`) och skiljer det som "ligger still" (typen) från det som "rör sig" (`hand/README.md:267-274`). Ramen mot konto, kohort och bank (`inlarning.md:128-132`). | **[visat]** i kod. Ingen människa har bedömt det (`hand/README.md:17`). | Ramen i tre koordinater är inte byggd (`inlarning.md:3`: "Inget av det är byggt än"). Typerna är tre fält ur kortet, och ägaren ska kalibrera dem (`hand/README.md:278`). |
| **Röra mot och från** | Bron notan → gelato: tio hållpunkter, var och en ett riktigt bevisklipp, med "tema mot förra" 0,97–1,00 (`hand/README.md:226-246`). Anpassa: kundens median per finger, "men aldrig utanför vad klipp av samma typ går (p10 till p90)" (`hand/README.md:37`). Reglaget 1–10 med tio verkligheter (`karta/videoforandring/README.md:12,52-60`). | **[visat]** att det körs. **[påstått]** att det är rätt: "Ingen människa har bedömt något av det" (`hand/README.md:17`). | **Enkelriktat:** "Styrande fingrar går mot målet, aldrig bort" (`rutt.py:5`). Ingen ömsesidig kompromiss och inget "från". Bilden är en blockout "med schablonmått" (`hand/README.md:227,372`). Mellanläget är *ett annat klipp* (bevisklipp), inte A förändrat. |
| **Utan mush** | `rutt.py:4`: "Varje hållpunkt är ett klipp som finns". Det är den enda inbyggda spärren. Språng redovisas när fler än två fingrar ändras (`rutt.py:27-29`). Gelato kan inte nås i steg om två (`hand/README.md:335`). | **[visat]** att regeln finns. Mitt prov visar att täthet ensam inte fångar mush (2.2). | Det finns inget prövat mått. Ingen människa har dömt ett mellanläge. Ägarens dialog efterlyser par där yta och mening går isär (`dialog.txt:324`). Det finns inte för dimensionerna. |
| **Deterministiskt** | Jev väljer bland lagliga drag. Koden utför och modellen ändrar aldrig tillståndet (`hand/README.md:138,176`). Förståndet skriver recept i ett slutet språk (`hand/README.md:138`). D:s operationer har 0 generativa anrop på 96 operationer (`motpart/runda-3-opus/D-medielager/RAPPORT.md:38`). B:s kedja är byte-identisk med `PYTHONHASHSEED=0` (`B-nasta-klipp/RAPPORT.md`, avsnitt 2). | **[visat]** i loggar. | Jev "varierar mellan körningar på oklara meningar" (`hand/README.md:205`). Dragens stegstorlek är satt av byggaren (`hand/README.md:204`). C:s router klarar 7 av 22 osedda meningar (`C-cm-mening/RAPPORT.md:8`). Det är meningsvägen som ägaren nu nedgraderar. |
| **Signal: publiken** (Lovables "trend") | Utfall `u` = log visningar minus medianen av ±10 grannar inom kontot (`overlamning-17nov.md:76`). Två motorer: visningar bärs av mötet, kommentarer och delningar av tilltal och uppmaning (`essens.md:342`). | **[visat]** och replikerat (`essens.md:301`). | **Brus:** `u` korrelerar bara +0,04 mellan klipp som följer på varandra, och sd är ×3,2 (`essens.md:271`). Ett enskilt publicerat utfall säger nästan ingenting om en enskild modulering. Kontotillväxt går inte att läsa (`essens.md:305-307`). Trender över tid har inte mätts [antagande: datum finns i `data/bank/*/lista.json`]. |
| **Signal: ägarens val** | Två domar: biblioteket (överförbarhet) och smaken. Smaken träffar publiken 20 av 26 (`k1-del1.md:19-29`). Väg aldrig ihop dem (minne `project-tva-domar.md:16`). Panelen i runda 4 är byggd med kontrollpar (`motpart/runda-4/A-domare/RAPPORT.md:74-84`). Bradley–Terry finns (`video/kalibrering/modell.mjs`; `inlarning.md:88`). | **[visat]** för klippval. | **Ingen ägardom på någon ändring** (`A-domare/RAPPORT.md:3,119`; T10 i `PROBLEMBILD.md:288`). Vertikalerna har 12 parvisa bedömningar, där 150 krävs (`data/bedomningar/rorlighet-uttryck.jsonl`, `wc -l`; `vertikaler.mjs:13`). Hittills 2 från ägaren och 10 från Gemini (`karta/videoforandring/NASTA.md:27`). |
| **Utföra: ta bort och ordna om** | D-medielager: skärmtext, ljud, b-roll och montage på riktiga filer, median 2,5 s (`D/RAPPORT.md:39`). | **[visat]** av D. | Klipp med minst 3 av 4 lager grönt: 1 av 20 (`D/RAPPORT.md:19`). Byt matbild: 0 av 20 ok (`:15`). |
| **Utföra: tillföra** (ny lokal, ny talare, ny rörelse) | 3D: `forvarld_karna/ut/` har 4 klipp (`ls`). Runda 3 B har en fryst allmän kedja. Arbetsbordet har Three.js. Kroppen kommer ur MaskedMimic och Kimodo. | **[visat]** att det fallerar: K4 faller som 1:1-krav, golv blir bord, fötter svävar, kroppar faller isär (`B/RAPPORT.md:9-16`). A1–A6 står (`motpart/PROTOKOLL.md:26-33`). Kinematisk känsla "ser ut som en apa" (`arbetsbord/STOPP_V2.md:6`). Kimodo fick KILL (`arbetsbord/RAPPORT.md:43`). C:s miljöer är "lådor, färger och etiketter" (`C/RAPPORT.md:12`). | **Det här är ägarens punkt 9.** K7 förbjuder generativ bild, video och röst i CM:s ändringsled (`motpart/runda-4/UPPDRAG.md:26`). Därför kan "samma manus från en kvinna" inte förhandsvisas med genererad röst eller bild. Kvar finns manus (det kunden spelar in), ett riktigt exempelklipp eller 3D. |
| **Förstå varför en modulering lyckas** | Tomrummen T3 (vad en ändring gör med poängen), T4 (ändringen värderad mot banken) och T9 (rörelsemodellen vet inte varför) (`PROBLEMBILD.md:281-287`). | – | Ingenting är byggt. Lärloopen från CM saknas (T11, `PROBLEMBILD.md:289`). |

**Leveransen:** "Manuset är produkten" (`inlarning.md:229-230`). Täckningskartan anger fyra lägen: original, original omformat, 3D-skiss och spela in. Kartan räknas fram och väljs inte av CM (`inlarning.md:182-192`). Det ger en färdig ram för att märka varje dimension med *hur* en flytt längs den kan utföras.

### 2.2 Mitt prov: ett rum utan språkmodell, och två sätt att få mush

Kör: `scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/T1-tolkning/lokalrum.py`

- **Underlag:** 2 703 klipp och 125 konton. 24 mått ur `e28/tek.jsonl`, `e30/tal.jsonl` och `e37/personer.jsonl`.
- **Behandling:** skeva mått på log-skala, sedan standardiserade. "Första X" saknas när X aldrig händer, och sätts då till klippets längd. Annars faller klipp utan tal bort.
- **Typ:** sållningstypen i `e15/klipp.jsonl`.

| fråga | utfall |
|---|---|
| effektiva riktningar | deltagandekvot 7,96; 8 av 24 axlar för 80 % |
| gemensamma över konton (som E15) | axlar från halva kontona förklarar 0,937 av andra halvans egna (min 0,918, 10 delningar) |
| täckning för riktiga klipp | avstånd till 5 närmaste riktiga klipp: median 2,13, 95:e percentilen 3,54 |

| mellanläge (1 500 par per rad, olika konton) | utanför täckningen | särprägel mot svagaste ändpunkt (median) | närmaste riktiga klipp har A:s typ / B:s typ |
|---|---|---|---|
| samma typ, rak 50/50 | 2,1 % | **0,83** | 61 % / 61 % |
| samma typ, två mått helt mot B | **23,6 %** | 2,19 | 61 % / 61 % |
| olika typ, rak 50/50 | 2,2 % | **0,81** | 33 % / 33 % (slump 28 %) |
| olika typ, två mått helt mot B | **27,5 %** | 2,20 | 41 % / 26 % |

Slumpnivån 0,276 är räknad ur typfördelningen: sketch 975, tilltal 787, matporr 641, annat 142, provsmakning 116.

**Läsning** (diagnos, inte krav):
1. **Det finns ett rum utan språkmodell, och det är gemensamt.** Det motsvarar E15 (0,93 på text) och fingrarna (8–9 riktningar). Talsegment, en riktning i det, följer utfall på osedda klipp (`essens.md:299`).
2. **Det finns två sätt att misslyckas, och de syns åt olika håll.**
   - **Mush:** den raka blandningen drar mot mitten. Den ser "typisk" ut och ligger inom täckningen, men har tappat det som skilde. När typerna skiljer sig är närmaste riktiga klipp av en tredje typ i cirka 34 % av fallen.
   - **Frankenstein:** att byta mått ett och ett bryter sambanden mellan måtten, och en fjärdedel hamnar där inga riktiga klipp finns.
3. **Ett mått på täthet belönar mush.** Den som mäter "ligger det nära riktiga klipp?" godkänner den raka blandningen. Därför behövs ett andra villkor om särprägel. Rutt v0 (`rutt.py:4`) undviker båda felen på ett annat sätt: hållpunkten *är* ett riktigt klipp. Det har inte prövats mot ögat.
4. **Gränser:** inget av de 24 måtten ser lokal, talare eller mat, alltså inte ägarens egna exempel. Mätt på 2 bilder/s. Särprägeln mäts i ett whitenat rum, och där blåser brutna samband upp avståndet. Typen är Geminis sållning.

---

## 3. Stegen

### 3.1 Vad en dimension är här

En **dimension** är ett mått per klipp (eller per scen) som uppfyller fem villkor:

1. **Har en källa som inte kräver att en modell förstår videon:**
   - (a) signalbehandling: ffmpeg, VAD, LUFS, skott, OCR-yta, YOLO-antal, homografi
   - (b) en inbäddning av en observation: talarröst (WavLM, `essens.md:345`), bildinnehåll per ruta [antagande: en bildinbäddning räknas som observation, inte tolkning]
   - (c) en *sluten observationsfråga* till en läsare, med uppmätt överensstämmelse mellan två läsare eller tvillingpar. Ett exempel är relation och insats, med tvillingkappa 0,71–0,80 (`hand/README.md:304-313`). Fri text räknas inte.
2. **Uttrycks relativt populationen:** percentil inom typ eller kohort, enligt ramen i `inlarning.md:128-132`, inte i absoluta enheter. Ett halvt snöre blir ett snöre först i förhållande till något (`inlarning.md:134`).
3. **Är stabil:** riktningen ska hålla när hälften av kontona hålls undan (prov 2.2 och E15). Ett mått som bara finns på de klipp där det hittades är ingen dimension.
4. **Är märkt med täckningsläge:** kan en flytt längs den utföras som *original omformat* (ta bort, ordna om, lägga på: D-medielager), som *spela in* (manus till kunden), som *3D-skiss* eller *inte alls* (`inlarning.md:182-192`).
5. **Har en ägare för betydelsen, inte för kalibreringen.** Ägarens ord får säga *vad* måttet ska fånga och vad det inte ska fånga, som "iscensättning, inte skak" (`feedback-rorlighet-ar-iscensattning.md:11,15`). Var klipp ligger och vad som är bra kommer ur populationen och valen.

Ägarens exempel, översatta till dimensioner:

| exempel | dimensioner | täckning |
|---|---|---|
| annan lokal | bakgrund, rumstyp | spela in, 3D-skiss [finns inte som mått i dag] |
| samma manus från en kvinna | talare och röst, person i bild | spela in. Förhandsvisning bara som exempelklipp (K7) |
| energin långsammare | skottlängd, byten per sekund, talsegment per sekund, pauser, LRA | spela in, delvis omformat (ta bort byten) |
| presenteras på ett annat sätt | tilltal mot spelad scen, person mot produkt | spela in. Ofta ett typbyte, som ryggraden stoppar (`hand/README.md:150`) |

### 3.2 Det gemensamma och det som skiljer, för ett par

För varje dimension *d* jämförs avståndet |A_d − B_d| med typens spridning (IQR inom kohorten):
- **Gemensamt:** avståndet är under en fjärdedels IQR. Det blir handflatan och rörs inte (`rutt.py:4`).
- **Skiljer:** avståndet är över en halv IQR. Det blir kandidatfingrar.
- **Ryggrad:** typ, inspelningsteknik och ton, längd och mening, och det mellan raderna (minne `project-ryggrad-och-intention.md:13-17`). Ryggraden låses som standard och får bara släppas genom ett uttryckligt val.
- **Gränserna (¼ och ½ IQR) är mina.** De är diagnos och ska kalibreras mot X1.

### 3.3 Kompromissen, uttryckt deterministiskt

Ett recept, inte en prompt:

```
recept/1 {
  a, b: klipp-id
  rum: "lokal-24" | "lokal+fält" | …           # vilka dimensioner
  harma: { a_fran_b: [d…], b_fran_a: [d…] }     # ömsesidigt: vad var och en tar
  grad:  { a: 0..1, b: 0..1 }                   # hur långt; >1 eller <0 = "från varandra"
  las:   [d…]                                   # handflata + ryggrad
  prio:  [d…]                                   # vid krock: vem har företräde (dialog.txt:243)
  max_per_steg: 2                               # som rutt.py:27
  klamma: "typens p10–p90"                      # som anpassa (hand/README.md:37)
  snap: "riktigt klipp" | "projektion"          # se 3.4
}
```

- **Samma recept ger samma utfall.** Spärren är hash plus `PYTHONHASHSEED=0`, som i B.
- **Mening blir recept.** En CM-mening eller en expertinstruktion "över" blir ett recept genom att välja bland `harma`, `grad` och `las`. Det är Jevs plats: att välja bland lagliga recept, inte att tolka fritt.
- **Standardvärden.** Utan instruktion kommer `harma`, `grad` och `las` ur standardvärdena i 3.5. Det är Lovables "beslut åt användaren".

### 3.4 Distinktion bevarad: vad det betyder och hur det mäts utan att bli krav

Ett mellanläge **bevarar distinktionen** när tre villkor gäller:
- **(i) Täckning:** det ligger där riktiga klipp finns (5-NN-avstånd inom 95:e percentilen för riktiga klipp, alltså relativt populationen och inte en egen siffra).
- **(ii) Särprägel:** det är inte mer "typiskt" än den mindre särpräglade ändpunkten. Avståndet till kohortens mitt ska vara minst lika stort som den ändpunktens.
- **(iii) Identitet:** de låsta dimensionerna ligger kvar inom A:s egen spridning. Prejudikatet är E14, där kundens egna undanhållna klipp kändes igen med AUC 0,94 (`essens.md:36`).

Provet i 2.2 visar att (i) ensamt godkänner mush och att (ii) ensamt godkänner Frankenstein. Båda behövs.

**Hur villkoren hålls som diagnos:**
- De publiceras aldrig som "lyckat".
- De gäller bara om de förutsäger ägarens blinda val i X1. Gör de inte det, stryks de.
- Gränserna sätts ur ägarens svar, inte av byggaren. Det är regeln i `feedback-egna-matt-ar-inte-krav.md:12` och `motpart/runda-4/UPPDRAG.md:25`.

**Två sätt att snäppa:**
- **(a) Riktigt klipp:** hållpunkten väljs bland de riktiga klipp som klarar (i)–(iii). Det är rutt v0, och mush är omöjlig per konstruktion. Men hållpunkten är någon annans klipp.
- **(b) Projektion:** målvärdet flyttas till närmaste punkt där (i)–(iii) gäller, och A:s eget manus ändras dit. Det blir A förändrat, men realismen går inte att garantera.

För produkten behövs (b). För att pröva rummet räcker (a).

### 3.5 Smaken som signal i stället för artikulerade meningar

1. **Publiken:** en frusen modell per typ, utfall `u` inom konto mot dimensionerna. Den ger förväntat Δu med intervall för en flytt.
   - Bara replikerade riktningar får vara standard: talsegment, sju fält, tal tidigt, "inte två klipp samma dag" (`essens.md:373`).
   - Två motorer hålls isär (visningar mot respons, `essens.md:342`). Det är Lovables "målgruppens viljor", och det är flerdimensionellt.
   - Modellen anpassas om på ett rullande fönster för "trend" [antagande, inte prövat].
2. **Ägarens smak:** parvisa val mellan *deterministiska alternativ*, utan krav på skäl. Valen ger en Bradley–Terry-skala, som redan finns (`inlarning.md:88`).
   - Biblioteksdomen och smaken samlas var för sig och vägs aldrig ihop (`project-tva-domar.md:16`).
   - Smaken är den enda läsaren som träffar publiken parvis (`k1-del1.md:85`).
3. **CM:s val:** godkänner, ångrar, väljer bort. Detta saknas (T11) och är den långsiktiga lärslingan.
4. **Ägarens ord:** används för att definiera och förbjuda vad en dimension mäter, och för expertvägen "över". De används inte som facit för var ett klipp ligger.

**Gräns:** ett enskilt publicerat utfall är brus (sd ×3,2, `essens.md:271`). "Förstå varför en modulering lyckas" går därför bara att lära på populationsnivå: frusen modell plus ägarens val. Det går inte från ett klipps siffror.

### 3.6 Stegen i ordning

| # | steg | ur vad | användbart som mellansteg? |
|---|---|---|---|
| 1 | Lätt ingest till observationer, inte tolkning | ny hämtning i ≥ 8 bilder/s (originalen raderade); ingest v2 utan SAM 3D Body, 7–15 s per klipp | ja, allt vilar på det |
| 2 | Rummet: dimensioner enligt 3.1, relativt kohorten, stabilitetsprov, täckningsläge per dimension | 2 703 klipp i dag; fler efter steg 1 | ja |
| 3 | Paret: gemensamt, skiljer, ryggrad (3.2) | rummet | ja; det är också CM:s förklaring ("det här delar de, det här skiljer") |
| 4 | Receptet (3.3), med standardvärden ur 3.5 | rummet och utfallsmodellen | ja |
| 5 | Snäppning mot data (3.4 a eller b) | rummet | ja; det är spärren mot mush |
| 6 | Utförande: omformat (D-medielager) där det går, annars manusdelta plus exempelklipp, 3D bara som valfri förhandsvisning | D, manus | delvis: bara subtraktiva dimensioner kan utföras på riktig film i dag |
| 7 | Ommätning av utfallet med samma ingest: landade det där receptet sa, och står låsningarna kvar? | steg 1 | ja; det är den minsta formen av "förstå om moduleringen lyckades" |
| 8 | Dom: förväntat Δu, ägarens parvisa smak, senare CM:s val. Uppdatera standardvärden och dimensioner. | 3.5 | ja |

### 3.7 Mellansteg som inte är användbara

- **Täta mellanlägen** (0,1, 0,2 …) som var och en renderas. Ägaren säger själv att de inte behövs.
- **Latent interpolation eller morfning av video.** Det ger mush per konstruktion (`dialog.txt:11`) och är generativt i ändringsledet (K7).
- **Fritextbeskrivningar av mellanlägen.** Fri text bär högst cirka +0,1 (`essens.md:392`), och det är den öppna tolkningen ägaren vill bort från.
- **3D-rekonstruktion av varje mellanläge, eller av varje klipp i banken.** B tog över 30 minuter på ett klipp utan att bli klar (`B/RAPPORT.md:8`). Det skalar inte till 1000+.
- **Ägarens skäl som träningsetiketter.** Ägarens val ska samlas, inte orden (1.2).

---

## 4. Första experiment, falsifiering, vad som bär

### 4.1 Minsta pipe

`klipp → lokala mått (steg 1–2) → par → recept → snäpp → (omformat | manus + exempel) → ommät → ägarens val`

Pipen kräver ingen 3D, ingen kropp och ingen generering. Den prövar idén (rummet, kompromissen och mush) skild från tekniken som ägaren säger inte fungerar. Det är en medveten avgränsning. Den bevisar inte att ett förändrat klipp kan *visas*. Den bevisar att harnessen vet vart det ska och vad som ska stå kvar.

### 4.2 Tre experiment, alla förregistrerade före ägarens svar

**X1. Ser ägaren mush och Frankenstein som rummet ser dem?**
- **Kostnad:** 0 USD, cirka 2 h bygge, ägaren cirka 10 min. Byggs på samma sätt som panelen i runda 4 A, men som en egen sida.
- **Material:** 12 par ur de 2 703 klippen: 4 av samma typ, 4 av olika typ och 4 inom samma konto. Låsta med frö.
- **Kandidater per par**, alla riktiga klipp:
  - K_blend: närmast den raka 50/50-blandningen
  - K_snap: flyttar två skiljande dimensioner minst halvvägs mot B och klarar (i)–(iii)
  - K_frank: närmast tvådimensionsbytet
- **Kontroller:**
  - en kandidat som är A själv: ska märkas "inte rörd"
  - en slumpad kandidat av en annan typ: ska inte väljas som "A med något av B"
- **Frågor, bara val:** (1) "Vilken är A som har tagit något från B?" (2) "Vilken är mest 'vilket klipp som helst'?"
- **Prognos:** K_snap väljs på fråga 1 i minst 7 av 12. K_blend väljs oftare än K_snap på fråga 2.
- **Fälls om:** K_snap väljs i högst 4 av 12 (slumpen är cirka 1/3), eller om fråga 2 inte följer särprägeln. Då bär de lokala måtten inte de distinktioner ägaren ser, och rummet behöver läsarfält eller nya videomått (lokal, talare) innan något mer byggs. Om fråga 2 inte följer (ii) stryks villkoret.
- **Svaghet:** kopiorna är 240p med 2 bilder/s, men ljudet är helt. Url:er finns i korten.

**X2. Ett reglage som går att utföra, i sluten slinga på riktiga filer.**
- **Kostnad:** 0 USD, cirka 3–4 h, ägaren cirka 10 min.
- **Dimension:** en som går att utföra utan generering, ljud (musik mot tal med Demucs) eller klipptempo (montage).
- **Material:** 10 par ur replikeringen.
- **Recept:** ömsesidigt där det är subtraktivt möjligt. Låst: talsegment och personer.
- **Utförande:** D:s frysta operatorer (anropas, ändras inte). Mät om med `e28-tek.mjs` och `e30_tal.py`.
- **Prognos:** minst 7 av 10 landar inom en fjärdedels IQR från målet med låsningarna kvar. Ägaren svarar ja/ja ("samma klipp?" och "syns ändringen?") på minst 6 av 10.
- **Fälls om:** utfallet inte rör sig dit receptet säger, eller om låsningarna bryts. Då finns inget deterministiskt reglage ens för de subtraktiva lagren, och pipen kan bara leverera manus.
- **Förväntan:** fel. D hade montage ok på 1 av 20 (`D/RAPPORT.md:19`). Det är just därför provet behövs.

**X3. Väljer publiken riktningen bättre än slumpen, utan ord?**
- **Kostnad:** 0 USD offline, ingen ägartid.
- **Modell:** frusen på biblioteket. Per typ ger den riktningen i rummet (lokala mått plus fält där de finns) som följer `u`.
- **Prov:** par inom samma konto i de osedda mängderna (960 i replikeringen och 744 i E34) som skiljer sig mycket på *en* dimension och lite på resten. Förutsäger riktningen vilket klipp som har högre `u`?
- **Prognos:** minst 55 % för talsegment, i linje med rho +0,13. Ägarens 26 smakpar redovisas bara som avläsning, eftersom de är för få.
- **Fälls om:** högst 52 %. Då kan de lokala måtten inte bära Lovables standardvärden, och standardvärdena måste komma ur läsarfält (Argon) eller ägarens par.
- **Gräns:** det här är observationsdata och inte en ingreppsstudie. Det säger att riktningen följer utfallet bland riktiga klipp, inte att en flytt orsakar det.

**Om alla tre faller** bär varken rummet, reglaget eller standardvärdena. Då återstår en stark läsare per klipp, alltså det ägaren kallar "inte målet". Det ska sägas rakt.

### 4.3 Vad som bär och vad som är sidospår, för just den här frågan

| del | bär? | skäl |
|---|---|---|
| Essensspåret (`video/format/e13–e42`, `data/format/e*`) | **ja, mest** | Mätmetoden (förregistrering, konton undanhållna, osedda klipp), utfallet `u`, lokala mått, fält och två domar. Det är det enda stället där mening har mätts pålitligt (minne `project-hjarna.md:28`). |
| `byggsten/hand` (fingrar, rum, rutt, ryggrad, anpassa) | **ja** | En v0 av ägarens idé med rätt ordförråd (handflata, finger, språng, klämning inom typen). Men den är oprövad mot ögat, bygger på text och är enkelriktad. |
| `video/kalibrering` (vertikaler, Bradley–Terry, reglaget) | ja, som form | Parvis kalibrering per dimension och "reglaget byter inte allt". Den saknar data: 12 bedömningar. |
| Runda 3 D, medielager | ja, för utförandet | Det enda icke-generativa sättet att utföra subtraktiva dimensioner på riktig film. |
| Runda 4 A, panelen | ja, som instrument | Blinda val med kontrollpar. Det är formen för ägarens smak som signal. |
| Ingest v2 (`arbetsbord/ingest_v2`) | delvis | Billiga observationer i skala om SAM 3D Body tas bort. Kvaliteten är oprövad i skala. |
| `forvarld_karna`, runda 3 B, arbetsbordets 3D och kropp, Kimodo | **sidospår här** | Per-klipps-1:1 som ägaren säger inte fungerar (`B/RAPPORT.md:9-16`, `PROTOKOLL.md:26-33`). Det skalar inte till 1000+. Möjligen förhandsvisning senare. |
| Runda 3 C (meningsroutern) | sidospår här | Meningsvägen som ägaren nedgraderar. 7 av 22 på osedda meningar. K7-loggningen och det ärliga nej går att återanvända. |
| Runda 1–2 (grindar, G7, rumsmått) | sidospår här | Hygien för 3D-kedjan, inte för rummet över klipp. |
| Liggaren och Jev på scenlagret | delvis | Jev som snabb väljare bland lagliga recept bär (`dialog.txt:193`). Liggarens frihetsgrader per tagning hör till 3D-utförandet. |

---

## 5. Svagheter i min egen analys

1. **"Meningar" är tvetydigt.** Ordet kan betyda CM:s meningar (gränssnittet, K1) eller ägarens rättelser i ord. Jag läser in båda, och slutsatsen (ord nej, val ja) lutar sig mot E18 och K1. Den lutar sig inte mot något ägaren har sagt om val just nu.
2. **Mush-provet är mitt eget mått.**
   - Särprägeln mäts i ett whitenat rum, där brutna samband blåser upp avståndet. Därför är ×2,2 för Frankenstein delvis en artefakt.
   - Tröskeln på 95:e percentilen och kvarten och halvan av IQR är mina.
   - Inget av det får användas förrän X1 har prövat det mot ägaren.
3. **Rummet jag har prövat innehåller inte ägarens exempel.** Lokal, talare och mat saknas bland de 24 måtten. Att det finns ett stabilt rum säger inget om att *de* dimensionerna går att mäta lätt. WavLM (E35) och en bildinbäddning är förslag, inte prövat.
4. **2 bilder/s och 240p.** Allt som rör rörelse och iscensättning är grovt mätt, och det är just de dimensioner ägaren definierade först (rörlighet).
5. **Typerna kommer från Gemini.** Kohortrelativa mått lutar då på en LLM-etikett. Det står i spänning med "inte målet".
6. **Snäppning mot riktiga klipp ger någon annans klipp.** X1 prövar rummet men inte produkten, A förändrat. Glappet mellan exempelklipp och A:s eget manus är olöst.
7. **Lovables "trend"** har jag tolkat som att utfallsmodellen anpassas om över tid. Ägaren kan mena omvärldsbevakning i bredare mening. Ingen trendanalys finns i repot.
8. **Jag har inte läst** liggarens svar (`delegat/svar/0031`, `0036`), `scen/3d/PIPE.md` eller `karta/vyer/`. Bedömningen att 3D-kedjan är ett sidospår vilar på B:s rapport och protokollet, inte på egen granskning av bilderna.
9. **Jag lutar mot essensspåret**, eftersom det har de starkaste siffrorna. Men de siffrorna gäller *val av klipp*. Ingen siffra i repot gäller en *ändring* (T10).
10. **"Mellanstegen är ett prov, inte produkten"** är min läsning av "det talar för pipen". En läsare som tar "röra dem mot varandra" som en funktion CM ska ha får en annan prioritet.
