---
id: 0011
titel: Depth Anything 3 (Apache 2.0) som mätt ram: fokal per tagning, metrisk skala, golv och disk som plan
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0006
tillåten_skrivning: [scen/3d/ingest/flervy_prov/]
---

## Mål
Det ska vara känt om en modell med licens som går att använda kommersiellt ger det VGGT gav (fokal, kameragrupper) och dessutom det VGGT inte gav: meter, och golv och diskens ovansida som plan.

## Bakgrund
`delegat/svar/0006-flervyrekonstruktion-pa-modal.md`. VGGT gav fokal inom cirka 10 % och bekräftade SIFT-grupperna, men licensen är icke-kommersiell, skalan blev oanvändbar (±35–50 %) och planen gick inte att passa. Tre saker i det provet kan ha gjort resultatet sämre än modellen är, och ska göras annorlunda här:
1. Personerna maskades inte. Olika personer på samma plats i rummet är för modellen olika innehåll. Kör båda: med personer, och med personerna maskade (eller deras punkter bortplockade efteråt med ingestens masker).
2. Planen söktes med höjdhistogram. Använd RANSAC för plan i punktmängden per tagning, med gravitationsriktningen som okänd, och kräv att golv och diskyta blir parallella.
3. Skalan togs ur personavståndet, som självt hänger på den antagna fokalen. Använd modellens egen metriska utdata om den har en, och kontrollera mot storlekar som inte beror på fokalen: personens längd i punktmängden (stående person, huvud till golvplan) och diskens höjd över golvet (deklarerat intervall 0,82–0,97 m).

Tolkningsnot: VGGT:s "S1/S2 mot S3/S4 är inte samma plats" gäller **kamerornas** läge. Ägarens läsning gäller var **männen** står. Det ena motsäger inte det andra. Redovisa därför båda: kameraavstånd, och avståndet mellan personernas platser i den gemensamma punktmängden.

## Underlag
- `scen/3d/ingest/flervy_prov/modal_vggt.py`, `analys.py`, `vggt_resultat.pkl` (samma bildurval ska användas, så att modellerna går att jämföra)
- Modal-volymen `hagen-rumsbank-da3-apache` finns redan i kontot. Leta i repot efter skriptet som skapade den (sök på `da3` och `rumsbank`) och återanvänd.
- Fokal ur andra källor: `scen/3d/kontrakt/ut/diag_0004/vp_tabell.md`, `scen/3d/kontrakt/ut/fore_fokal_0009/fyra_klipp.md`
- Personmasker: ingestens `masker.npy` per tagning
- Klipp: `b-tilltal-ravara`, `e-dialog-guacamole`, och `kand-kennysgelato` (rörlig kamera, två tagningar) som tredje om taket räcker

## Gränser
- Bara nya filer i `tillåten_skrivning`. Ingenting installeras i `scen/.venv`.
- Modal förhandsgodkänt enligt `REGLER.md`. Kostnadstak 1,00 dollar. Bara nyckelbilder skickas upp.
- Bekräfta licensen för just den modellvariant som körs (DA3 har varianter med olika licens) och skriv den i svaret.
- Bygg inte in något i kedjan. 0010 pågår i andra filer; rör inte dem.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Fokal per tagning för de tre klippen, bredvid VGGT, försvinningspunkter och reservvärdet. Särskilt: guacamole S1/S2 mot S3/S4 (VGGT: 1 100 mot 770 px, alltså olika zoom i samma klipp) och b-tilltal S8–S10 (VGGT: 1 400–1 650). Säger DA3 samma?
- Kameragrupper mot SIFT-facit, som i 0006.
- Skala i meter: personens längd och diskens höjd per tagning, och spridningen mellan tagningar. Är den under cirka 10 % är ramen användbar; säg vad den är.
- Golvplan och diskyta per tagning ur RANSAC: höjdskillnad, lutning mot varandra, och diskens framkant i golvkoordinater. Jämför diskens läge relativt personen med dagens plan.
- Personplatser i gemensam ram: avstånd mellan männens platser (S1/S2 mot S3/S4) och från dem till Lærkes (S5, S6–S11), med spridning över bildurvalen. Detta är hörnavståndet som i dag gissas (2,3 eller 4,1 m).
- Med och utan personmask: vad ändras.
- Topdown-bild per klipp i meter, med kameror, personplatser och diskens framkant.
- Bedömning i högst fem rader: kan detta vara kedjans mätta ram före deklarationen, och vad ska då vara givet till Gemini i stället för gissat.

## Leveransform
`delegat/svar/0011-da3-som-matt-ram.md` enligt mallen, högst cirka 80 rader, med faktisk eller uppskattad Modal-kostnad.
