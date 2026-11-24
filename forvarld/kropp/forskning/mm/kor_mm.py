"""FORSKNING (0039), körs i Modal-containern: referens -> MaskedMimic -> kroppar.

CLI: python kor_mm.py <in.npz> <ut.npz> <villkor.json>
Modulen delas också av arbetare.py. MMKornare håller simulator och policy laddade;
byt_motion skapar bara om MotionLib och MotionManager inför nästa reset.
"""
import sys, json, time
from protomotions.utils.simulator_imports import import_simulator_before_torch
import_simulator_before_torch('isaacgym')
import numpy as np, torch
from types import SimpleNamespace
from pathlib import Path
from protomotions.components.pose_lib import (extract_kinematic_info, fk_from_transforms_with_velocities, extract_qpos_from_transforms,
                                              compute_joint_rot_mats_from_global_mats, compute_angular_velocity as cav)
from protomotions.utils.rotations import matrix_to_quaternion
from protomotions.utils.hydra_replacement import get_class

PM = Path('/opt/protomotions'); CK = PM / 'data/pretrained_models/masked_mimic/smpl/last.ckpt'
EXEMPEL = Path('/opt/mm/smpl_humanoid_sit_armchair.motion')
sys.path.insert(0, str(PM / 'data/scripts'))


def bygg_motion(d, ut):
    from contact_detection import compute_contact_labels_from_pos_and_vel
    ki = extract_kinematic_info(str(PM / 'protomotions/data/assets/mjcf/smpl_humanoid.xml'))
    G = torch.tensor(d['G'], dtype=torch.float32); rot = torch.tensor(d['rot'], dtype=torch.float32); fps = float(d['fps'])
    lok = compute_joint_rot_mats_from_global_mats(kinematic_info=ki, global_rot_mats=G)
    m = fk_from_transforms_with_velocities(kinematic_info=ki, root_pos=rot, joint_rot_mats=lok, fps=fps, compute_velocities=True)
    m.local_rigid_body_rot = matrix_to_quaternion(lok, w_last=True)
    q = extract_qpos_from_transforms(kinematic_info=ki, root_pos=rot, joint_rot_mats=lok, multi_dof_decomposition_method='exp_map'); m.dof_pos = q[:, 7:]
    m.dof_vel = cav(batched_robot_rot_mats=lok[:, 1:], fps=fps).reshape(len(G), -1)
    fore = m.rigid_body_pos[:, 0].clone(); m.fix_height(height_offset=0.015); skift = (m.rigid_body_pos[:, 0] - fore)[0]
    namn = list(ki.body_names) if hasattr(ki, 'body_names') else None
    if 'mal' in d and len(d['mal_namn']):
        for k, bn in enumerate(d['mal_namn']):
            j = namn.index(str(bn)); w = torch.tensor(d['mal_vikt'][:, k], dtype=torch.float32)[:, None]
            m.rigid_body_pos[:, j] = (1 - w) * m.rigid_body_pos[:, j] + w * (torch.tensor(d['mal'][:, k], dtype=torch.float32) + skift)
    m.rigid_body_contacts = compute_contact_labels_from_pos_and_vel(positions=m.rigid_body_pos, velocity=m.rigid_body_vel, vel_thres=0.15, height_thresh=0.1).to(torch.bool)
    torch.save(m.to_dict(), ut); return namn, skift.numpy()


def forbered(inn, V, mf='/tmp/ref.motion'):
    """Läs uppdraget och bygg dess lilla .motion-fil utan att röra simulatorn."""
    t0 = time.time(); diag = str(V.get('diag', 'officiell')).lower()
    tillatna = {'officiell', 'noll', 'privilegierad', 'hall', 'exempel'}
    if diag not in tillatna: raise ValueError('okant diag %r; valj %s' % (diag, sorted(tillatna)))
    d = dict(np.load(inn, allow_pickle=True))
    if diag == 'exempel':
        if not EXEMPEL.exists(): raise FileNotFoundError('SMPL-exempel saknas: %s' % EXEMPEL)
        ki = extract_kinematic_info(str(PM / 'protomotions/data/assets/mjcf/smpl_humanoid.xml'))
        namn = list(ki.body_names); skift = np.zeros(3, dtype=np.float32); mf = str(EXEMPEL)
    else:
        namn, skift = bygg_motion(d, mf)
    return d, diag, str(mf), namn, skift, time.time() - t0


