#!/usr/bin/env bash
# Kör en fas av Scen3D i Codex. Användning: bash scen/3d/kor-fas.sh <fas-nummer> [ny|fortsatt] [codex-hem]
FAS=$1; LAGE=${2:-ny}; HEM=${3:-$HOME/.codex}
cd "C:/Users/praiseworthy/Desktop/hagen-wf"
UPPDRAG="Read scen/3d/CODEX-PROMPT.md carefully (the full plan and all context). Then do ONLY Phase $FAS as specified there, verify it against its acceptance criteria, append your decisions and numbers to scen/3d/LOGG.md, and end with a concise report: what you built, the measured numbers per shot, which alternatives you compared and why you chose as you did, what fails or is uncertain, and file paths to the verification images."
if [ "$LAGE" = fortsatt ]; then
  # resume ärver inte sandlådan: skrivrätt och nätverk måste anges igen. SESSION=<id> väljer session, annars den senaste.
  CODEX_HOME="$HEM" codex exec resume ${SESSION:---last} --skip-git-repo-check -c model_reasoning_effort='"xhigh"' -c sandbox_mode='"workspace-write"' -c sandbox_workspace_write.network_access=true --json "$UPPDRAG" > scen/3d/codex-fas$FAS.jsonl 2> scen/3d/codex-fas$FAS.err
else
  CODEX_HOME="$HEM" codex exec -m gpt-6-astra -c model_reasoning_effort='"xhigh"' -s workspace-write -c sandbox_workspace_write.network_access=true --skip-git-repo-check -C "C:\Users\praiseworthy\Desktop\hagen-wf" -o scen/3d/codex-fas$FAS-svar.md --json "$UPPDRAG" > scen/3d/codex-fas$FAS.jsonl 2> scen/3d/codex-fas$FAS.err
fi
echo "KLAR fas $FAS (exit $?)" >> scen/3d/codex-status.txt
