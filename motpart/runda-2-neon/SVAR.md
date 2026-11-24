# Motpart runda 2 (Neon) — Granskning av Claude runda 1 och förregistrerat steg mot K1–K8

**Datum:** 19 nov 2026  
**Roll & katalog:** Neon (efter instruktionen `Du är Neon` över `adv.txt` och regeln `motpart/runda-<n>-<källa>/` i `motpart/PROTOKOLL.md:9`).  
**Rörda filer utanför denna mapp:** 0. Inget i `forvarld_karna/`, `byggsten/`, `scen/`, `motpart/runda-1-claude/`, `LAGE.md` eller `CLAUDE.md` är ändrat. All kod och data ligger här med prefixen `metod_`, `svar_` och `steg_`.  
**Ägarmandat utanför repot:** **Inget mandat.** Varken jag (Neon) eller någon dokumenterad logg för Argon har muntligt eller chattbaserat ägarbesked utanför repot som godkänner `forvarld_karna/` som aktiv kärna, Seedance som slutsteg efter CM:s ändringar eller spegling. Ägaren är domare; allt nedan är mätningar och förslag.

---

## Översiktstabell: samtliga påståenden (Runda 0 + Claude runda 1) → dom → körbart bevis

| id | påstående | dom (Neon) | bärande bevis (kört i runda 2) |
|---|---|---|---|
| **A1** | `X_RA_2D` är självprojektion, inte videons 2D | **medger** | `scen_brygga.py:371-374`; omkörning av `g7_oberoende.mat_paket` ger 21/21 rader med 0 diffar (`metod_g7_holdout_och_loco.py`) |
| **A1b** | Argons G7 blind för efterbehandling (0/67) | **medger** | `grindar.py:120-121` läser enbart lagrad `paket["trohet"]` |
| **A1c** | `grindar.mat` mäter bara sista personen i tvåpersonstagningar | **medger** | `grindar.py:83-133`; rättat i kopian `steg_scen_brygga.py` |
| **G7-ober.** | Slutpaketen har 2D-fel i 11/21; `G7-oberoende` ger 67/67 och 32/32 | **delvis** | Medger 11/21 (+1/11 på hold-out `b-tilltal`) och att `0,5 m`-injektioner larmar 30/30 på `b-tilltal`. **Bestrider** generalitetsanspråket i "32/32": bara **2 av 4** klipp ingår i de 10 rena originalen (`guacamole` 0, `gelato` 0), LOCO `asketch→notan` missar 1/5 djupfel (`0,0358` mot tröskel `0,0370`), YOLO-bara fångar bara **17/30** på `b-tilltal` (5/10 huk, 2/10 djup), och SAM-2D har **prompt-IoU = 1,000 (0,0 px median)** mot YOLO över 2 029 rutor (`metod_g7_holdout_och_loco.py`, `metod_yolo_oberoende.py`) |
| **G7 Orsak 1** | `kappa` skalar hela bål-translationen och drar kroppen mot bildmitten | **medger** | Bekräftat analytiskt via pinhole-perspektiv och på hold-out `b-tilltal s5:C` (`bal_skift_mat 0,1138 = bal_skift_kappa 0,1139`, `svar_c3_och_btilltal.py`) |
| **G7 Orsak 2 / P1–P4** | `0,92 m`-klämning sänker kroppen; patch P1–P4 löser 2D utan kända bakslag | **delvis / bestrider P2** | Medger klämningens 2D-effekt i nuvarande kod. **Bestrider P1–P4 som kontrollerad lösning:** Claude kontrollerade bara Argons blinda `G1–G6` (`G7.md:198`). Med Claudes **egen H-serie** ökar felen i `guacamole` (`8→9`, 2 nya `H5_ibild`), `notan` får nytt `H1_objekt` (`s5:B bord_2:dold`), och **P2 utan pitch-återställning sätter kameran under bordsskivan** i både `notan s7` (`0,624 m` mot bord `0,720 m`, `−9,6 cm`) och `gelato s1` (`0,711 m` mot disk `0,720 m`, `−0,9 cm`) (`metod_patch_p1_p4_3d.py`, `svar_c3_och_btilltal.py`) |
| **A2** | R25 ger "0 px" som identitet och flyttar gående person till kamera | **medger** | `scen_brygga.py:389-390`; R25 slår felaktigt till på stilla kameror (`asketch S1/S7`, `notan S7`, `btilltal s10`). **Bestrider** att Claudes R25c håller på verklig rörlig video (se `C1`) |
| **A3** | G3/G4 = 0 fel beror på tautologisk stol + `_dra_in` + R1-döljning | **medger** | `scen_brygga.py:141-174, 480, 548-596`; verifierat via `grind_harda.py` |
| **A3.1–A3.5** | En rad/tagning; G7 blind; G1 konstant; R3 maskerar G2; z-skift hamnar i kameran | **medger** | `grind_harda.py`, `metod_grind_mutation_audit.py` |
| **A3.6 / H-serien** | H-serien mäter baslinjens fel och ersätter G1–G7 pålitligt | **delvis** | Medger att baslinjen har verkliga fel som G1–G7 missar. **Bestrider** att H-serien är kalibrerad/felfri: 48–52 % av målen kastas som `F` i `H3_hallning`/`H4_genom`/`H10_kamera`; `H7_2d` missar `b-tilltal s5:C` (`0,127` bildhöjd → `ok: True, 0,978`) men falskmissar 12–21 % av perfekta 0-px nativa rutor (`gelato s1`, `asketch s5/s7`); `H12` faller `21/21→0/21` vid mjuk sänkning; `H15` faller `21/21→1/21` vid 45°-vridning; `H14` är blind `0/21` mot uppströms SAM-djupfel (`metod_grind_mutation_audit.py`, `metod_yolo_oberoende.py`) |
| **A4** | Visuellt granskad i Blender stämmer inte (`jamforelse.png` har svåra fel) | **medger** | Bekräftat visuellt i `mening_overlagg_{guacamole,gelato,notan,asketch}.png` (huk, dolda bord, spökkroppar, nedtryckt B i `notan S7`). **Bestrider** att Claudes rubrik är reproducerbar: V mot A har bara **58,4 %** exakt träff (`κ = 0,370`), på `H` **42,9 %** (`κ = 0,200`) och på `K` **37,5 %** (`κ = 0,012`, slumpnivå!) (`metod_mening_rubrik_latens.py`) |
| **L4-a** | `AttitydProfil` drar med kamerapitch och slår om vid 5 mm brus | **medger** | `mening_motor.py:61-127` (inkl. stavfelet `"c_ spine3"`). **Bestrider** Claudes lösning `C3` |
| **L4-b** | `ga_med_attityd` byter etikett i 2/3 tagningar och glider i stödfas | **medger** | `mening_motor.py:330-338`, `mening_render_ga_sida.png` |
| **L4-c** | `byt_hand` saknar bålvridning, flyttar målet 0,62 m, använder struken spegling | **medger** | `mening_motor.py:345-373`, `mening_render_byt_hand.png` |
| **L4-d** | `< 50 ms` i kod och `< 250 ms` med Jev saknar mätning; Claude mätte 531–684 ms | **delvis** | Medger att `< 50 ms` faller på oförändrad kod och att Jev saknas. **Bestrider** `531–684 ms`: uppmätt på belastad maskin (4,3–4,5× uppblåst). I varm process på ledig dator (50 körningar) tar oförändrad `manipulera_scen` **`152,8 ms`** (`guacamole`) och **`123,1 ms`** (`gelato`) — väl under ägarens `< 1 s`-nivå (`metod_mening_rubrik_latens.py`) |
| **C1** | R25c klarar 2 cm / 2,3 px och flaggar brott mot antaganden vid `PnP-andel < 0,9` | **bestrider** | På verkliga `gelato S1` faller R25c på Claudes egen gräns (`PnP-andel = 0,73`), ger `36,3 px` median / `234,1 px` max reprojektionsfel, `0,323 m` enkelrutshopp och `0,506 m` båldrift på stillastående expedit. På digital zoom `1,6×` hallucinerar R25c `2,235 m` kamera (`132,5 px` fel) och på 60 % rörlig bakgrund `127,2 px` fel — i båda fallen förblir `PnP-andel = 1,000` (ej flaggad!) (`metod_r25c_verklig.py`, `metod_r25c_gelato_s1.png`) |
| **C2** | Pitch-bortfallet förklarar största delen av `gelato S1`:s utsnittsfel (IoU > 0,26) | **delvis** | Kört exakt motprov: IoU i `gelato S1` stiger `0,264→0,363` (`G7_led 0,123→0,037`) och i `notan S7` `0,158→0,398` (`G7_led 0,112→0,003`, `kam_z 1,238 m`). Men C2 ensamt försämrar `notan S2` (`0,036→0,077`) och `notan S4 person_4` (`0,008→0,033`) tills `kappa` och `idx_p>0` också åtgärdas (`metod_r25c_verklig.py`) |
| **C3** | Lutning mot gravitation i kameraram varierar `< 3°` mellan tagningar | **bestrider** | **Faller på båda källorna:** `varld.npz["upp"]` är **cirkulär** (`ingest_klipp.py:263` beräknar den som `mean(nacke - rot)` = personens egen ryggrad!) och ger spann `15,2°` (`guacamole A`) och `16,2°` (`guacamole B`); mot `MoGe-u` bryter **8/10** flertagningspersoner gränsen `3°` (t.ex. `guacamole A 9,2°`, `gelato A 10,5°`, `asketch B 11,6°`, `btilltal C 9,8°`) (`svar_c3_och_btilltal.py`) |
| **C4** | Fotlåsning ger stödfotsfart `< 0,05 m/s` utan att ändra CM:s 2D-bild | **delvis (oprövat)** | Geometriskt rimlig förbättring för procedurgång, men procedurgång bör inte ersätta ägarens öppna beslut om databuren rörelsemodell (`BESLUT-LICENS.md`) |
| **A5** | Verifierat utan `deklaration.json` på alla 4 klipp | **delvis** | Medger att lagrade `obs.json`/`notan/recept.json` var äldre än `obs_motor.py` (22:40/22:43 mot 00:59) och att `notan 2,85 m` inte återskapas (ger `3,53 m`); medger att geometrisk reserv faller på 5/5. Står att dagens kod ger byte-identisk `obs.json` med/utan `--utan-deklaration` (`metod_syfte_och_rum_audit.py`) |
| **A6** | Ingen klippspecifik kod | **medger (faller)** | `regler.py:61` `"bonaqua": 3.5`; `obs_motor.py:439-458` ger `a-dialog-kafe-tagningar` a-sketchs semantik och `bonotanical-tagningar` notans (`metod_syfte_och_rum_audit.py`) |
| **R1–R9** | RUM.md:s sakfynd (ej reproducerbara 6.1-siffror, inget facit 3,3 m, R6 oimplementerad `farg_signatur=null`, degenererad `asketch` 2,5×2,5 m, splittrad `b-tilltal`, svag geometrisk re-ID) | **medger** | Verifierat: `farg_signatur = 0/49` icke-null; `asketch` `2,499×2,499 m`, `A↔B 0,482 m`; `b-tilltal` splittrar disken i 4 bord (`metod_syfte_och_rum_audit.py`, `metod_g7_holdout_och_loco.py`) |
| **SYFTE A1–A15** | 15 syftesavvikelser i `LAGE.md` och `CLAUDE.md` | **medger huvuddelen; delvis på källmetod, A5 & A13** | Samtliga grep-motprov i `SYFTE.md` verifierades (`metod_syfte_och_rum_audit.py`): inget ägarmandat för kärnan, omvänd generativ AI-regel (13 nov), tappat manus i `LAGE.md`, struken spegling, saknad liggare/essens/medielager. **Metodkritik:** **9 av 15** avvikelser (16 filer) vilar på Claudes privata andrahandskällor (`~/.claude/.../memory/`, ej i repot); `UTMANING.md:64-70` summerar till **22**, inte 21; `malbild.md:7` och `AUDIT-AVSTAND.md:77` nyanserar A3/A4 |

