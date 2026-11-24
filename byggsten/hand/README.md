# hand

Sedan 14 nov 2026. Byggsten under `byggsten/`. Version 0. Kostnad: cirka 0,015 dollar (cirka 270 Jev-anrop). Inga andra betalda anrop.

**Vad det är:** tre sätt att röra ett klipp, alla räknade ur den metadata som redan finns i banken.

| verktyg | fråga | börja här |
|---|---|---|
| **Ryggraden** | Vilken typ är klippet, vad står kvar, i vilka riktningar kan det gå och hur långt? | `ut/ryggrad_<id>.md` |
| **Anpassa** | Vart flyttas klippet om det ska passa en viss kund, och vad måste bytas? | `ut/anpassa_<klipp>__<konto>.md`, bild: [ut/spela_kontaktblad.png](ut/spela_kontaktblad.png) |
| **Regibordet** | Ladda in ett klipp ur banken mot en kund. Skriv, klicka på handen eller följ planen mot kunden, och se takterna ritas om direkt. | `python -X utf8 bord.py`, sedan http://127.0.0.1:5197. Skärmbild: [ut/bord/2_efter_kappabar.png](ut/bord/2_efter_kappabar.png) |
| **Regi** | CM skriver en mening. Vilket drag är det, vad ändras, vad följer med, och hur ser det ut? | `ut/regi/<session>/logg.md`, bild: `ut/regi/<session>/kontaktblad.png` |
| **Rutten och bron** | Hur tar man sig mellan två klipp i begripliga steg? | bild: [ut/bro_kontaktblad.png](ut/bro_kontaktblad.png) |

Ryggraden är huvudspåret sedan ägarens besked 14 nov kväll. Rutten mellan två klipp var första frågan och står kvar som prov.

Ingen människa har bedömt något av det. Typindelning, fingrar och ordlistor är mina tills ägaren har kalibrerat dem.

Bakgrund: ägarens dialog med Gemini 14 nov (`Desktop/dialog.txt`) och `../hjarna/PROBLEMBILD.md` (T5).

## Kedjan från klipp till bild
```
samla.py → klipp.jsonl          fem metadatalager, 13 086 klipp
tema.py → tema.npz              temavektor per kort
lasning.py, lasning2.py         Fables läsning av kärnan: sketch (496 kort) och tilltal (387 kort)
stallen.py → stallen.json       ställe, hållning och hantering per takt, ur taktens beskrivning
ryggrad.py <id>                 typ, takter, platser, fingrar med räckvidd, byte av grepp
anpassa.py <id> <konto>         klippet mot kundens egen linje
jevyta.py <id>                  ryggraden som tillstånd och lagliga drag för Jev
spela.py <id> [<konto>]         uppställning per takt, original och kundversion
tillstand.py, regi.py           klippets tillstånd, dragen, och slingan mening → Jev → drag → bild
slinga.py, bord.py, bord/       ett steg i slingan som funktion, och regibordet i webbläsaren
blockout.py, kontaktblad.py     bilderna
```

## Anpassa (`anpassa.py`)
Kunden är ett konto i banken. Kundens egna klipp säger var kunden brukar ligga på varje finger, i vilka rum kunden filmar, vad kunden visar och vilka grepp kunden redan använt. Förslaget per finger är kundens vanliga värde, men aldrig utanför vad klipp av samma typ går (p10 till p90). Då byter klippet inte typ på vägen.

Kört exempel: talking head med visning (`blubnan.liljeholm-7520230113443663126`, "vad kostar en middag för två") mot `@kappabar` (22 kort, en bar).

| finger | klippet | kunden brukar | förslag |
|---|---|---|---|
| antal takter | 4 | 3 | 3: uppmaningen stryks |
| klipp per 10 s | 2,5 | 1,0 | lugnare klippning |
| mat i bild | 1,0 | 0,0 | 0,15, stoppad av typen |
| personer i bild | 1 | 2 | en kollega till |
| krav på produktion | 2 | 1 | enklare |

Rapporten säger också:
- **Kundens linje:** bara 5 % av kundens klipp är av den här typen. Kunden gör mest tilltal utan visning och kampanj.
- **Kunden har redan gjort något liknande:** två av kundens egna klipp ligger på 0,99–1,00 i temanärhet ("förklarar ett erbjudande rakt in i kameran").
- **Per takt:** vad CM gör, och vilka produkter kunden redan visar (burgare och drinkar, steak frites).
- **Samma idé i kundens sorts rum:** klipp av samma typ eller med samma grepp, nära i tema, inspelade i en bar och inte i källans rum. För gelato mot samma kund hittar den "gästen beställer minsta storleken men serveras en komiskt överdimensionerad version", alltså storlekskontrasten buren i en bar.

