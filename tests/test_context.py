from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ocp_town.context import build_recent_context
from ocp_town.memory import JsonlMemory


class BuildRecentContextTest(unittest.TestCase):
    def test_hides_internal_labels_and_scopes_to_telegram_chat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory = JsonlMemory(Path(tmp) / "memory.jsonl")
            memory.append(
                {
                    "role": "user",
                    "platform": "telegram",
                    "author": "KUGNUS",
                    "chat_id": 1,
                    "content": "답변 속도가 느려?",
                }
            )
            memory.append(
                {
                    "role": "user",
                    "platform": "discord",
                    "author": "someone",
                    "channel_id": 99,
                    "content": "Pod가 Pending이면 뭐야?",
                }
            )

            context = build_recent_context(memory, platform="telegram", chat_id=1)

        self.assertIn("사용자: 답변 속도가 느려?", context)
        self.assertNotIn("KUGNUS", context)
        self.assertNotIn("telegram/KUGNUS", context)
        self.assertNotIn("Pod가 Pending", context)

    def test_limits_to_recent_scoped_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory = JsonlMemory(Path(tmp) / "memory.jsonl")
            for idx in range(6):
                memory.append(
                    {
                        "role": "user",
                        "platform": "telegram",
                        "chat_id": 1,
                        "content": f"turn-{idx}",
                    }
                )

            context = build_recent_context(memory, platform="telegram", chat_id=1, limit=2)

        self.assertNotIn("turn-3", context)
        self.assertIn("turn-4", context)
        self.assertIn("turn-5", context)


if __name__ == "__main__":
    unittest.main()
