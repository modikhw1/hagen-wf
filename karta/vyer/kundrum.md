# Kundrummet

CM:s arbetsyta för en kund. Här ser CM läget, arrangerar planen och tar in nytt. Det är ingen dashboard. Känslan ska vara som arrangemangsvyn i en DAW: ordning, rytm och blandning syns direkt, och allt går att flytta.

Kod: `app/src/App.jsx` (komponenten `App` när en kund är vald).

## Delar

**Sidhuvud.** Kundens namn (klick tar dig tillbaka till [Ingången](ingang.md)) och balansen, se [Strategin](../bakom/strategi.md). Sidhuvudet har fast höjd, så att inget under det hoppar.

**Bänken (vänster).** Klipp CM har en relation till *för just den här kunden*. Det är inte biblioteket och inte ett sökverktyg. I datamodellen motsvarar det reserverade tilldelningar (`status: reserved`, `feed_order: null` i hagen-ui).
- Ett orört klipp är grått med originalets @konto, alltså fortfarande någon annans video.
- Ett klipp CM har gjort till kundens är svart, med ändrade scener i blått och tanken i blått under.
- Plusrutan överst öppnar popupen för inklistring. Se [Ingestkön](../bakom/ingestkon.md).

**Historiken.** De 3 senast publicerade, svagt, bakom nu-linjen. Den är bakgrund för mixen, inte en arbetsyta. Statistik hör inte hit (pin).

**Planen (höger).** Platserna nu, +1, … med minst 6 platser och alltid en tom sist. Varje plats har ett huvudkort (2) och en trio, se [Klippen › Trion](../bakom/klipp.md#trion).

**Mixspåret (under planen).** Alltid synligt. Per plats: typ (färg) och hur många som syns (ringar). Det är byggt för att få fler rader med annan metadata senare.

**Lösa kort.** När ett huvudkort med alternativ tas bort blir 1 och 3 lösa: de lägger sig i en blå ruta under planen och tomma platser pulserar. "Lägg sist" eller dra.

## Beteenden

- **Drag** mellan bänk och plan, inom planen och till 1/3 under ett kort. Medan man drar visar mixspåret och balansen hur det blir om man släpper där.
- **Drag från planen till ett annat kort byter plats i ordningen**, aldrig huvudkort.
- **Högerklick:** plan (Nästa i trion, Tidigare, Senare, Till bänken, 1/3 till bänken), bänk (Till planen, Tillbaka till biblioteket), alternativ (Gör till 2, Till bänken). Att hovra ett val förhandsvisar mixen.
- **Dubbelklick** på ett kort bläddrar i trion: 2 → 3 → 1 → 2.
- **Hovra platsen** så fälls 1 och 3 ut under kortet. De dras in snabbt igen.
- **Ankomsten:** när CM öppnar kunden spelas det upp som kunden gjort sedan sist. Se [Kundsvar](../bakom/kundsvar.md).

## Kopplingar

| Behöver | Från | Varför |
|---|---|---|
| Klipp på bänken och i planen | [Klippen](../bakom/klipp.md) | Allt kundrummet visar |
| Status för klipp som hämtas | [Ingestkön](../bakom/ingestkon.md) | Kö, nedräkning, "att granska" |
| Baslinje och typer | [Strategin](../bakom/strategi.md) | Balans och mixspår |
| Händelser sedan sist | [Kundsvar](../bakom/kundsvar.md) | Ankomsten |

| Lämnar ifrån sig | Till | Hur |
|---|---|---|
| Länkar och spellistor | [Ingestkön](../bakom/ingestkon.md) | Dra in, klistra in, plus |
| Ett klipp att granska | [Granskning](granskning.md) | Stämpeln "att granska" |
| Ett klipp att anpassa | [Anpassning](anpassning.md) | Inte kopplat än. Troligen klick eller dubbelklick på bänkkort |
| Ordning, trio, bänk | [Klippen](../bakom/klipp.md) | Drag och högerklick |
| Avsikter, baslinje | [Strategin](../bakom/strategi.md) | Balansen, och avsiktsrutan (pin) |
