# Prov 03: lokalitet/1, allmän rumsingest (21–22 nov 2026)

Agentens granskning, **ingen ägardom ännu**. Visning: `http://127.0.0.1:5206` (välj klipp). L = GPU-observationer, L-snabb = CPU-varianten, båda med samma kod på alla klipp och utan manuell inmatning.

## Vad som är allmänt och fungerar

**Kamera, lutning, höjd och skala.** Reglerna L1–L4 i `lokalitet.py` utan klamp och schablon:
- Due Piani har kamerahöjd 1,37–1,62 m i alla tagningar med person, och fötterna står på golvet (fotkontakt). Lodlinjen varierar ≤3° mellan nyckelrutor i 11 av 12 tagningar.
- Bilderna ovanifrån får brant vinkel utan handkartläggning: Due Piani S2 −60°, S8 −50°, S10 −51°; 08burgerkebab S4 −65°; babasburgers S2/S4/S6 −44 till −57°. Ögonhöjdsbilderna ligger på −10 till −17°.
- Två allmänna fel hittades och rättades i min egen kod: blandad brännvidd mellan MoGe och kropp (gav skala 1,5–2 och svävande fötter) och för breda matröster.
- Fysisk prior (uttalad): kameran tittar inte uppåt mer än 20°. Den räddar S8 och babasburgers S2, där segmenteraren kallar pannan och brickan "vägg".

**Tid (INFRA-kontraktet).** GPU-observationer (MoGe-2 ViT-L + OneFormer Swin-L) för 5 klipp och 84 rutor tog 107 s väggtid, varav 28 s modell-laddning, och 0,7 s per ruta. `lokalitet.py` tar 5–25 s per klipp. Ett nytt klipp blir bedömbart på cirka 2–3 min. Regeländringar ger ny bild på sekunder. Kostnaden är uppskattad till cirka 0,1 USD och inte verifierad mot fakturan. Engångsinstallationen (image, vikter) tog cirka 5 min. CPU-vägen tog 11 s per ruta och är avvecklad till förmån för kvalitet.

## Vad som inte bär ännu

- **Rummet som bild:** väggskivor, lådor och brickor är grova och svårlästa, särskilt i hold-out-klippen. Segmenteraren tappar i närbilder (pannan blir "vägg", brickan blir för stor för att räknas som kärl).
- **Lodlinjen i babasburgers S1** blir −46°, fast originalet är cirka −25°. Diagnosen fångar det (32–34° spridning mellan nyckelrutorna), men valet rättas inte ännu.
- **Kroppar:** hold-out-klippen saknar kroppsspår, eftersom ingen SAM3D körts. Spanjorskans kroppar från ingest_v2 är fel (små och långt bort).

## Steg 1 genomfört: instanser som texturerade 3D-bitar (22 nov)

Kolumnen "L · texturerade instanser" på 5206. `lokalitet.py` → `bygg_nat`: varje OneFormer-instans i tagningens mittruta blir ett eget nät ur MoGe-djupet, i samma världsram som kameror och kroppar. Ytan är originalets pixlar (projektiv textur). Standard är den levande originalvideon, eftersom kameran står still per tagning; omrörning och hällning lever därför på ytorna. En fryst nyckelruta finns som val.

- **Separata bitar:** 2–32 per tagning, med etikett, grupp och mittpunkt i `nat.json`. Trianglar över djupsprång tas bort. Trianglar över instansgränser med kontinuerligt djup tillhör majoritetsinstansen, så att inga sprickor uppstår.
- **Bakom personer:** observerad bakgrund hämtas ur andra nyckelrutor (statisk kamera ger samma pixelstråle) och får textur ur just den ruta där den syntes. Det som aldrig syns fylls från omgivningen, blir neutralt grått och märks som antaget. Personens pixlar målas aldrig på väggen.
- **Granskning:** fri kamera (orbit runt bitarnas mittpunkt) och färg per bit. Kontrollerat i bild för köket i Due Piani S4, S8, S10, S11 och babasburgers S1/S4. Djupet syns från sidan; burken står upp från brickan.
- **Generalisering:** alla fem klippen, samma kod. Tid: 5–25 s per klipp utöver GPU-observationen.
- **Begränsningar:** etiketterna kan vara fel trots rätt geometri (pannan i S8 heter "vägg"). Kanterna är taggiga (rutnät med steg 3 i halv upplösning). Grått syns där kroppsmodellen inte täcker personen; det är ett ärligt mått på kroppens passform.
- **Rättat på vägen:** renderarens orbit-läge rekurserar i oändlighet (ändringshändelse → omritning → update → ändringshändelse). Skyddet ligger i experimentappen; den delade renderaren är orörd.

