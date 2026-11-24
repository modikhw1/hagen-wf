---
id: 0043
titel: Omvänd läsning av skäl (karaktärens sinne och upphovets sinne), och dess stabilitet
status: redo
från: orkestratorn (Opus 5.5), efter ägarens utmaning 14 nov
datum: 2026-11-14
följer: –
tillåten_skrivning: [byggsten/hjarna/prov/0043/]
---

**Läs först:** `byggsten/hjarna/UTMANING.md` (A1, A2, A8, S1, S7) och `PROBLEMBILD.md` avsnitt 3 (gelato i båda hjärnorna).

## Varför
Avsiktsriggen kräver skäl. För inlästa TikTok-klipp måste skälen läsas *baklänges* ur videon. Det är ett illa ställt problem, och en stark modell hittar gärna på. Utmaningen delade dessutom skälen i två sinnen:
- **upphovets** (premiss, vändning, krok, mot tittaren)
- **karaktärens** (övertygelse, avsikt, prioriteringar i scenen)

Där upphovet styr karaktären genom vad den tror ("ingen ser mig nu"). Om läsningen inte är stabil mellan körningar, eller inte går att knyta till takter och rutor, faller P6 och S1 vid ingest, och då måste skälen komma från CM eller manus i stället.

## Att göra
1. **Klipp:** gelato (`kennysgelato2.0-7596403003901381910`, har både formatkort och liggare), notan (avslöjandet), guacamole och b-tilltal. Video i `scen/klipp/`.
2. **Karaktärens sinne:**
   - Be en modell (Gemini via Vercels AI Gateway, nyckeln enligt `AI_GATEWAY_NYCKELFIL`) läsa ut, per person och tagning: övertygelser, avsikt, vad personen är beredd att offra, och prioriteringar i form av marginal, överlapp och uppmärksamhet (se 0042). Varje post ska ha belägg i klippet (tid, vad som syns eller hörs) och märkningen `sett`, `hört` eller `antaget`.
   - Ge ingest-fakta som givna: personer per tagning, transkript och skärmtext.
   - Engelsk prompt, sparad bredvid resultatet.
3. **Upphovets sinne:** samma klipp. Premiss, vändning och vad tittaren ska tro och känna vid varje takt, och vilken *övertygelse hos karaktären* som skapar takten. Utgå från formatkortet där det finns (`data/format/harness/v5/<id>.json`), men låt modellen binda varje takt till rutor och till personer.
4. **Stabilitet som i E1:** fem körningar per klipp. Mät vilka fält som är stabila (samma innehåll i minst 4 av 5) och hur mycket som är `antaget`. Jämför karaktärens skäl mot liggarens `mening`, och upphovets mot kortets kärna, takter och risk.
5. **Påhitt:** markera varje påstående som saknar belägg i klippet.

## Gränser
- Kostnadstak 0,40 dollar, eftersom gatewayens kredit är låg. Billigaste modell som tar video först. Stanna och redovisa om taket nås.
- Ingen generering av bild eller video. Rör inte `scen/`, `forvarld/`, `app/` eller `video/`.

## Klart när
- Läsningarna (5 × 4 klipp × två sinnen), med prompter.
- En stabilitetstabell per fält, andelen antaget och listan med påhitt.
- Bindningen takt → rutor → person för gelato, jämförd med liggarens händelser.
- En bedömning i högst sex rader: går skälen att läsa vid ingest, eller måste de skrivas av människor?

## Leveransform
`delegat/svar/0043-omvand-lasning-av-skal.md`, högst cirka 60 rader. Data i `byggsten/hjarna/prov/0043/`.
