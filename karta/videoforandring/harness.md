# Harnessen: utkast v0 (3 nov 2026)

Det här är ett arbetsutkast som ska formas om tillsammans med ägaren. Inget är bestämt än. Den tekniska lösningen väntar tills innehållet finns: Lovables Scene-DSL med regi-JSON och enum-räcken, och 3D-renderingen.

## Frågan
> Om en CM vill anpassa ett klipp till just den här verksamheten, hur ökar vi chansen att hen får det hen vill i ett lättviktigt system, och lämnar samtidigt utrymme för kreativitet?

## Enheten är formatet, inte klippet och inte typen
- **Typen**, till exempel sketch eller matporr, är för grov. "Servitören blandar ihop två drycker" och "klipper in sig i en scen ur Seven" är båda sketcher, men bara det första går att göra på vilken verksamhet som helst.
- **Klippet** är en instans. Ett klipp består av ett format, ett utförande och en bindning till en verksamhet.
- **Formatet** är idén som mall med platser som kan bytas ut. Det är formatet CM väljer och anpassar.

| Nivå | Vad det är |
|---|---|
| typ | genren: sketch, matporr, tilltal |
| **format** | idén som mall: kärna, platser och lås |
| klipp | formatet utfört hos en viss verksamhet |
| scen och takt | delarna i manuset som CM redigerar ([inlarning.md](inlarning.md)) |
| profil | en mix av format över tid, med återkommande personer: serien |

## Vad harnessen vet om varje format
1. **Kärnan.** Det som bär värdet och är låst.
2. **Platserna.** Det som kan bytas ut. Varje plats har förslag för just den här verksamheten, och här finns CM:s frihet.
3. **Tröskeln.** Vad formatet kräver av kunden: antal personer, agerande, produktion och rekvisita. Den jämförs med vad verksamheten har.
4. **Räckena.** Det som gör att formatet tappar sitt värde. Det gäller när kärnan bryts, när tröskeln är för hög för kunden, och när intent glider från underhållning till säljande. CM får bryta mot ett räcke, men måste ange en orsak.

På profilnivå vet harnessen **mixen**: vilka format som bär serien och hur mycket ren marknadsföring som ryms.

## Pilot: formatkort (`video/format/kort.mjs`)
Tio klipp från mondocoatbridge, babulsofficial, kebabbabes, jirvelius och sharkamericansushi. Varje klipp lästes av två modeller via Lovable: `3.1-flash-lite` (ca 6 s per klipp) och `3.1-pro-preview` (ca 30 s per klipp). Resultatet ligger i `data/format/<modell>/`.

Fälten:
- **Formatet:** kärna, mall med [platser], lås.
- **Var dragningskraften kommer ifrån:** idé, framförande, produktion, produkt och trend, fördelat på 100.
- **Inbjudan:** varför tittaren stannar.
- **Säljet:** hur verksamheten säljs, alltså ingen, fond, vävd eller direkt.
- **Tröskeln:** produktionskrav, tankehöjd, antal personer och agerande.
- **Trend:** egen idé, anpassad trend eller ren trend.
- **Överföring:** fem verksamhetstyper, var och en med en version.
- **Serie:** om formatet kan bli ett återkommande inslag.

**Vad piloten visade:**
- Mallarna går att använda direkt. Till exempel: "[en anställd] serverar [två helt olika produkter]… kunden frågar vilken som är vilken… testar dem på ett opassande sätt och flyr."
- **Pro ser mer.**
  - Den hör trendljudet hos jirvelius och kallar klippet ren trend. Lite kallar samma klipp en egen idé.
  - Den lägger värdet i fish and chips på produkten, 50 av 100. Lite lägger 30 på idén.
  - Lite blåser upp idén: 7 av 10 klipp får minst 60 för idé.
- **Pro skiljer idén från personen.** Mondocoatbridges sketcher får idé 40–50 och framförande 40–50. Det stämmer med ägarens ögontest om balans.
- **Två fält säger ingenting än.** Överföringen ligger nästan alltid på 4–5, och serie är nästan alltid sant. Frågorna måste göras skarpare, till exempel "vad går förlorat hos en pizzeria", eller genom att modellen tvingas välja de två verksamheter där formatet passar bäst.

## Hypoteser att pröva på data
- **H1.** LeTrend-värde finns där dragningskraften bärs av idé och framförande, och där produktionskravet är högst 2. Prövas genom att jämföra ja-profilerna med de övriga.
- **H2.** Inom en typ skiljer sig överföringen och tröskeln mer än mellan typer. Då är formatet rätt enhet och typen fel enhet.
- **H3.** Balans, som hos mondocoatbridge och babulsofficial, betyder att de flesta klippen bärs av idén och att produktklippen är inslag, med säljet mest vävt och inte direkt.
- **H4.** Klipp som bärs av idén går bättre mot kontots egen norm än klipp som bärs av produkten. Det stämmer med sketch +0,11 och matporr −0,10 i [residual.md](residual.md).
- **H5.** Serier syns som återkommande mallar inom en profil, och de går att hitta genom att klustra mallarna.

## Ägarens svar (3 nov)
1. **Bärtestet.** Frågan är om idén fortfarande bär om någon mindre skicklig instrueras att spela rollen. Ett klipp som hänger på **personen**, **lokalen**, **en rekvisita** eller **en nisch** som bara den verksamheten har, är inte värdefullt. Ingen förväntar sig stordåd av en sketch. CM sållar i regel bort sådant före ingest, så bärtestet fungerar också som förfilter.
2. **Visningsklipp är en egen klass.** Montage och grafiktunga klipp, där maten är själva idén, är godkända i en LeTrend-serie men är inte kärnan när serien formas. Det behövs en gradering av hur mycket som vilar på montaget och grafiken. Den ska också skilja mellan rätter som bär för att de är unika, som etiopisk mat där tillagningen i sig är intressant, och rätter som bär för att de är aptitliga, som en fet burgare.
3. **Mixen.** Det kan vara vävt eller ha tydlig kontrast. De bästa profilerna väver in säljet nästan rakt igenom, med människorna i fokus och sketcher och humor. Det ska kännas som ett tv-program eller ett inside-skämt för de unga som tittar.
4. **Omfånget.** I dag gäller det restauranger, barer och kaféer. Senare tillkommer gym, butiker som jirvelius och livsmedelsbutiker som ICA, Coop och Hemmakväll. Den röda tråden:
   - en lokal och återkommande personer
   - en lekfull och livlig känsla
   - en självbild om marknadsföring. Antingen gör kontot "det som förväntas av en content creator", eller så gör det det som är roligt men höjer kvaliteten och håller ramarna: inte vulgärt och inte skadligt för varumärket.

   TikTok driver med klassisk marknadsföring, och det är det LeTrend är. Proffsigt utförande är tillåtet, och kunder med högre budget ska också servas. Kärnan är ändå en spelplan för verksamheter som inte tar sig själva på för stort allvar, men som vill ha bra resultat i sociala medier.

## Kalibrering, del 1: modellerna mot varandra (3 nov)
Urvalet består av 30 klipp i fem grupper: balans 6, ja 8, förebild 5, gamla banken 6 och strukna 5. De är spridda över typerna, slumpade med fast frö och ligger i `data/format/kalib/urval.json`. Formatkort v1 finns i `video/format/v1.mjs`. Ägarens lista ligger i [formatkalibrering.md](formatkalibrering.md).

| Jämförelse | Bärtest exakt | Bärtest ≥4 | Roll | Visning |
|---|---|---|---|---|
| Pro mot Pro, samma prompt (omtest) | 60 % | 90 % | 93 % | 87 % |
| Pro med principer mot utan | 30 % | 77 % | 87 % | 93 % |
| Text (Lites beskrivning) mot Pro på video | 33–43 % | 83 % | 87–93 % | 87 % |
| Lite mot Pro, båda på video | 20 % | – | 70 % | 83 % |

**Vad det säger om ingest och prompter:**
- **Lite duger inte för omdömen.** Den satte bärtest 5 på 29 av 30 klipp. För beskrivning duger den: omdömen som Pro gör på Lites text hamnar lika nära Pro på video som på Pros egen text.
- **Att tolka en gång och döma på text håller.** Där bärtestet läses som ja eller nej (≥4) är överensstämmelsen 83 %, nära omtestets 90 %. Fälten för roll, visning, idé och framförande ligger på omtestets nivå. Det sparar inte tokens per anrop, eftersom Pros resonemang dominerar kostnaden. Vinsten är att varje nytt fält, ny princip eller ny modell kan prövas på alla klipp utan att videon skickas igen.
- **Bärtestet på skalan 1–5 är brus.** Bara det binära svaret är stabilt, så det bör frågas som ja eller nej, eller tas som medianen av flera körningar.
- **Principerna flyttar omdömet.** Med och utan principer är Pro överens om bärtestet i bara 30 % av fallen. Vilken variant som ligger närmast ägaren avgör om principerna hör hemma i prompten.
- **Förlust per verksamhetstyp skiljer fortfarande inte klippen åt** (snitt 3,96 och instabilt). Fältet ska tas bort eller göras om.
- **Grupperna går i rätt riktning men n är litet.** Strukna konton har lägst idéandel (7 mot 27–36) och högst visningsgrad (2,8). Alla fem strukna fick rollen inslag.

## Miles-pass 1 med ägaren (3 nov, klipp 1–10, ca 1 h)
Transkriptet är `Desktop/transkript2.txt`. Kodningen av omdömena ligger i `data/format/kalib/agare.json`.

**Modellen v1 mot ägaren:** bärtestet stämmer i 8 av 10 klipp (Pro med principer), men rollen bara i 3 av 10. Modellen använde "inslag" som slasktratt och satte aldrig "utanför". Båda missarna på bärtestet (3 och 6) var klipp med låg produktion som modellen straffade: "the model is quite like horny for the general, like, super hookiness".

### Nya distinktioner
1. **Premiss och exemplar.** Ett format kan bära en kanal fast klippet är svagt, som i klipp 9: "it can be the main type of content, but the piece of content may not be good". Det gäller också tvärtom: klipp 10 är välgjort men går inte att flytta.
2. **Rollen är relativ till mixen**, och ägaren använder sju roller:
   - **huvudnummer:** det som visar verksamhetens huvudvärde
   - **stomme:** kanalens huvudinnehåll
   - **återkommande inslag:** en kategori som bär sig själv och används med avsikt
   - **glitter**
   - **utfyllnad:** en godtagbar "dud"
   - **engångsbit:** en karaktärsbit som inte går att upprepa
   - **annan kanal:** Instagram-polerat eller reklamfilm

   Ett inslag måste "own itself". Klipp 7 är därför inget inslag.
3. **Relation framför krok.** Det LeTrend värderar är att lära känna personalen och verksamheten. En visning väcker intresse men bygger ingen relation.
4. **Replikering har fler delar:**
   - tid och antal scener
   - någon på plats med öga för produktion (CapCut-vana)
   - hur bundna bilderna är till just den menyn: "you'd have to swap every single shot"
   - personalfrihet, alltså civila kläder och att spela karaktärer
   - om en CM kan skriva exakta instruktioner

   En CapCut-mall kan kopieras exakt om meny och miljö är lika, men som inspiration tappar den gnistan.
5. **Persona med röd tråd.** Innehåll som kräver en stark persona är meningsfullt bara om personan är varumärkets röda tråd: "it doesn't really make sense as a one-off".
6. **Humorns räckvidd.** Absurd vardagshumor förstår de flesta, medan dejtingteman är smala.
7. **Skala.** Giveaways i volym är kedjornas spel. För en enskild enhet fungerar de knutna till kalendern, till exempel en gång i kvartalet.
8. **Eskalering.** En lång tagning utan eskalering kräver karisma, medan ett klipp med uppbyggnad och vändning bär med en vanlig anställd.
9. **Plattformsspråk.** Instagram-polerade klipp, som riktar sig till kvinnor 25–35 och lovar en upplevelse, är en annan fil än TikTok-språket med självironi och personer i fokus.
10. **Alternativkostnad.** Ett klipp som inte engagerar tar ändå en plats i flödet.
11. **Förhöjning.** Samma idé kan bli minnesvärd med rätt rollbesättning eller utförande, till exempel om en äldre man gör det absurda i klipp 1.

### v2 (`video/format/v2.mjs`) mot klipp 1–10 (träning, inte test)
| Variant | Bär | Roll | Anm. |
|---|---|---|---|
| v1 Pro med principer | 8/10 | 3/10 | Tre roller |
| v2 Pro | 7/10 | 5/10 | Sju roller, fångar annan kanal (8, 10) |
| v2 Pro, omkörning | 7/10 | 4/10 | |
| v2 Pro med kontots klipp som kontext | 6/10 | 4/10 | |

- **Omtest av v2 (30 klipp).** De beskrivande kategorierna är stabila: persona 97 %, eskalering 93 %, produktionsöga 93 %, plattform 87 % och humor 87 %. De värderande skalorna är brusiga: vasshet 60 %, exemplar 63 %, formatpotential 63 % och roll 73 %.
- **Kontexten** (kontots övriga klipp i en rad var) flyttar bärtest och roll mer än omtestets brus gör, men inte närmare ägaren. Tesen H15 får inget stöd med så tunn kontext.
- **Kvar efter v2:** modellen blandar ihop formatets roll med exemplarets kvalitet (klipp 9). Den överskattar "charmiga misstag" (6, kallat stomme). Den ser inte att en karismapitch inte går att upprepa (7).

### Hypoteser efter pass 1
- **H6. Två axlar.** Formatvärde och exemplarvärde ska bedömas var för sig. Rekommendationen till en CM är den lägsta av dem.
- **H7. Rollen ska härledas ur stabila beskrivande fält, inte frågas direkt.** Fälten är plattform, visning, persona, eskalering, skala, relation och premiss. Exempel: instagram_polish eller reklamfilm ger annan kanal. Stark persona utan röd tråd, eller ingen eskalering med skådespel ≥4, ger engångsbit. Prövas genom att en regel skriven *innan* pass 2 jämförs med modellens direkta roll mot ägaren på klipp 11–30.
- **H8. Relation förklarar ägarens roller bättre än inbjudan eller krok.**
- **H9. Modellen överskattar polering.** Modellens bärtest korrelerar mer med produktionskravet än ägarens gör. Prövas på klipp 11–30.
- **H10. Personabundet innehåll är konsekvent inom de konton där det fungerar.** Där är personan röd tråd. Hos andra är den spridd. Prövas på profilnivå i banken.
- **H11. Eskalering ersätter karisma.** Klipp med vändning bär med en vanlig anställd, långa tagningar utan vändning gör det inte.
- **H12. Instagram-polering är en egen klass som går att känna igen** (inga personer, CapCut-övergångar). Den går sämre mot kontots norm på TikTok, i linje med montage −0,07 och matporr −0,10.
- **H13. Specificitet kan mätas** som hur stor andel av bilderna som måste bytas, och den förutsäger ägarens bedömning att något inte går att flytta.
- **H14. Harnessen behöver en profil av kunden:** enhet eller kedja, personalens kapacitet och frihet, och miljö. Formatets tröskel jämförs mot den profilen.
- **H16. Parvisa jämförelser är stabilare än betyg på absolut skala.** Frågan blir "vilket av två klipp är det bättre exemplet?" och resultatet räknas med Bradley–Terry, som i NASTA. Det prövas på vasshet och exemplar, som i dag ligger runt 60 % i omtest.
- **H17. Seriens mix** (profilnivå): de profiler ägaren gillar har en stomme av personbärande format, återkommande inslag med avsikt (ungefär var femte video) och lite annan kanal. Prövas genom att 20 klipp per profil beskrivs billigt (Lite) och döms på text (Pro), för ja-profilerna mot de strukna.

## Miles-pass 2 med ägaren (3 nov, klipp 11–20) och första riktiga testet
Transkriptet är `Desktop/transkript3.txt`. Omdömena är kodade i `agare.json`, med `funktion` (kött, stöd, utanför) och `bibliotek` (ja, villkorat, nej) för klipp 1–20.

### Testet: klipp 11–20 hade inte rättats när v2 och regeln låstes
| Variant | Personalen klarar det | Funktion (3) | Roll (7) |
|---|---|---|---|
| Majoritetsgissning | 5/10 | 4/10 | – |
| v1 Pro med principer | 4/10 | 5/10 | – |
| v2 Pro | 3/10 | 5/10 | 4/10 |
| v2 Pro, omkörning | 4/10 | 6/10 | 4/10 |
| v2 Pro med kontext | 5/10 | 6/10 | 4/10 |
| Låst regel (H7) | – | 6/10 | 4/10 |

**Slutsats:** modellens bedömning av om personalen klarar ett klipp håller inte på nya klipp. Den blir inte bättre än att alltid gissa "ja", och bilden från klipp 1–10 var för optimistisk. Felen följer ett mönster:
- Modellen säger "ja" där ägaren ser ett poleringsgap (16, 17), karisma (18) eller ett event som inte går att planera (12).
- Den säger "nej" där ägaren ser låg insats (13, 20): "it doesn't have an expectation of getting something right".

