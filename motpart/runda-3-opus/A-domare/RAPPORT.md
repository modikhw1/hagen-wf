# Rapport, spår A (domaren), runda 3

19 nov kväll (avbruten av kvoten kl. 22:53) och 20 nov förmiddag. Inga betalda eller generativa anrop. Inget utanför `A-domare/` är ändrat, utom tillägget längst ned i `../HOLDOUT.md`.

## Gjort

1. **Fryst hold-out** (19 nov 22:15): 4 klipp ur `data/format/kontroll/`, dragna med frö `20261119` efter uteslutning på klipp-id och kontonamn i 12 061 textfiler. Se `../HOLDOUT.md`. `sha256(holdout_lista.txt)` är oförändrad: `11e347a1…fddc5`.
2. **Mått** (`matt/`, körinstruktioner i `README.md`): rumsskala (a), 2D-trohet (b), bevarande (c), K7-vakt (d) och jämförelse mot hold-out-facit (a'). Alla larmar vid felinjektion (tabellen nedan).
3. **Facit för hold-out** (`holdout_facit/`, se README där): kamerahöjd ur enkelbildsmetrologi i 2 klipp och ordningsgränser plus epistemik i 2 klipp.
4. **Prövning av runda 2** (`prov_runda2.md`): 17 rader. 6 faller, 5 står eller står delvis, 3 är obevisade och 2 är blandade (R2-1d, R2-14). K7-krocken (R2-13) står.

## Kontroll 20 nov av det som stod kvar efter avbrottet

- Alla JSON-filer går att tolka, och inga skript är halvskrivna.
- **`matt/trohet2d.py` var i ett tyst felläge.** Koden ändrades 22:33 (gruppmax och radiell lutning), men kalibreringen från 22:32 gällde den äldre koden (`kappa_0.85` 0/7, `huk_ben` 0/7). En omkörning visade att 22:33-versionen gav falsklarm på rena data för 3/7 personer och 4/5 videor (`matt/trohet2d_kalibrering_v2_gruppmax_radiell.json`). Jag skrev om den med gränser per ledgrupp från brusgolvet och en skalkvot utan höfter, per person och som median per video. Den radiella lutningen togs bort, eftersom den var lika brusig ren som injicerad. De gamla versionerna finns kvar (`trohet2d_v2_gruppmax_radiell.py.bak`, `trohet2d_kalibrering_v1_*`, `_v2_*`). Spår C har bara använt `k7_vakt.py`, som inte påverkades.
- `prov/prov_lokalminne.json` var skriven före träffparen från GT_VIS-körningen och saknade precision/recall mot den blinda märkningen. Den är omkörd, och den gamla ligger kvar som `_v1_utan_pred`.
- Facitets ankare från 19 nov (`faros_7511_r0.json`, kamera 0,95–2,5 m) hade en för brusig horisont ur korta golvfogar. Det är ersatt av `_v2` (1,39–1,70 m) och har `ersatt_av`.

## Tabell (protokollformat)

| id | påstående | bevis | motprov | status |
|---|---|---|---|---|
| A-1 | Hold-out är orörd av kärnan och runda 2 | `holdout_valj.py`, `holdout_valj.logg.txt` (id- och kontosökning) | v1 drog `fratelli.stockhol`, som fanns i Neons glob, och regeln skärptes (`HOLDOUT.md`) | står (4 klipp, två från samma konto) |
| A-2 | rumsskala larmar | `matt/rumsskala_sjalvtest.json` | injektion 40/40, sanna värden 8/40 falsklarm | står |
| A-3 | 2D-trohet larmar och tål brusgolvet | `matt/trohet2d_kalibrering.json` | rent 0/7 personer och 0/5 videor; sidled 7/7, vänster/höger 7/7, skala 0,85 5/5, ben 1/1 | står, med smal marginal för skala |
| A-4 | bevarande larmar | `matt/bevarande_sjalvtest.json` | 12/12 (rubbning 2 mm, flyttad kamera, borttagen stol, text, npz, bild utanför mask) | står |
| A-5 | K7-vakten larmar | `matt/k7_vakt_sjalvtest.json` | 9/9 (import, nät, underprocess, spegling) | står inom sina gränser |
| A-6 | jämförelsen mot facit larmar | `matt/holdout_jamfor_sjalvtest.json` | 6/6 (+25 cm, bord 0,45, under gräns, mätt utan golv, tomt) | står |
| A-7 | facit faros_7540 r73: kamera 1,36–1,61 m | `holdout_facit/ankare/faros_7540_r73.json`, `rutor/z/f40_r73_*.png` | union över två antaganden om lodrät flyktpunkt (1,36–1,57 och 1,40–1,61); handräkning med horisonten y≈479 ger 1,48 | uppskattning |
| A-8 | facit faros_7511 r0: kamera 1,39–1,70 m | `ankare/faros_7511_r0_v2.json`, `rutor/z/f11_r0_*.png` | horisonten fri inom y 185–265; flyktpunkten ur fönsterbalkarna (y≈193) ligger inom | uppskattning |
| A-9 | sabai: 0,95–1,97 m; pitaspot: > 0,70 m; inte mätbart ur pixlar | `ankare/sabai_ordning.json`, `thepitaspot_ordning.json`, `rutor/z/sabai222_pita744.png` | golvet syns inte i någon av 8 översiktsrutor per klipp | ordningsgränser |
| A-10 | Neons påståenden | `prov_runda2.md` | se där | se där |

Z1-raden i `prov_runda2.md` (R2-8) räknades med:
`py -c "import json; ..."` över `prov/gt_vis_kopia_pred_pairs.json` mot `prov/lokalminne_blind/blind_zoner.json` via `prov/lokalminne_blind_nyckel.json`. Ett par räknas som sant om de två klippen delar minst en blind zon. Resultat (TP/FP): v1 4/0, v2 4/0, v3.1 6/0, v3.2 6/0.

## Inte hunnet

- Möbelhöjder i facit. I de märkta rutorna går bänken eller bordsbenen ut ur bild. Fler rutor (faros_7540 r147–258, där bänken går ner till golvet) kan märkas med samma verktyg.
- V5 (regelpipen v7) på hold-out. Den finns inte som körbar pipe (R2-1c).
- 2D-trohetsfacit för hold-out. `trohet2d.py` behöver inget handfacit (MediaPipe körs på originalrutorna), så det går att köra direkt på B:s paket.

## Svagast i min egen mätstock

1. **Facit är tunt.** Det finns en ruta per klipp, bara kamerahöjd och inga möbelhöjder. Två av fyra klipp har bara ordningsgränser. Den största osäkerheten är referensens längd (personlängd som befolkningsintervall), och personen står kanske inte helt rak (faros_7540: armarna uppe). Märkningen är min egen och inte blind. Linjefamiljerna föreslogs av LSD och godkändes av mig.
2. **Horisonten i faros_7511** vilar på ordningsgränser (y 185–265). Det ger ett brett intervall, som till stor del räddas av att servitrisens huvud ligger nära horisonten. Den lodräta flyktpunkten kunde inte avgöras i någon av faros-rutorna, och därför är facit en union av två antaganden.
3. **rumsskala falsklarmar 8/40 på sanna värden.** Utfallet blir larm om någon av fyra storheter ligger utanför sitt 90 %-intervall. Ett enstaka `utanfor` med några cm är svagt bevis, så läs `avstand_cm`.
4. **2D-trohet:** gränserna kommer från 5 klipp och 7 personer. Höfterna går nästan inte att mäta mellan olika leddefinitioner (brus upp till 0,66 bål). Skalgränsen 0,09 följer regeln 1,3 × största rena värdet, men marginalen är 0,068 ren mot 0,095 injicerad. Benfel kunde bara prövas på en person. MediaPipe är en oberoende detektor, inte sanningen.
5. **Bevarandets tolerans** är mitt val, och måttet är bara meningsfullt om räckvidden anges *före* ändringen. **K7-vakten** känner igen strukna metoder på namnet och ser inte lokala generativa modeller som laddas utan de listade modulerna.
6. Spår A har tittat på hold-out-klippen för att märka facit. Det förbrukar dem inte för B, C och D, men en domare som både märker facit och läser utfallet kan påverka det. En blind andra märkare av samma rutor vore nästa steg.
