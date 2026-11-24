# T2-tolkning av ägarens ord 20 nov 2026

## 1. Egen läsning före repot

Skriven efter att enbart ha läst `motpart/runda-4/AGARENS_ORD_20NOV.md` (rad 3, ett enda stycke).

1. **Meningar är ett exempel, inte svaret.** Om ägaren ger meningar (t.ex. "det här är ok") blir återkopplingen ändå beroende av att modellen förstår innehållet. Den förståelsen har två tak: modellens träning och att den inte läser video. Inte ens Gemini på bästa inställning förstår allt. Ägarens återkoppling pekar mot ett glapp mellan tre saker: videoförståelse, övergripande funktion, och hur den visuella sammansättningen förmedlar mening i TikTok-kontext. Slutsats: en styrsignal som går genom en LLM:s tolkning av en mening ärver LLM:ns blinda fläckar. Meningen "ger inget" eftersom mottagaren saknar ett sätt att bedöma.
2. **Byt perspektiv till populationen.** 1000+ klipp kan ingestas billigt. En LLM som visuellt kartlägger allt är en superkraft men inte målet. Frågan är: hur ställer man alla bredvid varandra och säger vad som är gemensamt, vad som skiljer, och rör dem mot varandra inom just de dimensionerna, där de kompromissar om vad de ska härma av varandra.
3. **Etniciteter med personligheter i en rad.** Två lager per klipp: en ytidentitet (utseende, plats, person, form) och ett beteende (energi, tempo, framförande). Gradvis omkalibrering av båda klippens tillstånd tills de rör sig mot eller från varandra men behåller distinktion. "Etnicitet kan brytas in till något som liknar den andra, men utan att bli mush på vägen." Jag läser det som två krav: (a) varje mellanläge ska vara ett trovärdigt eget fall, inte en överblandning av båda (på mångfalden, inte en linjär blandning av pixlar eller vektorer); (b) man rör en dimension i taget eller ett urval av dimensioner, inte allt samtidigt, så att resten av identiteten består.
4. **Alla mellansteg är inte användbara.** Ägaren kräver inte att varje punkt ska vara bra. Kravet är att pipen ska kunna gå i olika riktningar effektivt och billigt. Vilka punkter som är användbara avgörs någon annanstans (smak, publik).
5. **Konkreta riktningar:** talking head eller matmontage byter lokal; samma manus från en kvinna sätts i en annan scen; manusets energi ändras så att det går långsammare eller presenteras på annat sätt.
6. **Determinism.** Själva beskrivningen ("gör den långsammare") är en öppen prompt. Den måste bli något deterministiskt: en namngiven ratt med definierad verkan, så att man slipper öppna tolkningar och fram-och-tillbaka.
7. **Ägaren kan säga "det där är ok" men det hjälper inte**, eftersom han inte kan överföra sina upplevelsebaserade nyanser i en form modellen kan tolka. Smaken måste in som signal som inte kräver att han artikulerar.
8. **Lovable-liknelsen.** En bra harness har en förväntan om vad användaren typiskt vill ha, följer omvärlden och trender, och optimerar sig hela tiden mot målgruppens nya viljor. En enkel prompt räcker: harnessen respekterar innehållet och fattar alla relevanta beslut åt användaren. En erfaren användare kan instruera "över" och tala med den mer erfarna lyssnaren i harnessen. Ett outvecklat system (som vårt nu) missar känslan av framgång, och användaren tvingas artikulera allt för utvecklarna. Översatt: CM ska inte behöva förklara; systemet ska bära standardbesluten och lära sig av publiken; experten ska kunna styra explicit.
9. **Tekniken fungerar inte heller.** Förvärlden renderar inte rätt. Ingest läser inte rummet rätt. Kroppsrörelsen läses och återskapas inte tillräckligt likt. Även om den gjorde det kan karaktären inte anpassa sig till andra tillstånd och användbarheter i andra sammanhang, och systemet förstår inte varför en modulering lyckas eller misslyckas.
10. **"Du har allt där?"** är en fråga, inte ett påstående. Ägaren frågar om delarna finns i repot.

**Vad jag tror frågan egentligen är (före repot):** Hur ser en representation ut där klipp är punkter i ett rum med namngivna, mätbara axlar som man kan flytta längs, en i taget, med deterministiska operationer, där mellanlägena hålls på det som faktiskt förekommer i korpusen (inte mush), och där smaken kommer in som utfall (publik) och val (ägaren), inte som förklaringar? Och fungerar teknikkedjan bakom flytten?

**Min förhandshypotes:** "Dimension" måste vara något som mäts ur klippet utan att en LLM förstår det (t.ex. klipptakt, scenantal, talhastighet, kameraavstånd, plats-/personbyte som diskreta tillstånd). Mush undviks genom att flytt sker mot närmaste verkliga granne i korpusen (exemplar, inte medelvärde) och genom att diskreta dimensioner byts, inte blandas. Smak kommer in som parvisa val och publikutfall. Jag misstänker att 3D-förvärlden bara behövs för en del av riktningarna (lokalbyte med samma kropp), medan tempo/energi och manusbyte kan göras med billigare medel.

