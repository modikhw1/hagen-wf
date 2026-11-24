# Nästa: överlämning efter natten 11–12 nov 2026 (dagen 12 nov överst)

Läs `PIPE.md` först. Den här noten säger bara var arbetet står och vad som är nästa steg.

## Läge 13 nov natt: rörelsebanken v0 (0036, ändrat av 0038)

- **Banken:** `forvarld/kropp/BANK.md` och `bank/v0/`, med 23 poster och 32 s utan speglingar. Etiketterna är liggarens händelser. Vägen till tusen klipp står i BANK.md.
- **Helspegling och matchning är strukna** (0038). Provet ligger i `forvarld/kropp/forskning/speglad_0036/`.
- **Nästa:** 0038 (rörelsemodell och licensbeslut).

## Läge 13 nov natt: återskapning 1:1 (0035)

- **Måtten** för 1:1, kartan över generatorer och receptet finns: `gennedbrytning/ATERSKAPNING.md` och STRATEGI, "Recept för återskapning 1:1".
- **Huvudet:** originalets kant skär det i k2-källan, och Dreamina ärver det. Paketet med huvudrum ligger i `d_video/dreamina-paket/omgang3_huvudrum/` och väntar på ägaren, liksom omgång 2 och guacamole.
- **Saknas:** inversen för skalade källor i `g_forvarld`.

## Läge 13 nov natt: kroppen som förstår (0033, 0034)

- **Ägarens besked:** generativ video bara för 1:1 vid ingest. Ändringar görs blixtsnabbt i 3D, utan generativ AI.
- **0033:**
  - Kunden är en roll; `fg_kund_hand` har regi (en variant i scenbygget).
  - Alla meningar som Jev kan utföra har bild: `forvarld/gelato/ut_0033/kontaktblad.jpg`.
  - Speglingen (0031) är struken.
- **0034:** karta och gränssnitt finns (`forvarld/kropp/`).
  - **Provet:** optimering över sekvensen når målen inom 1–2 cm, men ser fel ut: bålen vrids 34° och armen korsar kroppen.
  - **Rekommendation:** motion matching mot en egen bank ur kedjans klipp, med liggarens händelser som etiketter, och sedan en kontroller av typen MaskedMimic, tränad på CMU och egna klipp (AMASS är icke-kommersiellt).
- **Nästa:** 0035 (vad löser 1:1).

## Läge 13 nov natt: liggaren på tre klipp (0032)

- **Liggare finns för b-tilltal och guacamole,** utan luckor: `liggare_0032.json` och källorna `kalla_0032.json`.
  - b-tilltal: gissa och väga är händelser, och "Morten före Mads" är en frihetsgrad.
  - guacamole: blicken (`tittar_pa(A,mobil)`) bär meningen.
- **Jev mot ytorna** gav rätt val 5 av 5 gånger, för 10 meningar i b-tilltal och 3 i guacamole.
  - b-tilltal: 7 meningar tillämpas, också m2 som föll i 0030. Tre går till den långsamma vägen med ett nej.
- **Flash blint** fångar gissning och vägning, och mobilen som entitet, men inte att mobilen bär meningen. Kontrollen ger 2 luckor och 11 faktafel (b-tilltal) och 1 lucka och 20 faktafel (guacamole).
- **Svar:** `delegat/svar/0032-liggaren-pa-fler-klipp.md`.
- **Viktigt framåt:** ägarens besked 13 nov (vagen.md) stryker generativ video som utförande. 0034 ändrar 0033, och speglingen ur 0031 ska inte byggas vidare.

## Läge 13 nov natt: liggaren (0031)

- **Gelatos liggare** finns, med kontroll och utan luckor: `kontrakt/ut/kand-kennysgelato_n06-hand/liggare_0031.json`. Källan `kalla_0031.json` pekar på den. Se PIPE, "Liggaren".
- **Jev mot liggarens yta:** 11 av 11 meningar fick rätt ändring, 5 av 5 gånger.
  - Åtta går till kompilerad plan, och tre går till den långsamma vägen med ett skälat nej (mimik, kundens hand, foodtruck).
  - Utan liggare blir det samma fel som i 0029.
