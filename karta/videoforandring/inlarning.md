# Inlärningen: vad som förändras per klipp

Skrivet 2 nov 2026. Det här dokumentet är ett utkast till tänkandet bakom videodelen i `video/`. Inget av det är byggt än.

Kärnfrågan är hur en content manager kan säga "gör det här klippet till kund Y, men…" och få en ny version. Den ska följa det som fungerar på TikTok, passa kundens linje och vara så trogen originalet som möjligt. Det som tränas är *vad* som ska förändras och *hur mycket*. Hur det ser ut i appen (reglage, etiketter) kommer senare.

## 1. Tre nivåer och en ram

| Nivå | Frågan | Vad vi har | Vad som saknas |
|---|---|---|---|
| **Klippet** | Hur är det byggt, och hur upplevs det? | Typ, intent A/B/C, mekanik, scener, takter, rörlighet per scen, kamera, personer, saker, manus ur rekonstruktionen. Vertikalerna scenografi, agerande och rytm. | Normen för typen. Repliker som redigerbar yta. Hur säljandet *tas* (seriöst eller med självdistans). |
| **Profilen** | Vad kännetecknar kontot genomgående? | Ingenting sammanslaget. Allt finns per klipp. | Typisk längd och scenografi, frontfigurer, humorns ton, mixen a/b/c som sekvens, och hur planerat kontot är. |
| **Ramen** | Relativt till vad? | Engagemang mot kontots egna klipp (förurvalet). | Samma relativa mått för alla egenskaper, mot tre ramar (se 4.3). |

Utöver det kommer **instruktionen**: det CM säger om ett enskilt klipp. Den är en ny sorts indata. Den ska översättas till operationer, och de ska balanseras mot allt ovan.

## 2. Referenspunkter

Var och en har lösts, helt eller delvis, någon annanstans. Under varje står principen vi tar med oss.

### 2.1 Redigering är val under idiom, inte fri generering
**Leake m.fl., Computational Video Editing for Dialogue-Driven Scenes (SIGGRAPH 2017).** Varje replik får en tagning ur materialet, utifrån *idiom* som användaren väljer: "börja brett", "den som talar syns", "undvik hoppklipp". Idiomen är kostnadstermer som kan läggas till positivt eller negativt, och en lösare väljer sekvensen på några sekunder. Handsatta vikter enligt idiomlistan gav bra klippning utan dyr annotering.

**Wang m.fl., Write-A-Video (SIGGRAPH Asia 2019).** Text blir en montage. Bilder matchas mot texten, och sedan sätts klippet ihop av en optimering över filmiska regler. Snabbare eller långsammare tempo och mer eller mindre rörelse är reglage på samma optimering. Användarstudien visade att varje energiterm bidrog.

**Principen:** Normpunkterna ("grundplaceringen") och flera slutmål blir *kostnadstermer* i en lösare. Det är redan vår delning, att en deterministisk lösare sköter siffrorna och Jev sköter omdömet. Vikterna kan sättas för hand först och läras sedan.

### 2.2 Redigera representationen, rendera mediet, syntetisera luckorna
**Fried m.fl., Text-based Editing of Talking-head Video (SIGGRAPH 2019).** Man redigerar transkriptet: lägger till, tar bort eller ändrar ord. Systemet letar upp de delar av originalet som kan bära den nya texten och *syntetiserar* det som saknas med en neural rendering. Det är samma idé som Descript gör vardaglig.

**Principen:** Vår redigeringsyta är manuset (rekonstruktionen ger det redan), inte videon. Efter en ändring avgör en **täckningskarta** per segment vad originalet fortfarande bär och vad som måste syntetiseras. Hos oss blir det en 3D-skiss, och på sikt AI-video.

### 2.3 Fri instruktion blir en plan av operationer ur en sluten låda
**Wang m.fl., LAVE (IUI 2024).** En plan-and-execute-agent gör om ett fritt kommando till en plan av redigeringsfunktioner och kör den. Användaren kan alltid justera för hand.

**Tilekbay m.fl., ExpressEdit (IUI 2024).** En studie med 10 redigerare och 176 kommandon visade att ett kommando består av tre sorters referenser: *tid* ("när skylten syns"), *rum* (en plats i bilden) och *operation med parametrar*. Deltagarna kände sig begränsade av sju operationer.

