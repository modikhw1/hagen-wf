# Nytt klipp genom aktuell pipe: guacamole

Start: 2026-11-11, Codex. Uppdrag: välj ett obearbetat klipp med 4–8 scener, 1–2 personer och helst ett rum; använd nuvarande pipe mot samma intention som notan. Dokumentera också misslyckanden och antaganden.

## Underlag och val

- Lästa ingångar: `PIPE.md`, `ingest/README.md`, `kontrakt/README.md`, aktuell deklarationsöversättare och notans deklaration (nu version 0.6).
- Ingen `.git` finns i arbetsmappen. Befintliga resultat lämnas kvar; nya resultat får prefix `e-dialog-guacamole`.
- Källa: `C:/Users/praiseworthy/Downloads/letrend-bank/mexik.se/7640008436805045527.mp4`, kopierad till `scen/klipp/e-dialog-guacamole.mp4`.
- Bankens urval anger 9,98 sekunder och fyra scener. Alla fyra befintliga kontaktbilder granskade: kund i grå tröja (A), personal i grön tröja (B), samma bar. S1/S3 visar kunden, S2 personalen, S4 båda. Inga tidigare ingestresultat för klippet finns bland ingest-mapparna.
- Alternativet Beirut (7535079989411122454) hade bakgrundsgäster och mycket rekvisita. Mexik ger ett renare prov av motbilder och gemensamt rum, men disken döljer benen: golv och kroppslängd kommer vara osäkra.

## Avsedd väg

Original → befintlig flerklippsingest → granskad semantik → kropp/kamera/rum → deklaration med explicit antagna mått → plats → källa och plan → närvaro → render och oberoende kvalitetskontroll. Generativ breddning används bara om den behövs och hjälper; bakom disk avslöjar breddning inte benen.

Deklarationen är agentens arbetshypotes på användarens uppdrag, inte ägarens uttryckligt godkända mått. Inga sådana antaganden får beskrivas som uppmätta.

## Körlogg

1. Startat befintlig `ingest_flera.py --semantiskt --uppdrag guacamole-2026-11-11`. Detta gör först lokala, billiga steg och pausar före kropp om semantiken saknas. Exakta artefakter ligger under `ingest/ut/e-dialog-guacamole-tagningar/`.
2. Detekterat exakt fyra tagningar: S1 0–87, S2 88–138, S3 139–189, S4 190–298 (inklusive slutruta), 30 fps. Två berättelsepersoner. S2:2 är en förgrundsarm, uttryckligen utesluten från kroppsläsning. S4:1 är B och S4:2 är A.
3. `semantik_ingest.py <I>/semantik_klipp.json`: första anropet gav HTTP 503 (överbelastning), andra lyckades, 12 118 tokens. Den befintliga semantikanropsräknaren står nu på 10/10; den har inte nollställts eller kringgåtts. Modellen var `gemini-3.5-flash`.
4. Granskade kontaktbladen. Gemini kopplade felaktigt S2 och S4 till samma kamerauppställning. Originalsvaret och `semantik_gemini_original.json` är bevarade; S4 har separat K3 i den granskade filen. Identiteterna och armavvisningen stämmer. Kunden bedöms sitta, men någon stol syns inte.
5. Lokal Whisper (`systran-small`, befintlig modell) gav 37 ord. Alla fyra repliker fick stöd, men täckningen var 100/75/75/64 procent. Sista repliken och dess slut är osäkra; originalljudet ska bevaras. Detta är inte en verifierad exakt transkription.
6. Budgetförhandsgranskning: 88 + 51 + 51 + 218 = 408 personrutor, under befintliga uppdrags- och totalgränser. Kropp/MoGe körs via befintlig Modal-konfiguration; inga nycklar skrivs i denna logg.

## Små allmänna anpassningar under provet

Säkerhetskopior av berörda filer: `<I>/fore_anpassning/`.

- `deklaration_till_hand.py`: valfri `kameror.<S>.spar_id` och `huvudroll`, så deklarationen inte behöver anta spår 1 eller sista rollen i en tvåpersonstagning. Äldre deklarationer behåller sina standardvärden. `layout.status` hämtas från deklarationen i stället för att alltid påstå `agare`.
- `plats.py`: respekterar explicit huvudroll (stoppar om rollen inte finns). En explicit deklaration med rumsmall går före semantikens generella mallförslag. Deklarerat golv tillåter att även roller med skymd underkropp får ankare; detta är deklarerat stöd, inte uppmätt fotkontakt.
- Regressionsprov: notans aktuella deklaration gav exakt samma handdata och läslogg med den gamla och nya översättaren (`verifiering_deklaration.json`). Inga gamla ingestresultat har körts om.
- Även notans plats och platsmätlogg är identiska före/efter anpassningen, prövat med befintlig handrollsväg utan att skriva om resultat. Enhetstestet `ingest/test_deklaration.py` prövar explicit spår 2/roll A i en tvåpersonstagning och rätt sittande höftmått (OK).
- För detta klipp är all geometri i deklarationen märkt antagen eller sedd. Bardisken approximeras med befintlig bordsmall; U-formad retur och glasdekor är ännu inte rekonstruerade.

## Återkörbara kommandon

### Återupptagning och upptäckt exportfel

Alla fyra ingesttagningar blev klara, med 408 kroppsrutor totalt. Första `prepare` byggde hand, plats och källa men stoppade i full kompilering: `kvalitet.kropp.rader[1].darr_cm_per_ruta2` innehöll NaN för byggd/stabil/rå. S2 har 0 tillförlitliga rutor enligt befintlig regel: exakt 7/21 punkter (33,3 %) är i bild i varje ruta, under 35 %-gränsen. Detta är inte tom persondetektion; silhuettmåttet kan fortfarande mätas.

Rättning: `kroppmatt.jitter` returnerar `None` när ingen giltig tre-rutorssekvens finns. `kvalitet.py` visar då streck. Trösklar och rådata är oförändrade. 19 tester i `test_kroppmatt.py` passerar, inklusive nytt prov av saknat mått och giltig JSON. Säkerhetskopior finns i `fore_anpassning/`. Den första avbrutna mappen `tom/` behålls; ny kompilering går till `tom_v2/`. `plan_diagnos_nan.json` är ett felsökningsunderlag med icke-standardiserade NaN-värden, inte en konsumtionsklar plan.

Från reporoten med `PYTHONIOENCODING=utf-8`. Ett tungt steg åt gången.

```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/ingest/flera/ingest_flera.py scen/klipp/e-dialog-guacamole.mp4 scen/3d/ingest/ut/e-dialog-guacamole-tagningar --semantiskt --uppdrag guacamole-2026-11-11
scen/.venv/Scripts/python.exe scen/3d/guacamole_kor.py prepare
scen/.venv/Scripts/python.exe scen/3d/guacamole_kor.py render
scen/.venv/Scripts/python.exe scen/3d/guacamole_kor.py edit
```

