Ett prov av en idé: kan en videomodell översätta ett klipp till ett format som vår 3D-läsning läser säkrare, utan att lämna originalets rörelse? Arbetet sker i C:\Users\praiseworthy\Desktop\hagen-wf. Skriv bara i den nya mappen scen/3d/lasformat/. Ändra ingen befintlig kod och inga befintliga data.

## Bakgrund
scen/3d bygger en 3D-förvärld ur filmade kortklipp. Kroppar läses med SAM 3D Body på Modal (scen/3d/ingest/modal_sam3db.py, volym `sam3db-vikter`, secret `huggingface`), rummet med MoGe (scen/3d/ingest/modal_rum.py). Kedjan körs med scen/3d/ingest/ingest_klipp.py (steg: personer, kamera, kropp, sekvens, varld, golv, kontakt, rum, blender, jamfor). Läs scen/3d/ingest/README.md först.

Svagheten sitter i indatat: tät beskärning, dolda fötter, röriga bakgrunder, handhållen kamera. Idén: låt en videomodell göra om klippet till ett mer läsbart format, kör vår kedja på det och jämför. Originalets SAM 3D Body-läsning är facit för rörelsen: resultatet är bara giltigt om rörelsen stämmer med originalet.

Ägarens regel: bilden ska förbli realistisk och databred. Ansikten, mimik och mat ska vara intakta. Förenkla bara det som stör läsningen. Ingen stilisering.

## Testklipp
Notan tagning S4: scen/3d/ingest/ut/notan-tagningar/klipp/S4.mp4 (85 rutor, 30 fps, 576x1024). Befintlig läsning av originalet ligger i scen/3d/ingest/ut/notan-tagningar/S4/ (personer.json, masker.npy, kropp/, sekvens_1.npz, sekvens_4.npz, kontakt_*.json, rum/, meta.json). Person 4 är servitören, vars fötter inte syns; dagens kedja gör honom 1,90 m lång, vilket troligen är fel. Person 1 är den andra personen.

## Modell
Wan VACE med Apache-2.0-vikter. Använd Wan2.1-VACE-14B eller Wan2.2-VACE-Fun-A14B (välj den som är enklast att få igång stabilt; kontrollera licensen på modellkortet och skriv den i rapporten). 1.3B får användas för att få pipen att fungera innan 14B. Underlag om modellerna, priser och fallgropar: scen/3d/licensrevy/V2V-ALTERNATIV.md. Taket är cirka 81 rutor vid 16 fps; S4 ryms i ett pass. Omsampla till modellens fps och mappa tillbaka exakt i tid vid jämförelsen.

## Modal
Ägaren har 24,59 USD Modal-kredit och upplever Modal som segt. Därför:
- Lägg vikterna i en Modal Volume (hämta en gång).
- Kör alla varianter i samma varma container (en funktion som tar en lista av jobb), inte en kallstart per variant.
- GPU: L40S eller A100-80 räcker troligen för 480p; H100 bara om det behövs. Logga GPU-tid och uppskattad kostnad per körning till scen/3d/lasformat/budget.json.
- Hård gräns: 12 USD totalt för hela uppdraget. Stanna och rapportera innan gränsen passeras.

## Format att pröva (480p räcker)
- A, realistiskt och städat: maskad omgenerering. Personernas pixlar behålls (masker ur masker.npy eller SAM 2), bakgrund och en breddad bildyta genereras nytt så att servitörens ben och fötter syns. Stillastående kamera. Prompten beskriver samma restaurang, samma ljus, inga andra gäster.
- B, förenklad bakgrund: som A, men bakgrunden förenklad till lugna, släta ytor med tydliga väggar, golv och bord. Personerna realistiska.
- C: som B, men med ett tydligt rutmönstrat golv, för att se om golvplan och skala blir läsbara.
Om maskad omgenerering inte fungerar i VACE, pröva närmaste variant (t.ex. referensbild plus pose- och djupstyrning) och skriv varför.

Kör varje format högst 3–4 gånger med justerad prompt. Spara alla utfall.

## Mätning
För varje format, kör vår kedja på resultatet (minst stegen personer, kropp, sekvens, varld, golv, kontakt; rum om det går) med utdata under scen/3d/lasformat/ut/<format>/. Mät och jämför mot originalets läsning:
1. Drift: följer rörelsen originalet? 2D-ledernas avstånd per ruta i originalbildens koordinater (räkna bort breddningen), rotbana, armgester. Detta avgör om utfallet är giltigt.
2. Läsning: skak, fotglidning, sula över golv, servitörens längd, hur säker kroppsskattningen är för dolda ben.
3. Rum (om rum körs): blir golvplan och väggar tydligare och stabilare?
4. Bild: sida-vid-sida-video (original, genererat, kroppen projicerad) per format, samt stillbilder.
Använd befintliga mätverktyg där de finns (scen/3d/ingest/vakt.py med flera) i stället för att skriva nya.

## Ramar
- Python: scen/.venv/Scripts/python.exe med PYTHONIOENCODING=utf-8. Ingen python i PATH.
- Skriv filer som UTF-8 med LF. Skicka aldrig filinnehåll genom PowerShell-pipe.
- Sök inte rekursivt genom scen/3d/kontrakt/ut/.
- Skriv scen/3d/lasformat/RAPPORT.md löpande, steg för steg. Kvoten kan ta slut mitt i; det som står i filen då ska vara användbart.

## Rapport
Kort, på svenska, för en ägare som inte läser kod. Dom först: höll videomodellen klippet, och läser vår kedja något format säkrare än originalet? Sedan en tabell per format (drift, skak, fotglidning, golv, servitörens längd, kostnad), bilder och videor, vad som inte fungerade, och rekommendation om nästa steg. Skilj på det du mätt och det du resonerar dig till.
