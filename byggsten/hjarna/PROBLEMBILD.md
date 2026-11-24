# Hjärna: problembild

> **14 nov, senare:** ägaren lade avsiktsriggen i centrum. Den är utmanad i [UTMANING.md](UTMANING.md), som skärper bilden: två sinnen (upphovets och karaktärens) och en kropp med minne. Uppgifterna är 0041–0045.

Skriven 14 nov 2026 på ägarens begäran. Det här är **inte** en lösning och inget beslut. Det är en karta över vad som behövs, vilka distinktioner som måste göras och var tomrummen finns, så att en lösning kan väljas med öppna ögon.

Ägarens fråga (14 nov):
> "om vi nu har jutsu som lekplats […] vill vi kunna ändra semantiskt vad som händer i scenerna, och ha NÅGON motor förstå vad som är ett bra utfall och varför. Inte lika platt som dagens idé med ledger/jev, utan faktiskt ge mening till rörelser och förstå varför något är något i en större kontext. […] hur infuserar vi mening, i ett större lager som nästan är 1:1 med aktionera på skärmen?"

Ägarens hypotes, som den här bilden prövar men inte avgör:
> "Den ledtrådsmässigt mest rimliga hypotesen av vad som är på samma dimensionalitet (pålitlighet) är att det bör vara sammanfört med NÅGON version (inte exakt samma) av något som LIKNAR vad vi gjorde med content-analysen."

Underlaget är:
- ägarens egna meddelanden 30 okt–14 nov (454 stycken, ur alla 39 sessioner)
- `karta/`, `delegat/kontext/`, `scen/3d/PIPE.md`
- liggaren
- innehållsbanken i `data/format/`
- de tre Jutsu-proven och bryggan i `byggsten/`

Det som är ägarens ord står som citat. Det som är min tolkning är markerat så.

---

## 0. Kort

1. **Det finns redan två hjärnor, men de vet inte om varandra.**
   - *Innehållshjärnan* (`video/format/`, `data/format/`) förstår varför ett klipp är bra: premiss, vändning, vad som bär, hylla, nytta, kundens linje och serie. Den är mätt mot ägaren och mot räckvidd i över 1 000 klipp.
   - *Scenhjärnan* (`scen/3d/`, `forvarld/`, liggaren, Jev) förstår vad som händer: vem gör vad med vad, över vilka rutor, och vad som får ändras.
   - Ingen av dem kan svara på hjärnans fråga: **vad gör den här ändringen med det som gör klippet bra?**
2. **Ett exempel visar att de redan beskriver samma sak oberoende av varandra.** Gelatoklippet (`kennysgelato2.0-7596403003901381910`) har både en liggare (0031) och ett v5-formatkort, ägarbedömningar (E9) och transkript. Båda hittade samma poäng, kontrasten. Bara kortet vet att vändningen sitter i texten "Vs" och musikbytet, att storleksskillnaden är det som bär, och att risken är att kunden inte vågar överdriva. Bara liggaren vet vilken hand, vilka rutor och vilken kontakt. Se avsnitt 3.
3. **Tomrummet är inte fler etiketter.** Det är att mening finns på minst sex tidsskalor (ruta, handling, takt, klipp, serie, strategi). Varje lager talar med sitt grannlager i ett eget språk, men ingen binder ihop lagren.
4. **"Bra utfall" har minst fem domare** (originalet, ägaren, kunden, nyttan och CM:s avsikt), och de är inte överens. Innehållsanalysen har visat det för klipp. För *ändringar* finns nästan inga domslut alls.
5. **Hypotesen håller på metodnivå.** Det innehållsanalysen gjorde pålitligt var metoden: distinktioner i stället för formuleringar, tre facit som hålls isär, låsta prognoser, residual inom konto, och ägarens omdöme som kalibrering. Enheten måste däremot bytas: från färdigt klipp till ändring av klipp. Det är det nya.

---

## 1. Vad som finns i dag (marknivån)

### 1.1 Scenlagret, det som kan återskapas
| del | var | vad den kan |
|---|---|---|
| Ingest till förvärld | `scen/3d/` (kedjan, deklarationen, källan, planen) | Klipp → rum, kameror, kroppar (MHR, 127 leder), föremål, rum per tagning. Bildtrohet 0,93–0,995 bbox-IoU i notan. |
| Bryggan | `byggsten/brygga/` | Sammanställer om till `scenpaket/1`, med grindar G1–G7 och T1-armatur. Samma bpy-skript körs lokalt och i Jutsu. |
| Jutsu | `byggsten/jutsu/` | Hostad Blender med versioner, gratis scenarbete, ändringar på cirka 2 s, shots per tagning som editorn behåller. Saknar mening, men bevarar våra `hagen_*`-egenskaper. |

