---
id: 0006
titel: Prov: framåtmatad flervyrekonstruktion (VGGT eller MASt3R) för lins, kameror och rum över uppställningar
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0002
tillåten_skrivning: [scen/3d/ingest/flervy_prov/]
---

## Mål
Det ska vara känt om en framåtmatad flervymodell, körd på nyckelbilder ur alla tagningar med personerna maskade, ger det som kedjan i dag saknar mätning för: brännvidd per tagning, kamerornas inbördes läge även mellan uppställningar, och en grov punktmängd av rummet (golv, väggar, diskens ovansida).

## Bakgrund
- Svar 0001: linsen är ett reservvärde (64 mm) och kamerorna är inte inbördes pålitliga.
- Svar 0002: SIFT mäter säkert vilka tagningar som delar kameraplats (S1–S2, S3–S4, S6–S7, S8–S9–S10) men ingenting mellan uppställningar, och ingen skala. Kaklet ger alias.
- Modeller som VGGT, MASt3R och DUSt3R skattar intrinsik, kameraposer och täta punktkartor direkt ur ett fåtal bilder och brukar klara glesa vyer med litet överlapp bättre än klassisk matchning. Det är oprövat här.

Uppdrag 0004 skattar linsen på andra sätt. Finns dess svar när du börjar, jämför mot det; annars räcker jämförelsen mot reservvärdet.

## Underlag
- Bildurval, masker och facitjämförelse: `scen/3d/ingest/bakgrund_prov/matcha.py` och `b_par.json` (svar 0002)
- Lösta kameror i dag: `scen/3d/kontrakt/ut/diag_0001/kameror.json`
- Hur Modal används i repot (en container per jobb, kör parallellt hellre än att spara cent): leta efter befintliga Modal-skript under `scen/3d/` (till exempel för SAM 3D Body eller GEM-X) och följ samma mönster och volymer.
- Klipp: `b-tilltal-ravara` (11 tagningar, 5 uppställningar) och `e-dialog-guacamole` (4 tagningar, facit finns).

## Gränser
- Bara nya filer i `tillåten_skrivning`. Ingenting installeras i `scen/.venv`; modellen lever i Modal-bilden.
- Modal är förhandsgodkänt enligt `REGLER.md`. Kostnadstak 1,00 dollar. Bara nyckelbilder skickas upp (högst cirka 4 per tagning), inte hela klipp.
- **Licens:** notera modellens licens i svaret (flera av dem är icke-kommersiella). Provet är en mätning av vad som går att få ut. Om resultatet bär blir licensen ägarens beslut, och ett kommersiellt gångbart alternativ ska då namnges.
- Välj en modell som huvudarm. Kör en andra bara om den första faller och taket räcker.
- Egna trösklar är diagnos och inte krav.

## Klart när
- Per tagning: skattad vertikal FOV, bredvid reservvärdet 31,4° (och 0004:s värde om det finns). Spridning mellan bildrutor i samma tagning.
- Per tagningspar: relativ pose. Jämförelse mot SIFT-facit ur 0002 (de fyra grupperna som delar plats ska ha liten förflyttning) och mot ägarens läsning: männen på ungefär samma ställe (S1/S2 mot S3/S4), Lærke i en vinkel som öppnar mot vågen (S5 mot S8–S11). Säg uttryckligen vilka kopplingar mellan uppställningar modellen ger med rimlig säkerhet och vilka som är gissning (till exempel genom att köra om med annat bildurval och se om posen står kvar).
- Skala: modellen ger rummet i egen skala. Ange skalfaktorn mot meter ur minst en känd storlek (personens längd mot läst avstånd, eller diskhöjd 0,82–0,97 m) och hur väl en andra storlek då stämmer.
- Rummet: går golvplan och diskens ovansida att passa som plan ur punktmängden, och på vilken höjd och i vilket läge hamnar disken jämfört med planen i dag.
- Guacamole som kontroll: S1–S3 delar plats enligt 0002. Säger modellen samma?
- En topdown-bild per klipp med kameror som pilar och punktmängden projicerad på golvet, så att ägaren kan se rummet.
- Bedömning i högst fem rader: kan detta bli kedjans mätta ram (PIPE 6b), före deklarationen?

## Leveransform
`delegat/svar/0006-flervyrekonstruktion-pa-modal.md` enligt mallen, högst cirka 80 rader, med faktisk Modal-kostnad. Skript, JSON och bilder i `scen/3d/ingest/flervy_prov/`.