---

## 2. Läsning efter repot, och vad som ändrades

Märkning: **[Ä]** ägarens ord, **[Äb]** ägarens besked återgivet av en assistent i repot eller minnet, **[T]** min tolkning, **[A]** antagande, **[D]** egen diagnos som körts i den här mappen. `README.md`, `rutt.py`, `fingrar.py`, `samla.py` och `tillstand.py` utan sökväg avser filerna i `byggsten/hand/`. "Minnet" avser `~/.claude/projects/C--Users-praiseworthy-Desktop-hagen-wf/memory/`.

### 2.1 Idén är inte ny. Den finns i tre generationer som aldrig kopplats ihop

1. **31 okt, `video/`: vertikaler och reglaget.** "Vertikalerna: dimensioner som ett klipp kan röra sig längs" (`video/kalibrering/vertikaler.mjs:1`). Varje vertikal mäts ur klippet och kalibreras med parvisa bedömningar (Bradley–Terry, `video/kalibrering/modell.mjs:1-2`) innan den får ingå i en kombinerad vertikal. Grinden är 150 bedömningar (`vertikaler.mjs:12`). Principerna står i `karta/videoforandring/README.md:13-14`: "Värdet mäts, det deklareras inte" och "Reglaget byter inte allt … Det ska inte rycka". Ägaren sade då [Äb] att centrala vertikaler kalibreras före kombinerade och att "1-10000 olika uttryck" väljs med hänsyn till helheten (`karta/forvarld-underlag.md:28`).
2. **2–6 nov, harnessen.** Inlärningsplanen gör en deterministisk lösare med kostnadstermer (`karta/videoforandring/inlarning.md:26`), en sluten operationslista (`inlarning.md:38`) och en ram med tre koordinater: mot kontot, kohorten och banken (`inlarning.md:128-134`). Scenplanen fattar per takt beslut som behåll, byt produkt, byt lokal eller frontfigur, med regler ur doktrinen och utfallen (`video/format/h-scener.mjs:1-11`).
3. **14–16 nov, `byggsten/hand/`.** Fingrar (axlar), handflatan (det gemensamma), rutten och bron mellan två klipp via riktiga klipp, ryggraden per typ, anpassning mot kundens median inom typens spann, och Jev-drag som utförs av kod (`byggsten/hand/README.md:7-13`, `rutt.py:3-9`).

**Vad det ändrade:** frågan "du har allt där?" handlar inte om att uppfinna representationen. Den handlar om varför tre versioner av samma idé aldrig har kalibrerats mot ägaren eller fått en utförare som fungerar.

### 2.2 Tvåklippsbilden är ett prov på pipen, inte produkten

Efter ägarens besked 14 nov gäller "inte en linje mellan två klipp, utan ett klipp i mitten och fingrar utåt" [Äb] (`byggsten/hand/README.md:249`), och rutten "står kvar som prov" (`README.md:15`). I dag säger ägaren "Det betyder inte att varje mellansteg mellan dem är användbar. Men det talar för pipen som 'ska' vara möjlig FÖR att effektivt … kunna gå i olika riktningar" [Ä] (`AGARENS_ORD_20NOV.md:3`).

[T] Det går ihop. Interpolationen mellan två klipp är ett **diagnostiskt prov på representationen**: klarar den att röra två klipp mot varandra utan mush, så klarar den också riktningar utåt (lokal, person, energi). Den som bygger "bron" som produkt har missförstått. Den som bygger riktningar utan att kunna klara bron har ingen garanti mot mush.

### 2.3 Meningar faller av två skäl, inte ett

Jag läste först att meningar faller för att modellen inte förstår video (skäl 1 i ägarens text). Repot visar ett andra skäl: **ägarens egna ord och ägarens egna val är olika domar.**
- "det ägaren säger i samtalen och det ägaren väljer är två olika saker" (`karta/videoforandring/essens.md:77`). LeTrend läst ur ägarens transkript träffar 9 av 19 val (`essens.md:73`).
- Ägarens smak (val) träffar klippet som gått bäst mot kontot i 20 av 26 par. Biblioteksdomen (det han motiverar i ord: överförbarhet) ligger på slumpnivå (`karta/videoforandring/k1-del1.md:19-25`, `k1-del1.md:29`).
- Pro som parvis läsare träffar ägarens smak i 11 av 22 och läser "som en biblioteksdomare med premissbias" (`k1-del1.md:73,81`).
- Fri text bär inte mer än cirka +0,1 (`essens.md:392`). Promptens formulering förklarar cirka 0 % av variansen (`byggsten/hjarna/PROBLEMBILD.md:311`).
- När systemet själv uppfyllde meningen "uttråkad" på sina egna ledmått såg det ut "som en apa" (minnet `feedback-kansla-ar-helkropp.md:11-13`).

