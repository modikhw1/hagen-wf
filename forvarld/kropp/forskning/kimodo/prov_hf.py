"""Prov: har Modal-hemligheten 'huggingface' åtkomst till Kimodos gated textkodare? Skriver bara status, aldrig token."""
import modal
app = modal.App('hagen-kimodo-prov')
img = modal.Image.debian_slim(python_version='3.11').pip_install('huggingface_hub>=0.25')

@app.function(image=img, secrets=[modal.Secret.from_name('huggingface')], timeout=120)
def prov():
    import os
    from huggingface_hub import HfApi, hf_hub_download
    tok = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
    ut = {'token_finns': bool(tok), 'nycklar': sorted(k for k in os.environ if 'HF' in k or 'HUGG' in k)}
    api = HfApi(token=tok)
    try: ut['konto'] = 'ok' if api.whoami() else '?'
    except Exception as e: ut['konto'] = type(e).__name__
    for rid, fil in (('meta-llama/Meta-Llama-3-8B-Instruct', 'config.json'), ('meta-llama/Llama-3.1-8B-Instruct', 'config.json')):
        try:
            if fil: hf_hub_download(rid, fil, token=tok); ut[rid] = 'nedladdning ok'
            else: ut[rid] = [f.rfilename for f in api.model_info(rid).siblings][:20]
        except Exception as e: ut[rid] = f'{type(e).__name__}: {str(e)[:160]}'
    return ut

@app.local_entrypoint()
def main():
    import json; print(json.dumps(prov.remote(), ensure_ascii=False, indent=1))
