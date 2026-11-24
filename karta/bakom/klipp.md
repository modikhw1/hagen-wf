# Klippen

Ett klipps liv, från någon annans video till ett publicerat klipp hos kunden. Alla vyer skriver sin del.

## Livscykel

```
länk → i kön → att granska → original → kundens → i planen → publicerat
       (ingest)  (1:a godk.)   grått     touched   2, 1 eller 3   historik
                                         (2:a godk.)
```

- **Original:** det neutrala biblioteksklippet. Det bär helst inte med sig originalets metadata ut till kunden.
- **Kundens version är en instans** (hagen-ui): biblioteket plus CM:s ändringar. Även ett orört klipp är tekniskt sett kundens.
- **Touched:** CM har skrivit en tanke eller ändrat scener. Det syns som svart kort, blå scener och blå tanke.

## Trion

En plats i planen är ett huvudkort (2) plus upp till två alternativ. Alternativen är bänkklipp som hängts på platsen.
- **1:** ett tryggt byte som fyller samma roll i mixen
- **3:** joker, som drar mixen åt ett annat håll

Alternativen finns mest för att ge kunden ett val. Det spelar mindre roll vilket som väljs, så länge balansen håller. CM erbjuder antingen alltid 1–2 alternativ eller inga alls. LeTrend antar att det oftast finns ett eller två, särskilt när 2 är svårt att filma.

| Händelse | Vad som händer |
|---|---|
| Platsen flyttas i planen | Hela trion följer med |
| 2 tas bort (till bänken) | 2 går till bänken, och **1 och 3 blir lösa** och ska in i planen igen. De går inte till bänken |
| Dubbelklick | Trion roterar: 2 → 3 → 1 → 2 |
| 1/3 dras upp på 2, eller "Gör till 2" | De byter plats |
| Bänkklipp släpps på 1/3 | Det blir alternativ. Det som låg där går till bänken |
| Kunden väljer 3 | 3 byter plats med 2 och får kundens markering |

## Fält i wireframen

`app/src/data.js`: `status`, `touched`, `cmNote`, `changed` (index för ändrade scener), `handle`, `alts {1, 3}`, `chosen`, `mark`, `series`, `format` och `picto`. Plus `kind` som räknas fram i `mix.js`.

## Kopplingar

- **Skrivs av:** [Ingestkön](ingestkon.md) (nya), [Granskning](../vyer/granskning.md) (godkänt), [Anpassning](../vyer/anpassning.md) (touched), [Kundrummet](../vyer/kundrum.md) (placering, trio) och [Kundsvar](kundsvar.md) (val, bak, nej).
