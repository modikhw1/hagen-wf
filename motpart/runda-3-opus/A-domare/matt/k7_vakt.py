# -*- coding: utf-8 -*-
"""K7-spärren (mått d): inget generativt och ingen struken metod i CM:s ändringsled.

Två lägen:

  1. Körvakt (det som räknas):
       python k7_vakt.py --logg ut.json -- path/till/andringsled.py [args ...]
     Kör målskriptet i samma process med tre vakter installerade INNAN det startar:
       - nät: varje socket.connect / getaddrinfo mot en icke-lokal adress loggas och STOPPAS
         (PermissionError), så att inget betalt anrop hinner gå iväg;
       - import: moduler ur GENERATIVA (fal_client, openai, google.genai, diffusers, ...) loggas
         och stoppas (ImportError);
       - underprocess: kommandon som innehåller codex/gemini/claude/curl/seedance/... loggas och
         stoppas;
       - metodnamn: varje anropad funktion utanför standardbiblioteket vars namn matchar
         STRUKNA (spegl, mirror, flip, ...) loggas (stoppas inte, men gör utfallet rött).
     Utfall: "gron" om noll träffar, annars "rod". Exitkod 0 = grön, 3 = röd, målets egen
     exitkod bevaras i loggen.

  2. Statisk genomsökning (stöd, inte dom):
       python k7_vakt.py --statisk mapp_eller_fil [...]
     AST-läsning av importer, funktionsnamn och URL-strängar. Säger var något KAN anropas.

  3. Självtest med felinjektion (protokollregel: grinden ska visas kunna larma):
       python k7_vakt.py --sjalvtest

Kända gränser: metodspärren är namnbaserad (en spegling som heter något annat syns inte);
nätspärren ser bara anrop från denna process och dess Python-trådar, inte en redan körande
server som målet pratar med via localhost. Lokala generativa modeller som laddas utan någon
av de listade modulerna syns inte heller. Se README.
"""
from __future__ import annotations

import argparse
import ast
import importlib.abc
import ipaddress
import json
import os
import re
import runpy
import socket
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
from pathlib import Path

GENERATIVA = {
    "fal_client", "fal", "openai", "google.genai", "google.generativeai", "vertexai",
    "replicate", "higgsfield", "dreamina", "seedance", "runwayml", "lumaai", "luma",
    "stability_sdk", "diffusers", "elevenlabs", "anthropic", "together", "cohere",
    "mistralai", "huggingface_hub.inference", "gradio_client", "comfy", "invokeai",
}
KOMMANDO_SPARR = re.compile(r"\b(codex|gemini|claude|curl|wget|seedance|dreamina|higgsfield|fal)\b", re.I)
STRUKNA = re.compile(r"(spegl|mirror|flip|reflekt|reflect)", re.I)
GEN_URL = re.compile(r"(api\.openai\.com|generativelanguage\.googleapis|aiplatform\.googleapis|fal\.run|"
                     r"queue\.fal|replicate\.com|higgsfield|dreamina|seedance|runwayml|lumalabs|"
                     r"api\.stability|api\.elevenlabs|api\.anthropic)", re.I)

STDLIB = {Path(sysconfig.get_paths()[k]).resolve().as_posix().lower()
          for k in ("stdlib", "platstdlib", "purelib", "platlib") if sysconfig.get_paths().get(k)}


class Vakt:
    def __init__(self):
        self.handelser: list[dict] = []
        self.lock = threading.Lock()
        self.sedda_namn: set[tuple[str, str]] = set()

    def logga(self, typ: str, **kw):
        with self.lock:
            self.handelser.append({"typ": typ, "t": round(time.time(), 3), **kw})


VAKT = Vakt()


