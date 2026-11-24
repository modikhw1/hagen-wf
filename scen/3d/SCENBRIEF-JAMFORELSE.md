# Blindförslag mot befintliga deklarationer (12 nov 2026)

Förslagen skrevs från paketens kontaktblad och `lasning.json`; först därefter öppnades deklarationerna för denna jämförelse. "Stöd" avser bild-/kropps-/diagnostikläsning, inte vad som verkar normalt i ett verkligt rum.

## a-sketch-servering-tagningar

| Fältgrupp | Överens | Skillnad | Vad läsningarna stöder |
|---|---|---|---|
| Format/ram | Samma klipp, meter, +Z och origo hos A | förslag 0.8 och golvintervall −0,05–0,05; befintlig 0.4 och hårt 0 | Inga fötter syns: ingen metrisk golvhöjd är läst. Intervallets osäkerhet stöds, inte dess gränser. |
| Rum/tagningar | S1–S7 är samma gatukök, A kund, B personal, disk emellan, B flyttar mellan disk/spett/bänk | ingen semantisk skillnad | Kontaktbladen stöder samma handling och delade rum; exakta lägen är okända. |
| Roller | Exakt samma A=S1,S7 och B=S2–S5, båda står | förslaget frågar uttryckligen om stark ansiktslikhet betyder samma skådespelare | Bilden stöder kläder/funktion som två berättelseroller men kan inte avgöra ägarens rollavsikt. |
| Platser | A vid (0,0), B bakom disken, blickar ±90° | förslag har tre B-platser (disk/spett/bänk); befintlig har bara B:s hemplats. B-y 1,50 mot 1,30 | Bilderna stöder tre arbetslägen men ingen metrisk koordinat. Förslagets topologi har mer bildstöd; inget avstånd har det. |
| Disk | Båda beskriver samma glas-/serveringsdisk | förslag: massiv och intervall 2,0–3,2 × 0,45–0,80 × 0,90–1,20; befintlig: hårt 2,4 × 0,6 × 1,1 | Rumscachen har inga godkända diskmått. Intervall är ärligare; massiv låda är bara en grov formhypotes. |
| Kameror | Samma motiv per S1–S7 och S6 utan person; övriga spår 1 | förslag anger huvudroll/plats och 1,2–1,6 m (S3/S4 1,0–1,6); befintlig hårt 1,35 m | Inga fötter/kända höjder: ingen hård kamerahöjd stöds. Kropparnas kameraavstånd stöder bara bildens relativa djup. |
| Närvaro | Exakt A+B i S1–S7 och samma kamerabärare | ingen sakskillnad | Berättelsehypotes, inte mätbar när bara en/ingen syns; ägaren måste godkänna. |
| Relevans | Mat, spett/kniv, händer, ansikten bär; disk, bänk/ugn, fönster sätter; text, folk, pynt stryks | förslaget nämner även glas, gester och logotyper som igenkänningstecken | Kontaktbladen stöder båda; relevans är ett ägarbeslut. S3:s två "card payment terminal"-detektioner motsägs visuellt av spettet och bör inte styra. |

## e-dialog-guacamole-tagningar

| Fältgrupp | Överens | Skillnad | Vad läsningarna stöder |
|---|---|---|---|
| Format/ram | Båda 0.8, meter, +Z, origo hos A | förslag golv −0,05–0,05; befintlig hårt 0 | Inga fötter: bara lokal nollnivå, inget metrisk golvmått. |
| Rum/tagningar | Exakt samma bar, S1–S4, A sittande kund och B stående personal på var sin sida | ingen sakskillnad | Kontaktblad, semantikcache och S4 med båda stöder detta starkt. |
| Roller/spår | Exakt A=P1 S1:1/S3:1/S4:2; B=P2 S2:1/S4:1 | förslaget märker identiteter/hållning `last` med briefkälla | `lasning.json` stöder befintlig och förslag lika. S2:2 saknar kropp och är förgrundsarm, inte ny roll. |
| A:s plats | Samma (0,0), blick +90°, barstol | förslag sitthöjd 0,65–0,85; befintlig hårt 0,75 | Inga fötter/sitsyta: intervallet uttrycker osäkerheten bättre; inga gränser är lästa. |
| B:s plats | Samma axel, blick −90° | förslag antaget y=1,60; befintlig läst y=1,73 och noterat intervall 1,60–1,85 | Diagnostiken stöder befintlig: S4 läser A–B 1,734 m och S2 stödjer 1,60–1,85; förslaget saknade denna korsrollsläsning. |
| Bardisk | Båda massiv med intervall och samma huvudform | förslag 2,0–3,5 × 0,5–0,9 × 0,95–1,20, mitt-y 0,5–0,9; befintlig 2,8 hårt, 0,5–0,8 × 0,95–1,15, mitt-y 0,5–0,8 | Diagnostiken väljer 2,80 × 0,65 × 1,00, mitt-y 0,65 och stöder befintligt intervall bättre. Längden 2,8 är ändå inte bildmätt. |
| Kameror | Exakt huvudroll, spår och personplats; S1/S3 mot A, S2/S4 mot B | förslag 1,2–1,6 och kamera_vid för motbilder; befintlig hårt 1,40 utan kamera_vid | Bildtrohetsdiagnosen bevarar 1,40 och projektionen är inom gränser, men höjden är fortfarande antagen; intervallet är korrekt proveniens. S4 är egen station i båda. |
| Närvaro | Exakt A+B i alla tagningar och samma kamerabärare | ingen sakskillnad | S4 bevisar samnärvaro; övriga tagningars dolda närvaro är berättelsehypotes. |
| Relevans | Dialog/gester/meny bär; bardisk/barstol/vägg sätter; etiketter/dekor/logotyper stryks | förslaget behåller kassaterminal och förenklade hängglas som rumsmarkörer; befintlig stryker hängglas | Bilderna visar båda men nivån kan inte utläsas: ägaren avgör. Text/taltider stöder dialogens betydelse men texten är modellsemantik, inte granskad OCR. |

## Slutsats

Förslagen hittar rum, roller, kameragrupper och relevans väl. De missar eller kan inte belägga det som kräver flerrollsdiagnostik eller ägarbeslut: A–B-avståndet, verkliga disk-/sits-/kameramått, dolda personers närvaro, rollavsikt och exakt relevans. Guacamoles befintliga deklaration är bättre där senare läsningar har förts tillbaka; båda befintliga filer behöver den nya talproveniensens konsekventa märkningar/intervall.