### 1.2 Handlingslagret, det som beskriver vad som händer
| del | var | vad den kan |
|---|---|---|
| Handlingsspår | `gennedbrytning/m_handling.py` | Segment per tagning: vem, verb, föremål, mål, kontakt och kamera. |
| Relevans | `relevans/`, deklarationens `relevans` | Vad som bär, vad som sätter rummet och vad som stryks. |
| Liggaren | `kontrakt/liggare.schema.json`, `forvarld/liggare/` | Entiteter med affordanser, predikat, händelser (roller, förvillkor och effekt), förlopp, mening (`poang`, `bar`, `tillfalligt`, `ramar`) och frihetsgrader med spridning och regi-mall. Ger Jev-ytan. |
| Jev | `forvarld/gelato/prov_liggare.mjs` m.fl. | Väljer en laglig ändring per mening på under 1 s, eller säger `ingen_passar`. 11 av 11 och 5 av 5 rätt mot liggarens yta (0031–0032). Varierar mellan körningar. |
| Långsam väg | `forvarld/liggare/langsam_vag.py` | En stark modell med liggaren svarar med regi eller ett skälat nej på 4–9 s. |
| Kropp i ändringar | `forvarld/kropp/` | Rörelsemodell (MaskedMimic nu, Kimodo eller annan senare) som tar mål per tid. Rörelsebank v0 med 23 poster, märkta med liggarens händelser. |

### 1.3 Innehållslagret, det som förstår varför ett klipp är bra
| del | var | vad den kan |
|---|---|---|
| Doktrinen | `karta/videoforandring/doktrin.md`, `video/format/doktrin.mjs` | LeTrend, grundvärde, linje, utfall och anpassning. Fem delar ur Miles-pass 1–6. |
| Formatkort v5 | `data/format/harness/v5/`, `e6/`, `e6r/`, `bank2/`, `bank3/` | Per klipp: helhet, handling, redigeringsskämt, kärna, **mall med platser**, **takter** (funktion, vad de bär, vad de är bundna till), grundvärde, språk, förlaga, krav och anpassningsrisk. |
| Bibliotek v6 | `data/format/harness/bibliotek-v6.json` | 1 480 kort. Kärnan har 302 från 90 konton, i hyllorna kärna, mitten, situation, CapCut-referens och ute. |
| Triaden | `data/format/triad.json`, doktrin.md | Sanning (stabilitet), preferens (ägaren) och nytta (räckvidd inom konto) hålls isär. |
| Metaanalysen | `harness.md`, `video/format/meta.mjs` | 1 390 klipp från 95 konton med 95 % konfidensintervall. Säkert positivt: grundvärde, eget tal, premiss, vändning, krok, sketch, höjer taket. Säkert negativt: ingen person, Instagram, klippberoende, trendljud, visning, bundna bilder. Karisma ger noll. |
| Scenplanen | `video/format/h-scener.mjs` | Takt → behåll, fritt, byt produkt, byt lokal, frontfigur, eget tal, förenkla eller risk. Varje val har ett skäl. |
| Anpassning v3 | `video/format/h-anpassa8.mjs`, `harness/pass8/v3/` | Scener (vad, bild, replik, åtgärd), tight, tillåt, undvik, brief. Bygger på ägarens formregler ur pass 8. |
| Teman och räcken | `harness/tema.json`, `tema.mjs` | Vuxna teman och ton mot kundens nivå. |
| Familjer | `familjer*.mjs` | Repertoaren i ägarens formatfamiljer förutsäger passform inom kund (+0,54). Familjerna gör olika jobb: sketch ger räckvidd, tilltal med mat är allsidigt, mat ger sparningar, kampanj ger kommentarer. |
| Serien och faserna | `serieprofil.mjs`, `serie2*.mjs`, `serie9/` | Ägaren läser kundens hela historik i faser. Att hålla fasen är preferens, valet av fas är nytta. Fasskifte från mat till person ger ×2,94. |
| Kundens linje | `h-linje.mjs` | Ur de tio senaste klippen. |
| Bank och utfall | `e4/` (1 327), E11 (10 650), metadata (10 283) | Räckvidd, gillanden och kommentarer, mätta inom konto. |

### 1.4 Människans omdöme, det som kalibrerar
- **Miles-pass 1–8:** ägarens omdöme i inspelade samtal, kodat i `agare.json` per pass.
- **Taket:** modellerna ligger kring rho 0,6 mot ägaren. Pro som CM gav 0,78 i pass 6.
- **Dubbel dissociation:** passform för en kund följer LeTrend-värdet, medan valet till biblioteket följer nyttan.
- **Pass 8 är det enda underlaget som rör ändringar.** Ägaren jämförde v0- och v5-anpassning av samma klipp och gav formregler: "säg inte det självklara", "instruera inte personlighet", "varje scen behöver känsla, struktur och vad den kräver, helst visuellt (3D)".

### 1.5 Processen själv
*Min tolkning, efter ägarens påpekande att Claude kan hållas som en samling dialoger, processer och trådar:* den hjärna som faktiskt har fungerat hittills är ingen modell. Det är en process: ägaren, Fable eller Opus, Miles-passen, doktrinen, minnesfilerna, delegat-kanalen och låsta prognoser. Den gör redan det hjärnan ska göra (förstår varför, väger mot helheten, rättar sig), men långsamt, dyrt och med ägaren som flaskhals. Frågan är vilka delar av processen som kan kompileras ut, och vilka som måste förbli en process.

---

## 2. Meningens lager

Mening finns på flera tidsskalor samtidigt. En och samma rörelse betyder olika saker på varje nivå.

