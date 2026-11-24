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
| 2 | **Scenbrief** | Rumshypotes och relevans, en gång per klipp | LLM över alla nyckelbilder, ägaren godkänner i chatten | **Saknas** (skrivs för hand i dag) |
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

## Öppet

1. **Luma helklipp mot Wan.** Prompter och ordning: `lasformat/luma-paket/STEG2-VIDEO.md`.
2. **Stilisering som läshjälp.** Stillbilderna talar emot. En videoarm stänger frågan.
3. **Gemensamt rum över tagningar.** Briefens rumshypotes behöver en plats i `kalla.json`.
4. **Briefen som eget steg.** Format och vem som skriver den avgörs efter experimentet.
5. **GEM-X** som alternativ kroppsläsare över tid: se `kroppsbank/GEMX-LOGG.md`.

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
