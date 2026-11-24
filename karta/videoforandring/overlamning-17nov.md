# Överlämning: essensspåret, läget 17 nov 2026 kl. 16

Läs den här filen först i en ny chatt. Detaljtabellerna finns i [essens.md](essens.md). Varje experiment har sin förregistrering i `data/format/eNN/forregistrering.json`, sitt skript i `video/format/eNN*` och sin data i `data/format/eNN/`.

---

## 1. Vad vi försöker göra

Klippen från LeTrends kunder (restauranger, barer, kaféer på TikTok) ska kunna placeras och graderas i en matris mot LeTrends strategi. Det ska ske med en återkopplingsslinga där prompt och modell ger insikt, som i sin tur ger bättre placering. Ägaren ger begränsad feedback, och målet är att hitta **essensen** av LeTrend-innehåll: röda trådar i väldigt många axlar.

### Ägarens styrning, i den ordning den kom, och alla gäller

1. **Bästa läsaren först.** Använd den bästa modellen (Argon) för att maximera avläsningen innan något planeras runt begränsningar.
2. **Abstrakta hypoteser.** De ska inte vara "sökande efter en sanning som försöker aligna det vi har för sakens skull". Skalor skrivs aldrig om efter ägarens betyg. Ägarens betyg redovisas som avläsning, inte som facit.
3. **Ta risker, inga genvägar.** Bygg "modellatur innan Gemini", hämta beroenden, skapa lager, läs i serie och rensa disken fritt. Blanda brett och aggressivt.
4. **Allt är inte en datapunkt.** Profilerna blandar LeTrend-klipp med ihopkastade klipp.
5. **Copy-normalisering.** Gemini skriver allt som copy ("två ungdomar engagerar i en socialt lyftande atletisk utmaning").
   - Att be om vardagligt språk ger bara samma normalisering med andra ord. Utgå från att du är smartare än Gemini och hacka modellen eller dess inställningar, inte prompten.
6. **Kompressormetaforen.** Gemini komprimerar alltid till samma nivå: "2 neutraliseras till 1".
   - Ge den neutrala återberättelsen ett identifierbart huvudrum, så att avståndet till copy syns.
   - INTE svarta skärmar eller suddiga bilder (E25 avbröts av det skälet).
   - Copy ska bara finnas där innehållet förtjänar den, som när en recensent beskriver världsklass.
7. **Total bild i serie.** Bilden ska även hålla klippning, produktionsvärde, tempo, manuskvalitet och hur uppmärksamheten hålls scen för scen (scener × repliker). Läs i en serie körningar (semantisk, semantisk-teknisk och teknisk mening) med enkla värden som "hookighet" och "svårighetsgrad att spela in".

### Arbetsregler

- Förregistrera före varje experiment.
- Pröva mot materialet självt:
  - undanhållna klipp
  - hela konton undanhållna i korsvalideringen
  - utfall som modellen aldrig ser
  - permutation inom konto
- Redovisa ärligt det som faller.

---

## 2. Infrastruktur

### Modellvägen

| Del | Detalj |
|---|---|
| Appen | Lovable-appen `modikhw1/token-budget-beacon`, projekt-id `29cf6c98-1bde-4d66-8752-c31662cc1e07`. Vertex, region global. Klon i scratchpad (`tbb`). Commits e3610ee och 367db2b är deployade. |
| Brygga | `video/typer/lovable.mjs`: `beaconDelar({ delar, schema, temperatur, modell, maxUt, extra })`. `LOVABLE_KONTO=beacon` krävs. |
| Nyckel | `BEACON_NYCKEL` i `video/.env.local`. Skriv aldrig ut den. |
| Användning | `mcp__lovable__query_database` mot tabellen `usage_logs` (model, status, cost_usd, created_at). |
| Kostnad | **213 USD loggat totalt**, budgetramen var cirka 300. |

### Gränser och fällor

- Gatewayen klipper vid cirka 60 s (502). `upstreamStream: true` (SSE) hjälper Flash men inte Argon.
- Vertex tar högst 10 videofiler per anrop. Därför används band om 4 klipp med klippnumret inbränt, 1 bild/s och crf 35 (`e13-band.mjs`).
- Kvoter:
  - Pro och Argon delar cirka 200 000 indatatokens per minut.
  - **Flash 3.8 har en dygnskvot.** Den tog slut cirka 14:00 den 17 nov (UTC 12–13), efter cirka 5 500 lyckade anrop under dagen. Sedan svarar Vertex 503/429 `quota_exhausted`.
  - Argon släpper igenom enstaka anrop.
