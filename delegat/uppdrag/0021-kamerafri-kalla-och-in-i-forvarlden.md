---
id: 0021
titel: Ta bort kameran och förgrunden ur källan före genereringen, och för den nya kroppen in i förvärlden
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0019
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Samlar det som återstår av 0017 (del G), 0018 (punkt 4–6) och 0019 (variant b och c). Sätt de tre svaren till `klart` med en pekare hit när du börjar; resten redovisas här.

## Mål
Lager 2 för gelato S1 visar hela kroppen i alla 148 rutor, utan kundens hand och utan föremål, och den kropp som läses ur det står i förvärlden bredvid originalet och dagens förvärld.

## Bakgrund
Variant (a) i svar 0019 höll: samma kvinna, samma rörelse, synk 1:1, bålens största hopp 7,3° till 2,9°, rotens hopp över 10 cm från 7 rutor till 0, för 0,15 dollar. Tre fel återstod, och alla tre har samma orsak: **videomodellen fick källan som den är**, med kamerans zoom och tippning, kundens hand, disken och skeden. Den följde källan, som den skulle, och tog med alltihop. Underkroppen klipps från ruta 80.

Lösningen följer den negativa strategin och trestegsplanen i `STRATEGI.md`: ta bort ur källan det som inte hör till lager 2, **innan** modellen ser den. Kameran hör till rummet (lager 1), inte till kroppen.

## Att göra
1. **Kamerafri källa.** För varje ruta: en likformig avbildning (skala, förskjutning, ingen vridning om den inte behövs) som lägger hennes överkropp på samma plats och i samma storlek som i ruta 0. Skatta den ur dagens 2D-leder (huvud, axlar, höfter där de syns) eller ur personmasken, och jämna den över tiden så att den inte för in eget skak. Spara avbildningen per ruta (`kamerafri/avbildning.json`). Den är också vägen tillbaka: med inversen kan allt i lager 2 läggas på rätt plats i originalets rutor.
2. **Förgrundsfri källa.** Lägg bara hennes pixlar (ingestens personmask per ruta, i full upplösning om en bättre mask går att få ur segmenteraren) på jämn grå duk, i den kamerafria ramen. Disken, rummet, texten och kundens hand finns då inte i källan alls. Det som hamnar utanför originalets bild när kameran zoomat in blir grått. Kontrollera masken i rutorna där kundens hand korsar hennes arm.
3. **Generera på den källan.** Ray 3.2 v2v med samma startbild som i (a) och en kortare prompt: hela kroppen ska synas hela tiden, komplettera det som saknas, tomma händer, stilla kamera. Jämför mot (a).
   - Om saldot räcker, en arm till: maskad video (`fal-ai/wan-vace-14b/inpainting` eller VACE på Modal) där hennes synliga pixlar skyddas och bara resten genereras. Det är princip 7 i dess rena form.
4. **Läs och mät** som i 0019. Lägg till:
   - hela kroppen i bild: antal rutor av 148
   - benlängdens spridning över hela tagningen (var 6,6 % i (a), där benen klipptes)
   - främmande händer eller föremål: antal rutor, kontrollerat med segmenteraren eller genom att titta
   - synliga leder förda tillbaka till originalets rutor genom inversen av avbildningen, i promille. Det är trohetsmåttet, och det ska göras i originalets ram.
5. **Sekvens och förvärld.** Gör den nya läsningen till en sekvens med ingestens sekvenssteg, i en kopia av gelatos plan (`kontrakt/ut/kand-kennysgelato_n06-hand/`). Kroppens läge i rummet ska komma ur dagens plan (plats, golv, kamera); det nya är lederna och rotens rörelse relativt platsen. Rendera tre bredvid varandra: original, dagens förvärld, förvärld med ny kropp.
6. **Rummet ur den tomma scenen** (0018 punkt 4–5), i den mån tiden räcker: segmenteraren på `nyckel/A_*.png` mot originalets rutor, och den tomma scenen som platta bakom förvärldens block i en stillbild. Kamerabanan för rummet är inversen av avbildningen i punkt 1; säg om den räcker som kamerarörelse för lager 1 eller vad som saknas.
7. **Nyckelbilder i den kamerafria ramen.** I den ramen har hon samma storlek och plats i alla rutor, så en isolerad helkroppsbild behöver inte göras om för varje nyckelruta från en närbild. Prova: ta startbilden, och låt bildmodellen bara ändra armarnas läge så att det stämmer med den kamerafria källrutan vid 55, 94 och 136 (två bilder in, ny kontext: startbilden och den kamerafria källrutan). Om det ger giltiga nyckelbilder: kör variant (b) eller (c) med dem. Ger Codex ingen bild: skriv exakt vilka bilder och vilken prompt ägaren ska köra i GPT, i `luma-agaren/gpt/NASTA-BILDER.md`.

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/`. Kedjans kod ändras inte; behövs en ändring för punkt 5, gör den i en kopia och beskriv den.
- Fal: det som är kvar av saldot (cirka 1,68 dollar). Punkt 3 med Ray först. Kör aldrig om en generering oförändrad.
- Codex: veckan står på 97 %. Högst tre körningar till, och bara för punkt 7. Stanna vid 99 %.
- Modal för läsning och segmentering som förut.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Kamerafri, förgrundsfri källa som film, med avbildningen per ruta. En översiktsbild av några rutor bredvid originalets.
- Ny isolerad video, läst och mätt, i samma tabell som (a) och dagens läsning.
- Filmen med tre bredvid varandra ur förvärlden, med sökväg.
- Titta på båda filmerna och beskriv vad som syns, också det som är fel.
- Tre rader om rummet: vad den tomma scenen och den inverterade avbildningen ger lager 1.
- `STRATEGI.md` uppdaterad: kamerafri och förgrundsfri källa som steg före genereringen, och tabellen "Prövat hittills".
- Bedömning i högst sex rader: är detta ingeststeget, vad kostar en tagning, och vad måste till innan det körs på ett helt klipp.

## Leveransform
`delegat/svar/0021-kamerafri-kalla-och-in-i-forvarlden.md` enligt mallen, högst cirka 80 rader. Sätt `pågår` med läget när den kamerafria källan finns, före genereringen.
