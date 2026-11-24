# Notan: förvärld och PS2-rendering i samma webbläsarscen

Detta är ett lokalt prov på ett enda klipp, inte en färdig produkt. Sju tagningar,
383 källrutor vid 30 fps, ljud, skärmtext, uppmätta kroppsrörelser och kameror.
Allt som detta prov skriver ligger under `forvarld/varld/`. Inga installationer,
modellservicer, nätanrop eller nedladdningar behövs.

## Vad som redan fanns och vad återupptagningen gjorde

Första körningen hade exporterat 1 800 trianglar per personinstans, sju binärfiler,
animation, texturer från en referensruta, medianplåtar, synlighetsmasker och ljud.
Visaren, tre direktändringar, endpointen och fångstskripten fanns. Sju jämförelseblad,
översikt och fyra rörelseremsor fanns. En privat kopia av mätdata hade hunnit skapas.
Den sparade mätningen saknade pipeline-resultat; den gamla felloggen visade inaktuella
hashar. README och film saknades.

Återupptagningen verifierade laddning och omfångst, körde den verkliga kompilatorn
framgångsrikt via endpointen och mätte hela ändringen. Den lade till flerbildsfusion,
synlighetskontroll, märkning av osedd texturyta, kroppsregionsvis fyllning, huvudfästa
källkort, förgrundskort, separat närbord i s7, modest ändrad kamera, jämförelse av
renderlägena i 1:1, uppdaterade rörelseremsor, film, denna dokumentation och slutmätning.
Tidigare bilder finns i `bilder/v1/`, `v2-textur/`, `v3-huvud/`, `v4-lager/`.
Kod och mätningar från starten finns i `history/`.

