---
id: 0025
titel: Relevanslistan per klipp, och färgkodade föremålslager ur bildmodellen
status: redo
från: orkestratorn (Fable), efter ägarens resonemang 13 nov förmiddag
datum: 2026-11-13
följer: 0024
tillåten_skrivning: [scen/3d/gennedbrytning/relevans/, scen/3d/gennedbrytning/fargkod/, scen/3d/gennedbrytning/STRATEGI.md]
---

Läs `delegat/kontext/malbild.md` först. Den är ny i dag och gäller alla uppdrag framöver.

**Ordning.** 0023 och 0024 saknar svar. Fal har slut på saldo, så deras videosteg står stilla. Gör så här: skriv svar för 0023 och 0024 med det som går utan fal (och säg vad som väntar på saldo), och gör sedan detta uppdrag. Punkt 2 i 0024 (disken som eget lager, rummet utan disk) görs **här** i del B i stället, som en av varianterna. Del A i detta uppdrag kräver ingen bildgenerering och kan börja genast.

## Mål
Två saker ska vara kända när uppdraget är klart:
1. Var och hur ingesten avgör **vad som är viktigt** i ett klipp, visat som en relevanslista för två klipp, framtagen utan ägarens input och sedan jämförd med ägarens egen läsning.
2. Om bildmodellen kan ge **föremålen** på samma sätt som den ger personen: isolerade och färgkodade så att kedjan lätt kan skilja vad som är vad och följa hur det rör sig, och vad det tillför utöver segmenteraren som redan finns.

## Bakgrund
Ägarens resonemang i dag:
- Personen isoleras nu med GPT Image i nyckelbilder och animeras med en videomodell. Frågan är om **samma teknik** ska användas för föremålen, eller om det finns något bättre.
- Före den frågan kommer en annan: **vilka** föremål. Förvärlden ska inte ha all detalj. Den ska ha det som gör att klippets mening lyser igenom, och det beror på konceptet: sketchens poäng, om mat visas, om bakgrunden visas. Den bedömningen måste ske på något stadium, och i dag vet ingen var den sker.
- Underlag för bedömningen finns redan på tre håll: appens innehållsbedömning (syfte, hur innehållet hänger ihop; inte komplett), klippets metadata, och det en modell själv kan läsa ur nyckelrutorna. Gemini provades delvis för just detta.
- När listan finns: be bildmodellen **färgkoda** föremålen, till exempel grön ton på disken, blå på vågen, gul på nästa. Då isoleras föremålet och blir samtidigt lätt för kedjan att känna igen och följa i 3D.
- Ägaren kan själv rendera över hundra bilder i ChatGPT. Det tar tid, så körningarna bör gå parallellt.

Det som redan finns, så att inget byggs två gånger:
- Kedjan placerar föremål och möbler (`kontrakt/foremallyft.py`, `mobellyft.py`, `handforemal.py`) och segmenterar på textprompt (`ingest/modal_segmentera.py`). Den bedömer **inte** hur viktigt något är och inte hur det rör sig.
- Deklarationen och briefen bär redan en del relevans (`ingest/ut/<klipp>/brief/`, `plats*/deklaration.json`, `ingest/ut/e-dialog-guacamole-tagningar/semantik/semantik.json`).
- Innehållsbedömningen: `data/analys/<konto>-<id>.json` (scener, klipp, kamera, händer, saker), `data/bedomningar/`, `data/bank/`, `video/src/forandring/` (motor, manus), `karta/videoforandring/`.
- Nyckelbilder av personen: `scen/3d/gennedbrytning/nyckel2/`, receptet i `CODEX-BILD.md`.

Orkestratorns hypotes, att pröva och inte att anta: segmenteraren räcker för det som **syns**. Bildmodellen tillför det som **inte syns** (diskens framsida, det som ligger bakom personen) och en gemensam namngivning över rutor. Om det stämmer är färgkodning värd sitt pris för skymda och delvis synliga föremål, och onödig för resten.

