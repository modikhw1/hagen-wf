"""FORSKNING (0039), körs i Modal-containern: referens (.npz med G, rot, mål) -> .motion -> MaskedMimic SMPL (AMASS-tränad) i IsaacGym -> kroppar per steg.

  python kor_mm.py <in.npz> <ut.npz> <villkor.json>
villkor.json: {"villkor": [{"kropp": "L_Hand", "tillstand": 0}, ...], "steg": N}   tillstand 0 = position, 1 = båda, 2 = rotation.
in.npz: G (T,24,3,3) globala rotationer i MJCF-ordning, rot (T,3), fps, mal_namn (kroppar vars position skrivs över), mal (T,k,3), mal_vikt (T,k).
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


def main():
    inn, ut, vf = sys.argv[1], sys.argv[2], sys.argv[3]; V = json.loads(Path(vf).read_text()); t0 = time.time()
    d = dict(np.load(inn, allow_pickle=True)); mf = '/tmp/ref.motion'; namn, skift = bygg_motion(d, mf); t_motion = time.time() - t0
    rc = torch.load(CK.parent / 'resolved_configs_inference.pt', map_location='cpu', weights_only=False)
    robot, sim, terr, scene, mlib, env_c, agent_c = rc['robot'], rc['simulator'], rc.get('terrain'), rc['scene_lib'], rc['motion_lib'], rc['env'], rc['agent']
    if sim._target_.split('.')[-3] != 'isaacgym':     # kontrollpunkten tränades i en annan simulator; samma byte som inference_agent.py
        from protomotions.simulator.factory import update_simulator_config_for_test
        print('SIMULATOR', sim._target_, '-> isaacgym'); sim = update_simulator_config_for_test(current_simulator_config=sim, new_simulator='isaacgym', robot_config=robot)
    from protomotions.utils.inference_utils import apply_backward_compatibility_fixes
    apply_backward_compatibility_fixes(robot, sim, env_c)
    sim.num_envs = 1; sim.headless = True; mlib.motion_file = mf
    jm = env_c.masked_mimic_obs.masked_mimic_masking.joint_masking
    jm.masked_mimic_fixed_conditioning = [SimpleNamespace(body_name=v['kropp'], constraint_state=int(v['tillstand'])) for v in V['villkor']]
    jm.masked_mimic_repeat_mask_probability = 1.0; jm.force_max_conditioned_bodies_prob = 0.0; jm.force_small_num_conditioned_bodies_prob = 0.0
    if 'tid' in V: env_c.masked_mimic_obs.masked_mimic_masking.time_sampling.alpha, env_c.masked_mimic_obs.masked_mimic_masking.time_sampling.beta = V['tid']
    from lightning.fabric import Fabric
    fabric = Fabric(devices=1, num_nodes=1, loggers=[], callbacks=[]); fabric.launch()
    from protomotions.utils.component_builder import build_all_components
    c = build_all_components(terrain_config=terr, scene_lib_config=scene, motion_lib_config=mlib, simulator_config=sim, robot_config=robot, device=fabric.device, save_dir=None)
    env = get_class(env_c._target_)(config=env_c, robot_config=robot, device=fabric.device, terrain=c['terrain'], scene_lib=c['scene_lib'], motion_lib=c['motion_lib'], simulator=c['simulator'])
    agent = get_class(agent_c._target_)(config=agent_c, env=env, fabric=fabric, root_dir=CK.parent); agent.setup(); agent.load(str(CK), load_env=False); agent.eval()
    t_upp = time.time() - t0
    n = int(V.get('steg', len(d['G']))); pos, rot, ref = [], [], []
    # Inference must start at the beginning of the supplied motion.  A plain
    # reset samples a random phase (MotionManager.sample_time), so a short clip
    # can reach its end almost immediately and the uncontrolled humanoid falls.
    # This is the same deterministic reset used by MimicEvaluator.
    env.motion_manager.motion_ids[:] = 0
    env.motion_manager.motion_times[:] = 0.0
    obs, _ = env.reset(None, sample_flat=True, disable_motion_resample=True)
    starttid = float(env.motion_manager.motion_times[0].item())
    spawn = env.respawn_root_offset[0].detach().cpu().numpy().copy()
    with torch.no_grad():
        for i in range(n):
            o = agent.obs_dict_to_tensordict(agent.add_agent_info_to_obs(obs)); mo = agent.model(o)
            a = mo['mean_action'] if 'mean_action' in mo else mo['action']
            obs, r, done, term, ex = env.step(a)
            b = env.simulator.get_bodies_state(); pos.append(b.rigid_body_pos[0].cpu().numpy()); rot.append(b.rigid_body_rot[0].cpu().numpy())
            if bool(done[0]) and i < n - 1: print('KLART_TIDIGT', i); break
    t_tot = time.time() - t0
    np.savez(ut, pos=np.array(pos), rot=np.array(rot), namn=np.array(namn), skift=skift,
             tider=np.array([t_motion, t_upp - t_motion, t_tot - t_upp]), dt=float(env.dt),
             starttid=starttid, spawn=spawn)
    print('MM_KLAR', len(pos), 'steg', 'starttid', starttid, 'spawn', spawn.tolist(),
          'tider motion/uppstart/inferens', round(t_motion, 1), round(t_upp - t_motion, 1), round(t_tot - t_upp, 1), 'dt', env.dt)


if __name__ == '__main__': main()
