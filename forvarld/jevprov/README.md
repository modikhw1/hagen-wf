# Jev-prov på Notan

Provet är klart: ett familjeval följt av ett delval (b) fungerade bäst i detta lilla material. Det gav 95 % rätt familj, 80 % exakt rätt delar och 335 ms median för hela meningen. Alla 180 routningar låg under en sekund. Det betyder snabb routning, inte att en redigerad bild hann visas; ingen spelare eller rendering ingick.

## Omfattning och filer

Endast filer under forvarld/jevprov/ skapades. meningar.json redigerades inte. Ingen Blender, ingest, installation, nedladdning eller testsvit startades. Alla HTTP-anrop gick till POST https://api.typesafe.ai/v1/systemone. Nyckeln lästes med samma nyckel()-funktion som app/kalibrering/jev.mjs; varken nyckel eller miljöfil sparades i experimentet.

- prov.mjs bygger tillstånd, gör utvecklingsprovet, fryser och kör testomgångarna.
- konkret.mjs gör fem konkreta val efter routningen från b, omgång 1.
- kompilera_latt.py skyddar skrivningar, blockerar nät och externa processer samt sätter 384 MiB privat minne, en numerisk tråd och 45 s gräns. --endast-edits stoppar före bild-/kroppsdiagnostiken.
- forbered_diagnostik.mjs skapar den separat märkta källkopian och regikopiorna.
- sammanstall.mjs och skriv_rapport.mjs räknar om rapporten lokalt, utan modellfrågor.
- ut/anrop/ innehåller varje exakt request (model/state/questions), HTTP-status, råa typade answers inklusive confidence/probabilities, usage och väggtid. ut/rutter/ innehåller de avkodade resultaten per mening. ut/anropslogg.jsonl räknar faktiska försök. Fryst text och skripthash ligger i ut/fryst.json.
- resultat.json innehåller mätvärden, fel per omgång och kompilatorutfall. ut/kontroll.json innehåller integritetskontroller.

## Utveckling, storlek och frysning

Endast de tio utv-meningarna användes för val av tillstånd och frågespråk. Samma frågemallar provades i fyra kombinationer: 12 respektive 28 rader och svenska respektive engelska frågor. Själva tillståndet och CM-meningen förblev svenska även när frågeinstruktioner och alternativbeskrivningar var engelska. Ingen ytterligare utvecklingsiteration gjordes. De första två anropen mätte tillstånden med exakt samma korta fråga, ”Är detta ett klipp?”.

| Tillstånd | Rader | Tecken | API input_tokens |
|---|---:|---:|---:|
| minimal | 12 | 927 | 664 |
| full | 28 | 2948 | 1564 |

Detta är API:ets tokenräkning för tillståndet med mätfråga och API-omslag, inte en separat tokenizerberäkning av enbart texten. Skillnaden är 900 tokens. API:ets input_tokens för varje verkligt anrop används i kostnadsberäkningen; frågor och alternativ är alltså medräknade.

| Variant | Familjeträff | Exakta delar | Tokens/mening | Median ms |
|---|---:|---:|---:|---:|
| full-sv | 29/30 | 12/30 | 5520,6 | 353 |
| full-en | 28/30 | 13/30 | 5115,8 | 349 |
| minimal-en | 28/30 | 11/30 | 3311,3 | 336 |
| minimal-sv | 28/30 | 11/30 | 3796,1 | 342 |

Urvalsregeln i skriptet före första anropet var flest familjeträffar, sedan exakta delar, sedan lägst medeltokens. Den valde full-sv och skapade ut/fryst.json innan någon testfråga ställdes. Samma prov.mjs-hash och samma text användes i alla tre testomgångar. Inga routingfrågor eller gränser ändrades efter testet. Utvecklingens träffmått var tillåtande för strategin som kan svara med flera familjer; därför redovisas även sträng familjeträff nedan. Det ändrar inte det redan frysta valet.

