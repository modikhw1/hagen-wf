# Utforskning: Jev som Slutspurt efter Smart Kontext-LLM & CM-Feedbackloop

Analys grundad i användarens arbetsflöde och utfallet från `arbetsbord/`-bygget (20 nov 2026), särskilt [`arbetsbord/motor/llm_regi.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/llm_regi.py) och [`arbetsbord/ut/feedback_logg.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/feedback_logg.jsonl).

---

## 1. Varför strikta "semantiska Jev-tester" nu vore fel ordning

Att bygga färdig en deterministisk, millisekundsnabb Jev-klassificerare (`< 250 ms` per drag) *innan* samtliga redigeringsmoduler (rum/miljö, prop-placering, kamera, tidslinje, skärmtext, ljudspår, ev. rörelsebyte) sitter ihop leder till två problem:
1. **Dolt underbesluts-träd:** En enkel CM-fras som *"sätt scenen i ett kök"* låter atomär, men utlöser i praktiken följdbeslut (**tidal waves**) genom hela sekvensen:
   - Vilka bänkar/skyltar behöver följa med över vilka tagningar?
   - Krockar en tillagd prop med personens ansikte eller blicklinje? *(I första körningen av `arbetsbord/` lade `nara="bord_1"` en `0.36x0.36x0.36 m` burgare rakt i Person A:s huvudlinje i `guacamole_kok`, tills operatören justerade storlek/placering mot bortre hörnet).*
   - Skapar ändringen en logisk klyfta mot K5-bärlistan eller slutrepliken (`k5_varning`), trots att humorn behålls?
2. **"Känns rätt" slår ren ordmatchning:** Huruvida en anpassning fungerar avgörs mer av om komisk tajming, fokus på rätt ord och känslomässig helhet känns äkta för CM än om ett ord i ett skript matchar en regel.

---

## 2. Vad "Smart Kontext-LLM" i Arbetsbordet faktiskt visade i praktiken

I `arbetsbord/` hoppades Jev-steget över för att låta en full-kontext-LLM resonera direkt ovanpå `scenpaket/2`, K5-bärlista, formatkort-beats, tagningar, skärmtext, kundprofil och tidslinjestatus (100 % styrda, ångerbara operationer under `K7`). Observerade körningar ur `ui_check/rapport.json` och `feedback_logg.jsonl` (8 loggade feedbackposter):

- **`guacamole -> kok` (`gemini-3-flash-preview`, `12.67 s`, `4` operationer):** Satte köksmiljö + bank + prop + ljudläge `"tal"`, noterade uttryckligen som `k5_varning` (`"info"`) att kvarvarande guacamole-dialog i köksmiljö skiftar tolkning till intern köksförberedelse, och lät alla kameravinklar, blickar och 4-tagningars rytm ärvas 1:1.
- **`notan -> kafe` (`gpt-5.6-sol` fallback via Codex, `21.17–22.05 s`, `4` operationer):** Kortade kroken `s1` (`2.43 s -> 1.63 s`), lade till `"Fika i Haga"` i `s1` och lade `0.50 s` paus före slutrepliken `s7`, med beräknad tidsförskjutning genom sekvensens `tidal_waves` och bevarad punchline i `s6`.
- **`gelato -> bar` (`gpt-5.6-sol` fallback via Codex, `27.15 s`, `5` operationer):** Byggde inte bara om miljön till burgerbar med `"TRYFFELBURGARE"`-skylt + `1.15x` inzoomning i `s1`, utan uppdaterade även `st1` & `st3` (`"Tryffelsåsproven..."`) så skämtets kontrast mellan liten sked och stor skopa fortsatte fungera i den nya miljön (`k5_varning: "varning"`).

### Tidskostnad i nuläget vs produktionsmål
- **Nuvarande fullkontext-LLM:** `6.2 s – 27.1 s` per regi-turn (`gemini-3.5-flash` via Beacon uppmättes till `6.2–8.4 s`; `gemini-3-flash-preview` `12.7 s`; `gpt-5.6-sol` `21.2–27.1 s`). Acceptabelt för chatt-/regiutforskning och insamling av **happy paths**, men för långsamt för direkt "live-reglage"-känsla i produktion.
- **Snabboperations-skiktet:** Enskilda parameterdrag (`byt_miljo`, `objekt_lagg_till`, `skarmtext_byt`, `tidslinje_korta`, `angra`) körs redan deterministiskt (`1 278 ms` totalt i UI-sviten för 5 operationer + ångra/återställ).

---

## 3. Vägen till Jev som Prod-Slutspurt

1. **Fas A (Nu — Etablera Happy Paths via Arbetsbordet):**
   - Låt operatörer/CM använda regichatten + manuella snabbreglage på riktiga kundcase och betygsätt varje förslag (`"Känns rätt"` vs `"Skaver"` i [`feedback_logg.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/feedback_logg.jsonl), som automatiskt lagrar hela klippkontext + `llm_svar` + exakta `operationer`).
2. **Fas B (När alla redigeringsmoduler är frysta):**
   - Gruppindela de godkända `"Känns rätt"`-spåren till ett bibliotek av **parametriserade recept** (t.ex. *"kroppslöst miljöbyte"*, *"hook-åtstramning före punchline"*, *"textkonvertering med bevarad kontrast"*).
3. **Fas C (Jev-kompilering < 250 ms):**
   - Först när operationerna nedanför är låsta byggs Jev-routern som mappar vanliga CM-avsikter till det säkraste förvaliderade receptet (`< 250 ms` i frontend/API) och enbart eskalerar till tunga kontext-LLM:en vid helt fria eller konfliktfyllda önskemål.
