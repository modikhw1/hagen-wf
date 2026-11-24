# Blind parvis bedömning (54 tagningar, X mot Y)

## 1. Utfall per kategori (antal tagningar, n = 54)

| Kategori | X | Y | lika |
|---|---:|---:|---:|
| Originalkamera (0°) | 18 | 16 | 20 |
| Rum vid vridning (35°/50h) | 29 | 21 | 4 |
| Föremål vid vridning (35°/50h) | 20 | 17 | 17 |
| **Helhet för omregi** | **26** | **27** | **1** |

*Not: X och Y är slumpade per tagning, vilket syns i den jämna totalfördelningen (26 mot 27 på helhet).*

## 2. God nog som 3D-nollpunkt (0.0) för omregi

| Variant | ja | delvis | nej |
|---|---:|---:|---:|
| X | 1 | 20 | 33 |
| Y | 0 | 15 | 39 |
| *Bästa i paret* | *1* | *34* | *19* |

Endast 1 tagning (`chickenstreet/s1` X) når **ja**. I 34 tagningar når den bättre **delvis** (i `08burgerkebab/s9` båda), och i 19 tagningar är båda **nej**.

## 3. Vanligaste fel i vardera (X och Y)

Eftersom metoderna slumpas mellan X och Y uppträder båda feltyperna ungefär lika ofta i X (33 `nej`) som i Y (39 `nej`), men per tagning framträder två tydliga felprofiler:

- **Ostrukturerad / skärvig rekonstruktion (vanligaste förloraren i både X och Y):**
  - Saknar golv, bordsskivor och diskar helt i 35°/50h; dockor och mat svävar i tomt rutnät.
  - Rum, bord och mat exploderar i papperstunna skärvor/konfetti med stora svarta hål.
  - Stora taggiga grå hålsiluetter skär rakt genom mat, väggar och skyltfönster.
  - Flaskor, burkar och lådor kollapsar till tunna halvskal; spökbilder av personer och videotext blir kvar i 0°.
- **Plan-/volymbaserad rekonstruktion (oftare vinnare, men förlorar när planen blir fel):**
  - Enfärgade plan (golv, bord, spis, vägg) lägger sig fel och slukar mat, pannor eller brickor (`duepiani/s10`, `spanjorskan/s2`, `babasburgers/s9`).
  - Gigantiska otexturerade block/skivor täcker halva scenen eller klyver dockor och föremål (`08burgerkebab/s2, s7`, `kennysgelato2.0/s1`, `chickenstreet/s4, s5`).

## 4. Vad den bättre fortfarande gör fel

Även vinnaren i varje par når sällan **ja** (34/54 stannar på **delvis**, 19/54 på **nej**) p.g.a.:
1. **Övermålade och förlorade föremål:** platta bords-/spis-/diskplan täcker stekpannor, pommes, muggar, brickpapper eller kortterminal (`duepiani/s5, s9`, `babasburgers/s1, s2, s6–s8`, `chickenstreet/s2`).
2. **Skymmande förgrunds- och taksjok i 50h:** taklampor, fläktkåpor, hyllor och dörrväggar bildar stora skärvor eller täta väggblock som blockerar kameravyn (`babasburgers/s1, s5, s8`, `chickenstreet/s3`).
3. **Inbränd videotext och spökrester:** överlagrad text blir svävande skärvor eller grå/bruna hål rakt i maten (`babasburgers/s3, s4, s7`, `08burgerkebab/s9`, `blackstone/s1`), och enstaka plagg/hår/händer dröjer kvar.
4. **Trasiga matkanter och fel djup:** matlådor och tallrikar får hål, fransiga/trappstegiga kanter eller svarta glipor i 50h, och dockans ben/bröst skär ibland genom bord eller mat (`duepiani/s11, s12`, `08burgerkebab/s1, s11`, `babasburgers/s11`).
5. **Saknade rumsväggar samt kollaps i mörker/rörelseoskärpa:** sidoväggar och bakgrundsmiljö saknas ofta i 50h, och mörka eller rörelseoskarpa tagningar (`blackstone/*`, `08burgerkebab/s8`) blir helt oanvändbara.
