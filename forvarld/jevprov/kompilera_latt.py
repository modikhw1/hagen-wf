"""Kör den oförändrade kompilatorn, med skrivskydd och små resursgränser."""
import sys
sys.dont_write_bytecode = True
import os
import json
import time
import ctypes
import threading
import ast
from pathlib import Path

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent.parent
OUT = DIR / 'ut'
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                  PYTHONDONTWRITEBYTECODE='1', TAL_CACHE=str(OUT / 'tal_cache'))

def grans():
    """Windows stoppar processen om den passerar 384 MiB privat minne."""
    if os.name != 'nt':
        return None
    from ctypes import wintypes as w
    class BASIC(ctypes.Structure):
        _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64),
                    ('LimitFlags', w.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                    ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', w.DWORD),
                    ('Affinity', ctypes.c_size_t), ('PriorityClass', w.DWORD), ('SchedulingClass', w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(x, ctypes.c_uint64) for x in ['ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount']]
    class EXT(ctypes.Structure):
        _fields_ = [('BasicLimitInformation', BASIC), ('IoInfo', IO), ('ProcessMemoryLimit',ctypes.c_size_t),
                    ('JobMemoryLimit',ctypes.c_size_t), ('PeakProcessMemoryUsed',ctypes.c_size_t), ('PeakJobMemoryUsed',ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p,w.LPCWSTR]
    kernel.SetInformationJobObject.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE,w.HANDLE]
    kernel.GetCurrentProcess.restype = w.HANDLE
    job = kernel.CreateJobObjectW(None,None)
    info = EXT(); info.BasicLimitInformation.LimitFlags = 0x100
    info.ProcessMemoryLimit = 384*1024*1024
    if not job or not kernel.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)):
        raise OSError('Kunde inte sätta minnesgräns')
    if not kernel.AssignProcessToJobObject(job,kernel.GetCurrentProcess()):
        raise OSError('Kunde inte aktivera minnesgräns')
    return job

def skydd(event,args):
    if event == 'open':
        name,mode,flags = args
        if isinstance(name,(str,bytes,os.PathLike)) and ((mode and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):
            p = Path(os.fsdecode(name)).resolve()
            if not p.is_relative_to(OUT):
                raise PermissionError('Skrivning utanför experimentets ut-mapp stoppades')
    if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):
        raise PermissionError('Ingen extern process eller nättrafik vid kompilering')
    if event == 'import' and args[0].split('.')[0] in ('torch','piper','bpy','transformers'):
        raise ImportError('Tung modell eller rendering är förbjuden i provet')

def main():
    case = sys.argv[1]
    if case not in ('t1','t2','t5','t11','t13'):
        raise ValueError('Okänd provmening')
    original = OUT / 'konkret' / case
    diagnostic = '--diagnostisk' in sys.argv
    core = '--endast-edits' in sys.argv
    diagnostic = diagnostic or core
    folder = original / ('diagnostisk_latt' if core else 'diagnostisk') if diagnostic else original
    result = dict(id=case, memory_limit_mib=384, timeout_s=45, unmodified_compiler=True, diagnostic_source=diagnostic, core_only=core)
    job = grans()
    sys.addaudithook(skydd)
    timer = threading.Timer(45, lambda: os._exit(124)); timer.daemon=True; timer.start()
    start = time.perf_counter()
    sys.path.insert(0,str(ROOT/'scen/3d/kontrakt'))
    try:
        from kompilera import kompilera
        from gemensamt import skriv
        from trohet import rapport
        source = OUT/'konkret/kalla_diagnostisk.json' if diagnostic else ROOT/'scen/3d/kontrakt/exempel/notan/kalla.json'
        if core:
            # Kör verklig validering, edittillämpning och planbygge. Stanna vid
            # första efterdiagnostiken; den fulla diagnostiken överskred vår gräns.
            # Resultatet är en diagnostisk kärnplan, inte en renderklar plan.
            class Klar(Exception):
                def __init__(self, plan):
                    self.plan = plan
            compiler_path = ROOT/'scen/3d/kontrakt/kompilera.py'
            tree = ast.parse(compiler_path.read_text(encoding='utf-8'))
            stop = next(n.lineno for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module=='trohet' and any(a.name=='mat' for a in n.names))
            def trace(frame,event,arg):
                if event=='line' and frame.f_code.co_filename==str(compiler_path) and frame.f_lineno==stop:
                    raise Klar(frame.f_locals['plan'])
                return trace if frame.f_code.co_filename==str(compiler_path) else None
            sys.settrace(trace)
            try:
                plan = kompilera(source,folder/'regi.json')
            except Klar as e:
                plan = e.plan
            finally:
                sys.settrace(None)
            plan['diagnostik_utelamnad'] = 'Stopp före trohet.mat och kvalitet.komplettera för att undvika bild- och kroppsmätning. Ej renderklar plan.'
        else:
            plan = kompilera(source, folder/'regi.json')
        skriv(folder/'plan.json', plan)
        if not core:
            rapport(plan, folder/'plan.json')
        result.update(compiled=True,tillampat=plan['tillampat'],ej_tillampat=plan['ej_tillampat'],varningar=plan['varningar'])
    except Exception as e:
        result.update(compiled=False,error_type=type(e).__name__,error=str(e))
    finally:
        timer.cancel()
    result['seconds'] = time.perf_counter()-start
    (folder/'kompilering.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='tillampat'},ensure_ascii=False))

if __name__ == '__main__':
    main()
