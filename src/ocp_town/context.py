from __future__ import annotations

from .memory import JsonlMemory


def build_recent_context(memory: JsonlMemory) -> str:
    turns = memory.recent_turns(limit=8)
    if not turns:
        return ""

    compact: list[str] = ["최근 OCP Town 대화 요약:"]
    for turn in turns:
        role = turn.get("role", "unknown")
        author = turn.get("author", role)
        platform = turn.get("platform")
        content = str(turn.get("content", "")).replace("\n", " ")
        prefix = f"{platform}/{author}" if platform else str(author)
        compact.append(f"- {prefix}: {content[:500]}")
    return "\n".join(compact)
