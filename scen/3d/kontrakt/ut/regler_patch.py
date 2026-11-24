"""Engångspatch med bevarade original. Kör från projektroten."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera


def edit(path, old, new):
    p = Path(path); s = p.read_text(encoding='utf-8')
    if old not in s: raise ValueError(f'Saknar söktext i {p}: {old[:100]}')
    sakerhetskopiera(p); p.write_text(s.replace(old, new), encoding='utf-8', newline='\n')


I = 'scen/3d/ingest/ingest_klipp.py'
edit(I, 'import numpy as np, cv2', 'import numpy as np, cv2\nfrom sakra_filer import sakerhetskopiera, arkivera\nfrom regler import kamerabeslut, kort_kamerabana, overkropp')
edit(I, "    if not recs:\n        return dict(registrerade=0, av=antal, fel_px=None, fokal_px=None, statisk=True)", "    if not recs:\n        x = dict(registrerade=0, av=antal, fel_px=None, fokal_px=None, statisk=True)\n        x['beslut'] = kamerabeslut(x, M)\n        (ut / 'kamera.json').write_text(json.dumps(x))\n        return x")
edit(I, "    (ut / 'kamera.json').write_text(json.dumps(x)); x.pop('pose'); return x", "    x['beslut'] = kamerabeslut(x, M)\n    x['statisk'] = statisk or x['beslut']['kalla'] != 'COLMAP'\n    (ut / 'kamera.json').write_text(json.dumps(x)); x.pop('pose'); return x")
edit(I, "    fokal = K.get('fokal_px') or max(M['bredd'], M['hojd'])", "    beslut = kamerabeslut(K, M)\n    fokal = beslut['fokal_px']")
edit(I, "    (ut / 'jobb.json').write_text(json.dumps(jobb))", "    (ut / 'kropp_indata.json').write_text(json.dumps(dict(kamera=beslut, personrutor=len(jobb), personer=list(P))))\n    (ut / 'jobb.json').write_text(json.dumps(jobb))\n    if not jobb:\n        (ut / 'kropp').mkdir(exist_ok=True)\n        (ut / 'kropp/timing.json').write_text(json.dumps(dict(jobb=0, status='uppmatt', orsak='Inga personer; inget GPU-anrop.')))\n        return dict(jobb=0)")
edit(I, "        x[pid] = json.loads(r.stdout.strip().splitlines()[-1])", "        x[pid] = json.loads(r.stdout.strip().splitlines()[-1])\n        x[pid]['utsnitt'] = overkropp(x[pid])\n        (ut / f'utsnitt_{pid}.json').write_text(json.dumps(x[pid]['utsnitt']))")
edit(I, "    for pid, S in seq.items():\n        sk = np.ones(N)", "    for pid, S in seq.items():\n        utsnitt = json.loads((ut / f'utsnitt_{pid}.json').read_text()) if (ut / f'utsnitt_{pid}.json').exists() else {}\n        if utsnitt.get('endast_overkropp'):\n            S['golv_skala'] = np.ones(N)\n            np.savez(ut / f'sekvens_{pid}.npz', **S)\n            x[pid] = dict(status='saknas', orsak='Endast överkropp; golvkontakt används inte.')\n            continue\n        sk = np.ones(N)")
edit(I, "    if K.get('pose') and not K.get('statisk'):", "    kb = kamerabeslut(K, M)\n    if K.get('pose') and not K.get('statisk') and kb['kalla'] == 'COLMAP':")
edit(I, "    upp = np.mean([R[i]", "    bana = kort_kamerabana(k * C)\n    if bana['statisk']:\n        R = np.repeat(np.eye(3)[None], N, 0); C = np.zeros((N, 3)); k = 1.0\n    upp = np.mean([R[i]")
edit(I, "for p in seq for i in range(N) if seq[p]['inom'][i]], 0)", "for p in seq for i in range(N) if seq[p]['inom'][i]], 0) if seq else np.array([0., -1., 0.])")
edit(I, "return dict(skala=round(k, 4), ojamnhet_cm=round(ojamn(k) * 100, 3), kamerans_vag_m=round(vag, 2))", "return dict(skala=round(k, 4), ojamnhet_cm=round(ojamn(k) * 100, 3), kamerans_vag_m=round(vag, 2), kamerabeslut=kb, banbeslut=bana, upp_kalla='kroppsmodell' if seq else 'antagen: lodrät kamera utan personer')")
edit(I, "shutil.rmtree(d, ignore_errors=True);", "arkivera(d);")
edit(I, "    shutil.rmtree(ut / 'render', ignore_errors=True)", "    arkivera(ut / 'render')")
edit(I, "                shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)", "                arkivera(p)")
edit(I, "    cd.sensor_fit", "    cd.sensor_fit") if False else None

# Kontakt och golv får inte tolka en gissad underkropp som evidens.
C = 'scen/3d/ingest/kontakt.py'
edit(C, "        bs = S['ben_synliga'].astype(bool)", "        utsnitt = ut / f'utsnitt_{pid}.json'\n        if utsnitt.exists() and json.loads(utsnitt.read_text()).get('endast_overkropp'):\n            x[pid] = dict(status='saknas', orsak='Endast överkropp; ingen kontaktlösning.')\n            continue\n        bs = S['ben_synliga'].astype(bool)")
