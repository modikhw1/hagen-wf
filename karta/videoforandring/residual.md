# Steg 1: kontots baslinje och klippets residual

Körd 2 nov 2026. Kod i `video/profil/` (`npm run profil`, `npm run test:profil`), data i `data/profil/baslinje.json`. Bakgrund i [inlarning.md](inlarning.md), avsnitt 2.6 och 8.

## Hur

- **Underlag:** Metadata ur `data/bank/<konto>/lista.json`: längd, visningar, gillanden, kommentarer, delningar och datum. Klipp yngre än 14 dagar räknas inte, eftersom deras visningar inte har satt sig.
- **Baslinje:** För varje klipp tas medianen av de 15 tidsmässigt närmaste *andra* klippen i samma konto. Baslinjen är rullande, eftersom konton växer och krymper.
- **Residualer** (log10):
  - `rv`: visningar mot baslinjen (räckvidd)
  - `rl`, `rc`, `rs`: gillanden, kommentarer och delningar per visning, mot baslinjen
- **Egenskapernas effekt** mäts *inom* konto: klipp med egenskapen minus klipp utan. Det prövas i båda tidshalvorna av varje konto och med ett konto i taget utelämnat.

## Resultat

| Kontroll | Värde | Betyder |
|---|---|---|
| Underlag | 5 240 klipp, 59 konton | |
| Kontots baslinje förklarar | 48 % av variansen i log-visningar | Hälften är kontot, hälften är klippet och brus. |
| Spridning i `rv` | sd 0,48. p10 till p90 är −0,41 till +0,72 | Ett vanligt klipp hamnar mellan 0,4 och 5 gånger kontots normala visningar. |
| Autokorrelation mellan grannklipp | 0,04 | Den rullande baslinjen fångar kontots trend. Det som återstår är klippets eget. |
| `rv` mot längd och mot ålder | 0,05 och 0,02 | Ingen snedvridning av längd eller ålder. |
| `rv` mot gillanden per visning | 0,09 | Räckvidd och gillandegrad är nästan oberoende. |
| Gillanden mot delningar (per visning) | 0,32 | Engagemangsmåtten håller ihop med varandra. |
| `rv` mot kommentarer per visning | −0,47 | Mekaniskt: fler visningar späder ut kommentarerna. Det är inte ett innehållssamband. |
| De sållade klippens median-`rv` | +0,39 (alla: 0,00) | **Banken är vald på utfallet.** De nedladdade klippen gick i median 2,5 gånger bättre än sitt konto, och bara 97 av 532 ligger under baslinjen. |

### Egenskaper ur sållningen (inom konto, 532 sållade klipp)

| Egenskap | Konton | `rv` | `rl` | `rs` | Håller? |
|---|---|---|---|---|---|
| Relaterbar sketch | 23 | +0,05 | +0,07 | −0,06 | Svagt. Samma riktning i båda halvorna för `rv`. |
| Matporr och process | 20 | −0,01 | −0,02 | −0,03 | Nej |
| Direkt tilltal | 13 | −0,03 | −0,03 | **+0,29** (85 % av kontona) | Hypotes: tilltal delas ungefär dubbelt så mycket per visning. |
| Montage | 28 | −0,06 | +0,02 | −0,05 | Nej, halvorna är oense. |
| Texttungt | 21 | −0,06 | −0,05 | −0,08 | Svagt negativt, åt samma håll överallt. |
| Person i bild minst 80 % | 21 | +0,11 (67 %) | +0,03 | −0,02 | Halvorna är oense. |
| Minst två personer | 28 | 0,00 | +0,04 (71 %) | +0,06 | Svagt för gillanden. |
| Kort (högst 15 s), alla klipp | 52 | −0,02 | | | Nej. Längden spelar ingen roll i sig. |

Effekterna är små, högst cirka 0,1 log10 (ungefär 25 %), utom delningarna för direkt tilltal. De är dessutom pressade av selektionen.

## Slutsatser

