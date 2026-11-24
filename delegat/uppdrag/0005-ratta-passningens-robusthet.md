---
id: 0005
titel: Gör klart följdrättelsen i box- och möbelpassningen
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0001
tillåten_skrivning: [scen/3d/kontrakt/boxpassning.py, scen/3d/kontrakt/mobellyft.py, scen/3d/kontrakt/foremallyft.py, scen/3d/kontrakt/test_snabb.py, scen/3d/kontrakt/ut/fore_passning_0005/, scen/3d/kontrakt/ut/foremal_logg/LOGG.md]
---

## Mål
Passningen ska tåla dåligt indata utan att ge ett sämre läge än den fick: de brister svar 0001 listar under Del A är rättade och täckta av snabbtest.

## Bakgrund
`delegat/svar/0001-granska-flerbildspassning.md`, Del A, anger fil och rad. Uppdraget rättar bara mekaniken. Att bildrutorna och linsen är fel är andra uppdrag (0003, 0004), och målet här är inte lägre residualer på `b-tilltal-ravara`.

Kör efter 0002–0004 om de redan ligger före i kön; uppdraget beror inte på dem.

## Underlag
- Svar 0001 och `scen/3d/kontrakt/ut/diag_0001/tabeller.md`
- Ursprunglig avsikt: `scen/3d/CODEX-FLERTAGNING.md`
- Testkommandon och mönster: senaste avsnitten i `scen/3d/kontrakt/ut/foremal_logg/LOGG.md`

## Att rätta
1. `boxpassning.py`: en helt beskuren box hoppas över för den tagningen (`anvand: false` med orsak) i stället för `ValueError` som avbryter hela passningen.
2. `boxpassning.py`: startpunkten väljs inte ur en enda "tillförlitligast" box. Använd medianen av enbildslägena, eller den box som är mest överens med de andra. Avvikande boxar (långt från medianen på golvet) viktas ned eller utesluts, och det loggas vilka.
3. `boxpassning.py`: sökgränserna följer deklarationens ordning kamera–möbel–person redan i passningen, så att `lyckad` gäller det läge som faktiskt används.
4. `mobellyft.py`: kamerans nedre gräns tas aldrig bort. Ryms inte båda marginalerna behålls möbelns tidigare läge, med `granskonflikt: true` och orsak. Ingen möbel får hamna inuti en kamera.
5. `mobellyft.py:114–128`: dubbletten av `boxpassning.py:97` tas bort till förmån för den skyddade versionen.
6. `foremallyft.py`: ersättningsstöd när `pa` pekar på något som inte byggs (följdrättelse 2 i `CODEX-FLERTAGNING.md`).
7. `test_snabb.py`: prov för punkterna 1–4 och 6.

## Gränser
- Bara filerna i `tillåten_skrivning` ändras. Kopiera först de fyra filerna i nuvarande skick till `scen/3d/kontrakt/ut/fore_passning_0005/kod/`.
- Ändra inget medan ett test eller en kompilering kör. Verifiera med tom cache.
- Ingen rendering, inga nätverksanrop, inget Blender.
- Notans och guacamoles planer får inte ändras av rättningen (de har inga bildrutor för möbler). Visa det.

## Klart när
- `test_snabb.py` och ingesttesterna (`test_deklaration.py`, `test_rum.py`, `test_scenbrief.py`) är gröna, med antal.
- På en minneskopia av `b-tilltal-ravara_n06-fler/narvaro/plan.json`: ingen möbel har negativ kameramarginal, S6 är utpekad som avvikande box i loggen, och `disk_C` ligger närmare medianen utan S6 än före.
- Notan och guacamole: `prepare` ger oförändrad `plan.json` jämfört med före rättningen (byteidentisk, eller skillnaden förklarad).
- Ett avsnitt i `scen/3d/kontrakt/ut/foremal_logg/LOGG.md` i samma form som de tidigare.

## Leveransform
`delegat/svar/0005-ratta-passningens-robusthet.md` enligt mallen, högst cirka 50 rader.