**Principen:** En CM-instruktion tolkas till `{var, vad, hur}`. Operationerna kommer ur en sluten lista som får växa, och det finns en fritextreserv för det som inte passar. Instruktioner som *reviderar* en tidigare ändring ("lite mindre") täcktes inte av ExpressEdit, så det måste vi lösa själva.

### 2.4 Planera före rendering, med entiteter som håller ihop
**Lin m.fl., VideoDirectorGPT (2023).** En LLM skriver en videoplan: scenbeskrivningar, entiteter med placering, bakgrund per scen och *konsistensgrupper*, till exempel `{kock: [1,2,3,4], ugn: [1]}`. Renderaren håller sedan varje grupp likadan över scenerna.

**Xu m.fl., FilmAgent (2025).** Agenter i rollerna regissör, manusförfattare, skådespelare och fotograf arbetar i virtuella 3D-rum: 15 lokaler, 9 bildtyper, 21 handlingar. Två granskningsslingor används, *Critique-Correct-Verify* och *Debate-Judge*. Den fick bättre betyg än en ensam modell med mer resonemang. Den begränsas av förbyggda miljöer och saknar en roll för klippning.

**Principen:** Vårt manus är redan en sådan plan, och lokalen i 3D är redan ett sådant rum. Två saker kan vi lägga till:
- **Konsistensgrupper över klipp, inte bara över scener.** Profilens karaktärer är grupper som håller mellan klippen (se 4.2).
- **Klippningen som egen roll.** Den saknas i FilmAgent, och det är just där CM:s instruktioner landar.

### 2.5 Karaktärer och syfte som graf
**Vicol m.fl., MovieGraphs (CVPR 2018).** Klipp märkta som grafer: karaktärer med attribut, relationer, interaktioner och *motiveringar*, ankrade i tid och kopplade till ansiktsspår.

**Principen:** Profilens förmågor härleds som en graf: vem som återkommer, i vilken roll, med vilken funktion och mot vem. Grafen kommer ur klippen, inte ur text kunden skrivit. Ur den kan "frontperson" utläsas, och det behöver inte sägas.

### 2.6 Bra är relativt och mäts på rätt sak
**Wu, Rizoiu och Xie, Beyond Views (ICWSM 2018).** Om 5,3 miljoner YouTube-videor:
- Visningar drivs av extern spridning.
- *Relativt engagemang*, alltså tittartid justerad för längd, är stabilt över tid och följer kvalitet.
- Det går att förutsäga ur innehåll och kanal (R² 0,77 för andel sett).

**Li m.fl., Delving Deep into Engagement Prediction of Short Videos (2024).** Ett längdnormaliserat mått på andel sett, mätt bara ur innehållet. Historik om skaparen påpekas som en begränsning.

**TikTok:**
- Newsroom (2020) säger att följarantal och tidigare framgångar inte är direkta faktorer, och att det är starkt när någon tittar klart på en längre video.
- Det läckta "Algo 101" (NYT, 2021) beskriver poängen som en viktad summa av förutsagda handlingar: gilla, kommentera, speltid och om klippet spelas alls.

**Principen:** "Bra" är en *residual*, alltså hur mycket bättre eller sämre ett klipp gick än väntat för sitt konto, sin längd och sin tid. Råa visningar räcker inte. Tittartid är plattformens starkaste signal, och den saknas i banken. Den finns troligen i kundernas egen statistik (att kontrollera, se 7).

### 2.7 Strukturnormer finns publicerade och validerade
**TikTok Creative Codes.** Sex principer: TikTok-first, trender, produktion, struktur, stimulans och ljud. Strukturen är *krok, kropp, avslut*. Enligt TikTok fångas 90 % av annonsminnet under de första sex sekunderna.

**Google ABCD (Attract, Brand, Connect, Direct).** Validerad av Kantar på cirka 11 000 annonser, med modellerat samband mot försäljning och varumärke. Google har släppt *ABCDs Detector* som öppen källkod. Den bedömer en video mot checklistan automatiskt.

**Principen:** Marknadsföringsspåret (intent B, och delvis C) har en annan dimension än karaktärer i en lokal, och normen finns redan nedskriven. Den kan bli en checklista som en detektor bedömer, på samma sätt som ABCDs Detector.

Båda gäller *annonser* och visar modellerade samband, inte orsaker. Organiskt restauranginnehåll kan bete sig annorlunda, så banken får avgöra vad som håller.

