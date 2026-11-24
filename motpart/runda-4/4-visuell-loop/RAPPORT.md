# Prov 01: en visuell loop och en underkänd baslinje

21 november 2026. Agentens tekniska/visuella granskning; **ingen ägardom ännu**.

## Leverans

Lokalt granskningsbord på http://127.0.0.1:5204. Två tidigare utvecklingsklipp, originalvideo med ljud, synkroniserad befintlig 3D-tolkning, linsändring ±20 %, ångring, hopp mellan samtliga tagningar samt ordagrant sparade tidsbundna kommentarer. Båda scenerna är animerade från befintliga spår. Ingen ny eller manuellt förbättrad geometri har införts.

Modal app list gav timeout efter 20 s och subprocessen avslutades. Inget compute-jobb skickades. **Extern kostnad denna körning: 0 USD.** Aktuell Modal-åtkomst/kvot är fortfarande ej verifierad. CUA:s inbyggda browser saknade native pipe; visuell QA utfördes i stället med projektets befintliga playwright-core och lokal headless Chrome.

## Teknisk verifiering

- Due Piani: 12 tagningar, 92 kameranycklar, 5 person-id:n, 752 personrutor över spåren.
- Spanjorskan: 3 tagningar, 27 kameranycklar, 2 person-id:n, 448 personrutor över spåren.
- 15 representativa tagningar fångade; alla 13 inre övergångar kontrollerade före/efter gränsen.
- Vid noll ändring ger båda 3D-vyerna samma scen-/kamerastatus. Linsändring ändrar bara nyckelns linsfält. Identitetsoperation/ångring återställer paketet exakt och originalpaket muteras inte.
- Uppspelningens media-/scentid skilde cirka 10 ms respektive 3 ms vid testets mätpunkt. Detta är två observationer, inte en generell p95-garanti.
- Ändring till avslutat renderanrop: 2,9 respektive 3,6 ms i första lyckade Chrome-körningen. Detta är CPU-/WebGL-anropstid på cachelagrade scener, inte ny ingest, GPU-fence eller full perceptuell latens.
- Serverstart inklusive två paket och hashning: 0,125 s i första körningen.
- Webbtestet rapporterade inga JavaScript-fel. Maskinläsbart resultat: ut/qa/report.json. Käll-/paket-/renderarhashar: ut/inventering.json.

## Visuella fynd som styr nästa steg

Representativa rutor från alla 15 tagningar granskades i ut/qa. Fynden gäller det som kan ses i dessa rutor. Uppspelning/tagningsväxling kontrollerades även automatiskt; en full mänsklig bedömning av hela rörelseförloppet återstår.

1. **Due Piani S1/S3:** personen står vid en dörr och håller föremål/tallrik; 3D lägger ett stort bord framför personen. Underlaget är alltså fel redan före manipulation. Se ut/qa/duepiani-s1.png och duepiani-s3.png.
2. **Due Piani S2/S8/S10:** närbilder på maträtt och tillagning blir generisk skål/bord eller saknar den centrala matinteraktionen i utsnittet. Det är inte bara ytdetaljer som saknas. Se duepiani-karta-1.jpg och duepiani-karta-7.jpg.
3. **Spanjorskan S1/S3:** originalets närvarande person dominerar bild och samspel; 3D visar små avlägsna kroppar med annan inbördes placering och stort bord. Skalan/utsnittet och interaktionen är inte en användbar återskapning. Se spanjorskan-s1.png och spanjorskan-s3.png.
4. **Spanjorskan S2:** verklig servering blir en generisk skål. Formen och kameravinkeln bevarar inte den visuella läsningen av originalets tallrik.

Kodbelägg till problemen i arbetsbord/ingest_v2/modal_ingest_v2.py:
- Cirka rad 826–830 skapas bordskandidater när ben är skymda **eller** personen klassats som person_med_mat. Bord behöver inte ha observerats där.
- Cirka rad 844–868 skapas bord/matprimitiver och märks observerad trots att placering och dimensioner delvis kommer från regler.
- Cirka rad 709 används fast kamerahöjd 1,38 m; cirka rad 877–891 får rörliga tagningar en schablonmässig framåtrörelse 0,14/0,22 m. Detta är inte uppmätt kamerabana i meter.

## Beslut

**Skala inte denna baslinje till tusen 3D-klipp.** Det skulle skala kända antaganden och fel, och göra bedömningen av semantisk modulering missvisande. Första loopen är nu byggd för att snabbt se detta; den är inte bevis för att grundidén fungerar eller inte fungerar generellt.

Nästa avgränsade ingest-jämförelse ska använda samma original, urval och visning och pröva: (a) objekt/kontakt med bildstöd i stället för automatiskt bord, (b) stabila identiteter, (c) kameraregistrering mot oberoende bildobservationer med osäkerhet. Varje variant får egen proveniens. Att bara gömma det felaktiga bordet eller flytta kameran manuellt skulle inte lösa den allmänna ingesten.

Kameraprovet är en teknisk kontroll av en snabb reversibel ändring, inte en ersättning för den planerade referensstyrda rumsliga operatorn i INFRA v2. Den operatorn och det större urvalet återstår efter att en baslinje är läsbar nog. Ägarens bedömningar är nästa direkta underlag; inga sådana har fabricerats.
