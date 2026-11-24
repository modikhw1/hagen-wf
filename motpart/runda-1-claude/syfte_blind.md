# Syftet, läst blint (runda 1, Claude, 19 nov 2026)

Lane: blind läsning av användarens egna spår, innan Argons deklaration (`LAGE.md`, `forvarld_karna/ARKITEKTUR.md`) och den ändrade `CLAUDE.md` lästes. Jämförelsen står i [SYFTE.md](SYFTE.md).

## 0. Metod och kontamination

**Läst:** `AGENTS.md`, `karta/` (README, arbetssatt, beslut, pins, helhet, forvarld-underlag, vyer/*, videoforandring/README, doktrin, inlarning §7, essens, overlamning-17nov, overlamning-18nov-k1, k1-del1), `byggsten/README.md`, `byggsten/hand/README.md`, `byggsten/hjarna/` (README, UTMANING), `byggsten/brygga/README.md` (huvud), `byggsten/rumshypotes/EXPERIMENT.md` (huvud), `scen/3d/PIPE.md`, `scen/3d/SYFTE.md`, `scen/3d/NASTA.md` (huvud), `forvarld/kropp/` (KARTA, BESLUT-LICENS, forskning/kimodo/textprov/RESULTAT, VILLKOR), `delegat/` (README, REGLER, kontext/*, uppdrag 0040, svar 0044), användarens minnesfiler för hagen-wf och `../hagen-ui/wiki` (CM-aktören, antaganden, beslut, icke-mål).

**Källtyp** anges för varje påstående, eftersom mycket i repot är assistenters tolkning:
- **[Ä]** ägarens egna ord, citerade med logg- eller filreferens
- **[Äb]** ägarens besked eller beslut, återgivet av en assistent
- **[T]** assistentens tolkning (märkt så i källan eller uppenbart)

Minnesfiler citeras som `minne/<fil>:rad` (mappen `~/.claude/projects/C--Users-praiseworthy-Desktop-hagen-wf/memory/`). De är andrahandskällor.

**Kontamination, redovisad:** när jag sökte var "250 ms" förekommer (`grep -rn "250 ?ms"`) visade utdata fem rader ur Argons filer: `LAGE.md:20,22,37` och `forvarld_karna/ARKITEKTUR.md:49,143`. En sökning på "seedance" listade filnamnen `LAGE.md` och `forvarld_karna/ARKITEKTUR.md`. Jag läste inget mer i dem före steg 2. Slutsatserna nedan bygger inte på de raderna; där 250 ms nämns är källan `byggsten/hand/README.md`.

---

## 1. Slutmålet

**Kortast, i ägarens ord [Ä], 10 nov:** kreativt bricolage. Ett TikTok-klipp kommer in, CM formar om det som hen föreställer sig, "omedelbart och med bra UX", ut kommer en PS2-version på en sekund som läggs i kundens tidslinje. Ägaren kallar det "best best case", och vägen dit är "i process" (`minne/project-forvarlden-och-jev.md:13`; samma i `karta/helhet.md:7`, som är orkestratorns positionering och inte ägarens beslut, `helhet.md:3`).

**Vad som faktiskt levereras [Ä], 2 nov:** "Verktyget lämnar ifrån sig det CM godkänner … det här, så som det är utformat, ska kunden återskapa genom att spela in klippet scen för scen … Renderingen (3D, 2D eller AI) finns bara för att göra det tydligt för kunden vad som ska spelas in." Följden som skrevs ned: "Manuset är produkten" (`karta/videoforandring/inlarning.md:229-230`). Det stöds av hagen-ui: kunden producerar själv, "ett aktivt designbeslut", källa ägarens beskrivning 2026-07-07 (`hagen-ui/wiki/decisions/customer-produces-content-themselves.md:11,37`), och kunden ska "veta exakt vad som ska filmas" (`hagen-ui/wiki/jobs/know-exactly-what-to-film.md:11-15`).

**Förvärlden, fas 1 [Ä], 9–10 nov:** "isolerad till ett klipp, permutation av ett klipp baserat på deras spine", styrd med vanlig chatt med bilder och noter, och den ska bära "kamera, matbilder, montage/talking head och manus". "HTML är en beskrivning av lättviktighet, inget teknikkrav" (`karta/forvarld-underlag.md:45`). Fotorealism "är inte en prioritet" (7 nov, `forvarld-underlag.md:40`).

**Spänning i källorna:** orkestratorn skrev 13 nov "Förvärlden är produkten" (`delegat/kontext/malbild.md:7`, [T], på ägarens begäran men i orkestratorns ord), medan ägaren 2 nov sade att manuset är produkten. De går att förena: förvärlden är CM:s arbetsyta, manuset med en illustrativ förhandsvisning är leveransen. Den läsningen finns redan i `byggsten/hjarna/UTMANING.md:146` (S4: "Skälen reser till kunden, rörelsen gör det inte", [T]).

**Ett andra ben som ofta glöms [Äb], 17–18 nov:** essensspåret ska kunna "placera och gradera" kundernas klipp "i en matris mot LeTrends strategi" (`karta/videoforandring/overlamning-17nov.md:9`). Ägaren gör två domar, biblioteket (överförbarhet) och smaken (publik), och de "ska inte vägas ihop till en poäng" (`karta/videoforandring/k1-del1.md:85-86`). Det är urvalssidan av samma arbetsflöde: vilket klipp CM ska forma om.

**Min sammanfattning [T]:** CM ska på den lilla tid hen har per kund kunna (1) hitta ett klipp som passar kunden och LeTrend, (2) forma om det till kundens version med några meningar, med originalets bärande delar kvar och kreativiteten hos CM, och (3) lämna ett manus som kunden kan spela in efter. Förvärlden är medlet för (2). Ett mål på "en sekund" gäller ändringen, men ägaren har inte svarat på om det räknas från meningen eller från en tolkad ändring (`helhet.md:75`; `forvarld-underlag.md:172`).

## 2. Vem är CM

| Fakta | Källa |
|---|---|
| Anställd av LeTrend, **3–6 h i veckan** | `hagen-ui/wiki/actors/content-manager.md:11,15`; `assumptions/cm-is-employee.md:15`, "ägarens uttalande i session 2026-07-07" (:24) |
| **4–7 kunder**, arbetströskel 8–12 ärenden | `content-manager.md:19` |
| Kärnarbete: följa TikTok-trender (sketcher, humor, klipp som passar marknadsföring), klistra in länkar, ändra innehåll, placera koncept på kundens tidslinje, sätta kundens tempo | `content-manager.md:15,17` |
| **En kund per pass**, inga flikar | `karta/vyer/ingang.md:3`; `karta/beslut.md:10` |
| CM styr, AI:n föreslår; "kreativitet först först först" [Ä 30 okt] | `karta/arbetssatt.md:7`; `forvarld-underlag.md:19` |
| CM talar i ytor: 1 av 21 prövade CM-meningar ber om ett inre tillstånd | `byggsten/hjarna/UTMANING.md:62-71` |
| CM har en avsikt med passet, och den avsikten är frågan harnessen besvarar [Äb 16 nov] | `minne/project-ryggrad-och-intention.md:27` |

CM är alltså ingen filmproducent och ingen 3D-operatör. Det är en deltidsanställd som kurerar och anpassar, med under en timme per kund och vecka.

## 3. Vad CM gör på en dag (ett pass)

**Tidsbudgeten** (aritmetik på raderna ovan): 3–6 h per vecka över 4–7 kunder ger **cirka 26–90 minuter per kund och vecka** för allt. Hur många koncept per vecka en kund har (tempot) varierar per kund och står inte i det jag läst; det är **okänt**.

**Passet**, i den ordning kartan beskriver det (`karta/README.md:14-37`, `karta/vyer/*`):

1. **Ingången:** välj kund (`vyer/ingang.md:3`).
2. **Ankomsten:** se vad kunden gjort sedan sist, alltså valt 1/2/3, flyttat bak, sagt nej (`vyer/kundrum.md:31`, `vyer/kundens-vy.md:7-10`).
3. **Planen och mixen:** se balansen mellan underhållning, info och marknadsföring mot en baslinje (`beslut.md:14`).
4. **Hämta nytt:** standardfiltret är "vad planen saknar just nu" (`vyer/hamta.md:10`). Länkar går till ingestkön, ett i taget, 50–70 s per klipp (`beslut.md:25`). Här verkar essensspåret: vilka klipp som är värda att ta in.
5. **Granskning, första godkännandet:** bekräfta den neutrala versionen (`vyer/granskning.md:5`). Inte byggd.
6. **Anpassning, andra godkännandet:** gör klippet till kundens. "Inte byggd. Nästa stora del." Kunden filmar själv, så det som levereras är "tydliga scener och skisser, inte färdig video" (`vyer/anpassning.md:3-9`). **Här hör förvärlden hemma.**
7. **Placera i planen** som trio 1-2-3; planen tar bara godkända klipp, och kunden väljer (`beslut.md:16,24,26`; `vyer/kundens-vy.md:5`).

Förvärlden är ett steg av sju i ett pass på under en timme. Den måste därför ge ett användbart resultat på några minuter per klipp, inklusive CM:s egen tid att formulera och granska.

## 4. Var 3D-förvärlden passar in, och var den inte gör det

**Passar:**
- **Som motor i Anpassning,** för de ändringar som originalet inte kan visa själv. Ägaren 2 nov: "3d skisser (vad jag menade med html)" ska visa ändringar som originalet inte kan bära (`forvarld-underlag.md:33`).
- **Trogen originalet där inget ändras.** Ägaren 9 nov föredrar 1:1 framför stiliserat (`forvarld-underlag.md:43`; `minne/feedback-forrendering-1till1.md:13`); 12 nov "väldigt likt 1:1 från originalet" (återgivet i `UTMANING.md:36`). AGENTS.md (16 nov) kräver att klippets kamera, tagningar, personer och rörelser följer med (`AGENTS.md:7-11`).
- **Ändringar utan generativ AI.** Ägaren 13 nov: generativ video är "bara till för att återskapa originalet 1:1 vid ingest. Aldrig alternativa versioner" (`delegat/kontext/vagen.md:39`); Jevs ändringar ska vara "blixtsnabba ändringar i 3D utan generativ AI" och kroppen ska anpassa sig i sin helhet (`vagen.md:40`; ordagrant "Nej bror. Dreamina ska inte generera alternativa versioner" i `minne/feedback-generativt-bara-for-1till1.md:8`).
- **Allmänna regler, inte handarbete per scen.** Ägaren 17 nov: "Om jag ville ha en codex/claude som återskapar varje scen i 20 min per scen, hade jag bett om det"; ett recept som Jutsu bygger på sekunder (`byggsten/rumshypotes/EXPERIMENT.md:17`; `minne/feedback-allmanna-regler-recept.md:11-15`).

**Passar inte, eller bara delvis:**
- **Inte allt är 3D.** Av 1 322 analyserade klipp har 1 113 skärmtext, 1 007 musik, 1 004 mat i fokus och 392 montage (`helhet.md:44`). Ägaren räknar själv upp matbilder, montage/talking head och manus (`forvarld-underlag.md:45`). En förvärld som bara är kroppar i ett rum täcker inte det CM arbetar med.
- **Inte alla meningar behöver scenlagret.** 7 av 21 prövade CM-meningar är rent strukturella (kamera, längd, redigering) och "behöver inget sinne alls" (`UTMANING.md:66,74`). I `byggsten/hand` routas en mening först till ryggradsnivån eller scenlagret (`byggsten/hand/README.md:224`), och ryggraden är "huvudspåret sedan ägarens besked 14 nov kväll" (`hand/README.md:15`).
- **Inte som fotorealism eller renderad mp4 per anpassning** (hagen-ui: `non-goals/photorealistic-generated-scenes.md:11`, `non-goals/rendered-video-per-adaptation.md:11-15`; hagen-ui är intention, inte facit, enligt ägaren 9 nov, `minne/project-wf-ar-frontlinjen.md:11-17`).
- **Inte som stiliserat mellanled.** PS2 är ett slutval; mellanleden ska vara realistiska och databreda (`minne/feedback-stilisering-sist.md:11-15`).
- **Inte som ensam domare.** Ägaren 14 nov ville ha en hjärna "inte lika platt som ledger/jev", bunden till innehållsanalysen (`minne/project-hjarna.md:11-13`).

**Hastighet, det som faktiskt står:**
- Ägaren: "mindre en 1 sekund" för semantiska ändringar (7 nov, `forvarld-underlag.md:39`) och "PS2-generering på 1 sekund" (10 nov, `minne/project-forvarlden-och-jev.md:13`).
- Uppmätt, inte krav: Jev 164–169 ms i median på ryggradens yta (`hand/README.md:215-217`), 170–250 ms per mening (`hand/README.md:193`), cirka 250 ms med lärda drag (`hand/README.md:128`). Förståndet tar 13–19 s (`hand/README.md:162`). Kroppen med MaskedMimic cirka 30 s per mening (`minne/project-kroppsvagen.md:17`). Den långsamma vägen 4–9 s (`scen/3d/PIPE.md:189`).
- "Egna trösklar och mått är diagnos, inte ägarens krav" (`delegat/kontext/malbild.md:35`; `minne/feedback-egna-matt-ar-inte-krav.md:8-12`).

## 5. Levande spår enligt användarens senaste överlämningar

Ordnat efter senaste överlämning. "Levande" betyder att det finns ett angivet nästa steg som väntar på ägaren eller en utförare.

| Spår | Senaste överlämning | Läge | Källa |
|---|---|---|---|
| **Essens/K1** (`video/format`, `data/format/e41`, `e42`, `kontroll/`) | **18 nov kväll**, senast av alla | Levande. Nästa: ägarens svarsfil, K1 par 13–20, K2, K3 med v2-promptar | `karta/videoforandring/overlamning-18nov-k1.md:53-69`; `k1-del1.md:93-95` |
| Essens E13–E40 | 17 nov 16:00 (essens.md 21:25) | Pausat: "Inget startas om utan ägarens ord" | `essens.md:396`; `overlamning-17nov.md:250-263` |
| Rumshypotes (video → recept → Jutsu) | 17 nov sent | Vilande experiment, "inte en del av kedjan" | `byggsten/rumshypotes/EXPERIMENT.md:3`; `minne/project-rumshypotes.md:30` |
| Kroppen: MaskedMimic + Kimodo-textprov | 16–17 nov | Vägen fungerar, men ägaren 17 nov: "ser ut som en apa … förmodligen ett annat ramverk". Licensbeslutet (A/B/C) är ägarens och öppet | `minne/feedback-kansla-ar-helkropp.md:11`; `forvarld/kropp/BESLUT-LICENS.md:3,26`; `forskning/kimodo/textprov/RESULTAT.md:22-28` |
| `byggsten/hand` (ryggrad, regibord, förståndet) | 16 nov | Huvudspår för ryggraden sedan 14 nov; "Ingen människa har bedömt något av det" | `hand/README.md:15,17,125,158` |
| `byggsten/hjarna` (problembild) | 14 nov | Uppgifter 0041–0043 och 0045 utan svar; 0044 klar 16 nov | `UTMANING.md:159-170`; `delegat/svar/` (bara 0044); `overlamning-18nov-k1.md:85` |
| `byggsten/brygga`, `byggsten/jutsu` | 14 nov, 17 nov | Experiment; kedjeändringar är förslag | `byggsten/README.md:5,18-19`; `brygga/README.md:11` |
| `scen/3d` kedjan, liggaren, `forvarld/` | 13 nov | PIPE och NASTA senast 13 nov 22:42 | `scen/3d/PIPE.md`, `NASTA.md` |
| `app/` wireframen | fryst sedan 2 nov | Steg 1–6 | `karta/README.md:62`; `delegat/kontext/lagesbild.md:9` |
| `video/` `#v` (reglaget) | 2 nov | Ett mätinstrument, inte appens layout | `karta/videoforandring/README.md:3` |

**Observation [T]:** det senaste ägaren själv arbetade med före Argons deklaration (18 nov kväll) var essens/K1, alltså urvalet och ägarens två domar. 3D-kedjans senaste överlämning är fem dagar äldre.

## 6. Förbehåll som användaren själv har satt

Det här är de spärrar en ny deklaration måste bära med sig för att inte bli en egen tolkning.

| Förbehåll | Källa |
|---|---|
| En del i taget. Föreslå nästa steg på några rader och vänta på ja | `karta/arbetssatt.md:3`; `karta/beslut.md:7`; `minne/feedback-step-by-step-no-unasked-artifacts.md:11-15` |
| Egna mått är diagnos, inte krav | `malbild.md:35`; `minne/feedback-egna-matt-ar-inte-krav.md:8-12` |
| Kalla aldrig något lyckat på ledmått. Titta på bilden | `minne/feedback-kansla-ar-helkropp.md:15`; `AGENTS.md:13-14` |
| Ingenting i `byggsten/` är del av kedjan förrän ägaren har bestämt det | `byggsten/README.md:5` |
| Kedjeändringar är förslag som kräver ägaren | `brygga/README.md:11`; `minne/project-byggsten-brygga.md:24` |
| Inget i essensspåret startas om utan ägarens ord | `essens.md:396` |
| Generativ video bara för 1:1 vid ingest | `vagen.md:39` |
| Stilisering sist | `minne/feedback-stilisering-sist.md:11` |
| hagen-ui ändras inte drastiskt förrän förvärlden bär | `helhet.md:65` |
| "Ser man det?" Ett påstående som är sant i mätningen men inte i bilden är inte klart | `vagen.md:36`; `AGENTS.md:14` |
| Behåll interaktionen som testas | `minne/feedback-keep-core-interaction.md:11-15` |

## 7. Frågor ägaren inte har besvarat (och som ingen deklaration får avgöra åt hen)

Ur `karta/helhet.md:73-80` och `karta/forvarld-underlag.md:168-175`:
1. Gäller en sekund från inskickad mening, eller från att en tolkad ändring finns?
2. Vilka tre saker måste vara trogna originalet för att förvärlden ska godkännas?
3. Visas en bifogad matbild som den är, eller är den referens för ett ombyggt motiv?
4. Får en sketch en ny säljavslutning direkt, eller krävs uttrycklig upplåsning?
5. Låses exakta repliker bara när de bär premissen?
6. Betyder "stillastående" i foodtruck-exemplet låst förflyttning med gesterna kvar?

Till det kommer licensbeslutet för kroppen (`BESLUT-LICENS.md:3`) och om en generativ slutlook (Seedance) får användas för CM:s ändringar, vilket `byggsten/jutsu/AUDIT-AVSTAND.md:77` uttryckligen lämnar åt ägaren: "Det beslutet är ditt."