### 2.8 Bågar är få och kan klustras
**Reagan m.fl., The emotional arcs of stories are dominated by six basic shapes (2016).** Cirka 1 700 berättelser föll i sex bågar, och de populäraste var sammansättningar av dem.

**Principen:** Takterna per klipp, och sekvensen per profil, kan troligen klustras till ett fåtal former. Normen beskrivs då som "vilka former fungerar för den här typen", inte som en lista med siffror.

### 2.9 Skrivna principer och parvisa preferenser är harnessen
**Bai m.fl., Constitutional AI (2022).** Skrivna principer gör att modellen kan kritisera och revidera sig själv. AI-märkta par tränar en preferensmodell, och human feedback finns kvar för det svåra. Den kända risken är att policyn utnyttjar domarens svagheter (*reward hacking*).

**Principen:** Harnessen har tre delar:
- **Konstitutionen**: normpunkter, låsta invarianter och intent-låset som hagen-ui redan har (`scene-rails-intent-locked`: en ändring som gör underhållning till marknadsföring avvisas tills CM bryter formatet med en orsak).
- **En domare**: Gemini, validerad mot människa till minst 80 %, enligt NASTA.
- **Bradley–Terry** på par, som vi redan kör.

Risken för reward hacking är skälet att domaren valideras och att publicerade utfall till slut blir facit.

## 3. Det vi tar med oss, i sju meningar

1. Videon redigeras inte direkt. Manuset redigeras, och sedan renderas videon.
2. En instruktion blir en plan av operationer ur en sluten lista.
3. Abstrakta mål som krok och fart in är kostnadstermer i lösaren och villkoras av intent. De är inte operationer.
4. Normen är en uppsättning robusta idiom per typ, och "bra" är residualen mot en ram.
5. Det som inte får ändras (lokalens öppenhet, intent, profilens karaktärer) är låst mot originalet och profilen.
6. Täckningskartan säger vad originalet bär och vad som blir 3D eller ny inspelning.
7. Lärandet går från billiga och svaga signaler till dyra och starka: bank, bedömningar, CM:s val, publicerat utfall.

## 4. Modellen, lager för lager

### 4.0 Representationen
Manuset ur rekonstruktionen innehåller personer, rörelser, kamera och lokal. Det behöver fyllas på med:
- **repliker och skärmtext med tider**, så att "meningen i tredje scenen" och "när han säger badoo" går att peka på
- **takter** ur `typer`, alltså öppning, mitt och slut oberoende av bildklippen
- **karaktärernas roller i klippet**, kopplade till profilens karaktärer (4.2)

### 4.1 Normen, grundplaceringen
För varje kombination av typ, intent och längdintervall:
- **Fördelningar** i banken över egenskaper: längd, antal scener, tid till första takt, var punchlinen ligger, klipprytm, rörlighet, personer i bild, scenografins öppenhet.
- **Idiom:** vilka egenskaper som följer med positiv residual *inom* typen. Exempel: "punchline före 70 % av längden", "första scenen kortare än 2 s när intent är A", "produkten syns i bild före avslutet när intent är B".
- **Robusthet:** Ett idiom räknas bara om det håller när ett konto i taget lämnas utanför, och i båda halvorna av tiden. Det är "robusta och återkommande grundpunkter": det som inte beror på ett enskilt konto eller en enskild månad.
- **Utdata** är en lista med idiom, var och en med riktning, styrka och osäkerhet. Varje harness läser den.

### 4.2 Profilen
Tre delar:
- **Förmågor.** Karaktärsgrafen (2.5): återkommande personer, deras roller (frontperson, motspelare, statist, kund), lokaler och rekvisita. Den är härledd, aldrig angiven. Konsistensgrupperna (2.4) håller den ihop mellan klippen.
- **Linjen.** Profilens egen fördelning över samma egenskaper som normen, plus mixen a/b/c som tidssekvens. Är det serier, rotation eller slump?
- **Planeringsgrad.** Mäts indirekt med tre mått:
  - *spridning*: hur olika klippen är
  - *struktur i spridningen*: om mixen har mönster (låg entropi i övergångarna) eller är brus
  - *passform*: om utförandet följer intent

  Ihopslängt bör synas som stor spridning utan mönster. Helhetskänslan går inte att räkna fram, så den bedöms parvis mellan profiler ("vilken känns mer genomtänkt?") med samma Bradley–Terry som scenerna.

