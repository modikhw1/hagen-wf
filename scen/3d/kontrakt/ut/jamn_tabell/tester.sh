#!/bin/bash
cd /c/Users/praiseworthy/Desktop/hagen-wf; export PYTHONIOENCODING=utf-8; P=$PWD/scen/.venv/Scripts/python.exe
echo "== kontrollera $(date +%T)"; $P scen/3d/kontrakt/kontrollera.py 2>&1 | grep -v -i warn | tail -5; echo "exit ${PIPESTATUS[0]}"
cd scen/3d/kontrakt
echo "== unittest $(date +%T)"; $P -m unittest test_flode test_rumsmall test_regler test_text_disk test_kroppmatt 2>&1 | grep -v -i warn | tail -40
echo "== semantik $(date +%T)"; $P semantik/test_semantik.py 2>&1 | grep -v -i warn | tail -6
echo "== bro $(date +%T)"; $P -m unittest bro.test_bro 2>&1 | grep -v -i warn | tail -6
cd ../ingest; echo "== test_rum $(date +%T)"; $P test_rum.py 2>&1 | grep -v -i warn | tail -6
echo TESTER_KLARA $(date +%T)