`prepare` och `edit` vägrar skriva över befintligt källmanifest/respektive resultatmapp. För iteration: välj nya mappar eller kör de enskilda pipelinekommandona med nya utfilnamn. `render` är en diagnostisk rendering med befintliga kvalitetsflaggor kvar; flaggan betyder inte godkänd kvalitet. Inga nya modelljobb görs av detta hjälpskript. Första kommandot är däremot ingest och kan beställa modelljobb om dess cache saknas/har blivit ogiltig.

## Första fulla resultatet och visuell granskning

`tom_v2/plan.json` kompilerades med full diagnostik (83,3 s). `narvaro/` fick tre lånade roller: B i s1/s3 från s2, A i s2 från s3. Dessa är kamerabärare och visas inte i sina respektive motbilder. S4 har båda egna kroppsläsningarna. `narvaro/film.mp4` och `scen.blend` byggdes (110,17 s för Blender och mux). Originalets 299 rutor, fyra scener och originalljud (9,9667 s) behålls; inga repliker syntetiserades, noll klippta ljudsamplingar.

Visuellt granskat f0030, f0100 och f0230. **Första filmen underkänns visuellt:** s1 visar kundens kropp/gest men ingen disk; s2 och s4 är blockerade av mallvägg. Kroppsmåtten upptäcker inte den sista skymningen eftersom de mäter kroppens projektion mot mask, inte slutrenderns synlighet.

### Problem som det nya klippet blottlägger

1. **Deklarationen överlever inte hela kompilatorn.** `golvmatning.for_plan` löser om golvet även när platsen har en deklaration; `tropassning`/`trostod.sitt_hojd` begränsar barstolens deklarerade 0,75 m till vanlig stol-prior 0,43–0,48 m. Planen får 0,455 m. Kamerorna hamnar 1,092–1,450 m över golv trots deklarerade 1,40 m. Detta är inte en lyckad bevaring av rumsbriefen.
2. **Gemensamt rum driver i tvåpersonsbild.** A:s stöd ligger runt x=0 i s1/s3 men x=-1,169 m i s4. Huvudrollen B registreras, den andra kroppen följer den bildbaserade läsningen och hamnar på annan plats. Ett enda huvudpersonsankare räcker inte för att lösa båda rollerna. Kropparna har inte flyttats godtyckligt för att dölja problemet.
3. **Diskens antagna läge stämmer inte med bilderna.** Skymningskontrollen tar bort bardisken i alla fyra scener (före åtgärd 66,8/5,8/21,0/11,2 procent). Gränsen är oförändrad. Därför saknas en central rumsdel i filmen.
4. **Mallväggar blockerar motbilder.** Rumsmallen byggs kring personplatserna, inte kameraområdena. De två genererade väggarna saknar källmätning. En ny öppen granskningsvariant utelämnar dem, med förklaring i `plats_oppet/plats.json`; första resultatet är kvar.
5. **S2:s låga tillförlitlighet och S4:s kantperson.** S2 har 0/51 bedömbara poser enligt befintlig gräns. S4 A har synlig silhuett-IoU 0,55 (rå estimator 0,54). S4 B har darr 1,55 cm/ruta², strax över granskningsgränsen 1,5. Övriga synliga silhuett-IoU: A s1 0,68, B s2 0,69, A s3 0,68, B s4 0,75. Alla scener får `granska`, ingen är kvalitetsgodkänd.

### Öppen variant

Källbyggaren kördes på nytt med `--plats <I>/plats_oppet/plats.json`, utfil `kalla_oppet.json`. Kompilering: `kor_klipp.py ... --kalla kalla_oppet.json --undermapp oppet_data_v2 --hoppa-render`. Den tomma `oppet_data/` kom från ett för tidigt startat kommando innan källbyggaren var klar; inget resultat där används. Närvaro skrivs separat till `oppet/plan.json`, sedan `guacamole_kor.py render-open`. `edit` använder samma öppna källa och gör närbild på B i s4. Ingen ny ingest eller modellkostnad i dessa iterationer.

Öppen variant: full kompilering 12,2 s med återanvända mätcache, Blender 107,29 s. f0100 visar nu B i motbilden; f0230 visar båda kropparna och B:s framåtlutning. S4:s jämförelseblad visar god igenkännbar gest/timing men saknad disk, felaktig rumsplacering och påhittade synliga underkroppar.

**Ytterligare visuell brist:** textsteget lägger flera långa S4-texter över varandra och utanför bild. `oppet/film.mp4` behålls som evidens för pipelineutfallet. `oppet/film_utan_text.mp4` är samma kropp/kamera/ljud utan det felaktiga textlagret. Den huvudsakliga granskningsfilmen `jamforelse.mp4` visar original (vänster) och denna rena rendering (höger). Verifierad med ffprobe: 720×640, 299 bildrutor, 9,966667 s och ljudspår. Den rena filmens avsaknad av text är inte en lyckad rekonstruktion av originalets undertexter.

Närbildsprovet `redigerad/regi.json`: befintlig operation `renderkamera`, s4, stativ mot B:s huvud, inramning `nara`, 40 grader. Kompilatorn har tillämpat operationen och har tom `ej_tillampat`. Samma 299 källrutor; inga nya kroppsanrop. Full plan före närvaro sparas för granskning av kameraändringen.

## Deklarationen blir bindande genom kompilatorn (11 nov kväll)

Åtgärd av problem 1 ovan. Inga modelljobb, ingen rendering; kompileringen använde de befintliga mätfilerna (kropp, MoGe, kamera) och byggde bara om de lokala beräkningscacharna (golv2, höjdpassning, kvalitet), som nycklas på koden.

**Var värdena tappades.** (1) `kontrakt/golvmatning.py` `for_plan` (rad 358 före ändring) körde `platsbeslut(undersok(...))` även för en deklarerad plats. `platsbeslut` flyttade varje tagnings registrering med cue-golvet (`reg[...]['M'][2,3] -= value`): +0,308/−0,050/+0,307/+0,281 m för S1–S4, som ändrade både golv och kamerahöjd (kamerahöjden var 1,092–1,450 m). Det vinnande cuet var kamera-priorn 1,45 m eller sitsprioren (0,455 m), aldrig en mätt fot. (2) `kontrakt/tropassning.py` rad 35 och `kontrakt/trostod.py` `sitt_hojd` (rad 28–34) klämde sitthöjden mot `SATE_INTERVALL_M` 0,43–0,48 m. (3) Deklarationen fanns inte i `plats.json`: bara filnamn och version (`deklaration`), så kompilatorn kunde inte veta vad som var deklarerat och vad som var mallens standardvärde.

