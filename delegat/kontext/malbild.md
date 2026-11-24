# Målbild: vad allt arbete i `scen/` är till för

Fast bakgrund för uppdragstagaren. Skriven av orkestratorn 2026-11-13 på ägarens begäran ("passera in det som är relevant"). Läs den före varje uppdrag som rör `scen/3d/` eller `forvarld/`. Det som är orkestratorns tolkning och inte ägarens ord är märkt så.

## Vart det ska

- **Förvärlden** är produkten. Den är en lättviktig 3D-lekplats i 9:16 per klipp, nära originalet (bakgrund, kropp, föremål, kamera, kamerarörelse), som en CM ändrar med ord: "gör klippet längre", "låt henne le efter att hon fått maten", "byt bakgrunden till en foodtruck". Rendering är förvärldens utgång, inte tvärtom.
- **Ingesten** bryter ned ett TikTok-klipp till en orörd mall i förvärlden. Minuter per tagning är i sin ordning där. "Allt arbete nu är till för att effektivt få ner koncept till mallar i förvärlden, och sedan träna förvärlden."
- **Många klipp, inte ett.** Gelato, guacamole, b-tilltal och sketcherna är provkroppar. Varje steg ska gå att köra på nästa klipp utan att skrivas om. En lösning som bara fungerar för glassdisken är ett prov, inte ett steg.

## Mening före geometri

- **Rörelse är halva jobbet.** En perfekt kropp i 3D är bara värd något om den går att ändra med ord. Scenen ska bära mening: en person gör en handling över ett antal rutor, med en kamerarörelse. Belägg: i svar 0014 stannade ingen av tio CM-meningar på geometri, alla stannade på begrepp som saknades.
- **Det som bär idén ska finnas, resten får vara enkelt.** Förvärlden återger inte alla detaljer. Den återger det som gör att klippets mening och syfte lyser igenom. Vad det är beror på konceptet: visas maten, är maten relevant; visas bakgrunden, är bakgrunden relevant. Den bedömningen måste göras någonstans vid ingest, och i dag görs den ingenstans uttryckligt.
- **Kropp och möbel samspelar.** Disken skymmer henne, men den håller också platsen och visar hur kroppen förhåller sig till rummet. Samspelet har eget värde.
- **Föremål i handen hör till personen** och bakas in i genereringen av henne.
- Väg varje uppdrag mot frågan: ger detta mening åt en ändring senare?

## Den generativa nedbrytningen

- **Bildmodellen gör antagandet en gång, vid ingest.** GPT Image tar fram nyckelbilder (personen isolerad, det skymda kompletterat efter bästa antagande), en videomodell (Ray 3.2 eller annan) animerar mellan dem med originalet som styrning, och resultatet läses och ställs på sin plats i förvärlden. Se `scen/3d/gennedbrytning/STRATEGI.md` och `CODEX-BILD.md`.
- **En generering, ingen sammansättning.** Kroppen läses ur en enda genererad video. Brister rättas med bättre källa, nyckelbilder eller prompt, aldrig genom att blanda läsningar eller klippa ihop delar i efterhand.
- **Originalet är sanning där något syns, det genererade är hypotes.** Märk det påhittade `antagen`.
- **Negativ strategi, ny kontext.** Formulera bildsteg som borttagning ur originalet, en ny session per bild.
- **Trogen före stiliserad.** Stilisering är ett slutval. Mellanleden ska vara realistiska.
- **SAM 3D Body är ett redskap**, använt utanför sitt syfte. Det är inte målet och får bytas.

## Kända svårigheter som ska bäras, inte lösas nu

- **Utanför bild.** Det finns inget logiskt sätt att veta vad som ligger utanför rutan. Antagandet är att det går att fylla i (bildmodellen kan bygga ut scenen), och att en person eller ett viktigt föremål finns kvar i 3D-scenen när kameran fladdrar bort. Hur varje scen fylls ut är inte högsta prioritet.
- **Redigering.** Blixtrörelser, kamerasvep som byter vinkel helt (från taket ned till ett ansikte, som krok), och klipp på 0,1–0,5 s inom samma scen. De stör läsningen och ska kännas igen och bokföras, inte misstas för rörelse i scenen.

## Arbetssätt som följer av detta

- Egna trösklar och mått är diagnos, inte ägarens krav.
- Parallella körningar går före väggtid: en container eller session per jobb.
- Byt inte filer under en körning. Verifiera med tom cache.
- Prompter till modeller skrivs på engelska och sparas bredvid resultatet.
