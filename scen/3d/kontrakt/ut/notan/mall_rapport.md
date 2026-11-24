# Rumsmall för notan, 10 november 2026

## Valet av bord

Två bord. S7 visar B:s hela bortre bord med egen kant, ben och stolar, en passage, och A:s bord med Bonaqua-burk och matpapper i förgrunden. Det är starkare evidens än antagandet om motbilder från varandras sittplatser. S1 och S2 har olika uppsättningar mat och dryck; inga axlar eller händer förenar motbilderna. S4 visar en gång och separata gästbord men ger ingen säker geometrisk koppling mellan A och B.

Topologin och det avrundade stolsavståndet 2,48 m är märkta `antagen` i `ingest/ut/notan-tagningar/plats/hand.json`. Avståndet är den tidigare skattningen, inte en ny mätning. S4:s servitör flyttas från cirka (-1,97, 1,00) till (-0,95, 0,55), antaget bredvid A:s bord. Kamera och kropp följer med tillsammans. Bildkopplingen S1/S3/S6 och deras uppmätta rest lämnas kvar.

## Modell och passning

Banken finns på ett ställe, `kontrakt/rumsmall/`. Den gamla `plats_bank/fiktiv_lokal.json` pekar dit. Mallarna är `restaurang_tva` (ett bord för två), `notan_tva_bord`, `bar_disk` och `fiktiv_lokal`. Den sistnämnda är uttryckligen påhittad: rosa väggar, turkost golv, blå stolar, ljusa bord, disk och hylla.

Deltyper: golv, vagg, bord, stol, bardisk, hylla, fonster, lampa. Ankartyp: sate, staplats, sta_bakom, bordskant, annat. Mått, placering inom möbeln, material och konstruktionsdetaljer är mallvärden. `modell_ref` och `texturprojektion` reserveras men används inte. Byggaren skapar lådor och cylindrar med enkla material och fasning; ingen modell laddas ned.

Passningen matchar namn och typ och minimerar XY- och riktningsfel. Skala är 1, Z följer golvet. Antagna vikter: sitt/stå 1, bordskant 0,1, riktning motsvarande 0,5 m hävarm. Därefter fästs stolar och deras bord till de uppmätta ankarnas XY och riktning; varje lokal justering sparas separat. Djupfragmenten byggs aldrig i malläget.

Notan: RMS 0,09386 m före lokal anpassning. Stol A 0,03356 m, stol B 0,02206 m, ståplats C 0,01510 m, bordskant A 0,06995 m och bordskant B 0,50853 m. B:s kant har också nästan motsatt riktning: det osäkra fragmentet är ingen tillförlitlig bordsskiva. Dessa tal är passningsfel mot delvis antagna ankare, inte fel mot en inmätt verklig lokal.

Bar: en uttryckligen vald diskmodell passas mot den befintliga diskens kant och golv. Personerna rör sig och gav inga stationära personankare. Kantens höjdrest är 0,20074 m; XY och yaw passar med ett enda kantankare, vilket inte är en oberoende geometrisk kontroll. Standardplanen är byte-identisk med regressionens referens. Det separata mallprovet finns i `mall_bar/`; personer, renderkameror, källrutor och tidskarta är exakt lika, medan geometrin ändras från 4 till 12 byggobjekt. Den möblerade barplanen har inte renderats.

## Kroppsstöd

Ingest har en flagga för båda benen, `ben_synliga`, och inga finare ledmasker. En sann eller saknad flagga skyddar hela underkroppen. Notan har noll sanna benrutor. Varje faktiskt ingrepp och utdataruta står i filmmapparnas `stod_rapport.json`.

| Person och scener | Ändring | Antal rutor i tom film |
|---|---|---|
| A: S1, S3, S6 | root och båda benens 32 leder | 73, 57, 56 |
| B: S2, S5, S7 | root och båda benens 32 leder | 41, 25, 46 |
| C: S4 | båda benens 32 leder, root skyddad | 85 |

Benkedjan per sida är upleg, lowleg, foot, talocrural, subtalar, transversetarsal, ball, lowleg_twist1–4_proc och upleg_twist0–4_proc. Sittbäckenets ledcentrum sätts till sits 0,52 + mallens mjukdelsmått 0,11 = 0,63 m. Låren ligger horisontellt över sitsen. Fotledens mallhöjd är 0,065 m över golvet; tåleden använder ett enkelt sulmått. Ståstödet behåller bäckenet och löser benen mot golvet. Dessa höjder är mallvärden, inte nya mätningar.

Alla leder från c_spine0 och uppåt behåller exakt samma globala pose i numpy, inklusive händer och huvud. Blender bygger deras matriser med kompensation mot ändrade föräldrar. Kontroll av två rutor per scen ger högst 0,00359 mm lägesfel från flyttalsberäkning. Hud nära bäckenet kan ändå påverkas av skinnvikter.

