# RUM – motpart runda 1 (Claude), lane A5 + A6 + rumshjärnans sakpåståenden (Lager 1–2)

19 nov 2026. Allt nedan är kört i denna runda. Inga filer i `forvarld_karna/`, `byggsten/` eller `scen/` är ändrade; patchar görs i minnet (källtext läses, exakta strängbyten som måste träffa exakt en gång, modulen körs från minnet). Utdata ligger i `motpart/runda-1-claude/rum_ut/`.

## 0. Kort dom

| id | påstående (Argon) | dom | bärande bevis |
|---|---|---|---|
| A5 | Verifierat utan `deklaration.json` på alla 4 klipp | **delvis** | Nuvarande kod ger byte-identiska `obs.json` med och utan `--utan-deklaration` på alla 4 klipp, och identiska recept för notan/asketch. Men de lagrade `ut/*/obs.json` är alla skrivna före nuvarande `obs_motor.py` (00:59), och notans lagrade obs/recept (22:40/22:43) går inte att återskapa: dagens kod ger andra mätningar och A↔B 3,53 m i stället för 2,85 m. "Deklarationsfritt" betyder i praktiken Gemini-semantik som hämtas via mappnamn (se A6). Den rent geometriska reserven ger fel identitet eller hållning på 5/5 klipp (§4.3). |
| A6 | Ingen klippspecifik kod | **delvis faller** | Inga `if klipp == …`-grenar i Lager 1–2, men: (1) `regler.py:61` `"bonaqua": 3.5`; (2) `obs_motor.py:439–458` hämtar semantik via mappnamnsprefix/delsträng – ett påhittat klipp `a-dialog-kafe-tagningar` får a-sketchs roller (körbart prov, §4.2); (3) `_fokal` slår upp en fokaltabell för fyra namngivna klipp; (4) flera konstanter är införda med kommentarer om enskilda klipp. Känslighet ±30 %: notan 20/21 och guacamole 31/32 håller (bara fokalen × 0,7 bryter), gelato kräver gelato-klämman, asketch bryter i 5/30 (§4.4). |
| R1 (ny) | 6.1-tabellen: A↔B 2,85 m, σ_B 2,90→0,30 m, conf 0,812/0,618/0,802/0,578 | **faller som reproducerbart resultat**; kopplingen står | Kopplingen av A:s bord och burk till s7 återskapas. Siffrorna gör det inte (§2.3). |
| R2 (ny) | Verkligt A↔B ≈ 3,3 m | **faller som facit** | Det finns inget oberoende facit. Alla skattningar (2,3–4,2 m i denna runda) bygger på samma monokulära kroppsdjup, samma fokalantagande och antagandet att S7:s kamera står vid A:s plats (§3.1). |
| R3 (ny) | Bugg 1: grinden kastade bort s7-kopplingen innan lösaren fick pröva den | **faller som orsak; rättningen 1a+1b räcker ändå** | Gammal kedja: vidgad grind ger ingen koppling, ingen grind alls ger ingen koppling, 1b ensam ger ingen koppling. 1a+1b tillsammans ger koppling (A↔B 2,54 m). I nya kedjan behövs ingen av Lager 2-rättningarna (§3.2). |
| R4 (ny) | Bugg 2: `pa` mättes i 3D | **står som bugg, förklaringen fel** | Ankaret låg 1,43 m under kameran (MHR-rotens höjd), inte i axel/brösthöjd. Burken låg 0,26 m under kameran. Höjdskillnaden 1,17 m > tröskeln 1,0 m (§3.3). |
| R5 (ny) | Bugg 3: låst orientering | **delvis** | Den gamla kedjan hade verkligen B-kamerorna ~90° fel (yaw −81…−85° i stället för ~180°). Men "klipp 0 låstes till +90°" är gaugeval, inte en bugg, och ingen enskild Lager 2-rättning behövs i nya kedjan (§3.4). |
| R6 (ny) | Bugg 4: visuell ankarmatchning | **faller (inte implementerad)** | `farg_signatur` är `null` i alla 65 detektioner på 5 klipp (inga nyckelbilder i ingest) och läses aldrig av `rums_pussel.py`. `bonus_samma_distinkt_pa_bord` används aldrig. R22 är ett hårdkodat straff (−4,0), och att stänga av det ändrar ingenting på notan (§3.5). |
| R7 (ny) | 6.2: asketch "ett sammanhängande gatuköksrum" (P 0,86) | **delvis** | Återskapas, men geometrin är degenererad: rummet är 2,50 × 2,50 m (exakt `rum_min_m`), A↔B 0,48 m, och båda personerna står närmare den andras bord (§5). |
| R9 (ny) | 6.4.1: deklarationsfri person-re-ID och hållning (SIFT + 3D-knävinkel som reserv) | **faller för reserven** | `G_geometrisk_reid`: notan sittande→stående (6/6) och B i S7→D; gelato 1 person→2; asketch B→3 personer; guacamole S4-paret förlorat; b-tilltal C→2 personer (§4.3). |
| R8 (ny) | Allmän motor för nya klipp | **oprövat → svagt** | På hold-out b-tilltal (11 tagningar) körs kedjan utan krasch, men disken blir 4 bord med conf 0,02 och sluttron "B vid eget bord; C vid eget bord" (P 0,98) går emot deklarationen och semantiken: alla tre står bakom samma charkdisk (§6). |