Bilden `ut/spela_kontaktblad.png` visar originalet överst (dörr, sedan bord i tre takter) och kundversionen under (bardisk med kollega, sedan bord, tre takter).

Gränser:
- Förslaget är kundens median. Det säger vart, inte att det blir bra.
- Kundens produkter är hämtade ur kortens platser och är ofta fraser, inte rena produktnamn.
- Kundversionens uppställning är ett utkast ur siffror. Manus skrivs inte.
- Lokalens mått finns inte. Stället är ett ord.

## Ställen (`stallen.py`)
Scenografi på taktnivå. Varje takt i ett formatkort har en mening, och den säger ibland var takten utspelas, hur personen håller sig och vad hen gör med händerna. Ordlistor plockar ut det.

- 5 180 takter. Stället är utsagt i 22 % av dem.
- Mönstret per typ syns ändå. Tilltal med visning: kroken oftast utanför eller vid entrén (29 av 55 utsagda), visningen i köket eller vid bordet. Sketch: kroken vid disken.
- `spela.py` ställer upp en takt så här: taktens eget ställe, annars samma som takten före, annars typens vanligaste för funktionen, annars klippets rum.

Det är ord i en beskrivning, inte en läsning av bilden. 78 % av takterna säger inget om plats.

## Läsningen av tilltalsklipp (`lasning2.py`)
Samma metod som för sketcherna, på de 387 korten med strategi tilltal till kameran:

| fält | värden | tvillingkappa |
|---|---|---|
| grepp | svarar på fråga, provsmakar, visar tillagning, guidar, utmanar publiken, annonserar, bakom kulisserna, tycker till, krok som vänder | 0,87 |
| motpart | tittaren, kollega, gäst eller förbipasserande, kommentar | 0,77 |
| last (vad som bär) | produkten, människan, idén, erbjudandet | 0,77 |

18 tvillingpar, 9 av dem mellan olika konton. Det är färre än för sketcherna.

Greppet används i ryggraden som "samma ämne, annat grepp": för varje annat grepp det närmaste klippet i tema. För middagen för två blir det bland annat tillagning steg för steg, fast menypaket och "fråga förbipasserande om favorittillbehöret".

## Regibordet (`bord.py`, `bord/index.html`, `slinga.py`)
En lokal sida för slingan, för vilket klipp som helst i banken mot vilken kund som helst.

Start: `python -X utf8 bord.py` från `byggsten/hand/` med `scen/.venv`. Öppna http://127.0.0.1:5197. Servern binder bara loopback.

| del av sidan | vad den gör |
|---|---|
| **Sök och ladda in** | Sök bland 1 480 kort på ord i kärna och handling, filtrera på typ. Kund är ett konto i banken (95 med minst 8 kort). Ryggrad och anpassning räknas fram första gången, 1–8 s. |
| **Takterna** | En bild per takt, ritad i webbläsaren med three.js. Ryggradstakter har mörk kant. Raden under visar läget före senaste ändringen. |
| **Regi** | Skriv en mening. Jev väljer drag, koden utför, följderna listas. Under marginal 0,4 kommer en motfråga med knappar. |
| **Mot kunden** | Kundens linje i en rad, om kunden redan har gjort något liknande, och dragen som flyttar klippet mot kunden. Varje drag har ett skäl ("antal takter: klippet 4, kunden brukar 3") och en Gör-knapp. Listan räknas om efter varje ändring. |
| **Handen** | Ett spår per finger: typens spann (10–90 %), originalet, läget nu och var kunden brukar ligga. Pilarna gör draget åt det hållet. |
| **Mallen** | Kortets mall med platserna som fält. Efter ett produktbyte blir fält som gällde den gamla produkten röda. CM skriver direkt i fälten, utan modell. |
| **Ångra** | Ett steg bakåt. |

Kontrollkörningar i huvudlös webbläsare (`node bord/koll.mjs <port> <klipp> <konto>`), utan fel i sidan:

| pass | laddning | per steg |
|---|---|---|
| talking head (`blubnan…`) mot `@kappabar`, förberett | 1,3 s | klick 190–460 ms, mening via Jev 410–490 ms |
| oförberett klipp (`babulsofficial-7486183731082906902`) mot ny kund (`@basso.social`) | cirka 8 s första gången | klick 190–630 ms, mening via Jev 420–660 ms |

Skärmbilder: [ut/bord/2_efter_kappabar.png](ut/bord/2_efter_kappabar.png), [ut/bord/2_efter_basso.social.png](ut/bord/2_efter_basso.social.png).

