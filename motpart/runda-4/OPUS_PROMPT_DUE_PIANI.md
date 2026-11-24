# Till Opus: förbättra Due Pianis förvärld genom scenkartläggning och trogna tagningar

Du tar över ett aktivt experiment i `C:\Users\praiseworthy\Desktop\hagen-wf`. Läs denna prompt som ett konkret fortsättningsuppdrag. Bygg vidare från den visuella loopen som nu finns. Målet är ett nytt bedömbart före/efter-resultat, med avgränsad ändring, bevarade fungerande delar och redovisad tid/kostnad. Det räcker inte med en ny arkitekturtext.

## 1. Vad ägaren försöker uppnå

Ägaren vill kunna läsa stora mängder verkliga 9:16-klipp, jämföra deras innehåll och form, återskapa en redigerbar förvärld och röra scener mot/från referenser utan att förlora det som gör klippen distinkta. CM:s kreativitet påverkar scenen och scenens visuella möjligheter ger nya kreativa val tillbaka. Vaga instruktioner måste kunna omsättas till bedömbara visuella alternativ; ägaren ska inte behöva verbalisera varje nyans eller diagnostisera tekniska fel åt oss.

3D är arbetsrepresentationen för rum, personer, handlingar, föremål, kontakt och kameror. Den behöver inte vara fotorealistisk eller lika detaljerad som en full spelvärld. Den måste däremot stödja samma ungefärliga iscensättning och visuella läsning genom 9:16-kameran. Ett snyggt generiskt kök, en fristående översiktskamera eller statiska dockor ersätter inte originalklippets tagningar och rörelser.

Ägaren accepterar extern kapacitet, exempelvis Modal/RunPod, inom **totalt 100 USD för provomgången** (tolkning av ”0-100d”). Tidigare upplägg avsätter högst 20 USD till åtkomst/baslinje/första jämförelse innan större körning. Denna Codex-omgång har inte startat betald extern beräkning. Kontots övriga/historiska kostnader är okända. Riktmärket är **ungefär 15 minuter från ett definierat experiment till första bedömbara utfall**. Stor systeminstallation är ett separat redovisat uppdrag, inte en dold väntan. Kör inte en stor batch utan litet prov, ETA och tak.

## 2. Den nya ägaråterkopplingen är huvudstyrningen

Läs hela meddelandet ordagrant i [AGARFEEDBACK_DUE_PIANI_2026-11-21.md](AGARFEEDBACK_DUE_PIANI_2026-11-21.md). Viktiga delar:

> Det verkar synroniserat till personen i rörelser, helt ok.

> Det den inte klarar lika bra är unika/udda vinklar, rum i bakgrunden och allmän inpaketering i lokal (dvs bänk, spis, storlek av rätten och annat).

> Scener som är konstiga är s2, s8 är en stiliserad inzooming av något som inte zoomar i videon. s10 har ingen anpassad shot för inzooming där heller.

Ägaren föreslår också image-gen-idén för att kartlägga viktiga saker i scenen, men bara om det faktiskt bidrar. Bord på fel plats är inte bara ett ytdetaljfel: det kan styra CM till fel iscensättning och därmed bryta respekten för originalet.

**Konsekvens:** börja med rum, rekvisita, skala och kamera i S2/S8/S10. Bevara befintliga kroppsspår/rörelsesynk som regressionsbaslinje. Det innebär inte att alla identiteter är korrekta, men byt inte hela kroppspipen när användaren just har identifierat en fungerande del. Tidigare Codex-bedömning ”underkänd baslinje” ska inte tolkas som att ägaren underkänt allt. Spanjorskan har inte fått motsvarande ägarbedömning.

## 3. Det som finns att köra och granska

Från repots rot:

```powershell
.\scen\.venv\Scripts\python.exe -I -X utf8 motpart\runda-4\4-visuell-loop\server.py --port 5204
```

Öppna `http://127.0.0.1:5204`. Kontrollera först om servern redan kör; starta inte en dubblett eller stoppa en okänd process. Den lokala servern kan behöva startas igen i en ny session.

Granskningsbordet visar original med ljud, befintlig 3D och ett reversibelt linsprov ±20 %. Alla tagningar går att spela/söka. Kommentarer sparas med proveniens i `4-visuell-loop/ut/svar.jsonl`. Chattsåterkopplingen är sparad separat; den har inte fabricerats till ett tidsbundet panelsvar.