Den låsta regeln (H7) är lika bra som modellens direkta omdöme på funktion, 6 av 10. Det räcker inte för att avgöra H7.

### Vad ägaren egentligen bedömer
1. **Biblioteket är huvudfrågan:** "it works for the business, but it doesn't work for the library". Ett biblioteksklipp är planerat och har en fristående, stark idé som går att abstrahera, bärs av människor och fungerar i många miljöer.
   - Frågan om personalen klarar klippet är meningslös om klippet inte ska rekommenderas: "you're kind of assuming that you would recommend it in the first place".
   - Ordningen ska därför vara bibliotek först, sedan replikering.
2. **Planerat eller fångat.** Eventklipp (12, 20, 30) reagerar på något som redan händer. LeTrend är planerat innehåll. Ett event kan i bästa fall få en bildlista med exempel på vad man ska göra och undvika.
3. **Träffsäkerhet som sannolikhet:** "probably 50% chance". Briefen är en guide, inte en manual, och kunden spelar in utan handhållning. Två saker avgör:
   - poleringsgapet: "looks easy until you actually try to make it look that good"
   - precisionskravet, alltså om något måste bli exakt rätt
4. **Mänsklig förankring.** Visning och marknadsföring utan berättare blir "just a pretty picture" (11, 16).
5. **Förankring i verkligheten.** Sketcher i en filmvärld (19) är kött, men om de ska vara hela köttet behöver de blandas med direkt tilltal och publikkontakt.
6. **Två sorters strategi.** Idébaserade sketcher, som är det biblioteket är byggt för, skiljer sig från dialogprofiler som bygger en egen värld. Kebabdudes (18) bygger på direkt tilltal, quiz och monolog: "a different beast entirely", effektivt men inte överförbart.
7. **Segment.** Finare verksamheter kan bära visuella klipp som signalerar exklusivitet (16), medan enkla verksamheter inte kan det. Den rekommenderade mixen beror på kundsegmentet.
8. **Produktion skyddar konstiga idéer:** "the better production something has, the more you probably can get away with weird ideas".
9. **Evergreen eller tidsbundet.**
10. **Glitter är inte tomt per definition.** Om klippet fångar och förtjusar är det mer än glitter (14).
11. **Sju roller var för många.** "I think we had 3 before". Ägaren vill ha de bredaste kategorierna som ändå räcker.
12. **Ett perceptionsfel.** Modellen missade metaskämtet i redigeringen i klipp 14. Med en riktad fråga ser Pro skakningen även i originalet. Nedsaktat fyra gånger blir det skarpare, med detaljer som den tomma restaurangen och desperationen, men kostar fyra gånger fler tokens. I v3, utan exempel, missades skämtet ändå.

### v3 (`video/format/v3.mjs`) och prognoser låsta innan pass 3
v3 frågar om biblioteket först, med fem delfrågor:
- om klippet är planerat
- om det har en fristående idé
- om människor bär idén
- om idén fungerar i många miljöer
- hur stor träffsäkerheten är, med precisionskrav, poleringsgap och sannolikhet

Därefter kommer om personalen klarar det, funktionen i tre lägen, redigeringsskämt, strategityp, segment och tid. Med `--exempel` ligger ägarens omdömen om klipp 1–20 i prompten (H19).
- Prognoserna för klipp 21–30 är låsta i `data/format/kalib/v3-last-21-30.json`.
- **Med exempel blir modellen stabilare.** Omtestet stämmer i 97 % för biblioteket, 93 % för funktionen och 87 % för personalen, mot 53–73 % i v2.
- **Exemplen läcker.** Med exempel får v3 10 av 10 på klipp 1–20, eftersom modellen känner igen klippen. Den siffran ska inte användas.
- v3 säger nej till biblioteket för 8 av 10 klipp bland 21–30. Pass 3 frågar ägaren om det är för strängt.

### Hypoteser efter pass 2
- **H18. Biblioteksbeslutet är summan av fem grindar:** planerat, fristående idé, människor i centrum, bred miljö och träffsäkerhet. Prövas på 21–30 genom att regeln "alla grindar öppna" jämförs med modellens direkta beslut.
- **H19. Ägarens kodade exempel slår enbart principer.** Prövas på 21–30, med och utan exempel.
- **H20. Perceptionen behöver en egen fråga om redigeringen** och, när det gäller, nedsaktning. Prövas på de klipp i banken som har mycket efterarbete.
- **H21. Personalfrågan ska ersättas av sannolikheten att kunden träffar rätt**, med poleringsgap och precisionskrav, inte av vad personalen klarar.
- **H22. Profiler har strategityper:** idébaserade sketcher, dialog och egen värld, premiumvisning med vardagshumor, och kedjekampanj. Biblioteket tjänar främst den första typen. Prövas genom att 20 klipp per profil märks med strategi och fördelningen jämförs mellan ja-profiler och strukna.
- **H23. Mixen behöver förankras.** Profiler där sketcherna är huvudinnehåll och ägaren gillar dem har också direkt tilltal. Prövas på profilnivå.

## Miles-pass 3 (3 nov, klipp 21–27) och det första helt ärliga testet
Transkriptet är `Desktop/transkript 4.txt`. Passet slutade efter klipp 27, så 28–30 saknar ägarens omdöme. v3-prognoserna låstes innan passet.

| Låst prognos, klipp 21–27 | Bibliotek | Funktion | Personal |
|---|---|---|---|
| Majoritetsgissning | 3/7 | 3/7 | 4/7 |
| v3 med principer (P) | 4/7 | 2/7 | 5/7 |
| v3 med ägarens exempel (E) | 3/7 | 2/7 | 2/7 |
| v3 E, omkörning | 3/7 | 3/7 | 4/7 |
| H18, fem grindar ur P:s fält | 2/7 | – | – |

- **H19 får inget stöd.** Ägarens exempel ankrade modellen i strängheten från pass 2. Den sa nej till 22, 23 och 24, där ägaren sa villkorat eller ja.
- **H18 får inget stöd.** Grindarna är för stränga.
- **Ytterlägena stämmer.** I testmängden träffar modellen alla tydliga fall (21 och 25 ute, 26 kärna). Den missar i mitten.
- **Modellen hittar villkoren men gör dem till ett nej.**
  - 24 får "endast vid nyöppning", men domen blir nej.
  - 15, 22 och 23 får segmentet premium, men domen blir nej.
  - 27 får kedja och utåtriktad personal, men domen blir villkorat.

  En omvandling i efterhand, där nej plus ett villkor blir villkorat, ger 5 av 7 på testet för båda varianterna. Den är utforskande och inte låst, men pekar åt samma håll.

### Ägarens svar delar sig i tre zoner (klipp 1–27)
| Zon | Klipp | Vad som avgör |
|---|---|---|
| **Kärna** (bibliotek ja, kött) | 14, 19, 26 | En fristående, absurd eller igenkännbar premiss med människor, som tål dåligt utförande: "even if you fail, it's still funny" |
| **Mitten** (villkorat eller ja, stöd) | 1, 2, 3, 6, 11, 15, 22, 23, 24, 16, 27 | Villkor hos *kunden*: segment, kapacitet (någon som kan filma, CapCut, en energisk värd, en publik plats), situation (nyöppning, lansering, högtid), hur lik menyn och lokalen är, och hur ofta det används |
| **Ute** (bibliotek nej) | 5, 7, 8, 10, 12, 17, 20, 21, 25, samt 4, 9, 13, 18 | Inget innehåll ("doesn't raise the ceiling"), eventfångst, eller bärs av en persona eller dialog |

### Nya distinktioner i pass 3
1. **Feltolerans** är motsatsen till poleringsgapet. En absurd premiss är rolig även när den görs dåligt (26). Det kan vara det starkaste kännetecknet för kärnhyllan.
2. **Det systemet kan rätta räknas inte mot klippet.** Ett segt tempo eller lång dialog ska AI-redigeringen rätta senare (26). Bedöm premissen och strukturen, inte tempot.
3. **Biblioteket har hyllor:**
   - kärna
   - en CapCut-del, som referens för komposition och inte för att kopiera rätt för rätt (22, 23)
   - sällan använda situationer, som en PSA vid flytt (24): "it would probably be in the library, but no one would use it because they wouldn't know that it's there"

   Det sista kräver att CM kan **hitta klipp efter situation**.
4. **Utfall i data.** Ägaren använde själv gillanden ("13 likes", 23) och kontots storlek ("simplicity works when the profile is already huge", 21). Harnessen bör visa klippets residual mot kontots egen norm.
5. **Kontotyp.** 22 är en matguide och 25 en lekhall för barn. Banken innehåller alltså konton utanför restaurangbranschen, och de behöver märkas.
6. **Biblioteket och funktionen är olika saker.** 27 hör till biblioteket med villkor men har funktionen utanför i de flesta fall.
7. **Biblioteket ska höja taket.** Det räcker inte att något fungerar för just den verksamheten.

### Slutsats: harnessen är i mitten ett matchningsproblem
Kärnan och ute är egenskaper hos klippet, och där klarar modellen sig. I mitten avgörs saken av *kunden*: vem som filmar, segmentet och situationen. Där ska modellen inte fälla en dom, utan **extrahera klippets villkor**. Det gör den redan ganska bra. Harnessen matchar sedan villkoren mot en kundprofil. Det svarar på grundfrågan: CM får det hen vill ha när kärnklippen är säkra och mittenklippen kommer med sina villkor mot kundens förutsättningar.

## E1, E2 och E4: att skilja klippet, modellen, ägaren och bruset (3 nov, pågår)
Experimenten valdes av ägaren efter frågan om vad i omdömena som är klippet, modellen, ägarens egen läsning, LeTrend som känsla och brus. Skripten ligger i `video/format/`: `lager.mjs`, `e1*.mjs`, `e2.mjs`, `e4*.mjs`.

### E2: ingen är facit (Dawid–Skene, klipp 1–27, klar)
Ägaren och tio modellvarianter är bedömare. v3 med exempel är utesluten, eftersom den sett ägarens svar. Resultatet ligger i `data/format/kalib/e2.json`.
- **Modellerna bildar ett block.** Det skattade "sanna" omdömet blir modellernas samsyn, och ägaren får lägst träffsäkerhet mot det: 0,43–0,52, i nivå med Lite. Det betyder inte att ägaren brusar. Modellerna är samma Pro med olika prompter och därför inte oberoende. Dawid–Skene kan här inte avgöra vem som har rätt, men den visar att **ägaren och modellerna mäter olika saker**.
- **Ägarens "stöd" sväljer modellernas kött och modellernas utanför.**
  - Klipp 1, 4, 6 och 11 är svagare sketcher som modellerna kallar kött.
  - Klipp 22, 23 och 24 är visningar och PSA:er som modellerna kallar utanför.

  Ägaren bedömer hur klippet används i mixen, villkorat av kunden. Modellerna bedömer vad klippet är. Det stämmer med zonmodellen ovan.
- **Om personalen klarar det:** ägarens "delvis" motsvarar oftast modellernas "ja". Ägaren är mer försiktig och utgår från hur det fungerar i praktiken.
- **Drift.** Andelen bibliotek nej hos ägaren var 60 % i pass 1, 50 % i pass 2 och 29 % i pass 3. v3 låg på 60–71 % för samma klipp. Det är det första tecknet på att ägaren blev mer inkluderande i pass 3, i takt med att idén om hyllor växte fram. n är litet.

### E1: vilka lager är verkliga? (preliminärt)
Lovable-krediterna tog slut efter 227 av 540 anrop, med 9–17 av 30 klipp per villkor. Alfa nedan bygger bara på bedömningar som finns. Variansandelarna är snedvridna av utfyllnaden och redovisas inte förrän körningen är klar.
- **27 av 43 lager klarar kriteriet** (Krippendorffs alfa ≥ 0,667).
  - De beskrivande lagren är mycket pålitliga, med alfa 0,85–0,97: personer, tilltal, personal och gäst, tävling, händelse, högtid, montage, matandel och tal.
  - Bland konstrukten håller **fristående idé (0,87), humor (0,82) och relation (0,77)**.
- **Ägarens nya begrepp håller inte som modellmått än.** **Feltolerans** får alfa 0,57, och modellerna är exakt överens bara i 34 % av fallen. **Poleringsgap** får 0,65. De behöver ett annat mätsätt, som parvisa jämförelser eller ägaren själv.
- **Det som syns i tid och klippning är svagt:**
  - redigeringsskämt 0,31
  - krok 0,26
  - absurd 0,41, och Lite får 0,20 här
  - slowmotion 0,13
  - eskalering 0,46
  - trendljud 0,64

  Modellerna ser inte samma sak vid 1 bild per sekund.
- **Hur prompten är formulerad påverkar knappt.** Det är valet av modell som spelar roll, till exempel för bildkvalitet och feltolerans.

### E4: förregistrerat, väntar på krediter
Förregistreringen ligger i `data/format/e4/forregistrering.json` och låstes innan något utfall setts. Urvalet är 1 385 klipp från 104 konton och laddas ner till `Downloads/letrend-e4`. Märkningen kräver Lovable-krediter.

### E3-lite: vad ägarens omdömen faktiskt följer (klipp 1–27, utan kostnad)
Ägarens poäng jämfördes med modellernas samsyn per lager ur E1, med driften mellan passen bortrensad. Resultatet ligger i `data/format/kalib/e3-avslojat.json`. Med n = 27 är |rho| > 0,38 ovanligt för slumpen, men med ett 40-tal test väntas ett par falska träffar.

- Biblioteksbeslutet följer:
  - **lokalen i bild** (+0,59)
  - **självironi** (+0,57)
  - **en spelad situation** (+0,43)
  - **eskalering** och **vändning** (+0,39 vardera)
  - **absurditet** (+0,38)

  Det går emot händelse, matandel, utomhus och gäster i bild (−0,30 till −0,34).
- **Feltolerans (+0,07) och relation (+0,16) följer inte beslutet**, mätt med modell.
- **Lokalen:** ägaren säger att ett klipp som hänger på lokalen inte har värde, men beslutet följer hur mycket av lokalen som syns. Mellan raderna betyder det verksamheten som *scen*, inte som beroende.
- Det **avslöjade indexet** låstes som tillägg till E4-förregistreringen innan analysen: plus lokal, självironi, roll, vändning och eskalering; minus händelse, matandel och montage.

### Perception: tre videotyper (30 klipp × 2 billiga modeller × 2 körningar, 360 anrop)
Resultatet ligger i `data/format/perc/analys.json`.

| Videotyp | Tokens | Modellerna överens, tid och klippning | Alla lager |
|---|---|---|---|
| Original (1 bild/s) | 5 404 | 0,455 | 0,696 |
| 4× nedsaktat | 8 007 | 0,470 | 0,665 |
| 2×2-rutnät (4 tidpunkter per bild) | 5 465 | **0,515** | 0,695 |

- **Rutnätet förbättrar tidslagren gratis:** krok, eskalering, kamera och effekter blir bättre. Lokalen och bildkvaliteten blir sämre, eftersom upplösningen halveras.
- Nedsaktningen lönar sig inte.
- **Feltolerans blir sämre med båda, så den är ett begreppsproblem och inte ett perceptionsproblem.**
- Redigeringsskämtet i klipp 14 sågs inte av någon billig modell i någon videotyp. Bara Pro med en riktad fråga har sett det.
- **Ingest:** originalet för rummet, rutnätet för tiden och Pro för redigeringsskämt.

### E1 färdig (540 av 540 anrop)
- **29 av 43 lager är stabila.**
- **Promptens formulering förklarar cirka 0 % av variansen i alla lager.** Hur man frågar spelar ingen roll, bara vilken modell man frågar.
- Modellvalet väger tungt för krok (53 %), mimande (48 %), feltolerans (37 %), eskalering (34 %) och lokal (32 %).
- Ren slump dominerar redigeringsskämt (57 %) och slowmotion (76 %).

### E4: LeTrend-likhet mot utfall (1 322 klipp, 96 konton, inom konto, förregistrerat)
Resultatet ligger i `data/format/e4/analys-gemini-3.1-flash-lite.json`. Märkt med Lite på original.

| Förregistrerad hypotes | Resultat | Beslut |
|---|---|---|
| HE4a: det uttalade LeTrend-indexet → räckvidd | rho +0,137, 71 % av kontona positiva, p = 0,0005, båda tidshalvorna (+0,08/+0,18), leave-one-out 100 % | **håller** |
| HE4b: indexet → gillanden och delningar | gillanden +0,119 (p = 0,0005), delningar per visning −0,070 | håller för gillanden, **förkastas för delningar per visning** |
| HE4c: personer → räckvidd | andel personer +0,197, spelad situation +0,112 | **håller** |
| HE4d: polering ger inte räckvidd | ingen positiv effekt | **håller** |
| HE4e: det avslöjade indexet → räckvidd | +0,124, p = 0,0005 | **håller** |
| HE4f: det avslöjade indexet slår det uttalade | +0,124 mot +0,137 för räckvidd, 0,094 mot 0,119 för gillanden | **förkastas**: ägarens ord slår ägarens val, med liten marginal |