[T] Ägarens mening "det där är ok" bär alltså biblioteksdomen bättre än smaken, och modellen som tar emot den har varken sensorn (video) eller dimensionen där nyansen bor. Det är därför meningar "inte ger något". Det är inte en åsikt. Repot har mätt det.

### 2.4 Rundan som pågår mäter fortfarande meningsvägen

Runda 4:s mål är "en CM skriver en mening om ett riktigt 9:16-klipp" (`motpart/runda-4/UPPDRAG.md:6`). K1 bygger på frysta CM-meningar (`motpart/runda-1-claude/SYFTE.md:154-159`), och ägarpanelen visar en mening per par (`motpart/runda-4/A-domare/RAPPORT.md:41`). [T] K2:s metod, blinda val med kontrollpar, ligger i linje med dagens ord. Innehållet i panelen prövar däremot meningsvägen, som ägaren nu kallar ett exempel bland flera. Det bör orkestratorn veta innan K1 får styra nästa bygge.

### 2.5 Tekniken: ägarens dom stämmer med repots egna fynd

Se tabellen i 3.10. Inget i repot motsäger "förvärlden renderar inte rätt, ingest läser inte rummet rätt, kroppen kan inte anpassa sig".

### 2.6 Det jag ändrade i förhandshypotesen

- "Dimension mäts utan LLM" höll bara delvis. Min diagnos [D] (`diagnos_modellfri.py`, `diagnos_modellfri.json`) visar att 19 modellfria mått bär **kontots identitet** (närmaste granne samma konto 0,116 mot slump 0,012) men nästan inte **typen** (0,442 mot majoritet 0,388, LLM-fingrar 0,517). Repots eget "lokala tak" säger samma sak för utfall: bara talsegment håller utan modell (`essens.md:371-384`). [T] Ytan, det som liknar "etniciteten", syns utan LLM. Det som gör klippet till en viss sorts innehåll kräver en läsare. Läsaren får sätta koordinater i slutna fält med mätt pålitlighet, men den får inte vara domaren.
- "Mush undviks genom att gå mot närmaste verkliga granne" höll, och diagnosen gör det mätbart (avsnitt 4.4).

---

## 3. Karta mot repot, med belägg

Status: **visat** = körning eller fil som visar det, **påstått** = står i text utan prov, **saknas**.

### 3.1 "Meningar ger inget som styrsignal"
| vad | var | status |
|---|---|---|
| Ord och val skiljer sig | `essens.md:74-77`, `k1-del1.md:13-29` | visat (n = 19 och 26 par) |
| LLM missar smaken | `k1-del1.md:73-81` (E42) | visat |
| Fri text tak cirka +0,1 | `essens.md:148-156,392` | visat, replikerat negativt |
| Meningsvägen lever ändå kvar i rundans mål, i Jev och i förståndet | `runda-4/UPPDRAG.md:6`; `byggsten/hand/README.md:124-141` | faktum |
| **Glapp:** det finns ingen oberoende sensor i slingan mening → LLM → utförande → bedömning. Bedömaren är samma slags modell som tolkaren. | `PROBLEMBILD.md:258` ("Ingen domare finns" för meningen) | saknas |

### 3.2 "1000+ klipp ingestas lätt"
| vad | var | status |
|---|---|---|
| 13 086 klipp i fem metadatalager | `byggsten/hand/samla.py:32-87` | visat |
| 1 480 formatkort med mall och platser | `data/format/harness/bibliotek-v6.json` (`antal: 1480`) | visat |
| Modellfria mått: 2 703 rader i `e28/tek.jsonl`, `e30/tal.jsonl` och `e37/personer.jsonl`; 1 952 i `tempo/matt.jsonl` | `wc -l` körd 20 nov | visat |
| Ytlagren L3 är lästa av `gemini-3.1-flash-lite` | `samla.py:50-51` | visat. Billigt men en LLM-läsning |

### 3.3 "Ställ dem bredvid varandra: vad är gemensamt, vad skiljer"
| vad | var | status |
|---|---|---|
| 14 fingrar i två sorter, yta (L3) och mening (L4) | `byggsten/hand/fingrar.py:1-8,112-128` | visat |
| Cirka 8 effektiva dimensioner (8 för 80 % av variansen, deltagandekvot 9,24) | `byggsten/hand/ut/prov.json`, nyckeln `effektiva_dimensioner`; `README.md:332` | visat |
| Per typ: det som ligger still (typens identitet) och det som rör sig | `byggsten/hand/ut/typer.md:5-8`; "Det som ligger still är vad typen är" (`README.md:274`) | visat som beräkning |
| Gemensamma axlar över konton: 0,93 (svag text), 0,84 (motor) | `essens.md:44,66` | visat |
| Motor mot yta: kontot gissas ur närmaste granne 0,13 ur motorn, 0,60 ur ytan | `essens.md:61-63` | visat |
| **Glapp:** ingen människa har bedömt något av det (`README.md:17`). Ingen visuell inbäddning utan LLM-text finns (sökning på siglip, dinov2, videomae i `video/`, `karta/` och `byggsten/` gav bara rumshypotesens förslag, `byggsten/rumshypotes/EXPERIMENT.md:245`). | | saknas |

