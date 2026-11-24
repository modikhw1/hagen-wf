---
id: 0012
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

## Resultat
Alla fem punkterna är gjorda. `disk_C` ligger nu på x ≈ 2,27 i alla kameragrupper, mot 3,09 förut och referensen cirka 2,2. Vågen står till vänster i s11, som i originalet. Arbetet påbörjades av en tidigare session (kod, segmentering, prepare). Jag verifierade det, rättade en regression (se Avvikelser) och körde om.

1. **Beskuren kant är en olikhet** (`boxpassning.kantvillkor`, `olikhetsrest`): en beskuren kant straffas bara när den projiceras innanför bilden. Topp och botten mäts på den del av lådan som ligger inom bildens bredd.
2. **Förval** (`boxpassning.passa_grupp`, `mobellyft._forval`): förvalet ligger framför `framfor`-platsen, mot gruppens kameror och centrerat. En koordinat som har färre än två likhetskanter hålls vid förvalet och märks `antagen` i `kvalitet`. Väggarna är villkor med 0,10 m marginal.
3. **Ett läge per kameragrupp** (`mobellyft.los_grupper`): passningen görs per mätt grupp, och en tagning utan grupp passas för sig. Möbeln och dess `:pa:`-barn får en kopia per synlighetsintervall.
4. **Föremål ur masken** (`foremallyft.los_kopior`): strålen går genom maskens tyngdpunkt och skärs med stödets ovansida plus halva föremålshöjden. Bredden tas ur masken inom deklarerat intervall. En kopia i en tagning där föremålet saknar egen ruta byggs inte.
5. **Spridningen** (`modal_segmentera.py`, `rum_rutor.py`): orsaken var att alla element låg i samma Grounding DINO-prompt. 0008 hade med "white paper", 0010 inte, och därför flyttades S8-rutan. Nu körs ett pass per prompt på L4 med deterministisk torch, och fynd väljs på exakt prompt. **Två körningar gav byteidentiska fynd** (`seg_b1.json`, `seg_b2.json`; bara tidtagningen skiljer). `spridning_2d` per kant följer med och viktar kanterna.

### Projektion i slutkameran mot segmenterarens ruta (promille, projicerat − ruta; topp/vänster/botten/höger)
| tagn | disk n06-matt | disk n06-grupp | våg n06-matt | våg n06-grupp |
|---|---|---|---|---|
| S6 | −60 / 714 / 1 / 2 | 33 / 0 / 1 / 2 | ingen ruta | ingen ruta, döljs |
| S7 | −54 / 735 / 1 / 2 | 55 / 0 / 1 / 2 | ingen ruta | ingen ruta, döljs |
| S8 | 60 / 891 / 6 / 7 | −17 / 0 / 6 / 7 | −77 / 1000 / 36 / 89 | −83 / 0 / 39 / −82 |
| S9 | ingen ruta (stoppad) | ingen ruta | −253 / 975 / 66 / 142 | −264 / 0 / 66 / 142 |
| S10 | 100 / 567 / 3 / 2 | 48 / −212 / 3 / 2 | 32 / 784 / −4 / 67 | 37 / 0 / −119 / −362 |
| S11 | 22 / 406 / 1 / 181 | 38 / −31 / 1 / 181 | −83 / 373 / 1 / 219 | −83 / 0 / 1 / −34 |
Vänsterkanten är tydligt bättre (disk 406–891 → −212–0, våg 373–1000 → 0). Diskens övre kant är jämnare men inte bättre överallt (S6/S7 −60 → +33/+55). Vågen i S10 är 362 promille för smal mot rutan: rutan når nästan över hela bilden, men bredden hålls inom deklarerade 0,22–0,38 m.

**Lägen** (`kvalitet.mobel_lyft.grupper`): `disk_C` S5 (2,27; 0,81) x,y `antagen`; S6+S7 (2,26; 0,52) x `antagen`; S8+S10 (2,27; 1,00) x `antagen`; S11 (2,28; 0,81) y `antagen`. Bara S11 har två vänster-/högerkanter. **Väggar:** minsta marginal 0,10 m (väggen är vriden 3°), ingen möbel utanför. **Kamerarutor i objekt:** 0 (`vaggmarginal_omkorning.txt`).