1. **Residualen mot kontot är en användbar signal.** Den är oberoende mellan grannklipp, opåverkad av längd och ålder, och sprider sig mycket (en faktor 10 mellan p10 och p90). "Relativt till kontot" fungerar som ram.
2. **Räckvidd och engagemang är olika slutmål.** De korrelerar nästan inte, och typerna verkar vinna på olika mått: sketcher på gillanden, tilltal på delningar. Det är flera slutmål i praktiken, och tittartid från kundernas statistik blir ett fjärde.
3. **Normen kan inte byggas på dagens urval.** Klippen laddades ner för att de presterade väl, så allt under baslinjen är nästan borta. Det som behövs är ett **osållat stickprov**: slumpvisa klipp per konto oavsett utfall, cirka 10 per konto för de 39 kontona. Kostnad: nedladdning, plus sållning för 0,3–1 öre per klipp.
4. **Sållningens grova egenskaper förklarar lite.** Det var väntat. Normen behöver egenskaperna på scen- och taktnivå (tid till första takt, var punchlinen ligger, klipprytm) och humorn som eget mått, enligt ägarens svar 2 i inlarning.md.

## Stickprovet (3 nov)

`npm run stickprov -- --hamta` drar 10 slumpvisa klipp per konto för de konton som har sållade klipp. Klippen ska vara 5–90 s, mellan 14 och 900 dagar gamla, och urvalet är reproducerbart (fröet är kontots namn). Sedan sållas de med `bank/sallning.mjs`, numera via AI Studio, med samma modell som tidigare.

- **Utfall:** 333 klipp drogs från 35 konton. 235 är sållade, från 34 konton, och 25 konton har minst 6.
- **Bortfall:**
  - 23 bildposter utan video
  - 80 klipp som stoppades av AI Studios kvot (429); de körs om när kvoten är tillbaka
  - resten fel vid nedladdning
- **Median-`rv` 0,07** (urvalet: 0,36). Selektionen är i stort sett borta.

### Effekter inom konto, stickprovet

Tabellen tar bara med egenskaper som har samma riktning i båda tidshalvorna eller håller när ett konto i taget lämnas utanför. log10: +0,1 betyder ungefär +26 %, och +0,3 ungefär en fördubbling.

| Egenskap | Konton | `rv` räckvidd | `rl` gillanden | `rs` delningar | Läsning |
|---|---|---|---|---|---|
| **Person i bild minst 80 %** | 12 | **+0,28** (75 %, båda halvorna) | +0,06 | +0,13 (båda halvorna) | Tydligast. Klipp som bärs av en person når ungefär 1,9 gånger kontots vanliga räckvidd. |
| **Minst två personer** | 23 | +0,14 (61 %, båda halvorna) | +0,08 (70 %) | +0,19 (båda halvorna) | Samspel mellan personer ger mer räckvidd och fler delningar. |
| **Montage** | 20 | **−0,21** (60 % negativa, båda halvorna) | +0,08 (70 %, båda halvorna) | +0,06 | En konflikt mellan slutmål: färre visningar, men de som ser gillar mer. |
| **Texttungt** | 12 | +0,02 | −0,21 (83 % negativa) | −0,23 (75 % negativa, båda halvorna) | Text som bär budskapet gillas och delas mindre. |
| Matporr och process | 13 | +0,04 | +0,06 (båda halvorna) | +0,11 (båda halvorna) | Svagt positivt för engagemang. |
| Relaterbar sketch | 17 | +0,04 (båda halvorna) | +0,05 | −0,05 | Liten effekt som typ. Det som bär är personerna, inte typetiketten. |
| Kort (högst 15 s), alla klipp | 52 | −0,02 | +0,01 | −0,01 | Längden spelar ingen roll i sig. |

Selektionen hade pressat effekterna, som väntat. Montage gick från −0,06 i urvalet till −0,21 i stickprovet, och personer i bild från +0,11 till +0,28.

### Vad det säger

1. **Personerna bär räckvidden.** Det stämmer med LeTrends arbetsteori, där människor och humor står i förgrunden och verksamheten är fonden. Det är också den första kandidaten till en robust normpunkt: *en person i bild större delen av tiden*.
2. **Slutmålen krockar på riktigt.** Montage kostar räckvidd men ger engagemang. Det är just den vägning per klipp som ägaren beskrev (svar 2 i inlarning.md). Harnessen kan alltså inte optimera ett enda tal.
3. **Typetiketterna är för grova som norm.** Effekterna sitter i egenskaper som personer, montage och text, inte i typen. Normen bör byggas på egenskaper och takter, med typen som villkor.

### Förbehåll

