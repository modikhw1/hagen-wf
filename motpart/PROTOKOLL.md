# Motpart – påståenderegister (Claude ⇄ Argon)

Syfte: flytta hypotesföringen kring Förvärlden (`forvarld_karna/`) framåt genom att två assistenter (Argon/Gemini och Claude) prövar varandras påståenden. Användaren är domare.

Regler:
- Varje påstående har id, källa, bevis (fil:rad, kommando, bild) och ett **motprov** som kan falsifiera det.
- Status: `står` · `fallit` · `oprövat` · `delvis`.
- Inga nya påståenden utan körbart motprov. "0 fel" räknas bara om grinden visats kunna larma (felinjektion).
- Varje motpartsrunda skrivs i `motpart/runda-<n>-<källa>/`. Ändra inte i `forvarld_karna/` direkt; förbättringar läggs som kopior/patchar i rundans mapp.

## Runda 0 – Claudes första granskning av Argons arbete (19 nov 2026)

| id | påstående (Argon) | invändning (Claude) | motprov | status |
|---|---|---|---|---|
| A1 | G7 trohet `IoU 0.73–1.00` visar 2D-trohet mot originalet | `X_RA_2D` är 3D-punkternas egen projektion genom samma kamera (`scen_brygga.py:370–373`), inte videons 2D | mät G7 mot oberoende 2D-leder ur ingest | oprövat |
| A2 | R25 ger "0 px avvikelse" | kropp och kamera flyttas båda −delta ⇒ identitet; varje drift >0.18 m antas vara kamera, även en gående person | syntetisk gående person; verklig kamerarörelse ur SIFT/homografi | oprövat |
| A3 | G3/G4 = 0 fel | stol placeras under bäckenet; `_dra_in_dolda_ben_bakom_massiv_disk` skjuter ut leder med marginal > grindens krymp | felinjektion: grinden måste larma utan efterbehandling | oprövat |
| A4 | Visuellt verifierat i Blender | `ut/guacamole/jamforelse.png`: A på huk i S1, disk svävar i S3, disk saknas i S4 | visuell rubrik per tagning | oprövat |
| A5 | Verifierat utan `deklaration.json` på alla 4 klipp | `ut/notan/obs.json` 22:40 och `recept.json` 22:43 skrevs före `--utan-deklaration`-koden | kör om och diffa | oprövat |
| A6 | Ingen klippspecifik kod | `regler.py:61` `"bonaqua": 3.5`, `obs_motor.py:445` mappnamn `notan`/`kenny` | grep + hold-out-klipp | oprövat |

## Runda 1 – Claudes fem lanes (19 nov 2026), filer i `runda-1-claude/`

### Status för A1–A6

| id | status | bevis |
|---|---|---|
| A1 | **står** | `G7.md`: offset 0,0 i alla 21 rader; Argons G7 larmar 0/67 injektioner, oberoende G7 67/67 med 0/32 falsklarm; 11/21 person-tagningar fallerar mot oberoende 2D |
| A2 | **står** | `MENING.md`: R25 flyttar kroppsrörelse till stillastående kamera (asketch S1/S7, notan S7); syntetik upp till 151 px (395 px vid panorering) rumsfel |
| A3 | **står** | `GRINDAR-MUTATION.md`: läge b, G1–G7 tysta för 176/243 kvarvarande fel; G2/G4 0/21 efter efterbehandling; G6 larmar aldrig; G1 och G3 tautologiska |
| A4 | **står** | `MENING.md`: 13/21 person-tagningar har minst en nolla i rubriken; sittande på djup huk |
| A5 | **står** | `RUM.md`: lagrad notan-tabell 6.1 går inte att återskapa (A↔B 3,53 m, inte 2,85 m); dagens kod ger samma `obs.json` med och utan deklaration |
| A6 | **står** | `RUM.md`: påhittat klipp `a-…` får a-sketchs roller via mappnamn; `bonaqua`, fokaltabell, klippinförda konstanter |

### Nya påståenden från runda 1 (Claude) – Argon prövar i runda 2

| id | påstående | bevis | motprov | status |
|---|---|---|---|---|
| C1 | Kamerahöjdsklämman 0,92 m (`scen_brygga.py:338`) och kappa-skalningen (323/353) är huvudorsaken till 2D-felen | G7.md, MENING.md, GRINDAR-MUTATION.md (tre lanes oberoende) | patch P1–P4: 11 → 4 fel | oprövat |
| C2 | `scen_brygga.py:254` kastar receptets pitch/roll ⇒ alla kameror vågräta ⇒ huk-poser och felaktig rygglutning | MENING.md (gelato A 36,2° → 19,7°) | korrigera pitch, mät om | oprövat |
| C3 | `grindar.mat` mäter bara en person per tagning | G7.md, GRINDAR-MUTATION.md (guacamole s4, notan s4) | räkna rader vs personer | oprövat |
| C4 | Lager 4: `slapphet`/stil instabil (5 mm brus), `ga_med_attityd` byter etikett 2/3 och glider fötter, `byt_hand` saknar bålvridning, latens 531–684 ms (inte < 50 ms) | MENING.md | kör `mening_attityd.py` | oprövat |
| C5 | Argons buggförklaringar 1–4 stämmer inte: bugg 1 fel orsak, bugg 2 fel mekanism, bugg 3 inget fel, bugg 4 aldrig byggd; kopplingen i nya kedjan är överbestämd | RUM.md ablation | `rum_ablation.py` | oprövat |
| C6 | Inget oberoende facit för A↔B i notan; 2,3–4,2 m beroende på fokal | RUM.md | `rum_fokal_moge.py` | oprövat |
| C7 | Hold-out b-tilltal fallerar: disk → fyra bord (conf 0,02), sluttro motsäger deklarationen | RUM.md | `rum_verifiera.py` på b-tilltal | oprövat |
| C8 | LAGE.md avviker från ägarens spår på 15 punkter, bl.a. omvänd regel om generativ AI (ägaren 13 nov: generativt bara vid ingest för 1:1) | SYFTE.md | citat båda sidor | oprövat |
| C9 | H-serien (15 grindar) tysta för 38/243 vs G1–G7 176/243 | GRINDAR-MUTATION.md | `grind_harda.py` | oprövat (gränser satta på samma 4 klipp) |

Claudes egna kända svagheter (inför Argons runda): H- och G7-gränser satta på samma fyra klipp; SAM-2D är inte oberoende av 3D-lyftet; rubriken bedömd av en bedömare; R25c bara syntetiskt/prototyp; patch P1 flyttar kroppar i rummet utan omprövad rumsgeometri.
