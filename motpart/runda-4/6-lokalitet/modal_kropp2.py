"""kropp/2: personer per tagning ur 2D-posedetektioner (IoU-spårning) -> SAM 3D Body på Modal -> leder i kamerakoordinater.

Skillnad mot ingest_v2: ingen global utseendebaserad identitet (gav dubbletter/fantomer), ingen golvflytt,
samma fokal som lokaliteten (MoGe ViT-L). Skriver ut/<nyckel>/kropp2/paket.json i A-format (scenpaket/2) så att
lokalitet.py använder kedjan oförändrad. Återanvänder ingest_v2:s image och viktvolymer; laddar bara SAM3D.
Kör: PYTHONUTF8=1 scen/.venv/Scripts/modal.exe run motpart/runda-4/6-lokalitet/modal_kropp2.py --klipp "namn:nyckel,..."
"""
from __future__ import annotations
import io, json, sys, time
from pathlib import Path
import modal

HERE = Path(__file__).resolve().parent
LOKAL = modal.is_local()
ROOT = HERE.parents[2] if LOKAL else HERE
sys.path.insert(0, str(ROOT / "arbetsbord" / "ingest_v2") if LOKAL else "/root")
import modal_ingest_v2 as iv2  # noqa: E402  (image, volymer, ledlista)

app = modal.App("hagen-lokalitet-kropp2")
LEDER = iv2.LEDER_T1
IMG = iv2.img.add_local_file(str(ROOT / "arbetsbord" / "ingest_v2" / "modal_ingest_v2.py"), "/root/modal_ingest_v2.py") if LOKAL else iv2.img


@app.cls(image=IMG, gpu=["L4", "A10G", "L40S", "A100-40GB"], volumes={"/vikter_sam": iv2.vol_sam},
         secrets=[modal.Secret.from_name("huggingface")], timeout=1500, scaledown_window=60, max_containers=6)
class Kropp2:
    @modal.enter()
    def ladda(self):
        import json as _j, os, torch
        t0 = time.perf_counter()
        rigg = _j.loads(open("/root/tro_rigg.json", encoding="utf-8").read())
        self.mhr_ix = {n: i for i, n in enumerate(rigg["namn"])}
        sys.path.insert(0, "/kod")
        from huggingface_hub import snapshot_download
        sam_dir = snapshot_download("facebook/sam-3d-body-vith", local_dir="/vikter_sam/vith", token=os.environ.get("HF_TOKEN"))
        from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
        m, cfg = load_sam_3d_body(f"{sam_dir}/model.ckpt", device=torch.device("cuda"), mhr_path=f"{sam_dir}/assets/mhr_model.pt")
        self.sam = SAM3DBodyEstimator(sam_3d_body_model=m, model_cfg=cfg)
        self.ladd_s = round(time.perf_counter() - t0, 1)

    def _t1(self, o):
        """MHR -> 28 T1-leder i kamerakoordinater (OpenCV, meter). Huvudpunkterna: samma regler som ingest_v2,
        men 'uppåt' = bildens uppåt (-y) eftersom lodlinjen bestäms senare av lokaliteten."""
        import numpy as np
        P = o["pred_joint_coords"].astype(float) + o["pred_cam_t"].astype(float); m = self.mhr_ix; hi = m["c_head"]
        v = P[m.get("r_eye", hi)] * 0.5 + P[m.get("l_eye", hi)] * 0.5 - P[hi]; nv = float(np.linalg.norm(v))
        v = v / nv * 0.12 if nv > 0.01 else np.array([0.0, 0.0, -0.12])
        up = np.array([0.0, -1.0, 0.0]); ut = np.zeros((len(LEDER), 3))
        for i, j in enumerate(LEDER):
            if j == "huvud_upp":
                ut[i] = P[hi] + up * 0.10
            elif j == "nasa_mal":
                ut[i] = P[hi] + v + up * 0.02
            elif j in ("l_hand_mitt", "r_hand_mitt"):
                s = j[0]; a, b = m.get(f"{s}_index1"), m.get(f"{s}_pinky1")
                ut[i] = 0.5 * (P[a] + P[b]) if a is not None and b is not None else P[m[f"{s}_wrist"]]
            else:
                ut[i] = P[m[j]]
        return ut

    @modal.method()
    def kor(self, video: bytes, jobb: dict, f_px: float) -> dict:
        """jobb: {ruta: [[spar_id, x0, y0, x1, y1], ...]} -> {ruta: {spar_id: 28x3}}"""
        import cv2, numpy as np, torch, tempfile
        t0 = time.perf_counter()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video); vp = f.name
        cap = cv2.VideoCapture(vp); want = {int(k) for k in jobb}; ut = {}; i = 0; H = W = None
        while want:
            ok, fr = cap.read()
            if not ok:
                break
            if i in want:
                H, W = fr.shape[:2]; rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
                K = np.array([[f_px, 0, W / 2], [0, f_px, H / 2], [0, 0, 1]], np.float32)
                rader = jobb[str(i)] if str(i) in jobb else jobb[i]
                with torch.inference_mode():
                    out = self.sam.process_one_image(rgb, bboxes=np.array([r[1:] for r in rader], np.float32), masks=None, cam_int=torch.tensor(K)[None])
                ut[i] = {r[0]: self._t1(o).round(4).tolist() for r, o in zip(rader, out or [])}
                want.discard(i)
            i += 1
        return {"leder": ut, "ladd_s": self.ladd_s, "sek": round(time.perf_counter() - t0, 1), "anrop": len(ut)}


