"""0036: rörelsebanken v0 ur kedjans utdata, med liggarens händelser som etiketter. Spegling bara med --spegla (struken som lösning i 0038).

  scen/.venv/Scripts/python.exe forvarld/kropp/bank_bygg.py
Format (BANK.md): en post per händelse i liggaren och person: MHR-pose per ruta (global, modellrum), rotens kameraform (cam_t),
inom, uppåt i modellrummet per ruta (ur varld.npz), etiketter (klipp, scen, händelse, ram, roller, kroppsdel, förlopp), kvalitet,
och spegling: hela kroppen speglad över kroppens mittplan i postens första ruta. Ledernas axlar följer R' = H·R_källa·D, där D per led
räknas ur viloposen (D = (H0·R_vila_källa)^T · R_vila_led; vänster/höger byter plats, mittleder speglas i sig själva).
Ut: forvarld/kropp/bank/v0/poster.jsonl och <id>.npz.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Ro

SPEGLA = '--spegla' in sys.argv  # 0038: helspegling struken som lösning; bara på begäran, för forskning
ROOT = Path(__file__).resolve().parents[2]; KON = ROOT / 'scen/3d/kontrakt/ut'; UT = Path(__file__).resolve().parent / 'bank/v0'
N = json.loads((ROOT / 'scen/3d/ingest/mhr_ledernamn.json').read_text()); ix = N.index; F = np.diag([1., -1., -1.]); H0 = np.diag([-1., 1., 1.])
PART = [ix(('r_' + n[2:]) if n.startswith('l_') else ('l_' + n[2:]) if n.startswith('r_') else n) for n in N]
KALLOR = [  # klipp, källa, liggare, kvalitet
    ('gelato', 'kand-kennysgelato_n06-hand/kalla_0033.json', 'kand-kennysgelato_n06-hand/liggare_0033.json', {'s1': 'generering (Dreamina), roträttad; kontroll NEJ som diagnos', 's2': 'ingest ur originalet'}),
    ('b-tilltal', 'b-tilltal-ravara_n06-hand/kalla_0032.json', 'b-tilltal-ravara_n06-hand/liggare_0032.json', {}),
    ('guacamole', 'e-dialog-guacamole_grupp/kalla_0032.json', 'e-dialog-guacamole_grupp/liggare_0032.json', {}),
]


def D_led(rest):
    R = Ro.from_quat(rest[:, 3:7]).as_matrix(); return np.array([(H0 @ R[PART[i]]).T @ R[i] for i in range(len(N))])


def spegla(P, D):
    """Hela kroppen speglad över mittplanet i första rutan (normal: höftled vänster minus höger, genom roten)."""
    p0 = P[0]; nv = p0[ix('l_upleg'), :3] - p0[ix('r_upleg'), :3]; nv /= np.linalg.norm(nv); c = p0[ix('root'), :3]; H = np.eye(3) - 2 * np.outer(nv, nv)
    Q = P.copy(); R = Ro.from_quat(P[..., 3:7].reshape(-1, 4)).as_matrix().reshape(P.shape[0], P.shape[1], 3, 3)
    for i in range(len(N)):
        s = PART[i]; Q[:, i, :3] = c + (P[:, s, :3] - c) @ H.T
        Q[:, i, 3:7] = Ro.from_matrix(H @ R[:, s] @ D[i]).as_quat()
    return Q


def main():
    UT.mkdir(parents=True, exist_ok=True); poster = []
    for klipp, kf, lf, kval in KALLOR:
        K = json.loads((KON / kf).read_text(encoding='utf-8')); L = json.loads((KON / lf).read_text(encoding='utf-8')); fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare']
        sc = {s['id']: s for s in K['semantik']['scener']}; kam = {k['id']: k for k in K['matning']['kameror']}
        forl = {h: f['id'] for f in L['forlopp'] for h in f['handelser']}
        for h in L['handelser']:
            ag = h['roller'].get('agent')
            if h['ram'] == 'scenbyte' or ag not in {p['id'] for p in K['semantik']['personer']}: continue
            a, b = h['rutor']; sid = next((s for s, x in sc.items() if round(x['start_s'] * fps) <= a < round(x['slut_s'] * fps)), None)
            if sid is None: continue
            mp = next((m for m in K['matning']['personer'] if m['person'] == ag and m.get('scen') in (None, sid)), None)
            if mp is None: continue
            k = kam[sc[sid]['kamera']]; off = k.get('kalla_ruta0', 0); z = np.load(KON / Path(kf).parent / mp['rorelse']['sokvag']); V = np.load(KON / Path(kf).parent / k['spar_metrisk']['sokvag'])
            la, lb = a - off, min(b - off, len(z['pose']))
            if lb - la < 4: continue
            P = z['pose'][la:lb].astype(float); up = np.array([F.T @ V['kam_R'][f].T @ (V['upp'] / np.linalg.norm(V['upp'])) for f in range(la, lb)])
            D = D_led(z['rest'])
            kd = h['roller'].get('kroppsdel', '')
            for spegel in ((False, True) if SPEGLA else (False,)):
                pid = f'{klipp}_{sid}_{h["id"]}_{ag}' + ('_speglad' if spegel else '')
                PP = spegla(P, D) if spegel else P
                np.savez(UT / f'{pid}.npz', pose=PP.astype(np.float32), cam_t=z['cam_t'][la:lb], inom=z['inom'][la:lb], upp=up, rest=z['rest'])
                sida = ('hoger' if kd.endswith('_h') else 'vanster' if kd.endswith('_v') else 'bada') if kd else 'okand'
                if spegel and sida in ('vanster', 'hoger'): sida = {'vanster': 'hoger', 'hoger': 'vanster'}[sida]
                poster.append(dict(id=pid, klipp=klipp, scen=sid, handelse=h['id'], ram=h['ram'], roller=h['roller'], forlopp=forl.get(h['id']), person=ag,
                                   kroppsdel_sida=sida if not spegel else sida, rutor_kalla=[a, b], rutor=lb - la, sekunder=round((lb - la) / fps, 2), speglad=spegel,
                                   kvalitet=kval.get(sid, 'ingest ur originalet (ej roträttad)'), fil=f'{pid}.npz'))
    with open(UT / 'poster.jsonl', 'w', encoding='utf-8') as f:
        for p in poster: f.write(json.dumps(p, ensure_ascii=False) + '\n')
    from collections import defaultdict
    st = defaultdict(lambda: [0, 0.]); [st[p['ram']].__setitem__(slice(None), [st[p['ram']][0] + 1, st[p['ram']][1] + p['sekunder']]) for p in poster]
    print('poster', len(poster), 'sekunder', round(sum(p['sekunder'] for p in poster), 1)); print({k: (v[0], round(v[1], 1)) for k, v in sorted(st.items())})
    json.dump({k: dict(poster=v[0], sekunder=round(v[1], 1)) for k, v in st.items()}, open(UT / 'innehall.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__': main()