Klick på ett drag kostar inget Jev-anrop. Nyckeln stannar i servern. Varje pass loggas i `ut/regi/bord-<tid>/logg.json`. Taket är 300 Jev-anrop per serverstart.

Vad körningarna visade:
- **Dragen krockar.** "Enklare att spela in" samlade alla takter på ett ställe och flyttade tillbaka takten som nyss lagts vid bardisken. Nu rörs inte takter som CM själv har flyttat.
- **Kortare måste alltid gå att välja.** När bara ryggraden var kvar fanns inget drag för "kortare", och Jev svarade osäkert. Nu väljer den draget och koden stoppar med skälet.
- **Handen följer bara delvis med.** Längd, antal takter, klipptakt, personer och bundenhet räknas om ur tillståndet. Mat, lokal, text och säljande står kvar på originalets värde.

Gränser:
- Sidan är ett verktyg för att pröva slingan, inte ett förslag på hur appen ska se ut.
- Ett pass i taget, i serverns minne.
- Bilden är en uppställning med dockor. Den visar var och vem, inte hur.
- Manus skrivs inte. Mallen har fält, men takternas beskrivningar står kvar som i originalet med en markering när de inte längre stämmer.
- Sökningen är ordmatchning, inte tema.
- Planen mot kunden är kundens median per finger. Den säger vart, inte att det blir bra.

## Fri text: förståndet och lärda drag (`forstand.py`), 16 nov
Ägarens besked 16 nov: fri text är nyckeln, och utbyte sker på funktion i sammanhanget, inte på kategori.

```
mening → Jev bland lagliga + lärda drag ─ träff ─────────────► koden utför (cirka 250 ms)
                    │ inget passar / osäker
                    ▼
        förståndet (språkmodell, 13–19 s) läser meningen mot tillståndet,
        kundens linje och CM:s avsikt med passet → recept i ett slutet språk
                    ▼
        koden utför receptet → sparas i ut/lardrag.json som ett lärt drag
```

- **Avsikten** är ett fritt fält överst i Regi. Den följer med till både Jev och förståndet.
- **Receptet** har fem slags steg: `drag` (ett befintligt drag), `satt` (ställe, hållning, hantering, kollega, skylt, zoom, sek på valda takter), `byt_element` (ett inslag byts mot kundens, med funktionen som ärvs utskriven), `markera` (manus) och `ny_takt`. Modellen ändrar aldrig tillståndet själv.
- **Spärrar:** förståndet får ryggradens fyra delar (typ, teknik och ton, längd och mening, det mellan raderna) och stoppar det som bryter dem, med skäl och ett förslag. Kropp och kamera skickas till scenlagret.
- **Lärda drag** gäller klippet, typen eller alla. De syns under "Lärda drag" med knapparna Gör och Glöm.
- **Modellen** nås genom Codex CLI på ägarens plan (`codex exec`, skrivskyddat, tom mapp). Byt med `FORSTAND_MODELL` och `FORSTAND_EFFORT`. Varje anrop loggas i `ut/forstand/`.

Kört 16 nov mot `blubnan…` och `@kappabar`, med avsikten "samma upplägg, men det ska kännas som deras ställe: baren och stämningen, inte prisjakt":

| mening | väg | utfall |
|---|---|---|
| låt bartendern skaka en drink i början i stället för att han står vid dörren | förståndet, 19 s | takt 1 till baren; "presentatören vid entrén" byts mot "bartendern som skakar en drink", som bär "fångar intresset och visar vad som gör stället livligt". Sparat. |
| börja med att bartendern skakar en drink istället | Jev, 244 ms, marginal 0,98 | det lärda draget, samma ändring |
| de har livemusik på fredagar, få in det i stället för att räkna upp rätterna | Jev osäker (0,19), sedan förståndet, 16 s | uppräkningen i takt 3 byts mot livemusiken, som bär "mervärdet som gör måltiden till en hel kväll". Sparat. |
| gör om det till en sketch där gästen blir lurad på notan | förståndet, 15 s | stoppat: byter typ. Förslag: låt gästen reagera på notan inom samma upplägg. |
| han ska halta lite när han går in | förståndet, 13 s | scenlagret, ingen ändring här |

