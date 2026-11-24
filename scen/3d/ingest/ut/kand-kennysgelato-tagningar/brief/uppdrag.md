# Uppdrag: föreslå scenens deklaration

Du får ett självständigt paket med kontaktblad, `lasning.json` och `deklaration.schema.json`.
Läs alla tagningar tillsammans. Föreslå `forslag_deklaration.json` i format `deklaration/0.8` utan att hitta på mätningar.

## Det du ska avgöra

1. **Rumshypotes:** vilka tagningar delar rum och kamerauppställning; vilka personspår är samma person över tagningar; hur personerna står eller sitter i förhållande till varandra när bara en syns.
2. **Relevans i tre nivåer:** `bar_scenen` (bevaras exakt), `satter_rummet` (enkel geometri) och `stryks` (utelämnas).
3. **Öppna ägarfrågor:** skriv vad bilderna och läsningarna inte kan avgöra, särskilt identiteter, dold geometri, verkliga mått och berättelsens avsikt.

## Proveniens är obligatorisk

Varje numeriskt värde ska markeras i sitt objekt som exakt en av:

- `antagen`: gissning. Använd `[min, max]`, aldrig ett hårt tal, där 0.8-formatet tillåter intervall.
- `last`: hämtat ur `lasning.json`. Ange `kalla` eller fältspecifik `*_kalla` med exakt JSON-sökväg.
- `deklarerad`: uttryckligen sagt av ägaren, inte slutsats från bild.

## Ett rum, en ram, namn som kedjan kräver

- Alla `pos_m` och `mitt_m` ligger i en gemensam ram i meter (golvet z = 0). Lägg inte uppställningar som öar långt isär. Är det inbördes läget okänt, gissa ett rimligt läge i samma lokal och märk det `antagen`.
- Roller som syns i bild heter `A`, `B`, `C` … i den ordning de först syns; lägg personens namn i fältet `namn`.
- En rolls hemplats heter `staplats_<roll>` (stående) eller `stol_<roll>` (sittande). Övriga platser där rollen står har `roll: null` och anges via `kameror.<S>.person_plats`.
- Föremål som står på en möbel (våg, kassa, tallrik) är inga platser; formatet saknar staplade föremål, så beskriv dem under `relevans`.

Använd `hojd_status` för `kameror.*.hojd_m` och annars `status` på närmaste objekt. Hårda antagna tal är bara tillåtna för fält där översättaren kräver ett skalärt värde (t.ex. spår-id och blickvinkel). En status gäller inte automatiskt ett annat objekts tal.

Validera förslaget med:

```text
python ingest/scenbrief.py granska ingest/ut/<klipp> ingest/ut/<klipp>/brief/forslag_deklaration.json
```
