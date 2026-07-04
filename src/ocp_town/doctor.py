from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import load_dotenv
from .ollama_client import OllamaClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def check(name: str, ok: bool, detail: str) -> bool:
    marker = "ok" if ok else "fail"
    print(f"[{marker}] {name}: {detail}")
    return ok


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_home_server_status(base_url: str, api_key: str) -> dict[str, Any]:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        f"{base_url}/api/home-server/status",
        headers=headers,
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Check the OCP Town Discord/Ollama setup.")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Run a short Gemma chat completion, not just model discovery.",
    )
    args = parser.parse_args(argv)

    load_dotenv(PROJECT_ROOT / ".env")

    token = (
        os.getenv("OCP_TOWN_DISCORD_BOT_TOKEN", "").strip()
        or os.getenv("DISCORD_BOT_TOKEN", "").strip()
    )
    channel_id = (
        os.getenv("OCP_TOWN_DISCORD_CHANNEL_ID", "").strip()
        or os.getenv("DISCORD_CHANNEL_ID", "").strip()
    )
    require_mention = os.getenv("OCP_TOWN_REQUIRE_MENTION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    telegram_token = (
        os.getenv("OCP_TOWN_TELEGRAM_BOT_TOKEN", "").strip()
        or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    telegram_chat_id = (
        os.getenv("OCP_TOWN_TELEGRAM_CHAT_ID", "").strip()
        or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    )
    ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat").strip()
    ollama_num_predict = os.getenv("OCP_TOWN_OLLAMA_NUM_PREDICT", "320").strip()
    ollama_temperature = os.getenv("OCP_TOWN_OLLAMA_TEMPERATURE", "0.35").strip()
    home_server_base_url = os.getenv("OCP_TOWN_HOME_SERVER_BASE_URL", "").strip().rstrip("/")
    home_server_api_key = os.getenv("OCP_TOWN_HOME_SERVER_API_KEY", "").strip()
    llm_backend = os.getenv("OCP_TOWN_LLM_BACKEND", "").strip().lower()
    if not llm_backend:
        llm_backend = "home-server" if home_server_base_url else "ollama"
    prompt_path = PROJECT_ROOT / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md")
    memory_path = PROJECT_ROOT / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl")

    checks: list[bool] = []
    checks.append(
        check(
            "discord token",
            bool(token),
            "set" if token else "missing OCP_TOWN_DISCORD_BOT_TOKEN",
        )
    )
    checks.append(
        check(
            "discord channel",
            not channel_id or channel_id.isdigit(),
            channel_id if channel_id else "not pinned; bot will answer in any server channel it can read",
        )
    )
    checks.append(check("activation", True, "mention required" if require_mention else "channel messages"))
    checks.append(check("telegram token", True, "set" if telegram_token else "not configured"))
    checks.append(
        check(
            "telegram chat",
            not telegram_chat_id or telegram_chat_id.lstrip("-").isdigit(),
            telegram_chat_id if telegram_chat_id else "not pinned; Telegram bot will answer in any chat it can read",
        )
    )
    if telegram_token:
        try:
            telegram_me = fetch_json(f"https://api.telegram.org/bot{telegram_token}/getMe", timeout=10)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            checks.append(check("telegram api", False, f"getMe failed without exposing token: {exc}"))
        else:
            telegram_user = telegram_me.get("result", {})
            telegram_name = telegram_user.get("username") or telegram_user.get("first_name") or "unknown"
            checks.append(check("telegram api", bool(telegram_me.get("ok")), f"@{telegram_name}"))
    else:
        checks.append(check("telegram api", True, "skipped"))
    checks.append(check("resident prompt", prompt_path.exists(), str(prompt_path)))
    checks.append(check("memory directory", memory_path.parent.exists(), str(memory_path.parent)))
    checks.append(check("llm backend", llm_backend in {"ollama", "home-server", "home_server", "sweet12"}, llm_backend))
    checks.append(check("ollama num_predict", ollama_num_predict.isdigit(), ollama_num_predict))

    use_home_server = llm_backend in {"home-server", "home_server", "sweet12"}
    model_ready = False
    if use_home_server:
        try:
            status = fetch_home_server_status(home_server_base_url, home_server_api_key)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            checks.append(check("home-server status", False, f"status failed: {exc}"))
        else:
            checks.append(check("home-server status", True, "reachable"))
            status_text = json.dumps(status, ensure_ascii=False)
            model_ready = True
            model_detail = (
                f"{ollama_model} reported by status"
                if ollama_model and ollama_model in status_text
                else "gateway reachable; chat endpoint is authoritative"
            )
            checks.append(
                check(
                    "home-server chat model",
                    True,
                    model_detail,
                )
            )
    else:
        try:
            tags = fetch_json(f"{ollama_host}/api/tags")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            checks.append(check("ollama tags", False, f"{ollama_host}/api/tags failed: {exc}"))
            tags = {"models": []}
        else:
            checks.append(check("ollama tags", True, f"{ollama_host}/api/tags reachable"))

        model_names = {
            str(model.get("name") or model.get("model"))
            for model in tags.get("models", [])
            if model.get("name") or model.get("model")
        }
        model_ready = ollama_model in model_names
        checks.append(
            check(
                "ollama model",
                model_ready,
                f"{ollama_model} found" if model_ready else f"{ollama_model} not in ollama list",
            )
        )

    if args.chat and model_ready:
        payload = {
            "model": ollama_model,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": "한국어로 아주 짧게 답한다."},
                {"role": "user", "content": "OCP Town 연결 확인. '주민 온라인'이라고 답해."},
            ],
            "options": {"num_predict": 64},
        }
        try:
            if use_home_server:
                client = OllamaClient(
                    host=ollama_host,
                    model=ollama_model,
                    num_predict=64,
                    temperature=float(ollama_temperature),
                    backend=llm_backend,
                    home_server_base_url=home_server_base_url,
                    home_server_api_key=home_server_api_key,
                )
                content = client.chat("한국어로 아주 짧게 답한다.", "OCP Town 연결 확인. '주민 온라인'이라고 답해.")
            else:
                result = post_json(f"{ollama_host}/api/chat", payload)
                content = str(result.get("message", {}).get("content", "")).strip()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            checks.append(check("gemma chat", False, f"chat failed: {exc}"))
        except RuntimeError as exc:
            checks.append(check("gemma chat", False, str(exc)))
        else:
            checks.append(check("gemma chat", bool(content), content[:160] or "empty response"))

    if not all(checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
