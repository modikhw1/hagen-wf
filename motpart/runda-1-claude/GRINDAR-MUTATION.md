# Mutationstest av kvalitetsgrindarna G1–G7 (lane A3)

Runda 1, Claude, 19 nov 2026. Ingenting i `forvarld_karna/` eller `byggsten/` är ändrat. All kod ligger i den här mappen med prefixet `grind_`.

| fil | vad |
|---|---|
| `grind_mutation.py` | felkatalog, läge a (rå grind), läge b (fel före efterbehandling, facit mot omuterad kompilering), ablation |
| `grind_harda.py` | H-serien: härdade grindar med känd källa och uppmätt känslighet |
| `grind_bevis.py` | räknar om z-normaliseringen (`scen_brygga.py:317–344`) per tagning och ritar 2D-överlägget `grind_bevis_h7.png` |
| `grind_resultat.json` | varje mutation och mål: status per grind (L/F/N/tyst), facit, ablation |
| `grind_logg.txt` | utskrift från senaste körningen (matriserna nedan är kopierade därifrån) |

Reproduktion (PowerShell, repo-roten; senaste körningen tog 12 min med 6 processer):

```powershell
$env:PYTHONIOENCODING="utf-8"
.\scen\.venv\Scripts\python.exe motpart\runda-1-claude\grind_mutation.py          # läge a + b + ablation
.\scen\.venv\Scripts\python.exe motpart\runda-1-claude\grind_harda.py             # H-serien på de 4 lagrade paketen
.\scen\.venv\Scripts\python.exe motpart\runda-1-claude\grind_bevis.py             # z-normalisering + överlägg
```

---

## 0. Påståenden från den här rundan

A3 är Argons påstående från runda 0. A3.1–A3.6 är nya påståenden från den här rundan. Varje rad har ett motprov som Argon kan köra. Status enligt `PROTOKOLL.md`.

| id | påstående | belägg | motprov | status |
|---|---|---|---|---|
| A3 | G3/G4 = 0 fel visar att kroppen sitter rätt och inte går genom möbler | §3.3–3.4: G3 mäter avståndet till en stol som placerats 0,10 m under samma bäcken (`scen_brygga.py:480`); G4 mäts efter att `_dra_in…` flyttat ut leder och R1 dolt kolliderande bord | `grind_mutation.py`: genom_disk larmar G4 i 14/21 i läge a och 0/21 i läge b; ablation R1 av ger G4-fel 5 (asketch) och 3 (notan) | **fallit** |
| A3.1 | `grindar.mat` mäter inte alla personer | en rad per tagning; personslingan skriver över `rad` (`grindar.py:83–133`). guacamole s4 A och notan s4 C mäts aldrig | sank_04 och utanfor_bild: G2 respektive G5 missar exakt dessa två spår (19/21) | står |
| A3.2 | G7 kan inte larma på kroppsfel | G7 läser lagrad `paket["trohet"]` (`grindar.py:120`), som räknas mot kroppens egen projektion (`scen_brygga.py:371–373, 418`) | 0 larm i läge a över alla 279 mutationer; i läge b larmar G7 bara när R3 ändrar fötterna (skala_15 5/21, pose_flip 1/21) | står |
| A3.3 | G1 kan inte larma på scen_brygga-utdata | scen_brygga skriver ett rum och `rum="gemensamt"` på alla objekt (`scen_brygga.py:461–606`). Positiv kontroll rum_fel larmar 4/4, så koden fungerar men indata är konstant | G1 larmar i läge b 0/284; i läge a bara på etikettbyte mellan två sittande med egen stol (notan, 6/17) | står |
| A3.4 | R3 fotkontakt maskerar G2 | G2 larmar på sank_04 i 19/21 (läge a) men 0/21 (läge b). Ablation: R3 av → G2-fel guacamole 4, notan 6 | `grind_mutation.py --lage b`, ablation `("R3",)` | står |
| A3.5 | z-normaliseringen flyttar höjdfel från kroppen till kameran | sank_04 läge b: i 13/21 är kroppen tillbaka (≤ 0,06 m) och kameran 0,26–0,40 m fel; G larmar inte i 16 av 20 kvarvarande fel | `facit.kamera_m` i `grind_resultat.json`; `grind_bevis.py` återskapar paketets kamerahöjd exakt för alla 21 tagningar | står |
| A3.6 | Baslinjen har fel som G1–G7 inte ser | H-serien: §5. Två av dem är bekräftade i bild (överlägg notan s7, gelato s1), andra i Argons egna Blender-jämförelser | `grind_harda.py`, `grind_bevis_h7.png`, `ut/guacamole/jamforelse.png` | delvis (se §5 för vilka som är bekräftade) |

---

## 1. Metod

### 1.1 Felkatalog och mål

Varje mutation körs på varje mål där den är meningsfull, så att varje cell i matrisen är en andel och inte ett enskilt exempel.

| mutation | mål | läge a (paket.json) | läge b (före efterbehandling) |
|---|---|---|---|
| sank_04 | varje personspår (21) | leder z −0,4 m | SAM-rådata (`pose`, `cam_t_ra`) transformerade så att kroppen i världen ligger 0,4 m lägre |
| sank_04_delvis | 21 | −0,4 m i första 40 % av rutorna (mittrutan orörd) | samma i rådata |
| lyft_05 | 21 | +0,5 m | rådata |
| vand_180 | 21 | 180° kring lodaxeln genom c_spine2 | rådata, inklusive ledernas kvaternioner |
| genom_disk | 21 | bröstet till närmaste (synliga) bords mitt i xy | rådata, mot närmaste recept-bord |
| utanfor_bild | 21 | 3 m i kamerans sidled | rådata |
| teleport | 21 | 1,5 m sidled från halva tagningen | rådata |
| skala_15 | 21 | kroppen ×1,5 kring bröstet | rådata |
| byt_id | 17 tagningar | tvåpersonstagning: rörelserna byts; enperson: fel etikett | tvåperson: personernas ordning i obs vänds (spår tilldelas efter ordning, `scen_brygga.py:279`); enperson: `nyckel` byts |
| pose_flip | 21 detektioner | – | `pose` sittande ↔ stående i obs |
| kamera_1m_sida/bak/upp | 19 tagningar med person | kameranycklar flyttas 1 m | `recept.kameror[].position` flyttas 1 m |
| bord_2m / bord_bort / bord_svav_05 | 7 bord | objektet flyttas, tas bort, lyfts | recept-noden flyttas, tas bort, lyfts |
| stol_bort / stol_05 / stol_sank_03 | 4 stolar | stolen tas bort, flyttas 0,5 m i x, sänks 0,3 m | – (stolen skapas av pipelinen) |
| rum_fel | 4 klipp | positiv kontroll för G1: ett objekt flyttas till ett rum utan tagningar | – |

