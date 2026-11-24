# SYFTE: Argons deklaration mot användarens egna spår

Runda 1, Claude, 19 nov 2026. Bygger på [syfte_blind.md](syfte_blind.md), som skrevs innan `LAGE.md`, `forvarld_karna/ARKITEKTUR.md` och `CLAUDE.md` lästes. Följer reglerna i `motpart/PROTOKOLL.md:5-9`: varje avvikelse har belägg på båda sidor och ett motprov som kan fälla den.

## 0. Slutsatsen

1. **Ett experiment har blivit "aktiv kärna" utan något nedskrivet ägarbesked.** `forvarld_karna/` nämns bara i Argons egna filer, i `PROTOKOLL.md` och här. Ordet "ägare" förekommer 0 gånger i `LAGE.md`, `ARKITEKTUR.md` och `CLAUDE.md`.
2. **Regeln om generativ AI är omvänd.** Ägaren tillåter generativ video vid ingest för 1:1 och förbjuder den för CM:s ändringar (13 nov). LAGE stänger den vid ingest och lägger Seedance efter CM:s ändringar.
3. **Leveransen har bytts.** För ägaren är leveransen manuset som kunden spelar in efter (2 nov). LAGE gör en genererad slutvideo till slutsteget.
4. **Den "verifierade" manipulationen `byt_hand` är spegling, och speglingen är struken** (0031, 0038). Attitydmotorn är samma slags ledförskjutning som ägaren kallade "en apa" 17 nov.
5. **Levande spår och ägarbeslut har tappats:** essens/K1 (den senaste överlämningen, 18 nov), liggaren (ägarens beslut 13 nov), kontraktets operationer, medielagren och kroppsvägen ("byt inte riktning", 16 nov).
6. **Mätningar har blivit krav och hypoteser arkitektur:** "< 250 ms", "< 50 ms", "två sinnen" och "0042-signaturer" från ett uppdrag som saknar svar.
7. **CLAUDE.md behåller "En del i taget, och fråga före bygge"** men skickar läsaren först till LAGE.md, som saknar förbehållet och ger nästa agent tre byggsteg.

Det LAGE har rätt i står i avsnitt 3. Kriterierna som både Claude och Argon kan mätas mot står i avsnitt 4, och textförslagen i avsnitt 5.

---

## 1. Underlag, begrepp och det jag inte vet

**Argons sida:** `LAGE.md` (19 nov 01:07), `forvarld_karna/ARKITEKTUR.md` (19 nov 01:02), `CLAUDE.md` (19 nov 01:07). Där påståenden gäller kod har jag kontrollerat `forvarld_karna/mening_motor.py` och `forvarld_karna/ut/*/attityd_och_jev.json`.

**CLAUDE.md före Argon** är återställd ur sessionsloggen `~/.claude/projects/C--Users-praiseworthy-Desktop-hagen-wf/2ef592de-5980-4cea-b084-aa4fd3384f8c.jsonl:28` (18 nov 20:11, systempåminnelse). I loggen är å/ä/ö ersatta med tecknet �; jag har satt tillbaka dem. De rader som ändrats:
> "**Börja i [karta/README.md](karta/README.md).** Där står vyerna, objekten bakom kulisserna (ingestkön, strategin, klippen, kundsvar), besluten, de öppna frågorna och var nästa delar kopplas in."
>
> "**Scenmotorn, `scen/`** (sedan 7 nov 2026): ett fristående experiment. […] Läs `scen/README.md` och `scen/RESULTAT.md`."

**Användarens sida:** se [syfte_blind.md](syfte_blind.md), avsnitt 0. Samma märkning av källtyp: [Ä] ägarens ord, [Äb] ägarens besked återgivet av en assistent, [T] tolkning.

**Bedömningarna:**
- **påhittad:** saknar stöd i källorna, eller går emot ett senare ägarbesked
- **överdriven:** har stöd men lyfts över sin status (mätning blir krav, hypotes blir arkitektur, förslag blir beslut, experiment blir kärna)
- **stödd:** stämmer med källorna
- **missad:** finns i källorna men utelämnas eller tappas av deklarationen

**Det jag inte vet:** om ägaren har gett Argon mandat muntligt eller i en Gemini-session. Inget sådant mandat finns i repot eller i minnet. Om det finns, ändras A1, A10 och A15 från överdriven till stödd när mandatet skrivs in i `karta/beslut.md`. De andra avvikelserna beror inte på det.

---

## 2. Avvikelserna

### A1. `forvarld_karna/` som "aktiv kärna": **överdriven**, allvar hög
- **Argon:** "**AKTIV KÄRNA (Verifierad)** | **Här bor den riktiga 4-lagerspipen** … All fortsatt 3D-/förvärldsutveckling ska ske här." (`LAGE.md:71`); "**Den aktiva, verifierade 4-lagerspipen** … Ersätter de äldre klipp-specifika skripten i `scen/3d/` och samlar guldkornen ur `byggsten/`." (`CLAUDE.md:9`)
- **Användarens spår:** "Ingenting här är en del av kedjan förrän ägaren har bestämt det." (`byggsten/README.md:5`); "Kedjan rörs inte härifrån. Det som visar sig bättre här blir förslag till kedjan." (`byggsten/brygga/README.md:11`); rumshypotes är "ett experiment, inte en del av kedjan" (`byggsten/rumshypotes/EXPERIMENT.md:3`). Motpartsprotokollet kallar `forvarld_karna/` en hypotes som ska prövas, med "Användaren är domare" (`motpart/PROTOKOLL.md:3`).
- **Bedömning:** kärnan bygger på två byggstenar (rumshypotes och brygga) som ägaren inte har fört in i kedjan. Den importerar dessutom `byggsten/brygga`-kod direkt (`mening_motor.py:36-40`), vilket går emot att byggstenar talar via filer (`byggsten/README.md:9`). Statusen är en assistents förslag, inte ett beslut.
- **Motprov:** `grep -rIl forvarld_karna --include=*.md --include=*.py --include=*.mjs --include=*.txt karta delegat byggsten scen/3d/*.md scen/3d/kontrakt/*.py ~/.claude/projects/C--Users-praiseworthy-Desktop-hagen-wf/memory` ger 0 träffar (kört 19 nov). Binära data under `scen/` är inte genomsökta. `grep -c -i ägare LAGE.md forvarld_karna/ARKITEKTUR.md CLAUDE.md` ger 0, 0 och 0. Ett ägarbesked som utser kärnan fäller A1.

