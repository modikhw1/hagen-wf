# Notan: förvärld med chatt och levande källtextur

Uppdaterad 10 november 2026 (kväll): snabbvägen genom kontraktets kompilator är nu
kopplad till webbvärlden, se avsnittet ”Snabbvägen: ändring, visning, kompilerad plan”
längst ned i denna fil och SNABB-LOGG.md. Texten däremellan är från föregående omgång;
avsnittet ”Varför kompileringen tog 95 sekunder” är historiskt och ersatt.

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
äldre långsamma offlinevägen (ny Pythonprocess, full diagnostik); varken chatten eller
knapparna anropar den. Bakgrundskompileringen går i stället via POST /api/kompilera.
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

## Varför kompileringen tog 95 sekunder (historiskt, åtgärdat av snabbvägen)

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

## Snabbvägen: ändring, visning, kompilerad plan

Uppdaterad 10 november 2026. Tre mått skiljs åt: M = mätt av mig denna kväll,
K = läst i kod, B = bedömt.

### Så går en ändring, steg för steg

1. (K) Chatten eller en knapp skapar en eller flera regi-edits. viewer.js:applyEdits
   kör edits.mjs:apply på webbläsarens tillstånd, bygger om och ritar. Det är det
   som visas, och det tar 6–93 ms. Kompilatorn är inte inblandad här.
2. (K) rebuild() i viewer.js anropar sist kompileraBakgrund(). Den skickar hela
   edit-listan till POST /api/kompilera och får ett löpnummer direkt tillbaka.
   Varje tillståndsändring går genom rebuild(): ny ändring, ångra, återställ och
   sidladdning (sparad regi i localStorage). Ångra skickar alltså den kortare listan.
3. (K) server.mjs lämnar listan till kompilator.mjs, som lägger den som väntande jobb.
   Kommer en ny lista medan en kompilering pågår behålls bara den senaste.
4. (K, M) En enda Pythonprocess, kompilator_demon.py, startas när servern startar och
   importerar kompilera.py en gång. Den anropas som kompilera(kalla, regi, snabb=True)
   för varje lista, mot pipeline/kalla.json och regi = pipeline/base-regi.json plus
   edit-listan. Servern kompilerar en grundplan utan edits vid start (uppvärmning).
5. (K) Svaret är en sammanfattning av planen: tidskarta, källrutor, scener, skärmtext,
   kamera, tillämpade och ej tillämpade edits. kompilator.mjs kör sanning.mjs, som
   återskapar webbläsarens tillstånd med samma reducerare och jämför fält för fält.
6. (K, M) Webbläsaren väntar asynkront (long poll mot GET /api/kompilering) och skriver
   statusraden: ”kompilerad: ja, 557 ms (kompilator 533 ms), avvikelser: 0 av 11
   kontrollerade fält”. Hovring visar varje avvikelse. Visningen väntar aldrig på detta.
7. (K) Varje kompilering och varje avvikelse loggas i logg/kompilering.jsonl.
   Knappen ”Kvalitetskontroll” anropar POST /api/kvalitetskontroll. Servern sparar
   senaste snabba plan, startar en andra Pythonprocess som kör
   diagnostik.diagnostik() (samma funktion som diagnostik.py) och frågar GET
   /api/kvalitet var sekund. Redigering fortsätter under tiden (M, se nedan).

Vad som räknas var: webbläsaren räknar tidskarta, källrutor, text, kamerapose, kort,
bakgrund, ton och ångra (edits.mjs, viewer.js). Server.mjs räknar inget, den lägger
bara över. Kompilatorn räknar byggplanen: upplösta scener och tidskarta, text,
kamera, rum, föremål, skymning, höjdpassning och tal. Kompilatorn ritar inte.

Cachen för den långlivade processen ligger i pipeline/cache (och pipeline/cache_tal
för Piper). Den läggs dit genom att kompilator_demon.py sätter datacache.CACHE och
TAL_CACHE före import. Inget skrivs under scen/ av denna process; kompilatorn är
inte ändrad. Ett tal-cacheprov skrevs dock under scen/3d/kontrakt/ut/notan/tal_cache
av ett av mina tidiga prov (två filer, 17:12 UTC) innan omdirigeringen fanns.

