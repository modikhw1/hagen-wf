"""FORSKNING: en tagning ur kedjans källa och liggare som referens för kroppskontrollern, för vilket klipp som helst.

  las(kalla, liggare, scen, person)   sekvens, värld, bildfrekvens och liggarens händelser i tagningens egna rutor
  referens(t)                          MHR -> SMPL, rimlighetsgrind, och bara de rättningar grinden kräver (varje beslut med skäl)
  rimlighet(S)                         går ställningen att stå i? mätt, inte bedömt
  jamna(pos, rot, sigma)               tar bort simuleringens darr ur utfallet
  tillbaka(t, ref, mm_npz)             utfallet som MHR-sekvens i kedjans format

Sökvägar för kalla och liggare är relativa scen/3d/kontrakt/ut. Kör som prov:
  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/tagning.py <kalla> <liggare> [<scen> <person>]
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[3]; KON = ROOT / 'scen/3d/kontrakt/ut'
sys.path.insert(0, str(HIT)); import mhr_smpl as M
sys.path.insert(0, str(ROOT / 'scen/3d/ingest')); import metrisk as MET
ix = M.SN.index
BEN = [n for n in M.SN if any(k in n for k in ('Hip', 'Knee', 'Ankle', 'Toe'))]
# Diagnosgränser, satta 16 nov ur gelato S1. Inga krav från ägaren.
STOD_MAX_CM = 30      # bäckenet så långt från fotledernas mitt i vågrät led: går inte att stå i utan stöd
ROTVAG_MAX_CM = 15    # bäckenets väg i vågrät led som godtas när benen inte går att lita på
SITTER_M = 0.65       # bäckenhöjd under detta: personen sitter, och simuleringen har ingen möbel


def las(kalla, liggare, scen=None, person=None):
    K = json.loads((KON / kalla).read_text(encoding='utf-8')); L = json.loads((KON / liggare).read_text(encoding='utf-8'))
    fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare']; sc = {s['id']: s for s in K['semantik']['scener']}
    kam = {k['id']: k for k in K['matning']['kameror']}; scen = scen or K['semantik']['scener'][0]['id']
    mp = next((m for m in K['matning']['personer'] if m.get('scen') in (None, scen) and (person is None or m['person'] == person)), None)
    if mp is None: raise SystemExit(f'ingen rörelse för scen {scen}, person {person} i {kalla}')
    person = mp['person']; k = kam[sc[scen]['kamera']]; off = k.get('kalla_ruta0', 0); bas = KON / Path(kalla).parent
    # Läs som riggen läser (metrisk.las): äldre filer utan golv_version visas med pose_fore_kontakt och cam_t_fore_golv. Rå np.load gav fel
    # utgångsläge (cam_t 7 cm fel i b-tilltal S3), och tillbaka skrev en fil som riggen sedan ersatte med originalet (trofé, 16 nov).
    z = dict(MET.las(bas / mp['rorelse']['sokvag'])); V = dict(np.load(bas / k['spar_metrisk']['sokvag'])); n = len(z['pose']); H = []
    for h in L['handelser']:
        if h['ram'] == 'scenbyte' or h['roller'].get('agent') != person: continue
        a, b = max(0, h['rutor'][0] - off), min(n, h['rutor'][1] - off)
        if b - a < 3: continue
        kd = h['roller'].get('kroppsdel', ''); sida = 'R_Hand' if kd.endswith('_h') else 'L_Hand' if kd.endswith('_v') else None
        H.append(dict(id=h['id'], ram=h['ram'], rutor=[a, b], kropp=sida, roller={x: y for x, y in h['roller'].items() if x != 'agent'}, not_=h.get('anmarkning', '')))
    P = next((p for p in K['semantik']['personer'] if p['id'] == person), {})
    besk = f"{P.get('beskrivning', 'En person.')} Roll: {P.get('roll', 'okänd')}. Scenen: {sc[scen].get('syfte') or sc[scen].get('funktion') or ''} Miljö: {sc[scen].get('miljo') or 'okänd'}."
    klipp = Path(kalla).parent.name.split('_')[0]
    return dict(namn=f'{klipp}_{scen}_{person}', kalla=kalla, liggare=liggare, scen=scen, person=person, fps=fps, off=off, z=z, V=V, handelser=H, beskrivning=besk,
                ben_synliga=float(np.mean(z['ben_synliga'])) if 'ben_synliga' in z else None, sekvens=str(mp['rorelse']['sokvag']))


def rimlighet(S):
    """Mått på om ställningen går att stå i. S: (T, 24, 3), z upp, meter."""
    mitt = (S[:, ix('L_Ankle'), :2] + S[:, ix('R_Ankle'), :2]) / 2; d = np.linalg.norm(S[:, 0, :2] - mitt, axis=1) * 100
    return dict(stod_median_cm=round(float(np.median(d)), 1), stod_max_cm=round(float(d.max()), 1),
                rotvag_cm=round(float(np.linalg.norm(np.ptp(S[:, 0, :2], axis=0))) * 100, 1),
                fotvag_cm=round(float(max(np.linalg.norm(np.ptp(S[:, ix(f), :2], axis=0)) for f in ('L_Ankle', 'R_Ankle'))) * 100, 1),
                backenhojd_m=round(float(np.median(S[:, 0, 2])), 2), lagsta_fot_m=round(float(min(S[:, ix('L_Ankle'), 2].min(), S[:, ix('R_Ankle'), 2].min())), 2))


def referens(t, tvinga=None):
    """Ger dict(G, rot, S, u, fore, efter, beslut). tvinga: {'ben': bool, 'rot': bool} går förbi grinden (för prov)."""
    u = M.till_smpl(t['z'], t['V']); G, rot = u['G'].copy(), u['rot'].copy(); T = len(G); S = M.fk_smpl(G, rot); fore = rimlighet(S); beslut = []
    rot_fore = rot.copy()
    bs = t['ben_synliga']; tv = tvinga or {}
    if fore['backenhojd_m'] < SITTER_M:
        beslut.append(dict(vad='sitter', skal=f"bäckenet ligger på {fore['backenhojd_m']} m: personen sitter, och simuleringen har ingen möbel att sitta på", atgard='ingen: utfallet är opålitligt tills sitsen finns i simuleringen'))
    byt_ben = tv.get('ben', (bs is not None and bs < 0.5) or fore['stod_max_cm'] > STOD_MAX_CM)
    if byt_ben and fore['backenhojd_m'] >= SITTER_M:
        skal = (f'benen syns inte i bild (ben_synliga {bs:.2f})' if bs is not None and bs < 0.5 else
                f"bäckenet ligger upp till {fore['stod_max_cm']} cm från fötternas mitt: ingen kan stå så utan stöd")
        y = G[:, 0] @ np.array([0., 1., 0.]); yaw = gaussian_filter1d(np.unwrap(np.arctan2(y[:, 1], y[:, 0])) - np.pi / 2, 6, mode='nearest'); c, s = np.cos(yaw), np.sin(yaw)
        Rz = np.zeros((T, 3, 3)); Rz[:, 0, 0] = c; Rz[:, 0, 1] = -s; Rz[:, 1, 0] = s; Rz[:, 1, 1] = c; Rz[:, 2, 2] = 1
        for n in BEN: G[:, ix(n)] = Rz
        beslut.append(dict(vad='ben', skal=skal, atgard='raka ben under bäckenet, vända som bäckenet (antagen: står)'))
        if tv.get('rot', fore['rotvag_cm'] > ROTVAG_MAX_CM):
            rot[:, :2] = rot[0, :2]
            beslut.append(dict(vad='rot', skal=f"bäckenet färdas {fore['rotvag_cm']} cm medan fötterna rör sig {fore['fotvag_cm']} cm, och benen går inte att lita på: "
                                               'troligen kamerarörelse som hamnat i kroppen', atgard='roten står kvar i sidled och djupled (antagen: står kvar)'))
        S = M.fk_smpl(G, rot); rot[:, 2] -= np.minimum(S[:, ix('L_Ankle'), 2], S[:, ix('R_Ankle'), 2]) - 0.05; S = M.fk_smpl(G, rot)
    u['G'], u['rot'] = G, rot
    # aterflytt: det grinden tog bort ur roten. Kroppen simuleras utan det, men scenens kamera förväntar sig det, så det läggs tillbaka i tillbaka().
    return dict(G=G, rot=rot, S=S, u=u, fore=fore, efter=rimlighet(S), beslut=beslut, aterflytt=rot_fore - rot)


def jamna(pos, rot=None, sigma=1.0):
    """Gaussfilter över tid. sigma 1 ruta tar rycket till referensens nivå utan att träffen ändras (FELSOK.md). rot: kvaternioner xyzw."""
    p = gaussian_filter1d(pos, sigma, axis=0, mode='nearest') if sigma else pos
    if rot is None: return p
    q = rot.astype(float).copy()
    for f in range(1, len(q)): q[f] *= np.where((q[f] * q[f - 1]).sum(-1, keepdims=True) < 0, -1.0, 1.0)
    q = gaussian_filter1d(q, sigma, axis=0, mode='nearest') if sigma else q
    return p, q / np.linalg.norm(q, axis=-1, keepdims=True)


def las_utfall(mm_npz, S, sigma=1.0):
    """Simulatorns kroppar lagda på referensens plats. Ger P (k, 24, 3), kvaternioner, och antal steg."""
    d = dict(np.load(mm_npz, allow_pickle=True)); pos, q = jamna(d['pos'].astype(float), d['rot'].astype(float), sigma); k = min(len(pos), len(S) - 1)
    P = pos[:k] - d['skift'][None, None]; P = P - np.r_[(P[0, 0] - S[1, 0])[:2], 0.]
    return P, q[:k], k, float(d['dt'])


def tillbaka(t, ref, mm_npz, ut, sigma=1.0):
    """Utfallet som MHR-sekvens med samma nycklar som kedjans sekvens. Märkt forskning av den som anropar."""
    from scipy.spatial.transform import Rotation as Ro
    z, V, u = t['z'], t['V'], ref['u']; n = len(z['pose']); P, q, k, _ = las_utfall(mm_npz, ref['S'], sigma)
    Gs = Ro.from_quat(q.reshape(-1, 4)).as_matrix().reshape(k, -1, 3, 3); rs = P[:, 0]
    G = np.concatenate([u['G'][:1], Gs, np.repeat(Gs[-1:], max(0, n - 1 - k), 0)])[:n]; R = np.concatenate([u['rot'][:1], rs, np.repeat(rs[-1:], max(0, n - 1 - k), 0)])[:n]
    R = R + ref['aterflytt'][:n]   # samma förflyttning som originalet hade i scenens kamera (till exempel en inåkning som låg i kroppen)
    Pm, T = M.fran_smpl(G, R, u, z); Gr = M.gravitation(V['upp']); cam_t = np.array([V['kam_R'][f].T @ (Gr.T @ T[f] - V['kam_C'][f]) for f in range(n)])
    zz = dict(z); zz['pose'] = Pm.astype(z['pose'].dtype); zz['cam_t'] = cam_t.astype(z['cam_t'].dtype); np.savez(ut, **zz)
    return ut


if __name__ == '__main__':
    a = sys.argv[1:]; t = las(a[0], a[1], *(a[2:4])); r = referens(t)
    print(t['namn'], '|', len(t['z']['pose']), 'rutor,', round(t['fps'], 2), 'fps | ben_synliga', t['ben_synliga']); print(t['beskrivning'])
    print('händelser:', [(h['id'], h['ram'], h['rutor'], h['kropp']) for h in t['handelser']])
    print('före :', r['fore']); print('efter:', r['efter'])
    for b in r['beslut']: print(' -', b['vad'] + ':', b['skal'], '=>', b['atgard'])