**Ändrat.** `ingest/deklaration_till_hand.py` skriver `hand.deklarerat` (golv, sitthöjd per sittplats, kamerahöjd per tagning; tal eller `[min, max]`, intervall ger sin mitt som startvärde för lutning och mall). `ingest/plats.py` för det till `plats.json`. `kontrakt/golvmatning.py` `platsbeslut(bunden_golv_m)`: ingen höjdkoppling mellan stationer, golvet är platsens deklarerade, cue-beslutet loggas (`fri_varde_m`, `avvikelse_fri_mot_deklarerad_m`, `konflikt_med_deklaration`). `kontrakt/trostod.py` `sitt_hojd(deklarerat)` och `tropassning.py`: deklarerad sitthöjd ersätter prioren. Nytt `kontrakt/deklarationskontroll.py` anropad från `kompilera.py`: `plan.kvalitet.deklaration` med en post per deklarerat värde, `avvikelser` och `matkonflikter`; avvikelse över 1 cm blir en varning i `plan.varningar`. Två nya tester i `test_rumsmall.py`. Rumsmallarna `dekl_*.json` är byte-identiska (sha256 före/efter).

**Före/efter, guacamole** (`kontrakt/ut/e-dialog-guacamole/bindande/`, före: `fore_dekl_bindande/guacamole_omkord_fore/`, samma kod före ändringen; den sparade `tom_v2/plan.json` skiljer sig från den bara i filsignaturer).

| | före | efter | deklarerat |
|---|---|---|---|
| golv (flytt per tagning S1/S2/S3/S4, m) | +0,308 / −0,050 / +0,307 / +0,281 | 0 / 0 / 0 / 0 | 0 (platsramens golv) |
| sitthöjd stol_A (m) | 0,455 | 0,750 | 0,75 |
| bäcken över sits (m), kroppsläsning önskad sitthöjd | 0,085, 0,455 | 0,092, 0,757 (läsrest 7 mm) | |
| kamerahöjd s1 / s2 / s3 / s4 (m) | 1,092 / 1,450 / 1,093 / 1,119 | 1,400 / 1,400 / 1,400 / 1,400 | 1,40 |
| `kvalitet.deklaration` | finns inte | status bunden, 0 avvikelser, 6 poster | |

Mätkonflikter som nu redovisas men inte får styra: det fria GOLV2-beslutet hade lagt golvet 0,31/0,31/0,28 m högre i S1/S3/S4 (familj: sits, alltså sitsprioren 0,455 m mot deklarerade 0,75 m). Det är samma konflikt som problem 1 beskrev, nu synlig i diagnostiken i stället för tyst. Bildtrohetens flaggor per person är oförändrade (endast S2 B flaggad). Följdändringar i kvalitetsrapporten: skymningskontrollens bardisk-andel i S1/S3/S4 sjunker från 66,8/21,0/11,2 till 0,2/3,2/0,0 % och disken utelämnas inte längre där (S2 går åt andra hållet, 5,8 → 11,9 %, och disken utelämnas kvar där). Det ändrar inte problem 3 som sådant, men en del av den skymningen kom av att kropparna låg 0,3 m för högt mot disken. S4 B darr 1,55 → 1,57 cm/ruta² (gräns 1,5, flaggad båda gångerna). Gränsvärden är orörda.

**Notan** (`notan_berattat/bindande/`, baslinje `fore_dekl_bindande/notan_omkord_fore/`). Notans `plats.json` byggdes inte om med `plats.py` (en omkörning med dagens kod ger andra cue-beslut än filen som kalla.json byggdes på); `plats_bindande/plats.json` är den befintliga plus `deklarerat`-blocket, vilket är allt `plats.py` nu lägger till. `kalla_bygg.py` återger den befintliga kalla.json utan en enda skillnad. Skillnader mot baslinjen, alla väntade (deklarationen vinner): kamerahöjd s1/s2/s3/s5/s6 1,184–1,191 → 1,200, s4 1,141 → 1,270, s7 1,450 → 1,200 (deklarerade värden); stolarna 0,455 → 0,450 (deklarerat 0,45, bort från prioren); stolsdelarna 2,5–5 mm lägre därefter. Golvet är deklarerat och kamerorna följer det (registreringens z ändras 0,009–0,016 m, S4 +0,129 m, S7 −0,250 m). En följd att granska: C:s benlängd i S4 blev 8,7 % längre (faktor 0,92 från `dolda_fotter` används inte längre, eftersom golvet inte längre sätts av en mätt fot). Mätkonflikt: fötterna i S4 hade lagt golvet 0,129 m högre än deklarerade kameran 1,27 m, och kamera-priorn S7 0,25 m lägre än deklarerade 1,20 m. Ingen regression i bildtrohetens flaggor (endast S6 A flaggad, som före).

**Gamla vägen** (`kalla_jamn_golv.json`, platsen `plats/plats.json` utan `deklarerat`): planen före och efter är identisk, 0 skillnader (`fore_dekl_bindande/gamla_vagen_fore` mot `gamla_vagen_efter`).

**Ej löst.** Äldre `plats.json` (utan `deklarerat`) och de kalla.json som pekar på dem får fortfarande det gamla beteendet tills platsen byggs om. Problem 2–5 är orörda. Bordshöjder (bardisken 1,05 m) rörs aldrig av kompilatorn eftersom disken saknar `folj_ankare`, men `BORD_INTERVALL_M` 0,72–0,76 m i `tropassning.py` skulle kläma ett deklarerat följbord; där finns samma tapp som för sitthöjden. Narvaro (`narvaro.py`) är inte kontrollerad mot deklarationen.

**Tester efter ändringen** (loggar i `kontrakt/ut/fore_dekl_bindande/test_efter/`). Gröna: `ingest/test_deklaration.py`, `ingest/test_rum.py`, `kontrakt/test_rumsmall.py` (inklusive två nya prov för bindande sitthöjd och deklarationskontrollen), `test_steg11`, `test_regler`, `test_kroppmatt`, `test_props`, `test_handelser`, `test_text_disk`, och 26 av `test_flode` (Flode, BarOforandrad, Notan, första Plats-proven). Röda eller ofullständiga: `test_snabb.test_planbeslut_cache_ogiltig_vid_geometri_och_matfil` (KeyError `dolda_fotter` i `kvalitet.planbeslut`) – felar identiskt med de ursprungliga filerna återställda, alltså redan trasig före ändringen. `test_flode.Plats.test_bar_identitet_ger_samma_plan` hann inte klart (900 s tak, och ett tidigare påbörjat prov av samma test hade då gått över 50 minuter processortid), så det och de Plats-prov som följer det i filen är inte körda till slut. `test_plats_snapshot.py` är ett hjälpskript med argument, inte ett prov. Gamla vägen är i stället verifierad direkt: planen för `kalla_jamn_golv.json` är identisk före och efter.

## Flera roller i samma tagning: kameran passas mot alla (11 nov natt)

