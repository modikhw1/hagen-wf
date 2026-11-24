# Överlämning: runda 4, session 20 nov 2026 (orkestratorn, Claude Opus 5.5)

Läs detta först om du tar över. Det sammanfattar vad sessionen gjorde, vad ägaren sa, vad som står och faller, och vad som pågår. Detaljerna finns i de länkade filerna. Allt ligger i `motpart/runda-4/` om inget annat anges.

## 0. Läget i en mening
Ägaren styrde om projektet: från "CM skriver en mening, förvärlden ändras" till "1 000+ lätt ingestade klipp läggs bredvid varandra i gemensamma dimensioner och kan röras mot och från varandra utan mush, deterministiskt, med en harness som fattar besluten åt användaren (som Lovable)". Sessionen byggde en granskningskedja (T1–T4) och påbörjade de första proven. Provet i steg 2 tog orimligt lång tid. Det ledde till en diagnos (`DIAGNOS_VANTETID.md`) och en infrastrukturspecifikation (`INFRA.md`) som ska byggas innan fler tunga prov körs.

## 1. Kronologi
| # | vad | filer |
|---|---|---|
| 1 | Genomgång av runda 0–3 och Geminis arbetsbord v1/v2. Fynd: ingen ägardom (K2) någonsin; v2 bygger kinematiska attitydreglage mot ägarens dom 17 nov ("ser ut som en apa"); Gemini granskade Gemini; egna trösklar togs som krav; `LAGE.md` vilseleder. | (konversation) |
| 2 | **v2 stoppad** (ägarens beslut). | `arbetsbord/STOPP_V2.md`, stopprad överst i `arbetsbord/EXIT_NOTES_V2.md` |
| 3 | Runda 4 inrättad: roller, cykel, regler. | `UPPDRAG.md` |
| 4 | **Domaren byggde ägarpanel 1** (K2, blind). 19 ändringspar och 7 par för 1:1, med 5 kontrollpar. Ingen ägardom finns än. | `A-domare/RAPPORT.md`, `A-domare/panel/` |
| 5 | Ägarens ord, ordagrant: meningar räcker inte som styrsignal; modellen ser inte video; lägg klipp bredvid varandra, rör dem längs dimensioner, ingen mush, determinism, Lovable-liknelsen; tekniken fungerar inte idag. | `AGARENS_ORD_20NOV.md` |
| 6 | T1 och T2 (Opus xhigh, oberoende) tolkade orden och kopplade dem till repot. | `T1-tolkning/TOLKNING.md`, `T2-tolkning/TOLKNING.md` (+ `lokalrum.py`, `diagnos_modellfri.py`) |
| 7 | Orkestratorns dom över T1 och T2. | `DOM_T1_T2.md` |
| 8 | T3 (GPT-6-astra xhigh via Codex) fällde två av domens slutsatser; omkörning verifierade det. | `T3-codex/GRANSKNING.md`, `T3-codex/robusthet.py/.json`, tillägg i `DOM_T1_T2.md` |
| 9 | Steg 1 klart: 200 klipp hämtade om i originalbildtakt. | `1-datagrund/RAPPORT.md`, klipp i `C:\Users\praiseworthy\Downloads\letrend-r4\` |
| 10 | T4 (astra xhigh) förregistrerade steg 2 (invarians) och steg 3 (ömsesidigt ingrepp). | `T4-codex/FORREGISTRERING.md` |
| 11 | Ägarens svar på B7 omsatta i kontraktet för steg 3. | `3-ingrepp/KONTRAKT.md`, minne `project-bevarande-och-salj` |
| 12 | Steg 2 kört (referens klar, testet pågår). Ägaren väntade 82 min utan resultat. | `2-invarians/` |
| 13 | Diagnos och infrastrukturspecifikation. | `DIAGNOS_VANTETID.md`, `INFRA.md` |

## 2. Det som står (insikter)
1. **Styrsignalen är ägarens val, inte hans ord.** Smaken träffar publiken i 20/26 par (`karta/videoforandring/k1-del1.md:19-29`); orden ger 9/19 (`essens.md:73`). Ord har ändå informationsvärde (T3).
2. **Embryot finns i `byggsten/hand`**: handflata (det gemensamma hålls), fingrar (det som rörs), `rutt.py` (högst två drag per steg, hållpunkter är riktiga klipp), `anpassa.py`. Ingen människa har bedömt det. Det går bara åt ena hållet.
3. **Mellanläget är ett prov på pipen, inte produkten** ("ett klipp i mitten, fingrar utåt", ägaren 14 nov, `byggsten/hand/README.md:249`).
4. **Sidospår för just denna fråga:** kärnans attitydmotor, rumsmått i cm, G1–G7, Kimodo, arbetsbord v2. 3D behövs bara för riktningar som kräver ny iscensättning.
5. **Datagrunden var för tunn:** de gamla kopiorna är 240p och 2 bilder/s, och originalen är raderade. Det är löst för 200 klipp (`letrend-r4`).
6. **Medielagret saknar operatorer** för pauskortning, tempo utan ändrad tonhöjd och ljudnivå. Montage kan bara stryka. Det finns en bugg: skyddet för första och sista tagningen saknas i fas 2 (`runda-3-opus/D-medielager/medielager/operationer.py:453`) (T4 B1).
7. **T4:s varning:** dagens tempomått (`takt` = byten/längd, `tal_per_s` = segment/längd) stiger av aritmetik när ett klipp kortas. En policy får aldrig "bevisa" sin ändring med samma mått. Steg 3 avgörs av ägarens blinda dom och antal rättelser.

## 3. Det som har fallit (använd inte)
- "Mush går att mäta som avstånd från mitten." Det är geometri: ett medelvärde av två centrerade vektorer har ≈ 1/√2 av normen. Avståndet mäter ovanlighet, inte distinktion (T3 A).
- "Vald korsning bevarar särprägel, 82 % nära verkligt." Normen bevaras av algebraiska skäl, och 82 % är bästa av 64 på samma bank (T3 A3).
- T2:s kontofynd 0,116. Med medelrang för lika värden blir det 0,058 (`diagnos_modellfri.py:78`, rangfel). Fortfarande över slumpen 0,012.
- "Modellfritt = vem och var, läsare = mening." Det går inte att dra ur testerna. "Modellfritt" ska heta "utan fri LLM-tolkning".
- `LAGE.md` (Argon, 19 nov): påståendena A1–A6 föll i runda 1 (`PROTOKOLL.md`). `LAGE.md` är inte uppdaterad. Ägaren har inte svarat på om den ska märkas inaktuell.

## 4. Ägarens beslut och ord denna session (ordagrant där det går)
- **v2 stoppad.** Domaren startade med panelen.
- **Steg 1–4 godkända** ("skynda dig inte fram för att nå ett utfall du kan visa mig, ta det sekventiellt"). Steg 2 och 3 byttes enligt T3 (godkänt).
- **B7-svaren** (`3-ingrepp/KONTRAKT.md`):
  - Tempo är en ok avgränsning men är inte energi. Energi beror på krokighet, tema, intresse, taktik, trend och stimulans.
  - ±10 % och tre rättelser är ok. En stor rättelse som bryter ryggraden räcker för att fälla.
  - **Absolut: innehållstypen** (sketch förblir sketch; en kombination av talking head och montage är en enhet). Längden respekteras om den inte själv är målet eller en akt kan strykas. Undertexter hör inte till förvärlden, men text som bär premissen gör det. Ljudet förs över orört; en AI-röst är fejk. **Sälj mellan raderna**: maten, lokalen och känslan syns i förbigående och bygger relation till varumärket över flera klipp.
- Ägaren påpekar att orkestratorn inte ser video, och att även Gemini är begränsad. Ägarens nyanser ska bevaras ordagrant och inte tolkas bort.
- **Infrastruktur:** ägaren vill ha snabb iteration, inte "räcker". Modal upplevs som långsamt. Extern hjälp ska användas där den snabbar upp (`INFRA.md`).

## 5. Öppna frågor till ägaren
1. **Generativ rendering för tillförande ändringar** (ny lokal, ny talare): får ett låst, deterministiskt recept styra den? Annars krävs en fungerande 3D, och den finns inte. (Ägaren har sagt att en AI-röst är fejk, se §4.)
2. **Menyprovet** (T4 C): ägaren väljer bästa kandidat på två övningspar innan policyn visar sitt val. Inte besvarat.
3. **Ägarpanel 1** (`A-domare/panel/`): inte genomförd. Frågan är om den fortfarande är relevant, eftersom den bygger på meningsvägen.
4. **`LAGE.md`**: ska den märkas som inaktuell?
5. Egna meningar och osedda klipp (K1/K4): nedgraderat efter ägarens ord. Fråga bara om det blir relevant.

## 6. Det som pågår just nu
- **Steg 2:s skarpa test kör** utan agent. Agenten stängdes av misstag, men processen fortsätter: `scen/.venv/.../python.exe ... motpart/runda-4/2-invarians/test_kor.py`, startad 22:43. Klockan 23:00 var 18 av 156 mätfiler klara (cirka 1 per min). **Beräknad klar 01:00–01:30.** Utdata: `2-invarians/test_mat.jsonl`, logg `test_kor.logg.txt`. Den är återupptagbar.
  - Stoppa: hitta processen med `Get-CimInstance Win32_Process | ? CommandLine -match 'test_kor'` och avsluta den.
  - Efter körningen återstår: `analys.py` (dom enligt A4), kontaktkarta och `RAPPORT.md`. Ingen har skrivit dem än.
  - **Förbehåll** (`2-invarians/AVVIKELSER.md`, avvikelse 1): den blinda perceptuella kontrollen kan inte göras av en agent. Domen blir "ofiltrerad". Ett fällt mått kan räddas av en senare blind kontroll; ett klarat förblir klarat. Ingen allmän dom om tempo kan fällas utan ägarens lyssning.
  - Referensmätningen är klar och återanvändbar: `2-invarians/ref_mat.jsonl` (144 klipp, 72 konton). Manifestet är fryst: `2-invarians/MANIFEST.md`.
- **Arbetsfiler:** `C:\Users\praiseworthy\Downloads\letrend-r4-varianter\` (byggs och raderas per variant). Disken hade 8,3 GB ledigt klockan 23:00.

## 7. Rekommenderad väg framåt
1. **Bygg `INFRA.md` först**: jobbkörare (provlopp, ETA, tak, `FRAMSTEG.json`), observationslager för de 200 klippen och en varm maskin. Utan detta upprepas 82-minutersväntan.
2. Kör om steg 2 på den nya infrastrukturen (krav M2: < 3 min), eller läs ut nattens körning om den blev klar. Publicera ägarens blinda kontroll (12 korta par) **före** eller parallellt med automatiken.
3. Steg 3 öppnas först efter steg 2:s dom (P1:s grind kräver att `takt` och `tal_per_s` klarar A4) och efter ägarens svar på menyprovet. Skriv operatorerna som saknas (§2.6) och rätta buggen på rad 453.
4. Behåll ordningen: människans grind först, provlopp före full skala, förslag är inte låsta kontrakt.

## 8. Arbetssätt som gällt (håll fast vid det)
- **Korsfamilj:** Gemini granskar inte Gemini; T3 och T4 (GPT) granskade Claudes arbete. Varje invändning ska ha ett körbart motprov.
- **Egna mått är diagnos, inte krav.** Kalla aldrig ett utfall lyckat på egna mått (minne `feedback-egna-matt-ar-inte-krav`, `feedback-kansla-ar-helkropp`).
- **Codex:** inloggat som ägarens Plus-konto. Kvoten låg på 80 % av femtimmarsfönstret efter T4. Läs kvoten före varje uppdrag (minne `reference-codex-kvot`). Skicka prompten via stdin (minne `reference-codex-prompt-windows`): `codex exec -m gpt-6-astra -c model_reasoning_effort=xhigh -s workspace-write --skip-git-repo-check -C . - < PROMPT.md`.
- **Tidsuppskattning före start**, med provlopp. Orkestratorn bröt mot detta denna session (se diagnosen).