**Scenlagret går vidare till kroppen** (16 nov kväll). När förståndet lägger en mening på nivån scenlagret och klippet har en läst kropp i kedjan, visar bordet knappen "Kör på kroppen". Den skickar meningen till `forvarld/kropp/forskning/mm/mening.py` (ett kommando och filer, ingen import), som skriver villkor för en rörelsemodell, kör den, mäter och låter förståndet justera. Bordet visar bladet och filmen med streckfigurer, och vad som mättes. Det tar 1–3 minuter. I dag har bara gelato en kropp inlagd (`forstand.KROPP`). Kroppen kommer ur MaskedMimic, som är AMASS-tränad: forskning, inte kommersiellt bruk. Läget står i `forvarld/kropp/forskning/mm/FELSOK.md`.

**Vägen till modellen** (16 nov): Gemini direkt först (`gemini-3-flash-preview`, cirka 3 s när den svarar), och `codex exec` som reserv (13–19 s). Styrs med `FORSTAND_VIA`.

Gränser:
- Fem meningar, alla mina. Ingen människa har bedömt läsningarna.
- **Bilden följer inte med ett inslagsbyte.** Dockan står kvar; bytet syns som markering på takten och som fält under Mallen.
- Alla tre sparade recept gäller bara klippet. Om drag som gäller typen eller alla blir användbara är oprövat.
- Fler lärda drag ger Jev fler val. Vad det gör med marginalerna vid 50 eller 500 är inte mätt.
- Förståndet tar 13–19 s. Det är starten av `codex exec` plus modellen, inte optimerat.
- Motfrågans knappar står kvar i loggen efter att förståndet har svarat.

## Regi: slingan (`regi.py`, `tillstand.py`)
Det här är förvärldens slinga i miniatyr, på ryggradens nivå: CM skriver, Jev väljer, koden utför, bilden ritas om.

```
mening → Jev: ett Choice bland de drag som är lagliga i det aktuella tillståndet
       → spärrar: marginal under 0,4 utförs inte, ryggradstakter stryks aldrig
       → vid byt_lokal: vart, och vilka takter. Vid byt_produkt: ur meningen eller kundens. Vid byt_upplagg: vilket.
       → tillampa(): ändrar tillståndet och räknar upp följderna
       → blockout: en rad bilder per tillstånd
```

Jev väljer bara. Allt som ändras görs av `tillstand.py`, och det som kräver ny text märks som manus på takten.

Två körda pass mot `@kappabar` (loggarna ligger i `ut/regi/bar/` och `ut/regi/gelato_bar/`):

| mening | drag | utfall |
|---|---|---|
| byt maten till våra burgare och drinkar | byt_produkt | takt 2 och 3 märkta. Följd: måltidstyp och pris gällde den gamla produkten, manus. |
| spela in början vid bardisken istället | byt_lokal, bar, första takten | takt 1 flyttad. Följd: takten nämner sitt gamla ställe, manus. |
| ta bort slutet där han ber folk tagga | takt4_stryk | struken. Följd: kontrollera att takten före håller som slutbild. |
| ha med en kollega också | personer_upp | kollega i takt 1. Följd: kravet på personer går från 1 till 2. |
| gör honom gladare | osäkert | inte utfört. Se nedan. |
| kan vi göra det som en provsmakning istället? | byt_upplagg, provsmakar | inget drag: pekar på närmaste klipp i tema med det upplägget. |
| ta bort första scenen | takt1_skyddad | stoppat: takten är ryggrad. |
| gör skillnaden mellan portionerna större (gelato) | kontrast_upp | kontrasten 1,0 → 1,4. Syns i bilden: liten sak i takt 1, stor i sista takten. |
| ta bort Vs-skylten och musikbytet (gelato) | takt3_stryk | struken. Följd: vändningen är borta, kontrasten måste synas i bilden själv. |
| hoppa över när hon skopar (gelato) | takt1_skyddad | stoppat: skopandet är ryggrad. |

Tid per mening: 170–250 ms i Jev, ett eller två anrop. Blockouten tar några sekunder och ritas en gång i slutet.

**Vad passen lärde, i den ordning felen kom:**
1. **Dragen måste räknas om efter varje ändring.** När takt 4 är struken finns inte draget kvar. Ytan byggs ur tillståndet, inte ur klippet.
2. **Två drag som ger samma ändring är ingen osäkerhet.** "Kortare" ger ofta liten marginal mellan `langd_ned` och `takt3_korta`. Koden provkör båda och utför om tillstånden blir lika.
3. **Ryggradstakter måste finnas som val.** Utan det pekade Jev på grannen: "hoppa över när hon skopar" strök takt 2 (räcker fram skeden) med marginal 0,56. Med valet `takt1_skyddad` pekar den rätt (0,88) och koden stoppar.
4. **Kontrasten saknades som ratt.** "Gör skillnaden större" gick till scenlagret, fast det är gelatos bärande ratt (T5 i PROBLEMBILD.md). Nu finns `kontrast_upp` och `kontrast_ned` för klipp som är lästa som kontrast eller har två rekvisitaplatser i mallen. Kortets risk ("vågar inte överdriva") följer med draget nedåt.
5. **Produkten i meningen går före kundens.** "Gör det med pommes" fick först kundens burgare. Nu frågas Jev om meningen själv nämner en produkt.
6. **Marginalspärren behövs och 0,25 räckte inte.** "Gör honom gladare" gav i fyra körningar scenlagret, manus, byt_produkt och byt_produkt, alla med marginal 0,05–0,25. En gång utfördes ett produktbyte på 0,25. Spärren står nu på 0,4.