- **"Andra handen" på nivå 1:** speglingen går hela vägen till film (`forvarld/gelato/ut_0031/andra_handen.mp4`), men ser fel ut i räcka fram och deformerar axeln. Nivå 3 väntar som Dreamina-paket i `d_video/dreamina-paket/vanster_hand/`.
- **Flash som liggarskrivare** räcker inte utan efterkontroll: regin får fel form, det blir få frihetsgrader och kontrollen hittar luckor.
- **Svar:** `delegat/svar/0031-liggaren.md`. Nästa är 0032 (liggaren på b-tilltal och guacamole).

## Läge 13 nov sen kväll: kedjan och meningen på fler klipp (0030)

- **Kedjan:** den generativa nedbrytningen körs med en rad, `gennedbrytning/kedja.py kedja/<klipp>/<tagning>.json`, med cache per steg (se `gennedbrytning/README.md`). Gelato S1 från tom cache ger samma utfall som 0028, på cirka 20 minuter.
- **Väntar på ägaren:** kedjorna för guacamole S1 och gelatos omgång 2 står och väntar. Guacamole behöver säte som ankare och inversen av utzoomningen innan körningen.
- **Meningen:** handlingsspåret (`m_handling.py`, allmänt) och relevans med handlingsposter finns för b-tilltal och guacamole, och båda ligger i källorna (`kalla_0030.json`). Ordförrådet fick `tala`, `sitta`, `blick` och `i_handen`.
  - Blint missades guacamoles mobil. Med `i_handen` hittades den, men som brus.
  - Kundens hand i gelato saknas fortfarande.
- **Jev:** b-tilltal med mening i tillståndet når inte fler bilder. Jev varierar mellan körningar med samma tillstånd, så prov behöver upprepas.
- **Svar:** `delegat/svar/0030-bredd-kedjan-pa-fler-klipp.md`.

## Läge 13 nov kväll: gelato S1 i slingan (0028, 0029)

Gelatos nya S1 är nu en källa: `kontrakt/ut/kand-kennysgelato_n06-hand/kalla_0029.json`. Den har kroppen ur Dreamina med sitt ursprung, kameran som jämn inåkning (0028), disken med tråg och glasfront, och kunden som platshållare. Handlingsspåret och relevanslistan finns i semantiken. Se PIPE, "Mening, generering och handlingar i källan".
- **Regin:** `ta_bort_handling`, `tempo_handling` och `upprepa_handling`. En varning kommer när en ändring river det som bär meningen.
- **Slingan:** tio gelato-meningar har körts genom Jev med och utan mening i tillståndet (`forvarld/gelato/`).
  - Med spåret gick "hoppa över när hon skopar" och "gör skopandet långsammare" hela vägen till rätt bild.
  - Utan spåret stannade båda.
  - Spåret drog också två meningar fel: kunden med andra handen blev "ta bort h8", och kakan blev "föremålet saknas".
- **Svar:** `delegat/svar/0028-stang-0027-kameran.md` och `0029-gelato-in-i-slingan.md`. Tidslogg: `delegat/svar/tidslogg-0028-0029.log`.
- **Kvar:**
  - Jev väljer segment osäkert (h3 0,53 mot h8 0,35).
  - Upprepning av en följd blev ett segment.
  - Det finns inget begrepp för "innehållet i handen" (glassen på skeden), ingen mimik och inga personer att casta (kunden).
  - Stabilisering ska gälla scenen med inåkningen (s1), inte s2.
- **Nästa:** 0030 (bredd).

## Läge 12 nov natt: föremål och scengrupper i tillståndet (0016)

Det kedjan redan vet står nu i källan: vågen och köttbiten är namngivna props (`deklaration`), och s1+s2, s3+s4 och s5–s11 är scengrupper (`kontrakt/kalla_foremal.py`, b-tilltal `n06-hand/kalla_0016.json`).
- **Regin:** kan ta bort eller byta ett föremål i alla dess former, flytta eller ta bort en grupp, och hålla sista lästa rutan (`hall_sista`). En ogiltig edit kastar bara sig själv.
- **Utfall:** m2, m5, m6 och m9 ur 0014 går hela vägen till bild, och Jevs routning är lika snabb som förut. Se PIPE, "Det kedjan vet förs över till källan".
- **Svar:** `delegat/svar/0016-foremal-och-scengrupper-i-tillstandet.md`.
- **Kvar:** tavlan som datastruktur (m2 visar Mads före Morten), utsnitt per tagning (m4), ankare som roller (m8), personer att casta (m7) och rörelsebibliotek (m10).
- **Testsviten:** åtta tester faller redan i baslinjen, i skymning, möbelintervall, `ingest_klipp`-jämförelsen och platsens täckning.