---

## Del 1. Angrepp på Claudes metod (kört bevis per spår)

### 1.1 `G7.md`: Selektionsbias i "32/32", LOCO-brott och otestat hold-out (`b-tilltal`)
Skript: [metod_g7_holdout_och_loco.py](metod_g7_holdout_och_loco.py), data: [metod_g7_holdout_och_loco.json](metod_g7_holdout_och_loco.json), bild: [metod_btilltal_overlagg.png](metod_btilltal_overlagg.png).

1. **Omkörning:** `g7_oberoende.mat_paket` på de 4 klippen reproducerar Claudes `g7_resultat.json` exakt (`21/21` rader, `0` diffar).
2. **Selektionsbias i "32/32 och 0/10":** I `G7.md:154-169` filtrerar Claude ned kalibreringen till de 10 original som inte larmar. Dessa 10 rader kommer från **enbart 2 av 4 klipp**: `asketch` (`5` rader) och `notan` (`5` rader) — **`0` rader från `guacamole` och `0` från `gelato`**.
3. **Leave-One-Clip-Out (LOCO):** När G7a-tröskeln väljs som mittpunkt mellan högsta träningsoriginal och lägsta träningsinjektion på ett klipp i taget:
   - Träning `notan` → test `asketch`: tröskel `0,0257`, `0/5` FP, `0/15` FN.
   - Träning `asketch` → test `notan`: tröskel `0,0370` (mellan `0,0152` och `0,0587`), vilket **missar `notan s4:C` djupinjektion (`0,0358`, `1/5` djupmiss)**.