| nivå | enhet | exempel i gelato | vem skriver i dag | var | binds till nivån under? |
|---|---|---|---|---|---|
| **M0 Geometri** | ruta, led, låda, kamera | höger handled 0,4 m framför disken, ruta 90 | ingest (SAM 3D Body, segmentering) | källa, plan, scenpaket | – |
| **M1 Handling** | segment med roller | `ge(A, glass_prov, kund)`, `skopa(A, tråg)` | m_handling, liggaren | källa, liggare | ja, med rutor |
| **M2 Takt** | takt med funktion | uppbyggnad → visning → **vändning** → punchline | formatkort v5 | `data/format/` | **nej**: takterna har varken rutor eller entiteter |
| **M3 Idé** | premiss, mall, kärna | "kontrast små smakprov / enorma egna portioner"; mallen `[litet verktyg]` mot `[stort verktyg]` | formatkortet *och* liggarens `poang` (oberoende av varandra) | båda | **nej**: platserna i mallen pekar inte på liggarens entiteter |
| **M4 Linje och serie** | kundens fas, familj, frontfigur | kennysgelato: vilken fas, vilken familj | serieprofil, familjer, h-linje | `data/format/` | nej |
| **M5 Strategi** | mix, avsikter, tempo, intent-lås | underhållning 60 / info 20 / marknadsföring 20 (ägarens exempel 30 okt) | ingen motor; strategi-objektet i wireframen | `karta/bakom/strategi.md` | nej |

Tvärs över lagren ligger tre axlar till:
- **Värde:** sanning, preferens och nytta (avsnitt 5).
- **Vem:** originalets avsändare, kunden, CM och publiken.
- **Läge:** original eller ändring.

**Tomrummet i en mening:** M0–M1 och M2–M5 lever i olika delar av repot, skrivna av olika modeller, med olika ordförråd. Det finns ingen koppling som säger att takten "punchline" är rutorna 90–146, bärs av handlingen `ta(A, stor_portion)` och av föremålet spaden, och att storleksförhållandet mellan sked och spade är det som bär premissen.

---

## 3. Gelato: samma klipp i båda hjärnorna

Klippet `kennysgelato2.0-7596403003901381910` finns i båda:

| fråga | formatkortet v5 (`data/format/harness/v5/…`) | liggaren 0031 (`kontrakt/ut/kand-kennysgelato_n06-hand/liggare_0031.json`) |
|---|---|---|
| Vad är poängen? | "Kontrasten mellan de små smakproven man ger till kunder och de enorma portionerna personalen tar till sig själva." | "Kontrasten: kunden får ett pyttelitet smakprov (f_servera) medan personalen tar en jätteportion till sig själv (f_egen)." |
| Vad är den överförbara formen? | Mallen "liten [produkt] med [litet verktyg] vs enorm [produkt] med [stort verktyg]", med platserna produkt, litet verktyg och stort verktyg | Saknas. Liggaren är bunden till instansen. |
| Var vänder det? | Takt 3: texten "Vs" och musikbytet från klassiskt till hiphop, bunden till redigering | Saknas. Liggaren har varken text eller ljud. |
| Vad bär, och vad är fritt? | Takt 1 och 4 bär kärnan, takt 2 och 3 är stöd | `bar` = mottagare, sak, stor portion, ordningen servera före egen. `tillfalligt` = kroppsdel, tempo, kamerans rörelse. |
| Vad får ändras? | Implicit genom mallen: byt produkt och verktyg. Klumpigt utförande går bra. | Frihetsgrader, t.ex. `fg_hand` (vilken hand, `bar_meningen: false`) |
| Vad är risken? | "Att kunden inte vågar överdriva punchlinen tillräckligt mycket, vilket gör att kontrasten […] blir för liten." | Saknas. Liggaren har ingen storleksgrad. |
| Vem kan göra det? | Krav: minst 1 person, skådespel 3, produktion 1, disk eller kassa, något som kan portioneras | Saknas. |
| Hur bra är det? | Hylla kärna, premiss stark, höjer taket, utan efterarbete. Ägaren har bedömt det (E9). | Saknas. |
| Tal? | Transkript tomt: inget tal, texten och musiken bär | Saknas. |
| Exakt var i tid, med vilken hand, vilken kontakt? | Saknas. | Händelser med rutor, roller och kontakt. Frihetsgrader med spridning och regi-mall. |

Vad exemplet visar, utan att lösa något:
- **De två hjärnorna överlappar på M3 och kompletterar varandra överallt annars.**
- **Den viktigaste frihetsgraden för meningen finns i ingen av dem.** Storleksförhållandet (liten sked mot stor spade, "överdriva punchlinen") bär premissen och är en kontinuerlig grad. Liggaren har vilken hand. Kortet har att det är en risk. Ingen av dem har förhållandet som en ratt.
- **Vändningen bor i redigering och ljud**, som förvärlden inte representerar alls.
- En CM-mening som "gör kontrasten större", "byt till pommes och en skyffel" eller "gör det med kunden i bild" kan bara besvaras om båda hjärnorna är ihopbundna.

---

## 4. Distinktionerna som behövs

Varje distinktion är formulerad öppet: vad som behöver hållas isär, vad vi vet, och vad som är oklart.

### D1. Beskriva, betyda och värdera
- **Beskriva:** M0–M1, vad som händer.
- **Betyda:** M2–M3, varför det händer i klippet och vad det gör för tittaren.
- **Värdera:** om det är bra, för vem, enligt vem.

Liggaren beskriver och betyder lokalt. Innehållshjärnan betyder och värderar globalt. Ingen gör alla tre för en *ändring*. *Oklart:* måste en och samma struktur bära alla tre, eller ska de vara separata lager med kopplingar?