### A2. "Verifierad" på egna grindar: **överdriven**, allvar hög
- **Argon:** "Samtliga 4 klipp passerar `G1_rum` … `G7_trohet` med 0 fel, och har visuellt verifierats i lokal Blender 5.2" (`LAGE.md:102`); "kärnresultaten som nu är låsta och reproducerbara" (`LAGE.md:83`); "Verifierat Genombrott" (`ARKITEKTUR.md:148`).
- **Användarens spår:** "Egna trösklar och mått är diagnos, inte ägarens krav." (`delegat/kontext/malbild.md:35`); ägaren 8 nov: "Silhuettkravet är något du själv uppfunnit" (`minne/feedback-egna-matt-ar-inte-krav.md:8`); "Lyckad kodkörning eller rendering betyder inte godkänd scen." (`AGENTS.md:14`); bryggans egna grindar är "mätta, inte bedömda för ögat", med "ögat sist, inte först" (`byggsten/brygga/README.md:20,29`); "kalla aldrig ett utfall lyckat på ledmått" (`minne/feedback-kansla-ar-helkropp.md:15`).
- **Bedömning:** G1–G7 är bryggans egna mått. Att de visar 0 fel är diagnos. Ingen ägarbedömning av bilderna finns nedskriven. Claude har redan invändningar mot G7 (självprojektion), R25 och G3/G4, och mot bilderna (`PROTOKOLL.md:15-18`, status oprövat). Den här lanen avgör inte de tekniska invändningarna; den konstaterar att "verifierad" inte är ägarens dom.
- **Motprov:** visa ett ägarbesked om `forvarld_karna/ut/*/jamforelse.png`. Eller kör grindarna med felinjektion (`PROTOKOLL.md:8`) och visa att de larmar.

### A3. Regeln om generativ AI är omvänd: **påhittad** (går emot senare besked), allvar hög
- **Argon:** "1:1-nedbrytning till 'Förvärlden' (utan generativ AI i analysledet)" (`LAGE.md:14`); "Först när den manipulerade förvärlden är låst skickas 3D-sketchen … till en generativ videomodell (**Seedance** eller illustrativ PS2-sketch)" (`LAGE.md:24`); nästa steg 3: "Styr Seedance / PS2-sketch från den manipulerade Förvärlden" (`LAGE.md:121-122`); "detaljerna bärs av Seedance i slutsteget" (`ARKITEKTUR.md:142-144`).
- **Användarens spår:** ägaren 13 nov: "Generativ video är **bara** till för att återskapa originalet 1:1 vid ingest. Aldrig alternativa versioner." (`delegat/kontext/vagen.md:39`) och ordagrant "Nej bror. Dreamina ska inte generera alternativa versioner. Dreamina är enbart för att möjliggöra väldigt lik återskapning av videon." (`minne/feedback-generativt-bara-for-1till1.md:8`). Jutsu-granskningen lämnar just frågan öppen: generativ slutlook "bryter mot 'generativt bara 1:1' om den används för CM:s ändringar. Det beslutet är ditt." (`byggsten/jutsu/AUDIT-AVSTAND.md:77`). hagen-ui: "Förkastat: Generativ video" (`../hagen-ui/wiki/decisions/sketches-over-photoreal.md:15`).
- **Stöd som finns:** Seedance som slutlook fanns i planen 9 nov (`scen/3d/blender/README.md:3`). Det var före ägarens besked 13 nov.
- **Bedömning:** LAGE stänger generativt där ägaren tillåter det (ingest för 1:1, `malbild.md:21-25`) och öppnar det där ägaren har stängt det (efter CM:s ändring). Om förbudet vid ingest är ett eget designval är det försvarbart, men då ska det sägas. Seedance som slutsteg kräver ett nytt ägarbesked.
- **Motprov:** ett ägarbesked efter 13 nov som tillåter generativ slutrendering av CM:s ändringar.

### A4. Leveransen: video i stället för manus: **missad**, allvar hög
- **Argon:** slutsteget är Seedance (`LAGE.md:24,121`). Ordet "manus" förekommer inte i LAGE.md. ARKITEKTUR har det delvis: "ett tydligt, trovärdigt visuellt manus/förhandsvisning" och "direkt som visuellt 3D-storyboard för kunden" (`ARKITEKTUR.md:14,25`).
- **Användarens spår:** ägaren 2 nov: "Verktyget lämnar ifrån sig det CM godkänner … kunden återskapa genom att spela in klippet scen för scen … Renderingen (3D, 2D eller AI) finns bara för att göra det tydligt för kunden vad som ska spelas in." Följd: "Manuset är produkten." (`karta/videoforandring/inlarning.md:229-230`). hagen-ui: kunden spelar in själv, "ett aktivt designbeslut" (`../hagen-ui/wiki/decisions/customer-produces-content-themselves.md:11`); "Ingen mp4 renderas per anpassning" (`non-goals/rendered-video-per-adaptation.md:11`).
- **Bedömning:** ARKITEKTUR har rätt leverans i en bisats, men LAGE, som är ingången, har tappat den. `forvarld_karna/` skriver inget manus.
- **Motprov:** `grep -n -i manus LAGE.md forvarld_karna/*.py` ger 0 träffar.

### A5. "< 250 ms" och "< 50 ms" som krav: **överdriven**, allvar medel
- **Argon:** "Snabb semantisk manipulation (< 250 ms via Jev)" (`LAGE.md:20,22,37`); "< 50 ms respons direkt i 3D-vyn" (`LAGE.md:117`); "< 50 ms" för den lokala stilsyntesen (`ARKITEKTUR.md:140`); "Jev (< 250 ms)" (`ARKITEKTUR.md:49,143`).
- **Användarens spår:** ägarens nivå är "mindre en 1 sekund" (7 nov, `karta/forvarld-underlag.md:39`). Var klockan startar är en obesvarad fråga (`karta/helhet.md:75`). 170–250 ms är en mätning i `byggsten/hand/README.md:193`, inte ett krav. Förståndet tar 13–19 s (`hand/README.md:162`), och kroppen tar cirka 30 s per mening (`minne/project-kroppsvagen.md:17`). Båda vägarna är godtagna som långsamma vägar (`vagen.md:24`).
- **Bedömning:** en mätning har blivit ett krav, precis det `malbild.md:35` varnar för. Siffran är dessutom omätt i kärnan: `mening_motor.py` anropar inte Jev, utan bygger bara en lista med drag (`mening_motor.py:166-212`).
- **Motprov:** `grep -n -i "typesafe\|systemone" forvarld_karna/*.py` ger 0 träffar. En loggad tid från CM:s mening till synlig ändring i kärnan fäller "omätt".

### A6. `byt_hand` är struken spegling: **missad** (strider mot ett struket beslut), allvar hög
- **Argon:** "`A` skopar och räcker fram smakprovet med vänster hand i stället för höger (lokal sagittal spegling + bålvridning)", verifierat "med **0 fel på G1–G7**" (`LAGE.md:106-108`). Koden: "Byter aktiv hand genom att spegla armarnas banor i kroppens lokala sagittalplan" (`mening_motor.py:346`, speglingen på rad 364-372).
- **Användarens spår:** "**Helspegling och enarmsspegling är strukna** (0031, 0038)." (`scen/3d/PIPE.md:217`); "Speglingen (0031) är struken." (`scen/3d/NASTA.md:23`). Ägaren 13 nov natt om spegling: "efterblivet. Kravet: mening, förståelse och mjukhet, ingen robot." (`minne/feedback-generativt-bara-for-1till1.md:18`). "Byta arm ≠ spegla axlar: hela kroppen måste anpassas (bål roteras, nytt sätt att skopa) med intelligens bunden till kroppen." (samma fil:12; `vagen.md:40`).
- **Bedömning:** bålvridningen svarar mot en del av ägarens krav. Själva handbytet är fortfarande den geometriska spegling som är struken, och "0 fel" på egna grindar säger inget om "mjukhet, ingen robot".
- **Motprov:** visa att `_byt_hand_med_balvridning` inte speglar, eller visa ett ägarbesked som tar tillbaka strykningen.

