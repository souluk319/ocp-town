# OCP Town Agent Instructions

This project is an MVP for a three-party learning environment:

```text
Sung-uk <-> Gemma 4 12B OCP Resident <-> Michael / GPT verifier
```

The purpose is not to build a generic chatbot. The purpose is to help Sung-uk learn OpenShift/OCP faster by talking with a local LLM that roleplays as a resident living inside an OpenShift cluster.

## Product Intent

Gemma should act like a small local AI pet / resident inside an OpenShift world:

- Explain OpenShift concepts through an in-world lifestyle metaphor.
- Translate the metaphor back into real OCP/Kubernetes concepts.
- Suggest read-only checks or safe verification steps.
- Admit uncertainty and ask for Michael/GPT verification when needed.

Michael/GPT is not replaced by Gemma. Michael is the high-confidence verifier, planner, and debugger. Gemma is the always-available local companion that makes OCP feel embodied and memorable.

## Current Architecture

- Python package under `src/ocp_town`.
- Discord bot receives messages.
- Bot calls a local Ollama endpoint.
- Persona lives in `prompts/ocp-resident.md`.
- Memory is append-only JSONL under `data/memory.jsonl`.
- `.env` contains local runtime settings and must not be printed.

## Primary Near-Term Goal

Make the MVP actually run end to end:

1. Load `.env` without printing secrets.
2. Connect to Discord.
3. Send user messages to the configured local Gemma model through Ollama.
4. Reply in Discord as the OCP resident.
5. Save conversation turns to JSONL memory.

## Important Runtime Assumptions

- The user has already placed home-server/local-LLM settings in `.env`.
- Do not inspect or print `.env` contents.
- If runtime config must be checked, report only whether required variables exist.
- Default model names in docs may be placeholders. The `.env` value is authoritative.
- This repo may not be a git repository.

## Do

- Keep implementation small and boring.
- Prefer read-only health checks before trying to run the bot.
- Add tests around pure functions when changing behavior.
- Keep generated files out of git via `.gitignore`.
- Preserve the OCP resident metaphor while keeping factual guardrails strict.
- Document commands Sung-uk can run locally.

## Do Not

- Do not build a generic multi-agent framework yet.
- Do not add autonomous cluster-changing actions.
- Do not run `oc apply`, `oc delete`, deployment, account, credential, or public-posting actions without explicit approval.
- Do not print tokens, kubeconfigs, Discord tokens, OAuth files, `.env`, or Secret values.
- Do not make Gemma pretend to know facts it cannot verify.

## When Codex Is Asked To Help

First read:

1. `README.md`
2. `docs/codex-brief.md`
3. `prompts/ocp-resident.md`
4. Relevant files under `src/ocp_town`

Then inspect runtime safely:

```bash
python3 --version
test -f .env && echo ".env exists"
python3 -m compileall src
```

If dependencies are installed, optional checks:

```bash
python -c "import discord; print('discord.py ok')"
ocp-town-check
ocp-town-doctor
```

Interpretation:

- `ocp-town-check` passing means the local LLM/prompt side is basically reachable.
- `ocp-town-doctor` may still fail if `OCP_TOWN_DISCORD_BOT_TOKEN` is missing; that means Discord bot setup remains, not that Gemma/Ollama is broken.

Avoid network or bot startup unless Sung-uk asked for an actual run.
