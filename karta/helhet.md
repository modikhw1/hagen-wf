# Helheten: vart hagen-wf ska, och i vilken ordning

Skrivet 10 nov 2026 av orkestratorn, på ägarens begäran. Det här är min positionering av intentionen, inte ägarens beslut. Underlaget med ägarens egna formuleringar ur tidigare samtal, läget i koden och tre designkandidater finns i [forvarld-underlag.md](forvarld-underlag.md).

## Målet

Ett TikTok-klipp kommer in. CM formar om det så som hen föreställer sig det, direkt, i en värld som håller handen men lämnar kreativiteten hos CM. Ut kommer en PS2-version på en sekund, som läggs i kundens tidslinje. Ägaren kallar det kreativt bricolage och "best best case".

Det ägaren har sagt om vägen dit, i urval:

- "en typ av digital audio workstation (DAW), som 'inte' är en video editing suite" (22 okt)
- "en 1:1 representation i video" av CM:s idé (29 okt)
- "kreativitet först först först"; reglerna "ska inte antas bockas av en efter en" (30 okt)
- inte "html-sticks", utan en flexibel, trovärdig och billig animationsgrund; "10 verkligheter med en director" (31 okt)
- "3d skisser (vad jag menade med html)" (2 nov)
- semantiska ändringar på "mindre en 1 sekund", med videons ryggrad som grund; "Fotorealism är inte en prioritet" (7 nov)
- 1:1 mot originalet före stiliserad indata (9 nov)
- förvärlden "isolerad till ett klipp, permutation av ett klipp baserat på deras spine", styrd genom vanlig chatt med bilder och noter (10 nov)

## Två faser

**Fas 1, förvärlden.** En lättviktig värld per klipp. Den behöver inte vara snygg, men den ska hålla klippets semantiska utseende och flöde och visa vad slutrenderingen kommer att innehålla. CM ändrar den med meningar som "gör klippet längre", "stabilisera kameran", "gör att kvinnan ler efter att hon fått maten", "ändra bakgrunden till en foodtruck och gör henne stillastående". Harnessen från `video/` sätter ramarna.

**Fas 2, renderingen.** Förvärldens tillstånd blir film. Det är här arbetet i `scen/3d/` ligger.

Ägaren ser fas 2 som möjlig grund även för fas 1. Min läsning: kontraktet i `scen/3d/kontrakt/` (ryggrad, ändringar, kompilator) är golvet under förvärlden, men det är inte förvärlden.

## Kedjan och vad varje länk får kosta

| Länk | Tidskrav | Läge 10 nov |
|---|---|---|
| Klipp till ryggrad: mätning och semantik | minuter, en gång per klipp, i förväg | fungerar på fem klipp, ojämn kvalitet |
| CM:s mening till ändring | under en sekund | kompilatorn tar 0,5 s; chattloopen finns inte |
| Förvärlden visar resultatet | direkt | finns inte i den nya kedjan; `#v` i `video/` är ett äldre mätinstrument |
| PS2-generering | en sekund | finns inte; Blender tar 70–110 s, Seedance längre |
| In i kundens tidslinje | efteråt | bara en översättningstabell mot hagen-ui |

## Tre satsningar

De är mina, de är oprövade, och var och en har ett billigt prov.

1. **PS2-looken renderas i webbläsaren, i realtid.** Kravet på en sekund utesluter både Blender och Seedance i loopen. PS2-estetik är vad realtidsgrafik gör naturligt: få polygoner, låg upplösning, enkla texturer. Då blir förvärldens vy och slutbilden samma scen. Ansikten, väggar och föremål texturläggs med utsnitt ur källrutorna, vilket ger likhet med originalet nästan gratis. Risk: gårdagens PS2-look kom ur bildgenerering och Seedance, inte ur 3D. Prov: en tagning ur notan i webbläsaren, första bild till ägaren.
2. **Jev som gallrare, inte som tolk.** Jev (TypeSafe System One) ger typade svar på under en sekund: ja/nej, val bland högst 255 alternativ, poäng. Mönstret från spel: tillstånd plus lagliga handlingar in, ett val ut, och spelets kod utför. Här: scenens delar (kamera, personer, plats, repliker, text, föremål, scenstruktur) får CM:s mening och svarar om den gäller dem och vilken av deras ändringar som avses. Kompilatorn är den hårda spärren. En långsammare modell behövs för ny text och för att förstå bifogade bilder. Prov: `forvarld/jevprov/`, 30 meningar mot facit.
3. **Ryggraden är mer än kroppar i rum.** I harnessens 1 322 analyserade klipp har 1 113 skärmtext, 1 007 musik, 1 004 mat i fokus och 392 montage. Förvärlden måste bära medialager (matbilder, klipp ur källan, det CM bifogar), ljudspår och händelser som tidsankare ("efter att hon fått maten"), inte bara 3D-scener.

## Vad jag släpper

- Blender som renderare i loopen. Den blir verktyg för ingest och export.
- Rumsrekonstruktion ur djup; den gav tomt rum i 11 av 20 tagningar. Mallar och projicerade källbilder i stället.
- Att allt ska bli 3D. Mat och montage hålls som mediaklipp.
- Mer slipning av mätmått. De duger som spärr.

## Vad jag behåller

Ryggraden (`kalla`) och ändringarna mot den (`regi`), kompilatorn, platsen med ankare, den semantiska ingesten, textlagret, rörelsen ur kroppsmodellen, det oberoende kvalitetsmåttet.

## Ordning

Bredd före djup: varje steg görs på ett klipp först, sedan på fler.

1. Ett vertikalt snitt på ett klipp: scenen i webbläsaren ur planen, med rörelse, rum, text och ljud, i PS2-stil.
2. Chattloopen på samma klipp: meningen gallras av Jev, kompileras, och ändringen syns.
3. Ryggraden utvidgas: händelser, uttryck, rörelse per namn, medialager, ljudspår.
4. Harnessen som villkor och exempel i Jevs tillstånd; därefter sekvenser mot strategi.
5. Tidslinjen i hagen-ui, när förvärlden bär. hagen-ui ändras inte drastiskt före det.

## Det som inte är avgjort

- Det finns ingen gemensam definition av ryggrad. Harnessen menar kärna och bärande beats, hagen-ui menar räls och mekanik, kontraktet menar en fryst källbeskrivning. Beats och tagningar är inte samma enhet (lika antal i 4 av 33 klipp).
- Ingen uppmätt överensstämmelse mellan Jev och mänskliga bedömningar finns sparad. De visuella bedömningarna är 12 stycken.
- Träningsdata är i dag beskrivningar (1 480 kort, 5 180 beats, nio kundlinjer), inte exempel på önskemål och rätt ändring. Sådana exempel uppstår först när CM väljer bland varianter.

## Frågor till ägaren

1. Gäller en sekund från inskickad mening, eller från att en tolkad ändring finns?
2. Vilka tre saker måste vara trogna originalet för att förvärlden ska godkännas: handlingens ordning, kroppsrörelse, kamera och komposition, rytm, eller kontakt med föremål?
3. Ska en bifogad matbild visas som den är i klippet, eller vara referens för ett ombyggt motiv?
4. Får en sketch en ny säljavslutning direkt, eller krävs uttrycklig upplåsning av intentionen som i hagen-ui?
5. Låses exakta repliker bara när de bär premissen?
6. Betyder "stillastående" i foodtruck-exemplet att förflyttningen låses men gesterna är kvar?