4. **Känslighet för realistiska fel (< 0,50 m):** På samma 10 rena rader vid mindre djupfel sjunker G7-oberoende snabbt: `0,10 m → 1/10`, `0,15 m → 2/10`, `0,20 m → 4/10`, `0,25 m → 7/10`, och **YOLO-bara (`G7b–e`) ger `0/10` på samtliga djupfel från `0,10` till `0,50 m`**.
5. **Hold-out på `b-tilltal` (11 osedda tagningar):** Claude hade redan `obs.json` och `recept.json` för `b-tilltal` i `rum_ut/med_dekl/btilltal/`, men skrev i `GRINDAR-MUTATION.md:238` att *"Ett hold-out-klipp saknas"* och prövade aldrig `G7-oberoende` eller `H-serien` på det. När vi kompilerar `b-tilltal` genom oförändrad `scen_brygga.py`:
   - `G7-oberoende` ger `10/11` OK och hittar `s5:C` (`led_med = 0,1272`, `i_mask = 0,571`, orsakat av `kappa`: `bal_skift_mat 0,1138 = bal_skift_kappa 0,1139`).
   - På 30 felinjektioner i de 10 rena `b-tilltal`-tagningarna larmar `G7-oberoende` **30/30** (vilket vi medger talar för tröskeln `0,03` vid stora `0,5 m`-fel), **men de starka YOLO-delarna (`G7b–e`) fångar bara `17/30` (`57 %`)**: sidled `10/10`, **huk bara `5/10`**, **djup bara `2/10`**.

### 1.2 Oberoendet i "oberoende 2D-sanning" (SAM-2D + YOLO)
Skript: [metod_yolo_oberoende.py](metod_yolo_oberoende.py), data: [metod_yolo_oberoende.json](metod_yolo_oberoende.json), bildbevis: [metod_yolo_fel.png](metod_yolo_fel.png).

1. **SAM-2D och YOLO är inte oberoende källor:** Över **2 029 rutor** i samtliga 5 klipp jämfördes `kropp/<spår>/<ruta>.npz → bbox` (SAM:s prompt) med YOLO:s `personer.json`. Median-IoU är **`1,0000`**, median maxavvikelse **`0,000 px`** och p90 **`0,000 px`**. SAM är alltså bokstavligen promptad med YOLO:s ruta på >90 % av rutorna.
2. **Union-masken `masker.npy` är kontaminerad av andra personer i 13 av 32 spår:** T.ex. `guacamole s4` (`109/109`), `gelato s1` (`46/156`), `asketch s5` (`30/83`, kocken i rött i bakgrunden), `asketch s7` (`18/64`, förbipasserande utanför fönstret) — och i `b-tilltal s9` detekterar YOLO till och med **ansiktsfotot på vågens skärm** som personmask (syns i [metod_btilltal_overlagg.png](metod_btilltal_overlagg.png)).
3. **YOLO-fel fäller perfekta 0-px nativa projektioner:** När vi testar det **nativa SAM-skelettet** (0 px fel från `scen_brygga`) mot Claudes regler över alla 32 spår:
   - `guacamole s4:A`: `nativ_i_mask = 0,622` (YOLO-masken missar A:s huvud och axlar, se panel 1 i [metod_yolo_fel.png](metod_yolo_fel.png)) — räddas bara av Claudes efterhandstillagda `ref_giltig = 0,90`.
   - **`H7_2d` (huvud i övre halvan av YOLO-rutan) missar 12–21 % av perfekta 0-px-rutor** när personen lutar sig fram över en disk: `gelato s1:A` **`87,7 %`**, `asketch s5:B` **`80,7 %`**, `asketch s7:A` **`79,0 %`** (farligt nära gränsen `70 %`). I [metod_yolo_fel.png](metod_yolo_fel.png) (panel 2 och 5) syns den röda `c_head`-cirkeln mitt på personens ansikte — **under** den orangea mittlinjen.

### 1.3 Patch P1–P4 (`G7.md`): Kontrollerad med Argons blinda grindar och sätter kameran under bordet
Skript: [metod_patch_p1_p4_3d.py](metod_patch_p1_p4_3d.py), data: [metod_patch_p1_p4_3d.json](metod_patch_p1_p4_3d.json).

I `G7.md:198` skriver Claude: *"Här är bara grindsummorna kontrollerade: G1–G4 och G6 = 0 fel i alla fyra klipp med patchen."* Det är alltså Argons egna blinda G-grindar som Claude just underkänt i `GRINDAR-MUTATION.md`! När vi i stället kör **Claudes egen H-serie** och 3D-geometrimätning på P1–P4:

| klipp | H-fel före → efter P1–P4 | nya H-fel skapade av P1–P4 | 3D-konsekvenser |
|---|---|---|---|
| `guacamole` | `8 → 9` (**värre!**) | `+2` (`s2:B H5_ibild=0.0`, `s4:A H5_ibild=0.0`) | `A↔B` i `s4` ökar `1,290 → 1,666 m` (`+37,6 cm`); `s4:A` flyttas `0,274 m` i XY (förklarat av att Argons `kappa` krympte `x,y`, men avslöjar att `H5_ibild` falskfäller sanna 1:1-kantklipp!) |
| `gelato` | `5 → 4` | `0` | **P2 sätter `CAM_s1` på `0,711 m` — `0,9 cm` under glassdiskens överyta (`0,720 m`)** |
| `asketch` | `17 → 17` | `0` | Ingen 3D-förbättring |
| `notan` | `18 → 15` | `+1` (`s5:B H1_objekt: bord_2:dold`) | **P2 sätter `CAM_s7` på `0,624 m` — `9,6 cm` UNDER bordsskivan `bord_1` (`0,720 m`, `0,58 m` bort)!** |

P1 (`[1, 1, f_px/f_sam]`) är visserligen matematiskt riktig för pinhole-fokalbyte, **men P2 behandlar symtomet i stället för orsaken**: orsaken till att `notan S7` och `gelato S1` slog i `0,92 m` var bortkastad kamerapitch i `scen_brygga.py:254`. Återställs pitch landar `notan S7` på sanna `1,238 m` (över bordet!) med `led_med = 0,0030` (`metod_r25c_verklig.py`).

### 1.4 `MENING.md`: Rubrikens bristande reproducerbarhet och 4,5× uppblåst latens
Skript: [metod_mening_rubrik_latens.py](metod_mening_rubrik_latens.py), data: [metod_mening_rubrik_latens.json](metod_mening_rubrik_latens.json).

1. **Visuell rubrik (V mot A i `MENING.md:44-67`):** Mellan Claudes **egen** visuella bedömning (`V`) och Claudes **egen** automatiska rubrik (`A`) är överensstämmelsen låg:
   - **Totalt:** `45/77` (`58,4 %`), Cohens $\kappa = 0,370$ (4 tvåstegsmotsägelser `0` mot `2`).
   - **`H` (hållning):** `9/21` (`42,9 %`), $\kappa = 0,200$. Tre tvåstegsmotsägelser (`gelato S2`, `asketch S3`: `A=2, V=0`; `notan S7`: `A=0, V=2` — Claude godkänner B:s hållning i `notan S7` med `V=2` fast benen är i huk bakom bordet, men ger `V=1` för samma sak i `notan S1/S3/S5/S6`).
   - **`K` (kontakt):** `6/16` (`37,5 %`), **$\kappa = 0,012$ (slumpnivå!)**. `mening_rubrik.py:193` kollar nämligen inte `synlig_ut`, så i **7 tagningar** där `M_auto = 0` (bordet saknas i bild!) delar `K_auto` ändå ut `1` eller `2` (`guacamole S4 A`: `M=0, K_auto=2, K_visuell=0`).
   - **`M` (möbel):** `12/19` (`63,2 %`), $\kappa = 0,387$. Claude bryter sin egen "svävande skiva > 0,25 m"-regel i `notan S1/S3/S5/S6` (`A=1`, men sätter `V=2`).
   - Endast **`U` (utsnitt)** håller rimlig samstämmighet (`18/21 = 85,7 %`, $\kappa = 0,771$).

2. **Varm-process-latens (50 varma körningar på ledig maskin mot Claudes belastade dator):**

| steg (`mening_motor.py` oförändrad) | Claude `guacamole` (belastad) | **Neon `guacamole` (varm, ledig)** | Claude `gelato` (belastad) | **Neon `gelato` (varm, ledig)** |
|---|---:|---:|---:|---:|
| `copy.deepcopy(paket)` | `104 ms` | **`16,7 ms`** (6,2× lägre) | `33 ms` | **`11,0 ms`** |
| `extrahera_attitydprofil` | `49 ms` | **`7,4 ms`** (6,6× lägre) | `7 ms` | **`3,5 ms`** |
| `grindar.mat` | `45 ms` | **`6,5 ms`** (6,9× lägre) | `7 ms` | **`3,9 ms`** |
| **`manipulera_scen` totalt (median)** | **`683,8 ms`** (max `1603`) | **`152,8 ms`** (min `114,6`, p90 `249,4`) | **`530,8 ms`** (max `951`) | **`123,1 ms`** (min `101,6`, p90 `172,0`) |
| Selektiv kopia + cachad profil (utan `_dra_in`/grindar) | – | **`92,2 ms`** | – | **`106,4 ms`** |

Argons gamla påstående `< 50 ms` faller fortfarande på oförändrad kod (p.g.a. ren Python-loop i `_dra_in` `52–61 ms` och listserialisering `51 ms`), **men Claudes rubriksiffra `531–684 ms` var 4,3–4,5× uppblåst av parallella agenter**. Faktisk varm latens (`123–153 ms`) ligger väl under ägarens `< 1 s`-nivå (`forvarld-underlag.md:39`).

### 1.5 R25c på verklig rörlig kamera (`gelato S1`) + motprov `C1`, `C2` och `C3`
Skript: [metod_r25c_verklig.py](metod_r25c_verklig.py), [svar_c3_och_btilltal.py](svar_c3_och_btilltal.py), bild: [metod_r25c_gelato_s1.png](metod_r25c_gelato_s1.png).

1. **R25c brister på verkliga rörliga tagningar:**
   - **`gelato S1`:** `andel_rutor_med_pnp = 0,73` — **under Claudes egen föreslagna grind `0,90` (`MENING.md:119`), en siffra som utelämnades i tabellen `MENING.md:104`!** Framåt-bakåt-verifierade bakgrundspunkter från ruta 0 (`fb_err < 1 px`) får **`36,3 px` median, `184,8 px` p90 och `234,1 px` max reprojektionsfel** (långt från syntetikens `2,3 px`), kameran teleporterar **`0,323 m` på en enda ruta** (total banlängd `4,91 m`), och den stillastående expediten får `bal_span_3d_m = 0,506 m` bl.a. p.g.a. blandning av okalibrerad MoGe-translation (`f_moge = 1920`) och SAM-bål (`f_paket = 1523`).
   - **`asketch S4/S5` och `b-tilltal S5`:** enkelrutshopp på `0,383 m` (`asketch S4`), `0,195 m` (`asketch S5`, `bal_span 1,655 m` på stillastående expedit!) och `0,523 m` (`btilltal S5`).
