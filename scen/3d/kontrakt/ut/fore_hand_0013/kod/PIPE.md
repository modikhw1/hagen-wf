# Pipen: från klipp till förvärld (11 nov 2026)

Enda ingången till scenkreationen per klipp. Här står vad varje del gör, varför den är vald och vad som är omätt. Detaljerna ligger kvar i respektive mapp (se sist).

Nytt helklippsprov 11 nov: [GUACAMOLE-LOGG.md](GUACAMOLE-LOGG.md), Mexik-dialog med fyra tagningar och två roller vid samma bardisk. Loggen innehåller urval, körningar, antaganden, fel och verifiering. `guacamole_kor.py` återanvänder pipelinekommandona för deklaration, plats, källa, plan, närvaro och rendering. Deklarationen kan nu uttryckligen ange `kameror.<S>.huvudroll` och `spar_id` för tagningar med flera personer; explicit deklarerad rumsmall prioriteras framför semantikens mallförslag.

## Grundregeln

**Originalet är sanning för allt som syns i bild. Generativ AI är en hypotes om det som inte syns, och ett sätt att städa.** Varje generativt utfall mäts mot originalet. Driver det, vinner originalet.

Regeln kommer ur mätningarna 10–11 nov:

- SAM 3D Body läser kroppen lika bra ur originalet som ur en omgjord bild (städat: under 1 % posedrift, alltså ingen vinst). Grov stilisering skadar (färgytor: 32 % drift).
- Videomodellen tar egna beslut: ändrade händer (S6: 11,5 %), pizza i stället för hamburgare, påhittade skor, logotyper, krukväxter och gäster.
- Ett genererat rumsskal är ett nytt rum (djupets rangkorrelation 0,36–0,68).
- Vinsten finns utanför bildramen: breddat gav servitören hela kroppen, fotkontakt och längden 1,73 m i stället för 1,90 m.
- Breddning hjälper bara där kroppen finns men är beskuren av ramen (stående person på öppet golv). Bakom bord och disk finns inget att avslöja.

## Stegen

| # | Steg | Vad det ger | Källa | Läge |
|---|---|---|---|---|
| 1 | **Läs originalet** | Tagningar, personspår, kamera, kropp över tid, rum i bild | `ingest/ingest_klipp.py` (YOLO, COLMAP, SAM 3D Body, MHR, MoGe) | Finns |
| 2 | **Scenbrief** | Rumshypotes och relevans, en gång per klipp | `ingest/scenbrief.py`: cachepaket till LLM, validator och ägargranskning | Finns som eget steg; ägargodkännandet är manuellt |
| 3 | **Generativ komplettering** | Dold kropp (ben, fötter), städad bild | Wan VACE på Modal (`lasformat/`), Luma i appen (`lasformat/luma-paket/`) | Wan mätt på 5 tagningar. Luma mätt på stillbilder och två videor |
| 4 | **Mät och gallra** | Godkänt eller förkastat utfall per tagning | `lasformat/mat_klipp.py`, `luma-paket/poang.py`, `ingest/vakt.py` | Finns för bild och Wan-video |
| 5 | **Sätt ihop förvärlden** | Ett rum med alla personer, även det som kameran gömmer | `kontrakt/` (`kalla.json`) | Finns per tagning. Gemensamt rum över tagningar är ett hål |
| 6 | **Modulera semantiskt** | CM:s ändringar | `kontrakt/` (`regi.json`, plan) | Finns, översättningen mening till operation är inte inlärd |

Loopen går mellan 2, 3 och 4: briefen styr prompten, mätningen visar var modellen hittade på, briefen rättas.

## Steg 2: scenbriefen

De två svåra besluten tas här, före all generering, och på ett ställe:

**Rumshypotes** (arbetshypotes: ett klipp, ett rum)
- vilka tagningar som delar rum och kamerauppställning
- vilka personer som är samma över tagningarna (A, B, C)
- hur de står i förhållande till varandra, även när bara en syns

**Relevans i tre nivåer**
- *bär scenen*: det handlingen hänger på (notan, maten, kortläsaren). Behålls exakt.
- *sätter rummet*: bord, stolar, fönster, dörr, lampor. Behålls enkelt.
- *stryks*: gäster i bakgrunden, undertext, skyltar, smådekor.

Briefen har två mottagare: prompten till videomodellen (steg 3) och `kalla.json` (steg 5). Samma brief till båda, så att det genererade och det byggda rummet bygger på samma antaganden.

