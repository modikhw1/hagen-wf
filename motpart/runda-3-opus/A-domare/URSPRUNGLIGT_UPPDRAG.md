# Ursprungligt uppdrag (19 nov 2026, 21:49), ordagrant

Du är spår A (domaren) i runda 3 av ett motpartsprotokoll i repot C:\Users\praiseworthy\Desktop\hagen-wf (Windows, Git Bash/PowerShell; Python-miljö: `scen\.venv\Scripts\python.exe`, sätt `PYTHONIOENCODING=utf-8`). Skriv allt på svenska med korrekt å/ä/ö.

LÄS FÖRST: `motpart/runda-3-opus/UPPDRAG.md`, `motpart/PROTOKOLL.md`, `motpart/runda-1-claude/SYFTE.md` (särskilt §4 K1–K8), `LAGE.md`, `motpart/runda-2-neon/MOTANGREPP_V4_FINAL.md` och `motpart/runda-2-neon/SVAR.md`.

DITT MÅL: Bygg den mätstock som gör att ingen, varken Neon, de andra Opus-spåren eller du själv, kan visa ett resultat som bara ser bra ut. Tre leveranser i prioritetsordning:

1. **Fryst hold-out (görs FÖRST, inom de första 20 minuterna).** Välj med ett dokumenterat slumpfrö minst 3 klipp som varken `forvarld_karna/` eller `motpart/runda-2-neon/` har tunats på. Kandidater: klipp i `scen/3d/ingest/ut/` utanför notan/guacamole/gelato/a-sketch/b-tilltal (t.ex. c-sketch-tre-tagningar, biljard, bar), eller klipp ur banken (`data/bank`, `data/format`) som har råvideo. Kontrollera det med grep: varken kod eller rapporter i forvarld_karna/runda-2 får nämna dem. Skriv `motpart/runda-3-opus/HOLDOUT.md` med klipp-id, sökväg, frö, sha256 av listan och regeln "spår B/C/D får bara läsa klippen vid utvärdering". Spår B läser den filen. Gör den snabbt och robust, ändra den inte efteråt. Tillägg markeras med tid.
2. **Icke-cirkulära mått (`A-domare/matt/`).** Körbara skript som andra spår anropar, med felinjektion som visar att varje mått kan larma (protokollregel). Minst:
   - (a) rumsskala och möbelhöjder mot oberoende ankare som du själv märker i råpixlar: standardföremål med känd storlek, dörrar, personlängd med osäkerhet. Ange osäkerhetsintervall och säg uttryckligen var facit är en uppskattning.
   - (b) 2D-trohet mot oberoende 2D-detektion i originalrutor, inte mot projektionen av egna 3D-punkter.
   - (c) bevarande: förändrar en ändring något utanför sin räckvidd?
   - (d) K7-spärren: loggkontroll att ingen bild- eller videogenerering eller spegling anropas i ändringsledet.
3. **Prövning av runda 2 (`A-domare/prov_runda2.md` + skript).** Pröva Neons starkaste påståenden kallt och rättvist, och skriv vad som står och vad som faller:
   - Exp 7 (4,1 cm): kör V5, regelpipen v7 på hold-out, med en blind subagent om du behöver en. Är facit oberoende?
   - Exp 4/6: den virtuella djupsensorn. Mät mot ditt oberoende facit, inte mot hål eller kanter.
   - LokalMinne: kör eller granska `djup_hard_gt_vis_eval.py`. Är GT_VIS oberoende?
   - K7-konflikten: ägarens regel är att generativt bara används vid ingest för 1:1, aldrig som alternativ (minnet `feedback-generativt-bara-for-1till1.md`).
   Ge Neon rätt där Neon har rätt. Det som överlever är byggmaterial.

GEMENSAMMA REGLER (gäller alla spår):
- Skriv BARA i din mapp `motpart/runda-3-opus/A-domare/` (plus HOLDOUT.md). Ändra inget i `forvarld_karna/`, `byggsten/`, `scen/`, `data/`, `video/`, `app/`, `motpart/runda-1*`, `motpart/runda-2*`. Kopiera och patcha i din mapp om det behövs. Radera ingenting någonstans.
- Inga nya betalda generativa API-anrop (bild/video/LLM via Codex, fal, Higgsfield, Dreamina, Seedance, Gemini). Lokala modeller och befintliga cacher går bra. Om något verkligen kräver ett betalt anrop: skriv det som förslag i rapporten.
- Ingen klippspecifik kod (inga klipp-id, mappnamn eller handinförda per-klipp-konstanter i logik). Inga handskrivna deklarationer.
- Egna mått är diagnos, inte ägarens krav. Säg aldrig "lyckat" utifrån egna ledmått eller egna grindar.
- Varje påstående i rapporten har bevis (fil:rad, kommando, bild) och ett motprov. "0 fel" räknas bara om grinden visats kunna larma. Granska varje bild du hänvisar till med Read-verktyget innan du påstår något om den.
- Stoppa inte filer i ett tyst tillstånd mitt i en körning som andra läser (inga filbyten under test).
- Det finns tre parallella spår: B (nästa klipp och ingest), C (CM-mening till drag) och D (medielager och manus). De kan komma att läsa dina mått. Lägg ett kort `A-domare/README.md` som säger hur man kör varje mått.

AVSLUTA med `motpart/runda-3-opus/A-domare/RAPPORT.md`: vad som är gjort, vad som står eller faller (tabell i protokollformat: id, påstående, bevis, motprov, status), vad som inte hanns med och dina egna svagaste punkter. Ditt slutsvar till mig: max 25 rader sammanfattning plus sökväg till rapporten.