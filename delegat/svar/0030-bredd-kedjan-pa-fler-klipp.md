---
id: 0030
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat

**1. Kedjan.** Den körs med en rad: [kedja.py](../../scen/3d/gennedbrytning/kedja.py) `<kedja/<klipp>/<tagning>.json>`.
- **Steg:** generering → läsning → tid → kontroll → förvärld → samspel → rot → kamera → scen1 → sked → scen2 → mening → källa.
- **Cache per steg:** en hash av konfigen, indata och skriptet, med logg per steg (`kedja/<namn>/logg.jsonl`).
- **Genereringen är ett utbytbart steg.** `dreamina_hand` skriver eller läser paketet och stannar med `VÄNTAR` och kod 2 tills `svar/` har en mp4. `fal_ray` stannar på saldot. En befintlig generering kan köras om (`befintlig`).
- **Gelato-konstanterna** i nio skript är nu parametrar i `tagning.py` (konfig via `GENNED_TAGNING`; standard = gelato S1 med samma värden). Före-kopior ligger i `kontrakt/ut/fore_0030/gennedbrytning/`.
- [README.md](../../scen/3d/gennedbrytning/README.md) beskriver steg, kommando, parametrar och vilka skript som ersatts.

**Gelato S1 genom kedjan, tom cache** (ny variant `k30_gelato_s1`, Dreaminas befintliga generering, läsningen omkörd på Modal), jämfört med 0028:

| | 0028 | kedjan |
|---|---|---|
| läsningen (största skillnad, leder) | – | 0,5 mm |
| tidsavbildningen | – | identisk |
| roten (fötternas mål, flytt) | [0,292, 1,736, 0,065], max 1,15 m | identisk |
| kameran, väg | 0,73 m | 0,73 m |
| kameran, projektionsfel | 20,7 | 20,8 promille (h1–h9 inom 0,9) |
| skedens fäste | (−0,112, −0,082, −0,067) | (−0,112, −0,081, −0,067) |
| h1–h9 | sant utom h6 och h9 | samma utfall; läge och storlek inom 0,9 promille och 0,01 |
| synlighet i ruta 45–70 (hand, underarm, tråg) | 1,0, 1,0, 0,95 | 1,0, 1,0, 0,95 |

Kontrollen säger NEJ (rotens hopp 13 cm, överkroppens p90 64 promille). Den är diagnos och stoppar inte kedjan.
- **Väggtid:** cirka 20 minuter.
  - läsning 93 s
  - förvärld 365 s (stabilisering och bygge)
  - scen1 258 s
  - scen2 173 s
  - mening 82 s

**2. Meningen på fler klipp.**
- **Handlingsspåret** finns för alla tagningar: b-tilltal 11 tagningar och 25 segment, guacamole 4 och 14. Skriptet är [m_handling.py](../../scen/3d/gennedbrytning/m_handling.py), allmänt, ur ingestens läsning i världen.
  - **Mätt:** hållning, sitter, handens läge mot kroppen, rörelse, huvudet och kameran.
  - **Namngett av Flash:** handling, kroppsdel, föremål, mål, blick och kontakt.
- **Ordförrådet:** två verb har lagts till, `tala` (b-tilltal talar) och `sitta` (mannen i guacamole sitter). Två fält har lagts till, `blick` och `i_handen` (vad händerna bär). Inget verb hamnade utanför ordförrådet.
- **Relevansen** ([relevans_steg.py](../../scen/3d/gennedbrytning/relevans/relevans_steg.py) `--namn relevans_0030`) läser spåret och ger poster av typen `handling` (vem, segment, roll). Deklarationens relevansfält är struket som indata. Steget gör egna kontaktblad när ingestens saknas.

**Blind jämförelse mot ägarens läsning** (facit öppnat efter körningen):

| Ägaren | Blind körning | Efter `i_handen` (inte blind) |
|---|---|---|
| Guacamole: baren mellan dem | `bardisk` ramar | ramar |
| Guacamole: han håller mobilen och tittar på den | **saknas helt**, ingen handling eller post | spåret: "A looks down at a phone held in both hands" (blick ned); relevansen: `phone_A` som **brus** |
| Gelato: kundens hand | (0025 missade) | saknas fortfarande; kameran ramar "som kundens perspektiv". Ny bärande post: `glassportion_kund` (provet på skeden) |

- **In i källorna:** `kalla_mening.py` skrev [b-tilltal kalla_0030.json](../../scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand/kalla_0030.json) (revision 5) och [guacamole kalla_0030.json](../../scen/3d/kontrakt/ut/e-dialog-guacamole_grupp/kalla_0030.json) (revision 4).
- **Schemat:** segmenten har fått `handens_lage`, `huvud`, `blick` och `i_handen`, och relevansposterna `vem` och `segment`. Segment för olika personer får överlappa.
- **Bakåtkompatibelt** (sha256, tom cache, före-kod `fore_0030/kod/`): Notan, Notan med lokalbyte, bar, guacamole, b-tilltal 0016, gelato gammal och gelato 0029 ger samma plan före och efter.

**b-tilltals tio meningar** (`forvarld/btilltal/ut_0030/`; `utan/` har samma tillstånd som 0016, `med/` har spår och relevans):

