# Projektinstruktioner

Läs `CLAUDE.md` för projektets delar och `byggsten/jutsu/README.md` före arbete med Jutsu.

## Skapa en scen från klippbiblioteket

En begäran att skapa en scen från ett befintligt klipp innebär som standard att klippets bildutsnitt, tagningar, personer och rörelser ska följa med. Ersätt inte detta med en egen översiktskamera och statiska dockor utan att användaren uttryckligen efterfrågar en fri eller statisk illustration.

- Inventera befintlig scenplan, källdata och ingest innan du bygger. Läs och återanvänd klippets kamera (position, rotation, lins, sensor och bildformat), tidsbas, tagningar, personidentiteter, synlighetsintervall och kroppsrörelser.
- Följ Notans adapter (`byggsten/jutsu/notan_export.py`, `notan_ops.py`) eller C-sketchs adapter (`c_ops.py`) efter underlagets struktur. Hårdkodade klippsökvägar måste anpassas; kör inte en annan films adapter oförändrad.
- För över kameror och kroppar i samma koordinatram. Berättelsemarkörer ersätter inte kameraklipp, rörelser eller synlighet.
- Dokumentera vad som är skattat, antaget eller manuellt korrigerat. Saknat underlag ska identifieras, inte tyst ersättas med påhittad geometri eller kamera.
- Rendera och granska representativa rutor från varje tagning samt relevanta övergångar mot samma rutor i originalet. Kontrollera utsnitt, lins, personernas placering/riktning, synlighet och kontakt med möbler/golv. Kontrollera exportens animation när animation levereras.
- Lyckad kodkörning eller rendering betyder inte godkänd scen. Om bilden inte kan hämtas/granskas ska visuell kontroll rapporteras som återstående; scenen är då inte verifierad som färdig.

Bakgrund 2026-11-16: Guacamole byggdes felaktigt som en fristående statisk illustration trots att en plan med fyra scener och 299 kameranycklar fanns. Upprepa inte detta avsteg.
