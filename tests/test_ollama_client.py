from __future__ import annotations

import unittest

from ocp_town.ollama_client import extract_chat_content


class ExtractChatContentTest(unittest.TestCase):
    def test_extracts_common_gateway_shapes(self) -> None:
        self.assertEqual(extract_chat_content({"response": "주민 온라인"}), "주민 온라인")
        self.assertEqual(extract_chat_content({"message": {"content": "주민 온라인"}}), "주민 온라인")
        self.assertEqual(
            extract_chat_content({"choices": [{"message": {"content": "주민 온라인"}}]}),
            "주민 온라인",
        )
        self.assertEqual(extract_chat_content({"data": {"text": "주민 온라인"}}), "주민 온라인")

    def test_returns_empty_for_unknown_shape(self) -> None:
        self.assertEqual(extract_chat_content({"ok": True}), "")


if __name__ == "__main__":
    unittest.main()