---

## 1. Hur det kördes

```powershell
$env:PYTHONIOENCODING="utf-8"
# A5: omkörning med egen utmapp (kopia av verifiera.py, bara utmapp och lager-val ändrade)
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_verifiera.py --klipp alla
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_verifiera.py --klipp alla --utan-deklaration
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_verifiera.py --klipp btilltal            # hold-out
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_jamfor.py forvarld_karna\ut\notan motpart\runda-1-claude\rum_ut\med_dekl\notan
# buggarna på den gamla kedjan (byggsten/rumshypotes/hjarna.py + gamla notan-obs)
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_gammal.py --variant bas|grind|ingen_grind|barn|grind_barn|...
# ablation och känslighet ±30 % i nya kedjan
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_ablation.py --lista                 # alla patchar kontrolleras
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_ablation.py --klipp notan --variant L2_alla_rattningar_av
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_tabell.py notan
scen\.venv\Scripts\python.exe motpart\runda-1-claude\rum_namnprov.py                          # A6 mappnamn
```

| fil | vad |
|---|---|
| `rum_verifiera.py` | kopia av `forvarld_karna/verifiera.py`; skriver till `rum_ut/<med_dekl|utan_dekl>/<klipp>/`; Lager 3 bara med `--lager3` |
| `rum_jamfor.py` | diff av obs/recept mellan två körningar |
| `rum_gammal.py` | gamla `hjarna.py` med Argons rättningar 1a/1b inpatchade, på gamla `ut/notan/obs.json` |
| `rum_ablation.py` | 80 namngivna varianter (rättningar av/på, konstanter ±30 %); resultat i `rum_ut/ablation/<klipp>/<variant>.json` |
| `rum_tabell.py` | tabell ur ablationsresultaten |
| `rum_namnprov.py` | påhittade klippnamn mot `_modell_semantik`/`_fokal`; resultat `rum_ut/namnprov.json` |
| `rum_kanslighet.py` | sammanställer känslighet och ablation per klipp → `rum_ut/kanslighet.md` |
| `rum_fokal_moge.py` | notan med fokal × 0,78 (MoGe:s egen FOV), utan att ändra `rum_ablation.py` |

Lager 3 och Blender ingår inte i min lane och är inte körda. Importen av `byggsten/rumshypotes/regler.py` skapade en bytekodfil (`__pycache__/regler.cpython-312.pyc`) som inte fanns innan. Den är borttagen; inga källfiler utanför denna mapp är rörda. Körningarna gick på 8 delade kärnor medan andra agenter körde, så tiderna är inte jämförbara med Argons.

---

## 2. A5 – reproducerbarhet

### 2.1 Tidsstämplar
| tid (lokal) | fil |
|---|---|
| 18 nov 22:34 | `regler.py` |
| **22:40 / 22:43** | **`ut/notan/obs.json` / `recept.json`** |
| 22:57 | `schema.py` |
| 23:13 | `rums_pussel.py` |
| 23:24–23:25 | `ut/guacamole|gelato|asketch/obs.json` + `recept.json` |
| 19 nov 00:57 | `verifiera.py` |
| **00:59** | **`obs_motor.py`** (innehåller `--utan-deklaration`) |

Ingen av de lagrade `obs.json` är skriven av nuvarande `obs_motor.py`. Notans recept är också äldre än nuvarande `rums_pussel.py`.

### 2.2 Omkörning mot lagrat
| klipp | obs.json (med / utan dekl) | recept.json med dekl | recept.json utan dekl |
|---|---|---|---|
| guacamole | byte-identisk / byte-identisk | P 0,9828 mot lagrat 0,9831; bara alternativens etiketter skiljer | 1 rad skiljer (etikett i alternativ) |
| gelato | identisk / identisk | 1 rad (etikett) | 1 rad (etikett) |
| asketch | identisk / identisk | byte-identisk | byte-identisk |
| notan | **skiljer** (båda lika med varandra) | **skiljer** | **skiljer** (byte-identisk med med-dekl) |