Gränser:
- **Dragen är mina.** Vad som räknas som ett drag och hur stort ett steg är (halvera en takt, kontrast gånger 1,4) är satt av mig.
- **Jev varierar mellan körningar på oklara meningar.** Spärren fångar det, men då får CM en motfråga.
- **Sekunder per takt är klippets längd delad lika.** Takternas verkliga tider finns inte i korten.
- **Följderna är regler jag skrev,** inte något systemet räknar fram. Det är samma svaghet som liggarens handskrivna spridning (S2 i UTMANING.md).
- **Meningarna är mina,** utom gelatos elva.

## Jev på ryggradens yta (`jevyta.py`, `jevprov.mjs`)
Ryggraden kompileras till ett tillstånd (cirka 1 400 tecken) och en sluten lista av drag: fingrar med räckvidd, takter som får strykas eller kortas, byt produkt, byt lokal, byt upplägg, och tre utgångar (`manus`, `scenlagret`, `ingen_passar`). Jev väljer ett drag per CM-mening.

| prov | meningar | rätt per omgång | stabila | median |
|---|---|---|---|---|
| talking head, mina meningar | 22 | 22, 22, 22 | 22 av 22 | 166 ms |
| gelato, befintliga CM-meningar ur `forvarld/gelato` | 11 | 9, 9, 9 | 11 av 11 | 164 ms |
| gelato, omkörning med justerad yta | 11 | 11, 11, 11 | 11 av 11 | 169 ms |

- Meningar och facit låstes med hash före första anropet. Prognoserna står i `ut/jevprov*/forregistrering.json`.
- **Första provet är lätt.** Meningarna och dragens formuleringar är skrivna av samma hand.
- **Felen i gelatoprovet var de förutsagda:** "med andra handen" hamnade på draget som då hette `byt_grepp`. Ytan saknade en utgång för det som hör till kropp och kamera, och ordet grepp drog. Efter att draget döptes om och utgången `scenlagret` lades till gick alla rätt, men det är en omkörning på samma meningar och inget nytt prov.
- **Marginalen varnar.** "Hoppa över när hon skopar" gav `takter_ned` med marginal 0,07, och skopandet är ryggrad. Rätta svar ligger på 0,5–0,8 i medel.

Vad det visar: ryggraden och scenlagret (liggaren) är två nivåer, och en mening måste först routas till rätt nivå.

## Bron notan → gelato
Hållpunkterna är mätta (`rutt.py`). Scenen i varje steg är skriven (`bro_notan_gelato.json`). Bilderna är en blockout med schablonmått, inte en läsning av video.

| t | finger som rör sig | bevisklipp, kärna | tema mot förra |
|---|---|---|---|
| 0,00 | – | notan: kräver att han tar notan, de är främlingar | – |
| 0,14 | plats: matsal → disk | `inspektorcevap-7517…`: främling "betalar" hennes nota med hennes eget kort | 0,99 |
| 0,25 | relation: gäster → gäst mot personal | `gdk_sweden-7629…`: kund prutar | 0,99 |
| 0,32 | relation: → personal mot gäst | `fratelli.stockhol-7680…`: personalen stoppar mellanskillnaden i fickan | 1,00 |
| 0,40 | produkt i fokus | `chickiiburger-7491…`: kunden har inte råd, personalen tar en tugga som mellanskillnad | 0,99 |
| 0,56 | insats: betalning → mat | `anettesrestaurang-7614…`: "slut", och äter den själva framför kunden | 0,97 |
| 0,67 | poängen in i en sak | `mondocoatbridge-7620…`: serverar fel, irriterad över tillbehöret | 0,98 |
| 0,78 | språng 1 av 2: inget tal | `brunchoteket-7489…` (utanför rutten): släpper inte lådan | skrivet |
| 0,89 | språng 2 av 2: en person | inget bevisklipp | skrivet |
| 1,00 | – | gelato: liten sked, stor spade | 0,99 |