Svenska slog engelska med en av 30 familjeträffar på fullt tillstånd (29 mot 28), medan engelska fick en mer exakt delmängd. På minimalt tillstånd var båda 28/30 och 11/30. Materialet visar ingen säker generell språkfördel; svenska frystes enligt den förutbestämda regeln. Svarsmodellen var jev-1.14.0 bakom begärt jev-latest.

Källans verkliga semantik skiljer sig från bakgrundstexten i meningar.json: A har rollen woman, B man och C waiter. Props är bara bord_1, bord_A, bord_3, bord_4 och bord_B. Ingen burk eller mat har id där. Tillståndet följer kalla.json; inga saknade föremål eller handlingar uppfanns. Alla sju repliker, talare, scener, platser, ankare och undertexter finns med; det fylligare tillståndet innehåller också tider, text-id och fontstorlekar. Okänd funktion i s5 och okänd extra person i s4 förblir uttryckligen okända.

## Tre strategier

**a:** elva självständiga ja/nej-frågor i ett anrop, en per del. För de ja-markerade delarna görs ett andra anrop med ett familjeval per del bland delens familjer plus oklar. Inget ja ger oklar. Alla valda delar och alla unika familjer bevaras. Tvåvägs-choice användes i stället för Boolean, som uppdraget tillät.

**b:** ett Choice bland de 14 familjerna inklusive oklar. Vid konkret familj följer ett Choice för delar. Alternativen är tom mängd, elva ensamma delar och alla 55 par: totalt 67, under gränsen 255. Strategin kan därför inte svara med fler än två delar. Vid oklar blir delmängden tom utan andra anrop.

**c:** fjorton Score-frågor i samma anrop, en per familj, på samma fem förankringar 0–4. Högst returnerad score vinner; originalordningen bryter lika poäng. Därefter används samma delval som b, om vinnaren inte är oklar. API:ets score var kontinuerligt, inte bara ett heltalssteg. Marginal = högsta minus näst högsta score. Inget tröskelvärde anpassades på testet.

Alla oberoende frågor i samma steg batchades i questions-objektet. Nästa steg beror på föregående svar och behöver ett nytt HTTP-anrop. Försöken kördes sekventiellt, utan samtidig nättrafik, för läsbara latenser. Ingen lokal svarscache användes. Modell-/servertjänstens eventuella interna cache kan inte bedömas här.

## Resultat: 20 testmeningar × tre omgångar

| Strategi | Familj, sträng (minst en träff) | Delar exakt / minst en | Oklar TP; FP | Median / p90 ms | Anrop/mening | Inputtokens/mening | USD/1000 | Stabil familj / delar / båda |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| a | 0,0 % (90,0 % träff) | 3,3 % / 93,3 % | 3/6; 53/54 | 350 / 402 | 1,98 | 5753,5 | $0,23014 | 75,0 % / 50,0 % / 40,0 % |
| b | 95,0 % (95,0 % träff) | 80,0 % / 95,0 % | 3/6; 3/54 | 335 / 378 | 1,90 | 4536,0 | $0,18144 | 100,0 % / 100,0 % / 100,0 % |
| c | 80,0 % (80,0 % träff) | 65,0 % / 75,0 % | 6/6; 12/54 | 341 / 390 | 1,70 | 5858,3 | $0,23433 | 100,0 % / 90,0 % / 90,0 % |

”Familj, sträng” kräver att alla returnerade familjer är godtagbara. En massa extra familjer ger alltså inte ett rätt svar. Träffkolumnen visar separat om minst en rätt familj fanns med: för a var det 54/60 men inga helt rena familjesvar. Delar exakt kräver exakt mängd, med facitets uttryckliga alternativ. För minst en del räknas ett tomt facit rätt endast med tomt svar; överlapp på de 57 icke-tomma fallen är 98,2 %, 94,7 % respektive 73,7 %.