Läge b kör hela `kompilera_scenpaket` med alla steg: z-normalisering med kamerajustering, R25, R3, stol under bäckenet, kontaktkalibrerad disk, `_dra_in_dolda_ben_bakom_massiv_disk`, R1-döljning och trohetsberäkning. Injektionen sker genom att modulglobaler i den importerade `scen_brygga` byts ut under körningen (`np.load` för en utvald `sekvens_<spår>.npz`, `subprocess.run` till en tom funktion). Kroppsmutationerna i rådata är en exakt världstransform: `scen_brygga.py:322–323` ger `w = R·c + C`, så transformen uttrycks i kameraram som `A = Rᵀ M R` på ledoffseten och `Δct = (Rᵀ t / κ)·F` på rottranslationen (`grind_mutation.py:_kropp_fn_raw`).

### 1.2 Vad räknas som larm

Per grind och mål:

- **L, larmar**: minst en rad som inte var fel i omuterad baslinje blir fel.
- **F, redan fel**: målraden var redan fel i baslinjen, så grinden kan inte larma ytterligare. F räknas inte i nämnaren och redovisas separat.
- **N, slutade mäta**: en rad som var `ok=True` blir `ok=None` (grinden ger upp i stället för att larma).
- byt_id jämförs som antal fel per (tagning, grind), eftersom personnamnen byts.

Cellerna nedan är `larm/mätbara mål`, följt av `F` och `N` när de förekommer.

### 1.3 Facit i läge b

Det muterade paketet jämförs med en omuterad kompilering av samma kod: median ledavvikelse per spår, kamerans medelposition per tagning, objektens position, mått och `synlig_ut`, samt saknade spår. Om någon avvikelse överstiger 0,05 m, eller ett objekt eller spår ändrats, finns felet **kvar** efter efterbehandlingen. Ett kvarvarande fel utan larm är **maskerat**. Ett fel som försvinner helt har pipelinen **återställt**, och det räknas inte som maskering.

### 1.4 Reproducerbarhet hos baslinjen

En omkompilering med nuvarande `scen_brygga.py` ger bit-identiskt `paket.json` (utom `proveniens`) för guacamole, gelato och notan. **asketch skiljer**: det lagrade paketet har bordsmått 1,50 × 0,48 m och `bord_1.synlig_ut=[[0,60],[590,680]]`, nuvarande kod ger 1,45 × 0,44 m och `[[0,139],[590,680]]`. Det lagrade `ut/asketch/paket.json` kommer alltså inte från den kod som ligger i repot. Läge a mäter de lagrade paketen (det är dem påståendet "0 fel" gäller), och läge b samt ablationen mäter nuvarande kod.

---

## 2. Matris G1–G7

Celler: `larm/mätbara mål`, F = redan fel i baslinjen, N = grinden slutade mäta. Fet = minst ett larm.

### 2.1 Läge a: fel i färdigt paket (279 mutationer)

| mutation | n | G1 rum | G2 golv | G3 sate | G4 genom | G5 ibild | G6 skymning | G7 trohet |
|---|---|---|---|---|---|---|---|---|
| sank_04 | 21 | 0/21 | **19/21** | **9/21** | **5/21** | **4/21** | 0/21 | 0/21 |
| sank_04_delvis | 21 | 0/21 | 0/21 | 0/21 | **4/21** | 0/21 | 0/21 | 0/21 |
| lyft_05 | 21 | 0/21 | 0/21 | **9/21** | 0/21 | **5/21** | 0/21 | 0/21 |
| vand_180 | 21 | 0/21 | 0/21 | 0/21 | **1/21** | **3/21** | 0/21 | 0/21 |
| genom_disk | 21 | 0/21 | 0/21 | 0/21 | **14/21** | **13/21** | 0/21 | 0/21 |
| utanfor_bild | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **19/21** | 0/21 | 0/21 |
| teleport | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **18/21** | 0/21 | 0/21 |
| skala_15 | 21 | 0/21 | **19/21** | **8/21** | **6/21** | **1/21** | 0/21 | 0/21 |
| byt_id | 17 | **6/17** | 0/17 | **1/17** | 0/17 | 0/17 | 0/17 | 0/17 N15 |
| kamera_1m_sida | 19 | 0/19 | 0/19 | 0/19 | 0/19 | **18/19** | 0/19 | 0/19 |
| kamera_1m_bak | 19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 |
| kamera_1m_upp | 19 | 0/19 | 0/19 | 0/19 | 0/19 | **15/19** | 0/19 | 0/19 |
| stol_bort | 4 | 0/4 | 0/4 | 0/4 N4 | 0/4 | 0/4 | 0/4 | 0/4 |
| stol_05 | 4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| stol_sank_03 | 4 | 0/4 | 0/4 | **4/4** | **1/4** | 0/4 | 0/4 | 0/4 |
| bord_2m | 7 | 0/7 | 0/7 | 0/7 | **2/7** | 0/7 | 0/7 | 0/7 |
| bord_bort | 7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 |
| bord_svav_05 | 7 | 0/7 | 0/7 | 0/7 | **2/7** | 0/7 | 0/7 | 0/7 |
| rum_fel | 4 | **4/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |

### 2.2 Läge b: fel före efterbehandling (284 mutationer, 0 körfel)

| mutation | n | G1 rum | G2 golv | G3 sate | G4 genom | G5 ibild | G6 skymning | G7 trohet | felet kvar efter efterbehandling | kvar men inget G-larm | kvar men inget H-larm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sank_04_delvis | 21 | 0/21 | 0/21 | 0/21 | **1/21** | 0/21 | 0/21 | 0/21 | 10/21 | 10/10 | 0/10 |
| sank_04 | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **4/21** | 0/21 | 0/21 | 20/21 | 16/20 | 3/20 |
| lyft_05 | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **2/21** | 0/21 | 0/21 | 15/21 | 13/15 | 4/15 |
| vand_180 | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **3/21** | 0/21 | 0/21 | 21/21 | 18/21 | 0/21 |
| genom_disk | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **7/21** | 0/21 | 0/21 | 21/21 | 14/21 | 3/21 |
| utanfor_bild | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **19/21** | 0/21 | 0/21 | 21/21 | 2/21 | 0/21 |
| teleport | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **18/21** | 0/21 | 0/21 | 21/21 | 3/21 | 0/21 |
| skala_15 | 21 | 0/21 | 0/21 | 0/21 | 0/21 | **1/21** | 0/21 | **5/21** | 21/21 | 15/21 | 3/21 |
| pose_flip | 21 | 0/21 | 0/21 | 0/21 N9 | **8/21** | 0/21 | 0/21 | **1/21** | 20/21 | 12/20 | 5/20 |
| byt_id | 17 | 0/17 | 0/17 | 0/17 N1 | 0/17 | 0/17 | 0/17 | 0/17 | 17/17 | 17/17 | 4/17 |
| kamera_1m_sida | 19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 19/19 | 19/19 | 8/19 |
| kamera_1m_bak | 19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 19/19 | 19/19 | 7/19 |
| kamera_1m_upp | 19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 | 4/19 | 4/4 | 1/4 |
| bord_bort | 7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 7/7 | 7/7 | 0/7 |
| bord_svav_05 | 7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/0 | 0/0 |
| bord_2m | 7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 | 7/7 | 7/7 | 0/7 |

I läge b anger de tre sista kolumnerna: hur många mål där felet finns kvar efter all efterbehandling enligt facit (§1.3), och hur många av dessa som varken G-serien respektive H-serien larmar på.

**Läsning:**

- **G6 skymning larmar aldrig**, i någon mutation och i något läge.
- **G7 trohet larmar aldrig i läge a** (0 av 279). I läge b larmar G7 bara när R3 flyttar fötter (skala_15 5/21, pose_flip 1/21), eftersom referensen `X_RA_2D` är kroppens egen projektion.
- **G1 rum** larmar på scen_brygga-utdata bara på etikettbyte mellan två sittande personer som båda har egen stol (notan). Den positiva kontrollen (4/4) visar att koden fungerar.
- **G2 golv** går från 19/21 (a) till 0/21 (b) på sank_04. **G4 genom** går från 14/21 till 0/21 på genom_disk.
- **G5 i bild** är den enda grind som behåller känslighet i läge b (utanför bild 19/21, teleport 18/21).
- **Blinda i båda lägena:** stol 0,5 m bort (0/4), bord borttaget (0/7) och kamera 1 m bakåt (0/19).
- **Blinda i läge b:** kamera 1 m i sidled (0/19), bord 2 m (0/7) och byt identitet (0/17). Nästan blinda: vänd 180° (3/21) och lyft 0,5 m (2/21).

---

## 3. Blinda och maskerande grindar

### 3.1 Strukturellt fel i `grindar.mat`: en rad per tagning

`grindar.py:83` skapar `rad` per tagning och `:84–132` skriver G2–G7 för varje personspår i samma dict, så den sista personen skriver över den första. I tvåpersonstagningar mäts bara den sista: guacamole s4 visar B (A mäts aldrig), notan s4 visar person_4 (C mäts aldrig). Det är 2 av 21 spår.

**Motprov:** sank_04 och utanfor_bild i läge a larmar G2 respektive G5 i 19/21, och de två missarna är exakt `guacamole s4 A` och `notan s4 C` (`grind_resultat.json`). I läge a missar byt_id i guacamole s4 (A och B byter rörelser) alla G-grindar av samma skäl.

### 3.2 G2 golv: maskeras av R3 och mäter bara median

- R3 (`fotkontakt`, `scen_brygga.py:105–138`) lyfter varje fotled under 0,055 m till 0,065 m med 2-leds-IK. G2 kräver median ≥ −0,05 m. Efter R3 kan G2 inte falla för fotleden. **Ablation:** R3 av → G2-fel guacamole 4 tagningar och notan 6 tagningar. Råa SAM-fötter ligger 0,10–0,34 m under golvet i guacamole (`grind_bevis.py`: `ra_fot_z`).
- Läge b, sank_04: G2 0/21. Stående personer med fötterna under golvet får ingen uppåtskift (`scen_brygga.py:330` skiftar bara nedåt), så R3 böjer knät och kroppen hamnar på huk (H3_hallning larmar, G2 tyst).
- sank_04_delvis: 0/21 även i läge a, eftersom G2 mäter median över rutorna.
- G2 har ingen övre gräns: lyft_05 (kropp 0,5 m i luften) larmar aldrig G2.

### 3.3 G3 säte: tautologisk