"Tema mot förra" är andelen av alla kortpar i banken som ligger längre ifrån varandra i tema än de två hållpunkterna. Notan och gelato själva ligger på 0,71.

Klippet vid t 0,40 är bryggan i sak: betalning och mat blir samma sak i en bild.

Rutter med 2 till 8 hopp står i `ut/rutt_d-dialog-notan__kennysgelato2.0-7596403003901381910.json`. Alla med tre hopp eller fler har exakt ett språng, och det ligger alltid sist.

## Ryggraden (`ryggrad.py`, `typer.py`)
Efter ägarens besked 14 nov, kväll: inte en linje mellan två klipp, utan ett klipp i mitten och fingrar utåt. Typen av innehåll avgör vilka fingrar som finns.

`python -X utf8 ryggrad.py <id>` ger för ett klipp (`ut/ryggrad_<id>.md` och `.json`):
1. **Typen**, ur formatkortet: strategi, tilltal och om produkten visas. Till exempel "tilltal, till kameran, med visning av produkt" (213 klipp).
2. **Takterna**: vilka som är ryggrad, vilka som kan kortas eller strykas, vad varje takt är bunden till och vad CM gör med den (byt till kundens produkt, placera i kundens lokal, behåll mallen, skriv om fritt).
3. **Platserna i mallen**: det som byts mot kundens (produkt, pris, replik, lokal).
4. **Fingrarna med räckvidd**: var klippet ligger mot andra klipp av samma typ (p10, median, p90), hur långt det går att gå åt varje håll, och om typens kärnklipp ligger högre eller lägre.
5. **Dit kan det gå**: för varje riktning det närmaste klippet i tema som redan ligger där, med länk.

Fingrarna här är de CM frågar efter: längd, antal takter, klipptakt (mätt med ffmpeg), person, mat och lokal i bild, skärmtext, erbjudande och uppmaning, antal personer, hur bundet klippet är till produkt och lokal, krav på skådespel och produktion.

Körda exempel:
| klipp | typ | kohort |
|---|---|---|
| `blubnan.liljeholm-7520230113443663126` | tilltal till kameran med visning (vad kostar en middag för två) | 212 |
| `kennysgelato2.0-7596403003901381910` | sketch, spelad scen, med visning | 27 |
| `chickiiburger-7576259590170348822` (notans tvilling) | sketch, spelad scen, utan visning | 289 |

**Typerna har olika fingrar** (`ut/typer.md`). Spridning inom typen delad med spridningen i hela banken:
| typ | rör sig mest | ligger still |
|---|---|---|
| tilltal till kameran med visning | längd, lokalen i bild, skärmtext, erbjudande | person i bild, antal personer, antal takter |
| sketch, spelad scen | mat i bild, antal personer, klipptakt, bundet till lokalen | produktion, person i bild |
| visning utan tilltal | produktion, klipptakt, lokalen i bild, antal personer | skådespel, mat i bild |

Det som ligger still är vad typen är. Det som rör sig är där en CM kan flytta klippet utan att det byter typ.

Gränser:
- Räckvidden är vad andra konton har gjort, inte vad som fungerar. "Kärnklippen ligger högre" är ett samband inom typen, inget orsakspåstående.
- Typen är tre fält ur kortet. Ägaren ska kalibrera indelningen.
- Sex fingrar kräver ytlagren (L3). Små typer, som gelatos med 27 klipp, får bara de sju fingrar som alla kort har.
- Tematiska byten (scenen görs om för att bära kundens promo) och lokalens mått finns inte som fingrar. Takter märkta "placera i kundens lokal" är där en lokalskanning skulle gå in.
- Spridningstal över 1 för produktion kommer av att nästan hela banken ligger på 1.

## Vad som ändrades från första versionen
| brist | åtgärd i v0 | utfall |
|---|---|---|
| Bara 736 kort i rummet | Ord, produkt och ensemble hämtas ur formatkortet när ytlagren saknas | 1 480 kort. Ersättarna följer ytlagren med rho 0,74, 0,74 och 0,54 på de 736 som har båda. |
| Tema saknades | Temavektor per kort ur kärna och handling (`tema.py`, öppen modell lokalt) | Hållpunkterna ligger på 0,97–1,00 mot varandra. Första versionens rutt hoppade mellan orelaterade skämt. |
| Relationen mellan rollerna saknades | Min läsning av 496 sketchkärnor i fyra slutna fält (`lasning.py`) | Relation och insats styr rutten. Bytet från gäst till personal är hopp 0,25–0,32. |
| En läsning per kort, lägesfel | Kort där ytlager och formatkort säger emot varandra får inte bli hållpunkt | 184 av 1 480 kort uteslutna. |
| Text styrde fast den är osäkert läst | Text styr inte längre | Två läsare: kappa 0,21. Ersättare: rho 0,23. |
| Notans rad var handkodad | Notans tvilling i banken avgör meningsfingrarna | `chickiiburger-7576259590170348822` har samma mall (tjafs i närbild, vidbilden visar främlingar). Tre handkodade värden byttes mot tvillingens. |
| Ingenting syntes | Blockout i Blender per steg, kontaktblad | 10 bilder, 540×960. |