Åtgärd av problem 2. Inga modelljobb, ingen rendering; bara lokala steg på befintliga mätfiler. Baslinje (kod och planer före): `kontrakt/ut/fore_flerroll/`. Nya resultat: `kontrakt/ut/e-dialog-guacamole/kalla_flerroll.json` och `flerroll/`, `ingest/ut/e-dialog-guacamole-tagningar/plats_flerroll/` (jämförelsen med gammal kod: `plats_fore_flerroll/`), `kontrakt/ut/notan_berattat/flerroll/`, `kontrakt/ut/notan/gamla_flerroll/`.

**Var den andra rollen tappades.** `ingest/plats.py`, `landmark()` (i grammatikgrenen, tidigare ca rad 444–449): yaw = rollens deklarerade blick minus huvudpersonens lästa torsoriktning, och translationen sätter *huvudpersonens* bäcken på `person_pos_m`. Det är ett enda ankare. Varje annan kropp i tagningen följer sedan samma transform och landar där läsningen lägger den. I S4 är huvudrollen B, så B hamnade exakt på (0; 1,3) och A på (−1,167; 0,017), alltså 1,167 m från sin plats (0; 0). Torsoriktningen var dessutom fel för B: B:s torso läses 42° vid sidan av riktningen mot A, medan A:s torso pekar 4° från riktningen mot B. Mätkedjan i `kontrakt/` har ingen egen placering av kroppar. Den läser samma `till_plats` per scen. Ankaret `stol_A` (medel av A:s lägen över S1/S3/S4) drogs dessutom till x = −0,51 m av S4, och rumsmallen passades mot det (yaw −17,6°, translation 0,45 m).

**Ändring.**
- `ingest/deklaration_till_hand.py`: `hand[tagning].flera_roller` ({roll: plats, pos_m, blick_grader}) när minst två deklarerade roller har plats i tagningen och tagningen inte bryter rummet. Annars inget fält (notans `hand.json` byte-identisk, guacamole får fältet bara i S4).
- `ingest/plats.py`: `passa_roller()` (2D-passning yaw + translation, skala 1,0, lika vikt per roll; z, golv och kamerahöjd orörda, alltså fortsatt bindande) och `flera_roller()` i grammatikgrenen. Kräver två lästa roller med känd plats och riktning, annars faller den tillbaka på den gamla huvudrollsvägen. Restfel, blickrest och avståndsfel skrivs i `reg[...]['roller_registrering']` och `plats.json` `tagningar[].kvalitet`. Inga kroppar flyttas individuellt.
- `kontrakt/kalla_plats.py` och `kalla.schema.json`: valfritt fält `roller_registrering` i `matning.platser[].registreringar` (bara när det finns).
- `kontrakt/deklarationskontroll.py` och `kompilera.py`: `plan.kvalitet.deklaration.registrering` (restfel per roll och tagning, `over_troskel`), varning över `REGISTRERING_VARNING_M` = 15 cm. Tröskeln är en tredjedel av en stolsbredd (0,48 m) och strax över läsbruset: bäckenet spretar 2–12 cm inom en tagning och golvcuernas spann är 7–17 cm. Mindre än så kan en stel kamera inte skilja från brus. Gränsvärdena i kvalitets- och skymningskontrollerna är orörda.
- Nya prov: `ingest/test_deklaration.py` (fältet skrivs bara vid två roller, inte vid bryter_rummet; `passa_roller` exakt och med delat fel) och `kontrakt/test_rumsmall.py` (redovisning och varning).

**Före/efter, guacamole.** Läge = kroppens bäcken i platsramen, restfel mot deklarerad plats. S1–S3 har en synlig roll: oförändrade, `till_plats` lika på 1e-12.

| scen | roll | deklarerad (x; y) | före: läge | före: rest | efter: läge | efter: rest | blick efter mot deklarerad |
|---|---|---|---|---|---|---|---|
| s1 | A | 0; 0 | 0; 0 | 0 | 0; 0 | 0 | |
| s2 | B | 0; 1,3 | 0; 1,3 | 0 | 0; 1,3 | 0 | |
| s3 | A | 0; 0 | 0; 0 | 0 | 0; 0 | 0 | |
| s4 | A | 0; 0 | −1,167; 0,017 | 1,167 m | 0; −0,217 | 0,217 m | −4° |
| s4 | B | 0; 1,3 | 0; 1,3 | 0 | 0; 1,517 | 0,217 m | +42° |

S4:s kamera: plats (2,16; 0,34) → (2,24; 2,26), yaw 74° → 117°, höjd 1,40 (bunden, 0 avvikelser i `kvalitet.deklaration`). Båda rollerna ligger över tröskeln 15 cm och ger två varningar i planen. Restfelet minskar alltså för A (1,17 → 0,22 m) men B får 0,22 m i stället för 0.

**Läsningen säger något om deklarationen.** Restfelet går inte att kamera bort. Läst avstånd A–B i S4 är 1,734 m mot deklarerade 1,300 m (felet 0,434 m, delat lika). Den stela passningen lägger A:s torso på 86° mot deklarerade 90° (A tittar på B), medan B:s torso hamnar på −48° mot deklarerade −90° (B:s överkropp är vriden 42° vid sidan av A; troligen mot kassan eller kunden vid sidan). S2 ger en delvis självständig indikation: om kameran står vid A:s huvud ligger B:s huvud 1,59 m bort horisontellt (S2:s lästa huvudavstånd). Underlag för att rätta deklarationen (ägaren godkänner, deklarationen är orörd): `staplats_B` borde ligga ungefär 1,6–1,7 m från `stol_A`, inte 1,3 m, vilket stämmer med en bardisk som är djupare än de antagna 0,65 m (disken står i deklarationen med djup 0,65 m och mitt 0,65 m, alltså A 0,33 m från framkanten och B 0,33 m från bakkanten). Detta är en läsning av monokulär djupuppskattning, inte ett mått.

**Följdeffekter att känna till (rörs inte).** (1) Rumsmallen passas mot de lästa ankarna och ligger nu 0,05 m och 4° från deklarerat läge i stället för 0,45 m och 17,6° (ankar-RMS 0,066 → 0,133 m, eftersom ankaren nu bär S4:s avstånd 1,73 m). (2) Skymningskontrollen utelämnar nu bardisken även i s1 (före: s2 och s3), med oförändrade gränser: delen flyttade ca 0,26 m och vreds 22°. Det är problem 3 (diskens antagna läge) som blir synligt på ett annat ställe, inte ett nytt fel. (3) Bildtrohetens flaggor är oförändrade; måtten ändras högst 0,002 (bbox-IoU, kropps-IoU) eller inget alls.

