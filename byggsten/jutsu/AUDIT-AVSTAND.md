# Uppgift 1: avståndet mellan LeTrends förvärld och 3D Jutsu

14 nov 2026. Underlag: tre prov i Jutsu (`LOGG.md`, test 01–03), Higgsfields egen instruktion `/3d-jutsu` med fyra referenser, en läsning av vad editorn själv skrev in i scenen (`blockingStudio*`, `hf_id`), och vår kedja som den står i `scen/3d/PIPE.md`, `kontrakt/*.schema.json`, `forvarld/` och `delegat/kontext/vagen.md`.

**Ram:** vi binder oss inte till Higgsfield. Frågan är vad Jutsu är i förhållande till oss, och hur det hade sett ut om Jutsu var mallen för förvärlden: scenen som CM:s ändringar verkar på.

---

## 0. Slutsatsen först
1. **Jutsu är en scen, inte en förvärld.** Det är en hostad, versionerad Blender med ett tunt lager för kamera och shots ovanpå, plus generativa slutsteg (bild och video). Allt vi kallar förvärld finns inte där: läsning ur video, mening, liggare, frihetsgrader, typad regi, mätning mot originalet och kroppar som anpassar sig.
2. **Vår kedja passar ovanpå som den är.** Rum, kamera med klipp, tidslinje, kroppar och mening gick in på under två minuter i Jutsu (test 03). Det visar att Jutsu kan vara scenlagret, och att vi förblir allt ovanför det.
3. **Det som blockerar Jutsu som mall är dataflödet in**, inte begreppen. Egna modeller, riggar och kroppar kan inte importeras via MCP, och all data passerar agentens utdata. Det andra hindret är att editorn skriver om scenen (kamera, shots) när en människa öppnar den.
4. **Det vi kan lära av dem är tre saker:** revision med optimistisk låsning, deras grindar för scenbygge (form, proportion, djup, kontakt, kamerablick), och deras kameraspråk (bana, waypoints, siktmål, inramning). Det sista är ett färdigt ordförråd för CM:s kameraändringar, som vi saknar.

---

## 1. Lagren sida vid sida

### 1.1 Jutsu, uppifrån och ned
| lager | vad | belägg |
|---|---|---|
| Agent | I webbgränssnittet: deras agent "Supercomputer" med valbar språkmodell (Auto gratis). Via MCP: vi själva. | Bloggen, MCP-instruktionen |
| Scenpass | Agentens arbetsanteckning: avsikt, hierarki, föremål, bild, ljus, rörelse, godkännande. Sparas **inte** i scenen. | `/3d-jutsu/references/scene-building` |
| Grindar | Form, proportion, djup, kontakt, kamerablick och detalj, i den ordningen. En grind som faller stoppar putsen. | samma |
| Blocking Studio | Kamera som bana: `Path_<kam>` (centripetal kurva, spänning, easing, inramning "medium", fart), `Aim_<kam>` (siktmål), `Focus_<kam>` (skärpa), `WP_n` (waypoints). Tidslinje: `blockingStudioTimeline` = `{version, duration, shots:[{cameraId, start, end}]}` i sekunder. | Läst ur vår scen, revision 3–6 |
| Identitet | `hf_id` på varje objekt (266 av 266). Kameran identifieras i shots med sitt `hf_id`. | samma |
| Scen | Blender 5.2 headless, bpy, metrisk, z uppåt (editorn och glTF: y uppåt). | test 01 |
| Versioner | `revision` (sparad version) och `sceneSequence` (scenens läge). Varje ändring anger båda, och en inaktuell ändring avvisas med `REVISION_CONFLICT`. | test 03 |
| Resurser | Katalog med 994 GLB (inredning, skyltar, fordon, **inga människor**). 678 animationer (Meshys bibliotek) för riggade figurer ur `generate_3d` (bild till 3D, kostar). | test 01 |
| Rendering | CPU med 2 kärnor, ingen GPU. EEVEE cirka 19 s per ruta (640×360), Workbench cirka 0,2 s per ruta (288×512). Högst 300 s per operation, en operation i taget per projekt. | test 01–03 |
| Generativt slutsteg | `generate_angles` (Seedream: ny bild ur en render), `generate_video` (Seedance 2.5 med renderingen som startbild, 4–30 s). Genjutsu `hf_mult_motion_control` (rörelseöverföring) via `generate_video`. Kostar credits. | MCP-instruktionen |
| Ut | `.blend` och `.glb` automatiskt per revision, och upp till 8 bilder eller filmer per operation. | test 01 |

