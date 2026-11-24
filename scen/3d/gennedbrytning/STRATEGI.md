# Generativ nedbrytning vid ingest: strategin

Ägarens upplägg, 12 nov 2026 kväll. Gäller ingesten, alltså när ett klipp bryts ned till en orörd mall i förvärlden. Minuter per tagning är i sin ordning där.

## Problemet

Kedjan har ingen hjärna. Kroppsläsaren (SAM 3D Body) läser en bildruta i taget, kameran skakar, och det som ligger bakom en disk, bakom ett föremål eller utanför bild måste antas. Resultatet i förvärlden vobblar, vrider sig upp till 90° över enstaka rutor och är svårt att arbeta runt.

## Steg 0: relevanslistan (0025, 13 nov)

Innan något bryts ned avgörs **vad** som ska med (`relevans/relevans_steg.py`, `relevans/RELEVANS.md`). En modell ser tagningarnas kontaktblad och får underlaget som givna fakta: innehållsbedömningen, sållningen och planens id. Ut kommer klippets mening och en post per sak, med `typ`, `roll` (bar, ramar eller brus) och `behandling` (eget lager, förenklad form, bakas in i personen, utelämnas).
- Lagren nedan görs bara för poster med `bar` och `ramar`.
- **Deklarationens relevansfält ska inte vara indata.** Där ärver listan deklarationens fel: mobilen blev "meny".
- **Kör tre gånger och slå ihop.** Id-namn och posternas indelning skiftar mellan körningar.
- **Det formen saknar:** relationer ("hon bakom disken"), blick ("tittar på mobilen") och kroppsdelar utan egen person (kundens hand). Ägaren nämner alla tre.

## Idén

En generativ modell gör antagandet en gång, vid ingest. Tagningen delas i lager, och kedjan läser varje lager för sig:

| Lager | Innehåll | Används till |
|---|---|---|
| 0. Original | tagningen som den är | sanningen, där något syns |
| 1. Tom scen | originalet utan personen | rum, möbler, föremål, kamera |
| 2. Isolerad person **med det hon håller** | personen, hela kroppen kompletterad, med föremålet i handen (skeden, smakprovet), samma rörelse utan förgrund | kroppsläsningen; föremålet i handen bakas in här (0024) |
| 3. Bara disken | möbeln som samspelar med henne, utan rum och utan henne (0024) | möbelns läge, kanter och höjd; samspelet |
| 4. Rummet utan disk | tom scen minus disken: golvet och bakre bänken där disken stod (0024) | golvyta, avstånd disk–bänk; byte av möbel |

Kroppen läses ur lager 2 med samma läsare som i dag. Rum och föremål kommer ur lager 1 och 3 med de metoder som redan finns (segmenterare, kameragrupper, handfäste).

## Principerna

1. **Negativ strategi: ta bort, skapa inte.** Varje steg formuleras som en borttagning ur originalet. "Ta bort kvinnan" håller layouten. "Gör en bild av kvinnan" ger ett nytt foto. Prövat 12 nov: två försök med "gör en helkroppsbild" ställde upp henne mitt i bild med ändrad pose, trots uttryckligt förbud (`luma-agaren/steg1/`).
2. **Skillnaden är masken.** Original och tom scen är samma bild från samma kamera, och det enda som skiljer är personen. Lager 2 beställs som "utgå från originalet, allt som också finns i den tomma scenen ska bort". Disken finns i båda, alltså försvinner den, och då måste det dolda kompletteras.
3. **Lås positionen.** Personen ligger kvar på samma plats, i samma storlek och samma pose som i originalrutan. Video-till-video för över rörelse pixel mot pixel på plats; en omställd guidebild ger ett hopp i första rutan och inget för rörelsen att fästa vid.
4. **Bilden bestämmer vad, originalvideon bestämmer hur.** En redigerad första ruta låses vid ruta 0 och säger vad som ska synas. Originalvideon styr rörelsen med starkast följsamhet. (Receptet ur ägarens Luma-klipp: Ray3.2 Modify Video, städad första ruta låst vid 0, rörelse 9 av 9, struktur 9 av 9, poselås.)
5. **Nyckelbilder håller handen.** Fler låsta rutor längs tagningen (till exempel var tionde) binder antagandet vid det som hände. Korta handhållna steg hallucinerar mindre än tio fria sekunder.
6. **Originalet avgör där det syns.** Det genererade är hypotes (`../PIPE.md`, Grundregeln). Synliga leder mäts i originalets rutor. Jämnhet utan trohet är inget bevis.
7. **Mask hellre än prompt, när stacken tillåter.** Personens pixlar skyddas med mask och ritas aldrig om; bara det som saknas genereras. Wan VACE gjorde det i `../lasformat/RAPPORT.md`: dolda ben läsbara i 85 av 85 rutor, cirka 3 px drift, 0,26 dollar.
8. **Kontrollen är enkel och snabb.** Blev armen tre gånger längre, bytte personen form, kom det ett klipp mitt i. GEM-X behövs bara om enklare mått inte räcker, och kan bli onödig med rätt modell och prompt.

