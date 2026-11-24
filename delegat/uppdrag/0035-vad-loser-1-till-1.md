---
id: 0035
titel: Vad löser återskapningen 1:1? Generatorn vid ingest, prövad mot originalet
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov kväll
datum: 2026-11-13
följer: 0034
tillåten_skrivning: [scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0034.** Läs `delegat/kontext/vagen.md` först.

## Varför
Ägaren 13 nov kväll: generativ video (Dreamina och andra) är **bara** till för att återskapa originalet så likt som möjligt vid ingest. Det är "den större frågan", och den förtjänar ett eget uppdrag. Allt annat vilar på den: kroppen i förvärlden, liggarens mätningar, och (enligt 0034) de tusen klippen som träningsdata. Ju trognare återskapningen, desto bättre data.

Hittills har frågan provats i en tagning (gelato S1) med fyra försök (a, k, k2, Dreamina), och ingen klarar kontrollen. Det vi vet:
- Originalets pixlar i källan binder överkroppen (k2).
- Dreamina ger hela kroppen i alla rutor men drar ut tiden, skär huvudet där källan skär det, och låter kameran glida.
- Ray 3.2 har exakt längd och nyckelbilder på tid, men inget saldo.
- Skymda delar och delar utanför bild måste antas, och det är där genereringen hittar på.

## Mål
En rangordning av vägar till 1:1-återskapning, prövad på mer än en tagning, och ett recept som kedjan kan använda.

## Att göra
1. **Vad 1:1 betyder, mätbart.** Skriv det som tre till fem mått som redan finns eller är lätta att göra: synliga leder mot originalet (promille), hela kroppen i bild, tid (vändpunkter mot källan), kamera stilla där den ska vara, inga påhittade föremål. Detta blir kedjans kontroll, inte egna krav.
2. **Kartan över vägar** (`gennedbrytning/ATERSKAPNING.md`, högst två sidor). Leverantörer och metoder som kan ta originalvideon som styrning: Dreamina (Seedance), Ray 3.2 (Luma/fal), Kling, Runway, Wan VACE (maskstyrd, provad 11 nov), och annat du hittar. Per väg: tar den video som rörelsereferens, nyckelbilder på tid, mask, exakt längd; API eller hand; pris per tagning; licens. Ägaren har sagt nej till att själv hosta videomodeller på Modal; det gäller fortfarande.
3. **Pröva på tre tagningar** med det som går att köra utan ny kostnad: Dreamina-svaret som finns, och ägarens omgång 2 och guacamole S1 om de har kommit (`d_video/dreamina-paket/*/svar/`). Saknas de, förbered dem och säg vad som väntar. Mät enligt punkt 1.
4. **Huvudet och det som är utanför bild.** Dreamina ärvde källans bildkant. Vad i källan, nyckelbilderna eller prompten får generatorn att anta det som saknas i stället för att skära? Pröva det som går utan ny generering (till exempel hur källan ramas in före genereringen), och skriv resten som recept för nästa omgång.
5. **Receptet**, högst tio rader i `STRATEGI.md`: vilken väg, vilka indata, vilka inställningar, och vad kedjan ska kontrollera efteråt.

## Gränser
- Ingen generering som gör alternativa versioner. Bara återskapning.
- Ingen ny betald generering i uppdraget utan att ägaren har kört den själv eller fyllt på saldo. Codex: högst sex bilder om nyckelbilder behövs.
- Rör inte `app/`, `video/`, `scen/3d/kontrakt/`.

## Klart när
- Måtten, kartan, utfallet på de tagningar som finns, och receptet.
- Ett eller flera paket för ägarens nästa manuella omgång, om kartan pekar dit.

## Leveransform
`delegat/svar/0035-vad-loser-1-till-1.md` enligt mallen, högst cirka 70 rader.
