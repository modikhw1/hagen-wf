# `infra/` — Snabb iteration för hagen-wf (INFRA.md)

Infrastruktur byggd mot specifikationen i [`motpart/runda-4/INFRA.md`](../motpart/runda-4/INFRA.md) och orsaksdiagnosen i [`motpart/runda-4/DIAGNOS_VANTETID.md`](../motpart/runda-4/DIAGNOS_VANTETID.md).

## Delar

| Modul | Ansvar | Krav |
|---|---|---|
| [`infra/kor.py`](kor.py) | Jobbkörare med provlopp (1–2 enheter), ETA-grind (>5 min), platsval, tak (1,5× ETA / disk / kostnad), atomärt hjärtslag (`FRAMSTEG.json`), mänsklig grind först och återupptagbarhet | §3, M4 |
| [`infra/rang.py`](rang.py) | Enda implementationen för medelrang (`medelrang_z`) och fryst kontoviktad ECDF (`FrystECDFTransform`) med inbyggt 100-permutationstest (`<= 1e-12`) | §1 (rangfelet) |
| [`infra/extraktorer.py`](extraktorer.py) | Varma in-process extraktorer (Silero VAD ONNX + YOLOv8n laddade en gång i minnet + E28 i ett enda ffmpeg-pass inkl. bilaga), värdeidentiska med repots oförändrade skript | §1, M6 |
| [`infra/olager.py`](olager.py) | Versionerat O-lager per `<konto>-<videoid>`: `meta.json`, sammanhängande JPEG-lager `rutor_540p_5fps.jpack` + `rutor_index.json`, `ljud_16k_mono.wav`, `ljud_orig.*`, `e28/e30/e37.json`, valfritt `c_ref.json` och isolerad `lager/`-mapp | §1, M1, M3 |
| [`infra/steg2_snabb.py`](steg2_snabb.py) | Steg 2 (`FORREGISTRERING.md` A) med varianter byggda i RAM (`/dev/shm`), varma extraktorer och `FrystECDFTransform` | M2 |
| [`infra/modal_tjanst.py`](modal_tjanst.py) & [`infra/modal_klient.py`](modal_klient.py) | Driftsatt varm Modal-app (`hagen-infra`) med beständig volym `hagen-olager` (0 uppladdning per körning, 15 min varm fönstertid, $0 i vila) | §2, M1–M3, M6 |
| [`infra/varm_maskin/`](varm_maskin/worker_server.py) | Färdig varm HTTP-jobbtjänst + installationsskript för dedikerad Linux-maskin via SSH (RunPod / Hetzner / Vast.ai) | §2 |
| [`infra/panel/`](panel/tjanst.py) | Stående, autentiserad ägarpanel (lokalt och alltid-uppe på Modal `hagen-panel`) med publicerings-API, blindning, nyckelskydd (`404`), append-only svar, ordagranna kommentarer och reposynk | §4, §6, M5 |

## Snabbkommandon

```powershell
# 1. Kontrollera maskinens gränser (disk, RAM, CPU, Modal)
.\scen\.venv\Scripts\python.exe infra\kor.py --info

# 2. Mät varm Modal-tjänst (M6), O-lager (M1), URL-ingest (M3) och steg 2 (M2)
.\scen\.venv\Scripts\python.exe infra\modal_klient.py m6
.\scen\.venv\Scripts\python.exe infra\modal_klient.py m1
.\scen\.venv\Scripts\python.exe infra\modal_klient.py m3-url
.\scen\.venv\Scripts\python.exe infra\modal_klient.py m2-olager
.\scen\.venv\Scripts\python.exe infra\modal_klient.py m2-omrakning

# 3. Publicera nytt bedömningspass till den stående panelen (< 1 min, M5) och synka svar
$env:PANEL_TOKEN = Get-Content "$env:USERPROFILE\.hagen-panel-token"
.\scen\.venv\Scripts\python.exe infra\panel\publicera.py --url <PANEL_URL> --importera-k2 --pass-id k2-runda4
.\scen\.venv\Scripts\python.exe infra\panel\synka_svar.py k2-runda4 --url <PANEL_URL>
```

## Säkerhet (§6)
- Nyckelfiler i repots rot (`blender_token.txt`, `fal_ai.txt`, `.env*`) inkluderas aldrig i containeravbilder eller synkas till externa maskiner.
- Panelen och worker-API:et kräver autentiseringstoken när de exponeras utanför `127.0.0.1`. `nyckel.json` returnerar alltid `404` publikt.
- Inga ägaruppgifter (namn, e-post) skickas i URL:er, huvuden eller loggar.
