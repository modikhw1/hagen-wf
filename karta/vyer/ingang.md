# Ingången

CM väljer kund. Antagandet är att CM jobbar med **en kund per pass** (4–7 kunder, 3–6 h i veckan), så det finns inga flikar för snabbväxling. Man byter kund via namnet i [Kundrummet](kundrum.md).

Varje kund visas som ett kort med initial, namn och hur full planen är (rutor).

Kod: `Entry` i `app/src/App.jsx`.

## Öppet

- Om ingången bör visa mer, till exempel att något hänt sedan sist (en prick) eller att planen håller på att ta slut. Det fanns i steg 2 men togs bort tillsammans med flikarna.
- Ingången som "föregångare", alltså vad CM möter innan kundvalet, är medvetet utelämnad.
