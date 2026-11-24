import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

import scenbrief as s


class Paket(unittest.TestCase):
    def test_bygg_med_befintlig_bildcache_och_saknade_modellcache(self):
        with tempfile.TemporaryDirectory() as tmpnamn:
            rot = Path(tmpnamn); (rot / "granska").mkdir(); (rot / "S1").mkdir()
            (rot / "tagningar.json").write_text(json.dumps({"fps": 30, "tagningar": [{"id": "S1", "start": 10, "slut": 19}]}), encoding="utf-8")
            (rot / "S1/meta.json").write_text(json.dumps({"bredd": 160, "hojd": 90}), encoding="utf-8")
            (rot / "S1/personer.json").write_text("{}", encoding="utf-8")
            cv2.imwrite(str(rot / "granska/S1_a.jpg"), np.full((90, 160, 3), 100, np.uint8))
            ut = s.bygg_paket(rot)
            self.assertTrue((ut / "kontakt_S1.jpg").exists())
            self.assertTrue((ut / "kontakt_oversikt.jpg").exists())
            self.assertTrue((ut / "uppdrag.md").exists())
            self.assertEqual(json.loads((ut / "lasning.json").read_text(encoding="utf-8"))["tagningar"]["S1"]["rumsobjekt"]["status"], "saknas")
            self.assertIn("deklaration/0.8", json.loads((ut / "deklaration.schema.json").read_text(encoding="utf-8"))["properties"]["schema_version"]["enum"])


class Validator(unittest.TestCase):
    def test_fangar_referens_kamera_markning_och_hart_antagande(self):
        D = {
            "schema_version": "deklaration/0.8", "klipp": "x", "datum": "2026-11-12",
            "golv": {"hojd_m": 0, "status": "deklarerad"},
            "platser": {"a": {"typ": "staplats", "pos_m": [0, 0, 0], "roll": "B"}},
            "roller": {"A": {"tagningar": ["S1"], "lage": "står"}}, "kameror": {},
            "relevans": {x: {"saker": []} for x in ("bar_scenen", "satter_rummet", "stryks")},
        }
        self.assertTrue(s.referensfel(D)); self.assertEqual(s._tagningar(D), {"S1"})
        saknar, harda, _ = s.markeringsfel(D)
        self.assertIn("platser.a.pos_m[0]", saknar)
        D["platser"]["a"]["status"] = "antagen"
        D["prov"] = {"hojd_m": 1.4, "status": "antagen"}
        _, harda, _ = s.markeringsfel(D)
        self.assertIn("prov.hojd_m", harda)

    def test_intervall_ar_inte_hart_antaget(self):
        D = {"x": {"hojd_m": [1.2, 1.5], "status": "antagen"}}
        self.assertEqual(s.markeringsfel(D), ([], [], []))

    def test_befintliga_deklarationer_oversatts_och_har_bara_markeringsbrister(self):
        rot = Path(__file__).resolve().parent / "ut"
        for klipp in ("notan-tagningar", "e-dialog-guacamole-tagningar"):
            ingest = rot / klipp; fil = ingest / "plats/deklaration.json"
            D = json.loads(fil.read_text(encoding="utf-8"))
            self.assertEqual(s.schemafel(D), [], klipp)
            self.assertEqual(s.referensfel(D), [], klipp)
            self.assertEqual(sorted(t for t in s._tagningar(D) if not isinstance(D.get("kameror", {}).get(t), dict)), [], klipp)
            ok, logg = s.oversatt_i_scratch(ingest, fil)
            self.assertTrue(ok, logg)
            mark = s.markeringsfel(D)
            self.assertTrue(any(mark), f"{klipp} skulle lista äldre märkningar")


class Aterkoppling(unittest.TestCase):
    def test_foreslar_last_rollavstand_och_vald_mobelhojd_utan_mutation(self):
        D = {"platser": {
            "A": {"pos_m": [0, 0, 0]}, "B": {"pos_m": [0, 1.3, 0]},
            "disk": {"storlek_m": {"hojd": [0.95, 1.15]}},
        }}
        fore = json.dumps(D, sort_keys=True)
        diag = {"kvalitet": {
            "deklaration": {"registrering": {"roller": [
                {"tagning": "S4", "roll": "A", "deklarerad_plats": "A", "laspar_avstand_m": 1.73},
                {"tagning": "S4", "roll": "B", "deklarerad_plats": "B", "laspar_avstand_m": 1.73},
            ]}},
            "mobelintervall": [{"del_id": "disk", "atgard": "justerad", "parametrar": {"hojd_m": {"valt": 1.0}}}],
        }}
        f = s.foresla_aterkoppling(D, diag, "plan.json")
        self.assertEqual(f[0]["sokvag"], "/platser/B/pos_m"); self.assertEqual(f[0]["efter"], [0.0, 1.73, 0.0])
        self.assertEqual(f[1]["sokvag"], "/platser/disk/storlek_m/hojd"); self.assertEqual(f[1]["status"], "last")
        self.assertEqual(json.dumps(D, sort_keys=True), fore)


if __name__ == "__main__":
    unittest.main()