**Återställ linsreglaget till 0 % före baslinjegranskning.** Kameraändringen i högra vyn är ett tekniskt prov, inte inlärd modulering. Ägarens exakta reglageläge vid kommentaren är okänt. Undersök den oförändrade mittvyn och paketet innan orsaken till en upplevd zoom fastslås.

Relevanta filer:

| Fil | Användning |
|---|---|
| `data/format/kontroll/klipp/duepiani-7650849186912406806.mp4` | Originalreferensen som också visas i panelen, H.264, 540×960, 30 fps, cirka 19,436 s. |
| `arbetsbord/data/ingest_v2/duepiani/paket.json` | Fryst befintligt scenpaket: 12 tagningar, 92 kameranycklar, 5 person-id:n. |
| `arbetsbord/data/ingest_v2/duepiani/tidslinje.json` | Tidslinje, tal/text och tagningar. |
| `arbetsbord/ingest_v2/modal_ingest_v2.py` | Befintlig ingest och de schablonregler som behöver prövas. |
| `arbetsbord/web/scen3d.js` | Befintlig animerad Three.js-renderare, återanvänds av experimentet. |
| `motpart/runda-4/4-visuell-loop/` | Isolerat experiment: server, UI, bevarandetest, webbtest, rapport. |
| `motpart/runda-4/4-visuell-loop/ut/qa/` | Bilder från alla 15 tagningar i två klipp, kontaktkartor och teknisk report.json. |
| `motpart/runda-4/INFRA.md` | Aktuellt upplägg, budget och experimentkrav. |
| `arbetsbord/utforskning/IMAGEGEN_MALL_PILOT.md` | Tidigare image-gen-försök; påståendena måste granskas, inte ärvas som fakta. |
| `arbetsbord/utforskning/mall_pilot/` | Faktiska mallbilder, mätdata och mätkod från det tidigare försöket. |

Det som tekniskt verifierats är synkron uppspelning, alla tagningsövergångar, byte av enbart linsfältet, exakt återställning och append-only-sparande. Lokalt tog ändring till avslutat renderanrop 2,9/3,6 ms i två observationer. Detta är **inte** ny ingesttid, komplett GPU-latens eller bevis på semantisk korrekthet. Två äldre externa ingestjobb tog 79,12 och 67,34 s inklusive överföring på olika klipp; det är inte ett kontrollerat kall-/varmbenchmark.

Modal CLI och lokal konfiguration finns, men `modal app list --json` svarade inte inom 20 s i senaste kontrollen. Processen avbröts, inget compute-jobb skickades. Orsak, aktiv åtkomst, kvot och kostnadstak är inte fastställda. Börja inte med en lång ogenomskinlig remote-körning. Läs aldrig ut tokens i loggar och synka inte repots nyckelfiler.

## 4. Exakta tagningar och belägg att undersöka

Följande är **ur befintliga paketdata**, inte kalibrerade fysiska sanningar. Intervallen är halvöppna; tidsbasen är 30 fps.

| Tagning | Rutor | Tid | Fokus |
|---|---|---|---|
| S1, kontroll | [0,62) | 0–2,067 s | Personen står vid entrén; stor bordsmall dyker upp i 3D. Använd som negativ kontroll för att ”person med föremål” inte får innebära ”person bakom bord”. |
| S2 | [62,105) | 2,067–3,500 s | Ägaren bedömer tagningen som konstig. Originalet visar tallriken nära kameran; kartlägg utsnitt, tallrikens skala och hur den hålls. |
| S8 | [375,397) | 12,500–13,233 s | Ägaren ser en stiliserad zoom som inte finns i originalet. Kontrollera faktisk kamerarörelse och rörelse i panna/mat separat. |
| S10 | [436,463) | 14,533–15,433 s | Närbilden får inte rätt anpassad shot. Kontrollera vinkeln, utsnittet, hand/redskap, panna/mat och synlighetsintervall. |

**S8:s paket:** brännvidden är konstant 69,99 mm. Kameran går från ungefär (-0,001, 0,0, 1,38) till (0,001, 0,22, 1,34), med konstant rotation. Det är alltså en inlagd translation, inte en optisk linszoom i paketet. Ägarens ord ”inzooming” beskriver upplevelsen. Detta visar en möjlig mekanism, inte att originalets kamera redan är oberoende uppmätt.

**S2/S10:** har konstant brännvidd 59,50 respektive 61,22 mm, båda med inlagd Y-förflyttning 0,14 m. S10 startar vid Y=0 och slutar vid Y=0,14 med Z=1,38 oförändrat.

