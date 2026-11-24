# Ingestkön

Klipp som hämtas och analyseras. Kön **lever oavsett vy**: CM kan byta kund, öppna en annan vy eller göra något annat medan klipp fortsätter att laddas in. Den deklareras från vyerna men ägs av ingen av dem.

## Regler

- **Ett klipp i taget.** De andra står som "i kö" med sin plats i kön.
- **50–70 s per klipp.** Wireframen spelar upp det 10 gånger snabbare men visar den verkliga tiden.
- **En spellista blir flera klipp**, som alla hamnar i kön.
- **Allt landar på bänken**, aldrig direkt i planen. Bara klipp som har gått igenom granskningen kan användas i planen.
- **In:**
  - en länk som dras in startar direkt
  - plus öppnar en popup som känner igen spellistor
  - Ctrl/⌘V öppnar popupen med det inklistrade

## Tillstånd

```
queued → fetch → cut → review → ready
 i kö    hämtas   klipps  att      grått original,
                  i scener granska  kan användas
```

`review → ready` är det första godkännandet, se [Granskning](../vyer/granskning.md). Det andra godkännandet, tillägg och ändringar, sker i [Anpassning](../vyer/anpassning.md).

## I wireframen

`queue`, `pump`, `ingest` och `ingestAll` i `app/src/App.jsx`. Kön ligger i en `useRef` i `App`. Den överlever byte av kund men lever i gränssnittet. I riktiga appen är den en tjänst (jfr `ingest_runs` och `ingest_batches` i hagen-ui), och vyerna prenumererar på den.

## Kopplingar

- **Deklareras från:** [Kundrummet](../vyer/kundrum.md) (länkar), [Hämta-lådan](../vyer/hamta.md) (valda klipp).
- **Läses av:** bänken (status, nedräkning) och [Granskning](../vyer/granskning.md).
- **Saknas:** besked när ett klipp blir klart medan CM är någon annanstans.

## Idéer

- **✎ redan under kön.** Minuten blir tid att tänka, och tanken kommer före AI:n.
- **En spellista som hög.** Fem klipp från samma spellista ligger som en hög på bänken och fälls ut vid hovring, som trion.