### 1.2 Vår kedja, uppifrån och ned
| lager | vad | var |
|---|---|---|
| CM:s mening | Fri text: "hoppa över när hon skopar", "flytta det till en foodtruck" | `vagen.md` |
| Jev | Väljer en laglig ändring ur liggarens yta, eller `ingen_passar`, på under en sekund. Typad modell, majoritet av tre under 0,5. | `PIPE.md` (0031–0032) |
| Långsam väg | En stark modell med liggaren svarar med regi eller ett skälat nej (4–9 s). | `forvarld/liggare/langsam_vag.py` |
| Liggare | Entiteter med affordanser, starttillstånd i predikat, händelser med roller, förvillkor och effekt, förlopp, mening (poäng, bär, tillfälligt, ramar), frihetsgrader (domän, nivå, spridning, regi-mall). STRIPS-kontroll. | `kontrakt/liggare.schema.json`, `liggare_kontroll.py` |
| Regi | 28 typade operationer: `ta_bort_handling`, `tempo_handling`, `upprepa_handling`, `satt_frihetsgrad`, `byt_prop`, `flytta_prop`, `byt_miljo`, `casta`, `renderkamera`, `trimma_scen`, `duplicera_scen` med flera. Ramar: bevara beats, tillåt omtiming. | `kontrakt/regi.schema.json` |
| Källa | `semantik` (scener, beats, repliker, personer, props, rum, platser, händelser, scengrupper, handling, relevans, liggare) och `matning` (koordinater, kameror, personer med rörelse per ruta, rum, masker, kvalitet, platser, scenbygge). | `kontrakt/kalla.schema.json` |
| Deklaration | Rummet före läsning: platser, möbler med intervall, kameror per tagning med höjd och status (`agare`, `last`, `antagen`, `sedd`), berättat mot avslöjat rum. Skrivs av Gemini-konsensus och fokusfrågor, och ägaren godkänner. | `ingest/scenbrief.py`, `rum_video.py`, `rum_konsensus.py` |
| Ingest | YOLO, COLMAP, SAM 3D Body, MHR (127 leder), MoGe, segmentering, kameragrupper, boxpassning, möbel- och föremålslyft, skymning, föremål i hand. | `ingest/`, `kontrakt/` |
| Generativt, bara 1:1 | Dreamina, Wan och Luma återskapar originalet vid ingest, så att dolda kroppsdelar och ren bakgrund kan läsas. Aldrig alternativ. | `gennedbrytning/`, minnet "Generativt bara för 1:1" |
| Kropp i ändringar | En rörelsemodell (MaskedMimic nu, Kimodo eller annan senare) tar mål ur liggaren och ger hel kropp. Rörelsebank v0. | `forvarld/kropp/` |
| Kompilator | Källa + regi → plan. Plan → Blender (`mhr_rig.py`). | `kontrakt/kompilera.py` |
| Mätning | Bildtrohet i renderkameran, skymning, vakt, kvalitetsrapport. | `kontrakt/trohet.py`, `skymning.py` |

---

## 2. Avståndet, begrepp för begrepp

Skala: **0** = finns hos Jutsu i samma form. **1** = finns, men i annan form (en adapter räcker). **2** = finns delvis, och vi måste bygga till. **3** = finns inte, och Jutsu kan bara bära vår data.