def _lokal(host) -> bool:
    if host is None:
        return True
    h = str(host).strip("[]").lower()
    if h in {"localhost", "", "0.0.0.0"}:
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def _audit(event, args):
    try:
        if event == "socket.connect":
            addr = args[1]
            host = addr[0] if isinstance(addr, tuple) and addr else addr
            if isinstance(host, (str, bytes)) and not _lokal(host if isinstance(host, str) else host.decode()):
                VAKT.logga("nat", detalj=f"connect {addr!r}")
                raise PermissionError(f"K7-vakt: nätanrop stoppat ({addr!r})")
        elif event == "socket.getaddrinfo":
            host = args[0]
            if isinstance(host, bytes):
                host = host.decode(errors="ignore")
            if not _lokal(host):
                VAKT.logga("nat", detalj=f"getaddrinfo {host!r}")
                raise PermissionError(f"K7-vakt: namnuppslagning stoppad ({host!r})")
        elif event == "subprocess.Popen":
            cmd = args[1]
            txt = " ".join(map(str, cmd)) if isinstance(cmd, (list, tuple)) else str(cmd)
            if KOMMANDO_SPARR.search(txt):
                VAKT.logga("underprocess", detalj=txt[:300])
                raise PermissionError(f"K7-vakt: underprocess stoppad ({txt[:80]})")
        elif event == "os.system":
            txt = str(args[0])
            if KOMMANDO_SPARR.search(txt):
                VAKT.logga("underprocess", detalj=txt[:300])
                raise PermissionError("K7-vakt: os.system stoppad")
    except PermissionError:
        raise
    except Exception:
        pass


class SparrFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        for g in GENERATIVA:
            if fullname == g or fullname.startswith(g + "."):
                VAKT.logga("import", detalj=fullname)
                raise ImportError(f"K7-vakt: import av generativ modul stoppad ({fullname})")
        return None


def _ar_stdlib(fn: str) -> bool:
    if not fn or fn.startswith("<"):
        return True
    p = fn.replace("\\", "/").lower()
    return any(p.startswith(s) for s in STDLIB) or "/site-packages/" in p


def _profil(frame, event, arg):
    if event != "call":
        return
    co = frame.f_code
    namn = co.co_name
    if STRUKNA.search(namn) and not _ar_stdlib(co.co_filename):
        nyckel = (co.co_filename, namn)
        if nyckel not in VAKT.sedda_namn:
            VAKT.sedda_namn.add(nyckel)
            VAKT.logga("struken_metod", detalj=f"{namn} i {co.co_filename}:{co.co_firstlineno}")


def installera():
    sys.addaudithook(_audit)
    sys.meta_path.insert(0, SparrFinder())
    sys.setprofile(_profil)
    threading.setprofile(_profil)


def kor_vakt(mal: list[str], logg: str | None) -> int:
    installera()
    skript = mal[0]
    sys.argv = list(mal)
    mal_exit = 0
    fel = None
    t0 = time.time()
    try:
        runpy.run_path(skript, run_name="__main__")
    except SystemExit as e:
        mal_exit = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException as e:  # målets fel loggas, utfallet avgörs ändå av vakterna
        fel = f"{type(e).__name__}: {e}"
        mal_exit = 1
    sys.setprofile(None)
    threading.setprofile(None)
    utfall = "rod" if VAKT.handelser else "gron"
    rapport = {
        "matt": "K7-vakt (körvakt)",
        "mal": mal,
        "utfall": utfall,
        "traffar": VAKT.handelser,
        "mal_exitkod": mal_exit,
        "mal_fel": fel,
        "sekunder": round(time.time() - t0, 2),
        "obs": "Grön betyder: inga generativa importer, inga icke-lokala nätanrop, inga spärrade "
               "kommandon och inga funktionsnamn som matchar strukna metoder under DENNA körning.",
    }
    txt = json.dumps(rapport, ensure_ascii=False, indent=1)
    if logg:
        Path(logg).write_text(txt, encoding="utf-8")
    sys.__stdout__.write("\nK7-VAKT: " + utfall.upper() + f" ({len(VAKT.handelser)} träffar)\n")
    for h in VAKT.handelser:
        sys.__stdout__.write(f"  {h['typ']}: {h['detalj']}\n")
    return 0 if utfall == "gron" else 3


