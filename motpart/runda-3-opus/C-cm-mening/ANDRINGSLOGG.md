# Ändringar i router.py efter första körningen

Facit och meningar är frysta (meningar/manifest.json). Routern skrevs efter att byggaren läst meningarna, så
körningen på de frysta listorna är inte blind. Varje regeländring efter första körningen står här, med vilken mening
som visade felet. Holdouten (holdout/manifest.json) körs först efter att routern har hashats.

| # | fel | visades av | rättning | allmän regel? |
|---|---|---|---|---|
| 1 | Könsord ('kvinnan') gav "finns inte" när ingen person har känt kön | g11 | personer utan känt kön är kandidater, inte uteslutna | ja: gäller alla klipp utan könsuppgift |
| 2 | "X i stället för att <verb>" tolkades som byte av föremål | n_t4, l1 | byte kräver ett substantiv efter "i stället för", inte "att" | ja: svensk grammatik |
| 3 | "bara är en karaktär" missades (regeln krävde "bara en") | r2 | valfritt "är/vara" mellan | ja |

Routern hashades före holdouten (`holdout/manifest.json`, `router_sha256`). Efter det är `router.py` inte ändrad.

## Ändringar utanför routern efter första körningen

| # | fil | ändring | varför | påverkar siffrorna |
|---|---|---|---|---|
| 4 | kor.py | ett drag som kraschar blir ett redovisat nej (`krasch: true`), inte en avbruten körning | Argons `ga_med_attityd` kraschar i `grindar.mat` på B:s paket (l1@B) | l1@B räknas som ärligt nej och listas som krasch |
| 5 | kor.py (bedom) | alias för facitets dragnamn: `byt_foremal` = `byt_objekt` eller `byt_foremal_i_hand`; `kontrast` = `kontrast_upp/ned` | facit skrevs innan dragen hade namn; n_t6 blev "tyst fel" bara på namnet | n_t6: strikt räkning ger 1 tyst fel, med alias 0. Båda redovisas i RAPPORT.md |
| 6 | drag.py, kor.py | tidskartan märker skarvens blandade rutor (`blandade`), och tidslinjens bevarandemått hoppar över dem | måttet larmade på g3 (391 mm) för att skarvrutor märktes som heltalsrutor | g3, g3@B går från "lackage" till "bevarad"; felinjektionen i `ut/bevarande_prov.json` visar att måttet fortfarande larmar |
| 7 | forhand.py | en etikett per föremål i stället för en per lådsida | sex överlappande etiketter i bilderna (g4, n_t6) | bara bilderna |

## Avstämning 20 nov (ny agent tog över efter att kvoten tog slut 19 nov ca 22:53)

Ingen kod ändrades vid avstämningen. `router.py` har samma sha256 som vid holdouten (`1d449f81…b21e`, kontrollerat med `sha256sum router.py` 20 nov).

| # | fråga | utredning | åtgärd |
|---|---|---|---|
| 8 | 138 körningar mot väntade 132 | Inget fel. 138 = 66 frysta meningar, där 56 körs på två paket (kärnans och B:s) och de 10 btilltal-meningarna bara på ett (btilltal saknar paket), alltså 112 + 10 = 122, plus byggarens 8 meningar × 2 paket = 16. 132 är latensens nämnare: `sammanstall` hoppar över de 6 körningarna med utfallet `ej_korbar` (b1, b2, b4, b6, b8, b9; `kor.py:601-602, 612`). Det finns inga dubbletter av id i `ut/resultat.json`. Holdoutens 22 körningar ligger bara i `ut/holdout_resultat.json` och ingår inte. Kraschen l1@B (ändring #4) räknas en gång. K7-loggen har 138 rader `router.tolka`, en per körning. | ingen; RAPPORT.md redovisar båda talen |
| 9 | B:s paket skrevs om 22:44–22:48, efter huvudkörningen (22:41–22:44) | Huvudkörningens @B-rader gäller alltså en tidigare version av B:s paket. Jag körde om `kor.py --utan-bilder` med `C_UT=ut_B_slutpaket` på B:s slutliga paket. Utfall, klass, K5-nivå och drag är identiska för alla 138 körningar, och bevarandet gav 41 av 41 `bevarad`. | ny mapp `ut_B_slutpaket/`; inget i `ut/` är ändrat |
| 10 | Stämmer körningen under A:s K7-vakt med huvudkörningen? | `ut_k7A/resultat.json` har samma utfall och klass som `ut/resultat.json` för alla 138 körningar. Latensen där är ungefär tio gånger högre, eftersom vakten spårar varje anrop. Rapportens latens kommer därför från `ut/latens.json`. | ingen |
