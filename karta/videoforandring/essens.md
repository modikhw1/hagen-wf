# Essens: läsning i lager och geometri (natten 16–17 nov 2026)

Fortsättning på [harness.md](harness.md) och [harness-v6-kort.md](harness-v6-kort.md). Här står vad som prövades när den nya modellvägen (beacon-proxyn mot Vertex) kom på plats, vad som höll och vad som föll. Alla förregistreringar ligger i `data/format/e13` … `e19`, skripten i `video/format/e13*` … `e19*`.

## Riktningen
Ägaren, 17 nov: hypoteserna ska vara abstrakta och inte söka en sanning som bara linjerar det vi redan har. Den bästa modellen ska läsa så mycket den kan innan något planeras runt begränsningar. Profilerna blandar LeTrend-klipp med ihopkastade klipp, och allt är inte en värdig datapunkt. Målet är röda trådar i väldigt många axlar, med ägarens input som begränsad feedback.

Följden för arbetssättet: hypoteser mäts mot materialet självt (undanhållna klipp, utfall som modellen inte får se, konton som hålls undan). Ägarens betyg redovisas som avläsning, och frågan skrivs inte om efter dem.

## Modellvägen
- `LOVABLE_KONTO=beacon` i `video/typer/lovable.mjs` går via appen token-budget-beacon till Vertex. `beaconDelar` tar flera delar per anrop (text och video).
- Vertex tar högst 10 videofiler per anrop. En kunds historik sätts därför ihop till band om fyra klipp med klippnumret inbränt i bilden (`e13-band.mjs`).
- Kvot: Pro och Argon delar ungefär 200 000 indatatokens per minut. Argon tog helt slut 03:00 den 17 nov efter cirka 40 USD loggat och svarade sedan 429 även på en fråga om 39 tokens. Flash 3.8 har aldrig fått 429.
- Argon hänger (ingen första byte på 60 s) när prompten ber om ordagranna citat ur talet.

## E13: passform med historiken som video
Nio kunder med ägarbetyg (50 par). Modellen ser 24 av kundens klipp som video plus kandidatklippet och sätter passform på en skala.

| Läsare | inom kund (42 gemensamma par) |
|---|---|
| Argon, historik som video | +0,63 |
| Formatfamiljer räknade i historiken (text) | +0,56 |
| Pro, historik som video | +0,42 |
| Pro, textprofil | +0,40 |
| Flash 3.8, historik som video | +0,39 |

Förregistrerat utfall: Pro slog inte familjebaslinjen, och video av historiken slog inte en textprofil av samma historik. Argon var inte förregistrerad. Alla läsare var för stränga (medel cirka 2 mot ägarens 3,4) och satte 1 på "aldrig gjort", medan ägaren ger 4–4,5 åt en stark premiss även hos en kund utan sketcher. Skalan skrevs om efter det (b3), och ägaren pekade ut just det som fel väg. b3 avbröts efter 22 par.

## E14: tre lager i stället för en skala
1. **Självet.** Argon läser 20 av kundens klipp som video och beskriver aktören som spänningsfält: polariteter med belägg, motorer, gränser, ankarklipp, trajektoria. Ingen doktrin och ingen skala.
2. **Motorn.** Argon läser ett klipp och skiljer det som får klippet att fungera från ytan (vara, lokal, människor, språk). Ytan förs inte vidare.
3. **Mötet.** Bara text: självet plus ett klipps motor. Vad förstärks, vad bryts, vad offras.

Prov utan ägarbetyg: fyra av varje kunds nyare klipp hölls undan från självet. Av enbart motorn skulle mötet känna igen kundens egna klipp bland de andra kundernas.

- Alla nio kunder, Pro som domare på Argons lager: medel-AUC 0,94 (slump 0,50, tröskel 0,70); Argon som domare gav 0,93 på de fem den hann.
- Ingen av 62 motortexter nämner en vara utanför fältet för yta.
- Avläsning mot ägaren utan skala och utan doktrin (50 par): "hemma" +0,56 inom kund, nära Argon med skala (+0,61) och familjeräkningen (+0,54).


## E15: geometri på den svaga texten
10 911 bankklipp, en mening per klipp från sållningen plus bildtexten, inbäddade lokalt (multilingual-e5-small, `e15_badda.py`). Inga modellanrop.

- Axlar räknade på halva kontona förklarar 0,93 av det andra halvans egna axlar förklarar. Riktningarna är gemensamma.
- Första axeln skiljer spelad scen från matvisning och följer utfall inom konto (+0,07) utan att ha namngetts.
- Närhet till kundens moln mot ägarens passform: +0,41 inom kund, under familjeräkningen.
- Igenkänning av kundens egna klipp: AUC 0,86, men texten ser vara och konto.

## E16: läsning i serie, vägning av klipp
Andra passet: Argon ser samma band igen med självet som lins och ger varje klipp en roll (bärande, stöd, ihopkastat, avstickare). Visningar är borttagna ur underlaget.