- Stolen skapas med `sits_topp = max(0.35, median(bäcken_z) − 0.10)` och med xy = bäckenets median (`scen_brygga.py:478–488`). G3 mäter `median(bäcken_z) − sits_topp` och får därmed 0,10 m för varje sittande spår där bäckenet ligger över 0,45 m. Utfall i baslinjen: 0,10 i 8 av 10 sittande spår, 0,06 och 0,144 i de två övriga (stolen sätts på medianen över personens alla tagningar).
- G3 mäter bara z. stol_05 (stolen 0,5 m bort) larmar 0/4.
- Saknas stolen blir G3 `ok=None` ("inget säte"), inte fel. stol_bort ger N4.
- Läge b: sank_04, lyft_05 och genom_disk på sittande personer larmar G3 0 gånger, eftersom stolen följer bäckenet. pose_flip sittande → stående ger N9 (G3 slutar mäta).
- Den enda G3-känsligheten är att sänka stolen själv (stol_sank_03, 4/4), vilket pipelinen aldrig gör.

### 3.4 G4 genom: två maskerande steg i serie

1. `_dra_in_dolda_ben_bakom_massiv_disk` (`scen_brygga.py:141–174`) letar leder inom diskens halva mått + 0,02 m och flyttar dem till + 0,025 m (sidan) eller ovanpå skivan + 0,015 m (armar). G4 räknar en led som inne först vid halva mått − 0,01 m (`grindar.py:inne`). En flyttad led ligger alltså minst 2,5 cm utanför grindens låda och kan inte räknas. Flytten görs led för led utan IK (benlängder ändras) och skrivs inte i `beslut`. Uppmätt via omslag: 157 led-rutor i guacamole och 77 i gelato.
2. R1-döljningen (`scen_brygga.py:548–596`) tar bort ett bord ur en tagning när fler än 5 % av rutorna har en led inne i det (kollisionsskydd), eller när det skymmer mer än 25 % av överkroppen (skymningsskydd). G4 hoppar över objekt som inte är synliga (`grindar.py:103`).

**Ablation** (nuvarande kod, inga mutationer):

| klipp | G4-fel: allt på | `_dra_in` av | R1 av | allt av |
|---|---|---|---|---|
| guacamole | 0 | 0 (R1 döljer i stället ett bord till) | 0 | 1 |
| gelato | 0 | 0 (R1 döljer i stället) | 0 | 1 |
| asketch | 0 | 0 | **5** | **5** |
| notan | 0 | 0 | **3** | **2** |

Läge b, genom_disk: G4 0/21 (läge a 14/21). Dessutom ser G4 bara leder, inte ben. En kropp kan passera en 6 cm bordsskiva mellan två leder. I läge a missar G4 genom_disk på synliga bord i gelato s2, notan s3 A och notan s5 B; notan s4 C är överskrivningen i §3.1. H4 med 3 punkter per ben larmar 11/11 mätbara på genom_disk i båda lägena; med bara leder (första körningen) larmade samma grind 8/11.

Notera: docstringen säger "massiv disk ner till golvet" (`scen_brygga.py:11–13`), men koden bygger en 0,14 m skiva (`:524–526`).

### 3.5 G5 i bild: bara mittrutan

G5 mäter en ruta per tagning (`grindar.py:113`). Fel som inte rör mittrutan syns inte (sank_04_delvis 0/21). G5 larmar på kamera 1 m upp i läge a (15/19), men i läge b återställer z-normaliseringen kamerahöjden i 15 av 19 fall och G5 larmar 0/19.

### 3.6 G6 skymning: R1 tar bort det G6 skulle mäta

R1_skymningsskydd tar bort ett bord vid 25 % täckning (`scen_brygga.py:582`). G6:s gräns är 30 %. I guacamole döljs bardisken i s1 och s4. Med R1 avstängt larmar G6 ändå inte, så döljningen är strängare än grinden: disken tas bort i tagningar där den syns i originalet (s4, se `ut/guacamole/jamforelse.png`), och ingen grind registrerar att ett observerat objekt saknas.

### 3.7 G7 trohet: mäter kroppen mot sig själv

`X_RA_2D` räknas från samma `t1_pts` och samma kamera som paketet (`scen_brygga.py:371–373`). R25 flyttar kropp och kamera med samma delta. `_trohet_mot_2d` körs före `_dra_in` (rad 418 respektive 530), så diskflytten syns inte ens i den egna jämförelsen. Det enda G7 kan se är R3:s fotflytt. Uppmätt: 0 larm i läge a. I läge b larmar G7 bara där R3 flyttar fötter.

A1-lanen (`g7_oberoende.py`) bygger en G7 mot oberoende 2D. Det här dokumentet visar bara att nuvarande G7 inte kan larma.

### 3.8 z-normaliseringen: kameran som slackvariabel

`scen_brygga.py:329–344`: sittande bäcken flyttas till 0,55 m (eller till personens första sittande tagning) och stående fötter nedåt till 0,065 m. För första personen i tagningen flyttas kameran lika mycket (`C_z = max(0.92, C_z + z_skift)`), så projektionen bevaras och felet hamnar i kamerahöjden. `grind_bevis.py` räknar om stegen och återskapar paketets kamerahöjd exakt för alla 21 tagningar.

- **Kamerahöjd mot obs:** paketets kamera avviker upp till 0,65 m från obs `hojd_m` (asketch s1: 1,894 → 1,243 m, 5,4 σ).
- **Golvet 0,92 m:** när kameran slår i golvet flyttas kroppen relativt kameran. notan s7: `z_skift −0,659`, kameran stoppas vid 0,92 m, kroppen hamnar 0,341 m för lågt relativt kameran. gelato s1: 0,144 m. 2D-projektionen bryts (§5, `grind_bevis_h7.png`), men G7 ser det inte eftersom `X_RA_2D` redan innehåller flytten.
- **Läge b, sank_04:** i 13/21 hamnar hela felet i kameran (kroppen ≤ 0,06 m från baslinjen, kameran 0,26–0,40 m fel). G1–G7 larmar inte i 16 av de 20 kvarvarande felen. Det oberoende 2D-spåret (H7) larmar i 15/19.

