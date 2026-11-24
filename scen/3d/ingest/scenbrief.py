"""Bygger och granskar scenbriefen mellan ingest och deklarationsöversättningen.

Bygg paket (enbart befintlig ingest-cache):
    python scenbrief.py bygg ingest/ut/<klipp>

Granska förslag:
    python scenbrief.py granska ingest/ut/<klipp> <deklaration.json>

Kommandot startar inga modelljobb och ändrar aldrig en källdeklaration.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np


HIT = Path(__file__).resolve().parent
STATUS = {"antagen", "last", "deklarerad"}
STATUS_ALIAS = {"agare": "deklarerad", "uppmatt": "last", "modellbedomd": "last"}
TAL = {"type": "number"}
INTERVALL = {
    "oneOf": [
        TAL,
        {"type": "array", "items": TAL, "minItems": 2, "maxItems": 2},
    ]
}


def las_json(fil: Path, standard: Any = None) -> Any:
    # Äldre ingestfiler (tagningar.json, status.json) är sparade i cp1252.
    for kodning in ("utf-8", "cp1252"):
        try:
            return json.loads(fil.read_text(encoding=kodning))
        except UnicodeDecodeError:
            continue
        except (OSError, ValueError):
            break
    return copy.deepcopy(standard)


def skriv_json(fil: Path, data: Any) -> None:
    fil.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def deklarationsschema() -> dict[str, Any]:
    """Format 0.8 så som deklaration_till_hand.py faktiskt läser det.

    Beskrivande extrafält är tillåtna eftersom översättaren medvetet ignorerar dem.
    Validatorns proveniensregler ligger utanför JSON Schema: de beror på status i
    närmaste överordnade objekt och kan därför inte uttryckas begripligt här.
    """
    # Äldre deklarationer ligger kvar som 0.7 och använder agare/sedd/intervall.
    # De är syntaktiskt översättningsbara, men proveniensvalidatorn kräver de
    # tre nya orden för varje tal i nya förslag.
    status = {"type": "string", "enum": sorted(STATUS | {"agare", "sedd", "intervall", "uppmatt", "modellbedomd"})}
    punkt = {"type": "array", "items": TAL, "minItems": 3, "maxItems": 3}
    mittpunkt = {"type": "array", "items": INTERVALL, "minItems": 3, "maxItems": 3}
    plats = {
        "type": "object",
        "required": ["typ"],
        "properties": {
            "typ": {"type": "string", "enum": ["sits", "staplats", "bord"]},
            "pos_m": {"oneOf": [punkt, {"type": "null"}]},
            "mitt_m": mittpunkt,
            "blick_grader": TAL,
            "sitthojd_m": INTERVALL,
            "hofthojd_m": TAL,
            "roll": {"type": "string"},
            "status": status,
            "kalla": {"type": "string"},
            "las": {
                "type": "object",
                "required": ["kamera_vid", "tagning"],
                "properties": {"kamera_vid": {"type": "string"}, "tagning": {"type": "string"}},
            },
            "framfor": {"type": "string"},
            "hojd_regel": {"type": "string"},
            "roller": {"type": "array", "items": {"type": "string"}},
            "massiv": {"type": "boolean"},
            "storlek_m": {
                "type": "object",
                "required": ["langs_x", "langs_y", "hojd"],
                "properties": {"langs_x": INTERVALL, "langs_y": INTERVALL, "hojd": INTERVALL},
            },
        },
        "additionalProperties": True,
    }
    kamera = {
        "type": "object",
        "properties": {
            "huvudroll": {"type": "string"},
            "spar_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
            "person_plats": {"type": "string"},
            "kamera_vid": {"type": "string"},
            "hojd_m": INTERVALL,
            "hojd_status": status,
            "hojd_kalla": {"type": "string"},
            "xy_m": {
                "oneOf": [
                    {"type": "array", "items": INTERVALL, "minItems": 2, "maxItems": 2},
                    {"type": "object", "properties": {"x": INTERVALL, "y": INTERVALL}},
                ]
            },
            "status": status,
        },
        "additionalProperties": True,
    }
    roll = {
        "type": "object",
        "required": ["tagningar", "lage"],
        "properties": {
            "beskrivning": {"type": "string"},
            "tagningar": {"type": "array", "items": {"type": "string"}},
            "lage": {"type": "string", "enum": ["står", "sitter"]},
            "hofthojd_m": TAL,
            "status": status,
            "kalla": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "deklaration-0.8.schema.json",
        "title": "Scendeklaration 0.8",
        "description": "Inmatning som ingest/deklaration_till_hand.py accepterar 12 november 2026.",
        "type": "object",
        "required": ["schema_version", "klipp", "datum", "golv", "kameror", "roller", "platser", "relevans"],
        "properties": {
            "schema_version": {"type": "string", "enum": ["deklaration/0.8", "deklaration/0.7"]},
            "klipp": {"type": "string", "minLength": 1},
            "datum": {"type": "string"},
            "golv": {
                "type": "object",
                "required": ["hojd_m", "status"],
                "properties": {"hojd_m": INTERVALL, "status": status, "kalla": {"type": "string"}},
                "additionalProperties": True,
            },
            "berattat_rum": {"type": "object"},
            "avslojat_rum": {"type": "object"},
            "vaggar": {"type": "object"},
            "kameror": {
                "type": "object",
                "patternProperties": {"^S[0-9]+$": kamera},
                "additionalProperties": True,
            },
            "roller": {
                "type": "object",
                "additionalProperties": {"oneOf": [roll, {"type": "string"}]},
            },
            "platser": {"type": "object", "minProperties": 1, "additionalProperties": plats},
            "narvaro": {"type": "object"},
            "relevans": {
                "type": "object",
                "required": ["bar_scenen", "satter_rummet", "stryks"],
                "properties": {
                    n: {
                        "type": "object",
                        "required": ["saker"],
                        "properties": {"saker": {"type": "array", "items": {"type": "string"}}},
                    }
                    for n in ("bar_scenen", "satter_rummet", "stryks")
                },
            },
        },
        "additionalProperties": True,
    }


def _bildtext(bild: np.ndarray, text: str) -> np.ndarray:
    bild = bild.copy()
    cv2.rectangle(bild, (0, 0), (bild.shape[1], 42), (0, 0, 0), -1)
    cv2.putText(bild, text, (12, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)
    return bild


def _passa(bild: np.ndarray, bredd: int = 480, hojd: int = 300) -> np.ndarray:
    h, w = bild.shape[:2]
    skala = min(bredd / w, hojd / h)
    b = cv2.resize(bild, (max(1, round(w * skala)), max(1, round(h * skala))))
    duk = np.full((hojd, bredd, 3), 28, np.uint8)
    y, x = (hojd - b.shape[0]) // 2, (bredd - b.shape[1]) // 2
    duk[y:y + b.shape[0], x:x + b.shape[1]] = b
    return duk


def _hamta_nyckelrutor(ingest: Path, tagning: dict[str, Any], antal: int = 4) -> list[tuple[int, np.ndarray]]:
    """Läser enbart den redan segmenterade klippcachen, med bildcache som reserv."""
    tid = tagning["id"]
    video = ingest / "klipp" / f"{tid}.mp4"
    ut: list[tuple[int, np.ndarray]] = []
    if video.exists():
        cap = cv2.VideoCapture(str(video))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for lokal in np.linspace(0, max(0, n - 1), min(antal, max(1, n)), dtype=int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(lokal))
            ok, bild = cap.read()
            if ok:
                ut.append((int(tagning.get("start", 0)) + int(lokal), bild))
        cap.release()
    if ut:
        return ut
    # Äldre ingest kan sakna delklipp men ha granskningens cachade nyckelbilder.
    kandidater = sorted((ingest / "granska").glob(f"{tid}_*.jpg"))
    kandidater += sorted((ingest / "semantik" / "blad").glob(f"{tid}.*"))
    for i, fil in enumerate(kandidater[:antal]):
        bild = cv2.imread(str(fil))
        if bild is not None:
            ut.append((int(tagning.get("start", 0)) + i, bild))
    return ut


def bygg_kontaktblad(ingest: Path, brief: Path, tagningar: list[dict[str, Any]]) -> list[str]:
    oversiktsrutor, saknas = [], []
    for t in tagningar:
        rutor = _hamta_nyckelrutor(ingest, t)
        if not rutor:
            saknas.append(t["id"])
            continue
        celler = [_bildtext(_passa(b), f'{t["id"]} · ruta {nr}') for nr, b in rutor]
        blad = np.hstack(celler)
        cv2.imwrite(str(brief / f'kontakt_{t["id"]}.jpg'), blad, [cv2.IMWRITE_JPEG_QUALITY, 92])
        mitten_nr, mitten = rutor[len(rutor) // 2]
        oversiktsrutor.append(_bildtext(_passa(mitten, 360, 225), f'{t["id"]} · ruta {mitten_nr}'))
    if oversiktsrutor:
        kol = min(3, len(oversiktsrutor)); rad = math.ceil(len(oversiktsrutor) / kol)
        tom = np.full_like(oversiktsrutor[0], 28)
        oversikt = np.vstack([np.hstack((oversiktsrutor + [tom] * (rad * kol - len(oversiktsrutor)))[r * kol:(r + 1) * kol]) for r in range(rad)])
        cv2.imwrite(str(brief / 'kontakt_oversikt.jpg'), oversikt, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return saknas


def _semantik(ingest: Path) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    sem = las_json(ingest / "semantik" / "semantik.json", {}) or {}
    data = sem.get("data", {}) if isinstance(sem, dict) else {}
    spar: dict[tuple[str, str], dict[str, Any]] = {}
    plac = {x.get("person"): x for x in data.get("placeringar", []) if isinstance(x, dict)}
    for person in data.get("personer", []):
        for s in person.get("spar", []):
            spar[(s.get("tagning"), str(s.get("spar_id")))] = {
                "person": person.get("id"), "beskrivning": person.get("beskrivning"),
                "hallning": (plac.get(person.get("id")) or {}).get("hallning"),
                "kalla": "semantik/semantik.json (modellbedömd)",
            }
    return data, spar


def _kroppsmatt(mapp: Path, pid: str, meta: dict[str, Any], rutor: dict[str, Any]) -> dict[str, Any]:
    filer = sorted((mapp / "kropp" / pid).glob("*.npz"))
    if not filer:
        return {"status": "saknas", "orsak": "Ingen cachad kroppsläsning."}
    hoftavstand, ogonavstand, ogonhojd = [], [], []
    fot_i_ruta = 0
    for fil in filer:
        try:
            d = np.load(fil); K = d["pred_keypoints_3d"] + d["pred_cam_t"]
            k2 = d["pred_keypoints_2d"]
        except (KeyError, OSError, ValueError):
            continue
        hoft = K[[9, 10]].mean(0); ogon = K[[1, 2]].mean(0)
        hoftavstand.append(float(np.linalg.norm(hoft))); ogonavstand.append(float(np.linalg.norm(ogon)))
        box = rutor.get(str(int(fil.stem)))
        syn = False
        if box:
            for x, y in k2[15:21]:
                if 0 <= x < meta.get("bredd", 0) and 0 <= y < meta.get("hojd", 0) and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                    syn = True; break
        fot_i_ruta += int(syn)
        # Kroppens egen lodriktning ger ögon över lägsta modellerade fot. Värdet
        # publiceras bara när fotpunkterna faktiskt har bildstöd.
        lod = K[69] - K[[13, 14]].mean(0)
        norm = np.linalg.norm(lod)
        if norm > 1e-9:
            lod /= norm
            ogonhojd.append(float(ogon @ lod - np.min(K[15:21] @ lod) + 0.025))
    n = len(hoftavstand)
    if not n:
        return {"status": "saknas", "orsak": "Kroppscachen kunde inte läsas."}
    andel = fot_i_ruta / n
    return {
        "status": "last",
        "kalla": f"{mapp.name}/kropp/{pid}/*.npz och personer.json",
        "kamera_till_hoft_m": round(float(np.median(hoftavstand)), 3),
        "kamera_till_ogon_m": round(float(np.median(ogonavstand)), 3),
        "synliga_fotter": {
            "andel_rutor_med_fotpunkt_i_bild_och_personruta": round(andel, 3),
            "bedomning": bool(andel >= 0.5),
            "not": "2D-fotpunkt i egen personruta är bildstöd, inte en ocklusionsmask.",
        },
        "ogonhojd_m": round(float(np.median(ogonhojd)), 3) if andel >= 0.5 and ogonhojd else None,
        "ogonhojd_not": "Relativ till lägsta modellerade fot; utelämnas utan synliga fötter.",
    }


def _rumsobjekt(mapp: Path) -> dict[str, Any]:
    rum = las_json(mapp / "rum.json", {}) or {}
    objekt = rum.get("objects", []) if isinstance(rum, dict) else []
    return {
        "status": "last" if objekt else "saknas",
        "kalla": f"{mapp.name}/rum.json",
        "objekt": objekt,
        "not": None if objekt else "Rumstegets cache innehåller inga godkända objekt.",
    }


def bygg_lasning(ingest: Path, tagningar: list[dict[str, Any]]) -> dict[str, Any]:
    sem, sem_spar = _semantik(ingest)
    repliker = sem.get("repliker", []) if sem else []
    texter = sem.get("skarmtext", []) if sem else []
    ordtider = las_json(ingest / "semantik" / "ordtider.json", {}) or {}
    per = {}
    for t in tagningar:
        tid, mapp = t["id"], ingest / t["id"]
        meta = las_json(mapp / "meta.json", {}) or {}
        personer = las_json(mapp / "personer_matning.json", None)
        if personer is None:
            personer = las_json(mapp / "personer.json", {}) or {}
        spar = []
        for pid, rutor in personer.items():
            nycklar = sorted(int(x) for x in rutor) if rutor else []
            semrad = sem_spar.get((tid, str(pid)), {})
            spar.append({
                "spar_id": str(pid), "rutor": len(rutor),
                "forsta_ruta": nycklar[0] if nycklar else None, "sista_ruta": nycklar[-1] if nycklar else None,
                "identitet_och_hallning": semrad or {"status": "saknas", "orsak": "Ingen semantikcache för identitet/hållning."},
                "kropp": _kroppsmatt(mapp, str(pid), meta, rutor),
            })
        tal = [x for x in repliker if x.get("tagning") == tid]
        text = [x for x in texter if x.get("tagning") == tid]
        per[tid] = {
            "globala_rutor": [t.get("start"), t.get("slut")], "fps": (las_json(ingest / "tagningar.json", {}) or {}).get("fps"),
            "personspar": spar,
            "rumsobjekt": _rumsobjekt(mapp),
            "skarmtext": {"status": "last", "kalla": "semantik/semantik.json", "poster": text} if text else {"status": "saknas", "orsak": "Ingen cachad skärmtext för tagningen."},
            "tal": {"status": "last", "kalla": "semantik/ordtider.json och semantik.json", "repliker": tal} if tal else {"status": "saknas", "orsak": "Inga cachade taltider för tagningen."},
        }
    return {
        "schema_version": "scenbrief-lasning/1",
        "klipp": ingest.name,
        "princip": "Endast redan cachad ingest-utdata. Saknade cachefält har inte räknats om med modeller.",
        "tagningar": per,
        "taltider_cache": {"finns": bool(ordtider), "ursprung": ordtider.get("ursprung") if isinstance(ordtider, dict) else None},
    }


UPPDRAG = """# Uppdrag: föreslå scenens deklaration

