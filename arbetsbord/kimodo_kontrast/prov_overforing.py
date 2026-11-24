"""Fas 3: Kontrastprov för Kimodo-SOMA-RP (Commit eller Kill).

Kör 3 skarpa överföringstest på Modal (`hagen-kimodo`, 1 cachad modelladdning):
  1. Fall 1 (Hörn + ny arbetsbänk/waypoint): ~85° kurva runt hörn på riktigt 3.63 s-segment (guacamole s4 B).
  2. Fall 2 (Vänster hand +15 cm, noll spegling): glest LeftHand-villkor +15 cm högre över disk utan spegling (gelato s1 A).
  3. Fall 3 (Känslokontrast + SDEdit s=0.55 vs brus s=1.0): ändra energi/attityd med bibehållen taltajming (guacamole s4 B).

Körning:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\modal.exe run arbetsbord/kimodo_kontrast/prov_overforing.py
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import pickle
import sys
import time
from typing import Any

import modal
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
IS_LOCAL = len(HIT.parents) > 1 and (HIT.parents[1] / "forvarld").exists()
ROT = HIT.parents[1] if IS_LOCAL else HIT
KIMODO_DIR = ROT / "forvarld" / "kropp" / "forskning" / "kimodo"
MM_DIR = ROT / "forvarld" / "kropp" / "forskning" / "mm"
UT_DIR = HIT / "ut"

app = modal.App("hagen-kimodo-kontrast")
VOL = modal.Volume.from_name("hagen-kimodo", create_if_missing=True)
img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("git", "cmake", "build-essential", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.5.1", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("git+https://github.com/nv-tlabs/kimodo.git", "huggingface_hub>=0.25", "scipy")
    .env({"HF_HOME": "/vol/hf"})
)
if IS_LOCAL:
    img = img.add_local_file(str(KIMODO_DIR / "soma.py"), "/root/soma.py").add_local_file(
        str(MM_DIR.parent / "ProtoMotions/protomotions/data/assets/mjcf/smpl_humanoid.xml"),
        "/root/smpl_humanoid.xml",
    )

# Modal ungefärlig GPU-pris per sekund (USD/s, standard serverless prissättning)
GPU_USD_PER_SEC = {
    "NVIDIA A10G": 1.10 / 3600.0,
    "NVIDIA L4": 0.80 / 3600.0,
    "NVIDIA L40S": 1.95 / 3600.0,
    "NVIDIA A100-SXM4-40GB": 2.10 / 3600.0,
    "NVIDIA A100-PCIE-40GB": 2.10 / 3600.0,
}

BEN1_LEDER = [
    "c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head",
    "huvud_upp", "nasa_mal",
    "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
    "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    "l_upleg", "l_lowleg", "l_foot", "l_ball",
    "r_upleg", "r_lowleg", "r_foot", "r_ball",
]


def kanon(G: np.ndarray, rot: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Vrid kring Z så bäckenet vid ruta 0 pekar +x och flytta roten till origo i golvplanet."""
    fr = G[0, 0] @ np.array([1.0, 0.0, 0.0])
    a = np.arctan2(fr[1], fr[0])
    c, s = np.cos(-a), np.sin(-a)
    Rz = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    o = np.array([rot[0, 0], rot[0, 1], 0.0])
    return Rz @ G, (rot - o) @ Rz.T, Rz, o


