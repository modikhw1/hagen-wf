"""Read-only inventory of already downloaded weights; no GPU or gated downloads."""
import json
from pathlib import Path
import modal

app = modal.App('kroppsbank-preflight')
vol = modal.Volume.from_name('sam3db-vikter', create_if_missing=False)

@app.function(image=modal.Image.debian_slim(python_version='3.11'),
              volumes={'/vikter': vol}, timeout=90, max_containers=1)
def inventory():
    return [{'path': str(p), 'bytes': p.stat().st_size}
            for p in Path('/vikter').rglob('*')
            if p.is_file() and p.name in ('model.ckpt', 'mhr_model.pt', 'model_config.yaml')]

@app.local_entrypoint()
def main():
    result = inventory.remote()
    out = Path(__file__).resolve().parent / 'preflight.json'
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
