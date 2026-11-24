# Seedance-test 1 (9 nov 2026)

`gen_test1.mp4` är den genererade videon och `jamforelse_test1.mp4` visar källa | blockout | genererad med originalljud.

- Modell och inställningar: Seedance 2.5 via ElevenLabs MCP, 480p, 9:16, 6 s, 24 fps, 9 377 krediter.
- Indata:
  - referensbilder: `start_S1.png` (PS2-startbild från Codex) och mallarna A/B;
  - referensvideo: `rorelse_0-6s.mp4` (blockout);
  - referensljud: `ljud_0-6s.wav` (original);
  - prompt: PS2-mallen med låsta tider (finns i flödet).
- Klipptider: 2,458 / 3,792 / 5,833 s, mot målen 2,433 / 3,800 / 5,700 s.
- Ljudet: Seedance gjorde om repliken med liknande röster och nästan samma ordtider (±0,1 s) men fel ord. Det korrelerar 0,81 mot originalet vid 70 ms förskjutning, så originalljudet läggs på i efterhand.
- Ägarens bedömning: kedjan fungerar, men indatat (wobbliga, onaturliga dockor) begränsar.
