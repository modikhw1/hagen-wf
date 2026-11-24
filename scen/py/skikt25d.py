"""2,5D-skikt ur Lumas nyckelbildrutor + källvideons data -> scen25d.json (proof of concept).

Per tagning (klipptider från bankens analys v13):
  bild      : Lumas nyckelbildruta (linjeteckning) eller, om sådan saknas, källbildrutan stiliserad lokalt
  djup      : Depth Anything V2 Small på bilden (1 = nära)
  person    : YOLO11-seg (största personen); tagningens roll ur tagningslistan
  föremål   : YOLO-World (öppet ordförråd) på bilden; mask = ruta ∩ liknande djup, utan personen
  bakgrund  : resten, med hål och vattenmärke ifyllda (inpainting); delas i 'bakgrund' (längre bort än personen)
              och 'forgrund' (närmare än personen, t.ex. bordskanten som ska ligga framför personen)
  rörelse   : personens axelmitt, skala och lutning ur källvideons YOLO-spår, relativt nyckelbildrutans tid
Skikten sparas som utklippta PNG med placering (ruta 0-1), så att de kan flyttas, skalas, bytas och döljas.
Tillgångar: personer och föremål sparas även i ett bibliotek (byten mellan tagningar), plus en hamburgare
stiliserad ur källan (för att kunna ångra Lumas ersättning).

Användning: .venv/Scripts/python.exe py/skikt25d.py
"""
import json, glob, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image

ROT = Path(__file__).resolve().parent.parent
UT = ROT / "luma" / "d-dialog-notan"; SK = UT / "skikt"; SK.mkdir(parents=True, exist_ok=True)
LUMA = Path(r"C:\Users\praiseworthy\Desktop\test\My_first_board")
KALLA = ROT / "klipp" / "d-dialog-notan.mp4"
lista = json.load(open(UT / "tagningslista.json", encoding="utf-8"))
spar = json.load(open(ROT / "data" / "d-dialog-notan" / "spar.json", encoding="utf-8"))
W, H = 576, 1024

NYCKEL = {1: "KF_A_F036", 2: "KF_B_F110", 3: "KF_A_F167", 4: "KF_C_F213", 5: "KF_B_F277", 6: "KF_A_F308", 7: None}
T7 = 12.0  # tagning 7 saknar Luma-bild: källbildruta vid 12,0 s stiliseras

from transformers import pipeline
from ultralytics import YOLO, SAM
sam = SAM(str(Path(__file__).resolve().parent / "modeller" / "sam2.1_t.pt"))
GEM = Path(__file__).resolve().parent.parent / "luma" / "d-dialog-notan" / "gemini_skikt"; GEM.mkdir(parents=True, exist_ok=True)
from simple_lama_inpainting import SimpleLama
lama = SimpleLama()
def fyll(bgr, mask):
    ut = np.array(lama(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), Image.fromarray(mask)))[:H, :W]
    return cv2.cvtColor(ut, cv2.COLOR_RGB2BGR)
djupm = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
seg = YOLO(str(ROT / "py" / "modeller" / "yolo11n-seg.pt"))
vark = YOLO(str(ROT / "py" / "modeller" / "yolov8s-worldv2.pt"))
KLASSER = ["pizza slice", "burger", "paper cup", "drink can", "french fries", "card terminal", "paper tray", "sauce cup"]
SVENSKA = {"pizza slice": "pizzabit", "burger": "hamburgare", "paper cup": "mugg", "drink can": "burk", "french fries": "pommes",
           "card terminal": "kortterminal", "paper tray": "pappersbricka", "sauce cup": "såskopp"}
vark.set_classes(KLASSER)

cap = cv2.VideoCapture(str(KALLA)); FPS = cap.get(cv2.CAP_PROP_FPS)
def kallruta(t):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * FPS))); ok, f = cap.read(); return cv2.resize(f, (W, H))

import sys as _sys, types as _types
_stub = _types.ModuleType("controlnet_aux.mediapipe_face"); _stub.MediapipeFaceDetector = None
_sys.modules["controlnet_aux.mediapipe_face"] = _stub   # nya mediapipe saknar 'solutions'; ansiktsdelen behövs inte
from controlnet_aux import LineartDetector
_lineart = LineartDetector.from_pretrained("lllyasviel/Annotators")

def undertext(bgr):
    """inbränd undertext: mycket ljusa pixlar med mörk kontur i ett horisontellt band (TikTok-stil)"""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY); ljus = (g > 232).astype(np.uint8)
    mork = (cv2.erode(g, np.ones((5, 5), np.uint8)) < 70).astype(np.uint8)
    kand = ljus & cv2.dilate(mork, np.ones((5, 5), np.uint8))
    rad = kand.sum(1); m = np.zeros_like(g)
    for y in range(int(H * 0.25), int(H * 0.85)):
        if rad[y] > 6: m[max(0, y - 6):y + 7] |= cv2.dilate(kand[max(0, y - 6):y + 7], np.ones((9, 25), np.uint8))
    return cv2.dilate(m * 255, np.ones((7, 7), np.uint8))

