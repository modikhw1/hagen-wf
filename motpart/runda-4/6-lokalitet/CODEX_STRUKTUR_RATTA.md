Du arbetar i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska.

Din granskning ligger i ut/codex/struktur_granskning.md (16 punkter). Rätta dem i struktur.py, modal_sam3.py och app.js. I app.js får bara det ändras som rör varianten Ls (struktur), punkt 3 och 9. Lt och de andra vyerna ska fungera exakt som förut.

Prioritet:
1. Fel 1–11.
2. Risk 12–13.
3. Risk 16: SAM 3:s bildrepresentation beräknas en gång per ruta.
4. Risk 14–15 om det går rent.

Punkt 3 (projektiv textur): välj den robustaste lösningen. Antingen räknas UV per fragment från originalkamerans projektion (lägg då kameran per tagning i struktur.json), eller så blir rutnätet så tätt att felet blir under 1 px vid 540 px bredd. Motivera valet.

VIKTIGT: kör INTE struktur.py, lokalitet.py eller modal mot klippen, och ändra inget under ut/ utom i en egen temporär katalog för prov. Jag kör pipen själv efteråt. Prova med syntaxkontroll och små syntetiska prov utanför ut/. Python finns i .venv/Scripts/python.exe, node finns i PATH (node --check app.js).

Leverans: kodändringarna, och som slutmeddelande en lista med punkt, fil:rad, vad du ändrade och hur du provade det. Sista raden: KLAR eller BLOCKERAD: <orsak>.
