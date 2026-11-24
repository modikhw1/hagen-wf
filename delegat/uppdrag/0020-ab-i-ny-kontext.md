---
id: 0020
titel: Rättelse till 0019: steg B körs i ny kontext med exakt två bilder
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov 00:30
datum: 2026-11-13
följer: 0019
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Läs genast, mitt i 0019. Redovisa i svar 0019; här räcker en pekare.

## Mål
Steg B (isolerad person) ger en bild genom Codex, på samma sätt som det gav en bild för ägaren.

## Bakgrund
Ägaren beskriver vad som faktiskt fungerade i GPT (`scen/3d/gennedbrytning/luma-agaren/gpt/`):
- Tre **skilda körningar, var och en i ny kontext**. Det är enligt ägaren det viktigaste.
- Körning 1: bara originalbilden, "ta bort kvinnan".
- Körning 2: **bara två bilder**, originalet och bilden utan kvinnan, och prompten som säger att position, kroppsform och allt annat ska vara detsamma (STEP B i `luma-agaren/gpt/PROMPT-AB.txt`, som den står).
- Ägaren vet inte vilken modell som användes; gränssnittet säger det inte.

Dina fyra B-försök i `nyckel/` gav ingen bild: Codex svarade "Understood. Image 2 is the background plate…" och stannade. Två skillnader mot ägarens körning, och den ena är mitt fel: 0019 bad dig lägga till en tredje bild som identitetsreferens, och Codex-sessionen bär med sig annan kontext (verktyg, MCP, tidigare text).

## Att göra
1. **Ny Codex-session per bild.** Ingen fortsättning på en tidigare session, ingen systemtext utöver det nödvändiga, inga verktyg eller MCP-servrar om de går att stänga av för körningen.
2. **Exakt två bilder in för steg B**: `nyckel/ruta_NNN.png` och `nyckel/A_NNN.png`. Ingen tredje bild. Identiteten mellan nyckelbilder kontrolleras efteråt (stillbildsläsningen i 0019 punkt 4) i stället för att styras i prompten.
3. **Prompten som den står** i STEP B, utan stycket om bild 3. Ett tillägg, sist: `Her arms and hands are in exactly the same position as in image 1.` och en uttrycklig beställning: `Generate the image now and return only the image.`
4. Prova på **en** ruta först (112). Ger den bild: kör 55 och 146. Ger den ingen bild efter två försök: stanna, skriv i svaret exakt vad Codex svarade, och gå vidare med punkt 5. Ägaren kör då steg B själv i GPT.
5. **Vänta inte på nyckelbilderna för att börja med video.** Kör variant (a) ur 0019 nu: Ray 3.2 på fal med bara startbild, ägarens passade GPT-bild för ruta 0 (`passad/`). Läs och mät den. Den ger första svaret på huvudfrågan oavsett hur bildsteget går.

## Gränser
- **Codex veckokvot stod på 94 %** i din senaste logg (`sekundar.used_percent`). Stoppregeln i 0019 gällde femtimmarsfönstret och missade veckan. Ny regel: högst sex Codex-körningar till i natt, och stanna om veckan når 97 %. Misslyckade försök räknas.
- Fal: saldot är cirka 1,90 dollar. Variant (a) först, sedan (b) och (c) bara om nyckelbilder finns och saldot räcker.
- I övrigt som 0019.

## Klart när
- En rad i svar 0019: gav ny kontext med två bilder en bild genom Codex, ja eller nej, och vad som skilde mot de fyra försöken.
- Variant (a) körd, läst och mätt.

## Leveransform
`delegat/svar/0020-ab-i-ny-kontext.md` med en pekare till svar 0019.
