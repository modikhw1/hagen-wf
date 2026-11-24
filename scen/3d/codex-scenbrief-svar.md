## Slutrapport

Uppdraget är genomfört del 1–4 och dokumenterat i [SCENBRIEF-LOGG.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/SCENBRIEF-LOGG.md).

- Paketet innehåller märkta kontaktblad per tagning, översikt, cachebaserad `lasning.json`, LLM-instruktion och schema för deklaration 0.8.
- Validatorn hittar schema- och referensfel, saknade kameror, omärkta tal, hårda gissningar och lästa värden utan källa samt provöversätter isolerat.
- Sketch: förslaget och befintlig deklaration är ense om rum, roller, kameramotiv, närvaro och relevans. Förslaget uttrycker B:s tre arbetslägen och osäkra mått bättre; inga metriska koordinater stöds av läsningarna.
- Guacamole: rum, identiteter, hållning, kameror och närvaro överensstämmer. Befintlig deklarations A–B-avstånd 1,73 m och diskintervall stöds bättre av senare diagnostik; förslagets 1,60 m var en gissning.
- En LLM kan inte avgöra verkliga disk-, sits-, kamera- eller personavstånd, dold närvaro, sketchens rollavsikt eller ägarens relevansnivåer enbart ur rutorna.
- Återkopplingskommandot föreslår ägargodkända diffar utan att redigera deklarationen. Guacamoleprovet föreslog endast diskhöjd `[0,95, 1,15] → 1,0`.
- Detaljerad fältjämförelse: [SCENBRIEF-JAMFORELSE.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/SCENBRIEF-JAMFORELSE.md).

Paket och förslag:

- [Sketch-paket](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/ut/a-sketch-servering-tagningar/brief) · [förslag](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/ut/a-sketch-servering-tagningar/brief/forslag_deklaration.json)
- [Guacamole-paket](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/ut/e-dialog-guacamole-tagningar/brief) · [förslag](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/ut/e-dialog-guacamole-tagningar/brief/forslag_deklaration.json)

Verifiering: `test_scenbrief.py`, `test_deklaration.py` och `test_rum.py` — 14/14 gröna. Inga modelljobb, Blenderkörningar, källdeklarationsbyten eller plankompileringar från förslagen gjordes.

Kvar: extern LLM-/chattkoppling och godkännande är manuella, flerrollsavstånd bör föras in direkt i framtida briefpaket, och äldre deklarationer har ännu inte migrerats till den nya konsekventa proveniensmärkningen.