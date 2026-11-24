"""Skriver MANIFEST.md: daterat, före testmätning. Kod-sha256, paketversioner, ffmpeg/ffprobe/node/python-versioner, kommandorader, frön, referensparametrar.
  python manifest.py
"""
import hashlib, json, subprocess, sys, datetime, platform, importlib.metadata as md
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recept, mat_adapter as M, analys
from falt import FALT

HER = Path(__file__).parent
ROT = HER.parents[2]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(*a):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


L = []
w = L.append
w("# MANIFEST, steg 2 (invarians), version v1")
w("")
w(f"Skrivet {datetime.datetime.now().isoformat(timespec='seconds')} (lokal tid) **före första testmätningen** av de 12 testklippen. Protokoll: `motpart/runda-4/T4-codex/FORREGISTRERING.md` avsnitt Gemensamt och A. Tolkningar och avvikelser: `AVVIKELSER.md` (skriven före detta manifest).")
w("")
w("## Frön")
w("- Urvalsfrö 202611204 (T4, `las_urval.py`, redan utfört). Permutationsfrö i förtestet: `numpy.random.default_rng(202611204)`, 100 permutationer.")
w("- Ingen annan slumpkälla används i mätning eller dom. ffmpeg-recepten är deterministiska (kontrolleras med Cr och N0r).")
w("")
w("## Indata (sha256)")
for p in ["motpart/runda-4/1-datagrund/urval.json", "motpart/runda-4/1-datagrund/manifest.jsonl", "motpart/runda-3-opus/D-medielager/urval.json", "motpart/runda-4/T4-codex/FORREGISTRERING.md", "motpart/runda-4/T4-codex/las_urval.py"]:
    w(f"- `{p}` {sha(ROT / p)}")
w(f"- Alla 200 källfiler i `C:\\Users\\praiseworthy\\Downloads\\letrend-r4\\`: sha256 verifierad mot `manifest.jsonl` (0 avvikelser), `verifiera_kalla.py`; ffprobe för de 156 använda i `ffprobe_kallor.json` ({sha(HER / 'ffprobe_kallor.json')}).")
w(f"- Urval återskapat med `las_urval.py` i `urval_las.json` ({sha(HER / 'urval_las.json')}): 12 testklipp, 144 referensklipp i 72 konton.")
w("")
w("## Extraktorer (orörda; byte-identiska kopior körs, kontrolleras vid trädbygget)")
for k, p in M.SKRIPT.items():
    w(f"- `{p.relative_to(ROT).as_posix()}` {sha(p)}")
w(f"- `video/analys/verktyg.mjs` {sha(M.VERKTYG)}")
w(f"- Modellvikter `data/format/e37/yolov8n.pt` {sha(M.VIKTER)}")
w("- Silero VAD: `load_silero_vad(onnx=True)` ur paketet silero-vad (modellfil i paketet).")
w("")
w("## Min kod (sha256)")
for p in ["recept.py", "falt.py", "mat_adapter.py", "bilaga.py", "ref_kor.py", "test_kor.py", "analys.py", "kontaktkarta.py", "bygg_kontroll.py", "verifiera_kalla.py", "manifest.py"]:
    w(f"- `{p}` {sha(HER / p)}")
w("")
w("## Versioner")
w(f"- Python {platform.python_version()} (`scen/.venv`), plattform {platform.platform()}, processor {platform.processor()}")
for pk in ["numpy", "torch", "silero-vad", "onnxruntime", "ultralytics", "opencv-python", "opencv-python-headless", "scipy", "pillow"]:
    try:
        w(f"- {pk} {md.version(pk)}")
    except Exception:
        w(f"- {pk} (ej installerat)")