**LeTrend-likhet är alltså prestation och inte bara smak**, åtminstone för räckvidd och gillanden.

**Portföljen.** Kommentarer, gillanden och delningar räknas per visning, så den absoluta mängden är räckvidd plus andelen per visning. Siffrorna är rangkorrelationer inom konto (`format/e4-absolut.mjs`).

| Innehåll | Räckvidd | Gillanden (absolut) | Kommentarer (absolut) | Delningar (absolut) |
|---|---|---|---|---|
| Kött: spelad situation, humor, dialog, vändning, självironi, fristående idé | +0,10 till +0,16 | +0,13 till +0,20 | ±0 | +0,03 till +0,14 |
| Frågor till publiken: tävling, uppmaning, erbjudande | ±0 | ±0 | +0,10 till +0,15 | +0,08 till +0,10 (inte tävling) |
| Tilltal och personer i bild | +0,12 till +0,20 | +0,13 till +0,22 | +0,16 | +0,11 till +0,17 |
| Trendljud, montage | −0,13 till −0,15 | −0,15 | −0,08 till −0,13 | −0,09 till −0,11 |

Ägarens mixintuition får en mätbar grund. **Köttet ger räckvidd, gillanden och delningar. Stödet, alltså frågan till publiken, ger kommentarer. Direkt tilltal lyfter allt. Trendljud och montage sänker allt.**

**Visningsregeln** jämför medelresidual med och utan egenskapen inom samma konto, med permutationstest:

| Inom samma konto | Räckvidd | Konton där det gäller |
|---|---|---|
| Matvisning med en person i bild minst tre fjärdedelar av tiden | **×2,00** | 78 %, p < 0,001 |
| Klipp som inte är sketcher men har direkt tilltal | ×1,58 | 72 % |
| Matvisning som montage | ×0,70 | 33 % |
| Matvisning med trendljud | **×0,58** | 33 % |
| Sketch med trendljud | ×0,81 | inte säkert (p = 0,24) |

Ägarens princip "visning behöver en människa som förankrar den" innebär i siffror en fördubblad räckvidd. Straffet för trendljud sitter i visningarna, inte i sketcherna. **Det här blir ett räcke i harnessen:** en visning ska ha en person i bild och eget ljud.

**Profilnivån** jämför ägarens valda konton (ja och förebilder, 51) med den gamla banken (50):
- De valda kontona har mer direkt tilltal (+0,87 sd), färre trendljud (−0,94 sd), fler erbjudanden och uppmaningar (+0,74 och +0,68 sd), mer personer i bild och mindre montage.
- De har *inte* fler sketcher, mer humor eller mer självironi.
- Ägarens ögontest på profiler väljer alltså tilltal och personer som säljer öppet utan trendljud. På klippnivå väljer ägaren däremot sketcher och lokalen som scen. **Det är två olika konstruktioner på två nivåer.**

**Strategityper.** k-means på kontots mix gav fyra typer (`format/e4-typer.mjs`):
1. **Visning med trendljud:** 32 konton, 44 % valda.
2. **Dialogsketch:** 14 konton, **79 % valda**.
3. **Tilltal och erbjudande:** 30 konton, 67 % valda. Här finns alla förebilderna: kebabdudes, bramsburgers, kebabbabes och jirvelius.
4. **Trendsketch utan säljande:** 20 konton, 30 % valda. Här finns ägarens två balanskonton, mondocoatbridge och babulsofficial.

**H17, blandningen, förkastas.** Entropin i kontots mix skiljer inte de valda kontona från banken (p = 0,78). Det som skiljer är mindre visning: banken har 36 % visningsklipp, ja-kontona 25 % och förebilderna 14 %.

### Vad experimenten betyder för harnessen (sammanfattning 3–4 nov)
1. **Ingest.** Lite på originalet räcker för de stabila lagren, som är billiga och pålitliga inom modellen. Ett 2×2-rutnät förbättrar tidslagren gratis. Pro behövs bara för redigeringsskämt. Promptens formulering spelar ingen roll, så arbetet ska läggas på schemat och modellvalet, inte på formuleringarna.
2. **Kärnhyllan bekräftas av utfallen.** Personer, spelad situation, humor, vändning, självironi och fristående idé ger räckvidd och gillanden mot kontots egen norm. LeTrend-indexet håller som förregistrerad hypotes.
3. **Stödhyllan har en funktion: kommentarer.** Tävling, uppmaning och erbjudande ger kommentarer men inte räckvidd. En mix av kött och frågor till publiken är en portfölj över olika mått, och inte bara en smakfråga.
4. **Räcken med siffror.** En visning med en person i bild ger ×2,00 i räckvidd. Trendljud ger ×0,58 och montage ×0,70. Direkt tilltal lyfter alla mått.
5. **Två nivåer.** Biblioteket, alltså klippen, väljer sketcher och lokalen som scen. Mixen, alltså profilen, väljer tilltal och personer som säljer öppet. Harnessen behöver båda: biblioteket som idéförråd, och tilltalet som grundton genom hela kundens flöde.
6. **Det som inte går att mäta med modell:** feltolerans och poleringsgap. De är begreppsproblem, inte perceptionsproblem, och förblir CM:s eller ägarens bedömning, eller mäts parvis.
7. **Ägaren och modellerna mäter olika saker.** Modellen bedömer vad klippet är, ägaren hur det används för en viss kund. Mitten av biblioteket är därför ett matchningsproblem mot en kundprofil.

## Sekvenser och serier: flera klipp i en fil (4 nov)
Klippen skiljs åt med titelkort ("KLIPP n", 1 s) och är kodade i 360×640. Endpointen tar högst cirka 16 MB per anrop. Skripten heter `video/format/sekvens*.mjs` och `serie*.mjs`.

**A. Trohet** (Lite, 5 klipp per fil, framlänges och baklänges, 25 klipp)
| | Exakt överensstämmelse, 43 lager |
|---|---|
| Ensamt klipp, omtest | 0,946 |
| Samma klipp i sekvens mot ensamt | 0,807 |
| Sekvens framlänges mot baklänges | 0,777 |
| Position 1 → 5 | 0,85 → 0,83 → 0,80 → 0,77 → 0,75 |

- Det som är sant eller falskt håller i sekvens, med 0,92–1,00: tävling, högtid, dialog, vändning och självironi.
- Skalorna kollapsar och blir relativa till grannklippen: relation går från 0,92 till 0,44, och poleringsgap, lokal, fristående idé och bildkvalitet tappar också.
- Sekvensen kostar 38 % färre tokens per klipp.
- **Slutsats:** fakta kan tas in i sekvens, betyg ska tas klipp för klipp.

**C. Jämförelse** (Pro rangordnar 5 bedömda klipp, 10 sekvenser)
- Rangordningen är stabil: samma ordning framlänges som baklänges ger rho 0,80, och placeringen i sekvensen påverkar lite.
- Mot ägaren ger rangordningen rho 0,15, mot 0,41 för v3 klipp för klipp.
- Grupp 5 (klipp 21–25, pass 3) går helt åt motsatt håll. Där var ägaren mest generös.
- **H16 får inget stöd mot ägaren.** Skillnaden i begrepp väger tyngre än metoden.

**B. Serie** (Pro, 5 klipp från samma konto, 6 konton)
- Modellen hittar återkommande personer, format, röd tråd och om mixen är planerad. Det går inte att se i ett enskilt klipp.
- För mondocoatbridge föreslog modellen på egen hand att "personalen från sketcherna också presenterar maten". Det är visningsregeln från E4.

### Serietestet: 40 konton × 10 klipp i datumordning (Pro, cirka 23 000 tokens per anrop)
Förregistreringen ligger i `data/format/serie/forregistrering.json` och analysen i `serie/analys.json`. Rimlighetskontroll: av de klipp där serien ser en återkommande person säger Lite, som ser klippet ensamt, att personal syns i 90 %. För övriga klipp är andelen 49 %.

| Förregistrerat | Resultat | Beslut |
|---|---|---|
| HS1: huvudfrontfiguren → räckvidd | ×1,28, 57 % av kontona, p = 0,13 (28 konton) | förkastas (rätt riktning) |
| HS2: återkommande format → räckvidd | ×1,25, p = 0,085 | förkastas (rätt riktning) |
| HS3: anknytning till annat klipp → räckvidd | ×1,37, p = 0,11 (17 konton) | förkastas (rätt riktning) |
| HS1–HS3 för gillanden och delningar | ±0 | ingen effekt |
| HS4: ägarens valda har fler klipp med en återkommande person | 73 % mot 51 %, p = 0,025 | **håller** |
| HS4: inside och planerat enligt modellen | skiljer inte | förkastas |
| HS5: återkommande personer ger stabilare utfall | rho −0,17 | svagt |

**Utforskande**, inte förregistrerat:
- En återkommande person i klippet ger ×1,76 (p = 0,002).
- Om klippet redan har en person i bild ger en återkommande person ×1,35 (inte säkert).
- **Bland sketcher ger den ×2,85** (8 konton, p = 0,08). Bland övriga klipp med person ger den ×1,06.

Hypotesen blir att en återkommande person verkar som **karaktär i sketcher**, i linje med ägarens tes om tv-program och inside-skämt, men inte i tilltal eller visningar. Den prövas på nya konton som HS6.

### Replikering av serietestet: 53 nya konton × 10 klipp (4 nov)
Analysen ligger i `data/format/serie-r/analys.json`, och den sammanslagna datan (93 konton, utforskande) i `serie/analys-sammanslagen.json`.

| Låst i förväg | Upptäckt (40) | Replikering (53) | Beslut |
|---|---|---|---|
| HS1: klipp med kontots huvudfrontfigur → räckvidd | ×1,28, p = 0,13 | **×1,39, 64 %, p = 0,015**, gillanden ×1,24 (p = 0,001) | **håller** |
| HS2: återkommande format → räckvidd | ×1,25, p = 0,09 | **×1,30, 65 %, p = 0,025** | **håller** |
| HS3: anknytning till annat klipp | ×1,37, p = 0,11 | ×1,04 | förkastas |
| HS6: återkommande person bland sketcher | ×3,22 (8 konton) | ×1,92, p = 0,18 (10 konton) | rätt riktning, inte säker |
| Kontroll: återkommande person mot ny person bland klipp där personal syns | ×1,75, p = 0,007 | **×1,62, p = 0,005** | **håller på nya konton** |
| HS4: ägarens valda konton har fler återkommande personer | 73 % mot 51 %, p = 0,03 | 65 % mot 65 % | förkastas, replikerades inte |
| HS5: fler återkommande personer ger stabilare utfall | rho −0,17 | rho −0,33 | samma riktning |

Kontrollraden valdes efter upptäcktsdatan, men höll på nya konton. Sammanslaget ger HS1 ×1,34 (p = 0,005) och HS2 ×1,28 (p = 0,006).

**Vad det betyder:** ägarens tes om tv-program och inside-skämt håller mot utfall. Ett klipp med kontots **återkommande person** når ×1,3–1,7 längre än kontots övriga klipp, också jämfört med klipp där personal syns men är ny. Ett **återkommande format** ger ×1,3. Det syns bara när klippen läses som serie, aldrig i ett enskilt klipp.

**Konsekvens för harnessen:** CM bör förankra anpassade klipp i kundens återkommande personer och format, och bygga serier i stället för engångsklipp. Harnessen behöver därför en **seriebild av kunden**: vilka frontfigurer och format kunden har. Den byggs med ett serieanrop med Pro på tio klipp, cirka 23 000 tokens per kund.

## Harnessen v0: bibliotek, kundprofil, matchning och anpassning (4 nov)
Kedjan är byggd i fem steg, ett i taget. Alla skript ligger i `video/format/h-*.mjs`, `v4.mjs` och `kort4.mjs`, och all data i `data/format/harness/`.

1. **Urval** (`h-urval.mjs`, låst): sex kunder och ett bibliotek på 67 klipp.
   - Kunderna är pizzeriamums, chickenstreet.canada, kebabbabes, blackstonesteakhouse, babulsofficial och anettesrestaurang. De täcker strategityperna, kapacitetsnivåerna och ett konto utan frontfigur.
   - Biblioteket består av 27 kalibreringsklipp, 25 kärnkandidater och 15 mittenkandidater ur E4. Kandidaterna valdes på Lite-lagren och på att klippet gick bättre än kontots norm.
2. **Formatkort v4** (Pro, cirka 12 600 tokens per klipp) beskriver klippets *krav*:
   - platser med typ (person, produkt, lokal, replik, text)
   - zon
   - roller och om kundens frontfigur kan ta huvudrollen
   - skådespel, efterarbete och produktion
   - lokal, produkt, verksamheter, segment, situation, persona och ljud
   - visningsregeln, funktion och anpassningsrisk

   Kärnkandidaterna ur E4 hamnade till 72 % i kärnan. v4 stämmer med ägarens biblioteksbeslut i 11 av 25 fall och är strängare på visningar och PSA:er. Den missade metaskämtet i klipp 14 igen. **Hyllan kureras därför: ägarens zon gäller där den finns, och modellens zon för resten.**
3. **Kundprofil** (`h-kund.mjs`) bygger på serien och Lite-lagren, med en syntes av Pro på text. Den innehåller verksamhet, segment, frontfigurer med roll och styrka, hur mycket personalen spelar, max antal personer, produktion, efterarbete, lokal, produkter, persona, format, luckor och vad som bör undvikas. Produktionsnivån skiljer inte kunderna åt, eftersom Lites bildkvalitet ligger kring 4,6 överallt.
4. **Matchning** (`h-match.mjs` och `h-rerank.mjs`):
   - **Grindar** avgör vad som är genomförbart: zon, verksamhet, segment, personer, efterarbete, skådespel högst personalens vana + 1, persona och produktion. Hos anettesrestaurang, där personalen aldrig spelar, återstår 7 av 67 klipp.
   - **Mjuk passform** bygger på kunskapen från E4 och serietestet: frontfigur, luckor i portföljen, visningsregeln, ljud, lokal och produkt.
   - **Pro rangordnar sedan som en CM** efter ton, produkter och format.
   - **Det som fungerade:** rollerna knyts till kundens egna personer och produkter.
   - **Det som är svagt:** kärnhyllan är liten, så samma breda sketcher återkommer hos flera kunder.
5. **Anpassning och validering** (`h-valid.mjs`):
   - Pro skriver kundens version av förstahandsvalet: roller, scener, repliker, bild, vad som byts och vad som behålls, en brief och hur kunden vet att det blev rätt. Anpassningarna tillämpar visningsregeln av sig själva.
   - Valideringen är låst i förväg i `validering/forregistrering.json`. Per kund visas sex klipp blint: 2 från Pros rangordning, 2 från den regelbaserade matchningen och 2 lockklipp. HM1: R+D > L. HM2: R > D. HM3: ägaren och Pro är överens om passformen. HM4: minst 4 av 6 anpassningar kan skickas.
   - Underlagen är `miles/pass-4-underlag.md` och `pass-5-underlag.md`, och prompterna `pass-4.txt` och `pass-5.txt`. Ägarens svar ska kodas i `validering/agare.json`, och sedan körs `node format/h-valid-analys.mjs`.

Krediter: cirka 10–11 av de 31 som fanns kvar gick åt till harnessen v0.

### Miles-pass 4: matchningen mot tre kunder (4 nov, delresultat)
Transkriptet är `Desktop/transkript 5.txt`. Svaren kodades i `validering/agare.json` innan grupperna lästes. Ett svar som "4 or 5" utan avgörande kodas som 4,5. `h-valid-analys.mjs` hade en bugg: klippets eget fält `konto` (avsändaren) skrev över kunden, så testet parade inom 11 avsändare i stället för 3 kunder. Buggen är rättad, och testet är oförändrat. Tre av sex kunder är bedömda. Testet låstes för alla sex, så det här är ett delresultat.

| | Passform (ägaren) | Rekommenderas |
|---|---|---|
| R, Pros rangordning | 4,08 | 4 av 6 |
| D, regelmatchningen | 2,75 | 5 av 6 |
| L, lockklipp | 3,00 | 3 av 6 |

| Låst i förväg | Resultat (3 kunder) |
|---|---|
| HM1: R+D > L | +0,42, p = 0,25, **håller inte** |
| HM2: R > D | **+1,33, p = 0,012**. Positiv eller noll hos alla tre kunder, oavsett om halvorna avrundas uppåt eller nedåt |
| HM3: ägaren mot Pros passform | rho 0,76 (n 8, bara klipp med Pros passform) |
| HM4: anpassningen kan skickas | 3 av 3 (två med små ändringar, en som den är) |

Per kund: pizzeriamums 1R 4,5 · 2L 3 · 3R 4,5 · 4D 4,5 · 5D 4 · 6L 3. babulsofficial 1R 4 · 2D 2 · 3D 3 · 4R 5 · 5L 3 · 6L 2. anettesrestaurang 1D 2 · 2D 1 · 3L 3 · 4L 4 · 5R 3,5 · 6R 3.

