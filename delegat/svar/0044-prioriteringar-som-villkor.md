---
id: 0044
status: klart
från: uppdragstagaren (Fable)
datum: 2026-11-16
---

## Bedömning
Prioriteringar når kroppen. En ändrad prioritet, uttryckt som vilka kroppar som binds och hur deras mål förskjuts kring originalet, ger ett igenkännbart annat tillstånd, medan handlingen står kvar. Det gäller på två klipp. Tre förbehåll: måtten är mina och ingen människa har bedömt bilderna; referensens ben och rot är antagna (se nedan); och det som inte binds hittar på, så arvet måste bindas uttryckligen.

## Kontroller och licens
MaskedMimic SMPL ur ProtoMotions v3.0 (0039). AMASS-tränad, icke-kommersiell: FORSKNING. Kimodo (0040) är inte prövad.

## Vad som kördes
Vägen är allmän: `forvarld/kropp/forskning/mm/mening.py "<mening>" <namn> --kalla --liggare --scen --person --varv N`. Läget och alla siffror står i `mm/FELSOK.md`.

| mening | tagning | villkor (kort) | utfall |
|---|---|---|---|
| ont i höger höft, skyddar benet | gelato s1 A | bäcken 8 cm över vänster ben, höger fot lättad | står; höger knä böjt och avlastat |
| skopar och räcker fram med andra handen | gelato s1 A | bara vänster hand och fötter bundna, handen på högerhandens bana | vänster hand 9 cm från målet; kroppen vrider sig och tar ett steg |
| blyg, tittar ner hela tiden | gelato s1 A | huvudet 10 fram och 15 ned, mindre rörelse | huvud 7,6 cm från sitt mål; handlingen kvar (höger hand 10,8) |
| trött och ovillig, räcker fram sent | gelato s1 A | bäcken och huvud ned, handen 15 rutor sen | står; böjda knän, armen lägre |
| ivrig, sträcker sig långt fram | gelato s1 A | höger hand 26 cm fram vid ge | står; lutar fram, knäna följer. Böjningen vid skopandet försvann (fritt huvud) |
| osäker, tvekar, håller köttbiten lägre | b-tilltal s1 A | händerna 8 rutor sena och 10 cm ned | varv 1 föll, varv 2 står: händerna 13–23 cm från målen |
| håller köttbiten högre, som en trofé | b-tilltal s3 B | händerna 12–18 cm upp | står; höger hand 16 cm från originalet, vänster 9 |

Bilder: `mm/ut/mening_b_blyg/streck_blad.png` (blyg, trött, ivrig bredvid referensen), `mm/ut/mening_andra_handen3/streck_blad.png`, `mm/ut/mening_b_trofe/streck_blad.png`.

## Uppdragets tre ändringar
Uppdraget bad om uppmärksamhet, marginal och överlapp översatta för hand. Jag lät i stället förståndet översätta fria meningar till samma slags villkor, efter ägarens besked 16 nov. "Blyg" är uppmärksamheten (huvudets mål), "ont i höften" är marginalen (tyngden över ett ben), "tvekar" och "trött" är överlappet (handen startar senare). Signaturerna ur 0042 är inte mätta, eftersom 0042 inte är körd.

## Mått
- Bevarande: bäckenet 3–7 cm från originalet i alla körningar som står; obundna armar 30–40 cm (därför binds de nu).
- Fotväg: 13–48 cm över klippet, mot 25 cm när bara referensen följs.
- Ryck efter utjämning (sigma 1 ruta): i nivå med originalet.
- Möbler finns inte i simuleringen, så G4 (genom möbler) går inte att mäta.

## Det som bar
- **Slingan** (kör, mät, låt förståndet justera) rättade ett fall på slaktarklippet utan hjälp.
- **Erfarenheterna** (`mm/erfarenheter.json`, sju mätta regler) avgjorde "andra handen": utan dem 21–31 cm på tre varv, med dem 9 cm på ett.

## Avvikelser
- "Ingen språkmodell som skriver rörelsen": modellen skriver villkoren, inte rörelsen. Ägarens besked.
- Referensen är rättad av en rimlighetsgrind (`mm/tagning.py`): raka ben där benen inte syns eller ställningen inte går att stå i, och roten låst där kamerarörelse hamnat i kroppen. Besluten skrivs ut per körning.
- Remsorna är streckfigurer ur simulatorn. Utfallet finns som MHR-sekvens i kedjans format (`sekvens.npz`, rundresa 0,1 cm) men är inte kompilerat i förvärlden.

## Kostnad
Modal: cirka 60 körningar à 30–40 s under dagen, uppskattat under 2 dollar. Förståndet: Gemini gratisnivå och Codex på ägarens plan.
