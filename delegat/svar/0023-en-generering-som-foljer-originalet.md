---
id: 0023
status: blockerat
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
Läget efter k2. **fal-saldot tog slut efter k2**: uppladdningen inför nästa försök fick 403 "User is locked. Reason: Exhausted balance". Totalt har 0,465 USD gått åt på fal (`scen/3d/gennedbrytning/kostnad.json`), så saldot var cirka 0,15 USD och inte 1,50. Jag stannade enligt uppdraget. Allt utom fal-körningarna är gjort.

**Försöken** (mätt med `h_kontroll.py`, där den kamerafria läsningen förs tillbaka genom inversen):

| | dagens | a (källan som den är) | k (kamerafri, bara personmask) | **k2** (kamerafri, originalets pixlar kvar) |
|---|---|---|---|---|
| Ändring, kostnad | — | 0,15 | 0,15 | källa + prompt med antagandet och tider, 0,15 |
| Hela kroppen i bild | — | 48/148 | 148/148 | 124/148 |
| Benlängd, median (spridning) | 0,75 m (4,8 %) | 0,82 (6,6 %) | 0,82 (1,8 %) | 0,81 (4,6 %) |
| Rotens hopp, max | 16,5 cm | 4,1 cm | 2,0 cm | 4,2 cm |
| Bålens och höftens största hopp | 7,3° / 8,9° | 2,9° / 3,8° | 3,1° / 2,4° | 2,6° / 2,0° |
| Överkroppen i originalets ram, median och p90 (promille) | — | 15,8 / 61,6 | 14,8 / 79,7 | 15,9 / 57,0 |
| Överkroppen i rutorna 40–70, median | — | 23,4 | 29,1 | 21,4 |
| Lutningens korrelation mot dagens | 1 | 0,99 | 0,40 | 0,98 |
| Största lutning i rutorna 40–70 | 85° | 58° | 27° | 61° |
| Kontrollen | — | nej: kroppen i bild, ben, p90 | nej: p90, lutningen | **nej: kroppen i bild, ben** |

**Vad videorna visar** (`d_video/k2/oversikt.jpg`):
- **k2, följer originalet:** står upprätt i rutorna 0–15, böjer i höften och sträcker högerarmen ned i rutorna 20–70, rätar på sig kring ruta 80. Ingen påhittad form, ingen kundhand, ingen text.
- **k2, påhittat:** fötterna bleknar bort i bildens nederkant från cirka ruta 40, och huvudet bleknar i ruta 55. Från ruta 95 håller hon upp handflatan mot kameran ("stopp") i stället för att räcka fram armen med handflatan uppåt.
- a och k: se svar 0021. k tappar lutningen och har en svart form från ruta 30. a följer överkroppen men klipper benen.

**Lärdom:** det som binder överkroppen är originalets pixlar i källan. Disken och glaset får ligga kvar, och modellen tar bort dem själv när prompten säger det. Det k tappade (lutningen) kom tillbaka helt. Det som saknas är benen i de nära rutorna, och det är vad nyckelbilderna ska binda.

**Nyckelbilder: förberedda, inte körda.** Codex-isoleringarna i `nyckel2/` ligger i den kamerafria ramen i `kamerafri_k2/nyckel/kf_<ruta>.png` (översikt i `nyckel/oversikt.jpg`), alla åtta med hel kropp och utan ny bildgenerering. Två brister:
- Fotlinjen varierar mellan 1277 och 1820 px, eftersom avbildningen bara passar överkroppen och kamerans perspektiv ändras.
- Ruta 55 är för liten (huvudet låg redan 145 px fel i passningen).

Nästa försök är klart att köra. Efter 0024 punkt 1 är prompten bytt till `P_FOREMAL`, där skeden stannar i handen och "tomma händer" är struket. Försöken heter nu `d2_video.py k2s` (k2 med den nya prompten) och `k2sn` (k2s med nyckelbilder vid rutorna 0, 55, 94 och 136). Ruta 0 och 55 får skeden när ägarens GPT-bilder finns.