**Med och utan deklaration ger samma `obs.json` på alla 4 klipp (byte för byte).** Den delen av 6.4.1 står för nuvarande kod. För gelato finns ingen `deklaration.json`, så där jämförs `brief/konsensus/konsensus.json` mot Gemini-semantik.

**Determinism:** guacamole Lager 2 med samma obs och olika `PYTHONHASHSEED` ger P 0,9828 (frö 0 och slumpfrö) eller 0,9831 (frö 1, 2). Med `OMP_NUM_THREADS=1` blev P 0,9811. Sluttro, bord och A↔B (1,151 m) är stabila. På hold-out b-tilltal ger samma obs P 0,952 respektive 0,962 i s7 i två processer. Resultaten är alltså inte bit-reproducerbara mellan processer (`rum_ut/ablation/guacamole/bas_hash*.json`). Strålen bär också etikettpermuterade dubbletter ("A vid bord_1; B vid bord_2" och tvärtom med samma P), vilket äter beam-platser. Det är ärvt från den gamla koden.

### 2.3 Notan, ARKITEKTUR 6.1 mot omkörning
| mått | 6.1 (lagrat 22:43) | omkörning, nuvarande kod (med = utan dekl) |
|---|---|---|
| A:s bord, tagningar (conf) | s1,s3,s6,s7 (0,812) | s1,s3,s6,s7 (0,821), heter nu `bord_2` |
| B:s bord | s2,s5,s7 (0,618) | s2,s5,s7 (0,585) |
| burken `foremal_1` | s1,s3,s6,s7 (0,802) | s1,s3,s6,s7 (0,795) |
| B:s mugg `foremal_4` | s5,s7 (0,578) | s5,s7 (0,573) |
| σ_B s6 → s7 | 2,90 → 0,30 m (lagrat 2,94 → 0,30) | **0,71 → 0,34 m** |
| A↔B | **2,85 m** | **3,53 m** |
| tro per tagning s2 | "eget bord" P 0,51 | **"A och B vid samma bord" P 0,75** (omprövas i s3 med "B borde synas (0,3 m)") |
| B:s djup från S7-kameran (obs) | 3,05 m | 3,28 m |
| A:s djup i S1 (obs) | 1,26 m | 1,41 m |
| `delar_kamera_med` | inga | s3→s1, s5→s2, s6→s1 |
| Lager 2-tid | – | 480 s (under last; 8 kärnor delade) |

Den lagrade notan-obs har samma persondjup som den gamla `byggsten`-obs (A 1,26 m, B i S7 3,05 m). Den är alltså gjord före bytet till bålpunkt (`c_spine0/2`), som LAGE 3.1 räknar till rättningarna. 2,85 m bygger därmed inte på den rättning som anges.

Den gamla kedjan återskapas exakt (`rum_gammal.py --variant bas`): A↔B 6,756 m, `bord_4`/`foremal_5` i s7, σ_B 17,97/19,64/19,31/3,05/5,43/3,18, samma som `byggsten/rumshypotes/ut/notan/LOGG.md`.

---

## 3. Sakriktighet

### 3.1 Finns ett facit för A↔B i notan?
| källa | A↔B (stol–stol) | oberoende? |
|---|---|---|
| `EXPERIMENT.md` §6 och README steg 5 | "väntade 3–4 m" ur "s7 mäter B 3,05 m från kameran" | nej, samma S7-mätning |
| `ARKITEKTUR.md` §3 | "verkliga ~3,3 m" | ingen källa anges |
| `plats/plats_matt.json` `d_grammatik.stationer_ihop` | 2,318 m | nej, summan av kameraavstånd under antagandet att motbilderna står rygg mot rygg |
| `plats_matt.json` `vidvinkel` (S7, f = 1024) | 2,635 m | nej, SAM i S7 |
| `plats/hand.json` | 2,48 m | nej, filen säger själv "antaget … inte en oberoende mätning" |
| gamla kedjan + 1a+1b (denna runda) | 2,54 m | nej |
| Argon lagrat | 2,85 m | nej |
| nuvarande kod | 3,53 m | nej |
| nuvarande kod, ablationsvarianter (§3.6) | 2,31–3,60 m | nej |
| nuvarande kod, fokal × 0,78 (MoGe:s egen FOV ≈ 41°, EXPERIMENT 7.3) / × 1,3 | 2,99 / 3,69 m | nej |
| nuvarande kod, fokal × 0,7 | 4,22 m, **och s7-kopplingen bryts** | nej |