I `modal_ingest_v2.py` finns konkreta kodspår (kontrollera aktuella rader):

- Cirka 709: fast kamerahöjd 1,38 m.
- Cirka 826–830: bordskandidat skapas vid skymda ben **eller** klassningen person_med_mat; höjd från handleder och förskjutning från bål. Detta kräver inte ett observerat bord.
- Cirka 844–868: bord-/matprimitiver skapas med schablondimensioner, bland annat mat 0,34×0,34 m, och får tilltro observerad trots härledda delar.
- Cirka 873–891: om bakgrundsförskjutningen överskrider tröskeln ges tagningen en framåtrörelse på **0,22 m för mat, annars 0,14 m**. Det är inte skattad metrisk kamerarörelse bara för att tröskeln bygger på bilddata.
- Cirka 906–913: huvudbordet får synlighet över hela klippet. Ett bord från en tagning kan därmed synas även där det inte hör hemma.

Prioritera att ta bort falska påståenden om observation och pröva dessa regler. Att bara höjdklämma bord, minska skålen tills bilden ser bättre ut eller hårdkoda S8 till statisk kamera bevisar inte en generell förbättring. En sådan ändring kan vara ett tydligt märkt diagnostiskt motprov, men får inte presenteras som ny allmän ingest.

## 5. Image-gen: min bedömning och ett prov som kan avgöra nyttan

**Codex bedömning:** idén är värd ett litet prov som hjälp till kartläggning av viktiga rumsliga former och objekt. Den är inte visad som lösning och behövs inte för att först testa den uttryckligen felaktiga kameraregeln. Förväxla inte bildförenkling med rekonstruktion av dold verklighet.

Den gamla mallen förenklade en bild till matta block och tog bort text, reflektioner och detaljer. Men bland det borttagna fanns även glass, maskiner och annan kontext som ägaren nu uttryckligen behöver för att läsa scenen. Återanvänd därför inte dess prompt oförändrad.

Rapporten anger global fasförskjutning på cirka 0–1,6 px och kraftigt reducerad kantdensitet. Detta bevisar inte bevarad lokal geometri eller bättre 3D. Samma mätdata innehåller grov struktur-IoU omkring 0,14–0,23 och central gradientkorrelation omkring 0,016 respektive 0,025 i två av fallen. Måtten är inte heller ensamma bevis för misslyckande efter stilbyte; slutsatsen är att lokal och efterföljande 3D-nytta behöver kontrolleras. Den gamla metoden ritade dessutom in skymda ben i ett fall: syntetisk prior, inte observation.

### Rekommenderad jämförelse

1. **A – fryst baslinje:** dagens paket, samma original och samma renderer.
2. **B – bildstödd förbättring utan image-gen:** kartlägg originalens objekt, kontakt, skala i bild och kamera; ersätt de schabloner som saknar stöd. Behåll kroppsrörelserna.
3. **C – samma B plus image-gen-karta:** en kontrollerad mallbild som extra hypotes/kartstöd där B är otillräcklig. Samma övriga kod och bedömning så att image-gen får ett isolerbart bidrag.

Börja med S2, S8 och S10 och S1 som negativ kontroll. Inspektera början/mitten/slutet i originaltagningen för rörelse; en genererad stillbild får aldrig ensam bestämma en kamerabana. Begränsa första genereringen till **en representativ ruta per vald problemtagning**. Det är agentens föreslagna försöksstorlek, inte ägarens krav. Eskalera antalet först vid ett konkret behov. De gamla genereringstiderna 56–80 s per bild är historik, inte dagens garanti.

### Villkor för mallbilden

Utgå från bifogad originalruta och relevanta originalrutor i samma tagning, inte en fri textbeskrivning. Behåll exakt utsnitt/bildformat, perspektiv och överlappningsordning. Kartlägg identifierbara viktiga delar: person, händer, tallrik/panna, matvolym, bänk, spis och lokalens tydliga ytor/öppningar. Behåll deras relativa storlek och bildläge. Gör delarna enklare att särskilja utan att flytta dem. Lägg inte till bord eller andra stöd som inte syns eller kan styrkas av originalsekvensen. Återskapa inte dold kropp som om den vore observerad. Radera inte verksamhetskontext bara för att den är visuellt komplex. Presentera ingen påhittad ”bättre kameravinkel”.