### 3.4 "Röra dem mot varandra inom dimensionerna, med kompromisser"
| vad | var | status |
|---|---|---|
| Ett klipp rör sig mot ett annat via verkliga klipp, högst två fingrar per hopp, handflatan låst | `rutt.py:3-9,27-28`; bron notan → gelato `README.md:226-246` | visat som beräkning, blockout med schablonmått |
| Ett klipp rör sig mot kundens median, aldrig utanför typens p10–p90 | `README.md:37` | visat som beräkning |
| En dimension (rörlighet) med reglage, tröghet, "hem" och skyddsräcken | `karta/videoforandring/README.md:69-75`; `video/src/forandring/motor/valjare.js:5-9` | visat för kamerauttryck på ett fåtal klipp |
| **Glapp:** båda rör sig mot varandra (kompromiss) finns inte. Rutten flyttar ett klipp. Anpassningen flyttar mot en median. Resultatet är bevisklipp eller dockor, inte det flyttade klippet. "Handen följer bara delvis med" (`README.md:114`). | | saknas |

### 3.5 "Utan mush, med distinktion"
| vad | var | status |
|---|---|---|
| Handflatan bevaras, varje hållpunkt är ett riktigt klipp, språng redovisas | `rutt.py:4-6,28` | visat |
| Typens spann som räcke | `README.md:37,274` | visat |
| Ryggradens fyra delar ärvs; utbyte sker på funktion | minnet `project-ryggrad-och-intention.md:13-21` | [Äb] |
| Ägaren värderar att innehållet "sticker ut, eller blir platt om allt är likadant" | `k1-del1.md:48` | [Äb] ur transkript |
| **Glapp:** inget mått på distinktion efter en flytt. Inget perceptuellt prov av mush. Min diagnos i 4.4 är första räkneexemplet. | | saknas |

### 3.6 "Etniciteter med personligheter"
[T] Två lager som kan röras var för sig. Repot har uppdelningen på tre ställen: yta mot mening (`fingrar.py:3-5`), yta mot motor (`essens.md:58-68`) och ryggradens "inspelningsteknik och ton … den 'mänskligheten' ärvs" (minnet `project-ryggrad-och-intention.md:15`).
- Personligheten i kroppen (attityd) prövades kinematiskt och föll: "apa" (minnet `feedback-kansla-ar-helkropp.md:11`) och stopp av v2 (`arbetsbord/STOPP_V2.md:5-9`).
- Personligheten i framförandet (tal, tempo, klippning) är mätt modellfritt men har ingen operator för tal (se 3.9).
- **Glapp:** ingen representation håller isär "vem/var" och "hur" så att de kan röras oberoende i ett och samma klipp.

### 3.7 "Deterministiskt, inte öppna prompter"
| vad | var | status |
|---|---|---|
| Jev väljer bara; `tillstand.py` utför | `README.md:176` | visat |
| Medielagret: ffmpeg, Demucs och Pillow, 0 generativa anrop, felinjektion 32/32 | `motpart/runda-3-opus/D-medielager/RAPPORT.md:37-39` | visat |
| Dragens storlek är byggarens ("halvera en takt, kontrast gånger 1,4"), Jev varierar mellan körningar på oklara meningar | `README.md:204-205` | visat som brist |
| Förståndet är den öppna vägen (13–19 s, LLM skriver recept) | `README.md:124-141` | visat |
| **Glapp:** inga steglängder är kalibrerade i dimensionens enhet (kvantil inom typen). Ett drag mäts inte efteråt mot sin dimension. | | saknas |

### 3.8 "Smaken kommer in utan meningar"
| vad | var | status |
|---|---|---|
| BT per vertikal med aktiv parval (`nastaPar`) | `video/kalibrering/modell.mjs:26-44,100-123` | byggt |
| Bedömningar i `data/bedomningar/rorlighet-uttryck.jsonl`: 12 rader, 10 av `gemini-3-flash-preview` och 2 av `cm` | körd gruppering 20 nov | visat: nästan tomt |
| "endast 12 visuella uttrycksbedömningar … inte ett färdigt dataset av önskemål → korrekta edits" | `karta/forvarld-underlag.md:137` | visat |
| Ägarens smak som egen etikett ("which one do you like more as content") | `overlamning-18nov-k1.md:73` | förslag, inte gjort |
| Blind parpanel med kontrollpar | `motpart/runda-4/A-domare/RAPPORT.md:74-84` | byggt, ingen dom ännu |
| **Glapp:** ingen etikett finns på ändringar eller på lägen längs en dimension (T10 `PROBLEMBILD.md:288`), och ingen lärslinga från CM (T11 `PROBLEMBILD.md:289`). | | saknas |