## Efterbehandling: lås positionen (0018, 13 nov)

Princip 3 hålls i efterhand, oavsett vad bildmodellen gjorde. `passa.py` passar den isolerade personen likformigt (skala, förskjutning, rotation) mot originalets synliga överkropp, med ORB-träffar inom ingestens mask, och lägger resultatet på grå duk i originalets format. Steget körs alltid.

## Kamerafri och förgrundsfri källa före genereringen (0021, 13 nov)

Före videosteget görs källan om (`e_kamerafri.py`):
1. En likformig avbildning per ruta lägger överkroppen där den är i ruta 0. Den skattas ur dagens 2D-leder och jämnas över tiden (`kamerafri/avbildning.json`, med invers).
2. Bara hennes pixlar ur personmasken läggs på grå duk. Maskdelar som kommer in från bildkanten tas bort, eftersom det är kundens hand.

Läsningen ur den genererade videon förs tillbaka till originalets kamera genom inversen (roten: Z' = sZ, X' = X + Z(c - t - sc)/f) innan den blir en sekvens (`g_forvarld.py --kamerafri`).

## En generering är enda källan för kroppen (0023, 13 nov)

Kroppen i förvärlden läses ur **en** genererad video. Överkropp och ben tas inte ur olika läsningar, och delar klipps inte ihop i efterhand. Brister rättas med bättre källa, nyckelbilder eller prompt.

- **Källan (k2, `e2_k2.py`):** kamerafri, men med originalets pixlar kvar (disk, glas, rum, armen bakom glaset). Bara kundens hand målas grå. Det är detta som binder överkroppen. Med bara personmasken (k) saknades armen bakom glaset, och modellen hittade på en svart form och tappade lutningen.
- **Prompten (`d2_video.py`, `P_ANTAGEN`):** säger vad som ska bort, säger antagandet (fötterna stilla, benen raka, böjer i höften, tomma händer, stilla kamera) och beskriver rörelsen i tid.
- **Nyckelbilderna:** Codex-isoleringarna i `nyckel2/` förs in i den kamerafria ramen (passning följd av rutans avbildning) i `kamerafri_k2/nyckel/`. Ruta 55 hamnar för liten, med fötterna 400 px högre än i ruta 0. Fotlinjen varierar mellan 1277 och 1820 px, eftersom avbildningen bara passar överkroppen. Inte körda än (fal-saldot tog slut).
- **Kontrollen (`h_kontroll.py`):** ja eller nej per generering, med skäl. Lutningens korrelation mot dagens läsning är måttet på det som k tappade. Trösklarna ligger i `kontroll_gransar.json` och är diagnos.

## Tidspassning: genereringen på källans rutor (0026, 13 nov)

En videomodell håller inte källans längd: Dreamina ger 5, 8 eller 10 s. `t_tid.py` lägger en generering av godtycklig längd på källans rutor.
- **Metod:** monoton dynamisk tidspassning över kamera-oberoende drag, alltså bålens lutning, handledernas läge i bållängder och armbågens vinkel, mot dagens läsning av originalet.
- **Steglängd:** minst ett och högst tre genereringsrutor per källruta. Med noll steg frös kroppen i platåer på 30 rutor.
- **Slut:** fritt, så att genereringens överskott på slutet kapas.
- **Utfall för Dreamina (193 rutor):** följer originalet bättre än linjär omskalning.
  - lutningens korrelation 0,88 mot 0,81
  - handen lägst på källruta 58 mot 55 (linjärt 49)
  - armen halvvägs fram på källruta 90 mot 90 (linjärt 95)
- **Ut:** `d_video/<v>/tid.json` och `d_video/<v>_t/`, med 148 rutor som kedjan tar emot som vanligt.