TP gäller de sex observationerna av t17/t20; FP gäller de 54 andra. t20 tillåter scen.ordning som rätt familj, men det registreras ändå som missad oklar. t3/t12/t14 godtar A eller B, t15 godtar även kamera.utsnitt och props. Inga andra alternativ lades till efteråt. Facitets parentes om kamera.utsnitt på props i t15 tolkades strängt som props-mängden; kamera+props är därför inte exakt rätt.

Latensen summerar hela meningen från första anropets start till sista svaret, inklusive lokal journalföring. Kvantiler använder närmaste rang. Medelvärden för anrop och tokens gäller 60 meningstillfällen per strategi. Priset 0,04 USD per miljon inputtokens kommer från offentliga listningar enligt uppdraget, inte API:et; det kontrollerades inte via annan nättrafik. Kostnad/1000 = medeltokens × 0,00004 USD. Ingen output- eller annan avgift antas.

Stabilitet betyder identiska familjemängder/delmängder i alla tre svar för en unik mening. b var identisk på 20/20 meningar; c på 18/20; a på 8/20. Detta är en observation på 20 meningar, inte ett bevis på determinism.

| Strategi | Omgång | Sträng familj | Exakta delar | Median / p90 ms |
|---|---:|---:|---:|---:|
| a | 1 | 0,0 % | 0,0 % | 353 / 400 |
| a | 2 | 0,0 % | 5,0 % | 345 / 396 |
| a | 3 | 0,0 % | 5,0 % | 345 / 402 |
| b | 1 | 95,0 % | 80,0 % | 335 / 360 |
| b | 2 | 95,0 % | 80,0 % | 351 / 381 |
| b | 3 | 95,0 % | 80,0 % | 327 / 359 |
| c | 1 | 80,0 % | 70,0 % | 349 / 384 |
| c | 2 | 80,0 % | 65,0 % | 338 / 414 |
| c | 3 | 80,0 % | 60,0 % | 336 / 379 |

## Kan Score-marginalen förutsäga fel?

Ja, som en signal i detta material: medianmarginalen var 0,97 för rätt familj och 0,38 för fel, på skalan 0–4. AUC för låg marginal som felsignal var 0,852 (0,5 = slump). Marginal under 0,25 gav 4 fel av 6, 0,25–0,5 gav 4/9, 0,5–1 gav 4/21 och minst 1 gav 0/24. De 60 observationerna innehåller bara 20 unika meningar och samma familj upprepades i alla c-omgångar; det är därför en beskrivande analys, inte en oberoende validerad spärr. Ingen tröskel valdes eller testades på ett nytt material.

## Varför det blev fel

a tog ofta indirekta följder som ändringar av den egna delen trots instruktionen om direkt ändring. Delarna plats, scenstruktur och medialager fick många falska ja. När en sådan del inte hittade en familj svarade den ofta oklar; dessa lokala oklar blandades sedan med konkreta ändringar. Formuleringen ”berör detta dig?” och denna sammanslagning fungerade dåligt. Detta är ett resultat för just den frysta formuleringen; den korrigerades inte och kördes inte om på testet.

b klarade explicit kamera, plats, rekvisita, ljud, text och scenordning väl. Det blev för försiktigt vid casting (t12) och tog med följdarbete vid översättning (t8). t15 var godtagbar kamerafamilj men tog kamera+props. t20 fick en tillåten familj men fel delmängd och utebliven oklar.

c höjde oklar för uttryck som saknade exakt restaurangnamn, textstorlek eller ny repliktext (t9/t18/t19). För routning behöver sådana parametrar inte vara kända; familjen går ändå att välja. Det är en nackdel med denna skalfråga. c upptäckte däremot båda väntade oklar-fallen.

