---
id: 0018
titel: Tillägg till 0017: ägarens GPT-bilder höll (bara storleken skiljer), och trestegsplanen rum, person, kombination
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0017
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Läs detta så snart du ser det, också mitt i 0017. Är 0017 inte förbi del D: väv in punkterna 1–3 där och redovisa allt i svar 0017, och skriv ett kort svar 0018 som pekar dit. Är 0017 klart: gör detta som eget uppdrag.

## Mål
Ägarens två bilder används som lager 1 och lager 2 för gelato S1, storleken rättas lokalt, och trestegsplanen är provad hela vägen på den tagningen: rummet ur den tomma bilden och animerat med kameran, kvinnan läst och animerad, och de två kombinerade.

## Bakgrund
Ägaren körde AB-upplägget (`scen/3d/gennedbrytning/luma-agaren/gpt/PROMPT-AB.txt`) i vanliga GPT Image, utanför Luma. Resultat i `scen/3d/gennedbrytning/luma-agaren/gpt/`:
- `Modern gelateria med gelatodisk.png` (941×1672): **tom scen**. Disken, glasen, skyltarna och inramningen ligger kvar där originalet har dem. Det bakom henne (kaffemaskin, bänk) är påhittat och rimligt.
- `b4206629-….png` (941×1672): **isolerad person**. Samma kvinna, grå yta, hel kropp, armarna sträckta nedåt som i originalet, huvudet lutat, märket på tröjan kvar. Hon står ungefär rätt i sidled men är **cirka 1,5–1,7 gånger större** än i originalet. Ägarens bedömning: bara storleken skiljer.

Det är ett bättre utfall än Luma-agentens två försök, och det bekräftar principerna 1 och 2 i `STRATEGI.md`. Ägaren har en Codex-plan där sådana bilder kan genereras, så bildstegen behöver inte kosta per bild. Video är det som kostar.

Ägarens plan i tre steg:
1. **Rummet.** Bilden utan kvinnan bryts ned till block och objekt i rum, och animeras (kamerans rörelse spelas mot blocken).
2. **Kvinnan.** Hon analyseras för sig och animeras.
3. **Kombination.**

## Att göra
1. **Rätta storleken lokalt, inte med prompt.** Passa den isolerade personen mot originalets personmask (`scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1/masker.npy`, ruta 7) med likformig skala och förskjutning, på det som syns i båda: huvud, axlar, överkropp ned till diskkanten. Lägg resultatet på grå duk i originalets format. Redovisa skala, förskjutning och överlapp efter passningen. Princip 3 (lås positionen) blir då ett efterbehandlingssteg som alltid körs, oavsett vad bildmodellen gjorde. Skriv in det i `STRATEGI.md`.
2. **Jämför med det du själv tagit fram i 0017 del B och C** (fal). Vilken tom scen ligger närmast originalet utanför personmasken, och vilken isolerad person håller pose och identitet bäst efter passningen? Använd den bästa av varje vidare.
3. **Nyckelbilder som stillbilder, utan videomodell.** Kör kroppsläsaren direkt på den isolerade, passade bilden för ruta 0. Jämför med dagens läsning av samma ruta ur originalet: överkroppens leder (ska stämma), och höft, ben och fötter (som nu syns). Om det håller: detta är den billigaste formen av "hjärnan", och den kan upprepas för rutorna 112 och 146 om ägaren genererar dem. Skriv exakt vilka rutor och vilka indata ägaren i så fall ska köra genom AB-prompten, i `luma-agaren/gpt/NASTA-BILDER.md`.
4. **Rummet ur den tomma bilden.** Kör segmenteraren (`scen/3d/ingest/modal_segmentera.py`) på tom scen och på originalets ruta, med samma elementnamn. Vilka kanter på disken och bänken bakom syns nu som personen skymde, och ligger de gemensamma kanterna kvar på samma ställe (promille)? Lägg sedan den tomma bilden som bakgrundsplatta bakom förvärldens block i en stillbild genom slutkameran: ligger blocken där bilden har disken?
5. **Animera rummet.** Kameran i källan zoomar och tippar. Rendera förvärldens rum med tagningens lösta kamerabana, och säg vad som saknas för att det ska följa originalet (kamerabanan för rörlig kamera, se `kontrakt/bildkamera.py`).
6. **Kombination.** Lägg den lästa kroppen (ur 0017 del F om video finns, annars ur punkt 3 för ruta 0) i rummet, och rendera bredvid originalet.

## Gränser
- Som 0017: bara nya filer under `scen/3d/gennedbrytning/`, samma kostnadstak (det gemensamma taket 6,00 dollar gäller båda uppdragen tillsammans), `luma-agaren/steg1/`, `utfall/` och `gpt/` är ägarens och ändras inte (nya filer bredvid går bra, som `NASTA-BILDER.md`).
- Generera inga GPT-bilder själv. Behövs fler: beskriv dem i `NASTA-BILDER.md`, så kör ägaren dem.
- Det bakom kvinnan i den tomma scenen är påhittat. Det får bli underlag för block, men ska märkas `antagen`.

## Klart när
- Passad isolerad person som bild, med skala, förskjutning och överlapp.
- Tabellen ur punkt 2.
- Kroppsläsning av ruta 0 ur isolerad bild mot original, med tal för överkropp och en beskrivning av underkroppen.
- Segmenterarens rutor i tom scen mot originalet.
- Stillbild eller film med rum och person kombinerade bredvid originalet, med sökväg.
- `NASTA-BILDER.md` och tillägg i `STRATEGI.md`.
- Tre rader: vad i trestegsplanen fungerar i dag, vad som saknas, och om stillbilder vid nyckelrutor kan ersätta videomodellen för kroppen.

## Leveransform
`delegat/svar/0018-agarens-gpt-bilder-och-trestegsplanen.md`, högst cirka 60 rader, eller en pekare till svar 0017 om det vävdes in där.
