"""0019: bildgenerering genom Codex CLI på ägarens plan (image_generation-verktyget), ett anrop per bild.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/codex_bild.py <ut.png> <prompt.txt> <bild1> [<bild2> ...]
Prompt, Codex sista meddelande, sessionens id, väggtid och kvoten (rate_limits) före och efter sparas i <ut>.codex.json.
Bilden hämtas ur ~/.codex/generated_images (nyaste filen efter anropets start). Kör aldrig om en befintlig <ut.png>.
"""
import json, shutil, subprocess, sys, time, tempfile
from pathlib import Path

CX = Path.home() / '.codex'


def kvot():
    f = max(CX.glob('sessions/*/*/*/rollout-*.jsonl'), key=lambda p: p.stat().st_mtime)
    rad = None
    for r in f.read_text(encoding='utf-8', errors='replace').splitlines():
        if '"rate_limits"' in r and '"used_percent"' in r: rad = r
    if not rad: return dict(fil=f.name, kvot=None)
    rl = json.loads(rad)
    def hitta(o):
        if isinstance(o, dict):
            if 'rate_limits' in o: return o['rate_limits']
            for v in o.values():
                x = hitta(v)
                if x: return x
    r = hitta(rl) or {}
    return dict(fil=f.name, primar=r.get('primary'), sekundar=r.get('secondary'))


def generera(ut, prompt, bilder):
    ut = Path(ut)
    if ut.exists(): raise FileExistsError(ut)
    fore = kvot(); t0 = time.time(); start = time.time()
    import os
    raa = os.environ.get('CODEX_RAA') == '1'   # 0020: prompten som den står, inga tillägg från omslaget, inga MCP-servrar
    instr = prompt.strip() if raa else (prompt.strip() + '\n\nUse your image generation tool to produce exactly one image for this request, using the attached images as the inputs named above '
             '(image 1, image 2, ... in the order attached). Do not write code, do not edit files, do not describe alternatives. '
             'This is a non-interactive run: nobody can answer questions, so do not acknowledge or ask; call the image generation tool now, in this turn. After generating, reply with one line: done.')
    with tempfile.TemporaryDirectory() as d:
        sist = Path(d) / 'sista.txt'
        cmd = [shutil.which('codex') or 'codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-C', d, '-o', str(sist)] + (['-c', 'mcp_servers={}'] if raa else [])
        for b in bilder: cmd += ['--image=' + str(Path(b).resolve())]   # inte '-i a b': -i tar flera värden och slukar '-'
        # 13 nov: prompten går på stdin ('-'). Som argument klipper codex.CMD (cmd.exe) den vid första radbrytningen.
        cmd += ['-']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900, shell=False, input=instr)
        svar = sist.read_text(encoding='utf-8', errors='replace') if sist.exists() else ''
    # kontroll: vad kom fram som användarens text i sessionen
    try:
        sess = max(CX.glob('sessions/*/*/*/rollout-*.jsonl'), key=lambda p: p.stat().st_mtime)
        fram = ''
        for rad in sess.read_text(encoding='utf-8', errors='replace').splitlines():
            o = json.loads(rad); pl = o.get('payload', {})
            if pl.get('type') == 'message' and pl.get('role') == 'user':
                fram = ''.join(c.get('text', '') for c in pl.get('content', []) if c.get('type') == 'input_text' and not c.get('text', '').startswith(('<image', '</image', '<environment')))
        prompt_fram = dict(session=sess.name, tecken_skickade=len(instr), tecken_fram=len(fram), hel=" ".join(fram.split()) == " ".join(instr.split()))
    except Exception as e:
        prompt_fram = dict(fel=str(e)[:200])
    nya = [p for p in (CX / 'generated_images').rglob('*') if p.is_file() and p.stat().st_mtime >= start - 1]
    post = dict(prompt=instr, bilder=[str(b) for b in bilder], exit=r.returncode, svar=svar[-2000:], stderr_slut=r.stderr[-1500:],
                genererade=[str(p) for p in nya], sekunder=round(time.time() - t0, 1), kvot_fore=fore, kvot_efter=kvot(), prompt_fram=prompt_fram)
    if nya:
        src = max(nya, key=lambda p: p.stat().st_mtime); ut.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, ut); post['bild'] = str(ut)
    Path(str(ut) + '.codex.json').write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8')
    return post


if __name__ == '__main__':
    ut, pf, *b = sys.argv[1:]
    p = generera(ut, Path(pf).read_text(encoding='utf-8'), b)
    print(json.dumps({k: p[k] for k in ('exit', 'sekunder', 'genererade', 'prompt_fram', 'kvot_efter')}, ensure_ascii=False)[:1500])
