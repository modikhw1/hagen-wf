"""FORSKNING/0040: Kimodo kopplad till originalet. En mening -> flera prov -> MHR-sekvenser som förvärlden renderar.
  cd forvarld/kropp/forskning/kimodo && ../../../../scen/.venv/Scripts/modal.exe run kopplad.py --namn uttr --mening "<svensk mening>" --prompt "<engelsk kroppslig prompt>"
Recept (VILLKOR.md, textprov/RESULTAT.md): 75 rutor, rutorna 0..n-1 används. Helkropp + händer + fötter på rutorna 0-4 (klippet börjar
som originalet), rotens väg (root2d) på alla rutor, inga täta fotvillkor. cfg separated [text, villkor]. Prompten beskriver kropp och tempo
och innehåller ingen punkt (punkt delar prompten). Ut: forvarld/kropp/forskning/mm/ut/mening_km_<namn>_<k>/ (sekvens.npz, mm.npz, logg.json)."""
import json, sys, pathlib
import modal
HIT = pathlib.Path(__file__).resolve().parent; MM = HIT.parent / 'mm'
app = modal.App('hagen-kimodo-kopplad')
VOL = modal.Volume.from_name('hagen-kimodo', create_if_missing=True)
img = (modal.Image.from_registry('nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04', add_python='3.11')
       .apt_install('git', 'cmake', 'build-essential', 'libgl1', 'libglib2.0-0')
       .pip_install('torch==2.5.1', index_url='https://download.pytorch.org/whl/cu124')
       .pip_install('git+https://github.com/nv-tlabs/kimodo.git', 'huggingface_hub>=0.25')
       .env({'HF_HOME': '/vol/hf'})
       .add_local_file(str(HIT / 'soma.py'), '/root/soma.py')
       .add_local_file(str(HIT.parent / 'ProtoMotions/protomotions/data/assets/mjcf/smpl_humanoid.xml'), '/root/smpl_humanoid.xml'))
FORE, TOTAL = 5, 75


@app.function(image=img, volumes={'/vol': VOL}, secrets=[modal.Secret.from_name('huggingface')], gpu=['A10G', 'L40S', 'L4', 'A100-40GB'], timeout=2400)
def kor(G, rot, jobb):
    import io, time, sys, numpy as np, torch
    sys.path.insert(0, '/root'); import soma
    from kimodo import load_model
    from kimodo.tools import seed_everything
    from kimodo.constraints import load_constraints_lst
    t0 = time.time(); model = load_model('Kimodo-SOMA-RP-v1', device='cuda:0', default_family='Kimodo'); ladd = round(time.time() - t0, 1)
    G, rot = np.asarray(G, float), np.asarray(rot, float); n = len(G)
    k = soma.smpl_till_soma(G, rot); aa, rp = k['local_joints_rot'], k['root_positions']
    f = list(range(FORE)); bas = dict(frame_indices=f, local_joints_rot=aa[:FORE].tolist(), root_positions=rp[:FORE].tolist())
    r2 = np.concatenate([rp[:, [0, 2]], np.repeat(rp[-1:, [0, 2]], TOTAL - n, 0)])
    villkor = [dict(type='fullbody', **bas)] + [dict(type=t, **bas) for t in ('left-hand', 'right-hand', 'left-foot', 'right-foot')] + \
              [dict(type='root2d', frame_indices=list(range(TOTAL)), smooth_root_2d=r2.tolist())]
    cl = load_constraints_lst(villkor, model.skeleton, device='cuda:0')
    ut = {'_info': dict(laddning_s=ladd, gpu=torch.cuda.get_device_name(0), s=k['s'], golv=k['golv_skift'])}
    for j in jobb:
        t1 = time.time(); seed_everything(int(j.get('seed', 7)))
        o = model(j['prompt'], TOTAL, num_denoising_steps=100, constraint_lst=cl, cfg_type='separated', cfg_weight=[float(j['w'][0]), float(j['w'][1])],
                  num_samples=int(j['prov']), post_processing=True, return_numpy=True, progress_bar=lambda x, **kw: x)
        L, R = np.asarray(o['local_rot_mats']), np.asarray(o['root_positions'])
        if L.ndim == 4: L, R = L[None], R[None]
        Gs, rs = zip(*[soma.soma_till_smpl(L[i, :n], R[i, :n], s=k['s'], golv_skift=k['golv_skift']) for i in range(len(L))])
        b = io.BytesIO(); np.savez_compressed(b, G=np.stack(Gs).astype(np.float32), rot=np.stack(rs).astype(np.float32), posed_joints=np.asarray(o['posed_joints'], np.float32))
        ut[j['namn']] = {'npz': b.getvalue(), 's': round(time.time() - t1, 1)}
    return ut


