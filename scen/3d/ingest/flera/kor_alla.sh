#!/bin/bash
# kör de fyra klippen i ordning (ingest_flera är återupptagbart)
cd "$(dirname "$0")/../../../.."
export PYTHONIOENCODING=utf-8
PY=scen/.venv/Scripts/python.exe
for c in b-tilltal-ravara kand-kennysgelato2.0-7596403003901381910 a-sketch-servering c-sketch-tre; do
  u=scen/3d/ingest/ut/${c%%-7596*}-tagningar
  case $c in kand-kenny*) u=scen/3d/ingest/ut/kand-kennysgelato-tagningar;; esac
  $PY scen/3d/ingest/flera/ingest_flera.py scen/klipp/$c.mp4 $u
done
echo ALLA_KLARA