| # | vårt begrepp | vårt format | i Jutsu | avstånd | vad som krävs |
|---|---|---|---|---|---|
| 1 | Klippet och tidsbasen | `tidsbas` (fps som bråk, rutor, halvöppna intervall) | scenens fps och rutintervall; shots i **sekunder** | 1 | Räkna om rutor till sekunder. Notan: 383 / 30 = 12,77 s mot editorns 12,73, alltså en ruta fel i deras längd. Behåll rutor som sanning. |
| 2 | Tagningar och scener | `semantik.scener` med `ut`, personer, kamera, plats | `blockingStudioTimeline.shots` med `cameraId`, start och slut | 1 | En shot per tagning och en kamera per shot. Vi skrev en kamera med klipp, och editorn gjorde det till **ett** shot. Skriv 7 kameror och 7 shots själva. Oprövat om editorn då behåller dem. |
| 3 | Kamera per ruta | `renderkamera.nycklar` (matris, lins, sensor) | kameraobjekt med nycklar, som editorn bakade till 384; bana, siktmål, fokus och waypoints som eget lager | 1 | Fungerar redan. Banan är avstängd (`enabled: False`) när nycklar finns. CM:s kameraändringar kan uttryckas i deras ord: waypoint, siktmål, inramning, easing. |
| 4 | Bildformat | 576×1024, sensor 36 mm horisontellt | `blockingStudioAspect = 0.5625` på kameran | 0 | Det läste editorn själv. |
| 5 | Rummet | deklaration: platser, möbler med intervall, status per tal, berättat och avslöjat rum | bara geometri; meningen i namn och agentens huvud | 3 | Rummen per tagning finns inte. Vi måste bära `galler_tagningar` som synlighet eller som egna kollektioner per rum. Det är samma brist som orsakade blocken (BUGG-BLOCK.md). Status och intervall per tal måste ligga som egenskaper. |
| 6 | Möbler | mallådor (`lada`), massiva eller på ben, lyfta ur bildrutor | katalog-GLB (994), procedurellt via bpy | 1 | Lådor går (test 02–03). Riktiga möbler ur katalogen ger form, men måtten måste passas mot våra. Katalogen är generisk ("Club Bar Counter"), inte vår lokal. |
| 7 | Föremål som bär meningen | props, `handforemal` (Child Of mot handleden), `:pa:`-föremål på möbler | parenting och constraints i bpy | 1 | Samma mekanism (Child Of) finns. Notans föremål (burk, mugg, burgare) är inte byggda i vår plan heller. |
| 8 | Personer | roll, färg, ankare (`stol_A`, `staplats_C`), synlighet per tagning | **inga människor** i katalogen; `generate_3d` med riggning kostar, och resultatet kan inte importeras i scenen | 3 | Bara egna dockor byggda med kod (test 03: 18 leder, cylindrar). För riktiga kroppar krävs import av egen rigg, vilket inte är möjligt via MCP. |
| 9 | Kroppens rörelse | MHR 127 leder per ruta (cm + kvaternion), kamerarelativt, roten rättad, stöd och IK | inget; färdiga klipp ur ett bibliotek | 3 | Vi skickade 18 leder i 10 fps som positioner (36 KB för 7 tagningar). Hela MHR blir cirka 1 MB per klipp och går inte genom agentens utdata. Kräver filimport. |
| 10 | Kropp i ändringar | rörelsemodell med mål per tid ur liggaren | inget målstyrt; Genjutsu-rörelseöverföring är generativ video | 3 | Rörelsemodellen ligger hos oss (Modal). Jutsu tar emot resultatet som nycklar. Deras generativa rörelseöverföring strider mot "generativt bara 1:1". |
| 11 | Mening: handling och relevans | `semantik.handling` (segment, ordförråd), `relevans` (bär, sätter, stryks) | inget | 3 | Ligger som scenegenskaper i JSON (`hagen_*`). Editorn bevarade dem i revision 3–7. |
| 12 | Liggaren | entiteter, predikat, händelser, frihetsgrader, regi-mallar | inget | 3 | Liggaren stannar hos oss. I scenen bör varje entitet få en referens: `hagen_entitet` på objektet, så att regin kan peka på objekt. |
| 13 | Jev och regi | typad yta, 28 operationer, `ingen_passar` | fri bpy-kod skriven av en LLM; inga typade operationer | 3 | Detta är vår kärna. I en Jutsu-mall blir varje regi en liten bpy-patch som vår kompilator skriver, en revision per ändring. |
| 14 | Kompilatorn | källa + regi → plan → Blender | ingen; scenen ändras direkt | 2 | Två vägar: (a) kompilera som i dag och skriv om hela scenen, cirka 10–20 s, eller (b) kompilera till en patch mot förra revisionen, cirka 2 s plus förhandsbild. (b) kräver att kompilatorn kan uttrycka skillnader. |
| 15 | Versioner och ångra | regi per kund, `kalla.revision`, ingen scenhistorik | `revision` + `sceneSequence`, `.blend`/`.glb` per revision, optimistisk låsning | **Jutsu bättre** | Värt att ta efter: en revision per regi ger historik och ångra utan extra arbete. |
| 16 | Mätning mot originalet | trohet i renderkameran, skymning, vakt | ingen; deras motsvarighet är att agenten tittar på en render | 3 | Vår mätning körs lokalt mot planen. I Jutsu kan den köras som en query som renderar och publicerar bilder, men jämförelsen med originalet sker hos oss. |
| 17 | Ingest ur video | hela kedjan | ingen; närmast är "ny vinkel ur en bild" | 3 | Se avsnitt 4. |
| 18 | Status och proveniens | `agare`, `last`, `antagen`, `sedd`, `kalla`, `metod`, `osakerhet_m` | "observerat mot antaget" bara i agentens anteckningar | 2 | Samma filosofi, men inget format. Bär som egenskaper per objekt. |
| 19 | Rendering, förhandsbild | Blender lokalt, Workbench 576×1024 | Workbench cirka 0,2 s per ruta i halv upplösning på CPU | 1 | Duger för animatik. Slutlig bild (stilisering sist) kräver annat. |
| 20 | Rendering, slutlig look | stilisering sist (PS2 som slutval), inte bestämt | Seedream och Seedance ur render, generativt | 2 | Generativ slutlook ur en kontrollerad scen är en möjlig väg, men den bryter mot "generativt bara 1:1" om den används för CM:s ändringar. Det beslutet är ditt. |
| 21 | Fart | Jev under 1 s, ändring blixtsnabb | ändring cirka 2 s plus förhandsbild, köad per projekt, 300 s tak | 1 | Inom målet "någon sekund" för en geometriändring. En kroppsändring kräver vår rörelsemodell först. |
| 22 | Kostnad | Modal per jobb, Gateway per anrop | scenarbete 0 credits; generativt kostar | **Jutsu bättre** | Gratis scenlager. |
| 23 | Licens | MaskedMimic är forskning; Kimodo är kommersiell | oklart vad som gäller för scenfiler och katalog i kundleverans | ? | Måste läsas innan något levereras till kund. |
| 24 | Datatransport | lokala filer, npz, json | in: bara kod (256 KiB) och katalog-id; ut: signerade nedladdningslänkar | 3 | Den största skillnaden. Se avsnitt 6. |