## Kör från projektroten

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
node forvarld/varld/server.mjs
```

Öppna http://127.0.0.1:5195. Spela/pausa, dra tidsreglaget, jämför källan bredvid.
Ljudet kommer från originalet. PS2/vanlig, plåt/mall, mask, huvudkort och pappersteater
kan slås av var för sig. Kameraknappen ändrar aktuell scen; plåten ersätts då av
mallrummet. Färgknappen tonar A, textknappen ändrar text i s1. Återställ återställer
tidslinje och ändringar. Textändring är grafisk; den ändrar inte tal eller munrörelse.
Pappersteater använder källans bord/mat framför personen i mallvyn.

Porten är en enkel Node-server på loopback, inte Vite. Three.js 0.187.0 läses från
befintlig `video/node_modules/three`; Playwright Core från `app/node_modules`.
Ingen webbsida eller tjänst utanför 127.0.0.1 används under fångsten.

## Exportera och fånga igen

```powershell
# Återskapa plåtar och ursprungliga texturer ur befintliga råa skinningdata:
scen/.venv/Scripts/python.exe -B forvarld/varld/export.py --reuse-raw
# Ersätt sedan texturerna med flerbildsfusion och bygg alla källkort:
scen/.venv/Scripts/python.exe -B forvarld/varld/refine.py
# Servern måste köras. Standard kör även verklig pipeline och 6 s filmrutor:
node forvarld/varld/capture.mjs --layered
scen/.venv/Scripts/python.exe -B forvarld/varld/compose.py --layered
```

`--reuse-raw` läser paketets sparade plan så att senare ändringar i grannjobbet inte
kopplar ihop nya kameror med gamla kroppar. Rådata ligger i `intermediat/`.
Full ny Blender-export: kör `export.py` utan flaggan, sedan `refine.py`. Det läser
den aktuella planen och dess befintliga `scen.blend` i `scen/3d/kontrakt/ut/notan/jamn_tom/`.
De två måste fortfarande höra ihop; en andra version av klippet behöver en egen
anpassning av sökvägarna. Exporten använder två Blender-trådar. Processvakten väntar
30 s mellan kontroller om någon headless eller okänd Blender finns. GUI-sessionen
används aldrig. Inga andra processer stoppas. Exporten sparar ingen `.blend`.

Snabb bildomtagning utan pipeline/film: `capture.mjs --layered --pictures-only --no-mp4`.
En full bild- och prestandakörning utan kompilering: `--layered --skip-pipeline`.
Enbart kort och rumsklarering: `refine.py --layers-only` (återanvänder texturer).
`CHROME_PATH` kan peka på en annan redan installerad Chromium. Standard är den lokala
Playwright Chromium-installationen. Profil och cache ligger i `browser-profile/`.
`--software` väljer SwiftShader uttryckligen; de rapporterade slutmätningarna använder GPU.

## Paketformat och ursprung

`paket/notan/manifest.json` är ingången. Varje person har en egen `.bin`:
icke-indexerade float32-positioner, fyra ledindex, fyra vikter, UV och sedan alla
126 leders kolumnlagrade 4×4-skinnmatriser per ruta. Skelettets vilomatriser och
lednamn finns i `meshes.json`. Det är ett eget format, inte glTF.
Varje instans har exakt 1 800 trianglar, totalt 12 600 lagrade men bara 1 800 aktiva
samtidigt. Det är en billig, tydligt kantig budget för mobil porträttbild.
Decimering sker i viloposen; de fyra största vikterna normaliseras. Benmatriser och
benlängder från den redan byggda planen ändras inte. Flerbildspasset återställer
originalets exporterade mesh och tar bort den tidigare provisoriska skalpförskjutningen.

Varje textur är en 512×512 triangelatlas. 9–11 rutor från respektive tagning projiceras
på den poserade ytan. En färg accepteras bara inne i målpersonens mask och bild,
på en framåtvänd yta, inom 14 mm från kroppens egen främsta djupbuffert och utanför
skärmtext. Det täcker självskymning från armar/händer. Referensrutan prioriteras
på ansiktet; andra rutor fyller ytor som faktiskt sågs då. Atlasens per-texel-färg
väljs från den bästa accepterade rutan; ingen påhittad ansiktsdetalj genereras.

Maskerna är grova, 144×256, och kan räkna mat som person. Därför används dessutom
granskade konturer för bord/mat, mörk-kläd-filter och ett hudfärgfilter. Den hållna
burgarens region i s5 utesluts särskilt från kroppstexturen. Dessa filter och
handgranskade konturer är antaganden, inte perfekt objektsegmentering. Små fel vid
händer, ärmar och maskkanter kan återstå. Se `*-layer-audit.png` och manifestet.

`*-observed.png` är vit endast där atlasens yttexel verkligen fick en accepterad
källfärg; svart betyder antagen eller atlasens utfyllnad. Andelen antagen yta räknas
bara över triangelinteriörer, inte tom atlas. Osedd yta får närmaste observerade färg
från samma kroppsregion. Saknas observerade ben helt används enfärgat mörkt tyg från
personens överkropp, något mörkare. Detta säger inget om de verkliga byxorna eller ryggen.

Medianplåtarna är 288×512. Varje tagning använder sina rutor med personer bortmaskerade.
Aldrig sedda bakgrundspixlar fylls från närmaste observerade pixel och är antagna.
Den animerade synlighetsmasken ligger i en atlas med 144×256 per ruta och används
bara i oförändrad plåtvy. Det är en hybrid bild/3D-komposition, inte återbyggd skymning.
I s4 är endast servitören en 3D-person; den sittande åskådaren finns kvar i plåten.

Huvud/hår/keps är källutsnitt vid tagningens mittruta. Alpha förfinas lokalt med
GrabCut och källans mask, sedan följer kortet den uppmätta huvudleden. Ansiktsuttryck
och hårform är frusna; kortet ersätter inte en skannad identitet eller en 3D-frisyr.
Huvudet skymmer inte sig självt rätt vid en stor vridning.

Pappersteatern använder ett kameravänt, genomskinligt förgrundskort vid ett antaget
bordsdjup 22 cm framför torsot, placerat genom källkameran i platsens koordinater.
Konturen och den inverterade personmasken skiljer bord, mat, dryck och burk från kroppen.
I s7 finns ett separat närbordskort på 28 % av fjärrbordets kameradjup. s5 har ett
granskat utsnitt för den hållna burgaren. Källkorten är 576×1024 RGBA; helt transparenta
pixlars RGB nollas för mindre filer. De är fasta mittrutebilder. Handhål, grepp,
kontakt och föremålens baksidor rekonstrueras inte. Mallens bord döljs när korten används
för att undvika dubbla bord som skär genom källkortet.

Kameraprovet flyttar stativet 12 cm åt höger och 8 cm närmare, i kamerans lokala axlar,
med samma riktning och lins. Relativ parallax uppstår genom verkliga olika kortdjup.
Det återstår glapp vid grepp och kortkanter redan vid denna måttliga ändring.
Större kameraflytt, höjdändring och rundning bakom personer avslöjar pappersytorna.
Ett huvudkort och förgrundskort är 2,5D, inte nya mätningar av rum eller objekt.

Golv, väggar, stolar och övrig inredning är planens enkla mall. Per scen flyttas
kolliderande golv/vägg/stoldelar bort från meshens hörn vid sju provposer, med 3,5 cm
marginal (golv 2,5 cm). Ändringarna är uttryckliga `roomAdjustments` i manifestet.
Det är en konservativ kontroll av hörn mot lådor, inte kontinuerlig kollisionsfysik.

## PS2-läge och mätmetod

PS2 renderar internt i 192×342, uppskalning till 576×1024 med närmaste granne, ingen
kantutjämning. Vertexpositioner snäpps till intern pixelgrid. UV interpoleras affint
i bildplanet. Fragmenten får plana normaler för enkel ljussättning. Efterpasset
kvantiserar RGB till 5 bitar per kanal med 4×4 Bayer-dithering. Textlagret går också
genom den låga upplösningen. Vanligt läge är 576×1024, perspektivriktig UV, ingen
vertexsnäppning, färgkvantisering eller dithering; samma texturer och grundljus.
Det är en vald retrobehandling, inte en exakt PS2-hårdvaruemulator.

`bilder/ps2-jamforelse.png`: samma ruta 93, samma scen och utsnitt, 384×480 pixlar per
sida utan omskalning av de sparade 576×1024-bilderna. Ansikte, krage och text visar
pixelsteget tydligt. Fotografiska kort dominerar ändå; stilen läses främst som
pixlad källvideo, särskilt i plåtvyn. Det är ännu ingen stark sammanhållen PS2-art direction.

De exakta slutvärdena finns i `measurements.json`, `refine-result.json` och
`export-result.json`. Tidigare resultat finns i `history/baseline-measurements.json`.
Laddtid mäts från viewer-modulens start tills alla efterfrågade paketresurser är klara;
inte ett kallt OS-cacheprov och inte samma sak som full videonedladdning.
`navigationToReadyMs` inkluderar i fångstskriptet också en avsiktlig paus på 1 s.
Renderprovet kör rAF + `gl.finish()` och rapporterar median/p95 samt levererade fps.
Det är GPU-färdig render plus JS/sökning, inte en separat GPU-timer. Spelprovet mäter
rAF-kadens med ljud och källvideo. Animationens källa är fortfarande 30 fps.
Ändringstid börjar i knappens händelsehanterare och slutar vid nästa rAF efter
`gl.finish()` på ändrad bild. Det mäter inte skärmens fysiska scanout.

Första kontrollen i denna återupptagning: 334 ms paketladdning, ungefär 60 fps på
Intel UHD Graphics 620 via ANGLE/D3D11, 0,5 ms median / 1,2 ms p95 för PS2-provet.
Färg 7,8 ms, text 6,0 ms, kamera 10,6 ms. Pipeline 71 083 ms, varav kompilator/I/O
71 061 ms. Dessa är äldre kontrollvärden; slutmätningarna nedan gäller slutpaketet.

### Slutmätning, 10 november 2026

| Mått | Resultat |
|---|---|
| Paket på disk, inklusive källvideo och revisionsplan | 16 021 556 byte = 16,02 MB = 15,28 MiB |
| Första körningens offline-export | 68,445 s (sparat originalresultat) |
| Sista fulla flerbilds-/kortpasset | 65,048 s |
| Slutligt pass för kortkanter/PNG-komprimering | 14,731 s |
| Paket laddat i viewer-modulen | 386,7 ms |
| PS2 med plåt, 180 provrutor | 60,34 fps; färdig render median 1,0 ms / p95 2,5 ms |
| PS2 med lager och mallrum, 180 provrutor | 60,12 fps; median 1,0 ms / p95 2,2 ms |
| Vanligt läge, 60 provrutor | 60,88 fps; median 1,2 ms / p95 3,3 ms |
| Uppspelning med ljud och källvideo | 60,01 rAF/s; median 16,7 ms / p95 16,8 ms |
| Färg, klick till nästa rAF efter ändrad bild | 9,1 ms |
| Text, samma mått | 6,4 ms |
| Kamera och lager, samma mått | 10,1 ms |
| Verklig pipeline, samma mått | 94 765 ms; kompilering/I/O 94 741 ms |
| Grafik | Intel UHD Graphics 620, ANGLE Direct3D11, riktig GPU |
| Browserfel / externa HTTP-anrop under fångsten | 0 / 0 |

Exporttiderna är separata offlinepass; summan är cirka 148,2 s, inte ett mätt
sammanhängande ombyggnadsprov. Tidigare experimentpass och väntan ingår inte.
Kompilatorn och maskinens övriga last kan förändras genom grannjobbet; slutmätningen
var långsammare än kontrollen. Profilens 73,9 s är ett separat prov. Originalkoden
har inte ändrats här; dess fingeravtryck finns i `pipeline/compiler-fingerprints.json`.

`verification.json` visar exakt likhet mot exporterade positioner, vikter, ledindex
och alla skinningmatriser, samt noll meshhörn inne i golv/vägg/stollådor över hela
animationen. Det verifierar inte all triangelintersektion eller kortens handkontakt.
61,4–84,2 % av kropparnas atlasytor är antagna; det stora värdet beror främst på rygg,
skymda ben och ytor under bordet. Observerad andel per scen finns i manifestet.
`bilder/ps2-6s.mp4` är verifierad till 6,000 s, 180 H.264-rutor, 576×1024, med AAC-ljud.
Fyra remsor (`rorelse-1.png` till `rorelse-4.png`) visar fyra på varandra följande
rutor, med plåt överst och lager/ändrad kamera underst.

## Verklig regi-endpoint

POST `/api/regi` tar ett komplett regi-dokument eller en edit i samma schema:

```json
{"id":"remove-s2","op":"ta_bort_scen","ursprung":{"typ":"cm"},"scen":"s2"}
```

Servern kör oförändrad `scen/3d/kontrakt/kompilera.py` med `-B`, ingen Blender.
Regi, plan, logg och svar sparas under `pipeline/`. Den privata källkopian pekar på
531 frysta filer (125 MB) under `pipeline/snapshot/`, och `kalla_omhasha.omhasha`
har kontrollerat dessa. `prepare_pipeline.py` kan bygga kopian från aktuellt exempel
igen; den modifierar inget original. Dess sista rapport hade inga ytterligare hashbyten
eller saknade filer. Den äldre felloggen gällde live-originalens inaktuella hashpekare.

Svaret innehåller tillämpade/avvisade edits, ny tidskarta, källrutor, scener och text.
Visarens provknapp tar bort s2: 383 → 342 rutor och utdata 73 visar källruta 114.
Ljud/källvideo söker efter den nya mappningen vid scenhopp. Kroppspaketet återanvänds.
Det är ingen generell adapter för godtyckligt ändrad geometri eller röstanpassning.
Varningar och avvisade edits kommer från den riktiga kompilatorn.

Kompileringen klarar INTE en sekund. Profilen `pipeline/compile-profile.bin` gav
73,9 s: 63,4 s i kompletterande kvalitet, varav 55,4 s i silhuettmätning; bildtrohet
ytterligare 8,7 s. Inget diagnostiksteg har stängts av för att få ett bättre tal.
En framtida snabb väg behöver giltig återanvändning av oförändrade mätningar och
en tydlig uppdelning mellan planändring och full kvalitetskontroll.

## Bedömning av bilderna

Alla sju rader visar rätt person och ungefär rätt gest/framing. A är kvinnan med
långt hår, B mannen i mörk piké, C servitören i svart keps och T-shirt.

- s1: ansikte och handgest känns igen; bord, burgare, mugg och burk finns i lagervyn.
  Svagast är händer mot ärmar och klippta föremålskanter vid ny kamera.
- s2: hår och piké känns igen. Pommes/pommeslåda och mugg ger situationen.
  Den hållna pommesen/greppet följer inte den nya geometrin; händerna är kantiga.
- s3: kvinnan och bordet känns igen. Händer/underarmar blir en trasig väv mot bordet;
  det läses som ett renderfel, inte avsiktlig stil.
- s4: kepsen gör rollen tydlig och bara servitören blir 3D. Åskådaren finns i plåten.
  T-shirtens armar och silhuett är för tunna/ojämna; mallvyn förlorar restaurangens miljö.
- s5: man, hår, piké och hållna burgaren känns igen bättre med korten.
  Den fasta burgaren och rörliga handen separerar vid ändrad kamera; kontakt är sämst här.
- s6: kvinnans hår och matbordet hjälper mycket. De låga händerna får fel skymning
  mot kortets hål, särskilt i den ändrade kameran.
- s7: helbildsgesten och två bord med burken överlever; två olika förgrundsdjup syns.
  Plana bordsytor och antagna avstånd avslöjas. Osedda ben är bara mörka standardben.

Samlat: plåtvy ger hög situationslikhet eftersom mycket är källbild. Lager gör
en liten kameraförändring begriplig och behåller viktiga saker, men händerna och
2,5D-kanterna hindrar detta från att vara en färdig omformbar scen. Kroppens baksida,
osedd klädsel och generiska ansiktsmesh är antagna; ingen ny mimik eller läppsynk.

## Nästa klipp och kvarstående arbete

Ett andra klipp behöver en motsvarande plan, mätkameror, masker, kroppar och ljud,
nya referensrutor samt granskade förgrunds-/huvudregioner. Inga modeller laddas ned
här. Ett klipp med rörlig kamera kräver stabila kameror, fler observationer per yta,
bakgrundsgeometri eller flera djupkort och validering över hela kamerabanan.
En förgrundshand måste få egen tidsberoende alpha/djup och rätt hand/objekt-bindning;
vår fasta kortmetod räcker inte. För större omscenering behövs riktiga props,
klädes-/hårgeometri och kontaktlösning. Full realtidsljudsredigering, generering av
nya uttryck och export till kundtidslinjen ingår inte i detta prov.
