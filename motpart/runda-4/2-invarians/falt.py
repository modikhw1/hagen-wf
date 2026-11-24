"""Fältregister enligt FORREGISTRERING.md A3 (klass, tolerans ε, förväntad faktor) och uttag ur extraktorernas rader."""
import math
import numpy as np

# namn: (klass, eps, faktor, händelsefält som ska vara stabilt för storleksjämförelsen eller None)
# klass: Ttid, Ttat, Tq (T?), Gr (räkning), Ga (andelar/form), Gf (fast fönster), L, Gp (personer)
FALT = {
  "e28.langd": ("Ttid", 0.10, 0.8, None), "e28.skott_median": ("Ttid", 0.10, 0.8, "e28.byten"), "e28.skott_max": ("Ttid", 0.10, 0.8, "e28.byten"),
  "e28.forsta_byte": ("Ttid", 0.10, 0.8, "e28.byten"), "e28.forsta_ljud": ("Ttid", 0.10, 0.8, "e28.pauser"),
  "e30.langd": ("Ttid", 0.10, 0.8, None), "e30.forsta_tal": ("Ttid", 0.10, 0.8, "e30.tal_segment"),
  "e28.takt": ("Ttat", 0.02, 1.25, "e28.byten"), "e30.tal_per_s": ("Ttat", 0.005, 1.25, "e30.tal_segment"),
  "e28.rorelse": ("Tq", 0.20, None, None), "e28.rorelse_2s": ("Tq", 0.20, None, None), "e28.rorelse_kvot": ("Tq", 0.10, None, None),
  "e28.byten": ("Gr", 0.0, None, None), "e28.pauser": ("Gr", 0.0, None, None), "e30.tal_segment": ("Gr", 0.0, None, None),
  "e28.skott_max_andel": ("Ga", 0.02, None, None), "e28.skott_cv": ("Ga", 0.05, None, None), "e28.ljud_andel": ("Ga", 0.02, None, None), "e30.tal_andel": ("Ga", 0.02, None, None),
  "e28.byten_3s": ("Gf", 0.0, None, None),
  "e28.lufs": ("L", 0.5, None, None), "e28.lra": ("L", 0.5, None, None),
  **{f"e37.antal{k}": ("Gp", 0.0, None, None) for k in range(6)},
  "e37.personer_medel": ("Gp", 0.0, None, None), "e37.andel_minst_en": ("Gp", 0.0, None, None), "e37.andel_minst_tva": ("Gp", 0.0, None, None), "e37.personer_max": ("Gp", 0.0, None, None),
}
# T2:s fasta 19 fält (diagnos_modellfri.py TEK+TAL+tre personaggregat), för grann-diagnosen
T2_19 = ["e28.langd", "e28.takt", "e28.skott_median", "e28.skott_max_andel", "e28.skott_cv", "e28.forsta_byte", "e28.rorelse", "e28.rorelse_kvot", "e28.ljud_andel", "e28.pauser", "e28.lufs", "e28.lra",
         "e30.tal_andel", "e30.tal_segment", "e30.tal_per_s", "e30.forsta_tal", "e37.personer_medel", "e37.andel_minst_en", "e37.andel_minst_tva"]

def _num(x):
    if x is None: return None
    try: x = float(x)
    except (TypeError, ValueError): return None
    return None if math.isnan(x) or math.isinf(x) else x

def uttag(row):
    """row: {'e28':..,'e30':..,'e37':..} -> {fältnamn: float|None}, plus tillstånd {'e37_rutor': n, 'ljud': bool}."""
    v = {k: None for k in FALT}
    e28, e30, e37 = row.get("e28"), row.get("e30"), row.get("e37")
    if e28:
        for k in ("langd", "byten", "takt", "skott_median", "skott_max", "skott_max_andel", "skott_cv", "forsta_byte", "byten_3s", "rorelse", "rorelse_2s", "rorelse_kvot", "ljud_andel", "pauser", "forsta_ljud", "lufs", "lra"):
            v[f"e28.{k}"] = _num(e28.get(k))
    if e30:
        for k in ("langd", "tal_andel", "tal_segment", "tal_per_s", "forsta_tal"):
            v[f"e30.{k}"] = _num(e30.get(k))
    n = 0
    if e37 and e37.get("antal") is not None:
        a = e37["antal"]; n = len(a)
        for k in range(6): v[f"e37.antal{k}"] = float(a[k]) if k < n else None
        if n:
            v["e37.personer_medel"] = float(np.mean(a)); v["e37.andel_minst_en"] = float(np.mean([x >= 1 for x in a]))
            v["e37.andel_minst_tva"] = float(np.mean([x >= 2 for x in a])); v["e37.personer_max"] = float(max(a))
    return v, {"e37_rutor": n}