### Tider (M, i7-8650U, 16 GiB, Chromium och ett Modal-grannjobb igång)

| Läge | trim | text | föremål | ta bort scen | byt replik (Piper) |
|---|---:|---:|---:|---:|---:|
| Kall: ny process, tom cache | 5,8 s | 6,5 s | 6,4 s | 7,2 s | 12,9 s |
| Varm i ny process (inkl. start och import ca 0,2 s) | 0,76 s | 0,80 s | 0,81 s | 0,80 s | 0,80 s |
| Varm i långlivad process (mediantid, fem körningar) | 0,36 s | 0,36 s | 0,35 s | 0,35 s | 0,36 s |

Källa: snabb-tider.json (node forvarld/varld/snabb-mat.mjs tid). Sanningskontrollen
ensam tar 1 ms. Målet under 300 ms nås inte: 345–362 ms. Delar av tiden (M, utan
profilerare): kontraktets källkontroll i kompilera() tar 154 ms, varav 82 ms är
sha256 över 85 mätfiler vid varje anrop. Resten är bygget av planen. Ingen del av
detta ligger i min kod; att minnesbunda hashningen i kompilatorn efter filstämpel
vore det första att pröva (B).

Viktigt, och sämre än rubriktalen: de 0,35 s gäller bara edits som inte ger kompilatorn
ett nytt tidsurval. En ny trimning, en ny borttagning, flytt eller kopiering av scen
ger cachemiss i skymningsbeslutet (skymning.los, 7 av 7,7 s i cProfile) även i den
långlivade processen (M, samma process, nya värden):

| Ändring | Tid |
|---|---:|
| trim s3 till 5,45 s (ny) / 5,35 s (ny) / 5,35 s igen | 8,2 s / 7,9 s / 0,45 s |
| trim s4 till 8,0 s (ny scen) | 6,6 s |
| ta bort s4 / ta bort s3 (nya) | 2,5 s / 5,3 s |
| flytta s5 efter s6 (ny ordning) | 6,1 s |
| text i s4 (ny text, samma tidsurval) | 0,37 s |

Det betyder att en CM som drar i en trimning får ”kompilerar…” i 6–8 s för varje nytt
värde, inte en halv sekund. Webbvisningen berörs inte. Åtgärden ligger i kompilatorn
(skymningsbeslut per scen och ruta i stället för per hela tidsurvalet); jag har inte
ändrat den. Se SNABB-LOGG.md, avsnitt Fel.

Chatt hela vägen (M, logg/chatprov-snabb-*.json, 12 Jev-anrop, sex meningar, fem
ändringar och en osäker fråga med tre knappar, plus fem ångra): mening till visad
ändring 460–690 ms (Jev står för det mesta). Från visad ändring till kompilerad plan:
0,6–0,9 s för text, bakgrund, kamera och scenborttagning (kompilatorn var här
långsammare än i ensamt läge, 0,56–0,87 s, eftersom Chromium renderade samtidigt)
och 8,2 s för ”Korta scen 5 med 0,2 sekunder” (nytt tidsurval). Hela vägen
mening → kompilerad plan: 1,0–1,5 s, men 8,9 s för trimningen. Ångra: 0,5–0,7 s till
kompilerad plan. Planen efter ångra hade 0 avvikelser i alla fem fall.
”Dölj hela bord- och matkortet i scen 5” gav tre knappar i stället för en ändring
och ingen kompilering av ändring.

Kvalitetskontroll (M): 66,0 s första gången (kall diagnostikcache), 10,4 s när
kroppsmåttcachen var varm. Under de 66 s tog två kompileringar 0,47 och 0,88 s, så
redigering blockeras inte. Resultat för oredigerad Notan: bildtrohet flaggad,
1 av 7 person-scener över gräns, skymning 1 av 28 delar flaggad. Det är kontraktets
egna trösklar, inga ägarkrav.

### Sanningskontroll: webbläsaren mot den kompilerade planen

