# Notan: förvärld med chatt och levande källtextur

Uppdaterad 10 november 2026. Del 1–3 är lättkontrollerade på nytt. Del 4 fungerar
som en bild/3D-hybrid med tydliga kvarstående fel. Del 5, klipp b, är uppskjuten.
Ingen Blender eller kompilator kördes under denna återupptagning. Grannjobbet under
scen/ får slutföra kroppsombyggnaden först. Det nu visade kroppspaketet är det gamla.

## Starta

Från C:\Users\praiseworthy\Desktop\hagen-wf:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
node forvarld/varld/server.mjs
```

Öppna http://127.0.0.1:5195. Servern binder bara loopback. Three.js och Chromium
använder befintliga lokala installationer. Ingen installation eller nedladdning behövs.
Chattens enda externa tjänst är TypeSafe System One. Nyckeln läses från app/.env.local;
den kopieras inte till paketet eller loggarna. Skrivfilerna ligger under forvarld/.

## Del 1: direktändringar

edits.mjs är samma deterministiska tillståndsreducerare i server och webbläsare.
Den hanterar ta bort, trimma utan tidssträckning, flytta och kopiera scen, textbyte,
text till/från, helkroppston/rollnamn, kamera, bakgrund och sammansatta förgrundskort.
Tidskartan styr kropp, källvideo och ljud. Ångra arbetar per ändringsgrupp.
Ändringslistan visas på svenska och som sparbar regi/1 JSON.

Elva redigeringsfall med ångra gav 5,8–93,4 ms till nästa rAF efter färdig ändrad
render, utan JavaScript-fel. Ta bort s2 gav 383 → 342 rutor. Se edit-check.json.
21 sparade edits klarar den delmängd av JSON Schema som regi.schema.json använder;
se light-verification.json. Detta är en schemakontroll, inte en ny offlinekompilering
eller kontroll av alla referenser/hashar.

POST /api/regi ger snabb förhandsvisning med reduceraren. POST /api/compile är den
äldre långsamma offlinevägen; chatten och knapparna anropar den inte.
Den nuvarande förhandsvisningen har begränsningar jämfört med offlinekontraktet:
ingen tidssträckning, ny geometri, separat burksegmentering eller syntetiserat tal.

## Del 2: chatt

Först väljer Jev ändringsfamilj och berörda delar i ett anrop. Sedan räknar koden
upp giltiga konkreta alternativ från aktuellt tillstånd, utesluter ogiltiga mål och
oförändrade värden och låter Jev välja i ett andra anrop. Ny text hämtas ur citat;
annars ber chatten om den. Osäkra val ger upp till tre knappar. Gränsen är 0,5 i
sannolikhetsmarginal mellan bästa och näst bästa val i båda stegen. Detta är en
heuristik, inte kalibrerad säkerhet. Musik, nya uttryck och rörelser loggas som önskemål.

Varje mening, frågor, svar, tider, tillämpning, ångra och manuellt val sparas i logg/.
Chattens ursprungliga tio mätningar finns i chat-measurements.json:

| Mening | ms till ändrad render |
|---|---:|
| Stabilisera kameran i scen 1. | 897,0 |
| Kom närmare B i scen 7. | 503,2 |
| Ge A blå helkroppston. | 459,9 |
| Byt undertexten i scen 1 till ”Vem betalar?”. | 437,0 |
| Ta bort undertexten i scen 2. | 600,6 |
| Flytta scen 7 först. | 471,6 |
| Duplicera scen 3 med ljud. | 511,5 |
| Korta scen 5 med 0,2 sekunder. | 640,6 |
| Dölj hela bord- och matkortet i scen 5. | 396,9 |
| Byt bakgrunden i scen 1 till glassbar S1. | 532,4 |

Alla tio tillämpades; median enligt den tidigare mätningens lägre mittvärde 503,2 ms
(vanlig median av de två mittvärdena 507,4 ms), max 897 ms. Två nya kontroller gav
rätt textbyte och glassbarbyte, inklusive ångra, på 1 416 respektive 631,9 ms.
Ensekundsmålet hålls alltså inte alltid. Totalt 24 Jev-anrop i uppgiftens liggare,
varav fyra nya i denna återupptagning; budget 600. Inga fler nätanrop gjordes.

## Del 3: miljöer

Banken innehåller 13 plåtar från tre miljötyper: sju charkbutik, fem snabbmatsdisk,
en glassbar. Källor är b-tilltal-ravara-tagningar, a-sketch-servering-tagningar och
kand-kennysgelato-tagningar under scen/3d/ingest/ut/. Platsbeskrivningar kommer från
scen/3d/kontrakt/semantik/ut/{b,a,kenny}/semantik.json och är modellbedömda.
Rörliga kameror och olämpliga detaljbilder har uteslutits. Det finns ingen riktig
foodtruck-plåt; chatten ska inte lova en tillgång som saknas.

Bakgrunden är ett bakre plant kort, inte ett nytt uppmätt rum. Ursprungliga personer
och bord behåller sina djup. Horisont/golv och skalning är antagna och står i manifestet.
Aldrig sedda bakgrundspixlar och borttagen källtext fylls lokalt med inpainting.
PNG/JPEG/WebP kan släppas i chatten och sparas lokalt som ytterligare bakgrund.
Uppladdningsvägen är kodgranskad men har inte provats på nytt i återupptagningen.

miljobyten.png visar s1 och s7 i snabbmatsdisk och charkbutik med ändrad kamera.
Jag har tittat på bilden: miljöbytet läses, men plåtarna är utdragna och utsmetade,
särskilt charkbutiken. Bordens kontakt med det nya rummet är en kompositionsgissning.

## Del 4: levande ansikten och händer

viewer.js projicerar aktuell avkodad källruta med originalets mätkamera på den
poserade kroppen. Synlighetsmask, bildgräns och en separat djupbuffert från
källkameran avgör var levande RGB får användas; annars används den fusionerade
texturen. Mätkameran ändras inte när CM flyttar renderkameran.

Tre dynamiska plana kort reparerar huvud/hår och de två underarmarna/händerna.
Djup kommer från lederna; konturerna är antagna och begränsas av personmasken.
Huvudets referenskontur följer huvudleden och förfinas per ruta med lokal GrabCut.
Det finns ingen ny fingergeometri. Händer i den grova maskens hål kan fortfarande saknas.

Möjligt handhållet förgrundsinnehåll hittas nära vardera handen och följs med lokal
LK-optiskt flöde. Det måste stämma med handledsrörelsen: medianrest < 6 px,
p90 < 12 px och handledsförflyttning > 4 px. Gränserna är antagna, inte kalibrerade.
I detta paket accepteras bara vänster hand i s5: medianrest 2,73 px, max 6,85 px,
minst 38 följda punkter. Dess pixlar läggs till handmasken även utanför personmasken
och tas bort ur det frusna kortet. Ingen scenkod eller burgarpolygon finns i live.py.
Den äldre refine.py har fortfarande manuellt granskade klippspecifika förgrundskonturer;
dessa är dataantaganden och begränsar generaliseringen till klipp b.

Dubbelundertexten är rättad: källans tidsatta textrutor med 12 px marginal spärras
både i kroppsshadern och efter all sammanslagning av kortmasker. Bara det separata
redigerbara textlagret skriver undertext. Det lämnar ibland hål eller frusna/inpaintade
remsor där originaltexten dolde handen eller maten. 304 aktiva textrutor kontrollerades
mot alla tre alpha-kanalerna. undertextkontroll.png har textlagret av i sju scener;
jag har tittat på den och ser ingen läsbar kvarvarande dubbelundertext.

Ett fel i den avbrutna versionens bildfångst upptäcktes visuellt: videosök kunde
vara klart innan Three.js laddat den nya rutan till GPU-texturen. Bilder kunde då
visa föregående scen på personen. seeked och den explicita sökvägen markerar nu
videotexturen för uppladdning; fångsten väntar också medan video.seeking är sant.
De slutliga jämförelsebilderna är tagna efter rättningen och visuellt kontrollerade.

Vid ändrad replik tystas det blandade originalljudet i luckan, och undre ansiktet
använder frusen referenstextur i stället för levande mun. Ändringen anges i chatten.
Läppsynk till ny replik kräver en separat tal-/ansiktslösning. Inget nytt tal skapas.
Trimning, flytt och kopiering behåller källrutornas ordning lokalt; ingen retiming.
Vid sökning eller mer än 45 ms videoskillnad används frusen textur tillfälligt.
Det är ingen garanti om exakt läppsynk på varje visningsruta under uppspelning.

### Kostnad och paket

Sista korta kontrollen, resume-check.json, 75 rAF-prov per läge under uppspelning:

| Mått | Resultat |
|---|---:|
| Live, JS + render till gl.finish(), median / p95 | 1,2 / 1,9 ms per bild |
| Fruset, samma prov | 1,5 / 3,3 ms |
| Levererad rAF-kadens, live / fruset | 61,1 / 58,2 per sekund |
| Live aktiverat / avkodade källintervall i liveprovet | 74 av 75 / 38 olika källrutor |
| Paket laddat i viewer-modulen | 1 490,5 ms |
| Browserfel / otillåtna externa försök | 0 / 0 |
| Hela paket/, inklusive bakgrunder och schema | 17 640 844 byte, 17,64 MB, 16,82 MiB |
| Enbart paket/notan/ | 17 090 604 byte |
| Sista live-maskpasset, alla 383 källrutor | 15,96 s offline |

Mätningen gjordes med Chromium/ANGLE på befintlig Intel UHD 620, utan separat GPU
eller tunga lokala jobb från denna agent. gl.finish omfattar JS, render och aktuell
texturuppladdning; webbläsarens asynkrona videoavkodning mäts inte separat.
De korta proven och grannjobbets last ger brus: live är inte bevisat billigare än
fruset trots siffrorna i sista provet. Ett tidigare kort prov gav 0,6 / 1,2 ms live,
0,5 / 1,0 ms fruset. Ingen tillförlitlig separat merkostnad kan räknas ur dessa prov.
Källrörelsen är 30 fps; visningen är ungefär 60 fps. Ingen bildgenereringstjänst används.

### Vad jag faktiskt ser

ansikte-fore-efter.png visar källruta 18 och 54 med samma utsnitt före/efter:
munformen ändras mot källan i live, och händerna är sammanhängande där den frusna
versionen visar sönderbrutna trianglar. Hårkonturen är bättre än i det avbrutna
liveförsöket, men den har fortfarande ljusa väggfransar och kantiga avklipp.

hand-fore-efter.png visar ruta 262 och 274: fingrar och greppet om burgaren blir
betydligt mer begripliga. Det löser inte greppgeometri. Remsan över burgaren är
frusen eller inpaintad; underarmar har sömmar och statiska matkort behåller hål.
Vid 12 cm sidoflytt och 8 cm närmare kamera hålls situationen ihop, men pappersytor,
hand-/ärmskarvar och felaktig skymning syns tydligare. Vissa kortkanter blir sämre
än med en stilla källa. s6 har fortfarande stora hål över bord/mat. Detta är ännu
inte en fritt omformbar 3D-scen.

Titta först på bilder/ansikte-fore-efter.png, bilder/hand-fore-efter.png och
bilder/oversikt.png. Översikten är omtagen; föregående finns i
bilder/v4/oversikt-before-resume.png. chatt-tre-exempel.png bygger på de tidigare
chattprovens bilder och är märkt så, inte en ny mätning av liveversionen.

## När kropparna i scen/3d/ingest/ut/ ändras

Den enda namngivna ingången för kropparna är body_source.py:
load_body_source() läser den frusna paketplanen; full export väljer BODY_PLAN.
read_body_raw() läser Blenderutdragets pos, ids, weights, tri, matrices och visible.
body_rig_names() läser riggnamnen. export.py, export_blender.py, refine.py och live.py
använder denna gräns. Nyextraherade råfiler i paketet prioriteras före gamla intermediat.
body-dependencies.json räknar upp de konkreta ingångarna för nuvarande Notan:

- scen/3d/kontrakt/ut/notan/jamn_tom/plan.json och scen.blend, som måste höra ihop.
- scen/3d/kontrakt/tro_rigg.json.
- scen/3d/ingest/ut/notan-tagningar/S1–S7/varld.npz, sekvens_1.npz,
  masker.npy och personer.json, via scen.varld och person.rorelse i planen.
- Källvideon anges i plan.kallvideo. world-metadata.json innehåller frysta repliker,
  kortbindningar och bakgrundsposter; pipeline/base-regi.json ger källrevisionen.

En ny ingest ensam uppdaterar INTE den gamla scen.blend. Vänta tills grannjobbet
har levererat en ny matchande plan och scen.blend. Om deras plats ändras, ändra
BODY_PLAN i body_source.py; BODY_BLEND följer samma mapp. Vid nya ben-/lednamn
behövs adapter vid denna gräns och kontroll av huvud-/handledsnamnen i refine/live.
Det är inte verifierat mot den nya kroppsmodellen. Kör INTE följande medan
grenjobbet arbetar. Detta är framtida ombyggnadskommandon, inte körda här:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
# Kräver den nya färdiga planen + motsvarande scen.blend. Startar Blender:
scen/.venv/Scripts/python.exe -B forvarld/varld/export.py
scen/.venv/Scripts/python.exe -B forvarld/varld/refine.py
# Behövs när även bankklippens masker/ingest ändrats; annars kan banken återanvändas:
scen/.venv/Scripts/python.exe -B forvarld/varld/venues.py
scen/.venv/Scripts/python.exe -B forvarld/varld/live.py
# Med servern igång:
node forvarld/varld/capture-v5.mjs --pictures-only
scen/.venv/Scripts/python.exe -B forvarld/varld/compose-v5.py
scen/.venv/Scripts/python.exe -B forvarld/varld/verify-light.py
node forvarld/varld/resume-check.mjs --no-chat
```