## Roträttning: fötterna står still, kameran tar inåkningen (0027, 13 nov)

Eget steg efter tidspassningen och läsningen, före scenen. `r_rot.py`.
- **Felet:** planens kamera stod still med fast lins, så originalets inåkning (avbildningens skala 1,0 → 0,53) togs upp av att kroppen åkte mot kameran. Fötterna gled 1,8 m.
- **Rättningen:** kroppen flyttas som helhet per ruta så att fotledernas mitt står still i världen (bara förskjutning, leder och vinklar orörda). Glidningen blev 0,10 m.
- **Allmänt:** gäller varje generering med hela kroppen i bild. Sitter personen, låses sätet i stället för fötterna. k2 (fötterna bleknar) blev inte bättre: steget kräver att ankaret syns.

## Kameran: en jämn inåkning, löst över hela tagningen (0028, 13 nov)

`r_kamera.py`. Ersätter 0027:s kamera, som löstes fritt per ruta och sedan jämnades ut (väg 8,8 m, linsen 43–140 mm).
- **Låst:** kamerans höjd (1,30 m), en rak bana i golvplanet, linsen i början (64 mm, ingestens antagande som kroppen lästes med), och alla förlopp som jämna kurvor genom nio knutar.
- **Fritt:** åkningen längs banan och zoomen (samma förlopp, `dolly_zoom`), och en liten, jämn rättning av tippning och panorering (högst 13° och 8°).
- **Varför:** dolly och zoom går nästan inte att skilja åt per ruta. Fri lösning byter den ena mot den andra, och kameran skakar. Med fri tippning men utan gräns backade kameran ut ur rummet med 280 mm tele. Därför finns rummets gräns: kameran står på kundens sida, högst 0,8 m från disken.
- **Utfall:** väg 0,73 m, största ryck 2 mm per ruta² (mot 124), zoom 48–126 mm, projektionsfel 20,7 promille (0027: 20,9).
- **Tippningen bekräftas av originalet:** lösningen tippar ned till 30° i ruta 39–50, utan att ha fått veta det. Ingestens vertikalmätning såg 34,5° i ruta 39 men avvisade värdet som avvikande.
- **Prövat och förkastat:**
  - originalets COLMAP-bana (rotationerna avviker 5–23° från vertikalerna, felet blev 70 promille)
  - ren dolly (90 promille)
  - höjden fri (lösningen säger inget om höjden: 1,13–1,80 m ger samma fel)
  - höjden höjd i h3 (fel 23,5, ingen synlighet vunnen)

**Synligheten är geometrin, inte kameran.** Med originalets mätta tippning skymdes handen ändå helt av montern i 0027 (`r_synlig_blender.py`: 0 % i ruta 45–70). Handen går 0,6 m under diskens ovankant. Två antaganden i scenen, båda trogna originalet, gör den synlig (`s_scen.py`):
- **`--glas`:** montrens front blir glas, som i originalet (`s_glas_blender.py`).
- **`--bak-lag`:** kanten på hennes sida sänks under underarmen där den passerar. Montern är öppen mot personalen.

`--trag-max` låter tråget bli så djupt som handen når. Annars ligger fingrarna inne i diskens bas. Utfall: hand 100 %, underarm 100 %, tråg 95 %.

## Recept för återskapning 1:1 (0035, 13 nov)

Generativ video används bara för att återskapa originalet (se `ATERSKAPNING.md`).
1. **Källan:** kamerafri, med originalets pixlar (k2), med huvudrum. Skala den så att originalets överkant aldrig skär huvudet, med fötterna fasta (gelato: 0,82), och ta med skalningen i avbildningen.
2. **Generatorn:** Ray 3.2 med nyckelbilder på tid när saldo finns (exakt tid). Annars Dreamina med universell referens, följt av tidspassning (`t_tid.py`).
3. **Prompten:** borttagning ur originalet. Samma rörelse och tid, huvudet alltid synligt, låst kamera. En generering per tagning, ingen sammansättning.
4. **Kontrollen efteråt:**
   - överkropp p90 under cirka 60 promille
   - hela kroppen i alla rutor
   - huvud avskuret 0 rutor
   - fotlinjens glidning under cirka 30 px
   - vändpunkterna inom 3 rutor
   Trösklarna är diagnos. Det som faller körs om med en ändring i taget.