### D2. Mening på flera tidsskalor
Ägarens formulering (13 nov): "person gör (handling) över x många frames, med (kamerarörelse). Flera av dessa scener skapar mening, eller en skapar mening, eller en kombination skapar mening." Och (7 nov): "binda mening×rörelse i ett objekt för att abstrahera det som ett objekt i en större kontext (scen) i ett större objekt (klipp/content)."
- Samma rörelse (att räcka fram skeden) är handlingen *ge* (M1), takten *visning eller uppbyggnad* (M2) och halva *kontrasten* (M3).
- *Oklart:* går bindningen alltid uppåt (handling → takt → idé), eller kan en idé bäras av något som inte är en handling (text, musik, ett klipp)?

### D3. Två ordförråd för vad som bär
- Liggaren: `bar`, `tillfalligt` och `ramar`.
- Formatkortet: `kärna`, `stöd` och `fritt`, `bunden` (person, produkt, lokal, redigering, trend, ingen), `bars_av` (idé, person, produkt…).
- *Min tolkning:* de beskriver samma sak från två håll. "Tillfälligt" motsvarar ungefär "fritt", men "ramar" har ingen motsvarighet i kortet, och "bunden" har ingen i liggaren. *Oklart:* finns det ett gemensamt ordförråd, eller är skillnaden meningsfull (instans mot typ)?

### D4. Instansen och typen
- Förvärlden ändrar en *instans*: just den här expediten, just den här disken.
- Banken känner *typen*: mallen med platser, och 1 480 exempel på hur andra gjort samma mall.
- Ägaren (2 nov): "Per klipp så tänker jag att det måste skyddas någon typ av grundplacering baserat på norm, vad som är bra och dåligt, som robusta och återkommande grundpunkter."
- *Oklart:* är typen (mallen) förvärldens egentliga tillstånd, och instansen bara en fyllning av platserna? Eller är typen en referens som hjärnan slår upp i?

### D5. Att ändra inom meningen eller att byta mening
- Vissa CM-meningar bevarar poängen: "byt hand", "längre", "stabilisera kameran".
- Andra byter den medvetet. Ägaren (2 nov): "skapa en ny version där sista delen klipps bort och slutmeningen är 'shu vad händer'", "gör punchlinen lite tidigare".
- hagen-ui har ett intent-lås (`scene-rails-intent-locked`): en ändring som gör underhållning till marknadsföring avvisas tills CM bryter formatet med en orsak.
- *Oklart:* hur vet hjärnan vilken sorts ändring den har framför sig? Och när ska den varna, föreslå eller lyda?

### D6. Rörelse som handling, uttryck och tajming
- **Handling:** ge, skopa, äta (liggaren).
- **Uttryck eller iscensättning:** fart, energi, hur personen går in i scenen, hur stor del av bilden motivet tar. Ägaren 1 nov, i minnet: rörlighet är iscensättning, inte skak.
- **Tajming för poängen:** pausen före punchlinen, att "göra punchlinen tidigare".
- Rörelsemodellen (MaskedMimic, Kimodo) kan bara den första sorten, och bara som mål.

Ägaren (13 nov): "Det behöver egentligen en integrerad IQ som är bunden till kroppen och vad som är 'standard' […] att kroppen måste roteras och ett nytt sätt att skopa nu kommer upp."

*Oklart:* är uttryck och tajming egenskaper hos rörelsen, hos takten eller hos klippet?

### D7. Bildens mening och redigeringens mening
- Formatkortets takter är ofta `bunden: redigering`: krok, vändning, slutbild.
- Kameran och klippningen bär mening som inte finns i scenen: svep från taket som krok, snabba klipp, musikbyte, textskyltar.
- Ägaren 13 nov: redigeringen ska "kännas igen och bokföras, inte misstas för rörelse".
- Bryggan bygger en kamera per tagning, men ingen text, inget ljud och inga övergångar.
- *Oklart:* är redigering ett eget lager i förvärlden (tidslinjen), eller en egenskap hos takterna?

### D8. Ord: tal, repliker och text på skärmen
- Eget tal är bland de säkra positiva faktorerna.
- Premissen bärs ofta av repliken (tilltal, dialogsketch) eller av texten ("Smakproverna vi ger kunder").
- Förvärlden har inget lager för det: inga läppar, inga ord bundna till tid och talare. Bryggan har repliker bara som markörer.
- Exemplen i inlärningen ("när han säger 'badoo'", "gör meningen i tredje scenen så här") pekar på ord i tid.
- *Oklart:* är ordlagret en del av hjärnan eller av scenen?

### D9. Det synliga och det berättade
- Notan bygger på ett **avslöjande**. Rummet som berättas i S1–S6 är inte rummet i S7. Meningen ("men jag känner inte ens dig?") ligger i montaget, inte i någon scen.
- Blocken i animatiken uppstod just för att kedjan inte bar den distinktionen (`byggsten/jutsu/BUGG-BLOCK.md`).
- Gelatos vändning ligger i ett klipp och ett musikbyte.
- *Oklart:* hur representeras mening som bara finns *mellan* tagningar, och vem bevakar att en ändring inte förstör den?

### D10. Det som syns och det som antas
- Grundregeln: originalet är sanning där något syns, och det genererade är hypotes (`antagen`).
- Mening kan bygga på det som inte syns: kundens hand utanför bild i gelato, personen bakom disken, en publik.
- *Oklart:* kan hjärnan resonera om mening i det antagna utan att behandla det som fakta?

