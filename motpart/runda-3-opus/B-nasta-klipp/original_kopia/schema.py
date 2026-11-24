"""Enhetligt Pydantic-schema för Förvärldens Kärna (forvarld_karna).

Omfattar:
- Observationer (Lager 1 ut / Lager 2 in): rumshypotes.obs/2
- Recept / SceneTelemetry (Lager 2 ut / Lager 3 in): rumshypotes.recept/2

Koordinatram (samma som Blender 5.2 och Higgsfield 3D Jutsu):
- Meter, Z uppåt, golvet z = 0, högerhänt koordinatsystem.
- Yaw: riktningen framåt i XY-planet räknad från +X moturs, i grader.
- Bearing i kamerans bild: horisontell vinkel från optiska axeln, positiv åt höger.
  Världsriktningen blir (yaw - bearing).
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class _Bas(BaseModel):
    model_config = ConfigDict(extra="forbid")


class M(_Bas):
    """Ett uppmätt eller härlett värde med osäkerhet (1 sigma)."""
    v: float
    s: float = Field(ge=0)


Klass = Literal["person", "bord", "stol", "dorr", "fonster", "foremal"]
Kalla = Literal["observed", "amodal_inferred", "relational_hypothesis"]


# ---------------------------------------------------------------- Lager 1: Observationer

class Kamera(_Bas):
    bild_px: tuple[int, int] = (576, 1024)
    hfov_deg: M
    hojd_m: M
    pitch_deg: M
    roll_deg: M = M(v=0.0, s=2.0)
    statisk: bool = True


class Detektion(_Bas):
    id: str
    klass: Klass
    nyckel: Optional[str] = None          # identitet eller utseende, t.ex. "person:B", "foremal:bonaqua_burk_gul"
    unik: bool = False                    # nyckeln pekar ut en enda unik entitet i världen (t.ex. en identifierad person)
    bearing_deg: M
    djup_m: M                             # vågrätt avstånd i XY-planet till sakens mitt (amodalt)
    vridning_deg: Optional[M] = None      # personens vändning i kameraram (180° = tittar in i kameran)
    pose: Optional[Literal["sittande", "staende"]] = None
    blick_mot: Optional[str] = None       # nyckel för den roll personen tittar mot
    vid: Optional[str] = None             # id för bordet/disken personen sitter/står vid (i samma tagning)
    pa: Optional[str] = None              # id för bordet/disken föremålet står på (i samma tagning)
    pa_vagg: bool = False                 # dörr eller fönster i en vägg
    amodal: bool = False                  # bara en del syns; lådan kompletteras ned till golvet
    farg_signatur: Optional[list[float]] = None  # normaliserad visuell RGB/lab-signatur ur bilden för Cross-Shot Re-ID


class Vagg(_Bas):
    bearing_deg: M
    avstand_m: M
    nyckel: Optional[str] = None


class Stralar(_Bas):
    """Fri yta: vågrätt avstånd till första höga hinder (person, vägg) längs strålar i bilden."""
    bearing_deg: list[float]
    fri_m: list[float]


class Djupgrid(_Bas):
    """Grovt kalibrerat djup (z längs optiska axeln, meter) över bilden; -1 = okänt."""
    rader: int
    kolumner: int
    varden: list[float]


class KlippObs(_Bas):
    klipp: str
    rutor: tuple[int, int]                # halvöppet intervall [a, b)
    kamera: Kamera
    detektioner: list[Detektion] = []
    vaggar: list[Vagg] = []
    manhattan_deg: Optional[M] = None     # kamerans yaw modulo 90° mot rummets vertikala väggplan
    ljus_bearing_deg: Optional[M] = None
    takhojd_m: Optional[M] = None
    rumsnycklar: dict[str, str] = {}
    stralar: Optional[Stralar] = None
    djupgrid: Optional[Djupgrid] = None
    skala: Optional[float] = None         # MoGe-djupets kalibreringsskala mot kroppen (R19)
    delar_kamera_med: Optional[str] = None  # R23: tidigare klipp-id med SIFT-verifierad delad kameraplats/bakgrund


class Observationer(_Bas):
    schema_id: Literal["rumshypotes.obs/1", "rumshypotes.obs/2"] = "rumshypotes.obs/2"
    klipp_id: str
    fps: float
    klipp: list[KlippObs]


# ---------------------------------------------------------------- Lager 2: Recept (SceneTelemetry)

class Zon(_Bas):
    centrum: tuple[float, float, float]
    matt: tuple[float, float, float]


class Nod(_Bas):
    id: str
    klass: Klass
    nyckel: Optional[str] = None
    position: tuple[float, float, float]          # boxens mitt i meter
    rotation: tuple[float, float, float]          # euler XYZ i grader
    dimensions: tuple[float, float, float]        # w, d, h (lokala x, y, z)
    position_variance: tuple[float, float, float]
    confidence_score: float = Field(ge=0, le=1)
    evidence_shots: list[str]
    geometry_source: Kalla
    pose: Optional[str] = None
    giltig_i: Optional[list[str]] = None
    zon: Optional[Zon] = None


class Vaggnod(_Bas):
    sida: Literal["E", "N", "W", "S"]
    lage_m: float
    sigma_m: float
    geometry_source: Kalla
    evidence_shots: list[str]


class Rum(_Bas):
    granser: tuple[float, float, float, float]    # xmin, xmax, ymin, ymax
    takhojd_m: float
    takhojd_sigma_m: float
    vaggar: list[Vaggnod]
    rumsnycklar: dict[str, str] = {}


class KameraNod(_Bas):
    id: str
    klipp: str
    rutor: tuple[int, int]
    position: tuple[float, float, float]
    rotation: tuple[float, float, float]          # euler XYZ i grader (Blender-kamera)
    hfov_deg: float
    bild_px: tuple[int, int]
    position_variance: tuple[float, float, float]
    yaw_sigma_deg: float
    confidence_score: float = Field(ge=0, le=1)


class Ljus(_Bas):
    azimut_deg: float
    sigma_deg: float
    hojd_deg: float = 35.0


class HypotesRad(_Bas):
    id: str
    beskrivning: str
    poang: float
    sannolikhet: float
    termer: dict[str, float]


class LoggSteg(_Bas):
    klipp: str
    tro: str
    sannolikhet: float
    hypoteser: list[HypotesRad]
    omprovning: Optional[str] = None
    osakerhet_m: dict[str, float]
    bidrag: Optional[str] = None


class Recept(_Bas):
    """SceneTelemetry: komplett rumsrecept med osäkerhet och beslutslogg."""
    schema_id: Literal["rumshypotes.recept/1", "rumshypotes.recept/2"] = "rumshypotes.recept/2"
    klipp_id: str
    ram: str = "blender: meter, z upp, golv z=0, euler XYZ i grader"
    fps: float
    rutor: int
    tro: str
    sannolikhet: float
    rum: Rum
    noder: list[Nod]
    kameror: list[KameraNod]
    ljus: Optional[Ljus] = None
    logg: list[LoggSteg]
    regler: dict[str, float]


SceneTelemetry = Recept