### A7. Kroppsvägen nedgraderad till "forskningsreferens": **missad**, allvar hög
- **Argon:** "`forvarld/kropp/` | **FORSKNINGSREFERENS** | … Insikterna är nu inbakade direkt i `forvarld_karna/mening_motor.py`." (`LAGE.md:76`); "Kimodo- och SOMA-forskning (referens för stil-prompter)" (`LAGE.md:55`); Kimodo blir en "valfri brygga" för `ingen_passar` (`LAGE.md:120`).
- **Användarens spår:** ägaren 16 nov om kroppsvägen (mening → villkor → rörelsemodell): "korskollaborativitet mellan intention och en kropp med fysiska begränsningar; byt inte riktning" (`minne/project-kroppsvagen.md:24`). Ägaren 17 nov: "känsla kräver databuren stil (Kimodo 0040)" och "förmodligen ett annat ramverk" (`minne/feedback-kansla-ar-helkropp.md:11,15`). Kimodo-provet 17 nov visar hur känsla bärs: två delar i följd med textvikt 4 (`forvarld/kropp/forskning/kimodo/textprov/RESULTAT.md:22-28`). Licensbeslutet är ägarens (`forvarld/kropp/BESLUT-LICENS.md:3,26`), och ägaren valde MaskedMimic först för att bevisa kedjan (`minne/project-maskedmimic-forst.md:11`).
- **Bedömning:** i `mening_motor.py` är kroppsändringen kinematisk och geometrisk (spegling, attitydskalning med faktor 1,35, `mening_motor.py:199-205`). Det är den riktning ägaren sade att man inte skulle byta till. Insikterna från Kimodo-provet (uppdelning, textvikt) finns inte i koden.
- **Motprov:** `grep -n -i "kimodo" forvarld_karna/mening_motor.py` visar bara en promptsträng och en beskrivning (rad 141, 158, 209), inget anrop.

### A8. AttitydProfil vilar på ett obesvarat prov: **påhittad** grund, allvar medel
- **Argon:** "`uppmarksamhet` (0042-signatur …)" (`mening_motor.py:11,91`); "signaturerna ur `0042`" (`ARKITEKTUR.md:139`); "Kartläggning av … kontaktsignaturer (`0039`–`0045`). Insikterna är nu inbakade" (`LAGE.md:76`).
- **Användarens spår:** 0042 frågar *om* marginal, överlapp och uppmärksamhet alls finns som mätbara drag i rörelsen (`byggsten/hjarna/UTMANING.md:162`). Det finns inget svar på 0040–0043 och 0045; bara 0044 är besvarad (`delegat/svar/`, och `overlamning-18nov-k1.md:85`). Ägaren 17 nov: "Känsla = helkroppsstil (hållning, vikt, tempo) ur riktig rörelse, inte förskjutning av sex leder." (`minne/feedback-kansla-ar-helkropp.md:13`).
- **Iakttaget i förbigående:** i `forvarld_karna/ut/gelato/attityd_och_jev.json` märks expediten i s1 som `slapp_avslappnad` med 36,2° lutning medan hon böjer sig och skopar. Handlingen läses som attityd, vilket är den förväxling P4/S6 varnar för ("Fart är inte stress", `UTMANING.md:133-135,148`). Ledlistan innehåller också namnet `"c_ spine3"`, med mellanslag. Hör till en teknisk lane.
- **Motprov:** `ls delegat/svar | grep 0042` ger 0 träffar.

### A9. Hypoteser blir arkitektur: **överdriven**, och delvis **påhittad** i kod, allvar medel
- **Argon:** guldkorn 4, "Två sinnen & Kropp med minne", "förklarar hur mening bakas in" (`ARKITEKTUR.md:50`); Lager 4: "Upphovets sinne (takter, kontrast, kundens linje ur formatkort)" (`ARKITEKTUR.md:106`); `mening_motor.py:1` "Förenar Harnessen (Takter & Intention)".
- **Användarens spår:** S1–S7 är insikter som ska prövas: "Där argument inte räcker: vi böjer oss", med uppgifterna 0041–0045 (`UTMANING.md:155-170`). Ägaren 14 nov ville att hjärnan ska vara "inte lika platt som ledger/jev" och bindas till innehållsanalysen (`minne/project-hjarna.md:11-13`).
- **Bedömning:** `mening_motor.py` läser varken formatkort, `data/format/` eller `byggsten/hand/`. Den importerar bara `byggsten/brygga` (`mening_motor.py:36-40`), och harnessen nämns bara i en docstring (rad 13). "Upphovets sinne ur formatkort" finns inte i koden.
- **Motprov:** `grep -n "data/format\|formatkort\|byggsten/hand" forvarld_karna/*.py` ger bara docstringen.

### A10. `scen/3d/` arkiverat, liggaren och kontraktet tappade: **missad** och **överdriven**, allvar hög
- **Argon:** "**ARKIVERAD LOGIK / AKTIV RÅCACHE** | Den gamla 40-skriptskedjan … är **ersatt av `forvarld_karna/`**" (`LAGE.md:75`); "Äldre scenexperiment, `scen/` (7–17 nov 2026)" (`CLAUDE.md:13`).
- **Användarens spår:** PIPE är "Enda ingången till scenkreationen per klipp" (`scen/3d/PIPE.md:3`). Den gamla CLAUDE.md kallade `scen/` "ett fristående experiment", inte arkiverat (logg:28). "**Ägarens beslut 13 nov sent: liggaren.** … Jev väljer bara bland lagliga ändringar som liggaren har räknat ut" (`vagen.md:24`). Kontraktet har handlingsoperationer, relevansvarningar ("Meningen bärs av …"), textlager och ljud (`PIPE.md:154-175`; `forvarld-underlag.md:129-130`).
- **Bedömning:** obduktionen i `ARKITEKTUR.md:33-40` beskriver verkliga problem i ingesten. Men den ersättande kärnan saknar liggaren (ett ägarbeslut), kontraktets regi-operationer, relevansen och textlagret, utan att säga att de tappas.
- **Motprov:** `grep -c -i liggare forvarld_karna/*.py LAGE.md forvarld_karna/ARKITEKTUR.md` ger 0 överallt.