Utanför min lane, men mätbart: `R_cam = _euler_xyz_till_mat(90, 0, yaw)` (`scen_brygga.py:254`) kastar receptets pitch och roll. Höjdfelet som z-normaliseringen rättar korrelerar med `djup · sin(pitch)` (r = 0,74, n = 14 tagningar med `z_skift ≠ 0`; obs-pitch för gelato/asketch ligger på −18°, som ser ut att vara en klämgräns). Hypotes till kamera-lanen: en stor del av z-skiften, och därmed kamerahöjdsfelet, kommer av den tappade pitchen. Status: oprövat.

---

## 4. Härdade grindar (H-serien)

Princip: en grind får bara mäta något som efterbehandlingen inte redan har tvingat fram, mäter varje (tagning, person) för sig och gör det i varje ruta. Där det finns ett underlag som inte har passerat scen_brygga jämförs paketet mot det.

| grind | mäter | referens | oberoende av |
|---|---|---|---|
| H1_objekt | objekt som recept säger är observerat i tagningen finns och är synligt där | `recept.noder[].evidence_shots` | scen_brygga (R1-döljning) |
| H2_golv | andel rutor med fot < −0,05 m (inte median), plus att en stående persons lägsta led inte är > 0,15 m över golvet i > 25 % av rutorna | – | intern fysik |
| H3_sate | sittande: stol finns, bäckenet ligger inom sitsens fotavtryck + 0,10 m i ≥ 80 % av rutorna, sitshöjd 0,30–0,85 m | obs `pose` | stolplaceringen (mäter xy och existens) |
| H3_hallning | sittande: lår ≤ 45° och knä ≥ 0,30 m; stående: bäcken/benlängd ≥ 0,90 | obs `pose` | R3 och z-normaliseringen |
| H4_genom | genomträngning mot alla fysiska objekt **oavsett `synlig_ut`**, inklusive väggar, i leder och 3 punkter per ben | – | R1-döljningen (inte `_dra_in`, se §5) |
| H5_ibild | andel rutor med ≥ 70 % av överkroppen i bild ≥ 0,90 | – | mittrutan |
| H7_2d | projicerat huvud i övre halvan av ett 2D-spår i ≥ 70 % av rutorna | `personer.json` (YOLO/ByteTrack) | 3D-lyftet och scen_brygga |
| H8_skelett | benlängdernas variationskoefficient ≤ 0,05 inom spår; avvikelse ≤ 12 % mot personens övriga tagningar | – | fångar skala (16/17) och delvis identitet (6/13), men inte `_dra_in`:s flyttar på 2–4 cm (guacamole: 157 led-rutor, H8 tyst) |
| H9_identitet | projicerad bäring mot obs-bäringen för samma etikett, \|Δ\| ≤ max(6°, 4σ) | obs `bearing_deg` | scen_brygga |
| H10_kamera | kamerahöjd och pitch mot obs, ≤ 3σ | obs `hojd_m`, `pitch_deg` | z-normaliseringen |
| H11_vid | obs säger "vid bord" → ett bord observerat i tagningen inom 0,8 m och med skivan mellan bäcken − 0,30 och nacke − 0,15 | obs `vid`, recept | scen_brygga |
| H12_kontinuitet | bäckenets hastighet ≤ 8 m/s mellan sparade rutor | – | R25 |
| H13_stod | föremål vilar på en bordsskiva eller på golvet (≤ 0,05 m) | – | – |
| H14_djup | vågrätt avstånd kamera → bröst mot obs `djup_m`, ≤ max(3σ, 0,30 m) | obs `djup_m` | scen_brygga |
| H15_vridning | axellinjens vändning mot kameran mot obs `vridning_deg`, ≤ max(3σ, 60°) | obs `vridning_deg` | scen_brygga |

**Oberoendegrad, ärligt redovisat:** obs-personernas bäring, djup och vridning (`obs_motor.py:327–350, 711–735`) räknas ur samma `sekvens_<spår>.npz` som scen_brygga läser. H9, H14 och H15 fångar alltså fel som uppstår i eller efter scen_brygga (läge a, läge b, R25, z-normalisering), men **inte fel i själva SAM-lyftet**. H7 (YOLO-spåret) och H10 (MoGe-kamera) är de enda med en annan modell som källa. Gränserna är satta mot fördelningen på just dessa 4 klipp. Marginalen mot baslinjen redovisas i §5. Ett hold-out-klipp saknas.

### 4.1 H-seriens känslighet

#### Läge a

