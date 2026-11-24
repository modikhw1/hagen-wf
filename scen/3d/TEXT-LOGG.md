# Textlager S4 – arbetslogg

Start: 2026-11-11, Codex. Uppdraget i `CODEX-TEXT.md` är läst i sin helhet. Begränsningarna är noterade: inga modelljobb, inga tröskeländringar eller källfilbyten, obligatorisk förekopia innan kodändring och ny cache/resultatmapp vid verifiering.

## Steg 1 – uppdrag och första orientering

- Bekräftat problem 5 i `GUACAMOLE-LOGG.md`: den öppna guacamole-varianten har flera långa S4-texter samtidigt och utanför bild; filmen utan text är bara referens, inte en lösning.
- Läst textkedjans fyra angivna moduler. Första hypoteser att pröva mot plan och källa: reservtiming i `skarmtext.items`, gruppering i `textenheter.samordna`, villkorad radbrytning i `textmalning.rita` och avsaknad av geometri/tidskorsningsdiagnostik.
- Ingen kod är ändrad och ingen modell eller bakgrundsprocess har startats.

## Steg 2 – orsak och förekopia

- Planen `bildtro_massiv_narvaro/plan.json` har tre S4-enheter. `st6` och `st8` har båda `[190,299)` och samma reservbox `[46,737,484,60]`; `st7` är uppmätt till `[236,286)`.
- Grundorsak i `kontrakt/skarmtext.py`: när en delsträng lokaliserar en lång text men hela texten inte godkänns, blir `incomplete` sann och enheten behandlas som helt antagen. Då ersätts den verkliga delsträngens synlighetsmätning med hela scenintervallet (`intervals=[(0,len(frames))]`). I guacamole gäller det `st6` (delträff 0,380) och `st8` (delträff 0,550).
- Andra orsaken i `kontrakt/textmalning.py`: radbrytning aktiveras bara för ersatt replik eller CM-ursprung. Modelltext i en reservbox ritas därför på en enda rad och kan fortsätta utanför bilden.
- Obligatorisk förekopia skapad i `kontrakt/ut/fore_text_s4/`: `skarmtext.py`, `textmalning.py`, `kompilera.py`, `test_text_disk.py` samt aktuell plan som `plan_fore.json`. Ingen kod var ändrad när kopian togs.

## Steg 3 – kod och smala prov

- `skarmtext.py`: delsträngens teckenmall mäter nu sitt eget källintervall även när hela textens placering är osäker; hel scen används endast om inte heller delsträngen ger ett intervall. Timingens typ sparas i ursprung och mätlogg.
- `textmalning.py`: all text radbryts när dess verkliga teckenbredd passerar boxen. Målningen kläms till 5 % säker bildmarginal och reservtext centreras. En gemensam layoutfunktion ger samma gränser till målning och diagnostik.
- `kompilera.py` + `skarmtext.diagnostik`: planen får `kvalitet.skarmtext` och varningar för text utanför bild samt samtidiga skärmkorsningar utan explicit `samvisning_med`-källstöd. I den slutliga strikta regressionen skrivs diagnosposten bara när ett fel finns; en ren gammal plan förblir identisk.
- `test_text_disk.py`: tre nya prov för delsträngstiming, radbrytning samt kant/ostödd överlappsdiagnos. Smalt test: 15/15 gröna. `py_compile` för de tre kodmodulerna är grön.

## Steg 4 – gruppering, första fulla prov och sista justering (00:05–00:16)

- Den första lokala ombyggnaden av guacamoles källa visade att bevarad delsträngstiming gav `st6` källrutor 205–286 och `st7`/`st8` 236–286. `st7` och `st8` är delar av samma synliga undertextblock, inte två samtidiga block.
- `textenheter.py` lades därför till i förearkivet innan den ändrades. Ny generell blockregel slår ihop fragment med samma scen, källintervall och korsande skärmyta; ett tidigare block klipps vid nästa blocks uppmätta start om samtidigheten saknar källstöd. Självständigt uppmätta samtidiga enheter får i stället explicit `samvisning_med`.
- Efter grupperingen hade S4 två enheter utan tidsöverlapp: `st6` 205–236 och sammanslagen `st7` 236–286. Full diagnostisk kompilering använde den nya cachen `fore_text_s4/cache_guacamole`; `kvalitet.skarmtext` blev `bra`, 0 utanför bild och 0 ostödda överlapp.
- En lokal Blender-rendering med närvaro skapades i `text_s4_narvaro/`, 299 rutor. Jämförelsen granskades vid f210/f230/f245/f270. Huvudfelet var borta: ett centrerat block åt gången och ingen klippning. Två restfel noterades ärligt: de första 15 S4-rutorna saknade `AAAAA!`, och slutblocket blev en rad i stället för källans två.
- Sista ändringarna 00:16: `skarmtext.py` gör reservboxen smalare (72 % av bildbredden) och sparar sökt delsträng/scenstart; `textenheter.py` bevarar ett inledande utrop som eget block fram till den lokaliserade delsträngens start; `test_text_disk.py` provar både blockgruppering/ersättning och detta inledande block. Dessa sista ändringar är ännu inte slutverifierade i denna loggpost.

