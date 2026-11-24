---
id: 0023
titel: En generering som följer originalet hela vägen: rätt källa, rätt nyckelbilder, rätt prompt
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov 01:05
datum: 2026-11-13
följer: 0021
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

**Ersätter 0022, som är återkallat.** Sätt svar 0021 till `klart` med en pekare hit.

## Mål
**En** genererad video av gelato S1 där hela kroppen syns i alla rutor **och** överkroppen gör det originalet gör (lutar sig ned i disken, räcker fram armen mot kameran), så att kroppsläsaren kan läsa hela människan ur den videon och ingenting behöver sättas ihop efteråt.

## Bakgrund
Ägarens besked, som styr uppdraget:
- **Ingen sammansatt kropp.** Den första genereringen görs just för att slippa klippa och klistra. Att ta överkropp ur en läsning och ben ur en annan är fel väg.
- **Målet med bildgenerering och nyckelbilder med tydliga pekare** är att videomodellen ska generera så nära verkligheten som möjligt, med antagandet om det dolda inbakat i samma generering. Promptas den rätt följer den det som är antaget. Då kan SAM 3D Body skapa människan ur en enda sammanhängande video.
- **Varför alls:** kedjan har ingen LLM i ingesten som kan extrapolera det som är skymt. Det skymda spelar ingen roll för att återge klippet som det är. Det spelar roll för förvärlden: där ska miljön kunna bytas, personen kunna ställas upp, stå, flyttas. Därför behövs hela kroppen.

Läget efter 0021 (`g_forvarld/k/tre_bredvid_rutor.jpg`): variant k (kamerafri, förgrundsfri källa) gav hela kroppen i 148 av 148 rutor och stabila ben, men tappade överkroppen: ingen lutning i rutorna 40–70, armen åt sidan kring ruta 100, en påhittad svart form. Variant (a) (källan som den är) följde överkroppen men klippte benen. Felet i k ligger i **indatat till generatorn**, inte i idén: armen bakom glaset saknades i personmasken, så källan hade ett hål, och inga nyckelbilder band armarna.

Uppdraget är alltså att ge generatorn bättre pekare, tills en enda generering håller båda.

## Att göra
Arbeta som en serie försök, ett i taget, och titta på varje resultat innan nästa. Ändra en sak per försök. Ordningen nedan är ett förslag; följ det resultaten visar.

1. **Källa som inte tappar armen.**
   - **k2: kamerafri, men originalets pixlar kvar.** Samma avbildning som k, men disken, glaset och hennes arm bakom glaset ligger kvar. Bara kundens hand maskas bort. Startbild och prompt säger vad som ska bort. Variant (a) visade att modellen då tar bort disken själv och följer överkroppen; den kamerafria ramen ger den plats att visa benen.
   - **k3: förgrundsfri med hel mask.** Personmask ur segmenteraren i full upplösning, med armen bakom glaset medtagen, skärmtexten borttagen ur hennes yta.
2. **Nyckelbilder som binder överkroppen.** Ray 3.2 på fal tar upp till 64 nyckelbilder vid valda källrutor. I den kamerafria ramen har hon samma storlek och plats i alla rutor, så en nyckelbild är startbilden med ändrad överkropp. Behövs: ruta 55 (lutad ned i disken, armen nedsträckt), ruta 94 (vändpunkten) och ruta 136 (armen fram mot kameran). Tre vägar att få dem, i den här ordningen:
   - ur en tidigare generering: variant (a) följde överkroppen. Finns rutor i (a) eller k2 där både överkropp och ben är rätt, är de nyckelbilder redan, utan ny bildgenerering.
   - ur en bildmodell på fal som tar två bilder in (startbilden och den kamerafria källrutan): "samma kvinna och samma ben som i bild 1, överkropp och armar som i bild 2". Ny kontext per bild. `fal_modeller.md` har kandidaterna; Uni-1 ställde om henne förut, så prova den som håller layout bäst och kontrollera med `passa.py`.
   - ur ägarens GPT: skriv i `luma-agaren/gpt/NASTA-BILDER.md` exakt vilka två bilder och vilken prompt per nyckelruta, och lägg de två indatabilderna färdiga i en mapp per ruta. Ägaren kör dem. Vänta inte på dem; fortsätt med det andra.
   En nyckelbild går vidare först när den är passad och hennes armar ligger där källrutans armar ligger.
3. **Prompten.** Den ska säga vad som är antaget, så att modellen följer antagandet i stället för att hitta på ett eget: hon står hela tiden på samma ställe med fötterna stilla och benen raka; när hon lutar sig framåt böjer hon i höften; hon har inget i händerna och det finns inget framför henne; kameran står still. Beskriv rörelsen i ordning med ungefärliga tider. Spara varje promptversion bredvid sitt resultat.
4. **Läs och mät** varje försök med det som finns: hela kroppen i bild, benlängdens spridning, rotens hopp, bålens och höftens hopp, **överkroppens leder mot dagens läsning i originalets rutor** (genom inversen), och särskilt bålens lutning framåt per ruta mot dagens läsning. Lutningen är måttet på det som k tappade.
5. **Kontrollen.** Samma mått som en liten funktion som säger ja eller nej per generering, med skäl. Den avgör när en generering duger som enda källa för kroppen. Kör den på a, k och varje nytt försök. Trösklarna är diagnos; redovisa dem.
6. **In i förvärlden** med den generering som klarar kontrollen bäst: kroppen läst ur den videon och inget annat, i gelatos plan. Tre bredvid varandra: original, dagens förvärld, ny.

## Gränser
- **Ingen sammansättning av kroppar eller leder ur olika läsningar.** Kroppen i förvärlden kommer ur en video.
- Bara nya filer under `scen/3d/gennedbrytning/`. Kedjans kod ändras inte.
- Fal: det som är kvar av saldot, cirka 1,50 dollar, alltså ungefär åtta videokörningar à 0,15 plus bilder. Planera försöken efter det. Kör aldrig om en generering oförändrad. Tar saldot slut: stanna och redovisa, ägaren fyller på.
- Codex: inga körningar, veckan står på 97 %.
- Modal för läsning och segmentering som förut.
- Egna trösklar är diagnos och inte krav.

## Klart när
- En tabell över försöken: vad som ändrades, kostnad, och måtten ur punkt 4, med dagens läsning, a och k som jämförelse.
- Minst k2 och ett försök med nyckelbilder körda, eller skäl till varför inte.
- Titta på varje genererad video och skriv två rader: vad följer originalet, vad är påhittat. Med rutnummer.
- Kontrollens utfall per försök.
- Filmen med tre bredvid varandra för det bästa försöket, med sökväg.
- `NASTA-BILDER.md` med färdiga indata om ägarens GPT behövs.
- `STRATEGI.md` uppdaterad: en generering som enda källa för kroppen, vad som visat sig binda överkroppen, och tabellen "Prövat hittills". Stryk det som pekar mot sammansättning om något sådant står där.
- Bedömning i högst sex rader: vilken källa, vilka nyckelbilder och vilken prompt som gav en generering som håller, och om ingen gjorde det: vad som saknas.

## Leveransform
`delegat/svar/0023-en-generering-som-foljer-originalet.md` enligt mallen, högst cirka 80 rader. Sätt `pågår` med läget efter k2.