**Vad det betyder:**
- **Pro som CM fungerar, grindarna inte.** Pros rangordning slår regelmatchningen hos alla kunderna. Regelmatchningen ligger under lockklippen.
- **Kundprofilen var fel hos anettesrestaurang.** Profilen säger att personalen aldrig spelar, och grinden lämnade 7 av 67 klipp. Ägaren säger att kontot "in latter days" också gör sketcher. Lockklippet där var en enkel sketch, samma klipp som pizzeriamums 4, och fick 4. HM1 faller på det klippet. Seriebilden av tio klipp missar alltså en kurs som har ändrats nyligen. Det är ett argument för att vikta de senaste klippen tyngre, eller för att CM bekräftar profilen.
- **Montaget utan person** (berlinerdonermalmo, alla tre kunderna) fick 2–3 och rekommenderas inte: ingen krok, ingen person, ingen kärnidé att anpassa.
- **Kantighet är en egen dimension.** Gen Z-självironi och vuxna parteman passar inte en familjär kund (anettesrestaurang 1 och 2), och sketcher som är för fåniga sänker passformen lite hos en kantig kund (babulsofficial 4).

**Ägaren om anpassningarna:**
- Skriv inte in slumpen. "Intentionally miss with the dough" blir falskt och stelt. Anpassning A kändes för planerad, mer Instagram än TikTok.
- Om CM väljer en sketch, ska den rekommenderas för vad den är: "You wouldn't change the script to fit the client." Att skriva om beats är kreativt skrivande och riskabelt. De praktiska scenbytena kan personalen sköta själv.
- Skilj på **personen som fokus**, där karisman bär klippet, och **personen som behållare**, som bara säljer konceptet. Det ändrar vad briefen ska kräva av personen.
- Avsikten med harnessen: originalklippet är ryggraden. Scener som måste ändras, till exempel för att produkten byts, renderas om enkelt (platshållare, 3D), och harnessen ska veta *när* och *varför* en scen behöver ändras.

**Inför pass 5:** Ägaren bedömde först klipp A1 för avsändaren och inte för kunden, och betyget gjordes om. Prompten bör säga det redan i första repliken.

### Miles-pass 5 och hela valideringen (4 nov, 6 kunder)
Transkriptet är `Desktop/transkript 6.txt`. Kunderna var chickenstreet.canada, kebabbabes och blackstonesteakhouse. Hos kebabbabes hamnade ägaren och Miles i otakt i ordningen: klipp 3 ("you too") bedömdes aldrig, och betyget för montaget hör till klipp 4. Två kodningar är osäkra och står i `agare.json`. Hos kebabbabes 5 sa ägaren "4 with post-processing, 2 or 3 without", och eftersom LeTrend förutsätter inget efterarbete kodas det 2,5. Hos blackstonesteakhouse 5 höll ägaren isär "a visual 5, but a Latrend 2", och det kodas 3.

| Låst i förväg | Pass 4 (3 kunder) | Alla 6 kunder (35 klipp) | Beslut |
|---|---|---|---|
| HM1: R+D > L | +0,42, p 0,25 | +0,40, p 0,13 | **förkastas** |
| HM2: R > D | +1,33, p 0,012 | +0,46, p 0,12 | **förkastas** (rätt riktning) |
| HM3: ägaren mot Pros passform | rho 0,76 (n 8) | rho 0,18 (n 18) | **förkastas** |
| HM4: minst 4 av 6 anpassningar kan skickas | 3 av 3 | 5 av 6 | **håller** |

Medelpassform: R 3,79, D 3,27, L 3,13. Pass 5 per kund: blackstonesteakhouse 1D 3,5 · 2L 2,5 · 3R 4 · 4R 4,5 · 5L 3 · 6D 4. chickenstreet.canada 1D 5 · 2D 3 · 3R 4,5 · 4R 3 · 5L 4,5 · 6L 3. kebabbabes 1R 2,5 · 2D 4 · 4L 2,5 · 5R 2,5 · 6L 4.

**Klippet väger tyngre än matchningen.** Åtta klipp visades för flera kunder. Bland dem står klippet självt för cirka två tredjedelar av variansen i ägarens betyg, och kunden för en tredjedel. Sketchen med utrustningen (edessa.bistro) fick 4–5 hos alla. Montaget utan person (berlinerdonermalmo) fick 2–3 hos alla sex. Mest skiljer det för klippen med tilltal och personlighet: favoritprodukten med misstag (dirtytaco.se) fick 4,5, 3, 2,5 och 4,5, och tävlingen (louisburger.cph) 3 och 4. Det stöder ägarens tes att biblioteket är huvudfrågan.

**Luckorna styrde fel.** Matchningen gav poäng för klipp som fyller kundens luckor, och Pro motiverade valen med det. Ägaren bedömer passform som *fortsättning på kundens nuvarande linje*: "We're not asking the chicken shop to be improved, right?"
- Hos kebabbabes valde Pro sketcher för att fylla luckan "sketcher 14 %" och fick 2,5. Ägaren läser kontot som ett eget, högt producerat tilltal, där en sketch bara passar om premissen är stark (edessa.bistro, 4), och där tävlingen, ett lockklipp, fick 4.
- Hos chickenstreet.canada fick visningen med person i bild 3 (luckan "matvisning med person"). Kontot gör det kanske en gång på 50 klipp, och "no modification would actually change that".
- Där profilen och linjen stämde (pizzeriamums, babulsofficial, blackstonesteakhouse) gav Pro R ≥ D ≥ L. Där profilen var fel eller luckan pekade bort från linjen (anettesrestaurang, kebabbabes, chickenstreet.canada) föll det.

**LeTrends gräns.** Ett klipp som bara fungerar med efterarbete eller ett produktionsteam ska inte rekommenderas: "the recommended piece should be strong enough even if it doesn't have editing". Förlagan blir sämre ju längre den ligger från kundens färdiga version: kebabbilder är en dålig förlaga för ett steakhouse.

**Om anpassningarna:** Kärnan håller i 5 av 6. Felen ligger i rösten.
- Repliker ska låta som verklig kommunikation, skrivna i personalens eller CM:s egen röst (anpassning C).
- Inskrivna misstag ("at least one charming mistake") antar ett syfte som kunden inte har (anpassning B).
- En lista över sekvenser ger lika vikt åt det som inte bär. Harnessen behöver förstå helheten och vad som är kärnan: "if your assumptions going in is that it needs to look a certain way, then you will miss the mark."

**Konsekvenser för harnessen, som förslag:**
1. Byt den mjuka passformen från att fylla luckor till att fortsätta kundens linje. Luckorna blir ett andra steg, som CM väljer medvetet.
2. Vikta biblioteket först. Ett klipps grundvärde (stark premiss, går att göra utan efterarbete) bär två tredjedelar.
3. Kundprofilen ska bygga på de senaste klippen och bekräftas av CM.
4. Anpassningen ska ange kärnan och vad som bär, inte en scenlista, och lämna replikerna till kundens egen röst.

## Harnessen v5: doktrin, grundvärde, linje och kärna (4 nov, pågår)
Ägaren gav klartecken till de fyra förslagen efter valideringen och bad att Gemini som ingestmotor och logiken ur alla transkript och experiment ska spela ihop. Doktrinen ligger i [doktrin.md](doktrin.md) och `video/format/doktrin.mjs`, och alla steg läser den.

| Steg | Skript | Data | Läge |
|---|---|---|---|
| Formatkort v5: helhet, grundvärde, språk, förlaga, beats | `format/v5.mjs`, `kort5.mjs` | `harness/v5/` | 35 av 67 klipp, 11 av 19 bedömda |
| Kundlinje ur de tio senaste klippen, kursändring, att bekräfta | `format/h-linje.mjs` | `harness/linje/` | 1 av 6 (pizzeriamums) |
| Matchning: grund + linje + förlaga, Pro som CM | `format/h-match5.mjs` | `harness/match5/` | kod klar, Pro-delen inte körd |
| Anpassning: kärna, det som bär, fritt, person, ton | `format/h-anpassa5.mjs` | `harness/anpassning5/` | kod klar, inte körd |
| Utvecklingsutvärdering mot pass 4–5 | `format/h-dev5.mjs` | | se nedan |

**Första utvecklingssiffran.** Det är inget test, eftersom doktrinen skrevs med ägarens ord om samma klipp. v5:s grundvärde ensamt, alltså klippet utan någon kund, följer ägarens passform med **rho 0,59 (n 23)**. Pros passform i v0 gav 0,18 (n 18). Vikterna i `grund()` sattes ur doktrinen innan jämförelsen. Linjevikten justerades en gång efter pizzeriamums: strategin väger lätt för kärnklipp och tungt för mittenklipp, i linje med doktrinens "kärna bär överallt".

**Stopp: krediterna.** Båda Lovable-kontona har slut på krediter (402). Vertex i projektet Hagen säger "issues with your billing account, please resolve / pay your outstanding balance", och AI Studios förbetalda saldo är slut. Det som återstår är cirka 32 kort, 5 kundlinjer, matchning, anpassning och omtest, i storleksordningen 1 miljon tokens, eller ungefär 40–50 kr på Vertex med Pro-priserna i `typer/gemini.mjs`. `GEMINI_VAG=vertex` tvingar Vertex även när en AI Studio-nyckel finns.

**Pass 6 är testet.** Prognoserna låses innan ägaren ser något. Designen korsar klipp och kunder, så att samma klipp visas för två eller tre kunder. Det är den bästa designen för att skilja matchning från klippets värde, och den svarar på att jämförelsedatan är för tunn. Nya kunder, och klipp som ägaren inte sett. Miles nämner klippets innehåll med numret, säger i första repliken att klippet bedöms för kunden, och speglar sparsamt.

### v5 körd (4 nov, Lovable konto 3: cloud-setup-compass)
Alla 67 bibliotekskort och alla 6 kundlinjer är klara. **Kundlinjen hittade kursändringen hos anettesrestaurang av sig själv:** kontot "har gått från att sakna personlighet och enbart visa matmontage till att helt och hållet frontas av barn som gör sketcher". Kebabbabes läses som tilltal och kampanj, i linje med ägaren.

Utvecklingsdata, alltså inget test (`node format/h-dev5.mjs`), mot ägarens 35 bedömningar:

| | rho mot ägaren | Inom klipp (vilken kund passar bäst) |
|---|---|---|
| v0, Pros passform | 0,18 (n 18) | – |
| v5, bara grundvärdet | 0,57 | – |
| v5, grund + linje + förlaga | 0,61, och 0,68 efter justering 2 | 12–10, och 13–7 efter justering 2 |
| v5, Pro som CM | 0,56 | – |

Justering 2 gjordes efter att felen inom klipp setts, med ägarens egna ord som grund:
- Ett snällare klipp straffas inte.
- Ett lugnare klipp straffas hos en snabbare kund.
- En frontfigur räcker för att bära ett klipp med personen i fokus.

## E5: modell × prompt (40 klipp med ägarens omdöme, förregistrerat)
`format/e5.mjs`, data i `data/e5/` och `data/format/e5/`.

| Villkor | Passform | Bibliotek | Tokens | Sekunder |
|---|---|---|---|---|
| Pro + doktrin | 0,57 | 0,41 | 11 400 | ~43 |
| Pro + doktrin, omkörning | 0,58 | 0,42 | 11 300 | 43 |
| Pro utan doktrin | 0,50 | 0,31 | 10 200 | 43 |
| **Argon** (gemini-4-argon) + doktrin | 0,56 | 0,37 | 9 200 | 22 |
| **3.8 Flash** + doktrin | 0,62 | 0,31 | 9 800 | 23 |
| Medel av fyra körningar | 0,61 | 0,42 | | |

- **HE5a förkastas.** Doktrinen höjer överensstämmelsen med ägaren bara med 0,07–0,10. Det den gör är att hålla ihop värdebegreppen: utan doktrinen stämmer hyllan med Pro i bara 33 % av fallen. De beskrivande lagren påverkas knappt, och mycket av doktrinen ligger redan i schemats beskrivningar.
- **HE5b håller.** Argon är lika bra som Pro, dubbelt så snabb och använder 20 % färre tokens.
- **HE5c håller delvis.** Flash klarar 13 av 18 lager inom 10 procentenheter från Pros omtest. Värdelagren håller, men strategi och kantighet är svagare.
- **HE5d håller.** De beskrivande lagren är stabilare (~93 %) än de värderande (~81 %).
- **Taket ligger kring 0,6 för alla modeller.** Det sätts av begreppen och ägarens eget brus, inte av perceptionen.
- Bryggan tar video för Gemini (3.1 Pro, 4 Argon, 3.5–3.8 Flash, 3.1 Flash-Lite), men inte för Claude, GPT eller Omni (fel API).

## Abstraktionslagret: förkastat (utveckling)
Residualerna mot klipp 1–27 visade att ägaren kallar montage villkorade ("not deserve to throw out"), medan v5 lägger dem ute. Hypotesen var tre sorters överföring: idén, formen eller ingenting (`format/abstraktion.mjs`, en textkedja ovanpå korten). Som skala ger lagret rho 0,22 mot biblioteket, mot 0,41 för grundvärdet, eftersom "form" inte skiljer villkorat från nej (3, 15, 22, 23 mot 5, 8, 10, 17). **Villkoren för ett montage sitter i detaljerna, alltså meny, segment och vem som filmar, och inte i kategorin.** Kedjan video → kort → textomdöme fungerar och är billig: 67 klipp i 6 anrop.

## E6: preferens mot nytta (299 klipp, 29 konton, inom konto, förregistrerat)
v5-kort med Flash på 300 klipp ur E4 som ägaren inte sett, mot visningar och gillanden jämfört med kontots egen norm (`format/e6.mjs`).

| Låst i förväg | Resultat | Beslut |
|---|---|---|
| HE6a: grundvärdet → visningar | **+0,17, p = 0,003** | håller |
| HE6b: grundvärdet → gillanden | **+0,16, p = 0,006** | håller |
| HE6c: klipp på kontots egen strategi → visningar | −0,10 | **förkastas, åt motsatt håll** |
| HE6d: "höjer taket" är bara preferens | **+0,24, p = 0,001** | förkastas: det är också nytta, och det starkaste lagret |
| HE6e: klippberoende → färre visningar | −0,06 | förkastas (rätt riktning) |

Grundvärdet förutsäger utfall bättre än LeTrend-indexet i E4 (+0,14). Visningsregeln replikerar: visning med person i bild ger +0,20 i visningar.

## Sanning, preferens och nytta per lager
`format/triad.mjs`, `data/format/triad.json`. Sanning mäts som stabilitet mellan Pro och Pros omkörning, preferens som ägarens omdöme och nytta som E6.

| Klass | Lager | Betydelse |
|---|---|---|
| **Båda** | höjer taket, sketchvärld, hylla, premiss, kött, idén bär, vändning, utan efterarbete, bundna bilder (−) | LeTrends robusta kärna: ägarens smak och utfallen pekar åt samma håll. Biblioteksnivån |
| **Bara nytta** | bärs av karisma (+0,14), bärs av struktur, krok, TikTok mot Instagram | Fungerar hos avsändaren men flyttar inte. Karisma hör till **kunden** (profilen), inte till biblioteket |
| **Bara preferens** | roller i sketch, att stöd straffas, **fortsättning på kundens linje** (−0,10 i utfall) | Varumärkesräcken. De ska kalibreras mot ägarens och kundens preferens, inte mot räckvidd |

**Vad det betyder för planen och för klippet:**
- **Plannivån** frågar om klippet är bra i sammanhanget. Svaret är grundvärdet, som både preferens och nytta stöder, så där kan harnessen vara sträng.
- **Klippnivån** frågar hur klippet görs i kundens riktning. Fortsättningen på kundens linje är en preferens, alltså ett räcke för varumärket och ingen prestationsregel. Utfallen säger att avsteg från linjen inte kostar räckvidd, så räcket bör vara mjukt. Ett klipp med högt grundvärde utanför linjen kan föreslås som ett medvetet avsteg, och CM och kunden väljer.
- Räckena kalibreras alltså i två steg: först mot nytta där nytta finns, sedan mot preferens för det som är varumärke.

## Pass 6: låst test (4 nov)
`format/h-pass6.mjs`, låst i `data/format/harness/pass6/forregistrering.json`.
- **Kunder:** fratelli.stockhol (sketchvärld), blubnan.liljeholm (premium och stämning, med en magdansös) och cafepomflora (visning, ett familjärt kafé).
- **Klipp:** 4 delade klipp för alla tre kunderna, valda där v5 spår störst skillnad mellan kunderna. Dessutom 1 eget klipp per kund och 3 omtest ur pass 4–5.
- **Hypoteser:** HP6a (v5 total), HP6b (inom klipp), HP6c (Pro som CM), HP6d (anpassningarna) och HP6e (ägarens omtest).
- **Pro som CM** ger nästan bara 1:or till blubnan.liljeholm och cafepomflora. Det är en prognos som prövas.
- **Underlag och prompt:** `miles/pass-6-underlag.md` och `miles/pass-6.txt`. Svaren kodas i `pass6/agare.json`, och sedan körs `node format/h-pass6-analys.mjs`.