Första exemplet: `ingest/ut/notan-tagningar/plats/deklaration.json` (11 nov). Den skiljer det berättade rummet (S1–S6, ett gemensamt bord) från det avslöjade (S7, B vid eget bord). Kedjan läser den sedan 11 nov via `ingest/deklaration_till_hand.py`, som översätter deklarationen till `plats_berattat/hand.json` och skriver rumsmallen `notan_ett_bord`. `plats.py` tar då golv, kamerahöjd och lod ur deklarationen i stället för att mäta dem per tagning. Utdata: `ingest/ut/notan-tagningar/plats_berattat/` och `kontrakt/ut/notan_berattat/` (kalla och plan). Den gamla vägen med `plats/hand.json` (två bord) ligger kvar orörd och ger byte för byte samma resultat som före ändringen.

Första inpassningen (`ingest/passa_deklaration.py`, resultat i `plats/inpassning.json`): för stående C med synliga fötter (Lumas breddning) håller golvet, vänster och höger fot skiljer 0,9 cm och kamerahöjden 1,27 m varierar 0,6 cm över 85 rutor. För sittande A och B går lodriktningen inte att läsa ur kroppen, eftersom framåtlutningen blandas ihop med kamerans lutning. Deklarationen ger därför kamerahöjden i sittande tagningar (1,20 m, motpartens ögonhöjd). Med den blir läsningen samstämmig över fem tagningar: ögonhöjd 1,17–1,25 m, armbågar 0,70–0,80 m mot bordets 0,74 m, och avståndet kamera till höft 1,39–1,44 m i fyra av fem. De lästa avstånden är förda tillbaka till deklarationen (version 0.2), märkta `last`. Samma gjordes för guacamole (version 0.7): A–B-avståndet 1,73 m i S4 ersatte det antagna 1,30 m, och flerrollsrestfelet gick från 22 cm till 0,2 cm.

Vem skriver den: en LLM som ser alla tagningars nyckelbilder samtidigt. Gemini får föreslå men inte döma, eftersom dess föremålslistor varierar mellan körningar. Lumas agent flaggar själv sina avvikelser i chatten, och de är användbart underlag för rättningen. Ägaren godkänner.

Sedan 12 nov bygger `ingest/scenbrief.py bygg ingest/ut/<klipp>` ett självständigt cache-only-paket i `brief/`: märkta kontaktblad, `lasning.json`, LLM-uppdrag och schema för deklaration 0.8. `granska` kontrollerar schema, referenser, kameratäckning och talens proveniens samt provöversätter i scratch; `aterkoppla` kan föreslå, men aldrig tillämpa, rättningar ur planens deklarations-/registrerings-/möbeldiagnostik. Första experimentet och fältjämförelsen finns i `SCENBRIEF-LOGG.md` och `SCENBRIEF-JAMFORELSE.md`.

### Deklarationen som allmän mekanism

Det som byggdes för notan 11 nov är tänkt att gälla alla klipp. Fyra delar, där de tre sista inte vet något om notan:

| Del | Fil | Allmän? |
|---|---|---|
| Deklarationen: golv, platser, kameror, roller, närvaro, relevans | `ingest/ut/<klipp>/plats/deklaration.json` | Formatet ja. Innehållet skrivs per klipp |
| Översättning till platsstegets indata och rumsmall | `ingest/deklaration_till_hand.py` | Ja sedan 11 nov kväll. Allt klippspecifikt står i deklarationen (format 0.4), och rumsmallen `dekl_<klipp>` genereras ur platserna. Ger exakt samma rum för notan som den handskrivna |
| Platssteget tar golv, kamerahöjd och lod ur deklarationen; en tagning kan märkas som att den bryter rummet | `ingest/plats.py` | Ja |
| Närvaro: roller som finns i rummet utan att vara lästa i scenen | `kontrakt/narvaro.py`, stöd i `ingest/mhr_rig.py` | Ja |

Närvaron arbetar på den färdiga planen. För varje scen och varje deklarerad roll som saknas lånas rörelsen ur rollens närmaste tagning i tid, och eftersom alla tagningar ligger i samma plats hamnar rollen på sin plats utan ny placering. Rollen som kameran står hos finns i rummet men renderas inte i den scenen.