- Etiketterna kommer från Gemini, och är inte validerade mot människa för de här fälten.
- 12–23 konton per egenskap.
- 10 egenskaper gånger 3 mått ger 30 jämförelser, så ett par träffar kan vara slump. Det som står i fetstil håller i båda halvorna.
- Effekterna är samband inom konto, inte orsaker. Ett konto kan till exempel välja montage just för klipp som det redan väntar sig går sämre.

## Hela stickprovet (3 nov, 5 424 klipp)

`node profil/natt.mjs --per-konto 1000 --utan-sok` tog alla behöriga klipp från de 67 kontona som har en lista: 5 690 klipp, varav 5 424 sållades. Resten var bildposter eller borttagna klipp. Körningen tog 42 minuter och kostade 8,60 kr. Hämtningen sker nu i batchar, med 6 yt-dlp-processer samtidigt, och sållningen med 10 anrop samtidigt på originalfilen. Takten är ungefär 0,8 s per klipp, och TikTok spärrade inget. Median-`rv` är 0,01, alltså inget kvar av selektionen.

Sållningen märker vilken video Gemini fick: `video: '480p'` för omkodad (1 873 klipp) och `'original'` för 540p-originalet (resten). Ett parat test på 60 klipp gav samma svar på person i bild minst 80 % i 93 % av fallen och samma typ i 92 %. Bildkvaliteten blir däremot ungefär 0,25 högre med originalet, så jämför den inte rakt över märkningen.

| Egenskap | Konton | `rv` räckvidd | `rl` gillanden | `rs` delningar | Läsning |
|---|---|---|---|---|---|
| **Person i bild minst 80 %** | 58 | **+0,20** (79 %) | +0,07 (76 %) | +0,06 | Håller, nu över 58 konton. Ungefär 1,6 gånger kontots vanliga räckvidd. |
| **Relaterbar sketch** | 56 | **+0,15** (70 %) | +0,08 (82 %) | −0,05 | Med fler klipp syns typen tydligt. Den ger både räckvidd och gillanden. |
| **Minst två personer** | 63 | **+0,11** (71 %) | +0,04 (78 %) | +0,03 | Samspel hjälper, men svagare än en person som bär klippet. |
| Direkt tilltal | 46 | +0,05 | −0,01 | **+0,08** (72 %) | Delas mer. |
| **Matporr och process** | 58 | **−0,14** (21 % positiva) | −0,05 | −0,03 | Ungefär 0,7 gånger räckvidden. Det som visar verksamheten utan människor går sämre. |
| Montage | 63 | −0,07 (40 %) | 0,00 | 0,00 | Svagt negativt. Konflikten med gillanden från 235 klipp försvann. |
| Texttungt | 55 | −0,05 | −0,07 | −0,05 | Svagt negativt på alla mått. |
| Kort (högst 15 s) | 60 | −0,03 | 0,00 | −0,02 | Längden spelar fortfarande ingen roll. |
| Bildspel | 5 | −0,10 | −0,28 | −0,28 | För få konton för att säga något. |

Allt i fetstil har samma tecken i båda tidshalvorna och när ett konto i taget lämnas utanför.

**Vad som ändrades från 235 klipp:** Person i bild krympte från +0,28 till +0,20, vilket är väntat när bruset minskar. Montage gick från −0,21 till −0,07, och plusset för gillanden försvann. Matporr vände från +0,04 till −0,14, och sketch steg från +0,04 till +0,15. Med 12–23 konton per egenskap var de tidigare siffrorna för osäkra för att lita på typens roll. Punkt 2 och 3 under "Vad det säger" ovan behöver därför läsas om: slutmålen krockar inte i montage, och typen säger något när urvalet är stort nog.

**Läsningen nu:** Människor i förgrunden och en relaterbar situation bär räckvidden. När verksamheten visas utan människor, som matporr och process, går det sämre än kontots norm. Det ligger nära LeTrends arbetsteori. Minsta effekt som går att se är nu ungefär 0,04 log10 (+10 %).

## Nästa steg

1. Bredd: 30–50 nya konton av förebildernas sort (`profil/sok.mjs`), så att "pos %" vilar på fler verksamheter.
2. Profilnivån (steg 2 i inlarning.md) på stickprovet: spridning, mix som sekvens och planeringsgrad per konto.
3. Normen v0: egenskaper och takter per typ, med "person i bild" som första normpunkt att pröva. Tittartid från kundernas statistik kommer in som ett fjärde mått när den finns.