### D11. Rimligt och genomförbart
- Förvärlden bedömer om något är *rimligt*: fysik, kontakt, grindar.
- Innehållshjärnan bedömer om något är *genomförbart av kunden*: "om man instruerar någon mindre skicklig till att spela ut en roll, kommer idén fortfarande bära?" (ägaren 3 nov). Det gäller också krav på personer, skådespel och lokal, och att idén "tål att göras klumpigt".
- En ändring kan vara rimlig i 3D men omöjlig för kundens personal, till exempel en skådespelarprestation.
- *Oklart:* var i kedjan bedöms genomförbarheten för en ändring?

### D12. Förklaring
- Harnessen ger alltid skäl, och scenplanen har ett `skal` per takt.
- Ägaren 31 okt: "som en riktig harness kunna förklara, med en mix av förändrande variabler […] för att uppnå målet."
- Jev ger ett val utan skäl.
- *Oklart:* vem ska förklaringen vara för (CM, ägaren, kunden, nästa modell), och på vilken nivå?

### D13. Säker och osäker kunskap
Kunskapen har mycket olika säkerhet:
- Metaanalysens intervall och förregistrerade replikeringar.
- Geminis läsningar, där 29 av 43 lager var stabila (E1).
- Ägarens egen spridning: modellerna når taket kring 0,6.
- Jevs val, som varierar mellan körningar.

*Oklart:* bär hjärnan sin osäkerhet vidare, så att CM ser vad som är säkert och vad som är gissat, eller döljer den den?

### D14. Hastighet
Var räknas vad?
| | tid | exempel i dag |
|---|---|---|
| Live | under 1 s | Jev |
| Långsam väg | sekunder | stark modell med liggaren |
| Ingest | minuter | liggare, formatkort, generativ nedbrytning |
| Offline | timmar till dagar | bankanalys, kalibrering, träning |

*Oklart:* vilken del av meningen måste finnas *före* CM:s mening (förberäknad vid ingest), och vilken kan räknas fram efter?

### D15. Vem skriver mening, och vem rättar den
| källa | vad den ger | hur ofta |
|---|---|---|
| Stark modell vid ingest | liggare, formatkort | per klipp |
| Ägaren | doktrin, Miles-pass | sällan, dyrt, högst kvalitet |
| CM | val, ändringar, avvisningar | ofta, i flödet |
| Kunden | 1-2-3, flytta bak, nej | per plan |
| Publiken | räckvidd, kommentarer, sparningar | efter publicering, långsamt |

Ägaren 2 nov: "Lärandet går från billiga och svaga signaler till dyra och starka" (inlärningen, mening 7). *Oklart:* vilken av dem lär hjärnan, och hur hindras den från att lära sig fel?

### D16. Två banker
- **Innehållsbanken** har 1 480 kort och över 10 000 klipp med utfall, märkta med mening (premiss, takter, hylla) men utan rörelse.
- **Rörelsebanken** har 23 poster, märkta med liggarens händelser men utan innehållsmening.

Ägaren 13 nov: "det finns, och kommer finnas 1000+ analyserade klipp som håller olika versioner av rörelser, kameravinklar, scener och annat, det finns någon typ av dataset, bara att det inte finns en tydlig väg hur och varför det skulle lösa detta problem."

*Oklart:* är det samma bank sedd från två håll, och kan en märkning gå över till den andra?

---

## 5. Vad "bra utfall" betyder för en ändring

Innehållsanalysen har visat att "bra" inte är ett enda tal. För en *ändring* tillkommer nya domare.

| domare | frågan | finns facit? | belägg |
|---|---|---|---|
| **Originalet** (trohet) | Är ändringen fortfarande samma klipp där den inte skulle ändras? | Ja, mätbart: bildtrohet och grindar | G7 0,93–0,995; bryggans grindar |
| **Meningen** (poängen) | Bär poängen fortfarande, eller är den bytt med avsikt? | Nej | Liggarens `bar`, kortets kärna och risk. Ingen domare finns. |
| **Ägaren** (preferens, LeTrend-värde) | Är det LeTrend? | För klipp ja (Miles 1–8). För ändringar bara pass 8. | Pass 8 del 1 och formreglerna |
| **Nyttan** (räckvidd inom konto) | Går ändringen troligen bättre? | För klippdrag ja (metaanalysen). För ändringar indirekt: ändringen flyttar ett klipps drag. | Eget tal +, trendljud −, person + |
| **Kunden** (passform, linje, fas) | Passar ändringen kundens linje och förmåga? | Ja för klipp (pass 6: kunden står för 54 % av variansen) | Familjer och faser |
| **CM** (avsikt) | Gjorde den det CM ville? | Nej. CM:s val har inte samlats in. | – |
| **Genomförbarheten** | Kan kundens personal göra det? | Delvis: kravfältet. Modellen var inte bättre än att gissa "ja". | `harness.md` |

Det som komplicerar:
- **Preferens och nytta går isär** (dubbel dissociation). En hjärna som optimerar en av dem kan skada den andra.
- **Ägarens omdöme har ett tak för modeller** kring 0,6. Det är inte säkert att en hjärna kan bli bättre än ägarens egen spridning.
- **Belöningsfusk:** en domare som är en modell kan utnyttjas av den som optimerar (inlärningen 2.9).
- **"Bra" är relativt** (ägaren 2 nov: "ett snöre har ingen definierad längd […] det är alltid relativt. Ok, då är frågan relativt till vad."). Relativt till originalet, kundens linje, kohorten, banken eller CM:s förra version?

