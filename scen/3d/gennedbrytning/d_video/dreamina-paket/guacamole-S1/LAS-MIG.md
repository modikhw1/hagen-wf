# Dreamina, guacamole S1 (0026), att köra för hand

Samma steg som för gelato: kamerafri källa med originalets pixlar kvar (`e4_kamerafri.py`), föremålet i handen kvar (mobilen), prompt med antagandet och tiderna, och nyckelbilder ur Codex (steg A och B, ny session per bild).

## Körning 1 → `svar/guac_s1.mp4`
- **Läge:** Seedance 2.0 Fast, Universell referens, 9:16, 720P, **5 s**.
- **Referenser:** `2_kalla_kamerafri_5s.mp4` (källan nedsaktad från 2,93 till 5,00 s, 150 rutor), `3_nyckel_kallruta000.png` och `4_nyckel_kallruta087.png`.
- **Prompt:** `prompt_1_5s_universell.txt`.
- Om webbappen nekar videon (som förra gången): `1_kalla_kamerafri.mp4` är samma källa i originalfart (2,93 s). Då blir längden 5 s ändå, och tidspassningen (`t_tid.py`) tar hand om resten.

## Så valdes personerna
- **S1 har bara en person i bild:** kunden A, som sitter med mobilen. Personalen B syns först i S2 och S4.
- **En person per körning och tagning.** Varje generering ska ge en kropp ur en video. Med båda i samma bild (S4) får modellen hitta på två skymda kroppar samtidigt, och läsningen måste skilja dem åt.
- **B görs i en egen körning ur S2,** när A håller. **S4 med båda** blir ett senare prov, med två spår.

## Det som skilde guacamole från gelato (inte allmänt än)
1. **Han sitter.** Det skymda är ben och en pall, inte ben som står. Pallen bakas in med honom i genereringen. Det är en möbel, men utan den kan han inte sitta. Relevanslistan har pallen som `ramar`, så i förvärlden blir den egen form, och i genereringen är den ett stöd.
2. **Ramen måste zoomas ut.** Han sitter så nära kameran att benen hamnar under bildkanten. Källan och nyckelbilderna är därför förminskade till 62 % med grå marginal (`avbildning.json`, `extra_utzoomning`). Läsningen tillbaka ska ta inversen av både utzoomningen och avbildningen. `g_forvarld.py` kan bara den senare, så det behöver läggas till.
3. **Kameran står nästan still** (skala 0,98–1,00). Den kamerafria källan är nästan originalet, och avbildningen gör nästan ingenting.
4. **Ingen främmande hand i personmasken.** Handen med terminalen nere till vänster är inte med i ingestens mask, så den tas bort med prompten i stället för att målas grå.
5. **Tiderna är lästa ur kontaktbladet, inte mätta.** Det finns inget handlingsspår för guacamole än. Tal (en replik) och blick (han tittar på mobilen och sedan upp) är det som bär. Det är inte rörelse, och dagens drag i tidspassningen (lutning, handleder) ser det knappt. Tidspassningen behöver huvudets riktning som drag för den här tagningen.
6. **Nyckelbilden i ruta 87 tittar på mobilen,** men i originalet tittar han upp åt höger. Codex följde prompten ("looking at it") och inte bilden. Prompten säger därför att han tittar upp i slutet.

## Därefter
`f_las.py`, `t_tid.py` (med huvudets riktning som drag), `h_kontroll.py`, och in i förvärlden. Det sista kräver att inversen av utzoomningen finns (punkt 2).
