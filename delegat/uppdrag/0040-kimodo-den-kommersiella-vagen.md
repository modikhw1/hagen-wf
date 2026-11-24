---
id: 0040
titel: Kimodo-SOMA-RP på "andra handen": den kommersiellt fria vägen, prövad mot MaskedMimic
status: redo
från: orkestratorn (Fable)
datum: 2026-11-14
följer: 0039
tillåten_skrivning: [forvarld/kropp/, scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0039, före 0037.** Läs `delegat/kontext/vagen.md` först.

## Varför
0038 hittade det som kan lösa licensfrågan utan köp: NVIDIA Kimodo-SOMA-RP tar våra villkor (händer och fötter per ruta, nyckelbilder, rotens bana, text, upp till 10 s), är tränad på 700 timmar studiomocap och har vikter under NVIDIA Open Model License, märkta "ready for commercial use". SOMA-spåraren i ProtoMotions v3.3 ger fysiken. Om den håller i bild är det standardvägen för Jevs kroppsändringar, och MaskedMimic (0039) blir bara jämförelse. Ägarens krav gäller: mening, förståelse, mjukhet, ingen robot.

Orkestratorn känner inte Kimodo sedan tidigare. Första steget är därför att bekräfta det 0038 skrev ur primärkällor.

## Att göra
1. **Bekräfta ur primärkällor:** modellkortet, licenstexten (NVIDIA Open Model License: vad den tillåter, vad den kräver, eventuella begränsningar på utdata), repot, och vilka villkor inferensen faktiskt tar. Citera de rader som avgör kommersiellt bruk. Säg rakt om något i 0038 inte stämde.
2. **Kör på Modal**, samma upplägg som 0039 (avbildningen cachad, en container per jobb). Kostnadstak 10 dollar.
3. **MHR till SOMA och tillbaka**, i samma form som `mhr_smpl.py`. Mät rundresan.
4. **Samma villkor** som 0039 (`mal.json` ur liggaren via GRANSSNITT): vänster hand till tråget i h3, till kundens hand i h6–h8, fötterna på golvet, originalets rörelse som nyckelbilder eller stil där den inte ändras. Pröva med och utan textvillkor ("hands the sample over the counter with her left hand").
5. **Med och utan SOMA-spåraren** (fysiken): ger den mindre fotglidning och genomträngning av disken?
6. **I kedjan:** `kroppsmodell`-steget från 0039 får `modell: kimodo` som alternativ. Gäller licensen enligt punkt 1, behövs ingen forskningsflagga för den vägen; skriv beslutet i `PIPE.md` som förslag, ägaren bekräftar.
7. **Bild och mått:** original, 0034, 0036, MaskedMimic, Kimodo, Kimodo + spårare, med remsan. Måtten som i 0039 inklusive mjukhet. Titta själv på h3, h6, h8. Tiderna kallt och varmt, och vad som krävs för under en sekund per fönster.

## Gränser
- Modal högst 10 dollar. Inga köp, inga konton. Gated nedladdningar som kräver konto: stanna med exakt lista åt ägaren.
- Ingen generativ video eller bild, ingen LLM som skriver rörelsen.
- Rör inte `app/`, `video/`.

## Klart när
- Licensen bekräftad med citat.
- Kimodo kör på Modal, rundresan mätt, steget i kedjan.
- Filmen med sex varianter, måtten, tre rader om vad man ser, tiderna.
- Bedömning i högst sex rader: blir Kimodo standardvägen.

## Leveransform
`delegat/svar/0040-kimodo-den-kommersiella-vagen.md`, högst cirka 60 rader.