---

## 6. Tomrummen (det som saknas)

Ordnade från grund till yta. Inget av dem är löst i dag.

| # | tomrum | var det syns |
|---|---|---|
| T1 | **Ingen bindning mellan takt och handling.** Formatkortets takter har inga rutor och inga entiteter. Liggarens händelser har ingen funktion (krok, vändning, punchline). | Gelato, avsnitt 3 |
| T2 | **Ingen bindning mellan mallens platser och scenens entiteter.** `[stort verktyg]` pekar inte på spaden i förvärlden. Därför kan "byt produkt" inte gå från biblioteket till scenen. | Mallen i kortet mot liggarens entiteter |
| T3 | **Ingen modell för vad en ändring gör med poängen.** Kontrafaktiskt: om hon ger med andra handen håller kontrasten. Om spaden blir en sked försvinner den. Ingen hjärna kan avgöra det i dag annat än genom att fråga en stark modell från början. | Jevs `ingen_passar`, långsam väg |
| T4 | **Ingen värdering av en ändring mot banken.** Flyttar ändringen klippet mellan hyllor? Tar den bort eget tal, lägger den till visning utan person? Metaanalysen vet vad som lyfter klipp men har aldrig sett en ändring. | Doktrin, metaanalys |
| T5 | **Inga graderade, meningsbärande rattar.** Storleksförhållandet i gelato, kontrastens styrka, punchlinens placering och tempot före vändningen. Liggarens frihetsgrader är mest diskreta (vilken hand), och de som bär meningen är märkta `bar_meningen: true` men sällan graderbara. | Gelato, risken "vågar inte överdriva" |
| T6 | **Inget lager för uttryck och iscensättning bundet till rörelse.** Fart, energi och närvaro i bild finns som vertikaler i `#v`-reglaget, men inte bundna till kroppen. | Kalibreringen 31 okt, rörlighet = iscensättning |
| T7 | **Ord, text och ljud saknas i förvärlden.** Repliker med tid och talare, text på skärmen och musikbyten. Ofta är det just de som bär premissen eller vändningen. | Gelatos "Vs", eget tal |
| T8 | **Montage och berättarnivå är inte förstaklassiga.** Berättat och avslöjat rum, perspektivbyten, tagningar som bara betyder tillsammans. | Notan, BUGG-BLOCK.md |
| T9 | **Rörelsemodellen vet inte varför.** Den tar mål per tid. Målen kommer ur liggaren, inte ur meningen, så en ändring som behåller handlingen men förstör tajmingen för poängen ser korrekt ut. | 0039 och 0040 |
| T10 | **Facit för ändringar saknas.** All kalibrering hittills gäller klipp eller anpassningsbriefer (pass 8). Ingen har bedömt en förvärldsändring mot en annan. | – |
| T11 | **Ingen lärloop från CM.** CM:s val, ångrade ändringar och avvisningar samlas inte in. Kundens 1-2-3 finns bara simulerat. | `karta/bakom/kundsvar.md` |
| T12 | **Serien och strategin når inte scenen.** En ändring för kund X görs utan vetskap om X:s fas, familj eller mix. Fasvalet (bort från mat) var den största nyttan i analysen. | Serie 2, 2g |
| T13 | **Hur mening ska representeras för en maskin är oavgjort:** predikat (liggaren), fritext (kortens `helhet`), fält med slutna värden (kortens språk och grundvärde), inbäddningar, exempel (banken) eller vikter (en tränad modell). Var och en har prövats på ett ställe, ingen över lagren. | – |
| T14 | **Granulariteten skiljer sig.** Liggaren skrivs per tagning, kortet per klipp, serien per konto och strategin per kund. Ingen gemensam tidsaxel. | – |
| T15 | **Jutsus egen agent ser ingen mening.** Våra `hagen_*`-egenskaper ligger kvar men är döda för den. Deras "scenpass" finns bara i agentens huvud. | `byggsten/jutsu/AUDIT-AVSTAND.md` |
| T16 | **Kostnadsvägen.** Innehållsanalysens slinga stannade på krediter flera gånger (Lovable-kontona 2–5, Vertex). En hjärna som kräver stark modell per ändring blir dyr. En som är förberäknad blir stel. | `harness.md`, minnet |

---

## 7. Ägarens hypotes, prövad öppet

> "det bör vara sammanfört med NÅGON version (inte exakt samma) av något som LIKNAR vad vi gjorde med content-analysen där jag försökte hitta samband i klipp för att skapa en harness."

### 7.1 Det som talar för hypotesen
- **Enda pålitliga metoden vi har.** Innehållsanalysen är den enda del av projektet där mening har mätts och replikerats:
  - förregistrerade prognoser, låsta före ägarens svar
  - tre facit som hålls isär
  - residual inom konto
  - konfidensintervall och replikering på nya konton
  - ägarens omdöme som kalibrering i Miles-pass

  Liggaren och Jev har bara prövats på 2–3 klipp, mot orkestratorns egen bedömning.
