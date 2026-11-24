Du granskar kod i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska. Ändra inga filer. Skriv ditt svar som slutmeddelande.

Läs STRUKTUR.md (bakgrund och blinda prov). Granska struktur.py, modal_sam3.py och de delar av lokalitet.py som skriver ut/<k>/struktur_in (sök efter 'struktur_in'). Leta efter korrekthetsfel och dolda klippantaganden:
- Kamera och projektion: R/C-konventionen (B_from_cv, R^T(X-C)), normerade fx/fy, halv upplösning mot full, uv-orientering (1-yn).
- Skärvor (skarva): index, trianglar, kantkanter för kjolen, djupsprång.
- Grundreglerna: "dölj aldrig det kameran såg" (per triangel och per plan), att antagna ytor döljs från originalkameran (app.js rad med userData.antagen), att föremålspixlar inte blir textur på rumsytor (objpix).
- Stödytor (ytor) i huvudriktningens ram, och lådor och möbler (golv_, bort-förlängningen, stol).
- SAM 3: NMS per begrepp, exklusiv pixeltilldelning (minsta masken vinner), maskstorlek mot rutnätet, tröskelvärden, bfloat16-konvertering och post_process_instance_segmentation.
- Effektivitet: något som blir långsamt på 200–500 klipp.

Leverans: en lista med fynd. Varje fynd ska ha fil:rad, allvar (fel / risk / stil), ett konkret fall och en föreslagen ändring. Avsluta med raden "SAMMANFATTNING: n fel, m risker".