def stilisera(bgr):
    """lokal linjeteckning (ControlNet lineart-annotator) + dämpad gråton för mörka ytor, likt Lumas stil"""
    rent = fyll(bgr, undertext(bgr))
    lin = _lineart(Image.fromarray(cv2.cvtColor(rent, cv2.COLOR_BGR2RGB)), detect_resolution=768, image_resolution=1024)
    lin = cv2.resize(cv2.cvtColor(np.array(lin), cv2.COLOR_RGB2GRAY), (W, H)).astype(np.float32) / 255
    g = cv2.cvtColor(cv2.bilateralFilter(rent, 9, 60, 9), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    ton = cv2.GaussianBlur(np.clip(0.55 + 0.45 * np.clip((g - 0.08) / 0.5, 0, 1), 0.55, 1.0), (0, 0), 3)  # mjuk ton, bara mörka ytor (testad mot Luma, variant 3 av 3)
    v = (1 - lin * 0.95) * ton
    return np.clip(v[..., None] * np.array([226, 236, 240], np.float32), 0, 255).astype(np.uint8)

def djup(bgr):
    d = djupm(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))["predicted_depth"].squeeze().numpy()
    d = cv2.resize(d, (W, H)); return (d - d.min()) / (d.max() - d.min() + 1e-6)

def _vm1(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY); m = np.zeros((H, W), np.uint8)
    y0, y1 = int(H * 0.84), int(H * 0.96)
    band = g[y0:y1]; m[y0:y1] = ((band > 165) & (band < 228)).astype(np.uint8) * 255
    return m
# 'Luma AI'-märket sitter på samma plats i alla Luma-bilder: union av per-bild-maskerna ger hela bokstäverna
_alla = [cv2.resize(cv2.imread(f), (W, H)) for f in glob.glob(str(LUMA / "*.jpg")) if "Check" not in f]
_rost = np.mean([_vm1(b) > 0 for b in _alla], axis=0)
VM = cv2.morphologyEx(((_rost > 0.35) * 255).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
VM = cv2.dilate(VM, np.ones((13, 13), np.uint8))
def vattenmarke(bgr):
    return VM

def utklipp(bgr, mask, namn):
    namn = namn.translate(str.maketrans("åäöÅÄÖ", "aaoAAO"))  # OpenCV skriver inte icke-ASCII-filnamn på Windows
    ys, xs = np.where(mask > 0)
    if len(xs) < 50: return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = np.dstack([bgr[y0:y1, x0:x1], mask[y0:y1, x0:x1]])
    cv2.imwrite(str(SK / f"{namn}.png"), rgba)
    return {"bild": f"skikt/{namn}.png", "ruta": [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)]}

def huvudspar(a, b):
    """största personens spår i tagningen (källvideon)"""
    yta = {}
    for bb in spar["bilder"]:
        if a <= bb["t"] < b:
            for p in bb["p"]:
                if p["id"] is not None: yta[p["id"]] = yta.get(p["id"], 0) + (p["box"][2] - p["box"][0]) * (p["box"][3] - p["box"][1])
    return max(yta, key=yta.get) if yta else None

def rorelse(a, b, t_kf):
    pid = huvudspar(a, b)
    if pid is None: return None
    rad = []
    for bb in spar["bilder"]:
        if not (a <= bb["t"] < b): continue
        p = next((q for q in bb["p"] if q["id"] == pid), None)
        if not p: continue
        k = p["kp"]
        if k[5][2] < .4 or k[6][2] < .4: continue
        cx, cy = (k[5][0] + k[6][0]) / 2, (k[5][1] + k[6][1]) / 2
        bredd = np.hypot(k[5][0] - k[6][0], k[5][1] - k[6][1])
        vinkel = np.degrees(np.arctan2(k[6][1] - k[5][1], k[6][0] - k[5][0]))
        vinkel = ((vinkel + 90) % 180) - 90   # vänster/höger axel kan byta plats: räkna modulo 180
        rad.append([bb["t"], cx, cy, bredd, vinkel])
    if len(rad) < 3: return None
    r = np.array(rad); r[:, 1:] = np.array([np.median(r[max(0, i - 2):i + 3, 1:], axis=0) for i in range(len(r))])
    i0 = int(np.abs(r[:, 0] - t_kf).argmin()); ref = r[i0]
    v0 = ref[4]
    return {"kalla": "källvideon, YOLO-spår %s (axelmitt, axelbredd, axellutning)" % pid,
            "spar": [[round(x[0] - a, 2), round(x[1] - ref[1], 4), round(x[2] - ref[2], 4), round(x[3] / max(1e-3, ref[3]), 3),
                      round(float(np.clip(((x[4] - v0 + 90) % 180) - 90, -20, 20)), 1)] for x in r]}

