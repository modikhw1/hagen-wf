# Bildsteg genom Codex: så görs det rätt (13 nov 2026)

Läs detta innan `codex_bild.py` används eller ändras.

## Misstaget som kostade en natt
Codex fick aldrig hela prompten. `codex exec ... -- "<prompt>"` går på Windows via npm-shimmen `codex.CMD`, och cmd.exe klipper argumentet vid första radbrytningen. Varje körning fick bara promptens första rad:

- **Steg A** fick "Remove the woman from this photo." Kvinnan försvann, men skärmtexten och kundens hand stod kvar, eftersom de instruktionerna låg på senare rader.
- **Steg B** fick "Image 1 and image 2 are the same photo…" utan beställningen, och svarade bara "Understood".
- **"Create the image now."** gav en gissning från agenten, i praktiken den tomma scenen igen.

Felet tolkades först som att Codex inte kan isolera en person. Det var fel. Med hel prompt fungerar steg B direkt, på samma sätt som i ägarens ChatGPT-körning.

## Gör så här
1. **Prompten på stdin, aldrig som argument.** Avsluta kommandot med `-` och skicka texten som indata (`subprocess.run(..., input=prompt)`).
2. **Bilderna med `--image=<fil>`, en per bild.** Inte `-i a b`. `-i` tar flera värden och slukar `-`, och då läser Codex `-` som en bildfil.
3. **Kontrollera alltid i sessionsloggen** att hela prompten kom fram. Den senaste `~/.codex/sessions/<år>/<mån>/<dag>/rollout-*.jsonl` har användarens `input_text`. `codex_bild.py` gör det och skriver `prompt_fram.hel` i `<bild>.codex.json`. Lita inte på en bild som saknar `hel: true`.
4. **Ny session per bild och rått läge** (`CODEX_RAA=1`): ingen extra text från omslaget, `-c mcp_servers={}`, stängd stdin utöver prompten.
5. **Kontrollera att Codex faktiskt startar.** Vänta inte på en tidsgräns. Hänger körningen, se efter efter en minut om en sessionsfil har skapats. Första försöket hängde i 15 minuter utan att någon session startade.
6. **Läs kvoten** (`rate_limits` i sessionsloggen) före och efter. Varje bild tar cirka 2–3 % av femtimmarsfönstret och 0,5 % av veckan.

## Vad som körs
Agenten `gpt-6-astra` skriver om prompten (`revisedPrompt`) och anropar det inbyggda verktyget `image_gen`. Det är samma GPT Image-familj som i ChatGPT, men versionen syns inte i loggen. Modellen var inte felet.

## Receptet som höll (ägarens, 12–13 nov)
- **Steg A**, ny session: bara originalrutan, och STEP A ur `luma-agaren/gpt/PROMPT-AB.txt`. I rutor där kundens hand syns läggs en rad till som tar bort den också.
- **Steg B**, ny session: exakt två bilder, originalrutan och A-bilden. STEP B utan stycket om bild 3, med en rad kontext om vad hon gör i rutan och en rad om armens läge.
- **Efteråt:** `passa.py` mot originalets personmask (princip 3 i efterhand) och `las_stillbild.py` för att kontrollera att proportionerna är lika mellan nyckelbilderna.

Utfallet för gelato S1 finns i `nyckel2/` och `delegat/svar/0020-ab-i-ny-kontext.md`.

## Kvar
- Ruta 30 har för långa ben (ben mot överkropp 1,96 mot cirka 1,56) och bör göras om.
- Byxorna glider mellan rutor (svarta, sedan jeans). Prova en identitetsreferens först när två bilder fungerar stabilt.
- Fal har slut på krediter (13 nov), så video med nyckelbilderna (Ray 3.2 `keyframes`) är inte körd.
