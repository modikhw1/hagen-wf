#!/bin/bash
cd /c/Users/praiseworthy/Desktop/hagen-wf; export PYTHONIOENCODING=utf-8
P=scen/.venv/Scripts/python.exe; I=scen/3d/ingest/ut; K=scen/3d/kontrakt/kor_klipp.py; V=scen/klipp
for spec in "b b-tilltal-ravara-tagningar b-tilltal-ravara.mp4 tom3" "kenny kand-kennysgelato-tagningar kand-kennysgelato2.0-7596403003901381910.mp4 tom3" "a a-sketch-servering-tagningar a-sketch-servering.mp4 tom3" "notan notan-tagningar d-dialog-notan.mp4 jamn_tom"; do
  set -- $spec; echo "== $1 $(date +%T)"
  $P $K $1 $I/$2 $V/$3 --kalla kalla_jamn.json --undermapp $4 --tillat-flaggad 2>&1 | grep -v -i warn | tail -8
done
echo RENDER_KLART $(date +%T)
