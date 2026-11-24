---
id: 0039
titel: ProtoMotions och MaskedMimic igång, och "andra handen" genom kedjan med en riktig rörelsemodell
status: redo
från: orkestratorn (Fable), efter ägarens beslut 13 nov natt
datum: 2026-11-13
följer: 0038
tillåten_skrivning: [forvarld/kropp/, scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Ordning
**Kör det här före 0038:s punkt 4 (provet), som det ersätter.** 0038:s punkt 1–3 och 5 (kartan, licenserna, beslutsunderlaget, Jev-sidan) görs ändå, gärna medan Modal-bygget här går. 0037 kör efter båda.

## Ägarens beslut
"Ladda ner MaskedMimic eller ProtoMotions och kom igång med det i pipen." Ägaren skriver samtidigt till Meshcapade om en kommersiell licens (SMPL och AMASS-tränade modeller). Tills den finns gäller: allt som bygger på AMASS-tränade vikter är **forskning**, ligger under `forvarld/kropp/forskning/` eller bakom en flagga i kedjan (`licens: forskning`), och märks så i varje utdata. Det får inte bli standardvägen förrän licensen är klar.

## Varför
0034 (optimering) och 0036 (matchning ur en liten bank) gav rörelser som når målen men inte svarar på ägarens fråga: om hon räcker fram med vänster arm, hur hade hon förflyttat sig, bytt riktning, hållit resten av kroppen? 0036 kom närmast, men vred hela kroppen 55° med fötterna glidande. MaskedMimic är tränad på tiotals timmar mänsklig rörelse i en fysiksimulering och fyller i hela kroppen ur ofullständiga mål: några leder på vissa tider, plus en referensrörelse. Det är den kroppsbundna förståelsen ägaren beskrev. Nu prövas om den håller på vårt material.

## Mål
MaskedMimic kör på Modal, tar villkoren ur liggaren och originalets rörelse, och ger en ny helkroppsrörelse för "andra handen" som går tillbaka in i förvärlden och renderas bredvid 0034, 0036 och originalet.

## Att göra
1. **Hämta och läs.** ProtoMotions (NVIDIA, Apache-2.0) med MaskedMimic. Läs README och dokumentation: vilka simulatorer stöds (Isaac Gym, IsaacLab, Genesis, andra), vilka förtränade kontrollpunkter finns och var, vilken kropp (SMPL/SMPL-X), och vad som krävs för inferens med villkor (måluppföljning av leder, referensrörelse, text).
2. **Hårdvara.** Maskinen har ingen Nvidia-GPU. Kör på Modal: en container med CUDA och den simulator som är enklast att få igång headless. Bygg avbildningen en gång och cacha den. Kör inferens som jobb; en container per jobb. Kostnadstak 10 dollar för hela uppdraget. Läs `scen/3d/ingest/modal_*.py` för hur Modal används i repot.
3. **Det som kräver ägaren.** SMPL-modellfilerna och eventuella dataset kräver registrering hos Max Planck (smpl.is.tue.mpg.de m.fl.). Du får inte skapa konton. Om något sådant behövs: stanna inte hela uppdraget. Skriv exakt vilka filer, var de laddas ned, och var de ska ligga (`forvarld/kropp/forskning/modeller/`, utanför git om sådant finns), och gör allt annat klart så att det går direkt när filerna är på plats. Sätt i så fall status `blockerat` med den listan överst.
4. **Kroppen in och ut.** MHR till SMPL för referensrörelsen och målen (MHR-repot har ett konverteringsverktyg, enligt 0034), och tillbaka till MHR för förvärlden. Mät vad som tappas i varje led (ledpositioner i cm före och efter en rundresa).
5. **Villkoren** ur `forvarld/kropp/GRANSSNITT.md`: vänster hand till tråget i h3 och till kundens hand i h6–h8, fötterna på golvet, originalets rörelse som referens för resten av kroppen. Disken som hinder om simulatorn tar en enkel geometri; annars säg vad som saknas.
6. **I kedjan.** Ett steg `kroppsmodell` som tar en frihetsgrad ur liggaren, gör villkoren, kör MaskedMimic på Modal och skriver en ny sekvens som kompilatorn bygger som vanligt. Bakom flaggan `licens: forskning`. Utan flaggan ska kedjan bete sig som i dag.
7. **Prov och bild.** "Andra handen" i förvärlden: original, 0034, 0036 och MaskedMimic bredvid varandra, med remsan. Mått som i 0034 och 0036 plus mjukhet (ryck i händer och bål, fotglidning). Titta själv på h3, h6, h8: flyttar hon fötterna, vrider hon bålen mot kunden utan att fötterna glider, ser det ut som en människa?
8. **Tid.** Kalla och varma körningar. Vad krävs för att en ändring ska ta under några sekunder.

## Gränser
- Modal högst 10 dollar. Inga köp, inga konton.
- Icke-kommersiella vikter och data bara under `forvarld/kropp/forskning/` eller bakom flaggan, märkta. Lägg inga sådana filer i `scen/` utan flaggan.
- Ingen generativ video eller bild, ingen LLM som skriver rörelsen.
- Rör inte `app/`, `video/`.

## Klart när
- ProtoMotions med MaskedMimic kör på Modal, med kommandot och avbildningen beskrivna i `forvarld/kropp/forskning/PROTOMOTIONS.md`.
- Rundresan MHR–SMPL–MHR mätt.
- Steget `kroppsmodell` i kedjan bakom flaggan.
- Filmen med fyra bredvid varandra, måtten, tre rader om vad man ser, och tiderna.
- Eller, om ägarens filer behövs: `blockerat` med exakt lista, och allt annat klart.

## Leveransform
`delegat/svar/0039-maskedmimic-i-kedjan.md` enligt mallen, högst cirka 70 rader.
