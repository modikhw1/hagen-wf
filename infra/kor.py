"""Jobbkörare med provlopp, ETA-grind, tak, hjärtslag och återupptagbarhet (INFRA.md §3, M4).

Användning som bibliotek:
    from infra.kor import JobbKorare, JobbSpec, maskin_granser
    korare = JobbKorare(spec)
    res = korare.kor(enheter, kor_enhet_fn, ...)

Användning som CLI:
    python infra/kor.py --info                        # skriv ut maskinens kända gränser
    python infra/kor.py <uppdrag.json> [--torr] [--kraft-lokal] [--plats auto|lokal|modal|varm_maskin]

Garantier (INFRA.md §3 & DIAGNOS_VANTETID.md §4):
  1. Provlopp: kör 1-2 enheter och mäter verklig tid/enhet, diskdelta och RAM-topp.
     Inget uppdrag över 5 min (300 s) får starta utan uppmätt provlopps-ETA (M4).
  2. Platsval: <= 300 s och tillräcklig lokal disk/RAM -> lokal; över det -> modal/varm_maskin.
  3. Tak: stannar och rapporterar vid 1.5 x ETA (eller explicit tak_sek), låg disk eller kostnadstak.
  4. Hjärtslag: skriver atomärt till <mapp>/FRAMSTEG.json efter provlopp och varje enhet.
  5. Mänskliga grindar först: deklarerad human-gate-hook körs FÖRE tung automatik.
  6. Återupptagbarhet: varje klar enhet loggas i <mapp>/klara.jsonl; omstart hoppar över klara.
"""
from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

ROT = Path(__file__).resolve().parents[1]
GRANS_SEK_LOKAL = 300.0  # 5 min (M4 / INFRA §3.2)


def _iso_nu() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _atomisk_json(fil: Path, data: Any) -> None:
    fil.parent.mkdir(parents=True, exist_ok=True)
    tmp = fil.with_suffix(fil.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, fil)


def _ram_gb() -> tuple[float | None, float | None]:
    """Returnerar (ledigt_gb, totalt_gb) utan externa beroenden."""
    try:
        if os.name == "nt":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return round(st.ullAvailPhys / (1024**3), 2), round(st.ullTotalPhys / (1024**3), 2)
        else:
            info = {}
            for rad in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if ":" in rad:
                    k, v = rad.split(":", 1)
                    info[k.strip()] = int(v.strip().split()[0]) * 1024
            if "MemTotal" in info:
                avail = info.get("MemAvailable", info.get("MemFree", 0))
                return round(avail / (1024**3), 2), round(info["MemTotal"] / (1024**3), 2)
    except Exception:
        pass
    return None, None


def maskin_granser(disk_sokvag: Path | None = None) -> dict[str, Any]:
    """Läser maskinens kända gränser automatiskt före start (DIAGNOS §4.7)."""
    p = disk_sokvag or ROT
    if not p.exists():
        p = ROT
    du = shutil.disk_usage(str(p))
    ram_fri, ram_tot = _ram_gb()
    modal_konfig = (Path.home() / ".modal.toml").exists() or bool(os.environ.get("MODAL_TOKEN_ID"))
    varm_url = os.environ.get("HAGEN_VARM_URL")
    return {
        "tid": _iso_nu(),
        "os": platform.system(),
        "cpu_logiska": os.cpu_count() or 1,
        "disk_sokvag": str(p),
        "ledig_disk_gb": round(du.free / (1024**3), 2),
        "total_disk_gb": round(du.total / (1024**3), 2),
        "ledigt_ram_gb": ram_fri,
        "totalt_ram_gb": ram_tot,
        "ffmpeg": shutil.which("ffmpeg"),
        "modal_redo": modal_konfig,
        "varm_maskin_url": varm_url,
    }


