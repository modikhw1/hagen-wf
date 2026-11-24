"""K7: logg över varje anrop från CM:s mening till förhandsvisningen, och en spärr.

Spärren slår till (K7Brott, rad med "brott" i loggen) när
  - en funktion vars namn eller modul träffar FORBJUDNA anropas genom vakten (spegling, generering,
    betalda modeller: Jev, Gemini, Codex, Seedance, Dreamina …),
  - något i kedjan öppnar en nätverksanslutning (socket.connect / create_connection),
  - något i kedjan startar en underprocess (subprocess.Popen), t.ex. codex eller curl.
Allt annat loggas som "ok" med tid i ms. Loggen är JSON per rad.
`larmprov()` visar att spärren kan larma: tre avsiktliga brott ska ge rött.
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
import pathlib

FORBJUDNA = ("spegl", "mirror", "byt_hand", "balvridning", "generer", "generat", "seedance", "dreamina", "kling", "luma",
             "wan_vace", "gemini", "jev", "typesafe", "systemone", "codex", "openai", "anthropic", "beacon", "higgsfield",
             "elevenlabs", "imagegen", "kimodo_api")


TILLATNA_PROCESSER = {"ffmpeg", "ffprobe"}  # medielagrets klipp/ljud (spår D); inget annat får starta


class K7Brott(RuntimeError):
    pass


class Vakt:
    def __init__(self, logg_fil: str | pathlib.Path):
        self.logg_fil = pathlib.Path(logg_fil)
        self.logg_fil.parent.mkdir(parents=True, exist_ok=True)
        self.rader: list[dict] = []
        self._orig = {}
        self.mening_id = None
        self.brott = 0
        self.natanslutningar = 0
        self.underprocesser = 0

    # ------------------------------------------------------------ in/ut ur kedjan
    def __enter__(self):
        vakt = self
        self._orig = dict(connect=socket.socket.connect, create_connection=socket.create_connection, popen_init=subprocess.Popen.__init__)

        def connect(sock, adress, *a, **k):
            vakt.natanslutningar += 1
            vakt._skriv(dict(funktion="socket.connect", mal=str(adress), utfall="brott", skal="nätverksanslutning i CM:s ändringsled"))
            raise K7Brott(f"K7: nätverksanslutning till {adress}")

        def create_connection(adress, *a, **k):
            vakt.natanslutningar += 1
            vakt._skriv(dict(funktion="socket.create_connection", mal=str(adress), utfall="brott", skal="nätverksanslutning i CM:s ändringsled"))
            raise K7Brott(f"K7: nätverksanslutning till {adress}")

        def popen_init(proc, args, *a, **k):
            forsta = (args[0] if isinstance(args, (list, tuple)) else str(args).split()[0]) if args else ""
            if pathlib.Path(str(forsta)).stem.lower() in TILLATNA_PROCESSER:
                vakt._skriv(dict(funktion="subprocess.Popen", mal=str(args)[:200], utfall="ok", skal="tillåten (medielagrets ffmpeg, inte generativt)"))
                return vakt._orig["popen_init"](proc, args, *a, **k)
            vakt.underprocesser += 1
            vakt._skriv(dict(funktion="subprocess.Popen", mal=str(args)[:200], utfall="brott", skal="underprocess i CM:s ändringsled"))
            raise K7Brott(f"K7: underprocess {str(args)[:80]}")

        socket.socket.connect = connect
        socket.create_connection = create_connection
        subprocess.Popen.__init__ = popen_init
        return self

    def __exit__(self, *exc):
        socket.socket.connect = self._orig["connect"]
        socket.create_connection = self._orig["create_connection"]
        subprocess.Popen.__init__ = self._orig["popen_init"]
        return False

    # ------------------------------------------------------------ anrop
    def _skriv(self, rad):
        rad = dict(tid=time.strftime("%Y-%m-%dT%H:%M:%S"), mening=self.mening_id, **rad)
        if rad.get("utfall") == "brott":
            self.brott += 1
        self.rader.append(rad)
        with self.logg_fil.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rad, ensure_ascii=False) + "\n")

    def anrop(self, namn: str, fn, *args, **kwargs):
        fullt = f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__qualname__', namn)}"
        traff = [w for w in FORBJUDNA if w in namn.lower() or w in fullt.lower()]
        if traff:
            self._skriv(dict(funktion=namn, modul=fullt, utfall="brott", skal=f"förbjudet i CM:s ändringsled: {traff}"))
            raise K7Brott(f"K7: {namn} ({fullt}) träffar {traff}")
        t0 = time.perf_counter()
        try:
            ut = fn(*args, **kwargs)
            self._skriv(dict(funktion=namn, modul=fullt, utfall="ok", ms=round((time.perf_counter() - t0) * 1000, 2)))
            return ut
        except K7Brott:
            raise
        except Exception as e:
            self._skriv(dict(funktion=namn, modul=fullt, utfall="undantag", fel=f"{type(e).__name__}: {e}"[:300],
                             ms=round((time.perf_counter() - t0) * 1000, 2)))
            raise


def larmprov(logg_fil) -> dict:
    """Tre avsiktliga brott. Alla tre ska ge K7Brott och en röd rad, annars är spärren inte bevisad."""
    import sys
    rot = pathlib.Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(rot / "forvarld_karna"))
    sys.path.insert(0, str(rot / "byggsten/brygga"))
    ut = {}
    with Vakt(logg_fil) as v:
        v.mening_id = "LARMPROV"
        # 1. spegling ur kärnan (struken 0031/0038)
        try:
            import mening_motor
            v.anrop("drag.byt_hand", mening_motor._byt_hand_med_balvridning, None, [])
            ut["spegling"] = "INTE STOPPAD"
        except K7Brott as e:
            ut["spegling"] = f"stoppad: {e}"
        # 2. nätverk (som ett API-anrop till en betald modell)
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=0.2)
            ut["natverk"] = "INTE STOPPAD"
        except K7Brott as e:
            ut["natverk"] = f"stoppad: {e}"
        # 3. underprocess (som codex exec)
        try:
            subprocess.run(["codex", "exec", "hej"], capture_output=True)
            ut["underprocess"] = "INTE STOPPAD"
        except K7Brott as e:
            ut["underprocess"] = f"stoppad: {e}"
        ut["brott_i_loggen"] = v.brott
    ut["godkant"] = all(str(x).startswith("stoppad") for k, x in ut.items() if k in ("spegling", "natverk", "underprocess")) and ut["brott_i_loggen"] == 3
    return ut