### 3.9 Lovable-liknelsen: harnessen fattar besluten, följer publiken, experten kan styra över
| del | i repot | status |
|---|---|---|
| Standardbesluten åt användaren | scenplanen (`h-scener.mjs:1-11`), anpassning mot kundens median (`README.md:37`), doktrinen | byggt, regler skrivna av assistent |
| Följer publiken | residual inom konto, metaanalys, två motorer, replikerat på osedda klipp (`essens.md:287-301,342`) | visat för färdiga klipp |
| Experten styr över | regibordet: drag, avsikt, lärda drag (`README.md:85-98,136-140`) | byggt, ingen människa har använt det |
| **Glapp:** publiken har aldrig sett en ändring. "Metaanalysen vet vad som lyfter klipp men har aldrig sett en ändring" (T4 `PROBLEMBILD.md:282`). Standardbesluten lär sig inte av utfall. | | saknas |

### 3.10 "Tekniken fungerar inte heller"
| ägarens punkt | belägg | status |
|---|---|---|
| Förvärlden renderar inte rätt | hold-out: kroppar faller sönder i lemmar, golvet blir ett matbord, en skiva svävar i huvudhöjd (`B-nasta-klipp/RAPPORT.md:92-93,129`) | visat |
| Ingest läser inte rummet rätt | kamerahöjden är `antagen` i 20 av 20 tagningar och bestäms av möbelns prior; telefonpriorn ensam ligger närmare facit än kedjan på faros_7540 (`B/RAPPORT.md:121,128`); grindarna tysta för 176 av 243 fel (`motpart/PROTOKOLL.md:30`) | visat |
| Kroppen återskapas inte tillräckligt likt | 11 av 21 person-tagningar fallerar mot oberoende 2D (`PROTOKOLL.md:28`) | visat |
| Kroppen anpassar sig inte till andra tillstånd | "apa" (minnet); Kimodo KILL på egna mått (`arbetsbord/RAPPORT.md:43-52`); "Rörelsemodellen vet inte varför" (T9 `PROBLEMBILD.md:287`) | visat |
| Ingen förstår varför en modulering lyckas | "Ingen modell för vad en ändring gör med poängen" (T3 `PROBLEMBILD.md:281`) | visat som tomrum |
| Ordnivån | routern rätt nivå på 7 av 22 osedda meningar (`C-cm-mening/RAPPORT.md:8`) | visat |
| Medielagret | 3 av 4 lager i bara 1 av 20 klipp; b-roll 0 av 20 (`D-medielager/RAPPORT.md:13-19`) | visat |

### 3.11 Ägarens konkreta riktningar
| riktning | närmast i repot | glapp |
|---|---|---|
| Talking head eller matmontage byter lokal | `byt_lokal` på manusnivå (`byggsten/hand/tillstand.py:147,335`); scenplanens `byt_lokal` (`h-scener.mjs:7`); arbetsbordets rum/miljö i Three.js (`A-domare/RAPPORT.md:47`) | lokalen är ett ord, inte en läst lokal (`README.md:61`); 3D-lokalbyte vilar på rumsläsningen som fallerar |
| Samma manus från en kvinna i en annan scen | `frontfigur` i scenplanen; `personer_upp` | inget personbyte med bevarat framförande |
| Manusets energi långsammare, annat framförande | vertikalerna rörlighet, agerande och rytm (`vertikaler.mjs:14-72`); montage −30 % i D (`D/RAPPORT.md:16`); tal och tempo mätta modellfritt | ingen operator för talets tempo eller pauser; montage-kortningen gav `ok` i 1 av 20 |

**Svar på "Du har allt där?":** [T] Nej. Representationens delar finns, i tre okopplade versioner. Det som saknas är (1) smaken som etiketter på lägen och ändringar, (2) ett mått på distinktion och mush efter en flytt, (3) kompromiss där båda rör sig, (4) operatorer som mäts mot sin egen dimension, och (5) en utförare för de riktningar som kräver ny iscensättning.

---

## 4. Stegen: två klipp mot och från varandra längs dimensioner, utan mush

### 4.1 Vad en dimension är
[T] En dimension är fem saker. Saknas en av dem är det något annat:
1. **Mätning** `f(klipp) → värde`, reproducerbar. Antingen modellfri (ffmpeg, VAD, YOLO, optiskt flöde, OCR, Demucs), eller ett slutet fält läst av en modell med uppmätt pålitlighet (två läsare eller tvillingkappa, som `README.md:317-330` redan gör). *Utan mätning är det en prompt.*
2. **Läge inom typen**: kvantil mot typens fördelning (p10–p90, `README.md:37`) och mot kontot, kohorten och banken (`inlarning.md:128-134`). Ett snöre har ingen längd utan ram (`PROBLEMBILD.md:269`).
3. **Operator** `op(tillstånd, mål) → tillstånd'` på ett namngivet lager: manus/takter, medielager eller förvärld. *Utan operator är det bara en beskrivning.*
4. **Kontroll efteråt**: `f(op(x)) ≈ mål` mäts på resultatet ("Värdet mäts, det deklareras inte", `karta/videoforandring/README.md:13`).
5. **Koppling**: vilka dimensioner som rör sig tillsammans. Lånat ljud och eget tal har rho −0,69 (`prov.json`, `starkast_bundna`). Kopplade dimensioner flyttas som ett block.

