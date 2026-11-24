# Uppdrag: granskning omgång 2 av genererade rum (V2), bara de tagningar som bytts ut

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Svara på svenska. Ändra ingen kod.

Bakgrund: läs din egen förra granskning `ut/agy/rumshjarna/GRANSKNING.md`. Alla 8 falskt släppta var ankarbetingade. Hjärnan genererar nu en oberoende kandidat för de tagningarna också och väljer den som har minst lokal förskjutning mot originalet (DIS-flöde). Grinden kräver dessutom att förskjutningen är högst 3 px och att djupskalan är rimlig. Valet och grindens dom finns i `ut/<klipp>/lokalitet.json` → `tagningar.<sid>.rumshjarna_fyllnad`: `kalla`, `val`, `forskjutning_px`, `tillit` och `avvisad_av`.

Granska samma sak som förra gången (utsnitt, påhittat, borttaget fel, rimligheten bakom personen, och användbar ja/delvis/nej), men bara för de här tagningarna:
- duepiani: s5, s6, s7, s9, s12, s1, s3, s10
- 08burgerkebab: s6, s7, s1, s5
- babasburgers: s5, s1

Bilder: original `ut/rumshjarna/<klipp>/<sid>_orig.png`, och den valda V2-bilden registrerad till originalets utsnitt `ut/rumshjarna/<klipp>/fyllnad/<sid>_v2.png`.

Bedöm särskilt det som syns bakom personens silhuett. Det är bara där hypotesen används i 3D. Fel i synliga delar utanför personen påverkar inte 0.0.

Leverans:
- `ut/agy/rumshjarna/granskning_r2.json` med samma postformat som `granskning.json`, plus `grind_avvisad_av`.
- `ut/agy/rumshjarna/GRANSKNING_R2.md`: korstabell mellan grind och omdöme för de här 14 tagningarna, en jämförelse med förra omgången och kvarvarande allmänna förslag. Max 40 rader.

Sista raden: `KLAR` eller `BLOCKERAD: <orsak>`.
