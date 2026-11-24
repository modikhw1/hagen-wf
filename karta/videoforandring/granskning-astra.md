**Milstolpen är inte uppnådd.** Arkitekturen fungerar som experimentmotor, men nuvarande representation tappar innehåll som är centralt i restaurangklipp. Varken rekonstruktionsprocenten eller rörlighetsskalan visar att ägarens krav är uppfyllt. Fler kameravarianter löser inte detta.

Granskningen bygger på karta/, kod, sparade data, befintliga skärmbilder och rena beräkningar med modell/väljare. Ingen rendering eller analyskörning har gjorts; inga projektfiler har ändrats. Bilderna belägger visuella fel, inte rörelselikhet över tid. Sökvägar nedan är relativa till projektroten; skärmbilder ligger i rapportens katalog.

Bärande risker, rangordnade:

1. **Innehållet försvinner redan på nivå 5.** Handhållna föremål utesluts ur lokalbeskrivningen, överlappande objekt tas bort och figurerna får tomma tillbehör (`app/rekon/lokal.mjs:48`; `app/rekon/manus.mjs:146–154,193–196`). Bredängs sparade `data/rekon/bredangs.konditoribageri-1778864292655/manus.json:1`, fältet `antaget`, listar borttagen kaffekopp, fat och bricka med bakverk. Även espressomaskinen klassas som handhållen. `sbh-0.png` visar kundens hamburgare i originalet men ingen motsvarande i rekonstruktionen; `bdf-0.png` visar förlorad kopp och felaktig skymning. Detta är innehållsfel, inte bara stilskillnad.
2. **Acceptansmåttet kan godkänna dessa fel.** Åtta tekniska likheter summeras utan validering mot människors innehållsbedömning. Saknade delmått tas bort ur nämnaren (`app/rekon/jamfor.mjs:224–251`). Höga delpoäng kan kompensera för ett misslyckat viktigt moment.
3. **Kamerafriheten överstiger den observerade världen.** En projicerad nyckelbild och uppskattad geometri ger inte underlag för osedda ytor. Dessutom används äldre uttrycksmätningar utan den nya täckningskontrollen. Det gör även variantvalets tekniska giltighet opålitlig.
4. **Vertikalen och kedjans regler saknar mänsklig validering.** `data/bedomningar/` innehåller **0 filer, alltså 0 sparade bedömningar**. Kedjeoptimering finns, men innehållstypens skyddsräcken skickas inte in till väljaren. Att algoritmen hittar en lösning bevisar varken rörlighet eller bibehållet sammanhang.

Rekonstruktionsgraden säger följande:

| Klipp | Total | Pose | Personantal | Bildens uppbyggnad |
|---|---:|---:|---:|---:|
| Kebab | 87,9 % | 97,8 % | 95,8 % | 79,3 % |
| Sibylla | 85,1 % | 99,7 % | 54,3 % | 73,0 % |
| Bredäng | 80,2 % | 93,9 % | 47,0 % | 64,1 % |

Belägg: `data/rekon/b.b.kebab-1779386335747/grad.json`, `data/rekon/sibylla.mlnlycke-1779209627567/grad.json`, `data/rekon/bredangs.konditoribageri-1778864292655/grad.json`, samtliga rad 7, 67, 94 och 101. Dokumentationens kebabsiffra 81 % är äldre.

**Nej, detta mäter inte ”90 % grov likhet”.** Pose använder nio punkter kring huvud, armar och höfter, med toleransen 20 % av personrutans höjd; ben, fingrar och föremål ingår inte (`app/rekon/jamfor.mjs:4,63–73`). Bredängs 93,9 % döljer 36 % för `p1@s2` (`data/rekon/bredangs.konditoribageri-1778864292655/grad.json:27`). Pose och närvaro bygger på motorns projektioner och ska inte avfärdas som dockdetektorbrus. Däremot prövar projektionen inte verklig skymning: `synlig` är figurens aktiveringsflagga (`app/rekon/rendera.js:29–38`). Utsnitt och personantal påverkas av detektorns förmåga att känna igen dockorna. Sibyllas 100 % närvaro men 54,3 % personantal visar varför dessa måste skiljas åt.