- Argon hänger när prompten ber om ordagranna citat ur talet.
- Flash-inställningar:
  - `thinkingBudget: 0` fungerar bara utan `includeThoughts`.
  - `thinkingLevel: 'minimal'` stöds inte.
- Schema: `maxItems` i `responseJsonSchema` ger INVALID_ARGUMENT, medan `maxLength` fungerar.
- Skripten sväljer fel tyst (`catch { fel++ }`). Felsök med ett ensamt anrop.

### Lokalt

- **Klipp:** små kopior i `~/Downloads/letrend-e13/` (2 706 mp4). Originalen är raderade efter nedskalningen.
- **Python:** `scen/.venv` (Python 3.12, CPU), med multilingual-e5-small (kör med `HF_HUB_OFFLINE=1`) och `silero-vad`.
  - HF-cachen raderades externt cirka 11:32. Bara e5-small är nedladdad igen; scenmodellerna (sam-3d-body, depth-anything, faster-whisper) saknas.
- **ffmpeg:** finns via WinGet i PATH.
- **Minnet är trångt:** cirka 1–2,6 GB ledigt, och andra program tar resten (MCP-servrar, hagen-ui-krokar, `forvarld_film.py`).
  - Systemet har två gånger dödat bakgrundsköer när sessionen var ledig (04:00 och cirka 13:30).
  - **Kör därför i förgrunden i bitar** med `timeout 570 node ...` (skripten återupptas per klipp), en kö åt gången.

### Gemensam metod i analyserna

- **Utfall** `u` = log visningar minus medianen av ±10 grannar i tid inom kontot. Det finns i `data/format/e15/motorer-flash.jsonl` (fälten `id`, `konto`, `u`, `hel`): 2 213 klipp med utfall, 105 konton.
- Allt centreras inom konto.
- Korsvalidering med hela konton undanhållna (5 veck × 10 omgångar), SVD 30 axlar plus ridge för inbäddningar.
- Permutation inom konto ger p.
- **Bibliotek** = 1 253 klipp (harness v6 och E13). **Replikering** = 960 klipp med utfall ur `e19/ids.json`, som aldrig använts för att hitta något.
- Copyindex: copyord per 100 ord ur `e23/copyord.json`.

---

## 3. Experiment för experiment

### E13: passform med historiken som video
- **Gjordes:** nio kunder, 50 ägarbetygda par. Modellen såg 24 av kundens klipp plus kandidaten och satte passform.
- **Resultat:** Argon +0,63 inom kund, familjeräkning i text +0,56, Pro (video) +0,42, Flash +0,39.
- **Insikt:** alla läsare var för stränga och satte 1 på "aldrig gjort", medan ägaren ger 4–4,5 åt en stark premiss. Att skriva om skalan efter det (b3) var fel väg enligt ägaren och avbröts.
- **Status:** klart.

### E14: tre lager (självet, motorn, mötet)
- **Gjordes:** tre lager lästes.
  - Självet: Argon läser 20 av kundens klipp och beskriver aktören som spänningsfält, med polariteter, motorer, gränser, ankarklipp och trajektoria.
  - Motorn: det som får ett klipp att fungera, skilt från ytan (vara, lokal, språk).
  - Mötet: självet plus en motor, bara i text.
- **Resultat:** mötet känner igen kundens egna undanhållna klipp ur enbart motorn med AUC 0,94 (9 kunder), 0,88 inom samma formatfamilj. Ingen av 62 motortexter läcker vara.
- **Insikt:** ett lager som skiljer mekanism från yta går att läsa och bär identitet.
- **Filer:** `e14.mjs --steg sjalv|mekanism|mote`. Motorerna ligger i `e14/mekanism` (Argon) och `mekanism-3.8-flash`.

### E15: geometri på svag text
- **Gjordes:** 10 911 bankklipp med en mening per klipp, inbäddade lokalt.
- **Resultat:**
  - Axlarna är gemensamma mellan kontohalvor (0,93).
  - Första axeln (spelad scen mot matvisning) följer utfall med +0,07.
  - Igenkänningen ger AUC 0,86, men texten ser vara och konto.
- **Insikt:** rummet har en struktur, men den svaga texten bär ytan.

