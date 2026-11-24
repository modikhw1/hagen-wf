# Uppdrag: visuellt facit för 0.0 (38 tagningar), mot pipens egen tillförlitlighetsdom

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Svara på svenska. Ändra ingen kod.

## Varför

0.0 är scenen före all modifiering: originalvideon avläst till 3D. Den består av rummet som texturerade nät per objekt, personer som kroppar (blå dockor), kamerans lutning och höjd, och skalan. Pipen ska fungera "god nog" för de kommande 200–500 klippen, men vi saknar facit för vad i avläsningen som går att lita på. Pipen dömer sig själv per tagning (L8, `tillforlitlighet.dom`: hög / medel / låg / konflikt / okänd). Din dom är det oberoende facit, och den avgör vad avläsningen ska förbättras på först.

## Material

Klipp: `duepiani`, `spanjorskan`, `08burgerkebab`, `babasburgers`, `kennysgelato2.0` (38 tagningar). Tagningarna och deras mittruta står i `ut/rumshjarna/<klipp>/plan.json` (`tagningar.<sid>.ruta`). Per tagning:

- original: `ut/rumshjarna/<klipp>/<sid>_orig.png`
- 0.0 sett från originalkameran: `ut/<klipp>/qa/orbit-<ruta>-0.png`
- 0.0 vriden 35°: `ut/<klipp>/qa/orbit-<ruta>-35.png` (`-35f.png`: samma vy med varje nätbit i egen färg)
- hela rummet vridet 50°: `ut/<klipp>/qa/orbit-<ruta>-50h.png`
- pipens dom: `ut/<klipp>/lokalitet.json` → `tagningar.<sid>.tillforlitlighet` (dom och skäl). Där finns också `lutning_grader`, `kamerahojd`, `skala`, `rumshjarna_fyllnad` (genererad fyllnad bakom personen, `tillit`) och `kamerarorelse`.

Mörka partier i vridna vyer är normalt: originalkameran såg aldrig de ytorna. Döm det som syntes i originalet.

## Bedöm per tagning (ok / brist / fel, med kort skäl)

1. **Kamera:** horisont och lutning stämmer med originalet, och vyn från originalkameran täcker samma utsnitt.
2. **Golv och kontakt:** personen står eller sitter på golvet, stolen eller bänken, inte i luften och inte nedsjunken.
3. **Skala:** personens storlek mot rummet (dörrar, bänkar, bord).
4. **Rum:** väggar, golv och bänkar är plana och sammanhängande, inte trasiga skärvor; hål och spöksiluetter bakom personen.
5. **Objekt:** viktiga föremål (tallrikar, mat, det personen håller) ligger på rätt plats och på ytor, de svävar inte och skär inte genom bord.
6. **Kropp:** dockans pose och läge matchar personen. Hon håller det hon håller, och kroppen skär inte in i möbler.
7. **Helhet:** `god_nog` ja / delvis / nej, som utgångspunkt för att regissera om scenen.

## Leverans

- `ut/agy/facit00/facit.json`: en post per tagning `{klipp, sid, kamera, golv, skala, rum, objekt, kropp, god_nog, skal: {...}, L8_dom}`, där varje kategori är `{dom, skal}`.
- `ut/agy/facit00/FACIT.md` (max 80 rader), med fyra delar:
  - en korstabell mellan L8-domen och `god_nog`
  - vilka kategorier som brister oftast, rangordnade efter hur ofta och hur allvarligt
  - var L8 säger hög men bilden är dålig, och tvärtom
  - de fem vanligaste felen formulerade som allmänna problem i avläsningen, alltså vilket steg i pipen som rimligen orsakar dem (MoGe-djup, OneFormer-segmentering, skala via kroppen, golvplan, SAM 3D Body-kropp, registrering och så vidare), inga klippspecifika lösningar

Sista raden: `KLAR` eller `BLOCKERAD: <orsak>`.
