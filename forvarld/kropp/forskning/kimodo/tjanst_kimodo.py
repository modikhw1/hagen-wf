"""FORSKNING/0040: Kimodo-SOMA-RP på Modal. Avbildningen cachas, vikter i volymen 'hagen-kimodo'.
  scen/.venv/Scripts/modal.exe run forvarld/kropp/forskning/kimodo/tjanst_kimodo.py::utforska
Textkodaren (meta-llama/Meta-Llama-3-8B-Instruct via LLM2Vec) är gated: HF-kontot i Modal-hemligheten 'huggingface' måste ha åtkomst."""
import modal
app = modal.App('hagen-kimodo')
VOL = modal.Volume.from_name('hagen-kimodo', create_if_missing=True)
img = (modal.Image.from_registry('nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04', add_python='3.11')
       .apt_install('git', 'cmake', 'build-essential', 'libgl1', 'libglib2.0-0')
       .pip_install('torch==2.5.1', index_url='https://download.pytorch.org/whl/cu124')
       .pip_install('git+https://github.com/nv-tlabs/kimodo.git', 'huggingface_hub>=0.25')
       .env({'HF_HOME': '/vol/hf'}))

@app.function(image=img, volumes={'/vol': VOL}, secrets=[modal.Secret.from_name('huggingface')], timeout=1200)
def utforska():
    import os, subprocess, importlib, pkgutil, json
    from huggingface_hub import snapshot_download
    p = snapshot_download('nvidia/Kimodo-SOMA-RP-v1', token=os.environ.get('HF_TOKEN')); VOL.commit()
    import kimodo; rot = os.path.dirname(kimodo.__file__)
    ut = {'vikter': os.listdir(p), 'paket': sorted(m.name for m in pkgutil.walk_packages([rot], 'kimodo.'))[:80],
          'config': open(os.path.join(p, 'config.yaml')).read()[:3000]}
    ut['hjalp'] = subprocess.run(['python', '-m', 'kimodo.scripts.generate', '--help'], capture_output=True, text=True).stdout[-4000:]
    for sok in ('LLM2Vec', 'Meta-Llama', 'TEXT_ENCODER', 'somaskel77', 'end_effector', 'EndEffector', 'class .*Constraint'):
        ut['grep_' + sok] = subprocess.run(['grep', '-rnE', sok, rot, '--include=*.py'], capture_output=True, text=True).stdout[:1500]
    return ut

@app.local_entrypoint()
def main():
    import json; r = utforska.remote(); open('utforska.json', 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1)); print('ok', list(r))


@app.function(image=img, volumes={'/vol': VOL}, secrets=[modal.Secret.from_name('huggingface')], gpu=['A10G', 'L40S', 'L4', 'A100-40GB'], timeout=2400)
def generera(jobb):
    """jobb: lista av dict(namn, prompt, sekunder, seed, constraints=None, cfg=None). Ger {namn: {'npz': bytes, 'bvh': bytes, 's': tid}}."""
    import os, subprocess, time, json, tempfile
    ut = {}
    for j in jobb:
        d = tempfile.mkdtemp(); stam = os.path.join(d, j['namn']); arg = ['python', '-m', 'kimodo.scripts.generate', j['prompt'], '--model', 'Kimodo-SOMA-RP-v1',
                                                                          '--duration', str(j['sekunder']), '--seed', str(j.get('seed', 0)), '--output', stam, '--bvh']
        if j.get('constraints'):
            cf = os.path.join(d, 'constraints.json'); open(cf, 'w').write(json.dumps(j['constraints'])); arg += ['--constraints', cf]
        if j.get('cfg'): arg += ['--cfg_type', 'separated', '--cfg_weight'] + [str(x) for x in j['cfg']]
        t0 = time.time(); r = subprocess.run(arg, capture_output=True, text=True); s = round(time.time() - t0, 1)
        if r.returncode: ut[j['namn']] = {'fel': (r.stdout + r.stderr)[-3000:], 's': s}; continue
        ut[j['namn']] = {'npz': open(stam + '.npz', 'rb').read(), 'bvh': open(stam + '.bvh', 'rb').read() if os.path.exists(stam + '.bvh') else b'', 's': s, 'logg': (r.stdout + r.stderr)[-800:]}
    VOL.commit(); return ut


