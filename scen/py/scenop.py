"""Operationsbank för scen25d.json: semantiska ändringar som spårbara, ångringsbara steg.

Claude (orkestratorn) översätter en mening ("byt pizzan mot hamburgare hos kvinnan") till en eller flera operationer.
Varje operation sparar föregående version (historik/), loggar vad som gjordes och tar tid.

  python py/scenop.py <op> [--nyckel värde ...]
  ops:
    byt_foremal   --var S1|alla|roll:A  --fran <text i klass>  --till <bibliotek-klass>
    flytta        --skikt S1.O2 --dx 0.1 --dy 0          (andel av bildbredd/-höjd)
    dolj | visa   --skikt S1.O1
    spegla        --skikt S4.C
    skala         --skikt S1.O2 --f 1.3
    kamera        --scen S6 --mot S6.A --zoom 1.3        (eller --start x,y,z --slut x,y,z)
    langd         --scen S4 --s 1.5
    flytta_scen   --scen S6 --fore S5 | --sist
    duplicera     --scen S7 --ny S8
    ta_bort_scen  --scen S3
    rorelse       --skikt S1.A --styrka 2.0
    byt_person    --scen S4 --roll A                     (personskiktets bild byts mot rollens bild ur biblioteket)
    angra
"""
import json, sys, time, shutil, copy
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent / "luma" / "d-dialog-notan"
FIL = ROT / "scen25d.json"; HIST = ROT / "historik"; HIST.mkdir(exist_ok=True)

def arg(n, d=None):
    a = sys.argv
    return a[a.index("--" + n) + 1] if "--" + n in a else d

