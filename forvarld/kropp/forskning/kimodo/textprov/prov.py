"""FORSKNING/0040 textprov: känsla, formulering och textvikt i Kimodo-SOMA-RP.
  cd forvarld/kropp/forskning/kimodo/textprov && ../../../../../scen/.venv/Scripts/modal.exe run prov.py
Avbildningen är kopierad ur ../tjanst_kimodo.py (samma volym och hemlighet); egen app så att den filen lämnas orörd.
Modellen laddas en gång per container via Python-API:t; varje variant = 4 prov (num_samples=4) med samma frö,
så att alla varianter delar startbrus. En hel prompt utan punkter (CLI:t skulle dela vid punkt)."""
import modal, json, pathlib
app = modal.App('hagen-kimodo-textprov')
VOL = modal.Volume.from_name('hagen-kimodo', create_if_missing=True)
img = (modal.Image.from_registry('nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04', add_python='3.11')
       .apt_install('git', 'cmake', 'build-essential', 'libgl1', 'libglib2.0-0')
       .pip_install('torch==2.5.1', index_url='https://download.pytorch.org/whl/cu124')
       .pip_install('git+https://github.com/nv-tlabs/kimodo.git', 'huggingface_hub>=0.25')
       .env({'HF_HOME': '/vol/hf'}))

BAS = 'stands behind a shop counter, holding a piece of meat with both hands and showing it to the camera'
KANSLOR = {'neutral': 'A man', 'uttrakad': 'A bored man', 'stolt': 'A proud man', 'nervos': 'A nervous man', 'trott': 'A tired man', 'irriterad': 'An irritated man'}
KROPP = 'then slumps his shoulders, sighs, lets his arms drop slowly and turns his head to look to the side'
TEMPO = 'slowly and lazily'


def varianter():
    v = [dict(namn=f'k_{k}', prompt=f'{s} {BAS}', w=2.0) for k, s in KANSLOR.items()]
    v += [dict(namn='f_kropp', prompt=f'A man {BAS}, {KROPP}', w=2.0),
          dict(namn='f_tempo', prompt=f'A man {BAS} {TEMPO}', w=2.0),
          dict(namn='f_kombo', prompt=f'A bored man {BAS} {TEMPO}, {KROPP}', w=2.0)]
    for f, p in (('kropp', f'A man {BAS}, {KROPP}'), ('kombo', f'A bored man {BAS} {TEMPO}, {KROPP}')):
        v += [dict(namn=f'w_{f}_{w}', prompt=p, w=w) for w in (1.0, 2.5, 4.0, 6.0)]
    return v


@app.function(image=img, volumes={'/vol': VOL}, secrets=[modal.Secret.from_name('huggingface')], gpu=['A10G', 'L40S', 'L4', 'A100-40GB'], timeout=2400)
def generera(jobb):
    import io, time, numpy as np, torch
    from kimodo import load_model
    from kimodo.tools import seed_everything
    t0 = time.time(); model = load_model('Kimodo-SOMA-RP-v1', device='cuda:0', default_family='Kimodo')
    sk = model.skeleton; sk = getattr(sk, 'somaskel77', sk)
    ut = {'_skelett': {'namn': list(sk.bone_order_names), 'foraldrar': [int(x) for x in sk.joint_parents], 'fps': float(model.fps),
                       'gpu': torch.cuda.get_device_name(0), 'laddning_s': round(time.time() - t0, 1)}}
    for j in jobb:
        t1 = time.time(); seed_everything(7)
        delar = j.get('delar') or [[j['prompt'], 3.0]]   # i följd: [[text, sekunder], ...]
        o = model([d[0] for d in delar], [int(d[1] * model.fps) for d in delar], num_denoising_steps=100, multi_prompt=True, num_samples=4,
                  cfg_type='regular', cfg_weight=float(j['w']), post_processing=True, return_numpy=True, progress_bar=lambda x, **k: x)
        b = io.BytesIO(); np.savez_compressed(b, posed_joints=o['posed_joints'].astype(np.float32), global_rot_mats=o['global_rot_mats'].astype(np.float32))
        ut[j['namn']] = {'npz': b.getvalue(), 's': round(time.time() - t1, 1)}
    return ut


@app.local_entrypoint()
def main():
    v = varianter(); u = pathlib.Path('ut'); u.mkdir(exist_ok=True)
    grupper = [v[:9], v[9:]]
    (u / 'varianter.json').write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in generera.map(grupper):
        sk = r.pop('_skelett'); print('container', sk['gpu'], 'laddning', sk['laddning_s'], 's')
        (u / 'skelett.json').write_text(json.dumps(sk, ensure_ascii=False), encoding='utf-8')
        for n, d in r.items(): (u / f'{n}.npz').write_bytes(d['npz']); print('OK', n, d['s'], 's')


SEG1 = 'A man stands behind a shop counter, holding a piece of meat with both hands and showing it to the camera'
SEG2 = 'A bored man slumps his shoulders, sighs, lets his arms drop slowly and turns his head to look to the side'


@app.local_entrypoint()
def extra():
    """Följdprov: två delar i följd (visa 1,5 s, sedan uttråkad 1,5 s) och en kontroll med bara huvudvridning."""
    v = [dict(namn='s_seg', delar=[[SEG1, 1.5], [SEG2, 1.5]], w=2.0), dict(namn='s_seg_w4', delar=[[SEG1, 1.5], [SEG2, 1.5]], w=4.0),
         dict(namn='s_huvud', prompt='A man stands still and turns his head to look to the left side', w=2.0)]
    u = pathlib.Path('ut'); alla = json.loads((u / 'varianter.json').read_text(encoding='utf-8'))
    alla = [a for a in alla if not a['namn'].startswith('s_')] + v
    (u / 'varianter.json').write_text(json.dumps(alla, ensure_ascii=False, indent=1), encoding='utf-8')
    r = generera.remote(v); sk = r.pop('_skelett'); print('container', sk['gpu'], 'laddning', sk['laddning_s'], 's')
    for n, d in r.items(): (u / f'{n}.npz').write_bytes(d['npz']); print('OK', n, d['s'], 's')