---

## 3. Datatyperna: hur vår källa skulle ligga i en Jutsu-scen

Vad test 03 visade fungerar, och vad som bör läggas till.

| vår typ | i scenen (beprövat) | bör bli |
|---|---|---|
| `tidsbas` | `scene.render.fps`, `frame_start/end` | + `scene["hagen_tidsbas"]` med bråk-fps och regeln om halvöppna intervall |
| `scener[]` | markörer `s1 A` … och `scene["hagen_scener"]` (JSON-sträng) | en kamera per scen och `blockingStudioTimeline.shots` i sekunder; markörerna kvar |
| `repliker[]` | markörer `r1 A: …` (kapade vid 63 tecken) och `scene["hagen_repliker"]` | + text som Blender-textobjekt för undertext om det behövs i bild |
| `personer[]` | kollektion `RIG_<id>_<niva>` med `person`, `roll`, `niva` | + `hagen_entitet` som pekar in i liggaren; en armatur i stället för tomma objekt |
| rörelse per ruta | tomma objekt med positionsnycklar, cylindrar med Copy Location och Stretch To | en armatur (SMPL- eller MHR-skelett) med rotationsnycklar; kräver filimport |
| möbler och lådor | mesh per låda, `deklaration_id`, `synlig_ut`, synlighetsnycklar | + `hagen_rum` (berättat eller avslöjat) och `hagen_status`; en kollektion per rum |
| kamera | `CAM_main` med nycklar per ruta, lins | en kamera per tagning; deras bana och waypoint för CM:s kameraändringar |
| liggare och frihetsgrader | (inte införda) | `scene["hagen_liggare_ref"]` med sökväg och sha; frihetsgraderna stannar utanför scenen |
| regi | (inte införd) | en revision per regi, och `scene["hagen_regi_logg"]` med regi-id per revision |
| kvalitet | (inte införd) | resultat från mätningen som egenskap per revision |

