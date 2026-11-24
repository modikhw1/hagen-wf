---
id: 0012
titel: Placering som bilden faktiskt bestämmer: beskurna kanter som olikheter, och ett läge per kameragrupp
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0010
tillåten_skrivning: [scen/3d/kontrakt/boxpassning.py, scen/3d/kontrakt/mobellyft.py, scen/3d/kontrakt/foremallyft.py, scen/3d/kontrakt/test_snabb.py, scen/3d/ingest/rum_rutor.py, scen/3d/ingest/modal_segmentera.py, scen/3d/ingest/test_rum.py, scen/3d/kontrakt/ut/fore_sidled_0012/, scen/3d/kontrakt/ut/, scen/3d/ingest/ut/, scen/3d/kontrakt/ut/foremal_logg/LOGG.md, scen/3d/NASTA.md]
---

## Mål
I varje tagning ligger disk och våg där originalet har dem, också i sidled, och passningen hittar inte på ett läge som bilden inte bestämmer.

## Bakgrund
`delegat/svar/0010-matt-ram-in-i-kedjan.md`: rutorna är nu rätt, men `disk_C` hamnar på x ≈ 3,09 (bortom sidoväggen, referens cirka 2,2) eftersom en enda vänsterkant i S10 styr x, och vågen står i s11 som ett block över personens högra sida fast originalet har den nere till vänster.

Två principer som ska in. De kommer ur kvällens prov (`svar/0002`, `0006`, `0011`):
- **Avstånd mellan uppställningar går inte att mäta i den här klipptypen.** Kameror i olika grupper är inte överens om rummet, och ska inte tvingas till ett gemensamt läge för något som bara syns i den ena. Kameror i samma mätta grupp (`ingest/rum_grupper.py`) delar däremot plats.
- **Trohet mot originalet per tagning går före ett gemensamt läge.** Tagningarna är ihopklippta och ses aldrig samtidigt.

## Att göra
1. **Beskuren kant är en olikhet.** En ruta som når bildkanten säger "kanten ligger här eller längre ut", inte ingenting och inte "här". Passningen ska straffa lägen där en beskuren kant projiceras innanför bilden, och inte annars.
2. **Underbestämd riktning får ett uttalat förval.** När x (eller y) bara stöds av olikheter eller av en enda kant: använd deklarationens läge relativt personplatsen (disken framför platsen, centrerad om inget annat sägs) som svagt förval, och märk koordinaten `antagen` i `kvalitet`. Möbeln får inte hamna utanför rummets väggar.
3. **Ett läge per kameragrupp.** Passa möbler och föremål gemensamt bara över tagningar i samma mätta grupp. Tagningar utan grupp passas var för sig. Planen har redan en post per synlighetsintervall för samma id (se `svar/0009`, punkt 4); använd den mekanismen så att varje tagning renderar sitt eget läge. Lägena ska ligga inom deklarationens intervall för möbeln, så att mått och höjd fortfarande är ett värde per klipp.
4. **Föremål på möbel placeras ur masken.** Använd maskens tyngdpunkt (finns i segmenterarens utdata) i stället för rutans bottenmitt, och skär strålen med stödets ovansida i samma tagning. Föremålets mått i sidled tas ur maskens bredd på det djupet, inom deklarerat intervall, så att vågen inte blir ett block större än originalet.
5. **Segmenterarens spridning.** S8-rutan för `disk_C` blev [712,…] i ett prov och [603,…] i nästa. Ta reda på varför (bildurval, tröskel, ordning mellan träffar) och gör utdata reproducerbar, eller redovisa spridningen per ruta så att passningen kan vikta efter den.

## Gränser
- Bara filerna i `tillåten_skrivning`. Baslinje först till `kontrakt/ut/fore_sidled_0012/kod/`. I `ut/` skrivs bara nya varianter.
- Modal för segmentering är förhandsgodkänt, tak 0,50 dollar. Inga Gemini-anrop.
- Ändra inget medan test, kompilering eller rendering kör. Tom cache vid verifiering.
- Notans och guacamoles befintliga planer utan möbelrutor ska vara oförändrade. Visa det.
- Egna trösklar är diagnos. Redovisa dem.

## Klart när
- Tester gröna med antal, och nya prov för punkterna 1–4.
- b-tilltal, ny variant `n06-grupp`, `prepare` och `render`. Per tagning S6–S11: diskens övre kant och vågens ruta projicerade i slutkameran mot segmenterarens ruta i nyckelbilden, alla fyra kanter i promille. Bredvid samma tal för `n06-matt`.
- Ingen möbel utanför väggarna, ingen kamera i en möbel.
- I `blad/s11.png` står vågen på samma sida och i ungefär samma storlek som i originalet. Titta på bilden och beskriv vad som syns, också det som fortfarande är fel.
- Guacamole, variant `grupp`: går igenom, och jämförelsefilm mot originalet finns.
- `LOGG.md` och ett kort tillägg överst i `NASTA.md`.

## Leveransform
`delegat/svar/0012-sidled-och-placering-per-kameragrupp.md` enligt mallen, högst cirka 70 rader, med sökvägar till filmerna.
