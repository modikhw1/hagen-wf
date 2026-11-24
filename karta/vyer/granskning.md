# Granskning

**Inte byggd.** Det är porten mellan [Ingestkön](../bakom/ingestkon.md) och [Anpassning](anpassning.md).

När ett klipp är klart i kön får det stämpeln **att granska** på bänken. Granskningen är det **första godkännandet**: CM bekräftar den neutrala versionen, alltså att analysen och scenindelningen stämmer med originalet. Först därefter går klippet att använda i planen.

I wireframen godkänner ett klick på stämpeln direkt (`approve` i `App.jsx`). Det är en platshållare.

## Kopplingar

- **In:** klipp med status `review` från [Ingestkön](../bakom/ingestkon.md).
- **Ut:** klippet blir `ready` (ett grått original) i [Klippen](../bakom/klipp.md). Därifrån kan det gå vidare till [Anpassning](anpassning.md), som är det andra godkännandet.

## Idéer som hör hit

- "In bara med en tanke" (pin): godkänn den neutrala versionen plus en rad från CM.
- Harnessen kan visa var i planen klippet passar mixen, eller att det fortsätter en serie. Bara en hint, inget förbud. Se [Strategin](../bakom/strategi.md#harnessen).
- Det CM skrev i ✎ under kön följer med hit.
