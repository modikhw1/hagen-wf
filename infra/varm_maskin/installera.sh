#!/usr/bin/env bash
# Engångsinstallation av varm Linux-maskin (RunPod Pod + Network Volume / Hetzner AX102 / Vast.ai).
# Säkerhet (§6): synka aldrig lokala nyckelfiler (blender_token.txt, fal_ai.txt). Använd miljövariabler.
set -euo pipefail

DATA_ROT="${HAGEN_DATA_ROT:-/workspace/hagen}"
APP_ROT="${HAGEN_APP_ROT:-/workspace/hagen-app}"
mkdir -p "$DATA_ROT/kallor" "$DATA_ROT/olager" "$APP_ROT"

# 1. Statisk FFmpeg 8.1 (matchar lokal version)
if ! command -v ffmpeg >/dev/null 2>&1 || ! ffmpeg -version | head -n1 | grep -q "8\.1"; then
  URL81="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz"
  URLM="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
  (curl -fsSL "$URL81" -o /tmp/ff.tar.xz || curl -fsSL "$URLM" -o /tmp/ff.tar.xz)
  mkdir -p /tmp/ff && tar -xJf /tmp/ff.tar.xz -C /tmp/ff --strip-components=1
  install -m 755 /tmp/ff/bin/ffmpeg /usr/local/bin/ffmpeg
  install -m 755 /tmp/ff/bin/ffprobe /usr/local/bin/ffprobe
  rm -rf /tmp/ff /tmp/ff.tar.xz
fi

# 2. Python-miljö (förladdad på beständig volym -> start < 2 min vid återstart)
if [ ! -d "$DATA_ROT/.venv" ]; then
  python3 -m venv "$DATA_ROT/.venv"
fi
"$DATA_ROT/.venv/bin/pip" install --upgrade pip
"$DATA_ROT/.venv/bin/pip" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
"$DATA_ROT/.venv/bin/pip" install "numpy<2.3" scipy onnxruntime silero-vad ultralytics opencv-python-headless pillow "yt-dlp[default,curl-cffi]==2026.10.26"
"$DATA_ROT/.venv/bin/python" -c "from silero_vad import load_silero_vad; load_silero_vad(onnx=True); print('Silero ONNX redo')"

echo "Klar. Starta med:"
echo "  HAGEN_WORKER_TOKEN=\$(openssl rand -hex 24) HAGEN_DATA_ROT=$DATA_ROT $DATA_ROT/.venv/bin/python -m infra.varm_maskin.worker_server --host 127.0.0.1 --port 8765"
echo "Nå säkert lokalt via SSH-tunnel: ssh -L 8765:127.0.0.1:8765 user@<maskin>"