Regler som provet gav:
- **JSON-strängar som egenskaper överlever editorn.** Revision 3–7 rörde dem inte.
- **Editorn lägger till sina egna nycklar** (`hf_id`, `blockingStudio*`) och skriver om kameran. Vårt lager måste därför tåla att Jutsu-lagret ändras, och inte tvärtom.
- **Namnrymd:** allt vårt bör ha prefixet `hagen_` och en schemaversion, så att en läsare kan skilja det från deras lager.
- **Koordinater:** Blender har z uppåt och är det vi skriver i. Deras `blockingStudioPathAnchor` ligger i editorns y-uppåt-rum (origin `[-0.245, 1.2, -1.401]` = Blenders `(x, z, -y)`). En adapter som läser deras bana måste vända axlarna.

---

## 4. Hur vi hittar och planerar scener, mot hur de gör det

| steg | vi | Jutsu (`location-new-angles`, `scene-building`) | avstånd |
|---|---|---|---|
| Underlag | hela videon, alla tagningar | **en** stillbild per plats | stort: deras flöde vet inget om tagningar, personer eller tid |
| Vem tolkar | Gemini fem gånger, konsensus, fokusfrågor, härledning ur mätningar; ägaren godkänner | agenten en gång; frågar användaren om dolda ytor | vår väg är mer robust: deras agent får inte konsensus |
| Observerat mot antaget | `status` per tal: `agare`, `last`, `antagen`, `sedd`, med intervall | "record observed … separately from inferred" i agentens anteckningar | samma filosofi, men vi har ett format och de har inte det |
| Kameran | COLMAP, metrisk skala, kameragrupper, fokal per klipp, renderkamera ur kroppen | kalibrera källkameran mot bilden för hand i bpy och jämför sedan bild mot render | vi mäter, de passar in för ögat |
| Plan ovanifrån | ingen som standard (deklarationen är text och tal) | obligatorisk topplan med kameror, strålar och observerade och antagna ytor | **de är bättre**: en topplan per klipp vore ett billigt granskningsverktyg för deklarationen |
| Grindar | trohet, skymning och vakt efter bygget | form, proportion, djup, kontakt och kamerablick före putsen; en grind som faller stoppar | deras ordning är bra; vår mätning är skarpare |
| Dolda ytor | generativ 1:1-återskapning vid ingest | fråga användaren, märk som antaget; "include a neutral inferred ceiling" | lika i andan |
| Nya vinklar | inte vårt mål i dag | huvudsyftet: bakvinkel och sidvinkel, sedan Seedream för utseendet | olika mål |
| Rum per tagning | berättat och avslöjat rum (notan) | "never move objects independently per shot to rescue a composition" | **här krockar vi**: en avslöjning kräver just att rummet skiljer sig per tagning. Deras regel förbjuder det. Vi behöver rum som lager med giltighet per tagning. |

Slutsats: deras planering är ett bra mönster för **en** bild av **ett** rum och kan tas som granskningssteg (topplan och grindar). För video, flera tagningar, personer och avslöjningar är vår väg den enda av de två.

---

## 5. Animationsanalysen: våra val mot vad Jutsu erbjuder

| fråga | vårt val | Jutsu | konsekvens om Jutsu var mallen |
|---|---|---|---|
| Läsa kroppen | SAM 3D Body → MHR, 127 leder, kamerarelativt, roten rättad i metrisk värld | ingen läsning | analysen stannar hos oss; Jutsu får bara resultatet |
| Dolda delar | generativ 1:1 (Dreamina) så att hela kroppen kan läsas, en generering per tagning | ingen | oförändrat |
| Stöd och kontakt | säte och fot som ankare, `begransa`, kontakt-IK, skymning | constraints i bpy | kan uttryckas i bpy, men logiken är vår |
| Rörelsebank | v0 med 23 poster, liggarens händelser som etiketter | 678 Meshy-klipp med namn som "Talk_with_Left_Hand_Raised" | deras bibliotek är generiska rörelser utan koppling till vår mening. Möjligen användbart som extra träningsdata eller stil, men licensen är oläst. |
| Ändra kroppen | rörelsemodell (MaskedMimic, Kimodo) med mål ur liggaren | inget målstyrt; Genjutsu-rörelseöverföring är generativ video | modellen körs hos oss, och resultatet går in som nycklar |
| Kroppsformat i scenen | MHR-rigg i `mhr_rig.py` med Child Of för föremål | ingen människorigg; egen rigg kan inte importeras via MCP | det största hindret: utan import blir det dockor av leder (test 03) |
| Upplösning i tid | varje ruta (30 fps) | valfri | 10 fps räckte för en animatik. Ändringar som rör händer kräver 30 fps. |

