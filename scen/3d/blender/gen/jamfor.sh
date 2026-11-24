#!/usr/bin/env bash
# Användning: bash jamfor.sh <genererad.mp4> <start_s> <langd_s> <ut.mp4>
# Källa | blockout | genererad, alla i scentid, originalljud under. H.264 Main + AAC stereo (fungerar i Windows).
G=$1; S=$2; L=$3; UT=$4; H=$(cd "$(dirname "$0")/.." && pwd)
ffmpeg -v error -y -ss $S -t $L -i "$H/../../klipp/d-dialog-notan.mp4" -ss $S -t $L -i "$H/ut/blockout.mp4" -t $L -i "$G" -ss $S -t $L -i "$H/ljud-original.wav" \
 -filter_complex "[0:v]scale=432:768,setsar=1,fps=30[a];[1:v]scale=432:768,setsar=1,fps=30[b];[2:v]scale=432:768,setsar=1,fps=30[c];[a][b][c]hstack=3[v]" \
 -map "[v]" -map 3:a -c:v libx264 -profile:v main -pix_fmt yuv420p -crf 20 -c:a aac -ac 2 -ar 48000 -movflags +faststart -shortest "$UT"
