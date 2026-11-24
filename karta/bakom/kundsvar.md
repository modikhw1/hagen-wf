# Kundsvar

Det kunden har gjort sedan CM var här sist. Det samlas bakom kulisserna och spelas upp som **ankomsten** när CM öppnar kunden. Det är tänkt för när CM kommer tillbaka efter ett avbrott och kunden har gjort saker på egen hand.

## Händelser

| Händelse | Vad som händer i kundrummet | Märke |
|---|---|---|
| Publicerat | Nu glider in i historiken, och planen flyttas fram | ✓ |
| Flyttat bak | Klippet lämnar platsen och går till bänken, och planen sluter sig. CM kan återanvända klippet | ↩ |
| Gillar inte | Klippet går till bänken | ✕ |
| Valt 1 eller 3 | Alternativet byter plats med 2 | Orange siffra |

Märkena sitter kvar på korten. Det finns inga symboler i sidhuvudet, eftersom de bara dubblerade det korten redan visar.

## I wireframen

`events` per kund i `app/src/data.js`, `applyEvent` och `replay` i `App.jsx`. Från steg 2.

## Öppet

- Kunden ska ta minst ett av tre. Att avvisa alla tre flyttar fram planen (pin).
- Var alternativen som kunden inte valde ska leva (pin).