5. **Kedjan:** `kedja.py` med leverantörens paket. Vid NEJ i kontrollen stannar kedjan inte, men kroppen märks.

## Leverantörer för videosteget (0026)

| | Ray 3.2 (fal eller Luma) | Dreamina (Seedance 2.0 Fast) |
|---|---|---|
| Åtkomst | API | bara webbappen, ägaren kör för hand |
| Längd | exakt (5 s) | 5, 8 eller 10 s |
| Rörelsereferens | video-till-video | "Universell referens" tar video och bilder |
| Nyckelbilder | på exakta rutor | bara som referenser, eller i "Flera bildrutor" utan video |
| Utfall för gelato S1 | (a), k, k2 | hela kroppen i 148 av 148 rutor och lutning 82° (närmast originalet); huvudet avskuret i källrutorna 22–69; kameran tippar från 5 s |

Bygg inget som bara fungerar med en av dem. Tidspassningen och den kamerafria källan fungerar för båda.

## Scenen kring kroppen (0026)

`s_scen.py` bygger i en kopia av planen, med kedjans kod oförändrad:
- **Disken** flyttas med tråget som villkor. Det blev 0,33 m mot henne. Färgmaskerna sa +0,57 m (ruta 0) och −0,23 m (ruta 112).
- **Tråget** är en bas plus fyra kanter, 0,35 m djupt ur fingertoppens lägsta punkt.
- **En bakre bänk** läggs mot väggen (antagen).
- **Kunden** är en antagen stand-in vid kameran, med en arm som möter skeden i h8.

`v_mening.py` prövar spåret mot scenen. h1, h2 och h4–h8 är sanna, h3 nästan och h9 falskt.

**Det som bör in i kedjan först:** disken synlig i S1 (i n06-hand syns den bara i S2), och tråget eller öppningen i möbeln.

## Samspelet kropp och möbel är en mätning (0024, 13 nov)

Ur den byggda scenen (`j_samspel_blender.py`) och diskens ram (`j_samspel.py`) räknas per ruta:
- var höften står bakom diskens bakkant
- om fingertoppen är bakom, i tråget, över eller framför disken

Ur det kommer tre mått på rummet, som jämförs med planen:
- tråget, mätt som handens lägsta punkt
- avståndet till disken, mätt från höften
- diskens djup, mätt som hur långt handen når

**Med k2 och fötterna låsta (`--fotter-last`, antagen):**
- **Djupet stämmer:** handen når 0,75 m in över disken mot planens 0,70.
- **Disken står för långt bort:** handen når aldrig ned i tråget. I rutorna 40–70 stannar fingertoppen 0,14 m bakom bakkanten och 0,92 m upp. Staplatsen ligger 0,84 m bakom bakkanten. Kroppen säger alltså att disken bör stå cirka 0,15–0,4 m närmare henne.
- **Utan låsta fötter lyfts höften cirka 0,5 m när hon böjer sig,** både i dagens förvärld och i k2. Rotens placering i världen är svagare än kroppens form.

## Handlingsspåret ger rörelsen mening (0024, 13 nov)

`handling/<tagning>/handling.json` (`l_handling.py`) delar tagningen i segment utan luckor. Varje segment har följande fält:

| Fält | Källa |
|---|---|
| hållning, handens läge mot möbeln, handens rörelse, kundens hand i bild, kameran (zoom och tippning) | mätning (`matt`) |
| handföremål | planen |
| handling (ett verb ur ett litet, allmänt ordförråd), kroppsdel, mål, kontakt och beskrivning | Gemini (`last`) |

- **Gränserna kommer ur mätning, namnen ur modellen.**
- **Modellen ska inte få handläget som fakta** där kroppen står fel i rummet. Då upprepar den mätfelet: "handen står stilla bakom disken" mitt i skopandet.
- Remsan under originalet (`remsa.mp4`) är kontrollen för ögat.

## Arbetsfördelning (0019, 13 nov)

Codex (`codex_bild.py`, ny session per bild) gör stillbilder, fal gör rörelse (`luma/agent/ray/v3.2/video-to-video`, startbild eller upp till 64 nyckelbilder) och originalet styr tiden. I praktiken har bara steg A gått genom Codex hittills, se "Öppet".

## Stegen för en tagning

