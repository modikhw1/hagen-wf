"""Prov: har HF-kontot åtkomst till SAM 3.1, och vilken kodväg finns? Skriver bara metadata (inga vikter laddas här)."""
import modal

app = modal.App("hagen-sam3-prov")
img = modal.Image.debian_slim(python_version="3.11").pip_install("huggingface_hub>=0.30", "transformers")


@app.function(image=img, secrets=[modal.Secret.from_name("huggingface")], timeout=300)
def prov():
    import os, importlib, transformers
    from huggingface_hub import HfApi
    api = HfApi(token=os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"))
    ut = {"transformers": transformers.__version__, "har_Sam3Model": hasattr(importlib.import_module("transformers"), "Sam3Model")}
    for rid in ("facebook/sam3.1", "facebook/sam3"):
        try:
            info = api.model_info(rid, files_metadata=False)
            ut[rid] = {"gated": getattr(info, "gated", None), "filer": [s.rfilename for s in (info.siblings or [])][:25]}
            try:
                p = api.hf_hub_download(rid, "config.json") if any(s.rfilename == "config.json" for s in info.siblings or []) else None
                ut[rid]["nedladdning_ok"] = bool(p)
            except Exception as e:  # noqa: BLE001
                ut[rid]["nedladdning_fel"] = str(e)[:200]
        except Exception as e:  # noqa: BLE001
            ut[rid] = {"fel": str(e)[:300]}
    return ut


@app.local_entrypoint()
def main():
    import json
    print(json.dumps(prov.remote(), ensure_ascii=False, indent=1))