Bildens uppbyggnad är korrelation på 18×32 gråskalepixlar; föremålsform, färg och handling verifieras inte. Kameralikheten jämför scenvisa sammanfattningar och kan missa olika rörelseförlopp (`app/rekon/jamfor.mjs:165–210`). Samma extraherade spår används både för uppbyggnad och posejämförelse (`app/rekon/manus.mjs:65,106`; `app/rekon/mat.mjs:50–54`): det testar återgivning av skattningen, inte om skattningen är sann.

Mät i stället innehållsbevarande, tidssatta hand–föremålskontakter, person-/objektsilhuetter, kamera-/motivbanor och bakgrundens stabilitet separat. Redovisa täckning och sämsta scen. Låt flera bedömare jämföra hela klipp blint; saknad hamburgare eller fel avgörande handling ska underkänna oavsett medelpoäng. Definiera sedan ”90 %” med ägaren. Separata dimensioner för identitet, rörelse och flimmer har också stöd i [VBench](https://arxiv.org/abs/2311.17982); dess poäng är dock inget färdigt acceptanstest för detta projekt.

Den linjära Bradley–Terry-modellen är en rimlig förklarbar baslinje, men **ännu bara startvikter**. Utan bedömningar lämnas vikterna oförändrade (`app/kalibrering/modell.mjs:26–43`). Min rena beräkning använder 29 analyserade klipp/182 scener men 0 träningspar. Energi har vikt 1, symmetri −0,2; kant, entropi och balans har just nu vikt 0 (`app/kalibrering/vertikaler.mjs:33–34`). Påståendet att alla pixelmåtten redan belönar artefakter vore därför fel. Risken är däremot direkt för energi: flimmer, felprojicerade kanter och skak kan höja poängen utan bättre scenografi.

Det finns dessutom ett konkret mätfel: energi är rå bildskillnad utan normalisering för tid (`app/analys/pixlar.js:24–30`), men uttrycken mäts i 5 fps och bryggan i 10 (`app/uttryck/matning.js:56`; `app/brygga/kor.mjs:58`). Samma rörelse kan därmed få olika poäng. Bryggans energikorrelation 0,984 på 50 scener visar teknisk överensstämmelse på Nonna-varianterna, inte mänsklig rörlighet eller generalisering till dessa rekonstruktioner (`data/brygga/korrektion.json:278–286`; `app/brygga/rendera.js:13–14`). Okänd motivrörelse blir dessutom 0 i modellens indata (`app/kalibrering/egenskaper.mjs:57`).

Korsvalideringen grupperar klipppar, inte klipp: A–B och A–C kan hamna i olika delar (`app/kalibrering/modell.mjs:70–81`). Löftet om osedda klipp håller alltså inte. Standardisering använder också hela `items`. Dela på konto/klipp före träning och kräv oberoende test; 150 bedömningar/20 klipp/80 % överens är annars en missvisande grind (`app/kalibrering/vertikaler.mjs:12`).

Förklaringen summerar `vikt × egenskapsändring` och skalar om summan till skillnaden i rangsteg (`app/kalibrering/forklaring.mjs:73–89`). Det förklarar modellpoängen, inte en kausal eller isolerad ändring. Kameran kan förstora motivets bildrörelse utan ändrat `amp`. Skalan beror dessutom på vilka kandidater som råkar ingå (`app/kalibrering/placering.mjs:50–58`). Visa exakta parameterändringar, råa mätförändringar och osäkerhet; kalla inte poängandelarna bevis för vad ändringen orsakar.

Uttrycksrummets begränsning är skarpare än dokumentationen antyder. Av de två rekonstruktioner som har uttrycksfil saknar **7 av 8 scener** täckningsmått: hela Bredäng och Sibylla utom `scener[1]` (`data/uttryck/<respektive-klipp-id>.json:1`). Kebab saknar uttrycksfil. Äldre kandidater når ±35°, mot nuvarande ±15° (`app/src/forandring/manus/uttryck.js:24`). Vyn accepterar lagrat `giltig` utan versionskontroll (`app/src/forandring/Forandring.jsx:89–99`; `app/kalibrering/placering.mjs:51`). Vid beräkningen 5→1→10 väljs Sibylla-vyer med 35° och saknad täckning. Återgång till 5 fungerar i kontrollen.

Även ny täckning är otillräcklig: gränsen är 88 %, mätningen medelvärdesbildar tre tidpunkter och originalet märks alltid giltigt (`app/uttryck/matning.js:39–53,108,147`). Projektionsshadern kontrollerar bildgränser, inte djup/skymning från originalkameran (`app/src/forandring/motor/lokal.js:273–283`). Textur på en yta betyder alltså inte att ytan observerats korrekt. Geometrin antar dessutom 68° synfält och 1,42 meters axelhöjd (`app/rekon/geometri.mjs:13–18`), vilket behöver valideras för exempelvis barn och andra linser. Begränsa variation till verifierade bildområden; nya vinklar kräver mer underlag eller manuell modellering.

`amp` förstärker ledrotationer kring medelposen, utan kontaktvillkor; förflyttningsbanan förstärks inte (`app/src/forandring/motor/pose.js:122–135`; `app/src/forandring/motor/spelare.js:34–50`). Kamera + amp är därför användbara men smala spakar. Kontakt med mat/verktyg måste skyddas. Kedjans ytterlägen plattar ut profilens kontraster, grannkostnaden jämför kameraparametrar, och `tillat` är som standard alltid sant (`app/kalibrering/placering.mjs:64–101,129–133`; `app/src/forandring/Forandring.jsx:135`). Detta är inte innehållsbaserade TikTok-skyddsräcken.

Banken innehåller 5 143 metadataförslag, 1 012 valda (`data/bank/forurval.json:319`, räknat över `klipp`), men endast 29 analyser och inga bedömningar. Urvalet missgynnar föremålsbilder och montage (`app/bank/urval.mjs:25–39`), vilket riskerar att träna bort just restauranginnehåll. Typernas 17/4/3/2 klipp räcker inte för stabila regler (`karta/videoforandring/typer.md:15–30`).

Jag skulle prioritera originalvideo i 2D och använda 3D selektivt. Jämförelsen nedan är min tekniska riskbedömning, inte uppmätta leveranstider:

| Strategi | Pålitlighet, förklarbarhet, isolering | Kostnad och tid |
|---|---|---|
| Originalvideo i 2D | Bevarar registrerat innehåll. Digital omkadrering, zoom/pan, skak och stabilisering kan loggas exakt. Hastighetsramper, klipprytm och frysning ändrar även tal/timing/humor och kräver lås. Beskärning får inte dölja avgörande föremål. | Snabbast och billigast att pröva; etablerade [FFmpeg-filter](https://ffmpeg.org/ffmpeg-filters.html). |
| 2D som bas, 3D för nödvändiga vinklar | Bra avgränsning: 3D bara där geometri och innehåll kan verifieras. 2D skapar ingen redigerbar 3D-värld eller nytt agerande. | Måttlig utveckling; handpåläggning för undantagen. |
| AI-video styrd av original/rekonstruktion | Möjlig slutrendering. Styrsignalen förklarar avsikten, inte alla ändringar i resultatet. Kräver kontroll av identitet, föremål, kontakter och tidsförlopp. | Kostnad per omtag och oförutsägbar godkännandetid; avgränsat försök först. |

Nästa tre steg:

1. **Lås acceptansen och stoppa felaktiga godkännanden.** Bedöm de tre klippen scenvis, sedan exempelvis 20 undanhållna klipp från fler konton/typer. Inför veto för innehållsfel; versionsbind manus, mätning och korrektion. Rätta fps-skillnaden och avvisa gamla täckningslösa kandidater.
2. **Pröva vägvalet på samma klipp.** Jämför säkra 2D-variationer med befintlig 3D vid 3/5/7. Nivå 5 ska vara identisk med basen; bedöm både basens likhet och ändringens kvalitet. Om redigerbar 3D är obligatorisk: begränsa stödda klipp och budgetera manuell objekt-/kontaktmodellering.
3. **Kalibrera först därefter.** Samla minst den planerade grindens 150 par, med flera bedömare och separata frågor om rörlighet, innehåll och följdändringar. Testa hela kedjor på undanhållna konton; inför skydd för viktiga takter och kontakter. Testa uttryckligen att tillagt flimmer inte belönas.

Sluta optimera mot ensam totalprocent, massproducera okontrollerade kameravarianter och behandla bättre avatarer som huvudlösning. Pausa massrekonstruktion tills basrepresentationen bevarar klippets viktigaste innehåll.

