# Architecture

OCP Town starts as a Gemma resident bot, then adds OpenClaw as a separate Discord verifier bot.

## Components

- Gemma Discord bot: receives user messages and posts resident replies.
- OpenClaw Discord bot: handles Michael-style verification, tool use, and longer work.
- Ollama client: calls a local Gemma 12B model through `/api/chat`.
- Resident prompt: keeps Gemma inside the OCP resident learning frame.
- JSONL memory: stores short interaction history for continuity.

## Message Path

```text
Sung-uk in Discord
  -> OCP Town Gemma bot
  -> discord.py on_message
  -> JsonlMemory append user turn
  -> Ollama /api/chat with resident prompt
  -> JsonlMemory append assistant turn
  -> Discord reply

Sung-uk / Gemma asks for verification
  -> OpenClaw Michael bot
  -> OpenClaw Gateway
  -> local Ollama Gemma or stronger configured model
  -> Discord reply in review channel
```

## Next Steps

- Add `@Michael` routing through OpenClaw or an existing Discord operator bot.
- Add slash commands: `/mood`, `/ocp-map`, `/summarize`.
- Add cluster-read-only probes for labs: `oc get pods`, `oc get events`, `oc describe`.
- Add a trust mode that separates metaphor, facts, and commands more strictly.