Inget facit finns. Spridningen 2,3–4,2 m kommer från implementationsval och antaganden (personpunkt, R15-riktning, `vid_avstand_m`, fokal), inte från ny information. A↔B följer inte ens fokalen proportionellt (× 0,78 → 2,99; × 1,0 → 3,53; × 1,3 → 3,69), så avståndet är inte en ren mätning utan styrs av de andra termerna i lösningen. Fokalvalet 983,7 px (försvinningspunkter) mot MoGe:s ~770 px är fortfarande öppet (EXPERIMENT 7.3). Både "2,85 m som framgång" och "3,3 m som verklighet" saknar stöd. Det som går att säga är att A↔B nu följer S7:s egen mätning av B (skillnad ≤ 0,35 m), i stället för rummets typstorlek som i den gamla kedjan (6,8 m).

### 3.2 Bugg 1 – grinden (`hjarna.py:670–671`) och kamerainitieringen
Gamla kedjan, gamla obs (`rum_gammal.py`, `rum_ut/gammal/*.json`):

| variant | S7:t1 (förgrundsbord) | S7:f1 (burk) | A↔B | σ_B s7 |
|---|---|---|---|---|
| bas | kopia `bord_4` | kopia `foremal_5` | 6,76 | 3,18 |
| 1a: Argons grindformel | kopia | kopia | 6,76 | 3,18 |
| ingen grind alls | kopia | kopia | 6,76 | 3,18 |
| 1a + nya föremålspriser | kopia | kopia | 6,76 | 3,18 |
| 1b: precisionsviktad kamera + klusterflytt | kopia | kopia | 6,76 | 3,18 |
| **1a + 1b** | **A:s bord** | **`foremal_1`** | **2,54** | **0,35** |
| 1a + 1b + `max_nfev` 12 (± nya priser) | A:s bord | `foremal_1` | 2,54 | 0,35 |

Påståendet att grinden kastade bort hypotesen innan lösaren fick pröva den **faller**. Även helt utan grind väljer den gamla hjärnan kopian. Det som avgör är startläget för kameran (1b) **tillsammans med** grinden (1a). Rättningen som helhet räcker alltså på gammal data, men av ett annat skäl än det angivna.

Nya kedjan, nuvarande obs (`rum_ablation.py`): **alla** Lager 2-rättningar avstängda samtidigt (`L2_alla_rattningar_av`: gammal grind, medelvärdeskamera, ingen klusterflytt, en yaw, ingen R22) ger fortfarande koppling och A↔B 3,535 m. Detsamma gäller varje rättning för sig, R24 av, SIFT-kameradelning av och `max_nfev` 8 (tabell §3.6). I dagens kedja bärs kopplingen alltså av förändrade observationer, inte av de rättningar som ARKITEKTUR §3 beskriver.

### 3.3 Bugg 2 – `pa` i 3D (`obs_ingest.py:410`)
Uppmätt i S1 (nuvarande `Tagning`, samma fokal och djup):

| punkt | höjd relativt kameran |
|---|---|
| `cam_t_ra` (median, gamla personpunkten och därmed R15-ankaret) | −1,43 m |
| bålpunkt `c_spine0/2` | −0,39 m |
| axlar | −0,06 m |
| burken | −0,26 m |

Den gamla `pa`-testen jämförde burken med ett ankare 1,17 m lägre, och tröskeln var 1,0 m. Därför fick burk och mugg `pa = null` i s1, s3, s5 och s6 i gamla obs (verifierat), men `pa` i s7 där bordet inte var personförankrat. Buggen är verklig. Förklaringen i ARKITEKTUR §3 ("axelhöjd/brösthöjd") är fel; Argons egen kommentar i `obs_motor.py:341` ("~1,3 m under kameran") stämmer. I den gamla hjärnan ger `pa` bara en residual. I den nya kedjan gör återställningen (`L1_pa_3d`) ingen skillnad. Med bålpunkten ligger ankaret nu nära bordshöjd, så 3D-testet slår inte längre fel. Rättningen behövs alltså inte så länge personpunkten är bytt.

### 3.4 Bugg 3 – orienteringen (`hjarna.py:636–646`)
Gamla receptet har kamerornas yaw s1/s3/s6 ≈ 0°, men s2/s5/s7 = −81,7/−80,9/−85,4° och s4 −74°. Motbilderna står alltså ~90° fel i stället för ~180°. I Argons och mitt nya recept är s2/s5/s7 −168…−171°. Felet var verkligt och gör s7-kopplingen geometriskt omöjlig. Två saker i beskrivningen stämmer dock inte:
- "Klipp 0 låstes till yaw = +90°" är gaugevalet för första kameran, inte ett fel. Koden för k = 0 är oförändrad i `rums_pussel.py:828–830`.
- Ljuset ändrades samtidigt från ±60° till ±85° (`obs_motor.py:783–786`). Med ±85° pekar "ljus från höger" i A:s tagningar och "från vänster" i B:s mot en vridning på 170°, alltså nästan exakt motbild. Det är en konstant som passar notan. Ablationen `L2_yaw_en` (bara bästa Manhattan-axeln) och `L1_ljus_60` kopplar båda fortfarande (§3.6). Topp-2-rättningen är alltså inte nödvändig i dagens kedja.

