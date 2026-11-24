"""0040, körs i Modal-containern: Kimodo-SOMA-RP-v1.1 (NVIDIA Open Model License) med villkor ur referensen, utan textkodare
(tom text = nollvektor, som Kimodo själv gör för tom text; textvarianten kräver gated Llama-3 och körs inte här).

  python kor_kimodo.py <in.npz> <ut.npz> <inst.json>
in.npz: lok (T,30,3,3) lokala rotationer på somaskel30 i Kimodos värld, rot (T,3), mal (T,3) vänster hands mål, mal_vikt (T,), fot_alla (bool)
inst.json: {"varianter": {"namn": {"text": "", "efterbehandling": true, "nyckelbilder_steg": 3, "fotter": true, "hand_steg": 2, "rubrik_fri": false}}, "steg": 50, "frön": [0]}
"""
import json, sys, time
from pathlib import Path
import numpy as np, torch
t0 = time.time()
from kimodo import load_model
from kimodo.skeleton.definitions import SOMASkeleton30
from kimodo.constraints import FullBodyConstraintSet, EndEffectorConstraintSet
from kimodo.motion_rep.feature_utils import compute_heading_angle


class Nolltext:
    """Ersätter LLM2Vec-kodaren: tom text ger nollvektor och längd 0, precis som Kimodo hanterar en tom prompt."""
    def __call__(self, texts):
        return torch.zeros(len(texts), 1, 4096), [0] * len(texts)
    def to(self, *a, **k): return self
    def eval(self): return self


def main():
    inn, ut, inst = sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())
    d = dict(np.load(inn)); dev = 'cuda'
    model = load_model('Kimodo-SOMA-RP-v1.1', device=dev, text_encoder=Nolltext()); t_ladda = time.time() - t0
    sk = model.skeleton; sk30 = SOMASkeleton30().to(dev) if sk.name != 'somaskel30' else sk
    lok = torch.tensor(d['lok'], dtype=torch.float32, device=dev); rot = torch.tensor(d['rot'], dtype=torch.float32, device=dev); n = len(lok)
    lokm = sk30.to_SOMASkeleton77(lok) if sk.name == 'somaskel77' else lok
    gR, gP, _ = sk.fk(lokm, rot)
    # vänster hand: målet = originalets högra hand; handens globala rotation = den högra speglad i kroppens mittplan (vilan är symmetrisk i x)
    jl = sk.bone_index['LeftHand']; jr = sk.bone_index['RightHand']; Hx = torch.diag(torch.tensor([-1., 1., 1.], device=dev))
    hl, hr = sk.bone_index['LeftLeg'], sk.bone_index['RightLeg']
    w = torch.tensor(d['mal_vikt'], device=dev); mal = torch.tensor(d['mal'], dtype=torch.float32, device=dev)
    res = {}
    for namn, v in inst['varianter'].items():
        tv = time.time(); cons = []
        idx_h = torch.nonzero(w >= 0.999).squeeze(-1)[::v.get('hand_steg', 2)]
        if len(idx_h):
            P2, R2 = gP[idx_h].clone(), gR[idx_h].clone()
            for k, f in enumerate(idx_h.tolist()):
                nv = gP[f, hl] - gP[f, hr]; nv = nv / nv.norm(); Hm = torch.eye(3, device=dev) - 2 * torch.outer(nv, nv)
                Rl = Hm @ gR[f, jr] @ Hx; d0 = P2[k] - P2[k, jl]           # håll handens kedja stel kring handleden
                for j in [i for i, nm in enumerate(sk.bone_order_names) if nm.startswith('LeftHand')]:
                    P2[k, j] = mal[f] + Rl @ (gR[f, jl].T @ d0[j]); R2[k, j] = Rl @ gR[f, jl].T @ gR[f, j]
            cons.append(EndEffectorConstraintSet(sk, idx_h, P2, R2, None, joint_names=['LeftHand']))
        if v.get('fotter', True):
            idx_f = torch.arange(0, n, v.get('fot_steg', 2), device=dev)
            cons.append(EndEffectorConstraintSet(sk, idx_f, gP[idx_f], gR[idx_f], None, joint_names=['LeftFoot', 'RightFoot']))
        ks = v.get('nyckelbilder_steg', 0)
        if ks:
            idx_k = torch.nonzero(w[::1] <= 0.0).squeeze(-1)[::ks]
            if len(idx_k): cons.append(FullBodyConstraintSet(sk, idx_k, gP[idx_k], gR[idx_k], None))
        rub = compute_heading_angle(gP[:1], sk)
        utd = {}
        for fro in inst.get('frön', [0]):
            torch.manual_seed(fro)
            o = model(v.get('text', ''), n, inst.get('steg', 50), constraint_lst=cons, first_heading_angle=rub, post_processing=v.get('efterbehandling', True),
                      return_numpy=True, progress_bar=lambda x: x)
            l77 = torch.tensor(o['local_rot_mats'], device=dev).reshape(n, -1, 3, 3)
            l30 = sk30.from_SOMASkeleton77(l77) if l77.shape[1] == 77 else l77
            utd[fro] = dict(lok=l30.cpu().numpy(), rot=np.asarray(o['root_positions']).reshape(n, 3), kontakt=np.asarray(o['foot_contacts']).reshape(n, -1))
        res[namn] = dict(utd=utd, s=round(time.time() - tv, 2), villkor=[type(c).__name__ for c in cons])
        print('VARIANT', namn, 'villkor', res[namn]['villkor'], 'sekunder', res[namn]['s'], flush=True)
    pak = {}
    for namn, r in res.items():
        for fro, u in r['utd'].items():
            for k, x in u.items(): pak[f'{namn}__{fro}__{k}'] = x
        pak[f'{namn}__sekunder'] = np.array(r['s'])
    pak['ladda_s'] = np.array(t_ladda); np.savez(ut, **pak); print('KIMODO_KLAR', round(time.time() - t0, 1), 's; laddning', round(t_ladda, 1))


if __name__ == '__main__': main()
