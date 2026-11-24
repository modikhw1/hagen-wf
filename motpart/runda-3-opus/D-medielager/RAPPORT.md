# Rapport: Spår D — Medielager (`kor_k8` på Urval, Hold-out & Arbetsbordets Utvecklingsklipp)

Körning slutförd och granskad 20 nov 2026 utan ändringar i den frysta koden ([`FRYST_KOD.txt`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/FRYST_KOD.txt): **17/17 filer SHA256-verifierade, 0 avvikelser**).

---

## 1. Sammanfattning av K8-körningen ([`SAMMANSTALLNING.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/k8/SAMMANSTALLNING.md))

### Urvalet (20 klipp, 80 operationer i [`resultat.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/k8/resultat.jsonl))

| Lager / Operation | ok (`syns` & `kvar`) | `syns ej` | `rest ändrad` (`kvar=False`) | `nej` (ärlig begränsning) | `motfråga` | `fel` (krasch) |
|---|---:|---:|---:|---:|---:|---:|
| **skärmtext: byt texten** | 8 | 2 | 1 | 2 | 2 | **5** |
| **ljud: ta bort musiken** | 7 | 8 | 2 | 3 | 0 | 0 |
| **mat (b-roll): byt matbilden** | 0 | 0 | 1 | 19 | 0 | 0 |
| **montage: korta 30 %** | 1 | 3 | 4 | 12 | 0 | 0 |

- Per stratum (`ok` text/ljud/mat/montage): `montage` `0/2/0/0` (5 klipp), `sketch` `2/2/0/1` (5 klipp), `tilltal` `4/0/0/0` (5 klipp), `visning` `2/3/0/0` (5 klipp).
- Klipp med minst 3 av 4 lager faktiskt utförda & grönt mätta (`ok`): **1/20** (`blackstonesteakhouse-7565053584014888214`: text `ok`, ljud `ok`, broll `nej`, montage `ok`).
- **Ingesttid (urval):** cachad via `forbered.py`, median **17.2 s**, max **76.7 s**.

### Hold-out (4 obekanta klipp körda på exakt fryst kod i [`resultat_holdout.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/k8/resultat_holdout.jsonl))

| Lager / Operation | ok | `syns ej` | `rest ändrad` | `nej` | `motfråga` | `fel` |
|---|---:|---:|---:|---:|---:|---:|
| **skärmtext: byt texten** | 1 | 0 | 0 | 1 | 2 | 0 |
| **ljud: ta bort musiken** | 1 | 2 | 0 | 1 | 0 | 0 |
| **mat (b-roll): byt matbilden** | 0 | 0 | 0 | 4 | 0 | 0 |
| **montage: korta 30 %** | 1 | 0 | 1 | 2 | 0 | 0 |

- **Ingesttid (hold-out, ocachad första körning):** `79.1–138.0 s` per klipp, median **93.8 s**.
- **Antal krascher på hold-out:** `0` (`0/16` operationer).
- **Klippresultat (`ok` / antal):** `faros_shipandterrace-7540756212032326934` nådde 2 `ok` (`skarmtext`, `montage`) + 1 `nej` (`broll`); `faros_shipandterrace-7511394441094008086` nådde 1 `ok` (`ljud`) + 1 `motfraga` + 1 `rest_andr` (`montage`); `sabai.soong-7474616203366108439` svarade ärligt `nej` på samtliga 4; `thepitaspot-7680489103195917590` gav `motfraga` (`skarmtext`, flerordstextning) + `ljud syns_ej` + 2 `nej`.

### Ärlig redovisning av `"rätt hanterat*: 0/0"` & Felfiltering
1. **`rätt hanterat*` visar `0/0` i `SAMMANSTALLNING.md`:** `sammanstall.py` kräver filen `k8/facit_mitt.json` (manuell ground truth över vilka lager som faktiskt förekommer i varje klipp). Eftersom `k8/facit_mitt.json` inte fanns skapad på förhand blev alla rader `?/?/?/?` och nämnaren `0/0`. Bedömningen nedan grundas därför på JSONL-måtten och manuell visuell granskning av kontaktkartor i `granskning/`.
2. **Felinjektion (`variant a`: ingen ändring alls; `variant b`: otillåten sidoändring):** Måtten larmade i **32 av 32 injektioner (100 %)**.
3. **K7-efterlevnad:** **0 generativa anrop** över samtliga `96` körda operationer (`29` Demucs-stammar, `20` ffmpeg-strömkopior av bild, `13` Pillow-text, `12` ffmpeg `drawbox/boxblur/overlay`, `10` ffmpeg `trim/concat/amix/afade`, `1` kund-B-roll med `scale/overlay`, `1` kundens eget material).
4. **Operationstid till färdig förhandsvisning (43 utförda totalt):** median **2.5 s** (urval `2.7 s`, hold-out `1.6 s`), max **18.5 s** (`blubnan.liljeholm-7633500587832741143` B-roll-byte med textomritning).

---

## 2. Diagnostik per Fynd & Visuell Granskning (`granskning/`)

Nio kontaktkartor granskades visuellt (`blackstonesteakhouse__skarmtext`, `blackstonesteakhouse__montage`, `blubnan-763350__broll`, `chickenstreet__skarmtext`, `faros-754075__skarmtext`, `faros-751139__montage`, `blubnan-747937__skarmtext`, `anettesrestaurang__ljud`, samt rutmönsterkartan `rutnat/fratelli.stockhol-7539549931233807618.jpg`):

