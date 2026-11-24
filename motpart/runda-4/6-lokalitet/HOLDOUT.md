# Hold-out 21 nov: tre nya klipp, blint facit

Klipp: blackstone (6 tagningar, inga personer), fratelli (5) och chickenstreet (5). Hela kedjan kördes med `kor_holdout.sh` och tog 18,5 min, bildgenerering inräknad. Inga regler ändrades. Domare var Codex gpt-6.1-sol, en annan modell än Gemini som kalibrerade. Domaren bedömde bilderna innan den läste pipens domar (`ut/codex/facit_holdout/`).

| Vad | Kalibreringsklippen (38, Gemini) | Hold-out (16, Codex) |
|---|---|---|
| 0.0 god nog: ja / delvis / nej | 6 / 11 / 21 | 0 / 2 / 14 |
| L8 "hög" som var god nog | 3 av 10 | 0 av 3 |
| Grind 1b, släppta: användbar / delvis / oanvändbar | 21 / 3 / 0 | 8 / 1 / 0 |
| Grind 1b, avvisade som var användbara | 2 av 6 | 1 av 1 |
| Väljaren täcker meningen: ja / delvis / nej | 27 av 38 (strängt mått, efter justering) | 1 / 10 / 5 |
| Vanligaste brister | objekt, rum, skala | objekt (15 fel), rum (13 fel), golv och kontakt |
| Starkast | kamera | kamera (15 ok), skala (10 ok) |

Slutsatser:
- **Grind 1b håller på nya klipp.** Ingen oanvändbar bild har släppts igenom på 54 tagningar. Grinden är fortfarande något för försiktig.
- **Väljaren håller inte.** Justeringen mot Geminis facit var överanpassad, eller så dömer domarna olika strängt. Den ska inte styra något innan den har prövats på nya klipp med en egen signal (segmentering).
- **0.0 är inte god nog på nya klipp heller.** Objekt och rum brister i nästan varje tagning, oberoende av klipp och domare. Det är representationen (skärvor per pixel och klippning vid djupsprång) som brister, inte trösklarna. Det bekräftar facit och pipeutvärderingen: struktur (plan, lådor, kärl) och bättre segmentering är nästa steg.
- **L8 är inte pålitlig** som mått på visuell kvalitet och behöver kalibreras om efter strukturbytet.
