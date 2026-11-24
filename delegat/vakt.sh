#!/usr/bin/env bash
# Vakt: skriver en rad per nytt uppdrag (status: redo, saknar svar/ med samma filnamn).
# Tyst annars, så ingen tokenförbrukning i viloläge. Körs via Monitor i Claude-appen.
dir="$(cd "$(dirname "$0")" && pwd)"
declare -A seen
while true; do
  for f in "$dir"/uppdrag/*.md; do
    [ -e "$f" ] || continue
    n="$(basename "$f")"
    [ -n "${seen[$n]}" ] && continue
    if [ -e "$dir/svar/$n" ]; then seen[$n]=1; continue; fi
    if grep -qE '^status:[[:space:]]*redo([[:space:]]|#|$)' "$f"; then
      seen[$n]=1
      echo "NYTT UPPDRAG redo: delegat/uppdrag/$n"
    fi
  done
  sleep 30
done
