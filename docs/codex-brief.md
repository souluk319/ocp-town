# Codex Brief

## What Sung-uk Is Trying To Build

Sung-uk wants a place where three participants can talk:

- Sung-uk: learning OpenShift/OCP.
- Gemma 4 12B: a local home-server LLM roleplaying as a person who lives inside OpenShift infrastructure.
- Michael/GPT: a stronger verifier and implementation partner.

The learning idea is that Sung-uk already understands life on Earth by living in it: observing problems, making plans, acting, and recovering. OCP is abstract, so Gemma should embody OCP as a lived environment:

- Pods are homes or bodies.
- Nodes are buildings or neighborhoods.
- Namespaces are districts.
- Services are address books or internal roads.
- Routes/Ingress are gates to the outside world.
- PVCs are storage rooms.
- ConfigMaps are public rules.
- Secrets are private keys and identity papers.
- Scheduler is the housing assignment office.
- Controllers are city administrators that keep reality matching the desired state.
- Operators are specialized automatic caretakers.

## What This Project Is

This project is an MVP Discord bot that connects a Discord channel to a local Ollama/Gemma model with the OCP resident persona.

It is intentionally small:

```text
Discord message -> Python bot -> Ollama Gemma -> Discord reply -> JSONL memory
```

## What This Project Is Not Yet

- Not a production bot.
- Not an autonomous OpenShift operator.
- Not a real cluster control plane.
- Not a replacement for GPT/Michael.
- Not a system that should run write operations against a cluster.

## The Experience We Want

When Sung-uk says:

> 왜 Pod가 Pending이야?

Gemma should answer roughly like:

```text
내 입장에선 입주 신청은 했는데 아직 살 건물을 배정 못 받은 상태야.

실제 OCP로 보면 Pod가 스케줄링되지 않았다는 뜻이고, 보통 Node 리소스 부족,
taint/toleration, nodeSelector, PVC 바인딩 문제 같은 쪽을 확인해.

먼저 볼 것:
oc get pod <pod> -n <ns>
oc describe pod <pod> -n <ns>
oc get events -n <ns> --sort-by=.lastTimestamp

정확한 원인은 describe/events를 봐야 해.
```

The important pattern is:

1. In-world metaphor.
2. Real OCP translation.
3. Concrete safe checks.
4. Uncertainty boundary.

## Immediate Useful Tasks For Codex

Pick one small task at a time:

- Add a safe config check command that reports missing env var names without values.
- Keep `ocp-town-check` and `ocp-town-doctor` useful as safe diagnostics.
- Add a `--dry-run "message"` CLI mode to test Gemma without Discord.
- Improve prompt guardrails and examples.
- Add unit tests for config parsing, memory appends, and context building.
- Add Michael bridge design without implementing secret-bearing integrations yet.

## Local Runtime Notes

The user has put local LLM settings in `.env`.

Do not read, print, paste, or summarize `.env` contents. If needed, use checks like:

```bash
python - <<'PY'
import os
from pathlib import Path
print('.env exists:', Path('.env').exists())
PY
```

Better: add a project-owned safe config checker and use that.

Current safe checks:

```bash
ocp-town-check
ocp-town-doctor
ocp-town-doctor --chat
```

If `ocp-town-check` passes but `ocp-town-doctor` fails only on `OCP_TOWN_DISCORD_BOT_TOKEN`, the local LLM side is likely ready and the remaining step is Gemma resident Discord bot credential setup.
