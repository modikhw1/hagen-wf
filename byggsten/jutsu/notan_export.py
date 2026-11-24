"""Adapter: notans plan (kedjans utdata) -> kompakt JSON för 3D Jutsu.

Läser planen och kropparna med kedjans egen funktion (kontrakt/trohet.ruta), så att
lederna hamnar exakt där kedjans Blender lägger dem. Skriver bara under byggsten/jutsu/ut/.

Kör från projektroten:
  scen/.venv/Scripts/python.exe byggsten/jutsu/notan_export.py
"""
import json, sys
from pathlib import Path
import numpy as np

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "scen/3d/kontrakt"))
import trohet  # noqa: E402

PLAN = ROT / "scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json"
KALLA = ROT / "scen/3d/kontrakt/ut/notan_berattat/kalla_mobelintervall.json"
UT = Path(__file__).resolve().parent / "ut/notan/notan_jutsu.json"
STEG = 3  # var tredje ruta = 10 fps

LEDER = ["c_spine0", "c_spine2", "c_neck", "c_head",
         "l_uparm", "l_lowarm", "l_wrist", "r_uparm", "r_lowarm", "r_wrist",
         "l_upleg", "l_lowleg", "l_foot", "r_upleg", "r_lowleg", "r_foot", "l_ball", "r_ball"]
LIX = [trohet.IX[n] for n in LEDER]


def r3(x, n=3): return [round(float(v), n) for v in x]


def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    sem = json.loads(KALLA.read_text(encoding="utf-8"))["semantik"]
    fps = plan["utdata"]["fps_taljare"] / plan["utdata"]["fps_namnare"]

    # Rummet: alla lådor med synlighetsintervall (samma id kan ha flera kopior per scen).
    rum = []
    for o in plan["objekt"]:
        rum.append(dict(id=o["id"], p=r3(o["pos_m"]), rz=round(o["rotation_rad"][2], 4),
                        m=r3(o["matt_m"]), f=o["farg"], s=o.get("synlig_ut", [0, len(plan["kallrutor"])])))

    # Kameran: läge, kvaternion, lins, var tredje ruta plus sista rutan i varje scen.
    from mathutils_lite import mat_till_quat
    kam = []
    nyck = plan["renderkamera"]["nycklar"]
    gransrutor = set()
    for d in plan["scener"]:
        gransrutor |= {d["ut"][0], d["ut"][1] - 1}
    for u, k in enumerate(nyck):
        if u % STEG and u not in gransrutor: continue
        m = np.array(k["matris"])
        kam.append([u] + r3(m[:3, 3]) + r3(mat_till_quat(m[:3, :3]), 4) + [round(k["lins_mm"], 1)])

    # Kropparna: världsleder (m) per ruta, i heltal mm.
    scener = []
    for d in plan["scener"]:
        sc = dict(id=d["id"], ut=d["ut"], personer=[])
        for pm in d["personer"]:
            s = trohet.las_sekvens(pm["rorelse"]); v = dict(np.load(d["varld"]))
            rutor = []
            for u in range(*d["ut"]):
                if (u - d["ut"][0]) % STEG and u != d["ut"][1] - 1: continue
                f = d["lokal_start"] + u - d["ut"][0]
                x = trohet.ruta(d, pm, f, True, (s, v))[LIX]
                rutor.append([u] + [int(round(c * 1000)) for c in x.reshape(-1)])
            sc["personer"].append(dict(id=pm["id"], ankare=pm.get("ankare"), rutor=rutor))
        scener.append(sc)

    personer = {p["id"]: dict(roll=p["roll"], farg=p["farg"]) for p in plan["personer"]}
    repliker = [dict(id=r["id"], talare=r["talare"], text=r["text"], scen=r.get("scen"),
                     a=int(round(r["start_s"] * fps)), b=int(round(r["slut_s"] * fps)))
                for r in sem["repliker"]]
    ut = dict(fps=fps, antal_rutor=len(plan["kallrutor"]), bredd=plan["utdata"]["bredd"],
              hojd=plan["utdata"]["hojd"], sensor_mm=plan["renderkamera"]["sensor_bredd_mm"],
              leder=LEDER, personer=personer, rum=rum, kamera=kam, scener=scener, repliker=repliker,
              kalla=dict(plan=str(PLAN.relative_to(ROT)), kalla=str(KALLA.relative_to(ROT))))
    UT.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(ut, ensure_ascii=False, separators=(",", ":"))
    UT.write_text(txt, encoding="utf-8")
    print(UT, len(txt.encode()), "byte;", "rum", len(rum), "kamera", len(kam),
          "personrutor", sum(len(p["rutor"]) for s in scener for p in s["personer"]), "repliker", len(repliker))


if __name__ == "__main__":
    main()