## Steg 2 genomfört: kroppar för hold-out-klippen (22 nov)

`modal_kropp.py` återanvänder ingest_v2:s app och SAM 3D Body utan att köra dess hårdkodade `main()` och skriver bara till `ut/<klipp>/ingest_v2/`. Tre klipp kördes parallellt: 08burgerkebab (11 tagningar, 73 SAM3D-anrop), babasburgers (11 tagningar, 75 anrop) och kennysgelato2.0 (1 tagning, 27 anrop). GPU-tiden var 24–73 s per klipp, uppskattat 0,04 USD sammanlagt och inte fakturaverifierat. Väggtiden var 447 s, mest kallstart och kö. 2D-poserna för dem tog 50–105 s lokalt. Därefter kördes observationerna om med ingest_v2:s tagningsgränser: 67 s för 69 rutor.

- **INFRA-händelse:** L4-kön blockerade ett anrop i över 10 min (containrar i läget "Pending"). Den lokala processen stoppades och de kvarhängande apparna stoppades med `modal app stop`, så att inget startade senare. `modal_obs.py` har nu en reservlista: L4, A10G, L40S, A100-40GB.
- **Utfall 08burgerkebab:** kamerans 2D-fel sjönk från 97–232 px till 15–31 px i 8 av 11 tagningar. Kamerahöjden är 1,54–1,67 m och fötterna står på golvet. Flerpersonstagningarna S4 och S8 håller inte (89 och 142 px; S8 ger 2,8 m kamerahöjd).
- **Utfall babasburgers:** den sittande mannen syns vid bordet i det texturerade rummet. Fotkontakten gäller inte sittande, så skalan tas från personytan. S1 får nu −14° (förut −46°) med de nya tagningsgränserna.
- **Brister i kroppsingesten (ej lokaliteten):** kennysgelato2.0 (en liggande person blir fyra trasiga spår) och identitetsdubbletter som ligger längre isär än 0,6 m.

## Steg 3 genomfört: andra lodlinjevittne och fusion (22 nov)

GeoCalib (pinhole, Apache-2.0) är inbyggt i `modal_obs.py` (obs_gpu/2). Det ger tyngdkraft, roll och pitch, fokal och osäkerheter per nyckelruta. Alla fem klipp kördes om på 104 s väggtid, inklusive omkörd image.

**Vittnena jämförda (stående bål som skiljedomare):**
- Due Pianis ögonhöjdsbilder: bålen stämmer med GeoCalib inom 1–3°, men med MoGe-lodlinjen bara inom 5–7°. MoGe-vägen var cirka 5° för brant.
- Bilder ovanifrån: GeoCalib stannar vid 34–40°, medan MoGe säger 50–65° och den handkartlagda ellipsen 72° (S8). GeoCalib ger upp i Due Piani S10 (±18°).

**Regel L1b (`fusera_lodlinje`):** vittnena viktas med 1/σ².
- MoGe: σ = medianspridningen mellan nyckelrutorna, minst 3°.
- GeoCalib: egen σ, gånger 4 över 20° lutning.
- Stående bål: 6°.

Ett vittne som avviker mer än 2,5σ stryks i en omgång. Varje tagning redovisar vittnen, σ, avvikelse och om vittnet strukits (✗ i panelen och i `lokalitet.json`).