**Deklarerade värden är bindande genom kompilatorn (11 nov kväll).** Översättaren skriver det som uttryckligen står i deklarationen (golv, `sitthojd_m` per sittplats, `hojd_m` per kamera) som `hand.deklarerat`, `plats.py` för det oförändrat till `plats.json` (`deklarerat`), och `kontrakt/` läser det därifrån. Varje värde är ett tal (hårt) eller `[min, max]` (kompilatorn får röra sig inom intervallet). `golvmatning.platsbeslut(bunden_golv_m=...)` behåller platsens deklarerade golv och flyttar inga kameror; GOLV2-cuesen körs ändå och redovisas som mätkonflikt. `trostod.sitt_hojd(deklarerat=...)` ersätter stolsprioren 43–48 cm med det deklarerade värdet; prioren gäller bara när inget är deklarerat. `kontrakt/deklarationskontroll.py` jämför sedan planens golv, sitthöjd och kamerahöjd (per scen) med deklarationen och skriver `plan.kvalitet.deklaration` (poster, avvikelser, mätkonflikter); varje avvikelse blir också en varning. Klipp utan `deklarerat` (gamla vägen med `plats/hand.json`) går samma väg som förut och ger byte för byte samma plan. Följd: en körning bygger bara på en `plats.json` som skrivits efter ändringen, äldre `plats.json` måste byggas om (`plats.py` + `kalla_bygg.py`) för att deklarationen ska gälla. Mätningarna: `GUACAMOLE-LOGG.md`, sist.

**Flera roller i samma tagning (11 nov natt).** I ett deklarerat rum registrerades en tagning på huvudrollens plats, och den andra kroppen följde läsningen. Nu skriver översättaren `hand[tagning].flera_roller` (roll, plats, blickriktning) när minst två deklarerade roller finns i tagningen, och `plats.py` löser kameran (yaw + xy, skala 1,0, z orört) i minsta kvadratens mening mot alla synliga rollers platser (`passa_roller`). Kropparna flyttas inte var för sig. Restfel per roll står i `plats.json` (`tagningar[].kvalitet.roller_registrering`), kalla (`registreringar[].roller_registrering`) och `plan.kvalitet.deklaration.registrering`; över 15 cm (`deklarationskontroll.REGISTRERING_VARNING_M`) blir det en varning i planen. Tagning med en synlig roll, klipp utan `flera_roller` och gamla vägen går som förut (byte för byte). Mätningar: `GUACAMOLE-LOGG.md`, sist.

Prövat på ett andra klipp (`a-sketch-servering-tagningar`, utkast till deklaration skrivet av orkestratorn, inte av ägaren): översättaren går igenom utan ändring. Hela kedjan till plan är inte körd där. Tre saker visade sig:

- Stående personer med skymda ben tål en gissad kamerahöjd. Ögonhöjden ändras 4–9 cm när kamerahöjden ändras 40 cm, eftersom höften sätts av benens egen längd.
- Samma kropp får olika benlängd i olika tagningar när benen är skymda (0,77–0,89 m). Golvet är alltså osäkert på 5–10 cm tills benen syns, till exempel genom breddning.
- En roll som står på flera ställen (disk, spett, bänk) ryms i formatet med `person_plats` per tagning, men lägena måste komma någonstans ifrån.

### Händer utan bildstöd (11 nov kväll)

Kroppsestimatorn ger alltid två händer, också när de är skymda av mat, bord eller inbränd text. De är gissningar och rycker. Tre delar hanterar det, alla allmänna:

| Del | Fil | Vad den gör |
|---|---|---|
| Handsyn | `ingest/handsyn.py` | Per ruta och hand: synlig, störd (delvis under text) eller dold. Bygger på personmasken (en annan modell än kroppsestimatorn) och textrutorna i `kalla.json` |
| Handsyn i planen | `kontrakt/handsyn_plan.py` | För in handsynen per person och scen, även för närvaropersoner |
| Handvila | `ingest/mhr_rig.py` | Dold kort lucka interpoleras, dold lång hålls i luckans medelställning, störd jämnas ut. Bara handled och fingrar ändras |

I notan: S6 har båda händerna dolda hela tagningen, S2 och S5 den ena, S3 den ena dold och den andra under text i 45 av 57 rutor.

Två följdändringar: skymningskontrollen (`kontrakt/skymning.py`) låter bara ledpunkter som själva syns ge djup åt synliga pixlar, och i ett deklarerat rum registreras varje tagning på rollens plats i stället för med bildmatchning. Tillsammans med bordshöjden 0,70 m står det gemensamma bordet nu kvar i alla sju tagningar. Skymningsändringen gäller alla klipp, inte bara notan.

