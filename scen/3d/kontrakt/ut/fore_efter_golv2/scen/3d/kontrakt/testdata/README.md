# Fryst stödpose

`stod_s1_fore_jamn.npz` är notan S1 ruta 30 före jämn-passets omkörning.
Pose, Q och T beskriver precis det mätunderlag som de befintliga stödproven
skrevs för. Ankare, källfiler och hash finns i JSON-filen bredvid.

Tidigare läste dessa prov en föränderlig ingestfil. Efter omkörningen låg
knäna i den valda rutan under det gamla platsgolvet, och den korta vaden
kunde nå golvet i stället för att hänga. Det var andra provfall än namnen
och förväntningarna beskrev. Frysningen behåller de ursprungliga kraven,
utan ändrade toleranser eller ändrad stödberäkning.

`test_alla_notans_rutor_har_fasta_ben_skyddad_overkropp_och_sula_over_golv`
går fortfarande igenom dagens notan-mätningar. Den nya källkopian
`exempel/notan/kalla_jamn.json` har aktuella mätfilshashar; den gamla
`kalla.json` och barklippets exempel är oförändrade.

Platsprovet jämför två nya körningar byte för byte, både med historiska
indata (`test_plats_snapshot.py`) och med dagens mätningar. Den historiska
körningens hela plats.json jämförs också med den frysta
`plats_automatisk_fore_jamn.json`, framställd av arkivets oförändrade solver.
`plats_automatisk_fore_jamn.underlag.json` låser kod och 507 indata med SHA256. En ny, automatisk
platslösning ska inte jämföras byte för byte med en senare granskad och
anpassad filmplats. Filmens kamera/person/tid jämförs i stället exakt mot
`ut/notan/jamn_tom/plan.json` i `engang/prop_regression.py`.