1. **Rotorsak till 5 `skarmtext`-krascher (`RuntimeError: ffmpeg d_boxblur_2 ... Failed to evaluate filter params: -22`):**
   - Drabbade 5 klipp i urvalet (`fratelli.stockhol-764680`, `blackstonesteakhouse-743965`, `fratelli.stockhol-753954`, `blubnan.liljeholm-763350`, `duepiani-765084`), ofta vid små eller smala textrutor (synligt i `rutnat/fratelli.stockhol-7539549931233807618.jpg`, t.ex. enstaka ord `"noll"`, `"tio"`).
   - I [`operationer.py:126`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/medielager/operationer.py#L120-L130) beräknas blur-radien som `rad = max(2, min(h // 2 - 1, w // 2 - 1, 24))` före `crop={w}:{h},boxblur={rad}:4`. I `yuv420p` är krominansplanet bara `w/2 x h/2`, vilket gör att `rad` överstiger `min(w//4, h//4)` när boxen är smal (`<= 10 px`), eller tvingas till `2` via `max(2, ...)`. *(Lämnades orörd eftersom K8-koden var fryst inför hold-out; bör fixas med `boxblur={luma_r}:1:{chroma_r}:1` eller fallback till `platta` i nästa version.)*

2. **Varför `skarmtext` ibland ger `syns=False` trots synlig ändring:**
   - I `chickenstreet.canada-7696579583734320392__skarmtext.jpg` valdes den lilla texten `'KIOSK'` på kassaskärmen i vänster bildkant (medan gul dialogtextning rördes ej). Plattan + ny text syns svagt på POS-skärmen, men rutan är för liten för RapidOCR att läsa tillbaka (`ny_text_last = ""`), vilket fällde `syns`.
   - På rena centrerade överlägg fungerar flödet bra visuellt (`blackstonesteakhouse-756505`, `blubnan-747937`, hold-out `faros-754075`: mjuk oskarp rektangel täcker originalet utan läckage till bakgrunden).

3. **Varför `montage` och `broll` ofta flaggade `rest_andr` (`kvar=False`):**
   - `blackstonesteakhouse-756505__montage.jpg` klippte bort mittenbilden `t2` rent och passerade `ok` (`psnr_behallna_min = 37.31`).
   - Hold-out-klippet `faros_shipandterrace-751139__montage.jpg` (15.6 s -> 10.9 s) kortade däremot *inom* bevarade tagningar (`Strukna tagningar: inga`). Då förskjuts bildrutor i tid mot originalets referenspunkter så `psnr_behallna_min` föll till `18.63` -> `kvar=False`.
   - `blubnan.liljeholm-763350__broll.jpg` bytte ut cocktailglaset (`t2`) mot egen salladsbuffé (`t13` ur kundens klipp `-7597811030701477142`, dock hade källklippet egen inbränd text `"MED ANDRA SALLADER"` under omlagt lager `"Stockholms bästa libanesiska dinner club"`) och tappade PSNR runt skarven (`psnr_utanfor_min = 20.45`).

4. **Ljudseparationen i praktiken:**
   - Samtliga 17 körda ljudoperationer i urval + 3 i hold-out levererade strömkopierad bild (`bild_identisk=True`, synligt i `anettesrestaurang__ljud.jpg`). De 10 `syns_ej`-fallen beror främst på låg bakgrundsnivå utanför talsegment (`[null, null]` vid kompakt tal eller `< 3 dB` sänkning när trummor/bas var svaga eller sång låg kvar i röststammen).

---

## 3. Utvecklingsklippen för Arbetsbordet (`arbetsbord/data/medielager/`)

Alla 5 utvecklingsklipp ingestades med `MEDIELAGER_UT=.../arbetsbord/data/medielager` utan att ändra någon fryst fil:

| Klipp | Tidslinjefil (`tidslinje.json`) | Ingesttid | Verifiering mot `:5199` |
|---|---|---:|---|
| `notan` (`d-dialog-notan`) | `arbetsbord/data/medielager/lager/d-dialog-notan/tidslinje.json` | 125.9 s | `/api/ladda` -> `/media/tal/notan`, Range `206` (`RIFF....WAVE`, `2 249 030 B`) |
| `guacamole` (`e-dialog-guacamole`) | `arbetsbord/data/medielager/lager/e-dialog-guacamole/tidslinje.json` | 66.3 s | `/api/ladda` -> `/media/tal/guacamole`, Range `206` (`RIFF....WAVE`, `1 765 702 B`) + H.264 proxy `3 163 166 B` |
| `gelato` (`kand-kennysgelato2.0-7596403003901381910`) | `.../kand-kennysgelato2.0-7596403003901381910/tidslinje.json` | 165.6 s | `/api/ladda` -> `/media/tal/gelato` (`har_3d=true`) |
| `asketch` (`a-sketch-servering`) | `.../a-sketch-servering/tidslinje.json` | 133.0 s | `/api/ladda` -> `/media/tal/asketch` (`har_3d=true`) |
| `btilltal` (`b-tilltal-ravara`) | `.../b-tilltal-ravara/tidslinje.json` | 181.2 s | `/api/ladda` -> `/media/tal/btilltal` (`har_3d=false`) |

*(Slutsats: K7-principen att enbart använda icke-generativa ffmpeg/Demucs/Pillow-ingrepp med ärliga `nej`/`motfråga`-besked fungerar robust som grundmotor; dock måste `d_boxblur_2` krominansklampning, PSF/tidsanpassat PSNR-mått vid intern montage-trimning och GPU-accelererad Demucs åtgärdas innan v2 lyfts till produktion.)*