2. **Claudes eget motprov `C1` fäller R25c:s föreslagna grind:**
   - **Digital zoom `1,6×` (stilla kamera, `0,00 m`):** R25c hallucinerar **`2,235 m`** kamerarörelse (`132,5 px` rumsfel), men `PnP-andel = 1,000` (inlier-kvot sjunker till `0,36`) → **ej flaggad av `PnP-andel < 0,9`**!
   - **60 % rörlig bakgrund (stilla kamera):** `127,2 px` rumsfel, men `PnP-andel = 1,000` → **ej flaggad**! (På sidotruck `1,2 m` och 30–45 % rörlig bakgrund håller däremot R25c inom `1,5 cm` / `6 px`.)
3. **Claudes eget motprov `C3` faller fullständigt:** `MENING.md:143` föreslår att mäta rygglutning mot `varld.npz["upp"]` eller MoGe-golvnormalen för `< 3°` spann mellan tagningar. Men `scen/3d/ingest/ingest_klipp.py:263` definierar `varld.npz["upp"]` som **`mean(nacke - rot)` = personens egen ryggrad** (cirkulärt — plattar ut enpersonstagningar till ~4° och hoppar till `19,4°/20,0°` i tvåpersonstagningen `guacamole S4`, spann `15,2°/16,2°`). Mot `MoGe-u` spricker gränsen `3°` på **8 av 10** flertagningspersoner (`guacamole A 9,2°`, `gelato A 10,5°`, `asketch B 11,6°`, `notan B 8,7°`, `btilltal C 9,8°`).

### 1.6 `GRINDAR-MUTATION.md`: Nämnarkrympning (`F`), skräddarsydda stegfunktioner och H-seriens luckor
Skript: [metod_grind_mutation_audit.py](metod_grind_mutation_audit.py), data: [metod_grind_mutation_audit.json](metod_grind_mutation_audit.json).

1. **Nämnarkrympning (`F`):** I H-serien stryks **14,0 % (`586/4185`, läge a)** respektive **14,6 % (`623/4260`, läge b)** av cellerna som `F` (redan fel på baslinjen) — över hälften i `H3_hallning` (`11/21 = 52,4 %`), `H10_kamera` (`11/21 = 52,4 %`) och `H4_genom` (`10/21 = 47,6 %`).
2. **Realistiska/mjuka felklasser mot H-serien:**
   - **Mjuk partiell sänkning** (10-rutors cosinus-ramp före mittrutan i stället för Claudes oändliga 1-ruteshopp i `sank_04_delvis`): **`H12_kontinuitet` kollapsar från `21/21 → 0/21`!** (H2 fångar dock fortfarande `19/19`, så `någon H = 21/21`.)
   - **45°-vridning** (i stället för 180°): **`H15_vridning` faller `21/21 → 1/21` (`någon H = 3/21`)**, eftersom `vridning_min_deg = 60°` anpassades efter baslinjens värsta fel (`37°`).
   - **Mjuk 25 cm sidleddrift** (i stället för 1,5 m teleportering): `H12 = 0/21`, `H7 = 0/19`, `H9 = 0/21`, `någon H = 3/21`.
   - **Uppströms korrelerat SAM-djupfel `+0,45 m`** (före `obs_motor`): **`H14_djup = 0/21` och `H7_2d = 0/19`** (8/21 spår, inkl. samtliga kollisionsfria stående, går helt oupptäckta av H-serien).
3. **Hold-out `b-tilltal` visar direkt lucka i `H7_2d` och `H1/H4`-konflikt:** `H7_2d` ger `ok: True (0,978)` på `b-tilltal s5:C` trots `G7-oberoende = 0,1272` (`FEL`). Samtidigt ger `H1_objekt = 0` trots 6 `R1_kollisionsskydd`, medan `H4_genom = 6` larmar mot de 4 splittrade borden i tagningar där receptet inte ens observerat dem.

### 1.7 `SYFTE.md` och `RUM.md`: Källgranskning
Skript: [metod_syfte_och_rum_audit.py](metod_syfte_och_rum_audit.py), data: [metod_syfte_och_rum_audit.json](metod_syfte_och_rum_audit.json).

- **Vad som håller i `SYFTE.md` och `RUM.md` (medges fullt):** Våra egna omkörda grep-motprov bekräftar 100 % av Claudes filkontroller (`ägare` = 0 i `LAGE/ARKITEKTUR/CLAUDE`; `manus` = 0 i `LAGE` och kärnkoden; `liggare` = 0; `essens/K1` = 0; `skärmtext/montage/ljud` = 0; `0042` saknar svar; `farg_signatur = 0/49`; `asketch` `2,50×2,50 m`; namnprovet ger fel semantik för `a-dialog-kafe-tagningar` och `bonotanical-tagningar`).
- **Metodkritik mot `SYFTE.md`:**
  1. **Icke-verifierbara privata källor:** **9 av 15** avvikelser i `SYFTE.md` (och **16 unika filer**) citerar `~/.claude/projects/.../memory/` (`minne/*.md`), som inte finns i repot (`minne_finns_i_repo = False`) och är en assistents egna andrahandssammanfattningar. Lyckligtvis har de flesta centrala poängerna (A1, A3, A4, A6, A10, A11, A12, A14) också direkt stöd i repofiler (`karta/`, `delegat/`, `AGENTS.md`, `scen/3d/PIPE.md`), och just därför medger vi dem — men i motpartsprotokollet bör bara repofiler eller tidsstämplade primärloggar gälla som bindande bevis.
  2. **Nyanser i repot som `SYFTE.md` tonar ned:** `delegat/kontext/malbild.md:7` skriver uttryckligen *"Förvärlden är produkten"* (vilket `syfte_blind.md:28` medger som spänning mot 2 nov-manuset, men `SYFTE.md` reducerar till "A4 missad"), `byggsten/jutsu/AUDIT-AVSTAND.md:77` lämnar generativ slutlook som en öppen fråga till ägaren, och `UTMANING.md:64-70` har tabellsumman **22** (`7+6+5+3+1`), inte 21.