**Utfall:**
- Due Pianis ögonhöjdsbilder ligger på −7 till −13°, med bålen inom 1–4°.
- Bilderna ovanifrån ligger på −49 till −65°.
- GeoCalib stryks i Due Piani S10, bålen i S2. babasburgers S1 ligger på −12° (först −46°).

**Två följdregler på vägen:**
- Golvhöjd kräver minst 0,5 % golvpixlar.
- Segment under 0,75 i OneFormer-poäng röstar inte (S8:s "golv" hade 0,52–0,63, riktiga golv 0,95–0,99).

S8 och S10 redovisar därför "antagen 1,40 m" i stället för en falsk höjd. Spanjorskan S3 tar höjden från fötterna (1,49 m) i stället för ett felläst golv (0,76 m).

**Kvar:**
- Flerpersonstagningar (08burgerkebab S4/S8: 1,9 och 2,8 m) bär inte.
- Två bordsbilder ovanifrån i babasburgers får 0,5–0,6 m ur golvsegment med hög poäng, troligen felmärkta. Det är oprövat.

## Steg 4 genomfört: rum över tagningar (22 nov)

Regel L7 (`rum_over_tagningar`):
1. SIFT mellan tagningarnas mittrutor. Personerna maskas och textlisten i överkant tas bort.
2. Fundamentalmatris med MAGSAC.
3. De matchade pixlarnas 3D-punkter i båda tagningarnas världsram (lodlinjen är redan gemensam) passas med en stel transform med bara gir och förflyttning, via RANSAC (tröskel 10 cm). Därefter förfinas transformen.
4. En kant godtas vid minst 20 inliers och minst 25 % andel. Grupperna byggs som ett spännande träd från starkaste kanten. Kameror, kroppar och lådobjekt flyttas in i Python, näten via `transform` i manifestet.

Panelen har läget "Visa hela rummet". Antagna fyllnader visas bara i sin egen tagning.

| Klipp | Rum (utan facit) | Restfel mellan tagningar |
|---|---|---|
| Due Piani | köket {S4, S5, S6, S7, S9}, entrén {S1, S3}, bänken {S11, S12}; S2, S8 och S10 (närbilder) egna | 1,6–5,8 cm, 53–95 % inliers |
| 08burgerkebab | {S5, S6, S7}, {S1, S3} | 2,4–6,2 cm |
| babasburgers | {S1, S5, S8}, {S10, S11} | 1,3–3,8 cm |
| Spanjorskan, kennysgelato2.0 | inga par (3 respektive 1 tagning) | – |

Grupperna stämmer med vad som syns i originalen. Närbilderna (pannan, tallriken) knyts inte till köket, eftersom vyn skiljer sig för mycket för SIFT. Det är en känd lucka. En väg att pröva är att matcha mot texturerade bitar i stället för hela bilder.

**Rättat på vägen:** den antagna fyllnaden bakom personer fyllde världskoordinater och gav vilda skärvor från andra vinklar. Nu fylls bara djupet med normaliserad faltning, och punkten läggs på pixelns stråle. Ytan blir slät och ligger på väggen bakom personen.

## Motprov (Codex gpt-6-astra xhigh, 21 nov 05:04–05:20) och vad det ändrade

Fullständigt i `ut/codex/MOTPROV.md`, med kommandon, bildbevis och hashkontroll av att källfilerna är orörda.

| Påstående | Status | Konsekvens |
|---|---|---|
| Ingen klippspecifik kod | står | Oredovisade priorer finns i `ut/codex/KONSTANTER.md`: bänk 0,90 m, sula 0,08 m, rullningsgräns 35°, startkamera 1,38 m, reservhöjd 1,40 m, uppåtprior 20°. |
| Determinism (babasburgers två gånger) | står | Identisk SHA256. |
| Lodlinje mot oberoende flyktpunkt (handvalda regioner) | delvis | 24 av 38 tagningar mätbara, ingen avvikelse över 10° (median 1,8°, max 7,6°). 14 saknar vittne. |
| Spridning mellan nyckelrutor som tillförlitlighetsmått | **fallit** | En gemensam bias på 30° ger 0° spridning. Spridningen används nu bara som MoGe-vittnets σ, aldrig som dom. |
| Fotkontakt som belägg | **fallit** | Kontakten är byggd in i skalan (fötter på 0,08 m per konstruktion). Den är ett villkor, inte ett belägg. Jämförelsen med personytans skala blir signal i stället. |

