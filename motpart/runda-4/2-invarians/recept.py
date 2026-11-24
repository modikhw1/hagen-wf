"""Steg 2: de exakta ffmpeg-recepten ur FORREGISTRERING.md A2, som argv-listor (ingen shell).
Receptens text är låst; här finns inga egna parametrar. Varje recept är ett anrop.
"""
import subprocess, json, hashlib
from pathlib import Path

FF = "ffmpeg"
PRE = [FF, "-nostdin", "-hide_banner", "-loglevel", "warning", "-y"]

def c_cmd(o, c, audio=True):
    return PRE + ["-i", str(o), "-map", "0:v:0"] + ["-map", "0:a:0?"] + [
        "-map_metadata", "-1", "-map_chapters", "-1",
        "-vf", "fps=fps=30:start_time=0:round=near,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0,setsar=1",
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le",
        "-fps_mode", "passthrough", str(c)]

def var_prefix(c):
    return PRE + ["-i", str(c), "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "-1", "-map_chapters", "-1"]

SUFFIX = {
    "N0": ["-c", "copy"],
    "N1": ["-c:v", "libx264", "-preset", "medium", "-crf", "28", "-pix_fmt", "yuv420p", "-threads:v", "1", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N2": ["-vf", "scale=w='max(2,trunc(iw/4)*2)':h='max(2,trunc(ih/4)*2)':flags=lanczos,setsar=1", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N3": ["-af", "volume=-6dB", "-c:v", "copy", "-c:a", "pcm_s24le"],
    "N4": ["-af", "volume=-12dB", "-c:v", "copy", "-c:a", "pcm_s24le"],
    "N5": ["-vf", "fps=fps=15:start_time=0:round=near", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N6": ["-vf", "crop=iw-4:ih-4:2:2,pad=iw+4:ih+4:2:2:black,setsar=1", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "P": ["-vf", "setpts=(PTS-STARTPTS)/1.25,fps=fps=30:start_time=0:round=near", "-af", "atempo=1.25", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", "-fps_mode", "passthrough"],
}
VARIANTER = ["N0", "N1", "N2", "N3", "N4", "N5", "N6", "P"]

def var_cmd(name, c, out):
    return var_prefix(c) + SUFFIX[name] + [str(out)]

def kor(argv):
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stderr

def ffprobe(f):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(f)], capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout)

def slutider(f):
    """Slut på bild- och ljudström (sista pts + längd), via paketen. Sekunder."""
    res = {}
    for typ, sel in (("v", "v:0"), ("a", "a:0")):
        p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "packet=pts_time,duration_time", "-of", "csv=p=0", str(f)], capture_output=True, text=True, encoding="utf-8").stdout
        end, n = None, 0
        for line in p.splitlines():
            parts = line.strip().split(",")
            if len(parts) >= 2 and parts[0] not in ("", "N/A"):
                try:
                    t = float(parts[0]); d = float(parts[1]) if parts[1] not in ("", "N/A") else 0.0
                except ValueError: continue
                n += 1
                end = t + d if end is None else max(end, t + d)
        res[typ] = {"slut": end, "paket": n}
    return res

def innehallshash(f):
    """Hash av avkodad bild (framemd5 över alla bilder) och avkodat ljud (md5 på s32le), oberoende av container."""
    out = {}
    p = subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(f), "-map", "0:v:0", "-f", "framehash", "-hash", "sha256", "-"], capture_output=True, text=True, encoding="utf-8")
    out["bild"] = hashlib.sha256(p.stdout.encode()).hexdigest() if p.returncode == 0 else None
    p = subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(f), "-map", "0:a:0?", "-f", "hash", "-hash", "sha256", "-"], capture_output=True, text=True, encoding="utf-8")
    out["ljud"] = p.stdout.strip() if p.returncode == 0 else None
    return out

def sha256(f):
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