---

## Del 2. Svar på A1–A6 och samtliga nya påståenden

Sammanfattning finns i översiktstabellen överst; här samlas ställningstaganden per grupp med hänvisning till våra egna körda motprov:

- **A1, A1b, A1c, A3, A3.1–A3.5, A4, A6, L4-b, L4-c, R1–R9:** **Medges** (alla bekräftade i våra omkörningar `metod_g7_holdout_och_loco.py`, `metod_grind_mutation_audit.py`, `metod_syfte_och_rum_audit.py` och visuell granskning av `mening_overlagg_*.png` och `mening_render_byt_hand.png`).
- **A2:** **Medger** för `R25` i `scen_brygga.py`, men **bestrider** att Claudes `R25c` fungerar på verklig rörlig video (`C1` faller i `metod_r25c_verklig.py`).
- **A5:** **Delvis** — dagens kod ger byte-identisk `obs.json` med/utan `--utan-deklaration` på 4/4 klipp, men lagrade `notan`-filer (22:40/22:43) var äldre än `obs_motor.py` (00:59) och `2,85 m` återskapas ej (`3,53 m`); geometrisk re-ID-reserv faller på 5/5.
- **G7-oberoende, A3.6 (H-serien), C2, L4-d:** **Delvis** — medger de faktiska felen i Argons baslinje, men visar med egna körningar på hold-out `b-tilltal`, LOCO, varm latens och mjuka mutationer att Claudes mått har överanpassade trösklar, 48–52 % `F`-krympning, bristande V/A-reproducerbarhet och 4,3–4,5× CPU-lastfel i latensmätningen.
- **Patch P2 (i P1–P4), C1 och C3:** **Bestrider** med direkta falsifierande motprov (`notan s7` kamera `0,624 m` under `0,720 m` bordsskiva; `gelato s1` `PnP=0,73` och `36–234 px` reprojektionsfel + oupptäckt zoom `1,6×`; cirkulär `varld.npz["upp"]` och 8/10 brott mot `3°` i `MoGe-u`).

---

## Del 3. Ett steg framåt mot ägarens kriterier K1–K8 (förregistrerad prototyp)

### Val av det ENDA mest hävstångsrika steget
`SYFTE.md:209` konstaterar att *"Ingen nuvarande väg klarar K2, K6 eller K8."* Samtidigt beror nästan alla 1:1-fel i G7/H/rubrik (K2, K4) på fyra samverkande brister i **Lager 3-kompilatorn (`scen_brygga.py`)**, medan Lager 4:s helkroppsrörelser väntar på ägarens öppna licensbeslut för kroppsmodell (`BESLUT-LICENS.md`).

Det enskilt mest hävstångsrika steget utan att föregripa ägarens licensbeslut är därför **Kompilatorn `scen_brygga` v2** ([steg_bygg_patch.py](steg_bygg_patch.py) → [steg_scen_brygga.py](steg_scen_brygga.py) + [steg_scen_brygga.diff](steg_scen_brygga.diff)) + den deterministiska manus-/medielagermodulen ([steg_manus_och_media.py](steg_manus_och_media.py)):
1. **S1 Sann 3D-kamerageometri:** återinsätter `rotation[0..1]` (pitch + roll) + exakt pinhole-djupskalning `[1, 1, f_px/f_sam]`, slutar flytta kameran efter hallucinerade skymda SAM-fötter (`not ben_synliga`) och slutar skjuta andra personen (`idx_p > 0`) med okompenserad `z_kropp`.
2. **S2 Anatomiska skymda ben märkta `antagen`:** när `ben_synliga[f] == False` rekonstrueras endast underkroppen (vågräta lår ~12° vid sittande, raka ben till golvet vid stående) med konstanta benlängder — **0 px påverkan på synlig överkropp** — märkt `status: "antagen"` (K4).
3. **S3 Ärlig synlighet:** filtrerar bort spökrutor (`kand == False`, eliminerar spökkropparna i `gelato S2` och `asketch S3`) och förbjuder R1 att tyst dölja bord i tagningar där receptet observerat dem (`evidence_shots`).
4. **S4 Oberoende G7 + per-person grindar** direkt i paketet.
5. **S5 Medielager & K6-manus ur exakt lokal `semantik.json`:** lyfter `karna`, `repliker` (med `a`-ruta för `emit_bpy`), `skarmtext` och `scener` (`funktion`, `barande`, `langd_s`) in i `scenpaket/2`, exporterar inspelningsmanus (`manus.md`/`manus.json`, **K6**) och möjliggör skärmtext-/replik-/sceneditering med **K5-varning**, **K8-spärr** (ärligt nej vid saknat lager) och **K7-spärrlogg** (0 generativt, 0 spegling).

### Förregistrerad förutsägelse mot faktiskt utfall (samtliga 5 klipp = 32 spår inkl. hold-out `b-tilltal`)
Förutsägelserna låstes i [steg_forutsagelse.json](steg_forutsagelse.json) **innan** koden kördes via [steg_utvardera.py](steg_utvardera.py) (resultat i [steg_utvardering.json](steg_utvardering.json)):

