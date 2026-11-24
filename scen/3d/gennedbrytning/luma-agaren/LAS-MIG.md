# Luma-prov: isolerad hel person ur gelato S1

Ett prov, cirka 400 krediter. Frågan: kan modellen skilja kroppens rörelse från kamerans, och anta det som disken skymmer?

Tagningen är vald för att den är svår på rätt sätt: hon står bakom en glasdisk, kameran zoomar in, tippar ned i glassen och upp igen, och hon räcker fram ett smakprov. Det är ditt eget exempel.

## Filer

| Fil | Vad | Används till |
|---|---|---|
| `1_kalla_gelato_S1.mp4` | Källan, 4,94 s, 148 rutor, 1080×1920. De första 0,25 s är bortklippta så att klippet ryms i en femsekundersenhet. | Steg 2, källvideo |
| `2_ruta_000_start.png` | Första rutan. Hon står bakom disken, syns från midjan och upp. | Steg 1, bilden som görs om till guidebild |
| `3_ruta_112_racker_fram.png` | Hon räcker fram smakprovet. | Bara om appen tar fler nyckelbilder |
| `4_ruta_146_slut.png` | Slutet, armen framme vid kameran. | Bara om appen tar fler nyckelbilder |
| `PROMPT.txt` | Två prompter på engelska: steg 1 (guidebild) och steg 2 (video). | Klistras in |
| `utfall/` | Tom. Lägg resultaten här. | |

## Gör så här

1. **Guidebild.** Ladda upp `2_ruta_000_start.png` och klistra in STEP 1 ur `PROMPT.txt`. Kontrollera innan du går vidare: samma kvinna, hel kropp från huvud till fötter, grå bakgrund, tomma händer. Är den fel, rätta den hellre än att gå vidare. Videon ärver felet.
2. **Video.** Modify Video på `1_kalla_gelato_S1.mp4`, guidebilden låst vid ruta 0, klistra in STEP 2.

## Inställningar

- **Upplösning 540p, inte 720p.** 720p kostar enligt prislistan 360 krediter per 5 s och 540p 240. Guidebilden brukar kosta 70–120. 720p riskerar alltså att inte rymmas i 400. Kroppsläsaren klarar 540p. Titta på kostnaden appen visar före varje steg.
- **Rörelseföljsamhet 9 av 9.** Rörelsen är det vi vill ha kvar.
- **Strukturföljsamhet lägre än förra gången, runt 4–5.** Förra klippet hade 9 av 9 eftersom bilden skulle vara kvar. Här byts hela bilden (disk bort, kamera stilla, hel kropp), och 9 tvingar troligen kvar disken och kamerarörelsen. Frågar agenten, välj det den säger passar bäst för "samma rörelse, annan inramning".
- **Låsning: ansikten och kroppar på, poseläge** som förra gången.
- **9:16, samma längd som källan, inget ljud behövs.**

Säger agenten att Modify Video inte kan ändra inramningen: låt den då behålla kameran som den är och bara ta bort disk, rum, text och kundens hand mot grå bakgrund. Det är ett svagare prov men ger ändå svar på vad den antar bakom disken.

## Spara

- Videon som `utfall/isolerad_S1.mp4`, guidebilden som `utfall/guidebild_S1.png`.
- Agentens egen beskrivning av läge, modell och inställningar (som du klistrade in förra gången) i `utfall/luma.txt`, plus krediter per steg och det agenten själv flaggar som avvikelser.

## Vad som mäts sedan

Utföraren läser `utfall/isolerad_S1.mp4` med samma kroppsläsare som originalet (uppdrag 0017, del C–F):

- följde överkroppen originalet, ruta för ruta
- stod kameran still, eller följde kamerarörelsen med in i kroppen
- vobbel och vridning mot dagens läsning
- är ben och fötter rimliga, och står fötterna still
- höll klippet samma längd och takt, eller gled tiden

## Vad du kan se direkt med ögat

- Är det samma kvinna hela klippet?
- Räcker hon fram armen i samma ögonblick som i originalet? Spela dem bredvid varandra.
- Rör sig kameran fast den inte skulle?
- Händer något som inte finns i originalet: extra steg, vändning, klipp, föremål i handen?
