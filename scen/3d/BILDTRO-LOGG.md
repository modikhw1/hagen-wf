# Bildtrohet i slutplanen

## Del 1 – mätning (11 nov 2026)

Klart:

- Före kodändring kopierades 111 filer till `kontrakt/ut/fore_bildtro/`: alla översta Pythonfiler i `kontrakt/` och `ingest/`, deklarationerna, dokumenten och aktuella planer för guacamole, notans bindande väg och gamla vägen.
- `kontrakt/trohet.py` mäter nu varje läst roll genom `plan.renderkamera`, mot samma rutors cachade MHR70-2D-leder. Per scen/roll skrivs medeloffset i px och andel av slutbildshöjden, skalfaktor, bbox-IoU, antal mätta/opålitliga rutor och varningsskäl. Den äldre kontrollen i `matkamera` ligger kvar under `ingestkamera`.
- Trösklar (egna, inga ägarkrav): offset över 3 % av bildhöjden, skalfaktor utanför 0,85–1,15 eller bbox-IoU under 0,65. Motivering: 3 % är 30,7 px i 576×1024 och syns tydligt; 15 % är ett märkbart byte av bildstorlek; 0,65 är den befintliga ledkontrollens undre IoU-gräns.
- S2 mäts trots att alla 51 rutor är märkta opålitliga; frånvaron av godkända poser gör inte längre scenen omätt.
- Nya prov `test_kroppmatt.Slutbild`: 2 av 2 gröna.
- Resultat med oförändrade planer finns i `kontrakt/ut/fore_bildtro/matning_fore/` och den ursprungliga mätcachen är orörd.

Guacamole före kamerafix (medel px / % bildhöjd / skala / IoU):

| scen | roll | mått | flaggad |
|---|---|---|---|
| s1 | A | 2,56 / 0,25 % / 1,002 / 0,974 | nej |
| s2 | B | 3,98 / 0,39 % / 0,999 / 0,984 | nej (51/51 opålitliga) |
| s3 | A | 4,84 / 0,47 % / 0,998 / 0,939 | nej |
| s4 | B | 3,52 / 0,34 % / 1,000 / 0,965 | nej |
| s4 | A | 0,92 / 0,09 % / 0,999 / 0,980 | nej |

Notan, bindande väg före kamerafix:

| scen | roll | mått | flaggad |
|---|---|---|---|
| s1 | A | 2,72 / 0,27 % / 1,003 / 0,964 | nej |
| s2 | B | 6,14 / 0,60 % / 1,002 / 0,964 | nej |
| s3 | A | 6,88 / 0,67 % / 1,013 / 0,943 | nej |
| s4 | C | 2,62 / 0,26 % / 1,000 / 0,995 | nej |
| s5 | B | 5,49 / 0,54 % / 1,004 / 0,970 | nej |
| s6 | A | 28,35 / 2,77 % / 0,993 / 0,929 | nej, nära offsetgränsen |
| s7 | B | 1,88 / 0,18 % / 0,994 / 0,966 | nej |

Iakttagelse: `matkamera` och `renderkamera` är byte-/talidentiska i den aktuella guacamoleplanen (samma matris och 64 mm i alla provade rutor). Den nya planmätningen ser därför ingen inramningsdrift i s2 eller s4 trots den synliga skillnaden i de renderade jämförelsebilderna. Del 2 måste särskilt kontrollera överföringen plan → Blender och om 2D-läsningen själv bär felet.

Återstår: del 2 orsaksspårning; del 3 kameralösning inom deklarationen; del 4 solid disk om tid; full regression, ny rendering och slutrapport.

## Del 2 – var inramningen tappas (11 nov 2026)

Spårat hela vägen för s2 ruta 120 och s4 ruta 230:

- `ingest/plats.py:457–491` löser deklarerad plats som stel yaw + xy, skala 1,0 och bunden z. Samma transform förs på både kamera och kroppar. En sådan transform kan inte ändra deras 2D-projektion.
- `kontrakt/kompilera.py:183–184` bygger renderkameran av den transformerade källkameran; `:520` lägger exakt dessa nycklar i slutplanen. `matkamera` byggs separat på `:622–625`. I den aktuella planen är de två kamerorna identiska.
- `ingest/mhr_rig.py:232–237` sätter 576×1024, horisontell 36 mm-sensor, planens matris och planens lins. Den sparade `scen.blend` har exakt samma matriser som `plan.json` (max redovisad skillnad 0 på sex decimaler) och 64,0 mm.
- Blenderprojektion av de faktiska rigglederna sammanfaller med numpyprojektionen. Exempel s4/B ruta 230: skuldror `(485,5;526,6)` och `(454,3;538,4)` px i Blender, samma som planen; originalets cachade 2D är `(485,2;524,9)` och `(455,3;537,5)` px. Medelfelet är 2,80 px i just den rutan.

