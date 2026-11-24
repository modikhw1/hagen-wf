---
id: 0026
titel: Läs kroppen ur Dreamina-utfallet, och ställ scenen och föremålen kring den i förvärlden
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov eftermiddag
datum: 2026-11-13
följer: 0025
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

## Mål
Gelato S1 står i förvärlden med allt som bär tagningens mening på plats samtidigt: kroppen ur **en** generering (Dreamina-utfallet), skeden i handen, disken där kroppen säger att den står, en enkel bakgrund, och kunden som tar emot. Och det är känt vad nästa manuella Dreamina-omgång ska innehålla, för gelato och för guacamole.

## Bakgrund
- Ägaren har kört `d_video/dreamina-paket/` i Dreaminas webbapp. Utfallet ligger i `d_video/dreamina-paket/svar/k2s.mp4`, inställningarna i `svar/installningar.txt`. Dreamina har inget API. Ägaren kör nya klipp för hand och kan iterera på prompt och indata.
- Dreamina respekterar inte exakt längd. Den vill ha 5, 8 eller 10 s. Utfallet är 8,02 s och 193 rutor (cirka 24 fps), källan är 4,94 s och 148 rutor. Ägaren bedömer att det är i sin ordning. Ray 3.2 på fal eller Luma, med exakt längd och nyckelbilder på tid, är fortfarande ett alternativ när en nyckel med saldo finns. Bygg därför inget som bara fungerar med Dreamina.
- Orkestratorns läsning av utfallet (tolv rutor, inte ruta för ruta):
  - Ren grå bakgrund, hela kroppen i bild, skeden i höger hand, ingen disk, text eller kundhand. Lutningen finns kvar.
  - **Tiden är utdragen**, och troligen inte jämnt: lutningen upptar en större del av klippet än i källan.
  - **Huvudet är avskuret** med en rak kant i de böjda rutorna (ungefär 1,5–3,5 s). Källan har huvudet utanför bild där (rutorna 38–91, se `relevans/UTANFOR-OCH-REDIGERING.md`), och modellen har ärvt kanten i stället för att anta huvudet.
  - **Kameran är inte låst.** Från cirka 5 s ses hon mer uppifrån och blir större.
  - Hon böjer sig tills handen är i höjd med fötterna. I originalet stoppar tråget handen högre upp.
- Ägarens ram står kvar: kroppsanalysen är ett steg. Målen är scenen och föremålen i förvärlden, så att meningen går att ändra med ord (`delegat/kontext/malbild.md`).
- Det som redan är känt och ska användas, inte tas fram igen: handlingsspåret (`handling/S1/handling.json`), samspelet (`samspel/`), färgmaskerna och regeln ur 0025 (`fargkod/`, V1 och V3), relevanslistan (`relevans/kand-kennysgelato-tagningar/relevans.json`), och "rummet utan disk" och "bara disken" (`fargkod/codex/`).

## Att göra

### 1. Tiden: lägg utfallet på källans rutor
- Läs kroppen ur alla 193 rutor (`f_las.py` eller motsvarande).
- Hitta avbildningen från utfallets tid till källans 148 rutor. Den ska komma ur mätning: jämför överkroppens synliga leder (huvud där det syns, axlar, armbågar, handleder) mot originalets 2D-läsning och låt tiden töjas olika mycket i olika delar (dynamisk tidspassning eller motsvarande, monoton). Jämför med rak linjär omskalning (193 till 148) och säg vilken som följer originalet bäst.
- Segmentgränserna i `handling.json` är en kontroll: ligger vändpunkterna (handen lägst, armen framsträckt) på samma källrutor efter passningen?
- Resultatet är en läsning på 148 rutor som kedjan tar emot som vanligt. Avbildningen sparas, så att samma steg går att köra på nästa utfall oavsett längd.

### 2. Kroppen: kontroll och in i förvärlden
- `h_kontroll.py` på den tidspassade läsningen, samma tabell som i svar 0023, med en kolumn till bredvid a, k och k2.
- Mät särskilt det som syntes ovan: i vilka rutor saknas huvudet, hur mycket ändras kameran (hennes storlek och fotlinje över tid), och hur djupt går handen jämfört med originalets läsning i h3–h4.
- Där huvudet saknas i genereringen: lappa inte. Säg vad läsaren gör där, och ta det till punkt 5.
- In i förvärlden som i `g_forvarld.py`, tre bredvid varandra: original, dagens förvärld, ny kropp.

