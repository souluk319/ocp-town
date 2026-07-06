from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from .config import is_home_server_backend, is_openai_backend


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
        if is_home_server_backend(self.backend):
            return self.home_server_chat(system_prompt, content)
        if is_openai_backend(self.backend):
            return self.openai_chat(system_prompt, content)

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

    def openai_chat(self, system_prompt: str, prompt: str) -> str:
        if not self.home_server_base_url:
            raise RuntimeError("KUGNUS_GATEWAY_BASE_URL or OCP_TOWN_HOME_SERVER_BASE_URL is required for openai backend.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.num_predict,
            "stream": False,
        }
        errors: list[str] = []
        for url in openai_chat_urls(self.home_server_base_url):
            try:
                result = self.post_json(url, payload)
            except RuntimeError as exc:
                message = str(exc)
                if "HTTP 404" in message:
                    errors.append(message)
                    continue
                raise
            content = extract_chat_content(result)
            if content:
                return content
            errors.append("OpenAI-compatible gateway returned an empty response.")

        detail = errors[-1] if errors else "no endpoint candidates"
        raise RuntimeError(f"OpenAI-compatible gateway request failed: {detail}")

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
            raise RuntimeError(f"Gateway request failed: HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gateway request failed: {exc}") from exc


def openai_chat_urls(base_url: str) -> list[str]:
    base = base_url.rstrip("/")
    parts = urlsplit(base)
    candidates: list[str] = []
    if base.endswith("/v1"):
        candidates.append(f"{base}/chat/completions")
    else:
        candidates.append(f"{base}/v1/chat/completions")
    if parts.scheme and parts.netloc and parts.path.rstrip("/"):
        origin = urlunsplit((parts.scheme, parts.netloc, "", "", "")).rstrip("/")
        candidates.append(f"{origin}/v1/chat/completions")

    deduped: list[str] = []
    for url in candidates:
        if url not in deduped:
            deduped.append(url)
    return deduped


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
