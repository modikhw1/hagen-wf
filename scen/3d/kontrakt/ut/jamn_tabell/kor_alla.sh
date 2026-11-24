#!/bin/bash
cd /c/Users/praiseworthy/Desktop/hagen-wf; export PYTHONIOENCODING=utf-8
P=scen/.venv/Scripts/python.exe; I=scen/3d/ingest/ut
for d in notan-tagningar b-tilltal-ravara-tagningar kand-kennysgelato-tagningar a-sketch-servering-tagningar; do
  echo "== $d"; $P scen/3d/ingest/kor_jamn.py $I/$d 2>&1 | grep -v -i warn
done
for c in b kenny a; do $P scen/3d/ingest/kor_jamn.py --vertikaler $c 2>&1 | grep -v -i warn | tail -3; done
echo ALLT_KLART