@dataclass
class JobbSpec:
    jobb_id: str
    mapp: Path
    beskrivning: str = ""
    provlopp_antal: int = 2
    min_ledigt_disk_gb: float = 5.5
    max_kostnad_usd: float = 2.0
    tak_faktor: float = 1.5
    tak_sek_explicit: float | None = None
    plats_preferens: str = "auto"  # auto | lokal | modal | varm_maskin
    kostnad_per_enhet_usd: float = 0.0
    krav_godkannande_over_5min: bool = False
    torr: bool = False
    mansklig_grind_beskrivning: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class GrindStopp(RuntimeError):
    """Kastas när ett jobb stoppas av grind eller tak."""

    def __init__(self, kod: str, meddelande: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(meddelande)
        self.kod = kod
        self.data = data or {}


class JobbKorare:
    """Kör godtyckligt enhetsbaserat uppdrag med provlopp, ETA-grind, tak och FRAMSTEG.json."""

    def __init__(self, spec: JobbSpec) -> None:
        self.spec = spec
        self.mapp = Path(spec.mapp)
        self.mapp.mkdir(parents=True, exist_ok=True)
        self.framsteg_fil = self.mapp / "FRAMSTEG.json"
        self.grind_fil = self.mapp / "GRIND.json"
        self.klara_fil = self.mapp / "klara.jsonl"
        self.logg_fil = self.mapp / "kor.logg.jsonl"
        self._start_mono = time.monotonic()

    def _las_klara(self) -> dict[str, dict]:
        klara: dict[str, dict] = {}
        if not self.klara_fil.exists():
            return klara
        for rad in self.klara_fil.read_text(encoding="utf-8").splitlines():
            if not rad.strip():
                continue
            try:
                post = json.loads(rad)
                if post.get("status") == "ok" and "enhet" in post:
                    klara[str(post["enhet"])] = post
            except json.JSONDecodeError:
                continue
        return klara

    def _logga_enhet(self, post: dict[str, Any]) -> None:
        rad = json.dumps(post, ensure_ascii=False) + "\n"
        with self.logg_fil.open("a", encoding="utf-8") as f:
            f.write(rad)
        if post.get("status") == "ok":
            with self.klara_fil.open("a", encoding="utf-8") as f:
                f.write(rad)

    def _skriv_framsteg(
        self,
        *,
        status: str,
        steg: str,
        n: int,
        N: int,
        eta_kvar_sek: float | None,
        eta_total_sek: float | None,
        tak_sek: float | None,
        plats: str,
        kostnad_usd: float,
        senaste_fel: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        gr = maskin_granser(self.mapp)
        forflutet = round(time.monotonic() - self._start_mono, 2)
        post = {
            "jobb_id": self.spec.jobb_id,
            "beskrivning": self.spec.beskrivning,
            "status": status,
            "steg": steg,
            "n": n,
            "N": N,
            "procent": round(100.0 * n / max(N, 1), 1),
            "forflutet_sek": forflutet,
            "eta_kvar_sek": round(eta_kvar_sek, 1) if eta_kvar_sek is not None else None,
            "eta_total_sek": round(eta_total_sek, 1) if eta_total_sek is not None else None,
            "tak_sek": round(tak_sek, 1) if tak_sek is not None else None,
            "plats": plats,
            "ledig_disk_gb": gr["ledig_disk_gb"],
            "ledigt_ram_gb": gr["ledigt_ram_gb"],
            "kostnad_usd": round(kostnad_usd, 4),
            "senaste_fel": senaste_fel,
            "uppdaterad": _iso_nu(),
        }
        if extra:
            post["extra"] = extra
        _atomisk_json(self.framsteg_fil, post)
        return post

    def _kontrollera_disk(self) -> float:
        fri_gb = shutil.disk_usage(str(self.mapp)).free / (1024**3)
        if fri_gb < self.spec.min_ledigt_disk_gb:
            raise GrindStopp(
                "stoppad_tak_disk",
                f"Ledig disk {fri_gb:.2f} GB < gräns {self.spec.min_ledigt_disk_gb:.2f} GB",
                {"ledig_disk_gb": round(fri_gb, 2), "grans_gb": self.spec.min_ledigt_disk_gb},
            )
        return fri_gb

    def _valj_plats(
        self,
        eta_lokal_sek: float,
        disk_behov_gb: float,
        granser: dict[str, Any],
        har_fjarr: bool,
    ) -> tuple[str, str]:
        pref = self.spec.plats_preferens
        if pref != "auto":
            return pref, f"explicit val ({pref})"
        disk_marginal = granser["ledig_disk_gb"] - self.spec.min_ledigt_disk_gb
        if disk_behov_gb > max(0.0, disk_marginal):
            if granser["varm_maskin_url"] and har_fjarr:
                return "varm_maskin", f"diskbehov {disk_behov_gb:.2f} GB överstiger lokal marginal {disk_marginal:.2f} GB"
            if granser["modal_redo"] and har_fjarr:
                return "modal", f"diskbehov {disk_behov_gb:.2f} GB överstiger lokal marginal {disk_marginal:.2f} GB"
        if eta_lokal_sek <= GRANS_SEK_LOKAL:
            return "lokal", f"ETA {eta_lokal_sek:.1f} s <= {GRANS_SEK_LOKAL:.0f} s"
        if granser["varm_maskin_url"] and har_fjarr:
            return "varm_maskin", f"ETA {eta_lokal_sek:.1f} s > 300 s -> varm maskin"
        if granser["modal_redo"] and har_fjarr:
            return "modal", f"ETA {eta_lokal_sek:.1f} s > 300 s -> Modal-pool"
        return "lokal", f"ETA {eta_lokal_sek:.1f} s > 300 s men ingen fjärrkörare konfigurerad; lokal med tak"

    def kor(
        self,
        enheter: Sequence[str],
        kor_enhet: Callable[[str], dict[str, Any]],
        *,
        kor_batch_fjarr: Callable[[list[str], str], list[dict[str, Any]]] | None = None,
        mansklig_grind_fn: Callable[[], dict[str, Any]] | None = None,
        fjarr_speedup_faktor: float = 12.0,
    ) -> dict[str, Any]:
        """Kör hela cykeln: mänsklig grind -> provlopp -> ETA/platsgrind -> körning med tak."""
        enheter = [str(e) for e in enheter]
        N = len(enheter)
        granser_start = maskin_granser(self.mapp)
        klara = self._las_klara()
        aterstaende = [e for e in enheter if e not in klara]
        kostnad = sum(float(v.get("kostnad_usd", 0.0)) for v in klara.values())

        # 1. Mänsklig grind först (INFRA §3.5)
        mansklig_utfall = None
        if mansklig_grind_fn is not None:
            self._skriv_framsteg(
                status="pagar",
                steg="mansklig_grind",
                n=len(klara),
                N=N,
                eta_kvar_sek=None,
                eta_total_sek=None,
                tak_sek=None,
                plats="lokal",
                kostnad_usd=kostnad,
                extra={"mansklig_grind": self.spec.mansklig_grind_beskrivning},
            )
            mansklig_utfall = mansklig_grind_fn()
            _atomisk_json(self.mapp / "MANSKLIG_GRIND.json", {"tid": _iso_nu(), "utfall": mansklig_utfall})

        if not aterstaende:
            sl = self._skriv_framsteg(
                status="klar",
                steg="klar_redan_utford",
                n=N,
                N=N,
                eta_kvar_sek=0.0,
                eta_total_sek=0.0,
                tak_sek=None,
                plats="lokal",
                kostnad_usd=kostnad,
            )
            return {"status": "klar", "n": N, "N": N, "framsteg": sl, "mansklig_grind": mansklig_utfall}

        # 2. Provlopp: 1-2 enheter för mätt tid/disk/RAM (M4 / INFRA §3.1)
        self._kontrollera_disk()
        n_prov = max(1, min(self.spec.provlopp_antal, len(aterstaende)))
        prov_enheter = aterstaende[:n_prov]
        prov_tider: list[float] = []
        prov_disk_mb: list[float] = []
        senaste_fel: str | None = None

        self._skriv_framsteg(
            status="provlopp",
            steg=f"provlopp (0/{n_prov})",
            n=len(klara),
            N=N,
            eta_kvar_sek=None,
            eta_total_sek=None,
            tak_sek=None,
            plats="lokal",
            kostnad_usd=kostnad,
        )

        for idx, enh in enumerate(prov_enheter, 1):
            self._kontrollera_disk()
            disk_fore = shutil.disk_usage(str(self.mapp)).free
            t0 = time.monotonic()
            try:
                res = kor_enhet(enh) or {}
                dt = time.monotonic() - t0
                disk_efter = shutil.disk_usage(str(self.mapp)).free
                delta_mb = max(0.0, (disk_fore - disk_efter) / (1024**2))
                c_usd = float(res.get("kostnad_usd", self.spec.kostnad_per_enhet_usd))
                kostnad += c_usd
                post = {
                    "enhet": enh,
                    "status": "ok",
                    "sek": round(dt, 3),
                    "disk_delta_mb": round(delta_mb, 3),
                    "kostnad_usd": round(c_usd, 6),
                    "tid": _iso_nu(),
                    "resultat": res,
                }
                self._logga_enhet(post)
                klara[enh] = post
                prov_tider.append(dt)
                prov_disk_mb.append(delta_mb)
            except Exception as exc:
                senaste_fel = f"{enh}: {exc!r}"
                self._logga_enhet({"enhet": enh, "status": "fel", "fel": repr(exc), "tid": _iso_nu()})
                raise GrindStopp("fel_provlopp", f"Provlopp misslyckades på {enh}: {exc}", {"enhet": enh}) from exc

            self._skriv_framsteg(
                status="provlopp",
                steg=f"provlopp ({idx}/{n_prov})",
                n=len(klara),
                N=N,
                eta_kvar_sek=None,
                eta_total_sek=None,
                tak_sek=None,
                plats="lokal",
                kostnad_usd=kostnad,
            )

        # 3. ETA, platsval och grindlogg (M4 / INFRA §3.2)
        kvar_enheter = [e for e in enheter if e not in klara]
        sek_per_enhet = sum(prov_tider) / len(prov_tider)
        sek_min = min(prov_tider)
        sek_max = max(prov_tider)
        mb_per_enhet = max(prov_disk_mb) if prov_disk_mb else 0.0
        eta_lokal_kvar = sek_per_enhet * len(kvar_enheter)
        eta_intervall_lokal = [round(sek_min * len(kvar_enheter), 1), round(sek_max * len(kvar_enheter) * 1.25, 1)]
        disk_behov_gb = (mb_per_enhet * len(kvar_enheter)) / 1024.0
        est_kostnad_tot = kostnad + self.spec.kostnad_per_enhet_usd * len(kvar_enheter)

        granser_nu = maskin_granser(self.mapp)
        plats, plats_skal = self._valj_plats(eta_lokal_kvar, disk_behov_gb, granser_nu, kor_batch_fjarr is not None)
        eta_vald_kvar = eta_lokal_kvar if plats == "lokal" else eta_lokal_kvar / max(1.0, fjarr_speedup_faktor)
        forflutet_prov = time.monotonic() - self._start_mono
        eta_total = forflutet_prov + eta_vald_kvar
        tak_sek = self.spec.tak_sek_explicit or max(30.0, eta_total * self.spec.tak_faktor)

        grind = {
            "jobb_id": self.spec.jobb_id,
            "tid": _iso_nu(),
            "maskin_granser": granser_nu,
            "provlopp_utfort": True,
            "provlopp_enheter": prov_enheter,
            "provlopp_tider_sek": [round(x, 3) for x in prov_tider],
            "sek_per_enhet": round(sek_per_enhet, 3),
            "disk_mb_per_enhet": round(mb_per_enhet, 3),
            "kvar_enheter": len(kvar_enheter),
            "eta_lokal_kvar_sek": round(eta_lokal_kvar, 1),
            "eta_intervall_lokal_sek": eta_intervall_lokal,
            "eta_vald_kvar_sek": round(eta_vald_kvar, 1),
            "eta_total_sek": round(eta_total, 1),
            "tak_sek": round(tak_sek, 1),
            "est_disk_behov_gb": round(disk_behov_gb, 3),
            "est_kostnad_usd": round(est_kostnad_tot, 4),
            "max_kostnad_usd": self.spec.max_kostnad_usd,
            "plats": plats,
            "plats_skal": plats_skal,
            "over_5min": eta_lokal_kvar > GRANS_SEK_LOKAL,
            "mansklig_grind_utford": mansklig_utfall is not None,
        }
        _atomisk_json(self.grind_fil, grind)

        if est_kostnad_tot > self.spec.max_kostnad_usd:
            self._skriv_framsteg(
                status="stoppad_tak_kostnad",
                steg="grind_kostnad",
                n=len(klara),
                N=N,
                eta_kvar_sek=eta_vald_kvar,
                eta_total_sek=eta_total,
                tak_sek=tak_sek,
                plats=plats,
                kostnad_usd=kostnad,
                senaste_fel=f"Estimerad kostnad ${est_kostnad_tot:.3f} > tak ${self.spec.max_kostnad_usd:.2f}",
            )
            raise GrindStopp("stoppad_tak_kostnad", f"Kostnadstak överskridet: ${est_kostnad_tot:.3f}", grind)

        if self.spec.torr or (self.spec.krav_godkannande_over_5min and eta_vald_kvar > GRANS_SEK_LOKAL):
            status_kod = "torr_provlopp_klar" if self.spec.torr else "vantar_godkannande"
            sl = self._skriv_framsteg(
                status=status_kod,
                steg="grind_paus",
                n=len(klara),
                N=N,
                eta_kvar_sek=eta_vald_kvar,
                eta_total_sek=eta_total,
                tak_sek=tak_sek,
                plats=plats,
                kostnad_usd=kostnad,
            )
            return {"status": status_kod, "grind": grind, "framsteg": sl, "mansklig_grind": mansklig_utfall}

        if not kvar_enheter:
            sl = self._skriv_framsteg(
                status="klar",
                steg="klar",
                n=len(klara),
                N=N,
                eta_kvar_sek=0.0,
                eta_total_sek=round(time.monotonic() - self._start_mono, 2),
                tak_sek=tak_sek,
                plats=plats,
                kostnad_usd=kostnad,
            )
            return {"status": "klar", "n": len(klara), "N": N, "grind": grind, "framsteg": sl, "mansklig_grind": mansklig_utfall}

        # 4. Exekvering med tak och hjärtslag
        if plats in ("modal", "varm_maskin") and kor_batch_fjarr is not None:
            self._skriv_framsteg(
                status="pagar",
                steg=f"fjarr_{plats} ({len(kvar_enheter)} enheter)",
                n=len(klara),
                N=N,
                eta_kvar_sek=eta_vald_kvar,
                eta_total_sek=eta_total,
                tak_sek=tak_sek,
                plats=plats,
                kostnad_usd=kostnad,
            )
            fjarr_res = kor_batch_fjarr(kvar_enheter, plats)
            for post in fjarr_res:
                enh = str(post["enhet"])
                kostnad += float(post.get("kostnad_usd", 0.0))
                self._logga_enhet(post)
                if post.get("status") == "ok":
                    klara[enh] = post
                else:
                    senaste_fel = f"{enh}: {post.get('fel')}"
                self._skriv_framsteg(
                    status="pagar",
                    steg=f"fjarr_{plats}",
                    n=len(klara),
                    N=N,
                    eta_kvar_sek=max(0.0, eta_total - (time.monotonic() - self._start_mono)),
                    eta_total_sek=eta_total,
                    tak_sek=tak_sek,
                    plats=plats,
                    kostnad_usd=kostnad,
                    senaste_fel=senaste_fel,
                )
        else:
            tider_lopande = list(prov_tider)
            for idx, enh in enumerate(kvar_enheter, 1):
                forflutet = time.monotonic() - self._start_mono
                if forflutet > tak_sek:
                    sl = self._skriv_framsteg(
                        status="stoppad_tak_tid",
                        steg=f"tak_natt vid {enh}",
                        n=len(klara),
                        N=N,
                        eta_kvar_sek=(sum(tider_lopande) / len(tider_lopande)) * (len(kvar_enheter) - idx + 1),
                        eta_total_sek=eta_total,
                        tak_sek=tak_sek,
                        plats=plats,
                        kostnad_usd=kostnad,
                        senaste_fel=f"Väggtid {forflutet:.1f} s > tak {tak_sek:.1f} s (1.5x ETA)",
                    )
                    raise GrindStopp("stoppad_tak_tid", f"Väggtidstak nått: {forflutet:.1f} s > {tak_sek:.1f} s", sl)

                self._kontrollera_disk()
                if kostnad > self.spec.max_kostnad_usd:
                    raise GrindStopp("stoppad_tak_kostnad", f"Kostnadstak nått: ${kostnad:.3f}")

                t0 = time.monotonic()
                try:
                    res = kor_enhet(enh) or {}
                    dt = time.monotonic() - t0
                    c_usd = float(res.get("kostnad_usd", self.spec.kostnad_per_enhet_usd))
                    kostnad += c_usd
                    post = {
                        "enhet": enh,
                        "status": "ok",
                        "sek": round(dt, 3),
                        "kostnad_usd": round(c_usd, 6),
                        "tid": _iso_nu(),
                        "resultat": res,
                    }
                    self._logga_enhet(post)
                    klara[enh] = post
                    tider_lopande.append(dt)
                except Exception as exc:
                    senaste_fel = f"{enh}: {exc!r}"
                    self._logga_enhet({"enhet": enh, "status": "fel", "fel": repr(exc), "tid": _iso_nu()})

                snitt = sum(tider_lopande) / len(tider_lopande)
                kvar = len(kvar_enheter) - idx
                self._skriv_framsteg(
                    status="pagar",
                    steg=f"lokal ({len(klara)}/{N})",
                    n=len(klara),
                    N=N,
                    eta_kvar_sek=snitt * kvar,
                    eta_total_sek=(time.monotonic() - self._start_mono) + snitt * kvar,
                    tak_sek=tak_sek,
                    plats=plats,
                    kostnad_usd=kostnad,
                    senaste_fel=senaste_fel,
                )

        sl = self._skriv_framsteg(
            status="klar" if len(klara) == N else "delvis_klar",
            steg="klar",
            n=len(klara),
            N=N,
            eta_kvar_sek=0.0,
            eta_total_sek=round(time.monotonic() - self._start_mono, 2),
            tak_sek=tak_sek,
            plats=plats,
            kostnad_usd=kostnad,
            senaste_fel=senaste_fel,
        )
        return {
            "status": sl["status"],
            "n": len(klara),
            "N": N,
            "grind": grind,
            "framsteg": sl,
            "mansklig_grind": mansklig_utfall,
        }


def _ladda_callable(ref: str) -> Callable:
    mod_namn, fn_namn = ref.split(":", 1)
    if str(ROT) not in sys.path:
        sys.path.insert(0, str(ROT))
    mod = importlib.import_module(mod_namn)
    return getattr(mod, fn_namn)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Jobbkörare med provlopp, ETA-grind, tak och FRAMSTEG.json")
    ap.add_argument("uppdrag", nargs="?", help="JSON-fil med uppdragsspecifikation")
    ap.add_argument("--info", action="store_true", help="Visa maskinens kända gränser och avsluta")
    ap.add_argument("--torr", action="store_true", help="Kör bara provlopp + ETA-grind utan full körning")
    ap.add_argument("--plats", choices=["auto", "lokal", "modal", "varm_maskin"], default=None)
    ap.add_argument("--tak-sek", type=float, default=None, help="Explicit väggtidstak i sekunder")
    ap.add_argument("--krav-godkannande", action="store_true", help="Stanna om ETA > 5 min efter provlopp")
    args = ap.parse_args(argv)

    if args.info or not args.uppdrag:
        print(json.dumps(maskin_granser(), ensure_ascii=False, indent=2))
        return 0

    spec_data = json.loads(Path(args.uppdrag).read_text(encoding="utf-8"))
    spec = JobbSpec(
        jobb_id=spec_data["jobb_id"],
        mapp=Path(spec_data["mapp"]),
        beskrivning=spec_data.get("beskrivning", ""),
        provlopp_antal=int(spec_data.get("provlopp_antal", 2)),
        min_ledigt_disk_gb=float(spec_data.get("min_ledigt_disk_gb", 5.5)),
        max_kostnad_usd=float(spec_data.get("max_kostnad_usd", 2.0)),
        tak_faktor=float(spec_data.get("tak_faktor", 1.5)),
        tak_sek_explicit=args.tak_sek if args.tak_sek is not None else spec_data.get("tak_sek_explicit"),
        plats_preferens=args.plats or spec_data.get("plats_preferens", "auto"),
        kostnad_per_enhet_usd=float(spec_data.get("kostnad_per_enhet_usd", 0.0)),
        krav_godkannande_over_5min=args.krav_godkannande or bool(spec_data.get("krav_godkannande_over_5min", False)),
        torr=args.torr or bool(spec_data.get("torr", False)),
        mansklig_grind_beskrivning=spec_data.get("mansklig_grind_beskrivning"),
        extra=spec_data.get("extra", {}),
    )
    enheter = spec_data["enheter"]
    kor_enhet = _ladda_callable(spec_data["kor_enhet"])
    kor_fjarr = _ladda_callable(spec_data["kor_batch_fjarr"]) if spec_data.get("kor_batch_fjarr") else None
    mg_fn = _ladda_callable(spec_data["mansklig_grind_fn"]) if spec_data.get("mansklig_grind_fn") else None

    korare = JobbKorare(spec)
    try:
        res = korare.kor(enheter, kor_enhet, kor_batch_fjarr=kor_fjarr, mansklig_grind_fn=mg_fn)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    except GrindStopp as e:
        print(json.dumps({"stoppad": e.kod, "meddelande": str(e), "data": e.data}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 42


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
