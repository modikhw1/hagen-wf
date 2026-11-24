#!/usr/bin/env bash
# Observationer för alla klipp i provet (CPU). Cachade rutor hoppas över.
cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe
for spec in "duepiani-7650849186912406806 duepiani" "spanjorskansthlm-7474263274415082774 spanjorskan" \
            "08burgerkebab-7677567629392874774 08burgerkebab" "babasburgers-7558890194468932896 babasburgers" \
            "kennysgelato2.0-7587042895828503830 kennysgelato2.0"; do
  set -- $spec
  $PY -I -X utf8 -W ignore observera.py "$1" --nyckel "$2" 2>&1 | grep -v -i warn | tail -1
done
