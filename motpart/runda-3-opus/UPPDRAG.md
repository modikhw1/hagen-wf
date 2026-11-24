# Runda 3 (Opus): fyra spår mot målet, inte mot motparten

19 nov 2026, kväll. Beställt av ägaren: ta projektet så nära slutmålet att runda 2 (Neon) framstår som ett sidospår. Inga lögner, halvlösningar eller saker som bara ser bra ut.

## Målet (en mening)
En CM skriver en mening om ett riktigt 9:16-klipp. Systemet ändrar det som meningen ber om i en 1:1-förvärld av klippet (kamera, rum, kroppar, medielager) och behåller resten, eller säger ärligt nej eller ställer en motfråga. Det sker snabbt, utan generativ AI i CM:s ändringsled och utan klippspecifik kod. Måttstocken är K1–K8 i `motpart/runda-1-claude/SYFTE.md` §4.

## Varför runda 2 inte räcker (orkestratorns läsning)
- Den optimerar rumsmått i cm mot ett facit som Neon själv uppskattat, på samma två klipp som reglerna skrevs på (Exp 7). V5-holdouten är inte körd.
- "0 % hål" är en egenskap hos en genererad bild, inte bevis för att djupet är rätt. Kantalignering mot samma genererings städade bild är cirkulär.
- GT_N för LokalMinne är matcharnas egen union. GT_VIS (`djup_hard_gt_vis_eval.py`) är inte körd.
- K1 (CM-meningar), K5 (det som bär meningen), K6 (manus), K7 (spärr för generativt) och K8 (medielager) berörs inte alls.

## Spår
| spår | mapp | K | kärnfråga |
|---|---|---|---|
| A | `A-domare/` | alla (mätning), K4 hold-out | fryst hold-out + icke-cirkulära mått; prövning av Neons V4-påståenden |
| B | `B-nasta-klipp/` | K4, K2 delvis | osett klipp, allmän ingest till ändringsbar förvärld, utan handpåläggning |
| C | `C-cm-mening/` | K1, K3, K5, K7 | riktiga CM-meningar routas till lagliga drag eller ärligt nej, mätt |
| D | `D-medielager/` | K8, K6 | skärmtext, tal/musik, mat/B-roll och montage som ändringsbara lager + manus per scen |

## Gemensamma regler
Gemensamma regler finns i varje agents uppdrag. Där står också att varje spår avslutas med `RAPPORT.md` i sin mapp.