Möbler som intervall (11 nov natt): bordets och diskens höjd, mått och mittpunkt kan deklareras som tal (hårt) eller `[min, max]` (`storlek_m.hojd/langs_x/langs_y`, `mitt_m`; format 0.7). Översättaren för dem som `deklarerat.mobler`, och `kontrakt/mobelintervall.py` väljer före skymningskontrollen ETT värde per möbel för hela klippet, det som ger minst skymningskonflikt över alla tagningar (rutnät över intervallen; rör bara möbeln om någon scen annars skulle flaggas; kontrollens gränser orörda). Valt värde, konflikt före/efter och om gränsen nåddes står i `plan.kvalitet.mobelintervall`. Deklarerad bordshöjd har dessutom företräde framför `BORD_INTERVALL_M` (72–76 cm) i `tropassning.py`; prioren gäller bara utan deklaration. Det som lösaren inte klarar inom intervallet utelämnas som förut. Kvar: lösaren väljer bara bland rutnätets värden, och möbelns form är fortfarande skiva på fyra ben (en disk som täcker kroppen under skivan finns inte). Händernas viloställning är ett medel av gissningar, inte en läst ställning.

**Väggar som inte kan blockera (12 nov).** Rumsmallen byggs kring platserna, men kamerorna är inte kända då, så en genererad vägg kunde hamna mellan kamera och motiv (guacamole S4: kameran 1,0 m bakom sidoväggen). Nu byggs rummet i två steg: mallen som förut, och efter registreringen vidgar `kontrakt/vaggar.py` (anropad sist i `kompilera.py`) de GENERERADE väggarna och golvet så att rummet rymmer alla renderkamerans lägen (+0,5 m), alla möbler (+0,1 m) och alla rollankare (+0,3 m). Bara utåt, så ett rum som redan rymmer allt rörs inte. Uttryckligt deklarerade väggar (`vaggar.bak.y_m`, `vaggar.sida.x_m` i deklarationen, format 0.7) är hårda: de flyttas aldrig, och rymmer de inte kamerorna blir det en konflikt och en varning. Kontrollen mäter slutplanens geometri per scen: ligger kameran utanför rummet eller i en vägg, och skär sikten från kameran till en synlig roll (tre höjder) en vägg? Resultat i `plan.kvalitet.rumsvaggar` (genererade väggar märkta `antagen`, `kallmatning: null`) och som varning. Gäller bara platser med `deklarerat`; gamla vägen får ingenting nytt. Marginaler och provhöjder är antagna. Mätningar: `GUACAMOLE-LOGG.md`, sist.

**Bildtrohet i slutkameran och massiv disk (11 nov natt).** För deklarerade rum projicerar `kontrakt/trohet.py` nu samma riggleder genom `plan.renderkamera` och redovisar per scen/roll medeloffset, andel av bildhöjd, skalfaktor och bbox-IoU. `kontrakt/bildkamera.py` får lösa kamera-xy, yaw, pitch, roll och lins, men lämnar bunden kamerahöjd och kroppar orörda; en kamera inom gränserna bevaras exakt. Guacamoles plan- och Blenderkamera återgav redan 2D-lederna, så ingen kamera ändrades: den synliga skillnaden kommer främst av standardkroppens volym/kläder och möbelns form. Deklarerade bord kan därför ange `massiv: true`; guacamoles bardisk är nu en låda ner till golvet, medan notans bord förblir skivor på ben. Gamla vägen behåller sin äldre diagnostik byte för byte. Mätningar och rendering: `BILDTRO-LOGG.md` och `GUACAMOLE-LOGG.md`, sist.

Kända luckor: närvaron körs som ett eget steg efter kompileringen och är inte inkopplad i `kor_klipp.py`. Lånad rörelse är inte en reaktion på det som sägs. Skymningsregeln döljer det gemensamma bordet i A:s tagningar.

## Steg 3: vem gör vad