**Infört efter motprovet:**
- **Flyktpunktsvittne** (`vittne_vp.py`): Codex linjeanpassning, men regionerna väljs automatiskt ur OneFormers säkra arkitektursegment och personer maskas. Vittnet hålls utanför fusionen. Det kan mätas i 18 av 38 tagningar, med median 1,2° avvikelse.
- **L8 tillförlitlighetsdom** per tagning, bara ur oberoende signaler: flyktpunkt, kamerans restfel mot 2D-led, höjd enligt fotkontakt mot personyta, rimlig höjd, vittnesenighet. Domen är hög, medel, konflikt, låg eller okänd. Utfallet för fem klipp: 18 hög, 3 medel, 4 konflikt, 4 låg, 9 okänd (mest bilder ovanifrån utan oberoende vittne). Domen visas i panelen per tagning.
- **Permanenta grindar** (`test_grindar.py`): flyktpunktens självtest, 15° felinjektion (larm 17/17), gemensam 30° bias (larm 17/17, där spridningen ger 0) och att fotkontakt aldrig räknas som stöd.
- **Kroppsdubbletter (L3b):** samma person avgörs av projicerad 2D-överlappning (median-IoU över 0,4), inte av 0,6 m i 3D. Dubbletter skiljer sig ofta i djup.
- **Spår utan 2D-stöd (L3c):** fel över 3 gånger det bästa och över 120 px märks som antagna (cyan). De påverkar varken skala, lodlinje eller höjd. Exempel: babasburgers S1 B/C, kennysgelato B–E och Due Piani S1 B (person bakom glas, ej borttagen).
- **Närbilder och rum:** LoFTR (kornia, prov i scratchpad) ger 0–3 korrespondenser mellan S2/S8/S10 och rumstagningarna, och SIFT ger 0. Innehållet delar för lite synlig yta, så närbilderna förblir egna ramar. Det är ett belagt besked, inte en gissad placering.

## L9: kamerarörelse inom tagningen (05:30)

Codex hittade kamerarörelse i tagningar som ingesten kallar statiska. Den nya signalen jämför första och sista nyckelrutan på icke-person-ytor (SIFT, homografi med MAGSAC) och mäter rotation (K⁻¹HK) och bildförflyttning:
- stöd: högst 3° och högst 3 %;
- svag: högst 8° och högst 10 %;
- fel: mer än så.

Om matchningen misslyckas räknas det som tecken på rörelse (svag). Inliers koncentrerade till under 35 % av bilden räknas inte, eftersom de kan vara textöverlägg (kennysgelato S1: 0 % förflyttning från texten, fast vyn rör sig). Alla tre fall Codex hittade (08burgerkebab S8, Spanjorskan S1, kennysgelato S1) får signalen. En tagning med tecken på rörelse får högst domen medel.

**Dom för 38 tagningar:** 7 hög, 15 medel, 5 konflikt, 7 låg, 4 okänd. Medel dominerar eftersom handhållen kamera rör sig 3–8° eller några procent inom tagningarna. Statisk kamera per tagning är alltså en approximation som nu syns per tagning. `test_grindar.py` passerar 4/4.

## Status för listan

Steg 1–4 är genomförda och verifierade i bild på de fem klippen. Codex-motprovet är kört och dess fynd är inarbetade (se ovan). Kvar som kända brister: flerpersonstagningar med dålig kroppsingest (08burgerkebab S4/S8, kennysgelato), kamerarörelse inom tagningar som ingesten kallar statiska (Codex: 08burgerkebab S8, Spanjorskan S1, kennysgelato S1) samt att bilder ovanifrån saknar oberoende vittne. Alla tre är synliga per tagning i L8-domen.