**Notan och gamla vägen.** `plats.py` med ny och gammal kod ger byte-identisk `plats.json`, `plats_matt.json` och `plats.md` för notan (deklarerad väg, `plats_flerroll` mot `plats_fore_flerroll`) och för gamla vägen (`plats/hand.json`, `plats_gamla_flerroll` mot `plats_gamla_fore_flerroll`). Ingen tagning i notan har två deklarerade roller i samma tagning, så `flera_roller` skrivs aldrig där. Planerna (`kalla_bindande.json` och `kalla_jamn_golv.json`, ny kompilering) är byte-identiska med baslinjen: 0 skillnader. Notans `plats.json` byggdes inte om för kalla (en omkörning med dagens kod ger andra cue-beslut än den kalla.json byggdes på, se ovan); `plats_bindande` är orörd.

**Ej löst.** Deklarationens avstånd A–B (ägaren). B:s torsoriktning i S4 används inte till att styra yaw (positionerna gör det); blickresten redovisas bara. Tre eller fler roller i en tagning är kodade (minsta kvadrat) men ej prövade på riktig data, och `laspar_avstand_m` redovisas då som null. `test_snabb.test_planbeslut_cache_ogiltig_vid_geometri_och_matfil` är röd som förut (`KeyError: 'dolda_fotter'`). Plats-proven i `test_flode.py` är inte körda (de gamla gick redan).

**Tester efter ändringen** (loggar i `kontrakt/ut/fore_flerroll/test/`). Gröna: `ingest/test_deklaration.py` (3, varav 2 nya), `ingest/test_rum.py`, `kontrakt/test_rumsmall.py` (26, varav 1 nytt), `test_steg11`, `test_regler`, `test_kroppmatt`, `test_props`, `test_handelser`, `test_text_disk`, och `test_flode` utom Plats-klassen (`BarOforandrad`, `Flode`, `Notan`). Röd som förut: `test_snabb.test_planbeslut_cache_ogiltig_vid_geometri_och_matfil` (`KeyError: 'dolda_fotter'`).

## Läst avstånd tillbaka till deklarationen och disken som intervall (11 nov natt)

Åtgärd av problem 3 och av den öppna punkten "Deklarationens avstånd A–B" ovan. Inga modelljobb, ingen rendering, ingen ny mätning: bara lokala steg på befintliga mätfiler, mätcachen orörd (bara de lokala beräkningscacharna byggdes om). Baslinje (kod, deklarationer, planer före): `kontrakt/ut/fore_mobelintervall/`. Nya resultat: `ingest/ut/e-dialog-guacamole-tagningar/plats_mobelintervall/`, `kontrakt/ut/e-dialog-guacamole/kalla_mobelintervall.json` och `mobelintervall/` (plan), `kontrakt/ut/notan_berattat/mobelintervall/`, `kontrakt/ut/notan/gamla_mobelintervall/`.

### A. A–B-avståndet fört tillbaka (deklaration 0.7)

`plats/deklaration.json` är nu `deklaration/0.7`; föregående version ligger bredvid som `plats/deklaration_0.6.json`. `staplats_B.pos_m` y 1,30 → **1,73 m**, märkt `last`, med källa: S4:s läsning (flerrollsregistreringens `laspar_avstand_m` 1,734 m) och S2, som ger 1,60 m (kameran över A:s bäcken) till 1,85 m (vid A:s huvud, 0,25 m framåt). Osäkerheten står som `pos_intervall_m: {"y": [1.6, 1.85]}`. Formatet har inget intervall för platsers `pos_m` (det är inte ett av de bindande värdena), så intervallet är en anteckning som översättaren inte läser. Det är en läsning av monokulärt djup, inte ett mått. Nytt i 0.7 är också `status_nycklar` (guacamole hade ingen) och `intervall` som status för möbler.

Restfel per roll i S4 (kameran passad mot båda rollernas platser, `plats.json` `tagningar[].kvalitet.roller_registrering`):

| roll | före (1,30 m) | efter (1,73 m) | tröskel 15 cm |
|---|---|---|---|
| A | 21,7 cm | 0,2 cm | över, sedan inom |
| B | 21,7 cm | 0,2 cm | över, sedan inom |

Avståndsfelet mellan rollerna går från 43,4 cm till 0,4 cm, rumsmallens ankar-RMS från 0,133 m till 0,050 m och yaw från 4,4° till 3,3°. De två registreringsvarningarna i planen är borta (kvar är bildtrohetsvarningen), `kvalitet.deklaration` är `bunden` med 0 avvikelser. Blickresten är oförändrad (A −4,3°, B +42,3°): B:s överkropp är vriden åt sidan, och inget avstånd rättar det. Följd som inte rättats: mallens golv och väggar byggs kring platserna (xy-spannet plus 1,2 m), så bakväggen flyttades från y = 2,50 till 2,90 m. Det är problem 4 (mallväggar) och rörs inte.

### B. Disken (och bord) som deklarerat intervall

**Var läget kom ifrån (kartläggning).** Mallen `dekl_<klipp>` genereras av `ingest/deklaration_till_hand.py` `rumsmall()` ur deklarationens `bord`-plats: `mitt_m` ger x och y, `storlek_m.langs_x/langs_y/hojd` ger bredd, djup och höjd. `plats.py` passar mallen rigid mot rollernas ankare (yaw + translation, skala 1,0) och för över den som `plats.json` `rumsmall`. `ingest/rumsmall.py` `byggobjekt()` bygger en `bord`-del som en 4,5 cm tjock skiva i höjden `hojd` på fyra smala ben i hörnen, alltså inte en solid disk. `kontrakt/kvalitet.py` `_planbeslut_utan_cache` kör `skymning.los()`, som per scen och möbelgrupp (id före första kolon) tar bort gruppen om minst 2 % av maskproven eller över 10 % av en kroppsdel skyms av en låda 5 cm framför kroppens djup, och då utelämnar gruppen i just den scenen. Inget i kedjan lät disken eller notans bord röra sig: bordshöjden kunde bara sänkas av en synlig handled (`vilande_handled`), och bord med `folj_ankare` klämdes i `tropassning.py` mot `BORD_INTERVALL_M` 0,72–0,76 m.

**Ny mekanism.** Deklarationen (0.7) får ange `storlek_m.hojd/langs_x/langs_y` och `mitt_m` för bord och diskar som tal (hårt) eller `[min, max]`. Översättaren för dem som `deklarerat.mobler` (plats.py för det oförändrat till `plats.json`, rumsmallen får intervallets mitt). Nya `kontrakt/mobelintervall.py` `losa()` körs före `skymning.los()`: finns ett fritt intervall och minst en scen är flaggad vid utgångsvärdet, provas ett rutnät över intervallen (högst 125 kombinationer, utgångsvärdet alltid med) mot skymningskontrollens egen räkning (samma rutor, samma flaggregel; `skymning.py` är orörd, så dess cache är intakt). Värdet med minst (antal flaggade scener, summa skymningsandel) väljs, vid lika det närmast utgångsvärdet. Ett värde per möbel för hela klippet. Är ingen scen flaggad rörs möbeln inte. Löser inget värde alla scener väljs det bästa och `los()` utelämnar möbeln i de scener som ändå är flaggade, som förut. Redovisning: `plan.kvalitet.mobelintervall` (valt värde, utgångsvärde, intervall, gräns nådd, skymning per scen före och efter). Planens kopia av rumsmallen (`plan.plats[].rumsmall.delar`) får det valda måttet. `tropassning.bord_hojd()`: en deklarerad bordshöjd (tal eller intervall) har företräde framför `BORD_INTERVALL_M`; prioren gäller bara utan deklaration.

