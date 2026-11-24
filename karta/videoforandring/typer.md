# Innehållstyper och takter (för skyddsräckena)

Skyddsräckena ska följa hur TikTok-klipp klassiskt komponeras, per innehållstyp och per plats i klippet. Typerna är föreslagna av Gemini och grundade i biblioteket, inte i en lista vi hittat på.

## Hur

`npm run typer -- <fas>` (kod i `app/typer/`, data i `data/typer/`):

1. **forslag**: `gemini-3.5-flash-lite` ser varje klipp (480p, 2 fps, med ljud) tillsammans med analysens scengränser. Den ger syfte, hagen-uis `primary_intent` (A/B/C) och `mechanic` (1–4), en fri typ, och per scen funktion, kamera, varför scenen är filmad så och en egen rörlighetsbedömning 1–10.
2. **typlista**: `gemini-3.1-pro-preview` slår ihop förslagen till en sluten lista med typer (öppning, mitt, slut och scenografi per typ) och scenfunktioner (med vad varje funktion kräver av kameran). Resultatet ligger i `data/typer/typer.json`.
3. **marka**: flash-lite märker varje klipp mot de slutna listorna. Det ger typ, säkerhet, näst bästa typ, funktion och rörlighet per scen, samt **takter**: dramaturgin i tid, oberoende av bildklippen. En enda tagning har alltså också öppning, mitt och slut.

Autentisering sker med `gcloud auth print-access-token` mot Vertex i projektet Hagen. Ingen nyckel ligger i repot. Allt cachas med scengränsernas fingeravtryck, så ett klipp görs om bara när analysen ändrats.

## Första körningen (31 okt 2026, 26 klipp, 1,91 kr totalt)

| Typ | Antal | Intent |
|---|---|---|
| Relaterbar sketch | 17 | A |
| Värdens provsmakning | 4 | B |
| Direkt tilltal | 3 | B |
| Matporr och process | 2 | B |

Scenfunktioner: krok, uppbyggnad, produktbild, vändning, punchline, reaktion, uppmaning.

Att notera:

- **Humor med produkt finns inte som egen typ.** Pro slog ihop den med sketch. Tre klipp har A-intent men en säljandel på minst 0,4, och sannegarden-1050091 slutar i en uppmaning.
- **Gränserna är osäkra på två ställen.** coknajsbar-841300 och elbirria bytte typ mellan två märkningar.
- **Biblioteket är för litet för skyddsräcken per typ och plats.** Typerna utanför sketch har 2–4 klipp var. Det räcker för att se mönster, inte för att sätta gränser.