- **Distinktionerna, inte formuleringen.** E1 visade att promptens formulering förklarar cirka 0 % av variansen. Det som spelar roll är vilka distinktioner som finns. Det säger något om hjärnan: den blir bättre av rätt distinktioner, inte av en smartare modell.
- **Det finns redan bindningsytor.** Formatkortets takter (funktion, vad som bär, vad de är bundna till) och mall med platser är nästan exakt den nivå som saknas mellan handling och idé (avsnitt 2). Scenplanen (takt → åtgärd med skäl) är redan en primitiv hjärna för ändringar, bara utan scen under sig.
- **Samma klipp finns i båda** (gelato). Bindningen kan prövas på riktiga data utan ny insamling.
- **Banken är det dataset ägaren efterfrågar** (13 nov). Den har tusen versioner av samma mallar hos olika konton. *Min tolkning:* det är ett empiriskt variationsrum, alltså vad som kan ändras i en mall utan att den slutar fungera, och det är vad liggarens frihetsgrader i dag gissar fram per klipp.

### 7.2 Det som talar emot, eller kräver att hypotesen ändras
- **Fel enhet.** Innehållsanalysen bedömer *färdiga* klipp. Hjärnan måste bedöma *ändringar* och kontrafaktiska versioner, och det har ingen sett. Att klipp med eget tal går bättre betyder inte att en ändring som lägger till eget tal gör det.
- **Ingen tid och ingen rörelse.** Korten ser videon, men lagrar inget i tid och inget i 3D. Rutnätsvyn (E9) visade att det visuella läses bättre när modellen får se mer, men det blev aldrig bundet.
- **Taket kring 0,6 mot ägaren.** Om hjärnan ärver innehållsanalysens domare ärver den också dess tak.
- **Sanning för ändringar kan inte mätas mot räckvidd.** Förvärldsändringar publiceras inte direkt. Kunden spelar in efter manuset (ägaren 2 nov), så utfallet kommer sent och blandat med utförandet.
- **Ägaren har sagt nej till Gemini som källa för att *hitta* data**, men använder den som ingestmotor och läsare. Hjärnans ingest blir troligen beroende av en modell som ägaren litar på för läsning, men inte för urval.

### 7.3 Hypotesrummet (varianter, inget val)
Varianter av "en version av innehållsanalysen", ordnade efter hur nära de ligger det som finns. Var och en kan vara rätt, fel eller en del av svaret.

| variant | kort | vad den kräver | vad som skulle fälla den |
|---|---|---|---|
| **H1 Kortet som tillstånd** | Formatkortets takter och mall blir förvärldens semantiska tillstånd. Liggaren binds under dem (takt → händelser, plats → entitet). | Bindningen T1/T2 vid ingest; takter med rutor | Takterna går inte att binda stabilt till rutor (Gemini varierar) |
| **H2 Banken som minne** | För en ändring hämtar hjärnan klipp med samma mall eller premiss och ser hur de skiljer sig. Variationen i banken blir det lagliga ändringsrummet. | Sökbarhet per mall; jämförbara kort; mer än en instans per mall | Mallarna är för unika (1 480 kort, men hur många per mall?) |
| **H3 Hjärnan som domare** | Innehållsanalysens lager används för att bedöma *ändrade* versioner: grundvärde, nytta, passform, genomförbarhet och poängens bärighet. | Att läsa en ändrad förvärld som ett klipp (render → kort) | Kortet på en render skiljer sig från kortet på originalet av fel skäl (dockor, ingen text) |
| **H4 Hjärnan som översättare** | CM:s språk → mallens och takternas språk → liggarens frihetsgrader → regi. Innehållsanalysen ger mellanspråket. | Ett gemensamt ordförråd (D3) | CM:s meningar landar oftast utanför takt och mall (som i 0014: begrepp som saknas) |
| **H5 Par och preferens** | Som Bradley–Terry på scener (31 okt) och Miles-par (pass 7): ägaren eller CM väljer mellan två ändrade versioner, och hjärnan lär sig ur paren. | Ändringar att jämföra; bedömningsflöde | Ägarens tid; taket kring 0,6 |
| **H6 Processen kompileras** | Hjärnan är processen (avsnitt 1.5), och det som går att förberäkna flyttas till ingest: doktrin, liggare, kort, grindar. Resten förblir en långsam väg med stark modell och minne. | Att veta vilka frågor som är vanliga | Den långsamma vägen blir standard och därmed för dyr eller långsam |

*Min tolkning:* varianterna utesluter inte varandra. H1 och H2 handlar om vad hjärnan *vet*, H3 och H5 om hur den *vet att den har rätt*, H4 om hur den *förstår CM*, och H6 om *var den bor*.

---

## 8. Hur problemet påverkar ingesten

Ingesten är där mening måste skapas om hjärnan ska kunna använda den live (D14). Frågor som ingesten i dag inte ställer:

1. **Ordningen:** ska innehållskortet skrivas före scenen, efter eller samtidigt? I dag finns det för vissa klipp men läses inte av kedjan. Kedjans deklaration (Gemini-konsensus) och kortet (Gemini Flash med doktrin) är två läsningar av samma video som aldrig jämförs.
2. **Takter i tid:** kortet behöver rutor per takt, eller kedjan behöver funktion per handling (T1).
3. **Mallens platser som entiteter:** varje plats i mallen behöver peka på en entitet i källan (T2). Liggarens entiteter behöver märkas med vilken plats de fyller.
4. **Graderna som bär:** ingesten behöver hitta de kontinuerliga storheter som bär poängen (storlek, avstånd, tid till punchline) och göra dem till frihetsgrader med domän (T5).
5. **Ord, text och ljud:** transkript med talare och tid, text på skärmen med tid, musikbyten (T7). `data/format/tal/` finns för en del klipp.
6. **Montaget:** vilka tagningar betyder bara tillsammans, och var finns avslöjanden (T8)? Rum per tagning (berättat och avslöjat) är första exemplet.
7. **Krav och genomförbarhet:** kortets `krav` behöver följa med till förvärlden, så att en ändring kan prövas mot kundens förmåga (D11).
8. **Grannar i banken:** vid ingest kan klippet få sina närmaste mallar och familjer (H2), och sin hylla.
9. **Osäkerhet:** varje meningsfält behöver säga hur det är läst (mätt, läst, antaget) och hur stabilt det är (D13). Liggaren har `kalla: matt` på händelser, och kortet har inget.
10. **Kostnad:** varje nytt fält vid ingest kostar ett modellanrop. Innehållsanalysen visade att en kort doktrin med Flash räcker för biblioteket (E8), och att de billiga Lite-lagren sållar med rho 0,64–0,84.

Det berör också kedjan som den är:
- **Deklarationen** (`ingest/scenbrief.py`) läser redan relevans och roller. Den är närmast innehållskortet.
- **Liggarsteget** (`kedja.py`, `forvarld/liggare/`) skriver mening utan att se kortet.
- **Bryggan** (`byggsten/brygga/`) har platsen `mening` i paketet men fyller den bara med repliker, roller och rumsrelationer.

---

## 9. Var hjärnan kan bo (öppet)

| plats | hastighet | styrka | svaghet | belägg |
|---|---|---|---|---|
| I ingest (förberäknad mening) | live när den väl finns | billig att använda | stel; vet bara det någon förutsåg | liggaren, Jev-ytan |
| I en snabb väljare (Jev) | under 1 s | billig | väljer bara bland det givna; varierar mellan körningar | 0031–0032 |
| I en stark modell live | sekunder | förstår det oväntade | dyr och långsam; ägaren är tveksam ("Jag känner mig tveksam att ha en fable api nyckel som agerar orkestrator i live-appen", 13 nov) | långsam väg |
| I en process (Claude-trådar, minne, delegat) | minuter till dagar | rikast förståelse; kan rättas av ägaren | inte i appen; dyr | hur hagen-wf har arbetat |
| I data (banken som exempel) | snabb uppslagning | empirisk | täcker bara det som finns i banken | H2 |
| I vikter (tränad modell) | snabb | generaliserar | kräver facit vi inte har (T10) | rörelsemodellen, Bradley–Terry |

Ägaren 13 nov: "ju mer jag sitter känns det som att vi inte planerar för en verklighet där det ska finnas självgående, inherent meningsbärande och kontextualitetsbundet (animation:mening) förståelse som är mendable."

---

## 10. Öppna frågor till ägaren

Formulerade öppet. Ingen kräver ja eller nej.

1. Är **mallen** (typen) det CM egentligen ändrar, med instansen som en fyllning? Eller ändrar CM instansen, med mallen som ett räcke?
2. När en ändring **byter poäng** ("gör slutet 'shu vad händer'"), vad ska hjärnan göra med den gamla poängen: bevaka den, glömma den eller fråga?
3. Vilken domare ska väga tyngst för en ändring när de går isär: ägarens smak, nyttan, kundens linje eller CM:s avsikt?
4. Vad räknas som **facit för en ändring**, som vi kan börja samla redan nu? Pass 8 var ett steg dit.
5. Hur stor del av hjärnan får vara en **långsam väg** med stark modell, och hur stor del måste vara blixtsnabb?
6. Är **ord, text och ljud** en del av förvärlden, eller ett lager ovanpå den?
7. Ska **rörelsebanken och innehållsbanken** vara samma bank? Ska de tusen analyserade klippen också läsas för rörelse?
8. Vad i **processen** (avsnitt 1.5) ska finnas kvar som process även när produkten finns, och vad måste kompileras ut?

---

## 11. Underlag

| vad | var |
|---|---|
| Ägarens meddelanden, 30 okt–14 nov | Claude-loggarna; urval i den här bilden |
| Kartan, vyer och objekt | `karta/README.md`, `karta/bakom/` |
| Inlärningen (referenspunkter, norm, profil, ram) | `karta/videoforandring/inlarning.md` |
| Harnessen | `karta/videoforandring/harness.md`, `harness-v6-kort.md`, `doktrin.md`, `forslag-v6.md` |
| Formatkort, bibliotek och bank | `data/format/harness/`, `data/format/e*/`, `data/format/bank2/`, `bank3/` |
| Gelatos kort och liggare | `data/format/harness/v5/kennysgelato2.0-7596403003901381910.json`, `scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/liggare_0031.json` |
| Liggaren och dess förebilder | `kontrakt/liggare.schema.json`, `forvarld/liggare/LANA.md`, `PIPE.md` |
| Målbild och vägen | `delegat/kontext/malbild.md`, `vagen.md` |
| Jutsu, bryggan och felen | `byggsten/jutsu/AUDIT-AVSTAND.md`, `BUGG-BLOCK.md`, `byggsten/brygga/README.md` |
