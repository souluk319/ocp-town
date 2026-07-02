from __future__ import annotations

import urllib.error
import urllib.request
import os
from pathlib import Path

from .config import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def check_ollama(host: str) -> tuple[bool, str]:
    request = urllib.request.Request(f"{host}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status == 200:
                return True, "reachable"
            return False, f"unexpected status {response.status}"
    except urllib.error.URLError as exc:
        return False, str(exc)


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    print("ocp-town healthcheck")
    print(f"project_root: {PROJECT_ROOT}")
    print(f".env exists: {(PROJECT_ROOT / '.env').exists()}")

    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat").strip()
    prompt_path = PROJECT_ROOT / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md")
    memory_path = PROJECT_ROOT / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl")
    token_configured = bool(
        os.getenv("OCP_TOWN_DISCORD_BOT_TOKEN", "").strip()
        or os.getenv("DISCORD_BOT_TOKEN", "").strip()
    )
    channel_restricted = bool(
        os.getenv("OCP_TOWN_DISCORD_CHANNEL_ID", "").strip()
        or os.getenv("DISCORD_CHANNEL_ID", "").strip()
    )

    print(f"discord token configured: {token_configured}")
    print(f"discord channel restricted: {channel_restricted}")
    print(f"prompt exists: {prompt_path.exists()}")
    print(f"memory directory exists: {memory_path.parent.exists()}")
    print(f"ollama model configured: {bool(ollama_model)}")

    ok, detail = check_ollama(ollama_host)
    print(f"ollama: {'ok' if ok else 'fail'} ({detail})")
    return 0 if ok and prompt_path.exists() and ollama_model else 1


if __name__ == "__main__":
    raise SystemExit(main())