Du får ett självständigt paket med kontaktblad, `lasning.json` och `deklaration.schema.json`.
Läs alla tagningar tillsammans. Föreslå `forslag_deklaration.json` i format `deklaration/0.8` utan att hitta på mätningar.

## Det du ska avgöra

1. **Rumshypotes:** vilka tagningar delar rum och kamerauppställning; vilka personspår är samma person över tagningar; hur personerna står eller sitter i förhållande till varandra när bara en syns.
2. **Relevans i tre nivåer:** `bar_scenen` (bevaras exakt), `satter_rummet` (enkel geometri) och `stryks` (utelämnas).
3. **Öppna ägarfrågor:** skriv vad bilderna och läsningarna inte kan avgöra, särskilt identiteter, dold geometri, verkliga mått och berättelsens avsikt.

## Proveniens är obligatorisk

Varje numeriskt värde ska markeras i sitt objekt som exakt en av:

- `antagen`: gissning. Använd `[min, max]`, aldrig ett hårt tal, där 0.8-formatet tillåter intervall.
- `last`: hämtat ur `lasning.json`. Ange `kalla` eller fältspecifik `*_kalla` med exakt JSON-sökväg.
- `deklarerad`: uttryckligen sagt av ägaren, inte slutsats från bild.

## Ett rum, en ram, namn som kedjan kräver

