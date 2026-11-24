# Ursprungligt uppdrag (19 nov 2026, 21:49), ordagrant

Du är spår C i runda 3 av ett motpartsprotokoll i repot C:\Users\praiseworthy\Desktop\hagen-wf (Windows, Git Bash/PowerShell; Python-miljö: `scen\.venv\Scripts\python.exe`, sätt `PYTHONIOENCODING=utf-8`). Skriv allt på svenska med korrekt å/ä/ö.

LÄS FÖRST: `motpart/runda-3-opus/UPPDRAG.md`, `motpart/runda-1-claude/SYFTE.md` (hela, särskilt A10, A13 och §4 K1, K3, K5, K7), `LAGE.md`, `byggsten/hand/README.md`, de 21 CM-meningarna i `UTMANING.md` (hitta den med Glob; troligen under `byggsten/` eller `karta/`), `scen/3d/PIPE.md` (relevans: bär/sätter/stryks; "Meningen bärs av …"), `forvarld_karna/mening_motor.py`, `motpart/runda-1-claude/MENING.md` (C4), samt minnesfilerna i `C:\Users\praiseworthy\.claude\projects\C--Users-praiseworthy-Desktop-hagen-wf\memory\`: `project-liggaren.md`, `project-ryggrad-och-intention.md`, `feedback-generativt-bara-for-1till1.md`, `feedback-kansla-ar-helkropp.md` och `project-forvarlden-och-jev.md`.

DITT MÅL: kärnan i produkten, där CM:s mening blir en ändring. Runda 2 rörde det aldrig. I dag täcker kärnans Jev-yta ungefär 5 av 21 CM-meningar (kroppens sätt). Det CM oftast ber om är struktur, föremål och plats, och det saknas.

Bygg i `motpart/runda-3-opus/C-cm-mening/`:
1. **Router.** En mening går först till rätt nivå: ryggradsnivå (struktur, takter, ordning; finns i `byggsten/hand/`), scenlager (plats, föremål, kropp) eller medielager (spår D bygger det, så routa dit och markera "ej i detta spår"). Där det inte går blir det ärligt nej eller motfråga. Den som ändrar typen ("gör om till en sketch där gästen blir lurad") ska stoppas.
2. **Liggaren och relevansen (K5).** Innan något ändras listas det som bär klippet. En ändring som skulle ta bort det som bär ger en varning eller ett stopp, aldrig en tyst förlust.
3. **Lagliga drag på `scenpaket/2`.** Utöka dragytan till föremål och plats (flytta, byta, ta bort eller lägga till rekvisita; byta plats för en interaktion i rummet; hålla kamerakompositionen). Inget generativt, ingen spegling (K7). Kroppsdrag ärver attityden. Kom ihåg ägarens dom att ledförskjutning utan databuren stil ser ut som "en apa": påstå aldrig att en känsla är levererad på egna ledmått. Säg vad som är kinematisk platshållare.
4. **Mätning:**
   - K1: kör de 21 meningarna plus nya meningar som du INTE skriver själv. Använd fryst, hashad lista ur repots befintliga CM- eller ägartexter (sök i `karta/`, `byggsten/hand/`, `delegat/`). Om det inte räcker: redovisa att K1 kräver ägarens lista och mät på det du har, med tydlig märkning "skrivna av byggaren".
   - Klassning: rätt utförd / ärligt nej eller motfråga / tyst fel.
   - Räkna med att du kan ha fel om vad som är "rätt". Lägg facitförslag öppet så att ägaren kan döma.
   - K3: latens i median och p90 per nivå, mätt från mening.
   - K7: logg av alla anrop.
   - Kör på paketen i `forvarld_karna/ut/<klipp>/paket.json`. Om spår B har lagt bättre paket i `motpart/runda-3-opus/B-nasta-klipp/ut/`, kör även på dem och redovisa båda.
   - Lägg en minimal förhandsvisning per ändring (före/efter-bild) som ägaren kan döma blint (K2-förberedelse: slumpad ordning, dold nyckel i separat fil).

GEMENSAMMA REGLER (gäller alla spår):
- Skriv BARA i `motpart/runda-3-opus/C-cm-mening/`. Ändra inget i `forvarld_karna/`, `byggsten/`, `scen/`, `data/`, `video/`, `app/`, `motpart/runda-1*`, `motpart/runda-2*` (importera och kopiera gärna). Radera ingenting någonstans.
- Inga nya betalda API-anrop. Det gäller också LLM-anrop via Gemini, beacon eller Codex. Behövs en språkmodell för routern: bygg en deterministisk eller lokal väg först och skriv exakt var en LLM skulle behövas och vad den skulle kosta. Lokala modeller går bra.
- Ingen klippspecifik kod. Egna mått är diagnos, inte krav. Säg aldrig "lyckat" utifrån egna grindar.
- Varje påstående har bevis (fil:rad, kommando, bild) och ett motprov. "0 fel" räknas bara om grinden visats kunna larma. Granska varje bild du hänvisar till med Read-verktyget innan du påstår något om den.
- Parallella spår: A (domare: `motpart/runda-3-opus/A-domare/README.md` beskriver mått, bland annat bevarande och K7-spärr; använd dem om de finns), B (allmän ingest, bättre paket) och D (medielager: skärmtext, ljud, mat/B-roll, montage och manus). Lägg routerns gränssnitt mot medielagret i `C-cm-mening/README.md` så att D kan ansluta.

AVSLUTA med `motpart/runda-3-opus/C-cm-mening/RAPPORT.md`: täckning per meningskategori före och efter, utfallsklassning, latens, K7-logg, vad som är platshållare, vad som inte hanns med och dina svagaste punkter. Ditt slutsvar till mig: max 25 rader plus sökväg.