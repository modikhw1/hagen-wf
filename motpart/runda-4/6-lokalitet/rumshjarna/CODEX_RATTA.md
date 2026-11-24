Du arbetar i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska.

Din förra granskning ligger i ut/codex/rumshjarna/MOTPROV.md (12 punkter). Rätta nu punkterna i koden enligt nedan. Ändra bara lokalitet.py, rumshjarna/hjarna.py, rumshjarna/likhet.py, rumshjarna/rest.py och modal_obs.py (bara entrypointen bildobs, om det behövs).

VIKTIGT: kör INTE lokalitet.py, hjarna.py, likhet.py eller modal mot klippen. En annan granskare läser ut/ just nu, och filerna där får inte ändras under testet. Kontrollera dina ändringar med syntaxkontroll (python -c "import ast; ...") och små syntetiska prov i en temporär katalog utanför ut/. Python finns i .venv/Scripts/python.exe.

Punkter:
1. Kravet på djup bakom personen (×1,15) i fyllnaden ur andra rutor ska bara gälla person0, inte ringen.
2. Rotation mellan nyckelrutor: gör det konservativt. Nyckelrutor vars kamerarotation mot mittrutan överstiger 0,5° används inte som observerad fyllnad i bygg_nat. Hitta var main beräknar rotationen per nyckelruta (L9/L9b). Dokumentera i en kommentar att återprojicering är nästa steg.
3. Proveniens per triangel: en triangel med något hörn i en antagen eller genererad cell (-3/-4) ska tillhöra den biten (antagen går före genererad), inte majoritetens observerade instans.
4. Skalgrinden: bedöm modellernas relativa skala mellan originalets råa MoGe-djup och V2:s MoGe-djup, utan kroppsskala och brännviddsomräkning. Spann 0,6–1,6. Behåll kz (mot Zc) för att tillämpa djupet.
5. Cache: codex_bild återanvänder bara en bild om den sparade json-filen har samma prompt_sha, samma referensbilder och samma innehållshash för indatabilderna (lägg till de fälten). Annars genereras bilden på nytt och den gamla döps om till *.gammal.png. ruta_png skriver en sidofil med rutnumret och tar en ny ruta om numret ändrats.
6. Kandidatvalet: en ankarkandidat över 2,0 px får inte väljas i reservgrenen när en oberoende kandidat finns.
7. Förskjutningsgrinden i lokaliteten: räkna rest_px i lokalitet.py med samma synlighetsmask som djup- och kantgrinden (utan person, utan överlagrad text), i full upplösning, i stället för att läsa värdet ur fyllnad.json. Hjärnans val mellan kandidater får använda sin egen mask.
8. likhet.betingat(): läs proveniensen ur fyllnad.json, alltså den faktiskt valda bildens källa (_k<ankare> i filnamnet).
9. Risk: kantpixlar tas bort bara om det också finns ett djupsprång i originalet (cellen ligger framför sina grannar utanför personen), inte bara framför hypotesen.
10. Skicka originalets verkliga mått till bildobs och kontrollera formerna före användning. Avvisa vid fel form med en orsak.
11. Registreringen ska också warpa en giltighetsmask (noll utanför källbilden). Spara den som <sid>_v2_giltig.png och uteslut ogiltiga pixlar från grind och fyllnad i lokaliteten.
12. Modal: radera inte gamla obs-filer innan körningen lyckats. Kontrollera returkoden och att varje förväntad .obs.npz är nyare än sin png. Avbryt med tydligt fel annars.

Leverans: kodändringarna, och som slutmeddelande en lista med punkt, fil:rad, vad du ändrade och hur du provade det. Sista raden: KLAR eller BLOCKERAD: <orsak>.