### E16: läsning i serie, vägning av klipp
- **Gjordes:** Argon gav 155 klipp en roll med självet som lins.
- **Resultat:** **bärande ×1,44 mot ihopkastat ×0,82** i utfall inom konto (p 0,025), utan att modellen sett visningar.
- **HE16b föll:** ett själv skrivet om ur enbart de bärande klippen känner igen sämre (0,94 till 0,82). Kontot är också bruset.
- **Insikt:** "allt är inte en datapunkt" går att läsa ur videon.

### E17: motorrummet (Flash-motorer, 1 269 biblioteksklipp)
- **Resultat:** kontot gissas ur närmaste granne i 0,13 av fallen, mot 0,29 för den svaga texten och 0,60 för ytan. Utfall: motor +0,24, svag text +0,17, yta +0,08.
- **Föll:** ägarens val i pass 7 träffas i bara 10 av 19 par.
- **Insikt:** i en utläst axel och bland de högst förutsagda klippen finns nästan bara möten mellan gäst och personal där något står på spel och vänds. Det födde E20.
- **Filer:** den frusna modellen ligger i `e17/modell.npz`.

### E18: LeTrend ur ägarens ord
- **Gjordes:** Pro läste transkripten (`hagen-ui/_anteckningar/transkript`) och skrev LeTrend som aktör.
- **Resultat:** 9 av 19, förkastad.
- **Insikt:** ägarens ord ("abstrakt idé, låg tröskel") och ägarens val (karismatiska personer, provsmakning) skiljer sig åt. En del av det som kodats som ägarens begrepp kom från Miles frågor.

### E19: replikering
- **Gjordes:** 1 035 nya bankklipp, varav 960 med utfall. Utfallsmodellen frystes på biblioteket.
- **Resultat:**
  - Motorn ger +0,14 (håller), men den svaga texten ger också +0,14 (HE19b föll).
  - Värdet i idén eller personen ×1,23 (p 0,0004).
- **Insikt:** motorns försprång gällde det utvalda biblioteket, inte tvärsnittet.

### E20/E21: tjänstemötet, den röda tråden som replikerade
- **Gjordes:** Flash läste bara motortexten och angav sju fält: relation, friktion, insats, sida, uttryck, utgång, handling.
- **Resultat på replikeringen:**

| Fält | Utfall inom konto | p |
|---|---|---|
| Gäst–personal | ×1,55 | 0,0002 |
| Tydlig friktion | ×1,39 | |
| Oviss utgång | ×1,31 | |
| Handling sker | ×1,25 | |
| Gästens eller personalens sida | ×1,21 | |
| Lånat ljud | inte signifikant | |

- **Fälten tillsammans:** frysta ger de **+0,19**, mer än motorrummets +0,14. Motorn rensad från fälten ger +0,05.
- **Insikt, kärnan hittills:** *människor i ett möte där något står på spel och vänds.* Om utgången är spelad eller äkta spelar ingen roll, bara att den finns.
- **Filer:** `e21/faltvikter.npy` (frysta på alla 2 213, alltså inte rena för replikering).

### Argon-kontrollen
- **Gjordes:** 240 replikeringsklipp lästes om med Argon.
- **Resultat:** fälten ur Argons motor ger **+0,25**, mot +0,09 ur Flashs (skillnad +0,16, CI [+0,07, +0,26]).
- **Insikt:** alla tal i E17–E22 är lästa med den svagare läsaren och är troligen underskattningar.
- **Status för HA3** (resten av replikeringen med Argon): 992 motorer finns i `e14/mekanism`, fälten i `e20/lasning-argon` och `e21/lasning-argon` finns för 240. Ofullbordat. När fälten är lästa, anpassa `e19_argon.py` till `argon-ids.json` plus `argon-ids-rest.json`.

### E22: ägaren mot fälten
- **Resultat:** fältmodellen träffar ägarens biblioteksval i 11 av 19 par. Nyttan i harness v6 träffar 16 av 19.
- **Insikt:** publikens utfall och ägarens val överlappar men är inte samma sak. Biblioteket innehåller personalsketcher utan friktion till lånat ljud, som fälten sätter lägst.
- **Väntar på ägaren:** tio informativa par i `e22/urval-till-agaren.json`.

### E23: register och temperatur (400 replikeringsklipp, `e23/ids.json`)

| Text | Utfall inom konto |
|---|---|
| A, motorn (copy-register) | +0,15 |
| B, vardaglig, temp 0,1 | +0,09 |
| C, temp 1,0 | +0,13 |
| D, temp 1,8 | +0,11 |
| A + B | +0,19 |

