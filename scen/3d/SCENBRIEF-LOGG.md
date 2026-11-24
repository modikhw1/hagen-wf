# Scenbrief – arbetslogg (12 nov 2026)

## Del 1: briefpaket – klart

- Nytt cache-only-kommando: `ingest/scenbrief.py bygg ingest/ut/<klipp>`.
- Skriver ett märkt kontaktblad per tagning, en gemensam översikt, `lasning.json`, `uppdrag.md` och `deklaration.schema.json` i `<klipp>/brief/`.
- `lasning.json` sammanfattar personspår, semantiskt läge när cache finns, kamera–höft/öga ur cachade kroppar, fotbildstöd, ögonhöjd endast med fotbildstöd, rumstegets godkända objekt, skärmtext och taltider. Saknad cache anges som saknad; inget modelljobb startas.
- Uppdraget kräver rumshypotes, personidentiteter/relativ placering, relevans i tre nivåer samt `antagen`/`last`/`deklarerad`. Antagna numeriska värden ska vara intervall där 0.8-översättaren tillåter det.
- Schemat följer fälten som `deklaration_till_hand.py` läser i format 0.8; beskrivande extrafält är tillåtna.
- Första paketprovet (`test_scenbrief.Paket`) är grönt. Inga befintliga ingestmoduler är ändrade.

## Del 2: validator – klart

- Nytt kommando: `ingest/scenbrief.py granska <ingestmapp> <deklaration.json>`.
- Rapporterar strukturella schemafel, odefinierade plats-/rollreferenser, tagningar utan kamera, numerik utan `antagen`/`last`/`deklarerad`, hårda antagna tal där intervall stöds samt `last` utan källa.
- Kör en oförändrad kopia av `deklaration_till_hand.py` med all utdata och genererad rumsmall i en temporär mapp. Källfiler byts eller skrivs aldrig över.
- Skriver korta `granskning.md` och maskinläsbara `granskning.json` bredvid förslaget. Markdownfilen listar alla antagna tal/intervall, rollidentiteter och de tre relevansnivåerna för ägarbeslut.
- Format 0.8 är målformat; befintlig 0.7 godtas som bakåtkompatibel syntax. Äldre statusord godtas syntaktiskt men uppfyller inte den nya numeriska proveniensregeln.
- `test_scenbrief` 4/4 gröna. Både notans och guacamoles befintliga deklaration översätts i scratch och har inga struktur-, referens- eller kameratäckningsfel; äldre/missande numeriska märkningar listas.

## Del 3: första experimentet – klart

- Paket byggda för `a-sketch-servering-tagningar` och `e-dialog-guacamole-tagningar`; alla kontaktblad granskade och båda `lasning.json` lästa.
- Blindförslag skrivna som `brief/forslag_deklaration.json`. Båda är format 0.8, lämnar källdeklarationerna orörda och har inte använts för plan-kompilering.
- Validator: båda förslagen har 0 schemafel, 0 referensfel, 0 tagningar utan kamera, 0 omärkta tal, 0 hårda antagna tal där intervall stöds och 0 lästa tal utan källa. Båda översätts i scratch.
- Fältvis jämförelse finns i `SCENBRIEF-JAMFORELSE.md`.
- Sketch: förslaget och befintlig deklaration är ense om rum, roller, kameramotiv, närvaro och nästan all relevans. Förslaget gör B:s tre arbetsplatser uttryckliga och använder måttintervall; bilderna stöder platsernas funktion men inga koordinater. Befintliga hårda disk-/kamera-/A–B-mått saknar läsestöd.
- Guacamole: ense om rum, spåridentiteter, hållning, huvudkameror, närvaro och huvudsaklig relevans. Förslaget gissar B till y=1,60; den senare flerrollsläsningen stöder befintliga 1,73 m (intervall 1,60–1,85). Diskdiagnostiken väljer 2,80 × 0,65 × 1,00 m vid mitt-y 0,65 och stöder befintligt diskintervall bättre. Kamerans 1,40 m bevarar projektionen men är fortfarande antagen, så förslagets intervall har riktigare proveniens.
- Det en LLM inte kan avgöra ur rutorna: verkliga mått, dold närvaro, sketchens rollavsikt trots samma skådespelare, om inskottsbilder delar exakt layout samt ägarens relevansnivåer.

## Del 4: återkopplingsloop – klart

- Nytt förslagskommando: `ingest/scenbrief.py aterkoppla <deklaration.json> <plan-eller-diagnostik.json> [--ut ...]`.
- Läser `kvalitet.deklaration.registrering` och `kvalitet.mobelintervall` ur en hel plan eller motsvarande fristående diagnostik. Ett avvikande läst rollpar föreslås som ny plats längs den befintliga deklarerade axeln; ett möbelvärde föreslås bara när lösaren faktiskt ändrade det från utgångsvärdet.
- Skriver ägargranskningsbar Markdown-diff och maskinläsbar JSON med sökväg, före/efter, `last`, exakt diagnostikkälla och skäl. Deklarationen öppnas endast för läsning och ändras aldrig.
- Prov mot guacamoles slutplan föreslår en enda ändring: bardiskens höjd `[0,95, 1,15]` → `1,0`, källa möbelintervalldiagnostiken. A–B föreslås inte igen eftersom nuvarande 1,73 ligger inom 1 cm från lästa 1,734.
- `test_scenbrief.Aterkoppling` verifierar både läst rollavstånd, valt möbelvärde och att indata inte muteras.

## Slutverifiering

- `PIPE.md` uppdaterad: steg 2 finns nu som paket/validator med manuellt ägargodkännande; öppet-listan skiljer färdig mekanism från kvarvarande LLM-/chattkoppling.
- Krävda prov körda tillsammans i Python 3.12-miljön: `test_scenbrief.py`, `test_deklaration.py`, `test_rum.py` — **14/14 gröna**.
- Inga modelljobb, API-anrop eller Blenderkörningar gjordes. Inga källdeklarationer ersattes och inga planer kompilerades från förslagen.