scener, bibliotek = [], {"personer": {}, "foremal": {}}
for tg in lista["tagningar"]:
    n = tg["id"]; a, b = tg["in"], tg["ut"]
    if NYCKEL[n]:
        f = glob.glob(str(LUMA / (NYCKEL[n] + "*.jpg")))[0]
        img = cv2.resize(cv2.imread(f), (W, H)); kalla = "luma:" + Path(f).name; t_kf = int(NYCKEL[n].split("_F")[1]) / 30
        img = fyll(img, VM)  # vattenmärket bort ur hela bilden innan något klipps ut
    else:
        img = stilisera(kallruta(T7)); kalla = "lokal stilisering av källan @ %.1fs" % T7; t_kf = T7
    d = djup(img)
    # semantik: Gemini (etiketter + rutor) på bilden; för lokal stilisering används källbilden (samma geometri)
    gfil = GEM / f"S{n}.json"
    if not gfil.exists():
        tmp = GEM / f"S{n}.jpg"; cv2.imwrite(str(tmp), img if NYCKEL[n] else kallruta(T7))
        subprocess.run(["node", str(ROT / "sprak" / "gemini_bild.mjs"), str(tmp), "--ut", str(gfil)], check=True)
    sem = json.load(open(gfil, encoding="utf-8"))["saker"]
    box = lambda s: [s["box_2d"][1] / 1000 * W, s["box_2d"][0] / 1000 * H, s["box_2d"][3] / 1000 * W, s["box_2d"][2] / 1000 * H]
    sak = [s for s in sem if s["kategori"] != "rum"]
    masker = []
    if sak:
        rs = sam(img, bboxes=[box(s) for s in sak], verbose=False)[0]
        masker = [(cv2.resize(m.astype(np.uint8), (W, H)) > 0).astype(np.uint8) * 255 for m in rs.masks.data.cpu().numpy()]
    # person: den största personrutan (tagningens roll); reserv YOLO-seg
    pers = [(s, m) for s, m in zip(sak, masker) if s["kategori"] == "person"]
    pm = np.zeros((H, W), np.uint8)
    if pers:
        pm = max(pers, key=lambda x: x[1].sum())[1]
    else:
        r = seg.predict(img, classes=[0], verbose=False, conf=0.25, retina_masks=True)[0]
        if r.masks is not None and len(r.masks):
            ms = r.masks.data.cpu().numpy(); pm = (cv2.resize(ms[int(np.argmax([m.sum() for m in ms]))], (W, H)) > 0.5).astype(np.uint8) * 255
    pm = cv2.dilate(pm, np.ones((3, 3), np.uint8))
    pz = float(np.median(d[pm > 0])) if pm.any() else 0.5
    # föremål (allt utom personer, möbler och rum) med SAM-mask; möbler blir rumsankare
    fore = []; upptagen = pm.copy()
    par = sorted([(s, m) for s, m in zip(sak, masker) if s["kategori"] not in ("person", "möbel", "rum")], key=lambda x: (x[1] > 0).sum())
    mindre = np.zeros((H, W), np.uint8)
    for s, m in par:
        if s["kategori"] in ("person", "möbel", "rum"): continue
        m = ((m > 0) & (mindre == 0)).astype(np.uint8) * 255   # större föremål (bricka) förlorar det som ligger på dem
        mindre |= m
        m = (m > 0) & ~(pm > 0) if s.get("pa") != "hand" else (m > 0)
        m = m.astype(np.uint8) * 255
        if m.sum() / 255 < 150 or m.sum() / 255 > 0.25 * W * H: continue
        fore.append({"klass": s["etikett"], "kategori": s["kategori"], "karna": s["karna"], "pa": s.get("pa"),
                     "mask": m, "z": float(np.median(d[m > 0])), "yta": int((m > 0).sum())}); upptagen |= m
    # z: det som ligger på ett större föremål ritas ovanför det
    for f_ in fore:
        under = [g_ for g_ in fore if g_["yta"] > f_["yta"] and ((g_["mask"] > 0) & (cv2.dilate(f_["mask"], np.ones((15, 15), np.uint8)) > 0)).any()]
        if under: f_["z"] = max(f_["z"], max(g_["z"] for g_ in under) + 0.01)
    rum = [{"etikett": s["etikett"], "kategori": s["kategori"], "ruta": [round(v, 4) for v in [box(s)[0] / W, box(s)[1] / H, box(s)[2] / W, box(s)[3] / H]],
            "z": round(float(np.median(d[int(box(s)[1]):int(box(s)[3]) + 1, int(box(s)[0]):int(box(s)[2]) + 1])), 3)}
           for s in sem if s["kategori"] in ("rum", "möbel")]
    # bakgrund: fyll i person, föremål och vattenmärke
    hal = cv2.dilate(upptagen, np.ones((15, 15), np.uint8))
    bg = fyll(img, hal)
    nara = ((d > pz + 0.04) & (pm == 0)).astype(np.uint8) * 255      # närmare än personen -> framför
    nara = cv2.morphologyEx(nara, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    skikt = [{"id": f"S{n}.bakgrund", "typ": "bakgrund", "z": 0.0, "kalla": kalla,
              **utklipp(bg, np.full((H, W), 255, np.uint8), f"S{n}_bakgrund")}]
    rol = tg["vem"]
    if pm.any():
        ps = utklipp(img, pm, f"S{n}_person_{rol}")
        if ps:
            skikt.append({"id": f"S{n}.{rol}", "typ": "person", "roll": rol, "z": round(pz, 3), **ps,
                          "rorelse": rorelse(a, b, t_kf), "flytt": [0, 0], "skala": 1.0, "spegel": False, "synlig": True})
            bibliotek["personer"].setdefault(rol, {**ps, "fran": f"S{n}"})
    fg = utklipp(bg, nara, f"S{n}_forgrund")
    if fg: skikt.append({"id": f"S{n}.forgrund", "typ": "forgrund", "z": round(min(1.0, pz + 0.05), 3), **fg})
    for i, fo in enumerate(fore):
        u = utklipp(img, fo["mask"], f"S{n}_foremal_{i}_{fo['klass'][:20].replace(' ', '_')}")
        if u:
            skikt.append({"id": f"S{n}.O{i + 1}", "typ": "foremal", "klass": fo["klass"], "kategori": fo["kategori"], "karna": fo["karna"],
                          "fast_vid": f"S{n}.{rol}" if fo.get("pa") == "hand" else None,
                          "z": round(max(fo["z"], pz + 0.02 if fo.get("pa") == "hand" else fo["z"]) + 0.06, 3),
                          **u, "flytt": [0, 0], "skala": 1.0, "synlig": True})
            bibliotek["foremal"].setdefault(fo["klass"], {**u, "fran": f"S{n}"})
    scener.append({"id": f"S{n}", "orig": {"in": a, "ut": b}, "langd": round(b - a, 2), "takt": tg["takt"], "vem": rol,
                   "replik": tg.get("replik"), "handling": tg["handling"], "utsnitt": tg["utsnitt"],
                   "kamera": {"start": {"x": 0, "y": 0, "zoom": 1.0}, "slut": {"x": 0, "y": 0, "zoom": 1.0}, "kalla": "v13: stilla"},
                   "rum": rum, "skikt": sorted(skikt, key=lambda s: s["z"])})
    print(f"S{n} {kalla[:40]:<40} person {'ja' if pm.any() else 'nej'} z={pz:.2f}  föremål {[f['klass'] + ('*' if f['karna'] else '') for f in fore]}  rum {len(rum)}  förgrund {'ja' if fg else 'nej'}")

# extra tillgång: hamburgare ur källan, stiliserad (för att kunna ångra Lumas pizzabyte)
src = kallruta(1.2); r = vark.predict(src, verbose=False, conf=0.1)[0]
burg = [j for j in range(len(r.boxes)) if KLASSER[int(r.boxes.cls[j])] == "burger"]
if burg:
    j = max(burg, key=lambda j: float(r.boxes.conf[j])); x0, y0, x1, y1 = [int(v) for v in r.boxes.xyxy[j].tolist()]
    st = stilisera(src); m = np.zeros((H, W), np.uint8); m[y0:y1, x0:x1] = 255
    u = utklipp(st, m, "tillgang_hamburgare")
    bibliotek["foremal"]["hamburgare"] = {**u, "fran": "källan 1,2 s, lokalt stiliserad"}
    print("tillgång hamburgare:", u["ruta"])

ut = {"version": "scen25d v0", "klipp": lista["klipp"], "storlek": [W, H], "roller": lista["roller"],
      "bibliotek": bibliotek, "scener": scener, "logg": [{"vem": "skikt25d.py", "vad": "byggd ur Luma-nyckelbildrutor + källdata"}]}
json.dump(ut, open(UT / "scen25d.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("->", UT / "scen25d.json")