### 4.3 Ramen
Varje egenskap hos ett klipp uttrycks i tre koordinater:
- **mot kontot**: kortare än vanligt för det här kontot
- **mot kohorten**: liknande profiler i samma bransch och storlek, med liknande typmix
- **mot banken**: hur content görs i dag

Ett halvt snöre blir ett snöre i förhållande till något. Normen (4.1) bor i kohorten och banken. Linjen (4.2) bor i kontot.

### 4.4 Instruktionen
CM:s fria text tolkas, schemastyrt (som `typer` redan gör mot Gemini), till en plan:

```
{ mal:        "kund Y" | null,                // anpassa till profil
  operationer: [ { var: <tidsreferens>, vad: <operation>, hur: <parametrar> } ],
  stil:       [ "snärtig klippning", ... ],    // går till lösaren som mål
  abstrakt:   [ "mer fart in", ... ],          // går till lösaren, villkoras av intent
  las:        [ ... ] }                        // det CM uttryckligen vill behålla
```

**Tidsreferenser v0:**
- scen n
- sista delen eller öppningen
- en replik ("när han säger X")
- ett objekt ("scenen med rätten")
- en takt (punchlinen)

**Operationer v0:**

| Operation | Gäller |
|---|---|
| `ta_bort` | scen eller takt |
| `forlang` och `korta` | scen |
| `flytta` | takt |
| `byt_replik` | replik |
| `ny_avslutning` | slutet |
| `byt_kamera` | segment (vinkel, utsnitt) |
| `tydliggor` | objekt eller person i ett segment |
| `klipprytm` | segment |
| `anpassa_till_profil` | hela klippet: karaktärer, lokal, ton |

Listan får växa när det kommer instruktioner som inte passar. De loggas i fritextreserven.

### 4.5 Lösaren
Indata är planen, normen för typen, profilen, originalets låsta invarianter och slutmålens vikter. Utdata är ett nytt manus. Kostnadstermerna är slutmålen:

1. **Instruktionen uppfylld.** CM:s operationer går före allt annat de inte strider mot.
2. **Normen.** Typens idiom, med intent-villkor. Krok och fart in hör hemma här, inte i någon operation.
3. **Linjen.** Nära profilen eller medvetet bort från den.
4. **Trohet.** Så mycket av originalet som möjligt: lokalens öppenhet, handlingen och personerna.
5. **Täckning och kostnad.** Så lite syntes som möjligt.
6. **Enkelhet för CM.** Få och begripliga ändringar utöver det som bads om, så att resultatet går att förklara ("Ändrat / Mätt / Modellens tolkning" finns redan i `#v2`).

Vikterna sätts först för hand, som hos Leake. Sedan lärs de av CM:s val (4.7).

### 4.6 Täckningskartan
För varje segment i det nya manuset finns fyra möjligheter:

| Täckning | När |
|---|---|
| **Original** | Segmentet finns kvar orört. |
| **Original, omformat** | Trim, ny ordning eller virtuell kamera i 2D (`#v2`, `#bedom2d`). |
| **3D-skiss** | Ny replik, förlängd scen, ny vinkel som originalet inte har. Rummet `~modell` finns. |
| **Spela in** | Det som skissen bara kan visa och inte ersätta. Det är besked till kunden om vad som ska filmas. |

Kartan räknas fram, och CM väljer den aldrig. Den är också kostnadsterm 5 och det CM ser först: hur mycket av klippet som fortfarande är originalet.

### 4.7 Lärandet
Signalerna, från billiga och svaga till dyra och starka:

| Signal | Lär | Finns |
|---|---|---|
| Relativ prestation i banken (residual) | Normens idiom | Metadata för 5 143 klipp, nu |
| Parvisa bedömningar, människa och validerad Gemini | Vertikalerna, helhetskänslan, profilernas planeringsgrad | 2 + 10 + 54 (bankens urval) |
| CM:s val: accepterar, ändrar, ångrar | Lösarens vikter, operationslistan, parsern | När verktyget används |
| Publicerat utfall för kundens klipp mot förutsägelsen | Allt, som facit | När kunderna publicerar. Tittartid om deras statistik nås |

## 5. Dina exempel som testfall

