#!/usr/bin/env bash
# Startar Codex-uppdrag D när kvoten är tillbaka (20:58).
cd "C:/Users/praiseworthy/Desktop/hagen-wf"
while [ "$(date +%H%M)" -lt 2059 ]; do sleep 60; done
codex exec -m gpt-6-astra -c model_reasoning_effort='"xhigh"' -s workspace-write -c sandbox_workspace_write.network_access=true --skip-git-repo-check -C "C:\Users\praiseworthy\Desktop\hagen-wf" -o scen/3d/klipp2/codex-d-svar.md --json "Read scen/3d/klipp2/CODEX-D.md carefully and do exactly that task. Verify against its acceptance criteria and end with the concise report." > scen/3d/klipp2/codex-d.jsonl 2> scen/3d/klipp2/codex-d.err
echo "codex D klar $(date +%H:%M) exit $?"