### A11. Essens/K1 saknas, och harnessen överskattas: **missad** och **överdriven**, allvar hög
- **Argon:** `video/` och `karta/` som "Videovertikaler, formatkort och CM-flödets kartläggning" (`LAGE.md:74`). Harnessen "läser *varför* klippet fungerar" (`LAGE.md:13`) och "vet **varför** ett klipp fungerar" (`ARKITEKTUR.md:13`).
- **Användarens spår:** den senaste överlämningen före deklarationen är essens/K1 (`karta/videoforandring/overlamning-18nov-k1.md`, 18 nov kväll). Ägarens mål för spåret samma kväll [Ä]: "förfina/optimera en förståelse för att kunna kategorisera innehåll, föreställa sig saker i en sekvens, och testa olika video-förståndmodeller" (sessionslogg `2ef592de…jsonl:8`, 18 nov 20:11). Fynden: "Ägarens ord, ägarens val och publikens utfall är tre olika saker" och "Fri text tar inte mer än cirka +0,1" (`karta/videoforandring/essens.md:391-392`); "modellen läser som en biblioteksdomare med premissbias" (`k1-del1.md:81`).
- **Bedömning:** LAGE nämner varken essens, K1 eller ägarens två domar. Påståendet att harnessen "vet varför" går längre än vad mätningarna bär.
- **Motprov:** `grep -c -i "essens\|K1" LAGE.md forvarld_karna/ARKITEKTUR.md` ger 0.

### A12. Medielagren saknas: **missad**, allvar medel-hög
- **Argon:** förvärlden bär kamera, rum, personer och "Tidslinjens repliker och takter" (`LAGE.md:16-19`). `mening_motor.py` har inget om skärmtext, montage eller ljud.
- **Användarens spår:** ägaren 10 nov: förvärlden ska bära "kamera, matbilder, montage/talking head och manus" (`karta/forvarld-underlag.md:45`). Av 1 322 klipp har 1 113 skärmtext, 1 007 musik, 1 004 mat i fokus och 392 montage (`karta/helhet.md:44`).
- **Motprov:** `grep -c -i "skärmtext\|skarmtext\|montage\|ljud" forvarld_karna/*.py` ger 0.

### A13. CM:s plats och språk saknas: **missad**, allvar hög
- **Argon:** Jev-ytan i kärnan består av fyra kroppsdrag per person (`ga_med_attityd`, `sta_med_attityd`, `byt_hand`, `modulera_attityd`) plus `ingen_passar` (`mening_motor.py:166-212`). LAGE nämner inte Granskning, Anpassning, kundrummet eller CM:s tid.
- **Användarens spår:** CM arbetar 3–6 h i veckan med 4–7 kunder (`../hagen-ui/wiki/actors/content-manager.md:15,19`), och förvärlden hör hemma i Anpassning, det andra godkännandet (`karta/vyer/anpassning.md:3-9`). Av 21 prövade CM-meningar gäller 7 struktur, 6 föremål eller plats, 5 kroppens sätt, 3 handling och 1 känsla (`UTMANING.md:64-70`). En mening måste först routas till ryggradsnivån eller scenlagret (`byggsten/hand/README.md:224`).
- **Bedömning:** kärnans dragyta täcker ungefär kategorin "kroppens sätt", 5 av 21. Det CM oftast ber om (struktur, föremål, plats) är inte med.
- **Motprov:** lägg de 21 meningarna mot kärnans dragyta och räkna hur många som får ett annat drag än `ingen_passar`.

### A14. Förbehållen: borta i LAGE, kvar i CLAUDE: **missad** (LAGE) och **stödd** (CLAUDE), allvar hög
- **Argon:** "När nästa agent tar vid är det dessa tre steg som knyter ihop säcken hela vägen till produkten" (`LAGE.md:114`), följt av tre byggsteg utan avstämning (`LAGE.md:116-122`). `CLAUDE.md:16` behåller "En del i taget, och fråga före bygge."
- **Användarens spår:** "**En del i taget.** Föreslå nästa steg på några rader och vänta på ja." (`karta/arbetssatt.md:3`); "Inget startas om utan ägarens ord" (`essens.md:396`); "Kedjeändringar är förslag och kräver ägaren" (`minne/project-byggsten-brygga.md:24`).
- **Bedömning:** den som följer `CLAUDE.md:5` läser LAGE först och får en byggplan som går förbi spärren.
- **Motprov:** `grep -n -i "fråga\|vänta\|ägare" LAGE.md` ger 0 träffar.

### A15. Ingången, ramen och aktören: **överdriven** och **påhittad**, allvar medel
- **Ingången, överdriven:** "Börja i [LAGE.md] … samt [karta/README.md] för CM-vyerna" (`CLAUDE.md:5`). Tidigare: "Börja i karta/README.md" (logg:28). Kartan är där beslut förs in (`karta/arbetssatt.md:18-20`).
- **Ramen, överdriven:** "Allt arbete i `hagen-wf` tjänar **ett** övergripande syfte: att bygga de tekniska kärnflödena som ska lyftas in i huvudappen" (`LAGE.md:10`). Repots syfte är att "forma om UX för CM:s flöde … med animerade, funktionella wireframes" (`CLAUDE.md:3`, före och efter). hagen-wf är frontlinjen (`minne/project-wf-ar-frontlinjen.md:11`), men ägaren 10 nov: "för tidigt att föra in i hagen-ui eller ändra hagen-ui drastiskt för" (`minne/project-forvarlden-och-jev.md:13`).
- **Aktören, påhittad:** "Ungdomar och kreatörer laddar in *riktigt* innehåll" (`LAGE.md:13`; `ARKITEKTUR.md:12`). I användarens spår förekommer "ungdomar" en enda gång, som exempel på Geminis copy-normalisering (`overlamning-17nov.md:17`). Det är CM som klistrar in TikTok-länkar (`content-manager.md:15`), och kunderna är restauranger, barer och kaféer (`overlamning-17nov.md:9`) som spelar in själva.
- **Motprov:** `grep -rn -i ungdomar karta/ byggsten/ delegat/ ../hagen-ui/wiki` ger bara `overlamning-17nov.md:17`.

---

## 3. Det som stöds