**In i förvärlden:** k2 klarar kontrollen bäst (två skäl mot tre och fyra), så den har körts in i förvärlden. Filmen ligger i [g_forvarld/k2/tre_bredvid.mp4](../../scen/3d/gennedbrytning/g_forvarld/k2/tre_bredvid.mp4) och rutbilderna i `tre_bredvid_rutor.jpg`. Hon står upprätt i ruta 0, där dagens förvärld sitter på huk, och lutar sig ned i disken i rutorna 30–55 som originalet. Det gjorde inte k. I slutet blir kroppen för stor och för nära kameran, men det gör den lika mycket i k, så felet ligger i inversen av roten och inte i k2.

## Ändrade eller nya filer
Allt under `scen/3d/gennedbrytning/`:
- Nya skript: `e2_k2.py` (k2-källan och nyckelbilderna), `d2_video.py` (försöken, med prompten `P_ANTAGEN`), `h_kontroll.py` (mått och kontroll).
- Nya mappar och filer: `kamerafri_k2/`, `d_video/k2/` (med `kontroll.json`), `d_video/a/kontroll.json`, `d_video/k/kontroll.json`, `g_forvarld/k2/` och `kontroll_gransar.json`.
- Ändrad: `STRATEGI.md` (avsnittet "En generering är enda källan" och två rader i "Prövat hittills"; det fanns inget om sammansättning att stryka).
- Ändrad: `delegat/svar/0021-…md`, där pekaren nu går hit.

## Kontroll mot "Klart när"
- [x] Tabell över försöken med a, k och dagens läsning: ovan.
- [ ] Minst k2 och ett försök med nyckelbilder: k2 är kört. Nyckelbildsförsöket är förberett men stoppades av fal-saldot.
- [x] Två rader per genererad video: ovan.
- [x] Kontrollens utfall per försök: a, k och k2 fick nej, med skäl.
- [x] Filmen med tre bredvid varandra för bästa försöket: k2.
- [x] `NASTA-BILDER.md` behövs inte nu. Codex-nyckelbilderna finns redan och räcker till första nyckelbildsförsöket.
- [x] `STRATEGI.md` uppdaterad.
- [ ] Bedömning: preliminär, nedan.

**Bedömning (preliminär):**
- **Källa:** k2, alltså kamerafri med originalets pixlar kvar. Den binder överkroppen och lutningen.
- **Prompt:** `P_ANTAGEN`, med borttagningen, antagandet och rörelsen i tid.
- **Det som saknas:** benen i de nära rutorna. Nyckelbilderna ska binda dem.
- **Om k2n håller armarna men fötterna glider:** passa nyckelbilderna så att fotlinjen hålls i den kamerafria ramen. Det görs med en egen likformig avbildning per nyckelbild, inte genom att blanda läsningar.
- **Därefter:** prova `controls.pose.strength = "precise"` på fal (schemat finns i Ray 3.2) som enda ändring.

## Frågor
- **fal behöver fyllas på** (ägaren). Försöken som återstår kostar 0,15 USD styck: k2n, sedan ett eller två till. Cirka 0,50 USD räcker. När saldot är påfyllt kan arbetet fortsätta direkt med `d2_video.py k2s`, `f_las.py k2s` och `h_kontroll.py k2s`, sedan samma sak med `k2sn`.

## Avvikelser
- Kontrollen använder lutningens **korrelation** och inte medianskillnaden, eftersom även a, som följer originalet, har en fast förskjutning på 13°.
- Lutningen mäts i kamerans ram. Det går eftersom k2 är originalets pixlar utan vridning, så perspektivet är detsamma.
- Modals utskrift kraschade på teckenkodningen när loggen gick till fil. Jag körde om med `PYTHONUTF8=1`, utan kodändring.