Mätningen kräver inte att en LLM förstår videon. Där en läsare behövs (typ, relation, insats) läser den slutna fält vid ingest, och fältet får styra bara om pålitligheten är mätt. Läsaren dömer aldrig om en ändring blev rätt.

### 4.2 Pipen, steg för steg
1. **Ingest till koordinater.** Modellfria mått och slutna fält per klipp. Takterna med tid (T1 `PROBLEMBILD.md:279` saknas i dag).
2. **Identitet och rörligt per typ.** Det som ligger still inom typen är typens identitet, och det som rör sig är rörligt (`typer.md`). Ryggradens fyra delar låses (minnet `project-ryggrad-och-intention.md:13-17`).
3. **Paret läggs bredvid varandra.** Handflatan är där A och B är lika, och det som skiljer är där |A−B| är över tröskeln (`rutt.py:84-86`).
4. **Kompromissvektorn.** Per dimensionsblock som skiljer: `A`, `B`, `håll` eller `mål-kvantil q`. Det är data, deterministiskt, går att ångra och går att jämföra. "Mot varandra" betyder att båda får varsin vektor. "Från varandra" betyder att man går bort från den andras värde, men bara inom typens spann.
5. **Stödprov.** Det nya läget måste ha verkliga grannar i banken. Annars är det ett språng, som rutten redan redovisar (`rutt.py:28`).
6. **Distinktionsprov** (4.4).
7. **Utförande per lager:** manus (byt lokal, produkt, person, replik), medielager (tempo, pauser, text, ljud, montage) och förvärld (kamera, kropp) bara där ny iscensättning krävs. Varje operator mäts efteråt.
8. **Standardvektorn** (Lovable): harnessen väljer vektorn åt CM ur kundens linje, typens räcken och publikens riktning. CM ser resultatet. Experten ändrar enskilda poster i vektorn i stället för att skriva en mening.
9. **Lärslingan.** Varje förslag, godkännande och ångring loggas med sin vektor. Ägarens och CM:s parval tränar vikterna (BT finns). Publicerade utfall tränar standardvalen när de kommer.

### 4.3 Hur distinktionen bevaras och mäts
[T] Tre mått, alla räknebara utan LLM i domen:
- **Särprägel:** avståndet till typens eller populationens mitt. Mush är när det sjunker.
- **Stöd:** avståndet till närmaste verkliga klipp, delat med medianavståndet mellan verkliga klipp. Ett läge utan stöd är "Frankenstein", inte mush.
- **Igenkänning:** A' ska ligga närmare A än B i de block som inte byttes, och kontot ska fortfarande gå att känna igen. Modellfria mått bär kontot (0,116 mot slump 0,012 [D]), så igenkänningen kan mätas utan läsare.

### 4.4 Diagnos [D]: medelvärde, slumpkorsning och vald korsning
`diagnos_modellfri.py` på 978 klipp i 7 typer, 19 modellfria mått, 448 par av olika typ (`diagnos_modellfri.json:56-111`):

| läge | särprägel (median) | stöd (median) | andel med stöd som ett verkligt klipp |
|---|---|---|---|
| A, verkligt klipp | 4,27 | 1,01 | 0,48 |
| **medelpunkt** av A och B | **2,91** (−32 %) | 0,97 | 0,59 |
| slumpkorsning (varje mått helt från A eller B) | 4,29 | 1,26 | **0,10** |
| **vald korsning** (bästa av högst 64 masker, 30–70 % bytt) | 4,20 (−1,5 %) | 0,89 | **0,82** |

[T] Medelvärdet ser rimligt ut (det har stöd) men tappar en tredjedel av särprägeln. Det är ägarens mush: trovärdigt och generiskt. Att byta dimensioner på måfå behåller särprägeln men ger kombinationer som banken inte har. Att **välja vilka dimensioner som byts** under ett stödvillkor behåller båda. Kompromissen ska alltså vara ett val av vem som härmar vem, block för block, och inte ett medelvärde.

Förbehåll: det är ett räkneexempel i ett mätrum, inte en perceptuell dom. Den valda korsningen är vald *på* stöd, så stödsiffran är optimistisk. Poängen är att det går att hitta sådana lägen och samtidigt behålla särprägeln. Typen i provet är en LLM-läsning.

### 4.5 Hur kompromissen uttrycks deterministiskt
Som en vektor över namngivna block, till exempel `{lokal: B, frontfigur: A, tal_per_s: q35, klipprytm: håll, typ: låst}`. Samma vektor på samma klipp ger samma tillstånd och samma mätta värden. CM:s mening, om den alls används, översätts till en ändring i vektorn och visas som en sådan. Den blir aldrig ett eget recept. Det är den skillnad som `README.md:176` (Jev väljer, koden utför) redan pekar mot, men där stegen i dag har byggarens storlekar.

