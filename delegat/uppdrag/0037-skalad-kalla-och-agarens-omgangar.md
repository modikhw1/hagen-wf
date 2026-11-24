---
id: 0037
titel: Skalad källa genom hela kedjan, och ägarens Dreamina-omgångar in så fort de finns
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0035
tillåten_skrivning: [scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

**Kör efter 0038.** Läs `delegat/kontext/vagen.md` först.

## Varför
0035 landade i att det som skiljer oss från 1:1 är tiden och huvudet, inte kroppens form, och att huvudrum i källan (källan skalad, grå yta ovanför) är receptet. Samma mekanism behövs för guacamole (utzoomad till 62 %). Men `g_forvarld` saknar inversen för en skalad källa, så ingen av dem kan gå genom kedjan i dag. Det betyder att ägarens nästa manuella omgångar skulle fastna. Återskapningen är också grunden för rörelsebanken (0036): varje klipp som går rent genom kedjan är ett klipp till i banken.

## Mål
En skalad eller utzoomad källa går genom hela kedjan med rätt kropp i rätt värld, och ägarens svar i `omgang2/`, `omgang3_huvudrum/` och `guacamole-S1/` läses in automatiskt med ett kommando var.

## Att göra
1. **Inversen.** Kedjans avbildning ska bära källans skalning (och förskjutning) som en del av avbildningen, så att `g_forvarld`, roträttningen och kameran tar hänsyn till den. Allmänt, inte två specialfall.
2. **Prov utan ny generering:** skala den befintliga Dreamina-läsningen syntetiskt (som om källan hade varit skalad 0,82), kör kedjan, och visa att roten, kameran och h1–h9 blir samma som utan skalning, inom mätfelet.
3. **Säte som ankare** för sittande personer (guacamole), som 0027 pekade ut: där liggaren eller handlingsspåret säger `sitta`, hålls sätet stilla i stället för fötterna.
4. **Ägarens svar.** Finns filer i någon `svar/`-mapp: kör kedjan, mät med de fem måtten ur 0035, och lägg till en kolumn i `ATERSKAPNING.md`. Finns inga: skriv kommandona överst i `ATERSKAPNING.md` så att ägaren eller nästa uppdrag kör dem direkt.
5. **Cachen** (0032): en ändrad konfig ska bara ogiltigförklara de steg vars fält ändrades.

## Gränser
- Ingen ny generering. Modal bara för läsning av ägarens svar, högst 1,00 dollar.
- Före-kopior av ändrad kod. Rör inte `app/`, `video/`, `scen/3d/kontrakt/`.

## Klart när
- Den skalade provkörningen med jämförelsen.
- Säte som ankare, prövat på guacamole S1 med den läsning som finns.
- Ägarens svar inlästa, eller kommandona överst i `ATERSKAPNING.md`.
- Cachen per steg.

## Leveransform
`delegat/svar/0037-skalad-kalla-och-agarens-omgangar.md`, högst cirka 50 rader.