## Steg 5 – slutverifiering efter 00:16

- `py_compile` är grön och `test_text_disk.py` är 16/16 grön efter de sista ändringarna.
- Källan byggdes lokalt från befintlig giltig semantikcache till `kalla_text_s4_final.json`; inga modelljobb. S4 blev tre sekventiella enheter: `AAAAA!` rutor 190–205, `Jag trodde du var en sådan idiot,` 205–236 och `men nej, den kommer med nachos,` 236–286. Alla är centrerade; de två sista radbryts till två rader.
- Slutlig full kompilering med den helt nya cachen `fore_text_s4/cache_guacamole_slut/` gav `text_s4_slut_data/plan.json`: 8 textenheter totalt, 0 textvarningar. En ren plan får ingen tom diagnospost; syntetiska felprov verifierar att posten och varningarna skrivs vid kant-/överlappsfel.
- Slutlig lokal Blender-rendering med text på och närvaro: `text_s4_slut_narvaro/film.mp4`, 576×1024, 299 rutor, 9,966667 s och ljud. Ny jämförelse: `jamforelse.mp4`, 720×640, 299 rutor, 9,966667 s och ljud.
- Fyra gamla felrutor (195, 215, 245, 270) extraherades ur förefilmen och granskades: alla visar flera samtidiga strängar i samma rad, delvis utanför bild. Samma rutor extraherades ur den nya sida-vid-sida-filmen och granskades mot originalet: ett block åt gången, centrerat, inom bild och de långa blocken på två rader.
- En misstänkt visningsklippning vid sena rutor visade sig vara bildvisarens artefakt. Pixelkontroll mot textlagret gav samma 7 521 textpixlar på samma koordinater i f245/f260/f270/f280; filmens faktiska lager är stabilt.
- Ärlig visuell rest: typsnitt/storlek och exakt radbrytning är nära men inte pixelidentiska med originalet, och semantikens `AAAAA!` har färre A än den synliga källtexten. Textinnehållet kommer från sparad modellsemantik, inte OCR.
- Notan (`kalla_mobelintervall.json`) och gamla vägen (`kalla_jamn_golv.json`) kompilerades slutligt med var sin ny cache (`cache_notan_slut`, `cache_gamla_slut`). Mot de verifierade `bildtro`-baslinjerna: exakt 0 skillnader i vardera full plan. Alla sju textenheter, deras tider, boxar och stilar är därmed exakt lika; gamla vägens skillnader är bindande 0.
- Resterande obligatoriska prov: `test_snabb`, `test_regler`, `test_steg11`, `test_handelser` 60/60 gröna; `test_flode.Flode`, `BarOforandrad`, `Notan` 24/24 gröna. `test_flode.Plats` kördes uttryckligen inte. Tillsammans med textproven: 100/100 gröna.

## Steg 6 – dokumentation och avslut

- En full sektion med orsak (fil:rader), ändringar, S4 före/efter, regression, prov, artefakter, visuell dom och kvarvarande begränsningar är tillagd sist i `GUACAMOLE-LOGG.md`.
- `PIPE.md` är inte ändrad: ingen av dess uttryckligen listade öppna luckor motsvarar problem 5.

## Steg 7 – strikt nollskillnad och slutartefakter

- Den rena diagnosposten togs bort ur rena planer; `kvalitet.skarmtext` och planvarningar skrivs nu endast när diagnostiken faktiskt hittar kant- eller överlappsfel. Det syntetiska felprovet är fortsatt grönt.
- Efter denna sista kodändring: `test_text_disk` 16/16, övriga fyra moduler 60/60 och `test_flode` utan `Plats` 24/24; totalt 100/100.
- Notan och `kalla_jamn_golv.json` omkompilerades med nya slutcacher och jämfördes rekursivt mot respektive `bildtro`-baslinje: exakt 0 skillnader i båda fulla planer.
- Guacamole kompilerades och renderades på nytt efter sista kodändringen. Gällande slutartefakter är `text_s4_slut_data/` och `text_s4_slut_narvaro/`; tidigare `text_s4_final_*` är mellanresultat.
