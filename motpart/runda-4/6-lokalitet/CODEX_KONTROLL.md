# Codex-uppdrag: motprov av lokalitet/1 (gpt-6-astra xhigh)

Du granskar en allmän rumsingest i `motpart/runda-4/6-lokalitet/`. Det är ett motprov enligt `motpart/PROTOKOLL.md`: varje påstående prövas med ett körbart test som kan fälla det. Ändra inte i `lokalitet.py`, `observera.py`, `modal_obs.py` eller `ut/` (utom din egen mapp `ut/codex/`). Starta inga Modal-jobb. Varje enskilt kommando ska ta under 3 min. Väntan förbrukar kvot.

Läs först `RAPPORT.md` och `README.md` i mappen och docstringen i `lokalitet.py`.

## Påståenden att pröva

1. **Ingen klippspecifik kod.** Sök i `lokalitet.py`, `observera.py` och `modal_obs.py` efter klippnamn, tagnings-id och konstanter som bara passar ett klipp. Redovisa varje antagen konstant (t.ex. bänkhöjd 0,90, 20° uppåt-prior) och om den är uttalad i rapporten.
2. **Determinism.** Kör `.venv/Scripts/python.exe -I -X utf8 -W ignore lokalitet.py <nyckel> --obs gpu` två gånger för `babasburgers`. Jämför SHA256 för `ut/babasburgers/paket_L.json`. Kopiera först undan originalet till `ut/codex/` och återställ det efteråt.
3. **Lodlinje mot oberoende vittne.** Skatta kamerans lutning per tagning ur flyktpunkter för vertikala linjer (OpenCV LSD eller Hough på nyckelrutorna, som finns i `ut/<nyckel>/obs_gpu.json`). Läs videon från `data/format/kontroll/klipp/`. Jämför med `lutning_grader` i `ut/<nyckel>/lokalitet.json` för alla tagningar i de fem klippen. Lista avvikelser över 10°. Ange var flyktpunkten saknas (t.ex. bilder ovanifrån) i stället för att gissa.
4. **Diagnosen larmar.** Gäller `spridning_per_ruta_grader` som tillförlitlighetsmått? Visa en tagning där spridningen är stor och avvikelsen mot vittnet i punkt 3 också är stor, och en där båda är små. Saknas samband: säg det.
5. **Fotkontakt.** Mät i `ut/duepiani/lokalitet.json` hur `fot_over_golv_m` och `kamerahojd.fotter_m` mot `m` förhåller sig. Är fötterna på golvet bara för att skalan tvingas dit (tautologi), eller finns ett oberoende stöd? Förklara med källrader.

## Leverans

`ut/codex/MOTPROV.md`: en tabell med påstående, test (kommando), utfall och status (står, fallit, delvis), plus högst fem rader om vad som är svagast och vilket test som bör bli permanent. Fakta, inte beröm.