### 4.6 Hur smaken kommer in utan meningar
- **Parval och trioval.** "Vilken gillar du mer som innehåll?" (smaken, `overlamning-18nov-k1.md:73`) och "Vilken av B och C liknar A mest?" (perceptuellt avstånd, inga ord). Det ger BT per block och prövar om mätrummets avstånd är ägarens avstånd.
- **Publiken** som prior över regioner i rummet (residual inom konto), skild från ägarens bibliotek. De vägs inte ihop (minnet `project-tva-domar.md:16`).
- **CM:s handlingar:** godkänn, ångra, ändra post i vektorn.
- Experten instruerar "över" genom att låsa eller sätta poster i vektorn.

### 4.7 Mellansteg som är användbara på egen hand
1. **Uppställningen:** verkliga klipp sorterade längs en mätt dimension. Den ger ett perceptuellt prov utan rendering.
2. **Bevisklipp som förhandsvisning:** ett verkligt klipp som redan ligger i målläget visar hur läget ser ut (rutten gör det redan, `README.md:226-246`).
3. **Manus och medielager:** de riktningar som inte kräver ny iscensättning (tempo, pauser, text, ljud, montage, byte av replik eller produkt i takten). Produkten är manuset (`inlarning.md:229-230`).
4. **3D** kommer sist, som en operatorfamilj för lokal och kropp.

---

## 5. Är det här ens rätt väg? Den starkaste invändningen

**Den enklare tolkningen.** Allt detta är formatkort, ryggrad och utbyte på funktion i ny förpackning. `byggsten/hand` har redan axlar, handflata, rutt, typens spann, standardval mot kunden och Jev-drag (avsnitt 3.3–3.5). Mitt "kompromissvektor" är rutten med två ändpunkter som båda får röra sig. Om det är så, är nästa steg inte att bygga något nytt. Då ska ägaren kalibrera det som finns (`README.md:391-393` står redan som nästa steg), och 3D-förvärlden behövs inte för de flesta riktningarna eftersom kunden spelar in själv efter manuset (`inlarning.md:229-230`).

**Mitt svar:** jag håller med om det mesta. Min slutsats är just att representationen finns och att kalibreringen och utförandet saknas. Tre saker är ändå nya i ägarens ord och finns inte i `byggsten/hand`: kompromiss där båda rör sig, ett mått på mush och distinktion, och att smaken ska komma in som val och inte som meningar.

**Den starkaste invändningen mot min egen slutsats:** de dimensioner som bär mening går inte att mäta utan läsare. Repots lokala tak är talsegment (`essens.md:371-384`). Min diagnos visar att modellfria mått knappt känner igen typen (0,442 mot 0,388). Det som skiljer klipp i mening (mötet, friktion, var poängen bor) kommer ur en LLM:s läsning, och skillnaden mellan läsare är stor (Argon +0,25 mot Flash +0,09 på samma klipp, `essens.md:110-114`). Då flyttar problemet bara: koordinaterna blir lika opålitliga som läsningen ägaren säger är begränsad. Kompromissvektorn blir deterministisk över brusiga koordinater, och då är determinismen skenbar.

Det jag inte kan avfärda: **det enda kända sättet att röra sig mellan två bilder utan mush på pixelnivå är ett inlärt generativt latent rum**, och K7 förbjuder generativ AI i CM:s ändringsled (minnet `feedback-generativt-bara-for-1till1.md:8-12`). Utan det måste mush-fritt utförande komma ur verkliga klipp (att låna från grannar), ur manuset, eller ur en 3D-iscensättning som i dag fallerar (3.10). Pipen ägaren beskriver är alltså möjlig för koordinater och manus, men för video är den möjlig bara om rumsläsningen och kroppen fungerar, eller om generativ rendering tillåts efter ett nytt ägarbeslut. Det beslutet är ägarens.

---

## 6. Minsta bevis: tre första experiment

Alla tre: inga betalda eller generativa anrop. Panelinfrastrukturen i `motpart/runda-4/A-domare/panel/` (blinda id, kontrollpar, logg) kan återanvändas. Ägarens tid är cirka 10–15 minuter per experiment. Hypoteserna förregistreras före ägarens svar.

### E1. Trion: vilket rum ser ägaren?
- **Gör:** 40 trior ur en typ (`tilltal|till_kamera`, 379 klipp [D]), från konton ägaren inte sett (`overlamning-18nov-k1.md:79`). Fråga: "Vilken av B och C liknar A mest?" Inga ord om varför. Fem kontrolltrior där B är A omkodad. [A] Ägaren vill och kan svara på likhet utan att motivera; det är oprövat.
- **Jämför:** andelen trior där ägaren håller med (a) det modellfria mätrummet, (b) LLM-fingrarna, (c) temainbäddningen (`byggsten/hand/ut/tema.npz`).
- **Falsifiering:** om inget rum når 60 % på de riktiga trioerna, när kontrolltrioerna fälls, så fångar inget av repots rum det ägaren ser som "lika" och "olika". Då ska inga flyttar byggas på dem. Om det modellfria rummet ligger inom 5 procentenheter från LLM-fingrarna bär den modellfria vägen.
- **Kostnad:** cirka en halv dags arbete, 0 kr, 10 min av ägarens tid.