export.py --reuse-raw återanvänder GAMLA kroppar och är därför fel kommando efter
kroppsbyte. refine.py --layers-only uppdaterar bara kort, inte kroppens texturfusion.
upgrade.py är ett historiskt engångsskript som skriver över viewer.js; kör det inte
för ombyggnad. export.py bevarar nu chattens semantiska fält via world-metadata.json.
Om semantik eller scen-id ändras måste metadata, chat.mjs frysta klipptillstånd och
pipeline/base-regi.json synkas mot den nya källan. Om offlinekompilering behövs igen
måste även den privata pipeline/snapshot/ och kalla.json byggas om; de innehåller
531 frysta äldre mätfiler. prepare_pipeline.py är den gamla vägen och importerar
kontraktskod; den kördes inte här och måste granskas efter modellbytet.

## Varför kompileringen tog 95 sekunder

server.mjs /api/compile startar en NY Pythonprocess med kompilera.py för varje edit.
Den sparade mätningen var 94 765 ms totalt, 94 741 ms kompilering/I/O.
Den separata sparade cProfile-filen pipeline/compile-profile.bin innehåller:

- 73,901 s totalt, 73,051 s i kompilera().
- kvalitet.komplettera(plan, PL): 63,431 s.
- Därav kroppmatt.matt_plan → _matt_plan_utan_cache: 55,427 / 55,345 s.
- 684 anrop till kroppmatt.fyll: 37,121 s; cv2.fillPoly ensam 27,182 s.
- trohet.mat(plan): ytterligare 8,689 s; skymning.los: 7,977 s.

