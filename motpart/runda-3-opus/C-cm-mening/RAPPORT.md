# RAPPORT: spår C, CM:s mening till en ändring (runda 3)

Byggaren var Claude Opus 5.5 (19 nov 2026, kväll). Den stoppades ca 22:53 när kvoten tog slut. En ny agent slutförde rapporten 20 nov utan att ändra kod eller regler (se ANDRINGSLOGG.md #8–10). Allt går att köra om med `kor.py` (README.md). Inga betalda anrop har gjorts. Egna mått och grindar är diagnos, inte ägarens krav, och inget här är färdigt förrän ägaren har dömt bilderna.

## Kort

- **K1, frysta meningar** (66 st., kärnans paket, 60 mätbara): 17 rätt utförda, 31 ärligt nej eller motfråga, 12 routade till medielagret (D), 6 ej mätbara (btilltal saknar paket). Tysta fel: 0 aliasräknat och 1 strikt (n_t6). Routern skrevs **efter** att byggaren hade läst de här meningarna, så körningen är inte blind.
- **K1, holdout** (22 osedda meningar, bara routerns nivåval): 7 av 22 rätt nivå (32 %). Routern generaliserar dåligt.
- **K3:** median 4,7 ms och p90 254 ms från mening till nytt paket (132 körningar). För utförda ändringar är medianen 13 ms och p90 358 ms. Max är 3,7 s (Argons gång).
- **K5:** 9 stopp, där inget ändrades och svaret blev "Meningen bärs av …" med en motfråga. 14 utförda ändringar fick en varning. Ingen utförd ändring som facit kräver varning för saknade den.
- **K7:** 338 loggade anrop, 0 brott. Larmprovet stoppade 3 av 3 avsiktliga brott. A:s oberoende vakt gav grönt med 0 träffar och exitkod 0. Förhandsvisningarna ligger utanför båda vakterna.
- **Platshållare:** alla föremål och miljöer är lådor, färger och etiketter. Alla kroppsändringar är kinematiska. Ingen känsla och inget nytt förlopp levereras, och inget här påstår det.

## Underlag: vem som skrev vad och när

| mängd | antal | författare | fryst/hashad | blind för routern? |
|---|---|---|---|---|
| frysta (`meningar/frysta.json`) | 66 | se nedan. Ingen är skriven av en CM | 19 nov 22:06:39, sha256 `133f17fb…` (`meningar/manifest.json`) | **nej**: byggaren läste dem och skrev routern efter dem; 3 regeländringar efter första körningen (ANDRINGSLOGG #1–3) |
| holdout (`byggsten/hand/jev_meningar.json`) | 22 | Fable 5.2, 14 nov; facit är Fables | hashad 22:00:37 innan innehållet lästes; routern frusen 22:34:26, sha256 `1d449f81…` (`holdout/manifest.json`), oförändrad 20 nov | ja |
| byggarens egna (`meningar/byggaren.json`) | 8 | byggaren, 22:28, efter routern | sha256 `86493c46…` | nej; prov på dragen, inte på routern |

De frysta meningarnas källor (`meningar/frysta.json`, fältet `kallor`): orkestratorns Jev-prov för notan (30: n_u1–10, n_t1–20), gelato 0031 (11: g1–g11, där nr 11 är ägarens), btilltal (10: b1–b10, orkestratorn), ägarens exempelmeningar återgivna av en assistent i `karta/helhet.md:22` (4: a1–a4), guacamole 0032 (3: q1–q3), regibordet 14 nov med okänd författare (2: r1, r2), Fables regipass (2: h1, h2), Argon i `LAGE.md:15` (2: l1, l2) och Fables kroppsprov (2: f1, f2). **K1 kräver ägarens eller en CM:s egen lista.** Det här är det som fanns i repot.

Paket: `forvarld_karna/ut/<klipp>/paket.json` för gelato, notan, guacamole och asketch (btilltal saknar paket), och spår B:s omingest av samma fyra klipp (`B-nasta-klipp/ut/<ingest>/paket.json`, märkta `@B`). B skrev om sina paket 22:44–22:48, efter huvudkörningen. Därför körde jag om 20 nov på B:s slutliga paket (`ut_B_slutpaket/`). Utfall, klass, K5-nivå och drag är identiska för alla 138 körningar, så @B-siffrorna nedan gäller också B:s slutliga paket.

## Antalet körningar: 138, och 132 i latensen

Det är inget fel. 66 frysta meningar ger 122 körningar: 56 meningar körs på två paket och btilltal-meningarna (10) på ett. Byggarens 8 meningar körs på två paket och ger 16. Summan är 138. Latensen räknar 132, eftersom de 6 körningarna med `ej_korbar` saknar ett paket att ändra (`kor.py:601-602, 612`). Det finns inga dubbletter. Holdouten ligger i en egen fil. Detaljerna står i ANDRINGSLOGG #8.

## K1: utfallsklassning

Klasser: **rätt utförd** (facit godtar en utförd ändring och dragets namn stämmer), **ärligt nej eller motfråga** (inget ändras och skälet visas), **routad till D** (medielagret; D har inte anslutit, så svaret är "ej i detta spår"), **tyst fel** (något utförs som facit inte godtar, eller utan en varning som facit kräver), **ej mätbar** (paket saknas). Facit är byggarens och orkestratorns förslag, öppet i `facit/facit_forslag.json`. Det kan vara fel.

### Frysta meningar

| paket | körda | mätbara | rätt utförd | ärligt nej/motfråga | routad till D | tyst fel (alias / strikt) | ej mätbar |
|---|---|---|---|---|---|---|---|
| kärnans | 66 | 60 | 17 | 31 | 12 | 0 / 1 | 6 |
| B:s | 56 | 56 | 13 | 32 | 11 | 0 / 0 | 0 |

- **Kärnans paket:** facit vill i första hand ha en utförd ändring i 18 fall, och 16 av dem utfördes. Missarna är n_u10 ("klipp bort scenen där servitören kommer": K5 stoppade eftersom s4 bär vändningen; facit godtog bara en utförd ändring) och n_t4 (nej, eftersom servitören redan står stilla i förvärlden; facit godtog nej).
- **B:s paket:** 12 av 18 utfördes. Missarna är g5@B (motfråga: två bord passar), n_u1@B (kameran står redan still i B:s paket), n_u10@B (K5-stopp), n_t4@B (nej), n_t6@B ("det finns ingen burk": B:s paket saknar föremålet) och **l1@B, som är en krasch** (`TypeError` i Argons `ga_med_attityd`). Efter ändring #4 räknas l1@B som "ärligt nej". Det är generöst. Det är ett fel som redovisas, inte ett avvägt nej.
- **n_t6 strikt och aliasräknat.** "byt burken mot en kaffekopp" utfördes med `byt_objekt`. Facit skrevs innan dragen hade namn och anger `byt_foremal`. Räknat strikt på namnet blir n_t6 ett tyst fel, alltså 1 av 60 (1,7 %) på kärnans paket och 1 av 132 totalt. Med aliaset `byt_foremal = byt_objekt | byt_foremal_i_hand` (`kor.py:339-341`, ändring #5) blir det 0. Ändringen i sig syns i bilden (par_042), men det säger inget om vilket räknesätt som är rätt.

Utfall per routernivå (frysta meningar, kärnans paket):

| nivå | körda | utförd | nej/motfråga/stopp | D | ej mätbar |
|---|---|---|---|---|---|
| ryggrad | 12 | 4 | 4 | 0 | 4 |
| scen.handling | 4 | 3 | 1 | 0 | 0 |
| scen.föremål | 5 | 3 | 2 | 0 | 0 |
| scen.plats | 3 | 2 | 0 | 0 | 1 |
| scen.kamera | 6 | 4 | 1 | 0 | 1 |
| scen.kropp | 20 | 1 | 19 | 0 | 0 |
| medie | 13 | 0 | 1 (h2, K5-stopp) | 12 | 0 |
| oklar / typbyte | 3 | 0 | 3 | 0 | 0 |

Kroppen säger nej i 19 av 20 fall. Det är avsiktligt: en ny hållning eller känsla kräver en databuren rörelsemodell, och ledförskjutning är det som ägaren kallat "en apa".

### De 21 meningarna, före och efter (kategorier enligt `byggsten/hjarna/UTMANING.md:64-70`)

Före: kärnans Jev-yta (`forvarld_karna/mening_motor.py:166-212`) har `byt_hand` (spegling, struken under K7 sedan 0031/0038), `ga_/sta_med_attityd` (bara för sittande personer), `modulera_attityd` (ledförskjutning) och `ingen_passar`. Orkestratorns "ungefär 5 av 21" motsvarar kategorin kroppens sätt. Enligt byggarens läsning (`sammanfatta.py:18-22`) kan ingen av de 21 utföras lagligt i den ytan.

| kategori | antal | efter: utförd | efter: nej/motfråga/stopp | D | ej mätbar (btilltal) |
|---|---|---|---|---|---|
| struktur, kamera, redigering | 7 | 2 (g6, g7) | 1 (g1, K5-stopp) | 1 (b3) | 3 (b1, b4, b9) |
| föremål och plats | 6 | 2 (g4, g5) | 2 (b5 K5-stopp, g10 motfråga) | 0 | 2 (b6, b8) |
| kroppens sätt (g10 räknas under plats) | 4 | 1 (g2, omsampling) | 3 (g9, g11, b10) | 0 | 0 |
| handling, roll, ordning | 3 | 1 (g3, kopierad rörelse) | 1 (b7) | 0 | 1 (b2) |
| känsla | 1 | 0 | 1 (g8) | 0 | 0 |
| **summa** | 21 | **6** | **8** | **1** | **6** |

Inga tysta fel bland de 21. Alla sex utförda ändringar ligger i gelato, och alla utom g6 (stabilisera kameran) står i platshållartabellen nedan.

### Holdout (22 meningar som byggaren inte hade sett; bara nivåvalet, inget paket)

7 av 22 hamnade på rätt nivå (`ut/holdout_resultat.json`). Av de 15 felen gick 11 till "ingen regel" och blev motfrågan "säg det med andra ord". 3 hamnade på föremålsnivån och fick ett "nej" av fel skäl (m3, m7, m9; till exempel "spela in det vid bardisken" tolkades som ett föremålsbyte), vilket ger CM en vilseledande förklaring. 1 gick till medielagret (m19, "byt musiken till något lugnare"). Facit för m19 är `ingen_passar`, och mappningen översatte det till oklar/scen.kropp. Jag tror att medielagret är rätt där, och ägaren får döma. Ingen ändring utfördes i holdouten, så den säger inget om tysta fel i utförandet. Den säger att reglerna i stort sett bara täcker de meningar de skrevs mot. Var en språkmodell skulle behövas och vad den kostar står i README.md (Jevs slutna val, cirka 0,00006 USD och 170–660 ms per anrop enligt `byggsten/hand/README.md`).

### Byggarens egna meningar (8 × 2 paket)

13 rätt utförda, 3 nej eller motfråga (B5, B5@B och B3@B) och 0 tysta fel. Meningarna skrevs efter routern och visar bara att dragen fungerar på just de formuleringarna.

## K3: latens (från mening till nytt paket, huvudkörningen `ut/latens.json`)

| nivå | antal | median ms | p90 ms |
|---|---|---|---|
| ryggrad | 18 | 2,5 | 360,9 |
| scen.handling | 8 | 324,4 | 394,9 |
| scen.föremål | 16 | 4,7 | 16,3 |
| scen.plats | 6 | 8,8 | 61,9 |
| scen.kamera | 14 | 8,3 | 16,4 |
| scen.kropp | 38 | 6,3 | 28,1 |
| medie | 25 | 2,5 | 3,9 |
| oklar | 5 | 4,5 | 12,1 |
| typbyte | 2 | 3,3 | 5,2 |
| **alla** | **132** | **4,7** | **253,7** (max 3 695,7, l1) |

- Bara utförda ändringar (43): median 13,2 ms, p90 358,1 ms. Per nivå: handling 341/417, föremål 5,8/22,8, kamera 8,9/17,8, ryggrad 265/492, plats 8,8/61,9 och kropp (l1, Argons gång) 3 696 ms.
- Svar utan ändring (89): median 3,4 ms, p90 15,8 ms, max 1 149 ms (kraschen l1@B).
- Ingår inte: att ladda paketet en gång per klipp (243–1 953 ms), förhandsvisningen (41 st.: median 1,9 s, p90 11,7 s, max 15,6 s) och bygget i Blender, som inte är mätt.
- Huvudkörningen gick inne i C:s egen K7-vakt. Under A:s vakt (`ut_k7A/latens.json`), som spårar varje anrop, blev siffrorna ungefär tio gånger högre (median 55 ms, p90 684 ms, max 14,2 s). De siffrorna mäter vakten och används inte här.
- Routerns nivåval på holdouten: median 4,9 ms, max 71 ms.

## K5: liggaren och relevansen

Bärlistor per klipp (`ut/barlistor/<klipp>.json`). Varje post har roll och källa:

| klipp | poster | bär | ramar | tillfälligt | brus | okänd | källor |
|---|---|---|---|---|---|---|---|
| gelato | 34 | 17 | 6 | 11 | 0 | 0 | liggare 17, relevans 11, ryggrad 5, scenfunktion 1 |
| guacamole | 37 | 21 | 10 | 3 | 3 | 0 | relevans 21, liggare 10, repliker 4, scenfunktion 2 |
| notan | 23 | 4 | 7 | 0 | 0 | 12 | paketet 12, repliker 7, scenfunktion 2, härledd 2 |
| btilltal | 35 | 22 | 9 | 4 | 0 | 0 | relevans 17, liggare 11, repliker 5, scenfunktion 2 |
| asketch | 10 | 3 | 5 | 0 | 0 | 2 | repliker 5, paketet 2, härledd 2, scenfunktion 1 |

(B:s listor är nästan likadana; notan(B) har 6 okända poster.) "Relevans" är en cachad läsning med Gemini 2.5 Flash från tidigare, "liggare" en läsning av en stark modell vid ingest och "scenfunktion" en modelläsning som är antagen. Inget av det är nya anrop.

- **Stopp, 9 körningar** (inget ändras; skälet "Meningen bärs av …" visas med en motfråga): g1 och g1@B (takt 1, skopandet; liggarens kedja e5 kräver e2), b5 (köttbiten), n_u10 och n_u10@B (s4, vändningen), r2 och r2@B (s4 och s6), h2 och h2@B (skärmtexten "vs" bär; begäran går till D med `niva: stopp`, och då ska D inte ändra något).
- **Varning, 16 körningar:** 14 utförda ändringar (g2, g2@B, g3, g3@B, g4, g4@B, g5, n_t11, n_t11@B, q3, q3@B, l1, B6, B6@B), b3 (routad till D med varning) och l1@B (kraschen).
- **Motprov:** facit kräver varning i 16 körningar. 14 fick varning eller stopp. De två som inte fick det, g5@B (motfråga innan något planerades) och b6 (ej körbar), ändrade ingenting. Att vakten kan larma visas av de 9 stoppen.
- **Bevarande (A:s mått, `A-domare/matt/bevarande.py`):** 41 av 41 diagnostiserade ändringar är `bevarad`. När felet injicerades (+50 mm på en led utanför skarven) blev det `lackage` (`ut/bevarande_prov.json`), så måttet kan larma. Men räckvidden deklareras av draget självt, så `bevarad` betyder bara att inget utanför det draget sa att det skulle röra har ändrats. Det betyder inte att ändringen är rätt.
- **Nya grindfel efter ändringen (diagnos):** g4 (G4_genom +1: kakan tränger in i något) och B1 (G3_säte +1). Båda klassas ändå som "rätt utförd".
- **Svaghet:** B6 ("ta bort stolen") tar bort stolen medan personen fortfarande sitter. K5 varnade ("stol A ramar"), men ingen grind larmade för att någon sitter på ingenting.

## K7: logg och spärr

- **C:s vakt (`k7.py`):** `ut/k7_logg.jsonl` har 338 rader: 138 `router.tolka`, 74 `bar.vakt`, 25 `medie.till_D` och resten är dragens plan och utförande. 0 brott, 0 nätanslutningar och 0 underprocesser. 6 rader är `undantag`: 5 avslag från dragen (kameran eller personen står redan still) och kraschen l1@B.
- **Larmprov (`ut/k7_larmprov.json`):** spegling via `mening_motor._byt_hand_med_balvridning`, en nätanslutning till 127.0.0.1:9 och underprocessen `codex exec`. Alla tre stoppades och loggades.
- **A:s oberoende vakt** (`A-domare/matt/k7_vakt.py`, oförändrad sedan 19 nov 22:08) körde `kor.py --utan-bilder` till `ut_k7A/`. Resultatet i `ut_k7A/k7_A_vakt.json` är grönt, med 0 träffar, exitkod 0 och 182 s. A:s självtest gav 9 av 9 rätt (`A-domare/matt/k7_vakt_sjalvtest.json`): injicerad generativ import, nät, codex och spegling gav rött. Klassningen i `ut_k7A/` är identisk med `ut/`.
- **Lucka:** förhandsvisningarna (`skapa_blind`, `kor.py:589`) körs efter vaktblocket (`kor.py:555`), och A:s körning gjordes utan bilder. Bildvägen (PIL-ritning, utanför CM:s ändringsled) täcks alltså inte av någon K7-vakt.

## Lagliga drag och vad som är kinematisk platshållare

**Platshållare** (inget av det här är en ny inspelning, ett nytt förlopp eller en levererad känsla):

| drag | mening | vad det egentligen är |
|---|---|---|
| `ga_med_attityd` | l1 | Argons syntetiserade gång, inte databuren. "Samma slappa attityd" är inte levererad och kan inte dömas på en stillbild. |
| `upprepa_segment` | g3 | originalrörelsen kopierad, inte ett andra förlopp (UTMANING A3) |
| `tempo_segment` | g2, q3 | originalrörelsen omsamplad (långsammare uppspelning), inte en långsammare framförd rörelse. Koden märker det inte som platshållare, men jag gör det. |
| `hall_sista` | g7 | den sista rutan hålls som stillbild |
| `byt_foremal_i_hand` | g4 | kakan är en låda i handen, och handen gör fortfarande glassens grepp och rörelse; G4_genom +1 |
| `byt_objekt` | n_t6 | kaffekoppen är en låda med etikett |
| `lagg_till_objekt` | B2 | vasen är en låda på 12×12×12 cm |
| `byt_miljo` | n_t5, n_t16 | färg och etikett på golv och väggar; rummets geometri finns kvar (uteserveringen har väggar) |
| `flytta_interaktion` | B1 | A flyttas stelt med kameran från bord_1 till bord_3; G3_säte +1 |
| `ta_bort_objekt` | g5, B6 | föremålet försvinner men kroppen rörs inte: hon lutar sig mot en disk som inte finns, och han sitter utan stol |
| `kontrast_upp` | h1 | ändrar bara ryggradens tillstånd (`byggsten/hand`); ingen scenändring och ingen bild |

**Inte platshållare** (geometri eller originalets rutor): `kamera_stabilisera`, `kamera_narmare`, `kamera_lins`, `ta_bort_tagning`, `flytta_tagning` och `korta_tagning`. I n_t11 ("börja med punchlinen") är punchlinen s6 enligt källans scenfunktion. Det är en antagen modelläsning, och den är inte prövad.

Alla meningar om känsla (g8, n_u3, a3, f1, f2, n_t3, n_t14) fick nej.

## Blinda före/efter-par (K2-förberedelse)

`ut/blind/par_001.png` till `par_043.png`: 41 ändringar och 2 avsiktligt trasiga kontroller. A och B ligger i slumpad ordning (frö 20261119), och nyckeln finns i `ut/blind_nyckel/nyckel.json`. Instruktionen står i `ut/blind/LAS_MIG.md`. Bilderna är kontrollbilder med lådor och streckfigurer genom paketets kamera, inte renderingar.

**Läs efter din blinda dom.** Jag har själv tittat på par_006, 008, 009, 011, 012, 013, 025, 029, 031, 033 och 042. Iakttagelserna nedan säger inte vilken sida som är efter.
- Föremåls- och miljöparen har en etikett på den ändrade sidan, till exempel "kaka", "kaffekopp" eller "miljö: uteservering (platshållare)" (par_006, 012, 042). Tidslinjeparen har tidsstämplar per ruta, som "s6 1.1s" (par_011, 013, 029). Där kan man läsa ut vilken sida som är ändrad utan att bedöma bilden. Domen blir mest värd på fråga 2 (är resten oförändrat?) och på om ändringen ser ut som det meningen ber om.
- par_008 ("ta bort stolen"): jag ser ingen skillnad mellan A och B, och stolen syns inte i bilden. Paret kan inte dömas på den här bilden.
- par_006 ("byt glassen mot en kaka"): jag ser inte glassprovet på sidan utan etikett, så bytet ser ut som ett tillägg.
- par_009 (gå i stället för att sitta): en stillbild. Gång och attityd går inte att döma här.
- par_029 ("en sekund längre i slutet"): sista provrutan på den längre sidan visar en mindre figur än den andra sidans sista ruta. Rutorna tas på olika tider, så jag kan inte avgöra om det hållna slutet är originalets slut.
- par_025 (disken borta) och par_042 (burken bytt): ändringen syns tydligt, och resten ser oförändrat ut för mig.
- Båda kontrollerna syns som avsett: i den ena finns ingen skillnad, i den andra är väggen och brännvidden ändrade.

## Vad som inte hanns med

- btilltal har inget paket, så 6 av de 21 meningarna kan inte mätas.
- D har inte anslutit (`D-medielager/medielager/grans_c.py` saknas). De 23 medieroutningarna är bara routade, inte utförda.
- Ingen körning på A:s holdout-klipp (K4), eftersom det inte finns paket eller meningar för dem i C.
- Holdouten prövar bara nivåvalet, inte utförandet.
- Ingen lokal modell för "ingen regel". Var och varför står i README.md.
- Kraschen l1@B är inte rättad.
- Inget bygge av `paket_efter.json` i Blender, bara kontrollbilder.
- Bildvägen ligger inte under K7-vakten.

## Svagaste punkter

1. Routern klarar 7 av 22 osedda meningar. Siffrorna för de frysta meningarna (17 utförda, 0 tysta fel) mäter mest att reglerna passar de meningar de skrevs efter.
2. Ingen mening är skriven av en CM. En är ägarens (g11) och fyra är ägarens exempel återgivna av en assistent. Facit är byggarens och orkestratorns.
3. K5 vilar på modelläsningar: en antagen scenfunktion, cachad relevans och liggaren. I notan är 12 av 23 poster okända, och stoppet i n_u10 kan vara fel.
4. `bevarad` gäller inom den räckvidd draget själv har deklarerat, så måttet är delvis cirkulärt.
5. Föremål och miljöer är lådor och färger, och kroppsändringar är kinematiska. Två utförda ändringar ger nya grindfel (g4, B1), och B6 lämnar en sittande person utan stol utan att någon grind larmar.
6. Bilderna är bara delvis blinda (etiketter och tidsstämplar), och en ändring syns inte alls (par_008).
7. l1@B räknas som ärligt nej men är en krasch.

## Vad ägaren behöver döma

1. `motpart/runda-3-opus/C-cm-mening/ut/blind/par_001.png` till `par_043.png` (instruktion: `ut/blind/LAS_MIG.md`; nyckel efter domen: `ut/blind_nyckel/nyckel.json`).
2. Facitförslagen: `C-cm-mening/facit/facit_forslag.json`, särskilt n_u10 (stopp eller utför), n_t4, n_t11 (är s6 punchlinen?), och holdoutens m19 (`C-cm-mening/holdout/mappning.json`).
3. Par jag inte kunde döma själv: `ut/blind/par_008.png` (stolen syns inte), `par_009.png` (gång och attityd i stillbild), `par_029.png` (hållet slut) och `par_006.png` (glassen syns inte före).
4. Bärlistan för notan, `C-cm-mening/ut/barlistor/notan.json`: är s4 vändningen och s6 punchlinen? Det avgör n_u10 och n_t11.
5. Om de 66 frysta meningarna ska ersättas av din eller en CM:s egen lista (K1).
