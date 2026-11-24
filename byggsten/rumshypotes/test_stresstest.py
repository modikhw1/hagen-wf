"""Stresstestet ("Absurdist Diner") på den syntetiska dinern, med uppdragets kriterier.

    scen/.venv/Scripts/python.exe byggsten/rumshypotes/test_stresstest.py

Gränserna är uppdragets (UPPDRAG.md avsnitt 6). Där uppdraget inte anger något tal är
gränsen min egen och markerad som diagnos.
"""
from __future__ import annotations

import math
import pathlib
import sys

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))

import syntet  # noqa: E402
from hjarna import D2R, bearing, kor, logg  # noqa: E402
from jutsu_adapter import skript  # noqa: E402
from recept import bygg  # noqa: E402

_KORT = {}


def _kor():
    if not _KORT:
        f = syntet.facit(5.0)
        obs = syntet.simulera(f, 7)
        hist = kor(obs)
        rader = logg(hist, obs)
        _KORT.update(f=f, obs=obs, hist=hist, rader=rader, recept=bygg(hist, obs, rader))
    return _KORT


def test_c1_initial_tro_och_omprovning():
    r = _kor()["rader"]
    s2 = next(x for x in r if x["klipp"] == "s2")
    assert s2["tro"] == "A och B vid samma bord", s2["tro"]
    s7 = r[-1]
    assert s7["omprovning"], "ingen omprövning loggad i s7"
    assert s7["tro"] == "A vid eget bord; B vid eget bord", s7["tro"]


def test_c2_samma_rum_tva_bord():
    k = _kor()
    h = k["hist"][-1].stråle[0]
    assert len(set(h.rum_av.values())) == 1, "slutklippet lades i ett annat rum"
    assert "annat rum" in k["rader"][-1]["omprovning"], "räddningen 'annat rum' prövades inte"
    bord = [n for n in k["recept"].noder if n.klass == "bord"]
    assert len(bord) == 2


def test_c3_c_har_lagre_konfidens_och_zon():
    noder = {n.id: n for n in _kor()["recept"].noder}
    c = noder["C"]
    assert c.geometry_source == "relational_hypothesis" and c.zon is not None
    assert c.confidence_score < min(noder[i].confidence_score for i in ("A", "B", "bord_1", "bord_2"))


def test_c4_reprojektion_s7_bada_borden():
    """Bordens läge i s7:s bild, som andel av lådans bredd i bild. Uppdraget: ~15–20 %."""
    k = _kor()
    h, obs = k["hist"][-1].stråle[0], k["obs"]
    K = len(obs.klipp) - 1
    o = obs.klipp[K]
    W = o.kamera.bild_px[0]
    f_px = (W / 2) / math.tan(o.kamera.hfov_deg.v / 2 * D2R)
    andelar = []
    for d in o.detektioner:
        if d.klass != "bord":
            continue
        b, dist = bearing(h.x["cam"][K], h.x["ent"][h.assoc[(K, d.id)]])
        du = f_px * abs(math.tan(b) - math.tan(d.bearing_deg.v * D2R))
        bredd = f_px * 1.2 / dist
        andelar.append(du / bredd)
    assert len(andelar) == 2 and max(andelar) <= 0.20, andelar


def test_b1_golvet():
    for n in _kor()["recept"].noder:
        botten = n.position[2] - n.dimensions[2] / 2
        mal = 0.74 if n.klass == "foremal" else 0.0
        assert abs(botten - mal) < 0.02, (n.id, botten)


def test_b2_inga_kollisioner_mellan_bord():
    bord = [n for n in _kor()["recept"].noder if n.klass == "bord"]
    for i, a in enumerate(bord):
        for b in bord[i + 1:]:
            ax, ay = a.dimensions[0] / 2, a.dimensions[1] / 2
            bx, by = b.dimensions[0] / 2, b.dimensions[1] / 2
            ok = abs(a.position[0] - b.position[0]) >= ax + bx or abs(a.position[1] - b.position[1]) >= ay + by
            assert ok, (a.id, b.id)


def test_b3_skala_och_facit():
    k = _kor()
    for n in k["recept"].noder:
        if n.klass == "bord":
            assert 0.65 <= n.dimensions[2] <= 0.85
        if n.klass == "person" and n.pose == "staende":
            assert 1.55 <= n.dimensions[2] <= 2.0
    bord = [n for n in k["recept"].noder if n.klass == "bord"]
    d = math.dist(bord[0].position[:2], bord[1].position[:2])
    assert abs(d - 5.0) < 1.0, d                       # egen diagnosgräns
    g = k["recept"].rum.granser
    rum = sorted([g[1] - g[0], g[3] - g[2]])
    assert abs(rum[0] - 6.0) < 0.6 and abs(rum[1] - 10.0) < 1.0, rum   # egen diagnosgräns


def test_a_recept_och_skript_deterministiska():
    k = _kor()
    assert skript(k["recept"]) == skript(k["recept"])
    json_ = k["recept"].model_dump_json()
    assert '"schema_id":"rumshypotes.recept/1"' in json_


if __name__ == "__main__":
    fel = 0
    for namn, fn in sorted(globals().items()):
        if namn.startswith("test_") and callable(fn):
            try:
                fn()
                print("OK  ", namn)
            except AssertionError as e:
                fel += 1
                print("FEL ", namn, e)
    sys.exit(1 if fel else 0)