| # | 0016 | utan | med | Ändring |
|---|---|---|---|---|
| 1 | ta bort s5, bild | samma | samma | – |
| 2 | grupp_B först, **bild** | grupp_B efter grupp_B | samma | **föll i båda villkoren** (gruppen efter sig själv) |
| 3 | st79 byt | samma | samma | – |
| 4 | s6, C, nära | samma | samma | – |
| 5 | våg, ta bort, bild | samma | samma (ny typ `saknas`, oviktigt) | – |
| 6 | köttbit → "ost", bild | samma | köttbit → **platshållartyp** | sämre: typen tappades |
| 7 | lägg till scen, avvisad | handling, inga segment | lägg till scen, avvisad | – |
| 8 | glass_disk, avvisad | samma | samma | – |
| 9 | s11 +1 s, bild | samma | samma | – |
| 10 | rörelse, avvisad | samma | samma | – |

- **Tillståndet:** 27 rader och 4 257 tecken utan, 41 rader och 7 031 tecken med.
- **Jev:** mediantid 547 respektive 591 ms per mening. 59 anrop och 229 548 inputtokens, cirka 0,009 USD inklusive två felkörningar.
- **Ingen mening når fler bilder med spåret.** Talet och gissningarna bär b-tilltal, och dem uttrycker spåret inte.

**3. Ägarens genereringar.** Både `omgang2/svar/` och `guacamole-S1/svar/` är tomma. Kedjan står och väntar med ett kommando per tagning:
```
scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/kedja.py scen/3d/gennedbrytning/kedja/kand-kennysgelato-tagningar/S1_omgang2.json
scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/kedja.py scen/3d/gennedbrytning/kedja/e-dialog-guacamole-tagningar/S1.json
```
Båda ger `generering VÄNTAR` med sökvägen till paketet.

## Bedömning
- **Gelatos väg från en generering till källan** kräver ingen handpåläggning: ett kommando och cirka 20 minuter, med samma utfall som 0028.
- **Ett nytt klipp kräver i dag fyra saker för hand:**
  - en konfig per tagning
  - den tomma scenen och nyckelbilderna (bildmodellen ingår inte i kedjan än)
  - Dreamina-körningen (inget API)
  - för guacamole två saker som inte finns i koden: säte som ankare och inversen av utzoomningen
- **Scenbygget** (`s_scen.py`) är fortfarande skrivet för en disk med tråg: tråget, glaset och kunden vid kameran.
- **Meningslagret gick att köra blint på två nya klipp utan nya verb, men det missar det ägaren ser.** Mobilen kom först med fältet `i_handen`, och då som brus. Kundens hand saknas fortfarande.
- **Jev ändrade sitt svar** för b-tilltal m2 med samma tillstånd som i 0016. Jev varierar alltså mellan körningar, och ett enda prov per mening räcker inte.

## Ändrade eller nya filer
- **Gennedbrytning, nya:** `kedja.py`, `tagning.py`, `m_handling.py`, `README.md`, `kedja/` (konfigar och körning), `handling/<klipp>/`, `relevans/<klipp>/relevans_0030*.json` och `d_video/k30_gelato_s1*`.
  - Kedjans utfall: `g_forvarld/k30_gelato_s1_t*`, `s_k30_gelato_s1*` och `samspel/k30_*`.
- **Gennedbrytning, ändrade:** `f_las.py`, `t_tid.py`, `g_forvarld.py`, `r_rot.py`, `r_kamera.py`, `s_scen.py`, `r_sked2.py`, `v_mening.py`, `h_kontroll.py` och `relevans/relevans_steg.py`. Före-kopior finns i `kontrakt/ut/fore_0030/`.
- **Kontrakt:** `kalla.schema.json` och `kalla_mening.py` (före-kopior i `fore_0030/kod/`), plus de två nya källorna.
- **Förvärld:** `forvarld/btilltal/ut_0030/` och `forvarld/guacamole/`.

## Kontroll mot "Klart när"
- [x] Kedjan körd på gelato S1 med tom cache, samma utfall som 0028 (se tabellen).
- [x] `gennedbrytning/README.md`.
- [x] Relevans och handling i källorna för b-tilltal och guacamole, med jämförelsen.
- [x] b-tilltals tio meningar med och utan mening.
- [x] Kedjan redo för ägarens svar.
- [x] Bedömning.

## Avvikelser
- **Relevanssteget skrev över 0025:s `underlag.json` för guacamole** i första körningen (filen är ett mellanled och görs om ur samma indata). Nu skrivs `underlag_<namn>.json`.
- **`i_handen` lades till efter att facit öppnats.** Guacamoles spår och relevans med fältet är alltså inte blinda. Den blinda versionen finns i `handling/e-dialog-guacamole-tagningar_blind/` och `relevans_0030_blind.json`.
- **b-tilltals "med" kördes två gånger utan meningsraderna** (fel i kopieringen av tillståndet). Svaren ligger i `ut_0030/med_fel*/`. De två körningarna gav olika svar med samma tillstånd (m2, m7), vilket är samma variation som ovan.
- **Testsviten:** 240 prov, samma åtta fel som före. Kontraktets kod ändrades bara i schemat och i `kalla_mening.py`.
- **Kostnad:**
  - Flash cirka 0,28 USD av 0,30
  - Modal en läsning (193 rutor)
  - Jev cirka 0,009 USD
  - Codex användes inte
- **Tid:** cirka 50 minuter, 19:01–19:51, delvis parallellt med 0029:s rendering (`tidslogg-0028-0029.log`).