Detta stödjer att börja med en konkurrerande, sluten familjefråga och sedan filtrera mål/parametrar med deterministiska regler. Oberoende självbedömningar behöver en tydlig gemensam konfliktregel. I nästa experiment bör konkreta alternativ innehålla hela lagliga kombinationer, inte separata frågor vars svar kan bli oförenliga. Detta prov ändrades inte i efterhand för att testa den idén.

## Konkreta editer och kompilering

De fem valda meningarna är t1, t2, t5, t11 och t13. De täcker befintliga kamera-, rums-, scenordnings- och prop-operationer utan att behöva syntetisera tal. t13 är medvetet ett gränsfall: facitet markerar propborttagning som stödd men den angivna källan saknar maten. Det är ingen kontroll av ansiktsuttryck eller ny rörelse.

Först användes b:s redan sparade routning från omgång 1; ingen ny routing gjordes. Ett extra batchat Choice-anrop per mening valde bland verkliga scen-, replik-, person-, prop- och rumsmall-id samt schemats lagliga parametervärden. Saknas var tillåtet för oidentifierad mat. Nya texter genererades inte. Alla fullständiga regier ligger i ut/konkret/<id>/regi.json. Svaren ändrades inte när de visade sig fel.

**Originalkällan:** alla fem kompileringsförsök stoppade före edittillämpning, eftersom 16 sparade filhashar avvek från de aktuella mätfilerna. Originalförsöken gav därför inga plan- eller ej_tillampat-resultat. t13 stoppade också på att PLATSHALLARE krävde kommentar. Felen är bevarade i kompilering.json. Ingen originalfil korrigerades.

**Separat diagnostik:** en kopia av kalla skapades under ut/konkret/, med 16 aktuella hashvärden och 64 absoluta sokvag-referenser så att kopian kan ligga där. Semantikens hash är exakt samma. Endast i t13:s diagnostiska regikopia lades den obligatoriska förklarande kommentaren till; mål och parametrar ändrades inte. Ett fullständigt försök på t1 avslutades med exitkod 1 utan resultat under gränserna 384 MiB/45 s; exakt orsak fastställdes inte och gränserna höjdes inte.

Därefter kördes originalkompilatorns kod för validering, edittillämpning och planbygge för alla fem, med stopp precis före trohet.mat och kvalitet.komplettera. Det undviker bild-/kroppsmätningen. Dessa separata ut/konkret/<id>/diagnostisk_latt/plan.json är kärnplaner, inte renderklara planer. Körningarna tog 1,55–2,27 sekunder vardera. Följande är deras verkliga tillampat/ej_tillampat, inte utfallet mot originalets gamla hashar:

| Mening | Byggd edit | Lätt diagnostiskt utfall |
|---|---|---|
| t1: kameran skakar för mycket i början | `[{"op":"renderkamera","scen":"s1","mal":{"typ":"person","id":"C","punkt":"huvud"}}]` | ej_tillampat: Personmålet saknar rörelse. |
| t2: kom närmare honom när han säger sista grejen | `[{"op":"renderkamera","scen":"s7","mal":{"typ":"person","id":"B","punkt":"huvud"},"inramning":"nara"}]` | tillampat |
| t5: det ska vara på en uteservering | `[{"op":"byt_miljo","scen":"alla","rum":{"kalla":"bank","tillgang_id":"notan_tva_bord","rumsmall_id":"notan_tva_bord","ord":[],"beskrivning":null}}]` | tillampat |
| t11: börja med punchlinen i stället | `[{"op":"flytta_scen","scen":"s6","efter":"s6"}]` | ej_tillampat: En scen kan inte flyttas efter sig själv. |
| t13: ta bort maten från bordet | `[{"op":"ta_bort_prop","scen":"s5","prop":"PLATSHALLARE:mat"}]` | ej_tillampat: Objektet finns inte i scenen: PLATSHALLARE:mat |

