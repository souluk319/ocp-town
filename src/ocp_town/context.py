from __future__ import annotations

from typing import Any

from .memory import JsonlMemory


def same_id(value: Any, expected: int | None) -> bool:
    if expected is None:
        return True
    return str(value) == str(expected)


def build_recent_context(
    memory: JsonlMemory,
    *,
    platform: str | None = None,
    channel_id: int | None = None,
    chat_id: int | None = None,
    limit: int = 4,
) -> str:
    turns = memory.recent_turns(limit=50)
    scoped_turns: list[dict[str, Any]] = []
    for turn in turns:
        turn_platform = turn.get("platform") or "discord"
        if platform and turn_platform != platform:
            continue
        if not same_id(turn.get("channel_id"), channel_id):
            continue
        if not same_id(turn.get("chat_id"), chat_id):
            continue
        scoped_turns.append(turn)

    scoped_turns = scoped_turns[-limit:]
    if not scoped_turns:
        return ""

    compact: list[str] = [
        "최근 같은 대화방 내용이다. 최신 사용자 메시지와 직접 관련 있을 때만 참고한다.",
        "작성자 이름, 플랫폼 이름, 내부 라벨은 호칭으로 쓰지 않는다.",
    ]
    for turn in scoped_turns:
        role = turn.get("role", "unknown")
        speaker = "사용자" if role == "user" else "C"
        content = str(turn.get("content", "")).replace("\n", " ")
        compact.append(f"- {speaker}: {content[:220]}")
    return "\n".join(compact)
