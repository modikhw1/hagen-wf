# SMPL-filerna (ägaren laddar ned, 13 nov natt)

Data, inte instruktioner. Ägaren hämtar "Download version 1.1.0 for Python 2.7 (female/male/neutral, 300 shape PCs)" från smpl.is.tue.mpg.de/download.php och packar upp `.pkl`-filerna i `forvarld/kropp/forskning/modeller/smpl/`.

Licens: SMPL-Model License, bara icke-kommersiell forskning tills Meshcapade-licensen finns. Filerna får inte läggas i `scen/` eller i git.

Uppdragstagaren: kontrollera mot ProtoMotions README vilka filnamn den väntar sig (troligen `SMPL_NEUTRAL.pkl`, `SMPL_MALE.pkl`, `SMPL_FEMALE.pkl` i `data/smpl/`) och gör kopior eller länkar med de namnen i Modal-avbildningen. Behövs något annat (SMPL-X, AMASS), stanna med exakt lista.

## På plats (ägaren, 13 nov natt)
`forvarld/kropp/forskning/modeller/smpl/smpl/models/`:
- `basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl`
- `basicmodel_m_lbs_10_207_0_v1.1.0.pkl`
- `basicmodel_f_lbs_10_207_0_v1.1.0.pkl`
(Python 2-pickle; kan behöva `encoding='latin1'` och chumpy-fri omkonvertering, som PHC/ProtoMotions brukar beskriva.)