## Läge 12 nov natt: föremål i handen (0013)

Ett föremål som hålls följer handen i filmen: `kontrakt/handforemal.py` (hand och fäste per tagning ur maskens tyngdpunkt mot handlederna) → `plan.handforemal` → Child Of vid handledsbenet i `ingest/mhr_rig.py`. Se PIPE, "Föremål i handen". b-tilltal `n06-hand`: köttbiten i handen i S1–S8 och S11 (8–124 promille från maskens tyngdpunkt). Gelato `n06-hand`: provskeden i handen i S1, inte i S2. Svar: `delegat/svar/0013-foremal-i-handen.md`. Kvar: hållen del av tagningen byggs som hela tagningen, köttbiten skyms av vågens låda i s11, och gelatos uppsättning angav fel spår för S2.

## Läge 12 nov natt: placering per kameragrupp (0012)

Beskurna rutkanter är olikheter, underbestämd riktning får förval ur deklarationen (märks `antagen`), och möbler passas en gång per mätt kameragrupp med en kopia per synlighetsintervall (`boxpassning.passa_grupp`, `mobellyft.los_grupper`). Föremål på möbel placeras ur maskens tyngdpunkt, och en föremålskopia i en tagning utan egen ruta visas inte (`foremallyft.los_kopior`). Segmenteringen är reproducerbar (separat prompt per element, L4, deterministisk). b-tilltal `n06-grupp`: `disk_C` x ≈ 2,27 i alla grupper (var 3,09), vågen står till vänster i s11 som i originalet. Svar: `delegat/svar/0012-sidled-och-placering-per-kameragrupp.md`. Kvar: vågen är en hel låda som skymmer Lærke i s11 (formen, inte läget), och diskens x är `antagen` i de flesta grupper.

## Läge 12 nov sen kväll: mätt ram i kedjan (0010)

Nytt steg före deklarationen: `rum_grupper.py` (mätta kameragrupper) och `rum_rutor.py` + `modal_segmentera.py` (rutor ur segmenterare, tre kontroller). Se `PIPE.md`, avsnittet "Mätt ram före deklarationen". Provad på b-tilltal (variant `n06-matt`, jämförd med `n06-fler2`) och guacamole (`matt`). Svar och siffror: `delegat/svar/0010-matt-ram-in-i-kedjan.md`. Passningen (0007) och fokal per klipp (0009) ligger redan inne. Kvar: x-läget för `disk_C` är underbestämt, `fokal_klipp.py` är inte körd i ingesten, och DA3/VGGT ger ännu ingen användbar skala (svar 0006, 0011).

## Läge 12 nov kväll (gäller före allt nedan)

Kedjan från video till deklaration och nivå går utan ägarens input på fyra klipp: b-tilltal, guacamole, sketch och gelato.
- **Steg:**
  1. `rum_video.py --variant deklaration --reparera 2` × 5
  2. `rum_konsensus.py`
  3. `rum_fokus.py`
  4. `rum_konsensus.py --fokus`
  5. `rum_video.py --variant uppsattning` × 5
  6. `rum_uppsattning.py --niva L --deklaration`
  7. `klipp_kor.py <klipp> prepare|render --variant <namn> --deklaration <fil>`
- **Mot facit:** personerna stämmer 55/55, 6/6 och 15/15.
- **Föremål och möbler** placeras ur bildrutor mot den lösta kameran (Codex: `mobellyft.py`, `kvalitet.foremal_lyft`/`mobel_lyft`).
- **Närmast att göra:**
  - **Skymning rättad** (3D-segment; i s11 tar den bort 189 falska handträffar, och notan och guacamole har oförändrat 0 åtgärder). Diskarna behålls när de är bildbekräftade.
  - **Bildrutor per tagning** kommer ur nyckelbildsdetektion (`ingest/rum_detektera.py`), eftersom videorutor blev schablonvärden. Passningen över flera tagningar finns (`kontrakt/boxpassning.py`), men residualerna är 500–1000 px. De lösta kamerorna i olika uppställningar är inte överens om rummet. Den avbrutna följdrättelsen ligger i `kontrakt/ut/foremal_logg/LOGG.md` och ska granskas först.
  - **Vägval att ta:** konsekvens mellan tagningar (en mätt gemensam ram, PIPE 6b) eller placering per tagning när passningen inte går ihop.
  - föremål i handen
  - avståndet mellan hörn saknar mätning (gissningsvektor)
  - Argon eller 3.1 Pro när Vercel-krediter finns