| | Wan VACE (Modal) | Luma (appen) |
|---|---|---|
| Håller klippet över tid | Ja, cirka 3 px drift. Originalets personpixlar skyddas med mask och läggs tillbaka | Ja på två tagningar (11 nov): breddat S4 3,4 px, städat S1 1,3 px. Vid breddning lägger agenten originalramen oförändrad i bilden, som Wan |
| Breddning | Ja, 85/85 rutor med ben, fotkontakt utan glidning | Stillbild: bra för stående (1 %), dålig för sittande (16 %) |
| Städning | Inte prövat | Stillbild: bra (under 1 % drift) |
| Rum | Instabilt (MoGe-variation 23 % mot 2,4 %) | Breddad video stabil (2,1 %), men två personer ger golv som skiljer 25 cm. Rumsskal som stillbild otroget |
| Följer beordrad ändring | Inte prövat | JSON-bilaga gav bäst utslag av fyra sätt, men mätt på en bild |
| Kostnad | 0,26 USD per tagning, automatiskt | 70–140 krediter per bild, för hand i appen |

Vid breddning är Wan och Luma jämförbara: båda behåller originalets pixlar och genererar bara ytan runt om. Vid städning ritar Luma om hela bilden.

Rummet tas aldrig ur det genererade. Det kommer ur originalet (MoGe) och briefens hypotes, och byggs med enkla lådor och plan.

## Mätt ram före deklarationen (uppdrag 0010, 12 nov kväll)

Gemini säger **vad** som finns och vem som är vem. Där ett prov visade att mätning bär, mäts **var** och **vilka tagningar som delar kameraplats**, och mätningen går före Geminis gissning:
- **Kameragrupper:** `ingest/rum_grupper.py` (SIFT på bakgrund med maskade personer, ur `bakgrund_prov/matcha.py`). Utdata `grupper.json`: `delar_plats`, tal per par, `utan_koppling`. *Mätt:* parets F-inliers över en nollgräns som är härledd per klipp (p99 mot ett annat klipps tagningar, och 1,5 × vad parets egna slumpade matchningar nådde). *Valt:* homografin förklarar minst 60 %, rotation högst 30°, minst hälften av bildrutparen över gränsen. Resultat: b-tilltal S3–S4, S6–S7 och S8–S10; guacamole S1–S3. Övriga par är **inte mätta**, inte motbevisade.
- **Konsensus:** `rum_konsensus.py --grupper grupper.json` tar de mätta paren som givna fakta (andel 1,0) för frågan "samma kamera". Geminis röstning och fokusfrågorna gäller bara par som mätningen inte säger något om. Mätt och röstat skiljs åt i rapporten och i `_meta.json` (`kamera_vid_matta_par`).
- **Rutor:** `ingest/modal_segmentera.py` (Grounding DINO + SAM 2, Apache-2.0, på Modal; Geminis elementnamn som prompt) och `ingest/rum_rutor.py` (rutan ur SAM-masken, median över bildrutorna). Tre kontroller, var och en med orsak i utdata: överlapp mellan element (IoU ≥ 0,7), homografiöverföring inom grupperna (IoU ≥ 0,25 mot den egna rutan), och `null` när elementet inte hittas. En ruta som faller i en kontroll förs inte vidare. *Valda* trösklar, inte härledda. Flagga: `rum_detektera.py --rutor segment --seg <seg.json> [--grupper <grupper.json>]`; `--rutor gemini` (förval) är den gamla vägen.
- **Hypotes, inte mått:** att segmenterarens ruta är rätt avgörs av kontrollerna och av avläsning ur nyckelbilden (svar 0008: inom 1 promille för S6, S7 och S8). x-läget för en disk som går förbi bildkanten är underbestämt och styrs då av enstaka sidokanter.

## Öppet

