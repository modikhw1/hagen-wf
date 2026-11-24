---
id: 0027
titel: Kroppens plats i världen: roten ur en kamerafri generering, och föremålet som följer en ny kropp
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0026
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

## Mål
En kropp som lästs ur en kamerafri generering står på rätt plats och i rätt storlek i förvärlden under hela tagningen, också när originalets kamera zoomar och tippar. Skeden sitter i handen på den nya kroppen. Lösningen ska gälla nästa klipp och nästa generator, inte bara gelato S1.

## Bakgrund
Svar 0026 pekar ut det svagaste ledet: rotens plats i världen genom inversen. Felet är detsamma i k, k2 och Dreamina, så det ligger inte i genereringen. Orkestratorns läsning av `s_scen/film_rutor.jpg`:
- Planruta 70 (h4): kroppen fyller hela bilden, kameran är i praktiken inne i henne. Originalet visar hennes arm och tråget uppifrån.
- Planruta 100–150 (h6–h9): hon är ungefär dubbelt så stor som i originalet.
- Påståendena i handlingsspåret mäts som sanna i scenen, men bilden bär dem inte. Tråget och kunden syns inte så att en betraktare förstår dem. Mätt sant räcker inte: scenen ska gå att se.

Två saker till ur 0026:
- Skeden hänger cirka 5 cm från fingrarna i rutorna 45–62. Handfästet är mätt mot gårdagens kropp.
- Inversen (roten: Z' = sZ, X' = X + Z(c − t − sc)/f, se `STRATEGI.md`) bygger på en likformig avbildning i bild, skattad ur överkroppens 2D-leder. Den vet inget om att kameran tippar, och Dreamina hade dessutom en egen kameraglidning (fotlinjen 1121 till 892 px).

## Att göra
1. **Var sitter felet?** Dela upp rotens fel per ruta i sina delar: den kamerafria avbildningens skala, genereringens egen kameraglidning, läsarens djup, planens lösta kamerabana (zoom mot dolly), och tidspassningen. Mät mot det som är känt: i originalets rutor ska kroppens synliga leder projiceras där de syns (promille per ruta), och fötterna ska stå still på golvet bakom disken. En tabell: vilken del står för hur mycket, i h3–h4 och i h6–h9.
2. **Rätta platsen ur det som är mätt.** Roten ska bestämmas av originalet där det syns, inte ärvas ur genereringens ram. Kandidater, välj efter punkt 1: lös rotens läge per ruta så att de synliga överkroppslederna projiceras rätt genom planens kamera, med villkoret att fötterna står still (handlingsspåret säger när hon står); eller skatta genereringens kameraglidning ur golvlinjen och ta bort den före läsningen. Kroppens form och ledvinklar kommer fortfarande ur den enda genereringen. Det här är placering, inte sammansättning: säg till om du bedömer att gränsen passeras.
3. **Föremålet följer kroppen.** Handfästet räknas om mot den kropp som faktiskt används, ur var skeden syns i genereringen (den är inbakad där). Gör det som ett steg som går för vilken kropp och vilket handföremål som helst.
4. **Scenen ska gå att se.** Rendera S1 igen med rättad rot. Disken ska läsas som en disk med tråg (ljusare yta, synlig öppning), och kunden ska synas när hen finns i originalets bild (handen i h8). Ingen stilisering utöver det: enkla former, tydliga.
5. **Mät om.** Tabellen h1–h9 igen, och ett nytt mått bredvid: kroppens storlek och läge i bild mot originalet per segment (promille). h3 ska förklaras: varför är handen i tråget bara halva tiden, och ändrar rättningen det?
6. **Gäller det allmänt?** Kör samma rättning på k2 (Ray 3.2) utan att ändra något. Blir den lika bra som för Dreamina? Och skriv vad som behövs för guacamole S1, där ramen zoomades ut till 62 % och inversen saknas.

## Gränser
- Bara filer under `scen/3d/gennedbrytning/`. Kedjans kod ändras inte; säg vad som borde in i den.
- Ingen ny bild- eller videogenerering. Modal högst 0,50 dollar. Gateway, fal och Codex används inte.
- Inga leder eller vinklar ur andra läsningar än genereringen.
- Egna trösklar är diagnos, inte krav.
- Kommer ägarens svar på `omgang2/` under tiden: rör dem inte i det här uppdraget, de tas i nästa.

## Klart när
- Tabellen över felets delar.
- Rättad rot för Dreamina-kroppen, med projektionsfelet mot originalet före och efter.
- Skeden i handen, avstånd hand till sked per ruta före och efter.
- `s_scen/film2.mp4` och rutbilder, bredvid originalet och med remsan.
- h1–h9 och storleksmåttet.
- Samma rättning på k2, och raderna om guacamole.
- `STRATEGI.md` uppdaterad.
- Bedömning i högst sex rader: är roten löst, och vad är svagaste ledet nu.

## Leveransform
`delegat/svar/0027-kroppens-plats-i-varlden.md` enligt mallen, högst cirka 70 rader.
