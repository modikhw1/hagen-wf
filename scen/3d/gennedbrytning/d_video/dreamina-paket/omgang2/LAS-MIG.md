# Dreamina omgång 2, gelato S1 (0026), att köra för hand

Lärdomar ur utfall 1 (`../svar/k2s.mp4`, svar 0026):
- Tidspassningen klarar 8 s (DTW slår linjär omskalning). Men när källans 4,94 s blev 8 s töjde och tryckte modellen olika delar olika mycket, och höll ut armen på slutet.
- Huvudet ärvde källans raka bildkant i källrutorna 22–69.
- Kameran tippade från cirka 5 s: fotlinjen flyttade sig 230 px upp.
- Handen gick ned till fötterna.

Alla körningar använder **Seedance 2.0 Fast, 9:16, 720P**. Promptens tider är källans mätta segment ur handlingsspåret, skalade till körningens längd. Kör i den här ordningen och spara i `svar/` med namnen nedan.

| # | Läge | Längd | Referenser | Prompt | Spara som | Prövar |
|---|---|---|---|---|---|---|
| 1 | Universell referens | **5 s** | `1_kalla_k2_h264.mp4`, `4_…`–`7_nyckel_…png` | `prompt_1_5s_universell.txt` | `svar/o2_1.mp4` | längd nära källans (4,94 s), huvudet, låst kamera, handen till knähöjd |
| 2 | Universell referens | 5 s | `3_kalla_k2_markering_h264.mp4`, `4_`–`7_` | `prompt_2_5s_markering.txt` | `svar/o2_2.mp4` | som 1, plus en fast fotlinje i källan som ska hålla kameran |
| 3 | Universell referens | **8 s** | `2_kalla_k2_8s_h264.mp4` (källan nedsaktad till exakt 8,0 s), `4_`–`7_` | `prompt_3_8s_nedsaktad.txt` | `svar/o2_3.mp4` | om tiderna följer när källan redan är 8 s |
| 4 | **Flera bildrutor** (ingen video) | 5 s | `4_`–`7_nyckel_…png`, i ordning | en text per övergång i `prompt_4_flera_bildrutor.txt`, tiderna står där (1,8, 1,3, 1,4 s) | `svar/o2_4.mp4` | nyckelbilder på tid utan videoreferens, som jämförelse |

**Om du bara hinner en:** kör 1.

**Nyckelbilderna:** 4–7 är källrutorna 0, 55, 94 och 136, i samma ram som källan. Nyckelbild 5 (ruta 55) visar henne böjd med huvudet helt; den hör till prompten om huvudet. Ruta 0 och 55 saknar fortfarande skeden. Bilderna åt ägarens GPT finns i `luma-agaren/gpt/NASTA-BILDER.md`. Läggs de där, byts 4 och 5 ut av `e3_sked.py`.

**Notera i `svar/installningar.txt`:**
- om tiondels sekunder gick att ställa i Flera bildrutor
- om videon togs emot (den är H.264)
- längden och antalet rutor