| CM säger | Plan | Abstrakt eller stil | Täckning |
|---|---|---|---|
| "Gör denna video anpassad till restaurang Y, men skapa en ny version där sista delen klipps bort och slutmeningen är 'shu vad händer'" | `anpassa_till_profil(Y)`, `ta_bort(sista takten)`, `ny_avslutning(replik "shu vad händer")` | | Ny replik ger 3D-skiss eller spela in. Lokal och karaktärer från Y. |
| "Gör meningen i tredje scenen såhär, och förläng scenen för att möjliggöra det, men gör klippningen snärtig" | `byt_replik(scen 3)`, `forlang(scen 3, tills repliken ryms)` | stil: snärtig klipprytm | Scen 3 blir 3D-skiss. Resten original. |
| "Denna video börjar rätt långsamt, se om man kan inleda klippet med mer fart eller gå direkt till kärnan" | `korta` eller `ta_bort(öppningen)`, eller ingen operation | abstrakt: fart in, villkorad av intent | Helst original, omformat (trim). |
| "Videon är lite lång, gör punchlinen lite tidigare och ändra kameravinkeln för den scenen när han säger 'badoo'" | `korta(helhet)`, `flytta(punchline, tidigare)`, `byt_kamera(repliken "badoo")` | | Trim i originalet. Ny vinkel ger 2D-kamera om utsnittet ryms, annars 3D-skiss. |
| "Försök göra scenen med rätten lite tydligare" | `tydliggor(objekt "rätten")` | | Utsnitt eller tid i originalet. 3D-skiss vid ny vinkel. |

Testet för parsern är att de fem ger just de här planerna. Det kan mätas innan lösaren finns.

## 6. Vad banken redan tillåter, och vad den inte tillåter

- **Metadata:** 5 143 klipp från 63 profiler, med längd, visningar, gillanden, kommentarer, delningar och datum. Profilernas baslinjer, residualerna och tidssekvenserna kan räknas nu, utan nedladdning.
- **Nedladdat och sållat:** cirka 1 000 klipp är nedladdade. 547 är sållade med typ, från 39 konton (median 18 per konto, 27 konton med minst 10). Typerna: sketch 225, matporr och process 181, direkt tilltal 99, provsmakning 17, annat 25. Typ och intent per klipp finns för de sållade, så mixen som sekvens går att se per konto.
- **Lokalt analyserat:** 79 klipp. Det räcker inte för normer på scennivå än.
- **Saknas:**
  - tittartid och andel sett, alltså plattformens starkaste signal
  - repliker med tider i manuset
  - profilnivån helt och hållet
  - bedömningar mellan profiler

## 7. Ägarens svar (2 nov)

1. **Verktyget lämnar ifrån sig det CM godkänner.** Det CM godkänner är: "det här, så som det är utformat, ska kunden återskapa genom att spela in klippet scen för scen, så som de uppfattar videon". Renderingen (3D, 2D eller AI) finns bara för att göra det tydligt för kunden vad som ska spelas in.
   - **Följd:** Täckningskartans fjärde läge, "spela in", är huvudfallet och inte undantaget. Manuset är produkten.
   - **Planera för:** Tidsstämplar och tidsrum för voiceover loggas per scen, så att de kan ligga till grund för klippning senare. En app som hämtar en mall från LeTrend kan då be verksamheten spela in exakt 3,2 s.
2. **Vägningen görs per klipp.** I det stora hela kan profiler bedömas i olika kategorier. Det som väger tyngst är kvaliteten på scenerna och klippen: flöde och inspelningskvalitet. Humor räknas som ett eget metavärde. LeTrends arbetsteori är att humor som är effektiv och intressant, med verksamheten som fond, fungerar.
3. **Kunderna kan ge tillgång till sin statistik.** Tittartid blir alltså möjlig som facit.
4. **Marknadsföringsspåret är en egen distinktion.** Gränsen mellan underhållning och marknadsföring är ofta otydlig. Ibland ligger fokus på maten eller miljön, utan att det är ett klassiskt montage eller montage med voiceover. Det liknar CapCuts mallar: ett antal scener där vissa är matscener, och korta scener (0–1 s) som ger fart och marknadsföringskänsla. Spåret blir då en **mallstruktur**: en rad platser, var och en med längd, funktion och innehållsslag. Det är inte en checklista ovanpå scenmanuset.