### Vad som syns
- `blad/s11.png`: vågen står **till vänster**, som i originalet, och är ungefär lika bred som originalets våg med plattform (cirka 0,73 mot 0,78 av bildbredden). Den är en hel grå låda från bildens nederkant upp till brösthöjd, så **Lærkes kropp skyms helt**, och bara huvudet och höger arm syns. I originalet är vågen en display på stativ, och kroppen syns bakom. Läget stämmer, formen inte.
- `blad/s6.png`: Lærke syns hela vägen. Köttbiten är en låda på disken framför henne, men i originalet håller hon den på papper i brösthöjd (det tar 0013). Disken ligger under bildkanten, som i originalet.
- Film: `scen/3d/kontrakt/ut/b-tilltal-ravara_n06-grupp/narvaro/film.mp4`.

### Guacamole, variant `grupp`
Går igenom utan handpåläggning (prepare 0, render 0). Bardisken har tre grupper: S1+S3, S2 och S4. x är `antagen` i alla, eftersom disken går ut på båda sidor, och y är mätt i S1+S3 och S4. Väggvillkoren gick inte att uppfylla tillsammans med intervallet (`konflikt`), så bara deklarerat intervall gäller. Slutplanen har ändå 1,45 m till väggen. Jämförelse: `scen/3d/kontrakt/ut/e-dialog-guacamole_grupp/narvaro/jamforelse.mp4` (original till vänster). Film: `…/narvaro/film.mp4`.

## Ändrade eller nya filer
Baslinjen ligger i `scen/3d/kontrakt/ut/fore_sidled_0012/kod/`. Ändrade filer: `kontrakt/boxpassning.py`, `mobellyft.py`, `foremallyft.py` och `test_snabb.py` (+7), `ingest/rum_rutor.py`, `modal_segmentera.py` och `test_rum.py` (+1), `kontrakt/ut/foremal_logg/LOGG.md` och `scen/3d/NASTA.md`. Varianterna är `kontrakt/ut/b-tilltal-ravara_n06-grupp/` (omkörd) och `e-dialog-guacamole_grupp/`. Första körningen av n06-grupp är flyttad, inte raderad, till `fore_sidled_0012/forsta_korning/`. Underlag: `fore_sidled_0012/` (`seg_*`, `deklaration_*_grupp.json`, `jamfor_grupp.{py,json}`, `vaggmarginal.{py,txt}`, `oforandrad*.json`, loggar).

## Kontroll mot "Klart när"
- [x] Tester: `test_snabb` 34 OK och `test_rum` + `test_deklaration` + `test_scenbrief` 21 OK, med tom bytekodscache. Nya prov finns för punkterna 1–4 och för den dolda kopian.
- [x] b-tilltal `n06-grupp`: prepare och render. Fyra kanter per tagning S6–S11 står bredvid `n06-matt` (tabellen ovan).
- [x] Ingen möbel utanför väggarna och ingen kamera i en möbel.
- [x] `blad/s11.png`: vågen står på rätt sida och har ungefär rätt storlek, men formen skymmer personen (se ovan).
- [x] Guacamole `grupp` går igenom, och jämförelsefilmen finns.
- [x] `LOGG.md` och `NASTA.md` (överst).
- [x] Notan och guacamole: alla 66 befintliga planer går genom `mobellyft.los` + `foremallyft.los` utan ändring, och utdata är byteidentiska mellan baslinjen och den nya koden (`oforandrad_bas.json` = `oforandrad_ny2.json`).

## Avvikelser
- **Rättad regression:** i första körningen blev vågens kopia för S6+S7 (utan ruta, på disken som flyttats mot kameran) en stor låda framför Lærke. Nu byggs en föremålskopia inte i tagningar där föremålet har rutor någon annanstans men ingen egen. Vågen visas därför bara i S8–S11, vilket stämmer med `tagningar_i_bild`.
- `klipp_kor.py` byter katalog till repots rot, så `--deklaration` måste vara en absolut sökväg. Den första omkörningen föll på det.
- Föremål placeras på halva föremålshöjden över stödytan, där tyngdpunkten ligger, och inte på själva ovansidan.
- **Trösklar** (valda, diagnostiska): förval 20 px/m, låsning 2000 px/m, olikhetsvikt 10, minst två kanter per koordinat, spridningsskala 20 px, bakkant 0,15 m före platsen, väggmarginal 0,10 m (befintlig).
- **Kostnad:** Modal-segmentering 3 körningar, 162 GPU-sekunder på L4. Uppskattat under 0,10 USD (fakturan läste jag inte). Gemini 0 USD.
