# Argon-prov: rumsgeometri ur video (17 nov 2026)

Fråga: ger gemini-4-argon (och gemini-3.1-pro-preview) via ägarens Vertex-proxy bättre rumsgeometri i variant `scen3d` än gemini-2.5-flash gav 12 nov?

## Hur

- `rum_video.py --via beacon` (ny flagga): samma prompt, schema och video som gateway-vägen, översatt till Vertex-format och skickat till token-budget-beacon med `upstreamStream: true`. Argon får inget `thinkingConfig`. För argon stryks "and sound" ur scen3d-promptens ledtrådslista. Prompten frågar inte om tal. Gateway-vägen är fortfarande förval.
- Mätt med `rum_video_mat.py` på samma sätt som för flash.

## Resultat (mätt)

| modell | körning | median \|x-fel\| px (av 576) | median \|topp-fel\| px | median \|fot-fel\| px | max \|fel\| px | identiteter | kostnad USD | tid |
|---|---|---|---|---|---|---|---|---|
| gemini-2.5-flash (12 nov) | k1 | 107,5 | 114,4 | 620,9 | 1 375 (x, S9) | Mads S1–2, Morten S3–4, Lærke S5–11 (rätt) | 0,041 | ej loggad |
| gemini-2.5-flash (12 nov) | k2 | 75,3 | 388,8 | 282,2 | 513 (topp, S7) | Mads S1–S6 (fel) | 0,057 | ej loggad |
| gemini-4-argon | k1 | 72,6 | 110,1 | 672,0 | 1 055 (fot, S9) | samma som flash k1 (rätt) | 0,058 | 67 s |
| gemini-4-argon | k2 | 71,9 | 73,8 | 1 049,8 | 1 431 (fot, S9) | samma som flash k1 (rätt) | 0,044 | 64 s |
| gemini-3.1-pro-preview | k1, k2 | – | – | – | – | – | 0 | blockerad |

gemini-3.1-pro-preview: båda körningarna stoppades av proxyn, även ett nytt försök cirka 5 minuter senare. Felraden var:
`beacon HTTP 503: b'{"error":"quota_exhausted","placeholder":true,"upstream_status":429,"message":"Vertex AI quota exhausted. Retry later."}'`

Total kostnad för provet: 0,102 USD (två argon-anrop).

## Vad som syns (mätt)

- **Identiteter:** argon gav samma uppdelning i båda körningarna (Mads, Morten, Lærke). Namnen kommer ur skärmtexten. Flash gav rätt i 1 av 2 körningar.
- **Kamerauppställningar:** argon återanvände uppställningar med `samma_som` (S1=S2, S3=S4, S6=S7 …). Det gjorde flash inte.
- **x-fel:** 72 px mot flashs 75–108 px. Det är marginellt bättre, och felen är jämnare (S1–S4 under 80 px).
- **Topp-fel:** 74–110 px mot 114–389 px. Det är bättre.
- **Fot-fel:** 672–1 050 px mot 282–621 px. Det är tydligt sämre. Kamerahöjden är 1,3–1,4 m och lutningen nära 0 på cirka 1,3 m avstånd, så fötterna hamnar långt under bild trots att originalet visar dem i bild.
- **Avstånd:** argon bröt mot ett givet faktum i S5 (2,5 m mot läst 3,7 m, kvot 0,67) i båda körningarna. Övriga avstånd ligger inom 1,0–1,1.

## Bedömning (tolkning, inte mätt)

Argon är stabilare semantiskt: identiteter och uppställningar blev desamma i båda körningarna. Geometrin är inte klart bättre. x och topp förbättras lite, men fot och max-fel blir sämre, och ett givet avstånd motsägs. Slutsatsen från 12 nov står kvar: geometrin bärs av lösaren och inte av modellen. Steg 4 (variant deklaration ×3 med `--reparera 2`, konsensus och jämförelse mot v0.3) kördes därför inte. Två körningar per modell är för få för att säga något om spridningen.

## Filer

- `rum_video_scen3d_gemini-4-argon_k1.json`, `rum_video_scen3d_gemini-4-argon_k2.json`
- Flash som jämförelse: `rum_video_scen3d_k1.json`, `rum_video_scen3d_k2.json`
