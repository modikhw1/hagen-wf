# Strategin

Den övergripande bilden av hur kundens feed ska vara. Den är **länkad till kundrummet men abstraherad**: CM deklarerar den genom vyn (planens blandning, avsikter, serier), och den hålls bakom kulisserna där harnessen och andra vyer kan läsa den.

Grundhållning: CM vet redan intuitivt vart hen vill. Strategin **nudgar och visar, den överrider aldrig** CM:s intuition. Balansen är godtycklig och ska därför vara tyst.

## Delar

**Typer.** Varje klipp har en typ: underhållning, info eller marknadsföring. Den räknas fram ur formatet och kan rättas. Kod: `app/src/mix.js` (`KINDS`, `kindOf`).

**Baslinjen.** Till exempel 60/20/20. Den ställs **inte in i början**, eftersom det vore att definiera en magkänsla. Den räknas fram över tid ur publicerade klipp, eller blir en av 1–3 LeTrend-baslinjer som innehållet normaliseras mot. Kod: `BASE` i `mix.js`.

**Balansen** (sidhuvudet). En tunn, blek remsa. Den fälls ut vid hovring, fästs med klick och uppdateras live vid drag och förhandsvisning. Den varnar aldrig.

**Mixspåret** (under planen). Typ och hur många som syns per plats. Det ska kunna få fler rader med annan metadata. Längd togs bort: den hör till förhandsvisning eller klippets info.

**Serier.** Klipp i samma serie hör ihop (Nonnas regler). De ritas i steg 6, men det är inte omarbetat.

**Tempo.** Antal klipp per vecka, och därmed hur långt fram planen räcker.

**Avsikter** (pin). Varor, teman och händelser CM vill lyfta, som ikoner i en ruta där balansen sitter i dag. De blir kort för marknadsföring i planen. Risk: CM har redan avsikten i huvudet, och då blir det två platser för samma sak.

**Ton och humor.** Sitter i CM:s huvud. Ska inte definieras nu.

## Harnessen

Harnessen läser strategin, men tillämpar ingenting själv. Tänkta hintar:
- platser som lyser svagt där ett nytt klipp skulle balansera mixen
- att ett klipp fortsätter en serie
- förslag på alternativ 1 och 3

Steg 6 i wireframen visar en gammal version (lås, streckade alternativ, serielinje, formatbåge). Den är inte omarbetad efter de senaste besluten.

## Kopplingar

- **Deklareras från:** [Kundrummet](../vyer/kundrum.md) (planens innehåll, och avsiktsrutan när den finns), plus publicerade klipp över tid.
- **Läses av:** Kundrummet (balans, spår), [Hämta-lådan](../vyer/hamta.md) (filtret "vad saknas"), [Granskning](../vyer/granskning.md) (hintar), harnessen.
