"""Stående, alltid-uppe ägarpanel på Modal med autentisering och beständig volym (INFRA.md §4, §6, M5).

Deploy (efter att Modal-hemligheten `hagen-panel-auth` med PANEL_TOKEN skapats):
    .\\scen\\.venv\\Scripts\\modal.exe deploy infra/panel/modal_panel.py

Egenskaper:
  - Alltid uppe på en fast HTTPS-URL (skalar till $0 i vila, vaknar på ~1 s; ingen öppen oautentiserad åtkomst).
  - Beständig volym `hagen-panel` under `/panel_data`: svar skrivs atomärt och committas direkt.
  - Exakt samma router, blindhet, nyckelskydd (404) och publicerings-API som lokal infra/panel/tjanst.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import modal

_P = Path(__file__).resolve()
ROT = _P.parents[2] if len(_P.parents) > 2 else _P.parent
IS_LOCAL = (ROT / "infra" / "panel" / "tjanst.py").exists()

app = modal.App("hagen-panel")
vol_panel = modal.Volume.from_name("hagen-panel", create_if_missing=True)

img = modal.Image.debian_slim(python_version="3.12").env({"PYTHONPATH": "/app", "PYTHONUNBUFFERED": "1"})
if IS_LOCAL:
    img = (
        img.add_local_file(str(ROT / "infra" / "__init__.py"), "/app/infra/__init__.py")
        .add_local_file(str(ROT / "infra" / "panel" / "tjanst.py"), "/app/infra/panel/tjanst.py")
        .add_local_file(str(ROT / "infra" / "panel" / "index.html"), "/app/infra/panel/index.html")
    )


@app.function(
    image=img,
    cpu=0.5,
    memory=512,
    max_containers=1,
    scaledown_window=300,
    volumes={"/panel_data": vol_panel},
    secrets=[modal.Secret.from_name("hagen-panel-auth")],
)
@modal.concurrent(max_inputs=32)
@modal.asgi_app()
def panel_webb():
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from infra.panel.tjanst import PanelLagring, skapa_asgi_app

    token = os.environ.get("PANEL_TOKEN")
    if not token:
        raise RuntimeError("PANEL_TOKEN saknas i hemligheten hagen-panel-auth (§6).")
    vol_panel.reload()
    lagring = PanelLagring(Path("/panel_data"), on_write=vol_panel.commit)
    return skapa_asgi_app(lagring, token=token)
