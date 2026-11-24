import modal
app = modal.App('hagen-kimodo-prov2')
img = modal.Image.debian_slim(python_version='3.11').pip_install('huggingface_hub>=0.25')
@app.function(image=img, secrets=[modal.Secret.from_name('huggingface')], timeout=120)
def prov():
    import os; from huggingface_hub import HfApi
    w = HfApi(token=os.environ['HF_TOKEN']).whoami(); a = (w.get('auth') or {}).get('accessToken') or {}
    fg = a.get('fineGrained') or {}
    return {'konto': w.get('name'), 'roll': a.get('role'), 'globala_rattigheter': fg.get('global'), 'scoped': [s.get('permissions') for s in fg.get('scoped', [])][:5]}
@app.local_entrypoint()
def main():
    print(prov.remote())
