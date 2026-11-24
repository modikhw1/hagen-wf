Klart. Skymningen använder nu verkliga 3D-segment och bildbekräftade möbler stryks inte tyst.

- S11/ruta 439: gamla måttet gav 355 träffar (166 höft, 189 falska handträffar); nya måttet behåller endast de 166 riktiga höftträffarna.
- 3D-testet finns i [test_snabb.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/test_snabb.py:29).
- Kärnfixen finns i [skymning.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/skymning.py:35), och möbelordningen i [kompilera.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kompilera.py:652).
- Tester: `test_snabb` 16, `test_deklaration` 7, `test_rum` 3, `test_scenbrief` 5 — alla OK.
- Orkestrator: `python klipp_kor.py b-tilltal-ravara prepare --variant n06-skymning --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`, sedan samma med `render`.
- Notan/guacamole-kommandon och full numerisk rapport finns i [LOGG.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/skymning_logg/LOGG.md:1).
- Ingen full kompilering, rendering, modellkörning eller Blender kördes.