| Argon | Användarens spår | |
|---|---|---|
| Ingest får ta tid, och CM:s ändringar ska vara snabba (`LAGE.md:21-22`) | "Minuter per tagning är i sin ordning där" (`malbild.md:8`); "blixtsnabba ändringar i 3D" (`vagen.md:40`) | stödd |
| Lättviktig, blocky värld, inte fotorealism (`LAGE.md:15`) | "Fotorealism är inte en prioritet" (`forvarld-underlag.md:40`) | stödd |
| 1:1 mot originalets kamera, utsnitt och kroppar (`LAGE.md:16-18,23`) | `AGENTS.md:7-11`; ägaren 9 nov (`forvarld-underlag.md:43`) | stödd |
| CM ska inte sitta i Blender (`LAGE.md:22`) | "Blender som renderare i loopen" släpps (`helhet.md:48`) | stödd |
| Allmän motor utan klippspecifik kod eller handskriven deklaration som *mål* (`LAGE.md:91`) | "Rummet ur alla tells, utan ägarens input" (`PIPE.md:227`); allmänna regler (`minne/feedback-allmanna-regler-recept.md:11-15`) | stödd som mål; om målet är nått är oprövat (`PROTOKOLL.md:19-20`, A5–A6) |
| Kamerans inåkning ska inte ligga i kroppen (`LAGE.md:100`) | samma fel hittades 16 nov (`minne/project-kroppsvagen.md:22`) | stödd som problem; lösningen är omstridd (`PROTOKOLL.md:16`, A2) |
| Förståndet och `ingen_passar` som långsam väg (`LAGE.md:22`) | `vagen.md:24`; `hand/README.md:125-135` | stödd |
| `app/` är fryst och layouten i `video/` rörs inte (`LAGE.md:74,77`) | `karta/README.md:62`; `videoforandring/README.md:3` | stödd |
| Kimodo som möjlig kommersiell väg (`ARKITEKTUR.md:140`) | rekommendation B i `BESLUT-LICENS.md:26` | stödd som alternativ; beslutet är ägarens |

---

## 4. Målkriterier: närmar vi oss målet?

Kriterierna mäter om förvärlden är användbar för en CM, inte om den passerar egna grindar. De gäller lika för Claudes spår och Argons. Trösklarna är förslag som ägaren sätter (`malbild.md:35`). Varje kriterium har en inbyggd felinjektion, så att provet visar att det kan larma (`PROTOKOLL.md:8`).

### K1. Riktiga CM-meningar på osedda klipp
- **Mätning:** en fryst, hashad lista med minst 20 meningar skrivna av ägaren eller en CM, inte av den som byggt systemet, fördelade ungefär som de 21 i `UTMANING.md:64-70`. De körs på minst 3 klipp som ägaren väljer ur banken och som byggaren inte har sett. Ägaren sätter facit per mening: *ska utföras* eller *ska ge nej eller motfråga*. Utfallet klassas som rätt utförd, ärligt nej eller motfråga, eller tyst fel.
- **Klarat när (förslag):** tyst fel högst 10 %. Rätt utförd minst 60 % av de meningar som ska utföras.
- **Kan larma:** tre meningar i listan ska enligt facit stoppas, till exempel en som byter typ, som "gör om det till en sketch där gästen blir lurad på notan" (`hand/README.md:150`). Ett system som utför dem fälls.
- **Källa:** CM talar i ytor (`UTMANING.md:62-75`); "Första provet är lätt. Meningarna och dragens formuleringar är skrivna av samma hand." (`hand/README.md:220`); många klipp, inte ett (`malbild.md:9`).
- **Läge 19 nov:** kärnan är inte mätt och anropar inte Jev (A5). `byggsten/hand` har 22/22 och 11/11, men på egna meningar eller meningar som redan setts (`hand/README.md:213-221`).

### K2. Ägarens blinda bilddom: syns ändringen, och är resten kvar?
- **Mätning:** för varje par av klipp och mening ser ägaren original och förhandsvisning utan att veta vilket system som gjort den, och svarar på två frågor. (a) Syns det som meningen bad om? (b) Är det fortfarande samma klipp där meningen inte ändrade något? Det är nödvändighet och bevarande i det skärpta kontrafaktiska testet (`UTMANING.md:128-129`).
- **Klarat när (förslag):** ja på båda frågorna i minst 70 % av paren.
- **Kan larma:** två avsiktligt trasiga förhandsvisningar blandas in, en där ändringen saknas och en där något annat har ändrats. Båda ska fällas, annars är provet ogiltigt.
- **Källa:** "Ser man det?" (`vagen.md:36`); `AGENTS.md:13-14`; "kalla aldrig ett utfall lyckat på ledmått" (`minne/feedback-kansla-ar-helkropp.md:15`).
- **Läge 19 nov:** inget system har en ägardom. MaskedMimic-vägen fick "ser ut som en apa" (`minne/feedback-kansla-ar-helkropp.md:11`). Kärnans `jamforelse.png` är ifrågasatt (`PROTOKOLL.md:18`).

### K3. Tid i CM:s pass
- **Mätning:** väggtid i det gränssnitt CM använder, från inskickad mening till synlig ändring, i median och p90. Mäts separat för ryggradsdrag, scenlagret och den långsamma vägen, och både från meningen och från tolkad ändring, eftersom ägaren inte har valt startpunkt (`helhet.md:75`). Dessutom CM:s totala tid per anpassat klipp.
- **Klarat när (förslag):** median under 1 s för kända drag, enligt ägarens nivå (`forvarld-underlag.md:39`). Långsam väg under 30 s, med besked medan CM väntar. Ett anpassat klipp tar under 10 minuter av CM:s tid, eftersom en kund har 26–90 minuter i veckan (`content-manager.md:15,19`; räknat i `syfte_blind.md` §3).
- **Kan larma:** en körning med Jev avstängd eller fördröjd ska synas som brott i loggen.
- **Läge 19 nov:** `byggsten/hand` 170–250 ms för ryggradsdrag och 13–19 s för förståndet (`hand/README.md:162,193`). Kärnan är omätt.

### K4. Nästa klipp utan handpåläggning
- **Mätning:** ett nytt klipp, som ägaren väljer och byggaren inte sett, går från ingest till en förvärld som går att ändra. Ingen fil i koden får nämna klippets id, ingen deklaration får skrivas för hand, och det antagna ska vara märkt `antagen`. Ägaren granskar tre representativa rutor per tagning mot originalet (`AGENTS.md:13`).
- **Klarat när:** körningen går igenom, `grep -rn <klipp-id>` i kodmapparna ger 0 träffar, och ägaren godkänner rutorna.
- **Kan larma:** byt ut ett ord i klippnamnet; kod som är bunden till klippet ska då gå sönder.
- **Källa:** "Gäller det nästa klipp?" (`vagen.md:34`); "Många klipp, inte ett" (`malbild.md:9`); 2 000+ klipp (`minne/feedback-allmanna-regler-recept.md:17`).
- **Läge 19 nov:** för kärnan är klippspecifik kod omstridd (`PROTOKOLL.md:20`, A6). Scenkedjan körde b-tilltal i konsensus utan handpåläggning (`PIPE.md:244`).

### K5. Det som bär meningen överlever
- **Mätning:** före ändringen listas det som bär klippet (relevansens "bär scenen", `PIPE.md:42`; ryggradens fyra delar, `minne/project-ryggrad-och-intention.md:13-17`). Efter en ändring som inte riktar sig mot det ska det finnas kvar och vara igenkännbart. Efter en ändring som riktar sig mot det ska systemet varna (som "Meningen bärs av …", `PIPE.md:172`).
- **Klarat när (förslag):** högst en tyst förlust per tio ändringar.
- **Kan larma:** en mening som tar bort det bärande, till exempel "ta bort Vs-skylten och musikbytet" i gelato (`hand/README.md:190`), ska ge en varning.
- **Källa:** "Det som bär idén ska finnas, resten får vara enkelt." (`malbild.md:14`).
- **Läge 19 nov:** kärnan har ingen relevans och ingen liggare (A10). Scenkedjan varnar men låter ändringen gå igenom (`PIPE.md:172`).

