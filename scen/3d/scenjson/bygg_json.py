"""Bygg scen/0.1-filerna från frysta, redovisade mätpunkter och källdata."""
from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np

HIT = Path(__file__).resolve().parent
ROOT = HIT.parents[2]
W, H, F = 576, 1024, 1024.0


def skriv(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def punktrotera_y(p, pivot, grader):
    a = math.radians(grader)
    c, s = math.cos(a), math.sin(a)
    d = np.asarray(p, float) - np.asarray(pivot, float)
    q = np.array([c * d[0] + s * d[2], d[1], -s * d[0] + c * d[2]])
    return np.asarray(pivot, float) + q


def fov():
    return {
        "horisontell": round(math.degrees(2 * math.atan(W / (2 * F))), 3),
        "vertikal": round(math.degrees(2 * math.atan(H / (2 * F))), 3),
    }


def scen(s: str) -> dict:
    cfg = {
        "S1": {
            "helruta": 36,
            "lokal": 36,
            "tid": 1.2,
            "start": 0,
            "sam": 0,
            "h": 1.45,
            "pitch": -28.25,
            "roll": 3.1,
            "hip": [0.0890, 0.3930, 1.1358],
            "eyes": [0.0668, 1.0845, 1.0340],
            "head": [0.0768, 0.9831, 1.0821],
            "feet": [[0.1593, 0.0354, 0.5951], [-0.1801, 0.0344, 0.6748]],
            "yaw": -10.194,
            "length": 1.728,
            "length_source": "MHR:s nominella viloskelett 1,728 m; benen är osynliga och längden är därför osäkrare än bildpassningen",
        },
        "S4": {
            "helruta": 213,
            "lokal": 42,
            "tid": 7.1,
            "start": 171,
            "sam": 1,
            "h": 1.585,
            "pitch": -7.13,
            "roll": -1.3,
            "hip": [-0.0774, 1.0235, 1.7331],
            "eyes": [-0.0117, 1.7574, 1.6564],
            "head": [-0.0555, 1.6836, 1.7294],
            "feet": [[0.0821, 0.0, 1.7378], [-0.2506, 0.015, 1.6750]],
            "yaw": 9.809,
            "length": 1.734,
            "length_source": "Wan-format A:s råa MHR-längd 1,734 m; benen är synliga och båda fötterna har sammanhängande kontakt",
        },
    }[s]

    sam_path = ROOT / "scen/3d/lasformat/luma-paket/poang/kropp/p" / f"{cfg['sam']:04d}.npz"
    raw = np.load(sam_path)
    sam_t = np.asarray(raw["pred_cam_t"], float)
    # SAM:s translationspunkt uttryckt i scenens y-upp-system. Den punkten används
    # endast för avståndsmåttet; den är inte samma anatomiska punkt som höften.
    # Samma kamerarumsvektor i världens/gravitationsrätade koordinater. Blender-
    # källans kamera använder M = G @ Rw @ F och JSON byter (x, djup, höjd)
    # till (x, höjd över golv, djup).
    V = np.load(ROOT / f"scen/3d/ingest/ut/notan-tagningar/{s}/varld.npz")
    u = V["upp"] / np.linalg.norm(V["upp"])
    zz = np.array([0.0, 0.0, 1.0])
    vv = np.cross(u, zz)
    cc = float(np.dot(u, zz))
    vx = np.array([[0, -vv[2], vv[1]], [vv[2], 0, -vv[0]], [-vv[1], vv[0], 0]])
    G = np.eye(3) + vx + vx @ vx / (1 + cc)
    M = G @ V["kam_R"][cfg["lokal"]] @ np.diag([1.0, -1.0, -1.0])
    wb = M @ np.array([sam_t[0], -sam_t[1], -sam_t[2]])
    sam_p = [float(wb[0]), float(wb[2] + cfg["h"]), float(wb[1])]
    sam_avstand = float(np.linalg.norm(sam_t))

    gemensam = {
        "version": "scen/0.1",
        "kalla": {
            "klipp": "scen/klipp/d-dialog-notan.mp4",
            "ruta": cfg["helruta"],
            "tid_s": cfg["tid"],
            "tagning": f"scen/3d/ingest/ut/notan-tagningar/{s}",
            "tagning_start_ruta": cfg["start"],
            "lokal_ruta": cfg["lokal"],
            "originalbild": f"scen/3d/lasformat/luma-paket/indata/bild/{s}.png",
        },
        "koordinater": {
            "enhet": "meter",
            "handedness": "högerhänt",
            "axlar": {"x": "höger", "y": "upp", "z": "framåt längs originalkamerans horisontella blickriktning"},
            "origo": "golvet lodrätt under originalkameran",
        },
        "kamera": {
            "position": [0.0, cfg["h"], 0.0],
            "pitch_grader": cfg["pitch"],
            "roll_grader": cfg["roll"],
            "fokal_px": F,
            "bild_px": [W, H],
            "fov_grader": fov(),
            "linsmodell": "pinhole, huvudpunkt i bildcentrum",
        },
        "skala": {
            "ankare": "SAM 3D Body pred_cam_t för exakt keyframe samt MHR-kroppens längd",
            "sam_kamera_person_avstand_m": round(sam_avstand, 4),
            "sam_translation_punkt_m": [round(x, 4) for x in sam_p],
            "kroppslangd_m": cfg["length"],
            "kroppslangd_kalla": cfg["length_source"],
            "osakerhet_m": 0.08 if s == "S1" else 0.05,
            "osakerhet": "måttlig: direkt enbildskroppsmått är stabilt för jämförelse men inte ett måttband; rumsdjupet är svagare",
        },
        "golv": {
            "plan": {"normal": [0.0, 1.0, 0.0], "d": 0.0},
            "kamerahojd_m": cfg["h"],
            "metod": (
                "MoGe-planets bildläge, skalat mot SAM-personen; golvet är skymt, så kamerahöjd 1,45 m och sitt-/stolshöjd används"
                if s == "S1"
                else "Originalets MoGe-plan i bildläge, metrisk höjd härledd med Wan-format A:s synliga fötter och 1,734 m kropp"
            ),
            "status": "antagen" if s == "S1" else "harledd",
        },
        "personer": [
            {
                "id": "huvudperson",
                "ingest_id": 1,
                "roll": "kvinna vid bord" if s == "S1" else "servitör",
                "ogon": [round(x, 4) for x in cfg["eyes"]],
                "huvud": [round(x, 4) for x in cfg["head"]],
                "hoft": [round(x, 4) for x in cfg["hip"]],
                "fotter": {
                    "positioner": [[round(x, 4) for x in p] for p in cfg["feet"]],
                    "synliga": s == "S4",
                    "status": "antagen från sittpose/stol" if s == "S1" else "härledda från Wan-format A",
                },
                "sam_translation_punkt_m": [round(x, 4) for x in sam_p],
                "riktning_grader": cfg["yaw"],
                "riktning_konvention": "0 = vänd mot kameran; positivt = åt personens egen högra sida",
                "langd_m": cfg["length"],
                "pose_kalla": {
                    "fil": f"scen/3d/ingest/ut/notan-tagningar/{s}/sekvens_1.npz",
                    "lokal_ruta": cfg["lokal"],
                    "exakt_sam_fil": f"scen/3d/lasformat/luma-paket/poang/kropp/p/{cfg['sam']:04d}.npz",
                    "blender_kalla": f"scen/3d/ingest/ut/notan-tagningar/{s}/scen.blend",
                },
            }
        ],
        "mobler": [],
        "foremal": [],
        "vaggar": [],
        "kvalitet": {
            "kamera.fokal": {"status": "matt", "stod": "SAM-körningens uttryckliga fokal 1024 px"},
            "kamera.pitch_roll": {"status": "harledd", "stod": "ingestens gravitationsrotation från kropparna"},
            "skala.avstand": {"status": "matt", "stod": "SAM pred_cam_t på exakt originalruta"},
            "person.pose": {"status": "matt", "stod": "SAM/MHR på exakt lokal ruta"},
            "person.riktning": {"status": "harledd", "stod": "SAM global_rot runt lodaxeln"},
            "rum": {"status": "harledd", "stod": "MoGe + öppna objektboxar i originaltagningen; enkelbild, ingen parallax"},
            "osynligt_bakom_kameran": {"status": "antagen", "stod": "golv och närmaste väggar för den bakåtflyttade kamerans nya synfält"},
        },
    }

    if s == "S1":
        gemensam["mobler"] = [
            {"id": "bord", "typ": "låda", "centrum": [0.012, 0.399, 0.668], "storlek": [0.514, 0.797, 0.255], "vridning_grader": -5.7, "status": "harledd"},
            {"id": "stol_huvudperson", "typ": "låda", "centrum": [0.08, 0.47, 1.08], "storlek": [0.50, 0.08, 0.48], "vridning_grader": 0.0, "status": "antagen"},
        ]
        gemensam["foremal"] = [
            {"id": "burk", "typ": "låda", "centrum": [-0.14, 0.91, 0.61], "storlek": [0.07, 0.22, 0.07], "status": "harledd"},
            {"id": "mugg", "typ": "låda", "centrum": [-0.045, 0.94, 0.63], "storlek": [0.10, 0.28, 0.10], "status": "harledd"},
            {"id": "hamburgare", "typ": "låda", "centrum": [0.055, 0.84, 0.57], "storlek": [0.16, 0.11, 0.14], "status": "harledd"},
        ]
        gemensam["vaggar"] = [
            {"id": "bakvagg", "typ": "låda", "centrum": [0.0, 1.55, 3.4], "storlek": [5.0, 3.1, 0.08], "vridning_grader": 0.0, "status": "antagen"},
            {"id": "vanster_vagg", "typ": "låda", "centrum": [-2.45, 1.55, 1.2], "storlek": [0.08, 3.1, 4.5], "vridning_grader": 0.0, "status": "antagen"},
        ]
    else:
        gemensam["personer"].append({
            "id": "gast_vanster",
            "ingest_id": 4,
            "roll": "sittande gäst i bakgrunden",
            "ogon": [-0.80, 1.25, 3.45],
            "huvud": [-0.80, 1.30, 3.48],
            "hoft": [-0.82, 0.63, 3.50],
            "fotter": {"positioner": [[-0.65, 0.0, 2.95], [-0.92, 0.0, 3.15]], "synliga": True, "status": "harledd"},
            "riktning_grader": -10.0,
            "langd_m": 1.728,
            "pose_kalla": {"fil": "scen/3d/ingest/ut/notan-tagningar/S4/sekvens_4.npz", "lokal_ruta": 42, "blender_kalla": "scen/3d/ingest/ut/notan-tagningar/S4/scen.blend"},
        })
        gemensam["mobler"] = [
            {"id": "bord_vanster", "typ": "låda", "centrum": [-0.663, 0.385, 2.633], "storlek": [0.384, 0.770, 0.593], "vridning_grader": -78.9, "status": "harledd"},
            {"id": "stol_fram_hoger", "typ": "låda", "centrum": [0.373, 0.410, 1.584], "storlek": [0.228, 0.819, 0.234], "vridning_grader": -129.8, "status": "harledd"},
            {"id": "stol_bak_hoger", "typ": "låda", "centrum": [0.965, 0.265, 3.69], "storlek": [0.36, 0.53, 1.14], "vridning_grader": -35.0, "status": "harledd"},
        ]
        gemensam["foremal"] = [
            {"id": "terminal_mobil", "typ": "låda", "centrum": [-0.68, 0.81, 2.55], "storlek": [0.16, 0.025, 0.08], "status": "harledd"}
        ]
        gemensam["vaggar"] = [
            {"id": "bakvagg", "typ": "låda", "centrum": [0.0, 1.55, 5.6], "storlek": [5.0, 3.1, 0.10], "vridning_grader": 0.0, "status": "harledd"},
            {"id": "vanster_vagg", "typ": "låda", "centrum": [-2.1, 1.55, 2.8], "storlek": [0.10, 3.1, 5.6], "vridning_grader": 0.0, "status": "harledd"},
        ]
    return gemensam


def andrad(original: dict) -> dict:
    d = deepcopy(original)
    p = d["personer"][0]
    old_cam = np.asarray(d["kamera"]["position"], float)
    new_cam = old_cam + np.array([0.0, 0.0, -1.0])
    old_sam = np.asarray(p["sam_translation_punkt_m"], float)
    hip = np.asarray(p["hoft"], float)
    new_sam = punktrotera_y(old_sam, hip, 20.0)
    old_dist = float(np.linalg.norm(old_sam - old_cam))
    new_dist = float(np.linalg.norm(new_sam - new_cam))
    d["kamera"]["position"] = [round(x, 4) for x in new_cam]
    p["riktning_grader"] = round(float(p["riktning_grader"] + 20.0), 3)
    p["sam_translation_punkt_m"] = [round(float(x), 4) for x in new_sam]
    d["andring"] = {
        "ordning": ["kamera", "huvudperson"],
        "kamera": {"translation_m": [0.0, 0.0, -1.0], "beskrivning": "1,0 m bakåt; samma höjd, pitch, roll och fokal"},
        "huvudperson": {"rotation_grader": 20.0, "axel": [0.0, 1.0, 0.0], "pivot": "hoft", "riktning": "egen högra sida", "pose_i_ovrigt": "oförändrad"},
        "avstandsmal": {
            "original_sam_avstand_m": round(old_dist, 4),
            "andrat_sam_avstand_m": round(new_dist, 4),
            "forandring_m": round(new_dist - old_dist, 4),
            "forklaring": "exakt euklidiskt mål efter både kameratranslation och rotation av SAM:s translationspunkt runt höften",
        },
    }
    return d


def main():
    for s in ("S1", "S4"):
        o = scen(s)
        skriv(HIT / f"{s}.json", o)
        skriv(HIT / f"{s}_andrad.json", andrad(o))
        print(s, "avstånd", o["skala"]["sam_kamera_person_avstand_m"], "mål", andrad(o)["andring"]["avstandsmal"])


if __name__ == "__main__":
    main()