## 8. Föreslagen ordning

Billigast och mest grundande först. Varje steg går att pröva för sig.

1. **Profilbaslinje och residual** på de 5 143 klippens metadata. Kontrollen: är residualen stabil i delade halvor per konto? Wu m.fl. säger att engagemang är stabilt, men visningar inte är det. Gratis. **Gjort 2 nov, se [residual.md](residual.md).**
   - Residualen är en ren signal: oberoende mellan grannklipp och inte styrd av längd eller ålder.
   - Två saker måste tas om hand innan normen byggs:
     - Banken är vald på utfallet. Det behövs ett osållat stickprov.
     - Räckvidd och engagemang är olika mål.
   - **Stickprovet 3 nov:** 235 slumpvisa klipp, selektionen borta. Personer i bild bär räckvidden (+0,28 log10, ungefär 1,9 gånger). Montage kostar räckvidd men ger gillanden. Texttungt gillas och delas mindre.
2. **Profilnivån på de 547 sållade:** spridning, mix som sekvens och planeringsgrad per konto, plus ett första parvis bedömningsverktyg mellan profiler.
3. **Normen v0** på typnivå, med de egenskaper som finns för alla sållade (längd, typ, intent, säljandel, mekanik). Leave-one-account-out. Normen på scennivå kommer när fler klipp är analyserade.
4. **Parsern v0:** Gemini schemastyrt mot operationslistan, testad på de fem exemplen i avsnitt 5.
5. **Täckningskartan** för de tre rekonstruerade klippen, med parserns planer som indata.
6. **Lösaren v0** med handsatta vikter, på ett klipp hela vägen.

## Källor

- Leake, Davis, Truong, Agrawala. [Computational Video Editing for Dialogue-Driven Scenes](https://graphics.stanford.edu/papers/roughcut). SIGGRAPH 2017.
- Wang, Yang, Hu, Yau, Shamir. [Write-A-Video: Computational Video Montage from Themed Text](https://faculty.runi.ac.il/arik/site/includes/papers/WriteAVideo.pdf). SIGGRAPH Asia 2019.
- Fried m.fl. [Text-based Editing of Talking-head Video](https://arxiv.org/abs/1906.01524). SIGGRAPH 2019.
- Wang m.fl. [LAVE: LLM-Powered Agent Assistance and Language Augmentation for Video Editing](https://arxiv.org/abs/2402.10294). IUI 2024.
- Tilekbay m.fl. [ExpressEdit: Video Editing with Natural Language and Sketching](https://arxiv.org/abs/2403.17693). IUI 2024.
- Lin, Zala, Cho, Bansal. [VideoDirectorGPT](https://arxiv.org/abs/2309.15091). 2023.
- Xu m.fl. [FilmAgent: A Multi-Agent Framework for End-to-End Film Automation in Virtual 3D Spaces](https://arxiv.org/abs/2501.12909). 2025.
- Vicol, Tapaswi, Castrejón, Fidler. [MovieGraphs](https://arxiv.org/abs/1712.06761). CVPR 2018.
- Wu, Rizoiu, Xie. [Beyond Views: Measuring and Predicting Engagement in Online Videos](https://arxiv.org/abs/1709.02541). ICWSM 2018.
- Li m.fl. [Delving Deep into Engagement Prediction of Short Videos](https://arxiv.org/abs/2410.00289). 2024.
- TikTok Newsroom. [How TikTok recommends videos #ForYou](https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you/). 2020.
- Gizmodo om NYT:s "Algo 101". [Leaked TikTok doc](https://gizmodo.com/leaked-tiktok-doc-reveals-its-obvious-secret-to-an-addi-1848166901). 2021.
- TikTok for Business. [Creative Codes](https://ads.tiktok.com/business/en/creative-codes).
- Kantar. [Validating Google's ABCD framework](https://www.kantar.com/industries/technology-and-telecoms/validating-googles-abcd-framework-with-the-power-of-artificial-intelligence). Google, [ABCD playbook](https://thinkwithgoogle.com/_qs/documents/8472/ABCD_Complete_V7b_HR_1.pdf).
- Reagan m.fl. [The emotional arcs of stories are dominated by six basic shapes](https://arxiv.org/abs/1606.07772). 2016.
- Bai m.fl. [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073). 2022.
