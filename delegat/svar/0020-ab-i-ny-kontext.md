---
id: 0020
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**Nej:** ny kontext med exakt två bilder gav ingen isolerad person genom Codex. Detaljer och variant (a) finns i `delegat/svar/0019-nyckelbilder-via-codex-animation-via-fal.md`.

Gemensamt för alla försök: ny `codex exec`-session per bild, rått läge (`CODEX_RAA=1`, ingen text från omslaget, `-c mcp_servers={}`), och bara `ruta_112.png` och `A_112.png` in.
- **Försök 1** (STEP B som den står, med rubrikraden "Optional image 3 …" kvar) gav svaret "What would you like me to create or change using these two images? I'll treat image 3, if provided, as a layout reference only."
- **Försök 2** (rubrikraden borttagen, och tilläggen om armarna och "Generate the image now and return only the image.") gav svaret "Understood. Image 1 is the reference with the woman; Image 2 is the matching scene with her removed. …" och ingen bild.
- **Försök 3** ("Create the image now." först, utöver punkt 3, efter ägarens klartecken till fler bilder) gav en bild, men det var den tomma scenen igen ("Created the image with the server removed, matching Image #2").

**Skillnad mot de fyra tidigare försöken:** ingen tredje bild och inga MCP-servrar. Utfallet är detsamma: Codex bildverktyg tar inte originalet som underlag för att behålla henne och ta bort resten.

Veckokvoten för Codex gick från 96 till 97 %. Variant (a) är körd, läst och mätt (svar 0019).

## Tillägg 13 nov, efter ägarens fråga: orsaken till att Codex inte gav bild
**Orsaken:** `codex_bild.py` skickade prompten som ett argument till `codex.CMD`, och Windows-skalet klipper argumentet vid första radbrytningen. Alla tidigare körningar fick därför bara promptens första rad. Det syns i sessionsloggarna: B4 fick bara "Create the image now.".

**Modellen var inte orsaken.** Codex-agenten (`gpt-6-astra`) anropar sitt inbyggda verktyg `image_gen` (GPT Image-familjen, samma som i ChatGPT; versionen syns inte) med en prompt som agenten själv skriver om.

**Rättat:**
- Prompten skickas på stdin, och bilderna med `--image=<fil>`.
- Omslaget kontrollerar i sessionsloggen att hela prompten kom fram (`prompt_fram.hel`).

**Omkört med hel prompt:** `scen/3d/gennedbrytning/nyckel2/` (`oversikt.jpg`).
- Ruta 0: A ren, B isolerad med hel kropp. Efter passning ligger huvud och axlar inom 18–26 px.
- Ruta 112: A utan text, kundens hand och sked. B med armen framsträckt och hel kropp. Huvud och axlar inom 14–21 px, överlapp 0,63.

Steg B fungerar alltså genom Codex. Veckokvoten för Codex står på 99 %.

## Tillägg 13 nov, efter kvotåterställning: åtta nyckelbilder
**Körningarna:** rutorna 0, 30, 55, 80, 94, 112, 136 och 146 har steg A och B i Codex, en ny session per bild och två bilder in för B. Hela prompten kom fram i alla tolv nya körningar. Prompterna är dina STEP A och STEP B, med en kontextrad och en armrad per ruta. Från ruta 112 tar steg A också bort kundens hand. Kvoten gick från 0 till 5 % av veckan. Översikten ligger i `scen/3d/gennedbrytning/nyckel2/oversikt_alla.jpg`, och läsningen i `nyckel2/las/matt.json`.

**Utfall:**
- **Positionen:** efter passning ligger huvud och axlar inom 1–36 px i alla rutor utom 55. Där ligger huvudet 145 px fel, eftersom hon är djupt nedböjd och delvis utanför bild.
- **Proportionerna:** ben mot överkropp är 1,55–1,57 i rutorna 94–146 och 1,65 i rutorna 55–80, mot 1,53–1,63 i originalets läsning. Ruta 0 ligger på 1,74. Ruta 30 avviker med 1,96, alltså för långa ben, och en arm som ligger 284 promille från originalet.
- **Identiteten glider:** byxorna är svarta i rutorna 0–55 och mörkblå jeans med förkläde i 80–146.
- **Ruta 30 bör göras om eller strykas** innan den används som nyckelbild.