def kanon(G, rot):
    """Vrid kring z så att bäckenet vid ruta 0 pekar +x (MJCF framåt) och flytta roten till origo i golvplanet."""
    import numpy as np
    fr = G[0, 0] @ np.array([1., 0., 0.]); a = np.arctan2(fr[1], fr[0]); c, s = np.cos(-a), np.sin(-a)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]]); o = np.array([rot[0, 0], rot[0, 1], 0.])
    return Rz @ G, (rot - o) @ Rz.T, Rz, o


@app.local_entrypoint()
def main(namn: str, mening: str, prompt: str, vikter: str = '4,2;3,2', prov: int = 8, kalla: str = 'b-tilltal-ravara_n06-hand/kalla_0032.json',
         liggare: str = 'b-tilltal-ravara_n06-hand/liggare_0032.json', scen: str = 's3', person: str = 'B'):
    import io, numpy as np
    sys.path.insert(0, str(MM)); sys.path.insert(0, str(HIT)); import tagning as TG, soma
    t = TG.las(kalla, liggare, scen, person); ref = TG.referens(t); n = len(ref['G'])
    Gc, rc, Rz, o = kanon(ref['G'], ref['rot'])
    jobb = [dict(namn=f'w{w.replace(",", "_")}', prompt=prompt, w=[float(x) for x in w.split(',')], prov=prov) for w in vikter.split(';')]
    r = kor.remote(Gc.tolist(), rc.tolist(), jobb); info = r.pop('_info'); print('container', info)
    alla = []
    for jn, d in r.items():
        z = np.load(io.BytesIO(d['npz'])); print('jobb', jn, d['s'], 's', z['G'].shape)
        for i in range(len(z['G'])):
            G = np.einsum('ab,fjbc->fjac', Rz.T, z['G'][i].astype(float)); rt = z['rot'][i].astype(float) @ Rz + o
            nm = f'km_{namn}_{jn}_{i}'; ut = MM / 'ut' / f'mening_{nm}'; ut.mkdir(parents=True, exist_ok=True)
            soma.skriv_mm(G[1:n], rt[1:n], ut / 'mm.npz'); TG.tillbaka(t, ref, ut / 'mm.npz', ut / 'sekvens.npz')
            (ut / 'logg.json').write_text(json.dumps(dict(mening=mening, prompt=prompt, vikter=jobb[[j['namn'] for j in jobb].index(jn)]['w'], prov=i, modell='Kimodo-SOMA-RP-v1',
                                                          licens='NVIDIA Open Model License', tagning=t['namn'], kalla=t['kalla'], liggare=t['liggare'], scen=t['scen'],
                                                          person=t['person'], antaganden=ref['beslut'], villkor=f'helkropp+händer+fötter rutor 0-{FORE - 1}, root2d alla'),
                                                     ensure_ascii=False, indent=1), encoding='utf-8')
            alla.append(nm)
    (HIT / 'ut').mkdir(exist_ok=True); (HIT / 'ut' / f'kopplad_{namn}.json').write_text(json.dumps(alla, ensure_ascii=False), encoding='utf-8')
    print('KANDIDATER', ' '.join(alla))
