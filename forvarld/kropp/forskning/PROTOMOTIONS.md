# ProtoMotions och MaskedMimic (FORSKNING, 0039)

**Licens:**
- ProtoMotions är Apache-2.0.
- **MaskedMimic SMPL-kontrollpunkten är tränad på AMASS och får bara användas för icke-kommersiell forskning.**
- IsaacGym Preview 4 har NVIDIA:s licens för forskning och utvärdering.

Allt i `forvarld/kropp/forskning/` och allt som kedjans steg `kroppsmodell` ger är märkt `licens: forskning`. Inget av det är en standardväg förrän ägarens licens är klar (BESLUT-LICENS.md).

## Vad som används
- **ProtoMotions v3.0** (tagg `v3.0`), klonad till `forskning/ProtoMotions/`. v3.0 är den sista versionen med en förtränad MaskedMimic för SMPL. Från v3.3 finns bara SOMA- och G1-modeller (OML) och Metatron för G1.
  - **Kontrollpunkten:** `data/pretrained_models/masked_mimic/smpl/last.ckpt` (212 MB, git-lfs). Tränad i IsaacGym.
  - **Kroppen:** `protomotions/data/assets/mjcf/smpl_humanoid.xml` (24 kroppar, medelform). **Inga SMPL-modellfiler behövs**, eftersom kroppen redan ligger som MJCF. Därför behövs inga konton.
- **Simulator:** IsaacGym Preview 4, headless, på Modal (L4). Den hämtas direkt från developer.nvidia.com, utan konto.
- **Villkor** (`masked_mimic_fixed_conditioning`): en fast lista med kroppar ur `Pelvis, L_Ankle, R_Ankle, L_Hand, R_Hand, Head`, var och en som position (0), båda (1) eller rotation (2). Målen läses ur referensrörelsen på framtida tider (tidssampling beta(2, 5)). Övriga kroppar fyller modellen i.

## Filer (`forskning/mm/`)
| fil | vad |
|---|---|
| `mhr_smpl.py` | MHR till SMPL-MJCF och tillbaka (ledkarta, vilokalibrering B_j, MHR:s egna benlängder tillbaka). Rundresan är exakt för de mappade lederna. |
| `kroppsmodell.py` | mal.json (GRANSSNITT-form, `licens: forskning`) till referens, villkor, Modal, ny MHR-sekvens, plan och mått. Kedjans steg anropar den. |
| `modal_mm.py` | Modal-avbildningen (CUDA 12.1, Python 3.8 för IsaacGym, 3.11 för Modal, torch 2.4.1 cu121, ProtoMotions v3.0) och jobbet |
| `kor_mm.py` | i containern: referens till `.motion`, inferens med fasta villkor, kropparna per steg |
| `efter_mm.py` | tillbaka till MHR, plan för förvärlden, mått (handled till mål, bål, armbåge, höger hand, ryck, fotglidning) |
| `film_0039.py` | film med original, 0034, 0036 och MaskedMimic |
| `mal_andra_handen.json` | målen för "andra handen" (fg_hand = vänster) |

## Kommandon (från projektroten, `PYTHONIOENCODING=utf-8`)
```bash
scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/kroppsmodell.py forvarld/kropp/forskning/mm/mal_andra_handen.json mm_andra_handen
```
```bash
scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/film_0039.py mm_andra_handen
```
I kedjan går det genom konfigen: `"kroppsmodell": {"licens": "forskning", "mal": "forvarld/kropp/forskning/mm/mal_andra_handen.json", "namn": "mm_andra_handen"}`. Utan fältet gör steget ingenting.