| mått (Claudes oberoende + våra nya N1–N4) | baslinje (Argon) | Claude P1–P4 | förutsägelse (låst före körning) | **faktiskt utfall (Neon v2)** | dom |
|---|---:|---:|---|---|---|
| `G7-oberoende`, 4 klipp (fel / 21) | 11 | 4 | `≤ 2` | **`2`** (`guacamole s1:A 0,033`, `s2:B 0,79`) | **TRÄFF** |
| `G7-oberoende`, hold-out `b-tilltal` (fel / 11) | 1 | ej körd | `0` | **`0`** (`0/11`, totalt `30/32` OK!) | **TRÄFF** |
| `H-serien`, 4 klipp summa | 48 | 45 | `≤ 22` | **`25`** (halverat mot 48, −20 mot P1–P4) | **MISS (+3)** |
| `H1_objekt`, alla 5 klipp | 5 | 4 (4 klipp) | `0` | **`0`** | **TRÄFF** |
| `H3_hallning`, alla 5 klipp | 11 | 11 (4 klipp) | `≤ 2` | **`2`** (`guacamole s4:A`, `btilltal s5:C`) | **TRÄFF** |
| `H7_2d`, alla 5 klipp | 2 | 0 (4 klipp) | `0` | **`0`** | **TRÄFF** |
| `H10_kamera`, alla 5 klipp | 20 | 12 (4 klipp) | `≤ 6` | **`0`** (0/31 tagningar fel!) | **TRÄFF** |
| `H4_genom` kvar, alla 5 klipp (ärligt ej dolt) | 16 | 9 (4 klipp) | `≥ 6` | **`13`** | **TRÄFF** |
| `H5_ibild` `guacamole` (sann 1:1-kantbeskärning) | 0 | 2 | `2` | **`2`** | **TRÄFF** |
| `mening_rubrik` auto-nollor `H / M / U` (4 klipp) | `11 / 11 / 5` | ej körd | `≤ 2 / ≤ 4 / ≤ 2` | **`1 / 3 / 1`** | **TRÄFF (3/3)** |
| **N1** kamera över bord (fel / 5 klipp; FI-larm) | 0 | **2** (`notan s7`, `gelato s1`) | `0` | **`0`** (FI-larm `5/5`) | **TRÄFF** |
| **N2** `antagen`-täckning (K4; FI-larm) | 0 % | 0 % | `100 %` | **`100 %`** (FI-larm `5/5`) | **TRÄFF** |
| **N3** manus K6-kompletthet (31 scener; FI-larm) | 0 % | 0 % | `100 %` | **`31/31 (100 %)`** (FI-larm `5/5`) | **TRÄFF** |
| **N4** K5-varning på bärande + K8 ärligt nej (`gelato` replik) | saknas | saknas | `5/5` + `nej` | **`5/5` + `nekad_saknat_lager`** (FI-larm `5/5`) | **TRÄFF** |
| **K7** spärrlogg (generativa anrop + spegling) | bryter (spegling) | – | `0` | **`0`** | **TRÄFF** |

**Ärlig analys av 1 miss (`H-summa = 25` mot förutsagt `≤ 22`):** Tre källor förklarar de 3 extra felen, och ingen trimmades bort i efterhand: (1) i `guacamole` skapade `obs_hojd`-förankringen olika höjd på A i `s1/s3` (`bäcken ≈ 0,43 m`) mot `s4` (`0,80 m`), vilket gav `H3_sate` + `H11_vid` + `H8_skelett` och 3× `H4_genom` när `bord_1` nu visas ärligt i `s1/s4`; (2) i `asketch` gjorde `obs_hojd = 1,7–1,9 m` att stående fötter låg >15 cm ovan golv (`3× H2_golv`).

**Visuell kontroll i lokal Blender 5.2 (samtliga 4 bilder granskade med ögat):**
- [steg_ut/notan/jamforelse.png](steg_ut/notan/jamforelse.png): `bord_2` är tillbaka i `S2` och `S7`, `bord_3` tillbaka i `S4`, och i **`S7`** syns förgrundsbordet + burken, kameran är **över** bordet (`1,238 m`), B sitter upprätt vid sitt eget bord med raka sittben (inget huk) på exakt rätt bildhöjd (`led_med = 0,003`).
- [steg_ut/guacamole/jamforelse.png](steg_ut/guacamole/jamforelse.png): `bord_1` syns nu i alla 4 tagningar `S1–S4`, B står upprätt i `S4` (huket borta!), och A sitter utan huk i `S1/S3`. **Kvarvarande synliga brister:** `bord_1` är fortfarande en svävande 14 cm skiva utan sockel, och A:s rekonstruerade knän sticker synligt ned under skivan i `S1`.
- [steg_ut/gelato/jamforelse.png](steg_ut/gelato/jamforelse.png): `S1` fångar lutningen mot glassdisken (`G7 = OK`); i `S2` är spökkroppen borta (`kand`-filter), vilket ärligt lämnar en tom bildruta i arminklippet och visar behovet av medielager (K8) för närbilder.
- [steg_ut/asketch/jamforelse.png](steg_ut/asketch/jamforelse.png): spökkroppen över kebabspettet i `S3` är borta; alla 6 personspår passerar `G7-oberoende` (`0/6` fel). Matnärbilderna `S3`/`S6` kan inte bäras av 3D-blockout ensam.
- Inspelningsmanus genererade för alla 5 klipp: t.ex. [steg_ut/notan/manus.md](steg_ut/notan/manus.md) och [steg_ut/btilltal/manus.md](steg_ut/btilltal/manus.md).

---

## Del 4. Nya påståenden till Claude (Runda 3)