## Efter fönsterbytet (22 nov 12–13)

- **L9b, kamerans rotation inom tagningen:** rotation per nyckelruta ur homografin mot mittrutan, med `R_k = R·B·R_relᵀ·B`. Nycklarna interpoleras med slerp. Kropparna placeras med rotationen i varje ruta (projektionen bevaras). Rummet byggs ur mittrutan med rätt rotation för övriga rutor. Rörliga tagningar får fryst textur. 15 av 38 tagningar modelleras med 1,5–14°. Gruppbindningen L7 transformerar alla nycklar.
- **Rättat fel:** videorouten `/media/<klipp>` fångade `/media/ruta/...`, så frysta texturer gav alltid 404. Det förklarar de tidigare mörka "spökena" bakom personer.
- **Bakom person:** en cell från en annan ruta räknas som observerad bakgrund bara om den ligger minst 15 % djupare än personen i mittrutan. Det skyddar mot missar i personmasken.
- **Fart (INFRA):** bildvittnen (flyktpunkt, rotation, L7-pixelpar) cachas per ruta och fokal. Axelsökningen är vektoriserad och söker på ett fast urval av 6 000 normaler. Stödytornas egna normaler blir alltid kandidater, eftersom urvalet annars kunde tappa ett litet golv (Due Piani S4/S7 föll 14° innan rättningen). En regelkörning tar 6–20 s per klipp. Resultaten är stabila mot 20 000-baslinjen utom i bilder ovanifrån (3–5°, som redan har domen okänd eller medel).
- **Dom nu, 38 tagningar:** {'hög': 10, 'låg': 4, 'konflikt': 5, 'medel': 18, 'okänd': 1}. `test_grindar.py` passerar 4/4.
- **L3d, personceller ur kroppen:** OneFormer märkte ibland en del av personen som något annat (babasburgers S1: tröjan målades på rummet). Nu räknas också celler som ligger inom den registrerade kroppens projicerade siluett (skelettets ben som tjocka linjer, bål 0,30 m, lemmar 0,10–0,16 m, huvud 0,22 m) och inom 0,25 m från kroppens djup som person. Ett första försök med kroppens ruta tog även brickor och kartong framför personen och förkastades. Det som hålls tätt intill kroppen kan maskas. Därför visar texturkolumnen rätter som följer händerna som objekt.
- **Dom nu:** {'hög': 10, 'låg': 4, 'konflikt': 5, 'medel': 18, 'okänd': 1}.

## kropp/2: personer per tagning (22 nov 13)

`modal_kropp2.py` ersätter ingest_v2 som kroppskälla:
- **Spår per tagning:** posedetektionerna (yolo11n-pose) kopplas ihop ruta för ruta med IoU. Spår under 30 % av tagningen och mycket små personer tas bort. Det finns ingen global utseendeidentitet, som gav dubbletter och fantomer.
- **SAM3D:** körs var femte ruta per spår, alla personer i en ruta i ett anrop. Fokalen är MoGe-L, samma som lokalitetens. Lederna blir kamerakoordinater, utan golvflytt, och utjämnas med PCHIP.
- **Utdata:** ett A-kompatibelt paket (`ut/<k>/kropp2/paket.json`), så att lokalitetens kedja fungerar oförändrad.
- **Körning:** ingest_v2:s image och viktvolym återanvänds, men bara SAM3D laddas (12 s). Fem klipp tog 104 s väggtid.