### 3. Scenen kring kroppen
En kopia av planen (utgå från `n06-hand`), kedjans kod oförändrad där det går:
- **Disken** flyttas dit mätningarna pekar. Använd flera rutor och samspelet som villkor, så som 0025 kom fram till: färgmaskerna i ruta 0 och 112 (55 om den går att rädda), och kravet att handens lägsta punkt i h3–h4 ska ligga i tråget, under diskens ovankant och innanför dess yta. Redovisa läget, vad varje källa säger, och vad som valdes. Märk `antagen` där det är det.
- **Tråget.** Disken är i dag en låda utan öppning. Ge den det enklaste som gör att "handen är i tråget" är sant i scenen: en försänkt yta med djup ur handens lägsta punkt.
- **Skeden** i handen genom `plan.handforemal`, som i 0013. Stämmer handfästet med var skeden syns i utfallet?
- **Bakgrunden** som enkel form: en vägg och en bakre bänk, mått ur "rummet utan disk" och det planen redan har. Relevanslistan gav `ramar` och förenklad form.
- **Kunden.** I dag finns kunden bara som en hand i kantmasken. Ställ en person på kundens sida av disken, antagen i sin helhet, med en hand som möter skeden i h8. Detta är ett antagande utanför bild och ska märkas så. Ingen ny bild- eller videogenerering för kunden i det här uppdraget. Säg vad som skulle behövas för att göra kunden lika bra som henne.

### 4. Bär scenen meningen?
- Rendera S1 ur förvärlden med allt på plats, bredvid originalet, och med handlingsspårets remsa under.
- Gå igenom segmenten h1–h9: är det som spåret påstår sant i scenen? Handen i tråget i h3, över diskens kant i h8, kontakten hand mot sked mot kundens hand. En rad per segment: sant, nästan, eller falskt, och vad som felar.
- Ta de fem CM-meningarna ur svar 0024. För var och en: vad kan scenen nu, som den inte kunde i går, och vad saknas fortfarande. Utför ingen av dem.

### 5. Nästa Dreamina-omgång, åt ägaren
Lägg ett paket i `d_video/dreamina-paket/omgang2/` med numrerade indata, en prompt per körning i egen textfil, och en `LAS-MIG.md` som säger exakt vilket läge och vilka inställningar. Högst fyra körningar för gelato S1, valda efter vad punkt 1 och 2 visade. Kandidater:
- **Längd som passar.** Antingen 5 s, eller källan nedsaktad till jämnt 8 s och promptens tider omräknade, så att tidspassningen blir enkel. Välj efter vad punkt 1 visade.
- **Huvudet.** Prompten säger uttryckligen att huvudet lämnar källans bild och ska antas helt, och en nyckelbild ur en böjd ruta visar henne hel.
- **Kameran.** Källan med en fast ram ritad i (golvlinje eller markering) eller en prompt som låser hennes storlek. Välj det som troligast håller.
- **Flera bildrutor-läget** (nyckelbilder på tid, utan videoreferens) som jämförelse mot Universell referens.

Och ett paket för **guacamole S1** i `d_video/dreamina-paket/guacamole-S1/`, gjort med samma steg som gelato (kamerafri källa med originalets pixlar kvar, prompt med antagandet och tiderna, föremålet i handen kvar: mobilen). Två personer: säg hur du valde att dela upp det (en person per körning, eller båda), och varför. Anteckna allt som måste göras annorlunda än för gelato, för det är det som inte var allmänt.

## Gränser
- Bara filer under `scen/3d/gennedbrytning/`. Kedjans kod, `forvarld/`, källans schema, `video/` och `data/` ändras inte. Behövs en ändring i kedjan för punkt 3, gör den i en kopia under `gennedbrytning/` och säg vad som borde in i kedjan.
- **En generering.** Kroppen kommer ur Dreamina-utfallet ensamt. Inga leder ur andra läsningar, inget huvud ur originalet. Tidspassning är inte sammansättning.
- Modal: högst 1,00 dollar. Gateway: högst 0,20 dollar, Flash. Fal: bara om saldo finns, högst 0,30 dollar, och då `k2sn` med nyckelbilder som jämförelse. Codex: bilder bara om paketet i punkt 5 kräver det, högst sex.
- Prompter på engelska, sparade bredvid sina resultat.
- Egna trösklar är diagnos, inte krav.
- Byt inga filer under en körning.

## Klart när
- Tidsavbildningen sparad, med jämförelsen mot linjär omskalning.
- Tabellen ur 0023 med Dreamina-kolumnen, och de tre extra måtten (huvud, kamera, handdjup).
- `g_forvarld/dreamina/tre_bredvid.mp4`.
- En film av S1 ur förvärlden med kropp, sked, flyttad disk med tråg, bakgrund och kund, bredvid originalet och med remsan under.
- Tabellen h1–h9: sant, nästan, falskt.
- De fem meningarna, före och efter.
- `omgang2/` och `guacamole-S1/` klara att köra, med det som skilde guacamole från gelato.
- `STRATEGI.md`: tidspassningen som steg, Dreamina bredvid Ray 3.2 under leverantörer, och raderna i "Prövat hittills".
- Bedömning i högst åtta rader: duger Dreamina som generator i ingesten, vad är det svagaste ledet nu, och vad av punkt 3 bör in i kedjan först.

## Leveransform
`delegat/svar/0026-dreamina-kroppen-och-scenen-i-forvarlden.md` enligt mallen, högst cirka 90 rader. Filmer och tabeller länkas.
