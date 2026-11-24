# Dreamina omgång 3: huvudrum (0035, återskapning 1:1)

Syfte: återskapa originalet (gelato S1) trognare. Inga alternativa versioner.

Ändring mot första omgången (en sak):
- Källan har huvudrum. `1_kalla_k2_huvudrum.mp4` är samma kamerafria källa (k2), skalad till 82 % med fötterna fasta och grå yta ovanför.
- Skäl: originalets överkant skär hennes huvud i källrutorna 58–77 (`kamerafri/kanten_skar_huvudet.json`), och Dreamina ärvde det och skar dessutom 22–69.
- Prompten är densamma, med en rad om att huvudet alltid syns och att längden hålls.

Kör: Dreamina, Universell referens, referensvideo `1_kalla_k2_huvudrum.mp4`, prompt `prompt.txt`, 5 s, 9:16. Lägg svaret i `svar/`. Kedjan tar vid med en konfig likt `kedja/kand-kennysgelato-tagningar/S1_omgang2.json` (paket `d_video/dreamina-paket/omgang3_huvudrum`). Obs: avbildningen måste då ta med skalningen 0,82 (inversen före avbildningens invers, som för guacamoles 62 %).
