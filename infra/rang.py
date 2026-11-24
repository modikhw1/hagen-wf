"""Gemensamma rang- och ECDF-transformer med medelrang för lika värden.

Enda källan för rang/z-transform i hagen-wf (ersätter tidigare argsort(argsort())-bugg,
se motpart/runda-4/T3-codex/robusthet.py, DOM_T1_T2.md och T4-codex/FORREGISTRERING.md A3).

Innehåller:
  - medelrang(x) / medelrang_z(A): exakt medelrang för lika värden (oviktad, som T3 robusthet.py)
  - FrystECDFTransform: kontoviktad, fryst ECDF + z-transform (som FORREGISTRERING.md A3)
    med inbyggt permutationstest (100 permutationer <= 1e-12) och kopietest (== 0.0).
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Mapping, Sequence

import numpy as np


def medelrang(x: np.ndarray) -> np.ndarray:
    """1D medelrang (0-baserad) där lika värden får exakt samma medelrang."""
    a = np.asarray(x, dtype=float)
    _, inv, count = np.unique(a, return_inverse=True, return_counts=True)
    end = np.cumsum(count)
    return (end - (count + 1) / 2.0)[inv]


def medelrang_z(A: np.ndarray, eps: float = 0.0) -> np.ndarray:
    """Kolumnvis medelrang-standardisering för 2D-matris (n, d).

    Lika värden får exakt samma rang oberoende av radordning.
    Konstanta kolumner får 0.0 (ingen division med godtyckligt tal om eps == 0.0).
    """
    arr = np.asarray(A, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"Förväntade 2D-matris, fick form {arr.shape}")
    R = np.empty_like(arr, dtype=float)
    for j in range(arr.shape[1]):
        R[:, j] = medelrang(arr[:, j])
    mu = R.mean(axis=0)
    sd = R.std(axis=0)
    if eps > 0.0:
        return (R - mu) / (sd + eps)
    out = np.zeros_like(R)
    mask = sd > 0.0
    out[:, mask] = (R[:, mask] - mu[mask]) / sd[mask]
    return out


class FrystECDFTransform:
    """Kontoviktad, fryst ECDF + z-transform enligt FORREGISTRERING.md A3.

    För varje numeriskt fält j:
      F_j(x) = sum_i w_i * [1(r_ij < x) + 0.5 * 1(r_ij == x)]
      z_j(x) = (F_j(x) - mu_j) / sigma_j

    Varje giltigt referenskonto har lika total vikt (1 / K_j), fördelad lika
    över kontots giltiga klipp. Ingen ny observation påverkar F, mu eller sigma.
    """

    def __init__(
        self,
        ref_rader: Sequence[Mapping],
        falt: Iterable[str],
        min_konton: int = 30,
    ) -> None:
        self.falt = list(falt)
        self.min_konton = int(min_konton)
        self.nk = len({r["konto"] for r in ref_rader})
        self.par: dict[str, dict] = {}

        for j in self.falt:
            val = [(r["konto"], r["v"][j]) for r in ref_rader if r["v"].get(j) is not None]
            kk = sorted({k for k, _ in val})
            if len(kk) < self.min_konton:
                self.par[j] = {"kalibrerad": False, "giltiga_konton": len(kk)}
                continue
            per: dict[str, int] = defaultdict(int)
            for k, _ in val:
                per[k] += 1
            # Sortera efter (värde, konto) så numerisk summeringsordning är helt deterministisk
            # och helt oberoende av indatas radordning (<= 1e-15).
            val_ord = sorted(val, key=lambda kv: (float(kv[1]), kv[0]))
            x = np.array([float(v) for _, v in val_ord], dtype=np.float64)
            w = np.array([1.0 / per[k] for k, _ in val_ord], dtype=np.float64)
            w = w / w.sum()
            # Gruppera unika värden för O(n log n) och exakt lika värden -> exakt lika F
            uniq_x, inv = np.unique(x, return_inverse=True)
            uniq_w = np.bincount(inv, weights=w)
            cum_before = np.concatenate(([0.0], np.cumsum(uniq_w)[:-1]))
            uniq_F = cum_before + 0.5 * uniq_w
            F = uniq_F[inv]
            mu = float((w * F).sum())
            sd = float(math.sqrt(max(0.0, float((w * (F - mu) ** 2).sum()))))
            self.par[j] = {
                "kalibrerad": sd > 0.0,
                "giltiga_konton": len(kk),
                "mu": mu,
                "sigma": sd,
                "uniq_x": uniq_x,
                "uniq_w": uniq_w,
                "cum_before": cum_before,
                "min": float(uniq_x[0]),
                "max": float(uniq_x[-1]),
                "median": float(np.median(x)),
                "konstant": sd == 0.0,
            }

    def F(self, j: str, v: float) -> float:
        p = self.par[j]
        ux = p["uniq_x"]
        idx = int(np.searchsorted(ux, v, side="left"))
        if idx < len(ux) and ux[idx] == v:
            return float(p["cum_before"][idx] + 0.5 * p["uniq_w"][idx])
        if idx == 0:
            return 0.0
        if idx >= len(ux):
            return 1.0
        return float(p["cum_before"][idx])

    def z(self, j: str, v: float | None) -> float | None:
        p = self.par[j]
        if v is None or not p.get("kalibrerad"):
            return None
        return (self.F(j, float(v)) - p["mu"]) / p["sigma"]

    def utanfor(self, j: str, v: float | None) -> bool:
        p = self.par[j]
        return v is not None and "min" in p and (v < p["min"] or v > p["max"])

    def sammanfattning(self) -> dict[str, dict]:
        hoppa = {"uniq_x", "uniq_w", "cum_before"}
        return {j: {k: v for k, v in p.items() if k not in hoppa} for j, p in self.par.items()}

    def fortest(
        self,
        ref_rader: Sequence[Mapping],
        test_rader: Sequence[Mapping],
        n_perm: int = 100,
        seed: int = 202611204,
    ) -> dict:
        """Verifierar radordningsinvarians (<= 1e-12) och att tillägg av testkopia inte ändrar z."""
        rng = np.random.default_rng(seed)
        bas = {
            (t["id"], t.get("variant", "")): {j: self.z(j, t["v"].get(j)) for j in self.falt}
            for t in test_rader
        }
        maxd = 0.0
        for _ in range(n_perm):
            pr = [ref_rader[i] for i in rng.permutation(len(ref_rader))]
            pt = [test_rader[i] for i in rng.permutation(len(test_rader))]
            T2 = FrystECDFTransform(pr, self.falt, min_konton=self.min_konton)
            for t in pt:
                key = (t["id"], t.get("variant", ""))
                for j in self.falt:
                    a, b = bas[key][j], T2.z(j, t["v"].get(j))
                    if (a is None) != (b is None):
                        maxd = max(maxd, 1e9)
                    elif a is not None:
                        maxd = max(maxd, abs(a - b))

        d2 = 0.0
        if test_rader:
            ny = list(test_rader) + [dict(test_rader[0], variant=str(test_rader[0].get("variant", "")) + "_kopia")]
            for t in ny:
                key = (t["id"], t.get("variant", ""))
                if key not in bas:
                    continue
                for j in self.falt:
                    a = bas[key][j]
                    if a is not None:
                        b = self.z(j, t["v"].get(j))
                        d2 = max(d2, abs(a - (b if b is not None else 1e9)))

        return {
            "permutation_max_avvikelse": maxd,
            "permutation_ok": maxd <= 1e-12,
            "tillagg_kopia_max_avvikelse": d2,
            "tillagg_kopia_ok": d2 == 0.0,
        }
