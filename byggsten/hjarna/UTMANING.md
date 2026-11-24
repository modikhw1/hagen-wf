# Avsiktsriggen i centrum: utmanad mot det vi vet

14 nov 2026. Ägaren lade två texter i centrum av problembilden (`Desktop/utmana 1.txt`, `utmana 2.txt`). Uppdraget:
> "utforska det, utmana det, och se till att det inte kan stå emot våra antaganden eller insikter. Om våra insikter inte är tillräckligt vassa, böjer vi oss och lägger uppgifter i en pipe."

Den här filen gör tre saker:
- bryter ned tesen i påståenden
- angriper varje påstående med det vi har belägg för
- skiljer det som faller, det som står kvar och det vi inte kan avgöra med argument

Det sista blir uppgifter (0041–0045). Det som är min tolkning är markerat så. Resten bygger på belägg i repot eller i ägarens ord.

---

## 1. Tesen, i sju påståenden

| | påstående | ur texten |
|---|---|---|
| **P1** | Scenen sparar skälen, inte rörelsen. Kroppen räknas fram ur dem varje gång. | "I den nya versionen sparar scenen ingen rörelse alls." |
| **P2** | Mellan sinne och kropp går prioriteringar, inte etiketter. Stress syns som att marginalerna krymper, att handlingarna överlappar och att uppmärksamheten smalnar. | "Skickar sinnet 'stress = 0,8' har man bara flyttat etiketten ett steg uppåt." |
| **P3** | Meningen är inbakad om rörelsen med nödvändighet ändras när meningen ändras. Det är ett kontrafaktiskt test. | "Testet är kontrafaktiskt." |
| **P4** | Fart är inte samma sak som stress. | "En lugn person kan gå fort, och en stressad kan smyga in långsamt." |
| **P5** | Två hastigheter: rollen uppdateras när något händer, och ett snabbare motoriskt lager styr kroppen hela tiden. | "språkmodellen inte hinner tänka varje bildruta" |
| **P6** | Man kan fråga scenen varför och få orsakskedjan tillbaka. | "hon trodde att hon var sen", inte "keyframe 43" |
| **P7** | Delarna finns, men den obrutna kedjan från övertygelse via avsikt och kropp till konsekvens är ouppfunnen. | båda texterna |

Exemplet i texten är en *författad* scen: ett klassrum, en klocka, ett vått golv. Vårt material är *inlästa* TikTok-klipp. Den skillnaden bär de flesta angreppen nedan.

---

## 2. Angreppen

### A1. Riktningen: vi börjar i videon, inte i avsikten (angriper P1)
- **Det vi vet:**
  - Originalet är sanning för det som syns (`PIPE.md`, grundregeln).
  - Förvärlden ska vara "väldigt likt 1:1 från originalet" (ägaren 12 nov).
  - Ingesten ska först återskapa klippet orört och sedan ändra det.
- **Angreppet:**
  - Avsiktsriggen är framåtriktad: skäl ger rörelse.
  - Vi måste först gå baklänges, från rörelsen i ett klipp till skälen, och sedan framåt igen till exakt samma rörelse. Det är ett omvänt problem, och det är illa ställt. Många kombinationer av övertygelse, avsikt och kropp ger samma rörelse.
  - En simulerad kropp återger aldrig originalets rörelse exakt. Vår första MaskedMimic-körning hamnade 126 cm från målet i "ge" (0039, `matt_mm_a.json`).
  - Om scenen inte sparar rörelsen förlorar vi 1:1 i alla oändrade delar.
- **Vad som finns:** omvänd planering är etablerad forskning. Bayesian theory of mind härleder övertygelser, mål och percept ur rörelse (Baker, Saxe och Tenenbaum 2009; Baker m.fl. 2017). Det gäller agenter i enkla rum, inte människor i video.
- **Dom:** P1 faller i sin starka form ("ingen rörelse alls"). Kvar står en svagare form: **originalets rörelse sparas som referens, och skälen sparas bredvid och förklarar och styr avvikelsen.** Det är också vad MaskedMimic gör tekniskt: följer en referens och tar villkor. *Min tolkning:* rörelsen är minnet, skälen är förklaringen, och en ändring är en ändrad förklaring som räknar om avvikelsen från minnet.

