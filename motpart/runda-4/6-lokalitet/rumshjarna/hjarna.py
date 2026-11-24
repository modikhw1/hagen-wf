"""rumshjärna/1: orkestrator för genererat rum utan förgrund (V2) som hypotes i 0.0.

Bildgenerering används bara för BORTTAGNING (personer + det de håller, överlagrad text). Allt annat är hjärnans logik:
1. behov: tagningar där personen täcker >= 2 % av mittrutan (andra tagningar behöver ingen hypotes)
2. rum över tagningar (L7, geometriska bevis): i varje grupp väljs ett ankare (minst personyta). Ankarets referens är
   originalrutan om den saknar person, annars ankarets egen V2. Övriga i gruppen genereras MOT referensen (samma
   möbler, samma föremål, samma placering), så att scen 3 liknar scen 1 i stället för att varje scen bestämmer själv.
   Utan geometriska bevis: ingen koppling, oberoende generering.
3. linjering: varje bild registreras tillbaka till originalets utsnitt (ECC affin på kantbilder); misslyckas den
   märks bilden 'ej konvergerad' och lokaliteten använder den inte.
4. observation: samma MoGe/OneFormer/GeoCalib som originalet (modal_obs::bildobs)
5. andra rösten (likhet.py): geometri och utseende på V2; utseende ensamt länkar aldrig (matnärbilder liknar varandra
   oavsett plats), betingade par räknas inte (likheten är skapad av hjärnan själv). Kandidater renderas utan koppling.
Lokaliteten (lokalitet.py) avgör sedan per tagning om hypotesen får användas (djupfel, kanttrohet, linjering).

usage: python hjarna.py <nyckel> [--parallell 4] [--plan]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent; ROOT = LOK.parents[2]
sys.path.insert(0, str(LOK)); sys.path.insert(0, str(HERE))
import lokalitet as L  # noqa: E402

CX = Path.home() / '.codex'
PROMPT_V2 = (HERE / 'promptar' / 'v2_rum.txt').read_text(encoding='utf-8').strip()
PROMPT_K = (HERE / 'promptar' / 'v2_konsistent_allman.txt').read_text(encoding='utf-8').strip()
BILDINSTR = '\n\nUse your image generation tool to create the image. Reply only with "done." when the image exists.'
BEHOV = 0.02


def ruta_png(video, u, dst):
    kalla = ROOT / 'data/format/kontroll/klipp' / (video + '.mp4')
    nyckel = {'video': str(kalla.resolve()), 'ruta': int(u), 'video_sha256': L.sha(kalla)}
    sidofil = dst.with_suffix('.ruta.json')
    try:
        sparad = json.loads(sidofil.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        sparad = None
    if not dst.is_file() or sparad != nyckel:
        cap = cv2.VideoCapture(str(kalla))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, u); ok, fr = cap.read()
        finally:
            cap.release()
        if not ok or not cv2.imwrite(str(dst), fr):
            raise RuntimeError(f'Kunde inte hämta ruta {u} ur {video}')
        sidofil.write_text(json.dumps(nyckel, ensure_ascii=False), encoding='utf-8')
    return dst


def codex_bild(dst, prompt, bilder):
    """Ett bildanrop; parallellsäkert: bilden hämtas ur sessionens egen katalog (generated_images/<session-id>/)."""
    nyckel = {'prompt_sha': hashlib.sha256(prompt.encode()).hexdigest(),
              'referensbilder': [str(Path(b).resolve()) for b in bilder],
              'indata_sha256': [L.sha(b) for b in bilder]}
    if dst.is_file():
        try:
            sparad = json.loads(dst.with_suffix('.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            sparad = {}
        if all(sparad.get(k) == v for k, v in nyckel.items()):
            return sparad
        dst.replace(dst.with_suffix('.gammal.png'))
    t0 = time.time(); instr = prompt + BILDINSTR
    with tempfile.TemporaryDirectory() as d:
        cmd = [shutil.which('codex') or 'codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-C', d, '-c', 'model_reasoning_effort="low"']
        cmd += ['--image=' + str(Path(b).resolve()) for b in bilder] + ['-']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900, input=instr)
    m = re.search(r'session id:\s*([0-9a-f-]{36})', r.stderr or '')
    sid = m.group(1) if m else None
    kand = sorted((CX / 'generated_images' / sid).glob('*.png'), key=lambda p: p.stat().st_mtime) if sid else []
    fram = None
    if sid:
        sess = next(iter(CX.glob(f'sessions/*/*/*/rollout-*{sid}.jsonl')), None)
        fram = bool(sess) and prompt[:120] in sess.read_text(encoding='utf-8', errors='replace')
    post = {'exit': r.returncode, 'session': sid, 'prompt_fram': fram, 'sekunder': round(time.time() - t0, 1), 'bilder': [Path(b).name for b in bilder],
            **nyckel, 'stderr_slut': (r.stderr or '')[-400:]}
    if r.returncode == 0 and kand:
        shutil.copy(kand[-1], dst); post['kalla'] = str(kand[-1])
    dst.with_suffix('.json').write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8')
    return post


def kant(im):
    return cv2.GaussianBlur(cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 60, 160).astype(np.float32), (0, 0), 3)


def registrera(org, gen):
    gen = cv2.resize(gen, (org.shape[1], org.shape[0]), interpolation=cv2.INTER_AREA)
    try:
        W = np.eye(2, 3, dtype=np.float32)
        cc, W = cv2.findTransformECC(kant(org), kant(gen), W, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
        ut = cv2.warpAffine(gen, W, (org.shape[1], org.shape[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        giltig = cv2.warpAffine(np.ones(gen.shape[:2], np.float32), W, (org.shape[1], org.shape[0]),
                               flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0) >= 1.0
        return ut, giltig, {'linjering': 'registrerad', 'ecc': round(float(cc), 3), 'forflyttning_px': [round(float(W[0, 2]), 1), round(float(W[1, 2]), 1)],
                    'skala': round(float(np.sqrt(abs(np.linalg.det(W[:, :2])))), 3)}
    except cv2.error:
        return gen, np.zeros(org.shape[:2], bool), {'linjering': 'ej konvergerad'}


def valj_kandidat(bud):
    med = lambda b: b[1]['rest']['median_px'] if b[1].get('rest') else float('inf')
    obe = [b for b in bud if b[1]['konsistens'] == 'oberoende']
    ank = [b for b in bud if b[1]['konsistens'] != 'oberoende' and med(b) <= 2.0]
    if ank:
        val = min(ank, key=med)
        if not obe or med(val) <= med(min(obe, key=med)) + 0.5:
            return val, 'ankarbetingad: liten förskjutning'
    tillatna = obe + ank if obe else bud
    return min(tillatna, key=med), 'minst förskjutning' if len(bud) > 1 else 'enda kandidaten'


def observera_bilder(fyll, ids, bredd, hojd):
    """Behåll tidigare observationer tills ett komplett nytt resultat har validerats."""
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    with tempfile.TemporaryDirectory(prefix='rumshjarna-obs-') as td:
        stage = Path(td)
        for s in ids:
            shutil.copyfile(fyll / f'{s}_v2.png', stage / f'{s}_v2.png')
        try:
            r = subprocess.run([str(ROOT / 'scen/.venv/Scripts/modal.exe'), 'run', str(LOK / 'modal_obs.py') + '::bildobs',
                                '--katalog', str(stage), '--bredd', str(bredd), '--hojd', str(hojd)],
                               capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=1200)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f'Modal bildobs kunde inte slutföras: {e}') from e
        if r.returncode != 0:
            raise RuntimeError(f'Modal bildobs misslyckades (returkod {r.returncode}):\n{r.stderr}\n{r.stdout}')
        for s in ids:
            png = stage / f'{s}_v2.png'; obs = stage / f'{s}_v2.obs.npz'
            png_tid = max(png.stat().st_mtime_ns, (fyll / png.name).stat().st_mtime_ns)
            if not obs.is_file() or obs.stat().st_mtime_ns <= png_tid:
                raise RuntimeError(f'Modal bildobs: {obs.name} saknas eller är inte nyare än sin png.\n{r.stderr}')
            try:
                with np.load(obs) as z:
                    if z['depth'].shape != (hojd // 2, bredd // 2) or z['mask'].shape != z['depth'].shape:
                        raise RuntimeError(f'Modal bildobs: fel form i {obs.name}: {z["depth"].shape}')
            except (OSError, ValueError, KeyError) as e:
                raise RuntimeError(f'Modal bildobs: ogiltig observation {obs.name}: {e}') from e
        if not (stage / 'etiketter.json').is_file():
            raise RuntimeError('Modal bildobs: etiketter.json saknas')
        for s in ids:
            # Samma validerade bytes kopieras till målfilens disk före atomiskt byte.
            dst = fyll / f'{s}_v2.obs.npz'; tmp = dst.with_suffix('.tmp')
            shutil.copyfile(stage / dst.name, tmp); tmp.replace(dst)
        shutil.copyfile(stage / 'etiketter.json', fyll / 'etiketter.json')
    return r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('nyckel'); ap.add_argument('--parallell', type=int, default=4); ap.add_argument('--plan', action='store_true')
    a = ap.parse_args()
    out = LOK / 'ut' / a.nyckel; d = LOK / 'ut' / 'rumshjarna' / a.nyckel; gen = d / 'gen'; fyll = d / 'fyllnad'
    gen.mkdir(parents=True, exist_ok=True); fyll.mkdir(parents=True, exist_ok=True)
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8')); rep = json.loads((out / 'lokalitet.json').read_text(encoding='utf-8'))
    gk = L.gruppkarta(meta['etiketter']); video = meta['klipp']
    bredd, hojd = meta['bild_px']
    # 1. behov per tagning
    tag = {}; pmask = {}
    for t in meta['tagningar']:
        u = t['nyckelrutor'][len(t['nyckelrutor']) // 2]; o = L.ladda(out, u, gk, 'obs_gpu')
        pers = np.isin(o['I'], [i for i, l in o['segs'].items() if gk.get(l) == 'person']) if 'I' in o else o['G'] == 'person'
        tag[t['id']] = {'ruta': u, 'personandel': round(float(pers.mean()), 3), 'behov': bool(pers.mean() >= BEHOV)}; pmask[t['id']] = pers
        ruta_png(video, u, d / f"{t['id']}_orig.png")
    # 2. plan: ankare per rumsgrupp (L7), referens = originalruta utan person, annars ankarets V2
    grupper = rep.get('rum_over_tagningar', {}).get('grupper', [])
    i_grupp = {s: g for g in grupper for s in g}
    fas1, fas2 = [], []
    for g in grupper:
        ank = min(g, key=lambda s: tag[s]['personandel'])
        for s in g:
            tag[s]['grupp'] = sorted(g, key=lambda x: int(x[1:])); tag[s]['ankare'] = ank
        ref = d / f'{ank}_orig.png' if not tag[ank]['behov'] else gen / f'{ank}_v2.png'
        if tag[ank]['behov']:
            fas1.append((ank, None))
        for s in g:
            if s != ank and tag[s]['behov']:
                fas2.append((s, (ank, ref))); fas1.append((s, None))  # båda kandidaterna; valet görs på uppmätt förskjutning
    for s, v in tag.items():
        if v['behov'] and s not in i_grupp:
            fas1.append((s, None))
    plan = {'behov_tröskel': BEHOV, 'tagningar': tag, 'fas1_oberoende': [s for s, _ in fas1], 'fas2_mot_ankare': {s: r[0] for s, r in fas2}}
    (d / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    print('plan', a.nyckel, 'oberoende', plan['fas1_oberoende'], 'mot ankare', plan['fas2_mot_ankare'], flush=True)
    if a.plan:
        return

    def gor(job):
        s, ref = job
        src = d / f'{s}_orig.png'
        if ref is None:
            return s, codex_bild(gen / f'{s}_v2.png', PROMPT_V2, [src]), gen / f'{s}_v2.png', 'oberoende'
        ank, rfil = ref
        dst = gen / f'{s}_v2_k{ank}.png'
        return s, codex_bild(dst, PROMPT_K, [src, rfil]), dst, f'mot ankare {ank} ({"originalruta" if rfil.name.endswith("_orig.png") else "ankarets V2"})'
    t0 = time.time(); logg = {}
    for fas in (fas1, fas2):
        with ThreadPoolExecutor(a.parallell) as ex:
            for s, post, dst, kons in ex.map(gor, fas):
                logg.setdefault(s, []).append({'post': post, 'fil': dst, 'konsistens': kons})
                print(s, 'klar' if dst.is_file() else 'MISSLYCKAD', post.get('sekunder'), flush=True)
    # 3. linjering tillbaka till eget utsnitt
    # Gemini-granskningen 21 nov: alla 8 falskt släppta var ankarbetingade (perspektivskifte, inklistrat ankarinnehåll).
    # Ankarbetingad kandidat väljs bara om dess lokala förskjutning är liten och inte sämre än den oberoende.
    from rest import rest_px
    fl = {}
    for s, kand in logg.items():
        org = cv2.imread(str(d / f'{s}_orig.png'))
        if org is None or org.shape[:2] != (hojd, bredd):
            raise RuntimeError(f'{s}: originalets bildform stämmer inte med {bredd}×{hojd}')
        pm = cv2.resize(pmask[s].astype(np.uint8), (org.shape[1], org.shape[0]), interpolation=cv2.INTER_NEAREST)
        synlig = ~cv2.dilate(pm, np.ones((31, 31), np.uint8)).astype(bool)
        bud = []
        for v in kand:
            if not v['fil'].is_file():
                continue
            reg, giltig, info = registrera(org, cv2.imread(str(v['fil'])))
            info['rest'] = rest_px(org, reg, synlig & giltig) if info['linjering'] == 'registrerad' else None
            bud.append((reg, {'kalla': v['fil'].name, 'konsistens': v['konsistens'], **info, 'sekunder': v['post'].get('sekunder'), 'prompt_fram': v['post'].get('prompt_fram')}, giltig))
        if not bud:
            continue
        val, skal = valj_kandidat(bud)
        cv2.imwrite(str(fyll / f'{s}_v2.png'), val[0])
        cv2.imwrite(str(fyll / f'{s}_v2_giltig.png'), val[2].astype(np.uint8) * 255)
        fl[s] = {**val[1], 'val': skal, 'kandidater': [{k_: b[1].get(k_) for k_ in ('kalla', 'linjering', 'rest')} for b in bud]}
    (fyll / 'fyllnad.json').write_text(json.dumps(fl, ensure_ascii=False, indent=1), encoding='utf-8')
    gen_s = round(time.time() - t0, 1)
    # 4. observation på Modal (samma modeller som originalet)
    t1 = time.time()
    r = observera_bilder(fyll, list(fl), bredd, hojd)
    obs_s = round(time.time() - t1, 1)
    # 5. andra rösten om samma plats (likhet.py: geometri på V2, utseende, cirkularitet borträknad)
    import likhet
    likhet.main(a.nyckel)
    res = {'plan': plan, 'fyllnad': fl, 'tid_s': {'generering': gen_s, 'observation': obs_s}, 'modal_ok': r.returncode == 0}
    (d / 'hjarna.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('tid_s', 'modal_ok')}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