## Del A. Relevanslistan
Klipp: `kand-kennysgelato-tagningar` och `e-dialog-guacamole-tagningar`.

1. **Kartlägg underlaget.** En kort tabell: vilka fält i innehållsbedömningen, briefen, semantiken och metadata säger något om syfte och relevans, för de två klippen. Säg också vad som saknas (till exempel att `data/analys` inte har de här klippen, om det är så).
2. **Ta fram listan blint.** Ett steg som går att köra vid ingest: en modell som ser nyckelrutorna (kontaktbladen i `brief/`, eller rutor ur tagningarna) och får underlaget ur punkt 1 som givna fakta. Kör genom gatewayen som i `ingest/rum_video.py`. Spara prompten. Öppna inte `delegat/bilagor/0025/agarens-lasning.md` förrän listan är sparad.
3. **Formen**, `relevans/<klipp>/relevans.json`. Förslag, ändra om något bättre visar sig:
   - klippets **mening** i en eller två meningar: vad är poängen, vad ska en tittare förstå
   - en post per sak: `id`, `typ` (person, kroppsdel, föremål i hand, föremål, möbel, bakgrund, text, kamera), `roll` (`bär`: utan den faller poängen; `ramar`: paketerar scenen; `brus`: kan utelämnas), `varför` i en mening, tagningar där den syns, `samspel` (vad den rör eller står i förhållande till), `källa` (`matt`, `last`, `antagen`)
   - per post en **behandling**: eget lager i nedbrytningen, förenklad form (låda, plan, färgad vägg), bakas in i personen, eller utelämnas
   - koppla `id` till planens och deklarationens namn där de finns
4. **Jämför med ägarens läsning** i bilagan: vad träffade, vad missades, vad kom med i onödan. Kör sedan steget två gånger till och säg hur stabil listan är mellan körningar.
5. **Var i kedjan?** Högst tio rader: var steget hör hemma (före deklarationen, i den, eller efter), vad det behöver som indata, och vad nedbrytningen och handlingsspåret (0024) ska läsa ur det. Bygg inte in det i kedjan.

## Del B. Färgkodade föremålslager
Utgå från listan i del A (posterna med roll `bär` och `ramar`). Rutor: gelato S1 ruta 0, 55 och 112, och en ruta ur guacamole där baren och mobilen syns. Originalrutan in, ny session per bild, negativt formulerat där det går.

Varianter, samma rutor för alla:
- **V1, ton på plats.** Originalbilden oförändrad, men varje listat föremål får en platt, mättad ton (fast palett, en färg per `id`, samma i alla rutor). Inget flyttas, inget ritas om.
- **V2, ren id-karta.** Samma bild som platta färgfält utan textur: varje listat föremål i sin färg, allt annat neutralt grått. Personen i egen färg.
- **V3, ett föremål i taget.** Allt utom föremålet bort, föremålet hel och kompletterat där det var skymt (disken utan kvinnan framför, rummet utan disken). Detta är punkt 2 ur 0024.
- **V4, ton plus komplettering.** Som V1, men personen borttagen först (A-bilden ur `nyckel2/`), så att tonen också täcker det hon skymde.

Mät, per variant och ruta:
- **Går färgen att läsa av?** Tröskla tonen till en mask med ett enkelt skript. Blev det ett sammanhängande fält per föremål, eller läcker färgen?
- **Ligger bilden kvar?** Samma mått som i 0019–0020: hur mycket ritades om utanför föremålen, och hur långt flyttade kanterna (promille).
- **Mot segmenteraren.** Kör `modal_segmentera.py` på originalrutan med samma föremålsnamn. Var är maskerna lika, och vad har bildmodellens som segmenterarens saknar (skymda delar) eller tvärtom (skarpa kanter)?
- **Över rutor.** Samma färg på samma föremål i ruta 0, 55 och 112? Behåller föremålet form och storlek när kameran zoomar?
- **In i 3D.** Ta den bästa variantens disk och mata den genom dagens möbelplacering i en kopia av planen. Blir diskens mått och läge bättre, sämre eller lika mot `n06-hand`? Använd också samspelet ur 0024 punkt 3 om det finns.