**Förslag till v6, efter pass 6:**
- Fortsättningen blir ett mjukt räcke, och ett avsteg med högt grundvärde märks som medvetet.
- Karisma flyttas från biblioteket till kundprofilen.
- Argon eller Flash ersätter Pro i ingest (hälften av tiden, lika nära ägaren), med medel av två körningar.
- Doktrinen kortas där schemat redan bär den.

## Fördjupning efter E6 (4 nov kväll, utforskande)
`format/e6-djup.mjs` och `data/format/e6/djup.json`.
- **Fortsättning delar sig efter dimension.** Samma strategi (−0,10) och samma kantighet (−0,08) som kontots vanligaste ger ingen nytta. Samma sorts personnärvaro ger +0,07. Serietestet visade att kontots återkommande person och format ger ×1,3–1,7. *Vem* som syns är alltså nytta, medan *vilken genre* klippet har är preferens.
- **Samspel:** bland klipp med högt grundvärde ger samma strategi −0,12 i visningar. Ett starkt klipp utanför linjen kostar inget och verkar ge något.
- **Formelns räckvidd varierar.** Grundvärdet ger +0,28 i konton som mest visar mat (11), +0,12 i tilltalskonton (7) och −0,01 i sketchkonton (4). Det ger +0,23 i stora konton mot +0,12 i små. LeTrend-formeln lyfter mest där kontot inte redan gör det.
- **Två stora kluster** (principalkomponenter över 366 klipp):
  - **K1 (38 %):** premiss, kött, att klippet fungerar utan efterarbete och krok, mot Instagram och bundna bilder. Följer både preferens (+0,69) och nytta (+0,21).
  - **K2 (16 %):** sketch och roller mot tilltal, stöd och karisma. Följer preferens (+0,51) men inte nytta (−0,03).

  K2 följer ägarens passform hos både sketchkunder (+0,65) och tilltalskunder (+0,42), så den är mest en allmän LeTrend-smak.
- **Dina exempel sprids sämre än dina principer** (`format/knn.mjs`). Ägarens omdömen om 38 klipp hänger ihop med liknande klipp (rho 0,41 i leave-one-out med k = 3). Spridda till E6 via likhet ger de bara +0,11 till −0,02 i nytta, mot +0,17 för grundvärdet.

## E7: en skarp fråga mot de många lagren (förregistrerat)
En textkedja: Flash eller Pro läser videon till ett kort, och sedan bedömer Pro bara beskrivningen med en enda fråga: hur mycket värde som finns kvar när en annan verksamhet gör sin version med telefon och vanlig personal (`format/e7.mjs`, `e7-analys.mjs`).

| | Passform (35) | Bibliotek (25) | Nytta i E6 (299) |
|---|---|---|---|
| grund() ur v5-lagren | 0,57 | **0,41** | +0,17 (p 0,002) |
| En fråga | 0,55 | 0,22 | **+0,22 (p 0,0007)** |
| Medel | 0,59 | 0,34 | +0,19 |

- **HE7a förkastas.** Den enda frågan klarar inte biblioteksbeslutet.
- **HE7b håller.** Den enda frågan är den bästa prediktorn för nytta hittills.
- **HE7c förkastas.** Medlet slår inte den enda frågan på nytta.
- **Tolkning:** prestationen fångas av en helhetsfråga om överförbart värde. Ägarens biblioteksbeslut bärs av doktrinens distinktioner (hylla, planerat mot event, persona), som säger vad som *hör till* LeTrend och inte bara vad som presterar.

## Design v6: två mått som inte blandas, och en räckeskarta
Harnessen ger CM två mått per klipp och kund, och väger aldrig ihop dem till ett tal:
1. **LeTrend-värde (preferens):** grund() ur lagren, plus fortsättning och ton. Det svarar på om klippet hör till LeTrend och passar kunden.
2. **Förväntad nytta:** den enda frågan i E7, plus visningsregeln. Det svarar på om klippet troligen går bra.

När måtten går isär är det information: ett klipp med hög nytta och lågt LeTrend-värde är ett medvetet avsteg som CM tar ställning till.

**Räckeskartan**, där varje räcke har sin grund och sin stränghet:

| Räcke | Nytta | Preferens | Stränghet |
|---|---|---|---|
| Värdet finns kvar utan efterarbete | + (E6) | + | strängt |
| Visning med person i bild och eget ljud | ×2 (E4), +0,20 (E6) | neutral | strängt (nytta) |
| Inget trendljud i visning | ×0,58 (E4) | − | strängt |
| Planerat, inte fångat (event) | ± | − | mjukt, kategori: situation |
| Fortsättning på kundens strategi och genre | −0,10 | + | **mjukt varumärkesräcke**: avsteg tillåts med ett högt grundvärde |
| Kantighet uppåt mot kunden | ± | − | kundens gräns, bekräftas av CM |
| Karisma bär klippet | + hos avsändaren | − i biblioteket | på kundnivå: bara om kunden har en frontfigur i fokus |
| Stöd (tävling, uppmaning, erbjudande) | kommentarer, inte räckvidd | − | på mixnivå: en andel för kommentarer |
| Återkommande person och format | ×1,3–1,7 | + | förankra i kundens personer |

## E6-R: replikering på 30 nya konton (298 klipp, förregistrerat)
`format/e6r-analys.mjs` och `data/format/e6r/`. Samma kedja som E6: Flash 3.8 gör v5-kort, och Pro ställer E7-frågan på text. HR8 och HR9 lades till efter utforskning i E6 men innan någon E6-R-analys kördes.

| Låst i förväg | E6 (upptäckt) | E6-R (replikering) | Beslut |
|---|---|---|---|
| HR1: grundvärdet → visningar | +0,17 | **+0,17, p = 0,002** | **håller** |
| HR2: E7-frågan → visningar, minst som grund | +0,22 | +0,08, p = 0,09 | **förkastas**: försprånget i E6 var tur |
| HR3: samma strategi som kontot → färre visningar | −0,10 | −0,03, p = 0,32 | förkastas: fortsättning i genre är **neutral** för nyttan |
| HR4: samma personnärvaro → visningar | +0,07 | +0,09, p = 0,08 | rätt riktning |
| HR5: K1 → visningar | +0,21 | **+0,14, p = 0,008** | **håller** |
| HR5: K2 ≈ 0 | −0,03 | −0,10 | förkastas: sketchsmaken går snarare **lite emot** nyttan |
| HR6: formeln starkare i visningskonton än i sketchkonton | +0,28 mot −0,01 | +0,25 (12) mot +0,11 (6), tilltal +0,25 (5) | rätt riktning |
| HR7: höjer taket → visningar | +0,24 | **+0,15, p = 0,015** | **håller** |
| HR8: eget tal → visningar | +0,16 | **+0,19, p = 0,003** | **håller** |
| HR9: trendljud → färre visningar | −0,16 | −0,11, p = 0,07 | rätt riktning |

Eget tal följer också ägarens preferens (passform +0,46, bibliotek +0,26), och trendljud går emot den (−0,42 och −0,36). Ljudet hör alltså till båda.

**Det som står fast efter två oberoende urval (597 klipp, 60 konton):**
- **Grundvärdet** (premiss, att idén bär, utan efterarbete, krok, vändning, hylla) förutsäger nytta inom konto med +0,17 i båda urvalen, och ägarens preferens med 0,57.
- Att klippet **höjer taket** och har **eget tal** är både preferens och nytta.
- **Fortsättning i genre** (samma strategi som kontot) är bara preferens. För nyttan är den neutral, och den kostar inget.
- **Sketch framför tilltal** (K2) är ägarens och LeTrends smak, inte en prestationsregel.
- Formeln lyfter mest i konton som visar mat eller talar till kameran, och minst där kontot redan gör sketcher.

**v6-designen, rättad:**
- **LeTrend-värde (preferens)** = grundvärdet + sketchsmaken (K2) + det mjuka linjeräcket + tonen.
- **Förväntad nytta** = grundvärdet + eget ljud + person i visning.
- Grundvärdet är gemensamt och kan vara strängt. Det som skiljer måtten är smak och linje på ena sidan och ljud och person på den andra.
- E7-frågan behålls inte som nyttomått. Den v6-prognos som låstes för pass 6 med E7 som nytta prövas ändå, mot ägarens passform.

## Matchningens nyttosida: komplement, inte fortsättning (E6 + E6-R, 597 klipp, 60 konton, utforskande)
`format/e6-match.mjs`. Klipptyp mot visningar inom konto, per kontots vanligaste strategi:

| Klipptyp \ kontosort | visning (24) | tilltal (12) | sketchvärld (10) | kampanj (8) |
|---|---|---|---|---|
| sketch | **+0,20** | +0,13 | +0,04 | +0,09 |
| tilltal | **+0,24** | +0,14 | **+0,24** | +0,04 |
| visning | **−0,24** | −0,13 | −0,20 | −0,10 |
| grundvärdet | +0,27 | +0,18 | +0,06 | +0,09 |

- **Nyttan gynnar komplement.** Konton som mest visar mat vinner på personer, sketch och tilltal. Sketchkonton vinner på tilltal (+0,24) men inte på fler sketcher. Ägaren sa samma sak i pass 2: sketcher i en filmvärld behöver blandas med direkt tilltal och publikkontakt.
- **Karisma hör svagt till kunden.** Ett klipp med personen i fokus ger +0,09 hos konton där minst 30 % av klippen har en sådan person, och 0 hos andra.
- **Tilltal och eget tal lönar sig överallt**, +0,12 till +0,19, oavsett hur mycket kontot redan talar till kameran.
- **Kantighet mot kontot påverkar inte nyttan** (+0,05 åt båda hållen). Det räcket är rent varumärke.
- **Konsekvens:** v0:s luckor var nyttomässigt rätt men gick emot ägarens preferens. Matchningen har två svar: *fortsättning* (preferens och varumärke) och *komplement* (nytta). Harnessen ska visa båda, och konflikten mellan dem är en fråga till ägaren och kunden, inte en sak för modellen att avgöra.

## Biblioteket v6: kandidater ur 597 osedda klipp
`format/bibliotek-v6.mjs` skriver `data/format/harness/bibliotek-v6-kandidater.json`. Inget urval använder utfallen.
- **69 kärnkandidater** (hylla kärna, grund ≥ 5) från 36 konton, varav 60 sketcher och 6 tilltal.
- 85 mittenkandidater: 31 tilltal, 22 trend och 21 sketcher.
- 24 klipp för situationer.

Kärnhyllan kan alltså växa från cirka 25 till cirka 95 klipp, vilket svarar på v0:s svaghet att samma sketcher återkom hos alla kunder.

## Pass 7: parvis bibliotek, låst (4 nov)
`format/h-pass7.mjs` och `pass7/forregistrering.json`. Ägaren väljer det bättre biblioteksklippet i 20 par ur osedda E6- och E6-R-klipp och säger varför. I 10 par pekar grundvärdet och nyttan (nytta6) isär, och i 10 pekar de ihop.
- **HP7a:** ägaren följer grundvärdet i mer än hälften av paren.
- **HP7b:** i isär-paren följer ägaren grundvärdet oftare än nyttan.
- **HP7c:** därefter visas utfallen, för att se vem som hade rätt om räckvidden.

Det är H16 prövat på ägaren själv, och det första direkta testet av hur ägarens smak förhåller sig till nyttan. Underlag och prompt ligger i `miles/pass-7-underlag.md` och `pass-7.txt`, och analysen i `format/h-pass7-analys.mjs`.

## Portföljen och tiden (E6 + E6-R, utforskande)
`format/e6-portfolj.mjs`. Medel av rho inom konto:

| | Visningar | Gillanden | Kommentarer | Delningar |
|---|---|---|---|---|
| grundvärdet | +0,17 | +0,14 | −0,08 | −0,06 |
| kött | +0,13 | +0,15 | −0,17 | −0,12 |
| stöd | −0,02 | −0,02 | **+0,23** | **+0,15** |
| tävling | +0,03 | +0,03 | **+0,42** | +0,08 |
| tilltal | +0,14 | −0,02 | +0,07 | +0,12 |
| höjer taket | +0,19 | +0,08 | −0,13 | −0,15 |

Portföljen från E4 replikerar: kött ger räckvidd och gillanden, stöd och tävling ger kommentarer och delningar. Kommentarer och delningar räknas per visning, så kött sprids brett medan stöd engagerar dem som ser det. **Tiden:** grundvärdet ger +0,22 på kontots äldre klipp och +0,18 på de nyare (597 klipp från 2024–2026), så formeln är stabil över tid.

## E8: slår prompten i modellens gräns? (förregistrerat)
En kort doktrin, ungefär en tredjedel av längden, med bara grundvärdet och hyllorna (`doktrin.mjs` KORT, `v5.mjs` promptKort, `kort5.mjs --kortdoktrin`). Flash 3.8, samma 40 klipp som E5.

| | Passform | Bibliotek | Hyllan mot Pro | Tokens |
|---|---|---|---|---|
| Flash, full doktrin | 0,62 | 0,31 | 75 % | 9 800 |
| **Flash, kort doktrin** | **0,62** | **0,42** | **78 %** | **8 900** |
| Pro, full doktrin | 0,57 | 0,41 | – | 11 400 |

- **HE8a, HE8b och HE8c håller.** Den korta doktrinen är minst lika bra och billigare.
- **Linjen och utfallen hör inte hemma i ingesten.** De späder ut modellens uppmärksamhet på det klippet faktiskt är, och de behövs först vid matchningen.
- **Ingest i v6: Flash 3.8 med kort doktrin**, cirka 20 s och 8 900 tokens per klipp, gärna som medel av två körningar. Det ligger i nivå med Pro till ungefär halva tiden.

**Tillägg till E8:**
- Flash med kort doktrin, omkörning: 0,58 och 0,40. Argon med kort doktrin: 0,59 och 0,35. Medel av två Flash-körningar: 0,62 och 0,41. Medel av tre korta körningar: 0,63 och 0,41.
- Alla kombinationer landar på 0,57–0,63 mot passformen och 0,35–0,43 mot biblioteket. **Taket nås redan med en billig modell och en kort prompt.** Det som återstår är begrepp som ägaren avgör i detaljerna, som villkoren för ett montage eller ett event, och ägarens eget brus. Båda kräver nya intervjuer (pass 6 och 7), inte fler modeller eller prompter.

## Scenplanen: när och varför en scen görs om (4 nov)
`format/h-scener.mjs`. Ägaren i pass 4: originalet är ryggraden, och harnessen ska veta *när* och *varför* en scen behöver ändras, för omrendering med enkla platshållare. Scenplanen går igenom v5-kortets beats och kundens linje och ger varje beat en åtgärd:

| Åtgärd | När | Grund |
|---|---|---|
| behåll | beatet bär sig själv överallt | |
| fritt | beatet bär inte idén | anpassningen: lämna utrymme |
| byt produkt eller lokal | beatet är bundet till en annan produkt eller lokaldel | förlagsavståndet |
| frontfigur | beatet bärs av en persons karisma | karisma hör till kunden (e6-match +0,09) |
| risk | som ovan, men kunden saknar frontfigur | |
| eget tal | beatet är bundet till ett trendljud | eget tal +0,19, trendljud −0,11 (E6-R) |
| förenkla | beatet är bundet till redigering | utan efterarbete (både preferens och nytta) |

Sammanfattningen säger om anpassningen rör kärnan, alltså om ett kärnbeat måste göras om, eller bara stöd- och fria beats. Exempel: samma klipp (byens.hjerte) får frontfiguren i rollen hos fratelli.stockhol men "risk" hos cafepomflora, som inte har något ansikte. Produktjämförelsen är än så länge en grov ordheuristik.

## Pass 8: anpassningens form och scenplanen, låst (4 nov)
`format/h-pass8.mjs` och `pass8/forregistrering.json`. Det gäller de sex kunderna ur pass 4–5:
- Två anpassningar av **samma** källklipp i blind ordning: v0 (en scenlista) och v5 (kärna, det som bär, fritt, person och ton, i `anpassning5-samma/`).
- Scenplanen för källklippet.
- Sist punkterna "att bekräfta" i alla nio kundlinjer.

Hypoteserna:
- **HP8a:** v5 föredras hos minst 4 av 6 kunder.
- **HP8b:** ägarens val av scener stämmer med scenplanen för minst 70 % av beatsen.
- **HP8c:** beskrivande, andelen påståenden om kundlinjen som är fel.

Underlag och prompt ligger i `miles/pass-8-underlag.md` och `pass-8.txt`.