| mutation | n | H1 objekt | H2 golv | H3 sate | H3 hallning | H4 genom | H5 ibild | H7 2d | H8 skelett | H9 identitet | H10 kamera | H11 vid | H12 kontinuitet | H13 stod | H14 djup | H15 vridning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sank_04 | 21 | 0/14 F7 | **19/19** F2 | **10/21** | **10/10** F11 | **8/11** F10 | **4/21** | **17/19** F2 | 0/15 F6 | 0/21 | 0/10 F11 | **16/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| sank_04_delvis | 21 | 0/14 F7 | **19/19** F2 | 0/21 | **1/10** F11 | **5/11** F10 | **3/21** | **16/19** F2 | 0/15 F6 | 0/21 | 0/10 F11 | 0/21 | **21/21** | 0/21 | 0/21 | 0/21 |
| lyft_05 | 21 | 0/14 F7 | **9/19** F2 | **10/21** | 0/10 F11 | 0/11 F10 | **6/21** | **18/19** F2 | 0/15 F6 | 0/21 | 0/10 F11 | **10/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| vand_180 | 21 | 0/14 F7 | 0/19 F2 | 0/21 | 0/10 F11 | **2/11** F10 | **5/21** | 0/19 F2 | 0/15 F6 | 0/21 | 0/10 F11 | 0/21 | 0/21 | 0/21 | 0/21 | **21/21** |
| genom_disk | 21 | 0/14 F7 | 0/19 F2 | **10/21** | 0/10 F11 | **11/11** F10 | **15/21** | **16/19** F2 | 0/15 F6 | **15/21** | 0/10 F11 | **2/21** | 0/21 | 0/21 | **10/21** | **2/21** |
| utanfor_bild | 21 | 0/14 F7 | 0/19 F2 | **10/21** | 0/10 F11 | **4/11** F10 | **21/21** | **19/19** F2 | 0/15 F6 | **21/21** | 0/10 F11 | **17/21** | 0/21 | 0/21 | **19/21** | **11/21** |
| teleport | 21 | 0/14 F7 | 0/19 F2 | **10/21** | 0/10 F11 | 0/11 F10 | **20/21** | **18/19** F2 | 0/15 F6 | **21/21** | 0/10 F11 | **3/21** | **21/21** | 0/21 | **13/21** | 0/21 |
| skala_15 | 21 | 0/14 F7 | **19/19** F2 | **9/21** | **9/10** F11 | **5/11** F10 | **3/21** | **3/19** F2 | **16/17** F4 | 0/21 | 0/10 F11 | 0/21 | 0/21 | 0/21 | 0/21 | 0/21 |
| byt_id | 17 | 0/12 F5 | 0/16 F1 | **2/17** | **1/7** F10 | **1/8** F9 | 0/17 | 0/16 F1 | **6/13** F4 | **2/17** | 0/8 F9 | 0/17 | 0/17 | 0/17 | **1/17** | **1/17** |
| kamera_1m_sida | 19 | 0/14 F5 | 0/17 F2 | 0/19 | 0/9 F10 | 0/10 F9 | **18/19** | **17/17** F2 | 0/14 F5 | **19/19** | 0/8 F11 | 0/19 | 0/19 | 0/19 | **6/19** | **1/19** |
| kamera_1m_bak | 19 | 0/14 F5 | 0/17 F2 | 0/19 | 0/9 F10 | 0/10 F9 | 0/19 | **4/17** F2 | 0/14 F5 | **3/19** | 0/8 F11 | 0/19 | 0/19 | 0/19 | **18/19** | 0/19 |
| kamera_1m_upp | 19 | 0/14 F5 | 0/17 F2 | 0/19 | 0/9 F10 | 0/10 F9 | **15/19** | **17/17** F2 | 0/14 F5 | 0/19 | **8/8** F11 | 0/19 | 0/19 | 0/19 | 0/19 | 0/19 |
| stol_bort | 4 | 0/4 | 0/4 | **4/4** | 0/3 F1 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| stol_05 | 4 | 0/4 | 0/4 | **4/4** | 0/3 F1 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| stol_sank_03 | 4 | 0/4 | 0/4 | **4/4** | 0/3 F1 | **2/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| bord_2m | 7 | 0/7 | 0/7 | 0/7 | 0/6 F1 | **1/5** F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | **7/7** | 0/7 | **2/7** | 0/7 | 0/7 |
| bord_bort | 7 | **6/7** | 0/7 | 0/7 | 0/6 F1 | 0/5 F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | **7/7** | 0/7 | **2/7** | 0/7 | 0/7 |
| bord_svav_05 | 7 | 0/7 | 0/7 | 0/7 | 0/6 F1 | **1/5** F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | **7/7** | 0/7 | **2/7** | 0/7 | 0/7 |
| rum_fel | 4 | 0/4 | 0/4 | 0/4 | 0/3 F1 | 0/3 F1 | 0/4 | 0/4 | 0/4 | 0/4 | 0/2 F2 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |

#### Läge b

| mutation | n | H1 objekt | H2 golv | H3 sate | H3 hallning | H4 genom | H5 ibild | H7 2d | H8 skelett | H9 identitet | H10 kamera | H11 vid | H12 kontinuitet | H13 stod | H14 djup | H15 vridning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sank_04_delvis | 21 | 0/14 F7 | 0/19 F2 | 0/21 | 0/10 F11 | **3/11** F10 | **3/21** | **16/19** F2 | **1/15** F6 | 0/21 | 0/10 F11 | 0/21 | **21/21** | 0/21 | 0/21 | 0/21 |
| sank_04 | 21 | **3/14** F7 | 0/19 F2 | 0/21 | **1/10** F11 | 0/11 F10 | **4/21** | **15/19** F2 | **1/15** F6 | 0/21 | **2/10** F11 | **2/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| lyft_05 | 21 | **2/15** F6 | 0/19 F2 | 0/21 | 0/10 F11 | 0/11 F10 | **3/21** | **10/19** F2 | 0/15 F6 | 0/21 | 0/10 F11 | **2/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| vand_180 | 21 | 0/14 F7 | 0/19 F2 | 0/21 | 0/10 F11 | **1/11** F10 | **5/21** | 0/19 F2 | **1/15** F6 | 0/21 | 0/10 F11 | 0/21 | 0/21 | 0/21 | 0/21 | **21/21** |
| genom_disk | 21 | **2/14** F7 | 0/19 F2 | **9/21** | 0/10 F11 | **11/11** F10 | **8/21** | **9/19** F2 | **5/15** F6 | **10/21** | 0/10 F11 | 0/21 | **1/21** | 0/21 | **7/21** | **2/21** |
| utanfor_bild | 21 | 0/14 F7 | 0/19 F2 | **9/21** | 0/10 F11 | **4/11** F10 | **21/21** | **19/19** F2 | 0/15 F6 | **21/21** | 0/10 F11 | **17/21** | 0/21 | 0/21 | **19/21** | **11/21** |
| teleport | 21 | 0/14 F7 | 0/19 F2 | **10/21** | 0/10 F11 | 0/11 F10 | **20/21** | **18/19** F2 | 0/15 F6 | **21/21** | 0/10 F11 | **3/21** | **21/21** | 0/21 | **13/21** | 0/21 |
| skala_15 | 21 | **1/14** F7 | 0/19 F2 | 0/21 | **1/10** F11 | **3/11** F10 | **3/21** | **5/19** F2 | **16/17** F4 | 0/21 | 0/10 F11 | **2/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| pose_flip | 21 | **2/14** F7 | 0/19 F2 | 0/21 N10 | **10/10** F11 | **6/12** F9 | 0/21 | 0/19 F2 | **1/16** F5 | 0/21 | 0/10 F11 | **2/21** | 0/21 | 0/21 | 0/21 | 0/21 |
| byt_id | 17 | **1/13** F4 | 0/16 F1 | **7/17** | **1/7** F10 | **2/8** F9 | 0/17 | **1/16** F1 | **6/13** F4 | **2/17** | 0/8 F9 | 0/17 | 0/17 | 0/17 | **1/17** | **1/17** |
| kamera_1m_sida | 19 | 0/14 F5 | 0/17 F2 | **9/19** | 0/9 F10 | 0/10 F9 | 0/19 | 0/17 F2 | **1/14** F5 | 0/19 | 0/8 F11 | **3/19** | 0/19 | 0/19 | 0/19 | 0/19 |
| kamera_1m_bak | 19 | **1/14** F5 | 0/17 F2 | **9/19** | 0/9 F10 | **5/10** F9 | 0/19 | 0/17 F2 | **1/14** F5 | 0/19 | 0/8 F11 | 0/19 | **2/19** | 0/19 | 0/19 | 0/19 |
| kamera_1m_upp | 19 | **2/15** F4 | 0/17 F2 | 0/19 | 0/9 F10 | 0/10 F9 | 0/19 | **1/17** F2 | 0/14 F5 | 0/19 | 0/8 F11 | **2/19** | 0/19 | 0/19 | 0/19 | 0/19 |
| bord_bort | 7 | 0/7 | 0/7 | 0/7 | 0/6 F1 | 0/5 F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | **7/7** | 0/7 | **2/7** | 0/7 | 0/7 |
| bord_svav_05 | 7 | 0/7 | 0/7 | 0/7 | 0/6 F1 | 0/5 F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 |
| bord_2m | 7 | 0/7 | 0/7 | 0/7 | 0/6 F1 | **1/5** F2 | 0/7 | 0/7 | 0/7 | 0/7 | 0/4 F3 | **7/7** | 0/7 | **2/7** | 0/7 | 0/7 |

