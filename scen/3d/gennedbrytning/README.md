# Generativ nedbrytning: kedjan

Den generativa nedbrytningen för en tagning körs med en rad (0030):

```
scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/kedja.py scen/3d/gennedbrytning/kedja/<klipp>/<tagning>.json
```

- **Konfigen** säger allt som var gelato-specifikt (se `tagning.py`).
- **Cachen:** varje steg har en egen post i `kedja/<namn>/steg.json`, en hash av konfigen, indatafilerna och skriptet. Stegen körs om bara när något ändrats; `--tvinga` kör om ändå, och `--fran` och `--till` väljer ett intervall.
- **Loggen:** varje steg skriver kommando, tid och utfall till `kedja/<namn>/logg.jsonl`, och stegets egen logg bredvid.
- **Väntan:** kedjan stannar rent med kod 2 och `VÄNTAR` när genereringen inte finns än. Samma kommando tar vid när svaret ligger i paketets `svar/`.

Strategin står i `STRATEGI.md`. Den här filen säger bara hur kedjan körs.

## Stegen

| Steg | Skript | Ut |
|---|---|---|
| (före) relevans | `relevans/relevans_steg.py <klipp> --namn relevans_0030` | `relevans/<klipp>/relevans_0030.json` (med handlingsposter) |
| (före) tom scen, lager, kamerafri källa | `b_tom_scen.py`, `codex_bild.py`, `e4_kamerafri.py` | bilder och `avbildning.json`; körs inte av kedjan än |
| generering | leverantör: `dreamina_hand` skriver eller läser paketet; `fal_ray` (`d2_video.py`) kräver saldo | `d_video/<namn>/isolerad.mp4` |
| las | `f_las.py` (Modal, SAM 3D Body) | `d_video/<namn>/las/` |
| kontroll | `h_kontroll.py` | ja eller nej, med skäl |
| tid | `t_tid.py` | `d_video/<namn>/tid.json`, `d_video/<namn>_t/` |
| forvarld | `g_forvarld.py --kamerafri` (sekvensstabilisering i sam3db-venv, bygge) | `g_forvarld/<namn>_t/` |
| samspel | `j_samspel_blender.py` | `samspel/<namn>.json` |
| rot | `r_rot.py` | `g_forvarld/<namn>_t_rot/`, `samspel/<namn>_rot.json` |
| kamera | `r_kamera.py` | `g_forvarld/<namn>_t_kam/` |
| scen1, sked, scen2 | `s_scen.py`, `r_sked.py`, `r_sked2.py`, `r_synlig_blender.py` | `s_<namn>/` (plan, scen.blend, render, synlighet) |
| mening | `v_mening.py` | `s_<namn>/mening.json`, film |
| kalla | `kontrakt/kalla_generering.py`, `kontrakt/kalla_mening.py` | ny källa (om konfigen anger `kalla`) |
| handlingsspår (vilket klipp som helst) | `m_handling.py <kalla> <scen> --gemini …` | `handling/<klipp>/<scen>/handling.json` |

## Det som var gelato-specifikt och nu är parameter (`tagning.py`)

- tagningen och ingestmappen (`klipp`, `tagning`, `scen`)
- förskjutningen mellan klippets och ingestens rutor (`offs`, gelato 7)
- källans längd (`kalla_rutor`)
- kedjans plan (`plan`)
- handlingsspåret (`handling`)
- avbildningen (`avbildning`)
- kamerans modell och låsningar (`kamera`)
- scenens flaggor (`scen_flaggor`: tråg, glas, bakkant)
- föremålet i handen (`handforemal`, eller null)

Utan konfig gäller gelato S1 med de gamla värdena.

**Finns i konfigen men används inte än:**
- `ankare: sate`: `r_rot.py` låser bara fötterna.
- `utzoom`: inversen av guacamoles 62 % görs inte.
- `vandpunkter`: `t_tid.py` räknar fortfarande h3 och h8 som diagnos.

Guacamole S1 kräver de två första.

## Skript som kedjan ersätter

- `l_handling.py`: ersatt av `m_handling.py` (allmän, ur ingestens läsning). Gelatos spår är kvar som det var.
- `g_forvarld.py` utan konfig, `e_kamerafri.py` och `e2_k2.py`: `e4_kamerafri.py` är den allmänna.
- `d_video.py`, `d2_video.py` och `p_omgang2.py` är leverantörsskript. Kedjan anropar dem inte direkt; de skriver paket.

Experimentskript som inte ingår i kedjan:
- `komponera.py` (sammansättning, förkastad)
- `passa.py`
- `las_stillbild.py`
- `k_disk.py`
- `e3_sked.py`
- `b_registrera.py`
- `c_isolerad.py`
- `r_fel.py` (diagnos)
- `r_synlig.py` (snabbt mått före bygget)

## Konfigar

- `kedja/kand-kennysgelato-tagningar/S1.json`: Dreaminas befintliga generering genom hela kedjan (0030-provet).
- `kedja/kand-kennysgelato-tagningar/S1_omgang2.json`: väntar på ägarens svar i `d_video/dreamina-paket/omgang2/svar/`.
- `kedja/e-dialog-guacamole-tagningar/S1.json`: väntar på svar i `d_video/dreamina-paket/guacamole-S1/svar/` och behöver `ankare: sate` och `utzoom` (se ovan).
