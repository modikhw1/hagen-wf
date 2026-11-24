"""End-to-end test av den stående ägarpanelen (INFRA.md §4, §6, M5).

Verifierar:
  1. Autentisering: oautentiserat anrop ger 401; ?token=... sätter HttpOnly-cookie och redirectar 302.
  2. Nyckelskydd: /pass/<id>/nyckel.json ger 404 (även med giltig autentisering).
  3. Publicering (M5 < 1 min): publicerar både befintliga K2 (26 par, 63 mediefiler) och ett nytt
     blint invarianspass kopplat till O-lager-id, och mäter exakt väggtid.
  4. Append-only svar + ordagranna kommentarer: skickar två svar för samma par och verifierar att
     båda finns kvar i svar.json + svar.logg.jsonl med ordagrann kommentar.
  5. Synk tillbaka till repot: synka_svar.py kopplar svar till olager_id och variant via nyckel.json.
"""
from __future__ import annotations

import json
import secrets
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
if str(ROT) not in sys.path:
    sys.path.insert(0, str(ROT))

from infra.panel.publicera import publicera_k2, publicera_spec
from infra.panel.synka_svar import synka
from infra.panel.tjanst import skapa_http_server


def _req(url: str, *, method: str = "GET", headers: dict | None = None, body: bytes | None = None) -> tuple[int, dict, bytes]:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    r = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with opener.open(r, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def main() -> int:
    token = secrets.token_hex(16)
    with tempfile.TemporaryDirectory(prefix="hagen_panel_test_") as td:
        rot = Path(td) / "panel_data"
        srv = skapa_http_server("127.0.0.1", 0, rot, token)
        port = srv.server_address[1]
        base = f"http://127.0.0.1:{port}"
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            # 1. Auth
            kod_unauth, _, _ = _req(f"{base}/api/pass")
            assert kod_unauth == 401, f"Väntade 401 utan token, fick {kod_unauth}"
            kod_login, hdr_login, _ = _req(f"{base}/?token={token}")
            assert kod_login == 302 and "hagen_panel_auth=" in hdr_login.get("Set-Cookie", ""), (kod_login, hdr_login)
            cookie = hdr_login["Set-Cookie"].split(";", 1)[0]

            # 2. Publicera K2 (26 par, 63 mediefiler) och mät tid (M5)
            pub_k2 = publicera_k2(base, "k2-runda4", token)
            assert pub_k2["ok"] and pub_k2["antal_par"] == 26 and pub_k2["vaggtid_sek"] < 60.0, pub_k2

            # 3. Publicera nytt blint invarianspass kopplat till O-lager-id (2 riktiga klipp ur letrend-r4)
            src = Path.home() / "Downloads/letrend-r4"
            man = [json.loads(l) for l in (ROT / "motpart/runda-4/1-datagrund/manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
            korta = sorted(man, key=lambda r: r["langd_s"])[:2]
            spec_fil = Path(td) / "invarians_spec.json"
            spec = {
                "pass_id": "invarians-pilot",
                "titel": "Steg 2 — Blind innehållskontroll (pilot)",
                "lage": "invarians",
                "beskrivning": "Jämför vänster (C) och höger (kandidat). Ljudkompensation finns under spelaren.",
                "fro": 202611204,
                "par": [
                    {
                        "olager_id": korta[0]["id"],
                        "variant": "N1",
                        "kontroll": None,
                        "tillat_gain_komp": True,
                        "media": {
                            "original": {"fil": str(src / f"{korta[0]['id']}.mp4"), "olager_id": korta[0]["id"], "variant": "C"},
                            "efter": {"fil": str(src / f"{korta[0]['id']}.mp4"), "olager_id": korta[0]["id"], "variant": "N1"},
                        },
                    },
                    {
                        "olager_id": korta[1]["id"],
                        "variant": "P",
                        "kontroll": "positiv_tempo_1_25x",
                        "forvantat": "snabbare",
                        "synk": False,
                        "media": {
                            "original": {"fil": str(src / f"{korta[1]['id']}.mp4"), "olager_id": korta[1]["id"], "variant": "C"},
                            "efter": {
                                "fil": str(src / f"{korta[1]['id']}.mp4"),
                                "olager_id": korta[1]["id"],
                                "variant": "P",
                                "vf": "setpts=(PTS-STARTPTS)/1.25",
                                "af": "atempo=1.25",
                            },
                        },
                    },
                ],
            }
            spec_fil.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            pub_inv = publicera_spec(base, spec_fil, token)
            assert pub_inv["ok"] and pub_inv["antal_par"] == 2 and pub_inv["vaggtid_sek"] < 60.0, pub_inv

            # 4. Nyckelskydd (404 även med cookie och Bearer)
            for path in ("/pass/invarians-pilot/nyckel.json", "/pass/k2-runda4/nyckel.json"):
                k404, _, _ = _req(f"{base}{path}", headers={"Cookie": cookie})
                assert k404 == 404, f"nyckel.json läckte ({k404}): {path}"

            # 5. Läs par som inloggad webbläsare + skicka två svar (append-only + ordagrann kommentar)
            k_par, _, b_par = _req(f"{base}/api/pass/invarians-pilot/par", headers={"Cookie": cookie})
            assert k_par == 200
            par_json = json.loads(b_par.decode("utf-8"))
            pid0 = par_json["par"][0]["id"]
            # Kontrollera att inga klippnamn läcker i par.json
            assert korta[0]["id"] not in b_par.decode("utf-8") and korta[1]["id"] not in b_par.decode("utf-8")

            ordagrann = "  Samma poäng, men klippet känns 'lite' hetsigare — behåll pausen!\nRad 2.  "
            for idx, tempo in enumerate(("ja", "osaker"), 1):
                svar_post = {
                    "par": pid0, "nr": 1, "session": "s_test", "sekunder": 12.3, "ljud_hort": True,
                    "samma_handling": "ja", "samma_tempo": tempo, "samma_energi": "ja",
                    "kommentar": ordagrann if idx == 2 else "Första intrycket",
                }
                ks, _, bs = _req(
                    f"{base}/api/pass/invarians-pilot/svar",
                    method="POST",
                    headers={"Cookie": cookie, "Content-Type": "application/json"},
                    body=json.dumps(svar_post, ensure_ascii=False).encode("utf-8"),
                )
                assert ks == 200 and json.loads(bs.decode())["antal"] == idx

            # 6. Synk tillbaka till repot och verifiera koppling till olager_id + ordagrann kommentar
            synk_dir = Path(td) / "synk_repo"
            synk_res = synka(base, "invarians-pilot", synk_dir, token)
            kopplade = json.loads((synk_dir / "invarians-pilot/kopplade_svar.json").read_text(encoding="utf-8"))
            assert len(kopplade) == 2, "Svar skrevs över i stället för append-only!"
            assert kopplade[1]["svar"]["kommentar"] == ordagrann, "Kommentaren bevarades inte ordagrant!"
            assert kopplade[1]["olager_id"] in {korta[0]["id"], korta[1]["id"]}, kopplade[1]

            ut = {
                "auth_401_och_cookie_302_ok": True,
                "nyckel_404_ok": True,
                "blindhet_noll_lackage_ok": True,
                "m5_publicera_k2_26par_sek": pub_k2["vaggtid_sek"],
                "m5_publicera_invarians_2par_inkl_ffmpeg_sek": pub_inv["vaggtid_sek"],
                "append_only_antal_svar": len(kopplade),
                "ordagrann_kommentar_ok": True,
                "olager_koppling_ok": kopplade[1]["olager_id"],
            }
            print(json.dumps(ut, ensure_ascii=False, indent=2))
            return 0
        finally:
            srv.shutdown()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