Andel mål där minst en grind larmar, läge a:

| | sank_04_delvis | vand_180 | lyft_05 | kamera_1m_bak | stol_bort | stol_05 | bord_bort | bord_2m | byt_id | rum_fel |
|---|---|---|---|---|---|---|---|---|---|---|
| någon G | 4/21 | 4/21 | 14/21 | 0/19 | 0/4 | 0/4 | 0/7 | 2/7 | 7/17 | 4/4 |
| någon H | 21/21 | 21/21 | 21/21 | 18/19 | 4/4 | 4/4 | 7/7 | 7/7 | 7/17 | 0/4 |

I de övriga nio klasserna larmar någon H-grind på alla mål, utom kamera_1m_upp (18/19). rum_fel mäts inte av H-serien, eftersom scenpaket/2 har ett enda rum. byt_id i en enpersonstagning är den största kvarvarande luckan i läge a.

Kvarvarande luckor i läge b (kolumnen "kvar men inget H-larm" i §2.2):

| mutation (läge b) | kvar utan H-larm | mål | varför |
|---|---|---|---|
| kamera_1m_sida | 8/19 | gelato s1, asketch s1–s5, s7, notan s4 | kroppen är kamerarelativ och följer med kameran; stående personer utan stol och med bord längs sidled ger ingen kontaktkonflikt. Kräver jämförelse mot rummet (väggar/golv i MoGe-djupet), som inte är byggd. |
| kamera_1m_bak | 7/19 | guacamole s2, gelato s1, asketch s1–s4, notan s4 | samma skäl |
| byt_id | 4/17 | asketch s1, s3, s5, s7 (etikett A↔B i enpersonstagning) | A och B har nära samma benlängder (H8 ser inget). Behöver utseende-Re-ID (`farg_signatur`). |
| lyft_05 / sank_04 / pose_flip / skala_15 / genom_disk | 3–5 per klass | se `grind_resultat.json` | små kvarvarande avvikelser (0,04–0,26 m), eller målrader som redan var fel i baslinjen (F) |

Jämfört med G-serien (kolumnen "kvar men inget G-larm" i §2.2): G1–G7 är tysta för 176 av 243 kvarvarande fel. H-serien är tyst för 38 av 243, och 15 av dessa 38 gäller kamera 1 m i sidled eller bakåt.

---

## 5. De fyra klippen mätta med H-serien

`grind_harda.py` på de lagrade paketen. H1, H10 och H13 räknas per tagning, övriga per (tagning, person). G1–G7 ger 0 fel på samtliga.