w(f"- node {run('node', '-v').strip()}")
w("- ffmpeg (fullständigt versions- och konfigurationsblock):")
w("```text")
w(run("ffmpeg", "-version").strip())
w("```")
w("- ffprobe: " + run("ffprobe", "-version").splitlines()[0])
w("")
w("## Explicita extraktorparametrar (VAD och scen)")
import inspect
from silero_vad import get_speech_timestamps
w("- E30, anrop i skriptet: `get_speech_timestamps(audio, model, sampling_rate=16000, return_seconds=True, min_silence_duration_ms=300)`. Övriga argument är paketets standardvärden för installerad version, uppslagna med `inspect.signature` och fastlåsta här:")
w("```text")
w(str(inspect.signature(get_speech_timestamps)))
w("```")
w("- E30: avkodning `ffmpeg -v quiet -i <fil> -ac 1 -ar 16000 -f s16le -`, `torch.set_num_threads(2)`.")
w("- E28: `ffmpeg -hide_banner -nostats -i <fil> -vf \"select='gte(scene,0)',metadata=print\" -af \"silencedetect=n=-35dB:d=0.3,ebur128=framelog=quiet\" -f null -`; byte där scenpoäng >0,3; första bildens poäng ignoreras.")
w("- E37: YOLOv8n, sex rutor vid relativa positioner linspace(0,05, 0,95, 6), `imgsz=320`, klass 0, konfidens >=0,4, `torch.set_num_threads(2)`.")
w("- Extraktorerna körs sekventiellt (E28 `--par 1`), en batch i taget.")
w("")
w("## Kommandorader (argv; ingen shell). Platshållare: O.mp4 = originalfil, C.mkv = C-fil")
w("```text")
w(" ".join(recept.c_cmd("O.mp4", "C.mkv")))
for n in recept.VARIANTER:
    w(" ".join(recept.var_cmd(n, "C.mkv", f"{n}.mkv")))
w("```")
w("- Ytterligare en körning: `ffprobe`, `ffmpeg ... -f framehash -hash sha256`, `ffmpeg ... -af volumedetect`, samt E28/E30-bilagorna (`bilaga.py`).")
w("")
w("## Referensparametrar (fryst på R, endast C-versioner av de 144 referensklippen)")
ref = analys.ladda_ref()
T = analys.Transform(ref)
w(f"- Referensklipp med komplett C och E28-rad: {len(ref)} av 144, konton: {T.nk}. `ref_mat.jsonl` sha256 {sha(HER / 'ref_mat.jsonl')}.")
w("- Transform: `F_j(x) = sum_i w_i [1(r_ij < x) + 0,5 * 1(r_ij = x)]`, `z_j = (F_j - mu_j) / sigma_j`; kontovikter lika (summa 1), fördelade lika över kontots klipp med giltigt värde för fältet, normaliserade över giltiga konton. Färre än 30 giltiga konton eller sigma=0 ger ingen kalibrerad axel.")
w("")
w("| fält | klass | eps | giltiga konton | kalibrerad | mu | sigma | min | median | max |")
w("|---|---|---|---|---|---|---|---|---|---|")
for j, (kl, eps, *_r) in FALT.items():
    p = T.par[j]
    if "mu" in p:
        w(f"| {j} | {kl} | {eps} | {p['giltiga_konton']} | {'ja' if p['kalibrerad'] else 'nej (konstant)'} | {p['mu']:.6f} | {p['sigma']:.6f} | {p['min']:.4g} | {p['median']:.4g} | {p['max']:.4g} |")
    else:
        w(f"| {j} | {kl} | {eps} | {p['giltiga_konton']} | nej (<30 konton) | | | | | |")
w("")
w("## Dry run (mekanik, endast R-klipp, ingen testklipp)")
dry = HER / "dry_test_mat.jsonl"
w(f"- Dry-körningens mätvärden: {'`dry_test_mat.jsonl` sha256 ' + sha(dry) if dry.exists() else 'ej gjord ännu'}. Dry-värden används i ingen dom.")
(HER / "MANIFEST.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("MANIFEST.md skriven")
