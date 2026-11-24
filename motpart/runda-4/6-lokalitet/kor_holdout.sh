#!/usr/bin/env bash
# Hold-out: hela kedjan på klipp som aldrig ingått i kalibreringen (grind 1b, väljare, L8). Ingen regel ändras här.
# usage: bash kor_holdout.sh "namn:nyckel,namn:nyckel,..."
set -u
cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe; SPY=../../../scen/.venv/Scripts/python.exe; MODAL=../../../scen/.venv/Scripts/modal.exe
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
SPEC="$1"; t0=$(date +%s)
steg() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
steg "observation (Modal)"; $MODAL run modal_obs.py::main --klipp "$SPEC" 2>&1 | grep -E "klar|totalt|Error|Traceback"
for s in ${SPEC//,/ }; do n=${s%%:*}; k=${s##*:}; [ -f "ut/$k/pose2d.json" ] && continue; steg "pose2d $k"; $SPY -I -X utf8 -W ignore pose2d.py "$n" --nyckel "$k" 2>&1 | tail -1; done
for s in ${SPEC//,/ }; do k=${s##*:}; [ -f "ut/$k/obs_gpu.json" ] || { steg "STOPP: obs_gpu saknas för $k"; exit 1; }; done
steg "kroppar (Modal)"; $MODAL run modal_kropp2.py::main --klipp "$SPEC" 2>&1 | grep -E "klar|totalt|Error|Traceback"
for s in ${SPEC//,/ }; do k=${s##*:}
  steg "lokalitet $k"; $PY -I -X utf8 -W ignore lokalitet.py "$k" --obs gpu 2>&1 | grep -E "Traceback|Error"
  steg "rumshjärna $k"; $PY -I -X utf8 -W ignore rumshjarna/hjarna.py "$k" --parallell 4 2>&1 | grep -E "^plan|MISSLYCK|tid_s|Error|Traceback"
  steg "lokalitet med hypotes $k"; $PY -I -X utf8 -W ignore lokalitet.py "$k" --obs gpu 2>&1 | grep -E "Traceback|Error"
  steg "väljare $k"; $PY -I -X utf8 -W ignore rumshjarna/valjare.py "$k" 2>&1 | tail -1
  F=$($PY -I -c "import json;p=json.load(open('ut/rumshjarna/$k/plan.json',encoding='utf-8'));print(' '.join(str(t['ruta']) for s,t in sorted(p['tagningar'].items(),key=lambda x:int(x[0][1:]))))")
  steg "bilder $k"; node fanga_orbit.cjs "$k" $F 2>&1 | tail -1
done
steg "SLUT"
