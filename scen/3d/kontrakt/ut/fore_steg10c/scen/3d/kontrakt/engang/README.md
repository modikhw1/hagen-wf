# engang: historiska engångsskript

Skripten här användes en gång för att ta fram ett visst resultat (textarbetet, golv- och trohetsfaserna, mallprov för notan och bar). De är inte underhållna. Inget i `scen/3d/kontrakt/` eller `scen/3d/ingest/` importerar dem eller anropar dem, och de är inte en del av pipelinen.

De hittar sina syskonmoduler (`textarbete`, `gemensamt`, `kompilera`, `trohet`) i mappen ovanför. Vill du köra ett av dem måste `scen/3d/kontrakt` ligga i `sys.path` och sökvägarna till `ut/` kan ha ändrats. Räkna med att de behöver lagas först.

Raderat är inget; de flyttades hit i en städning 10 nov 2026. Det som pipelinen använder ligger kvar i `scen/3d/kontrakt/` och står i tabellen i dess README.

Återupptagning av steg 10: `steg10_filer.py` bevarar original/radslut;
`steg10_koppla.py`, `steg10_kontroller.py`, `steg10_sista_kod.py` och
`steg10_bakkompat.py` är engångsinkopplingar och ska inte köras igen.
`steg10_prov.py` kör begärda prov sekventiellt från projektroten.
`steg10_dokument.py` uppdaterar dokumentationen en gång.