### A2. Två sinnen: TikToks mening är upphovets, inte karaktärens (angriper P1, P6)
- **Det vi vet:**
  - Harnessen hittade det som bär värdet: premiss, vändning, krok, eget tal, "höjer taket". Allt det är riktat från avsändaren till tittaren.
  - Gelatos kort: poängen är kontrasten för tittaren, vändningen sitter i texten "Vs" och musikbytet, och takt 2 är "räcker fram den lilla skeden till kameran".
  - Risken är "att kunden inte vågar överdriva punchlinen" (`data/format/harness/v5/kennysgelato2.0-7596403003901381910.json`).
- **Angreppet:**
  - Expediten i gelato skopar inte en jättestor portion för att hon tror något. Hon gör det för att tittaren ska skratta.
  - Överdriften, riktningen mot kameran, texten och musiken finns inte i någon karaktärs sinne.
  - En fysisk kropp som drivs av en trovärdig övertygelse ger trovärdig rörelse, och trovärdighet dämpar komik. Fysiken drar mot det naturliga, medan poängen ofta kräver det onaturligt tydliga.
- **Motangrepp, som gör tesen starkare:** upphovet kan sätta karaktärens övertygelser för att framkalla takten. "Smakproverna vi ger oss själva" blir till exempel övertygelsen "ingen ser mig nu" plus en spelstyrka (amplitud). Komik i en sketch är ofta just en karaktär med en felaktig eller avslöjad övertygelse. Notans avslöjande ("men jag känner inte ens dig?") är exakt det: B:s övertygelse, okänd för A och tittaren, blottas i montaget.
- **Dom:** P1 och P6 räcker inte med ett sinne. Det behövs **två sinnen:**
  - **Upphovets sinne** (M3–M2): premiss, vändning, krok, mot tittaren. Det finns delvis i formatkorten.
  - **Karaktärens sinne** (M1–M0): övertygelse, avsikt, prioriteringar, i scenen. Det finns delvis i liggaren.

  Upphovet styr karaktären genom vad den tror, vet och vill, och genom hur tydligt den spelar. Tomrummen T1 och T3 i problembilden är gränssnittet mellan de två.

### A3. CM talar i ytor (angriper P1:s nytta, stärker en annan)
- **Det vi vet:** 21 CM-meningar har prövats mot förvärlden (`forvarld/*/meningar*.json`).
  | sort | meningar | antal |
  |---|---|---|
  | struktur, kamera, redigering | en sekund längre i slutet (två varianter), hoppa över skopandet, ta bort scen 5, stabilisera kameran, gå närmare Lærke, byt texten | 7 |
  | föremål och plats | kaka i stället för glass, ost i stället för kött, glassbar, ta bort disken, ta bort vågen, foodtruck | 6 |
  | kroppens sätt | andra handen (två varianter), skopandet långsammare, armarna i kors, stå still | 5 |
  | handling, roll, ordning | två smakprov, en fjärde gissare, Morten före Mads | 3 |
  | känsla | le efter att kunden fått smakprovet | 1 |
- **Angreppet:** bara en mening av 21 ber om ett inre tillstånd. CM:s språk är ytor: "långsammare", inte "hon har gott om tid". Ett system som kräver skäl som indata går emot hur CM uttrycker sig.
- **Motangrepp:** tesens värde ligger inte i att CM uttrycker skäl. Det ligger i att **målet består medan medlen räknas om.** "Kaka i stället för glass": målet att ge ett smakprov består, men skopandet ersätts av att plocka eller skära. "Ta bort disken": vad lutar hon sig mot, var står kunden? "Två smakprov": två förlopp, inte en kopierad rörelse. Det är ägarens egen formulering (13 nov): "byta arm är mer än att bara växla axlarna […] kroppen måste roteras och ett nytt sätt att skopa nu kommer upp."
  - *Min räkning:* ungefär 12 av 21 meningar har följder som ingen har angett (1, 2, 4, 6, 8, 10, 12, 13, 15, 16, 18, 21 i listan ovan).
  - De 7 rent strukturella behöver inget sinne alls.