- **Nyckel och kredit:** Gateway-krediten har 2,07 dollar kvar. Nyckeln står på första raden i `C:/Users/praiseworthy/Desktop/ky.txt`, och miljövariabeln `AI_GATEWAY_NYCKELFIL` pekar på filen.
- **Tester:** alla gröna 17:10, inklusive `test_flode.Plats` 11/11 (52 s med varm cache).

## Dagen 12 nov: blint briefprov på `b-tilltal-ravara`, hela vägen till film

Klippet visar en slaktarbutik i 11 tagningar med en person per tagning. Tre personer gissar vad en köttbit väger, och biten vägs sist.
- **Brief:** blindförslaget kom från en LLM som bara såg `brief/`. Det fick rum, roller och relevans rätt men lade varje uppställning som en ö 10 m bort och placerade möblerna i en lokal ram. Ägarens läsning ("samma lokal, männen på samma ställe, Lærke i en scen med en vinkel som öppnar mot vågen") gav `ingest/ut/b-tilltal-ravara-tagningar/plats/deklaration.json` version 0.3. Frågorna 5–10 är obesvarade och står som `antagen`.
- **Film:** `kontrakt/ut/b-tilltal-ravara/narvaro/film.mp4` och `narvaro/blad/`. Hela kedjan körs med den nya allmänna körfilen `klipp_kor.py <klipp> prepare|render`.
- **Rättat i dag:**
  - `scenbrief.py` läser cp1252-filer.
  - Validatorn och uppdraget kräver en gemensam ram, roller som heter A/B/C och hemplatser som heter `staplats_<roll>`/`stol_<roll>`. Båda konventionerna var outtalade, och blindförslaget får nu 13 fel.
  - Planbeslut-cachen nycklas på alla transitivt importerade moduler (`datacache.lokala_moduler`). Den fasta listan saknade 17 moduler, bland dem `dolda_fotter.py`, och det var troligen orsaken till de gamla besluten. Ett prov finns i `test_snabb`.
  - `plats.py:373` har en gren för deklarerat montage. Butik eller disk utan dialogaxel hamnade förut i identitetsgrenen, så kroppen låg 1,3 m under golvet (Codex, `CODEX-TILLTAL.md`, `kontrakt/ut/b-tilltal-ravara/CODEX-LOGG.md`).
  - `narvaro.py` läser briefens närvaroformat.
- **Resultat:** ankarrest 0,054 m och kamera-XY-rest 0,02–0,39 m. S5 har 2,29 m rest, eftersom dess lästa 3,67 m är misstänkt och kolliderar med den antagna kameraplatsen.
- **Brister som syns i filmen:** köttbiten och vågen saknas, eftersom formatet inte har föremål på möbler eller i händer. Rummet är grått, eftersom väggarnas kakel och stål inte förs vidare.
- **Att fixa, inget valt fokus:** PIPE Öppet punkt 6 (rummet ur alla tells utan ägarens input). Notans och guacamoles `plats.json` är byteidentiska bara med de frysta mallarna i `fore_mobelintervall/kod/`. Med dagens levande mallar skiljer de sig sedan nattens möbelintervall, vilket är väntat men inte godkänt.

## Gjort i natt (sju steg, i ordning)

| # | Steg | Kod | Baslinje / resultat |
|---|---|---|---|
| 1 | Deklarationen bindande genom kompilatorn (golv, sitthöjd, kamerahöjd; tal eller `[min, max]`) | `kontrakt/deklarationskontroll.py`, `golvmatning.py`, `trostod.py`, `tropassning.py` | `kontrakt/ut/fore_dekl_bindande/` |
| 2 | Tagning med flera roller registreras mot alla rollers platser | `ingest/plats.py` (`passa_roller`) | `kontrakt/ut/fore_flerroll/` |
| 3 | Möbler med deklarerat intervall, ett värde per möbel för hela klippet | `kontrakt/mobelintervall.py` | `kontrakt/ut/fore_mobelintervall/` |
| 4 | Genererade väggar vidgas kring kameror, möbler och roller | `kontrakt/vaggar.py` | `kontrakt/ut/fore_vaggar/` |
| 5 | Bildtrohet mäts i slutkameran; massiv möbel (`massiv`) | `kontrakt/bildkamera.py`, `trohet.py`, `ingest/rumsmall.py` | `kontrakt/ut/fore_bildtro/`, `BILDTRO-LOGG.md` |
| 6 | Textlagret: delsträngens egen tid, radbrytning, diagnostik | `kontrakt/skarmtext.py`, `textmalning.py`, `textenheter.py` | `kontrakt/ut/fore_text_s4/`, `TEXT-LOGG.md` |
| 7 | Scenbriefen som eget steg: paket, validator, återkoppling | `ingest/scenbrief.py` | `SCENBRIEF-LOGG.md`, `SCENBRIEF-JAMFORELSE.md` |

