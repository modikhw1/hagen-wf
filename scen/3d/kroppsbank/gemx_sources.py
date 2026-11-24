"""Fetch small primary sources only. No weights and no inference."""
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'kallor'
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'hagen-gemx-evaluation'}), timeout=60) as r:
        return r.read()

commit = json.loads(fetch('https://api.github.com/repos/NVlabs/GEM-X/commits/main'))['sha']
files = ['pyproject.toml', 'requirements.txt', 'gem/common/detectors.py',
         'gem/inference/geometry.py', 'gem/inference/postprocess.py',
         'gem/inference/motion_geometry.py', 'gem/inference/cli.py',
         'gem/inference/video.py', 'gem/inference/body_video.py',
         'gem/inference/camera_motion.py', 'docs/INSTALL.md', 'ATTRIBUTIONS.md']
record = {'gem_sha': commit, 'sources': {}}
for name in files:
    url = f'https://raw.githubusercontent.com/NVlabs/GEM-X/{commit}/{name}'
    try:
        data = fetch(url)
    except Exception as e:
        print(name, type(e).__name__)
        continue
    target = OUT / ('gemx_live_' + name.replace('/', '_'))
    target.write_bytes(data)
    record['sources'][name] = url
for repo, revision in [('nvidia/GEM-X', 'main'), ('nvidia/SOMA-X', 'v0.3.3')]:
    data = json.loads(fetch(f'https://huggingface.co/api/models/{repo}/revision/{revision}'))
    record[repo] = {'sha': data['sha'], 'gated': data.get('gated'),
                    'files': [x['rfilename'] for x in data['siblings']]}
(OUT / 'gemx_verified.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: v if k == 'gem_sha' else {'sha': v['sha'], 'gated': v['gated']} for k,v in record.items() if k != 'sources'}))