---

## 6. Det verkliga hindret: data in

- **Via MCP** kan bara kod (högst 256 KiB) och katalog-id komma in. All data i koden passerar agentens utdata. 36 KB rörelse gick (op2), men en hel MHR-sekvens (cirka 1 MB per klipp) går inte rimligt.
- **Via webbgränssnittet** kan GLB med animation importeras enligt bloggen. **Oprövat:**
  - om en sådan import syns och kan ändras via MCP efteråt
  - om den behåller våra egenskaper
  - om en armatur överlever
- **Inget nätverk** finns i deras Blender, och ingen sökväg till våra filer.

Om Jutsu ska vara mallen krävs en väg för filer. Antingen importerar ägaren en GLB per klipp i webbgränssnittet (manuellt, en gång per klipp), eller så öppnar Higgsfield en filimport i MCP. Utan det blir Jutsu en förhandsscen för rum, kamera och dockor, inte för riktiga kroppar.

---

## 7. Om Jutsu var mallen för förvärlden: hur det hade sett ut

```
video ──(vår ingest)──► källa + deklaration + liggare          [hos oss]
                               │
                               ▼
                   adapter: källa → Jutsu-scen                 [byggsten/jutsu]
          ENV/PRP per rum (kollektion per berättat/avslöjat rum)
          en kamera och ett shot per tagning
          RIG per person (armatur, kräver filimport)
          hagen_* på scen och objekt (mening, status, entitets-id)
                               │  revision 1
                               ▼
CM-mening ──► Jev (liggarens yta) ──► regi ──► kompilator ──► bpy-patch
                                                               │  revision n+1 (cirka 2 s)
                                                               ▼
                                         Workbench-förhandsbild (cirka 0,2 s per ruta)
                                                               │
                                         [mätning mot originalet hos oss]
                                                               │
                                   valfritt: slutlook (lokal render, eller generativt om du tillåter det)
```

Det som ändras hos oss:
1. **Kompilatorn skriver patchar**, inte hela scener. En regi blir en revision.
2. **Rummen får giltighet per tagning** i formatet (samma rättning som blocken kräver).
3. **Kameraspråket** för CM ("närmare", "från andra sidan", "följ henne") översätts till deras bana: waypoints, siktmål och inramning. Det blir regi-operationer på `renderkamera`.
4. **Läsaren av deras lager:** adaptern måste läsa scenen före varje patch, eftersom editorn kan ha ändrat den (`REVISION_CONFLICT`).

Det som inte ändras: ingest, deklaration, liggare, Jev, rörelsemodell, mätning och grundregeln.

---

## 8. Sammanfattning av avståndet, efter tyngd
**Blockerar (3):**
- egen kropp och rigg in
- människor
- rörelsedata i full upplösning
- ingest ur video
- mening, liggare och regi (finns inte hos dem, men kan ligga ovanpå som egenskaper)
- mätning mot originalet

**Kräver byggande (2):**
- rum per tagning
- kompilator som skriver patchar
- status och proveniens som egenskaper
- slutlook

**Adapter räcker (1):**
- tidsbas i sekunder
- shots per tagning
- kamera
- möbler
- föremål i hand
- förhandsbild
- fart

**Jutsu bättre:**
- versioner med låsning
- gratis scenlager
- topplan och grindar som granskning
- kameraspråk

## 9. Öppna prov, i ordning efter vad de avgör
1. **Import via webbgränssnittet:** ägaren importerar en GLB med armatur och animation. Sedan ska MCP läsa den och ändra den. Det avgör avsnitt 6.
2. **Sju shots:** skriv 7 kameror och `blockingStudioTimeline` med 7 shots. Behåller editorn det när scenen öppnas?
3. **Regi som patch:** "flytta B till bord_2" (motsvarar S7), en revision. Mät tiden från regi till förhandsbild.
4. **Deras agent på vår scen:** ge Supercomputer (Auto, gratis) samma mening i webbgränssnittet. Ser den våra `hagen_*`-egenskaper, och använder den dem?
5. **Licens:** villkor för scenfiler, katalog och Meshy-animationer i kundleverans.