- 155 klipp hos åtta kunder: 81 bärande, 39 stöd, 22 ihopkastade, 13 avstickare.
- Utfall inom konto (visningar mot grannarna i tid): bärande ×1,44, stöd ×0,86, ihopkastat ×0,82, avstickare ×0,92. Skillnaden bärande mot ihopkastat håller (p 0,025).
- Rollerna är läsbara: ihopkastat är återanvänt material, mallar och klipp utan vinkel; avstickare är genomarbetade försök i en riktning kontot sedan lämnar.

Tredje passet: Pro skrev om självet ur bara de bärande klippen (HE16b). Det känner igen kundens egna undanhållna klipp sämre än det första (AUC cirka 0,94 → 0,82; inom samma familj 0,91 → 0,82). HE16b förkastas. De undanhållna klippen är ett tvärsnitt av allt kontot lägger upp, även det ihopkastade, så en bild som räknar bort bruset beskriver kontot när det gör något med avsikt, inte allt det publicerar. För igenkänning behövs den första bilden.

## E17: motorrummet
Motorn läst ur biblioteksklippen med Flash 3.8 och inbäddad lokalt. Kriteriet för essens: ytan ska vara borta och värdet finnas kvar. 1 269 klipp från 109 konton (biblioteket och E13-klippen, inga replikeringsklipp).

| | Motor | Svag text | Yta |
|---|---|---|---|
| Kontot gissas ur närmaste granne (slump 0,02) | 0,13 | 0,29 | 0,60 |
| Utfall inom konto, hela konton undanhållna | +0,24 | +0,17 | +0,08 |

- **Håller:** ytan är borta (M1), värdet är kvar och starkare än i den svaga texten (M2), och axlarna är gemensamma: axlar från halva kontona förklarar 0,84 av andra halvans egna (M3).
- **Föll:** ägarens biblioteksval i pass 7 förutsägs i 10 av 19 par (M4; delmängden om 584 klipp gav 14, så talet är instabilt). Flyttbarhet mätt som närhet till andra kontons klipp skiljer ingenting (M6). Att träna bara på klipp med värdet i idén eller personen gav +0,23 mot +0,24 för alla (M7).
- **Utläst:** den tredje gemensamma axeln (+0,17 mot utfall) har i ena änden kunden som klagar och personalen som tar det bokstavligt, den snåla kommentaren om priset som bemöts, den namngivna gästens beställning. De klipp utfallsmodellen förutsäger högst är nästan alla ett möte mellan gäst och personal där något står på spel och som vänds; lägst hamnar verksamheten som presenterar sig själv (nyhet, stämning, trend, musiksynk).

## E18: LeTrend läst ur ägarens ord
Pro läste transkripten från pass 1–5 och skrev LeTrend som aktör i samma form som kunderna. Mötet mellan det självet och klippens motorer prövades på pass 7, som hölls undan.

- 9 av 19 (tröskel 13). Förkastad.
- Självet ur orden säger "abstrakt idé som vem som helst kan göra, låg tröskel". I pass 7 väljer ägaren ofta tvärtom: provsmakningen, den karismatiska kocken, personen som talar.
- Läsningen skilde själv ut vad som var Miles och inte ägarens: kategorierna stomme, huvudnummer, glitter, skalan 1–5 och frågan om idén överlever en vanlig anställd kom från frågorna.

Slutsatsen: det ägaren säger i samtalen och det ägaren väljer är två olika saker. Valet ligger inte heller nära publikens utfall (se E22); det som träffar valet bäst är fortfarande nyttan i harness v6 (16 av 19).

## E19: replikering
1 035 bankklipp utan motor, högst 10 per konto, slumpade utan att utfall lästs. Utfallsmodellen frystes på de 1 253 biblioteksklippen med utfall (`data/format/e17/modell.npz`). 960 av klippen har utfall (104 konton).

- **HE19a håller:** den frusna motormodellen följer utfall inom konto på osedda klipp, +0,14 (p 0,0002).
- **HE19b föll:** den svaga textens modell ger lika mycket, +0,14. Motorns försprång fanns i biblioteket, som är utvalt på idéklipp; i tvärsnittet av allt kontona lägger upp räcker grova skillnader (montage mot människa) långt.
- **HE19c håller:** klipp med värdet i idén eller personen mot bilden, klippningen eller erbjudandet ×1,23 (p 0,0004).
- Ytan är borta i motorn även i tvärsnittet: kontot gissas i 12 % mot 39 % ur svag text.

## E20 och E21: tjänstemötet, prövat på osedda klipp
Hypotesen kom ur ytterklippen i E17 och förregistrerades innan något fält lästs. Flash läste bara motortexten (ingen video, ingen yta) och angav sju fält. Provet är de 960 replikeringsklippen.

| Hypotes (utfall inom konto) | Replikering | p | Bibliotek |
|---|---|---|---|
| HE20a gäst–personal mot tilltal eller ingen relation | ×1,55 | 0,0002 | ×1,46 |
| HE20a samma, utan klipp där insatsen är pengar | ×1,52 | 0,0006 | ×1,42 |
| HE20b tydlig friktion mot ingen | ×1,39 | 0,008 | ×1,53 |
| HE20c gäst–personal mot personal–personal | ×1,61 | 0,098 | ×1,50 |
| HE20d gästens eller personalens sida mot verksamhetens | ×1,21 | 0,004 | ×1,14 |
| friktion inom tilltal | ×1,30 | 0,042 | ×1,39 |
| HE21a eget uttryck mot lånat ljud | ×1,17 | 0,13 | ×1,26 |
| HE21b oviss utgång mot ingen | ×1,31 | 0,002 | ×1,26 |
| oviss mot spelad utgång | ×1,04 | 0,67 | ×1,01 |
| HE21c handling sker mot visas | ×1,25 | 0,001 | ×1,16 |

