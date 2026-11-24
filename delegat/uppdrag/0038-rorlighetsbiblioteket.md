---
id: 0038
titel: Ändrar 0036. Rörlighetsbiblioteket: en rörelsemodell som svarar på "hur hade hon rört sig med vänster arm, i den här scenen", och licensbeslutet
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov natt
datum: 2026-11-13
följer: 0036
tillåten_skrivning: [forvarld/kropp/, scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Ändring av 0036 (gäller genast, också om 0036 pågår)
- **Stryk helspeglingen som lösning** (punkt 3–5 i den form de står). Ägaren: "Det måste finnas mening och förståelse. Det måste också finnas smoothness i rörelser. Det ska inte se ut som en robot." En speglad tagning svarar inte på frågan, den byter bara sida på allt, också på scenen.
- **Behåll** punkt 1 (bankens format), punkt 2 (v0 ur det som finns, utan speglingar) och punkt 6 (vägen till tusen klipp). Skriv svar 0036 med dem och peka hit.

## Varför
Ägarens fråga, som är kravet: **om person X rör sig så här med höger arm, i den här scenen, hur hade X rört sig med vänster arm? Hur hade X förflyttat sig, bytt riktning, hållit resten av kroppen?** Svaret ska ha mening (det är fortfarande att ge kunden ett smakprov över disken), förståelse (kroppen vet hur människor gör det) och mjukhet (ingen robot). 0034 visade vad som händer utan en rörelsemodell: målet nås, men kroppen blir vriden och stel.

Det som krävs är en **rörelsemodell**: tränad på mycket mänsklig rörelse, som tar villkor (vilken hand, mål per tid, kontakter som ska hållas, scenen, och originalets rörelse som stil) och ger en ny, naturlig helkroppsrörelse. Det är inte generativ video och inte en LLM som modellerar om. Det är det ägaren kallar ett rörlighetsbibliotek: en bank av rörelse som modellen har lärt sig, och som går att fråga.

Ägaren om AMASS: om licensen är det som blockerar, ska vi leta efter ramverk och data som uppnår samma sak, och **beslutet ska fattas**. Det här uppdraget ska göra det möjligt att fatta det i dag.

## Mål
1. En kort lista över rörelsemodeller som kan svara på ägarens fråga, med licens för kod, vikter och träningsdata, och vägen till kommersiellt bruk för var och en.
2. Ett beslutsunderlag på en sida med tre alternativ och en rekommendation.
3. Ett prov på "andra handen" med den bästa modell som går att köra nu, mjukt och naturligt, i förvärlden.

## Att göra
1. **Kartan över modeller** (`forvarld/kropp/RORELSEMODELLER.md`). Sök brett, i forskning och i produkter. Typer att täcka:
   - rörelseredigering och inpainting med villkor: text- och målstyrd redigering av en befintlig rörelse (MotionFix och efterföljare), diffusionsmodeller med villkor på leder och tid (till exempel OmniControl, GMD, CondMDI, och nyare)
   - samspel med scen och föremål: modeller som tar hänsyn till en möbel, en mottagare eller ett föremål i handen
   - fysikbaserade kontroller med ofullständiga mål (MaskedMimic, PHC och efterföljare)
   - kommersiella tjänster och verktyg med API eller export: till exempel Cascadeur (AutoPosing, AutoPhysics), Uthana, DeepMotion, Kinetix, och andra du hittar
   Per modell: vad den tar som villkor (hand, mål, tid, scen, stil ur en given rörelse), fart, hårdvara, kropp (SMPL, SMPL-X, BVH), och **tre licenser: kod, vikter, träningsdata**.
2. **Data och licens** (samma fil, eget avsnitt). Vilka rörelsedataset är fria för kommersiellt bruk (till exempel CMU mocap, 100STYLE; kontrollera), vilka går att **köpa licens för** (till exempel SMPL och AMASS-tränade modeller via Meshcapade eller Max Planck; kontrollera vad som erbjuds och ungefär vad det kostar), och vilka kommersiella rörelsebibliotek som säljer data för träning. Skriv vad som är bekräftat ur licenstexten och vad som är antaget.
3. **Beslutsunderlaget** (`forvarld/kropp/BESLUT-LICENS.md`, en sida), tre alternativ:
   - **A. Köp licens** för det bästa (SMPL/AMASS-baserat via den som säljer den): pris, tid, vad det låser upp.
   - **B. Bara fria eller egna data:** vilken modell, tränad på vad, hur långt från A i kvalitet, och hur mycket egna klipp det kräver.
   - **C. Kommersiell tjänst via API:** vem, pris, och om den kan ta våra villkor.
   Rekommendera ett, och säg vad som blockeras om inget väljs. Ägaren fattar beslutet. Ett prov i det här uppdraget med en icke-kommersiell modell är **inte** ett sådant beslut; det ska ligga under `forvarld/kropp/forskning/`, märkas så, och inte gå in i kedjan.
4. **Provet.** Ta den modell som bäst svarar på ägarens fråga och som går att köra inom uppdraget (lokalt eller Modal). Villkor ur `GRANSSNITT.md` (0034): vänster hand till tråget i h3 och till kundens hand i h6–h8, fötterna och disken som scen, skeden i handen, originalets rörelse som stil. Konvertera MHR till modellens kropp och tillbaka, eller kör i modellens kropp och säg vad som tappas.
   - Mät som i 0034, och lägg till mjukhet: ryck (jerk) i händer och bål, och fotglidning.
   - Film bredvid 0034:s prov och originalet.
   - Titta själv på h3, h6 och h8: flyttar hon fötterna, byter hon riktning, vrider hon sig naturligt mot kunden, ser det ut som en människa?
5. **Hur Jev och liggaren använder den:** en halv sida. Frihetsgraden ger villkoren, modellen ger rörelsen. Hur snabbt (sekunder är ok nu; vad krävs för under en sekund), och hur de tusen klippen förbättrar den (finjustering, stil per person, ny domän).

## Gränser
- Ingen generativ video eller bild, ingen LLM som skriver rörelsen.
- Modal: högst 3,00 dollar för provet. Paket i eget venv under `forvarld/kropp/`, med versioner i svaret.
- Icke-kommersiella vikter eller data får bara användas under `forvarld/kropp/forskning/` och märkas. Inget av det går in i `scen/` eller kedjan.
- Webbsökning tillåten. Inga köp, inga konton.
- Rör inte `app/`, `video/`.

## Klart när
- `RORELSEMODELLER.md` med licenser.
- `BESLUT-LICENS.md` med tre alternativ och rekommendation.
- Provet: mått inklusive mjukhet, film, och tre rader om vad en betraktare ser.
- Halva sidan om Jev och liggaren.

## Leveransform
`delegat/svar/0038-rorlighetsbiblioteket.md` enligt mallen, högst cirka 80 rader.
