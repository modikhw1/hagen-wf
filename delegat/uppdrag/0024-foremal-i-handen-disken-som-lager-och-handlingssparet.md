---
id: 0024
titel: Skeden stannar i handen, disken blir eget lager, och tagningen får ett handlingsspår
status: redo
från: orkestratorn (Fable), efter ägarens resonemang 13 nov 01:20
datum: 2026-11-13
följer: 0023
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Punkt 1 gäller **genast**, också mitt i 0023: den ändrar prompten där. Resten görs efter 0023.

## Mål
För gelato S1 finns, utöver kroppen, det som ger rörelsen mening: föremålet hon håller är med i genereringen, disken finns som eget lager i relation till henne, och tagningen har ett handlingsspår som säger vad hon gör, med vad, mot vad, under vilka rutor och med vilken kamerarörelse.

## Bakgrund
Ägarens resonemang:
- **Promptning och rätt bildmodell avgör.** Ju tätare och effektivare prompten är, desto närmare exakt det vi vill ha kan videomodellen styras.
- **Disken skymmer henne, men den håller också platsen och samspelar med hennes kropp.** Hur rummet ligger i relation till henne är ett samspel med eget värde: det visar när och hur kroppen förhåller sig till disken. I dag görs en scen utan kvinnan. Vad händer med rummet utan disk, eller med bara disken? Det finns många sätt att bygga ut en scen för det förvärlden behöver.
- **SAM 3D Body är ett tidigare val och ett redskap**, använt på ett sätt det inte är gjort för (video). Tanken var hela tiden att skapa rörelsen, sätta den i en 3D-värld med sammanhang, och samla allt i en form där sammanhanget får mening: en person gör en handling över ett antal rutor, med en kamerarörelse. En scen, flera scener eller en kombination bär meningen.
- **En perfekt rörelse är bara halva jobbet.** Efter den måste rörelsen ges mening för de anpassningar som kommer senare: scenen, hennes rörelser i den, vad hon gör, hur hon rör armen. Ägarens känsla är att 3D-modelleringen hittills inte riktigt förstår vad den gör eller varför.
- **Skeden med glass** ska sitta i hennes hand. Det mest logiska, fast det går emot isoleringstanken, är att baka in föremålet i handen i genereringen. Tidigt eller sent, men det är en del av kedjan.

Belägg för känslan finns i `delegat/svar/0014-b-tilltal-i-forvarlden.md`: av tio CM-meningar stannade ingen på geometri. Alla stannade på att tillståndet saknade begrepp. Planen vet var saker är, inte vad som händer.

## Att göra
1. **Skeden stannar i handen (gäller 0023 nu).** Stryk "tomma händer" ur alla prompter. Lager 2 är kvinnan **med det hon håller**: glasskeden, och smakprovet när hon räcker fram det. Kundens hand och disken ska fortfarande bort. Startbild och nyckelbilder ska ha skeden där originalrutan har den (ruta 0: handen nere i disken). Säg det i prompten i klartext och i ordning: hon håller en liten sked, för ned den, lyfter upp ett smakprov, räcker fram det. Mät efteråt: syns föremålet i handen i de rutor där originalet har det, och stör det kroppsläsarens hand (jämför handledens och fingrarnas läsning med och utan).
2. **Disken som eget lager, och rummet utan den.** Med bildmodell (fal, eller förbered indata åt ägarens GPT i `luma-agaren/gpt/NASTA-BILDER.md`), negativt formulerat och i ny kontext per bild:
   - **bara disken**: originalet minus kvinnan minus rummet. Indata: tom scen, eventuellt plus originalet.
   - **rummet utan disk**: tom scen minus disken, golvet och bakre bänken synliga där disken stod.
   Mät mot originalet: ligger diskens synliga kanter kvar på sin plats (segmenteraren, promille)? Vad blir känt som inte var det: diskens framsida och höjd från golvet, golvytan, avståndet från disken till bakre bänken. Märk det påhittade `antagen`.
