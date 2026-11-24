#!/bin/bash
# bk.sh <repo-relativ sökväg>... : kopierar filen till scen/3d/kontrakt/ut/fore_jamn/<sökväg> om ingen kopia finns.
cd /c/Users/praiseworthy/Desktop/hagen-wf
for f in "$@"; do
  m="scen/3d/kontrakt/ut/fore_jamn/$f"
  if [ -f "$f" ] && [ ! -e "$m" ]; then mkdir -p "$(dirname "$m")"; cp -p "$f" "$m"; echo "kopierad: $f"; fi
done
