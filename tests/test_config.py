from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ocp_town.config import load_settings


class LoadSettingsTest(unittest.TestCase):
    def test_reads_kugnus_gateway_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / ".env").write_text(
                "\n".join(
                    [
                        "OCP_TOWN_DISCORD_BOT_TOKEN=fake-token",
                        "OCP_TOWN_LLM_BACKEND=openai",
                        "KUGNUS_GATEWAY_BASE_URL=http://gateway.example/api",
                        "KUGNUS_GATEWAY_API_KEY=fake-key",
                        "KUGNUS_CHAT_MODEL=gemma4:12b-it-qat",
                    ]
                ),
                encoding="utf-8",
            )

            settings = load_settings(root)

        self.assertEqual(settings.llm_backend, "openai")
        self.assertEqual(settings.home_server_base_url, "http://gateway.example/api")
        self.assertEqual(settings.home_server_api_key, "fake-key")
        self.assertEqual(settings.ollama_model, "gemma4:12b-it-qat")


if __name__ == "__main__":
    unittest.main()