Variabler, s2 / s4:

| bärare | s2 | s4 | slutsats |
|---|---:|---:|---|
| deklarerad kamerahöjd | 1,400 m | 1,400 m | flyttar kamera och kroppar lika; 0 px inramningseffekt |
| kamera xy | (1,030; 0,390) m | (2,244; 2,476) m | följer den stela platsregistreringen; 0 px |
| yaw | −54,46° | −120,48° | följer rollposition/torsoriktning; 0 px när kamera och kroppar vrids lika |
| pitch | +0,20° | +0,77° | bevarad käll-/lodlutning, inte nollad |
| roll | ca +0,16° | ca +0,66° | bevarad käll-/lodlutning |
| lins / FOV | 64,0 mm; 31,42° H, 53,13° V | samma | samma 1024 px-fokal som kroppsläsningen |
| djupskala | 1,000 | 1,000 | ingen per-tagningsskalning; `golv_skala` är 1 i alla rutor |

Orsak per scen: ingen av de uppräknade kameravariablerna bär det synliga felet i s2 eller s4. S2:s cachade leder säger själva att vänster skuldra ligger vid x=702 px, alltså utanför den 576 px breda bilden; slutkameran återger det. S4:s båda roller återges också på samma ledpositioner som originalet. Den visuella storleksskillnaden bärs av den nakna standardkroppens volym/ytform jämfört med kläder och av att den tunna skivan inte döljer underkroppen som originalets massiva disk. Den oberoende maskkontrollen stödjer detta: s4/B:s byggda silhuett-IoU 0,738 är i nivå med estimatorns egen 0,736; s4/A är låg redan för estimatorn (0,539) och byggd kropp (0,545).

Återstår: del 3 bygger den allmänna slutkameralösaren men får inte hitta på en guacamolejustering när 2D-målet redan är uppfyllt. Del 4 kan lösa den tydligaste kvarvarande s4-skillnaden (massiv disk).

## Del 3 – kameralösning inom deklarationens regler (11 nov 2026)

Klart:

- Ny allmän modul `kontrakt/bildkamera.py`, anropad efter byggbesluten men före väggkontrollen. Den gäller bara deklarerade rum; gamla vägen och klipp utan deklaration får ingen ny post eller ändring.
- Per scen provas en gemensam kamera-xy, yaw, pitch, roll och lins mot alla synliga rollers cachade 2D-leder. Kamerans z lämnas exakt orörd, liksom golv, platser, sitthöjder och samtliga kroppar.
- En valfri deklarerad `kameror.<S>.xy_m` förs som `deklarerat.kamera_xy_m`: tal är hårt, intervall är lösarens gräns, utelämnad xy är fri. Guacamole och notan saknar fältet, alltså är deras xy fri.
- Överpassningsskydd: en kamera inom del 1:s trösklar bevaras byte för byte. En flaggad kamera ändras bara om medeloffset förbättras minst 10 % och 2 px utan att bbox-IoU försämras mer än 0,01.
- Syntetiskt prov återfinner en känd xy/yaw/pitch/roll/linsändring med högst 0,05 px rest; kroppspunkterna rörs inte.

Full guacamolekompilering med ny tom cache `kontrakt/ut/fore_bildtro/cache_del3_guacamole/` finns i `kontrakt/ut/e-dialog-guacamole/bildtro_data/`. Alla fyra kameror bevarades exakt eftersom startmåttet redan är inom gränserna. Kandidatens medeloffset före → kandidat: s1 2,557 → 2,553 px, s2 3,982 → 3,955 px, s3 4,844 → 4,876 px, s4 (båda roller) 2,218 → 2,210 px. Förbättringarna är brusnivå och får inte styra kameran.

Slutplanens guacamolemått är därför samma som del 1 på redovisad precision: s1/A 2,56 px; s2/B 3,98 px; s3/A 4,84 px; s4/B 3,52 px; s4/A 0,92 px. Ingen bildkameravarning och inga andra varningar.

Notans sparade plan provades genom samma lösare: alla s1–s7 bevarades. S6 låg närmast gränsen (28,35 px = 2,77 %), men är fortfarande inom 3 % och kandidatlösningen gav bara 0,04 px förbättring. Underlag: `kontrakt/ut/fore_bildtro/bildkamera_kandidat/`.

