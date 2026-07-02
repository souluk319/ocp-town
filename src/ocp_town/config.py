from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    discord_channel_id: int | None
    discord_require_mention: bool
    ollama_host: str
    ollama_model: str
    prompt_path: Path
    memory_path: Path


def load_settings(project_root: Path) -> Settings:
    load_dotenv(project_root / ".env")

    token = (
        os.getenv("OCP_TOWN_DISCORD_BOT_TOKEN", "").strip()
        or os.getenv("DISCORD_BOT_TOKEN", "").strip()
    )
    if not token:
        raise RuntimeError(
            "OCP_TOWN_DISCORD_BOT_TOKEN is required. Copy .env.example to .env first."
        )

    channel_id_raw = (
        os.getenv("OCP_TOWN_DISCORD_CHANNEL_ID", "").strip()
        or os.getenv("DISCORD_CHANNEL_ID", "").strip()
    )
    channel_id = int(channel_id_raw) if channel_id_raw else None
    require_mention = os.getenv("OCP_TOWN_REQUIRE_MENTION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return Settings(
        discord_bot_token=token,
        discord_channel_id=channel_id,
        discord_require_mention=require_mention,
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat"),
        prompt_path=project_root / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md"),
        memory_path=project_root / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl"),
    )
