import sys
from pathlib import Path
sys.path.insert(0,str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera
def edit(path,old,new):
 p=Path(path);s=p.read_text(encoding='utf-8')
 if old not in s:raise ValueError(f'{p}: {old[:100]}')
 sakerhetskopiera(p);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
F='scen/3d/ingest/flera/ingest_flera.py'
edit(F,"ut.mkdir(parents=True, exist_ok=True); M = IK.meta(klipp, ut)", "ut.mkdir(parents=True, exist_ok=True)\n    if (ut / 'meta.json').exists() and (ut / 'personer.json').exists(): M = json.loads((ut / 'meta.json').read_text())\n    else:\n        sakerhetskopiera(ut)\n        M = IK.meta(klipp, ut)")
I='scen/3d/ingest/ingest_klipp.py'
edit(I,"        x[pid]['utsnitt'] = overkropp(x[pid])", "        x[pid]['utsnitt'] = overkropp(x[pid])\n        # Knän krävs inne i både egen personruta och bild. Maskunion ensam räcker inte.\n        knan = []\n        for raw in (ut / 'kropp' / pid).glob('*.npz'):\n            f = str(int(raw.stem)); box = P[pid].get(f)\n            if box is None: continue\n            kp = np.load(raw)['pred_keypoints_2d'][11:13]\n            knan.append(any(0 <= xx < M['bredd'] and 0 <= yy < M['hojd'] and box[0] <= xx <= box[2] and box[1] <= yy <= box[3] for xx, yy in kp))\n        if knan and np.mean(knan) < .1:\n            x[pid]['utsnitt'].update(endast_overkropp=True, knan_i_egen_ruta_andel=float(np.mean(knan)), orsak='Under 10 % rutor med skattat knä i bild och egen personruta; underkroppen saknar bildstöd.')")
edit(I,"    return dict(id=valda", "    return dict(id=valda") if False else None
# Fokalen måste omvandlas från px även när en sekvens finns.
M='scen/3d/ingest/mhr_rig.py'
edit(M,"float(np.load(sekvenser[0])['fokal']) if sekvenser else max(meta['bredd'], meta['hojd']) * 36 /", "(float(np.load(sekvenser[0])['fokal']) if sekvenser else max(meta['bredd'], meta['hojd'])) * 36 /")