- **Dom:** P1 som *indata från CM* faller. Som *mekanism för följder* står den kvar, och det är där liggarens handkodade spridning (`frihetsgrader[].spridning`) är svagast: den räknar bara upp följder som skribenten förutsåg.

### A4. Produktens slutkropp är en människa (stärker P1 på manusnivå)
- **Det vi vet:**
  - Ägaren 2 nov: "Produkten är det manus CM godkänner, och kunden spelar in efter det scen för scen. Renderingen ska bara göra det tydligt."
  - Pass 8: "instruera inte personlighet", "förlagans personliga drag blir tillåt, tvinga inte", "varje scen behöver känsla, struktur och vad den kräver".
- **Angreppet mot vår egen väg:** vi lägger mycket arbete på att göra förvärldens kropp exakt. Den kropp som till slut rör sig är kundens personal, och den läser inte ledvinklar.
- **Följd:** avsiktsriggens kärna, att spara skälen och låta en kropp räkna fram rörelsen, är precis hur man regisserar människor: mål och omständigheter i stället för rörelser. *Min tolkning:* skälen är det som reser till kunden i manuset, och 3D-kroppen är förhandsvisningen av vad skälen brukar ge.
- **Dom:** P1 står starkare på manusnivå än på renderingsnivå. Det flyttar också vad som är facit: om skälen i manuset gör att personalen spelar rätt, inte bara om 3D-kroppen ser rätt ut.

### A5. Stil och personligt sätt (angriper P1)
- **Det vi vet:** "Trogen före stiliserad". Förlagans personliga drag ska tillåtas, inte tvingas. Ägaren märker direkt när en kropp är generisk ("armar som flaxar", 7 nov).
- **Angreppet:** två personer med samma övertygelse rör sig olika. Det som skiljer dem är stil, inte skäl. En kropp som räknas fram ur skäl utan minne blir generisk.
- **Dom:** P1 kräver en stil eller ett minne per person, och det kommer ur originalet. Det stöder A1:s svagare form.

### A6. Montaget (angriper P5, P6)
- **Det vi vet:** notans mening ligger mellan tagningarna (berättat och avslöjat rum, BUGG-BLOCK.md). Gelatos vändning ligger i ett klipp och ett musikbyte. Redigering är ett eget lager (målbilden).
- **Angreppet:** en simulering lever i en sammanhängande tid. TikTok-mening hoppar: klipp, ellipser, perspektivbyten. Kroppen behöver inte vara sammanhängande över ett klipp, och meningen kan finnas just i hoppet.
- **Dom:** P5 gäller inom en tagning. Montaget hör till upphovets sinne (A2), inte till kroppen.

### A7. Hastighet och kostnad (prövar P5)
- **Det vi vet:**
  - Jev under 1 s. Långsam väg med stark modell 4–9 s.
  - MaskedMimic kör i realtid på GPU (Modal, L4), men vårt prov är inte löst (0039).
  - Jutsu har ingen GPU.
  - Gatewayens kredit är nästan slut, och innehållsanalysen stannade flera gånger på krediter.
- **Angreppet:** ett sinne som spelar rollen och uppdateras vid händelser är en stark modell per ändring. Det motsvarar vår långsamma väg, inte vår snabba.
- **Dom:** P5 håller arkitektoniskt. Det motoriska lagret kan vara en kontroller i realtid, och sinnet uppdateras sällan. Men sinnet kan inte vara Jev. Jev kan som mest välja bland prioriteringar som sinnet redan har formulerat. Kroppen räknas på en GPU utanför Jutsu, och Jutsu får det bakade resultatet (T1-armaturen visar att bakade rotationer går in som skelettanimation).

### A8. De härledda skälen är hypoteser (angriper P6)
- **Det vi vet:**
  - Originalet är sanning, och det härledda är märkt `antagen`.
  - E1: 29 av 43 lager var stabila mellan körningar.
  - Jev varierar mellan körningar.
- **Angreppet:**
  - "Fråga scenen varför" ger ett svar som är internt sammanhängande men kanske fel om originalet. Vid ingest gissar någon fortfarande. Gissningen görs bara en gång och blir sedan sanning i scenen.
  - En stark modell hittar gärna på en rik bakgrundshistoria ("lektionen började 14:00") som ingenting i klippet stöder.
