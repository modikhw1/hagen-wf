---
id: 0017
titel: Generativ nedbrytning vid ingest: tom scen, isolerad person, läst kropp, på fal.ai
status: redo
från: orkestratorn (Fable), omskrivet 12 nov 23:30 efter ägarens förtydliganden (inte påbörjat dessförinnan)
datum: 2026-11-12
följer:
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

**Ersätter 0015, som är återkallat.** Kör detta före 0016.

## Mål
En tagning är nedbruten enligt `scen/3d/gennedbrytning/STRATEGI.md` hela vägen: tom scen, isolerad person med kompletterad kropp som spelar originalets rörelse utan förgrund, kroppen läst ur den, och resultatet i förvärlden bredvid originalet. Det ska vara känt vilken modell och vilken promptning på fal.ai som håller, och vad det kostar per tagning.

## Bakgrund
Läs `scen/3d/gennedbrytning/STRATEGI.md` först. Den är uppdragets ram: lagren, de åtta principerna, stegen och det som är öppet. Läs sedan det som redan är prövat:
- `scen/3d/gennedbrytning/luma-agaren/`: ägarens Luma-prov i kväll. `steg1/` har två misslyckade helkroppsbilder (omställda, fel pose) och `guidebild_last_position.png` (lokal komposit med låst position, grov). `PROMPT.txt` och `PROMPT-AB.txt` har prompterna, där AB är ägarens negativa upplägg: först "ta bort kvinnan", sedan original plus tom scen in och "behåll bara det som skiljer". `bygg_guide.py` bygger kompositen.
- `scen/3d/lasformat/RAPPORT.md`: Wan2.1-VACE maskstyrd på Modal (ben i 85 av 85 rutor, cirka 3 px drift, 0,26 dollar, något mer bålskak). Skript och volym `lasformat-wan21-vace` finns.
- `scen/3d/licensrevy/V2V-ALTERNATIV.md`: modeller, licenser och priser per 11 nov, flera av dem via fal.
- `scen/3d/lasformat/luma-paket/STEG2-VIDEO.md` och `logg.md`: Luma-proven och hur de mättes (`mat_video.py`).

Ägaren tror att detta går, och att det hänger på stacken och promptningen. Uppdraget är att hitta dem.

## Provtagning
`kand-kennysgelato` S1, förberedd i `scen/3d/gennedbrytning/luma-agaren/`: `1_kalla_gelato_S1.mp4` (4,94 s, 148 rutor, 1080×1920; motsvarar ingestens ruta 7 och framåt), `2_ruta_000_start.png`, och rutorna 112 och 146. Hon står bakom en glasdisk, kameran zoomar och tippar ned i glassen och upp igen, och hon räcker fram ett smakprov. Ingestens personmasker: `scen/3d/ingest/ut/kand-kennysgelato-tagningar/S1/masker.npy` (156 × 480 × 270). Dagens plan: `scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/`.

Andra tagning om taket räcker: `b-tilltal-ravara` S2 (fast kamera, handen utan bildstöd i 52 av 52 rutor) eller S11 (vågen framför kroppen).

## Delar
**A. Vad fal.ai har i dag (inga körningar).** Gå igenom fal:s modellsidor och dokumentation, inte minnet. Tre slag behövs:
- bildredigering som håller layouten: maskad inpainting, och instruktionsredigering som tar flera bilder in
- video-till-video som följer en källvideos rörelse och tar en låst första ruta eller referensbild
- maskstyrd video, där en mask per ruta skyddar pixlar
För varje kandidat: vad den tar in, pris per bild eller sekund, längsta klipp, bildfrekvens ut, och om sidan flaggar att modellen tas bort. Skriv tabellen i `fal_modeller.md`.

**B. Tom scen, bild** (princip 1). Två vägar, båda om det ryms: maskad inpainting med ingestens personmask (vidgad), och promptad borttagning (STEP A i `PROMPT-AB.txt`). Mät: hur mycket ändrades utanför masken, och ser det dolda bakom henne rimligt ut.

**C. Isolerad person, bild** (principerna 2 och 3). Original plus tom scen in, STEP B i `PROMPT-AB.txt`. Reserv om modellen ställer om henne: städa den färdiga kompositen (`guidebild_last_position.png`, STEP 1 VERSION 3 i `PROMPT.txt`), eller maskad inpainting där bara området under midjan och disken genereras. Mät låsningen: överlapp mellan hennes mask i resultatet och i originalet, och förskjutning av huvud och axlar i pixlar. En bild som inte håller positionen går inte vidare till video.

