# Avvikelser och tolkningar, steg 2 (invarians)

Skriven 20 november 2026 **före** den skarpa testmätningen (MANIFEST.md fryser kodens sha256 efter den här texten och före första testmätningen). Rubriker märkta "Tolkning" är punkter där protokollet (`T4-codex/FORREGISTRERING.md`) lämnar ett val öppet. Jag har fyllt luckan på det sätt som ligger närmast protokolltexten och skrivit ner det här, innan något testvärde fanns. Rubriker märkta "Avvikelse" är punkter där protokollet inte går att följa som det står.

## Avvikelse 1. Den blinda perceptuella innehållskontrollen går inte att utföra (påverkar domens styrka)

A2 kräver att C mot O och varje N mot C bedöms blint av en bedömare som ser/hör klippen (samma handling/ord/poäng, samma framförandetempo, samma upplevda energi; två lyssningar för ljudnivån; P ska identifieras som snabbare i minst 10 av 12 fall). Jag är en agent utan hörsel och utan oberoende blind bedömare. Det finns ingen mänsklig panel i den här körningen. Att jag själv "blindar" mig är meningslöst eftersom jag byggde varianterna.

Konsekvenser, bestämda i förväg:

1. Ingen variant kan kallas "blindgodkänd". Redovisningen visar därför **alla råskillnader** (det protokollet kräver) och domen enligt A4 beräknas på **alla 12 klipp utan blindfilter**. Varje dom märks "ofiltrerad".
2. Hur långt den ofiltrerade domen räcker: ett blindfilter kan bara ta bort N-observationer eller hela klipp. Ett fält som är KLARAT ofiltrerat förblir klarat med filter, utom där filtret skulle dra antalet giltiga klipp under 8 (villkor 1, "ej prövat"). Ett fält som är FÄLLT ofiltrerat kan i princip vändas av ett filter som tar bort just de ingrepp som flyttade måttet. Fällningar är alltså **villkorade** av att inget av de ingrepp som flyttade måttet skulle ha underkänts blint. Rapporten anger per fällt fält vilka N och vilka klipp som bär fällningen så att en senare bedömare kan pröva det.
3. **P:s perceptuella tydlighet (minst 10/12) kan inte intygas.** Enligt A2:s egen regel får försöket då ingen generell tempodom. Jag redovisar P:s mätbara effekt (längd/tempo i mätarna) men säger ingenting om att P "uppfattas som snabbare".
4. Det som jag kan göra, och redovisar som diagnos och inte som grind: A/V-sluttider mot avsedd tidsavbildning, hash av avkodad bild/ljud (determinism), uppmätt gain (volumedetect), antal bildpaket (bildtakt), och en kontaktkarta över två klipp som jag tittar på själv.
5. Domaren/ägaren kan komplettera med den blinda bedömningen efteråt. Då ska den registreras som ett separat tillägg med råsvaren sparade, inte som ersättning av det här resultatet.

## Avvikelse 2. Filerna som extraktorerna läser

Extraktorerna har hårdkodad ingång (`~/Downloads/letrend-e13/*.mp4`) och utgång (`../data/format/...`) och återupptar redan mätta id:n. Jag har inte ändrat dem. Min adapter (`mat_adapter.py`) gör så här:

- Extraktorerna körs som **byte-identiska kopior** (sha256 kontrolleras mot repots filer vid varje bygge av trädet, se MANIFEST.md) i ett eget träd under `Downloads\letrend-r4-varianter\tree_<etikett>\`, så att utgången hamnar i trädet och inte i repots `data/`.
- Ingången styrs med miljövariabeln `USERPROFILE`/`HOME` för just extraktorprocessen. Där ligger varje mätfil som **hårdlänk** med namnet `<konto>~<VARIANT>-<videoid>.mp4`. Innehållet i en hårdlänk för en variant är Matroska/FFV1 (protokollets `.mkv`); ändelsen `.mp4` krävs av extraktorernas filglob. ffmpeg och OpenCV avgör format ur innehållet, inte ur ändelsen. Ursprungs-id och variant återfås ur stammen.
- `video/analys/pipeline.mjs` ersätts av en stubb som bara exporterar `DATA` (E28 använder inget annat ur den). `verktyg.mjs` är en identisk kopia.
- E28 körs med `--par 1` (sekventiellt, extraktorns eget argument; påverkar inte värdena).
- `YOLO_OFFLINE=1`, `ULTRALYTICS_OFFLINE=1`, `HF_HUB_OFFLINE=1` sätts för att inget nätanrop ska ske. Vikterna `yolov8n.pt` är en kopia av repots fil (sha256 i manifestet).
- Utdata nollställs per batch så att `återupptas`-logiken inte hoppar över något; resultaten flyttas till `ref_mat.jsonl` respektive `test_mat.jsonl` med ursprungs-id och variant-id.
- E37 läser bilder med OpenCV (`CAP_PROP_FRAME_COUNT` och positionssökning). För Matroska/FFV1 är bildantalet en uppskattning ur ström-metadata. Det är en egenskap hos instrumentet som prövas, inte något jag korrigerar.

## Avvikelse 3. Disken räcker inte för alla varianter samtidigt

FFV1 i 1080x1920 blir cirka 18 MB per sekund. En enda C av ett 58 s långt klipp är cirka 1 GB, och alla 13 filer per klipp skulle bli över 9 GB. Därför byggs varje variant, mäts och raderas, en i taget; C ligger kvar medan klippet behandlas. Före radering loggas varje fils sha256, hash av avkodad bild (framehash) och avkodat ljud, A/V-sluttider, ffprobe-sammanfattning och volumedetect (`bygg_logg.jsonl`). Receptet är deterministiskt (kontrolleras via Cr och N0r), så en variant kan byggas om. Disken hålls över 5 GB (avbryt under 5 GB). Mätningarna av referensmängden R gjordes på samma sätt.

## Tolkningar (fastställda före testmätning)

1. **Mätfiler per klipp.** O (original, endast diagnos, ingår inte i någon dom), C, **C2** (samma C-fil extraherad en gång till), **Cr** (C kodad en gång till från O), N0, **N0r** (N0 gjord en gång till från C), N1 till N6, P. Därmed "N0 och extraktionen av C körs två gånger" (A2) och förtestets krav på identiska exporterade fält (A3) prövas på tre sätt: C2 mot C, Cr mot C, N0 mot C, N0r mot N0.
2. **"Stabilt händelseantal"** (A4, storlekskravet för T-tid/-täthet): det räknade händelsefältet är `e28.byten` för `skott_median`, `skott_max`, `forsta_byte`, `takt`; `e28.pauser` för `forsta_ljud`; `e30.tal_segment` för `forsta_tal` och `tal_per_s`; `langd` har inget händelsefält. Antalet är stabilt om det är lika i C och P.
3. **Giltig positiv kontroll** för ett klipp och ett T-/T?-fält: p>ε, för T-tid/-täthet dessutom rätt tecken (tid ska minska, täthet öka) och, vid stabilt händelseantal, avvikelse från den förväntade faktorn (0,8 respektive 1,25) högst `max(ε, 10 % av förväntad ändring)`. Ett klipp som inte uppfyller detta räknas inte som giltigt för villkor 1; fel tecken räknas dessutom i villkor 3.
4. **Villkor 3, "teknisk ändring över ε på minst 3/12 klipp"**: ett klipp räknas om t_ij>ε där t är maximum över N1 till N5 (union över ingrepp). Samma union-definition används för L-måtten ("minst 3 klipp"). För G-måtten är per-ingrepp- och unionräkning båda redovisade och fällning sker om någon av dem når 3.
5. **E37**: varje `antal[0..5]` och de fyra härledda aggregaten (`personer_medel`, `andel_minst_en`, `andel_minst_tva`, `personer_max`) bedöms var för sig som G-personfält med ε=0. Villkor 4 för E37 räknar klipp med färre än sex rutor i C eller N1 till N5.
6. **Villkor 4 (saknat värde)**: ett klipp räknas om fältet har värde i C men saknas (None/NaN) i någon av N1 till N5 eller P. Att C självt saknar värde (t.ex. `forsta_tal` utan tal) räknas inte som nytt saknat värde och ger bara att klippet inte är giltigt för just det fältet.
7. **Grann-diagnosen**: T2:s fasta 19 fält (`T2_19` i `falt.py`), z från den frysta transformen, saknade z ersätts med referensmedianen (z-medianen i R) och en saknasindikator per fält (19 st) läggs till i avståndet; normen räknas över de 19 z-värdena (utan indikatorer). Fält som saknar kalibrerad axel (färre än 30 giltiga referenskonton, eller konstanta i R) får z=0 och indikator 1 i alla vektorer. Fem närmaste grannar enbart i R, id som utslagsregel. "Byter minst 3 av 5 grannar" = högst 2 gemensamma id mellan C:s och N:s fem. Fällning om det gäller minst 3 klipp (någon av N1 till N5).
8. **T?-fälten** (rörelse, rörelse_2s, rörelse_kvot) bedöms med samma villkor som T men utan tecken- och storlekskrav (A4: "bara det svagare responskravet").
9. **ECDF-stödet**: råvärden utanför R:s [min, max] flaggas i `analys_resultat.json` (`utanfor_stod`) men räknas ändå (ECDF mättas).
10. **Kontaktkartans två klipp** valdes före testmätning: `krogcompanyvarnamo-7442013966571801879` (1080x1920, 30 fps, 8,6 s) och `babasburgers-7625983366470454550` (1080x1920, 60 fps, 35 s; visar 60→30 fps-omvandlingen i C).
11. **A/V-sluttidskontrollen** (en 30 fps-ruta plus en ljudsamplingsperiod, A2) tillämpas på P (mot C-längden/1,25) och, som diagnos, på alla N (mot C). Avvikelser rapporteras per variant; de stoppar inte mätningen ("stoppar renderaren, inte mätaren").
12. **Dry run.** Mekaniken (bygge, mätning, bilagor, kontaktkarta, analyskod) provas på fyra korta R-klipp (som redan är referensklipp) före manifestet. Inga testklipp berörs. Dry-värden används inte i någon dom.

## Intyg om exponering

Jag har läst protokollet, extraktorernas kod, T2:s diagnoskod och T3:s granskning, men **inte** öppnat några gamla E28/E30/E37-värden för de 24 testklippen (varken `data/format/e28/tek.jsonl`, `e30/tal.jsonl`, `e37/personer.jsonl` eller `rum.jsonl` för dessa id), och inga värden från de nya mätningarna av testklippen fanns när koden och dessa tolkningar skrevs. Jag har inte justerat någon del av metoden för de 12 testklippen individuellt. Klippens konton är dock enligt protokollet "prospektivt undanhållna" och inte bevisat aldrig sedda i T1:s och T2:s diagnoser (FORREGISTRERING.md, Gemensamt). Provet ska därför kallas utvecklingsprov om någon annan i kedjan har använt dem för justering.

## Tillägg (22:45, efter att testkörningen startats, men innan något testvärde har öppnats): bedömningsregler för T4:s prognoser (A5)

Testkörningen (`test_kor.py --lage test`) startades 22:43 efter MANIFEST.md. Reglerna nedan för hur prognoserna i A5 ska bedömas fastställs här innan `test_mat.jsonl` har lästs. De är min tolkning av A5:s formuleringar. A5 ger inga siffror.

1. **`rorelse`, `rorelse_2s` "förväntas falla som generell tempo/energi-axel"; `rorelse_kvot` "ofta"**: *rätt* om A4-domen är FÄLLD genom villkor 2, 3 eller 4. *Delvis* om fältet bara är FÄLLT genom villkor 1 (för få klipp där positiva kontrollen rör sig över ε, alltså att måttet inte är känsligt). *Fel* om KLARAD.
2. **`ljud_andel`, `pauser`, `forsta_ljud` "känsliga"** (för ljudnivå): *rätt* om fältet i N3 eller N4 skiljer sig från C mer än ε på minst 3 av 12 klipp. Delpåståendet om tystnad i slutet som saknas i summeringen prövas inte i steg 2.
3. **`lufs` ska förändras vid gain; `lra` betydligt stabilare**: *rätt* om A4:s L-dom för `lufs` är KLARAD (svar −6/−12 LU inom 0,5) och `lra` är KLARAD (stabil inom 0,5 LU över N1 till N5).
4. **E37 "kan falla i låg upplösning/nära tröskeln"**: *rätt* om minst ett E37-fält har över-ε-skillnad vid N2 på minst 3 av 12 klipp. Annars *fel*. N1 och N5:s bidrag redovisas separat.
5. **`tal_per_s` "kan överleva teknikprovet men ändå misslyckas som framförandeenergi"**: första halvan *rätt* om `tal_per_s` är KLARAD i A4 (T-dom). Andra halvan (energi) kan inte prövas i steg 2 och lämnas åt steg 3.
6. **`langd` bör klara teknikprovet**: *rätt* om KLARAD. **`takt` "bör ofta klara omkodning men kan få falska byten vid bildtakt/skala"**: *rätt* om (a) `takt` skiljer högst ε från C under N1 på minst 10 av 12 klipp och (b) antalet byten `e28.byten` skiljer sig från C under N2 eller N5 på minst 1 klipp.

Observera att dessa bedömningar gäller den **ofiltrerade** domen (Avvikelse 1).