**HE21d:** de sju fälten, frusna på biblioteket, följer utfall i replikeringen med +0,19. Det är mer än motorrummets +0,14. Motorn rensad från fälten ger +0,05 (tröskel 0,05, alltså på gränsen): sju läsbara fält bär nästan allt det inbäddade rummet ser.

Läsning: det som bär är **människor i ett möte där något står på spel och som vänds**. Mötet över disken är starkast; friktion lyfter även tilltal; något ska hända på riktigt i lokalen. Om utgången är spelad eller äkta spelar ingen roll, bara att det finns en. Lånat ljud mot eget uttryck håller inte på osedda klipp.

## Argon-kontrollen: läsaren spelar roll
Motorerna i stor skala lästes med Flash 3.8 när Argons kvot tog slut. 240 replikeringsklipp lästes om med Argon och fälten lästes ur båda (förregistrerat i `e19/tillagg-argon.json`). På samma 226 klipp, med samma frusna fältvikter:

| | Fält ur Flashs motor | Fält ur Argons motor |
|---|---|---|
| Mot utfall inom konto | +0,09 | +0,25 |

Skillnad +0,16, 95 % bootstrap [+0,07, +0,26]. Fälten stämmer överens i 83 % (relation) till 93 % (utgång) av fallen; det är i klippen där läsarna skiljer sig som Argon ser rätt. Alla tal i E17–E22 är alltså lästa med den svagare läsaren och är troligen underskattningar. Resten av replikeringsklippen läses med Argon (HA3).

## E23: register och temperatur
Ägaren (17 nov): Geminis texter är skrivna som copy och normaliserar temat. 400 replikeringsklipp lästes om med en prompt för vardagligt, bokstavligt språk vid tre temperaturer. A är motorn.

| Läsning | Copyord per 100 | Kontot gissas | Utfall inom konto |
|---|---|---|---|
| A, motorn (copy-register) | 4,2 | 0,09 | +0,15 |
| B, vardagligt, temperatur 0,1 | 0,2 | 0,25 | +0,09 |
| C, vardagligt, temperatur 1,0 | 0,2 | 0,26 | +0,13 |
| D, vardagligt, temperatur 1,8 | 0,2 | 0,24 | +0,11 |
| A och B tillsammans | | | +0,19 |

- Copyn är inte bara brus: motorns tolkning ordnar klippen efter något publiken svarar på. Den bokstavliga läsningen bär något annat, och tillsammans är de bäst.
- Den bokstavliga texten tar med ytan (ortnamn, märken, kläder), så kontot går att gissa. Det är därför den ensam är svagare.
- Högre temperatur hjälper den bokstavliga läsningen något. Spridningen mellan temperaturerna säger inget om utfall.
- Skattad ansträngning följer inte utfall (p 0,19).
- Ägarens invändning: att be om vardagligt språk ger samma normalisering med andra ord. Det följs upp i E26, där copyn får ett eget utlopp och avståndet mäts.

## E26 och E27: copyn får ett eget utlopp
Ägaren (17 nov): Gemini komprimerar alltid till samma nivå, som en kompressor. Copy är rätt när innehållet förtjänar den, så det neutrala återberättandet behöver huvudrum. I E26 fick modellen i samma anrop först återberätta klippet som en recensent, sedan skriva en säljtext och till sist ange hur mycket av säljtexten klippet håller för.

- Huvudrummet som mått bar ingenting: täckningen (+0,05) och avståndet mellan texterna (−0,07) följer inte utfall. Avståndet speglar mest genren: produktvisningar ligger nära sin säljtext, sketcher långt ifrån.
- Själva greppet fungerade på ett annat sätt (utforskande, samma 400 klipp som E23):

| Text | Utfall inom konto |
|---|---|
| A, motorn (copy-register) | +0,15 |
| B, ombedd att vara vardaglig | +0,09 |
| **N, återberättelse när copyn hade ett eget utlopp** | **+0,22** |
| S, säljtexten (utloppet) | +0,00 |

B och N är båda neutrala texter, men bara N blev bättre. Tolkningen var att copyn i N hade någonstans att ta vägen.

**E27, replikeringen: N håller inte.** 509 av 1 676 klipp som inte använts hann läsas innan Flash-kvoten tog slut:

| Text | E26 (400 klipp, där fyndet gjordes) | E27 (509 nya klipp) |
|---|---|---|
| A, motorn | +0,15 | +0,07 |
| N, återberättelse | +0,22 | **+0,01** |
| S, säljtext | 0,00 | +0,09 |