- Vardaglig text tar copyord från 4,2 till 0,2 per 100 ord, men tar med ytan (kontot gissas 0,25).
- **Insikt:** copyn är inte bara brus, för motorns tolkning ordnar klippen. Ägarens invändning håller: vardagligt språk ger samma normalisering med andra ord.

### E24: neutral logg
- **Gjordes:** Flash med tankar av och temperatur 1,3 skriver rader `{vem, gor, med, sags}`, tre läsningar per klipp.
- **Status:** **ofullbordad.** p1 har 376 av 400, p2 och p3 har 0. Analysen `e24_analys.py` kräver alla tre läsningarna och är inte körd.

### E25: svarta och suddiga poster som "negativ input"
- **Status:** avbruten. Ägaren menade inte svart skärm, se punkt 6 i avsnitt 1.

### E26: återberättelse med säljutlopp (kompressorns huvudrum)
- **Gjordes:** i samma anrop först en recensent som bara återberättar (N), sedan en copywriter (S), sedan täckning 0–100 och vad säljtexten fyller på. Flash, temperatur 0,3.
- **Resultat på E23:s 400 klipp:** N +0,22, S 0,00. Täckning och avstånd mellan texterna var noll.

### E27: replikering av E26, som FÖLL
- **Resultat på 509 nya klipp:** N **+0,01**, S +0,09, A +0,07.
- **Insikt:** N:s +0,22 var en egenskap hos urvalet. **Fri text bär inte stabilt mer än cirka +0,1 inom konto, vilken stil den än har.** Huvudrummet ändrade ordvalet men inte vad som går att läsa ut.
- **Status:** 509 av 1 676 klara (replikering plus biblioteket i `e27/urval.json`). `e27_analys.py` har ett ofärdigt HE27d (N plus fält; `falt()` är definierad men används inte).

### E28: tre lager (teknisk, semantisk-teknisk, semantisk)
- **Teknisk, utan modell** (`e28-tek.mjs`, `e28/tek.jsonl`, alla klipp: scenbyten, skottlängder, rörelse, tystnad, LUFS, LRA):
  - Längd +0,11, pauser +0,09, LRA +0,09, ljudnivå −0,07.
  - Klipptakt och tidiga klipp ger 0, så hookmåtten i tid säger ingenting.
  - Lagret som helhet ger +0,09 och +0,10 fryst från biblioteket till replikeringen.
- **Semantisk-teknisk** (`e28.mjs`, Flash, 327 av 400: scener med "bär sin tid", när premissen är klar, svårighet 1–5, manus):
  - **Repliker +0,18, inget manus −0,16.**
  - För långa scener −0,12 (p 0,056).
  - Premiss och svårighet att spela in ger 0 (HE28c och HE28d föll).
- **Lagren tillsammans:** de lägger inget till N. N är dock inte oberoende här (samma klipp som E26).
- **Insikt:** repliker bär det som längden såg ut att bära.

### E29: Argons återberättelse
- **Förregistrerad.** `e26.mjs --modell google/gemini-4-argon --ids ../data/format/e23/ids.json` skriver till `e26/lasning-4-argon`.
- **Status:** 6 av 400, stoppad av kvoten. Med tanke på E27 har frågan lägre prioritet.

### E30: att något sägs, utan modell (replikerat)
- **Gjordes:** Silero VAD lokalt (`e30_tal.py`, `e30/tal.jsonl`, 2 703 klipp) mätte tal på alla 2 213 klipp med utfall.
- **Resultat:**

| Mått | Alla | Bibliotek | Replikering |
|---|---|---|---|
| Talsegment | **+0,15** | +0,17 | +0,11 |
| Talsegment, längd konstant | +0,11 | | |
| Längd, tal konstant | +0,05 | | |

- **Fler resultat:**
  - Klipp utan tal (31 %) ligger på **×0,81** (p 0,0002).
  - Tidigt tal går bättre (−0,10 för sekunden då talet börjar).
  - Detektorn följer Flashs replikantal med 0,61.
- **Insikt:** det första fyndet som håller utan att en språkmodell läser något. Det är billigt att mäta vid ingest.
- **Förbehåll:** musik med sång räknas som tal.