### E2. Kompromiss eller mush, på verkliga klipp
- **Gör:** sex par (A, B) av olika typ. För varje par tre kandidater, alla verkliga klipp ur banken: närmaste klipp till medelpunkten, närmaste klipp till den valda korsningen (`diagnos_modellfri.py`), och rutt.py:s hållpunkt. Lägg till ett slumpklipp av samma typ som kontroll. Ägaren ser A, B och kandidaten blint och svarar "Ser du både A och B i den?" (ja/delvis/nej) och "Gillar du den som innehåll?"
- **Förregistrerat:** den valda korsningen och rutten får fler "ja/delvis" än medelpunkten och kontrollen.
- **Falsifiering:** om medelpunkten får lika många eller fler, så motsvarar särprägel och stöd inte ägarens mush. Då är 4.3 fel.
- **Kostnad:** 0 kr. Skripten finns. 10 min av ägarens tid.

### E3. En ratt, deterministisk, mätt efteråt: "långsammare"
- **Gör:** fem tilltalsklipp. Operatorer i medielagret: förläng eller korta pauserna mellan talsegmenten (VAD-segmenten finns i `data/format/e30/`), och glesa ut eller tätna bildbytena. Tre mål: kvantil 25, 50 och 75 av typens `tal_per_s` och `takt`. Kör två gånger och jämför hashen. Mät igen efteråt. Mät "kvar" som D gör.
- **Ägaren:** ordnar tre versioner efter "lugnast" och svarar "samma klipp?" (ja/delvis/nej).
- **Falsifiering:** om ägarens ordning går emot den mätta i 2 av 5 klipp eller fler, så är måttet inte ratten. Om "samma klipp" blir nej vid kvantil 50, så skapar operatorn mush.
- **Kostnad:** 0 kr (ffmpeg, D:s kod). Ungefär en dags arbete.

### Vad i det byggda som bär, och vad som är sidospår för just den här frågan
**Bär:** `byggsten/hand` (fingrar, `rum.jsonl`, `rutt.py`, typer, `anpassa.py`, `tillstand.py`, Jev-ytan); `video/kalibrering` (BT, `nastaPar`, vertikalerna); de modellfria måtten i `data/format/e28`, `e30`, `e37` och `tempo`; formatkortens mall och platser; essensspårets fynd om två domar och två motorer; D-medielagrets deterministiska operatorer och felinjektion; panelen i `A-domare`.

**Sidospår för den här frågan** (inte nödvändigtvis i övrigt): `forvarld_karna/mening_motor.py` (attityd som ledförskjutning, föll); runda 2:s rumsmått i cm; G1–G7 som godkännande; Kimodo-kontrasten; arbetsbord v2 (stoppad). 3D-förvärlden behövs för riktningar som kräver ny iscensättning (lokal med samma kropp, personbyte i bild). Den är flaskhalsen där, men den är inte förutsättningen för att röra klipp längs dimensioner.

---

## 7. Svagheter i den här analysen

1. **En läsare.** Kopplingen mellan "etnicitet" och yta, och mellan "personlighet" och framförande, är min tolkning [T]. Ägaren kan mena något annat med liknelsen, till exempel bara att två saker kan likna varandra utan att bli lika.
2. **Diagnosen är ett mätrum, inte en dom.** Rangstandardiserade mått, euklidiskt avstånd, k = 15. Typen är en LLM-läsning. LLM-fingrarna och typen kommer ur samma modellfamilj, så deras försprång (0,517) kan vara delvis cirkulärt. Den valda korsningen är vald på stöd. Slumpfröet styr dragningen: en tidigare körning med andra dragningar gav samma bild (medelpunkten −33 % särprägel).
3. **Inte läst:** ägarens dialog 14 nov (`Desktop/dialog.txt`), Granola-transkripten, `../hagen-ui`, `forvarld_karna/` i detalj, `delegat/`. Beskedet om "ett klipp i mitten" har jag bara i assistentens återgivning (`README.md:249`).
4. **LAGE.md** är delvis fallen (`motpart/PROTOKOLL.md:28-33`). Jag har inte använt den som källa för något påstående om läget.
5. **Lovable-liknelsen** har jag översatt till standardvektor, publik och överstyrning. Ägaren kan mena att harnessen ska ha en egen smak som är bättre än CM:s, och inte bara standardval.
6. **Experimenten kräver ägarens tid,** och ägarens smak har varit stabil bara på 26 par. Trioval är oprövade med ägaren. Om han inte vill svara på "vilken liknar mest" faller E1.
7. **Manus som produkt.** Jag lutar mig på 2 nov (`inlarning.md:229-230`). Om ägaren nu vill ha förhandsvisningar som bär själva värdet blir 3D mer central än jag ger den.
