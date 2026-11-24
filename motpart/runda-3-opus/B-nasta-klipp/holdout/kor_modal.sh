#!/usr/bin/env bash
# Hold-out: kropp (SAM 3D Body) och rum (MoGe-2) på Modal via ingestens egna kommando (RAPPORT.md §3.3), ett klipp i taget.
# Klippen körs i följd eftersom flera/budget.json läses en gång per process och skrivs över (parallella klipp tappar poster);
# inom en tagning går kroppsjobben parallellt på Modal (satser om 40, L4 först i reservlistan).
# Kostnadsvakt: före varje klipp läses dagens Modal-kostnad (holdout/kostnad.py); över 9 USD stoppas körningen
# (hårt tak 15 USD; sämsta fall för pitaspot på A100 är cirka 5 USD). Varje klipp har 45 min som längsta tid.
# Körs från repots rot (Git Bash).
set -u
export PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0 HAGEN_NO_GEMINI=1
PY=scen/.venv/Scripts/python.exe
B=motpart/runda-3-opus/B-nasta-klipp/holdout
mkdir -p $B/logg
for id in sabai.soong-7474616203366108439 faros_shipandterrace-7540756212032326934 faros_shipandterrace-7511394441094008086 thepitaspot-7680489103195917590; do
  echo "== $id $(date +%T)"
  $PY $B/kostnad.py --tak 9 | tee -a $B/logg/kostnad.jsonl
  if [ ${PIPESTATUS[0]} -eq 3 ]; then echo "STOPP: kostnad i dag över 9 USD före $id"; exit 3; fi
  timeout 2700 $PY scen/3d/ingest/flera/ingest_flera.py data/format/kontroll/klipp/$id.mp4 scen/3d/ingest/ut/$id-tagningar \
      --till rum --total 6300 --uppdrag holdout-runda3-B-2026-11-20 --uppdragstak 2800 > $B/logg/modal_$id.txt 2>&1
  echo "slut $id exit $? $(date +%T)"
  grep -E "klar|fel|vakt|stopp" $B/logg/modal_$id.txt | tail -20
done
$PY $B/kostnad.py --tak 15 | tee -a $B/logg/kostnad.jsonl
echo "ALLT KLART $(date +%T)"