**Intervall som deklarerats.** Guacamole, `bardisk`: höjd 0,95–1,15 m, djup 0,50–0,80 m, mittpunkt 0,50–0,80 m från stol_A (alla antagna, mitten = tidigare värde; längden 2,8 m hård). Notan, `bord_1`: höjd 0,66–0,74 m (mitten 0,70 = version 0.6:s lästa värde; deklaration 0.7, 0.6 bredvid som `deklaration_0.6.json`). `bord_2` är ett hårt tal (0,74 m).

**Guacamole, skymning för disken per scen.** "Flerroll" är planen som den var före detta arbete. "A ensam" är nya deklarationen med disken som tal, alltså lösarens utgångsvärde.

| scen | flerroll (före) | A ensam | efter lösaren | disk i planen, före och efter |
|---|---|---|---|---|
| s1 | 0,64 % flaggad (höft 26 % av delens prov) | 0,81 % flaggad | 0,0 % | struken, sedan med |
| s2 | 17,7 % flaggad | 0,0 % | 0,0 % | struken, sedan med |
| s3 | 3,5 % flaggad | 3,5 % flaggad | 0,0 % | struken, sedan med |
| s4 | 0,0 % | 0,0 % | 0,0 % | med, med |

Valt: höjd 1,00 m (utgångsvärde 1,05), djup 0,65 m (oförändrat), mittpunkt 0,725 m (utgångsvärde 0,65; framkanten 0,40 m från stol_A). Ingen gräns nåddes. Disken finns med i s1–s4 och skymningskontrollens `atgarder` är tom. Att s2 inte längre är en konflikt beror på A-ändringen (B står nu 0,43 m längre från disken); s1 och s3 löses av lösaren.

**Vad bilderna säger om disken** (rutnät över 243 värden, större spann än deklarerat, mätt med samma kontroll; underlag, inget påstående om hur baren ser ut). Vid djup och mittpunkt 0,65 m: skivans överkant 0,70–0,95 m ger ingen flaggad scen, 1,00 m flaggar s3 (0,3 %), 1,05 m flaggar s1 och s3 (0,8 och 3,5 %), 1,10 m flaggar alla fyra (7,5, 3,3, 15,3 och 1,0 %) och 1,15 m alla fyra (21, 11, 30 och 4 %). Kroppsmasken visar alltså A:s och B:s bäcken över skivan: antingen är skivans överkant högst ca 1,0 m, eller så står framkanten längre från A än antaget, eller så är kamerahöjden (1,40 m, antagen) eller sitthöjden (0,75 m, antagen) fel. En bardisk på 1,05–1,10 m är rimlig i verkligheten, så de antagna höjderna är lika misstänkta som disken. Inget av detta är åtgärdat.

**Notan** (`notan_berattat/mobelintervall/` mot baslinjen `fore_mobelintervall/planer/notan_bindande/`; `plats_mobelintervall/plats.json` är `plats_bindande/plats.json` plus `deklarerat.mobler` och versionen 0.7, eftersom en omkörning med dagens kod ger andra cue-beslut än de kalla.json byggdes på). Baslinjen hade inte bordet kvar i alla sju tagningar: `bord_1` utelämnades i s3 (höft 24 % av delens prov, totalandel 0,42 %). Lösaren väljer `bord_1` 0,66 m (gränsen nådd, utgångsvärde 0,70) och bordet står nu kvar i alla sju: s3 0,42 % till 0,0 %, s1 0,53 % till 0,06 %, övriga oförändrade. Skillnader mot baslinjens plan, alla väntade: `bord_1` är en post per del med synlig_ut 0–383 i stället för två, lägre skiva och ben, `kvalitet.mobelintervall`, skymningsdiagnostiken, `plats[].deklarerat.mobler`, kalla-sökvägar och hashar. Inget annat. Gränsen nåddes, så det bästa värdet kan ligga lägre än 0,66 m; intervallet får utvidgas av ägaren.

**Gamla vägen** (`kalla_jamn_golv.json`) och planer utan `mobler`: byte-identiska före och efter (0 skillnader, `notan/gamla_mobelintervall` mot `fore_mobelintervall/planer/gamla_vagen`). Guacamole-planen före mot den sparade: 0 skillnader (koden orörd vid baslinjen).

**Prov.** `test_rumsmall.Mobelintervall` (6): lösaren sänker och redovisar, gräns nådd och olöslig konflikt, tal och oflaggad möbel rörs inte, benen följer nya mått, förskjutning vrids in i platsens ram, deklarerad bordshöjd före prioren. `ingest/test_deklaration` (2 nya): `mobler` och mallens mitt, handleden sänker bara intervallets tak. Loggar: `kontrakt/ut/fore_mobelintervall/test/`.

**Ej löst och upptäckt.** Lösaren väljer bara bland rutnätets värden (7/5/4/3 per parameter beroende på antal fria parametrar). Möbeln är en skiva på ben, så en solid disk som skymmer kroppen under skivan prövas inte. Kamera- och sitthöjden är antagna och kan lika gärna vara orsaken till att en 1,05 m hög skiva skymmer A. Bildtrohetsflaggorna är orörda. Problem 4–5 (mallväggar, text) är inte åtgärdade; bakväggen i guacamole flyttades med B, se ovan. `test_snabb.test_planbeslut_cache_ogiltig_vid_geometri_och_matfil` är röd som förut (`KeyError: 'dolda_fotter'`). `test_flode.Plats` är inte körd.

## Väggar som inte kan blockera (12 nov)

Åtgärd av problem 4. Inga modelljobb. Baslinje: `kontrakt/ut/fore_vaggar/` (`kod/` kodkopior, `omkord_ratt_skymning/fore/` planer med färsk cache före ändringen, `omkord_ratt_skymning/efter/` efter, `test/` loggar). Nya resultat: `ingest/ut/e-dialog-guacamole-tagningar/plats_vaggar/`, `kontrakt/ut/e-dialog-guacamole/kalla_vaggar.json`, `vaggar_data/` (plan), `vaggar_narvaro/` (plan med närvaro, `film.mp4`, `film_utan_text.mp4`, `jamforelse.mp4`, `stillbilder/`).

