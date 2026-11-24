"""Small read-only network audit; saves primary source text only inside this bank."""
import concurrent.futures, datetime, hashlib, json, urllib.request
from pathlib import Path

BANK = Path(__file__).resolve().parent
SOURCES = {
 'map_readme':'https://raw.githubusercontent.com/facebookresearch/map-anything/main/README.md',
 'map_license':'https://raw.githubusercontent.com/facebookresearch/map-anything/main/LICENSE',
 'map_pyproject':'https://raw.githubusercontent.com/facebookresearch/map-anything/main/pyproject.toml',
 'map_model':'https://huggingface.co/facebook/map-anything-apache/raw/main/README.md',
 'map_model_license':'https://huggingface.co/facebook/map-anything-apache/raw/main/LICENSE',
 'vipe_readme':'https://raw.githubusercontent.com/nv-tlabs/vipe/main/README.md',
 'vipe_license':'https://raw.githubusercontent.com/nv-tlabs/vipe/main/LICENSE',
 'vipe_thirdparty':'https://raw.githubusercontent.com/nv-tlabs/vipe/main/THIRD_PARTY_LICENSES.md',
 'vipe_install':'https://raw.githubusercontent.com/nv-tlabs/vipe/main/docs/installation.md',
 'vipe_pyproject':'https://raw.githubusercontent.com/nv-tlabs/vipe/main/pyproject.toml',
 'mega_readme':'https://raw.githubusercontent.com/mega-sam/mega-sam/main/README.md',
 'mega_license':'https://raw.githubusercontent.com/mega-sam/mega-sam/main/LICENSE',
 'da3_readme':'https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/main/README.md',
 'da3_license':'https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/main/LICENSE',
 'da3_pyproject':'https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/main/pyproject.toml',
 'vggt_readme':'https://raw.githubusercontent.com/facebookresearch/vggt/main/README.md',
 'vggt_license':'https://raw.githubusercontent.com/facebookresearch/vggt/main/LICENSE.txt',
 'vggt_commercial':'https://huggingface.co/facebook/VGGT-1B-Commercial/raw/main/README.md',
 'vggt_omega_license':'https://raw.githubusercontent.com/facebookresearch/vggt-omega/main/LICENSE',
 'pi3_readme':'https://raw.githubusercontent.com/yyfz/Pi3/main/README.md',
 'pi3_license':'https://raw.githubusercontent.com/yyfz/Pi3/main/LICENSE',
 'pi3_model':'https://huggingface.co/yyfz233/Pi3/raw/main/README.md',
 'mast3r_license':'https://raw.githubusercontent.com/naver/mast3r/main/LICENSE',
 'mast3r_slam_license':'https://raw.githubusercontent.com/rmurai0610/MASt3R-SLAM/main/LICENSE',
 'dust3r_license':'https://raw.githubusercontent.com/naver/dust3r/main/LICENSE',
 'unidepth_license':'https://raw.githubusercontent.com/lpiccinelli-eth/UniDepth/main/LICENSE',
 'unidepth_model':'https://huggingface.co/lpiccinelli/unidepth-v1-vitl14/raw/main/README.md',
 'dvlt_readme':'https://raw.githubusercontent.com/nv-tlabs/dvlt/main/README.md',
 'dvlt_weights_license':'https://raw.githubusercontent.com/nv-tlabs/dvlt/main/LICENSES/NVIDIA-LICENSE.txt',
}

def fetch(item):
 name,url=item; dest=BANK/'sources'/f'{name}.txt'; dest.parent.mkdir(exist_ok=True)
 try:
  with urllib.request.urlopen(url,timeout=45) as r: data=r.read()
  dest.write_bytes(data)
  return name,dict(url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),path=str(dest.relative_to(BANK)))
 except Exception as e:return name,dict(url=url,error=str(e))

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=dict(pool.map(fetch,SOURCES.items()))
 (BANK/'sources/index.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=results),indent=2),encoding='utf-8')
 print(json.dumps({k:v.get('bytes',v.get('error')) for k,v in results.items()},indent=2))
