# Banken: masshämtning och urval av träningsdata

Från en lista med profiler till ett urval klipp som är värda att rekonstruera och träna på. Varje steg är billigare än nästa och sållar för det.

| Steg | Kommando | Vad | Kostnad |
|---|---|---|---|
| 1. Profiler | `npm run profiler -- <fil>` | Listan är ofta transkriberad med fel: å/ä/ö (TikTok tillåter bara a–z, 0–9, punkt och understreck) och avkortade handtag. Handtagen prövas som skrivna, sedan med ascii-vikning, sedan med Gemini och Google-sökning, och varje kandidat verifieras med yt-dlp. → `data/bank/profiler.json` | några kr |
| 2. Förurval | `npm run forurval -- [--per-profil 25] [--hamta]` | Ur metadata, utan nedladdning: längd 5–90 s, högst 900 dagar gammalt, poäng = engagemang relativt kontots egna klipp (visningar 60 %, gillanden per visning 40 %), högst 40 % ur samma serie. `--hamta` laddar ner de valda. | gratis |
| 3. Sållning | `npm run sallning` | Gemini Flash-Lite ser varje nedladdat klipp: typ (ur typlistan), personer, om det är filmat i verksamheten, bildkvalitet, montage, bildspel, texttyngd, rekonstruerbarhet 1–5. | ~0,3–1 öre per klipp |
| 4. Urval | `npm run urval -- [--mal 300]` | Användbarhet för 2D-spåret (bildspel, bildkvalitet, filmat i verksamheten; mat och montage straffas inte, se plan.md), engagemang, kvot per typ, tak per konto. Valda utan lokal analys märks `analysera`. | gratis |
| 5. Analys | `npm run analysera -- --kallor` | Den lokala analysen (Mät, Se, Tolka) för klippen i kallor.json. | ~40 s per klipp |
| 6. Rekonstruktion | `npm run rekon -- <id>` | Se [rekonstruktion.md](rekonstruktion.md). | ~2 kr per klipp (skivor) |

Klippen hämtas med yt-dlp via `uvx` (ingen installation, låst version) till `Downloads/letrend-bank/<konto>/`, med metadata i `<videoid>.info.json`. Klipp som laddats ner på annat sätt (bulktik, ssstik) registreras med `npm run importera -- <mapp>`, men saknar då visningar och gillanden.

`bank/profiler.mjs` och `bank/forurval.mjs` är skrivna av Codex (gpt-6-astra) efter en specifikation härifrån, med 22 tester.
