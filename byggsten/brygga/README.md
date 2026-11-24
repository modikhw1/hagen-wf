# brygga: från kedjans läsning till en scen som går att lita på

Sedan 14 nov 2026. Byggsten under `byggsten/`.

## Mandat
Ägaren, 14 nov:
> "det är ok att ändra vår nuvarande pipe för hur data sammanställs för att skapa en dataingest som kan anpassa och återskapa en content enligt våra övergripande mål. Var vågad."

Bryggan tar därför över **sammanställningen**. Kedjan i `scen/3d/` läser fortfarande originalet: kropp, kamera, rum och mening. Bryggan avgör hur läsningen sätts ihop till en scen, mäter den mot grindar och bygger den på valfri värd.

Kedjan rörs inte härifrån. Det som visar sig bättre här blir förslag till kedjan.

## Principen
```
ORIGINALET ──(kedjan läser)──► deklaration · plan · källa · kroppar     sanning för det som syns
                                         │
                               samla.py  ▼  egna regler, varje beslut med orsak
                                   scenpaket/1                           ett självständigt paket
                                         │
                             grindar.py  ▼  G1–G7, mätta, inte bedömda för ögat
                                    rapport                              rött = bygg inte vidare
                                         │
                            emit_bpy.py  ▼  ett och samma bpy-skript
                         ┌───────────────┴───────────────┐
                 lokal Blender 5.2                   3D Jutsu (Blender 5.2)
             full data, ingen tokenkostnad      inbäddad data, versioner, editor
                         └───────────────┬───────────────┘
                                kor.py   ▼  original ovanför, bygge under
                                   jämförelse                            ögat sist, inte först
```

## Kör
```bash
scen/.venv/Scripts/python.exe byggsten/brygga/kor.py notan --film      # allt: samla, grindar, bygg lokalt, jämför
scen/.venv/Scripts/python.exe byggsten/brygga/kor.py notan --jutsu     # skriver även ut/notan/jutsu_bygg.py
scen/.venv/Scripts/python.exe byggsten/brygga/emit_bpy.py byggsten/brygga/ut/notan/paket.json --jutsu --jutsu-steg 0   # utan kroppar
```
Utdata hamnar i `ut/<klipp>/`:
- `paket.json` och `paket_ra.json` (utan bryggans regler, alltså som kedjan sammanställer i dag)
- `GRINDAR.md`
- `lokal/` med kontrollbilder, `animatik.mp4` och `scen.blend`
- `jamforelse.png`
- `original_mot_brygga.mp4`
- `tider.json`

Ett nytt klipp läggs in i `KLIPP` i `kor.py` med plan, källa, deklaration och video.

## Vad bryggan valde, och varför
Utgångspunkten är granskningen (`byggsten/jutsu/AUDIT-AVSTAND.md`) och felet med blocken (`byggsten/jutsu/BUGG-BLOCK.md`). Det som gör återskapningen pålitlig behålls, och det som visat sig opålitligt sammanställs om.

| del | val | skäl |
|---|---|---|
| Kroppen | **behålls** ur kedjan: `kontrakt/trohet.ruta()`, alltså samma leder som kedjans Blender | Kedjans bildtrohet är redan god: bbox-IoU 0,93–0,995 i alla sju tagningar (G7). Ingen anledning att läsa om. |
| Kameran | **behålls**: planens `renderkamera`, men **en kamera per tagning** i stället för en kamera med klipp | En kamera per tagning är både Blenders markörer och Jutsus shots. Statiska tagningar får en nyckel i stället för 73. |
| Rummets geometri | **behålls**: planens lyfta möbler (`mobellyft`, `foremallyft`) | Mätt mot bildrutor. |
| Rummens giltighet | **sammanställs om**: R1 och R2 ur deklarationen | Kedjan läste aldrig `galler_tagningar` (BUGG-BLOCK.md). Det är den enskilt största källan till fel i bild. |
| Personers plats per tagning | **sammanställs om**: planens ankare, och annars deklarationens `kameror.<S>.person_plats` | Planen hade inget ankare för B i S7. |
| Kopior per tagning | **slås ihop** när läget skiljer högst 3 mm | 84 lådor blev 37, utan förlust. |
| Mening | repliker i rutor, roller, rumsrelationer, handling, relevans och liggarreferens följer med | Scenen bär sin mening (`hagen_*`), så att en regi senare kan peka på den. |
| Proveniens | sha256 för plan, källa och deklaration, och varje regel som tillämpades med orsak | Paketet går att spåra och köra om. |
| Generativt | **inget** | Grundregeln och "generativt bara för 1:1". Bryggan bygger bara det som är läst eller deklarerat. |