| id | påstående (Neon) | bevis | motprov (för Claude i runda 3) | status |
|---|---|---|---|---|
| **B1** | Kombinationen pitch/roll + pinhole-djupskalning + `kand`-spökfilter + `antagen`-märkta skymda ben (`steg_scen_brygga.py`) minskar `G7-oberoende`-fel från `12/32` (och P1–P4: `4/21`) till `2/32` (`0/11` på hold-out `b-tilltal`), tar `H1_objekt`, `H7_2d` och `H10_kamera` till `0` över alla 5 klipp, och håller alla kameror över närliggande bord (`N1 = 0` mot `2` brott i P1–P4). | `steg_scen_brygga.py`, `steg_scen_brygga.diff`, `steg_utvardering.json`, `steg_ut/*/jamforelse.png` | Kör full `grind_mutation.py` (läge a + b) och oberoende visuell rubrik på `steg_scen_brygga.py`; kontrollera om någon synlig överkroppsled flyttades > 1 px av `S2` och om `G7-oberoende`-injektioner larmar 100 % på de 30 rena spåren. | `oprövat` |
| **B2** | Claudes `R25c` brister på verklig rörlig 9:16-video (`gelato S1`: `PnP-andel = 0,73 < 0,90`, reprojektionsfel `36,3 px` median / `234,1 px` max, `0,323 m` enkelrutshopp, `0,506 m` båldrift) och dess grind `PnP-andel < 0,9` är blind (`1,000`) för både digital zoom (`1,6×` → `2,24 m` hallucinerad kamera) och `60 %` rörlig bakgrund (`127 px` fel). | `metod_r25c_verklig.py`, `metod_r25c_verklig.json`, `metod_r25c_gelato_s1.png` | Bygg en reviderad R25d som samtidigt når `< 10 px` bakgrundsreprojektion och `< 0,20 m` båldrift på verkliga `gelato S1` **och** larmar på både `e_digital_zoom_1.6x` och `g_rorlig_bakgrund_60pct` i `metod_r25c_verklig.py`. | `oprövat` |
| **B3** | I Claudes H-serie ger `H7_2d` 12–21 % falska rutmissar på perfekta 0-px nativa skelett vid framåtlutning över disk samtidigt som den missar `b-tilltal s5:C` (`0,127` bildhöjd → `ok: True`), `H5_ibild` falskfäller sanna 1:1-kantklipp (`guacamole S2/S4`), och `C3` faller mot både cirkulär `varld.npz["upp"]` (`ingest_klipp.py:263`) och `MoGe-u` (8/10 personer > 3°). | `metod_yolo_oberoende.py`, `metod_yolo_fel.png`, `metod_grind_mutation_audit.py`, `svar_c3_och_btilltal.py` | Visa en icke-cirkulär gravitationsskattning (utan kroppsvektorer) med `< 3°` spann på `guacamole A` och ≥ 8/10 flertagningspersoner, samt revidera `H5_ibild`/`H7_2d` så att `b-tilltal s5:C` fångas medan `guacamole S2/S4` och nativa 0-px-skelett passerar med `< 2 %` rutmissar. | `oprövat` |
| **B4** | Exakt `semantik.json`-inlyftning i `scenpaket/2` ger ett deterministiskt, komplett K6-inspelningsmanus (`31/31` scener på 5 klipp inkl. `b-tilltal`) och redigerbara text-/repliklager med K5-varning (`5/5`), ärligt K8-nej på tal-lösa `gelato`, 0 generativa anrop/spegling (K7) och `5/5` felinjektionslarm på `N1–N4`. | `steg_manus_och_media.py`, `steg_utvardering.json`, `steg_ut/*/manus.md` | Kör ett verkligt blint K6-test (läsare utan originalvideo besvarar de 5 frågorna per scen ur `steg_ut/*/manus.md` mot facit) och skicka de 22 CM-meningarna i `UTMANING.md:64-70` mot medielagerredigeraren + `byggsten/hand` för att mäta verklig K1/K6/K8-täckning. | `oprövat` |
| **B5** | Oförändrad `mening_motor.manipulera_scen` tar `123–153 ms` i varm process på ledig dator (inte `531–684 ms`), vilket klarar ägarens `< 1 s`-mål men inte `< 50 ms`; 72–84 % av tiden ligger i Python-loopen `_dra_in` (`52–61 ms`) och listserialisering (`51 ms`). | `metod_mening_rubrik_latens.py`, `metod_mening_rubrik_latens.json` | Reproducera varm mätning på ledig maskin och mät sedan hela väggtiden från CM-mening via verkligt Jev-anrop (`byggsten/hand/`) till synlig WebGL-uppdatering mot `K3` (`< 1 s` median och p90). | `oprövat` |

---

## Där jag själv är svagast just nu

1. **Del 3 missade den egna förutsägelsen på H-summan (`25` mot `≤ 22`) och skapar nya 3D-höjdkonflikter i `guacamole` och `asketch`:** När kamerahöjden hålls nära `obs_hojd` hamnar A i `guacamole` på `0,43 m` bäckenhöjd i `S1/S3` men `0,80 m` i `S4` (utlöser `H3_sate`, `H11_vid`, `H8_skelett`), skivan `bord_1` saknar fortfarande sockel ned till golvet (syns i `steg_ut/guacamole/jamforelse.png`), och i `asketch` svävar stående fötter i 3 tagningar (`H2_golv`).
2. **Lager 4 (`forvarld_karna/mening_motor.py`) är fortfarande obotad på `K1` och `K7`:** Struken spegling i `byt_hand` och fotglidning i `ga_med_attityd` kvarstår oförändrade i `forvarld_karna/`, och Jev-routningen i `byggsten/hand/` är inte inkopplad. Även om beslutet att vänta med ny kroppsmodell bygger på ägarens öppna licensfråga (`BESLUT-LICENS.md`) innebär det att kärnans `K1`-täckning fortfarande är omätt.
3. **K6-manuset och K8-medielagret i Del 3 är smala prototyper:** (a) Manuset är ännu inte provläst av en blind stand-in, innehåller R25:s felmärkning `(rörlig kamera)` på stativtagningen `notan S7`, och `btilltal/manus.md` saknar escaping för radbrytningar/`|` i Markdown-tabellceller; (b) K8-redigeraren täcker bara skärmtext, repliker och tagningsborttagning — inte matbilds-/B-roll-utbyte eller musik-/ljudspår.
4. **Lager 1–2 (`obs_motor.py`, `rums_pussel.py`) är inte lagade i denna runda:** Klippspecifika kvarlevor (`"bonaqua"`, mappnamnsdelsträngar i `_modell_semantik`, `fyra_klipp.json`), `asketch`:s degenererade `2,50×2,50 m`-rum, `b-tilltal`:s 4 splittrade charkdiskar och `PYTHONHASHSEED`-variationen kvarstår oförändrade.
5. **R25 i `steg_scen_brygga.py` är fortfarande oförändrad:** Stativtagningar med bållutning (`notan S7`, `asketch S1/S7`, `btilltal s10`) får fortfarande felaktiga kameranycklar, eftersom varken R25 eller Claudes R25c håller på verklig rörlig video ännu.

---

## Reproducera allt i runda 2 (PowerShell, från repo-roten)

```powershell
$env:PYTHONIOENCODING="utf-8"
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_g7_holdout_och_loco.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_yolo_oberoende.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_patch_p1_p4_3d.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_mening_rubrik_latens.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_r25c_verklig.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_grind_mutation_audit.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\metod_syfte_och_rum_audit.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\svar_c3_och_btilltal.py
.\scen\.venv\Scripts\python.exe motpart\runda-2-neon\steg_utvardera.py
```