### E31: tal mot fälten
- **Frysta på biblioteket, prövade på replikeringen:** fält +0,20, tal +0,14, fält + tal +0,22.
- **HE31b föll:** talet lägger +0,016 till fälten (CI −0,01 till +0,04).
- **HE31c håller:** fält och tal korrelerar bara 0,25.
- **Insikt:** talet är en billig ersättare som ger ungefär två tredjedelar av fältens värde. Oviss utgång har median 5 talsegment mot 1.
- **Utforskande** (`e31_modellfri.py`): tekniska mått plus tal lägger inget till talet. Den högsta femtedelen ligger på ×1,21 och resten mellan ×0,78 och ×0,94.

---

## 4. Det som står (ärligt)

1. **Röd tråd: tjänstemötet.** Människor i ett möte (helst över disken) där något står på spel, friktion uppstår och utgången är oviss.
   - Sju fält ger +0,19 till +0,20 på osedda klipp, och +0,25 med Argon som läsare.
   - Talet är samma sak mätt från ljudet (+0,14 utan modell).
2. **Läsaren spelar roll mer än prompten.** Argon slog Flash med +0,16 på samma fält. Skillnaden i prompt, register och temperatur ger ±0,05.
3. **Fri text har ett tak runt +0,1.** Strukturerade frågor om mötet slår allt fritext-embeddingarbete.
   - Det enda stora fritextfyndet (N +0,22) replikerade inte.
   - Copy-normaliseringen har inte gått att "hacka" fram till mer signal: huvudrummet ändrade ordvalet, inte det som går att läsa ut.
4. **Lager fungerar för identitet.** Självet plus motorn känner igen kundens klipp (AUC 0,94). Bärande klipp ×1,44 mot ihopkastade ×0,82.
5. **Teknik och hook i tid ger nästan inget.** Klipptakt, tidiga klipp, när premissen blir klar och svårighet att spela in bär inte. Längd bär bara genom tal.
6. **Tre olika saker:** ägarens ord, ägarens val och publikens utfall.
   - Mot ägarens val: fälten 11 av 19, nyttan i harness v6 16 av 19.
   - Utfall är inte detsamma som LeTrends strategi. Ägarens svar på E22-paren är det mest informativa nästa steget från ägaren.

---

## 5. Nästa steg, i föreslagen ordning

1. **HA3, Argon-fälten på hela replikeringen.**
   - Det är det starkaste spåret, eftersom läsaren var den största hävstången.
   - Läs fälten för de 992 Argon-motorerna med `e20.mjs` och `e21.mjs --motorer mekanism --ut lasning-argon --ids ../data/format/e19/argon-ids-rest.json`, en kö i taget.
   - Analysera sedan som i `e19_argon.py` över alla Argon-ids.
   - Frågan: håller +0,25 på cirka 900 klipp?
2. **E27 klart** (biblioteket och resten av replikeringen) för att stänga N-frågan helt. Kör HE27d (N plus fält).
3. **Bygg en ingestpoäng.**
   - Delar: fält (Argon eller Flash) + bärande/ihopkastat (E16) + tal (VAD, gratis).
   - Matrisen: mötesaxeln × vikten (bärande mot ihopkastat) × passform (självet).
   - Det knyter tillbaka till ursprungsmålet om placering och gradering mot strategin.
4. **Ägarens svar** på de tio paren i `e22/urval-till-agaren.json`.
5. **E24 och E29** har låg prioritet efter E27. Kör dem bara om kvoten räcker över.

**Körsätt:**
- `cd video && export LOVABLE_KONTO=beacon && timeout 570 node format/<skript> --par 4` i förgrunden, upprepat.
- Kolla kvoten först med ett ensamt anrop, eller i `usage_logs` (status 429 per timme).

---

## 6. Filkarta

| Vad | Var |
|---|---|
| Huvuddokument med tabeller | `karta/videoforandring/essens.md` |
| Skript | `video/format/e13*` … `e31*` |
| Data och förregistreringar | `data/format/e13` … `e31` |
| Utfall och konto per klipp | `data/format/e15/motorer-flash.jsonl` |
| Replikeringsklipp | `data/format/e19/ids.json`; Argon-delar `argon-ids.json` och `argon-ids-rest.json` |
| E23:s 400 klipp | `data/format/e23/ids.json` |
| Teknik och tal per klipp | `data/format/e28/tek.jsonl`, `data/format/e30/tal.jsonl` |
| Fält | `data/format/e20/lasning`, `e21/lasning` (Flash); `-argon` (Argon) |
| Minne | `~/.claude/projects/C--Users-praiseworthy-Desktop-hagen-wf/memory/`: `project-essens-lager.md`, `feedback-essens-inte-linjering.md`, `reference-beacon-proxy.md` |