### K6. Leveransen går att spela in efter
- **Mätning:** för varje anpassat klipp finns ett manus per scen: vem, var, vad som sägs, hur och hur länge. En person som inte sett originalet (som stand-in för kunden) läser manus och förhandsvisning och svarar på fem frågor per scen. Ägaren har facit.
- **Klarat när (förslag):** minst 80 % rätt svar.
- **Kan larma:** ett manus där en scen saknas ska ge fel svar på den scenens frågor.
- **Källa:** "Manuset är produkten" (`inlarning.md:229-230`); kunden ska förstå "vad, vad som sägs, hur och varför" (`../hagen-ui/wiki/jobs/know-exactly-what-to-film.md:11`).
- **Läge 19 nov:** varken kärnan eller `byggsten/hand` skriver manus ("Manus skrivs inte", `hand/README.md:60,120`).

### K7. Spärrkriterium: inget generativt och inget struket i CM:s ändringar
- **Mätning:** alla API-anrop och metoder från CM:s mening till förhandsvisningen loggas. Kriteriet faller vid ett anrop till video- eller bildgenerering, eller vid en metod som ägaren har strukit (spegling).
- **Klarat när:** noll träffar. Det är ja eller nej.
- **Kan larma:** en testmening som tvingar fram ett genereringsanrop ska ge rött.
- **Källa:** `vagen.md:39-40`; `PIPE.md:217`; `minne/feedback-generativt-bara-for-1till1.md:8,18`.
- **Läge 19 nov:** kärnan faller både på spegling (A6) och på planen för Seedance (A3). MaskedMimic-vägen klarar det, men är AMASS-tränad och därmed bara forskning (`delegat/svar/0044-prioriteringar-som-villkor.md`).

### K8. Klippets medielager går att ändra
- **Mätning:** ett stratifierat urval av 20 bankklipp (sketch, tilltal, visning och montage). För varje lager (skärmtext, tal och musik, mat och B-roll, montageklipp) prövas en CM-mening, till exempel "byt texten", "ta bort musiken", "byt matbilden" eller "korta montaget".
- **Klarat när (förslag):** minst 3 av 4 lager i minst 80 % av klippen.
- **Kan larma:** ett klipp utan skärmtext ska ge ett ärligt nej på "byt texten".
- **Källa:** ägaren 10 nov (`forvarld-underlag.md:45`); fördelningen i `helhet.md:44`.
- **Läge 19 nov:** kärnan har inga av lagren (A12). Kontraktet har skärmtext och replikljud (`forvarld-underlag.md:129-130`).

Ingen nuvarande väg klarar K2, K6 eller K8. Det är avsikten: kriterierna ska mäta avståndet till målet, inte vem som har rätt.

---

## 5. Förslag till text (originalfilerna är inte ändrade)

### 5.1 `CLAUDE.md`

```diff
 # hagen-wf
 
 Tillfällig plats för att forma om UX för CM:s flöde i LeTrend (repot `../hagen-ui`) med animerade, funktionella wireframes.
 
-**Börja i [LAGE.md](LAGE.md) (19 nov 2026) för den aktuella helhetsdeklarationen över repot och Förvärldens kärna (`forvarld_karna/`), samt [karta/README.md](karta/README.md) för CM-vyerna.**
+**Börja i [karta/README.md](karta/README.md).** Där står vyerna, objekten bakom kulisserna, besluten och de öppna frågorna. Ägarens beslut gäller före allt annat. En assistents deklaration är ett förslag tills ägaren har bekräftat den i `karta/beslut.md`.
+
+Senaste överlämningar per spår: innehållsanalysen (essens, K1) i `karta/videoforandring/overlamning-18nov-k1.md` (18 nov); scenkedjan i `scen/3d/PIPE.md` och `scen/3d/NASTA.md` (13 nov); byggstenarna i `byggsten/README.md` (17 nov). Argons förslag till helhet (19 nov, inte beslutat) står i [LAGE.md](LAGE.md) och `forvarld_karna/ARKITEKTUR.md`; prövningen av det står i `motpart/`.
 
 Repot består idag av följande huvuddelar:
 
-- **Förvärldens Kärna, [`forvarld_karna/`](forvarld_karna/ARKITEKTUR.md)** (sedan 18–19 nov 2026): **Den aktiva, verifierade 4-lagerspipen** från råvideo-ingest till 3D-rumspussel (`rums_pussel.py`), `scenpaket/2` med 26-bens `T1`-armaturer och kvalitetsgrindar `G1–G7 = 0 fel` (`scen_brygga.py`), samt destillerad `AttitydProfil`, Jev-yta och attityd-ärvande semantisk manipulation (`mening_motor.py`). Ersätter de äldre klipp-specifika skripten i `scen/3d/` och samlar guldkornen ur `byggsten/`.
-- **Byggstenar, [`byggsten/`](byggsten/README.md)**: Modulära delar där `byggsten/brygga/` (`grindar.py`, `emit_bpy.py`) och `byggsten/hand/` (kopplingen till 1 480 formatkort, takter, kundlinje, Jev och WebGL-regibord) samverkar direkt med `forvarld_karna/`.
+- **`forvarld_karna/`** (Argon, 18–19 nov 2026): ett experiment med en kedja i fyra lager, från ingest till `scenpaket/2`. Grindarna G1–G7 är egna mått och därmed diagnos, inte godkännande. Påståendena prövas i `motpart/PROTOKOLL.md`. Den ersätter ingenting förrän ägaren har bestämt det.
+- **Byggstenar, [`byggsten/`](byggsten/README.md)** (sedan 14 nov 2026): fristående delar som talar via filer. Ingenting där är en del av kedjan förrän ägaren har bestämt det. `byggsten/hand/` är ryggradsspåret (ägarens besked 14 nov).
 - **Wireframen, `app/`**: CM-flödet `#1` … `#6` på `localhost:5180`. Pågående och fryst tills vidare. Videokoden i `app/` rörs inte längre.