**D. Isolerad person, video** (principerna 4 och 5). Video-till-video på källan med bilden från C låst vid ruta 0, starkast rörelseföljsamhet. Om modellen tar fler låsta rutor: gör motsvarande bild för ruta 112 och 146 och prova med dem. Kameran i källan rör sig mycket; se vad som händer, och prova en gång med uttrycklig instruktion om stilla kamera.
Jämförelsearm, om taket räcker: maskstyrd video (VACE på Modal eller hostad), där hennes synliga pixlar skyddas och resten genereras.

**E. Synk och trohet, före läsning.** Antal rutor och bildfrekvens mot källan, och hur tiden mappas om de skiljer. Hennes mask i det genererade mot originalets mask ruta för ruta, för den del som syns i originalet. Titta igenom varje klipp och lista det ingen kroppskontroll fångar, med rutnummer: klipp eller övergångar, annan person, föremål som dyker upp, otydliga rutor.

**F. Läs kroppen** ur lager 2 med ingestens läsare (`ingest/modal_sam3db.py`). Mot dagens läsning ur originalet:
- **vobbel och vridning, huvudmåttet**: bålens och höftens vridning kring lodaxeln ruta för ruta, antal hopp över 15°, största hopp, och rotens hopp i meter per ruta
- synliga leder projicerade i originalets rutor, avstånd i promille av bildhöjden
- ben och fötter: konstanta benlängder, fötter som står still när de ska
- hur många rutor handen har bildstöd (dagens tal i `delegat/svar/0013-foremal-i-handen.md`)
- snabb rimlighetskontroll med `ingest/vakt.py` eller benlängder. GEM-X bara om det går fort och tillför något.
Skilj på vad som försvann för att kroppen nu syns hel, och vad som står kvar för att läsaren läser en ruta i taget.

**G. In i förvärlden.** Nya kroppsläsningen i tagningens befintliga plan, renderad. Tre bredvid varandra: original, dagens förvärld, förvärld med ny kropp. Kodändring som behövs görs i en kopia under `scen/3d/gennedbrytning/`.

**H. Förgrunden utan henne** (lager 3), om taket räcker: disken ensam, som bild. Hamnar dess kanter där originalets synliga kanter ligger?

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/`. Rör inte `luma-agaren/steg1/` och `utfall/`, där lägger ägaren egna resultat. Ingen ändring i kedjans kod.
- fal.ai och Modal är förhandsgodkända enligt `REGLER.md` (läs om filen från disk). Nyckeln till fal ligger i `fal_ai.txt` i repots rot: läs den i skriptet, skriv aldrig ut den, kopiera den inte.
- **Kostnadstak 6,00 dollar totalt**, varav högst 4,00 på fal. Kontrollera pris på modellsidan före varje körning och för en löpande summa i `kostnad.json`. Kör aldrig om en generering oförändrad. Bilder är billiga, video dyr: lås bilden innan du betalar för video.
- Det som lämnar maskinen: den förberedda tagningen (5 s), enstaka rutor och masker.
- Prompter på engelska. Varje prompt och varje modellanrop sparas bredvid sitt resultat.
- Uppdatera `STRATEGI.md`: tabellen "Prövat hittills" och avsnittet "Öppet", med det som blev känt. Ändra inte principerna; håller en inte, skriv det under "Öppet".
- Egna trösklar är diagnos och inte krav.

## Klart när
- `fal_modeller.md` med tabellen ur A.
- Tom scen och isolerad person som bilder, med låsningsmåtten ur C, och en rad om vilken promptning som höll positionen och vilken som inte gjorde det.
- Minst en isolerad video, läst kropp, och filmen med tre bredvid varandra, med sökvägar.
- Talen ur E och F i en tabell: dagens läsning mot den nya.
- Titta på filmen och beskriv: rör sig kroppen i förvärlden mer som människan i originalet än förut? Var är antagandet rimligt, och var syns det att modellen hittat på?
- Kostnad och väggtid per steg, och vad ett klipp på elva tagningar då kostar.
- Bedömning i högst sex rader: vilken stack (modell per steg) och vilken promptning som ska bli ingeststeget, och vad som återstår innan det går att lita på utan att någon tittar.

## Leveransform
`delegat/svar/0017-generativ-nedbrytning-vid-ingest.md` enligt mallen, högst cirka 90 rader. Sätt status `pågår` med en rad om läget efter del C, så att ägaren ser bilderna innan videon körs.
