"""Steg 2, kör invarians: för varje klipp i A1: C (två gånger), N0 (två gånger), N1-N6, P, mät varje fil med E28/E30/E37, logga allt.
  python test_kor.py --lage test|dry [--id <id> ...]
  dry = repetition av mekaniken på ett R-klipp (inga testklipp), skriver dry_*.
En variantfil i taget (disken räcker inte för alla samtidigt); varje fils sha256, avkodade innehållshash, A/V-sluttider och ffprobe loggas före radering.
Kontaktkarta (original och varje ingrepp) görs för klippen i --kontakt.
"""
import argparse, json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from recept import *
import mat_adapter as M

HER = Path(__file__).parent
SRC = Path(r"C:\Users\praiseworthy\Downloads\letrend-r4")
ap = argparse.ArgumentParser(); ap.add_argument("--lage", required=True); ap.add_argument("--id", nargs="*"); ap.add_argument("--kontakt", nargs="*", default=[])
a = ap.parse_args()
TEST = a.lage == "test"
pre = "" if TEST else "dry_"
urv = json.loads((HER/"urval_las.json").read_text(encoding="utf-8"))
ids = a.id or [x["id"] for x in urv["step2"]]
ARB = M.W / ("arb_test" if TEST else "arb_dry"); ARB.mkdir(parents=True, exist_ok=True)
LOGG = HER / f"{pre}bygg_logg.jsonl"; MAT = HER / f"{pre}test_mat.jsonl"; KONT = M.W / ("kontakt" if TEST else "kontakt_dry")
ORDNING = ["O", "C", "C2", "Cr", "N0", "N0r", "N1", "N2", "N3", "N4", "N5", "N6", "P"]
FRAC = (0.2, 0.5, 0.8)

def fri():
    f = shutil.disk_usage(str(M.W)).free
    if f < 5e9: print("AVBRYT: ledigt", f, flush=True); sys.exit(3)
    return f

def sammanfatta(f):
    p = ffprobe(f); v = [s for s in p["streams"] if s["codec_type"] == "video"]; au = [s for s in p["streams"] if s["codec_type"] == "audio"]
    v = v[0]; r = {"video": {k: v.get(k) for k in ("codec_name", "width", "height", "pix_fmt", "r_frame_rate", "avg_frame_rate", "sample_aspect_ratio", "color_transfer", "start_time", "duration")}}
    r["audio"] = {k: au[0].get(k) for k in ("codec_name", "sample_rate", "channels", "start_time", "duration")} if au else None
    r["format_duration"] = p["format"].get("duration"); return r

def volym(f):
    p = subprocess.run([FF, "-nostdin", "-hide_banner", "-i", str(f), "-map", "0:a:0?", "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    import re
    m = re.search(r"mean_volume: (-?[0-9.]+) dB", p); x = re.search(r"max_volume: (-?[0-9.]+) dB", p)
    return {"mean": float(m.group(1)) if m else None, "max": float(x.group(1)) if x else None}

def kontaktdata(f, namn, ut):
    """Bildrutor på 20/50/80 % av egen längd, sex på varandra följande rutor med pts, och ljudkuvert."""
    ut.mkdir(parents=True, exist_ok=True)
    s = slutider(f); vd = s["v"]["slut"]
    for k, fr in enumerate(FRAC):
        subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{fr*vd:.4f}", "-i", str(f), "-frames:v", "1", "-vf", "scale=-2:240", str(ut/f"{namn}_f{k}.png")])
    r = subprocess.run([FF, "-nostdin", "-hide_banner", "-y", "-ss", f"{0.4*vd:.4f}", "-i", str(f), "-frames:v", "6", "-vf", "scale=-2:240,showinfo", str(ut/f"{namn}_s%d.png")], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    import re
    pts = [float(x) for x in re.findall(r"pts_time:\s*([0-9.]+)", r)]
    raw = subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(f), "-map", "0:a:0", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    np.save(ut/f"{namn}_ljud.npy", x.astype(np.float16)); json.dump({"pts": pts, "vslut": vd}, open(ut/f"{namn}_meta.json", "w"))

def bygg(i, namn, C):
    """Bygger en fil och returnerar (argv, sökväg)."""
    out = ARB / f"{M.stem(i, namn)}.mkv"
    if namn == "C" or namn == "Cr": argv = c_cmd(SRC/f"{i}.mp4", out)
    else: argv = var_cmd("N0" if namn == "N0r" else namn, C, out)
    return argv, out

def logga(d):
    with LOGG.open("a", encoding="utf-8") as f: f.write(json.dumps(d, ensure_ascii=False) + "\n")

M.bygg_trad("test")
for i in ids:
    print("KLIPP", i, flush=True)
    C = None; hashar = {}
    for namn in ORDNING:
        fri(); stagefil = None
        try:
            t0 = time.time(); argv = None; stagefil = None; rc = 0; err = ""
            if namn == "O": stagefil = SRC/f"{i}.mp4"
            elif namn == "C2": stagefil = C
            else:
                argv, stagefil = bygg(i, namn, C); rc, err = kor(argv)
                if namn == "C": C = stagefil
            if rc != 0 or not stagefil.exists():
                logga({"id": i, "variant": namn, "argv": argv, "rc": rc, "stderr": err[-800:], "fel": "bygget misslyckades"}); print("BYGGFEL", namn, err[-300:], flush=True); continue
            post = {"id": i, "variant": namn, "argv": argv, "rc": rc, "stderr": err[-800:], "bygg_sek": round(time.time() - t0, 1), "storlek": stagefil.stat().st_size,
                    "sha256": sha256(stagefil), "innehall": innehallshash(stagefil), "slutider": slutider(stagefil), "ffprobe": sammanfatta(stagefil), "volym": volym(stagefil)}
            if i in a.kontakt: kontaktdata(stagefil, namn, KONT/i)
            logga(post); hashar[namn] = post
            ut, tid = M.kor_batch("test", {M.stem(i, namn): stagefil}, [])
            r = ut[M.stem(i, namn)]
            if namn not in ("C2",):   # adapterbilagor: scen-/tystnadslogg och VAD-intervall (nya loggar)
                import bilaga
                bl = {"e28": bilaga.e28_logg(stagefil), "e30": bilaga.e30_vad(stagefil)}
                bl["konsistens"] = {"byten_lika": len(bl["e28"]["byten_t"]) == (r.get("e28") or {}).get("byten"), "tal_segment_lika": len(bl["e30"]["vad"]) == (r.get("e30") or {}).get("tal_segment")}
                (HER / (pre + "bilagor")).mkdir(exist_ok=True)
                json.dump(bl, open(HER / (pre + "bilagor") / f"{M.stem(i, namn)}.json", "w"), ensure_ascii=False)
                print("   bilaga", bl["konsistens"], flush=True)
            with MAT.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"id": i, "konto": i.rsplit("-", 1)[0], "variant": namn, "e28": r.get("e28"), "e30": r.get("e30"), "e37": r.get("e37"), "extraktor_sek": tid}, ensure_ascii=False) + "\n")
            print(" ", namn, "ok", tid, flush=True)
        except Exception as e:
            logga({"id": i, "variant": namn, "fel": repr(e)}); print("UNDANTAG", namn, repr(e), flush=True)
        finally:
            if namn not in ("O", "C", "C2") and "stagefil" in dir() and stagefil and stagefil.exists() and stagefil != C: stagefil.unlink()
    if C and C.exists(): C.unlink()
    print("klar", i, "ledigt GB", round(shutil.disk_usage(str(M.W)).free / 1e9, 1), flush=True)
print("KLART", flush=True)