def spara(pose, shots, W0, H0, min_andel=0.3, min_yta=0.0025):
    """IoU-spårning av posedetektioner inom varje tagning."""
    import numpy as np
    def iou(a, b):
        x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
        i = max(0, x1 - x0) * max(0, y1 - y0); u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
        return i / u if u > 0 else 0.0
    ut = {}
    for s in shots:
        a0, b0 = s["ut"]; spar = []
        for u in range(a0, b0):
            def godkand(p):  # stor beskuren person (närbild) räcker med få säkra leder; liten person kräver fler
                yta = (p["box"][2] - p["box"][0]) * (p["box"][3] - p["box"][1]) / (W0 * H0); n = sum(1 for k in p["kp"] if k[2] > 0.5)
                return yta >= min_yta and (n >= 4 or (yta >= 0.15 and n >= 2))
            det = [p for p in pose["rutor"][u]["personer"] if godkand(p)]
            tagna = set()
            for sp in sorted(spar, key=lambda z: -len(z["rutor"])):
                if sp["rutor"][-1] < u - 6:
                    continue
                best, bi = 0.3, None
                for di, d in enumerate(det):
                    if di not in tagna and iou(sp["box"], d["box"]) > best:
                        best, bi = iou(sp["box"], d["box"]), di
                if bi is not None:
                    tagna.add(bi); sp["rutor"].append(u); sp["boxar"].append(det[bi]["box"]); sp["box"] = det[bi]["box"]
            for di, d in enumerate(det):
                if di not in tagna:
                    spar.append({"rutor": [u], "boxar": [d["box"]], "box": d["box"]})
        hall = [sp for sp in spar if len(sp["rutor"]) >= min_andel * (b0 - a0)]
        ut[s["id"]] = hall
    return ut


