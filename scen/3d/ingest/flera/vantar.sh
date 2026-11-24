#!/bin/bash
# vantar.sh <klippnamnsdel> <S-id> : väntar (max 160 s) på att tagningen rapporteras i kor_alla.log
L=scen/3d/ingest/flera/kor_alla.log
timeout 160 bash -c "until sed -n '/$1/,\$p' $L | grep -q '^$2 '; do sleep 10; done"
sed -n "/$1/,\$p" $L | grep -E '^S[0-9]+ ' | cut -c1-200
