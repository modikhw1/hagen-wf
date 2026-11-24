"""Headless Blender 5.2-rendering av valfria rutor (inte bara mitten) + extra kamera ovanifrån/från sidan.

Kör:  scen/.venv/Scripts/python.exe motpart/runda-1-claude/mening_render.py

Återanvänder Argons genererade lokal_bygg.py (scenbygget är paketoberoende och läser paketet ur argv)
fram till raden '# --- kontrollbilder ---' och byter bara ut renderslingan. Inget i forvarld_karna/ ändras.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

import cv2
import numpy as np

import mening_gemensamt as G

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
BAS_SKRIPT = G.KARNA / "ut" / "guacamole" / "manip_ga_med_attityd" / "lokal_bygg.py"

RENDER_SLINGA = r'''
# --- mening_render: valda rutor och extra kameror ---
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
JOBB=json.loads(os.environ["MENING_JOBB"])
UTD=os.environ["MENING_UT"]
# tidslinjemarkörer binder kameror och skulle annars skriva över s.camera vid rendering
for m_ in s.timeline_markers: m_.camera=None
for j in JOBB:
    s.frame_set(j["ruta"])
    if j.get("extra"):
        e=j["extra"]
        cd=bpy.data.cameras.new("CAM_extra"); cd.sensor_width=36
        if e.get("orto"): cd.type="ORTHO"; cd.ortho_scale=e["orto"]
        else: cd.lens=e.get("lins",24)
        c=bpy.data.objects.new("CAM_extra",cd); s.collection.objects.link(c)
        c.location=e["pos"]; c.rotation_mode="XYZ"; c.rotation_euler=[math.radians(v) for v in e["rot"]]
        s.camera=c
        for o_ in bpy.data.objects:
            if o_.name.startswith("ENV_vagg") and e.get("utan_vaggar"): o_.hide_render=True; o_.animation_data_clear()
        s.render.resolution_x=e.get("bx",P["bild"]["bredd"]); s.render.resolution_y=e.get("by",P["bild"]["hojd"])
    else:
        s.camera=bpy.data.objects["CAM_"+j["tagning"]]
        s.render.resolution_x=P["bild"]["bredd"]; s.render.resolution_y=P["bild"]["hojd"]
    # synlighet följer rutan (personer/objekt nycklade via hide_render)
    s.render.filepath=os.path.join(UTD,j["fil"])
    bpy.ops.render.render(write_still=True)
    if j.get("extra"):
        bpy.data.objects.remove(bpy.data.objects["CAM_extra"])
print("MENING_KLAR")
'''


def bygg_skript() -> pathlib.Path:
    txt = BAS_SKRIPT.read_text(encoding="utf-8")
    del_ = txt.split("# --- kontrollbilder ---")[0]
    ut = G.HIT / "mening_lokal_bygg_rutor.py"
    ut.write_text(del_ + RENDER_SLINGA, encoding="utf-8")
    return ut


def kor_blender(paket_fil: pathlib.Path, jobb: list[dict], utd: pathlib.Path) -> float:
    utd.mkdir(parents=True, exist_ok=True)
    skript = bygg_skript()
    env = dict(os.environ, MENING_JOBB=json.dumps(jobb), MENING_UT=str(utd))
    t0 = time.time()
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(skript), "--", str(paket_fil), str(utd)],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if "MENING_KLAR" not in r.stdout:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise RuntimeError("Blender misslyckades")
    return time.time() - t0


def person_pos(paket, pid, u):
    L = G.ix(paket)
    for sp in paket["rorelse"][pid]:
        U, X = G.X_av(sp)
        if U[0] <= u <= U[-1]:
            i = int(np.argmin([abs(x - u) for x in U]))
            return X[i, L["c_spine2"]]
    return None


def etikett(im, txt):
    cv2.putText(im, txt, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return im


def ark(filer_och_text, ut_namn, h=512):
    kol = []
    for f, t in filer_och_text:
        im = cv2.imread(str(f))
        if im is None:
            im = np.zeros((h, 288, 3), np.uint8)
        w = int(round(im.shape[1] * h / im.shape[0]))
        kol.append(etikett(cv2.resize(im, (w, h)), t))
    cv2.imwrite(str(G.UT / ut_namn), np.hstack(kol))


def main():
    tider = {}
    utd = G.UT / "mening_blender"
    # 1) ga_med_attityd: början/mitt/slut i S1 och S3 genom originalkameran + en sidokamera i S1
    pk = G.KARNA / "ut" / "guacamole" / "manip_ga_med_attityd" / "paket.json"
    paket = json.loads(pk.read_text(encoding="utf-8"))
    jobb = []
    for sid, rutor in (("s1", (2, 44, 87)), ("s3", (140, 164, 189))):
        for u in rutor:
            jobb.append(dict(tagning=sid, ruta=u, fil=f"mening_ga_{sid}_{u:03d}.png"))
    # sidokamera: vinkelrätt mot gångriktningen i S1, 4 m bort, i midjehöjd
    p0, p1 = person_pos(paket, "A", 2), person_pos(paket, "A", 87)
    mitt = (p0 + p1) / 2
    rikt = (p1 - p0)[:2] / (np.linalg.norm((p1 - p0)[:2]) + 1e-9)
    norm = np.array([-rikt[1], rikt[0]])
    cpos = [float(mitt[0] + norm[0] * 4.0), float(mitt[1] + norm[1] * 4.0), 0.9]
    yaw = float(np.degrees(np.arctan2(-norm[1], -norm[0]))) - 90.0
    for u in (2, 23, 44, 66, 87):
        jobb.append(dict(tagning="s1", ruta=u, fil=f"mening_ga_sida_{u:03d}.png",
                         extra=dict(pos=cpos, rot=[90, 0, yaw], orto=2.6, bx=480, by=480, utan_vaggar=True)))
    tider["ga_med_attityd_blender_s"] = round(kor_blender(pk, jobb, utd), 1)
    ark([(utd / f"mening_ga_{sid}_{u:03d}.png", f"{sid.upper()} f={u}") for sid, rr in (("s1", (2, 44, 87)), ("s3", (140, 164, 189))) for u in rr],
        "mening_render_ga_med_attityd.png")
    ark([(utd / f"mening_ga_sida_{u:03d}.png", f"sida f={u}") for u in (2, 23, 44, 66, 87)], "mening_render_ga_sida.png", h=360)
    if "bara_ga" in sys.argv:
        G.spara_json("mening_render_tider_ga.json", tider)
        return

    # 2) byt_hand: rutan med störst räckvidd (145) i S1, original vs manipulerad, kamera + ovanifrån
    for namn, pk in (("orig", G.KARNA / "ut" / "gelato" / "paket.json"),
                     ("byt", G.KARNA / "ut" / "gelato" / "manip_byt_hand" / "paket.json")):
        paket = json.loads(pk.read_text(encoding="utf-8"))
        c = person_pos(paket, "A", 145)
        jobb = [dict(tagning="s1", ruta=145, fil=f"mening_byt_{namn}_kamera_145.png"),
                dict(tagning="s1", ruta=145, fil=f"mening_byt_{namn}_topp_145.png",
                     extra=dict(pos=[float(c[0]), float(c[1]), 4.0], rot=[0, 0, 0], orto=2.0, bx=480, by=480)),
                dict(tagning="s1", ruta=145, fil=f"mening_byt_{namn}_fram_145.png",
                     extra=dict(pos=[float(c[0]), float(c[1]) - 4.0, 1.1], rot=[90, 0, 0], orto=2.0, bx=480, by=480))]
        tider[f"byt_hand_{namn}_blender_s"] = round(kor_blender(pk, jobb, utd), 1)
    ark([(utd / f"mening_byt_{n}_{v}_145.png", f"{'original' if n == 'orig' else 'byt_hand'} {v}")
         for v in ("kamera", "fram", "topp") for n in ("orig", "byt")], "mening_render_byt_hand.png", h=400)
    G.spara_json("mening_render_tider.json", tider)
    print(tider)


if __name__ == "__main__":
    main()