@app.function(
    image=img,
    volumes={"/vol": VOL},
    secrets=[modal.Secret.from_name("huggingface")],
    gpu=["A10G", "L40S", "L4", "A100-40GB"],
    timeout=2400,
)
def kor_kontrast_modal(indata: dict[str, Any]) -> dict[str, Any]:
    """Kör alla 3 fall i en enda GPU-session med cachad Kimodo-SOMA-RP-v1."""
    import inspect
    import sys
    import time
    import numpy as np
    import torch

    sys.path.insert(0, "/root")
    import soma
    from scipy.spatial.transform import Rotation as Ro
    from kimodo import load_model
    from kimodo.constraints import load_constraints_lst
    from kimodo.geometry import axis_angle_to_matrix, matrix_to_axis_angle
    from kimodo.tools import seed_everything

    t_load0 = time.time()
    model = load_model("Kimodo-SOMA-RP-v1", device="cuda:0", default_family="Kimodo")
    load_s = round(time.time() - t_load0, 2)
    gpu_name = torch.cuda.get_device_name(0)

    sk77 = getattr(model.skeleton, "somaskel77", model.skeleton)
    bone_names = list(sk77.bone_order_names)
    bix = {n: i for i, n in enumerate(bone_names)}

    def solve_left_hand_ik(
        aa_frame: np.ndarray,
        rp_frame: np.ndarray,
        target_pos: np.ndarray,
        steps: int = 180,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Optimera vänster axel/armbåge/handled lokala rotationer via SOMASkeleton77.fk mot target_pos (3,)."""
        dev = torch.device("cuda:0")
        aa_t = torch.tensor(aa_frame[None], dtype=torch.float32, device=dev)
        rp_t = torch.tensor(rp_frame[None], dtype=torch.float32, device=dev)
        tgt = torch.tensor(target_pos, dtype=torch.float32, device=dev)
        arm_names = ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand"]
        arm_idx = [bix[n] for n in arm_names if n in bix]
        delta = torch.zeros((1, len(arm_idx), 3), dtype=torch.float32, device=dev, requires_grad=True)
        opt = torch.optim.Adam([delta], lr=0.04)
        lh_i = bix["LeftHand"]
        for _ in range(steps):
            opt.zero_grad()
            aa_cur = aa_t.clone()
            for k, bi in enumerate(arm_idx):
                aa_cur[:, bi] = aa_cur[:, bi] + delta[:, k]
            mats = axis_angle_to_matrix(aa_cur)
            _, pos, _ = sk77.fk(mats, rp_t)
            err = ((pos[0, lh_i] - tgt) ** 2).sum() + 0.015 * (delta ** 2).sum()
            err.backward()
            opt.step()
        with torch.no_grad():
            aa_fin = aa_t.clone()
            for k, bi in enumerate(arm_idx):
                aa_fin[:, bi] = aa_fin[:, bi] + delta[:, k]
            mats = axis_angle_to_matrix(aa_fin)
            _, pos_fin, _ = sk77.fk(mats, rp_t)
        return aa_fin[0].cpu().numpy(), pos_fin[0, lh_i].cpu().numpy()

    # Läs faktiska `_generate` innan körning så SDEdit använder 100 % autentisk intern DDIM-loop
    gen_src = inspect.getsource(model._generate)
    print("KIMODO _generate signature:", inspect.signature(model._generate), flush=True)

    results: dict[str, Any] = {
        "meta": {
            "gpu": gpu_name,
            "load_s": load_s,
            "fps": float(model.fps),
            "bone_names_77": bone_names,
            "generate_src": gen_src,
        },
        "fall": {},
    }

    # Hämta A-matris från soma.py för tillbaka-konvertering
    K_soma = soma.soma()
    results["meta"]["A_mjcf_from_kimodo"] = K_soma["A"].tolist()

    # ==================== FALL 1: HÖRN + NY ARBETSBÄNK ====================
    f1_in = indata["fall1"]
    G1 = np.asarray(f1_in["G"], dtype=float)
    r1 = np.asarray(f1_in["rot"], dtype=float)
    n1 = len(G1)
    k1 = soma.smpl_till_soma(G1, r1)
    aa1, rp1 = k1["local_joints_rot"], k1["root_positions"]
    fore = 5
    bas1 = dict(
        frame_indices=list(range(fore)),
        local_joints_rot=aa1[:fore].tolist(),
        root_positions=rp1[:fore].tolist(),
    )
    # Bygg en smidig ~85-graders hörnbana i Kimodo (x vänster, z framåt):
    # Först steg 0.45 m åt vänster (+x), sedan sväng framåt (+z) 0.70 m till arbetsbänken
    t_norm = np.linspace(0.0, 1.0, n1)
    # Ease-in-out
    u = 0.5 - 0.5 * np.cos(np.pi * t_norm)
    r2_orig_0 = rp1[0, [0, 2]]
    path_x = r2_orig_0[0] + 0.55 * np.sin(0.5 * np.pi * u) + 0.35 * (u ** 2)
    path_z = r2_orig_0[1] + 0.85 * (1.0 - np.cos(0.5 * np.pi * u))
    root2d_f1 = np.stack([path_x, path_z], axis=1)
    # Padda upp till minst 75 rutor (n1=109 är >75 redan)
    cl1 = load_constraints_lst(
        [dict(type="fullbody", **bas1)]
        + [dict(type=t, **bas1) for t in ("left-hand", "right-hand", "left-foot", "right-foot")]
        + [dict(type="root2d", frame_indices=list(range(n1)), smooth_root_2d=root2d_f1.tolist())],
        model.skeleton,
        device="cuda:0",
    )
    seed_everything(11)
    t0 = time.time()
    out1 = model(
        f1_in["prompt"],
        n1,
        num_denoising_steps=100,
        constraint_lst=cl1,
        cfg_type="separated",
        cfg_weight=[3.0, 2.2],
        num_samples=4,
        post_processing=True,
        return_numpy=True,
        progress_bar=lambda x, **kw: x,
    )
    dt1 = round(time.time() - t0, 2)
    L1_out = np.asarray(out1["local_rot_mats"])
    R1_out = np.asarray(out1["root_positions"])
    PJ1_out = np.asarray(out1["posed_joints"])
    b1 = io.BytesIO()
    np.savez_compressed(b1, local_rot_mats=L1_out.astype(np.float32), root_positions=R1_out.astype(np.float32), posed_joints=PJ1_out.astype(np.float32))
    results["fall"]["fall1_horn"] = {
        "npz": b1.getvalue(),
        "elapsed_s": dt1,
        "n_frames": n1,
        "target_root2d": root2d_f1.tolist(),
        "orig_rp": rp1.tolist(),
        "s": float(k1["s"]),
        "golv_skift": float(k1["golv_skift"]),
    }

    # ==================== FALL 2: VÄNSTER HAND +15 CM (NOLL SPEGLING) ====================
    f2_in = indata["fall2"]
    G2 = np.asarray(f2_in["G"], dtype=float)
    r2 = np.asarray(f2_in["rot"], dtype=float)
    n2 = len(G2)
    k2 = soma.smpl_till_soma(G2, r2)
    aa2, rp2, L2_orig = k2["local_joints_rot"], k2["root_positions"], k2["local_rot_mats"]
    _, pk2_orig = soma.fk_soma(L2_orig, rp2)
    lh_orig_pos = pk2_orig[:, bix["LeftHand"]]
    rh_orig_pos = pk2_orig[:, bix["RightHand"]]
    # Mål: på rutorna [45, 75, 105] når LeftHand +15 cm högre (+y i Kimodo) & fram över bänken (+z)
    lh_frames = [45, 75, 105]
    lh_targets = []
    lh_aa_list = []
    lh_rp_list = []
    lh_ik_achieved = []
    base_y_counter = float(np.median(lh_orig_pos[:, 1]))
    for fi in lh_frames:
        tgt = np.array([
            float(lh_orig_pos[fi, 0]) + 0.08,   # något in mot mitten/vänster om disken
            base_y_counter + 0.15 + (0.04 if fi == 75 else 0.0),  # +15 till +19 cm över original bänknivå
            float(max(lh_orig_pos[fi, 2], rp2[fi, 2] + 0.36)),    # tydligt fram över disken
        ])
        aa_sol, ach = solve_left_hand_ik(aa2[fi], rp2[fi], tgt)
        lh_targets.append(tgt.tolist())
        lh_aa_list.append(aa_sol.tolist())
        lh_rp_list.append(rp2[fi].tolist())
        lh_ik_achieved.append(ach.tolist())

    bas2 = dict(
        frame_indices=list(range(fore)),
        local_joints_rot=aa2[:fore].tolist(),
        root_positions=rp2[:fore].tolist(),
    )
    cl2 = load_constraints_lst(
        [dict(type="fullbody", **bas2)]
        + [dict(type=t, **bas2) for t in ("left-hand", "right-hand", "left-foot", "right-foot")]
        + [dict(type="left-hand", frame_indices=lh_frames, local_joints_rot=lh_aa_list, root_positions=lh_rp_list)]
        + [dict(type="root2d", frame_indices=list(range(n2)), smooth_root_2d=rp2[:, [0, 2]].tolist())],
        model.skeleton,
        device="cuda:0",
    )
    seed_everything(22)
    t0 = time.time()
    out2 = model(
        f2_in["prompt"],
        n2,
        num_denoising_steps=100,
        constraint_lst=cl2,
        cfg_type="separated",
        cfg_weight=[3.0, 2.2],
        num_samples=4,
        post_processing=True,
        return_numpy=True,
        progress_bar=lambda x, **kw: x,
    )
    dt2 = round(time.time() - t0, 2)
    L2_out = np.asarray(out2["local_rot_mats"])
    R2_out = np.asarray(out2["root_positions"])
    PJ2_out = np.asarray(out2["posed_joints"])
    b2 = io.BytesIO()
    np.savez_compressed(b2, local_rot_mats=L2_out.astype(np.float32), root_positions=R2_out.astype(np.float32), posed_joints=PJ2_out.astype(np.float32))
    results["fall"]["fall2_vansterhand"] = {
        "npz": b2.getvalue(),
        "elapsed_s": dt2,
        "n_frames": n2,
        "lh_frames": lh_frames,
        "lh_targets": lh_targets,
        "lh_ik_achieved": lh_ik_achieved,
        "orig_lh_pos": lh_orig_pos.tolist(),
        "orig_rh_pos": rh_orig_pos.tolist(),
        "orig_pj": pk2_orig.tolist(),
        "s": float(k2["s"]),
        "golv_skift": float(k2["golv_skift"]),
    }

    # ==================== FALL 3: KÄNSLOKONTRAST + SDEDIT s=0.55 vs s=1.0 ====================
    f3_in = indata["fall3"]
    G3 = np.asarray(f3_in["G"], dtype=float)
    r3 = np.asarray(f3_in["rot"], dtype=float)
    n3 = len(G3)
    k3 = soma.smpl_till_soma(G3, r3)
    aa3, rp3, L3_orig = k3["local_joints_rot"], k3["root_positions"], k3["local_rot_mats"]
    _, pk3_orig = soma.fk_soma(L3_orig, rp3)
    bas3 = dict(
        frame_indices=list(range(fore)),
        local_joints_rot=aa3[:fore].tolist(),
        root_positions=rp3[:fore].tolist(),
    )
    cl3 = load_constraints_lst(
        [dict(type="fullbody", **bas3)]
        + [dict(type=t, **bas3) for t in ("left-hand", "right-hand", "left-foot", "right-foot")]
        + [dict(type="root2d", frame_indices=list(range(n3)), smooth_root_2d=rp3[:, [0, 2]].tolist())],
        model.skeleton,
        device="cuda:0",
    )

    # 3a. Baseline s=1.0 (rent brus)
    seed_everything(33)
    t0 = time.time()
    out3_brus = model(
        f3_in["prompt"],
        n3,
        num_denoising_steps=100,
        constraint_lst=cl3,
        cfg_type="separated",
        cfg_weight=[3.2, 2.0],
        num_samples=4,
        post_processing=True,
        return_numpy=True,
        progress_bar=lambda x, **kw: x,
    )
    dt3_brus = round(time.time() - t0, 2)
    b3b = io.BytesIO()
    np.savez_compressed(
        b3b,
        local_rot_mats=np.asarray(out3_brus["local_rot_mats"], np.float32),
        root_positions=np.asarray(out3_brus["root_positions"], np.float32),
        posed_joints=np.asarray(out3_brus["posed_joints"], np.float32),
    )
    results["fall"]["fall3_brus_s10"] = {
        "npz": b3b.getvalue(),
        "elapsed_s": dt3_brus,
        "n_frames": n3,
        "orig_pj": pk3_orig.tolist(),
        "s": float(k3["s"]),
        "golv_skift": float(k3["golv_skift"]),
    }

    # 3b. SDEdit s=0.55 direkt med Kimodos diffusion.q_sample + DDIM denoising_step
    sdedit_info: dict[str, Any] = {"ok": False}
    try:
        sk_in = model.motion_rep.skeleton
        idx30 = [bix[n] for n in sk_in.bone_order_names]
        L30 = torch.tensor(L3_orig[:, idx30][None], dtype=torch.float32, device="cuda:0")
        rp_t3 = torch.tensor(rp3[None], dtype=torch.float32, device="cuda:0")
        mr_sig = inspect.signature(model.motion_rep)
        mr_kw = {}
        if "to_normalize" in mr_sig.parameters:
            mr_kw["to_normalize"] = True
        if "lengths" in mr_sig.parameters:
            mr_kw["lengths"] = torch.tensor([n3], dtype=torch.long, device="cuda:0")
        x0_s30 = model.motion_rep(L30, rp_t3, **mr_kw)
        if isinstance(x0_s30, (tuple, list)):
            x0_s30 = x0_s30[0]
        k_target_step = int(round(0.55 * (100 - 1)))  # = 54 av 0..99 (55 denoisingsteg)
        orig_dstep = model.denoising_step
        step_counter = {"n": 0, "skipped": 0, "ran": 0, "q_shape": None, "sig": str(inspect.signature(orig_dstep))}

        def hooked_dstep(*d_args, **d_kwargs):
            # Exakta positionella arg i KimodoModel.denoising_step:
            # (cur_mot, pad_mask, text_feat, text_pad_mask, t, first_heading_angle, motion_mask, observed_motion, ...)
            step_counter["n"] += 1
            cur_mot = d_args[0] if len(d_args) > 0 else d_kwargs["cur_mot"]
            t_arg = d_args[4] if len(d_args) > 4 else d_kwargs["t"]
            t_cur = int(t_arg[0].item()) if isinstance(t_arg, torch.Tensor) else int(t_arg)

            if t_cur > k_target_step:
                step_counter["skipped"] += 1
                return cur_mot

            if t_cur == k_target_step:
                x0_rep = x0_s30.to(cur_mot.device, cur_mot.dtype)
                if x0_rep.shape[0] != cur_mot.shape[0]:
                    x0_rep = x0_rep.repeat(cur_mot.shape[0] // x0_rep.shape[0], 1, 1)
                if x0_rep.shape[1] != cur_mot.shape[1]:
                    if x0_rep.shape[1] > cur_mot.shape[1]:
                        x0_rep = x0_rep[:, : cur_mot.shape[1]]
                    else:
                        pad = x0_rep[:, -1:].repeat(1, cur_mot.shape[1] - x0_rep.shape[1], 1)
                        x0_rep = torch.cat([x0_rep, pad], dim=1)
                if x0_rep.shape != cur_mot.shape:
                    raise RuntimeError(f"SDEdit shape mismatch: x0={tuple(x0_rep.shape)} vs cur_mot={tuple(cur_mot.shape)}")
                seed_everything(33)
                t_tensor = t_arg if isinstance(t_arg, torch.Tensor) else torch.full((cur_mot.shape[0],), int(t_arg), device=cur_mot.device, dtype=torch.long)
                if t_tensor.ndim == 0:
                    t_tensor = t_tensor.expand(cur_mot.shape[0])
                cur_mot = model.diffusion.q_sample(x0_rep, t_tensor)
                step_counter["q_shape"] = list(cur_mot.shape)
                if len(d_args) > 0:
                    arg_l = list(d_args)
                    arg_l[0] = cur_mot
                    d_args = tuple(arg_l)
                else:
                    d_kwargs["cur_mot"] = cur_mot
            step_counter["ran"] += 1
            return orig_dstep(*d_args, **d_kwargs)

        model.denoising_step = hooked_dstep
        t0 = time.time()
        try:
            seed_everything(33)
            out3_sd = model(
                f3_in["prompt"],
                n3,
                num_denoising_steps=100,
                constraint_lst=cl3,
                cfg_type="separated",
                cfg_weight=[3.2, 2.0],
                num_samples=4,
                post_processing=True,
                return_numpy=True,
                progress_bar=lambda x, **kw: x,
            )
        finally:
            model.denoising_step = orig_dstep
        dt3_sd = round(time.time() - t0, 2)
        b3s = io.BytesIO()
        np.savez_compressed(
            b3s,
            local_rot_mats=np.asarray(out3_sd["local_rot_mats"], np.float32),
            root_positions=np.asarray(out3_sd["root_positions"], np.float32),
            posed_joints=np.asarray(out3_sd["posed_joints"], np.float32),
        )
        sdedit_info = {"ok": True, "step_counter": step_counter, "elapsed_s": dt3_sd}
        results["fall"]["fall3_sdedit_s055"] = {
            "npz": b3s.getvalue(),
            "elapsed_s": dt3_sd,
            "n_frames": n3,
            "step_counter": step_counter,
            "orig_pj": pk3_orig.tolist(),
            "s": float(k3["s"]),
            "golv_skift": float(k3["golv_skift"]),
        }
    except Exception as sd_err:
        import traceback
        sdedit_info = {"ok": False, "fel": repr(sd_err), "trace": traceback.format_exc()[-1500:]}
    results["meta"]["sdedit_info"] = sdedit_info
    return results


# ==================== LOKAL MÄTNING + SCENPAKET/2-EXPORT ====================
def soma_till_paket_rutor(
    pj_kimodo: np.ndarray,
    A_mjcf_from_kimodo: np.ndarray,
    bone_names: list[str],
    pak_ref: dict[str, Any],
    shot_id: str,
    pid: str,
) -> tuple[list[list[float]], np.ndarray]:
    """Mappar Kimodos kanoniska SOMA77 `posed_joints` (T,77,3) till `paket.json` världsrutor (T, 1+28*3) i mm."""
    bix = {n: i for i, n in enumerate(bone_names)}
    # Hämta originalets första bildruta i paket.json för exakt golv-, position- och yaw-ankring
    rutor_orig = next(s["rutor"] for s in pak_ref["rorelse"][pid] if s["tagning"] == shot_id)
    r0_mm = np.asarray(rutor_orig[0][1:], float).reshape(-1, 3)
    r0_m = r0_mm / 1000.0
    led_pak = pak_ref["leder"]
    pix = {n: i for i, n in enumerate(led_pak)}

    # 1. Konvertera SOMA77 -> MJCF kanonisk (+x framåt, +y vänster, +z upp)
    T = len(pj_kimodo)
    pj_mjcf = np.einsum("ij,tkj->tki", A_mjcf_from_kimodo, pj_kimodo)

    # 2. Hitta golvnivå och rotyaw i paket.json vid ruta 0
    pak_la, pak_ra = r0_m[pix["l_clavicle"]], r0_m[pix["r_clavicle"]]
    pak_left_vec = (pak_la - pak_ra)[:2]
    pak_fwd = np.array([pak_left_vec[1], -pak_left_vec[0]])  # framåt = left x up (-90° från left)
    pak_yaw = math.atan2(pak_fwd[1], pak_fwd[0])

    s_la, s_ra = pj_mjcf[0, bix["LeftShoulder"]], pj_mjcf[0, bix["RightShoulder"]]
    s_left = (s_la - s_ra)[:2]
    s_fwd = np.array([s_left[1], -s_left[0]])
    s_yaw = math.atan2(s_fwd[1], s_fwd[0])

    dyaw = pak_yaw - s_yaw
    c, s = math.cos(dyaw), math.sin(dyaw)
    Rz = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    pj_rot = np.einsum("ij,tkj->tki", Rz, pj_mjcf)

    # Ankra Hips XY och fotsula Z mot paket.json ruta 0
    pak_hips0 = r0_m[pix["c_spine0"]]
    s_hips0 = pj_rot[0, bix["Hips"]]
    pak_foot_z0 = min(r0_m[pix["l_foot"], 2], r0_m[pix["r_foot"], 2], r0_m[pix["l_ball"], 2], r0_m[pix["r_ball"], 2])
    s_foot_z0 = min(
        pj_rot[0, bix["LeftFoot"], 2],
        pj_rot[0, bix["RightFoot"], 2],
        pj_rot[0, bix.get("LeftToeBase", bix["LeftFoot"]), 2],
        pj_rot[0, bix.get("RightToeBase", bix["RightFoot"]), 2],
    )
    shift = np.array([pak_hips0[0] - s_hips0[0], pak_hips0[1] - s_hips0[1], pak_foot_z0 - s_foot_z0])
    pj_world = pj_rot + shift[None, None, :]

    # Bygg alla 28 BEN1-leder per ruta
    # Direkt mappning SOMA77 -> BEN1
    SOMA_TO_BEN1 = {
        "c_spine0": "Hips",
        "c_spine1": "Spine1",
        "c_spine2": "Spine2",
        "c_spine3": "Chest",
        "c_neck": "Neck1",
        "c_head": "Head",
        "huvud_upp": "HeadEnd",
        "l_clavicle": "LeftShoulder",
        "l_uparm": "LeftArm",
        "l_lowarm": "LeftForeArm",
        "l_wrist": "LeftHand",
        "l_hand_mitt": "LeftHandMiddle1",
        "l_index1": "LeftHandIndex1",
        "r_clavicle": "RightShoulder",
        "r_uparm": "RightArm",
        "r_lowarm": "RightForeArm",
        "r_wrist": "RightHand",
        "r_hand_mitt": "RightHandMiddle1",
        "r_index1": "RightHandIndex1",
        "l_upleg": "LeftLeg",
        "l_lowleg": "LeftShin",
        "l_foot": "LeftFoot",
        "l_ball": "LeftToeBase",
        "r_upleg": "RightLeg",
        "r_lowleg": "RightShin",
        "r_foot": "RightFoot",
        "r_ball": "RightToeBase",
    }

    rutor_ut: list[list[float]] = []
    world_28 = np.zeros((T, len(BEN1_LEDER), 3), dtype=float)
    for t_i in range(T):
        coords_mm: list[float] = []
        for j_i, ben_namn in enumerate(BEN1_LEDER):
            if ben_namn == "nasa_mal":
                h_p = pj_world[t_i, bix["Head"]]
                he_p = pj_world[t_i, bix.get("HeadEnd", bix["Head"])]
                la_p = pj_world[t_i, bix["LeftArm"]]
                ra_p = pj_world[t_i, bix["RightArm"]]
                up_v = he_p - h_p
                up_v = up_v / (np.linalg.norm(up_v) + 1e-8)
                left_v = la_p - ra_p
                fwd_v = np.cross(left_v, up_v)
                n_f = np.linalg.norm(fwd_v)
                fwd_v = fwd_v / n_f if n_f > 1e-6 else np.array([1.0, 0.0, 0.0])
                p_m = h_p + 0.04 * up_v + 0.11 * fwd_v
            else:
                sn = SOMA_TO_BEN1[ben_namn]
                if sn in bix:
                    p_m = pj_world[t_i, bix[sn]]
                else:
                    # Fallback för handändleder
                    base = "LeftHand" if ben_namn.startswith("l_") else "RightHand"
                    p_m = pj_world[t_i, bix[base]] + np.array([0.0, 0.0, -0.05])
            world_28[t_i, j_i] = p_m
            coords_mm.extend([round(float(v * 1000.0), 1) for v in p_m])
        rutor_ut.append([float(t_i)] + coords_mm)
    return rutor_ut, world_28


def _kimodo_xz_till_world_xy(
    kim_pt_3d: np.ndarray,
    pj0_kim: np.ndarray,
    A_mat: np.ndarray,
    bix: dict[str, int],
    pak_ref: dict[str, Any],
    shot_id: str,
    pid: str,
) -> list[float]:
    """Transformerar en enstaka 3D-punkt i Kimodo-världen till klippets paket.json-värld (meter)."""
    rutor_orig = next(s["rutor"] for s in pak_ref["rorelse"][pid] if s["tagning"] == shot_id)
    r0_m = np.asarray(rutor_orig[0][1:], float).reshape(-1, 3) / 1000.0
    pix = {n: i for i, n in enumerate(pak_ref["leder"])}
    pj_mjcf = np.einsum("ij,kj->ki", A_mat, pj0_kim)
    pak_left = (r0_m[pix["l_clavicle"]] - r0_m[pix["r_clavicle"]])[:2]
    pak_fwd = np.array([pak_left[1], -pak_left[0]])
    s_left = (pj_mjcf[bix["LeftShoulder"]] - pj_mjcf[bix["RightShoulder"]])[:2]
    s_fwd = np.array([s_left[1], -s_left[0]])
    dyaw = math.atan2(pak_fwd[1], pak_fwd[0]) - math.atan2(s_fwd[1], s_fwd[0])
    c, s = math.cos(dyaw), math.sin(dyaw)
    Rz = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    pj_rot = np.einsum("ij,kj->ki", Rz, pj_mjcf)
    s_foot = min(pj_rot[bix["LeftFoot"], 2], pj_rot[bix["RightFoot"], 2])
    pak_foot = min(r0_m[pix["l_foot"], 2], r0_m[pix["r_foot"], 2])
    shift = np.array([r0_m[pix["c_spine0"], 0] - pj_rot[bix["Hips"], 0], r0_m[pix["c_spine0"], 1] - pj_rot[bix["Hips"], 1], pak_foot - s_foot])
    pt_world = (Rz @ (A_mat @ kim_pt_3d)) + shift
    return [round(float(v), 3) for v in pt_world]


def mat_fotglidning_soma(pj_kim: np.ndarray, bix: dict[str, int]) -> dict[str, float]:
    """Beräkna fotglidning i Kimodo-världen (+y upp, x/z golv) där foten är i kontakt (<5 cm över 2-percentilen)."""
    y_l = np.minimum(pj_kim[:, bix["LeftFoot"], 1], pj_kim[:, bix.get("LeftToeBase", bix["LeftFoot"]), 1])
    y_r = np.minimum(pj_kim[:, bix["RightFoot"], 1], pj_kim[:, bix.get("RightToeBase", bix["RightFoot"]), 1])
    golv_y = float(np.percentile(np.concatenate([y_l, y_r]), 2))
    out = {}
    max_step = 0.0
    for sida, jn, yv in (("V", "LeftFoot", y_l), ("H", "RightFoot", y_r)):
        kontakt = (yv[:-1] - golv_y < 0.05) & (yv[1:] - golv_y < 0.05)
        xz = pj_kim[:, bix[jn], [0, 2]]
        d_cm = np.linalg.norm(np.diff(xz, axis=0), axis=1) * 100.0
        tot = float(np.sum(d_cm[kontakt])) if np.any(kontakt) else 0.0
        mx = float(np.max(d_cm[kontakt])) if np.any(kontakt) else 0.0
        out[f"glid_{sida}_tot_cm"] = round(tot, 2)
        out[f"glid_{sida}_max_steg_cm"] = round(mx, 2)
        max_step = max(max_step, mx)
    out["fotglidning_tot_cm"] = round(max(out["glid_V_tot_cm"], out["glid_H_tot_cm"]), 2)
    out["fotglidning_max_steg_cm"] = round(max_step, 2)
    return out


def speed_corr(pj_cand: np.ndarray, pj_orig: np.ndarray, bix: dict[str, int]) -> tuple[float, float, int]:
    """Hastighets- och beatsynk-korrelation (händer + huvud) samt optimal lag inom ±6 rutor."""
    joints = [bix["LeftHand"], bix["RightHand"], bix["Head"]]
    n = min(len(pj_cand), len(pj_orig))
    vc = np.linalg.norm(np.diff(pj_cand[:n, joints], axis=0), axis=-1).mean(axis=1)
    vo = np.linalg.norm(np.diff(pj_orig[:n, joints], axis=0), axis=-1).mean(axis=1)
    if np.std(vc) < 1e-8 or np.std(vo) < 1e-8:
        return 0.0, 0.0, 0
    r0 = float(np.corrcoef(vc, vo)[0, 1])
    best_r, best_lag = r0, 0
    for lag in range(-6, 7):
        if lag < 0:
            a, b = vc[-lag:], vo[: len(vo) + lag]
        elif lag > 0:
            a, b = vc[: len(vc) - lag], vo[lag:]
        else:
            a, b = vc, vo
        if len(a) >= 10 and np.std(a) > 1e-8 and np.std(b) > 1e-8:
            r = float(np.corrcoef(a, b)[0, 1])
            if r > best_r:
                best_r, best_lag = r, lag
    return round(r0, 4), round(best_r, 4), best_lag


@app.local_entrypoint()
def main() -> None:
    UT_DIR.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(MM_DIR))
    import tagning as TG

    # Ladda verkliga utvecklingssegment
    t_guac = TG.las(
        "e-dialog-guacamole_grupp/kalla_0032.json",
        "e-dialog-guacamole_grupp/liggare_0032.json",
        "s4",
        "B",
    )
    ref_guac = TG.referens(t_guac)
    Gg_c, rg_c, _, _ = kanon(ref_guac["G"], ref_guac["rot"])

    t_gel = TG.las(
        "kand-kennysgelato_n06-hand/kalla_0033.json",
        "kand-kennysgelato_n06-hand/liggare_0033.json",
        "s1",
        "A",
    )
    ref_gel = TG.referens(t_gel)
    Gk_c, rk_c, _, _ = kanon(ref_gel["G"], ref_gel["rot"])
    n_gel = min(120, len(Gk_c))  # 4.00 s stående med full spännvidd
    Gk_c, rk_c = Gk_c[:n_gel], rk_c[:n_gel]

    indata = {
        "fall1": {
            "G": Gg_c.tolist(),
            "rot": rg_c.tolist(),
            "prompt": "A person steps smoothly sideways around a bar counter corner and turns toward a new stainless workbench to set down a small dish",
        },
        "fall2": {
            "G": Gk_c.tolist(),
            "rot": rk_c.tolist(),
            "prompt": "A person standing behind a counter reaches forward and upward with only the left hand to place a small plate on a raised shelf while keeping the right hand down at the side",
        },
        "fall3": {
            "G": Gg_c.tolist(),
            "rot": rg_c.tolist(),
            "prompt": "An exhausted bored bartender slouches heavily behind a bar counter with drooping shoulders and minimal slow weary hand gestures",
        },
    }

    cache_fil = UT_DIR / "modal_raw_cache.pkl"
    if "--from-cache" in sys.argv and cache_fil.exists():
        print(f"Läser cachat Modal-utfall från {cache_fil}...", flush=True)
        payload = pickle.loads(cache_fil.read_bytes())
        res = payload["res"]
        wall_s = payload["wall_s"]
    else:
        t_tot0 = time.time()
        print("Skickar alla 3 Kimodo-kontrastfall i 1 GPU-körning på Modal...", flush=True)
        res = kor_kontrast_modal.remote(indata)
        wall_s = round(time.time() - t_tot0, 2)
        cache_fil.write_bytes(pickle.dumps({"res": res, "wall_s": wall_s}))

    meta = res["meta"]
    gpu_name = meta["gpu"]
    usd_per_s = GPU_USD_PER_SEC.get(gpu_name, 1.50 / 3600.0)
    bix = {n: i for i, n in enumerate(meta["bone_names_77"])}
    A_mat = np.asarray(meta["A_mjcf_from_kimodo"], float)

    print(f"Container: {gpu_name} | load_s={meta['load_s']} | wall_s={wall_s} | SDEdit={meta['sdedit_info']}", flush=True)

    # Packa mätningar & bygg scenpaket/2 för de 3 soundoverlay-renderingarna
    pak_guac = json.loads(
        (ROT / "motpart/runda-3-opus/B-nasta-klipp/ut/regr5/e-dialog-guacamole-tagningar/paket.json").read_text(encoding="utf-8")
    )
    pak_gel = json.loads(
        (ROT / "motpart/runda-3-opus/B-nasta-klipp/ut/regr5/kand-kennysgelato-tagningar/paket.json").read_text(encoding="utf-8")
    )

    matning: dict[str, Any] = {
        "container": {
            "gpu": gpu_name,
            "load_s": meta["load_s"],
            "total_wall_s": wall_s,
            "est_usd_per_s": round(usd_per_s, 6),
            "sdedit_info": meta["sdedit_info"],
        },
        "fall": {},
    }

    # --- 1. FALL 1 ---
    f1 = res["fall"]["fall1_horn"]
    z1 = np.load(io.BytesIO(f1["npz"]))
    pj1 = z1["posed_joints"]
    rp1_out = z1["root_positions"]
    tgt1 = np.asarray(f1["target_root2d"])
    rp1_orig = np.asarray(f1["orig_rp"])
    orig_pj_guac = np.asarray(res["fall"]["fall3_brus_s10"]["orig_pj"])
    samples_1 = []
    for i in range(len(pj1)):
        glid = mat_fotglidning_soma(pj1[i], bix)
        hips_xz = pj1[i, :, bix["Hips"], :][:, [0, 2]]
        wp_err_cm = np.linalg.norm(hips_xz - tgt1, axis=1) * 100.0
        end_err_cm = float(np.linalg.norm(hips_xz[-1] - tgt1[-1]) * 100.0)
        r0, r_best, lag = speed_corr(pj1[i], orig_pj_guac, bix)
        samples_1.append({
            "prov": i,
            "waypoint_mean_cm": round(float(np.mean(wp_err_cm)), 2),
            "waypoint_max_cm": round(float(np.max(wp_err_cm)), 2),
            "waypoint_slut_cm": round(end_err_cm, 2),
            "speed_corr_0": r0,
            "speed_corr_best": r_best,
            "best_lag": lag,
            **glid,
        })
    best1 = min(range(len(samples_1)), key=lambda i: samples_1[i]["waypoint_slut_cm"] + samples_1[i]["fotglidning_tot_cm"])
    div1_cm = round(float(np.std(pj1[:, :, [bix["Hips"], bix["LeftHand"], bix["RightHand"]], :], axis=0).mean() * 100.0), 2)
    matning["fall"]["fall1_horn"] = {
        "klipp": "e-dialog-guacamole s4 B",
        "elapsed_s": f1["elapsed_s"],
        "est_cost_usd": round((f1["elapsed_s"] + meta["load_s"] / 4.0) * usd_per_s, 4),
        "n_frames": f1["n_frames"],
        "vald_prov": best1,
        "diversitet_std_cm": div1_cm,
        "sampel": samples_1,
    }
    rutor1, _ = soma_till_paket_rutor(pj1[best1], A_mat, meta["bone_names_77"], pak_guac, "s4", "B")

    # --- 2. FALL 2 ---
    f2 = res["fall"]["fall2_vansterhand"]
    z2 = np.load(io.BytesIO(f2["npz"]))
    pj2 = z2["posed_joints"]
    orig_pj2 = np.asarray(f2["orig_pj"])
    lh_frames = f2["lh_frames"]
    lh_targets = np.asarray(f2["lh_targets"])
    orig_lh = np.asarray(f2["orig_lh_pos"])
    orig_rh = np.asarray(f2["orig_rh_pos"])
    samples_2 = []
    for i in range(len(pj2)):
        glid = mat_fotglidning_soma(pj2[i], bix)
        lh_pred = pj2[i, :, bix["LeftHand"], :]
        rh_pred = pj2[i, :, bix["RightHand"], :]
        err_tgt = np.linalg.norm(lh_pred[lh_frames] - lh_targets, axis=1) * 100.0
        err_y = np.abs(lh_pred[lh_frames, 1] - lh_targets[:, 1]) * 100.0
        lh_travel_cm = float(np.linalg.norm(np.ptp(lh_pred, axis=0)) * 100.0)
        rh_travel_cm = float(np.linalg.norm(np.ptp(rh_pred, axis=0)) * 100.0)
        # No-mirror: LeftHand räckte tydligt ut (> RightHand peak reach eller följde LeftHand-målet)
        lh_peak_y_cm = round(float(lh_pred[:, 1].max() * 100.0), 1)
        orig_lh_peak_y_cm = round(float(orig_lh[:, 1].max() * 100.0), 1)
        r0, r_best, lag = speed_corr(pj2[i], orig_pj2, bix)
        samples_2.append({
            "prov": i,
            "lh_target_err_cm": [round(float(x), 2) for x in err_tgt],
            "lh_target_mean_cm": round(float(np.mean(err_tgt)), 2),
            "lh_height_err_mean_cm": round(float(np.mean(err_y)), 2),
            "lh_peak_y_cm": lh_peak_y_cm,
            "orig_lh_peak_y_cm": orig_lh_peak_y_cm,
            "lh_travel_cm": round(lh_travel_cm, 1),
            "rh_travel_cm": round(rh_travel_cm, 1),
            "spegling_misstankt": bool(rh_travel_cm > lh_travel_cm * 1.4 and np.mean(err_tgt) > 15.0),
            "speed_corr_0": r0,
            "speed_corr_best": r_best,
            "best_lag": lag,
            **glid,
        })
    best2 = min(range(len(samples_2)), key=lambda i: samples_2[i]["lh_target_mean_cm"] + samples_2[i]["fotglidning_tot_cm"])
    div2_cm = round(float(np.std(pj2[:, :, [bix["LeftHand"], bix["RightHand"], bix["Head"]], :], axis=0).mean() * 100.0), 2)
    matning["fall"]["fall2_vansterhand"] = {
        "klipp": "kand-kennysgelato s1 A (rutor 0-119)",
        "elapsed_s": f2["elapsed_s"],
        "est_cost_usd": round((f2["elapsed_s"] + meta["load_s"] / 4.0) * usd_per_s, 4),
        "n_frames": f2["n_frames"],
        "vald_prov": best2,
        "diversitet_std_cm": div2_cm,
        "sampel": samples_2,
    }
    rutor2, _ = soma_till_paket_rutor(pj2[best2], A_mat, meta["bone_names_77"], pak_gel, "s1", "A")

    # --- 3. FALL 3 (s=1.0 vs SDEdit s=0.55) ---
    rutor3 = None
    best3_sd = 0
    for variant_namn in ("fall3_brus_s10", "fall3_sdedit_s055"):
        if variant_namn not in res["fall"]:
            continue
        fv = res["fall"][variant_namn]
        zv = np.load(io.BytesIO(fv["npz"]))
        pjv = zv["posed_joints"]
        orig_pj3 = np.asarray(fv["orig_pj"])
        samples_v = []
        # Mät även "sjunkande axlar / uttråkad hållning": minskad huvudhöjd - axelhöjd & minskad handhöjd
        orig_head_y = float(np.mean(orig_pj3[:, bix["Head"], 1]))
        orig_spine_tilt = float(
            np.mean(
                np.linalg.norm(
                    orig_pj3[:, bix["Head"]][:, [0, 2]] - orig_pj3[:, bix["Hips"]][:, [0, 2]], axis=-1
                )
            )
        )
        key_j = [bix["Head"], bix["Chest"], bix["LeftHand"], bix["RightHand"]]
        for i in range(len(pjv)):
            p = pjv[i]
            glid = mat_fotglidning_soma(p, bix)
            head_y = float(np.mean(p[:, bix["Head"], 1]))
            spine_tilt = float(
                np.mean(
                    np.linalg.norm(
                        p[:, bix["Head"]][:, [0, 2]] - p[:, bix["Hips"]][:, [0, 2]], axis=-1
                    )
                )
            )
            r0, r_best, lag = speed_corr(p, orig_pj3, bix)
            # Avstånd mot originalets leder (hur mycket känsloregin ändrar formen)
            mean_joint_diff_cm = float(
                np.linalg.norm(
                    p[:, key_j, :] - orig_pj3[:, key_j, :],
                    axis=-1,
                ).mean()
                * 100.0
            )
            samples_v.append({
                "prov": i,
                "head_sankning_cm": round((orig_head_y - head_y) * 100.0, 2),
                "framåtlutning_diff_cm": round((spine_tilt - orig_spine_tilt) * 100.0, 2),
                "overkropps_diff_cm": round(mean_joint_diff_cm, 2),
                "speed_corr_0": r0,
                "speed_corr_best": r_best,
                "best_lag": lag,
                **glid,
            })
        best_v = max(range(len(samples_v)), key=lambda i: samples_v[i]["speed_corr_0"] + 0.02 * samples_v[i]["overkropps_diff_cm"])
        div_v = round(float(np.std(pjv[:, :, [bix["Head"], bix["LeftHand"], bix["RightHand"]], :], axis=0).mean() * 100.0), 2)
        matning["fall"][variant_namn] = {
            "klipp": "e-dialog-guacamole s4 B",
            "elapsed_s": fv["elapsed_s"],
            "est_cost_usd": round((fv["elapsed_s"] + meta["load_s"] / 4.0) * usd_per_s, 4),
            "n_frames": fv["n_frames"],
            "vald_prov": best_v,
            "diversitet_std_cm": div_v,
            "sampel": samples_v,
        }
        if variant_namn == "fall3_sdedit_s055":
            best3_sd = best_v
            rutor3, _ = soma_till_paket_rutor(pjv[best3_sd], A_mat, meta["bone_names_77"], pak_guac, "s4", "B")
        elif rutor3 is None:
            rutor3, _ = soma_till_paket_rutor(pjv[best_v], A_mat, meta["bone_names_77"], pak_guac, "s4", "B")

    tot_est_usd = sum(v.get("est_cost_usd", 0.0) for v in matning["fall"].values())
    matning["container"]["total_est_cost_usd"] = round(tot_est_usd, 4)

    (UT_DIR / "matning.json").write_text(json.dumps(matning, ensure_ascii=False, indent=2), encoding="utf-8")

    # Bygg fristående scenpaket/2-JSON för varje fall så lokal Three.js + ffmpeg kan rendera 3 soundoverlay-MP4:or
    def bygg_segment_paket(
        bas_pak: dict[str, Any],
        shot_id: str,
        pid: str,
        nya_rutor: list[list[float]],
        extra_obj: list[dict[str, Any]],
        tema_id: str = "kok",
    ) -> dict[str, Any]:
        import copy
        p = copy.deepcopy(bas_pak)
        fps = float(p["tidsbas"]["fps"])
        sh = next(t for t in p["tagningar"] if t["id"] == shot_id)
        u0, u1 = int(sh["ut"][0]), int(sh["ut"][1])
        n_ny = len(nya_rutor)
        # Kapa eller sträck uttagna kameranycklar till [0, n_ny]
        nyck = []
        for k in sh["kamera"]["nycklar"]:
            if u0 - 1 <= k[0] <= u1 + 1:
                kk = list(k)
                kk[0] = max(0, min(n_ny - 1, round(kk[0] - u0)))
                nyck.append(kk)
        if not nyck:
            nyck = [list(sh["kamera"]["nycklar"][0])]
            nyck[0][0] = 0
        nyck = sorted(nyck, key=lambda x: x[0])
        if nyck[0][0] > 0:
            first = list(nyck[0]); first[0] = 0; nyck.insert(0, first)
        if nyck[-1][0] < n_ny - 1:
            last = list(nyck[-1]); last[0] = n_ny - 1; nyck.append(last)

        p["tidsbas"] = {"fps": fps, "antal_rutor": n_ny, "typ": "konstant"}
        p["tagningar"] = [{"id": shot_id, "ut": [0, n_ny], "kamera": {"typ": sh["kamera"].get("typ", "statisk"), "nycklar": nyck}}]
        p["leder"] = BEN1_LEDER
        p["rorelse"] = {pid: [{"tagning": shot_id, "ut": [0, n_ny], "rutor": nya_rutor}]}
        # Behåll rums-objekt aktiva över [0, n_ny] + lägg till fallets referensmarkörer (hörnbänk / upphöjd hylla)
        obj_ut = []
        for o in p.get("objekt", []):
            oo = copy.deepcopy(o)
            oo["synlig_ut"] = [[0, n_ny]]
            obj_ut.append(oo)
        for eo in extra_obj:
            eo_c = dict(eo, synlig_ut=[[0, n_ny]])
            obj_ut.append(eo_c)
        p["objekt"] = obj_ut
        return p

    # Spara de 3 scenpaketen med exakt transformerade målmått från Kimodos målkoordinater
    corner_kim_end = np.array([float(tgt1[-1, 0]), float(pj1[best1, 0, bix["Hips"], 1]) - 0.45, float(tgt1[-1, 1])])
    corner_pos = _kimodo_xz_till_world_xy(corner_kim_end, pj1[best1, 0], A_mat, bix, pak_guac, "s4", "B")
    corner_pos[2] = 0.45

    hylla_kim_mid = np.asarray(lh_targets[1], float)  # mittenmålet +19 cm
    hylla_pos = _kimodo_xz_till_world_xy(hylla_kim_mid, pj2[best2, 0], A_mat, bix, pak_gel, "s1", "A")
    hylla_pos[2] = round(hylla_pos[2] - 0.08, 3)

    pak1 = bygg_segment_paket(
        pak_guac,
        "s4",
        "B",
        rutor1,
        [{"id": "ny_hornbank", "typ": "bank", "etikett": "Hörnbänk (mål)", "pos": corner_pos, "matt": [0.85, 0.55, 0.90], "farg": "#9aa3b0"}],
    )
    pak2 = bygg_segment_paket(
        pak_gel,
        "s1",
        "A",
        rutor2,
        [{"id": "hojd_hylla", "typ": "bank", "etikett": "Hylla +15 cm (V-hand)", "pos": hylla_pos, "matt": [0.46, 0.36, 0.10], "farg": "#38b87c"}],
    )
    pak3 = bygg_segment_paket(
        pak_guac,
        "s4",
        "B",
        rutor3,
        [],
    )

    (UT_DIR / "scen_fall1_horn.json").write_text(json.dumps(pak1), encoding="utf-8")
    (UT_DIR / "scen_fall2_hand.json").write_text(json.dumps(pak2), encoding="utf-8")
    (UT_DIR / "scen_fall3_sdedit.json").write_text(json.dumps(pak3), encoding="utf-8")
    print("KIMODO_KONTRAST_KLAR! Est. USD:", matning["container"]["total_est_cost_usd"], flush=True)
    print(json.dumps(matning["fall"], ensure_ascii=False, indent=2)[:2500], flush=True)
