from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaClient:
    host: str
    model: str
    num_predict: int = 320
    temperature: float = 0.35
    backend: str = "ollama"
    home_server_base_url: str = ""
    home_server_api_key: str = ""

    def chat(self, system_prompt: str, user_message: str, context: str = "") -> str:
        content = user_message if not context else f"{context}\n\n사용자 메시지:\n{user_message}"
        if self.backend in {"home-server", "home_server", "sweet12"}:
            return self.home_server_chat(system_prompt, content)

        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "options": {
                "num_predict": self.num_predict,
                "temperature": self.temperature,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        message = result.get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("Ollama returned an empty response.")
        return content

    def home_server_chat(self, system_prompt: str, prompt: str) -> str:
        if not self.home_server_base_url:
            raise RuntimeError("OCP_TOWN_HOME_SERVER_BASE_URL is required for home-server backend.")

        payload = {
            "prompt": prompt,
            "systemPrompt": system_prompt,
            "temperature": self.temperature,
            "maxTokens": self.num_predict,
        }
        result = self.post_json(f"{self.home_server_base_url}/api/home-server/chat", payload)
        content = extract_chat_content(result)
        if not content:
            raise RuntimeError("Home-server gateway returned an empty response.")
        return content

    def post_json(self, url: str, payload: dict[str, object]) -> dict[str, object]:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.home_server_api_key:
            headers["Authorization"] = f"Bearer {self.home_server_api_key}"
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return dict(json.loads(response.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Home-server gateway request failed: HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Home-server gateway request failed: {exc}") from exc


def extract_chat_content(result: object) -> str:
    if isinstance(result, str):
        return result.strip()
    if not isinstance(result, dict):
        return ""

    for key in ("content", "text", "response", "answer", "output"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    message = result.get("message")
    if isinstance(message, str):
        return message.strip()
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()

    data = result.get("data")
    if isinstance(data, dict):
        content = extract_chat_content(data)
        if content:
            return content

    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        return extract_chat_content(choices[0])

    return ""
