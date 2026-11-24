# Lägesbild

Fast bakgrund för uppdragstagaren. Uppdatera bara genom ett uppdrag och med ägarens godkännande. Datum: 2026-11-12.

## Vad repot är
`hagen-wf` är en tillfällig plats för att forma om UX för CM:s flöde i LeTrend (det levande repot är `../hagen-ui`) med animerade, funktionella wireframes.

## Delar
- `app/`: wireframen, CM-flödet `#1`…`#6`, port 5180. Fryst.
- `video/`: inlärning av vad som förändras per klipp. Port 5181. Här sker arbetet framöver. Reglaget i `#v` är ett mätinstrument, inte appens layout; vänta på instruktioner innan layouten ändras.
- `scen/`: fristående experiment med scenmotor. Egen Python 3.12-venv, port 5190. Läs `scen/README.md` och `scen/RESULTAT.md`.
- `data/`: delas av `app/` och `video/`.
- `karta/`: vyer, objekt (ingestkön, strategin, klippen, kundsvar), beslut och öppna frågor. Börja i `karta/README.md`.
- `_utkast/`: första utkastet, byggs inte vidare på.

## Språk
Dokumentation och kommunikation på svenska.

## Läsordning för en ny uppdragstagare
1. `delegat/REGLER.md`
2. den här filen
3. `karta/README.md` och `karta/arbetssatt.md`
4. uppdraget