def las(): return json.load(open(FIL, encoding="utf-8"))
def spara(S): json.dump(S, open(FIL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def scen(S, sid): return next(s for s in S["scener"] if s["id"] == sid)
def skikt(S, kid):
    """skikt-id (S1.O2) eller semantisk väljare 'S1:burk' / 'S1:A' (roll) / 'S1:person'"""
    if ":" in kid:
        sid, term = kid.split(":", 1); s = scen(S, sid)
        for k in s["skikt"]:
            if k.get("roll") == term or (k["typ"] == term) or term in (k.get("klass") or ""): return s, k
        raise SystemExit(f"inget skikt som matchar {kid}")
    for s in S["scener"]:
        for k in s["skikt"]:
            if k["id"] == kid: return s, k
    raise SystemExit(f"inget skikt {kid}")
def urval(S, var):
    if var == "alla": return S["scener"]
    if var.startswith("roll:"): return [s for s in S["scener"] if s["vem"] == var[5:]]
    return [scen(S, v) for v in var.split(",")]

def kor(op, S):
    if op == "byt_foremal":
        fran, till = arg("fran"), arg("till"); t = S["bibliotek"]["foremal"][till]; n = 0
        for s in urval(S, arg("var", "alla")):
            for k in s["skikt"]:
                if k["typ"] == "foremal" and fran in k.get("klass", ""):
                    k.setdefault("orig_bild", k["bild"]); k["bild"] = t["bild"]; k["klass"] = till; k["bytt"] = True; n += 1
        return f"bytte {n} st '{fran}' mot '{till}'"
    if op == "flytta":
        _, k = skikt(S, arg("skikt")); k["flytt"] = [round(k.get("flytt", [0, 0])[0] + float(arg("dx", 0)), 4), round(k.get("flytt", [0, 0])[1] + float(arg("dy", 0)), 4)]
        return f"flyttade {k['id']} till {k['flytt']}"
    if op in ("dolj", "visa"):
        _, k = skikt(S, arg("skikt")); k["synlig"] = op == "visa"; return f"{op} {k['id']}"
    if op == "spegla":
        _, k = skikt(S, arg("skikt")); k["spegel"] = not k.get("spegel", False)
        for s in S["scener"]:
            for o in s["skikt"]:
                if o.get("fast_vid") == k["id"]: o["spegel"] = k["spegel"]
        return f"speglade {k['id']}"
    if op == "skala":
        _, k = skikt(S, arg("skikt")); k["skala"] = round(k.get("skala", 1) * float(arg("f")), 3); return f"skala {k['id']} {k['skala']}"
    if op == "kamera":
        s = scen(S, arg("scen"))
        if arg("mot"):
            _, k = skikt(S, arg("mot")); x0, y0, x1, y1 = k["ruta"]; z = float(arg("zoom", 1.3))  # även semantisk väljare
            cx, cy = (x0 + x1) / 2 - 0.5, (y0 + (y1 - y0) * 0.25) - 0.5  # mot övre delen av skiktet (ansiktet för en person)
            s["kamera"] = {"start": {"x": 0, "y": 0, "zoom": 1.0}, "slut": {"x": round(cx * (1 - 1 / z), 3), "y": round(cy * (1 - 1 / z), 3), "zoom": z}, "kalla": "Claude"}
        else:
            p = lambda v: dict(zip(("x", "y", "zoom"), map(float, v.split(","))))
            s["kamera"] = {"start": p(arg("start")), "slut": p(arg("slut")), "kalla": "Claude"}
        return f"kamera {s['id']}: {s['kamera']['start']} -> {s['kamera']['slut']}"
    if op == "langd":
        s = scen(S, arg("scen")); s["langd"] = float(arg("s")); return f"längd {s['id']} {s['langd']} s"
    if op == "flytta_scen":
        s = scen(S, arg("scen")); S["scener"].remove(s)
        if arg("sist"): S["scener"].append(s)
        else: S["scener"].insert(S["scener"].index(scen(S, arg("fore"))), s)
        return f"ordning: {[x['id'] for x in S['scener']]}"
    if op == "duplicera":
        s = scen(S, arg("scen")); ny = copy.deepcopy(s); nid = arg("ny"); ny["id"] = nid
        for k in ny["skikt"]:
            k["id"] = nid + "." + k["id"].split(".", 1)[1]
            if k.get("fast_vid"): k["fast_vid"] = nid + "." + k["fast_vid"].split(".", 1)[1]
        S["scener"].insert(S["scener"].index(s) + 1, ny); return f"duplicerade {s['id']} -> {nid}"
    if op == "ta_bort_scen":
        s = scen(S, arg("scen")); S["scener"].remove(s); return f"tog bort {s['id']}"
    if op == "rorelse":
        _, k = skikt(S, arg("skikt")); k["rorelse_styrka"] = float(arg("styrka")); return f"rörelse {k['id']} ×{k['rorelse_styrka']}"
    if op == "byt_person":
        s = scen(S, arg("scen")); roll = arg("roll"); t = S["bibliotek"]["personer"][roll]
        k = next(k for k in s["skikt"] if k["typ"] == "person")
        k.setdefault("orig_bild", k["bild"]); k["bild"] = t["bild"]; k["roll"] = roll; k["bytt"] = True; s["vem"] = roll
        return f"{s['id']}: personen är nu {roll}"
    if op == "lagg_till":
        # ny instans av en tillgång (person eller föremål) i en scen: fot/botten i (x, y), höjd som andel av bildhöjd, djup z
        s = scen(S, arg("scen")); typ, namn = arg("fran").split(":")  # personer:C / foremal:hamburgare
        t = S["bibliotek"][typ][namn]; import struct
        with open(ROT / t["bild"], "rb") as fh: fh.read(16); bw, bh = struct.unpack(">II", fh.read(8))
        h = float(arg("hojd")); w = h * (bw / bh) * (1024 / 576)  # rutan i andel av bredd/höjd (bild 576x1024)
        x, y = float(arg("x")), float(arg("y"))
        ruta = [round(x - w / 2, 4), round(y - h, 4), round(x + w / 2, 4), round(y, 4)]
        nid = f"{s['id']}.{'P' if typ == 'personer' else 'O'}+{namn}"
        ny = {"id": nid, "typ": "person" if typ == "personer" else "foremal", "roll": namn if typ == "personer" else None,
              "klass": namn if typ == "foremal" else None, "z": float(arg("z", 0.3)), "bild": t["bild"], "ruta": ruta,
              "flytt": [0, 0], "skala": 1.0, "spegel": arg("spegel") == "ja", "synlig": True, "tillagd": True}
        if typ == "personer":  # samma personrörelse som i rollens egen tagning
            for sc in S["scener"]:
                k = next((k for k in sc["skikt"] if k["typ"] == "person" and k.get("roll") == namn and k.get("rorelse")), None)
                if k: ny["rorelse"] = k["rorelse"]; break
        s["skikt"].append(ny); return f"lade till {namn} i {s['id']} vid ({x}, {y}), höjd {h}, z {ny['z']}"
    raise SystemExit("okänd op " + op)

if __name__ == "__main__":
    op = sys.argv[1]; a = time.perf_counter()
    if op == "angra":
        v = sorted(HIST.glob("v*.json"))
        if not v: raise SystemExit("ingen historik")
        shutil.copy(v[-1], FIL); v[-1].unlink(); print("ångrade till", v[-1].name); sys.exit()
    S = las(); n = len(list(HIST.glob("v*.json"))); shutil.copy(FIL, HIST / f"v{n:03d}.json")
    vad = kor(op, S); ms = (time.perf_counter() - a) * 1000
    S.setdefault("logg", []).append({"vem": "Claude", "vad": vad, "op": {"op": op, **{sys.argv[i][2:]: sys.argv[i + 1] for i in range(2, len(sys.argv) - 1, 2)}}, "ms": round(ms, 1)})
    spara(S); print(f"{vad}  ({ms:.1f} ms)")
