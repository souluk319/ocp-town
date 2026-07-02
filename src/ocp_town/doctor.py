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


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def check(name: str, ok: bool, detail: str) -> bool:
    marker = "ok" if ok else "fail"
    print(f"[{marker}] {name}: {detail}")
    return ok


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
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
    ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat").strip()
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
    checks.append(check("resident prompt", prompt_path.exists(), str(prompt_path)))
    checks.append(check("memory directory", memory_path.parent.exists(), str(memory_path.parent)))

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
    checks.append(
        check(
            "ollama model",
            ollama_model in model_names,
            f"{ollama_model} found" if ollama_model in model_names else f"{ollama_model} not in ollama list",
        )
    )

    if args.chat and ollama_model in model_names:
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
            result = post_json(f"{ollama_host}/api/chat", payload)
            content = str(result.get("message", {}).get("content", "")).strip()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            checks.append(check("gemma chat", False, f"chat failed: {exc}"))
        else:
            checks.append(check("gemma chat", bool(content), content[:160] or "empty response"))

    if not all(checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
