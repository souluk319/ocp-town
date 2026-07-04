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


def check_home_server(base_url: str, api_key: str) -> tuple[bool, str]:
    if not base_url:
        return False, "missing OCP_TOWN_HOME_SERVER_BASE_URL"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        f"{base_url}/api/home-server/status",
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
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
    ollama_num_predict = os.getenv("OCP_TOWN_OLLAMA_NUM_PREDICT", "320").strip()
    home_server_base_url = os.getenv("OCP_TOWN_HOME_SERVER_BASE_URL", "").strip().rstrip("/")
    llm_backend = os.getenv("OCP_TOWN_LLM_BACKEND", "").strip().lower()
    if not llm_backend:
        llm_backend = "home-server" if home_server_base_url else "ollama"
    prompt_path = PROJECT_ROOT / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md")
    memory_path = PROJECT_ROOT / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl")
    token_configured = bool(
        os.getenv("OCP_TOWN_DISCORD_BOT_TOKEN", "").strip()
        or os.getenv("DISCORD_BOT_TOKEN", "").strip()
    )
    telegram_token_configured = bool(
        os.getenv("OCP_TOWN_TELEGRAM_BOT_TOKEN", "").strip()
        or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    channel_restricted = bool(
        os.getenv("OCP_TOWN_DISCORD_CHANNEL_ID", "").strip()
        or os.getenv("DISCORD_CHANNEL_ID", "").strip()
    )

    print(f"discord token configured: {token_configured}")
    print(f"discord channel restricted: {channel_restricted}")
    print(f"telegram token configured: {telegram_token_configured}")
    print(f"prompt exists: {prompt_path.exists()}")
    print(f"memory directory exists: {memory_path.parent.exists()}")
    print(f"llm backend: {llm_backend}")
    print(f"ollama model configured: {bool(ollama_model)}")
    print(f"ollama num_predict configured: {ollama_num_predict}")

    if llm_backend in {"home-server", "home_server", "sweet12"}:
        ok, detail = check_home_server(
            home_server_base_url,
            os.getenv("OCP_TOWN_HOME_SERVER_API_KEY", "").strip(),
        )
        print(f"home-server gateway: {'ok' if ok else 'fail'} ({detail})")
    else:
        ok, detail = check_ollama(ollama_host)
        print(f"ollama: {'ok' if ok else 'fail'} ({detail})")
    return 0 if ok and prompt_path.exists() and ollama_model else 1


if __name__ == "__main__":
    raise SystemExit(main())