### 3.5 Bugg 4 – visuell ankarmatchning
- `farg_signatur` fylls av `Tagning.farg_vid`, som kräver `frames/<ruta>.jpg` eller `nyckelbild.*`. Sådana bilder finns inte i någon ingestmapp. Resultatet är `null` i alla 65 detektioner på 5 klipp, i både Argons och mina obs.
- `rums_pussel.py` läser aldrig `farg_signatur` (grep: 0 träffar). `R["bonus_samma_distinkt_pa_bord"]` läses aldrig.
- R22 i koden (`rums_pussel.py:583–593`) är ett straff på −4,0 nats (hårdkodat, inte i `regler.py`) när samma föremål står `pa` flera bord. Docstringen (rad 15–17) säger att hypotesen "belönas", och det gör den inte.
- `L2_R22_av` på notan: ingen skillnad (koppling ja, A↔B 3,533).

Bugg 4 är beskriven men inte byggd.

### 3.6 Ablation i nya kedjan, notan (s7-länk = A:s bord / burken sedd i s7)
| variant | vad | sluttro | P | s7: A:s bord / burk | n bord | A↔B m |
|---|---|---|---|---|---|---|
| `bas` | nuvarande kod | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L2_grind_gammal` | 1a av: gammal grind | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,535 |
| `L2_kamera_medel` | 1b av: medelvärdeskamera | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L2_klusterflytt_av` | 1b av: ingen klusterflytt | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L2_bugg1_hel_gammal` | hela bugg 1 av | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,535 |
| `L2_yaw_en` | bugg 3 av: bara bästa Manhattan-axeln | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,535 |
| `L2_R22_av` | R22-straffet av | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L2_R24_av` | R24 (vändning) av | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,534 |
| `L2_delar_kamera_av` | SIFT-kameradelning av i Lager 2 | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,527 |
| `L2_nfev8` | `max_nfev` 12 → 8 | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L2_alla_rattningar_av` | grind + kamera + klusterflytt + yaw + R22 av samtidigt | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,535 |
| `K_foremal_gamla` | föremålspriser som i byggsten | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `K_utan_bonaqua` | utan nyckeln `bonaqua` | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `K_vid_075` | `vid_avstand_m` 0,75 | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,596 |
| `L1_pa_3d` | bugg 2 av: `pa` i 3D < 1,0 m | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,533 |
| `L1_person_rot` | personpunkt = `cam_t_ra` (gammal) | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,334 |
| `L1_ljus_60` | ljus ±60°/σ45 (gammal) | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,512 |
| `L1_sift_av` | SIFT-kameragrupper av | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,527 |
| `L1_r15_sikt` | R15 längs siktlinjen (gammal) | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,149 |
| `L1_alla_gamla` | `pa` 3D + personpunkt + ljus 60 | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 2,425 |
| `X_ljus60_yaw_en` | ljus 60 + en yaw | A vid eget bord; B vid eget bord | 0,997 | ja / ja | 3 | 2,594 |
| `X_ljus60_bugg1_gammal` | ljus 60 + hela bugg 1 av | A vid eget bord; B vid eget bord | 1,000 | ja / ja | 3 | 3,514 |
| `X_allt_gammalt` | allt ovan tillbaka samtidigt (L1 + L2 + konstanter) | A vid eget bord; B vid eget bord | 1,000 | **NEJ** / **NEJ** | 4 | 6,67 |
| `G_geometrisk_reid` | utan dekl. och utan Gemini-semantik | A vid eget bord; B vid eget bord; D vid eget bord | 0,864 | ja / ja | 4 | 2,314 |

Slutsatser ur tabellen:
- **Ingen enskild rättning är nödvändig.** Varje Lager 2-rättning, alla Lager 2-rättningar samtidigt, varje Lager 1-rättning och alla Lager 1-rättningar samtidigt: s7 kopplas ändå. Först när allt återställs samtidigt (`X_allt_gammalt`) kommer den gamla felbilden tillbaka: kopiebord i s7 och A↔B 6,67 m (gamla kedjan 6,76 m). Det visar också att harnessen fångar den gamla kedjans beteende. Kopplingen är alltså överbestämd: två oberoende vägar räcker var för sig (nya Lager 2 på gamla observationer, §3.2, och nya observationer med gammal Lager 2).
- **Avståndet är inte robust.** A↔B varierar 2,31–3,60 m mellan varianter som alla "lyckas". Det styrs av personpunkten (bål eller MHR-rot), R15-riktningen och ljuskonstanten, inte av ny evidens.
- Argons påstående i ARKITEKTUR §3, att just de fyra rättningarna löste kopplingen, stämmer bara för den gamla kedjan och bara för 1a+1b tillsammans.


---

## 4. A6 – klippspecifik kod

### 4.1 grep i `forvarld_karna/` (Lager 1–2)
| plats | vad | typ |
|---|---|---|
| `regler.py:61` | `"bonaqua": 3.5` (märkesnamn i prislistan, slår före `"burk": 3.2` eftersom nyckeln delas på `_` och första träff vinner) | klippnamn i data |
| `obs_motor.py:439–458` | `_modell_semantik`: matchar `scen/3d/kontrakt/semantik/ut/<namn>` mot ingestmappen med `startswith(namn + "-")`, likhet, eller delsträng vid ≥ 3 tecken | mappnamnsheuristik |
| `obs_motor.py:51–62` | `_fokal`: fokal ur `fyra_klipp.json` (b-tilltal-ravara, e-dialog-guacamole, notan, kand-kennysgelato) via `startswith`; asketch saknas och får kedjans fokal | klippnamn i data (ärvt) |
| `obs_motor.py:159–165` | lodlinjen klämd till pitch ≤ 18°, roll ≤ 8° ("lutande glasdiskar … glassdisk") | konstant införd för gelato |
| `obs_motor.py:364–365, 372` | väggar bara 0,3–6,5 m ("14 000 m i asketch") | konstant |
| `obs_motor.py:671–672` | två namngivna personer och ett bord: bordet läggs mitt emellan ("Guacamole S4") | regel för ett fall |
| `obs_motor.py:228, 235` | skivdetektion kräver 25 000 och 15 000 px (absoluta pixlar, beror på djupkartans upplösning) | konstant |
| `obs_motor.py:719, 725, 749, 680, 688` | `vid` 1,6/1,35 m, `pa` 0,95 m, bäring 35°, R15 0,55 m | konstanter (nya eller ändrade) |
| `obs_motor.py:783–786` | ljus ±85° (σ 40°), tidigare ±60° (σ 45°) | ändrad konstant |
| `rums_pussel.py:593, 874, 920, 749–768, 357, 307–309` | R22 −4,0; yaw 70°/8°; grind 2,0·(σ+σ); klusterflytt 0,3/1,0/0,8/2,2/2,8 m; R24 35°; kameradelning 0,25 m/8° | konstanter utanför `regler.py` |
| `regler.py` | `vid_avstand_m` 0,75 → 0,65; burk/flaska 2,5 → 3,2; mugg 0,3 → 0,4 | ändrade talvärden |

### 4.2 Mappnamnsprov (`rum_namnprov.py` → `rum_ut/namnprov.json`)
| påhittat ingestnamn (finns inte) | får semantik från | roller | fokal |
|---|---|---|---|
| `a-dialog-kafe-tagningar` | **a-sketch** (pizzeria, danska) | P1: S1,S7; P2: S2–S5 | – |
| `b-ny-kund-tagningar` | **b-tilltal** (slaktare) | P1–P3 över S1–S11 | – |
| `kennys-burgare-tagningar` | **gelato** | P1: S1,S2 | – |
| `bonotanical-tagningar` | **notan** | P1–P3 | – |
| `notan-tagningar-v2` | notan | P1–P3 | 983,7 px |
| `z-helt-okant-tagningar` | ingen | – | – |

Ett nytt klipp vars mapp börjar på `a-` eller `b-` får ett annat klipps personer, spår och hållningar utan varning. Det är klippspecifik data som styrs av namnet. Notans semantik (Gemini) innehåller dessutom svaret i klartext ("mannen sitter vid ett helt annat bord"). Koden läser bara `hallning`, men källan är inte "blind".

### 4.3 Deklarationsfritt utan semantik
`obs_motor._roller_ur_kalla` har tre nivåer: deklaration/konsensus, sedan Gemini-semantik (via mappnamn), sedan `_geometrisk_reid_och_pose` (SIFT-grupper och knävinkel). Argons "deklarationsfritt" har bara prövat nivå 2. Nivå 3 provas här genom att sätta `sem = None` (`G_geometrisk_reid`, med `--utan-deklaration`):

| klipp | roller/hållning med deklaration eller semantik | nivå 3 (ren geometri) | sluttro nivå 3 |
|---|---|---|---|
| notan | A, B sittande; C stående; B i S7 | **alla 6 sittande blir "staende"**; B i S7 blir **D** | "A vid eget bord; B vid eget bord; **D** vid eget bord" (P 0,86) |
| guacamole | A sittande, B stående; S4 = A + B | A blir "staende"; S4 = **C** + okänd; disken når inte s4 | "A och B vid samma bord" (P 0,62), 2 bord |
| gelato | en person, A, i S1 och S2 | delas i **A och B** | "**A och B** vid samma bord" (P 0,82) |
| asketch | A (S1, S7), B (S2–S5) | B delas i **B, C, D** | samma kärntro (P 0,73) |
| b-tilltal (hold-out) | A, B, C (C i S5–S11) | C delas i **C och D** | "B och D vid samma bord" (P 0,74) |

Den rent geometriska vägen ger fel identitet eller hållning på 5 av 5 klipp. Knävinkeltestet (`cos_kna < 0,65`) klassar sittande personer bakom bord som stående, och SIFT-grupper knyter inte ihop samma person över vinkelbyten. Utan Gemini-semantik, som hämtas via mappnamn, finns ingen fungerande deklarationsfri person-re-ID. Det begränsar 6.4.1.

### 4.4 Känslighet ±30 %
Varje konstant ändras med × 0,7 och × 1,3, en i taget, och hela Lager 1–2 körs om (Lager 1 bara när konstanten sitter där). "Håller" betyder samma kärntro och samma bordsstruktur som `bas`; för notan räcker det att s7-kopplingen och kärntron står. Konstanterna och deras källrader står i `rum_ablation.py` (prefix `S_`); sammanställningen finns i `rum_ut/kanslighet.md` (`rum_kanslighet.py`).

| klipp | varianter | håller | bryter | A↔B-spann (bas) |
|---|---|---|---|---|
| notan | 21 | 20 | fokal × 0,7: s7-kopplingen bryts (4 bord) | 2,99–4,22 m (3,53) |
| guacamole | 32 | 31 | fokal × 0,7: disken binds bara i s2, kärntron blir "B vid eget bord" | 0,88–1,33 m (1,15) |
| gelato | 52 | 52 | – (flera varianter saknar verkan här: ingen VLM-data för ljus, föremål eller `pa`, och ingen sittande) | – |
| asketch | 30 | **25** | lodlinjeklämma × 0,7; `bord_minsta_avstand_m` × 0,7 **och** × 1,3; `pris_bakgrundsbord` × 0,7; `vid_avstand_m` × 0,7 (blir "A och B vid samma bord") | 0,48–0,78 m (0,48) |

Rättningar avstängda (samma körningar, tabell §3.6 för notan):

| klipp | avviker från bas |
|---|---|
| notan | bara `X_allt_gammalt` (allt samtidigt) och `G_geometrisk_reid` |
| guacamole | bara `G_geometrisk_reid` |
| gelato | `L1_klamp_av`, `L1_person_rot`, `L1_alla_gamla`, `X_allt_gammalt` (glassdisken försvinner ur s2), `G_geometrisk_reid` |
| asketch | `L1_person_rot` ("A och B vid samma bord; flyttat: B"), `X_allt_gammalt` |

Slutsatser:
- Notan och guacamole tål ±30 % på alla prövade konstanter utom fokalen. Fokalen är en klippspecifik tabellpost (`fyra_klipp.json`), och −30 % ligger nära MoGe:s egen skattning (−22 %, där kopplingen fortfarande står men A↔B blir 2,99 m).
- Gelato behöver lodlinjeklämman (pitch ≤ 18°, roll ≤ 8°), som infördes för just gelatos glasdisk. Utan den syns disken inte i s2. Klämman tål ±30 %, men regeln är ett exempel på en konstant som infördes för att ett klipp skulle gå igenom.
- Asketch är skör: 5 av 30 ändringar bryter resultatet. Två av dem är samma regel, bordsavståndet 1,0 m, åt båda hållen. Det stämmer med §5: lösningen ligger mot gränserna.

---

## 5. Asketch (6.2) – återskapas, men geometrin är degenererad
Omkörningen är byte-identisk med Argons recept:

| mått | värde |
|---|---|
| rum | 2,4992 × 2,4992 m = `rum_min_m` 2,5 (straffgräns), alla fyra väggar "observed" |
| A↔B (kund–personal över glasdisk) | 0,48 m (person–person-gräns 0,5 m) |
| A → `bord_1` (sitt bord) / `bord_2` | 0,74 / **0,25** m |
| B → `bord_2` (sitt bord) / `bord_1` | 0,71 / **0,34** m |
| `bord_1` ↔ `bord_2` | 0,97 m (bord–bord-gräns 1,0 m) |

Båda personerna står närmare den andras bord än sitt eget, och A står 0,25 m från en bordsmitt, alltså inne i bordet (`MATT["bord"]` 1,2 × 0,6 m). Lager 2 saknar kollision mellan person och bord. Lösningen ligger mot tre gränser samtidigt (rumsminimum, personavstånd, bordsavstånd). "Ett sammanhängande gatuköksrum, P 0,86" är rätt som kärntro, men 2D-layouten är inte fysiskt rimlig.

Guacamole och gelato återskapas enligt 6.2: bord_1 s1–s4 conf 0,761 och A↔B 1,151 m; gelato CAM_s1 −0,2° och CAM_s2 +63,0°.

---

## 6. Hold-out: b-tilltal-ravara-tagningar
Av klippen i `scen/3d/ingest/ut/` har bara b-tilltal komplett ingest (11 tagningar med `sekvens_*.npz`, `rum/depth`, `rum.json` och `personer.json`). `c-sketch-tre-tagningar` har en tagning utan sekvens och djup; `bar`, `biljard`, `bar_mask` och `bar-fore-omkorning` är tomma. Det finns ingen VLM-cache och inget omaskat djup för b-tilltal, så ljus, föremål och dörrar saknas.

| | resultat |
|---|---|
| körning | Lager 1 195 s, Lager 2 121 s, ingen krasch |
| roller | A (S1–S2), B (S3–S4), C (S5–S11), alla stående: stämmer med deklaration och semantik |
| SIFT-delning | s2→s1, s4→s3, s7→s6, s9→s8, s10→s8 |
| sluttro | "B vid eget bord; C vid eget bord", P 0,975 |
| bord | 4 entiteter (s4; s6; s7+s8; s10), alla zoner med conf 0,02 |
| personer | A conf 0,80. B och C är zoner med conf 0,02. A är inte bunden till något bord. |
| facit-ish | `deklaration.json`: "En slaktarbutik, ett rum", en `disken`. Semantiken säger "Står bakom charkdisken" för P1, P2 och P3 |

Ett rum och inga påhittade flyttar är rätt. Disken bryts däremot upp i fyra bord, även mellan tagningar som enligt SIFT delar kamera (s6/s7). Kärntron går emot både deklarationen och semantiken, med P 0,98, medan lägena är obestämda. Detta är ett mot-exempel för allmängiltighet, inget bevis för att motorn är fel om alla avstånd: det finns inget metriskt facit.
Utan deklaration (`--utan-deklaration`) blir `obs.json` byte-identisk. Receptet har samma sluttro men skiljer på 58 rader: flyttal i femte decimalen och P i s7 0,952 mot 0,962. Det är samma obs i båda körningarna, så skillnaden är icke-determinism i Lager 2 (jfr §2.2). Utan Gemini-semantik (`G_geometrisk_reid`) delas C i två personer (C i S5, D i S6–S11), och sluttron blir "B och D vid samma bord" (P 0,74).

---

## 7. PROTOKOLL – föreslagna uppdateringar

| id | ny status | motprov som avgjorde | nästa motprov |
|---|---|---|---|
| A5 | delvis | omkörning: obs med = utan dekl på 4/4. De lagrade notan-filerna går inte att återskapa (A↔B 2,85 → 3,53 m) | kör om `verifiera.py` och checka in utdata med kodens hash; fixa `PYTHONHASHSEED` |
| A6 | delvis faller | `rum_namnprov.py`; grep §4.1; känslighet §4.4 (asketch 5/30 bryter; gelato kräver klämman; fokalen är en klipptabell) | ta bort `"bonaqua"`; kräv exakt klipp-id för semantik/fokal; flytta konstanter till `regler.py` |
| R1 | faller (siffror), står (koppling) | §2.3 | – |
| R2 | faller | §3.1 | oberoende metriskt mått i S7 (t.ex. känd bordsbredd mot båda borden, oberoende av SAM) |
| R3 | faller (orsak), står (1a+1b räcker på gammal data) | `rum_gammal.py` | – |
| R4 | står (bugg), faller (förklaring) | höjdmätning §3.3 | – |
| R5 | delvis | gamla yaw −81…−85°; ablation | pröva ±60/±85 på klipp utan motbild |
| R6 | faller | grep + `null` i obs | – |
| R7 | delvis | §5 | inför person–bord-kollision i Lager 2 och kör om asketch |
| R8 | svagt | §6 | fler hold-out-klipp med full ingest |
| R9 | faller (reserven) | `G_geometrisk_reid` på 5 klipp, §4.3 | knävinkel bara när benen syns; re-ID över vinkelbyte med annan signal än SIFT-bakgrund |
