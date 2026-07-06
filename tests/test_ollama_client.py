from __future__ import annotations

import unittest

from ocp_town.ollama_client import extract_chat_content, openai_chat_urls


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

    def test_openai_chat_urls_falls_back_to_origin_when_base_has_path(self) -> None:
        self.assertEqual(
            openai_chat_urls("http://gateway.example/api"),
            [
                "http://gateway.example/api/v1/chat/completions",
                "http://gateway.example/v1/chat/completions",
            ],
        )


if __name__ == "__main__":
    unittest.main()