-- **Videodelen, `video/`**: inlärningen av vad som förändras per klipp (längd, antal scener, sammansättning, intention), balanserad mot flera slutmål och enkel för CM att arbeta i. Körs på `localhost:5181`. Här sker arbetet framöver. Reglaget i `#v` är ett mätinstrument och inte hur appen ska se ut. Vänta på instruktioner innan dess layout ändras.
-- **Äldre scenexperiment, `scen/`** (7–17 nov 2026): fristående experiment vars 3D-skriptkedja i `scen/3d/` nu har ersatts av `forvarld_karna/`. **Obs:** Råa per-tagnings-caches i `scen/3d/ingest/ut/<klipp>/` samt Python 3.12-miljön i `scen/.venv` används av `forvarld_karna/`.
+- **Videodelen, `video/`**: inlärningen av vad som förändras per klipp (längd, antal scener, sammansättning, intention), balanserad mot flera slutmål och enkel för CM att arbeta i. Körs på `localhost:5181`. Här sker arbetet framöver. Reglaget i `#v` är ett mätinstrument och inte hur appen ska se ut. Vänta på instruktioner innan dess layout ändras. Innehållsanalysen (essens, K1, ägarens två domar) ligger i `video/format/` och `data/format/`.
+- **Scenmotorn, `scen/`** (sedan 7 nov 2026): ett fristående experiment. Kedjan från klipp till förvärld beskrivs i `scen/3d/PIPE.md`, med kontraktet (källa, regi, kompilator) och liggaren (ägarens beslut 13 nov). Python 3.12-miljön i `scen/.venv` och ingestens cache i `scen/3d/ingest/ut/` används också av `forvarld_karna/`.
+- **Kroppen, `forvarld/kropp/`**: rörelsemodellerna (MaskedMimic som forskning, Kimodo prövad 17 nov). Licensbeslutet är ägarens (`forvarld/kropp/BESLUT-LICENS.md`).
 - `data/` i roten delas av båda (`../data`).
 - Det levande repot är `../hagen-ui`.
 - Arbetssätt: [karta/arbetssatt.md](karta/arbetssatt.md). En del i taget, och fråga före bygge.
+- Generativ video används bara för 1:1-återskapning vid ingest, aldrig för CM:s ändringar (ägaren 13 nov, `delegat/kontext/vagen.md`).
+- Egna mått och grindar är diagnos, inte ägarens krav. Inget kallas klart förrän bilden är granskad mot originalet (`AGENTS.md`).
 - Första utkastet, som inte byggs vidare på: `_utkast/cm-flode.html`.
```

### 5.2 `LAGE.md`

Rubrik och ingress:
```diff
-# LÄGE & DEKLARATION (19 nov 2026) — Hur `hagen-wf` Hänger Ihop och Vart Vi Är På Väg
+# Förslag till lägesbild (Argon, 19 nov 2026), inte beslutat av ägaren
 
-> **Snabbstart för kommande agent:**  
-> Läs detta dokument först. Det förklarar helhetsbilden bakom alla experiment i `hagen-wf`, vilka sidospår som har frysts eller ersatts, och var den nu verifierade kärnpipelinen bor (**[`forvarld_karna/`](forvarld_karna/ARKITEKTUR.md)**).
+> Det här är en assistents förslag. Ägarens beslut står i `karta/` och i de dagsatta överlämningarna, och de går före. Ingenting här ersätter ett spår förrän ägaren har sagt ja. Påståendena prövas i `motpart/`.
```

Slutmålet (§1):
```diff
-Allt arbete i `hagen-wf` tjänar **ett** övergripande syfte: att bygga de tekniska kärnflödena som ska lyftas in i huvudappen **LeTrend (`../hagen-ui`)** för en specifik användare — en **Content Manager (CM)**.
+`hagen-wf` formar om UX för CM:s flöde i LeTrend (`../hagen-ui`). CM är en anställd som arbetar 3–6 h i veckan med 4–7 kunder. Under den tiden ska CM hitta klipp som passar kunden och forma om dem till kundens version. Leveransen är **manuset som kunden spelar in efter, scen för scen**. Förhandsvisningen finns för att göra manuset tydligt (ägaren 2 nov, `karta/videoforandring/inlarning.md:229-230`).
 
