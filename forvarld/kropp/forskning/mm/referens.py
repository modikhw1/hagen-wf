"""FORSKNING (0039): referens och villkor för MaskedMimic ur liggarens mål (GRANSSNITT.md, "andra handen").

  scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/referens.py <sekvens.npz> <varld.npz> <ut-mapp>
Referensen är originalets rörelse i SMPL-kroppen. Vänster hand skrivs om till målet i fönstren (skopa 28–66 till tråget, ge 90–146 till
kundens hand), med samma vikt per ruta som 0034 (prov_optimering.vikt). Målet = originalets högra hand i SMPL-kroppen.
Villkor (fasta över klippet): bäcken och fötter som position (stilen och platsen ur originalet), vänster hand som position.
Höger hand, armbågar, bål och huvud är fria: modellen fyller i dem.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mhr_smpl as M
import prov_optimering as O

VARIANTER = {
    'a': [dict(kropp='Pelvis', tillstand=0), dict(kropp='L_Ankle', tillstand=0), dict(kropp='R_Ankle', tillstand=0), dict(kropp='L_Hand', tillstand=0)],
    'b': [dict(kropp='Pelvis', tillstand=0), dict(kropp='L_Ankle', tillstand=0), dict(kropp='R_Ankle', tillstand=0), dict(kropp='L_Hand', tillstand=0),
          dict(kropp='Head', tillstand=2)],
}


def main():
    z = dict(np.load(sys.argv[1])); V = np.load(sys.argv[2]); ut = Path(sys.argv[3]); ut.mkdir(parents=True, exist_ok=True)
    u = M.till_smpl(z, V); S = M.fk_smpl(u['G'], u['rot']); n = len(S)
    w = np.array([O.vikt(f) for f in range(n)], float)
    mal = S[:, M.SN.index('R_Hand')][:, None]           # originalets högra hand i SMPL-kroppen
    np.savez(ut / 'ref.npz', G=u['G'].astype(np.float32), rot=u['rot'].astype(np.float32), fps=29.97, mal_namn=np.array(['L_Hand']), mal=mal.astype(np.float32),
             mal_vikt=w[:, None].astype(np.float32))
    np.savez(ut / 'ref_orig.npz', G=u['G'].astype(np.float32), rot=u['rot'].astype(np.float32), fps=29.97, mal_namn=np.array([], dtype=str),
             mal=np.zeros((n, 0, 3), np.float32), mal_vikt=np.zeros((n, 0), np.float32))
    for k, v in VARIANTER.items(): (ut / f'villkor_{k}.json').write_text(json.dumps(dict(villkor=v, steg=n - 2), ensure_ascii=False, indent=1), encoding='utf-8')
    print('ref', n, 'rutor; vikt>0', int((w > 0).sum()), '; s', round(u['s'], 3))


if __name__ == '__main__': main()