Deklarationen hindrar alltså inte en match i s2/s4; den lästa ledprojektionen är redan matchad. Ingen deklaration har redigerats och ingen kropp har flyttats för att dölja en rest. Kvarvarande synlig skillnad kan inte rättas hederligt med kameran mot det givna 2D-underlaget.

Återstår: del 4 solid disk, därefter full notan-/gammal-väg-regression, hela provlistan, ny guacamolerendering och slutrapport.

## Del 4 – massiv bardisk (11 nov 2026)

Klart:

- Deklarerade bord/diskar kan ange `massiv: true`. Fältet förs till `hand.deklarerat.mobler`, den genererade rumsmallen och `plats.json`.
- `ingest/rumsmall.py` bygger då exakt en ogenomskinlig låda från golv till ovansida i stället för en 4,5 cm skiva på fyra ben. Blender behöver ingen särregel: den befintliga planrumsbyggaren bygger lådan från planens `matt_m` och `pos_m`.
- Rumsmallsschemat tillåter det nya booleska fältet. Fokuserat prov kontrollerar både deklarationsöverföring och att geometrin är en enda 2,8 × 0,65 × 1,05 m-låda med centrum z=0,525.
- Guacamoles deklaration är version 0.8 med `bardisk.massiv: true`; version 0.7 är sparad bredvid. Notans båda bord saknar fältet och förblir skivor på ben.
- Ny deklarations-/platskedja: `ingest/ut/e-dialog-guacamole-tagningar/plats_bildtro/`; ny källa: `kontrakt/ut/e-dialog-guacamole/kalla_bildtro.json`.
- Full kompilering med tom cache `kontrakt/ut/fore_bildtro/cache_final_guacamole/`: 121,27 s, resultat `kontrakt/ut/e-dialog-guacamole/bildtro_massiv_data/`.

Guacamoles valda slutdisk är en enda låda 2,80 × 0,65 × 1,00 m, centrum `(0,012; 0,651; 0,500)` m, synlig i alla 299 rutor. Möbelintervallet såg s3 flaggad vid 1,05 m, valde 1,00 m och fick 0 flaggade scener; skymningskontrollens åtgärdslista är tom. Kamerorna är fortfarande bevarade och bildtrohetsmåtten är oförändrade. Inga planvarningar.

Del 1–4 är därmed genomförda. Återstår den samlade obligatoriska verifieringen, ny rendering och dokument/slutrapport.

## Slutverifiering (11 nov 2026)

- Notan kompilerad med tom cache `fore_bildtro/cache_final_notan/` till `notan_berattat/bildtro/`. Mot korrekt baslinje `fore_vaggar/omkord_ratt_skymning/efter/notan.json` är enda skillnaderna de nya `kvalitet.bildkamera`/`bildtrohet` och att den äldre s6-varningen försvinner: s6 är 28,35 px = 2,77 %, under nya 3 %-gränsen. När dessa diagnostikskillnader räknas bort är planen identisk; alla kameror, kroppar, möbler, väggar, tider och ljudbeslut är oförändrade. `fore_bildtro/verifiering.json`.
- Gamla vägen kompilerad med tom cache till `notan/gamla_bildtro/plan.json`: byte-identisk med baslinjen, 0 skillnader, samma sha256 `dd227ba28301119491972f959f048cc7e8c73b63da03818298ef978fc6ab1c1d`. Klipp utan deklarerat rum går samma bevarade kodväg; `test_flode.BarOforandrad` är grön.
- Provloggar i `fore_bildtro/test/`: `test_deklaration` + `test_rum` 9/9; `test_rumsmall`, `test_steg11`, `test_regler`, `test_kroppmatt`, `test_props`, `test_handelser`, `test_text_disk`, `test_snabb` 138/138; `test_flode.Flode`, `BarOforandrad`, `Notan` 24/24. Totalt 171/171 gröna. `test_flode.Plats` kördes inte enligt uppdraget.
- Slutrendering med väggar och utan textlager: `kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/film_utan_text.mp4`; sida vid sida `jamforelse.mp4`, verifierad 720×640, 299 rutor, 9,966667 s. Exakta stills ligger i `stillbilder/`.
- Visuell dom: f0030 får bättre diskfront och rimlig överkant men lådan är grov; f0100 och f0120 behåller B:s högerbeskärning eftersom originalets cachade leder själva ligger där; f0230 förbättras tydligt av att disken döljer underkropp, men B:s standardkropp är fortfarande för voluminös/nära, A läser lågt/litet och U-returen saknas. Inte godkänt som bildtrogen rekonstruktion.
- `PIPE.md` och `GUACAMOLE-LOGG.md` är uppdaterade. Ingen modellkörning gjordes, ingen gammal cache raderades och inga processer startade av detta arbete lämnades kvar.
