"""Modal-baserad varm beräkningstjänst med beständig volym (INFRA.md §1, §2, M1, M2, M3, M6).

Deploy (en gång; inga nyckelfiler från repots rot skickas med, §6):
    .\\scen\\.venv\\Scripts\\modal.exe deploy infra/modal_tjanst.py

Beständig volym `hagen-olager` under `/vol`:
    /vol/kallor/<id>.mp4          200+ källklipp (uppladdade en gång, aldrig per körning)
    /vol/meta/repo_meta.json      metadata ur klipp.jsonl, bibliotek-v6.json, manifest.jsonl
    /vol/meta/urval_las.json      låst steg 2-urval (144 R + 12 testklipp)
    /vol/olager/<id>/             komplett versionerat O-lager (meta, rutor jpack, wav16k, orig, e28/e30/e37, c_ref)

Kostnadskontroll:
    scaledown_window=900 (15 min varm efter senaste anrop -> 0 kallstarter i normal iteration, $0/h i vila).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import modal

ROT = Path(__file__).resolve().parents[1]
IS_LOCAL = (ROT / "infra" / "olager.py").exists()

app = modal.App("hagen-infra")
vol = modal.Volume.from_name("hagen-olager", create_if_missing=True)

img = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "xz-utils", "ca-certificates", "libgl1", "libglib2.0-0", "libsndfile1", "nodejs")
    .run_commands(
        # Installera statisk Linux FFmpeg 8.1 (matchar lokal ffmpeg 8.1) med fallback till master-latest
        "set -e; "
        "URL81='https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz'; "
        "URLM='https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz'; "
        "(curl -fsSL \"$URL81\" -o /tmp/ff.tar.xz || curl -fsSL \"$URLM\" -o /tmp/ff.tar.xz); "
        "mkdir -p /tmp/ff && tar -xJf /tmp/ff.tar.xz -C /tmp/ff --strip-components=1; "
        "install -m 755 /tmp/ff/bin/ffmpeg /usr/local/bin/ffmpeg; "
        "install -m 755 /tmp/ff/bin/ffprobe /usr/local/bin/ffprobe; "
        "rm -rf /tmp/ff /tmp/ff.tar.xz; "
        "ffmpeg -version | head -n 2"
    )
    .pip_install(
        "torch==2.6.0",
        "torchaudio==2.6.0",
        index_url="https://download.pytorch.org/whl/cpu",
    )
    .pip_install(
        "numpy>=1.26,<2.3",
        "scipy",
        "onnxruntime",
        "silero-vad",
        "ultralytics",
        "opencv-python-headless",
        "pillow",
        "yt-dlp[default,curl-cffi]==2026.10.26",
    )
    .run_commands(
        # För-ladda Silero ONNX-modellen i imagen så kallstart inte kräver nätverk
        "python -c 'from silero_vad import load_silero_vad; load_silero_vad(onnx=True); print(\"silero_ok\")'"
    )
    .env(
        {
            "PYTHONPATH": "/app",
            "PYTHONUNBUFFERED": "1",
            "YOLO_OFFLINE": "1",
            "ULTRALYTICS_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "YOLO_CONFIG_DIR": "/tmp/ultralytics",
        }
    )
)

# Säkerhet (§6): lägg BARA till uttryckliga kod- och viktfiler, aldrig rotens nyckelfiler!
if IS_LOCAL:
    img = (
        img.add_local_file(str(ROT / "infra" / "__init__.py"), "/app/infra/__init__.py")
        .add_local_file(str(ROT / "infra" / "rang.py"), "/app/infra/rang.py")
        .add_local_file(str(ROT / "infra" / "extraktorer.py"), "/app/infra/extraktorer.py")
        .add_local_file(str(ROT / "infra" / "olager.py"), "/app/infra/olager.py")
        .add_local_file(str(ROT / "infra" / "steg2_snabb.py"), "/app/infra/steg2_snabb.py")
        .add_local_file(str(ROT / "data" / "format" / "e37" / "yolov8n.pt"), "/app/data/format/e37/yolov8n.pt")
    )

VOL_ROT = Path("/vol")
KALLOR_DIR = VOL_ROT / "kallor"
OLAGER_DIR = VOL_ROT / "olager"
META_DIR = VOL_ROT / "meta"
VIKTER_FIL = Path("/app/data/format/e37/yolov8n.pt")


@app.cls(
    image=img,
    cpu=4.0,
    memory=8192,
    timeout=900,
    scaledown_window=900,
    volumes={"/vol": vol},
)
class VarmArbetare:
    """Varm arbetare med förladdad Silero ONNX + YOLOv8n och beständig volym."""

    @modal.enter()
    def starta(self) -> None:
        t0 = time.monotonic()
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from infra.extraktorer import VarmExtraktor

        self.extr = VarmExtraktor(yolo_vikter=VIKTER_FIL, torch_threads=2)
        self.anrop = 0
        self.ff_ver = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
        self.container_laddtid_sek = round(time.monotonic() - t0, 3)

    @modal.method()
    def ping(self) -> dict[str, Any]:
        """Verifierar M6: noll kallstart vid normal iteration (modeller redan i minnet)."""
        t0 = time.perf_counter()
        self.anrop += 1
        vol.reload()
        n_olager = sum(1 for p in OLAGER_DIR.iterdir() if p.is_dir() and (p / "meta.json").exists()) if OLAGER_DIR.exists() else 0
        return {
            "varm": self.anrop > 1,
            "anrop_nr": self.anrop,
            "container_laddtid_sek": self.container_laddtid_sek,
            "extraktor_laddtid_sek": self.extr.laddtid_sek,
            "svar_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            "ffmpeg": self.ff_ver,
            "n_olager_klipp": n_olager,
            "shm_fri_gb": round(os.statvfs("/dev/shm").f_bavail * os.statvfs("/dev/shm").f_frsize / (1024**3), 2) if Path("/dev/shm").exists() else None,
        }

    @modal.method()
    def bygg_olager_chunk(
        self,
        clip_ids: list[str],
        force: bool = False,
        med_c_ref: bool = True,
    ) -> list[dict[str, Any]]:
        """Bygger O-lager (+ c_ref.json i /dev/shm) för en batch klipp och commitar volymen en gång."""
        from infra.olager import bygg_klipp
        from infra.steg2_snabb import mat_ref_c_klipp

        vol.reload()
        repo_meta_fil = META_DIR / "repo_meta.json"
        repo_meta = json.loads(repo_meta_fil.read_text(encoding="utf-8")) if repo_meta_fil.exists() else {}

        resultat: list[dict[str, Any]] = []
        for cid in clip_ids:
            vid = KALLOR_DIR / f"{cid}.mp4"
            if not vid.exists():
                resultat.append({"id": cid, "status": "saknar_kalla"})
                continue
            r = bygg_klipp(
                cid,
                vid,
                OLAGER_DIR,
                self.extr,
                extra_meta=repo_meta.get(cid),
                force=force,
                ffmpeg_threads=2,
            )
            if med_c_ref:
                c_fil = OLAGER_DIR / cid / "c_ref.json"
                if force or not c_fil.exists():
                    c_res = mat_ref_c_klipp(cid, vid, self.extr)
                    tmp = c_fil.with_suffix(".json.tmp")
                    tmp.write_text(json.dumps(c_res, ensure_ascii=False), encoding="utf-8")
                    os.replace(tmp, c_fil)
                    r["c_ref_sek"] = c_res.get("total_sek")
            r["status"] = "ok"
            resultat.append(r)

        vol.commit()
        return resultat

    @modal.method()
    def ingest_url(self, url: str, clip_id: str, force: bool = True) -> dict[str, Any]:
        """M3 (enstaka klipp): från TikTok-URL till komplett O-lager på < 60 s."""
        from infra.olager import bygg_klipp, hamta_fran_url

        t0 = time.monotonic()
        vol.reload()
        KALLOR_DIR.mkdir(parents=True, exist_ok=True)
        ut_mp4 = KALLOR_DIR / f"{clip_id}.mp4"
        t_h0 = time.monotonic()
        hamta_fran_url(url, ut_mp4, ytdlp_cmd=["yt-dlp"])
        t_hamta = round(time.monotonic() - t_h0, 3)

        t_b0 = time.monotonic()
        bygg = bygg_klipp(clip_id, ut_mp4, OLAGER_DIR, self.extr, url=url, force=force, ffmpeg_threads=4)
        t_bygg = round(time.monotonic() - t_b0, 3)

        t_c0 = time.monotonic()
        vol.commit()
        t_commit = round(time.monotonic() - t_c0, 3)

        return {
            "id": clip_id,
            "url": url,
            "hamta_sek": t_hamta,
            "bygg_sek": t_bygg,
            "commit_sek": t_commit,
            "total_sek": round(time.monotonic() - t0, 3),
            "mp4_bytes": ut_mp4.stat().st_size,
            "olager": bygg,
        }

    @modal.method()
    def mat_m1(self, clip_ids: list[str] | None = None, antal_varv: int = 3) -> dict[str, Any]:
        """Mäter M1 (< 50 ms per klipp) direkt mot O-lagret på volym och i RAM-cache."""
        import numpy as np
        from infra.olager import OLager

        vol.reload()
        ol = OLager(OLAGER_DIR)
        ids = clip_ids or ol.lista_klipp()[:40]
        t_disk: list[float] = []
        t_disk_6r: list[float] = []

        for _ in range(antal_varv):
            for cid in ids:
                t0 = time.perf_counter()
                kl = ol.las_klipp(cid, ladda_ljud=True, ladda_jpack_bytes=False)
                t_disk.append((time.perf_counter() - t0) * 1000.0)

                nr = kl["rutor_index"]["n_rutor"]
                ix = [int(x) for x in np.linspace(0, max(nr - 1, 0), min(6, nr))]
                t0 = time.perf_counter()
                ol.las_klipp(cid, ladda_ljud=True, dekoda_rutor=ix)
                t_disk_6r.append((time.perf_counter() - t0) * 1000.0)

        forl = ol.forladda_i_minnet(ids, med_jpack=True)
        t_ram: list[float] = []
        for _ in range(antal_varv * 2):
            for cid in ids:
                t0 = time.perf_counter()
                ol.las_klipp(cid, anvand_cache=True)
                t_ram.append((time.perf_counter() - t0) * 1000.0)

        return {
            "n_klipp": len(ids),
            "volym_meta_ljud_ms": {
                "median": round(float(np.median(t_disk)), 2),
                "p95": round(float(np.percentile(t_disk, 95)), 2),
                "max": round(float(np.max(t_disk)), 2),
            },
            "volym_inkl_6_rutor_dekod_ms": {
                "median": round(float(np.median(t_disk_6r)), 2),
                "p95": round(float(np.percentile(t_disk_6r, 95)), 2),
                "max": round(float(np.max(t_disk_6r)), 2),
            },
            "ram_forladdning": forl,
            "ram_cache_ms": {
                "median": round(float(np.median(t_ram)), 4),
                "max": round(float(np.max(t_ram)), 4),
            },
        }

    @modal.method()
    def steg2_ref_chunk(self, clip_ids: list[str], fran_olager: bool = False) -> list[dict[str, Any]]:
        """Läser C-referens ur O-lagret eller räknar om C i /dev/shm för en grupp referensklipp."""
        from infra.steg2_snabb import mat_ref_c_klipp

        vol.reload()
        ut: list[dict[str, Any]] = []
        for cid in clip_ids:
            c_fil = OLAGER_DIR / cid / "c_ref.json"
            if fran_olager and c_fil.exists():
                ut.append(json.loads(c_fil.read_text(encoding="utf-8")))
            else:
                ut.append(mat_ref_c_klipp(cid, KALLOR_DIR / f"{cid}.mp4", self.extr))
        return ut

    @modal.method()
    def steg2_test_klipp(self, clip_id: str) -> dict[str, Any]:
        """Bygger och mäter alla 13 varianter (O, C, C2, Cr, N0, N0r, N1..N6, P) i /dev/shm."""
        from infra.steg2_snabb import mat_test_klipp

        vol.reload()
        return mat_test_klipp(clip_id, KALLOR_DIR / f"{clip_id}.mp4", self.extr)

    @modal.method()
    def sammanfatta(self) -> dict[str, Any]:
        vol.reload()
        klipp = sorted(p.name for p in OLAGER_DIR.iterdir() if p.is_dir() and (p / "meta.json").exists()) if OLAGER_DIR.exists() else []
        n_cref = sum(1 for c in klipp if (OLAGER_DIR / c / "c_ref.json").exists())
        bytes_ol = sum(p.stat().st_size for p in OLAGER_DIR.rglob("*") if p.is_file()) if OLAGER_DIR.exists() else 0
        bytes_kal = sum(p.stat().st_size for p in KALLOR_DIR.glob("*.mp4")) if KALLOR_DIR.exists() else 0
        return {
            "n_olager": len(klipp),
            "n_c_ref": n_cref,
            "olager_mb": round(bytes_ol / (1024**2), 1),
            "kallor_mb": round(bytes_kal / (1024**2), 1),
        }


@app.function(
    image=img,
    cpu=2.0,
    memory=4096,
    timeout=900,
    scaledown_window=900,
    volumes={"/vol": vol},
)
def orkestrera_olager_200(chunk_storlek: int = 8, force: bool = False, med_c_ref: bool = True) -> dict[str, Any]:
    """Bygger O-lagret för alla 200 klipp i /vol/kallor parallellt (M3 batch < 10 min)."""
    t0 = time.monotonic()
    vol.reload()
    ids = sorted(p.stem for p in KALLOR_DIR.glob("*.mp4"))
    chunks = [ids[i : i + chunk_storlek] for i in range(0, len(ids), chunk_storlek)]
    arb = VarmArbetare()
    alla: list[dict[str, Any]] = []
    for batch_res in arb.bygg_olager_chunk.map(chunks, kwargs={"force": force, "med_c_ref": med_c_ref}):
        alla.extend(batch_res)
    ok = [r for r in alla if r.get("status") == "ok"]
    tot_mb = round(sum(r.get("olager_bytes", 0) for r in ok) / (1024**2), 1)
    return {
        "antal_klipp": len(ids),
        "antal_ok": len(ok),
        "antal_fel": len(alla) - len(ok),
        "n_chunks": len(chunks),
        "vaggtid_sek": round(time.monotonic() - t0, 2),
        "total_olager_mb": tot_mb,
        "medel_sek_per_klipp": round(sum(r.get("sek", 0) for r in ok) / max(len(ok), 1), 2),
    }


@app.function(
    image=img,
    cpu=2.0,
    memory=4096,
    timeout=900,
    scaledown_window=900,
    volumes={"/vol": vol},
)
def orkestrera_steg2(fran_olager: bool = True, ref_chunk_storlek: int = 6) -> dict[str, Any]:
    """Kör hela steg 2 (144 referensklipp + 12 testklipp x 13 varianter + A3/A4-analys) för M2 (< 3 min)."""
    from infra.steg2_snabb import kor_analys

    t0 = time.monotonic()
    vol.reload()
    urv = json.loads((META_DIR / "urval_las.json").read_text(encoding="utf-8"))
    ref_ids = urv["reference_ids"]
    test_ids = [x["id"] for x in urv["step2"]]

    arb = VarmArbetare()

    # Starta ref- och testjobb SAMTIDIGT för lägsta väggtid!
    t_par0 = time.monotonic()
    if fran_olager:
        # Läs alla 144 c_ref direkt från O-lagret på volymen i ett svep (< 1 s)
        ref_rows: list[dict[str, Any]] = []
        saknade_ref: list[str] = []
        for cid in ref_ids:
            cf = OLAGER_DIR / cid / "c_ref.json"
            if cf.exists():
                ref_rows.append(json.loads(cf.read_text(encoding="utf-8")))
            else:
                saknade_ref.append(cid)
        t_ref_las = round(time.monotonic() - t_par0, 3)
        ref_calls = [arb.steg2_ref_chunk.spawn(saknade_ref[i : i + ref_chunk_storlek], False)
                     for i in range(0, len(saknade_ref), ref_chunk_storlek)]
    else:
        t_ref_las = 0.0
        ref_rows = []
        ref_calls = [arb.steg2_ref_chunk.spawn(ref_ids[i : i + ref_chunk_storlek], False)
                     for i in range(0, len(ref_ids), ref_chunk_storlek)]

    test_calls = [arb.steg2_test_klipp.spawn(cid) for cid in test_ids]

    for fc in ref_calls:
        ref_rows.extend(fc.get())
    t_ref_klar = round(time.monotonic() - t_par0, 2)

    test_results = [fc.get() for fc in test_calls]
    test_rows: list[dict[str, Any]] = []
    per_klipp_sek: dict[str, float] = {}
    for tr in test_results:
        per_klipp_sek[tr["id"]] = tr["total_sek"]
        test_rows.extend(tr["rader"])
    t_test_klar = round(time.monotonic() - t_par0, 2)

    t_an0 = time.monotonic()
    analys = kor_analys(ref_rows, test_rows, test_ids)
    t_analys = round(time.monotonic() - t_an0, 3)

    vaggtid = round(time.monotonic() - t0, 2)
    ut = {
        "fran_olager": fran_olager,
        "vaggtid_sek": vaggtid,
        "ref_las_sek": t_ref_las,
        "ref_klar_sek": t_ref_klar,
        "test_klar_sek": t_test_klar,
        "analys_sek": t_analys,
        "per_testklipp_sek": per_klipp_sek,
        "n_ref_rader": len(ref_rows),
        "n_test_rader": len(test_rows),
        "analys": analys,
    }
    # Spara mätresultatet i volymen för reproducerbarhet
    ut_dir = VOL_ROT / "resultat"
    ut_dir.mkdir(exist_ok=True)
    namn = "steg2_olager.json" if fran_olager else "steg2_omrakning.json"
    (ut_dir / namn).write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    vol.commit()
    return ut