1. **Tom scen, bild.** Första rutan, personen borttagen (inpainting med ingestens personmask, eller promptad borttagning).
2. **Isolerad person, bild.** Original plus tom scen in. Ut: personen på sin plats mot jämn grå yta, dolda kroppsdelar kompletterade. Reserv: `luma-agaren/bygg_guide.py` bygger en grov komposit med låst position som modellen bara städar.
3. **Isolerad person, video.** Video-till-video på originaltagningen med bilden från steg 2 låst vid ruta 0, eller maskstyrd video där personens pixlar skyddas.
4. **Tom scen och förgrund, video** (valfritt): samma sak för lager 1 och 3.
5. **Läs.** Kroppsläsaren på lager 2. Segmenteraren på lager 1.
6. **Mät mot originalet.** Synliga leder i originalets rutor, vobbel och vridning mot dagens läsning, tidssynk, benlängder.
7. **In i förvärlden.** Tre bredvid varandra: original, dagens förvärld, förvärld med ny kropp.

## Öppet

- **Kameran följer med in i lager 2 (13 nov).** Ray 3.2 med startbild bar med sig källans zoom och tippning. Underkroppen klipps från cirka ruta 80, så "hel kropp hela klippet" kräver att kameran hålls stilla på något annat sätt, till exempel med nyckelbilder i helbild eller utvidgning (`reframe`).
- **Bildmodellerna ritar om det de inte borde (13 nov).** Kundens hand och smakprovet stod kvar i den isolerade videon, trots "hands empty". Steg A i Codex lämnade text, kundens hand och en svävande sked.
- **Steg B i Codex: löst (13 nov).** De första försöken misslyckades för att prompten klipptes vid första radbrytningen, inte för att modellen inte klarade uppgiften. Se `CODEX-BILD.md`. Med hel prompt gav Codex isolerade personer för åtta nyckelrutor.
- **Nära rutor har inte plats för en hel kropp (13 nov).** I rutorna 55, 112 och 146 är kameran så nära att en isolering på låst position inte har utrymme för benen. Nyckelbilder vid sådana rutor kräver en annan ram än källans.

- Kan en video-till-video-modell skilja kroppens rörelse från kamerans, eller följer kameraskaket med in i lager 2?
- Håller tiden? Modellerna har ofta egen bildfrekvens och längd.
- Hur mycket av vobblet sitter i läsaren och står kvar även på en ren bild? I `lasformat/RAPPORT.md` hade det genererade något mer bålskak än originalet.
- Vilken leverantör: fal.ai (nyckel finns), Wan VACE på Modal (körd, Apache-2.0), Luma (begränsat, inte planerbart).

## Prövat hittills

