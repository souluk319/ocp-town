from __future__ import annotations

import asyncio
from pathlib import Path

import discord

from .config import load_settings
from .memory import JsonlMemory
from .ollama_client import OllamaClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_recent_context(memory: JsonlMemory) -> str:
    turns = memory.recent_turns(limit=8)
    if not turns:
        return ""

    compact: list[str] = ["최근 OCP Town 대화 요약:"]
    for turn in turns:
        role = turn.get("role", "unknown")
        author = turn.get("author", role)
        content = str(turn.get("content", "")).replace("\n", " ")
        compact.append(f"- {author}: {content[:500]}")
    return "\n".join(compact)


class OcpTownBot(discord.Client):
    def __init__(
        self,
        settings,
        prompt: str,
        memory: JsonlMemory,
        ollama: OllamaClient,
    ) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.prompt = prompt
        self.memory = memory
        self.ollama = ollama

    async def on_ready(self) -> None:
        print(f"ocp-town connected as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if self.settings.discord_channel_id and message.channel.id != self.settings.discord_channel_id:
            return

        user_text = message.content.strip()
        if self.settings.discord_require_mention:
            if self.user not in message.mentions:
                return
            if self.user:
                user_text = (
                    user_text.replace(f"<@{self.user.id}>", "")
                    .replace(f"<@!{self.user.id}>", "")
                    .strip()
                )
        if not user_text:
            return

        self.memory.append(
            {
                "role": "user",
                "author": str(message.author),
                "channel_id": message.channel.id,
                "content": user_text,
            }
        )

        async with message.channel.typing():
            try:
                reply = await asyncio.to_thread(
                    self.ollama.chat,
                    self.prompt,
                    user_text,
                    build_recent_context(self.memory),
                )
            except Exception as exc:
                reply = f"OCP Town 주민 호출에 실패했어. Ollama/Gemma 상태를 확인해줘: `{exc}`"

        self.memory.append(
            {
                "role": "assistant",
                "author": "ocp-resident-gemma",
                "channel_id": message.channel.id,
                "content": reply,
            }
        )
        await message.reply(reply[:1900], mention_author=False)


def main() -> None:
    settings = load_settings(PROJECT_ROOT)
    prompt = settings.prompt_path.read_text(encoding="utf-8")
    memory = JsonlMemory(settings.memory_path)
    ollama = OllamaClient(host=settings.ollama_host, model=settings.ollama_model)
    bot = OcpTownBot(settings=settings, prompt=prompt, memory=memory, ollama=ollama)
    bot.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()