3. **Samspelet kropp och disk.** Ur lagren och läsningen, per ruta: var är höften i förhållande till diskens bakkant, när är handen innanför diskens yta (i tråget), när är den över diskens ovankant (räcker fram). Kontakt- och korsningspunkterna är mätningar av rummet: handens lägsta punkt ger trågets djup, höftens läge ger hur nära disken hon står, armens längsta punkt ger hur långt disken är djup. Jämför med diskens mått och läge i dagens plan. Säg vad som stämmer och vad kroppen rättar.
4. **Handlingsspåret.** En fil per tagning, `handling.json`, som säger vad som händer i ord förvärlden och Jev kan använda. Förslag på form, ändra om något bättre visar sig:
   - segment med rutintervall, i ordning, utan luckor
   - per segment: vem, **handling** (verb), kroppsdel, **föremål** (id ur planen), **mål** (möbel, person eller kamera), **kontakt** (vad rör vad), hållning, och **kameran** (stilla, zoomar in, tippar ned, följer)
   - var uppgiften kommer ifrån: `matt` (ur läsningen), `last` (ur en modell som såg klippet) eller `antagen`
   Bygg den ur det som redan finns, i den här ordningen: handledens vändpunkter (`nyckel/handledsbana.json`), kamerans skala och förskjutning per ruta (`kamerafri/avbildning.json`), samspelet ur punkt 3, handföremålet ur planen (`plan.handforemal`), och sist en videoläsning med Gemini genom gatewayen som får segmentgränserna givna och bara ska namnge handlingarna (se `scen/3d/ingest/rum_video.py` för hur anropen görs; ingestens fakta ges som givna, modellen föreslår semantiken). Gränserna ska komma ur mätning, namnen ur modellen.
5. **Bär spåret något?** Skriv fem meningar en CM kunde säga om just den här tagningen och som rör handlingen, inte geometrin (till exempel "låt henne räcka fram två smakprov", "hoppa över när hon skopar", "låt kunden ta emot med andra handen", "gör skopandet långsammare", "byt glassen mot en kaka"). För var och en: vilket segment och vilket fält i `handling.json` pekar meningen på, och vad saknas i spåret för att den ska gå att utföra. Kör inget genom Jev; detta är en läsning av formatet.

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/`. Kedjans kod, `forvarld/` och källans schema ändras inte. Hur `handling.json` ska in i källan och tillståndet blir ett eget uppdrag när formen har visat sig bära.
- **Ingen sammansättning av kroppar** (se 0023).
- Fal: bilder ur det som är kvar av saldot, video bara inom 0023. Gateway: högst 0,30 dollar. Codex: inga körningar.
- Prompter på engelska, sparade bredvid sina resultat.
- Egna trösklar är diagnos och inte krav.
- Handlingsspårets ordförråd ska vara litet och allmänt (räcka, ta, hålla, luta sig, vända sig, gå, peka, titta), inte skrivet för glass. Det ska gå att använda på nästa klipp.

## Klart när
- En generering i 0023 med skeden i handen, mätt enligt punkt 1.
- Bilderna "bara disken" och "rummet utan disk" bredvid originalet och tom scen, med måtten, eller färdiga indata åt ägaren.
- Tabell för samspelet: tre mått ur kroppen mot dagens plan.
- `handling.json` för gelato S1, och en bild eller film där segmenten ligger som textremsa under originalet så att ägaren kan se om indelningen stämmer.
- De fem meningarna mot spåret.
- `STRATEGI.md`: lagren utökade (disk för sig, rum utan disk, föremål i handen hör till lager 2), samspelet som mätning, och handlingsspåret som det som ger rörelsen mening.
- Bedömning i högst sex rader: vad i handlingsspåret går att få ur mätning utan modell, vad kräver en modell som ser klippet, och vad bör provas på nästa tagning.

## Leveransform
`delegat/svar/0024-foremal-i-handen-disken-som-lager-och-handlingssparet.md` enligt mallen, högst cirka 80 rader.
