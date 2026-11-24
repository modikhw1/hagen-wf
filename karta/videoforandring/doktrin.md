# LeTrend-doktrinen v5 (4 nov 2026)

Ägarens principer ur Miles-pass 1–6 och experimenten E1–E4 och serietestet, samlade på ett ställe. Det är samma text som alla steg i harnessen v5 läser: `video/format/doktrin.mjs`. Ändras doktrinen, ändras den där.

## Varför en doktrin
Pass 4–5 visade att harnessen v0 mätte fel saker. Luckor gav poäng, kundprofilen var inaktuell, och klippets eget värde räknades inte alls ("inte efter hur bra det är i allmänhet"). Gemini kan bara söka efter det prompten beskriver, så distinktionerna måste stå i prompten. E1 visade att *formuleringen* av en fråga knappt spelar roll. Det som spelar roll är *vilka distinktioner* som finns.

## Fem delar
| Del | Vad den säger | Källa |
|---|---|---|
| LeTrend | Personalen spelar in med telefon, utan handhållning och utan avancerad klippning. Det bästa känns som ett tv-program med personalen, där verksamheten är scenen. | pass 1, 2 |
| Grundvärde | En fristående premiss som tål att göras klumpigt. Värdet ska finnas kvar utan efterarbete. Vändning ersätter karisma. Människor bär idén, och verksamheten är scenen, inte beroendet. Planerat, inte fångat. Visning utan person är "just a pretty picture". Instagram och CapCut är en annan fil. Klippet ska höja taket. Hyllor. | pass 1–3, 5 ("the recommended piece should be strong enough even if it doesn't have editing") |
| Linje | Passform är fortsättning på kundens nuvarande linje ("we're not asking the chicken shop to be improved"). Språket har flera delar: strategi, kantighet, tempo, klippberoende och personens funktion. Det kontot gjort på sistone väger tyngst. Luckor är ett medvetet val för CM. Förlagsavstånd. | pass 4–5 |
| Utfall | Personer, spelad situation, humor och tilltal ger räckvidd. Visning med person ger ×2, med trendljud ×0,58. Återkommande person ger ×1,3–1,7. Frågor till publiken ger kommentarer. | E4, serietestet |
| Anpassning | Originalet är ryggraden. Ange kärnan och det som bär. En sketch som passar rekommenderas som den är. Skriv inte in slumpen. Personalens egen röst. Fokus eller behållare. | pass 4–5 |

## Lager i formatkort v5 (`video/format/v5.mjs`)
- **helhet** kommer först: hur idé, personer, tempo och bild samverkar. Det svarar på ägarens kritik "you're doing it literal again": modellen ska förstå helheten innan den delar upp.
- **grundvärde:**
  - premiss (stark, medel, svag eller ingen)
  - vad som bär
  - *klumpigt*: vad som finns kvar om en ovan anställd gör det stelt. Det är feltoleransen frågad konkret, eftersom E1 visade att begreppet som skala inte gick att mäta.
  - om värdet finns kvar utan efterarbete
  - krok, vändning, om klippet är planerat, om det höjer taket
  - hylla
- **språk:** strategi, kantighet, tempo, klippberoende, person (fokus, behållare, roll), tilltal och plattform.
- **förlaga:** hur bundna bilderna är, vad de är bundna till och vilken verksamhet de ligger längst ifrån.
- **beats:** funktion, om beatet bär (kärna, stöd, fritt) och vad det är bundet till. Anpassningen bygger på dem.
- Kravblocket från v4 behålls.

## Var hör vad: sanning, preferens och nytta (E5 och E6, 4 nov)
Doktrinen är en idé och inget facit. Varje princip prövas mot tre facit som hålls isär:

| | Mäts som | Vad det säger |
|---|---|---|
| **Sanning** | stabilitet mellan körningar och modeller | om lagret är något modellen faktiskt ser |
| **Preferens** | ägarens omdöme | om det är LeTrend enligt ägaren: överförbart och på varumärket |
| **Nytta** | utfall mot kontots egen norm | om det ger räckvidd och gillanden där det görs |

- **Båda:** premiss, att klippet höjer taket, vändning, att idén bär, att det fungerar utan efterarbete, kött och sketchvärld. Här kan harnessen vara sträng.
- **Bara nytta:** karisma och krok. Det fungerar hos avsändaren men flyttar inte, så det hör till kundprofilen och inte till biblioteket.
- **Bara preferens:** fortsättning på kundens linje, och att stöd straffas. Det är varumärkesräcken, som ska vara mjuka och kalibreras mot ägarens och kundens smak, inte mot räckvidd.

## Två mått och en räckeskarta (v6)
Preferens och nytta blandas inte. CM får **LeTrend-värdet** (hör det till LeTrend och passar det kunden) och den **förväntade nyttan** (går det troligen bra) som två tal. Båda bygger på grundvärdet, som replikerats mot utfall i två urval (+0,17 inom konto i E6 och E6-R). Måtten skiljer sig sedan åt:
- LeTrend-värdet lägger till sketchsmaken, det mjuka linjeräcket och tonen.
- Nyttan lägger till eget ljud och person i visning.

En helhetsfråga (E7) verkade först bättre för nyttan men replikerades inte. Räckena har olika grund och därför olika stränghet. Kartan står i [harness.md](harness.md) under "Design v6" och "E6-R".

## Räckeskartan med konfidens (4 nov)
Den slutliga kartan med 95 % konfidensintervall över 1 390 klipp och 95 konton står i [harness.md](harness.md) under "Metaanalys". Kort sammanfattat:
- **Säkert positiva:** utan efterarbete, eget tal, premiss, vändning, krok, sketch och att klippet höjer taket.
- **Säkert negativa:** ingen person bär klippet, Instagram-språk, klippberoende, trendljud, visning och bundna bilder.
- **Noll:** karisma.
- **Gränsfall:** kantighet och tilltal i sig.
