# Förregistrering: runda 4, steg 2 och 3

T4, 20 november 2026. **Förslag till låst pilotprotokoll, inte ett genomfört eller godkänt försök.** Jag har läst koden och kört endast metadataurvalet i `las_urval.py`. Inga filmer har bearbetats, inga extraktorer eller paneler körts och hämtningen har inte rörts. Alla trösklar nedan är **T4:s förslag**, inte etablerade ägarkrav. Ägarens kvarvarande beslut står i B7.

Uppdragets senaste ändring ersätter vektorpanelen med invarians och faktiska ömsesidiga ingrepp (`motpart/runda-4/UPPDRAG.md:42–43`). T3 kräver oberoende bedömning av riktning, innehåll, sammanhang och rättelser (`motpart/runda-4/T3-codex/GRANSKNING.md:71–79`). Det är dessa hypoteser som prövas. Ett godkänt pilotutfall säger inget om ny lokal, ny talare, publiklyft eller generell frånvaro av mush.

## Gemensamt: låsning, urval och vad ”osett” betyder

**Förslag — ordning:** lås detta protokoll → verifiera färdiga källfiler → gör referensmätningar och frys förbehandling → bygg och lås implementation på referenskonton → kör steg 2 en gång → öppna steg 3 endast enligt den redan angivna grinden → blind panel → avkoda metodnamnen. Implementationens kod, modellvikter, paketversioner, ffmpeg-version, kommandorader, frön, källornas SHA256 och referensparametrar ska finnas i ett daterat manifest före testmätning. En rättelse efter testinsyn skapar **v2 och ett nytt test**, aldrig ett ersättningsresultat i v1. Den här leveransen bygger inte implementationen.

**Underlag och historik.** Steg 1 har 200 valda klipp från 96 konton, fem typer och ett visningsbaserat urval; typerna är inte mänskligt verifierade (`motpart/runda-4/1-datagrund/URVAL.md:20–36`). Gamla E28/E30/E37-resultat gäller den gamla källmappen; skripten har hårdkodad in- och utmatning och återupptar redan mätta id:n (`video/format/e28-tek.mjs:13–16`; `video/format/e30_tal.py:10–14`; `video/format/e37_personer.py:8–12`). **Kör dem inte oförändrade.** En separat adapter måste läsa de nya filerna och skriva separata resultat med både ursprungs-id och variant-id. Återanvänd inga gamla mätvärden som nya originalvärden.

**Urvalsregel, redan utförd en gång:** frö **202611204**. Sortera varje typ efter den hexadecimala SHA256-strängen av UTF-8-texten `202611204|STEG|TYP|ID`, sekundärt id. Ta nästa kandidat vars konto inte redan valts och inte är uteslutet. Först S3: två par direkt tilltal, två par mat/process, ett par sketch, ett par provsmakning. Sedan S2: 3 tilltal, 3 mat/process, 2 sketch, 2 provsmakning, 2 annat. Ingen videoinformation, lokal mätning eller visningssiffra används. Exakt regel och ordning finns i `motpart/runda-4/T4-codex/las_urval.py:7–38`.

Uteslut från båda testgrupperna alla konton i D-medielagrets tidigare urval, hold-out och utvecklingsklipp, plus de försiktiga aliasuteslutningarna `duepiani`, `spanjorskansthlm`, `kennysgelato2.0`, `gelatonova`. Tidigare använda id:n finns i `motpart/runda-3-opus/D-medielager/urval.json:12–137`; aliasproblemet beskrivs i `motpart/runda-4/1-datagrund/URVAL.md:30–31`. Detta är kontouppdelning, inte bara klippuppdelning. Alla andra klipp från de 24 valda testkontona sätts i karantän. **Referensmängden R är de återstående 144 valda klippen från 72 konton**, exakt mängd given av `las_urval.py:38–49`. Tidigare använda konton får finnas i R.

Ingångarnas SHA256 vid urvalet:

```text
motpart/runda-4/1-datagrund/urval.json
41f5010b60b268264244b69df43be0e2d9fb057dd7c64e946e0a69abacb434e1
motpart/runda-3-opus/D-medielager/urval.json
ec4bf80d26b22acceea98085bc06d27b4d7fc3557354ce2cb3de08dcdd570c37
```

Återskapa enbart metadata: `.\scen\.venv\Scripts\python.exe -I -X utf8 motpart/runda-4/T4-codex/las_urval.py`. Skriptet skriver bara till stdout. Hasharna och id-tabellerna får inte uppdateras efter att mätutfall blivit kända.

**Begränsning som inte går att döpa bort:** T1:s diagnos använde redan 2 703 klipp och T2 läste bankens lokala mått före sin utvärdering (`motpart/runda-4/T1-tolkning/TOLKNING.md:131–138`; `motpart/runda-4/T2-tolkning/diagnos_modellfri.py:34–80`). Dessa konton är alltså **prospektivt undanhållna från just den nya policyn**, inte bevisat aldrig sedda. Byggaren ska före körning intyga att de inte använts för individuell justering av den nya metoden. Finns sådan exponering: provet får kallas utvecklingsprov, inte hold-out. Att byta frö tills man får andra, lovande klipp är förbjudet. Helt historiskt rena konton kan kräva en senare datagrund.