## Läget efter varvet utan ägaren (4 nov kväll)
Det som går att lära utan ägaren är gjort. Modellerna och prompterna har nått taket kring 0,6 mot ägaren (E5, E8). Grundvärdet och nyttans komponenter är replikerade på två oberoende urval (E6, E6-R). Matchningens nyttosida är kartlagd (komplement). Nästa kunskap kommer från ägaren: tre låsta pass (6, 7 och 8, cirka 1 h 45 min) prövar matchningen, preferensen mot nyttan och anpassningens form.

## E9: 2×2-rutnät mot original (avbrutet, krediterna slut)
`format/e9.mjs`, `kort5.mjs --rutnat` och `data/format/e9/`. Förregistrerat: 12 konton ur E6-R × 10 klipp i original och rutnät, plus ägarens 40 klipp i rutnät. Lovable konto 3 tog slut på krediter (402) efter cirka 20 kort per villkor. Det räcker inte för något beslut: 17 klipp från 2 konton, och 12 par mot ägaren (original 0,59, rutnät 0,47). Original och rutnät stämmer överens i 88 % för krok, vändning och hylla, och i 65 % för premiss. **E9 körs om när det finns krediter.** Skriptet hoppar över de kort som redan finns.

**Krediter:** konto 3 (cloud-setup-compass) klarade cirka 14 miljoner tokens. Det mesta gick till Flash i E6 och E6-R (2 × 3 miljoner) och till Pro. Alla vägar är nu stängda: Lovable 1–3, Vertex (en obetald faktura) och AI Studio (saldot slut).

## E10: grundvärdet ur billig perception (förregistrerat, inga anrop)
`format/e10.mjs` och `data/format/e10/modell.json`. En ridge-regression från E4:s beskrivande Lite-lager (3.1 Flash-Lite, cirka 4 800 tokens och under 0,001 $ per klipp) till v5:s grundvärde, korsvaliderad per konto på de 597 klippen i E6 och E6-R.

| Låst i förväg | Resultat | Beslut |
|---|---|---|
| HE10a: korsvaliderad rho mellan proxy och grund ≥ 0,6 | **0,84** | håller |
| HE10b: proxyn → visningar inom konto på osedda E4-klipp | **+0,124, p = 0,011** (606 klipp, 71 konton) | håller |
| HE10c: proxyn minst lika stark som E4:s LeTrend-index | +0,124 mot +0,125 på samma klipp | förkastas med en tusendel: lika |

- **Vad som går att abstrahera ur ren perception:** grundvärdet bärs i Lite-lagren främst av fristående idé (+0,80), sedan av självironi, roll, humor, andel person, relation och vändning. Tillagning drar ned.
- **Vad varje steg i kedjan tillför i nytta:**
  - Lite-lagren (proxyn eller E4-indexet): +0,12
  - v5:s värdelager med Flash: +0,17
  - med eget ljud och person i visning: +0,22–0,25
- **En kedja i tre nivåer för biblioteket:**
  1. Lite sållar banken med proxyn, nästan gratis.
  2. Flash med kort doktrin gör v5-kort på de bästa.
  3. Ägaren eller CM avgör hyllan och villkoren i mitten.

**Banken som tratt** (`format/e10-bank.mjs`, `data/format/harness/bank-tratt.json`). Bankens sållningstyp från 3.5 Flash-Lite ger ensam korsvaliderad rho 0,64 mot v5:s grundvärde. Medelgrundvärdet per typ:

| Sållningstyp | Medelgrundvärde | Antal på överlappet |
|---|---|---|
| relaterbar sketch | 3,3 | 190 |
| värdens provsmakning | 1,0 | 33 |
| direkt tilltal | 0,6 | 149 |
| annat | −1,4 | 34 |
| matporr och process | −1,5 | 191 |

Banken har 10 911 sållade klipp, varav **2 632 relaterbara sketcher från 109 konton** saknar v5-kort. Flash med kort doktrin på dem kostar cirka 23 miljoner tokens. Det är nästa steg för biblioteket när det finns krediter: nivå 2 i tratten på de bästa, och ägaren eller CM på mitten.

## E11: klipptyp mot utfall i hela banken (10 650 klipp, 88 konton, förregistrerat, inga anrop)
`format/e11.mjs`. Bankens sållningstyp (3.5 Flash-Lite) mot visningar inom konto. Resultaten är desamma utan de klipp som ingått i v5-körningar (9 958 klipp).

| Låst i förväg | Resultat | Beslut |
|---|---|---|
| HE11a: relaterbar sketch → visningar | **+0,09, p < 0,001** | håller |
| HE11b: matporr och process → färre visningar | **−0,11, p < 0,001** | håller |
| HE11c: direkt tilltal → visningar | **+0,05, p < 0,001** | håller |
| HE11d: sketch lyfter mest i matporrkonton (komplement) | +0,04–0,07 i matporrkonton, **+0,15–0,16 i sketchkonton** | **förkastas, åt motsatt håll** |
| HE11e: kontots vanligaste typ → färre visningar | +0,01 till +0,03 | förkastas: fortsättning är neutral till svagt positiv |

- **Tilltal är komplement.** Tilltal lyfter matporrkonton (+0,10 till +0,11) men inte sketchkonton (±0,01).
- **Rekonstruerbarhet** (hur lätt klippet är att göra om, 1–5) ger +0,13, och **andel med person** +0,12. Montage ger −0,08.

**Rättelse av matchningens nyttosida.** Komplementfyndet för sketch i E6 (+0,20 i visningskonton, 11 konton) höll inte i tio gånger större skala. Rätt bild är:
- **Sketch är fortsättning.** Sketcher går bäst där kontot redan gör sketcher. Ägarens preferens att sketchkunder fortsätter med sketch stämmer alltså också med nyttan.
- **Tilltal och personer är komplement.** En visningskund lyfter av att någon talar till kameran eller syns i bild. Det är visningsregeln i större form.
- **Fortsättning i sig är neutral** för nyttan. Den är ett varumärkesräcke som inte kostar något.
- v0:s lucka "sketcher för kebabbabes", ett tilltalskonto, hade alltså inte heller stöd i nyttan: sketch lyfter tilltalskonton med bara +0,06–0,07. Ägarens nej var rimligt även mätt i räckvidd.

**v6.1 låst för pass 6** (`format/h-v61.mjs`, `pass6/forregistrering-v61.json`), efter v5 och v6 men innan ägaren sett passet. Det är v6 med E11:s rättelse: sketch räknas som fortsättning hos sketchkunder, och tilltal och personer som komplement hos visningskunder. Pass 6 jämför nu tre låsta versioner mot ägaren (HP6a–j, `h-pass6-analys.mjs`).

## E11b: distinktioner inom klipptyp (10 806 bankklipp, 88 konton, utforskande)
`format/e11b.mjs`. Medel av rho inom konto mot visningar, för alla klipp och inom typ:

| | Alla | Sketch | Tilltal | Matporr | Provsmakning |
|---|---|---|---|---|---|
| antal personer | +0,09 | +0,11 | +0,11 | +0,06 | +0,13 |
| längd | +0,08 | +0,09 | +0,10 | +0,13 | +0,15 |
| lätt att göra om (rekonbar) | +0,13 | ±0 | −0,05 | **+0,19** | −0,03 |
| andel med person | +0,12 | −0,02 | −0,03 | **+0,13** | +0,07 |
| bildkvalitet | ±0 | ±0 | +0,03 | ±0 | +0,08 |
| montage | −0,08 | −0,03 | +0,05 | −0,05 | ±0 |

- **Två universella spakar:** fler personer och längre klipp, i alla typer.
- **Visningsregeln i stor skala:** bland matklippen går de med person i bild och enkel form bättre (70 konton). Inom sketch och tilltal säger samma mått ingenting, eftersom personer redan finns där.
- **Polering lönar sig inte i någon typ** (bildkvalitet ±0). Det stöder ägarens princip att värdet ska finnas kvar utan efterarbete.
- För räckeskartan: "fler personer" och "låt klippet få ta tid" är nyttoråd som gäller alla kunder. "Person i bild" gäller kunder som mest visar mat.

### E9 omkörd på konto 4 (cloud-credit-companion): rutnät mot original
Med 3.8 Flash och kort doktrin fick 119 klipp från 12 konton ur E6-R och ägarens 40 klipp kort både i original och i 2×2-rutnät. Förregistreringen ändrades två gånger innan några resultat lästes: modellen och kontot byttes när krediterna tog slut.

| Låst i förväg | Original | Rutnät | Beslut |
|---|---|---|---|
| HE9a: grund → visningar | +0,18 | +0,16 | förkastas (lika) |
| HE9b: krok → visningar | +0,14 | **+0,26** | **håller** |
| HE9c: vändning → visningar | +0,18 | +0,15 | förkastas |
| HE9d: grund mot ägarens passform | 0,61 | **0,67** | **håller** |

- Original och rutnät stämmer överens i 92 % för vändning, 85 % för krok, 82 % för hylla och 72 % för premiss.
- **Utforskande:** med kroken ur rutnätet och resten ur originalet ger grundvärdet +0,21 i nytta. Medlet av båda vyerna ger 0,65 mot ägaren.
- **Slutsats:** rutnätet ser det som händer i tiden (kroken) bättre, och originalet ser rummet. **Två vyer av samma klipp** är ett bättre medel än två körningar på samma vy, till samma kostnad. Förslag för ingest i v6: Flash med kort doktrin på original och på rutnät, med kroken från rutnätet och medel för resten. n är litet (12 konton), så det bör prövas igen i större skala.

## bank2: 448 sketcher ur banken (konto 4, förregistrerat)
`format/bank-tratt2.mjs` och `bank2-analys.mjs`. Urvalet är bankens relaterbara sketcher med rekonbar ≥ 4, högst 5 per konto, från 105 konton. Flash 3.8 med kort doktrin.

| Låst i förväg | Resultat | Beslut |
|---|---|---|
| HB1: grundvärdet skiljer sketcher åt inbördes → visningar | **+0,10, p = 0,047** (79 konton) | håller |
| HB2: stark premiss → visningar | **+0,11, p = 0,028** | håller |
| HB3: minst 30 % hamnar i kärnan | **42 %** (182 av 432) | håller |

**Utforskande:** eget tal inom sketcher ger **+0,29** (p < 0,001, 56 konton), och +0,15 i E6 och E6-R (11 konton). nytta6 ger +0,14 och "höjer taket" +0,11. **En sketch med egna repliker slår en sketch till trendljud.** Det blir ett räcke på klippnivå: när en sketch anpassas ska trendljudet bytas mot repliker, vilket scenplanens åtgärd "eget tal" redan gör.

## Bibliotek v6 (`format/bibliotek-v6-bygg.mjs`, `harness/bibliotek-v6.json`)
1 111 v5-kort från v0, E6, E6-R och bank2. Varje klipp har:
- två mått: LeTrend-värde och förväntad nytta
- hylla, språk och villkor
- ägarens omdöme där det finns

Ägarens biblioteksbeslut går före modellens hylla.

| Hylla | Klipp | Konton | Mest |
|---|---|---|---|
| **kärna** | **285** | 90 | sketch 243, tilltal 26 |
| mitten | 279 | 89 | trend 81, tilltal 80, sketch 79 |
| situation | 58 | 41 | sketch, tilltal, kampanj |
| CapCut-referens | 28 | 20 | trend, visning |
| ute | 461 | 87 | visning 183, kampanj 98 |

Kärnhyllan har vuxit från cirka 25 till 285 klipp från 90 konton. Det löser v0:s problem att samma sketcher återkom hos alla kunder. Ägaren har bara sett 16 av kärnklippen.

### E9-R: rutnätets krok replikerad (200 bank2-sketcher, 41 konton, förregistrerat)
`format/e9r.mjs`. Rutnätet med samma modell och doktrin som originalen i bank2.

| Låst i förväg | Rutnät | Original | Beslut |
|---|---|---|---|
| HE9Ra: krok → visningar, starkare ur rutnätet | **+0,37** | +0,17 | **håller** (skillnad +0,21, p = 0,015) |
| HE9Rb: grund med rutnätets krok, minst som original | +0,18 | +0,15 | håller (p = 0,13 för skillnaden) |

Kroken stämmer överens mellan vyerna i 90 % av klippen, men de 10 % där vyerna skiljer avgör mycket. **Kroken ska läsas ur rutnätet:** fyra tidpunkter per bild visar vad som händer de första sekunderna. Efter E9 och E9-R är krok ur rutnätet den starkaste enskilda prediktorn för nytta inom sketcher (+0,26 och +0,37). Förslag till nyttomåttet i v6.2: grundvärdet, eget ljud, person i visning och krok ur rutnätet med full vikt.

**Kärnhyllan med rutnätskrok.** Alla 285 kärnklipp har nu kroken ur rutnätsvyn (`karna-rutnat/kort`), och `bibliotek-v6.json` har fältet `nytta_v62` (nytta6 plus kroken ur rutnätet). På bank2-sketcherna med rutnät (288 klipp) ger grundvärdet +0,16, nytta6 +0,19 och nytta62 +0,20 i visningar inom konto. Data överlappar E9-R, så siffran är delvis cirkulär. Hyllorna sorteras på LeTrend-värde plus nytta62.

## bank3: tilltalshyllan (371 tilltalsklipp ur banken, 94 konton, förregistrerat)
`format/bank-tratt3.mjs` och `bank3-analys.mjs`. Det här är komplementet för kunder som mest visar mat (E11). Kärnhyllan hade bara 26 tilltalsklipp.

| Låst i förväg | Resultat | Beslut |
|---|---|---|
| HT1: grundvärdet skiljer tilltalsklipp åt → visningar | **+0,19, p = 0,002** (70 konton) | håller |
| HT2: personen i fokus (karisma) → visningar | −0,01 | förkastas: inom tilltal är det inte karisman som avgör |
| HT3: högst 20 % kärna | 5 % (115 i mitten, 85 i situation) | håller: tilltal är villkorat |

**Utforskande:** eget tal ger +0,31, "höjer taket" +0,24 och nytta6 +0,21.

**Grundvärdet håller inom varje typ:** +0,10 bland sketcher, +0,19 bland tilltal, och +0,17 över alla typer i E6 och E6-R.

**Bibliotek v6 efter bank3:** 1 480 kort. Hyllorna:
- kärna: 302 (sketch 248, tilltal 36)
- mitten: 397 (tilltal 179)
- situation: 144 (tilltal 72)
- CapCut-referens: 31
- ute: 606

Tilltalet i mitten och situation är det CM ska ta fram till kunder som mest visar mat, med kundens villkor.

## CM-förslag v6.2: hur harnessen ser ut för en CM (`format/h-forslag.mjs`, [forslag-v6.md](forslag-v6.md))
Varje kund med en kundlinje (nio kunder) får tre topplistor ur bibliotek v6 (843 klipp på hyllorna kärna, mitten och situation). Listorna blandas inte:
1. **LeTrend-värde** (preferens): grundvärdet, ett mjukt linjeräcke och förlagan.
2. **Förväntad nytta för kunden:** nytta62 (grundvärdet, eget ljud, person i visning, kroken ur rutnätet) och E11:s kundberoende regler, alltså sketch som fortsättning och tilltal och personer som komplement. Regler som bygger på utfall hör till nyttosidan.
3. **Särskilt för kunden:** grundvärde minst 4 och störst skillnad mot medlet över alla kunder. Det motverkar v0:s problem att samma sketch toppade överallt, ett problem som kom tillbaka i list 1 eftersom grundvärdet dominerar.

Förstahandsvalet får också en scenplan.

**Känd brist:** skalan för kantighet fångar inte vuxna teman som relationer, partner eller fylla. Hos anettesrestaurang, som numera leds av barn, hamnar ett klipp om att "skämma bort sin partner" under "särskilt för kunden", fast ägaren i pass 4 sa att sådana teman inte passar en familjär kund. v7 bör få ett lager för tema, med vuxet tema som räcke mot familjära kunder.

## Temalagret: vuxna teman som räcke (`format/tema.mjs`, `harness/tema.json`)
Det här fyller bristen ovan. En textkedja med Flash 3.8 ovanpå v5-korten (helhet, handling, kärna) ger varje klipp tema, "vuxet" och "familjevänligt". Den kördes på 843 klipp i kärna, mitten och situation. **114 klipp är vuxna och 125 är inte familjevänliga.**

Kontroll mot ägarens omdömen:
- Lappklippet (steamhotel), som ägaren gav 1 hos anettesrestaurang för att det var för vuxet, märks relation och romantik, alltså vuxet.
- "Tack detsamma"-sketchen märks vardag och familjevänlig.
- Partnerklippet som slank in hos anettesrestaurang märks vuxet.

**Räcket** i `h-forslag.mjs` sänker LeTrend-värdet med 2 för ett vuxet tema hos en familjär eller lekfull kund. Det gäller bara preferenssidan, eftersom utfallen inte säger något om teman. Partnerklippet är nu borta från anettesrestaurangs lista.

## Rutnät för mitten och situation (konto 4, förregistrerat): krediterna slut
`format/hyllor-rutnat-analys.mjs`. 188 av 439 klipp hann få rutnätskort innan konto 4 svarade 402. 184 klipp har båda vyerna, varav 102 tilltal.