### Reglerna
- **R1, rum per tagning:** ett rums objekt syns bara i rummets tagningar. Huvudrummets objekt (det rum som täcker flest rutor) står kvar i övriga tagningar. Det motsvarar deklarationens "A och bord_1 står kvar".
- **R2, hemplatsen ledig:** en persons hemplats (vanligaste ankaret) syns inte i tagningar där personen sitter någon annanstans. I notan blir `stol_B` borta i S7.
- **Tagningens ankare:** saknar planen ankare tas `person_plats` ur deklarationen.

Reglerna är allmänna. Varje klipp med ett berättat och ett avslöjat rum, eller en person som byter plats, faller under dem.

## scenpaket/1
| fält | innehåll |
|---|---|
| `klipp`, `tidsbas`, `bild` | id, video, fps, antal rutor (rutor är sanning, intervall [a, b)), upplösning, sensor |
| `rum[]` | id, tagningar, intervall, platser, status, beskrivning, regel; `huvudrum` |
| `objekt[]` | id, bas, typ, pos, rot, mått, färg, status, **rum**, **synlig_ut** (lista av intervall) |
| `tagningar[]` | id, intervall, personer med ankare, kamera (`statisk`, nycklar `[ruta, x, y, z, qw, qx, qy, qz, lins]`) |
| `personer{}` | roll, färg, hemplats |
| `leder`, `rorelse{}` | ledset (`docka` 18, `bal` 25, `alla` 120), rutsteg, per person och tagning rutor med leder i heltal mm i världen |
| `mening` | repliker (rutor), skärmtext, roller, relevans, handling, liggare, rumsrelationer |
| `trohet{}` | kedjans bildtrohet per tagning och person |
| `beslut[]`, `regler`, `proveniens` | varje tillämpad regel med orsak; källfiler med sha256 |

Notan: 106 KB med full upplösning (30 fps, 18 leder).

## Grindarna
Mätta på paketet, före bygget. Tröskelvärdena är egna diagnosgränser och inga krav från ägaren.

| grind | mäter | gräns |
|---|---|---|
| G1 rum | varje synligt objekt hör till ett rum som gäller tagningen; hemplatsen är ledig | inga fel |
| G2 golv | fötternas median-z | ≥ golv − 5 cm |
| G3 säte | sittande bäcken över sitsens ovansida | 2–20 cm |
| G4 genom | andel rutor där en led ligger inne i en möbel (sitsen undantagen för bäcken och lår) | ≤ 10 % |
| G5 i bild | andel av överkroppens leder inom bilden | ≥ 70 % |
| G6 skymning | möbler närmare kameran som täcker överkroppen | ≤ 30 % |
| G7 trohet | kedjans egen mätning av kroppen genom renderkameran mot originalets 2D-leder | inte flaggad |

## Utfall på notan (14 nov)
| | kedjans sammanställning (`paket_ra`) | bryggan (`paket`) |
|---|---|---|
| G1 rum | **7 av 7 tagningar fel** (bord_2 och stol_B_avslojad i S1–S6, stol_B i S7) | 0 fel |
| G2 golv | S7: B:s fötter −0,25 m | samma (läsfel i kroppen, se nedan) |
| G3–G7 | ok | ok |

- **Lokalt:** hela flödet tog cirka 47 s, varav samla 5 s, grindar 0,4 s och Blender 36 s med 7 kontrollbilder och film i 30 fps. Själva scenbygget tog 0,9 s.
- **I Jutsu:** samma skript utan kroppar tog 2,4 s (projekt `byggsten-brygga-notan`, id `7661a0ff-8008-4a37-96ea-d89f95788306`). Sju kameror och sju shots i `blockingStudioTimeline`, och markörerna byter kamera per tagning. Jutsus körning satte `hf_id` på alla objekt redan vid sparandet.
  - När scenen hade öppnats i webbgränssnittet (revision 4) låg **alla sju shots kvar**, mappade till våra kameror, utan någon egen kamerarigg från editorn. Det skiljer sig från test 03, där en kamera med klipp blev ett enda shot.
  - Kropparna lades till som en egen revision (`emit_bpy.py --jutsu --bara-kroppar`, 10 fps, 3,6 s), revision 5. Kontrollbilder: `ut/notan/jutsu/`.
- **Bild:** `ut/notan/jamforelse.png` och `ut/notan/original_mot_brygga.mp4`. Blocken är borta. S2 och S5 har inget bord bakom B, och S7 har en fri mitt med B vid sitt eget bord.

