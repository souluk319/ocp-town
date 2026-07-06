from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


HOME_SERVER_BACKENDS = {"home-server", "home_server", "sweet12"}
OPENAI_BACKENDS = {
    "openai",
    "openai-compatible",
    "openai_compatible",
    "kugnus-gateway",
    "kugnus_gateway",
}


def bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc


def float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number.") from exc


def first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


def home_server_base_url_env() -> str:
    return first_env("KUGNUS_GATEWAY_BASE_URL", "OCP_TOWN_HOME_SERVER_BASE_URL").rstrip("/")


def home_server_api_key_env() -> str:
    return first_env("KUGNUS_GATEWAY_API_KEY", "OCP_TOWN_HOME_SERVER_API_KEY")


def llm_backend_env(home_server_base_url: str | None = None) -> str:
    base_url = home_server_base_url if home_server_base_url is not None else home_server_base_url_env()
    llm_backend = first_env("OCP_TOWN_LLM_BACKEND").lower()
    if llm_backend:
        return llm_backend
    if first_env("KUGNUS_GATEWAY_BASE_URL"):
        return "openai"
    return "home-server" if base_url else "ollama"


def is_home_server_backend(backend: str) -> bool:
    return backend in HOME_SERVER_BACKENDS


def is_openai_backend(backend: str) -> bool:
    return backend in OPENAI_BACKENDS


def ollama_host_env() -> str:
    return first_env("OLLAMA_HOST", "LLM_BASE_URL", default="http://localhost:11434").rstrip("/")


def ollama_model_env() -> str:
    return first_env("OLLAMA_MODEL", "LLM_MODEL", "KUGNUS_GATEWAY_MODEL", default="gemma4:12b-it-qat")


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
    llm_backend: str
    home_server_base_url: str
    home_server_api_key: str
    ollama_host: str
    ollama_model: str
    ollama_num_predict: int
    ollama_temperature: float
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
    require_mention = bool_env("OCP_TOWN_REQUIRE_MENTION")
    home_server_base_url = home_server_base_url_env()
    llm_backend = llm_backend_env(home_server_base_url)

    return Settings(
        discord_bot_token=token,
        discord_channel_id=channel_id,
        discord_require_mention=require_mention,
        llm_backend=llm_backend,
        home_server_base_url=home_server_base_url,
        home_server_api_key=home_server_api_key_env(),
        ollama_host=ollama_host_env(),
        ollama_model=ollama_model_env(),
        ollama_num_predict=int_env("OCP_TOWN_OLLAMA_NUM_PREDICT", 320),
        ollama_temperature=float_env("OCP_TOWN_OLLAMA_TEMPERATURE", 0.35),
        prompt_path=project_root / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md"),
        memory_path=project_root / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl"),
    )