N:s +0,22 var en egenskap hos de 400 klippen och inte hos läsningen. Säljtexten och återberättelsen byter till och med plats. Med spridningen ±0,02–0,03 över omgångar är skillnaderna mellan texterna på nya klipp små. Ingen av de fria texterna bär stabilt mer än cirka +0,1 inom konto. Det som replikerat är de sju fälten (+0,19, E21) och Argons motor (+0,25).

## E28: tre lager (teknisk, semantisk-teknisk, semantisk)
Ägaren (17 nov): en total bild håller även klippning, produktionsvärde, tempo, manus och hur uppmärksamheten hålls scen för scen, i en serie körningar snarare än en prompt.

**Teknisk mening, lokalt utan modell** (`e28-tek.mjs`, alla 2 213 klipp med utfall):

| Mått | rho mot utfall inom konto |
|---|---|
| Längd | +0,11 |
| Pauser i ljudet | +0,09 |
| Ljudets dynamik (LRA) | +0,09 |
| Längsta skottet | +0,08 |
| Ljudnivå | −0,07 |
| Andel tid med ljud | −0,06 |
| Klipptakt | −0,03 |
| Tid till första klipp, byten de första 3 s | 0,00 |

Lagret som helhet ger +0,09 med konton undanhållna, och +0,10 när det fryses på biblioteket och prövas på replikeringen. Tal med pauser och varierande ljud går bra, konstant hög musik sämre (samma bild som E4:s trendljud ×0,58). Klipptakt och tidiga klipp säger ingenting.

**Semantisk-teknisk läsning** (`e28.mjs`, Flash, scen för scen; 327 av 400 klipp innan kön stoppades av minnesbrist):

| Mått | Medel | rho inom konto | p |
|---|---|---|---|
| Repliker totalt | 5,8 | **+0,18** | 0,001 |
| Repliker per sekund | 0,24 | +0,18 | 0,003 |
| Manus: inget behövs | 43 % | **−0,16** | 0,007 |
| Manus: skrivet | 35 % | +0,10 | 0,12 |
| Scener som stannar för länge (HE28b, −) | 3 % | −0,12 | 0,056 |
| Sekund då premissen är klar (HE28c, −) | 1,7 | +0,01 | 0,85 |
| Svårighet att spela in 1–5 (HE28d) | 2,0 | +0,09 | 0,20 |

- HE28b pekar åt väntat håll men når inte gränsen. HE28c och HE28d faller: när premissen blir klar och hur svårt klippet är att spela in säger ingenting om utfall.
- **Repliker är det som bar längden.** Längd och repliker korrelerar 0,62. Med längden hållen konstant ligger repliker kvar på +0,15. Med replikerna hållna konstant faller längden till +0,02. Det är inte längre klipp som går bra, utan klipp där något sägs.
- Det hänger ihop med mötet: ett klipp utan manus (en visning, en stämning) är ett klipp där ingen möter någon.

**Lagren tillsammans** (samma 327 klipp, konton undanhållna):

| | rho |
|---|---|
| Tekniskt lager | +0,01 |
| Semantisk-tekniskt lager | +0,13 |
| Sju fält | +0,08 |
| **N, återberättelse med säljutlopp** | **+0,22** |
| N + fält + semantisk-tekniskt (rangsumma) | +0,23 |
| Alla fyra | +0,18 |

Obs: de 327 klippen är en del av E23:s 400, alltså samma klipp där N först gav +0,22. N replikerade inte i E27, så N:s plats överst här är inte oberoende. Repliker och manus är nya mått som inte valts ut på de här klippen.

HE28e faller: lagren lägger inget till N. Återberättelsen bär redan replikerna, mötet och friktionen, och de tekniska måtten späder ut den. På 327 klipp är det tekniska lagret noll; på alla 2 213 var det +0,09, så det finns men är svagt och överlappar med det N läser.

## E30: att något sägs, mätt utan modell
E28 visade att Flashs replikantal bar det längden såg ut att bära, men på samma klipp där andra fynd gjorts. E30 mäter tal lokalt med en röstdetektor (Silero VAD, `e30_tal.py`) på alla 2 213 klipp med utfall. Förregistrering i `data/format/e30/forregistrering.json`.

| Mått, rho mot utfall inom konto | Alla | Bibliotek (1 253) | Replikering (960) |
|---|---|---|---|
| **HE30a** antal talsegment | **+0,15** | +0,17 | +0,11 |
| **HE30b** talsegment, längd konstant | **+0,11** | +0,13 | +0,08 |
| Andel tid med tal | +0,11 | +0,11 | +0,11 |
| Sekund för första tal | −0,10 | −0,10 | −0,10 |
| Längd | +0,11 | +0,11 | +0,11 |
| Längd, talsegment konstant | +0,05 | +0,03 | +0,08 |

- **HE30c:** klipp utan tal (31 %, oftast musik eller lånat ljud) ligger på ×0,81 mot övriga, p 0,0002.
- **HE30d:** röstdetektorn följer Flashs replikantal (rho 0,61). Klipp som Flash säger saknar manus har median 0 % tal, övriga 78 %.
- Alla fyra håller, i båda halvorna, p < 0,05.

