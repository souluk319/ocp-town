from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import bool_env, float_env, int_env, load_dotenv
from .context import build_recent_context
from .memory import JsonlMemory
from .ollama_client import OllamaClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_MESSAGE_LIMIT = 3900


@dataclass(frozen=True)
class TelegramSettings:
    bot_token: str
    chat_id: int | None
    require_mention: bool
    ollama_host: str
    ollama_model: str
    ollama_num_predict: int
    ollama_temperature: float
    prompt_path: Path
    memory_path: Path


def load_telegram_settings(project_root: Path) -> TelegramSettings:
    load_dotenv(project_root / ".env")

    token = (
        os.getenv("OCP_TOWN_TELEGRAM_BOT_TOKEN", "").strip()
        or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    if not token:
        raise RuntimeError("OCP_TOWN_TELEGRAM_BOT_TOKEN is required.")

    chat_id_raw = (
        os.getenv("OCP_TOWN_TELEGRAM_CHAT_ID", "").strip()
        or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    )
    chat_id = int(chat_id_raw) if chat_id_raw else None

    return TelegramSettings(
        bot_token=token,
        chat_id=chat_id,
        require_mention=bool_env("OCP_TOWN_TELEGRAM_REQUIRE_MENTION"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat"),
        ollama_num_predict=int_env("OCP_TOWN_OLLAMA_NUM_PREDICT", 320),
        ollama_temperature=float_env("OCP_TOWN_OLLAMA_TEMPERATURE", 0.35),
        prompt_path=project_root / os.getenv("OCP_TOWN_PROMPT", "prompts/ocp-resident.md"),
        memory_path=project_root / os.getenv("OCP_TOWN_MEMORY", "data/memory.jsonl"),
    )


class TelegramApi:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"

    def call(self, method: str, payload: dict[str, Any] | None = None, timeout: int = 60) -> dict[str, Any]:
        data = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/{method}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram API {method} failed: HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Telegram API {method} failed: {exc}") from exc

        if not result.get("ok"):
            raise RuntimeError(f"Telegram API {method} returned not ok: {result}")
        return result

    def get_me(self) -> dict[str, Any]:
        return dict(self.call("getMe").get("result", {}))

    def get_updates(self, offset: int | None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": 30,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        return list(self.call("getUpdates", payload, timeout=40).get("result", []))

    def send_chat_action(self, chat_id: int, action: str, message_thread_id: int | None = None) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "action": action}
        if message_thread_id is not None:
            payload["message_thread_id"] = message_thread_id
        self.call("sendChatAction", payload, timeout=10)

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> None:
        for chunk in split_message(text):
            payload: dict[str, Any] = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            }
            if reply_to_message_id is not None:
                payload["reply_parameters"] = {"message_id": reply_to_message_id}
            if message_thread_id is not None:
                payload["message_thread_id"] = message_thread_id
            self.call("sendMessage", payload)


def split_message(text: str) -> list[str]:
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        return [text]
    chunks: list[str] = []
    remaining = text
    while remaining:
        chunks.append(remaining[:TELEGRAM_MESSAGE_LIMIT])
        remaining = remaining[TELEGRAM_MESSAGE_LIMIT:]
    return chunks


def should_answer(message: dict[str, Any], settings: TelegramSettings, bot_username: str) -> tuple[bool, str]:
    chat = message.get("chat", {})
    chat_id = int(chat.get("id"))
    if settings.chat_id is not None and chat_id != settings.chat_id:
        return False, ""

    sender = message.get("from", {})
    if sender.get("is_bot"):
        return False, ""

    text = str(message.get("text", "")).strip()
    if not text:
        return False, ""

    if text.startswith("/start"):
        return True, "성욱아, 나 C야. 이제 Telegram 쪽 `kugnus-town` 출입구도 열렸어."

    if text.startswith("/town"):
        cleaned = text.removeprefix("/town").strip()
        return True, cleaned or "오늘 우리 OCP Town 어디부터 볼까?"

    if settings.require_mention and chat.get("type") != "private":
        mention = f"@{bot_username}"
        if mention not in text:
            return False, ""
        text = text.replace(mention, "").strip()

    return bool(text), text


def handle_message(
    api: TelegramApi,
    message: dict[str, Any],
    settings: TelegramSettings,
    prompt: str,
    memory: JsonlMemory,
    ollama: OllamaClient,
    bot_username: str,
) -> None:
    should, user_text = should_answer(message, settings, bot_username)
    if not should:
        return

    chat = message.get("chat", {})
    chat_id = int(chat.get("id"))
    message_id = int(message.get("message_id"))
    message_thread_id = message.get("message_thread_id")
    author = message.get("from", {}).get("username") or message.get("from", {}).get("first_name") or "telegram-user"

    if user_text.startswith("성욱아, 나 C야."):
        api.send_message(chat_id, user_text, reply_to_message_id=message_id, message_thread_id=message_thread_id)
        return

    memory.append(
        {
            "role": "user",
            "platform": "telegram",
            "author": author,
            "chat_id": chat_id,
            "content": user_text,
        }
    )

    try:
        api.send_chat_action(chat_id, "typing", message_thread_id=message_thread_id)
        reply = ollama.chat(
            prompt,
            user_text,
            build_recent_context(memory, platform="telegram", chat_id=chat_id),
        )
    except Exception as exc:
        reply = f"OCP Town 주민 호출에 실패했어. Ollama/Gemma 상태를 확인해줘: `{exc}`"

    memory.append(
        {
            "role": "assistant",
            "platform": "telegram",
            "author": "ocp-resident-gemma",
            "chat_id": chat_id,
            "content": reply,
        }
    )
    api.send_message(chat_id, reply, reply_to_message_id=message_id, message_thread_id=message_thread_id)


def run_telegram_polling(
    project_root: Path,
    prompt: str | None = None,
    memory: JsonlMemory | None = None,
    ollama: OllamaClient | None = None,
) -> None:
    settings = load_telegram_settings(project_root)
    prompt = prompt if prompt is not None else settings.prompt_path.read_text(encoding="utf-8")
    memory = memory if memory is not None else JsonlMemory(settings.memory_path)
    if ollama is None:
        ollama = OllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
            num_predict=settings.ollama_num_predict,
            temperature=settings.ollama_temperature,
        )
    api = TelegramApi(settings.bot_token)
    bot = api.get_me()
    bot_username = str(bot.get("username", "")).strip()
    print(f"ocp-town-telegram connected as @{bot_username or bot.get('first_name', 'unknown')}")

    offset: int | None = None
    while True:
        try:
            updates = api.get_updates(offset)
            for update in updates:
                offset = int(update["update_id"]) + 1
                message = update.get("message")
                if message:
                    handle_message(api, message, settings, prompt, memory, ollama, bot_username)
        except KeyboardInterrupt:
            print("ocp-town-telegram stopped")
            return
        except Exception as exc:
            print(f"ocp-town-telegram warning: {exc}")
            time.sleep(3)


def main() -> None:
    run_telegram_polling(PROJECT_ROOT)


if __name__ == "__main__":
    main()