Senaste guacamole-film: `kontrakt/ut/e-dialog-guacamole/text_s4_slut_narvaro/jamforelse.mp4` (original till vänster). Guacamoles deklaration är version 0.8; 0.6 och 0.7 ligger bredvid.

Uppdragsfilerna (`CODEX-BILDTRO.md`, `CODEX-TEXT.md`, `CODEX-SCENBRIEF.md`) visar hur uppdragen formulerades.

## Att lita på och inte

- **Skymningssiffror från steg 1–3 är ogiltiga.** `kontrakt/skymning.py` var utbytt mot en äldre version 21:21–22:59 av ett bakgrundstest från en tidigare session. Rätt baslinje: `kontrakt/ut/fore_vaggar/omkord_ratt_skymning/`. Med rätt regel: guacamoles disk höjd 1,00 m, mittpunkt 0,65 m; notans bord 0,70 m, orört.
- **Inramningen är rätt.** Slutkameran projicerar lederna 1–5 px från originalet (ram-IoU 0,94–0,98). Det som ser fel ut i bilderna är standardkroppens volym och avsaknaden av kläder.
- **Guacamoles briefjämförelse är inte blind.** Uppdragsfilen bad Codex läsa den handskrivna deklarationen före experimentet. Servering-klippets jämförelse är okontrollerad på samma punkt.
- **Intervallen för guacamoles disk och A–B-avståndet 1,73 m är inte godkända av ägaren.** Avståndet är läst (monokulärt djup, märkt `last`), diskintervallen är antagna.

## Nästa, i ordning

0. **Gemini-deklaration med konsensus (arbetshypotes, 12 nov eftermiddag).** Se PIPE Öppet punkt 6. Med flash × 5 och `rum_konsensus.py` blir topologin lika med ägarens läsning och ankarresten 0,036 m (ägarens version 0,054 m). Kedjan går till film utan handpåläggning. Nästa steg:
   - samma prov på ett klipp av en annan typ
   - Argon eller 3.1 Pro när krediterna finns
   - föremål på möbler och i händer i formatet
1. ~~Blint briefprov~~ klart 12 nov (se ovan). Nästa prov: ett klipp av en annan typ, till exempel en sketch med två personer i bild eller snabb klippning mellan miljöer, för att se om bristerna i punkt 6 kommer tillbaka.
2. ~~Cachen `planbeslut`~~ rättad 12 nov (transitiv kodnyckel).
2b. **Föremål i händer och på möbler** (köttbit, våg). Bär scenen i b-tilltal men byggs inte.
3. ~~`test_flode.Plats`~~ körd 12 nov (96 min): 9/11 gröna. De två felen var en föråldrad förväntan (bord_A-segmenteringen fanns före steg 1) och en drift på 7,9 mm i bar-kamerans målpunkt (orsaken är inte utredd, och testet har nu tolerans 1e-2). Se `kontrakt/ut/testflode_logg/LOGG.md`.
4. **Diskens U-form** (sammansatta möbler i deklarationen) och textens ord-för-ord-visning.
5. **Kroppens yta** (kläder, volym). Hör till stiliseringen, som kommer sist.

Mindre, från vägen: `narvaro.py` kontrolleras inte mot deklarationen; C:s ben i notans s4 blev 8,7 % längre när golvet blev bindande (fötterna säger golv 0,13 m över deklarerat); B:s torso i guacamole s4 är vriden 42° från riktningen mot A; `test_snabb` blev grön av ett cachefilter utan att `KeyError: 'dolda_fotter'` felsöktes.

## Kvoter vid avslut (01:05)

- Codex, konto 2: 86 % av femtimmarsfönstret, 76 % av veckan. Konto 1: femtimmarsfönstret åter 04:15, veckan 63 %.
- Fable: ont om tokens i kväll. Sonnet-agenterna drog ungefär 950 000 tokens på steg 1–4.