Det är det första fyndet som håller utan att en språkmodell läser något. Det säger samma sak som mötet i E20/E21: någon säger något till någon. Det går också att mäta billigt vid ingest. Tal tidigt är bättre än tal sent. Längd bär nästan bara genom att längre klipp har mer tal.

**E31: tal och fälten tillsammans** (frysta på biblioteket, prövade på replikeringen, 960 klipp):

| | Bibliotek | Replikering |
|---|---|---|
| Sju fält (Flash) | +0,26 | **+0,20** |
| Tal, tre mått (utan modell) | +0,17 | +0,14 |
| Fält + tal | +0,29 | +0,22 |

- HE31b faller: tal lägger +0,016 till fälten, och intervallet över konton går från −0,01 till +0,04.
- HE31a missar knappt (p 0,058).
- HE31c håller: fältpoäng och tal korrelerar bara 0,25. Ändå finns den del av talet som följer utfall redan i fälten.
- Oviss utgång har median 5 talsegment mot 1; det är där talet och mötet sammanfaller tydligast.

Slutsats: talet är en billig ersättare som ger ungefär två tredjedelar av fältens värde utan modellanrop. Fälten är fortfarande den bästa läsningen.

Utforskande (`e31_modellfri.py`): de tekniska måtten lägger inget till talet på replikeringen (tal +0,14, tekniskt + tal +0,135). Den högsta femtedelen ligger ändå på ×1,21 inom konto, och resten ligger mellan ×0,78 och ×0,94. Utan modell går alltså toppen att skilja ut, men inte ordningen i mitten.

## E22: ägaren mot fälten (avläsning)
Fältmodellen frystes på alla 2 213 klipp med utfall. Vikter, log visningar inom konto: tydlig friktion +0,39, insats pengar +0,34, gäst–personal +0,27, tilltal +0,23, oviss utgång +0,22, mild friktion +0,22, eget uttryck +0,20.

- Pass 7 (ägarens biblioteksval): 11 av 19. Nyttan gav 16, grundvärdet 10.
- Pass 4–6 (passform inom kund): +0,34, under familjeräkningen (+0,54) och läsningen i lager (+0,56).

Det som går bra hos publiken och det ägaren väljer till biblioteket överlappar, men de är inte samma sak. Bibliotekets kärna innehåller personalsketcher utan friktion till lånat ljud (kollegor som blir bästa vänner, en synkroniserad dans i trånga utrymmen), som fälten placerar lägst. Biblioteket har också klipp på hyllan "ute" som fälten placerar högst (servitören som tjuvlyssnar när gästen hyllar stället i telefon). Tio sådana par ligger i `data/format/e22/urval-till-agaren.json` och är de klipp där ägarens svar ger mest information.

## E32: försök att fälla tjänstemötet, och oanvänd data (17 nov kväll, inga modellanrop)
Förregistrerat i `data/format/e32/forregistrering.json`, skript `video/format/e32_analys.py` och `e32b_kontroll.py` (kontrollerna efteråt är utforskande). Utfallet återskapades ur `data/bank/*/lista.json` (r 0,998 mot lagrat u; 18 % av klippen avviker > 0,1 eftersom listorna hämtats om). Fältpoängen fryst på biblioteket ger +0,21 på replikeringen (+0,205 med lagrat u).

| Hypotes | Resultat | |
|---|---|---|
| HE32a samma riktning i de flesta konton | 60 av 91 konton positiva (66 %, p 0,002), median +0,21; ett konto bort ger +0,20 till +0,22 | håller |
| HE32b andra definitioner av utfallet | ±5 +0,21, ±20 +0,23, medel +0,21, hela kontots median +0,26, utan klipp yngre än 21 dagar +0,21 | håller |
| HE32c friktion ger fler kommentarer | tvärtom: ×0,84 kommentarer per visning med u konstant | faller |
| HE32d gäst–personal ger fler delningar | tvärtom: ×0,78 delningar per visning med u konstant | faller |
| HE32e hashtags negativt | +0,01 | faller |
| HE32f seriemarkör positivt | ×0,84, n 59 | faller |
| HE32g erbjudandeord negativt | tvärtom: ×1,18 (p 0,0002) | faller |
| HE32h fråga eller premiss i bildtexten | ×1,05 (p 0,047) | håller knappt, för litet för att bära |

Utforskande:
- **Dos:** femtedelarna av fältpoängen ger ×0,68, ×0,84, ×1,01, ×1,03, ×1,24. Mest av värdet ligger i att undvika botten (verksamheten som presenterar sig själv).
- **Var det fallerar:** rho per konto följer hur mycket kontot varierar i innehåll (+0,40), inte kontots storlek (−0,09). Där kontot provar både möte och annat vinner mötet; enhetliga konton ger inget att skilja.
- **Två sorters respons:** mötesklipp får fler visningar och fler gillanden per visning (×1,09) men färre kommentarer (×0,76) och delningar (×0,78) per visning. Mötet ses och gillas; samtal och spridning drivs av något annat.
- **Pris i bildtexten:** siffra + kr ×1,41 (n 180), % ×1,40, gratis ×1,38, öppnar ×1,57; meny, nyhet och boka ligger kring ×1. Ett konkret pris i bildtexten, ofta som fråga ("är det för dyrt med 40 kr?"). Efterhand, inte förregistrerat.
- **Upprepning dementerad:** mötesklipp efter ett annat mötesklipp såg ut att tappa (×1,05 mot ×1,48), men med hela kontots median krymper skillnaden till ×1,11 och interaktionen över 744 par ger p 0,13. Det var grannmedianen som straffar klipp i en följd av starka klipp.
- **Ägarens 19 val i pass 7** träffas 11 av 19 av utfall, gillanden, kommentarer och delningar var för sig, alltså slumpnivå. Ägarens val går inte att läsa ur någon publiksiffra.
- **Brus:** u mellan på varandra följande klipp korrelerar +0,04. Utfallet är nästan rent per klipp och har sd ×3,2.

