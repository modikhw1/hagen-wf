set -e
for n in tom redigerad; do
  mkdir -p scen/3d/kontrakt/ut/notan/plats_$n
  s=$(date +%s.%N)
  /c/Users/praiseworthy/Desktop/hagen-wf/scen/.venv/Scripts/python.exe scen/3d/kontrakt/bygg_ljud.py scen/3d/kontrakt/ut/notan/plan_plats_$n.json scen/3d/kontrakt/ut/notan/plats_$n/ljud.wav scen/3d/kontrakt/ut/notan/plats_$n/ljud_rapport.json > scen/3d/kontrakt/ut/notan/plats_$n/ljud.log 2>&1
  m=$(date +%s.%N)
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python-exit-code 1 --python scen/3d/ingest/mhr_rig.py -- scen/3d/ingest/ut/notan-tagningar/S1 scen/klipp/d-dialog-notan.mp4 --plan scen/3d/kontrakt/ut/notan/plan_plats_$n.json --ut scen/3d/kontrakt/ut/notan/plats_$n --ljud scen/3d/kontrakt/ut/notan/plats_$n/ljud.wav --render > scen/3d/kontrakt/ut/notan/plats_$n/bygg.log 2>&1
  e=$(date +%s.%N)
  echo "$n ljud $(echo "$m - $s" | bc) s, blender $(echo "$e - $m" | bc) s" >> scen/3d/kontrakt/ut/notan/plats_tid.txt
done
