"""Engångsmigrering 21 nov: fyll i hjarna.py:s nya cachenyckel (full prompt_sha, referensbilder, indata_sha256) för bilder
som redan genererats, MEN bara där den gamla metadatan visar samma prompt (prompt_sha[:12] eller promptens text) och samma
referensbilder (filnamn). Annat lämnas orört och genereras om av hjarna.py. Märks 'migrerad': true."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LOK = HERE.parent
sys.path.insert(0, str(LOK)); sys.path.insert(0, str(HERE))
import hjarna as H  # noqa: E402
import lokalitet as L  # noqa: E402


def main(nyckel):
    d = LOK / 'ut' / 'rumshjarna' / nyckel; gen = d / 'gen'
    meta = json.loads((LOK / 'ut' / nyckel / 'obs_gpu.json').read_text(encoding='utf-8'))
    for t in meta['tagningar']:
        if (d / f"{t['id']}_orig.png").is_file():
            H.ruta_png(meta['klipp'], t['nyckelrutor'][len(t['nyckelrutor']) // 2], d / f"{t['id']}_orig.png")
    n_ok = n_hopp = 0
    for png in sorted(gen.glob('s*_v2*.png')):
        if png.name.endswith('.gammal.png'):
            continue
        js = png.with_suffix('.json'); post = json.loads(js.read_text(encoding='utf-8')) if js.is_file() else {}
        if 'referensbilder' in post:
            continue
        prompt = H.PROMPT_K if '_k' in png.stem else H.PROMPT_V2
        sha = hashlib.sha256(prompt.encode()).hexdigest()
        samma_prompt = post.get('prompt_sha') == sha[:12] or str(post.get('prompt', '')).startswith(prompt[:200])
        namn = post.get('bilder') or []
        namn = [Path(n).name for n in namn]
        refs = [(d / n) if n.endswith('_orig.png') else (gen / n) for n in namn]
        if not samma_prompt or not refs or not all(r.is_file() for r in refs) or Path(namn[0]).name != f"{png.stem.split('_')[0]}_orig.png":
            print('hoppar', nyckel, png.name, 'prompt' if not samma_prompt else 'referenser'); n_hopp += 1
            continue
        post.update({'prompt_sha': sha, 'referensbilder': [str(r.resolve()) for r in refs], 'indata_sha256': [L.sha(r) for r in refs], 'migrerad': True})
        js.write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8'); n_ok += 1
    print(nyckel, 'migrerade', n_ok, 'hoppade', n_hopp)


if __name__ == '__main__':
    for k in sys.argv[1:]:
        main(k)