- **Dom:** P6 står bara om skälen bär märkning, osäkerhet och stabilitet, och om de prövas som formatkortens lager prövades. Det är obeprövat → 0043.

### A9. "Ouppfunnet" stämmer delvis (angriper P7)
Det som finns, med källor:
- **Språkmodell som planerare över fysiskt simulerade kroppar:** SIMS (ICCV 2025) med skript genererade av en språkmodell och textstyrda fysiska policyer; UniHSI (ICLR 2024) med en kedja av kontakter till en enad kontroller.
- **Rörelse som uppstår ur fysik och beteende:** Euphoria (NaturalMotion), där snubblingar och tag i omgivningen inte är animerade.
- **Kontroller som tar ofullständiga villkor och en referens:** MaskedMimic (ProtoMotions), som vi redan kör.
- **Omvänd planering:** Baker m.fl., som ovan.

Det som inte finns: skript och kontaktkedjor i SIMS och UniHSI är fortfarande **etiketter** (gå till stolen, sätt dig). Gränssnittet med prioriteringar (marginal, överlapp, uppmärksamhet) och kopplingen till inläst video med återgivning 1:1 har jag inte hittat. **Dom:** P7 står i smal form.

### A10. Det kontrafaktiska testet måste skärpas (prövar P3)
- **Angreppet:**
  - Liggaren klarar testet formellt redan i dag. Sätt `fg_hand` till vänster, så ändras rörelsen med nödvändighet, eftersom spridningen och regi-mallen säger det. Ändå är det etiketter med handskriven följd, precis det tesen vill ersätta.
  - Testet saknar också sin motsats: det som *inte* ska ändras får inte ändras (1:1 utanför ändringen, våra grindar).
- **Skärpt test, i tre delar** (*min formulering*):
  1. **Nödvändighet:** ändras meningen, så ändras rörelsen.
  2. **Bevarande:** det som inte berörs av meningen är oförändrat, mätt mot originalet.
  3. **Oförutsedda följder:** antalet riktiga följder som ingen har skrivit in, till exempel att dörren stängs med handen och att blicken vidgas. Det är det som skiljer ett sinne från en spridningslista.
- **Dom:** P3 står i skärpt form och blir hjärnans grind (förslag: G8 i bryggan) → 0041.

### A11. Fart och stress (P4) mot det vi redan vet
- **Det vi vet:** ägaren 31 okt och 1 nov: rörlighet är iscensättning, alltså fart i hur scenen spelas ut, inte skak och effekter. Ägarens läsning av kebabklippet skilde på tempo, motivets andel av bilden och entréer.
- **Dom:** P4 är samma insikt från andra hållet, och står. Tesen ger dessutom tre mätbara signaturer (marginal, överlapp, uppmärksamhet) som går att räkna på MHR-rörelser vi redan har. Om de finns i vårt material är obeprövat → 0042.

---

## 3. Det som står kvar (skärpt)

| | insikt | ur |
|---|---|---|
| **S1** | **Två sinnen och en kropp med minne.** Upphovets sinne (premiss, vändning, krok, mot tittaren) styr karaktärens sinne (övertygelse, avsikt, prioriteringar), som styr en kropp som utgår från originalets rörelse och bara avviker där skälen kräver det. | A1, A2, A5 |
| **S2** | **Gränssnittet är prioriteringar och villkor, inte etiketter.** Det gäller liggarens frihetsgrader, som är etiketter med handskriven spridning, och rörelsemodellens "mål per tid", som är nyckelbilder i ny form. | P2, A3, A10 |
| **S3** | **Målet består, medlen räknas om.** Där ger ett sinne mest: för cirka 12 av 21 CM-meningar har ändringen följder som ingen angett. | A3 |
| **S4** | **Skälen reser till kunden, rörelsen gör det inte.** Manuset bär mål och omständigheter, och 3D-kroppen är förhandsvisningen. | A4 |
| **S5** | **Det skärpta kontrafaktiska testet** (nödvändighet, bevarande, oförutsedda följder) är definitionen av inbakad mening, och blir en grind. | A10 |
| **S6** | **Fart är inte stress**, precis som rörlighet inte är skak. Tillstånd syns i marginal, överlapp och uppmärksamhet. | P4, A11 |
| **S7** | **Upphovet styr genom övertygelser.** Komik är ofta en karaktär med en felaktig eller avslöjad övertygelse, plus spelstyrka. | A2 |