def statisk(vagar: list[str]) -> dict:
    traffar = []
    filer = []
    for v in vagar:
        p = Path(v)
        filer += [p] if p.is_file() else sorted(p.rglob("*.py"))
    for f in filer:
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except (SyntaxError, OSError) as e:
            traffar.append({"fil": str(f), "rad": 0, "typ": "oläslig", "detalj": str(e)[:80]})
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if any(a.name == g or a.name.startswith(g + ".") for g in GENERATIVA):
                        traffar.append({"fil": str(f), "rad": n.lineno, "typ": "import", "detalj": a.name})
            elif isinstance(n, ast.ImportFrom) and n.module:
                if any(n.module == g or n.module.startswith(g + ".") for g in GENERATIVA):
                    traffar.append({"fil": str(f), "rad": n.lineno, "typ": "import", "detalj": n.module})
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and STRUKNA.search(n.name):
                traffar.append({"fil": str(f), "rad": n.lineno, "typ": "struken_def", "detalj": n.name})
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                if GEN_URL.search(n.value):
                    traffar.append({"fil": str(f), "rad": n.lineno, "typ": "gen_url", "detalj": n.value[:120]})
                elif re.search(r"\bcodex\b.*\b(exec|image|imagegen)\b|\bimagegen\b|image_generation", n.value, re.I):
                    traffar.append({"fil": str(f), "rad": n.lineno, "typ": "gen_kommando", "detalj": n.value[:120]})
    return {"matt": "K7 statisk genomsökning", "filer": len(filer), "traffar": traffar}


INJEKTIONER = {
    "ren_numpy": ("import numpy as np\nx=np.arange(10)\nprint(float(x.mean()))\n", "gron"),
    "ren_lokal_socket": ("import socket\ns=socket.socket()\ntry:\n    s.connect(('127.0.0.1', 9))\nexcept OSError:\n    pass\n", "gron"),
    "inj_import_fal": ("import fal_client\n", "rod"),
    "inj_import_openai_inne_i_try": ("try:\n    import openai\nexcept ImportError:\n    pass\n", "rod"),
    "inj_nat_openai": ("import urllib.request\ntry:\n    urllib.request.urlopen('https://api.openai.com/v1/images/generations', timeout=2)\nexcept Exception:\n    pass\n", "rod"),
    "inj_nat_ip": ("import socket\ns=socket.socket()\ntry:\n    s.connect(('8.8.8.8', 443))\nexcept Exception:\n    pass\n", "rod"),
    "inj_codex_underprocess": ("import subprocess\ntry:\n    subprocess.run(['codex','exec','gör en bild'])\nexcept Exception:\n    pass\n", "rod"),
    "inj_spegling": ("def spegla_armar(x):\n    return [-v for v in x]\nspegla_armar([1,2])\n", "rod"),
    "inj_mirror_i_klass": ("class K:\n    def mirror_pose(self):\n        return 1\nK().mirror_pose()\n", "rod"),
}


def sjalvtest() -> int:
    ut = {}
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        for namn, (kod, vantat) in INJEKTIONER.items():
            f = Path(td) / f"{namn}.py"
            f.write_text(kod, encoding="utf-8")
            logg = Path(td) / f"{namn}.json"
            r = subprocess.run([sys.executable, __file__, "--logg", str(logg), "--", str(f)],
                               capture_output=True, text=True, timeout=300)
            j = json.loads(logg.read_text(encoding="utf-8")) if logg.exists() else {"utfall": "inget"}
            traff = j["utfall"] == vantat
            ok += traff
            ut[namn] = {"vantat": vantat, "fick": j["utfall"], "ratt": traff,
                        "traffar": [h["typ"] for h in j.get("traffar", [])]}
            print(f"{'OK ' if traff else 'FEL'} {namn:32s} väntat={vantat:5s} fick={j['utfall']}")
    print(f"självtest: {ok}/{len(INJEKTIONER)} rätt")
    Path(__file__).with_name("k7_vakt_sjalvtest.json").write_text(
        json.dumps({"ratt": ok, "av": len(INJEKTIONER), "fall": ut}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if ok == len(INJEKTIONER) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logg")
    ap.add_argument("--statisk", nargs="+")
    ap.add_argument("--sjalvtest", action="store_true")
    ap.add_argument("mal", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    if a.sjalvtest:
        sys.exit(sjalvtest())
    if a.statisk:
        r = statisk(a.statisk)
        txt = json.dumps(r, ensure_ascii=False, indent=1)
        if a.logg:
            Path(a.logg).write_text(txt, encoding="utf-8")
        print(txt)
        return
    mal = a.mal[1:] if a.mal and a.mal[0] == "--" else a.mal
    if not mal:
        ap.error("ange mål efter --")
    sys.exit(kor_vakt(mal, a.logg))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