## E33: vad driver kommentarer och delningar (17 nov kväll, inga modellanrop)
Förregistrerat i `data/format/e33/forregistrering.json`, skript `video/format/e33_analys.py`. 12 976 bankklipp. Takt per visning residualiserad på u inom konto (kommentarstakten faller med räckvidden, lutning −0,36).

| Hypotes | u (visningar) | gillanden | kommentarer | delningar | |
|---|---|---|---|---|---|
| HE33a fråga '?' (n 2 050) | ×1,04 | ×1,01 | **×1,07** | ×0,97 | håller (litet) |
| HE33b uppmaning att kommentera (n 474) | ×1,08 | ×1,03 | **×1,31** | ×0,96 | håller |
| HE33c tagga/skicka (n 352) | ×0,96 | ×0,99 | ×1,29 | **×1,63** | håller |
| HE33d pris (n 350) | ×1,41 | ×0,94 | **×1,14** | ×1,15 | håller |
| HE33e talsegment sänker kommentarer | rho +0,13 | +0,10 | +0,03 | +0,03 | faller (neutralt) |
| HE33f tävling (kontroll, n 185) | ×0,90 | ×1,16 | **×3,62** | ×1,13 | håller: måttet fångar konstgjorda kommentarer |

Utforskande, fälten: tilltal till publiken ger ×0,97 i visningar men ×1,27 kommentarer och ×1,22 delningar; "berättas" ×1,26 och ×1,16. Gäst–personal, handling som sker och personalens sida ger tvärtom fler visningar och färre kommentarer och delningar. Insats pengar är det enda fält som lyfter alla tre (×1,33, ×1,15, ×1,16). Ordutforskningen (upptäckt i halva kontona, prövad i andra) replikerar svagt (rho +0,23 för kommentarer, +0,15 för delningar); stabila ord för delningar är öppnar, vän, tagga, börjar.

## E34: bildtextfynden på osedda klipp (17 nov kväll)
Förregistrerat i `data/format/e34/forregistrering.json` innan något hämtats. Nya listor via `video/format/e34-listor.mjs` till `data/format/e34/listor/` (data/bank orört). Osedda: 3 593 äldre klipp bortom förra hämtningens 200–300 och 192 nya (minst 5 dagar gamla), 58 konton. Id i `e34/osedda.json`. Skript `e34_analys.py`.

| Hypotes | Resultat | |
|---|---|---|
| HE34a pris ger fler visningar | ×1,04 (n 53, p 0,82) | **faller**: E32:s ×1,41 replikerade inte |
| HE34b pris ger fler delningar | ×1,26 (p 0,046) | håller knappt |
| HE34c tagga/skicka ger fler delningar | ×1,36 (p 0,0002) | håller |
| HE34d uppmaning ger fler kommentarer | ×1,24 (p 0,001) | håller |
| HE34e inbjudan i tid ger fler delningar | ×1,08 (p 0,41) | faller |
| HE34f fråga ger fler kommentarer | ×1,05 (p 0,10) | faller |
| kontroll tävling | kommentarer ×1,77 | |
| HE34g talsegment följer u | rho **+0,128** (p 0,001, 744 klipp, 58 konton) | **håller** |

HE34g: urval högst 40 osedda klipp per konto (frö 34, `e34/ljud-urval.json`, taket höjt från 12 innan något analyserats), ljud via `e34-ljud.mjs` till `~/Downloads/letrend-e34`, Silero VAD som i E30 (`e34_tal.py`, `e34/tal.jsonl`), analys `e34g_analys.py`. 95 % över konton +0,06 till +0,20. Med längden konstant +0,12; längd med talet konstant +0,07. Klipp utan tal 36 %, ×0,86. Äldre klipp +0,12, nya +0,20. Talet lyfter inte kommentarer eller delningar per visning (−0,04, −0,03). **Kärnfyndet, att det sägs något i ett möte, håller nu på tre oberoende uppsättningar: biblioteket, replikeringen och 744 klipp som aldrig fanns i banken.**