| Låst i förväg | Rutnät | Original | Beslut |
|---|---|---|---|
| HG1: tilltal, krok → visningar, starkare ur rutnätet | +0,41 | +0,43 | **förkastas** (13 konton) |
| HG2: alla, grund med rutnätets krok, minst som original | −0,11 | −0,15 | håller (+0,04, p = 0,044) |

- **Rutnätets fördel för kroken gäller sketcher, inte tilltal.** I en sketch är kroken en situation som syns de första sekunderna, och fyra tidpunkter per bild fångar den. I ett tilltal är kroken det som sägs, och det hörs lika bra i båda vyerna. Det blir ingesten i v6.2: rutnätsvy för sketcher, originalet räcker för tilltal.
- **Grundvärdet är negativt inom urvalet.** Det beror troligen på det begränsade spannet: det är de högst rankade klippen i mitten och situation, och inom varje konto jämförs bara likartade klipp. Det bör prövas på ett slumpmässigt urval innan det tolkas.

**Krediterna:** konto 4 (cloud-credit-companion) är slut. Alla vägar till modellerna är stängda: Lovable 1–4, Vertex med obetald faktura, och AI Studio, där gratisnivån snabbt ger 429.

## Grundvärdet sorterar mellan hyllorna, nyttan inom dem (inga anrop)
`format/hyllor-grund.mjs`. Visningar inom konto per hylla i bibliotek v6, på alla klipp med utfall:

| Hylla | Klipp | grund | nytta6 |
|---|---|---|---|
| kärna | 297 | −0,02 | **+0,24** (46 konton) |
| mitten | 390 | −0,04 | +0,10 |
| situation | 143 | +0,04 | −0,10 |
| ute | 591 | −0,01 | +0,08 |
| **alla hyllor** | 1 452 | **+0,17** | **+0,21** |
| hyllan som ordningstal | | **+0,18** | |

**Två steg:**
1. Grundvärdet och doktrinen avgör *vilken hylla* klippet hör till. Där bär de både preferens och nytta, och hyllan ensam ger +0,18.
2. *Inom* en hylla skiljer grundvärdet inte längre (±0). Där är det nyttospakarna, alltså eget tal, person i visning och krok, som rangordnar (+0,24 inom kärnan).

Det förklarar det negativa resultatet i HG2, som jämförde klipp inom en hylla. Det stämmer också med ägarens omdöme att biblioteket är huvudfrågan. Klippets kategori och LeTrend-värde avgörs på plannivå. Inom kategorin är det utförandet som avgör, och det är där anpassningen och scenplanen gör skillnad. **Följd:** bibliotek v6 sorteras nu efter hylla och sedan efter nytta62 inom hyllan.

## E12: gratis ingest via AI Studio? (förregistrerat, avbrutet)
`LOVABLE_KONTO=aistudio`, som är inbyggt i `typer/lovable.mjs`. Gratisnivån tar video och v5-schemat med `gemini-3-flash-preview`, `gemini-3.5-flash` och `gemini-3.1-flash-lite`, och använder cirka 5 000 tokens per klipp. **HE12c (beskrivande): kvoten är 20 anrop per dag, modell och projekt** ("GenerateRequestsPerDayPerProjectPerModel-FreeTier", limit 20). Kvoten tog slut efter två kort, så HE12a och HE12b kan inte prövas i dag. Gratis ingest räcker för stickprov, inte för biblioteket.

## Metaanalys: räckeskartan med konfidens (1 390 klipp, 95 konton, inga anrop)
`format/meta.mjs` och `data/format/meta.json`. Underlaget är alla v5-kort med utfall från E6, E6-R, bank2 och bank3: medel av rho inom konto mot visningar, med 95 % konfidensintervall genom bootstrap över konton.

| Spak | rho | 95 % KI | |
|---|---|---|---|
| nytta6 | +0,22 | [+0,16, +0,29] | säkert positiv |
| utan efterarbete | +0,19 | [+0,13, +0,25] | säkert positiv |
| eget tal | +0,19 | [+0,12, +0,25] | säkert positiv |
| grundvärdet | +0,18 | [+0,11, +0,24] | säkert positiv |
| sketch | +0,15 | [+0,08, +0,22] | säkert positiv |
| höjer taket | +0,14 | [+0,07, +0,22] | säkert positiv |
| premiss stark | +0,13 | [+0,06, +0,21] | säkert positiv |
| krok (original) | +0,12 | [+0,06, +0,18] | säkert positiv |
| vändning | +0,10 | [+0,03, +0,17] | säkert positiv |
| kantighet | +0,06 | [+0,00, +0,12] | gränsfall |
| tilltal | +0,06 | [−0,00, +0,13] | gränsfall |
| karisma (fokus) | −0,04 | [−0,10, +0,03] | noll |
| bundna bilder | −0,09 | [−0,15, −0,04] | säkert negativ |
| visning | −0,12 | [−0,18, −0,06] | säkert negativ |
| trendljud | −0,12 | [−0,19, −0,05] | säkert negativ |
| klippberoende | −0,13 | [−0,18, −0,07] | säkert negativ |
| Instagram-språk | −0,15 | [−0,21, −0,08] | säkert negativ |
| ingen person bär | −0,18 | [−0,24, −0,12] | säkert negativ |

**Vad som går att abstrahera, och med vilken säkerhet:**
- **Doktrinens kärna står fast.** Värdet ska finnas kvar utan efterarbete, idén ska ha en premiss och vändning, en person ska bära klippet och det ska höras eget tal. Instagram-språk, montage, trendljud och bundna bilder drar ned.
- **Karisma ger noll räckvidd i sig** (KI över noll). Ägarens princip att ett klipp som bärs av en persons karisma inte är ett biblioteksklipp får stöd också i utfallen: karismaklipp når inte längre.
- **Kantighet ger inget säkert lyft** (+0,06, gränsfall). Den ska förbli ett varumärkesräcke och styras av kundens smak och temat, inte av räckvidd.
- **Tilltal ger lite i sig**, men det är det starkaste komplementet hos kunder som mest visar mat (E11).

Läs dessa tillsammans med de två stegen ovan: spakarna ovan sorterar mest *mellan* hyllorna, och nyttospakarna (eget tal, person, krok) sorterar *inom* dem.

**E12, delresultat** (12 av 19 klipp, två nycklar med 20 anrop per dag och nyckel, där omförsöken räknas): 3.5 Flash gratis ger rho 0,53 mot ägarens passform (23 par), mot 0,62 för 3.8 Flash via Lovable. Hyllan stämmer med Pro i 75 %, mot 78 %. HE12a går inte att avgöra på 23 par men pekar något lägre. HE12b håller (75 % ≥ 70 %). Gratis ingest håller ungefär samma nivå, men bara för stickprov: cirka 15–20 klipp per dag och nyckel. De återstående 7 klippen körs när kvoten nollställs.

## Pass 6: matchningen hos tre nya kunder (6 nov, transkript 7)
Ägarens svar finns i `harness/pass6/agare.json` och analysen körs med `node format/h-pass6-analys.mjs`. Det är 15 nya par från tre kunder: fratelli (sketchvärld), blubnan (premium, stämning) och pomflora (kafé som visar mat, utan ansikten).

| Prognos (låst 4 nov) | rho mot ägaren | inom kund | inom delade klipp |
|---|---|---|---|
| v5 total | +0,39 (p 0,07) | +0,14 | 7 rätt, 1 fel (p 0,035) |
| Pro som CM | **+0,78** (p 0,001) | +0,30 | |
| v6 LeTrend-värde | +0,37 (p 0,09) | +0,10 | 7 rätt, 1 fel |
| v6 nytta (E7) | −0,04 | −0,15 | |
| v6.1 (E11-reglerna i preferensen) | +0,19 | +0,14 | 5 rätt, 3 fel |

- **HP6a håller inte på 5 %-nivån men pekar rätt.** HP6b håller: v5 ordnar kunderna rätt för samma klipp. HP6c håller. HP6d håller med 2 av 3, eftersom anpassningen för blubnan inte skulle skickas. HP6f håller ungefär lika (0,37 mot 0,39) och HP6g håller: nyttan är ett annat mått än preferensen. HP6i håller inte: v6.1 är sämre än v6.
- **Reglerna för nytta ska inte in i preferensprognosen.** v6.1 lade E11:s komplementregler i passformen och blev sämre. Det bekräftar designen med två mått.
- **Kunden väger tyngre än klippet här.** På de fyra delade klippen står kunden för 54 % av variansen och klippet för 13 %. I pass 4–5 stod klippet för två tredjedelar. Skillnaden är att de delade klippen i pass 6 låg nära varandra i grundvärde, medan kunderna låg långt isär.
- **Pros höga rho kommer från nivån mellan kunder.** Pro ger sketchkunden höga betyg och de två andra 1, och det följer ägaren. Inom kund ger ingen prognos mer än +0,30.
- **Omtest:** 5 → 4, 3 → 4 och 2,5 → 3. Ägarens eget brus ligger kring ±0,7 på skalan 1–5.

**Strukturen inom kund (pass 4–6, utforskande):**
- **5:** formatet finns i kundens *historik*, även om det ligger långt tillbaka. A2 (tilltal med matmontage) och C3 (textöverlägg med relationshumor, som pomflora gjorde för cirka 100 klipp sedan) fick 5.
- **2:** klippet sänker kundens självbild, eller kräver en förmåga kunden aldrig visat. Blubnan B2 (goofy, "they don't want to belittle themselves") och B5 (att äta kundens mat bryter respekten för maten) fick 2, liksom pomflora C2 (gatuinslag kräver någon som talar, och ingen talar i kundens klipp). I pass 4–5 föll anettes 1–2 på självbilden och babuls communityklipp på den slutna världen.
- **Övriga klipp:** kring kundens egen nivå (3–4).

**Ägarens läsning av en serie:**
- Ägaren läser hela historiken i faser, inte de tio senaste klippen. "They've done it before" lyfter ett klipp, till exempel pomfloras gamla sketcher och fratellis gatuinslag.
- Communityinslag är högst 10–25 % av en LeTrend-formel.
- Klipp som går emot idealbilden "fill the pipe" men för inte serien mot en enhet.
- Om anpassningen: en anpassning som bara byter miljö är begränsad. En riktig ändring byter premiss eller skämt och följderna av det. CM ska kunna gå långt från förlagan om idén är lika rolig, med räcken.

## Serieprofil ur sållningen (`format/serieprofil.mjs`, inga anrop)
Hela historiken visas i block om 10 med bankens Lite-typ (mat, tilltal, sketch, gata, annat), andelen person och medianvisningar. Den återger ägarens läsning hos fyra av fyra kunder:
- **fratelli:** gatuinslagen var en fas 2025 och den senaste för 50 klipp sedan ("not in the last 30"). Sedan april 2026 nästan bara sketcher, och medianvisningarna har gått från 10–25k till 80–90k.
- **blubnan:** blandat tilltal, gata och sketch fram till februari 2026, därefter cirka 45 klipp med mat och stämning ("the last 40, 50, 60"). Andelen person sjunker från 0,95 till 0,63.
- **pomflora:** sketcherna ligger i klipp 71–110 ("100 clips ago").
- **anettes:** de senaste tio klippen innehåller fyra sketcher och fyra tilltal ("in latter days more sketches").

Kundlinjen (Pro, de tio senaste klippen, cirka 25 000 tokens per kund) ser inte faserna. Sållningen är redan betald och räcker för faser och repertoar. Typerna är dock för grova för ägarens formatfamiljer: Lite kallar gatuintervjuer för sketch och skiljer inte textöverlägg utan tal från dialogsketch. Ägarens familjer är dialogsketch med roller, snabb ordvits, absurd improvisation, gatuinslag, tilltal med matmontage, textöverlägg med relationshumor utan tal, stämningsmontage, kampanj och trend.

Repertoaren mot ägarens passform med grova typer (`format/repertoar.mjs`, 43 par, 9 kunder, utforskande):

| Mått | rho | inom kund |
|---|---|---|
| andel av samma typ i hela historiken | +0,30 | +0,24 (p 0,054) |
| andel i de 30 senaste | +0,37 | +0,21 |
| andel i de 10 senaste | +0,25 | +0,13 |

Riktningen stämmer med ägaren: hela historiken slår de tio senaste. Signalen är ändå svag med fem typer.

## Serie 2: lönar det sig att hålla kontots fas? (`format/serie2.mjs`, 10 398 klipp, 78 konton, förregistrerat, inga anrop)
- **S1 förkastas.** Inom konto och typ ger ett klipp som ligger i kontots fas ingen extra räckvidd (rho −0,008, p 0,76). I fas mot utanför fas: ×0,98.
- **S4 förkastas.** Block om 10 med en mer enhetlig mix når inte längre (rho −0,018).
- **S3:** fler än 25 % gatuinslag i ett block skadar inte räckvidden (×1,06, 23 konton).
- **S2 (beskrivande):** 13 av 78 konton har ett tydligt fasskifte. 10 av 13 hade fler visningar efter skiftet. Skiften bort från mat gav ×2,7 (n 10), skiften till mat ×0,43 (n 2). Tid och val är inte bortrensade.

**Slutsats:** att serien är enhetlig är preferens och varumärke, inte nytta per klipp. Det replikerar E6 ("fortsättning på kundens linje = preferens") på hela historiken. Nyttan ligger i vilken fas kontot väljer, med person och tilltal före mat (E11), inte i att hålla fasen. För matchningen innebär det:
- Preferenssidan läser serieprofilen, alltså faser, repertoar, självbild och förmåga.
- Nyttosidan behåller E11.
- Där de två drar åt olika håll, som hos blubnan, ska CM se båda.

**Läget 6 nov:** pass 7 är redo. Prompten har fått engelska dialogsammanfattningar, och Miles frågar inte "Why?" efter att ägaren förklarat. Pass 8 har fått en lista över seriens faser att bekräfta. Nästa test av serieprofilen kräver nya par med låsta prognoser.

## Pass 7: ägarens biblioteksval (6 nov, transkript 8)
Kodat i `pass7/agare.json` innan analysen kördes (`format/h-pass7-analys.mjs`). Ägaren valde i 19 av 20 par. Par 7 blev lika: "both are good ... they both have their own functions".

| Ägaren följer | Alla par | Isär-paren |
|---|---|---|
| grundvärdet (= LeTrend-värde i bibliotek v6) | 10 av 19 (p 0,50) | 2 av 10 |
| nytta6 (= förväntad nytta) | **16 av 19 (p 0,002)** | **8 av 10** |
| nytta62 | 15 av 18 | 7 av 9 |
| hylla, sedan nytta62 inom hyllan | 15 av 19 | |
| visningarna på skärmen | 7 av 19 | |

- **HP7a och HP7b förkastas.** Prognosen var att ägaren följer grundvärdet. Ägaren följer nyttan, i isär-paren 8 mot 2.
- **Dubbel dissociation med pass 6.** När frågan är om ett klipp passar en viss kund följer ägaren LeTrend-värdet (+0,37) och inte nyttan (−0,04). När frågan är vilket klipp biblioteket ska ha följer ägaren nyttan och inte LeTrend-värdet. Båda måtten behövs, och frågan CM ställer avgör vilket som gäller.
- **Alla tio isär-paren låg i mitten-hyllan.** Där hyllorna skiljde valde ägaren kärnklippet i 7 av 7. Det är samma två steg som i räckvidden (hyllan +0,18, nyttan inom kärnan +0,24), och bibliotek v6 sorteras redan så. Tvåstegsregeln låstes inte för pass 7, men klippen var osedda.
- **HP7c:** i isär-paren hade nyttans klipp högre rv i 5 av 10 och grundvärdets i 5. Tio par säger inget om räckvidden.
- **Visningarna på skärmen styrde inte valen** (7 av 19), men ägaren säger själv att likes påverkade par 16.

**Isär-paren:** tilltal före trend i 5 av 6 par (3, 5, 6, 11, 15). Undantaget är par 14, där tilltalet var ett PSA utan krok. Det svårare klippet med person och mat vann när det "has more meat", "builds a relationship" eller är "actually better in terms of marketing". Det lättare vann när det svårare krävde överflöd (hotellpool, par 13), ett tema (OS, par 2) eller saknade krok (par 14).

**Distinktioner (utforskande):**
- **Lätt att rekommendera mot värde i flödet.** Ägaren skiljer på dem i nästan varje par. Lätt betyder få personer, kort inspelning, lite klippning och inget specifikt erbjudande, tema eller personlighet. Värdet väger tyngre, men bara om LeTrend kan göra klippet rekommenderbart: "if one creates a system where that can be repurposed in a good way" (par 15). Det är den ursprungliga frågan, hur CM får det hen vill i ett lättviktigt system.
- **Två sorters återbruk.** En kärnsketch återanvänds genom premissen. Ett tilltal eller en visning återanvänds genom ryggraden: scenföljd, tempo och komposition, med varan och replikerna utbytta ("describe each phase", par 6; "how does one basically recommend compositional structures", par 14). Grundvärdet mäter premissen. Det förklarar troligen varför det inte skiljer inom mitten-hyllan.
- **Unika drag är en fälla** (par 20). Personlighet och planerade repliker följer inte med till en annan kund.
- **För många enkla enkeltagningar** signalerar låg ambition och gör att kunderna smälter ihop (par 4, 12). Det är en seriefråga, inte en klippfråga.
- **Originalets kvalitet** (ljus, komposition) spelar roll när CM visar förlagan för kunden (par 7).

