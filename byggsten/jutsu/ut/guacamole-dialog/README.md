# Guacamole-dialog – Jutsu

## Korrigerad scen, revision 5 (2026-11-16)

Revision 1 nedan är den ersatta statiska illustrationen. Revision 5 följer nu `scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_data/plan.json`. Denna version har samma kameror och kroppar som `skymning`, men den redan korrigerade massiva bardisken. Inga lånade närvarorörelser används.

- Fyra tagningar: [0,88), [88,139), [139,190), [190,299), 30 fps, 576 × 1024.
- 299 kamerarutor lästes. Identiska värden inom tagningarna komprimerades till åtta gränsnycklar utan ändring av de 299 evaluerade kamerarutorna.
- 408 personrutor överfördes, 18 leder per personruta, via `trohet.ruta`. Rörelse och synlighet följer planen. Gemensam Blender-animation med 95 action slots.
- Jutsus fyra klipp registrerade även i `blockingStudioTimeline`. Startbild ruta 30.
- Jutsu-renderingar granskade mot originalet vid 30, 110, 165, 245 samt 0, 87, 88, 138, 139, 189, 190, 298. EEVEE-ljuskontroll vid 30.
- Numerisk kontroll på servern: kameraavvikelse mot exporterade värden < 1e-7, linsavvikelse 0, huvudled < 1e-7 m; inga synlighetsfel på kontrollrutorna. Lokal kamerakontroll mot den okvantiseringade planen < 0,0005 i matriselement.
- Bildhämtningen löstes genom Higgsfields `sandbox_exec` med `image_paths`; det lokala nätverksfelet blockerar inte längre granskningen.

### Kvarstående begränsningar

Scenen följer den skattade planen, inte en exakt rekonstruktion av alla originalpixlar. Rummets detaljer saknas, dockorna har förenklade huvuden/händer, vissa gester avviker och personalens underkropp i s4 har brister i källdata. Dessa är inte korrigerade genom påhittade rörelser.

Den faktiska hostade GLB-exporten i revision 5 delar fortfarande den gemensamma animationen i 86 objektklipp. Geometri och synlighetskanaler klarar kontroll, men testet för en gemensam exporttidslinje fallerar. Synkron uppspelning i Jutsus förhandsvisning är därför inte verifierad. Blender-scenen är verifierad separat. Lokal `preview/delivery.glb` har en gemensam animation och klarade återimport med kontroll av position/synlighet vid tolv rutor; rapport i `glb_local_audit.json`. Ändra inte serverns exportmekanik genom runtime-hookar.

### Återskapa och granska

Kör `scen/.venv/Scripts/python.exe byggsten/jutsu/guacamole_pipeline.py`, därefter lokal Blender med `ut/guacamole-dialog/local_preview.py`. Kör `guacamole_verify.py` mot sparad `preview/scene.blend` för lokal exportkontroll. Jutsu-operationerna körs i ordning med färska revisions-/sekvenslås; `op4_delivery.py` dokumenterar sista metadatasteget och ljuskontrollen. `preview/original_vs_scene.jpg` visar fyra jämförelser.

## Historik: första bygget

Skapad 2026-11-16 via Higgsfield MCP.

Projekt: https://higgsfield.ai/3d-jutsu/7ac98ac4-cd30-4411-a5d3-11c26c0e8711

Revision 1, operation `guacamole-blockout-02`. 39 objekt, fyra berättelsemarkörer, 30 fps, rutor 0–298. Statisk blockning, ingen animation eller ljudöverföring.

Källor: `scen/3d/kontrakt/ut/e-dialog-guacamole/kalla.json`, `scen/3d/kontrakt/rumsmall/dekl_e-dialog-guacamole-tagningar.json`, originalbild vid 1 sekund ur `scen/klipp/e-dialog-guacamole.mp4`.

Förenklade dockor, material och antagen översiktskamera. Rummets dimensioner kommer från befintlig rumsmall. Inte en exakt rekonstruktion av originalbilden.

Servern verifierade kamera, diskens dimensioner och markörer. PNG-render 360 × 640 skapad. Visuell granskning återstår: artefaktens nedladdning misslyckades i klienten.

`build.py` innehåller den körda byggkoden.