| klipp | H-fel | vad | belägg | status |
|---|---|---|---|---|
| guacamole | H1 ×2 (s1, s4) | bardisken `bord_1` är dold i tagningar där obs har sett den (S4:t1 `amodal=False`) | R1_skymningsskydd i `beslut`; `ut/guacamole/jamforelse.png` S4: disken syns i originalet men inte i renderingen | **bekräftad i bild** (s4) |
| | H3_hallning ×5 | A sittande med knä på 0,18–0,22 m och lår 53–55°; B stående med bäcken/benlängd 0,73–0,86 (normalt ≈ 1,1 i de andra klippen) | Argons egen `jamforelse.png`: A på huk i S1/S3/S4 och B med böjda knän i S4 | **bekräftad i bild** (s1, s3, s4); s2 obekräftad (benen skymda) |
| | H10 ×1 (s3) | paketets kamera har pitch 0°, obs −9,56 ± 3° | `scen_brygga.py:254` | bekräftad i kod |
| gelato | H7 (s1) | projicerat huvud i YOLO-spåret i 23 % av rutorna | `grind_bevis_h7.png`: huvudet hamnar på bröstet. Orsak: kameran stoppas vid 0,92 m och kroppen hamnar 0,144 m för lågt relativt kameran (`grind_bevis.py`) | **bekräftad i bild** |
| | H2 svävar (s1) | lägsta led > 0,15 m över golvet i 31 % av rutorna | – | obekräftad (benen skymda av disken) |
| | H8 (s1) | höger underarm varierar 0,18–0,36 m | finns kvar med `_dra_in` avstängt, så orsaken ligger före | orsak oprövad |
| | H10 ×2 | höjd −2,3 σ, pitch 0° mot −18° | – | bekräftad i kod |
| asketch | H4 ×6 | kroppen ligger inne i disken i 97–100 % av rutorna, i tagningar där R1 har dolt disken | paketets egna koordinater; R1_kollisionsskydd i `beslut`. Nuvarande kod ger också H4 = 6 | geometriskt bekräftad |
| | H10 ×7 | kamerahöjd 2,7–5,4 σ under obs, pitch 0° mot −15…−18° | `grind_bevis.py` återskapar höjderna ur z-normaliseringen | bekräftad i kod |
| | H8 ×3, H2 ×1 | underarm/nacke varierar (cv 0,06–0,14); s5 svävar i 34 % av rutorna | – | obekräftad |
| notan | H3_hallning ×6 | A och B sittande med knä på 0,14–0,22 m (person_4: 0,50 m) | `ut/notan/jamforelse.png` S2: B med låga knän | delvis bekräftad i bild |
| | H4 ×4 | B sitter i södra väggen i s5 och s7 (`stol_B` y = −3,157, väggen −3,155 ± 0,04); B i `bord_2` i s2; person_4 i `bord_3` i s4 | paketets koordinater | geometriskt bekräftad |
| | H1 ×3 | `bord_2` dold i s2 och s7 (B:s eget bord), `bord_3` dold i s4 | R1_kollisionsskydd | bekräftad i `beslut` |
| | H7 (s7) | huvudet i spåret i 0 % av rutorna | `grind_bevis_h7.png`: huvudet vid bordsskivan. Kameran stoppas vid 0,92 m och kroppen hamnar 0,341 m för lågt relativt kameran | **bekräftad i bild** |
| | H8 ×2, H10 ×2 | B s7 benlängder 13 % från övriga tagningar; s6/s7 pitch −11…−12° mot 0° | – | H10 bekräftad i kod, H8 obekräftad |

**Specificitet på baslinjen:** H3_sate, H5, H9, H11, H12, H13, H14 och H15 ger 0 fel på alla 21 spår. Minsta marginaler: H9 2,6° mot gränsen 6°; H14 1,8 σ mot 3 σ; H15 37° mot 60°; H12 6,1 m/s mot 8 m/s; H11 0,45 m mot 0,8 m, och skivhöjden ligger 0,07 m under övre armhöjdsgränsen (guacamole A).

**Ablation och H-serien:** när ett efterbehandlingssteg stängs av ändras H-resultatet bara där steget självt döljer eller orsakar felet. R3 av ger H2-fel (guacamole 5, notan 6). R1 av tar bort H1-felen. `_dra_in` av ger ett H4-fel till i guacamole och i gelato, alltså kollisioner som `_dra_in` annars flyttar bort även för H4. H3_hallning, H7, H8 och H10 är oförändrade i alla ablationer. R1, R3 och R25 maskerar alltså inte H-serien, men `_dra_in` döljer fortfarande enstaka kollisioner. Det är skälet till förslag 2 i §7: logga flyttarna.

---

## 6. Begränsningar

- Mutationerna är syntetiska. Läge b injicerar i SAM-rådata, obs och recept, men inte i djup/MoGe eller i rums_pussel.
- Gränserna i H-serien är satta på samma 4 klipp som de mäts på. Specificiteten är alltså inte prövad på hold-out-data.
- H9, H14 och H15 delar källa med SAM-lyftet (se §4). En etikettförväxling i en enpersonstagning upptäcks bara av H8 (benlängder mellan tagningar) och bara när personerna har olika proportioner (6/13 i läge a). Utseende-Re-ID (`farg_signatur` finns i obs) är inte använd.
- Facitgränsen 0,05 m är godtycklig. Med 0,10 m ändras klassningen för 1 av 284 mål (sank_04 notan s7, kameran 0,058 m).
- Läge b jämförs mot nuvarande kod, läge a mot lagrade paket. För asketch är de olika (§1.4).

---

## 7. Förslag

1. **Byt `grindar.mat` mot en rad per (tagning, person)**, så att inga spår går omätta (§3.1).
2. **Kör grindarna två gånger: på rådata före efterbehandling och på slutpaketet**, och redovisa varje efterbehandlingsstegs flyttar i `beslut`, inklusive `_dra_in` (som i dag inte loggas). Ett steg som tar bort ett grindfel ska synas som ett beslut, inte som "0 fel".
3. **Låt R1 inte ta bort objekt som är observerade i tagningen** (H1). Kollision mellan kropp och observerat bord är ett fel i kropp eller bord som ska rapporteras.
4. **Ersätt G3 med H3_sate + H3_hallning**, G2 med H2, G4 med H4 (oavsett `synlig_ut`, med benpunkter) och G5 med H5. G6 kan behållas, men bara om R1-skymningsskyddet tas bort, annars mäter den aldrig något.
5. **Ersätt G7** med en 2D-grind mot oberoende spår. A1-lanens `g7_oberoende.py` är det utförliga förslaget; H7 här är en grov kontroll som visats kunna larma.
6. **Använd obs som motpart:** H9, H10, H11, H14 och H15 kostar några millisekunder och fångar kamera-, identitets- och möbelfel som G1–G7 saknar mått för.
7. **Ny regel i protokollet:** "0 fel" redovisas tillsammans med mutationsmatrisen för samma grindversion.
