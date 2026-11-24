"""Klippets kontext: paketet plus de semantiska källor som redan finns i repot (inga nya anrop).

Kopplingen är allmän. Den utgår från paketets ingestmapp (`paket.klipp.video`) och letar:
  relevans   scen/3d/gennedbrytning/relevans/<ingestmapp>/relevans*.json (Gemini-läsning, cachad)
  källa      scen/3d/kontrakt/{ut,exempel}/*/kalla*.json som nämner ingestmappen; den rikaste väljs
             (liggare > relevans > handling > revision > ändringstid)
  liggare    källans semantik.liggare.fil (skriven av stark modell vid ingest, 13 nov)
  ryggrad    byggsten/hand/ut/ryggrad_<källans klipp-id>.json (typ, takter, platser)
  recept     recept.json bredvid paketet (föremålens nycklar)
Det som saknas för ett klipp står i `saknas`. Ingen fil här nämner ett enskilt klipp.
"""
from __future__ import annotations

import glob
import json
import os
import pathlib

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[2]


def _json(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _valj_kalla(ingestnamn: str):
    kand = []
    for f in glob.glob(str(ROT / "scen/3d/kontrakt/ut/*/kalla*.json")) + glob.glob(str(ROT / "scen/3d/kontrakt/exempel/*/kalla*.json")):
        try:
            txt = pathlib.Path(f).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if ingestnamn not in txt:
            continue
        d = _json(f)
        if not isinstance(d, dict):
            continue
        s = d.get("semantik") or {}
        nyckel = (bool(s.get("liggare")), bool(s.get("relevans")), bool(s.get("handling")), d.get("revision") or 0, os.path.getmtime(f))
        kand.append((nyckel, f, d))
    if not kand:
        return None, None
    kand.sort(key=lambda x: x[0])
    _, f, d = kand[-1]
    return pathlib.Path(f), d


class Klipp:
    """Allt som systemet vet om ett klipp innan CM skriver något. Byggs en gång per klipp (ingestsidan)."""

    def __init__(self, paket_fil: str | pathlib.Path | None, namn: str | None = None, ingestnamn: str | None = None):
        self.paket_fil = pathlib.Path(paket_fil) if paket_fil else None
        self.paket = _json(self.paket_fil) if self.paket_fil and self.paket_fil.exists() else None
        self.namn = namn or (self.paket["klipp"]["id"] if self.paket else ingestnamn)
        if ingestnamn is None and self.paket:
            ingestnamn = pathlib.Path(self.paket["klipp"]["video"]).name
        self.ingestnamn = ingestnamn
        self.saknas: list[str] = []
        if self.paket is None:
            self.saknas.append("paket (ingen förvärld för klippet)")
        # relevans: alla körningar, den nyaste först
        rel = sorted(glob.glob(str(ROT / f"scen/3d/gennedbrytning/relevans/{ingestnamn}/relevans*.json")), key=os.path.getmtime, reverse=True)
        self.relevans_korningar = [(pathlib.Path(f), _json(f)) for f in rel]
        self.relevans_korningar = [(f, d) for f, d in self.relevans_korningar if isinstance(d, dict) and d.get("poster")]
        # källa
        self.kalla_fil, self.kalla = _valj_kalla(ingestnamn) if ingestnamn else (None, None)
        sem = (self.kalla or {}).get("semantik") or {}
        # den relevans som källan själv bär går före, annars den nyaste filen
        self.relevans = sem.get("relevans") if sem.get("relevans") else (self.relevans_korningar[0][1] if self.relevans_korningar else None)
        if not self.relevans:
            self.saknas.append("relevans (ingen läsning av vad som bär)")
        self.liggare = None
        lg = (sem.get("liggare") or {}).get("fil", {}).get("sokvag")
        if lg and self.kalla_fil:
            self.liggare = _json(self.kalla_fil.parent / lg)
        if not self.liggare:
            self.saknas.append("liggare")
        kid = ((self.kalla or {}).get("klipp") or {}).get("id")
        self.bank_id = kid
        rf = ROT / f"byggsten/hand/ut/ryggrad_{kid}.json" if kid else None
        self.ryggrad = _json(rf) if rf and rf.exists() else None
        if not self.ryggrad:
            self.saknas.append("ryggrad (klippet finns inte i banken med ryggrad)")
        self.recept = _json(self.paket_fil.with_name("recept.json")) if self.paket_fil and self.paket_fil.with_name("recept.json").exists() else None
        self.repliker = sem.get("repliker") or []
        self.skarmtext = sem.get("skarmtext") or []
        self.ljud = sem.get("ljud") or []
        self.kalla_personer = sem.get("personer") or []
        self.kalla_scener = sem.get("scener") or []
        self.handling = sem.get("handling") or []
        if not self.kalla:
            self.saknas.append("källa (repliker, skärmtext, roller)")

    # ------------------------------------------------------------------ hjälp
    @property
    def fps(self):
        if self.paket:
            return float(self.paket["tidsbas"]["fps"])
        return float(((self.kalla or {}).get("tidsbas") or {}).get("fps") or 30.0)

    def tagningar(self):
        return [t["id"] for t in self.paket["tagningar"]] if self.paket else []

    def personer(self):
        return list(self.paket["personer"].keys()) if self.paket else []

    def tagning_for_ruta(self, u):
        for t in (self.paket or {}).get("tagningar", []):
            if t["ut"][0] <= u < t["ut"][1]:
                return t["id"]
        return None

    def foremals_nycklar(self) -> dict:
        """paketets objekt-id -> nyckel ur receptet (t.ex. foremal_1 -> foremal:bonaqua_burk_gul)."""
        if not self.recept:
            return {}
        return {n["id"]: n.get("nyckel") for n in self.recept.get("noder", [])}

    def kort(self) -> dict:
        return dict(namn=self.namn, ingest=self.ingestnamn, paket=str(self.paket_fil) if self.paket_fil else None,
                    kalla=str(self.kalla_fil.relative_to(ROT)) if self.kalla_fil else None, bank_id=self.bank_id,
                    relevans_korningar=[str(f.relative_to(ROT)) for f, _ in self.relevans_korningar],
                    liggare=bool(self.liggare), ryggrad=bool(self.ryggrad), typ=(self.ryggrad or {}).get("typ"), saknas=self.saknas)
