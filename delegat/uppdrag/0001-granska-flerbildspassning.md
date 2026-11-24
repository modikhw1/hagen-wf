---
id: 0001
titel: Granska avbruten följdrättelse och förklara varför tagningarnas kameror inte är överens
status: redo
från: orkestratorn (Fable, ägarens session 12 nov kväll)
datum: 2026-11-12
följer:
tillåten_skrivning: [scen/3d/kontrakt/ut/diag_0001/]
---

## Mål
Det ska vara känt (a) om de halvfärdiga ändringarna i `scen/3d/kontrakt/boxpassning.py` och `scen/3d/kontrakt/mobellyft.py` är säkra att köra på, och (b) vad som orsakar residualer på 500–1000 px när en möbel passas mot flera tagningars lösta kameror i klippet `b-tilltal-ravara`.

## Bakgrund
Arbetet gäller scenmotorn i `scen/3d` (inte `app/` eller `video/`). Läs i den här ordningen: `scen/3d/NASTA.md` (avsnittet "Läge 12 nov kväll"), `scen/3d/PIPE.md` (Grundregeln, samt Öppet punkt 6), `scen/3d/kontrakt/ut/foremal_logg/LOGG.md` (de tre sista avsnitten).

Kort: varje tagning får sin kamera löst ur kroppen (`kontrakt/bildkamera.py`). Möbler och föremål med bildruta placeras mot dessa kameror. När samma möbel (till exempel `disk_C`) syns i flera tagningar ska ett gemensamt läge passas (`boxpassning.py`), men kamerorna pekar ut olika lägen. Ett vägval väntar på svaret: en gemensam mätt ram för alla tagningar, eller placering per tagning.

Ett följduppdrag (`scen/3d/CODEX-FLERTAGNING.md`) avbröts mitt i körningen. De två filerna hann ändras, snabbtesterna är gröna, men ändringen är inte provad i kedjan.

## Underlag
- `scen/3d/kontrakt/boxpassning.py`, `mobellyft.py`, `foremallyft.py`, `bildkamera.py`
- `scen/3d/CODEX-FLERTAGNING.md` (vad som skulle göras)
- Färdiga planer att mäta på utan omkompilering: `scen/3d/kontrakt/ut/b-tilltal-ravara_n06-mobel2/` och närliggande `b-tilltal-ravara_n06-*`
- Deklarationen: `scen/3d/ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`
- Python: venv i `scen/.venv`

## Gränser
- Ändra inga befintliga filer. Egna mätskript läggs som nya filer i `tillåten_skrivning`.
- Ingen kompilering till befintliga ut-mappar, ingen rendering, inga modell- eller nätverksanrop, inget Blender.
- Byt inte ut eller kopiera över moduler medan något test kör (en utbytt `skymning.py` har tidigare förgiftat tre körningar).
- Föreslå rättningar som text eller diff i svaret. Inför dem inte.

## Klart när
- Del A: varje ändring i de två filerna jämfört med avsikten i `CODEX-FLERTAGNING.md` är bedömd som färdig, ofullständig eller fel, med fil och rad.
- Del B: en tabell per tagning S1–S11 visar löst kamera (läge, yaw, pitch, FOV) i den gemensamma ramen och hur långt `disk_C`, `disk_A` och vågen hamnar från sitt passade läge när de lyfts ur just den tagningens bildruta (meter på golvet, inte bara px).
- Del B: tagningarna är grupperade efter vilka som är inbördes överens (inom cirka 0,3 m) och vilka som avviker, med den troligaste orsaken per avvikare: fel bildruta, fel kameralösning, fel personplats, möbeln bakom kameran eller deklarationens topologi.
- En rekommendation i högst fem rader: gemensam ram, placering per tagning eller en blandning, och vilken enskild mätning som skulle avgöra det.

## Leveransform
`delegat/svar/0001-granska-flerbildspassning.md` enligt mallen, högst cirka 80 rader. Tabeller och skript i `scen/3d/kontrakt/ut/diag_0001/`, länkade från svaret.
