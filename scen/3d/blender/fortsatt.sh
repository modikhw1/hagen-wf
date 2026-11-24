#!/usr/bin/env bash
# Återuppta Codex-uppdrag A (opt) och B (ps2) om de stannat utan slutrapport. Väntar till efter 15:57.
cd "C:/Users/praiseworthy/Desktop/hagen-wf"
declare -A ID=( [opt]=01a1c0b9-1df2-7b00-a806-7f6558469c4d [ps2]=01a1c0b9-7c85-7c32-bae4-f5ab9bb2fbd1 )
declare -A UPP=( [opt]=CODEX-OPTIMERA.md [ps2]=CODEX-PS2-MALLAR.md )
while [ "$(date +%H%M)" -lt 1558 ]; do sleep 30; done
lever() { powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'codex.exe' -and \$_.CommandLine -match 'exec' -and \$_.CommandLine -match '$1' }).Count"; }
for d in opt ps2; do
  D=scen/3d/blender/$d
  if grep -q "\"type\":\"turn.completed\"" $D/codex.jsonl $D/codex-fortsatt.jsonl 2>/dev/null; then echo "$d: klar, ingen fortsättning"; continue; fi
  # kör processen fortfarande (och inte slut på kvot)? exec-raden innehåller uppdragsfilen
  if [ "$(lever ${UPP[$d]} | tr -d '\r')" != "0" ]; then echo "$d: lever fortfarande"; continue; fi
  echo "$d: återupptar session ${ID[$d]} $(date +%H:%M)"
  codex exec resume ${ID[$d]} --skip-git-repo-check -c model_reasoning_effort='"xhigh"' -c sandbox_mode='"workspace-write"' -c sandbox_workspace_write.network_access=true --enable image_generation \
    --json "Continue the task in scen/3d/blender/${UPP[$d]} from where you stopped (usage limit interrupted you). Do not redo finished steps; check the files on disk. Finish, verify the acceptance criteria and end with the concise report." \
    > $D/codex-fortsatt.jsonl 2> $D/codex-fortsatt.err &
done
wait
for d in opt ps2; do D=scen/3d/blender/$d; [ -s $D/codex-fortsatt.jsonl ] && grep -o '"type":"agent_message"[^}]*' $D/codex-fortsatt.jsonl | tail -1 | cut -c1-2000 > $D/codex-svar.md; done
echo "fortsatt.sh klar $(date +%H:%M)"