@app.local_entrypoint()
def text():
    import json, sys, pathlib
    jobb = json.loads(pathlib.Path('jobb.json').read_text(encoding='utf-8')); u = pathlib.Path('ut'); u.mkdir(exist_ok=True)
    for n, r in generera.remote(jobb).items():
        if 'fel' in r: print('FEL', n, r['s'], r['fel']); continue
        (u / f'{n}.npz').write_bytes(r['npz']); (u / f'{n}.bvh').write_bytes(r['bvh']); print('OK', n, r['s'], 's')


@app.function(image=img, timeout=600)
def axlar():
    import torch
    from kimodo.skeleton import SOMASkeleton77
    s = SOMASkeleton77(); J = s.nbjoints; I = torch.eye(3).expand(1, J, 3, 3).clone()
    g, p, _ = s.fk(I, torch.zeros(1, 3)); p = p[0]   # modellens lokala rotationer ligger i standard-T-posen: lokal I = T-pose
    n = list(s.bone_order_names); ix = n.index
    return {'namn': n, 'foraldrar': [int(x) for x in s.joint_parents], 'rot': int(s.root_idx),
            'tpose': {k: [round(float(v), 3) for v in p[ix(k)]] for k in ('Hips', 'Head', 'LeftHand', 'RightHand', 'LeftToeBase', 'LeftFoot', 'LeftLeg', 'LeftShin', 'Neck1', 'LeftShoulder', 'LeftArm', 'LeftForeArm')},
            'global_i_tpose_max_avvikelse': float((g[0] - torch.eye(3)).abs().max())}


@app.local_entrypoint()
def visa_axlar():
    import json; r = axlar.remote(); open('soma77.json', 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in r.items() if k != 'foraldrar'}, ensure_ascii=False))


# ---------- 0040b: SMPL-G <-> SOMA77 (soma.py) ----------
#   scen/.venv/Scripts/modal.exe run forvarld/kropp/forskning/kimodo/tjanst_kimodo.py::prov_soma
# soma.py och SMPL-humanoidens MJCF läggs i /root bredvid varandra; soma.py letar efter smpl_humanoid.xml där.
import pathlib as _pl
_HIT = _pl.Path(__file__).resolve().parent
img_soma = (img.pip_install('scipy')
            .add_local_file(str(_HIT / 'soma.py'), '/root/soma.py')
            .add_local_file(str(_HIT.parent / 'ProtoMotions/protomotions/data/assets/mjcf/smpl_humanoid.xml'), '/root/smpl_humanoid.xml'))


@app.function(image=img_soma, cpu=2, timeout=600)
def soma_prov(G, rot, kimodo_npz=None):
    """G (T,24,3,3), rot (T,3) som numpy. Ger SOMA-villkoret, rundresan tillbaka, Kimodos egen FK på villkoret, T-pose-provet,
    och (om kimodo_npz ges som bytes) ett Kimodo-utfall översatt till SMPL-G."""
    import sys, io, numpy as np, torch
    sys.path.insert(0, '/root'); import soma as SO
    from kimodo.skeleton import SOMASkeleton77
    from kimodo.geometry import axis_angle_to_matrix
    sk = SOMASkeleton77(); K = SO.soma()
    G, rot = np.asarray(G, float), np.asarray(rot, float)   # listor in: lokal numpy 2.5 kan skilja från containerns
    o = SO.smpl_till_soma(G, rot); G2, rot2 = SO.soma_till_smpl(o['local_rot_mats'], o['root_positions'], o['s'], o['golv_skift'])
    # villkoret läst som Kimodo läser villkorsfilen: axis-angle -> matris -> skeleton.fk
    Lk = axis_angle_to_matrix(torch.tensor(o['local_joints_rot']).float()); _, pk, _ = sk.fk(Lk, torch.tensor(o['root_positions']).float())
    _, pn = SO.fk_soma(o['local_rot_mats'], o['root_positions'])
    T0 = np.repeat(np.eye(3)[None, None], 24, 1); t0 = SO.smpl_till_soma(T0, np.array([[0., 0., 0.95]]), golv=False)
    g0, p0, _ = sk.fk(torch.tensor(t0['local_rot_mats']).float(), torch.tensor(t0['root_positions']).float())
    icke_lem = [K['ix'][v] for k, v in SO.KARTA.items() if k not in SO.LEMBEN]; lem = [K['ix'][v] for k, v in SO.KARTA.items() if k in SO.LEMBEN]
    ut = dict(villkor={k: o[k] for k in ('local_joints_rot', 'root_positions')}, s=o['s'], golv_skift=o['golv_skift'], G2=G2, rot2=rot2,
              P_soma=pk.numpy().astype(float), fk_kimodo_mot_numpy_m=float(np.abs(pk.numpy() - pn).max()), namn=K['namn'], far=K['far'].tolist(),
              tpose=dict(icke_lem_max_avvikelse_fran_I=float((g0[0, icke_lem] - torch.eye(3)).abs().max()),
                         lem_max_vinkel_grader=float(SO.vinkel(g0[0, lem].numpy().astype(float), np.eye(3)).max()),
                         sula_y=float(SO.sula_soma(p0.numpy().astype(float))[0])),
              A=K['A'], B_grader={j: float(SO.vinkel(b, np.eye(3))) for j, b in K['B'].items() if j in SO.LEMBEN})
    if kimodo_npz:
        d = np.load(io.BytesIO(kimodo_npz)); Gk, rk = SO.soma_till_smpl(d['local_rot_mats'], d['root_positions'])
        ut['kimodo'] = dict(G=Gk, rot=rk, posed=d['posed_joints'].astype(float))
    return ut