**Hur väggarna blev till.** `ingest/deklaration_till_hand.py` `rumsmall()` lägger golv och två väggar 2,0 m bortom lägsta och 1,2 m bortom högsta PLATS (bara platsernas mittpunkter, varken kameror eller möbelmått). Kamerorna finns först efter registreringen (plats.py) och i planen. Därför ligger sidoväggen vid x=1,22 medan S4:s kamera står vid x=2,24, och disken (2,8 m lång) går genom sidoväggen.

**Lösning.** Två steg. Mallen byggs som förut (byte-identisk, sha256 oförändrad). `kontrakt/vaggar.py` `kor()` anropas sist bland byggbesluten i `kompilera.py`: de GENERERADE väggarna och golvet vidgas utåt i rummets egna axlar till att rymma renderkamerans alla lägen +0,5 m, alla möbler +0,1 m och alla rollankare +0,3 m (antagna marginaler). Rymmer rummet redan allt rörs inget. Väggar som deklarationen anger uttryckligen (`vaggar.bak.y_m`, `vaggar.sida.x_m`, översätts till `deklarerat.vaggar`) är hårda: de flyttas inte, och då redovisas konflikt och varning. Kontrollen (`kontrollera`) mäter slutplanens geometri: per scen och provruta, ligger kameran utanför golvet/innanför en vägg eller i en vägg, och skär sträckan kamera till rollens ankare (höjderna 0,4/1,0/1,6 m) en vägg. Utfall i `plan.kvalitet.rumsvaggar` (vägg: `status` antagen eller deklarerad, `kallmatning`, läge före/efter) och som varning. Bara platser med `deklarerat`; gamla vägen får ingenting.

**Guacamole, väggar (platsramen, m).**

| del | före | efter |
|---|---|---|
| vagg_bak (mitt) | (-0,518; 2,904), bredd 3,20 | (0,099; 2,978), bredd 5,35 |
| vagg_sida (mitt) | (1,221; 0,535), längd 4,93 | (2,910; 0,652), längd 4,97 |
| golv | 3,20 x 4,93 | 5,35 x 4,97 |

**Kontroll per scen** (kamerans provrutor). Före (gamla väggar, kontrollen körd på baslinjens plan): s1, s2, s3 rena; s4 kameran utanför rummet i 37 av 37 provrutor, vagg_sida mellan kameran och både A och B. Efter: alla fyra rena, inga varningar utöver bildtrohetens. Noteras: s2 var inte blockerad i den nuvarande baslinjen (loggens iakttagelse om s2 gällde första filmen, innan B:s plats flyttades).

**Notan.** Geometrin är oförändrad (rummet rymde redan allt); enda skillnaden mot baslinjen är det nya fältet `kvalitet.rumsvaggar` (alla sju scener rena, inga väggar flyttade). **Gamla vägen** (`kalla_jamn_golv.json`): 0 skillnader.

**Rätt skymningsregel.** `kontrakt/skymning.py` (14458 byte, oförändrad under körningen) hade tidvis varit utbytt mot en äldre version. Alla jämförelser här gäller omkompilering med färsk cache (`datacache.CACHE` på tom mapp) och den rätta regeln. Möbellösaren väljer då: guacamole bardisk höjd 1,00 m (utgångsvärde 1,05), djup 0,65, mittpunkt 0,65 m (utgångsvärde, oförändrat; under den gamla regeln 0,725); flaggade vid utgångsvärdet bara s3 (3,42 %; s1 0,57 % under gränsen), efter lösaren alla 0,0 %, disken med i alla fyra scener, `atgarder` tom. Notan bord_1: ingen scen flaggad (s1 0,25 %), lösaren rör inte bordet: 0,70 m (under den gamla regeln 0,66 m, gräns nådd). Det första baslinjeförsöket med standardcachen gav de gamla besluten (0,725 och 0,66); planbeslutscachen (`ut/cache/planbeslut`) nycklas på kodinnehåll men gav alltså gamla svar för de ursprungliga kalla-sökvägarna, vilket är en misstänkt förgiftad post (inget raderat). `test_snabb` är nu grön (7 av 7, inklusive provet som tidigare gav KeyError) och möbellösarens prov (`test_rumsmall.Mobelintervall`) håller.

**Rendering** (`vaggar_narvaro/`): 299 rutor, originalljud, Blender 124 s. Stillbilder `stillbilder/jamforelse_f0030.png`, `f0100`, `f0120` (s2), `f0230` (jämförelse original vänster, ren rendering höger). Visuell bedömning i rapporten. Textlagret (problem 5) rörs inte; `film_utan_text.mp4` används.

**Prov.** `test_rumsmall.Vaggar` (5) och `ingest/test_deklaration` (1 nytt). Alla gröna: `ingest/test_deklaration`, `test_rum`, `kontrakt/test_rumsmall` (37), `test_steg11`, `test_regler`, `test_kroppmatt`, `test_props`, `test_handelser`, `test_text_disk`, `test_snabb`, `test_flode` utom Plats.

**Ej löst.** Marginalerna är antagna. Väggarna är fortfarande tomma mallplan utan källmätning, och rummet blev större (golv 5,35 m) än verkligheten. Kamerans lins och bildvinkel prövas inte mot väggens kant (bara mittpunkt). Problem 2 (rollernas djup/storlek i S4), 3 och 5 orörda.

## Bildtrohet i slutkameran och massiv disk (11 nov natt)

Uppdrag och återupptagningslogg: `CODEX-BILDTRO.md`, `BILDTRO-LOGG.md`. Baslinje med kod och planer före arbetet: `kontrakt/ut/fore_bildtro/`. Alla verifieringskompileringar använde egna tomma cachemappar; den gamla `ut/cache/planbeslut` lästes eller raderades inte.

**Ny mätning.** `kvalitet.bildtrohet` projicerar för deklarerade rum de byggda rigglederna genom den slutliga `renderkamera` och jämför med samma rutors cachade MHR70-2D. Per scen/roll: medeloffset i px och bildhöjdsandel, skalfaktor och bbox-IoU. Egna gränser: 3 % bildhöjd, skala 0,85–1,15, IoU 0,65. S2 mäts trots 51/51 opålitliga rutor. Den äldre ingestkamerakontrollen finns under `ingestkamera`; gamla vägen använder oförändrad äldre post.

Guacamole före och efter kamera-/diskarbetet (px / % höjd / skala / IoU): s1/A 2,56 / 0,25 / 1,002 / 0,974; s2/B 3,98 / 0,39 / 0,999 / 0,984; s3/A 4,84 / 0,47 / 0,998 / 0,939; s4/B 3,52 / 0,34 / 1,000 / 0,965; s4/A 0,92 / 0,09 / 0,999 / 0,980. Alla oförändrade och inom gränserna.

