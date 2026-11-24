# Beslut

I ordning. Varje rad säger vad vi bestämde och varför. Ändras ett beslut skrivs det nya under och det gamla stryks.

## 2026-10-30

1. **Bygg en del i taget.** Första utkastet (`_utkast/cm-flode.html`) visade allt på en gång och var för mycket. Stegen 1–6 i `app/src/step.js` gör att varje del kan kollas av för sig.
2. **Wireframe som webapp.** Vite + React, dnd-kit (drag), motion (animation) och Balsamiq Sans. Platshållare i stället för video. Datamodellen bygger på scener med längd, alltså samma sak som en enkel ffmpeg-del ger.
3. **Kundens tidslinje är startsidan.** Det är ingen dashboard. Jobbet syns på tidslinjen själv.
4. **Ingen flik för snabbväxling.** En kund per pass, välj vid ingången.
5. **Vänster är bänken, inte historiken.** Historiken lästes som en shortlist. Bänken visar CM:s relation till klippet: grått original eller svart, CM:s eget.
6. **Historiken är svag och bara de 3 senaste.** Statistik hör inte till det här flödet.
7. **Inga symboler för "sedan sist" i sidhuvudet.** Märkena sitter på korten.
8. **Mixen är en blandning, inte en varning.** Underhållning, info och marknadsföring mot en baslinje. Ingen röd färg.
9. **Energi och längd hör inte hemma i planöversikten.** Hur många som syns gör det.
10. **Trion:** 1 och 3 kommer från bänken. Hela trion följer med när platsen flyttas. När 2 tas bort blir 1 och 3 lösa och går inte till bänken.
11. **Drag från planen till ett kort byter plats i ordningen** och ersätter aldrig huvudkortet. Att byta huvudkort sker inom trion.
12. **Dubbelklick roterar trion** (2 → 3 → 1 → 2). Att dra 1/3 upp på 2 finns kvar.
13. **1 och 3 i en ram under kortet**, som fälls ut vid hovring och dras in snabbt. Prövat och förkastat:
    - alternativ som kanter inne på kortet: för inklämt
    - fingeravtryck på kortet vid hovring: typen ska stå under
14. **Mixspåret är alltid synligt under planen. Balansen är tyst** och fälls ut vid hovring, fästs med klick.
15. **Sidhuvudet har fast höjd.** Annars hoppar korten när balansen öppnas.
16. **Nytt material landar alltid på bänken.** Planen tar bara godkända klipp.
17. **Ingest i kö, ett i taget, 50–70 s.** En spellista blir flera klipp. En länk som dras in startar direkt. Plus och klistra in går via popup.
18. **Två godkännanden:** den neutrala versionen (Granskning), sedan tillägg och ändringar (Anpassning, ffmpeg).