Jag har läst profilen, inte kört om diagnoserna. Dagens kod anropar fortfarande
kompilera.py:588 trohet.mat, :591 kvalitet.komplettera och :604 trohet.rapport.
Kroppsmåttets cache är bara processlokal; den försvinner när endpointen startar om
Python. Diagnosmodulernas fingeravtryck matchar profilen, men kompilera.py har
ändrats av annat arbete sedan dess. Exakta nya körtider är därför inte uppmätta.

Ingen befintlig CLI-flagga hoppar över diagnoserna; bara --platsbank finns.
Den minsta ändringen som tar bort huvudflaskhalsen är en flagga som kringgår
kroppmatt.matt_plan-anropet i kvalitet.komplettera. Det sparar cirka 55 s i profilen,
men lämnar cirka 18 s och når alltså INTE en sekund.

För en verklig snabb förhandskompilering behövs exempelvis --utan-diagnostik,
vidarebefordrad till kompilera(), som hoppar över trohet.mat, de tunga kvalitetsmåtten
och trohet.rapport samt markerar kvalitet som ej kontrollerad. Viktig detalj:
komplettera är inte bara rapportering: skymning.los ändrar plan.objekt och funktionen
kan sätta skyddade_knan. Att bara hoppa över hela funktionen ändrar alltså planen.
Dessa beslut måste separeras eller återanvändas från en giltig fryst grundplan;
kontroll av schema, referenser och hashar ska vara kvar. Under en sekund är inte
bevisat för den föreslagna flaggan. Ingen sådan ändring gjordes här.
Den redan fungerande snabba vägen är webbläsarens reducerare.

## Inte gjort

Klipp b är uppskjutet; ingen Blenderexport, ny kroppsmodell eller full ombyggnad
har verifierats. Ingen ny filmexport, talgenerering, fullständig läppsynk, finger-
eller kontaktgeometri. De gamla manuella förgrundskonturerna är inte generaliserade.
Inga nya tunga tester eller tjänster har körts. Fortsättningsläget och exakta körda
kommandon finns i VARLD3-LOGG.md. Tidigare README är bevarad i history/resume-before/.
