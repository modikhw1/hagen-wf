# Kimodo textprov: känsla, formulering, textvikt (17 nov 2026)
Man bakom disk visar köttbit, 3 s, 20 varianter × 4 prov (samma frö 7 i alla varianter, så startbruset är gemensamt). Modellen laddad en gång per container (A10 54 s, sedan 7 s per variant om 4 prov). Filer: `prov.py` (Modal, app hagen-kimodo-textprov), `mat.py` → `matt.csv`/`matt.md`/`prov.csv`, `bild.py` → `streck_uttrakad.png`, rådata `ut/`.
Mått: vrid = huvud (ögonlinje) mot höft (höftlinje) i golvplanet; nick = huvud mot bål (≈40° = tittar ner på köttet); axelsänk = axlarnas fall mot nacken; hand = medelhöjd (0,89 m = armar hängande); rörelse/fart = kroppsleder; spridn = medelavstånd mellan de 4 proven, höftrelativt.

| variant | w | vrid max° | vrid slut° | nick max° | axelsänk cm | hand start→slut m | rörelse m | fart m/s | spridn cm |
|---|---|---|---|---|---|---|---|---|---|
| neutral | 2 | 26±11 | 16±6 | 44 | 0,8 | 1,13→1,11 | 5 | 0,07 | 5,1 |
| uttråkad (ordet) | 2 | 22±10 | 11±9 | 43 | 0,1 | 0,99→1,14 | 4 | 0,06 | 4,6 |
| stolt | 2 | 29±16 | 16±11 | 41 | 1,0 | 1,19→1,21 | 5 | 0,07 | 5,0 |
| nervös | 2 | 28±16 | 17±9 | 46 | 1,1 | 1,10→1,08 | 5 | 0,07 | 4,3 |
| trött | 2 | 28±8 | 19±11 | 42 | 0,3 | 0,95→1,08 | 3 | 0,04 | 4,9 |
| irriterad | 2 | 35±11 | 23±11 | 52 | 1,6 | 1,22→1,23 | 8 | 0,12 | 5,5 |
| kroppslig beskrivning | 2 | 25±12 | 16±13 | 40 | 0,7 | 1,14→1,03 | 4 | 0,06 | 4,2 |
| tempo (slowly, lazily) | 2 | 22±10 | 11±10 | 38 | 0,2 | 1,03→1,23 | 4 | 0,06 | 4,9 |
| kombination | 2 | 22±10 | 14±10 | 37 | 0,4 | 1,14→1,14 | 4 | 0,05 | 4,1 |
| kroppslig, w 1 / 2,5 / 4 / 6 | | 26/24/25/27 | 9/14/15/15 | 41–42 | 0,7–1,0 | slut 0,98/1,04/1,01/0,99 | 4/4/6/7 | 0,05→0,10 | 4,1–5,1 |
| kombination, w 1 / 2,5 / 4 / 6 | | 24/20/19/21 | 16/13/10/9 | 37–39 | 0,4–0,6 | slut 1,12/1,13/1,10/1,08 | 4/4/5/6 | 0,05→0,09 | 4,2–4,8 |
| **i följd** visa 1,5 s + uttråkad kropp 1,5 s, w 2 | 2 | 14±5 | 6±7 | 44 | 0,8 | 1,05→0,89 | 5 | 0,07 | 5,0 |
| **i följd, w 4** | 4 | 37±12 | **31±12** | 49 | 0,9 | 1,04→**0,89** | 7 | 0,10 | 6,6 |
| kontroll: bara "turns his head to the left" | 2 | 81±6 | 73±11 | 2 | 0,1 | 0,89→0,91 | 2 | 0,03 | 5,3 |

## Slutsats
- **En mening med känsloord bär energi, inte gest.** Känsloordet styr tempo och handhöjd (trött 0,04 m/s och lägre händer; irriterad 0,12 m/s, mest huvudrörelse; uttråkad startar med lägre händer). Ingen formulering i en enda mening vrider huvudet mer än neutral (vrid slut 9–16° mot 16°), och axlarna sjunker inte mätbart (≤1 cm i alla). Visningen av köttet dominerar meningen.
- **Det som bär är att dela upp i två delar i följd** (`model([visa, uttråkad], [1,5 s, 1,5 s], multi_prompt=True)`) **med textvikt 4**: armarna sjunker till hängande (0,89 m), huvudet vrids 43° och stannar där i 3 av 4 prov (det fjärde 14°). I streckbilderna ser rörelsen naturlig ut: köttet visas, armarna faller, blicken går åt sidan. Med w 2 sjunker armarna men huvudet vrids knappt (6°).
- **Textvikt:** 4 är bäst. w 6 ökar rörelsemängden med 50 % och ger konstiga gester (w_kropp_6: en hand upp mot huvudet i flera prov). w 1 tappar innehållet. Vikt utan uppdelning hjälper inte huvudvridningen.
- Kontrollen visar att måttet och modellen klarar huvudvridning (73°) när meningen bara handlar om det.
- **Spridning:** 4–7 cm mellan prov, lika stor som skillnaden mellan formuleringar. Huvudvridningen har sd ≈ 10–12° i alla varianter, så ett enskilt prov säger lite om formuleringen. Proven vrider åt olika håll (vänster/höger), så sidan måste anges om den spelar roll.
- **Antal prov:** dra 4 per mening (≈7 s på en A10 i en batch) och välj automatiskt på det mätta draget (här vrid slut > 25° och hand slut < 0,95 m). Med träff i 3 av 4 är risken att alla 4 missar under 1 %. Jämförelser mellan formuleringar kräver ≥ 8 prov per variant.
- Uppdelningen kräver punkt mellan delarna i CLI:t (varje del får hela --duration), så ange tider per del (`--duration "1.5 1.5"`) eller använd API:t som här.

Kostnad: 2 Modal-körningar, 3 containrar (2 × A10 ca 2,5 min, 1 × L40S ca 1,5 min), uppskattat ca 0,15–0,25 USD.