t2 landade rätt: r7/B/s7 och nära kamera. t5 accepterades tekniskt men valde fel mall, originalets notan_tva_bord i stället för lokal_uteservering. Ett accepterat id garanterar inte att CM:s avsikt har utförts. t1 visar varför personval måste filtreras med vald scen: C finns inte i s1. t11 visar behovet att förbjuda egen scen som efter-position. För t13 hittades ingen mat i verkliga props och kompilatorn nekade den uttryckliga platshållaren. Alla tre avvisningar kom från den verkliga edittillämpningen. Ingen render kördes.

## Praktisk slutsats och begränsningar

Jev var snabb och billig för att känna igen vilken sorts ändring en konkret mening handlar om. Här passar en fråga där några tydligt åtskilda, lagliga alternativ konkurrerar med varandra. Den var sämre på självständig ja/nej-avgränsning och på att kombinera flera val till en förenlig edit. En snabb familjeroutare räcker därför inte ensam som redigeringskompilator.

En långsammare språkmodell eller motfråga behövs för att skriva eller översätta nya repliker, tolka ”vår kund”, hitta på en fungerande omskrivning till enpersonsformat, föreslå innehåll till vaga kvalitetsönskemål och reda ut saknade eller tvetydiga mål. Saknade prop-id och oförenliga ankare kräver också bättre data eller ett uttryckligt användarval. Säkra, mätbara ändringar kan därefter utföras deterministiskt.

Provet mätte HTTP-routning under en sekund; det visade inte ändrad bild i en förhandsvisning. Originalets hashkonflikt hindrade full kompilering mot just den källan. Efterdiagnostiken ingår inte i de lätta kärnplanerna. De här begränsningarna gör att vi inte kan påstå fem färdiga, korrekta scenändringar.

Totalt 572 HTTP-anrop: 2 storleksmätningar, 230 utveckling, 335 frysta test och 5 konkreta val. Inga nätfel eller återförsök. Totalt 1514008 inputtokens, uppskattad inputkostnad $0,06056 vid det angivna listpriset. Taket 2000 anrop nåddes inte.

## Köra om

Kör från C:/Users/praiseworthy/Desktop/hagen-wf med befintlig Node och scen/.venv/Scripts/python.exe. Inga paket behöver installeras. Behåll app/.env.local där den är, eller använd befintlig TYPESAFE_API_KEY. Läs aldrig ut den i terminalen. För att bevara detta prov: byt först namn på ut/ och resultat.json inom forvarld/jevprov/ (t.ex. ut_20261110 och resultat_20261110.json); skripten vägrar att betala för redan sparade anrop med samma namn. Arkivera också README.md om den ska bevaras före ny rapportgenerering.

1. node forvarld/jevprov/prov.mjs utv
2. node forvarld/jevprov/prov.mjs test
3. node forvarld/jevprov/konkret.mjs
4. För vart och ett av t1, t2, t5, t11, t13: scen/.venv/Scripts/python.exe -B forvarld/jevprov/kompilera_latt.py <id> (originalkontroll; räkna med hashfel i dagens källa).
5. node forvarld/jevprov/forbered_diagnostik.mjs
6. För samma fem: scen/.venv/Scripts/python.exe -B forvarld/jevprov/kompilera_latt.py <id> --endast-edits
7. node forvarld/jevprov/skriv_rapport.mjs

Kör inte --diagnostisk med full efterdiagnostik igen på den minnespressade maskinen. Rapportskriptet bevarar uppgiften om det enda fulla diagnostiska försöket i detta historiska prov; en ny körning bör märka den delen som inte gjord. Den ursprungliga ordningen och alla frågor finns i råfilerna. Ett avbrutet test kan återupptas om alla dess påbörjade meningar redan har fullständiga ruttfiler; halvfärdiga anrop kräver manuell genomgång och får inte döljas eller köras om som nya resultat. Skriptet stoppar vid 1990 anrop i aktuell ut/-journal. Arkiverade journaler ska räknas med om flera experiment körs inom samma budget.
