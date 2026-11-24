# Uppdrag: oberoende visuell granskning av 30 genererade rum (V2) mot grinden

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Svara på svenska. Du ska bara läsa och skriva granskningsfiler, ingen kod ändras.

## Varför

Rumshjärnan låter en bildmodell ta bort personer, det de håller och överlagrad text ur en ruta per tagning (V2). Resultatet är en hypotes om rummet bakom personen. Lokaliteten släpper bara igenom hypotesen om en automatisk grind godkänner den: djupfel ≤ 12 % och kanttrohet ≥ 0,4 på de ytor originalet ser, samt lyckad linjering. Grinden har släppt igenom 26 av 30. Vi vet inte om grinden fångar det som verkligen är fel, till exempel påhittade föremål, borttagen fast inredning, ändrat utsnitt eller fel perspektiv. Det är din uppgift att avgöra.

## Material

För klippen `duepiani`, `spanjorskan`, `08burgerkebab`, `babasburgers` och `kennysgelato2.0`:

- original: `ut/rumshjarna/<klipp>/<sid>_orig.png`
- V2 registrerad till originalets utsnitt: `ut/rumshjarna/<klipp>/fyllnad/<sid>_v2.png`
- grindens dom: `ut/<klipp>/lokalitet.json` → `tagningar.<sid>.rumshjarna_fyllnad` (tillit, djupfel, trohet_synligt, linjering, konsistens)
- planen: `ut/rumshjarna/<klipp>/plan.json` (vilka tagningar som genererades mot ett ankare, dvs. i samma rum enligt geometrin)

## Uppgift

Titta på varje par (original och V2) och bedöm:

1. Utsnitt och perspektiv: är kanter och linjer på samma plats?
2. Påhittat: föremål eller inredning som inte finns i originalet och inte rimligen döljs bakom personen.
3. Borttaget som inte skulle bort: fast inredning, föremål på bord, eller ett motiv (t.ex. en tallrik som är huvudsaken).
4. Rimligheten bakom personen: fortsätter rummet trovärdigt?
5. Användbar som bakgrund bakom personen i 3D: ja, delvis eller nej. Ange skäl.

För tagningar i samma rumsgrupp, alltså genererade mot samma ankare: är rummen sinsemellan konsekventa (samma föremål på samma plats)?

Jämför sedan ditt omdöme med grindens dom: hur många av de släppta är dåliga, och hur många av de avvisade hade varit användbara? Föreslå konkreta, allmänna förbättringar av grind eller prompt, inga klippspecifika.

## Leverans

- `ut/agy/rumshjarna/granskning.json`: en post per tagning `{klipp, sid, anvandbar: ja|delvis|nej, utsnitt_ok, pahittat: [...], borttaget_fel: [...], skal, grind_tillit}`
- `ut/agy/rumshjarna/GRANSKNING.md`: korstabell mellan grind och ditt omdöme, de värsta fallen och förslag. Max 70 rader.

Sista raden i ditt svar: `KLAR` eller `BLOCKERAD: <orsak>`.