**Utfall:**
- Ett spår per synlig person: Due Piani har en person per helbild och inga fantomkroppar i närbilderna S2, S8 och S10.
- 2D-fel redan före registrering är 13–47 px, mot 100–270 px med ingest_v2.
- 08burgerkebab S8 går från 142 till 39 px, och kamerahöjden från 2,8 till 1,60 m. Inga spår saknar stöd.
- **Dom:** {'hög': 13, 'okänd': 2, 'konflikt': 3, 'medel': 17, 'låg': 3} (före kropp/2: 10 hög, 18 medel, 5 konflikt, 4 låg, 1 okänd).

## Vittnen för bilder ovanifrån: två prov, båda negativa (22 nov 13)

- **Tallriksellips** (`vittne_ellips.py`, självtest godkänt). Vilande runda kärl ger elevationen ur axelkvoten. 0 av 11 bilder ovanifrån godkänns. Kärlen skärs nästan alltid av bildkanten, och masken är en ring under maten. Att släppa spärrarna för delbågar gav fel tidigare (Due Piani S10:449) och vore en genväg.
- **Stödplanets två flyktpunkter** (`vittne_plan.py`, självtest godkänt för −30, −50 och −70°). Planets normal räknas ur två kantfamiljer. Det stämmer i ögonhöjdsbilder med bord (babasburgers S5, S8 och S11: −13,6, −16,9 och −9,3° mot L −14,2, −15,4 och −10,5°, i linje med flyktpunktsvittnet). Ovanifrån är det opålitligt: positiva värden och −21° för en bild som tydligt är 55–60°. Matkanter och tryckt text på brickpappret förorenar linjefamiljerna, och flyktpunkterna ligger nära oändligheten.
- **Slutsats:** inget av dem kopplas in. Branta bilder ovanifrån saknar ett pålitligt oberoende vittne med dagens verktyg, och domen "okänd" eller "medel" där är korrekt, inte en brist i domen. Ett möjligt nästa prov är ett vittne ur kontakt: tallrik och händer på bänken ger skala och plan via kroppen.

**Oberoende visuell granskning:** Gemini 4 Neon xhigh via agy, uppdrag `AGY_GRANSKNING.md`, svar i `ut/agy/GRANSKNING.md`.

## Gemini-granskning runda 1 (agy, gemini-4-neon-xhigh, 12:53–13:02) och åtgärder

Hela granskningen ligger i `ut/agy/GRANSKNING.md`. Kameran stämmer i 37 av 38 tagningar (08burgerkebab S8 är rörelseoskarp). Fem återkommande fel, ordnade efter hur mycket de hindrar iscensättning:
1. Grå hål.
2. Föremål i händerna ersätts av generiska brickor eller raderas.
3. Personer i svåra poser (liggande, gäster i bakgrunden).
4. Svarta trappstegsskarvar.
5. Inbrända undertexter.

**Fynd om L8:** domen sa "hög" i 9 av 13 fall med tydliga bildfel, eftersom den mätte geometri men inte bildtrohet.

**Åtgärder (allmänna):**
- **Föremål inom personens siluett behåller sin textur:** mat, kärl, flaskor och lådor maskas inte bort som person. De generiska ersättningsbrickorna har tagits bort ur texturkolumnen.
- **Bakgrundsduk:** originalets pixlar ligger 40 m bakom scenen i kamerans synfält. Från originalkameran syns originalet genom skarvar och hål; grå antagen fyllnad visas bara i fri kamera.
- **Ny L8-signal, bildtäckning:** andelen observerad textur från originalkameran (≥95 % stöd, ≥85 % svag, annars fel).
- **Undertexter:** ingest_v2:s OCR klassade all text som "overlag", och stilfälten var konstanta. Ny klassning mätt på materialet: vågrätt centrerad (0,50 ± 0,06), minst 20 % bred och med ljus fyllning är undertext. Den skiljer "pa babas?", "SAFTIG HOGREV" och "du ta gyroskött" från Coca-Cola, BABAS-papper och skyltar. Undertextceller behandlas som hål: de fylls ur andra rutor eller blir antagna. Från originalkameran syns texten fortfarande, via duken, som i originalet.

