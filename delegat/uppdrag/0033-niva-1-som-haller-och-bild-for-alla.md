---
id: 0033
titel: Nivå 1 som håller i bild: andra handen räcker fram på riktigt, kunden som roll, och bild för varje mening
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0031
tillåten_skrivning: [scen/3d/kontrakt/, scen/3d/gennedbrytning/, forvarld/gelato/, forvarld/liggare/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0032.** Läs `delegat/kontext/vagen.md` först.

## Varför
0031 visade att liggaren bär: Jev valde rätt i elva av elva meningar, fem av fem gånger, på 169 ms. Förståelsen är alltså löst för gelato. Det som brister är att **se** det:
- "Andra handen", ägarens egen mening och skälet till hela liggaren, ser fel ut. Vänster arm viks upp och bakåt i h6–h8 i stället för att räcka fram, skeden hamnar vid axeln, och höger axel deformeras i hela scenen.
- Sju meningar nådde "plan ✔" men ingen bild. En CM ser inte en plan.
- m9 (kunden tar emot med andra handen) fick rätt val av Jev men ingen regi, eftersom kundens arm bara är ett objekt i scenbygget.
- Svaret har två platshållare som aldrig fylldes i: `SE_KOMPAT` och `SE_TESTER`.

Nivå 1 är den snabba vägen som ska göra förvärlden omedelbar. Om den bara klarar tidsändringar och inte kroppsändringar, blir varje ändring av en arm en Dreamina-körning på minuter. Det är värt att se hur långt nivå 1 når innan det avgörs.

## Mål
"Gör att kvinnan ger glassen med andra handen" ser rätt ut i alla segment: vänster hand skopar i tråget, lyfter, och räcker fram skeden till kundens hand. Alla meningar som Jev kan utföra har en bild eller film. Kunden är en roll med en hand som går att ändra.

## Att göra
1. **Rätta 0031:s lucka först:** kör bakåtkompatibiliteten och testsviten för 0031:s ändringar och fyll i svaret 0031 (`SE_KOMPAT`, `SE_TESTER`).
2. **Speglingen.**
   - Felet enligt 0031: speglingens plan och IK-målet räcker inte, och de vridande lederna (`*_twist`) speglas som vanliga leder. Pröva det först.
   - **Målet ska komma ur liggaren**, inte ur högerhandens bana: i `skopa` är målet tråget (entiteten finns), i `räcka fram` och `ge` är målet kundens hand. Den högra handens bana speglad över hennes mittplan är bara en startgissning.
   - Bålens lätta vridning mot den hand som räcker fram följer med i originalet. Säg om den behöver speglas också, och gör det i så fall som en del av samma frihetsgrad.
   - Mät: avståndet sked–kundens hand i h8 (före och efter), vänster hand i tråget i h3 (andel rutor), ledvinklar inom MHR:s gränser, och ingen deformation av den arm som inte ändras (jämför höger axels läge med före).
   - Titta själv ruta för ruta i h3, h6 och h8 och skriv två rader om vad en betraktare ser.
3. **Kunden som roll.**
   - Kundens arm blir en prop (eller en enkel kropp med två armar) med läge och hand som frihetsgrad i liggaren, så att `fg_kund_hand=vanster` får en regi.
   - Kunden är fortfarande antagen och utanför bild utom armen. Märk det så.
4. **Bild för allt.** Rendera före och efter (eller kort film där tiden är poängen) för m1–m7, m9 och m11 ur 0031:s regier, i `forvarld/gelato/ut_0033/`. Ett kontaktblad med alla, en rad per mening, så att ägaren kan se allt på en gång.
5. **Nivå 3 bredvid.** Har ägaren lagt en fil i `d_video/dreamina-paket/vanster_hand/svar/`, kör den genom kedjan och lägg den bredvid nivå 1 i samma film. Annars skriv att den väntar.

## Gränser
- Före-kopior, testsvit före och efter, bakåtkompatibelt med sha256.
- Ingen ny bild- eller videogenerering. Jev bara om en regi måste göras om, högst 0,02 dollar. Modal och Codex: nej.
- Rör inte `app/`, `video/`, `forvarld/btilltal/`, `forvarld/guacamole/`.
- Inga leder ur andra läsningar. Ändringen är en följd av CM:s mening, inte en lapp över en dålig läsning.

## Klart när
- Svar 0031 ifyllt.
- `forvarld/gelato/ut_0033/andra_handen.mp4` med måtten före och efter, och de två raderna per segment.
- `fg_kund_hand` med regi och bild.
- Kontaktbladet med alla meningar.
- Bedömning i högst sex rader: räcker nivå 1 för armändringar, och var går gränsen mot nivå 3.

## Leveransform
`delegat/svar/0033-niva-1-som-haller-och-bild-for-alla.md` enligt mallen, högst cirka 60 rader.
