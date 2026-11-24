"""Uppgift 2: vilka block syns i vilken tagning, och hör de hemma där?

Projicerar planens lådor (samma objekt som Jutsu-scenen byggdes av) genom planens
renderkamera, mitt i varje tagning, och ritar konturerna över originalets bild.
Skriver ut/notan/bugg/<scen>.png, en översiktsbild och bugg_block.json.

Kör från projektroten:
  scen/.venv/Scripts/python.exe byggsten/jutsu/bugg_block.py
"""
import json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROT = Path(__file__).resolve().parents[2]
PLAN = ROT / "scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json"
VIDEO = ROT / "scen/klipp/d-dialog-notan.mp4"
UT = Path(__file__).resolve().parent / "ut/notan/bugg"; UT.mkdir(parents=True, exist_ok=True)
EXPORT = Path(__file__).resolve().parent / "ut/notan/notan_jutsu.json"

plan = json.loads(PLAN.read_text(encoding="utf-8"))
W, H = plan["utdata"]["bredd"], plan["utdata"]["hojd"]
kam = plan["renderkamera"]["nycklar"]
exp = json.loads(EXPORT.read_text(encoding="utf-8"))
led_ix = {n: i for i, n in enumerate(exp["leder"])}


def horn(o):
    p = np.array(o["pos_m"]); m = np.array(o["matt_m"]) / 2; rz = o["rotation_rad"][2]
    R = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    s = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    return (s * m) @ R.T + p


KANTER = [(a, b) for a in range(8) for b in range(a + 1, 8) if bin(a ^ b).count("1") == 1]


def proj(x, key):
    m = np.array(key["matris"]); c = (np.asarray(x) - m[:3, 3]) @ m[:3, :3]
    fok = key["lins_mm"] / 36 * W
    djup = -c[..., 2]
    uv = c[..., :2] / np.maximum(djup[..., None], 1e-6) * [fok, -fok] + [W / 2, H / 2]
    return uv, djup


def ruta(u):
    t = u / 30
    ut = UT / f"_orig_{u:03d}.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(VIDEO), "-frames:v", "1",
                    "-vf", f"scale={W}:{H}", str(ut)], check=True)
    return Image.open(ut).convert("RGB")


def personens_djup(scen_id, u, key):
    for s in exp["scener"]:
        if s["id"] != scen_id: continue
        for p in s["personer"]:
            r = min(p["rutor"], key=lambda r: abs(r[0] - u))
            x = np.array(r[1:]).reshape(-1, 3) / 1000
            _, d = proj(x, key)
            return float(np.median(d)), p["id"]
    return None, None


rapport = []
bilder = []
for sc in plan["scener"]:
    a, b = sc["ut"]; u = (a + b) // 2; key = kam[u]
    pd, pid = personens_djup(sc["id"], u, key)
    im = ruta(u); dr = ImageDraw.Draw(im, "RGBA")
    rad = dict(scen=sc["id"], ruta=u, person=pid, person_djup_m=pd and round(pd, 2), objekt=[])
    for o in plan["objekt"]:
        sa, sb = o.get("synlig_ut", [0, len(plan["kallrutor"])])
        if not (sa <= u < sb): continue
        x = horn(o); uv, d = proj(x, key)
        if (d <= 0.05).all(): continue
        framfor = d > 0.05
        uvf = uv[framfor]
        x0, y0 = np.clip(uvf.min(0), 0, [W, H]); x1, y1 = np.clip(uvf.max(0), 0, [W, H])
        yta = max(0, x1 - x0) * max(0, y1 - y0) / (W * H)
        if yta <= 0: continue
        bas = o["id"].split(":")[0]
        mdjup = float(np.median(d[framfor]))
        fore_person = pd is not None and mdjup < pd - 0.15
        rad["objekt"].append(dict(id=o["id"], bas=bas, djup_m=round(mdjup, 2), bildyta=round(float(yta), 3),
                                  framfor_person=bool(fore_person), synlig_ut=[sa, sb]))
        farg = {"bord_1": (255, 60, 60), "bord_2": (255, 160, 0), "stol_A": (60, 200, 255), "stol_B": (60, 255, 60),
                "stol_B_avslojad": (255, 0, 255), "golv": (200, 200, 200), "vagg_bak": (255, 255, 0),
                "vagg_sida": (255, 255, 120)}.get(bas, (255, 255, 255))
        for i, j in KANTER:
            if d[i] > 0.05 and d[j] > 0.05:
                dr.line([tuple(uv[i]), tuple(uv[j])], fill=farg + (230,), width=2)
    dr.rectangle([0, 0, W, 34], fill=(0, 0, 0, 170))
    dr.text((8, 8), f"{sc['id']} ruta {u}  person {pid}", fill=(255, 255, 255))
    im.save(UT / f"{sc['id']}.png"); bilder.append(im.resize((W // 2, H // 2)))
    # sammanfatta per bas
    per = {}
    for ob in rad["objekt"]:
        q = per.setdefault(ob["bas"], dict(bildyta=0, framfor_person=False, delar=0, djup_m=ob["djup_m"]))
        q["bildyta"] = round(q["bildyta"] + ob["bildyta"], 3); q["delar"] += 1
        q["framfor_person"] |= ob["framfor_person"]; q["djup_m"] = min(q["djup_m"], ob["djup_m"])
    rad["per_mobel"] = per
    rapport.append(rad)

ark = Image.new("RGB", (W // 2 * len(bilder), H // 2), "black")
for i, im in enumerate(bilder): ark.paste(im, (i * W // 2, 0))
ark.save(UT / "oversikt.png")
for f in UT.glob("_orig_*.png"): f.unlink()
(UT / "bugg_block.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding="utf-8")
for r in rapport:
    print(r["scen"], r["ruta"], r["person"], r["person_djup_m"])
    for k, v in sorted(r["per_mobel"].items(), key=lambda kv: kv[1]["djup_m"]):
        print(f"   {k:16s} djup {v['djup_m']:5.2f}  yta {v['bildyta']:.3f}  delar {v['delar']}  {'FRAMFÖR PERSON' if v['framfor_person'] else ''}")