**Dom nu:** {'konflikt': 26, 'låg': 3, 'hög': 4, 'okänd': 1, 'medel': 4}. Runda 2 granskar läget efter dessa åtgärder (`AGY_GRANSKNING_R2.md`, `ut/agy/runda2/`).

## Gemini-granskning runda 2 (13:06–13:16) och åtgärder

Hela granskningen ligger i `ut/agy/runda2/GRANSKNING.md`. 34 av 38 tagningar ser renare ut från originalkameran (3 lika, 1 sämre). Gemini varnar uttryckligen:
- **Bakgrundsduken döljer** att 14–41 % av bilden saknar 3D-geometri bakom personer.
- Duken skapar **spöksiluetter**: originalpersonen syns runt dockan.
- **Dockornas händer och ben** kolliderar med mat och kartonger.
- **L8 med bildtäckning** lyfte personlösa närbilder till "hög" och fällde 25 av 26 persontagningar.

**Åtgärder:**
- **Bildtäckning mäts på icke-personytor** (personens yta täcks av kroppen). Den är nu ett kvalitetstak (≥92 % tak hög, ≥80 % tak medel, annars tak låg) och aldrig ett geometriskt stöd. "Hög" kräver minst två geometriska stöd. Täckningen ligger på 84–100 %, median 96 %.
- **kropp/2:** en stor beskuren person (minst 15 % av bilden) godtas med minst 2 säkra leder, och den minsta personytan sänks till 0,25 %. Due Piani S2 får nu en kropp.
- **L3e, kroppsdelar utan stöd:** överkropp och underkropp vars projektion avviker mer än 60 px från originalets 2D-leder, eller som syns i mindre än 30 % av rutorna, märks som antagna och visas som cyanspöken. Det gäller 9 tagningar, alla underkroppar hos beskurna eller sittande personer. Exempel: S2:s ben, som SAM3D gissade framför tallriken.
- **Kvar:** spöksiluetter från duken (avvägning: utan duk syns grå hål, med duk syns originalpersonen runt dockan). Kollisioner mellan docka och föremål. Liggande personer (kennysgelato). Sedel-klistermärket, som inte är centrerat och därför inte klassas som undertext.
- **Dom nu:** {'hög': 13, 'medel': 18, 'konflikt': 3, 'okänd': 1, 'låg': 3}. `test_grindar.py` passerar 4/4.

## L2c: händer mot föremål (22 nov 13:45)

Kroppens djup är fritt längs kamerans strålar, eftersom projektionen inte ändras. Den närmaste MoGe-ytan i en ring runt varje hand (kärl, mat, bord, bänk, spis; 20:e percentilen av djupet) är ytan handen rör. Ligger händerna bakom den ytan i mer än 10 % av proven flyttas kroppen till median-kvoten, om det minskar kollisionerna och fötterna inte lämnar golvet mer än 0,15 m. Annars redovisas konflikten.

- **babasburgers S5 och S8** (sittande vid bordet): händerna låg bakom brickan i 60 % av proven. Kroppen flyttades 14–18 % närmare, och kollisionerna gick till 0 %.
- **Stående personer** har händerna framför närmaste yta (k 1,0–1,6) och lämnas orörda.
- **Due Piani S6/S7** har konflikt: handkontakten vill flytta kroppen, men fötterna skulle lämna golvet med mer än 0,15 m. Det redovisas.
- **Ny L8-signal, händer mot föremål** (≤10 % stöd, ≤30 % svag, annars fel).
- **Begränsning:** dockan är kapslar och bitarna är tunna 2,5D-ytor. Visuell genomskärning kan därför kvarstå även när djupet stämmer.

**Dom nu:** {'hög': 12, 'medel': 15, 'konflikt': 8, 'okänd': 1, 'låg': 2}.

## Rumshjärna/1: genererat rum som hypotes bakom personen (21 nov 14–15)

Detaljer finns i `rumshjarna/RUMSHJARNA.md`.

