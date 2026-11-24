"""rumshjärna/1: kör promptvarianterna V1-V3 per nyckelruta genom Codex image_gen (codex_bild.py, en session per bild).
  scen/.venv/Scripts/python.exe generera.py <klipp-nyckel> <videonamn> <tagning:ruta,...> [variant,...]
Skriver ut/rumshjarna/<nyckel>/<tagning>_<variant>.png + .codex.json (prompt, kvot före/efter, tid). Hoppar över befintliga.
"""
import sys, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scen/3d/gennedbrytning'))
import codex_bild  # noqa: E402

# Låg resonemangsnivå för bildanrop (bildmodellen gör jobbet; sparar Codex-kvot). Den delade wrappern lämnas orörd.
_orig_run = codex_bild.subprocess.run
def _run(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and cmd[1] == 'exec':
        cmd = cmd[:2] + ['-c', 'model_reasoning_effort="low"'] + cmd[2:]
    return _orig_run(cmd, *a, **k)
codex_bild.subprocess.run = _run

def main():
    nyckel, video, lista = sys.argv[1], sys.argv[2], sys.argv[3]
    varianter = sys.argv[4].split(',') if len(sys.argv) > 4 else ['v1_pipe', 'v2_rum', 'v3_essens']
    ut = HERE.parent / 'ut' / 'rumshjarna' / nyckel; ut.mkdir(parents=True, exist_ok=True)
    for spec in lista.split(','):
        sid, ruta = spec.split(':'); src = ut / f'{sid}_orig.png'
        if not src.exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ROOT / 'data/format/kontroll/klipp' / (video + '.mp4')), '-vf', f"select='eq(n\,{ruta})'", '-frames:v', '1', '-fps_mode', 'passthrough', str(src)], check=True)
        for v in varianter:
            dst = ut / f'{sid}_{v}.png'
            if dst.exists():
                continue
            prompt = (HERE / 'promptar' / f'{v}.txt').read_text(encoding='utf-8')
            try:
                codex_bild.generera(dst, prompt, [src])
                print('klar', dst.name, flush=True)
            except Exception as e:
                print('fel', dst.name, repr(e)[:200], flush=True)

if __name__ == '__main__':
    main()