## E36: kommer publiken tillbaka? (inga modellanrop)
Förregistrerat i `data/format/e36/forregistrering.json`, skript `e36_analys.py`. Efterverkan = median log visningar för de 5 följande klippen minus de 5 föregående, inom konto.
- **HE36a, kontrollen, faller:** klippets eget utfall följer inte efterverkan (rho +0,005, n 11 936). Ett klipp som går bra lyfter inte kontots följande klipp. Det stämmer med att u mellan på varandra följande klipp bara korrelerar +0,04 (E32).
- HE36b–e (fält, tal, delningar, kommentarer) faller därmed också och går inte att tolka; kommentarer och gillanden per visning ligger svagt negativt (−0,03, −0,04).
- **Läsning:** för de här kontona är varje klipp ett eget dragningsförsök i flödet. Kontotillväxt går inte att läsa ur visningarna på följande klipp; följarsiffror över tid skulle behövas.

## E38: publiceringstakt (inga modellanrop)
Förregistrerat i `data/format/e38/forregistrering.json`, skript `e38_analys.py`. Upptäckt på banken (12 871), replikering på de osedda klippen ur E34 (3 768).

| | Bank | Osedda | |
|---|---|---|---|
| HE38a längre paus före ger mer | +0,015 (p 0,10) | +0,034 (p 0,04) | faller |
| HE38b samma dag som föregående | ×0,89 (p 0,001) | ×0,83 (p 0,0002) | **håller** |
| HE38c dagar till nästa saknar koppling | +0,021 | +0,040 | faller: klipp som följs av ett klipp samma dag tappar också |
| Glapp 0 / 1 / 2–3 / 4–7 / 8+ dagar | ×0,90 / 1,01 / 1,01 / 1,00 / 1,02 | ×0,85 / 1,04 / 1,02 / 0,98 / 1,06 | |
| Veckodag | ×0,96–1,04 | ×0,96–1,05 | inget |

**Regel för CM:** två klipp samma dag tar räckvidd från varandra. Från en dag och uppåt spelar takten ingen roll för det enskilda klippet, och veckodagen spelar ingen roll.

## E37: syns mötet i bilden? (inga modellanrop)
Förregistrerat i `data/format/e37/forregistrering.json`. YOLOv8n (personer, 6 rutor per klipp) på 2 605 klipp (`e37_personer.py`, `e37/personer.jsonl`), analys `e37_analys.py`.

| | Replikering | Bibliotek | |
|---|---|---|---|
| HE37a andel rutor med minst två personer | +0,085 (p 0,014) | +0,130 | håller |
| HE37b ingen person i någon ruta | ×0,93 (p 0,54, n 128) | ×0,57 (n 79) | faller |
| HE37c giltighet: skiljer möte från övrigt | AUC 0,71 | | håller |
| HE37d minst två personer, med talet konstant | +0,075 (p 0,027) | +0,120 | håller |
| andel rutor med minst en person (utforskande) | +0,122 | +0,118 | |

Läsning: bilden ger en egen, oberoende motsvarighet till mötet som lägger till talet. En människa i bild över huvud taget bär mer än kravet på två.

## E39: lokal ingestpoäng med två axlar (inga modellanrop)
Förregistrerat i `data/format/e39/forregistrering.json`, skript `e39_analys.py`. Tal, längd, samma dag och bildtextens uppmaningar; fryst på 2 605 bankklipp, prövad på 744 osedda.
- HE39a räckvidd: +0,10 (95 % −0,01 till +0,20), mindre än talsegment ensamt (+0,13). **Faller.**
- HE39b respons: +0,06 (−0,01 till +0,13). **Faller.**
- HE39c två axlar: poängen korrelerar 0,61. **Faller**: båda lutar sig på talandel och längd.
- **Läsning:** lokalt är talsegment den enda robusta signalen; att lägga till fler lokala mått överanpassar. Uppmaningar i bildtexten är för sällsynta för att bära en responsaxel. Tilltalet måste läsas ur klippet (fältet avsändare–publik gav kommentarer ×1,27 och delningar ×1,22 i E33), vilket kräver en läsare.

Läsning: **två motorer.** Visningarna bärs av mötet (människor, något står på spel, handling som sker). Kommentarer och delningar per visning bärs av att avsändaren vänder sig till publiken och ber om något (kommentera, tagga, skicka), och lite av pengar. Mötet ses men delas inte; tilltalet delas men ses inte mer. Det enda som syntes i bildtexten för visningar (pris) var en egenskap hos urvalet.

## E35: talarbyten (inga modellanrop)
Förregistrerat i `data/format/e35/forregistrering.json`. VAD plus WavLM-SV (cosinus 0,86), skript `e35_talare.py` och `e35_analys.py`.
- **Avvikelse:** systemet stoppade mätningen på grund av minnesbrist vid 3 146 av cirka 3 450 klipp. Analysen kördes på det som fanns, utan omstart. Med utfall: replikering 871, osedda 665, bibliotek 1 517.

| Hypotes | Resultat | |
|---|---|---|
| HE35a: byten med talsegment konstant | +0,017 (p 0,54) | faller |
| HE35b: monolog mot dialog | kommentarer ×1,11 (p 0,14), delningar ×0,94 | faller |
| HE35c: byten skiljer möte från övrigt | AUC 0,61 | håller (knappt) |
| HE35d: dialog mot monolog på u | ×0,88 | faller |