## Läsningen (`lasning_fable_*.txt`, `ut/lasning.json`)
Jag har läst kärnan (en mening per kort) för de 496 kort som är sketchvärld eller spelad scen, och satt fyra fält:

| fält | värden |
|---|---|
| mekanik | kontrast, avslöjande, bokstavligt, eskalering, fasad, överdrift, satt på plats, missförstånd, igenkänning, ingen |
| relation | personal mot gäst, gäst mot personal, personal sinsemellan, chef och personal, gäster sinsemellan, personal ensam, annan |
| offer | personal, gäst, chef, ingen |
| insats | betalning, service, mat, uppmärksamhet, vila, regler, ingen |

**Stabilitet på tvillingar.** Banken har 29 par av kort med nästan samma kärna (temanärhet cos ≥ 0,93), 26 av dem från olika konton. Jag visste inte vilka som var tvillingar när jag läste.

| fält | lika i tvillingpar | kappa |
|---|---|---|
| offer | 86 % | 0,80 |
| insats | 83 % | 0,79 |
| relation | 76 % | 0,71 |
| mekanik | 52 % | 0,45 |

Relation, offer och insats får styra. Mekanik (typen av skämt) får inte det: jag är inte överens med mig själv.

Underlaget är en mening skriven av Gemini, inte videon. Fel i kärnan följer med.

## Vilka fingrar får styra
Regeln i v0: ett finger styr rutten bara om det finns ett mått på att det går att lita på.

| finger | styr | belägg |
|---|---|---|
| ord | ja | två läsare, kappa 0,69 |
| ensemble | ja | ersättare rho 0,54 |
| produkt | ja | ersättare rho 0,74 |
| relation, insats, offer | ja | tvillingkappa 0,71–0,80 |
| vändning | bevaras | två läsare, kappa 0,76 |
| plats | ja | **obelagt**: en läsare, inget att jämföra med |
| poäng i sak, poäng i ord | ja, mjukt | **obelagt**: en läsare |
| text, klippning, lånat ljud, ansikte | nej | kappa 0,2 eller ingen kanal i förvärlden |
| mekanik | nej | tvillingkappa 0,45 |

Provet på de ursprungliga fingrarna (kappa, ortogonalitet, proxy, 528 hårda motexempel) står kvar i `ut/prov.json`. Kort: 14 fingrar är ungefär 8–9 oberoende riktningar, och var poängen bor går inte att gissa ur ytan (R² 0,04–0,19).

## Vad språnget säger
Gelato är en ovanlig kombination: personal mot gäst, på gästens bekostnad, men en ensam person utan tal. Bland de 58 klipp som ligger mellan notan och gelato är 2 ensamma och 7 utan tal. Därför går det inte att nå gelato i steg om två ändringar.

Motprov: från notans tvilling till `brunchoteket-7489440202146974998` (två personer, inget tal, personalen vill ha maten själv) går rutten utan språng i 2–4 hopp.

*Min tolkning:* det sista hoppet är där en spelad scen mellan två personer blir en uppvisning mot kameran. Det är en annan sorts ändring än de andra, och den borde vara ett eget finger (kunden i bild eller utanför).

