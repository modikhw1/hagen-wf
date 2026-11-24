"""Bryggan från början till slut för ett klipp: samla -> grindar -> emit -> lokal Blender -> jämförelse.

  scen/.venv/Scripts/python.exe byggsten/brygga/kor.py notan [--film] [--jutsu]

Klippen beskrivs i KLIPP nedan (indata ur kedjan). Allt skrivs under byggsten/brygga/ut/<klipp>/.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[1]
PY = ROT / "scen/.venv/Scripts/python.exe"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
KLIPP = {
    "notan": dict(plan="scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json",
                  kalla="scen/3d/kontrakt/ut/notan_berattat/kalla_mobelintervall.json",
                  deklaration="scen/3d/ingest/ut/notan-tagningar/plats/deklaration.json",
                  video="scen/klipp/d-dialog-notan.mp4"),
}


def kor(args, **kw):
    t = time.time(); r = subprocess.run([str(x) for x in args], cwd=ROT, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-3000:]); raise SystemExit(f"fel i {args[1]}")
    return r.stdout, round(time.time() - t, 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("klipp"); ap.add_argument("--film", action="store_true")
    ap.add_argument("--jutsu", action="store_true"); ap.add_argument("--steg", type=int, default=1); ap.add_argument("--leder", default="t1"); ap.add_argument("--kropp", default="t1")
    a = ap.parse_args(); K = KLIPP[a.klipp]; ut = HIT / "ut" / a.klipp; ut.mkdir(parents=True, exist_ok=True)
    tider = {}
    bas = ["--klipp", a.klipp, "--plan", K["plan"], "--kalla", K["kalla"], "--deklaration", K["deklaration"], "--steg", a.steg, "--leder", a.leder]
    o, tider["samla_ra"] = kor([PY, HIT / "samla.py", *bas, "--utan-regler"])
    o, tider["samla"] = kor([PY, HIT / "samla.py", *bas]); print(o.splitlines()[0])
    o, tider["grindar"] = kor([PY, HIT / "grindar.py", ut / "paket_ra.json", ut / "paket.json"])
    (ut / "GRINDAR.md").write_text(o, encoding="utf-8"); print(o)
    o, tider["emit"] = kor([PY, HIT / "emit_bpy.py", ut / "paket.json", "--kropp", a.kropp, *(["--film"] if a.film else [])])
    if a.jutsu: kor([PY, HIT / "emit_bpy.py", ut / "paket.json", "--jutsu"])
    bild = ut / "lokal"; bild.mkdir(exist_ok=True)
    o, tider["blender"] = kor([BLENDER, "-b", "--factory-startup", "--python", ut / "lokal_bygg.py", "--", ut / "paket.json", bild])
    res = next((json.loads(l.split(" ", 1)[1]) for l in o.splitlines() if l.startswith("RESULTAT")), {})
    tider["blender_inre"] = res
    # jämförelse: original ovanför, bryggans bild under, en kolumn per tagning
    p = json.loads((ut / "paket.json").read_text(encoding="utf-8")); W, H = p["bild"]["bredd"] // 2, p["bild"]["hojd"] // 2
    from PIL import Image
    ark = Image.new("RGB", (W * len(p["tagningar"]), H * 2), "black")
    for i, t in enumerate(p["tagningar"]):
        u = (t["ut"][0] + t["ut"][1]) // 2; o_png = bild / f"_orig_{u:03d}.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{u / p['tidsbas']['fps']:.3f}", "-i", str(ROT / K["video"]),
                        "-frames:v", "1", "-vf", f"scale={W}:{H}", str(o_png)], check=True)
        ark.paste(Image.open(o_png).convert("RGB"), (i * W, 0)); o_png.unlink()
        ark.paste(Image.open(bild / f"kontroll_{t['id']}_{u:03d}.png").convert("RGB").resize((W, H)), (i * W, H))
    ark.save(ut / "jamforelse.png")
    if a.film and (bild / "animatik.mp4").exists():
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(ROT / K["video"]), "-i", str(bild / "animatik.mp4"), "-filter_complex",
                        f"[0:v]scale={W}:{H},setsar=1,fps=30[a];[1:v]scale={W}:{H},setsar=1[b];[a][b]hstack=inputs=2[v]",
                        "-map", "[v]", "-map", "0:a?", "-shortest", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
                        str(ut / "original_mot_brygga.mp4")], check=True)
    (ut / "tider.json").write_text(json.dumps(tider, indent=1), encoding="utf-8")
    print("tider:", tider)


if __name__ == "__main__":
    main()