def _vinkel3(a, b, c):
    import numpy as np
    u, w = a - b, c - b; return np.degrees(np.arccos(np.clip((u * w).sum(-1) / np.linalg.norm(u, axis=-1) / np.linalg.norm(w, axis=-1), -1, 1)))


def _lutning(u, ax):
    import numpy as np
    return np.degrees(np.arccos(np.clip(u[..., ax] / np.linalg.norm(u, axis=-1), -1, 1)))


@app.local_entrypoint()
def prov_soma():
    """Rundresan SMPL -> SOMA -> SMPL på b-tilltal S3/B, och ut/neutral.npz -> SMPL-G -> mm.npz -> TG.tillbaka.
    Skriver ut/soma_prov.json, ut/streck_soma.png, ut/neutral_mm.npz och ut/neutral_mhr.npz."""
    import sys, json
    import numpy as np
    sys.path.insert(0, str(_HIT.parent / 'mm')); sys.path.insert(0, str(_HIT))
    import tagning as TG, mhr_smpl as M, soma as SO
    t = TG.las('b-tilltal-ravara_n06-hand/kalla_0032.json', 'b-tilltal-ravara_n06-hand/liggare_0032.json', 's3', 'B'); ref = TG.referens(t)
    G, rot = np.asarray(ref['G'], float), np.asarray(ref['rot'], float)
    r = soma_prov.remote(G.tolist(), rot.tolist(), (_HIT / 'ut/neutral.npz').read_bytes())
    v = SO.vinkel(G, r['G2']); P1 = M.fk_smpl(G, rot); P2 = M.fk_smpl(r['G2'], r['rot2']); d = np.linalg.norm(P1 - P2, axis=-1) * 100
    rap = dict(rutor=len(G), s=r['s'], golv_skift=r['golv_skift'], A=r['A'].tolist(), B_grader={k: round(x, 1) for k, x in r['B_grader'].items()},
               tpose=r['tpose'], fk_kimodo_mot_numpy_m=r['fk_kimodo_mot_numpy_m'],
               rundresa={n: dict(vinkel_max=round(float(v[:, i].max()), 4), vinkel_median=round(float(np.median(v[:, i])), 4), pos_max_cm=round(float(d[:, i].max()), 3)) for i, n in enumerate(M.SN)})
    ki = {n: i for i, n in enumerate(r['namn'])}; sx = M.SN.index; p = r['P_soma']
    rap['sula_soma_y_p2_min'] = [round(float(np.percentile(p[:, [ki[k] for k in ('LeftToeEnd', 'RightToeEnd')], 1].min(1), 2)), 3), round(float(p[:, :, 1].min()), 3)]
    # trohet: SOMA-led mot SMPL-kropp relativt höftmitten (Kimodo-värld, SMPL skalad med s); skillnad = proportioner, inte pose
    A = r['A']; Pk = np.einsum('ab,fjb->fja', A.T, P1) * r['s']
    mS = (p[:, ki['LeftLeg']] + p[:, ki['RightLeg']]) / 2; mM = (Pk[:, sx('L_Hip')] + Pk[:, sx('R_Hip')]) / 2
    rap['proportion_cm'] = {f'{a}->{b}': round(float(np.median(np.linalg.norm((p[:, ki[b]] - mS) - (Pk[:, sx(a)] - mM), axis=-1))) * 100, 1)
                            for a, b in [('L_Wrist', 'LeftHand'), ('L_Elbow', 'LeftForeArm'), ('L_Ankle', 'LeftFoot'), ('L_Knee', 'LeftShin'), ('Head', 'Head')]}
    # Kimodo-utfallet -> SMPL-G -> mm.npz -> TG.tillbaka
    k = r['kimodo']; mm = _HIT / 'ut/neutral_mm.npz'; SO.skriv_mm(k['G'], k['rot'], mm); ut = _HIT / 'ut/neutral_mhr.npz'; TG.tillbaka(t, ref, str(mm), str(ut))
    Ps = M.fk_smpl(k['G'], k['rot']); q = k['posed']; z = np.load(ut); mp = z['pose'][:, :, :3].astype(float); mi = M.ix; jmf = {}
    for sida, (a, b, c), (e, f, g), (x, y, w) in [('V', ('L_Hip', 'L_Knee', 'L_Ankle'), ('LeftLeg', 'LeftShin', 'LeftFoot'), ('l_upleg', 'l_lowleg', 'l_foot')),
                                                  ('H', ('R_Hip', 'R_Knee', 'R_Ankle'), ('RightLeg', 'RightShin', 'RightFoot'), ('r_upleg', 'r_lowleg', 'r_foot'))]:
        ks, kk, km = _vinkel3(Ps[:, sx(a)], Ps[:, sx(b)], Ps[:, sx(c)]), _vinkel3(q[:, ki[e]], q[:, ki[f]], q[:, ki[g]]), _vinkel3(mp[:, mi(x)], mp[:, mi(y)], mp[:, mi(w)])
        n = min(len(km) - 1, len(kk))
        jmf['knä_' + sida] = dict(kimodo_min=round(float(kk.min()), 1), kimodo_median=round(float(np.median(kk)), 1), smpl_mot_kimodo_max_fel=round(float(np.abs(ks - kk).max()), 3),
                                  mhr_median=round(float(np.median(km[1:n + 1])), 1), mhr_mot_kimodo_max_fel=round(float(np.abs(km[1:n + 1] - kk[:n]).max()), 2))
    jmf['bål_lutning'] = dict(kimodo_median=round(float(np.median(_lutning(q[:, ki['Neck1']] - q[:, ki['Hips']], 1))), 1), smpl_median=round(float(np.median(_lutning(Ps[:, sx('Neck')] - Ps[:, sx('Pelvis')], 2))), 1))
    jmf['nacke_huvud_mot_bål'] = dict(kimodo=round(float(np.median(180 - _vinkel3(q[:, ki['Hips']], q[:, ki['Neck1']], q[:, ki['HeadEnd']]))), 1),
                                    smpl=round(float(np.median(180 - _vinkel3(Ps[:, sx('Pelvis')], Ps[:, sx('Neck')], Ps[:, sx('Head')]))), 1),
                                    mhr=round(float(np.median(180 - _vinkel3(mp[:, mi('root')], mp[:, mi('c_neck')], mp[:, mi('c_head')]))), 1))
    rap['kimodo_neutral'] = jmf; rap['mm_npz'] = str(mm); rap['mhr_npz'] = str(ut)
    (_HIT / 'ut/soma_prov.json').write_text(json.dumps(rap, ensure_ascii=False, indent=1), encoding='utf-8')
    _streck(Pk, p, M.SP, r['far'], _HIT / 'ut/streck_soma.png'); print(json.dumps(rap, ensure_ascii=False, indent=1))