**G2 i S7 rättas medvetet inte.** Bäckenet ligger rätt över sitsen (G3 ok, 10 cm), men benen är lästa genom golvet. Att lyfta kroppen skulle sätta bäckenet 25 cm över sitsen. Felet sitter i benens pose och ska rättas vid läsningen, till exempel med kontakt-IK mot golvet. Det ska inte maskeras här.


## Kroppar: T0 och T1 (14 nov)
| | T0, docka | T1, armatur (standard) |
|---|---|---|
| leder | 18 punkter | 28 punkter, varav `huvud_upp` och `nasa_mal` räknas ur huvudets MHR-rotation och `*_hand_mitt` ur index och lillfinger |
| styrning | positioner, cylindrarna sträcks | en armatur med 26 ben och **fasta benlängder** (median ur läsningen), riktad mot lederna och **bakad till rotationsnycklar** |
| riktning | ingen | huvudet (MHR-rotationen, näsan visar blicken), händerna (handflatan mot pekfingret), bäckenet (mot vänster höft), bröstet (mot vänster axel) |
| kontakt | ingen | R3 fotkontakt: en fot under golvet lyfts till fotledshöjd och knät räknas om med fasta längder; bäckenet flyttas inte |
| kropp | cylindrar och sfär | kapslar per ben, handflator, fötter, huvud och näsa, parentade till benen |
| GLB | punkter med begränsningar | **riktig skelettanimation** (3 skins, 3 animationer, rotationskanaler); kan läsas av andra verktyg |
| data i Jutsu | 36 KB (10 fps) | 30 KB med gallring 15 mm (85 av 383 rutor; `--jutsu-tol 15`) |
| tid i Jutsu | 3,6 s | 2,2 s |

**Varför MHR-rotationen för huvudet:** ögonpunkterna gav fel riktning för A (huvudbenet nästan parallellt med nacken). Huvudledens egen rotation stämde för alla: ansiktet mot kameran, cosinus 0,90–1,00 mot kamerariktningen, som i originalet.

**Kvar i T1:**
- B i s7 har knäna i möblerna efter fotkontakten (G4 17 %), eftersom benen i s7 är dåligt lästa.
- Fingrar och grepp finns inte, och underarmens vridning följer inte med.
- Kroppen är inte MHR:s form. T2, med MHR-kroppen lokalt via `mhr_rig.py`, är nästa nivå.

## Vad som fortfarande saknas för pålitlig återskapning (i ordning)
1. **Föremålen som bär meningen.** Notan själv, burgarna, burken och muggarna finns inte i planen. Deklarationens `relevans` listar dem. Nästa steg för bryggan är att föra in dem som `objekt` med rum och synlighet. Läget kommer ur kedjans föremålslyft där det finns, och annars ur bildrutan mot tagningens kamera.
2. **Rummets skal där kameran tittar.** S4 (servitören) har inga väggar, och bakväggen är platt där originalet har fönster. Deklarationen behöver väggar per riktning, eller så får bryggan härleda ett skal ur kamerornas synfält.
3. **Riktiga kroppar på den lokala värden.** Kedjans `ingest/mhr_rig.py` bygger MHR-kroppen i Blender. Lokalt kan bryggan använda den i stället för dockor. I Jutsu går det inte förrän en egen rigg kan importeras.
4. **Benen genom golvet** (G2) ska rättas vid läsningen, inte här.
5. **Blicken.** Huvudet är en sfär. Lederna `c_head`, `l_eye` och `r_eye` (ledsetet `bal`) ger riktningen.
6. **Fler klipp.** Guacamole, b-tilltal och gelato läggs in i `KLIPP` och körs genom samma grindar. Först då vet vi att reglerna är allmänna.

## Förslag till kedjan
Det som fungerar här och bör flyttas in, enligt PIPE-regeln "bygg allmänt":
- **R1 och R2** i `deklaration_till_hand.py` och kompilatorn, så att `synlig_ut` följer rummen (BUGG-BLOCK.md).
- **G1, G2 och G4** som kontroll efter kompileringen, bredvid `trohet.py`.
- **En kamera per tagning** i planen, i stället för en kamera med klipp.

## Filer
| fil | vad |
|---|---|
| `samla.py` | kedjans utdata → `scenpaket/1`, med R1, R2 och ankare ur deklarationen; `--utan-regler` ger kedjans sammanställning för jämförelse |
| `grindar.py` | G1–G7 på ett eller flera paket, med tabell i markdown |
| `emit_bpy.py` | paket → bpy-skript för lokal värd (läser fil) eller Jutsu (inbäddat, gallrat) |
| `kor.py` | hela flödet för ett klipp, med jämförelse mot originalet |
| `rotation.py` | matris och kvaternion |
