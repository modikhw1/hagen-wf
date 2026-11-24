# DOM: Kimodo-SOMA-RP — Kontrastprov ("Commit eller Kill")

**Utlåtande: KILL för 1:1-regering, känsloregi och halvkropps-/diskscener i `arbetsbord/` och produktionspipen.**

*(Forskningen i `forvarld/kropp/` parkeras som referensarkiv. Om Kimodo någonsin väcks igen framöver ska det enbart vara som fristående offline-generator för helt nyskapade helkropps-/gångscener på öppet golv med `ben_synliga > 0.7`, utan krav på talsynk och bakom strikta kollisions- och fotglidningsgrindar — aldrig i CM:s 1:1-regiloop.)*

---

## 1. Varför provet kördes

Hypotesen från användaren (samt `LAGE.md` §4.2) var att Kimodo-SOMA-RP skulle kunna ta ett riktat beteende (exempelvis runda ett hörn, sträcka ut en specifik hand mot en ny hylla utan spegling, eller ändra kroppskänsla till trött/slouch) och anpassa rörelsen organiskt i en ombyggd 3D-miljö — **med bevarad kamerakomposition, talsynk och rumskontakt** (`soundoverlay`). Samtliga tre skarpa kontrastfall kördes på Modal (`NVIDIA A10G`, 1 cachad modelladdning `load_s = 46.76 s`, total exekveringstid `wall_s = 114.41 s`, beräknad total GPU-kostnad `$0.0247` för alla 3 fall / 4 körningar med 4 sampel vardera).

---

## 2. Uppmätta resultat ([`matning.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/matning.json), [`render_logg.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/render_logg.json))

| Fall & Källklipp | Inställning | Tid / Est. USD | Träffsäkerhet & Spegling | Talsynk (`speed_corr_0`) | Fotglidning (max/tot) |
|---|---|---|---|---|---|
| **1. Runda hörn + ny bänk** (`e-dialog-guacamole s4 B`, `109` rutor, `ben_synliga=0.0`) | `root2d` + begynnelsefönster | `10.61 s` / `$0.0068` | Waypoint mean `2.72–2.96 cm` (max `4.0 cm`) | **`-0.19 .. +0.16`** (förstörd) | **`102.07–151.69 cm`** (`max 6.88–10.14 cm/ruta`) |
| **2. Vänster hand +15 cm upp, ingen spegling** (`kand-kennysgelato s1 A`, `120` rutor, `ben_synliga=0.95`) | Glest `LeftHand`-villkor | `9.51 s` / `$0.0065` | `lh_target_mean = 7.15 cm`, **`spegling_misstankt = false` (4/4)**, L-färd `51.8–104.5 cm` vs R `34.7–47.4 cm` | `0.05–0.40` (späs ut mellan ankare) | **`7.10–11.95 cm`** (`max 0.59–0.83 cm/ruta`) |
| **3a. Känsla "trött/slouch" — Rent brus (`s=1.0`)** (`guacamole s4 B`, `109` rutor) | Text + rutor `0–4` | `8.91 s` / `$0.0063` | `overkropps_diff = 14.67–19.06 cm`, men `head_sankning = -3.60 .. +0.45 cm` (oftast *högre* huvud!) | **`-0.31 .. +0.21`** (död talsynk) | `2.53–7.38 cm` |
| **3b. Känsla "trött/slouch" — SDEdit (`s=0.55`)** (`guacamole s4 B`, `109` rutor, `45` hoppade / `55` körda DDIM-steg) | `q_sample(x0, t=54)` + text | `5.07 s` / `$0.0051` | **`overkropps_diff = 4.10–4.52 cm`**, `head_sankning = -1.38 .. -1.89 cm`, div `1.24 cm` (knappt synlig ändring!) | **`0.9111–0.9324`** (`lag = 0` i 4/4) | **`34.57–46.58 cm`** (`max 1.66–2.78 cm/ruta`) |

