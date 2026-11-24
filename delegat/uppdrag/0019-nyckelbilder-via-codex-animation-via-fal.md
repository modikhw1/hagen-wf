---
id: 0019
titel: Nyckelbilder genereras via Codex, animationen mellan dem via fal.ai
status: redo
från: orkestratorn (Fable), efter ägarens besked 12 nov 23:45
datum: 2026-11-12
följer: 0018
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Ändrar en gräns i 0018: du **får** nu generera bilder själv, genom Codex. Läs detta så snart du ser det. Är 0017 och 0018 inte klara: väv in, och redovisa i deras svar med en pekare härifrån.

## Mål
För gelato S1 finns isolerad person och tom scen som passade nyckelbilder vid början, mitten och slutet av tagningen, och en animation mellan dem som följer originalets rörelse. Det ska vara känt vilken uppsättning nyckelbilder (bara början, början och slut, eller också mitten) som ger en rörelse kroppsläsaren kan läsa jämnt och troget.

## Bakgrund
Besked från ägaren:
- **Codex är inloggad på ägarens konto och kan generera bilder själv.** AB-upplägget höll i vanliga GPT Image (`scen/3d/gennedbrytning/luma-agaren/gpt/`): tom scen rätt, isolerad person rätt bortsett från storleken. Bildsteget går alltså att köra härifrån utan att ägaren klistrar prompter.
- **fal.ai är fortsatt rätt plats för animationssteget**, särskilt om modellen tar nyckelbilder. Det generativa steget kan göras för början och slutet, eller för mittensteg.

Arbetsfördelningen blir: Codex gör bilderna (vad som syns, vid några rutor), fal gör rörelsen mellan dem (hur det rör sig), originalet styr tiden och avgör där något syns. Se `STRATEGI.md`, principerna 4 och 5.

## Att göra
1. **Codex för bild.** Ta reda på hur Codex anropas för bildgenerering härifrån (tidigare uppdrag i repot: `scen/3d/CODEX-*.md` och `codex-*.jsonl` visar hur Codex startats; bildgenerering är nytt, så prova med en bild först). Läs kvoten före och efter. Skriv ett litet omslag `codex_bild.py` eller motsvarande: indata bilder plus prompt, utdata en bild, prompt och svar sparade bredvid.
2. **Nyckelrutor.** Välj dem ur rörelsen, inte med jämna mellanrum: där armen byter riktning och där den är som längst fram. Utgå från 0, 112 och 146 i `luma-agaren/` och lägg till en eller två i mitten (hon lutar sig ned i disken runt ruta 50–80, och kameran är då nära). Motivera valet med handledens bana ur dagens läsning.
3. **AB per nyckelruta.** Tom scen (steg A) och isolerad person (steg B) för varje, med prompterna i `luma-agaren/gpt/PROMPT-AB.txt`. I rutor där kundens hand är i bild: ta bort den också i steg A. Passa varje isolerad person mot originalets personmask med skalan och förskjutningen från 0018 punkt 1. **Samma kvinna i alla nyckelbilder**: ge den första godkända isolerade bilden som identitetsreferens till de följande, och kontrollera kläder, hår och proportioner (benlängd mot överkropp) mellan dem.
4. **Stillbildsläsning först.** Kör kroppsläsaren på varje passad nyckelbild. Är benlängder och proportioner lika mellan nyckelbilderna (inom några procent)? Det är den snabba kontrollen av att antagandet är samma antagande i alla rutor.
5. **Animation på fal.** Ur `fal_modeller.md`: vilka modeller tar start- och slutbild, och vilka tar bilder vid fler tidpunkter. Kör tre varianter på samma tagning, i den ordningen, och sluta när taket är nått:
   - (a) bara startbild, källvideon styr rörelsen (video-till-video)
   - (b) start- och slutbild
   - (c) start, mitt och slut, antingen i en modell som tar det, eller som två segment som delar mittbilden. Kontrollera skarven.
6. **Läs och mät** varje variant som i 0017 del E och F: tidssynk mot källan, vobbel och vridning, synliga leder i originalets rutor, benlängder. Lägg till: avståndet mellan den animerade kroppen och nyckelbildens kropp vid nyckelrutorna (följde modellen bilderna den fick?).
7. **Tom scen över tid.** Behövs en animerad tom scen, eller räcker nyckelbildernas tomma scener som plattor bakom förvärldens block? Prova det billiga först (plattor), och säg vad som saknas.

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/`. `luma-agaren/steg1/`, `utfall/` och `gpt/` ändras inte.
- Codex och fal.ai är förhandsgodkända enligt `REGLER.md` (läs om från disk; Codex lades till i kväll). Nyckeln till fal i `fal_ai.txt`, skrivs aldrig ut.
- Kostnadstak för fal i det här uppdraget: 5,00 dollar utöver det som gått i 0017 och 0018. Läs priset på modellsidan före varje körning, för `kostnad.json` vidare. Kör aldrig om en generering oförändrad.
- Codex: håll det till de bilder som behövs (cirka tio). Går kvoten under 30 % av femtimmarsfönstret: stanna och redovisa.
- Lås bilderna innan video körs. En nyckelbild som inte håller position eller identitet efter passningen byts eller stryks, den går inte vidare.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Passade nyckelbilder (isolerad person och tom scen) för minst tre rutor, bredvid originalets rutor i en översiktsbild.
- Tabell över stillbildsläsningen: benlängder och proportioner per nyckelbild.
- Minst variant (a) och (b) animerade, lästa och mätta. Tabell: variant, synk, vobbel, trohet i synliga leder, avstånd till nyckelbilderna, kostnad, väggtid.
- Den bästa varianten i förvärlden bredvid originalet och dagens förvärld, med sökväg.
- Titta på filmerna och beskriv vad som syns, också det som är fel.
- Bedömning i högst sex rader: hur många nyckelbilder som behövs per tagning, hur de ska väljas, vilken modell på fal, och vad en tagning och ett klipp på elva tagningar då kostar i pengar och Codex-kvot.
- `STRATEGI.md` uppdaterad: arbetsfördelningen Codex för bild och fal för rörelse, och tabellen "Prövat hittills".

## Leveransform
`delegat/svar/0019-nyckelbilder-via-codex-animation-via-fal.md` enligt mallen, högst cirka 80 rader. Sätt `pågår` med läget när nyckelbilderna är låsta, före första videokörningen.