Sittlösningen behåller lårlängden men kan förlänga de osynliga underbenen 41–71 procent från MHR:s ursprungliga gissning. Det är en tydlig kvarstående anatomisk brist. De byggda fotsulorna når som lägst cirka -0,01856 m på de granskade rutorna. Ledkontakt är alltså inte samma sak som exakt hudkontakt.

S4:s `okand_s4_4` är 2,713 m från närmaste lediga mallsits, mot antagen tolerans 0,35 m. Personen utelämnas och listas med skäl. Inget nytt ankare uppfinns åt personen.

## Kontrakt och filer

Endast valfria tillägg i de befintliga schemana: `semantik.platser[].rumsmall_id`, `matning.platser[].rumsmall` (id, mallhash, RMS, ursprung), och `regi.edits[].rum.rumsmall_id` för byt_miljo. Den passade instansen ligger i den hashlåsta platsfilen och löses ut till planen. Notans källa och båda regiexemplen har revision 3. Byten skyddar ankartyp och följer varje persons eget ankare, även när flera personer finns i samma scen. Felaktiga mallar nekar bara redigeringen.

Fullständig lista med skapade/ändrade kod-, schema-, exempel- och platsfiler samt +/− rader finns i `filandringar.json`. Ursprungliga filer ligger under `fore_mall/scen/...`; de tidigare filmmapparna har inte skrivits över. Binära filmer och stillbilder redovisas separat nedan.

## Kontroller och kommandon

Alla vanliga Python-anrop använder `scen/.venv/Scripts/python.exe` och `PYTHONIOENCODING=utf-8`. Körningarna startas från projektroten; unittest körs enligt uppgiften med arbetsmapp `scen/3d/kontrakt`.

```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py exempel/bar
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py exempel/notan
C:/Users/praiseworthy/Desktop/hagen-wf/scen/.venv/Scripts/python.exe -m unittest test_flode
```

Resultat: bar 0 fel, 0 varningar, 15 hashar; notan 0 fel, 0 varningar, 64 hashar. Slutlig unittest: 41 tester, OK, 38,718 s (39,135 s väggtid inklusive start). Logg: `unittest_mall.log`.

Tester omfattar mallbankens schema och negativa värden, återfunnen känd rigid transform, fel ankartyp, sittbäcken/lår/fötter, exakt skyddad överkropp, oförändrade synliga ben och saknad flagga, ståkontakt, utelämnad okänd person, bevarade bindningar vid byte, två personers separata ankare, atomiskt nekat byte och deterministisk plats och plan. Bars äldre plan jämförs byte för byte med sin tidigare referens.

`mall_utan_plan.py -- fore` och `-- nu` körde den säkerhetskopierade respektive nya byggaren mot samma S1 utan --plan i egna bakgrundsprocesser. Objektnamn, kameramatriser och alla benmatriser är exakt lika på rutorna 0, 36 och 72. Detta är ett scenprov, inte en jämförelse av alla bildpixlar eller alla klipp.

`mall_granska_blender.py` granskar de sparade riggarna; `byggkontroll.json` finns i alla tre filmmappar. `stod_numpy_kontroll.json` granskar alla notans rutor i numpy. Alla filmer har H.264 och AAC och avkodas med `ffmpeg -v error -i <film> -f null -` utan fel. `film_kontroll.json` innehåller antal rutor, ljud och längder. Ingen lyssningsbedömning har gjorts.

Blender hittas genom BLENDER-konstanten i `ingest_klipp.py`, utan att ingest importeras eller körs. Alla byggen använder egna bakgrundsprocesser. Ingen GUI-session används. Inga befintliga ingeststeg, nätjobb, installationer eller nedladdningar kördes.

## Filmer, stillbilder och tider

Relativt denna rapport:

- `mall_tom/film.mp4`: 383 rutor, 12,7667 s.
- `mall_redigerad/film.mp4`: 326 rutor, 10,8667 s. S3 bortklippt, B röd, S1 har regins ändrade kamera, lokalt Piper-ljud enligt tidigare regi.
- `mall_byt_lokal/film.mp4`: 383 rutor, 12,7667 s.
- `mall_tom/oversikt_ovan.png`, `mall_tom/oversikt_sned.png`.
- `mall_byt_lokal/oversikt_ovan.png`, `mall_byt_lokal/oversikt_sned.png`.
- `mall_jamforelse/s1.png`–`s7.png`: två identiska källrutor per scen bredvid tidigare platsrum, tom mall, redigerad mall och kundmall.

