# hagen-wf

Tillfällig plats för att forma om UX för CM:s flöde i LeTrend (repot `../hagen-ui`) med animerade, funktionella wireframes.

**Börja i [LAGE.md](LAGE.md) (19 nov 2026) för den aktuella helhetsdeklarationen över repot och Förvärldens kärna (`forvarld_karna/`), samt [karta/README.md](karta/README.md) för CM-vyerna.**

Repot består idag av följande huvuddelar:

- **Förvärldens Kärna, [`forvarld_karna/`](forvarld_karna/ARKITEKTUR.md)** (sedan 18–19 nov 2026): **Den aktiva, verifierade 4-lagerspipen** från råvideo-ingest till 3D-rumspussel (`rums_pussel.py`), `scenpaket/2` med 26-bens `T1`-armaturer och kvalitetsgrindar `G1–G7 = 0 fel` (`scen_brygga.py`), samt destillerad `AttitydProfil`, Jev-yta och attityd-ärvande semantisk manipulation (`mening_motor.py`). Ersätter de äldre klipp-specifika skripten i `scen/3d/` och samlar guldkornen ur `byggsten/`.
- **Byggstenar, [`byggsten/`](byggsten/README.md)**: Modulära delar där `byggsten/brygga/` (`grindar.py`, `emit_bpy.py`) och `byggsten/hand/` (kopplingen till 1 480 formatkort, takter, kundlinje, Jev och WebGL-regibord) samverkar direkt med `forvarld_karna/`.
- **Wireframen, `app/`**: CM-flödet `#1` … `#6` på `localhost:5180`. Pågående och fryst tills vidare. Videokoden i `app/` rörs inte längre.
- **Videodelen, `video/`**: inlärningen av vad som förändras per klipp (längd, antal scener, sammansättning, intention), balanserad mot flera slutmål och enkel för CM att arbeta i. Körs på `localhost:5181`. Här sker arbetet framöver. Reglaget i `#v` är ett mätinstrument och inte hur appen ska se ut. Vänta på instruktioner innan dess layout ändras.
- **Äldre scenexperiment, `scen/`** (7–17 nov 2026): fristående experiment vars 3D-skriptkedja i `scen/3d/` nu har ersatts av `forvarld_karna/`. **Obs:** Råa per-tagnings-caches i `scen/3d/ingest/ut/<klipp>/` samt Python 3.12-miljön i `scen/.venv` används av `forvarld_karna/`.
- `data/` i roten delas av båda (`../data`).
- Det levande repot är `../hagen-ui`.
- Arbetssätt: [karta/arbetssatt.md](karta/arbetssatt.md). En del i taget, och fråga före bygge.
- Första utkastet, som inte byggs vidare på: `_utkast/cm-flode.html`.