@app.local_entrypoint()
def main(klipp: str, steg: int = 5):
    import numpy as np
    from scipy.interpolate import PchipInterpolator
    t0 = time.perf_counter(); jobb_lista = []
    for spec in klipp.split(","):
        namn, nyckel = spec.split(":")
        ut = HERE / "ut" / nyckel; meta = json.loads((ut / "obs_gpu.json").read_text(encoding="utf-8"))
        pose = json.loads((ut / "pose2d.json").read_text(encoding="utf-8")); W0, H0 = meta["bild_px"]
        # fokal: MoGe ViT-L i mittrutan per klipp (samma som lokaliteten använder utan A)
        mid = meta["tagningar"][0]["nyckelrutor"][len(meta["tagningar"][0]["nyckelrutor"]) // 2]
        import numpy as _np
        K = _np.load(ut / "obs_gpu" / f"{mid:04d}.npz")["intrinsics"]; f_px = float(K[0, 0] * W0)
        S = spara(pose, meta["tagningar"], W0, H0)
        jobb = {}; namnge = {}
        for s in meta["tagningar"]:
            for k, sp in enumerate(S[s["id"]]):
                sid_p = f"{s['id']}_p{k}"; namnge[sid_p] = sp
                for j, (u, bx) in enumerate(zip(sp["rutor"], sp["boxar"])):
                    if j % steg == 0 or j == len(sp["rutor"]) - 1:
                        jobb.setdefault(str(u), []).append([sid_p, *[float(v) for v in bx]])
        data = (ROOT / "data/format/kontroll/klipp" / (namn + ".mp4")).read_bytes()
        jobb_lista.append((namn, nyckel, meta, S, namnge, f_px, W0, H0, Kropp2().kor.spawn(data, jobb, f_px), sum(len(v) for v in jobb.values())))
        print(f"skickat {nyckel}: {sum(len(v) for v in S.values())} spår, {sum(len(v) for v in jobb.values())} personrutor, f={f_px:.0f}px", flush=True)
    for namn, nyckel, meta, S, namnge, f_px, W0, H0, fc, n in jobb_lista:
        r = fc.get(timeout=1500); led = {int(k): v for k, v in r["leder"].items()}
        # A-kompatibelt paket: fast kamera (0,0,1,38) tittande vågrätt längs +Y; världsled = C + R B(cv)
        C0 = np.array([0, 0, 1.38]); RA = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.0]]); B = np.diag([1.0, -1.0, -1.0])
        lens = f_px / W0 * 36.0; rorelse = {}; personer = {}; tagn = []
        for s in meta["tagningar"]:
            a0, b0 = s["ut"]; pers = []
            for pid, sp in namnge.items():
                if not pid.startswith(s["id"] + "_"):
                    continue
                us = [u for u in sp["rutor"] if u in led and pid in led[u]]
                if len(us) < 2:
                    continue
                X = np.array([led[u][pid] for u in us])
                full = np.arange(min(sp["rutor"]), max(sp["rutor"]) + 1)
                Xf = PchipInterpolator(us, X, axis=0)(np.clip(full, us[0], us[-1]))
                Wd = C0 + np.einsum("ij,fkj->fki", RA @ B, Xf)
                ix = {n_: i for i, n_ in enumerate(LEDER)}
                knae = []
                for sd in "lr":
                    h_, k_, a_ = Xf[:, ix[f"{sd}_upleg"]], Xf[:, ix[f"{sd}_lowleg"]], Xf[:, ix[f"{sd}_foot"]]
                    v1, v2 = h_ - k_, a_ - k_
                    knae.append(np.degrees(np.arccos(np.clip((v1 * v2).sum(1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-9), -1, 1))))
                pose_lbl = "staende" if float(np.median(np.concatenate(knae))) > 140 else "sittande"
                rorelse.setdefault(pid, []).append({"tagning": s["id"], "ut": [a0, b0], "rutor": [[int(u)] + [int(round(v * 1000)) for v in Wd[i].reshape(-1)] for i, u in enumerate(full)]})
                personer[pid] = {"roll": pid, "farg": "#4c8bf5", "hemplats": None, "pose": pose_lbl, "unik": True,
                                 "tilltro": {"overkropp": "observerad", "underkropp": "observerad"}, "status": {"identitet": "spår per tagning (IoU)", "hallning": "observerad"}}
                pers.append({"id": pid, "ankare": None})
            tagn.append({"id": s["id"], "ut": [a0, b0], "personer": pers, "klass": "person" if pers else "miljo",
                         "kamera": {"typ": "statisk", "statisk": True, "nycklar": [[a0, 0.0, 0.0, 1.38, *[round(c, 6) for c in iv2_quat(RA)], round(lens, 2)]]}})
        paket = {"schema": "scenpaket/2", "klipp": {"id": namn, "nyckel": nyckel, "ingest_v": "kropp2"}, "tidsbas": {"fps": meta["fps"], "antal_rutor": meta["antal_rutor"], "regel": "kropp2 var 5:e ruta + PCHIP"},
                 "bild": {"bredd": W0, "hojd": H0, "sensor_mm": 36.0}, "koordinater": "Blender: Z upp, meter; kvaternion (w,x,y,z); leder i hel-mm.",
                 "golv_z": 0.0, "objekt": [], "tagningar": tagn, "personer": personer, "leder": LEDER, "rorelse": rorelse}
        d = HERE / "ut" / nyckel / "kropp2"; d.mkdir(parents=True, exist_ok=True)
        tmp = d / "paket.json.tmp"; tmp.write_text(json.dumps(paket, ensure_ascii=False), encoding="utf-8"); tmp.replace(d / "paket.json")
        print(f"klar {nyckel}: {len(personer)} spår, {r['anrop']} rutor, laddning {r['ladd_s']} s, anrop {r['sek']} s", flush=True)
    print(f"totalt {round(time.perf_counter() - t0, 1)} s väggtid", flush=True)


def iv2_quat(R):
    import numpy as np, math
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    return q