def logga_normalisering(agent):
    from protomotions.agents.utils.normalization import RunningMeanStd
    antal = laddade = 0
    for mod_namn, mod in agent.model.named_modules():
        if isinstance(mod, RunningMeanStd):
            antal += 1; mean = mod.mean.detach().float(); var = mod.var.detach().float()
            ar_laddad = bool(mean.abs().max() > 1e-7 or (var - 1).abs().max() > 1e-7); laddade += int(ar_laddad)
            count = float(mod.count.item()) if hasattr(mod, 'count') else float('nan')
            print('NORM', mod_namn, 'laddad', ar_laddad, 'mean_abs/max', float(mean.abs().mean()), float(mean.abs().max()),
                  'var_mean/min/max', float(var.mean()), float(var.min()), float(var.max()), 'count', count)
    print('NORM_SUMMA', laddade, '/', antal, 'avviker_från_noll_ett')


def modellhandling(model_out):
    return model_out['mean_action'] if 'mean_action' in model_out else model_out['action']


class MMKornare:
    """Långlivad simulator och policy; MotionLib kan bytas mellan körningar."""
    def __init__(self, motion_file, V=None):
        # A10/L4 har tensor cores; policyn är tränad i float32 och TF32 håller
        # numeriken nära float32 men kortar de täta matmul-operationerna.
        torch.set_float32_matmul_precision('high')
        torch.backends.cuda.matmul.allow_tf32 = True
        rc = torch.load(CK.parent / 'resolved_configs_inference.pt', map_location='cpu', weights_only=False)
        self.robot, self.sim, self.terr, self.scene = rc['robot'], rc['simulator'], rc.get('terrain'), rc['scene_lib']
        self.mlib_c, self.env_c, self.agent_c = rc['motion_lib'], rc['env'], rc['agent']
        if self.sim._target_.split('.')[-3] != 'isaacgym':
            from protomotions.simulator.factory import update_simulator_config_for_test
            print('SIMULATOR', self.sim._target_, '-> isaacgym')
            self.sim = update_simulator_config_for_test(current_simulator_config=self.sim, new_simulator='isaacgym', robot_config=self.robot)
        from protomotions.utils.inference_utils import apply_backward_compatibility_fixes
        apply_backward_compatibility_fixes(self.robot, self.sim, self.env_c)
        self.sim.num_envs = 1; self.sim.headless = True; self.mlib_c.motion_file = str(motion_file)
        self.satt_villkor(V or {'villkor': []})
        from lightning.fabric import Fabric
        from protomotions.utils.fabric_config import FabricConfig
        self.fabric = Fabric(**FabricConfig(devices=1, num_nodes=1, loggers=[], callbacks=[]).to_dict()); self.fabric.launch()
        from protomotions.utils.component_builder import build_all_components
        save_dir = getattr(self.env_c, 'save_dir', None)
        c = build_all_components(terrain_config=self.terr, scene_lib_config=self.scene, motion_lib_config=self.mlib_c,
                                 simulator_config=self.sim, robot_config=self.robot, device=self.fabric.device, save_dir=save_dir)
        self.env = get_class(self.env_c._target_)(config=self.env_c, robot_config=self.robot, device=self.fabric.device,
                                                 terrain=c['terrain'], scene_lib=c['scene_lib'], motion_lib=c['motion_lib'], simulator=c['simulator'])
        self.agent = get_class(self.agent_c._target_)(config=self.agent_c, env=self.env, fabric=self.fabric, root_dir=CK.parent)
        self.agent.setup(); self.agent.load(str(CK), load_env=False); self.agent.eval()
        self.motion_file = str(motion_file)
        self.uppdrag = 0

    def satt_villkor(self, V):
        jm = self.env_c.masked_mimic_obs.masked_mimic_masking.joint_masking
        jm.masked_mimic_fixed_conditioning = [SimpleNamespace(body_name=v['kropp'], constraint_state=int(v['tillstand'])) for v in V.get('villkor', [])]
        jm.masked_mimic_repeat_mask_probability = float(V.get('upprepa_mask', 0.0))
        ts = self.env_c.masked_mimic_obs.masked_mimic_masking.time_sampling
        ts.alpha, ts.beta = V.get('tid', [2, 60])

    def byt_motion(self, motion_file):
        """Byt bara referensbiblioteket och dess lätta manager; simulatorn består."""
        if str(motion_file) == self.motion_file:
            return
        from protomotions.utils.component_builder import build_motion_lib_from_config
        self.mlib_c.motion_file = str(motion_file)
        ny = build_motion_lib_from_config(self.mlib_c, self.fabric.device)
        if ny.num_motions() > 0 and self.env.config.ref_contact_smooth_window > 0:
            ny.smooth_contacts(self.env.config.ref_contact_smooth_window)
        self.env.motion_lib = ny
        self.env.create_motion_manager()
        self.agent.motion_lib = ny
        self.agent.motion_manager = self.env.motion_manager
        self.motion_file = str(motion_file)

    def kor_forberedd(self, d, diag, mf, namn, skift, ut, V, t0, t_motion):
        self.satt_villkor(V); self.byt_motion(mf)
        # En långlivad process får annars en annan mask-/målsekvens beroende på
        # tidigare uppdrag. Samma förval i CLI och arbetare gör jämförelser rena.
        fro = int(V.get('fro', 0)); np.random.seed(fro); torch.manual_seed(fro); torch.cuda.manual_seed_all(fro)
        cb = self.env.masked_mimic_obs_cb
        cb.masked_mimic_target_poses = None; cb.historical_pose_obs = None; cb._initialized = False; cb.envs_requiring_reset = None
        cb.masked_mimic_target_bodies_masks.zero_(); cb.masked_mimic_target_poses_masks.zero_(); cb.target_times.zero_()
        # BaseSimulator.reset_envs återställer pose men inte actions, och
        # HumanoidObs.reset_hist_ref återställer inte actionhistoriken.
        self.env.simulator._common_actions.zero_(); self.env.simulator._previous_actions.zero_()
        action_hist = self.env.self_obs_cb.previous_actions_hist_buf
        if action_hist is not None: action_hist.data.zero_()
        self.env.self_obs_cb._initialized = False
        if self.env.config.mimic_obs.enabled:
            self.env.mimic_obs_cb._initialized = False
            self.env.mimic_obs_cb.mimic_target_poses = None
        if hasattr(self.agent, 'vae_noise'): self.agent.vae_noise.zero_()
        t_upp = time.time() - t0; logga_normalisering(self.agent)
        n = int(V.get('steg', len(d['G']))); pos, rot = [], []
        self.env.motion_manager.motion_ids[:] = 0; self.env.motion_manager.motion_times[:] = 0.0
        obs, _ = self.env.reset(None, sample_flat=True, disable_motion_resample=True)
        starttid = float(self.env.motion_manager.motion_times[0].item())
        spawn = self.env.respawn_root_offset[0].detach().cpu().numpy().copy()
        print('BRUS', V.get('brus', 'noll'), float(self.agent.vae_noise.abs().mean()) if hasattr(self.agent, 'vae_noise') else None)
        obs = self.agent.add_agent_info_to_obs(obs); obs_td = self.agent.obs_dict_to_tensordict(obs)
        hall = None
        if diag == 'hall':
            dof = self.env.simulator.get_dof_state().dof_pos
            hall = ((dof - self.env.simulator._common_pd_action_offset) / self.env.simulator._common_pd_action_scale).clamp(-1.0, 1.0)
        print('DIAG_LAGE', diag, 'motion', mf, 'steg', n, 'dt', self.env.dt, 'control', str(self.robot.control.control_type),
              'action_scale', self.robot.control.action_scale, 'pd_offset_minmax', float(self.env.simulator._common_pd_action_offset.min()),
              float(self.env.simulator._common_pd_action_offset.max()), 'pd_scale_minmax', float(self.env.simulator._common_pd_action_scale.min()),
              float(self.env.simulator._common_pd_action_scale.max()))
        b0 = self.env.simulator.get_bodies_state(); print('ROTHOJD', 0, float(b0.rigid_body_pos[0, 0, 2]))
        with torch.no_grad():
            for i in range(n):
                mo = self.agent.model(obs_td); policy_a = modellhandling(mo)
                if i == 0: print('MODELL_NYCKLAR', sorted(str(k) for k in mo.keys()))
                if i in (0, 1, 5, 30) and 'masked_mimic_target_bodies_masks' in obs_td.keys():
                    mk = 'masked_mimic_target_bodies_masks'; print('MASK', i, 'aktiva', int(obs_td[mk][0].sum()), 'av', obs_td[mk][0].numel(), 'sista steget', obs_td[mk][0][-22:].int().tolist())
                if diag == 'noll': a = torch.zeros_like(policy_a)
                elif diag == 'privilegierad': a = mo['privileged_action']
                elif diag == 'hall': a = hall
                else: a = policy_a
                if V.get('detaljlogg') and i < 10:
                    print('HANDLING', i, 'norm', float(torch.linalg.vector_norm(a[0])), 'minmax', float(a[0].min()),
                          float(a[0].max()), 'policy_norm', float(torch.linalg.vector_norm(policy_a[0])))
                obs, r, done, term, ex = self.env.step(a)
                obs = self.agent.add_agent_info_to_obs(obs); obs_td = self.agent.obs_dict_to_tensordict(obs)
                b = self.env.simulator.get_bodies_state(); pos.append(b.rigid_body_pos[0].clone()); rot.append(b.rigid_body_rot[0].clone())
                # GPU->CPU-synkronisering varje ruta kostar flera sekunder per klipp.
                # Kontroll var tionde ruta räcker för diagnosen; godkända klipp når
                # ändå aldrig done före sitt sista referenssteg.
                if (i + 1) % 10 == 0:
                    print('ROTHOJD', i + 1, float(b.rigid_body_pos[0, 0, 2]))
                    if bool(done[0]) and i < n - 1: print('KLART_TIDIGT', i); break
        t_tot = time.time() - t0
        pos_np = torch.stack(pos).cpu().numpy(); rot_np = torch.stack(rot).cpu().numpy()
        np.savez(ut, pos=pos_np, rot=rot_np, namn=np.array(namn), skift=skift,
                 tider=np.array([t_motion, t_upp - t_motion, t_tot - t_upp]), dt=float(self.env.dt),
                 starttid=starttid, spawn=spawn, diag=np.array(diag))
        print('MM_KLAR', len(pos), 'steg', 'diag', diag, 'starttid', starttid, 'spawn', spawn.tolist(),
              'tider motion/uppstart/inferens', round(t_motion, 1), round(t_upp - t_motion, 1), round(t_tot - t_upp, 1), 'dt', self.env.dt)

    def kor(self, inn, ut, V):
        self.uppdrag += 1
        t0 = time.time(); data = forbered(inn, V, '/tmp/ref_%d.motion' % (self.uppdrag % 2))
        self.kor_forberedd(*data[:5], ut, V, t0, data[5])


def main():
    inn, ut, vf = sys.argv[1], sys.argv[2], sys.argv[3]; V = json.loads(Path(vf).read_text()); t0 = time.time()
    data = forbered(inn, V); kornare = MMKornare(data[2], V)
    kornare.kor_forberedd(*data[:5], ut, V, t0, data[5])


if __name__ == '__main__': main()
