# -*- coding: utf-8 -*-
"""Mat/B-roll kontra person per tagning. Körs i scen/.venv (OpenAI CLIP ViT-B/32 lokalt, YOLO11n-seg lokalt).

Per tagning läses tre rutor (25, 50, 75 % in i tagningen):
- YOLO11n-seg: personer (antal, största lådans andel av bilden, högsta lådans höjd).
- CLIP noll-skott: sannolikhet för grupperna mat, person, miljö, text över en fast promptlista,
  och platsen (kök, disk, matsal, ute, bil ...). Promptlistan är allmän och skriven en gång.
- Bildvektorn (CLIP) sparas för mattagningar, så att "byt matbilden mot X" kan söka i kundens material.

Klass (mina trösklar, diagnos):
  mat             p_mat >= 0.45 och ingen person över 12 % av bilden
  person_med_mat  person >= 12 % och p_mat >= 0.45
  person          person >= 12 %
  text            p_text >= 0.5
  miljo           annars
Utsnitt ur högsta personlådans höjd: närbild > 0.75, halvbild > 0.45, helbild annars.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from .gemensamt import CLIP_VIKT, YOLO_SEG

PROMPTER = {
    "mat": ["a close-up photo of food on a plate", "a photo of a dish of food", "a close-up of a drink in a glass",
            "food being cooked in a pan", "a close-up of a burger", "a close-up of a pizza", "a bowl of food",
            "a dessert or pastry", "hands preparing food"],
    "person": ["a person talking to the camera", "a person eating food", "people sitting at a table in a restaurant",
               "a waiter serving a customer", "a person standing behind a counter", "a selfie video of a person"],
    "miljo": ["the interior of an empty restaurant", "the outside of a restaurant building", "a city street",
              "a kitchen with no people", "a view of the sea"],
    "text": ["text on a plain colored background", "a screenshot of a phone screen", "a menu with prices"],
}
PLATSER = {
    "kök": "a restaurant kitchen", "disk": "a counter or bar in a restaurant", "matsal": "a dining room with tables",
    "ute": "outdoors on a street or terrace", "bil": "inside a car", "butik": "inside a shop",
    "kontor": "an office or back room", "hemma": "a home living room",
}
MAT_ORD = {  # allmän svensk-engelsk ordlista för CM:s matord, inte bunden till något klipp
    "pizza": "pizza", "pizzan": "pizza", "burgare": "burger", "burgaren": "burger", "hamburgare": "burger",
    "kebab": "kebab", "kebaben": "kebab", "falafel": "falafel", "pita": "pita bread", "tunnbröd": "flatbread wrap",
    "glass": "ice cream", "glassen": "ice cream", "kaffe": "coffee", "kaffet": "coffee", "latte": "latte",
    "pommes": "french fries", "pommesen": "french fries", "sallad": "salad", "salladen": "salad",
    "tårta": "cake", "tårtan": "cake", "bulle": "bun", "bullen": "bun", "kanelbulle": "cinnamon bun",
    "smörgås": "sandwich", "macka": "sandwich", "sushi": "sushi", "pasta": "pasta", "pastan": "pasta",
    "öl": "beer", "ölen": "beer", "vin": "wine", "vinet": "wine", "drink": "cocktail", "drinken": "cocktail",
    "cocktail": "cocktail", "biff": "steak", "biffen": "steak", "kött": "meat", "kyckling": "chicken",
    "fisk": "fish", "räkor": "shrimp", "soppa": "soup", "soppan": "soup", "tacos": "tacos", "nudlar": "noodles",
    "ramen": "ramen", "dessert": "dessert", "efterrätt": "dessert", "frukost": "breakfast", "brunch": "brunch",
    "pannkaka": "pancake", "våffla": "waffle", "korv": "hot dog", "gyros": "gyros", "shawarma": "shawarma",
    "dryck": "a drink", "drycken": "a drink", "juice": "juice", "smoothie": "smoothie", "te": "tea",
}

_m = {}


def _clip():
    if "clip" not in _m:
        import clip
        import torch
        modell, prep = clip.load(str(CLIP_VIKT), device="cpu", jit=False)
        modell.eval()
        _m["clip"] = (modell, prep, torch, clip)
    return _m["clip"]


def _yolo():
    if "yolo" not in _m:
        from ultralytics import YOLO
        _m["yolo"] = YOLO(str(YOLO_SEG))
    return _m["yolo"]


def text_vektorer(texter):
    modell, prep, torch, clip = _clip()
    with torch.no_grad():
        t = modell.encode_text(clip.tokenize(texter))
        t = t / t.norm(dim=-1, keepdim=True)
    return t.numpy()


def bild_vektorer(bilder_bgr):
    from PIL import Image
    modell, prep, torch, clip = _clip()
    x = torch.stack([prep(Image.fromarray(cv2.cvtColor(b, cv2.COLOR_BGR2RGB))) for b in bilder_bgr])
    with torch.no_grad():
        v = modell.encode_image(x)
        v = v / v.norm(dim=-1, keepdim=True)
    return v.numpy()


def _rutor(video, tider):
    from .gemensamt import las_rutor
    return las_rutor(video, tider)


def personer(bilder):
    ut = []
    for b in bilder:
        r = _yolo()(b, verbose=False, classes=[0], conf=0.35)[0]
        H, W = b.shape[:2]
        lador = r.boxes.xyxy.numpy() if r.boxes is not None else np.zeros((0, 4))
        if len(lador) == 0:
            ut.append(dict(antal=0, andel=0.0, hojd=0.0))
            continue
        andel = ((lador[:, 2] - lador[:, 0]) * (lador[:, 3] - lador[:, 1])) / (W * H)
        hojd = (lador[:, 3] - lador[:, 1]) / H
        ut.append(dict(antal=int(len(lador)), andel=float(andel.max()), hojd=float(hojd.max())))
    return ut


def klassa_tagningar(video, tagningar):
    grupper = list(PROMPTER)
    pl = [p for g in grupper for p in PROMPTER[g]]
    gidx = np.array([grupper.index(g) for g in grupper for _ in PROMPTER[g]])
    T = text_vektorer(pl)
    P = text_vektorer(list(PLATSER.values()))
    alla_tider = [tg["fran"] + (tg["till"] - tg["fran"]) * f for tg in tagningar for f in (0.25, 0.5, 0.75)]
    alla = _rutor(video, alla_tider)
    for i, tg in enumerate(tagningar):
        bilder = [b for b in alla[3 * i:3 * i + 3] if b is not None]
        if not bilder:
            continue
        V = bild_vektorer(bilder)
        lg = 100.0 * V @ T.T
        pr = np.exp(lg - lg.max(1, keepdims=True))
        pr /= pr.sum(1, keepdims=True)
        gp = np.array([[pr[i, gidx == k].sum() for k in range(len(grupper))] for i in range(len(bilder))]).mean(0)
        lp = 100.0 * V @ P.T
        pp = np.exp(lp - lp.max(1, keepdims=True))
        pp = (pp / pp.sum(1, keepdims=True)).mean(0)
        pers = personer(bilder)
        p_andel = float(np.median([p["andel"] for p in pers]))
        p_hojd = float(np.median([p["hojd"] for p in pers]))
        antal = int(np.median([p["antal"] for p in pers]))
        p = dict(zip(grupper, [round(float(x), 3) for x in gp]))
        if p["mat"] >= 0.45 and p_andel < 0.12:
            k = "mat"
        elif p_andel >= 0.12 and p["mat"] >= 0.45:
            k = "person_med_mat"
        elif p_andel >= 0.12:
            k = "person"
        elif p["text"] >= 0.5:
            k = "text"
        else:
            k = "miljo"
        utsnitt = None if antal == 0 else ("närbild" if p_hojd > 0.75 else ("halvbild" if p_hojd > 0.45 else "helbild"))
        plats = list(PLATSER)[int(np.argmax(pp))]
        tg.update(klass=k, p=p, personer=dict(antal=antal, storsta_andel=round(p_andel, 3), hojd=round(p_hojd, 3)),
                  utsnitt=utsnitt, plats=dict(gissning=plats, p=round(float(pp.max()), 3)),
                  vektor=[round(float(x), 4) for x in V.mean(0)])
    return tagningar


def matcha_mat(x_text, vektorer):
    """Sannolikhet att varje bildvektor visar X, mot allmänna alternativ. Returnerar lista p(X)."""
    x = MAT_ORD.get(x_text.lower().strip(), x_text)
    T = text_vektorer([f"a photo of {x}", "a photo of food", "a photo of a person", "a photo of a restaurant"])
    V = np.array(vektorer, dtype=np.float32)
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    lg = 100.0 * V @ T.T
    pr = np.exp(lg - lg.max(1, keepdims=True))
    pr /= pr.sum(1, keepdims=True)
    return x, pr[:, 0].tolist()


if __name__ == "__main__":
    import json
    tg = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    for t in klassa_tagningar(sys.argv[1], tg):
        print(t["id"], t.get("klass"), t.get("p"), t.get("personer"), t.get("utsnitt"), t.get("plats"))