- Varianterna V1 (stiliserad), V2 (borttagning) och V3 (essens) prövades på Due Piani. Bara V2 håller. V1 försämrar lodlinjen. V3 ger en rimlig rangordning, men den är ingen sanning.
- `rumshjarna/hjarna.py` tar en bild per tagning med behov, ankare per L7-grupp och återkoppling mot ankaret. Bilden registreras tillbaka till sitt utsnitt och observeras på Modal.
- Grinden i `lokalitet.py` (regel 1b) kräver djupfel ≤ 12 %, kanttrohet ≥ 0,4 och lyckad linjering. 26 av 30 släpps igenom på 5 klipp. Observationer går alltid före hypotesen. Genererade bitar räknas inte som observerad täckning.
- Två allmänna fel rättades på vägen. Den svävande "slangen" i Due Piani S4 var en ring av antagen fyllnad kring personkanten. Kantpixlar framför hypotesen blir hål.
- A/B (`LOKALITET_UTAN_GENFYLL=1`): de grå siluetterna ersätts av rum i alla tre provade klipp.
- Körningen tog cirka 17 min för 5 klipp och cirka 0,6 % av Codex 5h-kvot per bild. Grindarna i `test_grindar.py` håller.
- Utseende länkar aldrig rum (`likhet.py`), eftersom DINO ger 0,94 för matnärbilder från olika vinklar.
- agy: Opus 5.5 high bygger väljaren (`AGY_VALJARE.md`). Neon xhigh granskar de 30 bilderna mot grinden (`AGY_V2_GRANSKNING.md`).

## Facit, pipeutvärdering och hold-out (21 nov 16–17)

- Visuellt facit för 0.0 (Gemini, 38 tagningar, `ut/agy/facit00/FACIT.md`): 6 god nog, 11 delvis, 21 inte god nog. Objekt och rum brister nästan överallt. L8 "hög" är god nog i bara 3 av 10.
- Pipeutvärdering (Codex med webbsökning, `ut/codex/pipeval/PIPEVAL.md`): behåll MoGe, GeoCalib och SAM 3D Body. Byt till struktur (plan, lådor, kärl), SAM 3.1-segmentering och anpassning av kontakt. Kontrollera licenserna.
- Hold-out på 3 nya klipp (`HOLDOUT.md`): grind 1b håller (0 oanvändbara släppta på 54 tagningar). Väljaren håller inte (överanpassad). 0.0 är inte god nog på nya klipp heller: 0 ja, 2 delvis, 14 nej.

## Nästa steg mot en allmän 0.0 (i ordning)

1. ~~Kamerans rotation inom tagningen (L9b)~~ genomfört; se ovan. ~~Personceller ur kropp och djup (L3d)~~ genomfört. Rotation per nyckelruta ur homografin på statisk bakgrund blir kameranycklar. Kropparna motroteras per ruta så att projektionen bevaras och de står stilla i rummet. Rummet förblir fast. Fryst textur per nyckelruta.
2. ~~Flerpersonstagningar via kropp/2~~ genomfört; se ovan.
3. **Närbilder:** semantisk koppling (panna på spis, tallrik på bänk) som hypotes med osäkerhet, märkt som antagen. Ingen visuell överlappning finns.

## Tidigare förslag (genomförda som steg 1–4)

1. **Instanser som texturerade 3D-bitar:** varje OneFormer-instans (bänk, tallrik, vägg, panna) blir ett eget nät ur MoGe-djupet med originalets pixlar som textur. Rummet blir troget originalet sett genom kameran, och varje bit förblir ett separat, flyttbart objekt för regibordet. Lådor och mått behålls som redigerbart lager.
2. **Kroppar för hold-out-klippen:** ingest_v2:s SAM3D på Modal, så att 0.0 alltid innehåller personerna.
3. **Ett andra lodlinjevittne** (t.ex. GeoCalib) där MoGe-normalerna sprider sig mer än 5° mellan rutorna.
4. **Rum över tagningar:** tagningar på samma plats (Due Piani S4–S7 och S9) slås ihop i en gemensam ram.