Rörelse:
- Skriv hur ett färgkodat föremål skulle följas över tid: nyckelbilder i samma färg, animerade med Ray 3.2, färgen trösklad per ruta till en bana. Gör det om fal har saldo (en körning, högst 0,20 dollar). Annars lägg färdiga indata i `fargkod/video-paket/` med prompt och inställningar, så att ägaren kan köra det för hand.
- Säg vilka föremål som alls rör sig i de två klippen. För de som står still räcker en ruta.

Parallellt:
- Läs Codex-kvoten först. Kör bilderna i två eller tre samtidiga sessioner om `codex_bild.py` tål det (egna utfiler per session), annars i tur och ordning.
- Det som inte ryms i kvoten läggs som paket åt ägaren: `fargkod/gpt-paket/` med numrerade indatabilder, en prompt per bild i en textfil, och en rad om vad varje bild ska visa. Ägaren kör dem i ChatGPT och lägger svaren i `fargkod/gpt-paket/svar/`. Sikta på högst 40 bilder i paketet, de viktigaste först.

## Del C. Utanför bild och redigering: bara bokföring
Inget byggs här. En sida, `relevans/UTANFOR-OCH-REDIGERING.md`:
- För gelato, guacamole och b-tilltal: i vilka rutintervall lämnar en post med roll `bär` bilden helt eller delvis, och vad gör kedjan med den i dag (försvinner, fryser, antas)? Ägarens antagande är att personen finns kvar i 3D-scenen när kameran fladdrar bort.
- Vilka redigeringshändelser finns i `data/analys` och ingestens tagningsdata som kan misstas för rörelse: blixtar, svep som byter vinkel helt, klipp på 0,1–0,5 s i samma scen. Finns de i våra fyra klipp? Namnge ett eller två klipp i `data/analys` som har dem, som framtida provkroppar.
- Tre rader om var i kedjan sådana händelser borde bokföras.

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/relevans/` och `fargkod/`, samt tillägg i `STRATEGI.md`. Kedjans kod, `forvarld/`, källans schema, `video/` och `data/` ändras inte.
- Ingen sammansättning av läsningar eller lager i efterhand (se målbilden).
- Gateway: högst 0,40 dollar. Fal: bara om saldo finns, högst 0,20 dollar. Modal: segmenteraren, högst 0,30 dollar. Codex: bildkörningar enligt `CODEX-BILD.md`, omfång efter kvoten, lämna minst en tredjedel av femtimmarsfönstret.
- Prompter på engelska, sparade bredvid sina resultat.
- Listans ordförråd (`typ`, `roll`, behandling) ska vara litet och allmänt, inte skrivet för glass eller guacamole.
- Egna trösklar är diagnos, inte krav.
- Profilsmak och kontobedömning hämtas inte från Gemini. Gemini får läsa rutor och föreslå, inte vara källa för vad ägaren tycker.

## Klart när
- Svar för 0023 och 0024 finns, med det som väntar på fal utpekat.
- `relevans.json` för de två klippen, tre körningar var, med jämförelsen mot ägarens läsning.
- Tabellen över underlaget och de tio raderna om var steget hör hemma.
- Ett kontaktblad per ruta med original och varianterna V1–V4 bredvid varandra, och måtten i en tabell.
- Bedömning i högst åtta rader: ska föremål tas fram med bildmodellen, med segmenteraren, eller delat, och i så fall efter vilken regel. Vilken variant, och vad kostar den per tagning.
- Disken ur bästa variant provad i en kopia av planen.
- Rörelsedelen körd eller paketerad.
- `gpt-paket/` klart om kvoten inte räckte.
- `UTANFOR-OCH-REDIGERING.md`.
- `STRATEGI.md` har fått relevanslistan som steg före lagren, och färgkodningens utfall under "Prövat hittills".

## Leveransform
`delegat/svar/0025-relevanslistan-och-fargkodade-lager.md` enligt mallen, högst cirka 90 rader. Bilder och tabeller länkas.
