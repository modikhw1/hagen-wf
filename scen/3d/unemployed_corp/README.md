# unemployed_corp: hur PS2-klippen görs (9 nov 2026)

Kontot (@unemployed_corp, 20 000 följare, 29 inlägg mellan 20 okt och 9 nov 2026) säljer t-shirts via unemployedcorp.com. Det kör samma format som **Luca Maxim / Children of Khan**:
- en återkommande figur, egen "lore" och satir;
- AI-video i PS2-stil med tal;
- nostalgisk musik under;
- merch i slutet ("grab ur unemployment in bio").

## Arbetsflödet (spårat, inte gissat)

Kedjan kommer från CYBORG-handledningen ([YouTube xI51f2FFbpk](https://www.youtube.com/watch?v=xI51f2FFbpk)). Dess SOP finns i `spar/ps2_viral_sop.txt`, och CYBORG länkade den från [X @cyborg_mp4](https://x.com/cyborg_mp4/status/2099170925170102534).

1. **Figurblad (stillbild).** Gör det med en bildmodell i Higgsfield: GPT Image 2.5, Nano Banana Pro eller Seedream 5.0 Pro. Ge en spelfigur (Tekken/DMC-typ) och produktbilden som referens. Prompten lyder "Make a character similar to this style, PS2 graphics, but wearing the [garment] in image 2 …".
2. **Prompten.** Klistra in hela SOP:n i ChatGPT. Ge den sedan bara en idé, repliken och vad som händer. ChatGPT skriver resten: referensroller, PS2-värld, 3–5 kameravinklar med hårda klipp, regi för skådespelet, objektfysik och negativa krav.
3. **Video: Seedance 2.5 i Higgsfield.**
   - Inställningar: ljud på, 10 s, 9:16, 720p och hög bitrate.
   - Referenser: IMAGE 1 är figuren, IMAGE 2 plagget, IMAGE 3 rekvisita och AUDIO en röstreferens (valfri mp3 med önskad brytning).
   - Talet kommer inbyggt från modellen med läppsynk, och flera kameravinklar ryms i samma generering.
4. **Förlängning.** Använd "extend video" från sista bildrutan, 2–3 gånger, så att klippet blir 20–30 s.
5. **Redigering.** Lägg nostalgisk musik från TikTok under, pixeltext eller överlägg (till exempel klocka och "POV"), och avsluta med produktbild och CTA. Kreatören uppger cirka 10 min per video och upp till 15 videor per dag.

Alternativ med ett klick: Flashloops förinställning "PS2 Retro Style" ([YouTube EaX1grcrQbo](https://www.youtube.com/watch?v=EaX1grcrQbo)). Gratisvägen: Google Flow (Veo) med prompten "PlayStation 2 graphic style" ([YouTube 4MUN4YvCGpY](https://www.youtube.com/watch?v=4MUN4YvCGpY)).

## Belägg i unemployed_corps egna klipp

- Alla 25 videor har talade repliker (`transkript.json`, Whisper small). Ingen separat speaker eller TTS ovanpå syns, vilket stämmer med Seedances inbyggda ljud.
- Det finns 2–5 s mellan kameraklippen och 3–5 vinklar per cirka 10 s-block, vilket motsvarar SOP:ns avsnitt 5–6. Klippen är 16–30 s långa, alltså 2–3 genereringar.
- Tröjans logga är identisk i alla tagningar, vilket betyder att produktbilden använts som referens enligt SOP:ns IMAGE 2.
- Samma blonda huvudfigur återkommer i varje klipp (SOP avsnitt 1 och 4).
- I kommentarerna (317 av 320 hämtade, `kommentarer/`) svarar skaparen aldrig. Många frågar "which ai?", och en kommentar lyder "Bro bought the elite ball knowledge ai course". Det syftar på Luca Maxims kurs (eliteballknowledge.ai, 197 USD), som uppger "the exact stack we use" utan att namnge den.
- Instagram rensar metadata, så det finns inga verktygsspår i filerna.

**Inte bevisat:** vem som driver kontot och om det är just Higgsfield eller ett annat gränssnitt till Seedance (till exempel Flashloop). Allt som syns stämmer med kedjan ovan.

## Filer

- `inlagg/`: bildtexter och metadata (instaloader).
- `video/`: 25 mp4-filer.
- `ramar/`: kontaktark med en bildruta per 2 s.
- `kommentarer/`: yt-dlp info.json med kommentarer.
- `alla_kommentarer.txt`.
- `transkript.json`, skapad av `transkribera.py`.
- `spar/`: SOP:n, transkript och metadata från handledningarna.

## Koppling till Scen3D

Det här är motsatsen till vår väg. Inga meshar finns. PS2-looken kommer helt från prompten mot en videomodell med referensbilder. För LeTrend betyder det att "PS2-rendering" kan nås utan Blender, men då utan JSON-redigering och utan deterministisk kontroll.
