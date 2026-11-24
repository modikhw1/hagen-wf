"""Wan2.1-VACE-14B på Modal, en varm container för en lista av jobb.

Vikterna hämtas en gång till Volume ``lasformat-wan21-vace``. Kör från
projektroten med venvens Modal-klient; alla lokala utdata ska ligga under
lasformat/.
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import time
from pathlib import Path

import modal


MODEL_ID = "Wan-AI/Wan2.1-VACE-14B-diffusers"
MODEL_REVISION = "db79b90c60bbb45ceec9e41b9d5a4df934538ac4"
MODEL_DIR = "/models/Wan2.1-VACE-14B-diffusers"
GPU_RATE_USD_S = 0.000694  # Modal A100-80, verifierad prissida 2026-11-11.

app = modal.App("hagen-lasformat-vace")
volume = modal.Volume.from_name("lasformat-wan21-vace", create_if_missing=True)
secret = modal.Secret.from_name("huggingface")
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.7.1",
        "torchvision==0.22.1",
        index_url="https://download.pytorch.org/whl/cu128",
    )
    .pip_install(
        "diffusers==0.35.2",
        "transformers==4.56.2",
        "accelerate==1.10.1",
        "huggingface_hub[hf_transfer]==0.35.0",
        "safetensors",
        "sentencepiece",
        "ftfy",
        "opencv-python-headless",
        "imageio[ffmpeg]",
        "numpy<2.3",
    )
)


@app.function(image=image, volumes={"/models": volume}, secrets=[secret], timeout=7200)
def hamta_vikter() -> dict:
    from huggingface_hub import snapshot_download

    marker = Path(MODEL_DIR) / ".complete"
    if marker.exists():
        return {"downloaded": False, "model": MODEL_ID, "revision": MODEL_REVISION}
    t0 = time.perf_counter()
    snapshot_download(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=MODEL_DIR,
        token=os.environ.get("HF_TOKEN"),
    )
    marker.write_text(MODEL_REVISION + "\n")
    volume.commit()
    return {"downloaded": True, "seconds": time.perf_counter() - t0, "model": MODEL_ID, "revision": MODEL_REVISION}


@app.cls(
    image=image,
    gpu="A100-80GB",
    volumes={"/models": volume},
    secrets=[secret],
    timeout=7200,
    scaledown_window=900,
    max_containers=1,
)
class VaceBatch:
    @modal.enter()
    def ladda(self) -> None:
        import torch
        from diffusers import AutoencoderKLWan, WanVACEPipeline
        from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler

        self.load_started = time.perf_counter()
        torch.backends.cuda.matmul.allow_tf32 = True
        vae = AutoencoderKLWan.from_pretrained(MODEL_DIR, subfolder="vae", torch_dtype=torch.float32, local_files_only=True)
        self.pipe = WanVACEPipeline.from_pretrained(
            MODEL_DIR,
            vae=vae,
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config, flow_shift=3.0)
        self.pipe.to("cuda")
        if hasattr(self.pipe, "enable_vae_tiling"):
            self.pipe.enable_vae_tiling()
        if hasattr(self.pipe, "enable_vae_slicing"):
            self.pipe.enable_vae_slicing()
        self.load_seconds = time.perf_counter() - self.load_started

    @modal.method()
    def kor(self, video_bytes: bytes, mask_bytes: bytes, jobs: list[dict]) -> dict:
        import cv2
        import numpy as np
        import torch
        from PIL import Image
        from diffusers.utils import export_to_video

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "condition.mp4"
            source.write_bytes(video_bytes)
            cap = cv2.VideoCapture(str(source))
            frames = []
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            cap.release()
            masks = np.load(io.BytesIO(mask_bytes))["mask"]
            mask_images = [Image.fromarray(m.astype(np.uint8), mode="L") for m in masks]
            if len(frames) != 49 or len(mask_images) != 49:
                raise RuntimeError(f"Oväntade VACE-indata: video={len(frames)}, mask={len(mask_images)}")

            results = []
            for job in jobs:
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                started = time.perf_counter()
                generator = torch.Generator(device="cuda").manual_seed(int(job["seed"]))
                with torch.inference_mode():
                    output = self.pipe(
                        video=frames,
                        mask=mask_images,
                        prompt=job["prompt"],
                        negative_prompt=job["negative_prompt"],
                        height=832,
                        width=480,
                        num_frames=49,
                        num_inference_steps=int(job.get("num_inference_steps", 30)),
                        guidance_scale=float(job.get("guidance_scale", 5.0)),
                        conditioning_scale=float(job.get("conditioning_scale", 1.0)),
                        generator=generator,
                    ).frames[0]
                seconds = time.perf_counter() - started
                output_path = Path(td) / f"{job['id']}.mp4"
                export_to_video(output, str(output_path), fps=16)
                results.append(
                    {
                        "id": job["id"],
                        "format": job["format"],
                        "seed": job["seed"],
                        "seconds": seconds,
                        "estimated_gpu_usd": seconds * GPU_RATE_USD_S,
                        "peak_vram_gb": torch.cuda.max_memory_allocated() / 1024**3,
                        "video": output_path.read_bytes(),
                    }
                )
            return {
                "model": MODEL_ID,
                "revision": MODEL_REVISION,
                "gpu": torch.cuda.get_device_name(0),
                "load_seconds": self.load_seconds,
                "load_estimated_gpu_usd": self.load_seconds * GPU_RATE_USD_S,
                "results": results,
            }


@app.local_entrypoint()
def main(condition: str, mask: str, jobs: str, ut: str) -> None:
    download = hamta_vikter.remote()
    job_list = json.loads(Path(jobs).read_text(encoding="utf-8"))
    result = VaceBatch().kor.remote(Path(condition).read_bytes(), Path(mask).read_bytes(), job_list)
    out = Path(ut)
    out.mkdir(parents=True, exist_ok=True)
    serializable = {k: v for k, v in result.items() if k != "results"}
    serializable["download"] = download
    serializable["results"] = []
    for item in result["results"]:
        video = item.pop("video")
        path = out / f"{item['id']}_raw_16fps.mp4"
        path.write_bytes(video)
        serializable["results"].append({**item, "video": str(path)})
        print(json.dumps(serializable["results"][-1], ensure_ascii=False), flush=True)
    (out / "modal_result.json").write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({k: v for k, v in serializable.items() if k != "results"}, ensure_ascii=False), flush=True)