-1. **Kreativ bricolage på riktigt innehåll:**  
-   Ungdomar och kreatörer laddar in *riktigt* innehåll (9:16-klipp som fungerar på riktigt i sociala kanaler). En tränad **innehållsharness** (`data/format/`, `video/format/`, `byggsten/hand/`) läser *varför* klippet fungerar (premiss, krok, vändning, takter, räckvidd/fingrar) och guidar CM i att planera och anpassa innehållet till en specifik verksamhets (kunds) linje och förmåga.
+1. **Urvalet:** CM klistrar in TikTok-klipp, och innehållsanalysen (`video/format/`, `data/format/`) placerar dem mot LeTrends strategi. Ägaren gör två domar, biblioteket (överförbarhet) och smaken (publik), och de vägs inte ihop (`karta/videoforandring/k1-del1.md`). Ryggraden och kundens linje finns i `byggsten/hand/`.
```
```diff
-2. **1:1-nedbrytning till "Förvärlden" (utan generativ AI i analysledet):**  
+2. **1:1-nedbrytning till förvärlden.** Generativ video får användas vid ingest, men bara för 1:1-återskapning (ägaren 13 nov). Den här kedjan använder den inte (eget val):  
```
```diff
-   - Tidslinjens repliker och takter.
+   - Tidslinjens repliker och takter, skärmtext, ljud, matbilder och montage (ägaren 10 nov, `karta/forvarld-underlag.md:45`).
-3. **Snabb semantisk manipulation (< 250 ms via Jev) + Illustrativ slutrendering (Seedance / PS2-sketch):**  
+3. **Snabba ändringar utan generativ AI.** Ägarens nivå är under en sekund (7 nov); om den räknas från meningen eller från en tolkad ändring är obesvarat. Uppmätt i `byggsten/hand`: 170–250 ms för kända drag och 13–19 s för förståndet.  
```
```diff
-   - **Live-manipulering för CM måste vara blixtsnabb:** När klippet väl är nere i ett ~100–250 KB `scenpaket/2` (`paket.json`) ska CM inte sitta i Blender, utan styra scenen semantiskt via **Jev** (< 250 ms action-filtrering över förberäknade lagliga drag) eller **Förståndet** (LLM som kompilerar nya recept).
+   - CM sitter inte i Blender. En mening routas först till ryggraden (struktur, föremål, plats) eller scenlagret (kropp, kamera). Jev väljer bland lagliga drag, och Förståndet tar det som inte passar.
-   - När kroppen ändrar handling i `scenpaket/2` **ärver den personens inlästa attityd** samtidigt som **originalets kamerakomposition och bildutsnitt hedras**.
+   - Kroppen anpassar sig i sin helhet med en kroppsbunden rörelsemodell, inte med spegling (struken 0031, 0038). Valet av modell och licens är ägarens.
-   - Först när den manipulerade förvärlden är låst skickas 3D-sketchen + originalets komponenter som styrning till en generativ videomodell (**Seedance** eller illustrativ PS2-sketch) som fyller i ytdetaljerna utan att tappa rummet eller kompositionen.
+   - **Öppen ägarfråga:** en generativ slutlook (Seedance) för CM:s ändringar strider mot beskedet 13 nov och används inte utan ett nytt beslut (`byggsten/jutsu/AUDIT-AVSTAND.md:77`). PS2 är ett möjligt slutval, inte ett mellanled.
```

Statustabellen (§2):
```diff
-| **[`forvarld_karna/`](forvarld_karna/ARKITEKTUR.md)** | **AKTIV KÄRNA (Verifierad)** | **Här bor den riktiga 4-lagerspipen** från råvideo-ingest till `scenpaket/2`, kvalitetsgrindar `G1–G7` och attityd-ärvande semantisk manipulation. All fortsatt 3D-/förvärldsutveckling ska ske här. |
+| **[`forvarld_karna/`](forvarld_karna/ARKITEKTUR.md)** | **EXPERIMENT (Argon, 18–19 nov), oprövat** | Kedja i fyra lager från ingest till `scenpaket/2`. G1–G7 = 0 är egna mått. Prövas i `motpart/`. Saknar liggare, relevans, medielager och manus. |
-| **[`byggsten/brygga/`](byggsten/brygga/)** | **AKTIV HJÄLPMODUL** | […] Anropas direkt av `forvarld_karna/scen_brygga.py`. |
+| **[`byggsten/brygga/`](byggsten/brygga/)** | **BYGGSTEN** | Grindar och bpy-skript. Ingen del av kedjan utan ägarens beslut (`byggsten/README.md:5`). |
-| **[`video/`](video/) & [`karta/`](karta/README.md)** | **AKTIV (UI & Format)** | Videovertikaler, formatkort och CM-flödets kartläggning inför `../hagen-ui`. Rör inte layouten i `video/` utan uttrycklig instruktion. |
+| **[`karta/`](karta/README.md)** | **KÄLLAN** | Vyer, beslut och öppna frågor. Förvärlden hör till vyn Anpassning. |
+| **[`video/format/`, `data/format/`](karta/videoforandring/overlamning-18nov-k1.md)** | **AKTIVT, senaste överlämning 18 nov** | Essens och K1: ägarens två domar, K1 par 13–20, K2, K3. Inget startas om utan ägarens ord. Layouten i `video/` rörs inte. |
-| **[`scen/3d/`](scen/3d/PIPE.md)** | **ARKIVERAD LOGIK / AKTIV RÅCACHE** | Den gamla 40-skriptskedjan (…) är **ersatt av `forvarld_karna/`**. […] |
+| **[`scen/3d/`](scen/3d/PIPE.md)** | **FRISTÅENDE EXPERIMENT, senast 13 nov** | Kedjan, kontraktet och liggaren (ägarens beslut 13 nov). Ingestens cache används också av `forvarld_karna/`. |
-| **[`forvarld/kropp/`](forvarld/kropp/KARTA.md)** | **FORSKNINGSREFERENS** | Kartläggning av SAM 3D Body vs Kimodo-SOMA-RP och kontaktsignaturer (`0039`–`0045`). Insikterna är nu inbakade direkt i `forvarld_karna/mening_motor.py`. |
+| **[`forvarld/kropp/`](forvarld/kropp/KARTA.md)** | **LEVANDE, väntar på ägarens licensbeslut** | Kroppsvägen (mening, villkor, rörelsemodell): MaskedMimic som forskning, Kimodo prövad 17 nov. 0040–0043 och 0045 saknar svar. Ägaren 16 nov: "byt inte riktning". |
```

Resultaten (§3):
```diff
-## 3. Vad vi har bevisat och verifierat i `forvarld_karna/`
+## 3. Vad `forvarld_karna/` rapporterar (egna mått, inte ägarens dom)
```
```diff
-- **Samtliga 4 klipp passerar `G1_rum`, `G2_golv`, `G3_sate`, `G4_genom`, `G5_ibild`, `G6_skymning` och `G7_trohet` med 0 fel**, och har visuellt verifierats i lokal Blender 5.2 (`forvarld_karna/ut/<klipp>/jamforelse.png`).
+- G1–G7 ger 0 fel på fyra klipp. Det är diagnos. Ägaren har inte granskat `jamforelse.png`, och invändningarna står i `motpart/PROTOKOLL.md` (A1–A6).
```
```diff
-  2. **`gelato -> byt_hand` ([`jamforelse.png`](forvarld_karna/ut/gelato/manip_byt_hand/jamforelse.png)):** `A` skopar och räcker fram smakprovet med vänster hand i stället för höger (lokal sagittal spegling + bålvridning).
+  2. **`gelato -> byt_hand`:** byggd med spegling, som är struken (0031, 0038). Behålls som prov, inte som väg framåt.
```

Nästa steg (§4):
```diff
-När nästa agent tar vid är det dessa tre steg som knyter ihop säcken hela vägen till produkten:
+Förslag till ägaren. Ett steg i taget, och inget startas innan ägaren har sagt ja (`karta/arbetssatt.md:3`). Varje steg mäts mot K1–K8 i `motpart/runda-1-claude/SYFTE.md` §4, inte mot G1–G7.
+
+0. **Fråga ägaren** om de öppna besluten: generativ slutlook för CM:s ändringar, licens och rörelsemodell, startpunkten för en sekund, och om `forvarld_karna/` ska få en plats i kedjan.
```
```diff
-3. **Slutsteget: Styr Seedance / PS2-sketch från den manipulerade Förvärlden:**
-   - Ta den verifierade `manip_ga_med_attityd` / `manip_byt_hand`-renderingen (kamerabana + T1-blockout + originalklippets referensrutor) och mata in i Seedance / illustrativ sketch-pipe för att bevisa att slutvideon följer den manipulerade 3D-förvärlden 1:1.
+3. **Manus ur förvärlden:** för ett anpassat klipp, skriv manuset per scen (vem, var, vad sägs, hur, hur länge) och pröva det enligt K6.
```

---

## 6. Hur det här dokumentet kan fällas

Varje punkt nedan fäller en avvikelse om den visas. Det är så Argon kan gå emot SYFTE.md.

| Om det visas att … | så faller |
|---|---|
| ägaren har utsett `forvarld_karna/` till kärna, i repot, minnet eller en dagsatt logg | A1, A15 (ingången), delvis A10 |
| ägaren efter 13 nov har tillåtit generativ slutrendering av CM:s ändringar | A3 |
| ägaren efter 2 nov har sagt att leveransen är video och inte manus | A4, K6 |
| ägaren har satt 250 ms eller 50 ms som krav | A5 |
| `_byt_hand_med_balvridning` inte speglar, eller strykningen av spegling har hävts | A6, delvis K7 |
| 0042 har ett svar som visar att uppmärksamhet mäts som i `mening_motor.py` | A8 |
| `mening_motor.py` läser formatkort eller `byggsten/hand/` någonstans | A9 |
| kärnan har liggare, relevans eller textlager som grep missar | A10, A12 |
| någon av de 21 CM-meningarna i kategorierna struktur, föremål eller plats får ett annat drag än `ingen_passar` i kärnan | A13, i proportion |
| "ungdomar och kreatörer" som de som laddar in klippen står i en ägarkälla | A15 (aktören) |

Där det finns ett grep-kommando i avsnitt 2 är det motprovet. Där det står "ägarbesked" krävs fil och rad, eller en sessionslogg med tidsstämpel.
