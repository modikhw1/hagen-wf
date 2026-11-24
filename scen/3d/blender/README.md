# Blender som förvisualisering (9 nov 2026)

Blender bestämmer **var** saker finns och **när** de händer. Videomodellen (Seedance/Kling/Veo) bestämmer **hur det ser ut**, till exempel i PS2-stil enligt `../unemployed_corp/`.

**Grundregel (ägaren):** originalljudet ska gå att lägga under och passa kroppar och munnar. Därför är allt bildruteexakt över hela tagningen, från start till slut, med klipp på samma bildrutor som three.js-spelaren och källan. Det räcker inte med generella bilder per tagning.

## Kedjan

```
scen3d.json ──bygg_scen.py──► Blender: rum, rekvisita, kamera per tagning (markörer = klipp), originalljud i VSE
three.js-spelaren ──baka.mjs (Codex)──► bake.json ──importera_bake.py──► X Bot-dockor, varje bildruta (kropp, händer, mun)
Blender ──rendera.py──► ut/: blockout.mp4 (+ originalljud), tagning_<id>.mp4, ljud_<id>.wav, forsta_<id>.png, djup_<id>.png, promptpaket.md
promptpaket.md + PS2-SOP ──ChatGPT──► prompt ──Seedance m.fl. (startbild + videoreferens + ljudreferens)──► rendering
```

## Köra

- Live: Blender öppet med MCP-tillägget. Kör `runpy.run_path(r'...\blender\bygg_scen.py', init_globals={'ARGV': []}, run_name='__main__')` via MCP.
- I bakgrunden: `blender -b --factory-startup --python scen/3d/blender/bygg_scen.py -- --spara scen/3d/blender/scen.blend`.
- Rendering: `rendera.py` (`--bara-bilder` för bara still- och djupbilder, `--skala 50` för halv upplösning).

## Status (9 nov 2026)

| Del | Läge | Siffror |
|---|---|---|
| `bygg_scen.py` (Claude) | ✔ | Ger 20 set, 15 rekvisita och 7 kameror. Klippen ligger på bildrutorna 0/73/114/171/256/281/337, totalt 383 bildrutor (12,767 s). Kamerorna stämmer mot källan (`verifiering/kameror_mot_kalla.jpg`). Bygget tar cirka 45 s med dockor. |
| Bakning av rörelsen (Codex: `baka.mjs`, `importera_bake.py`, `verifiera_bake.py`) | ✔ | Ledfelet mot three.js är i median 0,0007 mm och högst 0,003 mm. Silhuettöverlappet är 0,985–0,996 per tagning. Munnen stämmer exakt, och webbspelaren är oförändrad (42 bilder pixelidentiska). Se `BAKE.md`, `LOGG.md` och `verifiering-bake.json`. |
| Rekvisita i händerna | ✔ | Nycklas per bildruta ur `bake.json` (`rekvisita_fran_bake`). |
| `rendera.py` | ✔ | `ut/blockout.mp4` har 383 bildrutor med originalljudet (utfyllt med 21 ms tystnad i slutet). Den renderas på cirka 2 min 20 s i 576×1024. Jämförelsen mot källan finns i `ut/jamforelse.mp4`. |

Bakningen verifierar överföringen från three.js till Blender. Hur väl själva spårningen stämmer mot källan är fortfarande samma som i Scen3D, alltså fas 1–4.

## Kontrakt för vidare bygge

- Koordinater: three (Y upp) blir Blender `(x, −z, y)`. Yaw är samma vinkel kring Z. Kamerorna använder three:s lookAt och vertikal fov.
- Objektnamn: set- och rekvisita-id (`table:A`, `A:can`) som tomma föräldrar med `semantik` (JSON). Kamerorna heter `kam:S1` …, och dockorna `actor:A` … (från Codex).
