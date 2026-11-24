---
id: 0041
titel: Det skärpta kontrafaktiska testet på det vi har (liggare, Jev, regi)
status: redo
från: orkestratorn (Opus 5.5), efter ägarens utmaning 14 nov
datum: 2026-11-14
följer: –
tillåten_skrivning: [byggsten/hjarna/prov/0041/]
---

**Läs först:** `byggsten/hjarna/UTMANING.md` (särskilt A3, A10, S2, S5) och `byggsten/hjarna/PROBLEMBILD.md`.

## Varför
Ägaren har lagt "avsiktsriggen" i centrum: mening är inbakad bara om rörelsen *med nödvändighet* ändras när meningen ändras. Utmaningen skärpte testet i tre delar:
1. **Nödvändighet:** ändras meningen, så ändras rörelsen.
2. **Bevarande:** det som inte berörs är oförändrat, mätt mot originalet.
3. **Oförutsedda följder:** antalet riktiga följder som ingen har skrivit in, som skiljer ett sinne från en spridningslista.

Påståendet att pröva är att liggaren och Jev bara klarar del 1 och 2, med handskriven spridning, och nästan aldrig del 3. Stämmer det är dagens mening etiketter, och utmaningens S2 är bekräftad. Stämmer det inte är vi längre än vi tror.

## Att göra
1. **Underlaget:** de 21 CM-meningar som har prövats mot förvärlden (`forvarld/*/meningar*.json`), med befintliga utfall i `forvarld/*/ut*`, svaren 0014, 0016 och 0029–0033, samt liggarna för gelato, b-tilltal och guacamole.
2. **Per mening:**
   - Vilken regi valdes, eller `ingen_passar`?
   - Ändrades rörelsen, och var (rutor, leder)?
   - Låg rörelsen utanför ändringen kvar 1:1? Mät leddifferens mot baslinjens plan.
   - Lista de följder en människa skulle vänta sig, oberoende av liggaren. Skriv listan **innan** utfallet öppnas och lås den i `prognos.json` med tidsstämpel. Kontrollera sedan vilka som faktiskt uppstod och vilka som kom ur liggarens `spridning` (handskrivna) eller ur något annat.
3. **Klassa varje mening** enligt utmaningens tabell i A3: struktur, föremål och plats, kroppens sätt, handling, känsla.
4. **Föreslå grinden G8** för bryggan (`byggsten/brygga/grindar.py`) som en specifikation. Bygg den inte.

## Gränser
- Inga nya modellanrop, utom att köra om redan sparade utfall om de saknas (högst 0,20 dollar).
- Rör inte `scen/`, `forvarld/`, `app/` eller `video/`.

## Klart när
- En tabell med 21 rader: sort, regi, nödvändighet ja/nej, bevarande (mm), förväntade följder, uppstådda följder, varav oförutsedda.
- Den låsta prognosfilen.
- G8 som specifikation, på högst 15 rader.
- En bedömning i högst sex rader: håller S2?

## Leveransform
`delegat/svar/0041-kontrafaktiska-testet.md`, högst cirka 60 rader. Tabellen i `byggsten/hjarna/prov/0041/`.