1. **Luma helklipp mot Wan.** Prompter och ordning: `lasformat/luma-paket/STEG2-VIDEO.md`.
2. **Stilisering som läshjälp.** Stillbilderna talar emot. En videoarm stänger frågan.
3. **Gemensamt rum över tagningar.** Briefens rumshypotes behöver en plats i `kalla.json`.
4. **Briefens ägargodkännande.** Paket, format och validator finns; extern LLM-körning och att föra chattens godkända beslut till slutlig `deklaration.json` är ännu inte automatiserade.
5. **GEM-X** som alternativ kroppsläsare över tid: se `kroppsbank/GEMX-LOGG.md`.
6. **Rummet ur alla tells, utan ägarens input** (att fixa, inget valt fokus; 12 nov). Målet är att kedjan själv placerar alla tagningar korrekt i ett rum. Ägaren ska inte behöva säga det. Blindprovet på `b-tilltal-ravara` (11 tagningar, en person per bild, ihopklippt) visade två brister. Formatet kan inte uttrycka "okänt inbördes läge", så briefen lade varje kamerauppställning som en ö 10 m bort. Uppställningar och platser gissas också i stället för att mätas. Ägaren läste klippet rätt på en gång: samma lokal, de två männen på ungefär samma ställe, och Lærke i en scen med en vinkel som öppnar mot vågen. Spår att pröva:
   - (a) Gemini eller en annan videomodell ser hela klippet och ger strukturerad utdata, alltså ett rum med karaktärer, viktiga objekt och en bästa gissning om lokalen. Det kan vara xyz-text eller en annan form som binder ihop väggar, kakel, möbler, ljus, förkläden och klippformat. Det gäller som hypotes enligt grundregeln, och Gemini föreslår men dömer inte.
   - (b) Bakgrundsmatchning mellan tagningarna med maskade personer, med SIFT/LoFTR/COLMAP över tagningsgränser. Det ger mätt överlapp mellan uppställningarna.
   - (c) Befintliga beroenden som kartlägger rum ur innehåll.
   
   Klipptypen ska vara en del av hypotesen: mobil som håller scenen, sketch eller snabb klippning mellan olika miljöer. Om samma brist kommer tillbaka i senare klipp ska den rättas.

   **Första prov på (a), 12 nov.** Skriptet är `ingest/rum_video.py`: hela videon och tagningsgränserna går till Vercels AI Gateway med ett JSON-schema för strukturerad utdata. Svaren ligger i `ingest/ut/b-tilltal-ravara-tagningar/brief/rum_video_*.json`. Nyckeln står på gratisnivån, där bara `gemini-2.5-flash` tar video; Argon, Carbon och 3.8 kräver betalda krediter. Två körningar kostade cirka 3 cent var.
   - Stabilt mellan körningarna: klipptyp (ihopklippt i samma lokal), en lokal, namnen ur skärmtexten, relevansen och vad som står på vad. Vågen står på disken, och köttbiten hålls av en fjärde person utanför bild.
   - Instabilt: geometrin och vilken person som syns i vilken tagning. Körning 1 gav Morten S3–S4, Lærke i en egen zon 3,75 m bort och vinkeln mot vågen från S7. Körning 2 gav Morten S3–S6 och alla på samma punkt.
   - Slutsats: låt ingestens fakta vara givna (person per tagning, lästa avstånd, antal personer), be modellen bara om semantiken och den grova layouten, och ta konsensus över flera körningar.
   - Variant `scen3d` (`rum_video.py --variant scen3d`) ber om ett 3D-språk: golvpolygon, väggar med öppningar, orienterade lådor, kameror med yaw och pitch. Ingestens personrutor, avstånd och FOV ges som fakta. `ingest/rum_video_mat.py` projicerar modellens personer genom modellens kameror och jämför med ingestens rutor. Två körningar gav en median på 75–108 px x-fel (av 576), 110–390 px vertikalt fel och upp till 1 375 px fel när kameran pekade fel. Avstånden höll, eftersom de var givna. Identiteterna var rätt i en körning och fel i den andra. Geometrin bärs alltså av lösaren, inte av modellen.
   - **Arbetshypotes, prövad 12 nov:** Gemini ser videon och skriver deklarationen, och konsensus tas över flera körningar.
     - Verktyg: `rum_video.py --variant deklaration` (fakta, uppdrag, schema och guacamole som formatexempel) och `ingest/rum_konsensus.py`.
     - Konsensusmetod: topologin avgörs med samförekomst och genomsnittlig koppling över 0,5. Talen blir `[min, max]` över körningarna. Platsens djup är medianen av klustrets lästa avstånd, så att S5:s felläsning inte styr.
     - Fem körningar med flash kostade cirka 20 cent. Ingen körning var giltig för sig: referensfel, hårda tal och saknade kameror. Identiteterna var rätt i 3 av 5, och männen stod på samma ställe i 4 av 5.
     - Konsensusen godkänns av validatorn. Mot ägarens v0.3 stämmer personerna i 55 av 55 tagningspar och kamerauppställningarna i 51 av 55. Männen står på samma punkt, och avståndet till Lærkes hörn är 3,2–5,0 m (median 4,1 m).
     - Hela kedjan går igenom utan handpåläggning: `klipp_kor.py b-tilltal-ravara prepare --variant konsensus --deklaration …` ger `kontrakt/ut/b-tilltal-ravara_konsensus/`. Ankarresten är 0,036 m, mot 0,054 m för ägarens version.
     - Möbler i konsensus (iteration 2): finns massiva diskar i minst hälften av körningarna (här 5 av 5) står en disk framför varje plats, med mått som medianen av körningarnas gränser: 2,0–3,0 × 0,6–0,8 × 0,82–0,97 m. Ankarresten är fortfarande 0,036 m. I film `kontrakt/ut/b-tilltal-ravara_konsensus_mobler/narvaro/` ligger diskkanten där originalets ligger (s6).
     - Saknas: små föremål (vågen finns på disken i 4 av 5 körningar) listas bara i `konsensus_mobler_meta.json`, eftersom formatet inte bygger dem. Namnen på A och B saknas, och relevansposterna har olika namn mellan körningarna. Dessutom läser konsensusen berättelsen som "en kund visar ett köttstycke för olika biträden".
     - **Iterationer, 12 nov kväll:**
       - (1) *Reparationsvarv* (`--reparera 2`): validatorns fel går tillbaka i samma konversation. Promptregler lades till för kameraplatser (typ staplats, aldrig ett tagnings-id i `kamera_vid`) och golv `[0, 0]`. Felen sjönk från upp till 70 till 0–7 per körning, och 2 av 5 blev giltiga.
       - (2) *Stabilitet mellan omgångar:* personerna stämmer 55 av 55 och uppställningarna 50–52 av 55, både mellan omgångarna och mot ägaren. "Männen på samma ställe" var instabilt: 4 av 5 i omgång 1, 2 av 5 i omgång 2.
       - (3) *Fokusfrågor* (`ingest/rum_fokus.py`): osäkra par (andel 0,25–0,75) ställs som smala frågor, fem gånger var, och svaret ersätter den breda röstningen i `rum_konsensus.py --fokus`. Svaren blev motsägelsefulla för samma ställe (S1–S3 0,2, S2–S3 0,8) men tydliga för samma kamera (S1–S3 och S1–S4 5 av 5).
       - (4) *Härledning ur mätningar:* delar två platskluster kamerakluster och ingesten mäter nästan samma avstånd (< 0,5 m) och bildmitt (< 15 %), slås platserna ihop. Då ger båda omgångarna ägarens läsning, männen på samma punkt.
       - Kvar som gissningsvektor: avståndet mellan hörnen, 2,3 m i ena omgången och 4,1 m i den andra. Ingenting i bild mäter det, och platsers läge kan ännu inte bära intervall i formatet.
     - **Prov mot facit på två klipp till (12 nov kväll).** Metoden: fem körningar med `--reparera 2`, konsensus, fokusfrågor, konsensus igen. Guacamole använde notan som formatexempel. Jämförelse med `ingest/rum_jamfor.py`.
       - Guacamole: 4 av 5 körningar giltiga. Konsensusen stämmer med facit på personer (6 av 6) och platser (6 av 6), och A sitter (`stol_A`). Hållningen avgörs med majoritet över körningarna sedan rättningen i kväll; innan blev allt ståplatser.
       - Sketch (servering): 2 av 5 giltiga. Personerna stämmer med facit (15 av 15): A i S1 och S7, B i S2–S5. S6 får en egen person C, där facit saknar roll.
       - Kostnad per klipp: cirka 0,35 dollar med flash, inklusive fokusfrågor.
       - Facit saknar `kamera_vid` för båda klippen, så kamerauppställningarna kan inte jämföras där.
       - Nytt klipp utan facit, `kand-kennysgelato` (2 tagningar, rörlig kamera): 3 av 5 körningar giltiga. Konsensusen godkänns: en person, en plats, två uppställningar, en disk. Uppsättningen ger rekommenderad nivå 0,6 (5 av 5): disken 0,4, provskeden i A:s hand 0,6, kaffemaskinen 0,8, frukten 1,0. Det som bär handlingen hålls ofta i handen, så föremål i hand är den lucka som kommer igen.
     - **Uppsättning och nivå (pass 2):** `rum_video.py --variant uppsattning --konsensus …` och `ingest/rum_uppsattning.py`. Varje element får en tröskel på en fast stege: 0 figurer, 0,2 rumsskal, 0,4 möbler som rörs, 0,6 föremål som handlingen hänger på, 0,8 identitet, 1 allt. Reglaget L bygger det som har tröskel ≤ L.
       - På b-tilltal, fem körningar: figurer 0, golv och kakel 0,2, `disk_A`/`disk_C` 0,4 (5 av 5), köttbit och papper 0,6, vågen 0,6 (spann 0,6–0,8). Rekommenderad nivå 0,6, med spann 0,6–0,8.
       - `--niva L --deklaration` skriver en deklaration för nivån: möbler över L stryks och föremål läggs i fältet `foremal`. Föremål på en möbel byggs som massiv låda med id `<möbel>:pa:<id>` (`deklaration_till_hand.py`). Film för nivå 0,6: `kontrakt/ut/b-tilltal-ravara_n06/`.
       - Brister: vågen hamnar utanför bild i s10, eftersom läget på disken är gissat. Den svävar också 7 cm, eftersom den inte följer möbelintervallets valda höjd. Föremål som hålls i handen byggs inte.
       - Bildrutor provade: uppsättningen ger `bild` (tagning, `box_2d` 0–1000), och `rum_uppsattning.py` tar medianrutan i den vanligaste tagningen. `deklaration_till_hand.lyft_bildruta` skär strålen genom rutans bottenmitt med möbelns ovansida. Vågen flyttades från gissat läge (x 2,86) till lyft läge (x 2,15) men syns ändå inte i s10, eftersom lyftet använder den deklarerade kameran och renderingen den kamera som löses ur kroppen (`bildkamera`). Slutsats om var Geminis bedömning ska in: topologin före lösaren (deklarationen), 2D-placeringar av föremål efter att kamerorna är lösta (i kompileringen, mot `renderkamera`).
       - **Föremål i kompileringen (Codex, 12 nov kväll; `CODEX-FOREMAL.md`, `CODEX-MOBELLYFT.md`, logg `kontrakt/ut/foremal_logg/LOGG.md`):**
         - `:pa:`-föremål följer möbelns lösta höjd och mitt (`mobelintervall`).
         - Föremål med bildruta placeras mot den slutliga renderkameran (`kvalitet.foremal_lyft`). Föremål kan stå på föremål, till exempel köttbiten på vågen.
         - Möbler med bildruta placeras på samma sätt (`kontrakt/mobellyft.py`, `kvalitet.mobel_lyft`) och kläms till deklarationens ordning kamera–möbel–person. Utan klämning hamnade disken bakom personen, eftersom golvkontakten inte syns i bild.
         - Data går vägen `hand.json` → `plats.json` → `plan.plats[].deklarerat`.
         - Resultat på b-tilltal (`kontrakt/ut/b-tilltal-ravara_n06-mobel2/`): disken står 0,15 m framför Lærke, och disken och vågen projiceras in i bild där originalet har dem (s11: diskkant y 864 av 1024, vågen till vänster).
       - **Hinder: skymningskontrollen stryker möbeln.** `skymning` utelämnar `disk_A`/`disk_C` (och därmed föremålen på dem) i alla scener med skälet "minst 2 % av synliga maskprov skyms". Kontrollen jämför mot närmaste MHR70-leds djup och tar inte hänsyn till höjd. Händerna och köttet över diskkanten räknas därför som skymda.
       - Nästa steg: skymningen ska mäta verklig 3D-skymning (strålen träffar diskens ovansida under handen, inte framför den). En möbel vars läge bildrutan bekräftar ska justeras inom intervallet i stället för att strykas. Föremål i handen (`halls_av`) kräver handled per ruta i planen och ett fäste i `mhr_rig.py`.
     - Argon och Gemini 3.1 Pro antas bli bättre och exaktare. Samma kommandon tar `--modell google/gemini-4-argon`, men gatewayen kräver köpta krediter.
   - Formatet saknar fortfarande två saker som modellen ger gratis: föremål som står på eller hålls av något, och personer som bara syns som en hand.

## Var saker ligger

| Mapp | Innehåll |
|---|---|
| `ingest/` | Steg 1, ett kommando per klipp |
| `lasformat/` | Wan VACE: rapport, skript, mätning |
| `lasformat/luma/` | Lumas linjeteckningar mot originalet |
| `lasformat/luma-paket/` | Lumas format F1–F7, poäng, körlogg, videoprovet |
| `scenjson/` | Följer Luma en beordrad ändring (siffror, ord, guidebild, JSON) |
| `kontrakt/` | `kalla.json`, `regi.json`, plan, golv |
| `kroppsbank/` | GEM-X och kroppskällor |
| `blender/` | Rendering, fas 2 |
| `README.md` | Första scenen från 7 nov (MediaPipe, webbläsare). Historik |