**Var kamerafelet inte finns.** `ingest/plats.py:457–491` registrerar kamera och kroppar med samma stela transform; `kontrakt/kompilera.py:183,520` för nycklarna till slutplanen; `ingest/mhr_rig.py:232–237` sätter samma upplösning, matris och 64 mm lins i Blender. Kontrollerat i sparad blend: s2 och s4:s matriser stämmer på sex decimaler. Blenderben, numpyprojektion och cachade 2D-leder stämmer inom några px. Höjd 1,40 m, xy/yaw, pitch/roll, 64 mm och djupskala 1,0 bär alltså ingen s2/s4-drift. Den upplevda skillnaden kommer efter skelettet: lod3-standardkropp utan kläder och den gamla tunna möbeln.

**Allmän kameralösare.** Nya `kontrakt/bildkamera.py` provar per scen gemensam xy, yaw, pitch, roll och lins mot alla roller. Kamerans z, deklarerade platser och kroppar rörs inte. Valfri `kameror.<S>.xy_m` kan vara hårt tal eller intervall. En kamera inom gränserna bevaras exakt; annars krävs minst 10 % och 2 px förbättring. Guacamole s1–s4 och notan s1–s7 bevarades. Ingen deklaration rättades för att dölja rest.

**Massiv disk.** Deklaration 0.8 anger `bardisk.massiv: true` (0.7 sparad bredvid). Rumsmallen/Blender bygger en enda låda ner till golvet. Möbelintervallet valde 2,80 × 0,65 × 1,00 m, centrum `(0,012; 0,651; 0,500)` m; disken finns i alla 299 rutor, 0 flaggade scener och inga skymningsåtgärder. Notans bord saknar flaggan och ändras inte.

**Regression.** Notan mot `fore_vaggar/omkord_ratt_skymning/efter/notan.json`: efter att de två nya diagnostikposterna och deras gamla s6-varning räknats bort är planen identisk; alla sju kameror bevarade, all geometri/tid oförändrad. Gamla vägen `kalla_jamn_golv.json` är byte-identisk, sha256 båda `dd227ba28301119491972f959f048cc7e8c73b63da03818298ef978fc6ab1c1d`. Prov: 9 ingest + 138 kontrakt + 24 flödesprov utan `Plats` = 171 gröna; loggar i `fore_bildtro/test/`.

**Slutrendering.** `kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/`: 299 rutor, 720×640 jämförelse, 9,9667 s, väggar på, ren film utan text bevarad. f0030: A:s huvud/armar ligger nära originalet och diskens överkant är rimlig, men den svarta lådan är för grov. f0100/f0120: B är fortfarande högerställd/beskuren som både originalets cachade leder och planen anger; kameran ändrades inte, miljön är mycket förenklad. f0230: massiv front döljer underkropp och förbättrar läsningen klart, men B är fortfarande för voluminös/nära i den nakna standardkroppen, A låg/liten och U-returen saknas. Resultatet är bättre som rumsblockning men inte bildtroget nog för godkännande.

## Textlagret i S4 (12 nov)

Problem 5 är åtgärdat allmänt. Förearkiv: `kontrakt/ut/fore_text_s4/` med berörd kod och `plan_fore.json` tagna innan kodändring; `textenheter.py` kopierades innan den filen berördes. Arbetslogg: `TEXT-LOGG.md`. Inga modelljobb, tröskeländringar eller källfilbyten.

**Orsak.** I dåvarande `kontrakt/skarmtext.py:143–152` gjorde en ofullständig fulltextträff hela enheten `antagen` och ersatte den uppmätta delsträngens synlighet med hela scenen. S4:s `st6` och `st8` blev därför båda `[190,299)` i samma reservbox, trots delträffar 0,380 och 0,550. `textenheter.py` samordnade bara tal + `kg`, inte delar av samma undertextblock eller ersättande block. I dåvarande `kontrakt/textmalning.py:16–18` radbröts bara CM-/replikersatt text; modelltext i reservbox målades på en rad utanför bild.

**Ändrat.** `skarmtext.py` behåller delsträngens egna källrutor och faller tillbaka till hel scen bara utan mätbart intervall; timingens ursprung sparas. `textenheter.py` samlar samtidiga fragment i samma skärmyta till ett block och låter ostödda block ersätta varandra; verkligt uppmätt samvisning markeras uttryckligt. Ett inledande utrop bevaras fram till delsträngens första ruta. `textmalning.py` radbryter all överbred text och håller målningen inom 5 % säker bildyta. `kompilera.py` anropar ny plandiagnos: vid fel skrivs `kvalitet.skarmtext` och varningar för bildkant respektive tids- och ytkorsning utan källstöd; en ren plan får ingen tom post och gamla vägen kan förbli identisk. Fyra nya prov finns i `test_text_disk.py`.

**S4 före/efter.** Före: tre enheter, två långa synliga hela S4 och en tredje ovanpå rutor 236–285; enradiga och klippta. Efter: `AAAAA!` 190–204, `Jag trodde du var en sådan idiot,` 205–235, `men nej, den kommer med nachos,` 236–285. De visas ensamma, centrerade och de långa blocken på två rader. Slutplanens diagnos gav 0 varningar; därför skrevs ingen felpost.

**Bindande regression.** Notan (`kalla_mobelintervall.json`) och gamla vägen (`kalla_jamn_golv.json`) kompilerades med nya separata slutcacher. Mot `notan_berattat/bildtro/plan.json` respektive `notan/gamla_bildtro/plan.json`: exakt 0 skillnader i vardera full plan. Alla sju textenheter, tider, boxar och stilar är exakt oförändrade; gamla vägens bindande skillnader är 0.

**Verifiering.** Färsk slutcache `fore_text_s4/cache_guacamole_slut/`, plan `text_s4_slut_data/plan.json`, rendering `text_s4_slut_narvaro/film.mp4`, jämförelse `text_s4_slut_narvaro/jamforelse.mp4`. Båda 299 rutor, 9,966667 s och ljud; filmen 576×1024, jämförelsen 720×640. f195/f215/f245/f255 granskades mot originalet: tidsersättning, centrering och tvåradsbrytning fungerar, ingen text klipps. Typsnitt, storlek och exakt radbrytning är nära men inte pixelidentiska; sparad semantik har `AAAAA!` med färre A än källans synliga utrop. Texten är modellsemantik, inte OCR.

**Prov.** `test_text_disk` 16/16; `test_snabb`, `test_regler`, `test_steg11`, `test_handelser` 60/60; `test_flode.Flode`, `BarOforandrad`, `Notan` 24/24. Totalt 100/100 gröna. `test_flode.Plats` kördes inte enligt uppdraget. `PIPE.md` är oförändrad eftersom dess listade öppna luckor inte omfattar detta textfel.

**Ej löst.** Textinnehållets bokstavsexakthet, fontmatchning och exakt källradbrytning kräver granskad textreferens/OCR; inga sådana tjänster fick användas. Övriga redan dokumenterade bildtrohetsbrister i kropp, miljö och bardisk är orörda.