**Materialgrind, förslag:** läs endast färdiga filer i `C:\Users\praiseworthy\Downloads\letrend-r4\`; invänta hämtningens färdigmarkering och stabil filhash. Arkivera ffprobe för bildtakt, PTS, längd, bildformat, färgrymd, SAR och ljud. Ingen uppskalad 2 fps-kopia får räknas som original. Saknat, korrupt eller ersatt id ger dokumenterat materialbortfall, inget nytt handplock. Saknas något av de 24 testklippen avslutas komplett pilot som **ej genomförbar med låst urval**; tillgängliga resultat får redovisas separat. Steg 1:s egna reserver är en annan urvalsoperation, inte ett tyst tillstånd att ändra detta prov (`motpart/runda-4/1-datagrund/URVAL.md:25`).

## A. Steg 2 — försök fälla mätinstrumentet

### A1. De tolv klippen

Radreferenserna nedan avser `motpart/runda-4/1-datagrund/urval.json`; id-raden följs av konto och typ.

| Nr | Typ | Id | Källa |
|---|---|---|---|
| 1 | direkt_tilltal | krogcompanyvarnamo-7442013966571801879 | `urval.json:950` |
| 2 | direkt_tilltal | dirtytaco.se-7383747000782703904 | `urval.json:938` |
| 3 | direkt_tilltal | heat.restauranger-7644981195918314774 | `urval.json:878` |
| 4 | matporr_och_process | burgerism-7571037325820448022 | `urval.json:1010` |
| 5 | matporr_och_process | kroatorpet-7525131256913235222 | `urval.json:1034` |
| 6 | matporr_och_process | deliitaliasegeltorp-7576667334358633750 | `urval.json:1346` |
| 7 | relaterbar_sketch | burgerhytten-7516846069498547458 | `urval.json:1622` |
| 8 | relaterbar_sketch | scandiclaholmen-7450083156335660310 | `urval.json:1610` |
| 9 | vardens_provsmakning | ahlancoffeehouse-7644306822559485204 | `urval.json:2078` |
| 10 | vardens_provsmakning | yucmexican-7461900020187450646 | `urval.json:1982` |
| 11 | annat | youmpjonkoping-7612607465808514326 | `urval.json:494` |
| 12 | annat | babasburgers-7625983366470454550 | `urval.json:158` |

### A2. Exakta ingrepp och kontrollernas innebörd

**Förslag.** O är originalet. C är en gemensam, intraframekodad 30 fps-referens; inga förändringar staplas efter varandra. C är ett försöksvillkor, inte påståendet att originalet var 30 fps. O→C måste först klara nedanstående blinda innehållskontroll. Är källan exempelvis HDR, icke-kvadratiska pixlar eller har en avsiktlig A/V-startförskjutning som kommandot inte bevarar, räknas det som material-/adapterbegränsning; ingen dold färg-, beskärnings- eller synkrättning tillåts. Alla varianter genereras från C, med samma låsta ffmpeg-bygge. In- och utvägar anges som separata argv-element, ingen shellinterpolering.

Baslinje, för SDR med kvadratiska pixlar; ljudet behåller sin samplingsfrekvens och sina kanaler:

```text
ffmpeg -nostdin -hide_banner -loglevel warning -y -i O.mp4
  -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1
  -vf "fps=fps=30:start_time=0:round=near,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0,setsar=1"
  -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a pcm_s24le
  -fps_mode passthrough C.mkv