Visuella renderingar (Original + Three.js sida-vid-sida med ljud):
- [`fall1_horn_soundoverlay.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/fall1_horn_soundoverlay.mp4) & [`kontakt_fall1.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall1.png)
- [`fall2_ny_prop_hand_soundoverlay.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/fall2_ny_prop_hand_soundoverlay.mp4) & [`kontakt_fall2.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall2.png)
- [`fall3_kansla_sdedit_soundoverlay.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/fall3_kansla_sdedit_soundoverlay.mp4) & [`kontakt_fall3.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall3.png)

---

## 3. Fyra avgörande fynd som fäller 1:1-spåret

1. **Olöslig Pareto-fälla mellan talsynk och attityd (Fall 3):**
   - Med `s=1.0` kan texten flytta lederna (`14.7–19.1 cm`), men all rytm och taltajming mot originalets repliker försvinner (`speed_corr_0 = -0.31..+0.21`) och `"slouches heavily"` missar ändå riktningen (`head_sankning_cm` blir negativ i 3 av 4 prov).
   - Med `SDEdit s=0.55` bevaras taltajmingen extremt väl (`speed_corr_0 = 0.91–0.93`, `lag = 0`), vilket syns i `kontakt_fall3.png` vid `00:00:00.500–01.533`. **Men** på samma `s=0.55` stannar den fysiska attitydförändringen vid bara `4.1–4.5 cm` (knappt skönjbar som en ny känsla), samtidigt som införd `q_sample`-brusning av dolda ben höjer fotglidningen tiofaldigt till `34.6–46.6 cm`.
2. **Skymda ben bakom disk/bord kollapsar fysik och kollision (Fall 1):**
   - Majoriteten av restaurang- och bardialogklipp (`guacamole`, `notan`, `asketch`) är halvkroppsklipp med `ben_synliga = 0.0`. När Kimodo genererar förflyttning runt hörn glider fötterna `102–152 cm` (upp till `10.1 cm/ruta`) och i `kontakt_fall1.png` (`00:00:02.067–03.100`) skär person B:s ben och underkropp rakt in i främre kanten av `Hörnbänk (mål)` eftersom Kimodo saknar scenens kollisionsgeometri.
3. **Spegling går att stoppa på stående helkropp (Fall 2), men lokal IK slår Kimodo på allt utom ny fri gång:**
   - Fall 2 bevisar att glesa `EndEffector`-villkor i canonical-koordinater på riktigt stående klipp (`ben_synliga = 0.95`) undviker spegling (`spegling_misstankt = false` i 4/4, vänster hand når hyllan med `7.15 cm` medelfel och låg fotglidning `7.1–12.0 cm`).
   - Dock förlorar mellanhändelserna originalets dopprörelse och talsynk (`speed_corr_0 = 0.05–0.40`), och i `kontakt_fall2.png` (`01.702–02.836`) glider/intersekterar underkroppen tätt med originaldisken när armen svingar upp till `163 cm`.
4. **Latens, cold start och kostnad passar inte CM:s arbetsbord:**
   - `46.76 s` container-/modelladdning + `5–11 s` GPU per ~4-sekunderssegment på A10G bryter den direkta redigeringsloopen i webben (`arbetsbord/` ligger annars på `< 50 ms` per operation).

---

## 4. Konsekvens & Ersättningsbeslut

Svärmgranskning (#9 `opus-kontext` och #10 `neon-three`) är helt enig med mätningarna:
1. **Ingen Kimodo i `arbetsbord/` eller 1:1-regin.**
2. **Ersätt Fall 3 (känsla/attityd) med deterministiska kinematiska lager på T1-armaturen** (`forvarld_karna/mening_motor.py`: rygglutning, axelsänkning, huvudvinkel, gestskala) -> `< 5 ms`, `$0`, `speed_corr_0 ≈ 1.0`, `0 cm` fotglidning.
3. **Ersätt Fall 2 (flyttad hand/räckvidd) med lokal 2-leds-/CCD-IK + bålvridning** ovanpå originalets T1-rörelse och `G4`-kollisionskontroll mot bord/disk -> `< 1 cm` målavvikelse, garanterat noll spegling, full talsynk.
4. **Bevara Kimodo enbart i `forvarld/kropp/` som experimentarkiv.**
