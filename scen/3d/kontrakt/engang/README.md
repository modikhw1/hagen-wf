# engang: historiska engångsskript

Skripten här användes en gång för att ta fram ett visst resultat (textarbetet, golv- och trohetsfaserna, mallprov för notan och bar). De är inte underhållna. Inget i `scen/3d/kontrakt/` eller `scen/3d/ingest/` importerar dem eller anropar dem, och de är inte en del av pipelinen.

De hittar sina syskonmoduler (`textarbete`, `gemensamt`, `kompilera`, `trohet`) i mappen ovanför. Vill du köra ett av dem måste `scen/3d/kontrakt` ligga i `sys.path` och sökvägarna till `ut/` kan ha ändrats. Räkna med att de behöver lagas först.

Raderat är inget; de flyttades hit i en städning 10 nov 2026. Det som pipelinen använder ligger kvar i `scen/3d/kontrakt/` och står i tabellen i dess README.

Återupptagning av steg 10: `steg10_filer.py` bevarar original/radslut;
`steg10_koppla.py`, `steg10_kontroller.py`, `steg10_sista_kod.py` och
`steg10_bakkompat.py` är engångsinkopplingar och ska inte köras igen.
`steg10_prov.py` kör begärda prov sekventiellt från projektroten.
`steg10_dokument.py` uppdaterar dokumentationen en gång.

Steg 10c (lokalt, utan rendering):

- `steg10c_filer.py`: säkerhetskopior i `ut/fore_steg10c/` och bevarade radslut.
- `steg10_platsreferens.py`: den historiska fullständiga platsreferensen;
  redan körd, vägrar skriva över referensen.
- `steg10c_synka.py`: redan utförd synk av tider.json mot sparade slutvärden.
  Kör inte igen utan att granska proveniensen.
- `steg10c_mata.py`: en edit eller testmodul åt gången, tider/loggar i
  `ut/steg10c/`. `fore` läser den frysta baslinjekoden, `snabb` använder den
  nya flaggan, `efter` använder dagens kod och de snabba editproven.
- `steg10c_mhr.py`: läsinventering som endast skriver `MHR-BEROENDEN.md`.

Exakta körkommandon och senaste tillstånd finns i `../STEG10C-LOGG.md`.