- Alla `pos_m` och `mitt_m` ligger i en gemensam ram i meter (golvet z = 0). Lägg inte uppställningar som öar långt isär. Är det inbördes läget okänt, gissa ett rimligt läge i samma lokal och märk det `antagen`.
- Roller som syns i bild heter `A`, `B`, `C` … i den ordning de först syns; lägg personens namn i fältet `namn`.
- En rolls hemplats heter `staplats_<roll>` (stående) eller `stol_<roll>` (sittande). Övriga platser där rollen står har `roll: null` och anges via `kameror.<S>.person_plats`.
- Föremål som står på en möbel (våg, kassa, tallrik) är inga platser; formatet saknar staplade föremål, så beskriv dem under `relevans`.

Använd `hojd_status` för `kameror.*.hojd_m` och annars `status` på närmaste objekt. Hårda antagna tal är bara tillåtna för fält där översättaren kräver ett skalärt värde (t.ex. spår-id och blickvinkel). En status gäller inte automatiskt ett annat objekts tal.

Validera förslaget med:

```text
python ingest/scenbrief.py granska ingest/ut/<klipp> ingest/ut/<klipp>/brief/forslag_deklaration.json
```
"""


def bygg_paket(ingest: Path, ut: Path | None = None) -> Path:
    ingest = ingest.resolve(); brief = (ut or ingest / "brief").resolve()
    brief.mkdir(parents=True, exist_ok=True)
    data = las_json(ingest / "tagningar.json")
    if not isinstance(data, dict) or not isinstance(data.get("tagningar"), list):
        raise ValueError(f"Saknar läsbar tagningar.json i {ingest}")
    saknas = bygg_kontaktblad(ingest, brief, data["tagningar"])
    lasning = bygg_lasning(ingest, data["tagningar"])
    if saknas:
        lasning["saknade_kontaktblad"] = saknas
    skriv_json(brief / "lasning.json", lasning)
    skriv_json(brief / "deklaration.schema.json", deklarationsschema())
    (brief / "uppdrag.md").write_text(UPPDRAG, encoding="utf-8")
    return brief


def _typfel(v: Any, typ: str) -> bool:
    if typ == "object": return not isinstance(v, dict)
    if typ == "array": return not isinstance(v, list)
    if typ == "string": return not isinstance(v, str)
    if typ == "number": return isinstance(v, bool) or not isinstance(v, (int, float))
    return False


def schemafel(D: Any) -> list[str]:
    """Liten deterministisk 0.8-kontroll utan nytt paketberoende."""
    fel = []
    if not isinstance(D, dict): return ["Roten ska vara ett JSON-objekt."]
    for k in ("schema_version", "klipp", "datum", "golv", "kameror", "roller", "platser", "relevans"):
        if k not in D: fel.append(f"Saknat obligatoriskt fält: {k}")
    if D.get("schema_version") not in ("deklaration/0.8", "deklaration/0.7"): fel.append("schema_version ska vara deklaration/0.8 (0.7 godtas för befintliga filer).")
    for k in ("schema_version", "klipp", "datum"):
        if k in D and not isinstance(D[k], str): fel.append(f"{k} ska vara en sträng.")
    for k in ("golv", "kameror", "roller", "platser", "relevans"):
        if k in D and not isinstance(D[k], dict): fel.append(f"{k} ska vara ett objekt.")
    if not isinstance(D.get("platser"), dict) or not D.get("platser"): fel.append("platser ska innehålla minst en plats.")
    for pid, pl in (D.get("platser") or {}).items():
        if not isinstance(pl, dict): fel.append(f"platser.{pid} ska vara ett objekt."); continue
        if pl.get("typ") not in ("sits", "staplats", "bord"): fel.append(f"platser.{pid}.typ ska vara sits, staplats eller bord.")
        if pl.get("typ") == "bord":
            for k in ("mitt_m", "storlek_m"):
                if k not in pl and not (k == "mitt_m" and pl.get("framfor")): fel.append(f"platser.{pid} saknar {k}.")
            for k in ("langs_x", "langs_y", "hojd"):
                if not isinstance(pl.get("storlek_m"), dict) or k not in pl["storlek_m"]: fel.append(f"platser.{pid}.storlek_m saknar {k}.")
        for k in ("pos_m", "mitt_m"):
            if k in pl and pl[k] is not None and (not isinstance(pl[k], list) or len(pl[k]) != 3): fel.append(f"platser.{pid}.{k} ska ha tre komponenter.")
    for rid, roll in (D.get("roller") or {}).items():
        if not isinstance(roll, dict): continue
        if not isinstance(roll.get("tagningar"), list): fel.append(f"roller.{rid}.tagningar ska vara en lista.")
        if roll.get("lage") not in ("står", "sitter"): fel.append(f"roller.{rid}.lage ska vara står eller sitter.")
    for namn in ("bar_scenen", "satter_rummet", "stryks"):
        nivå = (D.get("relevans") or {}).get(namn)
        if not isinstance(nivå, dict) or not isinstance(nivå.get("saker"), list): fel.append(f"relevans.{namn}.saker ska vara en lista.")
    def tal(v: Any, vag: str) -> None:
        ok = isinstance(v, (int, float)) and not isinstance(v, bool)
        ok = ok or (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) and v[0] <= v[1])
        if not ok: fel.append(f"{vag} ska vara tal eller stigande [min, max].")
    if isinstance(D.get("golv"), dict) and "hojd_m" in D["golv"]: tal(D["golv"]["hojd_m"], "golv.hojd_m")
    for tid, k in (D.get("kameror") or {}).items():
        if not isinstance(k, dict): continue
        if "hojd_m" in k: tal(k["hojd_m"], f"kameror.{tid}.hojd_m")
    for pid, pl in (D.get("platser") or {}).items():
        if not isinstance(pl, dict): continue
        if "sitthojd_m" in pl: tal(pl["sitthojd_m"], f"platser.{pid}.sitthojd_m")
        if isinstance(pl.get("storlek_m"), dict):
            for k in ("langs_x", "langs_y", "hojd"):
                if k in pl["storlek_m"]: tal(pl["storlek_m"][k], f"platser.{pid}.storlek_m.{k}")
    return fel


def _tagningar(D: dict[str, Any]) -> set[str]:
    ut = set()
    for roll in (D.get("roller") or {}).values():
        if isinstance(roll, dict): ut.update(x for x in roll.get("tagningar", []) if isinstance(x, str))
    ut.update((D.get("narvaro") or {}).get("tagningar", {}).keys())
    for namn in ("berattat_rum", "avslojat_rum"):
        ut.update(x for x in (D.get(namn) or {}).get("galler_tagningar", []) if isinstance(x, str))
    return ut


def referensfel(D: dict[str, Any]) -> list[str]:
    fel, P, R = [], set((D.get("platser") or {}).keys()), {k for k, v in (D.get("roller") or {}).items() if isinstance(v, dict)}
    def plats(v: Any, vag: str) -> None:
        if isinstance(v, str) and v not in P: fel.append(f"{vag} refererar till odefinierad plats {v}.")
    def roll(v: Any, vag: str) -> None:
        if isinstance(v, str) and v not in R: fel.append(f"{vag} refererar till odefinierad roll {v}.")
    for tid, k in (D.get("kameror") or {}).items():
        if not isinstance(k, dict): continue
        plats(k.get("kamera_vid"), f"kameror.{tid}.kamera_vid"); plats(k.get("person_plats"), f"kameror.{tid}.person_plats")
        roll(k.get("huvudroll"), f"kameror.{tid}.huvudroll")
    for pid, p in (D.get("platser") or {}).items():
        if not isinstance(p, dict): continue
        roll(p.get("roll"), f"platser.{pid}.roll"); plats(p.get("framfor"), f"platser.{pid}.framfor")
        plats((p.get("las") or {}).get("kamera_vid"), f"platser.{pid}.las.kamera_vid")
        for i, r in enumerate(p.get("roller", [])): roll(r, f"platser.{pid}.roller[{i}]")
    for tid, roller in (D.get("narvaro") or {}).get("tagningar", {}).items():
        for i, r in enumerate(roller): roll(r, f"narvaro.tagningar.{tid}[{i}]")
    for tid, r in (D.get("narvaro") or {}).get("kamerabarare", {}).items(): roll(r, f"narvaro.kamerabarare.{tid}")
    # Namnkonventioner som kedjan kräver men inte själv kontrollerar (hittade på b-tilltal-ravara 12 nov):
    # plats.py döper synliga roller till A, B, C …, och rumsmall.passa matchar ankare på namnet <staplats|stol>_<roll>.
    for rid, r in (D.get("roller") or {}).items():
        if isinstance(r, dict) and r.get("tagningar") and not (len(rid) == 1 and rid.isupper()):
            fel.append(f"roller.{rid}: en roll som syns i tagningar ska heta A, B, C … (plats.py namnger rollerna så); lägg namnet i ett eget fält.")
    for pid, p in (D.get("platser") or {}).items():
        if isinstance(p, dict) and p.get("roll") and p.get("typ") in ("staplats", "sits"):
            ratt = f'{"staplats" if p["typ"] == "staplats" else "stol"}_{p["roll"]}'
            if pid != ratt: fel.append(f"platser.{pid}: hemplatsen för roll {p['roll']} ska heta {ratt}, annars matchar rumsmallens ankare inte; sätt roll till null på övriga platser.")
    return fel


def _status_for(obj: dict[str, Any], key: str, arvd: str | None) -> str | None:
    rå = obj.get(f"{key[:-2] if key.endswith('_m') else key}_status", obj.get(f"{key}_status", obj.get("status", arvd)))
    return STATUS_ALIAS.get(rå, rå)


def markeringsfel(D: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    saknar, harda, kallor = [], [], []
    # Fält där översättaren kräver skalär eller som är diskreta identifierare.
    # troskel/varde/rekommenderad är lägen på nivåreglaget 0–1 och box_2d bildlägen (rum_uppsattning.py), inga mått.
    ej_intervall = {"spar_id", "blick_grader", "rollning_grader", "hofthojd_m", "pos_m", "troskel", "varde", "rekommenderad", "box_2d"}
    ignorera = {"schema_version", "datum"}
    def ga(v: Any, vag: str, arvd: str | None = None, foralder: dict[str, Any] | None = None, nyckel: str = "") -> None:
        if isinstance(v, bool) or v is None: return
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ignorera or k.endswith("_version"): continue
                ga(x, f"{vag}.{k}" if vag else k, _status_for(v, k, arvd), v, k)
            return
        if isinstance(v, list):
            # Två tal är ett deklarationsintervall, inte två omärkta tal.
            if len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                if arvd not in STATUS: saknar.append(vag)
                if arvd == "last" and foralder is not None and not (foralder.get("kalla") or foralder.get(f"{nyckel}_kalla")): kallor.append(vag)
                return
            for i, x in enumerate(v): ga(x, f"{vag}[{i}]", arvd, foralder, nyckel)
            return
        if isinstance(v, (int, float)):
            if arvd not in STATUS: saknar.append(vag)
            if arvd == "antagen" and nyckel not in ej_intervall: harda.append(vag)
            if arvd == "last" and foralder is not None and not (foralder.get("kalla") or foralder.get(f"{nyckel}_kalla")): kallor.append(vag)
    ga(D, "")
    return sorted(set(saknar)), sorted(set(harda)), sorted(set(kallor))


def antagna_varden(D: dict[str, Any]) -> list[str]:
    """Alla numeriska antaganden, både korrekta intervall och otillåtna hårda tal."""
    ut = []
    def ga(v: Any, vag: str, status: str | None = None, nyckel: str = "") -> None:
        if isinstance(v, bool) or v is None: return
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ("schema_version", "datum") or k.endswith("_version"): continue
                ga(x, f"{vag}.{k}" if vag else k, _status_for(v, k, status), k)
        elif isinstance(v, list):
            if len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                if status == "antagen": ut.append(f"{vag} = {json.dumps(v, ensure_ascii=False)}")
            else:
                for i, x in enumerate(v): ga(x, f"{vag}[{i}]", status, nyckel)
        elif isinstance(v, (int, float)) and status == "antagen":
            ut.append(f"{vag} = {v}")
    ga(D, "")
    return sorted(set(ut))


def oversatt_i_scratch(ingest: Path, deklaration: Path) -> tuple[bool, str]:
    """Kör en orörd kopia av översättarskriptet; dess rumsmall hamnar i scratch."""
    with tempfile.TemporaryDirectory(prefix="scenbrief_") as tmpnamn:
        tmp = Path(tmpnamn); skriptmapp = tmp / "ingest"; mallar = tmp / "kontrakt" / "rumsmall"
        skriptmapp.mkdir(); mallar.mkdir(parents=True)
        skript = skriptmapp / "deklaration_till_hand.py"
        shutil.copy2(HIT / "deklaration_till_hand.py", skript)
        ut = tmp / "ut"
        r = subprocess.run([sys.executable, str(skript), str(ingest.resolve()), "--ut", str(ut), "--deklaration", str(deklaration.resolve())],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode == 0 and (ut / "hand.json").exists(), (r.stdout + r.stderr).strip()


def granska(ingest: Path, deklaration: Path, ut: Path | None = None) -> dict[str, Any]:
    rapport: dict[str, Any] = {"schemafel": [], "referensfel": [], "tagningar_utan_kamera": [], "numerik_utan_markning": [], "antagna_harda_tal": [], "lasta_utan_kalla": []}
    try: D = json.loads(deklaration.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        rapport["schemafel"] = [f"JSON kan inte läsas: {e}"]; D = {}
    if D:
        rapport["schemafel"] = schemafel(D)
        rapport["referensfel"] = referensfel(D)
        rapport["tagningar_utan_kamera"] = sorted(t for t in _tagningar(D) if not isinstance((D.get("kameror") or {}).get(t), dict))
        rapport["numerik_utan_markning"], rapport["antagna_harda_tal"], rapport["lasta_utan_kalla"] = markeringsfel(D)
        ok, logg = oversatt_i_scratch(ingest, deklaration)
        rapport["oversattning"] = {"ok": ok, "logg": logg[-2000:]}
    else:
        rapport["oversattning"] = {"ok": False, "logg": "Inte körd på oläsbar JSON."}
    rapport["godkand"] = not any(rapport[k] for k in ("schemafel", "referensfel", "tagningar_utan_kamera", "numerik_utan_markning", "antagna_harda_tal", "lasta_utan_kalla")) and rapport["oversattning"]["ok"]
    granskningsfil = (ut or deklaration.parent / "granskning.md").resolve()
    grupper = [
        ("Gissade värden att godkänna", antagna_varden(D) or ["Inga numeriska värden är markerade `antagen`."]),
        ("Rollidentiteter att godkänna", [f"{r}: {v.get('beskrivning', '')} — {', '.join(v.get('tagningar', []))}" for r, v in (D.get("roller") or {}).items() if isinstance(v, dict)]),
        ("Relevansnivåer att godkänna", [f"{n}: {', '.join((D.get('relevans') or {}).get(n, {}).get('saker', []))}" for n in ("bar_scenen", "satter_rummet", "stryks")]),
    ]
    tekniska = []
    for rubrik, nyckel in (("Schema", "schemafel"), ("Referenser", "referensfel"), ("Tagningar utan kamera", "tagningar_utan_kamera"), ("Numerik utan märkning", "numerik_utan_markning"), ("Läst utan källa", "lasta_utan_kalla")):
        if rapport[nyckel]: tekniska.append(f"- {rubrik}: " + "; ".join(rapport[nyckel]))
    text = ["# Granskning för ägaren", "", f"Översättning i scratch: {'godkänd' if rapport['oversattning']['ok'] else 'misslyckad'}.", ""]
    if tekniska: text += ["## Måste rättas före godkännande", "", *tekniska, ""]
    for rubrik, rader in grupper:
        text += [f"## {rubrik}", "", *[f"- {x}" for x in rader], ""]
    text += ["Svara med vilka antaganden/intervall, identiteter och relevansnivåer du godkänner eller rättar.", ""]
    granskningsfil.write_text("\n".join(text), encoding="utf-8")
    skriv_json(granskningsfil.with_suffix(".json"), rapport)
    return rapport


def _diagnostik(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    kvalitet = data.get("kvalitet", data) if isinstance(data, dict) else {}
    dekl = kvalitet.get("deklaration", data.get("deklaration", {})) or {}
    reg = dekl.get("registrering", kvalitet.get("registrering", data.get("registrering", {}))) or {}
    mob = kvalitet.get("mobelintervall", data.get("mobelintervall", [])) or []
    return dekl, reg, mob


def foresla_aterkoppling(D: dict[str, Any], diagnos: dict[str, Any], kalla: str) -> list[dict[str, Any]]:
    """Föreslår deklarationsändringar; muterar aldrig D."""
    _, reg, mobler = _diagnostik(diagnos)
    forslag: list[dict[str, Any]] = []
    rader = reg.get("roller", []) if isinstance(reg, dict) else []
    # Ett läst paravstånd kan inte kamera-passas bort. Behåll första platsen som
    # ramens ankare och flytta den andra längs deklarationens befintliga axel.
    per_tagning: dict[str, list[dict[str, Any]]] = {}
    for rad in rader:
        if isinstance(rad, dict): per_tagning.setdefault(str(rad.get("tagning")), []).append(rad)
    redan = set()
    for tagning, par in per_tagning.items():
        if len(par) < 2 or par[0].get("laspar_avstand_m") is None: continue
        a, b = par[0], par[1]; pa, pb = a.get("deklarerad_plats"), b.get("deklarerad_plats")
        A, B = (D.get("platser") or {}).get(pa, {}), (D.get("platser") or {}).get(pb, {})
        if not (isinstance(A.get("pos_m"), list) and isinstance(B.get("pos_m"), list)): continue
        v = np.array(B["pos_m"][:2], float) - np.array(A["pos_m"][:2], float); d = float(np.linalg.norm(v)); last = float(a["laspar_avstand_m"])
        if d < 1e-9 or abs(d - last) <= 0.01: continue
        xy = np.array(A["pos_m"][:2], float) + v / d * last
        efter = [round(float(xy[0]), 3), round(float(xy[1]), 3), float(B["pos_m"][2])]
        forslag.append({
            "sokvag": f"/platser/{pb}/pos_m", "fore": B["pos_m"], "efter": efter,
            "status": "last", "kalla": f"{kalla}: kvalitet.deklaration.registrering, {tagning}, laspar_avstand_m",
            "orsak": f"Läst rollavstånd {last:.3f} m mot deklarerat {d:.3f} m; första rollens plats behålls som ramankare.",
        }); redan.add(pb)
    # Ensam roll med stort restfel: föreslå den direkt lästa positionen.
    for rad in rader:
        pid = rad.get("deklarerad_plats") if isinstance(rad, dict) else None
        if not pid or pid in redan or rad.get("status") != "over" or not isinstance(rad.get("last_pos_m"), list): continue
        pl = (D.get("platser") or {}).get(pid, {}); fore = pl.get("pos_m")
        if not isinstance(fore, list): continue
        efter = [round(float(x), 3) for x in rad["last_pos_m"][:2]] + [float(fore[2])]
        forslag.append({"sokvag": f"/platser/{pid}/pos_m", "fore": fore, "efter": efter, "status": "last",
                         "kalla": f"{kalla}: kvalitet.deklaration.registrering, {rad.get('tagning')}/{rad.get('roll')}",
                         "orsak": f"Registreringsrest {rad.get('restfel_m')} m är över tröskeln {rad.get('troskel_m')} m."})
    # Möbelvärden som diagnostiken faktiskt justerade för hela klippet.
    karta = {"hojd_m": ("storlek_m", "hojd"), "langs_x_m": ("storlek_m", "langs_x"), "langs_y_m": ("storlek_m", "langs_y")}
    for mob in mobler:
        if not isinstance(mob, dict) or mob.get("atgard") != "justerad": continue
        pid = mob.get("del_id"); pl = (D.get("platser") or {}).get(pid, {})
        for namn, värde in (mob.get("parametrar") or {}).items():
            valt = värde.get("valt") if isinstance(värde, dict) else None
            if valt is None or namn not in karta: continue
            if värde.get("utgangsvarde") == valt: continue
            grupp, falt = karta[namn]; fore = (pl.get(grupp) or {}).get(falt)
            if fore == valt: continue
            forslag.append({
                "sokvag": f"/platser/{pid}/{grupp}/{falt}", "fore": fore, "efter": valt,
                "status_sokvag": f"/platser/{pid}/{grupp}/{falt}_status", "status": "last",
                "kalla_sokvag": f"/platser/{pid}/{grupp}/{falt}_kalla",
                "kalla": f"{kalla}: kvalitet.mobelintervall[{pid}].parametrar.{namn}.valt",
                "orsak": "Planens gemensamma möbellösare valde värdet för att minska bildskymning över tagningarna.",
            })
    return forslag


def aterkoppla(deklaration: Path, diagnosfil: Path, ut: Path | None = None) -> list[dict[str, Any]]:
    D = json.loads(deklaration.read_text(encoding="utf-8")); diagnos = json.loads(diagnosfil.read_text(encoding="utf-8"))
    forslag = foresla_aterkoppling(D, diagnos, str(diagnosfil.resolve()))
    fil = (ut or deklaration.parent / "aterkoppling.md").resolve()
    text = ["# Föreslagen återkoppling", "", f"Källdeklaration: `{deklaration.resolve()}`", f"Diagnostik: `{diagnosfil.resolve()}`", "", "Ingenting har ändrats. Ägaren kan godkänna varje post separat.", ""]
    if not forslag:
        text += ["Diagnostiken ger ingen föreslagen deklarationsändring.", ""]
    for i, f in enumerate(forslag, 1):
        text += [f"## {i}. `{f['sokvag']}`", "", "```diff", f"- {json.dumps(f['fore'], ensure_ascii=False)}", f"+ {json.dumps(f['efter'], ensure_ascii=False)}", "```",
                 "", f"Märkning: `{f['status']}`", f"Källa: {f['kalla']}", f"Skäl: {f['orsak']}", ""]
    fil.write_text("\n".join(text), encoding="utf-8")
    skriv_json(fil.with_suffix(".json"), {"deklaration": str(deklaration.resolve()), "diagnostik": str(diagnosfil.resolve()), "andringar": forslag, "tillampad": False})
    return forslag


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kommando", required=True)
    b = sub.add_parser("bygg"); b.add_argument("ingest"); b.add_argument("--ut")
    g = sub.add_parser("granska"); g.add_argument("ingest"); g.add_argument("deklaration"); g.add_argument("--ut")
    f = sub.add_parser("aterkoppla"); f.add_argument("deklaration"); f.add_argument("diagnostik"); f.add_argument("--ut")
    x = p.parse_args()
    if x.kommando == "bygg":
        print("->", bygg_paket(Path(x.ingest), Path(x.ut) if x.ut else None))
    elif x.kommando == "granska":
        r = granska(Path(x.ingest), Path(x.deklaration), Path(x.ut) if x.ut else None)
        print(json.dumps(r, ensure_ascii=False, indent=2)); raise SystemExit(0 if r["godkand"] else 1)
    else:
        r = aterkoppla(Path(x.deklaration), Path(x.diagnostik), Path(x.ut) if x.ut else None)
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