## Filer
| fil | vad |
|---|---|
| `samla.py` → `ut/klipp.jsonl` | fem metadatalager, en rad per klipp (13 086) |
| `fingrar.py`, `prov.py` → `ut/prov.json` | fingrarna och provet på dem |
| `tema.py` → `ut/tema.npz` | temavektor per kort (`intfloat/multilingual-e5-small`, lokalt) |
| `lasning.py` → `ut/lasning.json`, `ut/lasning_prov.json` | läsningen och tvillingprovet |
| `rum.py` → `ut/rum.jsonl` | rummet v0: 1 480 kort med styrande fingrar, källa och oenighet |
| `rutt.py` → `ut/rutt_<start>__<mål>.json` | rutter för 2–12 hopp mellan vilka två kort som helst |
| `bro_notan_gelato.json` | scenen per steg, med uppställning för blockout |
| `blockout.py`, `kontaktblad.py` → `ut/blockout/`, `ut/bro_kontaktblad.png` | bilderna |
| `ryggrad.py`, `typer.py` → `ut/ryggrad_<id>.md`, `ut/typer.md` | ett klipp i mitten, fingrar utåt; typernas fingrar |
| `anpassa.py` → `ut/anpassa_<klipp>__<konto>.md` | klippet mot en kunds linje |
| `stallen.py` → `ut/stallen.json`, `ut/stallen_typ.json` | ställe, hållning, hantering per takt |
| `lasning2.py`, `lasning2_fable_*.txt` | läsningen av tilltalsklipp |
| `jevyta.py`, `jevprov.mjs`, `jev_meningar*.json` → `ut/jev_<id>.json`, `ut/jevprov*/` | Jev-ytan och proven |
| `spela.py` → `ut/spela_*.json`, `ut/spela_kontaktblad.png` | uppställning per takt, original och kundversion |
| `tillstand.py`, `regi.py` → `ut/regi/<session>/` | tillståndet, dragen och slingan |
| `slinga.py`, `bord.py`, `bord/index.html`, `bord/koll.mjs` → `ut/bord/`, `ut/regi/bord-*/` | regibordet och dess kontroll |
| `notan_kort.json` | handkodat kort för notan |

Kör från `byggsten/hand/` med `scen/.venv`:
```
python -X utf8 samla.py && python -X utf8 prov.py
python -X utf8 tema.py && python -X utf8 lasning.py && python -X utf8 rum.py
python -X utf8 rutt.py [start-id] [mål-id]
blender -b --factory-startup --python blockout.py -- bro_notan_gelato.json ut/blockout
python -X utf8 kontaktblad.py
```

## Gränser som står kvar
- **Scenografin är fortfarande en kategori.** Uppställningen i blockouten (var folk står, avstånd, blick) är skriven av mig med schablonmått. Banken har ingen placering.
- **Kroppen saknas.** Dockorna har fyra poser. Hur någon rör sig finns inte i metadatan.
- **Relation och insats finns bara för 496 sketchkort.** Rutter utanför sketchvärlden får inte de fingrarna.
- **Min läsning är gjord en gång, på en mening per kort.** Tvillingprovet mäter 29 par.
- **Plats och var poängen bor är obelagda** men styr ändå.
- **Bevisklippet visar formen, inte scenen.** Vid t 0,67 är beviset svagt: klippet har poängen i en sak men inte storlekskontrasten.
- **Språngets andra halva står utan bevisklipp.**
- **Rutten är inte unik.** Den väljs på temanärhet och hållpunktens hylla. Andra vikter ger andra klipp.
- **Text, ljud och redigering** bär gelatos vändning och har varken pålitlig läsning eller plats i förvärlden (T7).

## Vad en ny Gemini-läsning borde ge, när det finns pengar
1. Uppställning per takt: vem står var mot disk, bord och kamera, och vart blicken går.
2. Kunden i bild eller utanför, och vem scenen spelas mot (motspelare eller kamera). Det är språnget.
3. Vad som bär poängen, som ett val bland kanaler (replik, text, sak, storlek, klipp, ljud, min) med tidpunkt. Läst två gånger.
4. Relation, offer och insats direkt ur videon, så att min läsning får en andra läsare.
5. De graderade storheterna: storlek, avstånd, tid till punchline.
6. Observation först (tidskodat protokoll), tolkning sedan, i två anrop.

## Nästa steg (inget är påbörjat)
- Ägaren kalibrerar: typindelningen, vilka fingrar som finns per typ, och vad som räknas som ryggrad.
- CM:s egna meningar mot Jev-ytan. Det första provet behöver meningar som jag inte har skrivit.
- Ägaren provar regibordet med egna meningar. Loggarna i `ut/regi/bord-*/` blir det första underlaget med meningar som jag inte har skrivit.
- Koppla utgången `scenlagret` till liggarens drag, så att "med andra handen" går vidare i stället för att stanna.
- Routning i två steg: först nivå (ryggrad, scenlagret, manus), sedan drag. Liggaren har redan dragen för scenlagret.
- Blint prov med de 528 hårda motexemplen och tvillingparen, för att belägga plats och var poängen bor.
- En ny videoläsning när det finns pengar, enligt listan ovan. Ställe per takt (utsagt i 22 % i dag) och kunden i bild eller utanför väger tyngst.
- Första hoppet i bron (matsal → disk) på notans riktiga 3D-data i bryggan.