```

Radbrytningarna är för läsning; varje recept är ett anrop. Gemensamt prefix för varianterna: `ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1`. Lägg till exakt följande suffix:

| Variant | Exakt suffix | Avsedd kontroll |
|---|---|---|
| N0, identitet | `-c copy N0.mkv` | Hantering/adapter ska inte skapa skillnad. |
| N1, omkodning | `-c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p -threads:v 1 -c:a copy -fps_mode passthrough N1.mkv` | Kompression med oförändrad tidslinje och ljud. |
| N2, halverad upplösning | `-vf "scale=w='max(2,trunc(iw/4)*2)':h='max(2,trunc(ih/4)*2)':flags=lanczos,setsar=1" -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N2.mkv` | Halva bredden/höjden, avrundat ned till jämna pixlar. |
| N3, −6 dB | `-af volume=-6dB -c:v copy -c:a pcm_s24le N3.mkv` | Ren förstärkningsändring, ingen limiter/normalisering. |
| N4, −12 dB | `-af volume=-12dB -c:v copy -c:a pcm_s24le N4.mkv` | Starkare förstärkningsstörning, ingen klippning genom förstärkning. |
| N5, 30→15 fps | `-vf "fps=fps=15:start_time=0:round=near" -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N5.mkv` | Samma varaktighet och händelsetider; varannan bild försvinner. Ingen `setpts` här. |
| N6, kantbeskärning | `-vf "crop=iw-4:ih-4:2:2,pad=iw+4:ih+4:2:2:black,setsar=1" -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N6.mkv` | Två pixlar per kant ersätts av svart, ingen omskalning. Sekundärt stresstest. |
| P, verkligt snabbare | `-vf "setpts=(PTS-STARTPTS)/1.25,fps=fps=30:start_time=0:round=near" -af "atempo=1.25" -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a pcm_s24le -fps_mode passthrough P.mkv` | Bild och ljud blir 1,25 gånger snabbare, cirka 0,8 gånger långa; `atempo` ändrar inte avsiktligt tonhöjd. |

För ljudlösa källor utelämnas enbart `-af` och ljudcodec, och N3/N4 markeras ej tillämpliga. Ingen syntetisk tystnad skapas för att få ett VAD-resultat. N0 och extraktionen av C körs två gånger. P ska behålla hela källans innehåll i samma ordning: inget trim, inget `-shortest`, ingen ny musik. Logga A/V-sluttider och kräv avvikelse från avsedd tidsavbildning högst en 30 fps-ruta plus en ljudsamplingsperiod; avvikelse stoppar renderaren, inte mätaren.

**En förändring är inte innehållsbevarande bara för att den heter teknisk.** Före extraktorresultaten öppnas bedöms C mot O, och varje N mot C, blint: (i) samma handling/ord/poäng läsbar, (ii) samma framförandetempo, (iii) samma upplevda energi? Svar ja/nej/osäker, separata frågor. Vid ljudnivåkontrollen görs två lyssningar: oförändrad spelarnivå för ljudnivådimensionen; exakt +6 respektive +12 dB uppspelningskompensation för innehåll/framförande. **Mätfilerna normaliseras aldrig.** Bedömaren ser inte varianternas namn eller mätvärden. Ett ”nej/osäker” gör just den invariansutsagan ogiltig för klippet, inte klippet godkänt. Redovisa både alla råskillnader och den i förväg blindgodkända delmängden; inga bortfall baserade på måttens storlek.

P är positiv kontroll för tidsförlopp, inte för personantal, ljudstyrka eller automatiskt för ”mer energi”. Bedömaren ska identifiera P som snabbare och med samma handling/ord; energibedömningen hålls separat. Om färre än 10/12 P är perceptuellt tydliga är kontrollen otillräcklig och försöket får ingen generell tempodom. N6 är sekundärt: det får fälla ett påstående om kantrobusthet men får inte rädda/fälla huvudgrinden för N1–N5. N5 kan vara perceptuellt betydelsefullt för vissa rörelser; sådana fall får inte kallas mätarfel enbart för att måttet reagerar.

### A3. Mått, fryst förbehandling och rangfelet

**Kör de existerande definitionerna**, med explicit nya sökvägar och frysta versionsberoenden. E28 använder scenpoäng vid varje bild, gränsen `>0.3`, tystnad `−35 dB / 0,3 s` samt EBU R128 (`video/format/e28-tek.mjs:23–38`). E30 använder 16 kHz mono, Silero ONNX och minst 300 ms tystnad (`video/format/e30_tal.py:15–25`). E37 tar sex rutor vid relativa positioner 0,05…0,95, YOLOv8n, `imgsz=320`, klass 0 och konfidens ≥0,4 (`video/format/e37_personer.py:12–23`). Modellvikter ska redan finnas lokalt; ingen automatisk nedladdning. VAD-standardargument som inte syns i skriptet ska lösas ur installerad version och skrivas explicit i manifestet före körning. Byt inte till medielagrets andra VAD-standarder i smyg (`motpart/runda-3-opus/D-medielager/medielager/steg_ljud.py:57–63`).

Alla skalärfält i följande tabell mäts, inte bara de som ser bra ut. Spara också E28:s `skott`-lista och scen-/tystnadslogg, E30:s faktiska VAD-intervall som adapterbilaga och E37:s sex `antal`. Utdataformaten kan kontrolleras i `data/format/e28/tek.jsonl:1`, `data/format/e30/tal.jsonl:1`, `data/format/e37/personer.jsonl:1`. Adapterbilagorna är **nya loggar**, inte redan existerande E30-fält.

| Klass | Fält | Vad P får belägga / rå tolerans ε för tekniska ändringar |
|---|---|---|
| T: tid | E28 `langd`, `skott_median`, `skott_max`, `forsta_byte`, `forsta_ljud`; E30 `langd`, `forsta_tal` | Förväntad faktor 0,8 när händelsen finns. ε=0,10 s. Noll eller frånvarande händelse ger inget känslighetsbevis. |
| T: händelsetäthet | E28 `takt`; E30 `tal_per_s` | Förväntad faktor 1,25 om samma händelser detekteras. ε=0,02/s respektive 0,005/s. **Segment/s är inte ord/s.** |
| T?: bildförändring | E28 `rorelse`, `rorelse_2s`, `rorelse_kvot` | Kandidater för tidslig känslighet, ingen förutbestämd energitolkning. ε=0,20; 0,20; 0,10 i respektive utdataenhet. |
| G: räkning | E28 `byten`, `pauser`; E30 `tal_segment` | Ingen tvingad positiv respons på global hastighet. ε=0. Detektionens minsta pauslängd kan ändra segmentantalet. |
| G: andelar/form | E28 `skott_max_andel`, `skott_cv`, `ljud_andel`; E30 `tal_andel` | Inte generella tempomätare. ε=0,02; 0,05; 0,02; 0,02. |
| G: fast tidsfönster | E28 `byten_3s` | ε=0 för N. P får flytta händelser över 3 s-gränsen; jämför med originalets bytestider, inte ett antagande om bevarat antal. |
| L: ljudnivå | E28 `lufs`, `lra` | LUFS ska ändras −6/−12 LU i N3/N4, tolerans 0,5 LU. För övriga N: ε=0,5 LU; LRA ska vara stabil även vid ren gain, ε=0,5 LU. Ingen tempokvot för dessa. |
| G: personer | E37 `antal[0..5]`; härledda `personer_medel`, `andel_minst_en`, `andel_minst_tva`, `personer_max` | ε=0 per ruta, medel/andel/max. Ingen positiv temporiktning krävs. Härledningar: medel av antal, medel av indikator ≥1/≥2, max. |

Fältens definitioner står i `video/format/e28-tek.mjs:34–38`, `video/format/e30_tal.py:25`, `video/format/e37_personer.py:23`; T2:s tre personaggregat i `motpart/runda-4/T2-tolkning/diagnos_modellfri.py:49–53`. Alla toleranser ovan är valda före mätning, inte skattade ur testresultatet.

**Fryst referenstransform:** mät endast R:s C-versioner vid anpassning. Varje konto har total vikt 1/72, fördelad lika över dess referensklipp. För varje numeriskt fält definieras

```text
F_j(x) = Σ_i w_i [1(r_ij < x) + 0,5 · 1(r_ij = x)]
z_j(x) = (F_j(x) − μ_j) / σ_j
```

Här är μ och σ det viktade medelvärdet och standardavvikelsen av F på R, frysta efter R. Lika råvärden får exakt samma värde; ingen testvariant, testkonto eller ny omkodning får bidra till F, μ eller σ. Detta rättar T2:s dubbla `argsort`, som gav lika värden olika rang och anpassades på hela materialet (`motpart/runda-4/T2-tolkning/diagnos_modellfri.py:76–80`; `motpart/runda-4/T3-codex/GRANSKNING.md:31–45`).

Referenskonstant fält: ingen division med godtycklig epsilon och inget påstående om informativ axel; använd endast rå invarianskontroll och flagga nya råvärden utanför referensstödet. Spara alla råvärden även när ECDF mättas utanför stödet. Saknade ljudspår, modellfel och ej avkodade bilder är tre olika tillstånd. `forsta_tal=None` vid inget tal behålls som censurerat/”inget tal”; det ersätts inte av noll och hela raden kastas inte. Vid avståndsdiagnosen används fryst referensmedian för saknade numeriska värden och en separat saknasindikator; saknasindikatorn får aldrig avgöra tempopolicyn. Om referensvärden saknas, normalisera vikter över giltiga referenskonton för just fältet; färre än 30 giltiga referenskonton innebär ingen kalibrerad axel.

**Förtest av transformen:** permutera R och testtabellens radordning 100 gånger med `numpy.random.default_rng(202611204)`; efter återställning av id-ordningen ska alla z skilja högst 1e−12. Lägg därefter till en kopia av en testvariant utan att passa om; tidigare z ska vara oförändrade. N0 och dubbel extraktion ska ge identiska exporterade fält. Ett enda brott stoppar instrumentet före övriga slutsatser. Varianter är upprepade mätningar av samma klipp, aldrig nya oberoende observationer.

### A4. Förutbestämd dom per mått

**Förslag — inte signifikanstest.** Analysenheten är klippet/kontot, n=12. Redovisa per ingrepp, per klipp och per fält; inga poolade ”72 observationer” eller sökta bästa koordinater.

För ett T-/T?-fält j och klipp i, bland blindgiltiga N1–N5:

```text
t_ij = max_N |x_j(N_i) − x_j(C_i)|
p_ij = |x_j(P_i) − x_j(C_i)|
q_ij = t_ij / p_ij
```

Beräkna q endast om p överstiger tabellens ε, annars märk **positivt okänslig**; använd inte ett litet tillsatt tal för att få en bekväm kvot. Beräkna samma kvot i fryst z som separat diagnos; god z får inte dölja ett rått fel genom ECDF-mättnad. Vid T-tid/-täthet krävs dessutom förväntat tecken, och vid stabilt händelseantal högst `max(ε, 10 % av den förväntade positiva ändringen)` från faktor 0,8/1,25. T? har bara det svagare responskravet och får inte kallas semantiskt validerat av det.

**T/T? fälls som styrmått** om något av följande gäller:

1. Färre än 8 klipp har både giltig positiv kontroll, p>ε och giltiga N1–N5 för fältets avsedda innehållsegenskap: **otillräckligt känsligt/underlag**, inte godkänt.
2. Median q≥0,5, eller q≥1 på minst 3 klipp. Godkänt kräver median q<0,5 och högst 2 sådana klipp. Även ett tydligt enskilt q≥1 redovisas som motexempel, inte bortfall.
3. Teknisk ändring över ε på minst 3/12 klipp; eller fel positivt tecken på minst 3 tillämpliga klipp. Därmed räcker det inte att både teknisk och positiv påverkan är stora.
4. Nytt saknat värde, förlorat ljudspår eller färre än sex E37-rutor på minst 2 klipp: tekniskt otillförlitligt. Enstaka fel redovisas och får inte imputeras bort i grinden.

För **G** används endast det invarianspåstående som passar fältet: fäll vid skillnad över ε på minst 3/12 blindgiltiga klipp, per tekniskt ingrepp eller i deras union. För **L** används det förväntade gain-svaret ovan, inte invarians mot gain; fäll vid avvikelse från detta eller övriga stabilitetskrav på minst 3 klipp. Om färre än 8 klipp överhuvudtaget är giltiga för en angiven kontroll blir domen ”ej prövat”, inte pass. Samma personer ska helst detekteras vid motsvarande relativa innehållstid även efter P; avvikelser är sampling-/detektionsdiagnos, inget bevis på identitetsförlust.

**Grannar och ”särprägel”, endast negativa diagnoser:** använd T2:s fasta 19 fält (`motpart/runda-4/T2-tolkning/diagnos_modellfri.py:39–41,53,87`) med ovanstående korrekta transform, plus saknasindikatorer; ingen ny viktoptimering. Beräkna euklidisk norm och fem närmaste grannar **bara i R**, med id som utslagsregel vid exakt lika avstånd. Redovisa kvarvarande grannar, normförskjutning och avstånd för C/N/P. Fäll användning som stabilt granninstrument om N1–N5 byter minst 3/5 grannar på minst 3 klipp. Normen får inte döpas till uppmätt mush: just den slutsatsen drogs tillbaka i domen (`motpart/runda-4/DOM_T1_T2.md:45–48`). Ingen ny mush-gräns efter resultaten. Om någon vill föra vidare en gammal binär mush-regel måste dess exakta formel och referenströskel låsas före körning; en teknisk variant som ensam växlar dom är då ett motexempel. Utan sådan regel rapporteras ingen binär mush-dom.

### A5. Prognoser före körning

- **Förväntas falla som generell tempo/energi-axel: `rorelse`, `rorelse_2s`, ofta `rorelse_kvot`.** Medelvärdet av bildvisa scenpoäng har ingen normalisering per tidssteg; 30→15 fps ändrar avståndet mellan jämförda bilder (`video/format/e28-tek.mjs:25,33–37`). Detta är en mekanistisk prognos, inte ett observerat utfall.
- **Förväntas vara känsliga: `ljud_andel`, `pauser`, `forsta_ljud`.** Absolut −35 dB-gräns kan passeras när samma ljud sänks; tystnad i slutet kan dessutom saknas i summeringen eftersom bara avslutade start/slut-par matchas (`video/format/e28-tek.mjs:23,29–31`).
- **`lufs` ska förändras vid gain.** Det fäller användning som gain-invariant innehålls-/framförandeenergi, men är rätt beteende för ljudstyrkemåttet. `lra` bör vara betydligt stabilare. Att ge LUFS samma positiva tempokvot som `takt` vore ett kategorifel (`video/format/e28-tek.mjs:32,38`).
- **E37 kan falla i låg upplösning/nära tröskeln.** Sex rutor och hård 0,4-tröskel ger stegvisa hopp; detta är inte ett bevis för att personen eller identiteten ändrades (`video/format/e37_personer.py:17–23`).
- **`tal_per_s` kan överleva teknikprovet men ändå misslyckas som framförandeenergi.** Sammanhängande snabbare tal kan fortfarande vara ett enda segment; 300 ms-gränsen kan slå samman pauser (`video/format/e30_tal.py:23–25`). Den semantiska frågan lämnas till steg 3.
- **`langd` bör klara teknikprovet; `takt` bör ofta klara omkodning men kan få falska byten vid bildtakt/skala.** Ett godkänt längdmått bevisar bara rätt tidslinje, inte användbar stil (`video/format/e28-tek.mjs:26–28,34`).

## B. Steg 3 — en fryst policy på faktiska par

### B1. Vad som faktiskt finns och vad som måste skrivas

I denna tabell betyder `D/` den fullständiga sökvägen `motpart/runda-3-opus/D-medielager/`; förkortningen gäller endast källhänvisningar.

| Förmåga | Verifierat i källkod | Begränsning för detta prov |
|---|---|---|
| Korta montage | `D/medielager/operationer.py:423–511`: tar bort vissa tysta B-rolltagningar och trimmar andra; ffmpeg trim/concat; tidsavbildning returneras. | Kan ändra tempo, men tar bort innehåll och har ingen förlängande motsvarighet. Färre än tre tagningar ger nej (426–428). **Inte en allmän pauskortare.** |
| Skydda krok/avslut | `operationer.py:433–440` skyddar första/sista i listan som stryker hela tagningar. | Fas 2:s filter på 453 saknar `id not in skydd`; även första/sista utan tal kan trimmas. Det motsäger `D/README.md:75–77` och resultattexten `operationer.py:507–508`. Måste rättas/verifieras, inte tas som garanti. |
| Ta bort musik | `operationer.py:248–273`, särskilt 255–262. | Befintlig röststam krävs; separationsfel/sång kan finnas. Deterministisk operation på frysta stammar, ingen garanti om upplevd energi. |
| Byta musik | `operationer.py:276–304`; mix med `volume=0.6`, `amix normalize=0` på 291–293. | Kräver given fil. **Utan talstam byts hela ljudet**, 295–299; detta får inte användas som ”tal bevarat”. Ingen automatisk musikpolicy eller nivåparameter. |
| Justera ljudnivå | Endast den hårdkodade musiknivån ovan; API-listan i `D/README.md:51–60` och ljudgrenen i `D/medielager/api.py:78–84`. | Ingen fristående gain-/LUFS-/duckningsoperator i det granskade API:t. Måste skrivas om den ska ingå. |
| Pauskorta/pausförlänga | VAD-intervall finns i `D/medielager/steg_ljud.py:57–63,77–89`. Operationslistan är `operationer.py:7–14`. | Ingen sådan operator i detta medielager. Behövs symmetrisk tidsavbildning för bild, tal, musik och text. VAD-fritt är inte lika med innehållsfritt. |
| Tempo utan avsiktlig tonhöjdsändring | Befintliga `setpts` nollställer trimsegment (`operationer.py:478–496`); de skalar inte tempo. | Ingen `atempo`-operator i den granskade operationsfilen/API:t. Ny gemensam styckevis retimer med `setpts` + `atempo` behövs. |
| Styra klipprytm åt båda håll utan innehållsborttagning | Befintlig montageoperation ovan är ensidigt subtraktiv. | Ny retiming per tagning/paus behövs; får inte ersättas med att stryka fler tagningar och kalla det samma ingrepp. |

**Befintliga mätgrindar räcker inte:** montage räknas synligt vid ≤85 % längd och godtar ordåterkallelse ≥0,8 (`D/medielager/matning.py:202–221`); det är varken riktning mot en partner eller bevarad poäng/avsikt. PSNR jämför dessutom tre rutor per bevarat segment, inte hela framförandet (207–215). Rapporten anger bara 1/20 montagefall med både egna `syns` och `kvar`, samt 12 nej (`D/RAPPORT.md:9–19`). Detta är underlag för försiktiga förväntningar, inte skäl att byta testklipp. Att underkänna en faktiskt lyckad retiming med oförändrad gammal PSNR-tidsavbildning vore också fel; efterkontrollen måste använda den levererade avbildningen.

### B2. Sex låsta par

A/B nedan är bara stabila id-etiketter, inte påstådd hög/låg energi. Alla tolv konton är olika och skilda från steg 2 och R. Källa för varje id är `motpart/runda-4/1-datagrund/urval.json` på angiven rad; dragningen finns i `motpart/runda-4/T4-codex/las_urval.py:20–33`.

| Par | Typ | A | B |
|---|---|---|---|
| 1 | tilltal | landhskonditori-7428326881197378849 (`:530`) | the_street_food_labs-7564700889705909526 (`:614`) |
| 2 | tilltal | vaso.streetfood-7395943137727761697 (`:710`) | restaurantkulhuset-7651339833960385814 (`:758`) |
| 3 | mat/process | brunchoteket-7430146350924320022 (`:1130`) | kebabdudes-7421553554965499169 (`:1082`) |
| 4 | mat/process | dedeskungsholmen-7702833079445949719 (`:1070`) | pataka.stockholm-7554026124938841366 (`:1310`) |
| 5 | sketch | edessa.bistro-7694714579225529622 (`:1694`) | kebabbabes-7564062593711705366 (`:1826`) |
| 6 | provsmakning | njuta.orebro-7568175701023608086 (`:2174`) | germandonerkebabuk-7548756229569383702 (`:2282`) |

Ingen sållning efter att någon tittat på vilka par som har snygga pauser, tydlig skillnad eller lättredigerat innehåll. Denna täckning är en del av provet. Ett olämpligt par får ett ärligt nej som räknas i nämnaren sex. Typetiketten används bara för urvalet; den får inte rädda en policy som läst klippet fel.

### B3. Fryst förinställd policy P1 — konkret och avsiktligt begränsad

**Förslag, inte befintlig kod.** Uppdraget är: ”För A och B närmare respektive längre ifrån varandra i framförandets tempo/energi; behåll deras innehåll och särart.” P1 prövar hypotesen att **temporal händelsetäthet plus innehållsanpassad tidsfördelning** räcker för ett första sådant standardbeslut. Den påstår inte att all energi är en skalär.

**Ingångar:** ursprungliga C-filer, deras E28 `takt` och bytestider, E30 `tal_per_s`, `tal_andel` och VAD-intervall, längd, R:s frysta z-transform samt riktning `mot|från`. Ingen fri texttolkning, inga visningar, inget kontonamn, ingen manuell tidsmarkering, inga nya modeller eller målklipp från en granne. Id används bara för loggning. Ingen provrendering följd av val av ”bästa” resultat.

**Grind från steg 2:** både `takt` och `tal_per_s` måste klara A4 som T-mått. `tal_andel` måste klara sitt G-krav och adapterloggen måste vara reproducerbar. Annars stoppas P1; ingen efterhandsviktning där ett fällt mått försvinner. Ett separat rent ffmpeg-prov får fortfarande göras men ska kallas operatörsprov. Instrumentets grind är nödvändig, inte ett positivt facit för steg 3.

**Läsning och tecken:** beräkna för varje original `e = 0,5·z(takt) + 0,5·z(tal_per_s)`. Saknade styrfält, referenskonstant styrfält eller `|e_A−e_B|<0,5` ger nej för paret, utan ersättning. Det lägre e-klippet får högre hastighet och det högre lägre hastighet i **mot**; i **från** vänds båda tecknen. Detta läses bara på originalen, inte iterativt på de manipulerade filerna. Om panelens ursprungliga rangordning inte håller med är det ett möjligt läsfel hos policyn, inte fel hos panelen.

**Tillåtna åtgärder:** endast styckevis tidsomskalning av klippets egna bild- och ljudintervall i ursprunglig ordning. Ingen tagning, replik, person eller bildyta byts/tas bort; ingen bildinterpolering, frameblend, ny musik, tonhöjdseffekt eller Demucs behövs. Att korta en paus här betyder att spela dess befintliga innehåll snabbare, inte förutsätta att tystnad kan raderas. Inbränd text följer bilden; externa tidsstämplar får samma tidsavbildning.

**Tidsindelning:** skydda exakt första och sista 0,25 s. Använd E28:s bytestider och E30:s VAD-start/slut, med ±0,15 s skyddsmarginal runt tal. Slå samman överlappande talintervall. Lägg brytpunkter vid dessa gränser och skyddsgränserna. Kvantisera inre brytpunkter till närmaste C-ruta (`floor(30t+0,5)/30`); ta bort dubletter och nollintervall. Försöket använder samma indelning för P1 och jämförelseregeln, och hela mixljudet följer bilden. Märk ett intervall som tal om det överlappar ett skyddat talintervall. Logga även den okvantiserade VAD:n.

**Val av fördelning, utan sökning:**

1. Om klippets `tal_andel≥0,20`: vikt w=4 för intervall helt i en inre VAD-lucka som efter marginalerna är minst 0,50 s; w=1 för övriga icke-talintervall; w=0,25 för talintervall. Första/sista 0,25 s har w=0. Vikterna prioriterar pauser men förbjuder inte måttlig talretiming när pauser saknas.
2. Annars: låt m vara medianen av originalets tagningslängder, och l längden på den tagning som intervallet tillhör. Vid snabbare: `w=clip(l/m,0,5,2)`; vid långsammare: `w=clip(m/l,0,5,2)`. Skyddad början/slut har w=0. Detta förkortar främst långa tagningar respektive ger främst korta tagningar mer tid. Det är en förregistrerad estetisk hypotes, inte härlett ägarfacit.
3. För varje intervall med längd d väljs tidsmultiplikator `g=1+σ·min(c,λw)`, där σ=−1 för snabbare, +1 för långsammare; c=0,20 respektive 0,25. Välj den enda λ≥0 som ger `Σ d·|g−1|=0,10·L`. Lös monotont: fördubbla övre gräns från 1 tills målet innesluts, därefter 80 bisektionssteg. Om kapaciteten inte räcker: nej, ingen ensidig ändring. Hastighet är `r=1/g`, alltså inom [0,8;1,25].
4. Rendera varje [a,b)-del med bild `trim=start=a:end=b,setpts=g*(PTS-STARTPTS)` och ljud `atrim=start=a:end=b,asetpts=PTS-STARTPTS,atempo=1/g`; concat i samma ordning, avsluta bild med `fps=30`. Alla numeriska parametrar skrivs med 9 decimaler och invariant decimalpunkt. Samma renderare, splitpunkter, kodekar och ljudbehandling för P1 och C1. Inga automatiska extra övergångar/loudnessnormaliseringar som skiljer armarna. Konkatenering får inte ändra ordning eller skapa extra innehållstid. Små skarvfel bedöms, inte göms med generering.

Byggaren måste leverera en explicit monotont växande original→ut-tidskarta och en ny tidslinje för alla lager. Kontrollera start/slut, ljudsynk och budget mot kartan, med tolerans en C-ruta. Exportera alla fyra parvarianter före panelen. Dubbelkörning ska ge samma recept och avkodade A/V-innehåll med det låsta bygget; bytehash av container är sekundär.

### B4. Konstant jämförelseregel C1 och lika redigeringsbudget

**Förslag.** C1 får **samma ursprungliga e-rangordning och riktning** som P1. Den gör inga innehållsanpassade prioriteringar: alla oskyddade intervall får samma tidsmultiplikator `g=1+σ·0,10L/(L−0,50)`, och de två skyddade ändarna g=1. Den använder samma renderare och tidsindelning som P1. Det är en konstant dosregel, inte en medvetet felvänd eller slumpmässig svag motståndare. Jämförelsen isolerar P1:s extra beslut om **var** tiden ska ändras; den bevisar inte att P1 läser energiriktningen bättre än C1, eftersom läsningen delas.

Budgeten låses **per klipp och riktning**, inte bara som total över paret:

```text
B = Σ d·|g−1| / L = 0,10
antal borttagna källintervall = 0
antal införda källintervall = 0
hastighet i varje intervall ∈ [0,8;1,25]
samma tillgängliga intervall och samma 0,25 s ändskydd
snabbare: total längd 0,90L; långsammare: 1,10L, inom en C-ruta
```

Redovisa också maxhastighet, antal hastighetsövergångar och faktiskt utfall av budgeten; de kan förklara skillnader men får inte ändra gränserna efteråt. Är en arm tekniskt oförmögen ska det synas som misslyckande, inte få en mindre budget utan markering. Samma redigeringsbudget betyder här samma tidsmängd och åtgärdsutrymme; det betyder inte påstått samma perceptuella styrka. Just fördelningen av styrkan är vad P1 väljer.

**Viktig avgränsning:** de globala nämnarna kan nästan garantera att `takt` och `tal_per_s` ökar när L minskar även om valet är estetiskt dåligt. Därför får deras eftermätning bara verifiera mekaniken. Riktning, innehåll och färre rättelser avgörs nedan, inte av e eller avstånd till R. Mot/från får inte översättas till att båda klippen enbart blir snabbare.

### B5. Panel: frågor, blindning och kontrollpar

**Förslag.** Sex par × två riktningar × två regler = **24 bedömningsfall, 48 redigerade filmer**, plus de 12 originalen. Visa hela klipp, samma bildyta och fast spelarnivå; ingen redigerad sammanfattning. Ordna först originalens A och B efter hash av `202611204|panel-original|par`; visa dem före varianterna och registrera ursprunglig tempotolkning. Blanda sedan alla fall efter `SHA256(202611204|panel|par|riktning|regel)`. Vänster/höger och spelordning styrs av sista hashbit. Dölj metod, mål-riktning, filnamn, mått, visningar och kontoetiketter; ansikten/varumärken maskeras inte eftersom det skulle ändra innehållet. Två versioner av samma par ska om möjligt inte visas direkt efter varandra; deterministisk genomgång flyttar annars senare version till nästa lediga position. Nyckeln hålls av domaren.

Frågor besvaras i följande ordning utan krav på fri förklaring:

1. **Riktning för varje medlem:** ”Jämfört med sitt original, går framförandet i A′ snabbare/långsammare/ungefär lika/osäkert?” Samma för B′. Separat fråga med orden ”mer/mindre energi” så att mekaniskt snabbare inte automatiskt betyder mer energi.
2. **Ömsesidighet:** ”Har de två framförandena kommit närmare varandra, längre ifrån, är skillnaden oförändrad, eller går det inte att avgöra?” Bedöm tempo och energi var för sig. Samma enskilda klipp får inte bära båda medlemmarnas godkännande.
3. **Avsikt och särart kvar, per medlem:** ”Är detta fortfarande samma klipp med samma poäng/avsikt, vem/vad som händer och sitt eget uttryck kvar?” ja/nej/osäker. ”Kan du fortfarande tydligt skilja A:s uttryck från B:s?” ja/nej/osäker. Ingen norm används som facit.
4. **Sammanhang, per medlem:** ”Fungerar tal, pauser, rörelse, textens lästid och ljud tillsammans utan en störande skarv eller felaktig betoning?” ja/nej/osäker. Tillåt val av felkategori men kräv ingen motivering.
5. Först nu visas önskad riktning `mot` eller `från`, fortfarande utan metodnamn: ”Kan du godkänna första förslaget för detta uppdrag?” ja/nej. Registrera separat uppskattat antal nödvändiga rättelser 0/1/2/3+; detta är **bedömd rättelsebörda**, inte redan utförda rättelser.

**Faktisk rättelsebörda, primär för Lovable-påståendet:** efter att första domarna låsts får varje arm samma begränsade rättelsemöjlighet: ägaren väljer medlem samt (a) halvera tidsändringen, (b) vänd riktningen, (c) använd jämn tidsändring i stället, (d) återställ medlemmen. Varje val är en rättelse och utgår från armens aktuella recept; högst tre val per parfall. Ny version får inte förbättras manuellt mellan valen. Ägaren kan godkänna vid varje omgång. Återställd/fortfarande felriktad medlem klarar inte uppdraget även om originalet är snyggt. Ingen godkänd uppdragsenlig version inom tre val, avbrutet fall eller nej från policyn kodas som 4 (censurerad kostnad). Det betyder inte att fyra redigeringar faktiskt utfördes. Redovisa antal val, tid och andel färdiggodkända separat. Om denna loop inte genomförs får man bara säga ”lägre bedömd rättelsebörda”, inte ”krävde färre rättelser”.

**Sex förutbestämda kontrollfall, från R:** sortera R-id efter `SHA256(202611204|panelkontroll|id)`; välj de första fyra från olika konton. K1–K2: två originalpar visas åter som identiska originalpar (rätt svar: oförändrad riktning). K3–K4: de två första kontrollklippen visas vardera mot sin globala 1,25×-version med A2:s P-recept (rätt svar på tempo: snabbare; ingen förhandsdom om energi/avsikt). K5–K6: kontrollparen visas med båda utgångarna ersatta av samma ena medlem (rätt svar: den andra källans identitet/särart är inte bevarad). Dessa är kontroller, inte policyutfall. Saknas tydlighet i en kontroll får den inte ersättas efter panelen; markera kontrollbrist.

Lägg dessutom in blinddubletter av de två först hashordnade ordinarie fallen. För giltig panel krävs minst 5/6 korrekta kontroller, ingen miss av båda identitetskontrollerna och överensstämmelse om riktning/avsikt i båda dublettfallen. Annars blir panelen **otillförlitlig/ej avgörande**, inte automatiskt godkänd eller underkänd metod. En ny panelomgång ska redovisas separat; första svaren sparas. Tillåt ”osäker” utan att pressa fram svar.

Detta är inte ärligt ett tiominutersprov: full längd, 24 fall och rättelser kan behöva flera pass. Budgetera med de uppmätta spellängderna före inbjudan, behåll samma bedömningsförhållanden mellan passen och logga avbrott. Uppdragets cirka tio minuter är en äldre cykelbeskrivning, inte skäl att ersätta filmer med utvalda lyckade rutor (`motpart/runda-4/UPPDRAG.md:34`).

### B6. Fällningskriterier och rapportering

**Förslag — två separata domar, utan efterhandskomposit.** Alla sex par finns i nämnaren även vid nej, haveri, likvärdiga utgångspunkter eller saknad stödjande modell. Är material-/panelgrinden ogiltig blir provet ej avgörande; ett korrekt körbart nej räknas däremot som utebliven täckning.

1. **Riktningshypotesen för tempo:** minst 5/6 par ska i första förslaget klara **båda riktningarna**, med båda medlemmarna i avsett håll, rätt parrelation, avsikt/särart och sammanhang bevarade. Alla berörda ja krävs; osäker är inte ja. Färre än fem fäller denna pilots överförbarhet. **Energi får en egen likadan dom**; tempo godkänt och energi underkänt får aldrig sammanfattas som ”energi fungerar”.
2. **Ingen mush i denna snäva mening:** ägarens avsikt/särart och sammanhang måste passera samtidigt enligt ovan; synlig likhet med en bankgranne ger ingen dispens. En återkommande samma felkategori på minst två olika par ska rapporteras som ett systematiskt motexempel även om totalsiffran annars är bra.
3. **Extra beslutsförmåga:** summera den faktiska rättelsekostnaden över mot/från till en kostnad per par för P1 respektive C1. P1 ska ha strikt lägre kostnad i minst 4/6 par **och** minst 25 % lägre total kostnad över alla 12 riktningsfall, utan sämre antal godkända riktnings-/bevarandefall än C1. Vid C1-total 0 kan P1 inte visa strikt förbättring. Uppfylls inte detta: extra beslutsförmåga har inte visats, även om båda reglerna levererar snygga filmer. Om bara uppskattad rättelsebörda finns är denna dom uttryckligen oprövad.
4. **Determinism och budget:** varje render måste följa fryst recept, tidskarta och B4. Handändring, ny urvalsregel, extra val av rendering, saknad logg eller olika budgeter ogiltigförklarar jämförelsen. Ett semantiskt dåligt men reproducerbart recept passerar endast denna tekniska kontroll.

Redovisa samtliga par, båda riktningar och armar, bortfall, ursprunglig ägarrangordning, första dom, kontrollresultat och rättelsehistorik. Inga p-värden som gör 24 upprepningar till 24 oberoende par; sex par är en falsifieringspilot. Ingen slutsats om publikens respons eller förändrade trender utan senare separata data, vilket T3 också avgränsar (`motpart/runda-4/T3-codex/GRANSKNING.md:65,79`).

### B7. Vad T4 föreslår och vad ägaren måste sätta

**T4 föreslår och har nu specificerat:** urval, referensdelning, ingrepp, fält, trösklar, policy P1, jämförelseregel C1, lika budget, panelblindning och fällningsregler. Byggaren får omsätta detta i kod och testa mekaniken på R; ändrad policy eller tröskel kräver ny förregistrerad version före testinsyn.

**Ägaren måste sätta före den skarpa panelen:** (1) om uppdragets godkännande ska kräva upplevd energi eller om ett begränsat temporiktat förstaprov är relevant — båda utfallen registreras oavsett; (2) om föreslagna 10 % tidsändring och högst tre rättelser motsvarar en användbar första leverans; (3) vilka bevarandekrav som är absoluta, exempelvis poäng, all begriplig dialog, produkt och textens läsbarhet. Det kan göras genom att acceptera/ändra dessa få kontraktspunkter och eventuellt välja mellan referensexempel; ägaren ska inte behöva lista varje estetisk nyans eller märka testklippens pauser. Ändringar registreras innan ägaren sett testvarianterna. Hans svar kan inte fyllas i av T4.

Ägarens ord är stöd för målets riktning och beslutsavlastning, inte ett redan lämnat godkännande av våra numeriska toleranser (`motpart/runda-4/AGARENS_ORD_20NOV.md:3`). Tillförande generering lämnas utanför detta protokoll; dess öppna ägarbeslut kvarstår (`motpart/runda-4/UPPDRAG.md:16`).

## C. Insikt till orkestratorn — högst en sida

**Det kvarvarande huvudfelet är att ett styrbart tal fortfarande riskerar att bli definitionen av den önskade känslan.** I E28 är takt antal detekterade byten delat med längd, och i E30 är `tal_per_s` antal segment delat med längd (`video/format/e28-tek.mjs:34`; `video/format/e30_tal.py:25`). Förkorta samma film så ökar båda nästan av konstruktion. Om policyn sedan ”bevisar” att klippet rört sig genom att läsa samma kvoter igen har vi bara flyttat T1/T2:s geometriska cirkel till en tidsnämnare. Steg 3 behöver därför en oberoende upplevelsedom och en verklig kostnad för rättelser. Ett fungerande tempoverktyg kan ändå vara en dålig harness.

**Styrdokumenten motsäger fortfarande den rättade domen.** UPPDRAG säger alltjämt ”modellfritt = identitet, läsare = mening” och definierar ingen mush genom banknärhet plus särprägel (`motpart/runda-4/UPPDRAG.md:11–12`), trots att domen uttryckligen drog tillbaka just härledningen och mush-slutsatsen (`motpart/runda-4/DOM_T1_T2.md:45–48`). Även den gamla stegordningen står kvar (`UPPDRAG.md:18`). Läs senaste ändringen som styrande; gamla formuleringar får inte återkomma som verifierade krav. Sex nya kontopar ur en redan analyserad bank är inte heller historiskt orörda data, och en innehållsberoende policy är inte visad bättre bara för att den jämförs med en avsiktligt dum regel.

**[Härledning] Alla nuisance-ändringar är inte nuisance för alla mål.** Gain är irrelevant för replikinnehåll men direkt relevant för ljudstyrka; pauser kan bära både rytm och poäng. Full invarians mot allt kan därför ta bort det ägaren faktiskt vill kunna styra. Kräv ett kontrakt per axel: vad ska bevaras, vad ska följa med ändringen, och vad måste människan avgöra? Denna axel behöver ett styrbart åtgärdsutrymme med kopplingar, inte bara ett populationsavstånd. Ägaren efterfrågar just många relevanta beslut utan en lång korrigeringsdialog (`motpart/runda-4/AGARENS_ORD_20NOV.md:3`).

**Mitt nya billiga förslag: mät avståndet till ett mänskligt bästa val inom en liten, låst åtgärdsmeny.** På två **referenspar**, före testöppning, visa blint original samt samma fasta lokala/jämna ±10 %-retimingar som detta protokoll redan behöver. Låt ägaren välja bästa tillgängliga kandidat för mot och från, med ”ingen duger”. Jämför först därefter med policyns förhandsval; logga även dess näst bästa möjlighet, utan att göra det till nytt testfacit. Finns en godtagbar kandidat men policyn missar den är beslut/läsning flaskhalsen. Finns ingen vet vi att just menyn eller dess utförande inte räcker; mer ranggeometri hjälper inte det försöket. Om originalet vinner lär vi oss var ett ärligt nej bör ingå. Det isolerar **nåbart resultat från förmågan att välja det**, utan ny modell, omvärldsingest eller krav på att ägaren formulerar varför. Det är mitt förslag, inte ett redan genomfört prov eller ett bevis på att ingen annan åtgärd kan fungera. Ägarval som används för att ändra P1 skapar en ny låst version innan de sex testparen öppnas.

Viktigast: Låt oberoende bedömning av faktiska ändrade klipp och färre nödvändiga rättelser avgöra om harnessen fattar bättre beslut, aldrig de mått som samma policy just har optimerat.