def _streck(Ps, Pk, far_s, far_k, fil):
    """SMPL (skalad, Kimodo-värld, röd) bredvid SOMA (blå), framifrån och från sidan, sex rutor."""
    import numpy as np
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    rutor = np.linspace(0, len(Ps) - 1, 6).astype(int); fig, ax = plt.subplots(2, 6, figsize=(14, 6))
    for kol, t in enumerate(rutor):
        for rad, (a, namn) in enumerate(((0, 'fram'), (2, 'sida'))):
            x = ax[rad, kol]
            for P, far, c, dx in ((Ps[t], far_s, '#c33', -0.45), (Pk[t], far_k, '#236', 0.45)):
                Q = P - P[0] * np.array([1, 0, 1])
                for j, f in enumerate(far):
                    if f >= 0: x.plot([Q[j, a] + dx, Q[f, a] + dx], [Q[j, 1], Q[f, 1]], '-', c=c, lw=1)
            x.axhline(0, c='#aaa', lw=0.5); x.set_aspect('equal'); x.set_xlim(-1.1, 1.1); x.set_ylim(-0.05, 1.95); x.axis('off')
            if rad == 0: x.set_title(f'ruta {t}', fontsize=8)
            if kol == 0: x.text(-1.1, 1.9, namn + ': röd SMPL, blå SOMA', fontsize=7)
    plt.tight_layout(); fig.savefig(fil, dpi=90)
