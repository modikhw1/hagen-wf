#!/usr/bin/env bash
# Fas 3: de sju semantiska ändringarna som operationer (Claude översatte meningarna). Spelas upp från basen:
#   bash scen/3d/demo-andringar.sh
set -e
cd "$(dirname "$0")/../.."
export PYTHONUTF8=1
P="scen/.venv/Scripts/python.exe -B scen/3d/op.py"
cp scen/3d/scen3d.bas.json scen/3d/scen3d.json; rm -rf scen/3d/historik

# 1 "Byt hamburgaren mot pizza på A:s bord." (lådan är eget föremål och står kvar)
$P byt A:burger --typ pizza_slice
# 2 "Långsam inzoomning på hennes ansikte i punchlinen."
$P dolly S6 --mot A:huvud --faktor 0.55
# 3 "Servitören vänder sig mot henne, och tagningen kortas till 1,6 s."
$P vand S4 C --mot A
$P langd S4 --s 1.6
# 4 "I kroken: bort med burken, flytta muggen närmare henne."
$P dolj A:can --tagning S1
$P flytta A:cup --mot A --m 0.12 --tagning S1
# 5 "Ny sista tagning där kameran kretsar 90 grader runt hans bord." (går bara i riktig 3D)
$P duplicera S7 --som S8
$P orbit S8 --runt B --grader 90 --radie 1.7
$P langd S8 --s 3.0 --lage stretch
# 6 "Servitören står bakom henne i punchlinen, på rätt djup och i rätt skala."
$P lagg-till-aktor S6 C --bakom A --avstand 0.85 --sida 0.3 --vand-mot A --fran-tagning S4
# 7 "Hon ska kännas mer stressad." (mer gestik, stressat humör, kortare tagningar)
for S in S1 S3 S6; do $P intensitet $S A --varde 1.5; $P humor $S A --namn stressed --mangd 0.8; done
$P langd S1 --s 1.9
$P langd S3 --s 1.5