| Datum | Vad | Utfall |
|---|---|---|
| 11 nov | Wan2.1-VACE maskstyrd, notan S4 (`../lasformat/RAPPORT.md`) | ben i 85 av 85 rutor, rörelsen höll, något mer bålskak |
| 11 nov | Luma Reframe, breddning, S4 (`../lasformat/luma-paket/`) | samma nivå som VACE |
| 11 nov | Luma Modify Video, städad första ruta, S1 | gesterna höll över 73 rutor |
| 12 nov | Luma/GPT Image, "gör helkroppsbild" av gelato S1, två försök | omställd, centrerad, fel pose: principerna 1 och 3 |
| 12 nov | Lokal komposit med låst position (`luma-agaren/steg1/guidebild_last_position.png`) | position rätt, grov |
| 12–13 nov | fal: maskad borttagning (`object-removal/mask`) mot promptad (Uni-1), ruta 0 | maskad: 12 % ändrat utanför masken men rörig fyllning; promptad: ren, men 29 % omritat och annan ram |
| 12–13 nov | fal Uni-1: STEP B mot städning av komposit | STEP B ställde om henne (huvudet 476 px bort); städning höll positionen (8 px) |
| 13 nov | `passa.py` på ägarens GPT-isolering | skala 1,09 mot originalet, huvud och axlar inom 15–18 px efter passning |
| 13 nov | Codex, steg A för rutorna 55, 112 och 146 | kvinnan borttagen; text, kundens hand och sked kvar |
| 13 nov | Codex, steg B (fyra varianter, med och utan tredje bild) | ingen isolerad person |
| 13 nov | fal Ray 3.2, startbild = passad GPT-ruta 0, 540p, 0,15 USD | 148 rutor i 29,97 fps (synk 1:1); rörelsen följer; kamerazoomen följer med; kundens hand kvar |
| 13 nov | Läsning ur den isolerade videon mot dagens | bålens största hopp 2,9° (var 7,3°), höften 3,8° (8,9°), roten 4 cm (16,5 cm), 0 rutor över 10 cm (7) |
| 13 nov | (a) in i förvärlden, sekvens via `sekvens_stabil.py` i kopia av planen | står rakt i ruta 10 där dagens sitter på huk; lutningen behålls; benen fel i slutet där de klipptes |
| 13 nov | Kamerafri, förgrundsfri källa och Ray 3.2 (k), 0,15 USD | hela kroppen i 148 av 148 rutor (a: 48), benlängdens spridning 1,8 % (a: 6,6 %), stilla kamera; påhittad svart rund form från cirka ruta 30; lutningen ned i disken försvinner |
| 13 nov | Codex steg A och B med hel prompt (stdin), rutorna 0–146 (`nyckel2/`) | alla åtta isolerade, position inom 1–36 px utom ruta 55; proportioner lika i 80–146; ruta 30 har för långa ben; byxorna glider |
| 13 nov | k2: kamerafri källa med originalets pixlar, startbild, prompt med antagandet och tider, 0,15 USD | lutningen följer (korrelation 0,98, största 61° mot dagens 85°; k: 0,40 och 27°); hela kroppen bara i 124 av 148 rutor, fötterna bleknar i nederkanten från cirka ruta 40; benlängdens spridning 4,6 %; i slutet handflatan mot kameran i stället för att räcka fram; kontroll: nej |
| 13 nov | k2n: som k2 med nyckelbilder vid 0, 55, 94, 136 | inte körd: fal-saldot slut ("Exhausted balance") efter 0,465 USD totalt; ersatt av k2s/k2sn (0024: skeden i handen) |
| 13 nov | Samspel kropp–disk ur k2 med fötterna låsta | djupet 0,75 m mot planens 0,70; handen når inte tråget, disken står cirka 0,15–0,4 m för långt bort |
| 13 nov | Dreamina Seedance 2.0 Fast, Universell referens, k2-källan + fyra nyckelbilder + P_FOREMAL, 8 s (ägaren för hand) | hela kroppen 148/148 efter tidspassning; lutning 82° i 40–70 (dagens 85°), korrelation 0,88; benlängdens spridning 3,3 %; roten hoppar 13 cm en gång; huvudet avskuret i 48 genereringsrutor (källruta 22–69); kameran tippar från 5 s (fotlinjen 230 px upp); kontroll: nej på ben, rot och p90 |
| 13 nov | Tidspassning DTW mot linjär (193 → 148) | DTW följer bättre; utan minsta steg fryser kroppen i platåer |
| 13 nov | Scen kring Dreamina-kroppen (disk flyttad med tråg, bänk, antagen kund) | h1–h8 sanna utom h3 nästan; skeden hänger en bit från handen (handfästet mätt mot gårdagens kropp) |
| 13 nov | Relevanslistan, Gemini 2.5 Flash, tre körningar per klipp (0,09 USD totalt) | meningen rätt och stabil; disk, bakgrund och sked träffar ägarens läsning; kundens hand saknas i alla tre; mobilen blir "meny" (ur deklarationen) |
| 13 nov | Färgkodning genom Codex, V1–V4 × gelato 0, 55, 112 och guacamole 0 (18 bilder, 46 % av femtimmarsfönstret) | V1 (ton på plats) håller layouten (utanför tonen ändrad 0,3–14 % >40 nivåer) och hittar det lilla i handen (skeden, mobilen) där segmenteraren missar; V3 (ett föremål, kompletterat) håller för glassdisken men ritar om baren helt; V4 (ton på tom scen) ger flytande hyllfragment; segmenteraren bäst när föremålet syns helt (disk 112 IoU 0,95, personer 0,92–0,97) |
| 13 nov | Diskens läge ur färgmask och segmenterare genom mobellyft, i kopia av planen | ruta 112: alla källor lika (0,23–0,26 m bort från henne); ruta 0: färgmaskerna 0,57 m mot henne (samspelet: 0,15–0,4), segmenteraren 1,3 m (fångade bara en del av disken); ruta 55: strålen når inte ytan; en ruta räcker inte |
| 13 nov | Handlingsspår S1, gränser ur mätning, namn ur Gemini 2.5 Flash (0,017 USD för två anrop) | nio segment; utan handläget i prompten namnges skopandet ("ta") och kundens mottagande rätt |