Det här ändrar problembilden: nivåerna M0–M3 får två ägare. Upphovets sinne äger M3–M2, karaktärens sinne äger M1, och kroppen med minne äger M0. Tomrummen T1 och T3 blir frågan om hur upphovet uttrycker en takt som övertygelser hos karaktären.

---

## 4. Där argument inte räcker: vi böjer oss

Det här kan inte avgöras utan försök. Var och en är en uppgift i `delegat/uppdrag/`.

| uppgift | frågan som bara data kan avgöra | om svaret blir nej |
|---|---|---|
| **0041** Det skärpta kontrafaktiska testet på det vi har | Hur långt når liggaren, Jev och regin på nödvändighet, bevarande och oförutsedda följder, för gelato, b-tilltal och notan? | Då är dagens mening bara etiketter, och S2 är bekräftad. |
| **0042** Signaturerna i rörelse | Finns marginal, överlapp och uppmärksamhet som mätbara drag i våra MHR-rörelser, och skiljer de sig från fart? | Då står P4 och S6 utan mätbart innehåll i vårt material. |
| **0043** Omvänd läsning av skäl, och dess stabilitet | Kan en modell läsa ut övertygelse, avsikt och prioriteringar per person och tagning ur videon, stabilt mellan körningar och utan påhitt? Och kan upphovets sinne läsas ur formatkortet och knytas till takter? | Då faller P6 och S1 vid ingest, och skälen måste komma från människor (CM, manus). |
| **0044** Prioriteringar som villkor på en riktig kontroller | Ger en ändrad prioritet (marginal, uppmärksamhet, överlapp), uttryckt som villkor kring originalets rörelse, en igenkännbar ändring av tillståndet utan att 1:1 förstörs? | Då når P2 inte kroppen med dagens modeller, och vi stannar vid IK och spegling. |
| **0045** Ägarens blinda prov på skäl mot rörelse | Föredrar ägaren ett manus med skäl framför ett med rörelser för samma ändring, och ser hen skillnad i förhandsvisningen? | Då är S4 fel, och produkten ska bära rörelser. |

Ordning och beroenden:
- **0041, 0042 och 0043** kan köras direkt och parallellt. De kräver ingen ny modell, bara befintlig data. 0043 kostar några cent via gatewayen.
- **0044** körs efter att 0039 eller 0040 har gett en fungerande kontroller.
- **0045** kräver ägaren, och underlaget ur 0043.

---

## 5. Källor
- Tesen: `Desktop/utmana 1.txt`, `Desktop/utmana 2.txt` (ägaren, 14 nov).
- [SIMS: Simulating Human-Scene Interactions with Real World Script Planning (arXiv 2411.19921)](https://arxiv.org/abs/2411.19921), [ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Wang_SIMS_Simulating_Stylized_Human-Scene_Interactions_with_Retrieval-Augmented_Script_Generation_ICCV_2025_paper.pdf)
- [UniHSI (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/file/6a6ecedac816a24f92ad1f444b1edcb0-Paper-Conference.pdf)
- [Baker, Saxe och Tenenbaum, Action understanding as inverse planning (MIT DSpace)](https://dspace.mit.edu/handle/1721.1/60852); [Baker m.fl. 2017, Rational quantitative attribution of beliefs, desires and percepts](https://cbmm.mit.edu/publications/rational-quantitative-attribution-beliefs-desires-and-percepts-human-mentalizing)
- [Euphoria (GTA-wikin, andrahandskälla)](https://gta.wiki/w/Euphoria), [MCV om Euphoria](https://mcvuk.com/development-news/ecstatic-movement-naturalmotion-on-euphoria/)
- I repot: `byggsten/hjarna/PROBLEMBILD.md`, gelatos kort och liggare, `forvarld/*/meningar*.json`, `forvarld/kropp/forskning/mm/ut/matt_mm_a.json`, `byggsten/jutsu/BUGG-BLOCK.md`, `karta/videoforandring/harness.md`.
