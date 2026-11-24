## Slutrapport

- Orsak: [skarmtext.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/fore_text_s4/kod/skarmtext.py:143>) ersatte delsträngens uppmätta timing med hela scenen; [textmalning.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/fore_text_s4/kod/textmalning.py:16>) radbröt inte modelltext.
- Ändrat: [skarmtext.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/skarmtext.py:44>), [textenheter.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/textenheter.py:16>), [textmalning.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/textmalning.py:9>), [kompilera.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kompilera.py:632>) och [test_text_disk.py](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/test_text_disk.py:63>).
- Före: två långa S4-enheter låg över hela scenen, med en tredje ovanpå; texten var enradig och klippt.
- Efter: `AAAAA!` rutor 190–204, första meningen 205–235 och slutmeningen 236–285. Endast ett centrerat block visas åt gången; långa block har två rader.
- Diagnostiken varnar för text utanför bild och ostödda tids-/ytöverlapp. Rena planer lämnas oförändrade.
- Notan: exakt 0 skillnader mot baslinjen; planfilerna är byte-identiska.
- Gamla vägen `kalla_jamn_golv.json`: exakt 0 skillnader och samma SHA-256.
- Tester: 100/100 gröna. `test_flode.Plats` kördes inte enligt instruktionen.
- Film: [film.mp4](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/film.mp4>).
- Jämförelse: [jamforelse.mp4](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/jamforelse.mp4>).
- Stills: [f195](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/stillbilder/jamforelse_f195.png>), [f215](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/stillbilder/jamforelse_f215.png>), [f245](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/stillbilder/jamforelse_f245.png>), [f255](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/stillbilder/jamforelse_f255.png>).
- Visuell dom: timing, ersättning, centrering och radbrytning fungerar; ingen text lämnar bildytan.
- Ej löst: exakt font/radbrytning och bokstavsantalet i `AAAAA!` avviker eftersom innehållet kommer från sparad modellsemantik, inte granskad OCR. Övriga kropps- och miljöbrister är orörda.
- [TEXT-LOGG.md](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/TEXT-LOGG.md>) och [GUACAMOLE-LOGG.md](</C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/GUACAMOLE-LOGG.md:237>) är uppdaterade. `PIPE.md` lämnades oförändrad. Inga bakgrundsprocesser återstår.