**Följd:** sorteringen behålls (hylla, sedan nytta62). Hypotes till pass 8 och framåt: för mitten-klipp med tilltal ska anpassningen beskriva ryggraden (scener, tempo, vad som byts, var personen är fri), och för kärnsketcher premissen. Pass 8 visar om v5-formen räcker för det.

**Miles** hoppade fram två gånger, sa själv "Left" efter en fråga, avbröt i par 7 och sammanfattade nästan varje par med "You're weighing ...". Ägaren krävde kriterier före par 1. Pass 8-prompten har rättats.

**Läget 6 nov, kväll:** pass 7 klart. Pass 8 väntar på ägaren (cirka 30 min).

## Pass 8, del 1: kund A (6 nov, transkript 9.1)
Ägaren gick igenom kund A (pizzeriamums, källklipp dirtytaco: drinkinstruktion med missar) och avbröt sedan för att låta AI:n iterera på formen. Kodat i `pass8/agare.json`.
- **Val:** "Both. I don't know." Valde version 2 (v0, scenmanus med repliker och tider) först när Miles sa "Pick one". Den andra skickas också. HP8a: 0 av 1, ett svagt val.
- **Scenplanen:** 3 av 4 beats stämmer med den låsta regeln (75 %). Missen är beat 1: frontfiguren räknas som "ändra", men ägaren behåller scenen och tycker att personbytet är självklart.

**Ägarens jämförelse:**
- **v5** (kärnan, det som bär, fritt) "tries to find the core ... the underlying thing that drives the recommendability". Den balanserar mellan att säga för mycket och för lite, och passar dagens LeTrend där kunden får text och originalklippet.
- **v0** säger exakt vad som ska sägas. Det ger tighthet, så kunden inte svävar ut som tjejen i källklippet, men det blir mindre spontant, "like a CM in the room telling them do this, do that". v0 blir rätt om LeTrend äger kedjan, med en studiodel där CM skriver allt och replikerna förhandsgranskas.

**Regler för anpassningens form (ägarens ord, kund A):**
1. Inga tidsstämplar. Scenen tar den tid repliken behöver, men ska vara tight: "every line has its purpose".
2. Säg inte det självklara, till exempel att drinken byts mot pizza hos en pizzeria.
3. Instruera inte personlighet ("be goofy").
4. Förlagans personliga drag, som missar och slarv, blir tillåtelse och inte instruktion: "if you fail, leave it in ... but don't force anything". Det är en ny åtgärd, *tillåt*, som scenplanen saknar.
5. Varje scen behöver känslan, platsen i strukturen och vad scenen kräver ("pointedness"). Text ensam bär det dåligt. Det bör visas, till exempel med en 3D-skiss per scen där pizzabaket ersätter drinken.

**Koppling till pass 7:** källklippet är ett ryggradsklipp, och ägaren vill ha ryggraden (scenerna och vad de kräver) med fria repliker. Hypotes: formen beror på klippet. Ett ryggradsklipp får scener med syfte och fria repliker. En premissketch får de repliker som bär skämtet ordagrant, och resten fritt. Kvar i pass 8 finns både premissketcher (B, D) och ryggradsklipp (C, E).

**Miles** pratade i munnen på ägaren, upprepade kriterieraden utan att bli tillfrågad och tvingade fram ett val. Prompten är rättad: kriterieraden är borttagen, "both/neither" följs av "What would you take from each?", och efter "quiet" är Miles tyst tills ägaren ställer en fråga.

## Krediter 6 nov kväll: version 3, formatfamiljer och återbruk (konto 5)
Konto 5 (`LOVABLE_KONTO=5`) gav cirka 430 000 tokens innan det svarade 402 kl. 18:18. Arbetsytans 30 promokrediter verkar inte betala anrop genom endpointen; en ny nyckel till samma projekt gav också 402.

**Version 3 av anpassningen** (`format/h-anpassa8.mjs`, Pro, förregistrerat i `pass8/forregistrering-v3.json`): ägarens formregler från kund A (`FORM8`) för alla sex kunder. Den maskinella kontrollen (HP8f) hittade ett brott: kebabbabes scen 2 bad personen göra ett misstag. Regeln skärptes och kebabbabes genererades om innan ägaren sett något. Pro väljer själv återbruk: premiss (babuls, chickenstreet, blackstone), ryggrad (anettes, kebabbabes) eller båda (pizzeriamums). `format/h-pass8b.mjs` bygger `miles/pass-8b-underlag.md` (kund B–F, tre versioner i låst blind ordning), och prompten är `miles/pass-8b.txt`.

**Ägarens formatfamiljer** (`format/familjer.mjs`, Flash 3.8 på sållningens text, förregistrerat i `familjer/forregistrering.json`): 1 980 klipp hann klassas, vilket täcker hela historiken hos kunderna i pass 4–6.

| Mått mot ägarens passform, inom kund (43 par, 9 kunder) | Lite-typ | Familjer |
|---|---|---|
| andel av klippets familj i hela historiken (HF1) | +0,24 | **+0,48 (p 0,001)** |
| log antal av familjen | +0,25 | **+0,54 (p 0,001)** |
| familjen förekommer minst två gånger (HF2) | +0,15 | **+0,38 (p 0,018)** |
| andel bland de 30 senaste | +0,21 | +0,38 |
| andel bland de 10 senaste | +0,13 | +0,29 |

- **HF1 och HF2 håller.** Paren är sedda, men familjerna låstes före klassningen och inget anpassades.
- **Repertoaren slår Pro som CM inom kund:** på samma 43 par ger log antal av familjen +0,54 och Pros passform +0,42. Repertoaren kostar inget per kund när familjerna finns.
- **S1f håller:** att ligga i fas ger ingen räckvidd, både på de 12 konton som Flash klassade (rho +0,015) och på hela banken med den lokala klassaren (rho −0,023, i fas mot utanför ×0,87). Block med mer blandade familjer når något längre (+0,06, utforskande). S2f gick inte att pröva: med tio familjer hittar segmenteringen nästan inga skiften.

**Lokal klassare** (`format/familjer-lokal.mjs`, inga anrop): naive Bayes på sållningens text, Lite-typ, flaggor, nyckelord och TikToks metadata (ljudspår och bildtext ur `Downloads/letrend-bank/<konto>/<id>.info.json`). Den träffar 77 % på nya konton (största klassen 27 %), med 91–98 % på dialogsketch, tilltal och stämning, men 0–56 % på trend, text utan tal, kampanj och gata. Sållningens enda mening bär inte de fina familjerna; de kräver ljud och bild. `familjer/familjer-lokal.json` märker hela banken (Flash där det finns, annars lokalt), också 1 475 av 1 480 bibliotekskort.

**Serien med familjer** (`format/serieprofil.mjs --familj`): tre påståenden i pass 8 rättades innan ägaren såg dem. Blackstones "gatuinslag" var provsmakning (ett gatuinslag på 231 klipp), babuls hade en trend- och läppsynksfas 2024, och fratellis gatufas låg december 2025–april 2026. Pass 8- och 8b-underlagen har den nya listan.

**Ljudet ur metadata** (`format/ljud-rv.mjs`, utforskande): 41 % eget ljud, 18 % någon annans originalljud och 40 % låtar. Text utan tal har eget ljud i 6 % av klippen och trend i 24 %. Inom konto och familj ger eget ljud mot lånat ×1,09 (60 av 103, p 0,057), och i dialogsketcher ×1,15 (26 av 39 konton). Det replikerar "en sketch med egna repliker slår en sketch till trendljud" med gratis metadata.

**Återbruk och unika drag** (`format/aterbruk.mjs`, förregistrerat i `aterbruk/forregistrering.json`): bara 2 av 21 satser hann köras. HR1–HR3 väntar på krediter.

**Kö när det finns krediter:** återbruket (19 satser), familjerna för resten av banken (cirka 150 satser) och familjer från video för trend och text.

## Engagemang per formatfamilj (`format/engagemang.mjs`, 10 283 klipp, 78 konton, förregistrerat, inga anrop)
TikToks metadata (`Downloads/letrend-bank/<konto>/<id>.info.json`) ger kommentarer, sparningar, reposts och likes per klipp. Graderna per visning görs relativa inom konto. Varje familj jämförs med kontots övriga klipp, som median över konton (antal konton där familjen ligger högre):

| Familj | Räckvidd | Kommentarer | Sparningar | Reposts | Likes |
|---|---|---|---|---|---|
| dialogsketch | **×1,22 (53/70)** | ×0,75 (10/70) | ×0,85 (17/70) | ×0,80 (21/70) | ×1,13 (55/70) |
| tilltal_med_mat | ×1,14 (49/74) | ×1,14 (49/74) | ×1,05 (46/74) | ×0,99 | ×1,01 |
| stamningsmontage | ×0,74 (11/71) | ×1,06 | ×1,08 (42/71) | ×0,97 | ×0,85 (14/71) |
| kampanj | ×1,12 (41/67) | ×1,14 (46/67) | ×1,02 | **×1,47 (48/67)** | ×1,00 |
| trend | ×0,95 (15/35) | ×0,96 | ×0,85 (9/35) | ×0,98 | ×1,20 (26/35) |
| gatuinslag | ×0,88 (8/22) | ×0,79 (9/22) | ×0,96 | ×1,25 (14/22) | ×1,11 (16/22) |

- **E1 förkastas.** Gatuinslag ger inte fler kommentarer (×0,79). De ger reposts och likes, men lägre räckvidd.
- **E2 håller.** Mat ger fler sparningar än dialogsketch (×1,20, 45 av 63 konton, p 0,0004), och tilltal med mat likaså (×1,25, 53 av 67, p < 0,0001).
- **E3 håller till hälften.** Dialogsketch ger mest räckvidd (×1,22, 53 av 70, p < 0,0001) men färre reposts (×0,80).
- **E4 håller till hälften.** Kampanj ger fler kommentarer (×1,14, 46 av 67, p 0,0015) men inte lägre räckvidd (×1,12). Klassaren är svag på kampanj (45 % träff), så delar kan vara tilltal.

**Följd:** familjerna gör olika jobb i en serie. Sketch ger räckvidd och likes men lite samtal. Tilltal med mat är det mest allsidiga, med räckvidd, kommentarer och sparningar. Matmontage ger sparningar men tappar räckvidd. Kampanj ger kommentarer och reposts. Det stöder portföljen från E4/E6 (kött ger räckvidd, stöd ger engagemang) med finare familjer, och ger CM ett skäl att blanda.

## Serie 2g: fasskiften med grupperade familjer (`format/serie2g.mjs`, förregistrerat, inga anrop)
Familjerna grupperade i person (dialogsketch, ordvits, absurd, gata, tilltal med mat, text utan tal), mat, trend och kampanj. Kontrollen är en låtsasbrytpunkt på samma relativa position i konton utan skifte, med lika långa fönster.
- 15 skiften i 15 konton. Konton utan skifte sjunker ×0,73 över samma tid; med skifte stiger de ×1,59, netto ×1,99 (12 av 15 uppåt).
- **S2g1 håller.** Mat → person: 9 av 9 uppåt netto, median ×2,94 (teckentest p 0,002).
- **S2g2 kan inte prövas** (n 2, netto ×0,81). Inga skiften till eller från trend.

**Följd:** att lämna en matfas för en personfas är det enskilt tydligaste nyttovalet i serien. Det replikerar serie 2 (bort från mat ×2,7) med kontroll för tidstrend och styrker E11: tilltal och personer som komplement hos kunder som mest visar mat.

## Tempo, längd och ljud ur lokala mp4 (`format/tempo-matt.mjs`, `format/tempo-analys.mjs`, förregistrerat, inga anrop)
ffmpeg.exe blockeras av Windows på datorn ("Åtkomst nekad"), så allt mäts med ffprobe och lavfi-filter: scenbyten (scene > 0,3 på 8 bilder/s) per 10 s, längd, andel tystnad (−35 dB) och loudness range (LRA). 1 912 klipp ur letrend-bank, letrend-e4 och letrend-bibliotek; 1 800 med relativ räckvidd i 87 konton.

Median per familj: matmontage 3,4 scenbyten per 10 s, tilltal med mat 1,6, gatuinslag 1,6, dialogsketch 1,3, kampanj 1,1, trend 1,0, text utan tal 0,7. Tilltal med mat är längst (23 s), trend och text kortast (9–10 s).

- **T1 håller svagt.** Inom konto × familj ger högre klipptakt något högre räckvidd i dialogsketch och tilltal (rho +0,06, p 0,031). Effekten är liten.
- **T2 förkastas, åt andra hållet.** Längre klipp når längre inom konto × familj (rho +0,11; tilltal med mat +0,13). Ägarens "too long" om enskilda klipp syns inte i räckvidden; längd i sig straffas inte.
- **T3 håller till hälften.** Eget ljud har högre LRA än låtar (AUC 0,59, p < 10⁻⁹), men *mindre* tystnad (AUC 0,36): restaurangljud gör att −35 dB-tystnad inte fångar talpauser. LRA är en svag talsignal; metadatans ljudspår är bättre.
- **T4 håller.** I pass 7 hade ägarens valda klipp högre klipptakt i 14 av 19 par (p 0,032), i isär-paren 8 av 10. Takten pekar som nytta6 i 13 av 19 par och tillför lite utöver den (bara takten rätt i 2 par, bara nyttan i 4): ägaren väljer klipp med flera scener framför enkeltagningar, vilket nyttan redan fångar.

**Följd för anpassningen:** "tight" betyder inte kort. Scenplanen ska ta bort dötid mellan stegen (takt), inte korta klippet; ett tilltal med mat får vara 20–30 s om varje scen bär. Det stöder FORM8: inga tidsstämplar, men varje replik har ett syfte.

## Sammanfattning 6 nov kväll (lokalt, inga krediter)
| | Höll | Höll inte |
|---|---|---|
| Engagemang | E2 (mat och tilltal sparas mer än sketch), E3 räckvidd, E4 kommentarer | E1 (gata ger inte kommentarer), E3 reposts, E4 lägre räckvidd |
| Fasskiften | S2g1 (mat → person 9 av 9, netto ×2,94) | S2g2 ej prövbar (n 2) |
| Tempo | T1 svagt, T3 LRA, T4 (pass 7, 14 av 19) | T2 (längre når längre), T3 tystnad |

**För matchningen:** preferenssidan läser repertoaren i familjer (+0,54 inom kund). Nyttosidan får tre nya stöd: personfasen före matfasen (S2g1), tilltal med mat som allsidigaste familjen, och familjernas olika jobb (sketch räckvidd, mat sparningar, kampanj kommentarer) som skäl att blanda. **För anpassningen:** tight genom takt, inte längd; eget ljud i sketcher (×1,15) och tal i tilltal behålls.

## Tal ur lokala transkript (`format/transkript.mjs`, `format/tal-analys.mjs`, förregistrerat, inga anrop)
whisper.cpp v1.9.5 (base-q5_1, silero-VAD) på de 232 prioriterade klippen (pass 7, pass 8:s källklipp, pass 4–6:s kandidater och kundernas lokala klipp); resten stoppades med flit. 230 med relativ räckvidd i 49 konton.
- **TA1 förkastas: instrumentet håller inte.** Talandelen skiljer inte eget ljud från låtar (AUC 0,54, p 0,17). Whisper och VAD räknar sångtext och läppsynk som tal. Dötiden blir 0 i nästan alla klipp, eftersom VAD slår ihop segmenten.
- **TA2 och TA3 förkastas** (dötid och ord per sekund mot räckvidd: rho −0,05 och −0,07). **TA4 kan inte prövas** (ett konto). **TA5 förkastas:** ägarens val i pass 7 har högre talandel i 10 av 19 par.
- **Slutsats:** lokala transkript med base-modellen ger inga meningsfulla mått på tal eller tighthet. Metadatans ljudspår (eget, lånat, låt) är bättre för eget tal. Transkripten (`data/format/tal/`) kan fortfarande användas som text: engelska sammanfattningar till Miles (`--engelska`) och som underlag för familjerna.

**Kontaktark** (`format/kontaktark.mjs`): hela historiken som en bild per kund, nyast överst, tio klipp per rad, med familjebokstav och färgband (grönt person, orange mat, lila trend, blått kampanj). Omslagen hämtas färska med `yt-dlp --flat-playlist`. Sju kunder ligger i `miles/serie/` och är länkade från serielistan i pass 8 och 8b.