Körd med node forvarld/varld/snabb-mat.mjs sanning (logg/sanning-*.json), femton
fall. Webben = edits.mjs:apply. Kamerans webbvärden räknas om med samma formel som
viewer.js:tripodKey (läst i kod; webbläsarens renderade pose jämfördes inte pixel för
pixel). ”Stämmer” betyder lika i alla kontrollerade fält för fallet; fälten är
scenordning, ut- och källintervall per scen, källrutornas ordning, ljud per scen,
vilka texter som finns och deras text, start, slut, ruta, box och storlek, samt
kamera, föremål, miljö, helkroppston, rollnamn och replik när fallet rör dem.

| Ändringstyp | Resultat |
|---|---|
| trim (klipp_slut) | stämmer, 11 av 11 fält |
| text byt / ta bort | stämmer |
| text lägg till | skiljer: standardstorlek 27 px i webben, 30 px i planen |
| föremål, dölj kort (ta_bort_prop) | stämmer semantiskt: samma id och scen, men olika sak. Webben döljer ett fotokort (bord och mat), planen tar bort en 3D-låda med samma id |
| föremål, byt kort (byt_prop med tillgang_id) | kan inte uttryckas: kompilatorn avvisar ”Extern proptillgång är reserverad” (edit ej tillämpad) |
| lokalbyte (byt_miljo, webbens plåtar b_*, a_*, kenny_*) | kan inte uttryckas: platserna finns inte i kontraktets platsbank (rumsmall/); samma gäller egna uppladdade bilder (B) |
| kamera (stativ, närmare B) | skiljer: brännvidd ×1,12 i webben, ×1,374 i planen; avstånd från uppmätt kamera 0,14 m mot 0,50 m |
| kamera (stativ, ”hel”) | skiljer: webben ×0,88, planen ×1,374 (samma som ”nära”; B: planen ignorerar inramning när mål saknas, ej utrett) |
| helkroppston + rollnamn (casta) | stämmer: färg och roll |
| ta bort / flytta / duplicera scen | stämmer. Obs: efter duplicering har två texter samma id (st1 i s1 och s1_copy) i både webb och plan |
| byt replik | skiljer: kompilatorn syntetiserar tal med Piper (12,9 s kall) och byter också undertexten till nya texten. Webben tystar originalet, fryser munnen och behåller gamla undertexten |
| ångra | stämmer: alla sanningsrader lika före ändring och efter ångra, i spårfallet och i fem chattfall |
| sammansatt (trim + text + ta bort scen) | stämmer |

Ändringar webben kan göra som kontraktet inte kan uttrycka (M för de två första,
K för resten): byt kort med tillgang_id, plåtbakgrunder, och alla visuella lager som
bara finns i webben (levande ansikte och händer, pappersteaterkort). Omvänt (K, läst
i schema och kompilera.py, inte körda): kontraktet har trimning med tidssträckning
och händelseankare, lägg till scen, flytta och lägg till föremål ur propbanken, lägg
till replik, rörelse, uttryck och rösttempo. Webben avvisar tidssträckning med
meddelandet ”saknar förhandsvisning”.

Avvikelserna visas i statusraden som antal, med detaljer vid hovring, och finns i
logg/kompilering.jsonl (typ kompilerad, fältet avvikelser) och i logg/sanning-*.json.

### Kommandon

```powershell
$env:PYTHONIOENCODING='utf-8'
node forvarld/varld/server.mjs                 # startar också kompilatorprocessen
node forvarld/varld/snabb-mat.mjs tid          # tider, skriver snabb-tider.json (ca 70 s)
node forvarld/varld/snabb-mat.mjs sanning      # sanningskontroll, skriver logg/sanning-*.json
node forvarld/varld/ui-snabb-check.mjs         # statusrad och kvalitetsknapp i riktig sida (servern igång)
node forvarld/varld/chat-snabb.mjs             # sex meningar, 12 Jev-anrop, servern igång
```

Nya filer: kompilator_demon.py, kompilator.mjs, sanning.mjs, snabb-mat.mjs,
chat-snabb.mjs, ui-snabb-check.mjs. Ändrade (säkerhetskopior i history/fore_snabb/):
server.mjs, viewer.js, index.html, README.md.
