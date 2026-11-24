"""FORSKNING (0039): varm MaskedMimic-arbetare med kompatibel kor-funktion.

Utplacera från projektroten med PYTHONIOENCODING=utf-8 PYTHONUTF8=1:
  scen/.venv/Scripts/python.exe -m modal deploy forvarld/kropp/forskning/mm/tjanst.py
"""
import sys
from pathlib import Path
import modal

if modal.is_local():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from modal_mm import image as basbild
    image = basbild.add_local_file(str(Path(__file__).resolve().parent / 'arbetare.py'), '/opt/mm/arbetare.py')
else:
    image = None

app = modal.App('hagen-mm-tjanst')


@app.cls(image=image, gpu=['L4', 'A10G', 'T4'], timeout=900, startup_timeout=900,
         memory=16384, scaledown_window=1200, max_containers=6)
@modal.concurrent(max_inputs=1)
class VarmKroppSlutlig:
    @modal.enter()
    def starta(self):
        self._starta_arbetare()

    def _miljo(self):
        import os
        env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
        env.update(PYTHONPATH='/opt/mm:/opt/protomotions:/opt/isaacgym/python',
                   LD_LIBRARY_PATH=os.environ['IG_LD'] + ':' + os.environ.get('LD_LIBRARY_PATH', ''),
                   PYTHONUNBUFFERED='1')
        return env

    def _starta_arbetare(self):
        import subprocess, tempfile
        gammal = getattr(self, 'arbetare', None)
        if gammal is not None and gammal.poll() is None:
            gammal.kill(); gammal.wait(timeout=10)
        fel = getattr(self, 'arbetsfel', None)
        if fel is not None:
            fel.close()
        self.arbetsfel = tempfile.TemporaryFile(mode='w+', encoding='utf-8')
        self.arbetare = subprocess.Popen(['/usr/bin/python3.8', '-u', '/opt/mm/arbetare.py'], cwd='/opt/protomotions',
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.arbetsfel,
                                         text=True, encoding='utf-8', bufsize=1, env=self._miljo())
        self.startkod = Path('/opt/mm/kor_mm.py').read_text(encoding='utf-8')

    def _stoppa_arbetare(self):
        gammal = getattr(self, 'arbetare', None)
        if gammal is not None and gammal.poll() is None:
            gammal.kill(); gammal.wait(timeout=10)

    def _feltext(self):
        self.arbetsfel.flush(); self.arbetsfel.seek(0)
        text = self.arbetsfel.read()[-12000:]
        self.arbetsfel.seek(0, 2)
        return text

    def _gammal_vag(self, d, inn, villkor, kod):
        import subprocess, time
        fil = '/opt/mm/kor_mm.py'
        if kod and kod != self.startkod:
            fil = str(d / 'kor_mm.py'); Path(fil).write_text(kod, encoding='utf-8')
        r = subprocess.run(['/usr/bin/python3.8', fil, str(d / 'in.npz'), str(d / 'ut.npz'), str(d / 'v.json')],
                           cwd='/opt/protomotions', capture_output=True, text=True, encoding='utf-8',
                           errors='replace', env=self._miljo(), timeout=600)
        ut = d / 'ut.npz'
        return r.returncode == 0 and ut.exists(), ut.read_bytes() if ut.exists() else b'', r.stdout[-20000:], r.stderr[-12000:]

    def _skicka(self, d, V):
        import json, selectors
        if self.arbetare.poll() is not None:
            raise RuntimeError('arbetaren har dött')
        rad = json.dumps({'inn': str(d / 'in.npz'), 'ut': str(d / 'ut.npz'), 'villkor': V}, ensure_ascii=False)
        self.arbetare.stdin.write(rad + '\n'); self.arbetare.stdin.flush()
        sel = selectors.DefaultSelector(); sel.register(self.arbetare.stdout, selectors.EVENT_READ)
        try:
            if not sel.select(timeout=120):
                raise TimeoutError('arbetaren svarade inte inom 120 s')
            svar = self.arbetare.stdout.readline()
        finally:
            sel.close()
        if not svar:
            raise RuntimeError('arbetaren stängde stdout')
        return json.loads(svar)

    @modal.method()
    def kor(self, inn: bytes, villkor: str, kod: str = '') -> dict:
        import json, os, tempfile, time
        t0 = time.time()
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); (d / 'in.npz').write_bytes(inn); (d / 'v.json').write_text(villkor, encoding='utf-8')
            V = json.loads(villkor)
            if kod and kod != self.startkod:
                ok, npz, stdout, stderr = self._gammal_vag(d, inn, villkor, kod); vag = 'process'
            else:
                try:
                    svar = self._skicka(d, V); ut = d / 'ut.npz'
                    ok = bool(svar.get('ok')) and ut.exists(); npz = ut.read_bytes() if ut.exists() else b''
                    stdout = str(svar.get('logg', ''))[-20000:]; stderr = self._feltext(); vag = 'arbetare'
                except Exception as e:
                    arbetsfel = self._feltext(); self._stoppa_arbetare()
                    ok, npz, stdout, stderr = self._gammal_vag(d, inn, villkor, kod)
                    self._starta_arbetare()
                    stderr = (arbetsfel[-5000:] + '\n' + stderr[-5000:] + '\nARBETARE_FALLBACK: ' + repr(e))[-12000:]
                    vag = 'process'
            return {'ok': ok, 'npz': npz, 'stdout': stdout, 'stderr': stderr,
                    's': round(time.time() - t0, 1), 'container': os.environ.get('MODAL_TASK_ID', ''), 'vag': vag}

    @modal.method()
    def ping(self) -> str:
        import subprocess
        status = 'arbetare pid %s %s' % (self.arbetare.pid, 'lever' if self.arbetare.poll() is None else 'död')
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
        return gpu + '; ' + status + '; stderr: ' + self._feltext()[-1500:].replace('\n', ' | ')


@app.function(timeout=900, scaledown_window=1200, max_containers=6)
def kor(inn: bytes, villkor: str, kod: str = '') -> dict:
    """Bakåtkompatibel ingång för kropp.py och mening.py."""
    varm = modal.Cls.from_name('hagen-mm-tjanst', 'VarmKroppSlutlig')()
    return varm.kor.remote(inn, villkor, kod)


@app.function(timeout=900, scaledown_window=1200, max_containers=6)
def ping() -> str:
    varm = modal.Cls.from_name('hagen-mm-tjanst', 'VarmKroppSlutlig')()
    return varm.ping.remote()