Märk mallutdata genererad och varje ny geometri antagen eller modellskattad. Använd inte mallens egna punkter som facit för dess validering. Mät/bedöm mot originalet: skål-/pannkant, bänkkant, handkontakt, storlek relativt kropp/bild, centrala linjer och ocklusion. Kontrollera om C förbättrar den **resulterande animerade scenen** jämfört med B. En snyggare mallbild i sig är inte framgång.

Om C flyttar kameran, ändrar objektgränser, tillför geometri eller tappar bärande kontext utan att den färdiga scenen blir mer användbar: förkasta C för detta ändamål. Om den hjälper i en viss typ av svår tagning: behåll som selektivt ingeststöd med kostnads-/tidslogg. Kör den inte över hela banken och inte vid varje CM-reglage. Generativt kartstöd vid ingest är inte tillåtelse till generativ video/röst i ändringsledet.

## 6. Genomförande och leverans

1. Läs AGENTS.md, CLAUDE.md och byggsten/jutsu/README.md. Gamla ”verifierad”-påståenden i LAGE/arkitekturdokument kan vara fällda; läs motpart/PROTOKOLL.md och aktuell ägaråterkoppling före sådana slutsatser.
2. Inventera paket, original och befintlig ingest. Lås/hashmärk A. Skriv separat B/C och recept/proveniens. Skriv inte över arbetsbord/data/ingest_v2/duepiani eller historiska ägarsvar.
3. Verifiera kamera-/objektproblemen på korta originalsekvenser. Kontrollera om kamerarörelse verkligen kan skattas; bildrörelse från mat, händer eller foreground är inte automatiskt kamera.
4. Gör minsta B som kan ge ett ärligt nytt före/efter-resultat. Visa osäkerheter. Om bara ett manuellt diagnostiskt motprov går att göra, märk det som sådant och separera det från en generell metod.
5. Pröva C enligt ovan endast där kartstödet har en konkret funktion. Följ tillgängliga image-gen-verktygs aktuella instruktioner; gamla wrapper-/modellnamn är historik.
6. Återanvänd panelens synkroniserade 9:16-visning. Gör A/B/C jämförbara med samma kroppsspår, ljud, tidsbas och relevanta tagningar. Kropp, kamera och objekt måste leva i samma koordinatram. Välj inte bort besvärliga rutor i jämförelsen.
7. Visa original plus förändrade tagningar som rörelse, inte bara en kontaktkarta. Kontrollera början/mitten/slutet, kontakter, synlighet och övergångar. Spara kommentarsfält för ägaren med exakt variant. Om visuell granskning inte går: skriv att verifiering återstår.
8. Redovisa vad förbättringen ändrade, vad som bevarades, vad som fortfarande är fel och vilket nästa tekniska beslut utfallet stödjer. Ange uppmätt tid/kostnad och obekräftade siffror separat.

**Första leveransen ska kunna besvara:** är S2/S8/S10 närmare originalets vinklar, utsnitt och objektstorlekar utan att den redan godtagbara rörelsesynken försämrats? Har falsk kamerarörelse försvunnit utan att riktig kamerarörelse försvinner? Får CM fortfarande samma ungefärliga inspelningssituation? Bidrog image-gen mer än B, eller kan den grenen strykas?

Det finns ingen beställd generell finjustering av modell, helt ny editor, fotorealistisk värld eller massingest i detta delprov. Ändra inte grundidén för att få ett lättare mått att lyckas. Lägg inte tid på att få ägaren att bekräfta uppenbara tekniska fel. Ägarens uppgift är att bedöma om den nya visuella representationen är användbar nog och vilket innehåll som fortfarande går förlorat.

## 7. Rapporteringsformat vid återkomst

- Länk/kommando till fungerande A/B/C-visning och vilka tagningar som förändrats.
- Före/efter-rörelse samt representativa rutor från S2/S8/S10 och kontrollfallet.
- Ägaråterkopplingen ordagrant, separat från agentens tolkning och tekniska diagnos.
- Tids-/kostnadslogg inklusive kö, start, generation, beräkning och publicering; timeout/avbrott ska stoppa fjärrarbete, inte bara den lokala väntan.
- Reproducerbara recept, versionshashar, antal manuella korrigeringar och kvarvarande antaganden.
- Ett tydligt vägval: fortsätt med B, använd C selektivt, eller förkasta försöket och säg vilken observation som motiverar nästa metod.

**Bärande instruktion:** bevara det ägaren nu accepterar, rätta det som ändrar hur CM läser och iscensätter klippet, och pröva image-gen som ett avgränsat hjälpmedel med originalvideon som kontroll.