- Utan talet konstant följer bytena u (+0,10 till +0,15), men det försvinner när talet hålls konstant. Samma bild vid tröskel 0,80 och 0,90. Vid 0,80 når monolog kommentarer ×1,15 (p 0,046), men den är inte förregistrerad och bara en av tre trösklar.
- **Läsning:** vem som talar och hur ofta det byts lägger inget till *att* något sägs.

## E40: tal och personer i bild på osedda klipp (inga modellanrop)
Förregistrerat i `data/format/e40/forregistrering.json`. Video i lägsta h264-kvalitet, YOLOv8n som i E37, skript `e40_analys.py`.
- **Avvikelse:** 712 av 744 videor hämtades. Personräkningen stoppades på grund av minnesbrist vid 601. Prövat på 601 osedda klipp från 46 konton; anpassat på 2 605 bankklipp.

| Hypotes | Resultat | |
|---|---|---|
| HE40a: kombinerad poäng mot tal ensamt | +0,160 mot +0,179, skillnad −0,019 (95 % −0,08 till +0,04) | faller |
| HE40b: andel ≥2 personer med talet konstant | +0,052 (p 0,22) | faller |
| HE40c: andel ≥1 person | +0,032 (p 0,45) | faller |

- Andel ≥2 personer ensam ger +0,08 men lägger inget till talet. I 11 % av klippen finns ingen person i någon ruta.
- **Läsning:** E37:s bildsignal håller inte på osedda klipp. Talet bär det som bilden såg.

## Lokalt tak (17 nov kväll)
Efter E32–E40 utan modellanrop:
- **Bevisat och lokalt:** talsegment (+0,13 på osedda), inga två klipp samma dag (×0,83), uppmaning att kommentera eller tagga i bildtexten (×1,24 respektive ×1,36 på respons).
- **Faller lokalt:**
  - talarbyten
  - personer i bild
  - en tvåaxlig poäng
  - eftereffekter
  - takt och veckodag
  - bildtextens frågetecken och tidsord
- **Nästa värde kräver en läsare:**
  1. HA3: Argon-fält på resten av replikeringen. Argon gav +0,25 mot Flash +0,09 på 240 klipp.
  2. Fältet avsändare–publik läst ur klippet, som responsaxel. E39 visade att bildtexten inte räcker.
- Ägarens svar på paren i `e22/urval-till-agaren.json` är fortfarande den enda vägen till smakaxeln.

## Vad som står
1. **Läsning i lager fungerar.** En aktör läst som spänningsfält känner igen sina egna undanhållna klipp på enbart motorn: AUC 0,94 över nio kunder, 0,88 inom samma formatfamilj. Det håller oberoende av vilken modell som dömer.
2. **Allt är inte en datapunkt, och det går att läsa.** Bärande klipp ×1,44 mot ihopkastade ×0,82 i utfall, utan att modellen sett visningar.
3. **Motorn tar bort ytan och behåller värdet.** I biblioteket bär den mer än den svaga texten; i tvärsnittet lika mycket.
4. **Röd tråd, replikerad:** människor i ett möte där något står på spel och vänds. Sju fält lästa ur motorn bär den på osedda klipp (+0,19) och slår det inbäddade rummet.
5. **Ägarens ord, ägarens val och publikens utfall är tre olika saker.** LeTrend läst ur transkripten träffar 9 av 19 av ägarens val; fälten 11 av 19; nyttan 16 av 19. En del av det som kodats som ägarens begrepp kom från Miles frågor.
6. **Fri text tar inte mer än cirka +0,1, vilken stil den än har.** Återberättelse med säljutlopp såg ut som ett genombrott (+0,22) men replikerade inte (+0,01 på 509 nya klipp). Det som håller är strukturerade frågor om mötet (sju fält) och en starkare läsare (Argon).
7. **Om något sägs.** Repliker (+0,18) och inget manus (−0,16) är de enda scenvisa mått som bär. E30 replikerade det utan modell på alla 2 213 klipp: talsegment +0,15, klipp utan tal ×0,81, tidigt tal bättre. Det förklarar varför längd såg ut att bära. Det är samma sak som mötet, sett från ett annat håll.

## Kvar
- 17 nov, eftermiddag: alla fyra köer stoppades av systemet på grund av minnesbrist medan sessionen var ledig. Inget startas om utan ägarens ord. Läget då:
  - HA3 (Argon-motorer för resten av replikeringen): 992 motorer finns, fälten för 240.
  - E27 (N på 1 676 nya klipp): 503 klara.
  - E24 (neutral logg): läsning 1 376 av 400, läsning 2 och 3 inte påbörjade.
  - E28 semantisk-teknisk: 327 av 400, analyserad ovan.
- Sedan cirka 14:00 svarar Vertex 429 på Flash, efter cirka 5 500 anrop under dagen. Argon släpper igenom enstaka anrop. En prövning var femte minut ser när kvoten öppnar. E29 (Argons återberättelse, förregistrerad) har 6 av 400 klipp.
- När Flash öppnar: E27 klart (resten av replikeringen och biblioteket) och HA3-fälten. Kör en kö i taget, i förgrunden.
- E25 (svarta poster) avbröts efter ägarens förtydligande.
- Ägarens svar på klippen i `e22/urval-till-agaren.json`.