| Fas, väggtid i sekunder | Tom | Redigerad | Bytt lokal |
|---|---:|---:|---:|
| Slutlig kompilering | 0,343 | 0,513 | 0,435 |
| Bygge inne i Blender | 12,588 | 10,289 | 11,042 |
| Rendering och ljudmux | 85,304 | 68,613 | 86,467 |
| Ljudbygge | 0,444 | 0,511 | 0,577 |

Plats och mallpassning notan: 5,905 s inklusive Python-start. Barpassning: 6,3 s enligt platsloggen; kallbygge och kompilering av separat barprov: 1,924 s. Fullständiga fasloggar ligger i `tider_mall.json` och respektive filmmapp. Globala loggen behåller också tider från det första kundprovet; slutliga kundfaser ligger i `mall_byt_lokal_slutliga_faser` och filmmappens egen tidsfil.

Efter sista kundrenderingen skrevs alla 383 PNG, blend, ljudmux och tidsfil färdigt. Sedan gav Intel `ig9icd64.dll` EXCEPTION_ACCESS_VIOLATION när Blender avslutades. Processens exitkod var 3221225477. Logg: `mall_byt_lokal/blender_slut.log`. Filmen har därefter avkodats utan fel och dess slutliga stillbilder och rigg har granskats.

## Vad bilderna faktiskt visar

Granskade källrutor: S1 10/60, S2 80/105, S3 120/160, S4 180/240, S5 260/275, S6 300/320 och S7 350/375. Även de tidigare översikterna och källbilderna k_300/k_350 öppnades.

1. A och B sitter nu på stolar vid separata bord i översikterna. S7 visar särskilt tydligt B:s stol, knän, horisontella skiva och bordsben. Stolarnas utformning är antagen och kroppen är fortfarande en neutral MHR-figur.
2. Handkontakt är ungefärlig. A:s handled i S6 är minst cirka 3 cm, median 8 cm över skivan. B:s handleder är minst 11–13 cm över skivan i S2/S5/S7; vissa fingrar kommer närmare. S1:s händer är höjda i en gest. Ingen exakt hand/skivkontakt löses och mat, muggar och burk saknas.
3. Servitören står på golvet bredvid A:s bord i översikten. Vilket bord som är rätt är antaget från samtalet; S4 kan inte bevisa positionen. Den gamla ensamma bakgrundspersonen är borta.
4. Väggar, golv, stolsryggar och bordsben gör att bilden läses som ett enkelt möblerat rum. Kundlokalen skiljer sig genom färger, disk och hylla. Det är ingen fotorekonstruktion; ytorna är rena och material och skuggor är enkla.
5. Tom och bytt mall behåller i huvudsak det tidigare personutsnittet. S2 beskär fortfarande huvudet kraftigt, precis som tidigare. B är för stor mot källan i S7. S1 i redigerad film har avsiktligt vidare utsnitt genom den befintliga regin. Mallarna rättar inte dessa tidigare kamerafel.

## Nästa klipp och gränser

Automatiskt efter befintlig ingest: platsregistrering där det finns stöd, enkel mallregel från ankartyper, rigid passning, stödens lokala anpassning, utelämning utan stöd, deterministisk kompilering, procedurbygge och benregel från synlighetsflaggan. Mallankarnas namn måste motsvara platsens namn; ett felpassat generellt rum blir inte automatiskt en korrekt lokal.

Handarbete behövs när topologin är tvetydig, roller/ankarnamn skiljer sig, kamerastationerna saknar bildkoppling, kundlokalen saknar mall eller riktiga mått behövs. Notan behövde tvåbordsvalet och S4:s läge. En verklig kundlokal matas som samma mallformat; en ensam bild räcker inte för säker geometri.

Viktigaste kvarstående problemen, högst sex:

1. Tidigare fel i kamera, skala och övre kroppsmodell kvarstår, särskilt S2:s huvudbeskärning och S7:s storlek.
2. Sittstödet kan ge 41–71 procent längre underben och cirka 1,9 cm hudpenetration i golvet. Bättre kroppsmått/skin kontakt behövs för anatomiskt säkra resultat.
3. Exakt handkontakt och källans bordsrekvisita saknas. Skyddade händer flyttas inte till skivan.
4. Stolsavstånd, C:s plats och rummets fulla utsträckning är antagna; residualerna bevisar inte verklig rumsgeometri.
5. Intel-drivrutinen kraschade vid ett Blender-avslut efter färdig render. Utdata klarade avkodning och granskning; drivrutinen är inte åtgärdad.
6. Ingen möblerad barfilm, verklig kundlokal, externa tillgångar, ytprojektion, ljudlyssning eller bred provning av rörlig kamera/flera platser har verifierats. Munnen följer fortfarande inte nytt tal.
